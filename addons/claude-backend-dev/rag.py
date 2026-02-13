"""RAG (Retrieval Augmented Generation) module with semantic search."""

import os
import json
import logging
import math
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)
STORAGE_DIR = "/config/.storage/claude_rag"

# Try to import embedding models
SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass


def ensure_rag_dir() -> None:
    """Ensure RAG storage directory exists."""
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)


def embed_text(text: str, use_local: bool = True) -> Optional[List[float]]:
    """Generate embedding for text.
    
    Args:
        text: Text to embed
        use_local: Use local model if available, else OpenAI
    
    Returns:
        Embedding vector or None if failed
    """
    if not text or not text.strip():
        return None
    
    if use_local:
        return _embed_local(text)
    else:
        return _embed_online(text)


def index_document(
    doc_id: str,
    content: str,
    metadata: Optional[Dict] = None
) -> bool:
    """Index a document for semantic search.
    
    Args:
        doc_id: Document ID
        content: Full document content
        metadata: Optional metadata dict
    
    Returns:
        True if successful
    """
    ensure_rag_dir()
    
    try:
        # Chunk the document
        chunks = _chunk_text(content, chunk_size=500, overlap=100)
        if not chunks:
            return False
        
        # Embed chunks
        embeddings = _load_embeddings()
        backend = _detect_embedding_backend()
        
        doc_chunks = []
        for i, chunk in enumerate(chunks):
            embedding = embed_text(chunk)
            if embedding:
                chunk_id = f"{doc_id}_chunk_{i}"
                doc_chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "text": chunk,
                    "embedding": embedding,
                    "metadata": metadata or {},
                    "chunk_index": i
                })
        
        if not doc_chunks:
            logger.warning(f"No chunks embedded for {doc_id}")
            return False
        
        # Store chunks
        if doc_id not in embeddings:
            embeddings[doc_id] = {
                "metadata": metadata or {},
                "chunks": [],
                "backend": backend,
                "indexed_at": __import__('datetime').datetime.utcnow().isoformat()
            }
        
        embeddings[doc_id]["chunks"] = doc_chunks
        _save_embeddings(embeddings)
        
        logger.info(f"Indexed {doc_id}: {len(doc_chunks)} chunks")
        return True
        
    except Exception as e:
        logger.error(f"Indexing error for {doc_id}: {e}")
        return False


def semantic_search(
    query: str,
    limit: int = 5,
    threshold: float = 0.0
) -> List[Dict]:
    """Semantic search in indexed documents.
    
    Args:
        query: Search query
        limit: Max results
        threshold: Minimum similarity score (0-1)
    
    Returns:
        List of (text, similarity, metadata) dicts
    """
    try:
        # Embed query
        query_embedding = embed_text(query)
        if not query_embedding:
            return []
        
        # Search all chunks
        embeddings = _load_embeddings()
        results = []
        
        for doc_id, doc_data in embeddings.items():
            for chunk in doc_data.get("chunks", []):
                if not chunk.get("embedding"):
                    continue
                
                # Calculate similarity
                similarity = _cosine_similarity(query_embedding, chunk["embedding"])
                
                if similarity >= threshold:
                    results.append({
                        "text": chunk["text"],
                        "similarity": similarity,
                        "doc_id": doc_id,
                        "chunk_id": chunk.get("chunk_id"),
                        "metadata": chunk.get("metadata", {})
                    })
        
        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
        
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return []


def get_rag_context(query: str, limit: int = 3) -> str:
    """Get RAG context for a query.
    
    Args:
        query: User query
        limit: Max passages to include
    
    Returns:
        Formatted context string
    """
    results = semantic_search(query, limit=limit, threshold=0.0)
    if not results:
        return ""
    
    context_lines = []
    for i, result in enumerate(results, 1):
        score = result.get("similarity", 0)
        text = result.get("text", "")[:200]  # Truncate to 200 chars
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
    embeddings = _load_embeddings()
    if doc_id in embeddings:
        del embeddings[doc_id]
        _save_embeddings(embeddings)
        logger.info(f"Deleted {doc_id} from RAG index")
        return True
    return False


def get_rag_stats() -> Dict:
    """Get RAG indexing statistics.
    
    Returns:
        Statistics dictionary
    """
    embeddings = _load_embeddings()
    total_chunks = sum(len(doc.get("chunks", [])) for doc in embeddings.values())
    total_docs = len(embeddings)
    backend = _detect_embedding_backend()
    
    return {
        "indexed_documents": total_docs,
        "total_chunks": total_chunks,
        "embedding_backend": backend,
        "storage_path": STORAGE_DIR
    }


# ---- Helper Functions ----

def _embed_local(text: str) -> Optional[List[float]]:
    """Embed using local sentence-transformers model."""
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Local embedding error: {e}")
        return None


def _embed_online(text: str) -> Optional[List[float]]:
    """Embed using OpenAI API."""
    try:
        import os
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Online embedding error: {e}")
        return None


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Chunk size in characters
        overlap: Overlap between chunks
    
    Returns:
        List of chunks
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return [c for c in chunks if c]  # Remove empty chunks


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        vec1: Vector 1
        vec2: Vector 2
    
    Returns:
        Similarity score (0-1)
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def _detect_embedding_backend() -> str:
    """Detect which embedding backend is available."""
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        return "local (sentence-transformers)"
    else:
        return "online (OpenAI)"


def _load_embeddings() -> Dict:
    """Load embeddings from storage."""
    ensure_rag_dir()
    embeddings_file = os.path.join(STORAGE_DIR, "embeddings.json")
    
    if os.path.exists(embeddings_file):
        try:
            with open(embeddings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
    
    return {}


def _save_embeddings(index: Dict) -> None:
    """Save embeddings to storage."""
    ensure_rag_dir()
    embeddings_file = os.path.join(STORAGE_DIR, "embeddings.json")
    
    try:
        with open(embeddings_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving embeddings: {e}")
