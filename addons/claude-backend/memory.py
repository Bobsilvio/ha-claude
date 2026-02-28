"""
Persistent memory system for storing and retrieving conversation history.
Enables the AI assistant to remember past conversations and learn from previous interactions.
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


AMIRA_DIR = "/config/amira"
MEMORY_DIR = os.path.join(AMIRA_DIR, "memory")
CONVERSATIONS_FILE = os.path.join(MEMORY_DIR, "conversations.json")
MEMORY_INDEX_FILE = os.path.join(MEMORY_DIR, "memory_index.json")

# Nanobot-style two-layer memory files
MEMORY_FILE = os.path.join(MEMORY_DIR, "MEMORY.md")   # long-term facts, always in context
HISTORY_FILE = os.path.join(MEMORY_DIR, "HISTORY.md")  # append-only session log


def ensure_memory_dir() -> None:
    """Ensure memory directory exists. Migrates from legacy /config/.storage/claude_memory if needed."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    # One-time migration from old path
    old_dir = "/config/.storage/claude_memory"
    if os.path.isdir(old_dir):
        import shutil
        try:
            for fname in os.listdir(old_dir):
                src = os.path.join(old_dir, fname)
                dst = os.path.join(MEMORY_DIR, fname)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    logger.info(f"Migrated memory file: {fname} → /config/amira/memory/")
        except Exception as e:
            logger.warning(f"Legacy memory migration error: {e}")


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

    # Append summary entry to HISTORY.md (nanobot-style append-only log)
    try:
        summary = record.get("summary", "")
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        history_entry = f"[{date_str}] {title} ({provider}/{model}) — {summary}"
        append_history(history_entry)
    except Exception as e:
        logger.warning(f"Could not append to HISTORY.md: {e}")

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


# Minimum relevance score to consider a past conversation worth injecting.
# Score 2.0 means at least: 1 keyword match (1.5) + 1 word in summary (0.5).
# This prevents generic greetings like "ciao" from triggering unrelated memories.
MIN_MEMORY_SCORE = 2.0


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
        
        if score >= MIN_MEMORY_SCORE:
            results.append((conv, score))
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:limit]


def get_long_term_memory() -> str:
    """Read MEMORY.md content (long-term facts). Returns empty string if not present or empty."""
    ensure_memory_dir()
    try:
        if os.path.exists(MEMORY_FILE):
            content = open(MEMORY_FILE, encoding='utf-8').read().strip()
            # Return content only if it has substantive data (> 150 chars filters out empty templates)
            if content and len(content) > 150:
                return content
    except Exception as e:
        logger.warning(f"Could not read MEMORY.md: {e}")
    return ""


def update_long_term_memory(content: str) -> None:
    """Write/replace MEMORY.md with new content."""
    ensure_memory_dir()
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        logger.warning(f"Could not write MEMORY.md: {e}")


def append_history(entry: str) -> None:
    """Append an entry to HISTORY.md (append-only session log)."""
    ensure_memory_dir()
    try:
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            f.write(entry.rstrip() + "\n\n")
    except Exception as e:
        logger.warning(f"Could not append to HISTORY.md: {e}")


def get_memory_context() -> str:
    """
    Return long-term memory content for system prompt injection (nanobot style).

    Reads MEMORY.md once and returns its content formatted for the system prompt.
    No per-message search, no cross-session BM25 injection.
    Returns empty string if MEMORY.md is empty or does not exist.
    """
    long_term = get_long_term_memory()
    if long_term:
        return f"## MEMORIA A LUNGO TERMINE\n\n{long_term}\n"
    return ""


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

# ============================================================================
# ============================================================================
# GREP SEARCH — fast recursive search on YAML config files
# ============================================================================

