"""Document upload and management module for Claude Backend."""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

logger = logging.getLogger(__name__)
STORAGE_DIR = "/config/amira/documents"


def ensure_upload_dir() -> None:
    """Ensure document storage directory exists."""
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)


def process_uploaded_file(
    file_content: bytes,
    filename: str,
    note: str = "",
    tags: Optional[List[str]] = None
) -> str:
    """Process uploaded file and store it.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        note: Optional user note about document
        tags: Optional list of tags for categorization
    
    Returns:
        Document ID
    
    Raises:
        ValueError: If file format not supported
    """
    ensure_upload_dir()
    
    # Detect file type from extension
    _, ext = os.path.splitext(filename.lower())
    ext = ext.lstrip('.')
    
    # Extract text
    success, text = _extract_text_from_file(file_content, ext)
    if not success:
        raise ValueError(f"Could not extract text from {filename}")
    
    # Generate document ID
    doc_id = str(uuid.uuid4())
    
    # Store content
    content_file = os.path.join(STORAGE_DIR, f"{doc_id}.txt")
    with open(content_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    # Save metadata
    index = _load_index()
    index[doc_id] = {
        "id": doc_id,
        "filename": filename,
        "file_type": ext,
        "uploaded_at": datetime.utcnow().isoformat(),
        "size_bytes": len(file_content),
        "content_length": len(text),
        "note": note,
        "tags": tags or []
    }
    _save_index(index)
    
    logger.info(f"Document uploaded: {doc_id} ({filename}, {len(text)} chars)")
    return doc_id


def get_document(doc_id: str) -> Optional[Dict]:
    """Get document metadata and content.
    
    Args:
        doc_id: Document ID
    
    Returns:
        Document info with content, or None if not found
    """
    index = _load_index()
    if doc_id not in index:
        return None
    
    # Load content
    content_file = os.path.join(STORAGE_DIR, f"{doc_id}.txt")
    content = ""
    if os.path.exists(content_file):
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
    
    doc_info = index[doc_id].copy()
    doc_info["content"] = content
    return doc_info


def list_documents(tags: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
    """List all documents, optionally filtered by tags.
    
    Args:
        tags: Filter by tags (all tags must match)
        limit: Max documents to return
    
    Returns:
        List of document metadata (without content)
    """
    index = _load_index()
    docs = list(index.values())
    
    # Filter by tags if provided
    if tags:
        docs = [d for d in docs if all(tag in d.get("tags", []) for tag in tags)]
    
    # Sort by upload time descending
    docs.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return docs[:limit]


def search_documents(query: str, limit: int = 5) -> List[Tuple[Dict, float]]:
    """Search documents by keyword.
    
    Args:
        query: Search query
        limit: Max results
    
    Returns:
        List of (document, relevance_score) tuples
    """
    query_words = set(query.lower().split())
    index = _load_index()
    results = []
    
    for doc_id, doc_info in index.items():
        # Score based on filename, note, tags, and content
        score = 0.0
        text_to_search = (
            (doc_info.get("filename", "") + " ") * 2 +  # Filename weighted 2x
            doc_info.get("note", "") +
            " ".join(doc_info.get("tags", []))
        ).lower()
        
        # Load content for search
        content_file = os.path.join(STORAGE_DIR, f"{doc_id}.txt")
        if os.path.exists(content_file):
            with open(content_file, 'r', encoding='utf-8') as f:
                text_to_search += " " + f.read().lower()
        
        # Count matching words
        for word in query_words:
            score += text_to_search.count(word)
        
        if score > 0:
            doc_info_copy = doc_info.copy()
            results.append((doc_info_copy, score))
    
    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def delete_document(doc_id: str) -> bool:
    """Delete a document.
    
    Args:
        doc_id: Document ID
    
    Returns:
        True if deleted, False if not found
    """
    index = _load_index()
    if doc_id not in index:
        return False
    
    # Remove content file
    content_file = os.path.join(STORAGE_DIR, f"{doc_id}.txt")
    if os.path.exists(content_file):
        os.remove(content_file)
    
    # Remove from index
    del index[doc_id]
    _save_index(index)
    
    logger.info(f"Document deleted: {doc_id}")
    return True


def get_upload_stats() -> Dict:
    """Get document upload statistics.
    
    Returns:
        Statistics dictionary
    """
    index = _load_index()
    total_size = 0
    file_types = {}
    
    for doc_id, doc_info in index.items():
        total_size += doc_info.get("size_bytes", 0)
        file_type = doc_info.get("file_type", "unknown")
        file_types[file_type] = file_types.get(file_type, 0) + 1
    
    return {
        "total_documents": len(index),
        "total_size_bytes": total_size,
        "file_types": file_types,
        "storage_path": STORAGE_DIR
    }


def get_document_context(limit: int = 3, max_content_chars: int = 4000) -> str:
    """Get recent documents as context for chat, including content.
    
    Args:
        limit: Max documents to include
        max_content_chars: Max characters of content per document
    
    Returns:
        Formatted context string with document content, empty if no documents
    """
    docs = list_documents(limit=limit)
    if not docs:
        return ""
    
    context_lines = []
    for doc in docs:
        context_lines.append(
            f"### {doc['filename']} ({doc['file_type'].upper()}, "
            f"{doc['content_length']} chars)"
        )
        if doc.get("note"):
            context_lines.append(f"Note: {doc['note']}")
        
        # Include actual document content
        full_doc = get_document(doc['id'])
        if full_doc and full_doc.get('content'):
            content = full_doc['content']
            if len(content) > max_content_chars:
                content = content[:max_content_chars] + "\n... (truncated)"
            context_lines.append(f"```\n{content}\n```")
        context_lines.append("")
    
    return "\n".join(context_lines)


# ---- Helper Functions ----

def _extract_text_from_file(file_content: bytes, file_type: str) -> Tuple[bool, str]:
    """Extract text from file based on type.
    
    Supports: txt, md, markdown, yaml, yml, pdf, docx, doc
    
    Returns:
        (success, text)
    """
    if file_type in ('txt', 'md', 'markdown', 'yaml', 'yml'):
        return _extract_text_plain(file_content)
    elif file_type == 'pdf':
        return _extract_text_pdf(file_content)
    elif file_type in ('docx', 'doc'):
        return _extract_text_docx(file_content)
    else:
        # Try plain text as fallback
        try:
            text = file_content.decode('utf-8')
            return (True, text)
        except UnicodeDecodeError:
            return (False, "")


def _extract_text_plain(content: bytes) -> Tuple[bool, str]:
    """Extract text from plain text file."""
    try:
        text = content.decode('utf-8')
        return (True, text)
    except UnicodeDecodeError:
        return (False, "")


def _extract_text_pdf(content: bytes) -> Tuple[bool, str]:
    """Extract text from PDF."""
    if not PDF_SUPPORT:
        return (False, "PDF support not available")
    
    try:
        from io import BytesIO
        pdf_file = BytesIO(content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return (True, text)
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return (False, "")


def _extract_text_docx(content: bytes) -> Tuple[bool, str]:
    """Extract text from DOCX."""
    if not DOCX_SUPPORT:
        return (False, "DOCX support not available")
    
    try:
        from io import BytesIO
        docx_file = BytesIO(content)
        doc = Document(docx_file)
        text = "\n".join(para.text for para in doc.paragraphs)
        return (True, text)
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        return (False, "")


def _load_index() -> Dict:
    """Load document index from storage."""
    ensure_upload_dir()
    index_file = os.path.join(STORAGE_DIR, "documents_index.json")
    
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading index: {e}")
    
    return {}


def _save_index(index: Dict) -> None:
    """Save document index to storage."""
    ensure_upload_dir()
    index_file = os.path.join(STORAGE_DIR, "documents_index.json")
    
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving index: {e}")
