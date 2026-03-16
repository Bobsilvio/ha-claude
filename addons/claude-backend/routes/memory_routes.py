"""Memory routes blueprint.

Endpoints:
- GET /api/memory
- GET /api/memory/search
- GET /api/memory/stats
- DELETE /api/memory/<conversation_id>
- POST /api/memory/cleanup
- POST /api/memory/clear
"""

import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

memory_bp = Blueprint('memory', __name__)


@memory_bp.route('/api/memory', methods=['GET'])
def api_get_memory():
    """Get recent saved conversations from memory."""
    import api as _api
    if not _api.ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400

    try:
        limit = request.args.get('limit', default=10, type=int)
        days_back = request.args.get('days_back', default=30, type=int)
        provider = request.args.get('provider', default=None, type=str)

        convs = _api.memory.get_past_conversations(limit=limit, days_back=days_back, provider=provider)

        return jsonify({
            "success": True,
            "count": len(convs),
            "conversations": convs
        }), 200
    except Exception as e:
        logger.error(f"Memory retrieval error: {e}")
        return jsonify({"error": str(e)}), 500


@memory_bp.route('/api/memory/search', methods=['GET'])
def api_search_memory():
    """Search past conversations by query."""
    import api as _api
    if not _api.ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400

    query = request.args.get('q', default='', type=str)
    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400

    try:
        limit = request.args.get('limit', default=5, type=int)
        days_back = request.args.get('days_back', default=30, type=int)

        results = _api.memory.search_memory(query, limit=limit, days_back=days_back)
        convs = [{"conversation": conv, "score": score} for conv, score in results]

        return jsonify({
            "success": True,
            "query": query,
            "count": len(convs),
            "results": convs
        }), 200
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        return jsonify({"error": str(e)}), 500


@memory_bp.route('/api/memory/stats', methods=['GET'])
def api_memory_stats():
    """Get statistics about stored memories."""
    import api as _api
    if not _api.ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400

    try:
        stats = _api.memory.get_memory_stats()
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
    except Exception as e:
        logger.error(f"Memory stats error: {e}")
        return jsonify({"error": str(e)}), 500


@memory_bp.route('/api/memory/<conversation_id>', methods=['DELETE'])
def api_delete_memory(conversation_id):
    """Delete a conversation from memory."""
    import api as _api
    if not _api.ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400

    try:
        deleted = _api.memory.delete_conversation(conversation_id)
        if deleted:
            return jsonify({
                "success": True,
                "message": f"Conversation {conversation_id} deleted"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
    except Exception as e:
        logger.error(f"Memory delete error: {e}")
        return jsonify({"error": str(e)}), 500


@memory_bp.route('/api/memory/cleanup', methods=['POST'])
def api_cleanup_memory():
    """Clean up old conversations from memory."""
    import api as _api
    if not _api.ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400

    try:
        body = request.get_json(silent=True) or {}
        days = int(body.get('days', 90))

        deleted_count = _api.memory.clear_old_memories(days=days)
        return jsonify({
            "success": True,
            "deleted": deleted_count,
            "message": f"Deleted {deleted_count} conversations older than {days} days"
        }), 200
    except Exception as e:
        logger.error(f"Memory cleanup error: {e}")
        return jsonify({"error": str(e)}), 500


@memory_bp.route('/api/memory/clear', methods=['POST'])
def api_memory_clear():
    """Clear file memory cache (Layer 2)."""
    import api as _api
    try:
        file_cache = _api.memory.get_config_file_cache()
        old_stats = file_cache.stats()
        file_cache.clear()
        logger.info(f"Memory cache cleared: was {old_stats['cached_files']} files, {old_stats['total_bytes']} bytes")
        return jsonify({
            "status": "success",
            "message": f"Cleared {old_stats['cached_files']} files",
            "freed_bytes": old_stats['total_bytes'],
        }), 200
    except Exception as e:
        logger.error(f"Memory clear error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
