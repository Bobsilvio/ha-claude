"""
Persistent memory system for storing and retrieving conversation history.
Enables the AI assistant to remember past conversations and learn from previous interactions.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path


MEMORY_DIR = "/config/.storage/claude_memory"
CONVERSATIONS_FILE = os.path.join(MEMORY_DIR, "conversations.json")
MEMORY_INDEX_FILE = os.path.join(MEMORY_DIR, "memory_index.json")


def ensure_memory_dir() -> None:
    """Ensure memory directory exists."""
    os.makedirs(MEMORY_DIR, exist_ok=True)


def save_conversation(
    session_id: str,
    title: str,
    messages: List[Dict],
    provider: str,
    model: str,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Save a completed conversation to persistent storage.
    
    Args:
        session_id: Unique conversation identifier
        title: Human-readable conversation title
        messages: List of message dicts with role/content
        provider: AI provider used (anthropic, openai, etc.)
        model: Model identifier
        metadata: Optional extra metadata (tags, summary, etc.)
    
    Returns:
        Saved conversation record
    """
    ensure_memory_dir()
    
    # Create conversation record
    record = {
        "id": session_id,
        "title": title,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "provider": provider,
        "model": model,
        "message_count": len(messages),
        "messages": messages[-50:],  # Keep last 50 messages to avoid bloat
        "summary": _generate_summary(messages),
        "keywords": _extract_keywords(messages),
        "metadata": metadata or {}
    }
    
    # Load existing conversations
    conversations = _load_conversations()
    
    # Add/update
    conversations[session_id] = record
    
    # Save back
    with open(CONVERSATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)
    
    # Update index for faster searching
    _update_memory_index(conversations)
    
    return record


def get_past_conversations(
    limit: int = 10,
    days_back: int = 30,
    provider: Optional[str] = None
) -> List[Dict]:
    """
    Retrieve past conversations within time window.
    
    Args:
        limit: Maximum number to return
        days_back: Only retrieve conversations from last N days
        provider: Filter by specific provider (optional)
    
    Returns:
        List of conversation records sorted by recency
    """
    ensure_memory_dir()
    conversations = _load_conversations()
    
    cutoff = datetime.now() - timedelta(days=days_back)
    
    results = []
    for conv_id, conv in conversations.items():
        created = datetime.fromisoformat(conv["created"])
        
        # Check time window
        if created < cutoff:
            continue
        
        # Check provider filter
        if provider and conv.get("provider") != provider:
            continue
        
        results.append(conv)
    
    # Sort by recency (newest first)
    results.sort(key=lambda x: x["updated"], reverse=True)
    
    return results[:limit]


def search_memory(
    query: str,
    limit: int = 5,
    days_back: int = 30
) -> List[Tuple[Dict, float]]:
    """
    Search past conversations for relevant discussions.
    Returns conversations ranked by relevance score.
    
    Args:
        query: Search query/keywords
        limit: Maximum results to return
        days_back: Search window in days
    
    Returns:
        List of (conversation, score) tuples sorted by relevance
    """
    import re
    ensure_memory_dir()
    conversations = _load_conversations()
    
    query_lower = query.lower()
    # Extract meaningful words from query (length > 2)
    query_words = set(w for w in re.findall(r'[a-zA-ZàèìòùáéíóúñÑ0-9]+', query_lower) if len(w) > 2)
    
    cutoff = datetime.now() - timedelta(days=days_back)
    results = []
    
    for conv_id, conv in conversations.items():
        created = datetime.fromisoformat(conv["created"])
        if created < cutoff:
            continue
        
        score = 0.0
        
        # Score based on keyword matches (individual word matching)
        conv_keywords = set(conv.get("keywords", []))
        keyword_matches = query_words & conv_keywords
        score += len(keyword_matches) * 1.5
        
        # Score based on individual word matches in title
        title_lower = conv.get("title", "").lower()
        for word in query_words:
            if word in title_lower:
                score += 1.0
        
        # Score based on individual word matches in summary
        summary_lower = conv.get("summary", "").lower()
        for word in query_words:
            if word in summary_lower:
                score += 0.5
        
        # Score based on actual message content search
        messages = conv.get("messages", [])
        msg_text = " ".join(
            m.get("content", "").lower() for m in messages 
            if isinstance(m.get("content"), str)
        )
        content_matches = sum(1 for word in query_words if word in msg_text)
        score += content_matches * 0.8
        
        if score > 0:
            results.append((conv, score))
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:limit]


def get_memory_context(
    query: Optional[str] = None,
    limit: int = 3,
    max_tokens: int = 2000
) -> str:
    """
    Generate memory context for AI - relevant past conversations formatted for injection.
    
    Args:
        query: Current user query (used for semantic search)
        limit: Number of conversations to include
        max_tokens: Approximate token limit for context
    
    Returns:
        Formatted string of past conversations to inject into system prompt
    """
    if query:
        # Search for relevant conversations
        results = search_memory(query, limit=limit)
        conversations = [conv for conv, _score in results]
    else:
        # Just get recent ones
        conversations = get_past_conversations(limit=limit)
    
    if not conversations:
        return ""
    
    context_lines = ["## MEMORIA PERSISTENTE - Conversazioni passate rilevanti:\n"]
    token_count = 0
    
    for i, conv in enumerate(conversations, 1):
        title = conv.get("title", "Untitled")
        created = conv.get("created", "Unknown date")[:10]
        
        # Include actual messages for better context, not just summary
        messages = conv.get("messages", [])
        msg_lines = []
        for m in messages:
            content = m.get("content", "")
            if not isinstance(content, str):
                continue
            role = m.get("role", "unknown")
            if role in ("user", "assistant"):
                msg_lines.append(f"  {role}: {content[:200]}")
        
        block = f"{i}. [{created}] {title}\n"
        if msg_lines:
            block += "\n".join(msg_lines[:8]) + "\n"  # Max 8 messages per conversation
        else:
            block += f"  {conv.get('summary', 'No summary')}\n"
        
        block_tokens = len(block) // 4
        if token_count + block_tokens > max_tokens:
            context_lines.append(f"   ... ({len(conversations) - i} more conversations disponibili)")
            break
        
        context_lines.append(block)
        token_count += block_tokens
    
    context_lines.append("\nUSA queste informazioni dalle conversazioni passate per dare risposte personalizzate e coerenti. Se l'utente ha condiviso informazioni personali (nome, età, preferenze), ricordale.\n")
    
    return "\n".join(context_lines)


