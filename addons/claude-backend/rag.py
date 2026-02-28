"""RAG (Retrieval Augmented Generation) module with lightweight TF-IDF search.

Uses a lightweight TF-IDF approach that works without heavy dependencies
(no sentence-transformers / PyTorch needed). Falls back to keyword search
if TF-IDF is not available.
"""

import os
import json
import logging
import math
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)
STORAGE_DIR = "/config/amira/rag"

# Global vocabulary built from indexed documents (word -> doc_count)
_idf_vocab: Dict[str, int] = {}
_total_docs: int = 0


def ensure_rag_dir() -> None:
    """Ensure RAG storage directory exists."""
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase, split on non-alphanumeric, remove short tokens."""
    return [w for w in re.findall(r'[a-z0-9àáâãäåèéêëìíîïòóôõöùúûüñç]+', text.lower()) if len(w) > 2]


def _tfidf_vector(tokens: List[str], vocab: Dict[str, int], total_docs: int) -> Dict[str, float]:
    """Compute TF-IDF sparse vector for a list of tokens."""
    tf = Counter(tokens)
    total = len(tokens) or 1
    vec: Dict[str, float] = {}
    for word, count in tf.items():
        tf_val = count / total
        doc_freq = vocab.get(word, 0)
        idf_val = math.log((total_docs + 1) / (doc_freq + 1)) + 1
        vec[word] = tf_val * idf_val
    return vec


def _sparse_cosine(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors (dicts)."""
    if not vec1 or not vec2:
        return 0.0
    common = set(vec1.keys()) & set(vec2.keys())
    dot = sum(vec1[k] * vec2[k] for k in common)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def index_document(
    doc_id: str,
    content: str,
    metadata: Optional[Dict] = None
) -> bool:
    """Index a document for TF-IDF search.

    Args:
        doc_id: Document ID
        content: Full document content
        metadata: Optional metadata dict

    Returns:
        True if successful
    """
    global _idf_vocab, _total_docs
    ensure_rag_dir()

    try:
        chunks = _chunk_text(content, chunk_size=500, overlap=100)
        if not chunks:
            return False

        index = _load_index()

        # Store chunks with their tokens (TF-IDF computed at search time)
        doc_chunks = []
        all_words: set = set()
        for i, chunk in enumerate(chunks):
            tokens = _tokenize(chunk)
            if not tokens:
                continue
            all_words.update(set(tokens))
            doc_chunks.append({
                "chunk_id": f"{doc_id}_chunk_{i}",
                "doc_id": doc_id,
                "text": chunk,
                "tokens": tokens,
                "metadata": metadata or {},
                "chunk_index": i
            })

        if not doc_chunks:
            logger.warning(f"No chunks tokenized for {doc_id}")
            return False

        index[doc_id] = {
            "metadata": metadata or {},
            "chunks": doc_chunks,
            "indexed_at": __import__('datetime').datetime.utcnow().isoformat()
        }
        _save_index(index)

        # Update global IDF vocabulary
        _rebuild_idf(index)

        logger.info(f"Indexed {doc_id}: {len(doc_chunks)} chunks")
        return True

    except Exception as e:
        logger.error(f"Indexing error for {doc_id}: {e}")
        return False


def semantic_search(
    query: str,
    limit: int = 5,
    threshold: float = 0.05
) -> List[Dict]:
    """TF-IDF based search in indexed documents.

    Args:
        query: Search query
        limit: Max results
        threshold: Minimum similarity score (0-1)

    Returns:
        List of dicts with text, similarity, doc_id, chunk_id, metadata
    """
    global _idf_vocab, _total_docs
    try:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        index = _load_index()
        if not index:
            return []

        # Rebuild IDF if needed
        if not _idf_vocab:
            _rebuild_idf(index)

        query_vec = _tfidf_vector(query_tokens, _idf_vocab, _total_docs)
        results = []

        for doc_id, doc_data in index.items():
            for chunk in doc_data.get("chunks", []):
                tokens = chunk.get("tokens", [])
                if not tokens:
                    continue
                chunk_vec = _tfidf_vector(tokens, _idf_vocab, _total_docs)
                similarity = _sparse_cosine(query_vec, chunk_vec)

                if similarity >= threshold:
                    results.append({
                        "text": chunk["text"],
                        "similarity": round(similarity, 4),
                        "doc_id": doc_id,
                        "chunk_id": chunk.get("chunk_id"),
                        "metadata": chunk.get("metadata", {})
                    })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


def get_rag_context(query: str, limit: int = 3) -> str:
    """Get RAG context for a query.

    Args:
        query: User query
        limit: Max passages to include

    Returns:
        Formatted context string
    """
    results = semantic_search(query, limit=limit, threshold=0.05)
    if not results:
        return ""

    context_lines = []
    for i, result in enumerate(results, 1):
        score = result.get("similarity", 0)
        text = result.get("text", "")[:300]
        doc_id = result.get("doc_id", "unknown")
        context_lines.append(
            f"{i}. (relevance: {score:.2f}) {text}...\n   [from {doc_id}]"
        )

    return "\n".join(context_lines)


def delete_indexed_document(doc_id: str) -> bool:
    """Delete a document from RAG index.

    Args:
        doc_id: Document ID

    Returns:
        True if deleted
    """
    global _idf_vocab, _total_docs
    index = _load_index()
    if doc_id in index:
        del index[doc_id]
        _save_index(index)
        _rebuild_idf(index)
        logger.info(f"Deleted {doc_id} from RAG index")
        return True
    return False


def get_rag_stats() -> Dict:
    """Get RAG indexing statistics.

    Returns:
        Statistics dictionary
    """
    index = _load_index()
    total_chunks = sum(len(doc.get("chunks", [])) for doc in index.values())
    total_docs = len(index)

    return {
        "indexed_documents": total_docs,
        "total_chunks": total_chunks,
        "embedding_backend": "tfidf (lightweight)",
        "storage_path": STORAGE_DIR
    }


# ---- Helper Functions ----

def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks."""
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]


def _rebuild_idf(index: Dict) -> None:
    """Rebuild global IDF vocabulary from all indexed documents."""
    global _idf_vocab, _total_docs
    vocab: Dict[str, int] = {}
    total = 0

    for doc_data in index.values():
        for chunk in doc_data.get("chunks", []):
            total += 1
            unique_words = set(chunk.get("tokens", []))
            for word in unique_words:
                vocab[word] = vocab.get(word, 0) + 1

    _idf_vocab = vocab
    _total_docs = total


def _load_index() -> Dict:
    """Load RAG index from storage."""
    ensure_rag_dir()
    index_file = os.path.join(STORAGE_DIR, "rag_index.json")

    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading RAG index: {e}")

    # Migrate from old embeddings.json if it exists
    old_file = os.path.join(STORAGE_DIR, "embeddings.json")
    if os.path.exists(old_file):
        try:
            os.remove(old_file)
            logger.info("Removed old embeddings.json (migrated to TF-IDF)")
        except Exception:
            pass

    return {}


def _save_index(index: Dict) -> None:
    """Save RAG index to storage."""
    ensure_rag_dir()
    index_file = os.path.join(STORAGE_DIR, "rag_index.json")

    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving RAG index: {e}")
