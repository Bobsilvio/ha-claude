"""Semantic caching layer with similarity-based retrieval.

Inspired by nanobot: Minimal semantic cache that stores and retrieves based on meaning,
not just exact hash matching. Uses simple embeddings and similarity scoring.
"""

import json
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class SimpleEmbedding:
    """Simple token-based embedding for semantic similarity."""
    
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Get simple embedding based on token frequency (TF-IDF style).
        
        Uses minimal approach: token frequency scaled by inverse document frequency.
        """
        if not text:
            return []
        
        # Simple tokenization
        tokens = text.lower().split()
        token_freq = {}
        for token in tokens:
            token_freq[token] = token_freq.get(token, 0) + 1
        
        # Convert to sorted vector for reproducibility
        sorted_tokens = sorted(token_freq.items(), key=lambda x: x[1], reverse=True)[:100]
        
        # Create simple embedding: [frequency, token_hash] pairs
        embedding = []
        for token, freq in sorted_tokens:
            # Normalize frequency
            norm_freq = freq / max(len(tokens), 1)
            embedding.append(norm_freq)
        
        # Pad to fixed size
        while len(embedding) < 100:
            embedding.append(0.0)
        
        return embedding[:100]
    
    @staticmethod
    def cosine_similarity(embed1: List[float], embed2: List[float]) -> float:
        """Calculate cosine similarity between embeddings."""
        if not embed1 or not embed2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(embed1, embed2))
        magnitude1 = math.sqrt(sum(a * a for a in embed1))
        magnitude2 = math.sqrt(sum(b * b for b in embed2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


class SemanticCacheEntry:
    """Represents a cached entry with metadata."""
    
    def __init__(self, query: str, result: Any, ttl_minutes: int = 30):
        """Initialize cache entry."""
        self.query = query
        self.result = result
        self.embedding = SimpleEmbedding.get_embedding(query)
        self.hash = hashlib.md5(query.encode()).hexdigest()
        self.created_at = datetime.now()
        self.ttl = timedelta(minutes=ttl_minutes)
        self.access_count = 0
        self.last_accessed = datetime.now()
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.now() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """Update access time and count."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def similarity_to(self, query: str) -> float:
        """Calculate similarity to another query."""
        other_embedding = SimpleEmbedding.get_embedding(query)
        return SimpleEmbedding.cosine_similarity(self.embedding, other_embedding)


class SemanticCache:
    """Semantic cache with similarity-based retrieval."""
    
    def __init__(self, max_entries: int = 100, similarity_threshold: float = 0.85):
        """Initialize semantic cache.
        
        Args:
            max_entries: Maximum number of cached entries
            similarity_threshold: Minimum similarity (0-1) to return cache hit
        """
        self.max_entries = max_entries
        self.similarity_threshold = similarity_threshold
        self.entries: Dict[str, SemanticCacheEntry] = {}
        self.queries_hash: Dict[str, str] = {}  # Query text -> hash
    
    def set(self, query: str, result: Any, ttl_minutes: int = 30) -> None:
        """Store query result in cache."""
        entry = SemanticCacheEntry(query, result, ttl_minutes)
        
        # LRU eviction if needed
        if len(self.entries) >= self.max_entries:
            oldest = min(self.entries.values(), key=lambda e: e.last_accessed)
            del self.entries[oldest.hash]
            logger.debug(f"Evicted cached entry (age: {(datetime.now() - oldest.created_at).seconds}s)")
        
        self.entries[entry.hash] = entry
        self.queries_hash[query] = entry.hash
        logger.debug(f"Cached query: {query[:50]}... (size: {len(self.entries)}/{self.max_entries})")
    
    def get(self, query: str, exact_only: bool = False) -> Optional[Any]:
        """Retrieve from cache by exact match."""
        entry = self.entries.get(hashlib.md5(query.encode()).hexdigest())
        
        if entry and not entry.is_expired():
            entry.touch()
            logger.debug(f"Cache HIT (exact): {query[:50]}...")
            return entry.result
        
        return None
    
    def find_similar(self, query: str, limit: int = 1) -> List[Tuple[str, Any, float]]:
        """Find similar cached queries.
        
        Args:
            query: Query to search for
            limit: Maximum number of results
            
        Returns:
            List of (original_query, result, similarity_score) tuples
        """
        results = []
        search_embedding = SimpleEmbedding.get_embedding(query)
        
        for entry in self.entries.values():
            if entry.is_expired():
                continue
            
            similarity = SimpleEmbedding.cosine_similarity(
                search_embedding,
                entry.embedding
            )
            
            if similarity >= self.similarity_threshold:
                results.append((entry.query, entry.result, similarity))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[2], reverse=True)
        
        if results:
            logger.info(f"Cache SEMANTIC MATCH: {query[:50]}... (similarity: {results[0][2]:.2%})")
        
        return results[:limit]
    
    def get_or_similar(self, query: str) -> Tuple[Optional[Any], Optional[float]]:
        """Get exact match or fall back to semantic search.
        
        Returns:
            Tuple of (result, similarity_score) or (None, None)
        """
        # Try exact match first
        exact = self.get(query)
        if exact is not None:
            return exact, 1.0
        
        # Try semantic search
        similar = self.find_similar(query, limit=1)
        if similar:
            return similar[0][1], similar[0][2]
        
        return None, None
    
    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()
        self.queries_hash.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_accesses = sum(e.access_count for e in self.entries.values())
        avg_age = sum((datetime.now() - e.created_at).seconds for e in self.entries.values()) / max(len(self.entries), 1)
        
        return {
            "cached_queries": len(self.entries),
            "max_capacity": self.max_entries,
            "utilization": f"{len(self.entries) / self.max_entries * 100:.1f}%",
            "total_accesses": total_accesses,
            "avg_query_age_seconds": int(avg_age),
            "similarity_threshold": f"{self.similarity_threshold:.2%}",
        }


# Global semantic cache instance
_semantic_cache: Optional[SemanticCache] = None


def initialize_semantic_cache(max_entries: int = 100, threshold: float = 0.85) -> SemanticCache:
    """Initialize global semantic cache."""
    global _semantic_cache
    _semantic_cache = SemanticCache(max_entries, threshold)
    logger.info(f"Semantic cache initialized (max: {max_entries}, threshold: {threshold:.0%})")
    return _semantic_cache


def get_semantic_cache() -> Optional[SemanticCache]:
    """Get global semantic cache instance."""
    return _semantic_cache
