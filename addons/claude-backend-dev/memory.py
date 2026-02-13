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
    ensure_memory_dir()
    conversations = _load_conversations()
    
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    cutoff = datetime.now() - timedelta(days=days_back)
    results = []
    
    for conv_id, conv in conversations.items():
        created = datetime.fromisoformat(conv["created"])
        if created < cutoff:
            continue
        
        # Score based on keyword matches
        score = 0.0
        conv_keywords = set(conv.get("keywords", []))
        score += len(query_words & conv_keywords) * 1.0
        
        # Score based on title match
        if query_lower in conv.get("title", "").lower():
            score += 2.0
        
        # Score based on summary match
        if query_lower in conv.get("summary", "").lower():
            score += 0.5
        
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
    
    context_lines = ["🧠 **MEMORY CONTEXT** - Relevant past conversations:\n"]
    token_count = 0
    
    for i, conv in enumerate(conversations, 1):
        # Format conversation summary
        summary = conv.get("summary", "No summary available")
        title = conv.get("title", "Untitled")
        created = conv.get("created", "Unknown date")[:10]  # Just date part
        
        block = f"{i}. **{title}** ({created})\n   {summary}\n"
        block_tokens = len(block) // 4  # Rough estimate
        
        if token_count + block_tokens > max_tokens:
            context_lines.append(f"   ... ({len(conversations) - i} more conversations available)")
            break
        
        context_lines.append(block)
        token_count += block_tokens
    
    context_lines.append("\nUse this context to provide more personalized and consistent responses.\n")
    
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


def _generate_summary(messages: List[Dict], max_length: int = 200) -> str:
    """Generate a brief summary of the conversation."""
    if not messages:
        return "Empty conversation"
    
    # Take first user message and last assistant message
    first_user = next((m.get("content", "")[:100] for m in messages if m.get("role") == "user"), "")
    last_assistant = next((m.get("content", "")[:100] for m in reversed(messages) if m.get("role") == "assistant"), "")
    
    if first_user and last_assistant:
        return f"Q: {first_user}... A: {last_assistant}..."
    elif first_user:
        return f"User asked: {first_user}..."
    else:
        return "Conversation with various messages"


def _extract_keywords(messages: List[Dict], max_keywords: int = 10) -> List[str]:
    """Extract keywords from conversation for better searching."""
    # Simple keyword extraction: words > 5 chars that appear multiple times
    from collections import Counter
    
    all_text = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))
    words = all_text.lower().split()
    
    # Filter: length > 5, not common words
    common_words = {"what", "which", "where", "when", "there", "these", "those", "about", "with", "from"}
    filtered = [w for w in words if len(w) > 5 and w not in common_words]
    
    # Get most common
    counter = Counter(filtered)
    keywords = [word for word, count in counter.most_common(max_keywords) if count > 1]
    
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
