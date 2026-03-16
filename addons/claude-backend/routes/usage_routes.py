"""Usage routes blueprint.

Endpoints:
- GET /api/usage_stats
- GET /api/usage_stats/today
- POST /api/usage_stats/reset
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

usage_bp = Blueprint('usage', __name__)


@usage_bp.route("/api/usage_stats", methods=["GET"])
def usage_stats():
    """Return usage statistics (daily, by model, by provider).

    Query params:
        days (int): number of days to include (default 30)
    """
    try:
        from usage_tracker import get_tracker
        days = request.args.get("days", 30, type=int)
        return jsonify(get_tracker().get_summary(days)), 200
    except Exception as e:
        logger.error(f"Usage stats error: {e}")
        return jsonify({"error": str(e)}), 500


@usage_bp.route("/api/usage_stats/today", methods=["GET"])
def usage_stats_today():
    """Return today's usage totals."""
    try:
        from usage_tracker import get_tracker
        return jsonify(get_tracker().get_today()), 200
    except Exception as e:
        logger.error(f"Usage stats today error: {e}")
        return jsonify({"error": str(e)}), 500


@usage_bp.route("/api/usage_stats/reset", methods=["POST"])
def usage_stats_reset():
    """Clear all accumulated usage data."""
    try:
        from usage_tracker import get_tracker
        get_tracker().reset()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Usage stats reset error: {e}")
        return jsonify({"error": str(e)}), 500
