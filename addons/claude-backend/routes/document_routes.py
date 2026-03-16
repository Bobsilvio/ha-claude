"""Document routes blueprint.

Endpoints:
- POST /api/documents/upload
- GET /api/documents
- GET /api/documents/<doc_id>
- GET /api/documents/search
- DELETE /api/documents/<doc_id>
- GET /api/documents/stats
- POST /api/rag/index
- GET /api/rag/search
- GET /api/rag/stats
"""

import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

document_bp = Blueprint('documents', __name__)


@document_bp.route("/api/documents/upload", methods=["POST"])
def upload_document():
    """Upload a document (PDF, DOCX, TXT, MD, etc.)."""
    import api as _api
    if not _api.ENABLE_FILE_UPLOAD or not _api.FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    try:
        file_content = file.read()
        note = request.form.get("note", "")
        tags = request.form.getlist("tags")

        doc_id = _api.file_upload.process_uploaded_file(
            file_content,
            file.filename,
            note=note,
            tags=tags
        )

        # Auto-index in RAG if available AND enabled
        rag_indexed = False
        if _api.RAG_AVAILABLE and _api.ENABLE_RAG:
            try:
                doc_info = _api.file_upload.get_document(doc_id)
                if doc_info:
                    rag_indexed = _api.rag.index_document(
                        doc_id,
                        doc_info.get("content", ""),
                        {
                            "filename": doc_info.get("filename"),
                            "uploaded_at": doc_info.get("uploaded_at"),
                            "tags": doc_info.get("tags", []),
                            "note": doc_info.get("note")
                        }
                    )
            except Exception as e:
                logger.error(f"RAG indexing failed (non-fatal): {e}")

        return jsonify({
            "status": "uploaded",
            "doc_id": doc_id,
            "filename": file.filename,
            "indexed_in_rag": rag_indexed
        }), 201

    except Exception as e:
        logger.error(f"File upload error: {e}")
        return jsonify({"error": str(e)}), 500


@document_bp.route("/api/documents", methods=["GET"])
def list_documents():
    """List uploaded documents."""
    import api as _api
    if not _api.ENABLE_FILE_UPLOAD or not _api.FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503

    try:
        tags_filter = request.args.getlist("tags")
        docs = _api.file_upload.list_documents(tags=tags_filter)
        return jsonify({"documents": docs}), 200
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return jsonify({"error": str(e)}), 500


@document_bp.route("/api/documents/<doc_id>", methods=["GET"])
def get_document(doc_id):
    """Get a specific document."""
    import api as _api
    if not _api.ENABLE_FILE_UPLOAD or not _api.FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503

    try:
        doc = _api.file_upload.get_document(doc_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        return jsonify(doc), 200
    except Exception as e:
        logger.error(f"Get document error: {e}")
        return jsonify({"error": str(e)}), 500


@document_bp.route("/api/documents/search", methods=["GET"])
def search_documents():
    """Search documents by query."""
    import api as _api
    if not _api.ENABLE_FILE_UPLOAD or not _api.FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503

    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400

    try:
        results = _api.file_upload.search_documents(query)
        return jsonify({"query": query, "results": results}), 200
    except Exception as e:
        logger.error(f"Search documents error: {e}")
        return jsonify({"error": str(e)}), 500


@document_bp.route("/api/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Delete a document."""
    import api as _api
    if not _api.ENABLE_FILE_UPLOAD or not _api.FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503

    try:
        # Remove from RAG index if available
        if _api.RAG_AVAILABLE:
            _api.rag.delete_indexed_document(doc_id)

        success = _api.file_upload.delete_document(doc_id)
        if not success:
            return jsonify({"error": "Document not found"}), 404
        return jsonify({"status": "deleted", "doc_id": doc_id}), 200
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        return jsonify({"error": str(e)}), 500


@document_bp.route("/api/documents/stats", methods=["GET"])
def document_stats():
    """Get document upload statistics."""
    import api as _api
    if not _api.ENABLE_FILE_UPLOAD or not _api.FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503

    try:
        stats = _api.file_upload.get_upload_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({"error": str(e)}), 500


@document_bp.route("/api/rag/index", methods=["POST"])
def rag_index():
    """Index a document for semantic search."""
    import api as _api
    if not _api.RAG_AVAILABLE:
        return jsonify({"error": "RAG feature not available"}), 503

    data = request.get_json()
    doc_id = data.get("doc_id")
    content = data.get("content", "")
    metadata = data.get("metadata", {})

    if not doc_id or not content:
        return jsonify({"error": "doc_id and content required"}), 400

    try:
        _api.rag.index_document(doc_id, content, metadata)
        return jsonify({
            "status": "indexed",
            "doc_id": doc_id,
        }), 201
    except Exception as e:
        logger.error(f"RAG index error: {e}")
        return jsonify({"error": str(e)}), 500


@document_bp.route("/api/rag/search", methods=["GET"])
def rag_search():
    """Semantic search in indexed documents."""
    import api as _api
    if not _api.RAG_AVAILABLE:
        return jsonify({"error": "RAG feature not available"}), 503

    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400

    try:
        limit = int(request.args.get("limit", "5"))
        threshold = float(request.args.get("threshold", "0.0"))

        results = _api.rag.semantic_search(query, limit=limit, threshold=threshold)
        return jsonify({
            "query": query,
            "results": results
        }), 200
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return jsonify({"error": str(e)}), 500


@document_bp.route("/api/rag/stats", methods=["GET"])
def rag_stats():
    """Get RAG indexing statistics."""
    import api as _api
    if not _api.RAG_AVAILABLE:
        return jsonify({"error": "RAG feature not available"}), 503

    try:
        stats = _api.rag.get_rag_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"RAG stats error: {e}")
        return jsonify({"error": str(e)}), 500