def delete_conversation(session_id: str) -> bool:
    """Delete a conversation from memory."""
    ensure_memory_dir()
    conversations = _load_conversations()
    
    if session_id in conversations:
        del conversations[session_id]
        with open(CONVERSATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
        _update_memory_index(conversations)
        return True
    
    return False


def clear_old_memories(days: int = 90) -> int:
    """Delete conversations older than N days. Returns count deleted."""
    ensure_memory_dir()
    conversations = _load_conversations()
    cutoff = datetime.now() - timedelta(days=days)
    
    to_delete = []
    for conv_id, conv in conversations.items():
        created = datetime.fromisoformat(conv["created"])
        if created < cutoff:
            to_delete.append(conv_id)
    
    for conv_id in to_delete:
        del conversations[conv_id]
    
    if to_delete:
        with open(CONVERSATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
        _update_memory_index(conversations)
    
    return len(to_delete)


def get_memory_stats() -> Dict:
    """Get statistics about stored memories."""
    ensure_memory_dir()
    conversations = _load_conversations()
    
    if not conversations:
        return {"total_conversations": 0, "total_messages": 0, "oldest": None, "newest": None}
    
    total_messages = sum(conv.get("message_count", 0) for conv in conversations.values())
    dates = [conv.get("created") for conv in conversations.values()]
    dates_sorted = sorted([d for d in dates if d])
    
    return {
        "total_conversations": len(conversations),
        "total_messages": total_messages,
        "oldest": dates_sorted[0] if dates_sorted else None,
        "newest": dates_sorted[-1] if dates_sorted else None,
        "storage_kb": os.path.getsize(CONVERSATIONS_FILE) / 1024 if os.path.exists(CONVERSATIONS_FILE) else 0
    }


# Private helper functions

def _load_conversations() -> Dict:
    """Load all conversations from storage."""
    ensure_memory_dir()
    
    if not os.path.exists(CONVERSATIONS_FILE):
        return {}
    
    try:
        with open(CONVERSATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _generate_summary(messages: List[Dict], max_length: int = 500) -> str:
    """Generate a summary of the conversation including key facts."""
    if not messages:
        return "Empty conversation"
    
    # Collect ALL user messages (up to a limit) for better context
    user_msgs = []
    assistant_msgs = []
    for m in messages:
        content = m.get("content", "")
        if not isinstance(content, str):
            continue
        if m.get("role") == "user":
            user_msgs.append(content[:150])
        elif m.get("role") == "assistant":
            assistant_msgs.append(content[:150])
    
    parts = []
    # Include first few user messages for context
    for i, msg in enumerate(user_msgs[:5]):
        parts.append(f"User: {msg}")
    # Include key assistant responses
    for i, msg in enumerate(assistant_msgs[:3]):
        parts.append(f"Assistant: {msg}")
    
    summary = " | ".join(parts)
    if len(summary) > max_length:
        summary = summary[:max_length] + "..."
    
    return summary if summary else "Conversation with various messages"


def _extract_keywords(messages: List[Dict], max_keywords: int = 20) -> List[str]:
    """Extract keywords from conversation for better searching."""
    from collections import Counter
    import re
    
    all_text = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))
    # Extract words, including numbers
    words = re.findall(r'[a-zA-ZàèìòùÀÈÌÒÙáéíóúÁÉÍÓÚñÑ0-9]+', all_text.lower())
    
    # Filter: length > 2, not common stop words
    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her",
        "was", "one", "our", "out", "has", "have", "been", "some", "them", "than",
        "its", "over", "such", "that", "this", "with", "will", "each", "make",
        "che", "non", "per", "una", "sono", "come", "del", "della", "con",
        "les", "des", "une", "que", "qui", "est", "dans", "pour", "sur",
        "los", "las", "por", "como"
    }
    filtered = [w for w in words if len(w) > 2 and w not in stop_words]
    
    # Get most common - include even single mentions for short conversations
    counter = Counter(filtered)
    keywords = [word for word, count in counter.most_common(max_keywords)]
    
    return keywords


def _update_memory_index(conversations: Dict) -> None:
    """Update search index for faster queries."""
    # Create a quick lookup index
    index = {
        "total": len(conversations),
        "providers": {},
        "recent": list(sorted(conversations.keys(), 
                            key=lambda x: conversations[x].get("created", ""),
                            reverse=True))[:20]
    }
    
    for conv_id, conv in conversations.items():
        provider = conv.get("provider", "unknown")
        if provider not in index["providers"]:
            index["providers"][provider] = 0
        index["providers"][provider] += 1
    
    with open(MEMORY_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