class GrepSearch:
    """Fast grep-based text search on HA config files."""

    @staticmethod
    def search_in_file(filepath: str, pattern: str) -> List[Dict[str, Any]]:
        """Search for a regex pattern in a single file. Returns list of {line, content}."""
        try:
            if not os.path.exists(filepath):
                return []
            result = subprocess.run(
                ["grep", "-n", "-i", "-E", pattern, filepath],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return []
            matches = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split(":", 1)
                if len(parts) == 2:
                    try:
                        matches.append({"line": int(parts[0]), "content": parts[1].strip()})
                    except ValueError:
                        pass
            return matches
        except Exception as e:
            logger.error(f"GrepSearch.search_in_file error: {e}")
            return []

    @staticmethod
    def search_in_directory(
        directory: str,
        pattern: str,
        file_pattern: str = "*.yaml",
    ) -> Dict[str, List[str]]:
        """Recursively search for a regex pattern in all matching files under directory.

        Returns {filepath: [matching_line, ...]} for files that contain matches.
        """
        try:
            result = subprocess.run(
                ["grep", "-r", "-n", "-i", "-E", pattern, directory,
                 f"--include={file_pattern}"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return {}
            results: Dict[str, List[str]] = {}
            for line in result.stdout.strip().split("\n"):
                if not line or ":" not in line:
                    continue
                filepath, content = line.split(":", 1)
                results.setdefault(filepath, []).append(content.strip())
            return results
        except Exception as e:
            logger.error(f"GrepSearch.search_in_directory error: {e}")
            return {}


# Convenience module-level function
def grep_config(pattern: str, file_pattern: str = "*.yaml") -> Dict[str, List[str]]:
    """Search recursively in /config for a regex pattern. Returns {filepath: [lines]}."""
    return GrepSearch.search_in_directory("/config", pattern, file_pattern)


# ============================================================================
# TWO-LAYER MEMORY SYSTEM FOR CONFIG_EDIT (Layer 2: File Cache)
# ============================================================================

import hashlib
from collections import Counter as CounterCollections


class FileMemoryCache:
    """Long-term file cache for config_edit operations with grep-based search.
    
    Caches read YAML files for fast access and search during multi-round config editing.
    Uses MD5 hashing for invalidation detection.
    """
    
    def __init__(self, max_files: int = 20, max_size_per_file: int = 100000):
        """Initialize file memory cache.
        
        Args:
            max_files: Maximum files to keep in cache (default 20)
            max_size_per_file: Max bytes per file before skipping cache (default 100KB)
        """
        self.cache: Dict[str, Dict] = {}  # filename -> {content, hash, size}
        self.max_files = max_files
        self.max_size_per_file = max_size_per_file
        self.access_order: List[str] = []  # For LRU eviction
        
    def store(self, filename: str, content: str) -> bool:
        """Store file in cache.
        
        Args:
            filename: File path (relative, e.g. 'packages/sensor.yaml')
            content: File content
            
        Returns:
            True if cached, False if too large
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if len(content) > self.max_size_per_file:
            logger.warning(f"FileCache: {filename} too large ({len(content)} bytes), skipping")
            return False
        
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Store in cache
        self.cache[filename] = {
            "content": content,
            "hash": content_hash,
            "size": len(content),
        }
        
        # Update access order for LRU
        if filename in self.access_order:
            self.access_order.remove(filename)
        self.access_order.append(filename)
        
        # Evict oldest if over limit
        if len(self.cache) > self.max_files:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
            logger.debug(f"FileCache: Evicted {oldest} (LRU)")
        
        logger.debug(f"FileCache: Cached {filename} ({len(content)} bytes)")
        return True
    
    def get(self, filename: str) -> Optional[str]:
        """Retrieve file from cache.
        
        Args:
            filename: File path
            
        Returns:
            File content if cached, None otherwise
        """
        if filename in self.cache:
            # Update access order (LRU)
            self.access_order.remove(filename)
            self.access_order.append(filename)
            return self.cache[filename]["content"]
        return None
    
    def check_changed(self, filename: str, new_content: str) -> bool:
        """Check if file has changed since caching.
        
        Args:
            filename: File path
            new_content: New file content
            
        Returns:
            True if file changed, False if unchanged (cache hit)
        """
        if filename not in self.cache:
            return True  # Not cached, consider as "changed"
        
        new_hash = hashlib.md5(new_content.encode()).hexdigest()
        old_hash = self.cache[filename]["hash"]
        
        return new_hash != old_hash
    
    def search(self, filename: str, search_term: str, max_results: int = 5) -> List[Tuple[int, str]]:
        """Search for lines in cached file (grep-like).
        
        Args:
            filename: File path
            search_term: Search term (case-insensitive)
            max_results: Max results to return
            
        Returns:
            List of (line_number, line_text) tuples
        """
        content = self.get(filename)
        if not content:
            return []
        
        results = []
        search_lower = search_term.lower()
        
        for line_num, line in enumerate(content.split("\n"), 1):
            if search_lower in line.lower():
                results.append((line_num, line))
                if len(results) >= max_results:
                    break
        
        return results
    
    def get_yaml_path_suggestions(self, filename: str, depth: int = 1, max_count: int = 10) -> List[str]:
        """Extract YAML keys at indentation depth (for autocomplete suggestions).
        
        Args:
            filename: File path
            depth: Indentation level (1 = top-level)
            max_count: Max suggestions
            
        Returns:
            List of key names
        """
        content = self.get(filename)
        if not content:
            return []
        
        keys = []
        target_indent = (depth - 1) * 2  # Assuming 2-space indent
        
        for line in content.split("\n"):
            if not line.strip() or line.strip().startswith("#"):
                continue
            
            indent = len(line) - len(line.lstrip())
            if indent == target_indent:
                key = line.strip().split(":")[0].lstrip("- ").strip()
                if key and key not in keys:
                    keys.append(key)
                    if len(keys) >= max_count:
                        break
        
        return keys
    
    def stats(self) -> Dict:
        """Get cache statistics.
        
        Returns:
            Dict with cache info
        """
        total_bytes = sum(item["size"] for item in self.cache.values())
        return {
            "cached_files": len(self.cache),
            "total_bytes": total_bytes,
            "files": list(self.cache.keys()),
            "capacity": f"{len(self.cache)}/{self.max_files}",
        }
    
    def clear(self) -> None:
        """Clear all cached files."""
        self.cache.clear()
        self.access_order.clear()


# Global file memory cache instance (Layer 2)
_config_file_cache = FileMemoryCache(max_files=20)


def get_config_file_cache() -> FileMemoryCache:
    """Get the global file memory cache for config_edit.
    
    Returns:
        FileMemoryCache instance
    """
    return _config_file_cache