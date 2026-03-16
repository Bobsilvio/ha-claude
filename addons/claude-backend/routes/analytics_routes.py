"""Analytics routes blueprint.

Endpoints:
- GET /api/cache/semantic/stats
- POST /api/cache/semantic/clear
- GET /api/tools/optimizer/stats
- GET /api/quality/stats
- GET /api/image/stats
- POST /api/image/analyze
"""

import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/cache/semantic/stats', methods=['GET'])
def api_semantic_cache_stats():
    """Get semantic cache statistics."""
    import api as _api
    try:
        if not _api.SEMANTIC_CACHE_AVAILABLE:
            return jsonify({"status": "error", "message": "Semantic cache not available"}), 501

        cache = _api.semantic_cache.get_semantic_cache()
        if not cache:
            return jsonify({"status": "error", "message": "Semantic cache not initialized"}), 503

        stats = cache.stats()
        return jsonify({
            "status": "success",
            "cache_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Semantic cache stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/cache/semantic/clear', methods=['POST'])
def api_semantic_cache_clear():
    """Clear semantic cache."""
    import api as _api
    try:
        if not _api.SEMANTIC_CACHE_AVAILABLE:
            return jsonify({"status": "error", "message": "Semantic cache not available"}), 501

        cache = _api.semantic_cache.get_semantic_cache()
        if not cache:
            return jsonify({"status": "error", "message": "Semantic cache not initialized"}), 503

        cache.clear()
        return jsonify({
            "status": "success",
            "message": "Semantic cache cleared",
        }), 200
    except Exception as e:
        logger.error(f"Semantic cache clear error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/tools/optimizer/stats', methods=['GET'])
def api_tool_optimizer_stats():
    """Get tool execution optimizer statistics."""
    import api as _api
    try:
        if not _api.TOOL_OPTIMIZER_AVAILABLE:
            return jsonify({"status": "error", "message": "Tool optimizer not available"}), 501

        optimizer = _api.tool_optimizer.get_tool_optimizer()
        stats = optimizer.stats()
        return jsonify({
            "status": "success",
            "optimizer_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Tool optimizer stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/quality/stats', methods=['GET'])
def api_quality_metrics_stats():
    """Get response quality metrics statistics."""
    import api as _api
    try:
        if not _api.QUALITY_METRICS_AVAILABLE:
            return jsonify({"status": "error", "message": "Quality metrics not available"}), 501

        analyzer = _api.quality_metrics.get_quality_analyzer()
        stats = analyzer.get_stats()
        return jsonify({
            "status": "success",
            "quality_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Quality metrics stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/image/stats', methods=['GET'])
def api_image_stats():
    """Get image analyzer statistics."""
    import api as _api
    try:
        if not _api.IMAGE_SUPPORT_AVAILABLE:
            return jsonify({"status": "error", "message": "Image support not available"}), 501
        analyzer = _api.image_support.get_image_analyzer()
        return jsonify({"status": "success", "image_stats": analyzer.get_stats()}), 200
    except Exception as e:
        logger.error(f"Image stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/image/analyze', methods=['POST'])
def api_image_analyze():
    """Analyze an image file using vision models with automatic fallback.

    JSON body: { "image_path": "/config/amira/images/photo.jpg", "prompt": "Describe this image" }
    """
    import api as _api
    try:
        if not _api.IMAGE_SUPPORT_AVAILABLE:
            return jsonify({"status": "error", "message": "Image support not available"}), 501
        data = request.json or {}
        image_path = data.get("image_path", "")
        prompt = data.get("prompt", "Describe this image in detail.")
        if not image_path:
            return jsonify({"status": "error", "message": "image_path is required"}), 400
        analyzer = _api.image_support.get_image_analyzer()
        success, analysis, provider = analyzer.analyze_with_fallback(image_path, prompt)
        if success:
            return jsonify({"status": "success", "analysis": analysis, "provider": provider}), 200
        else:
            return jsonify({"status": "error", "message": analysis}), 502
    except Exception as e:
        logger.error(f"Image analyze error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
