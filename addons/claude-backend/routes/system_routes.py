"""System routes blueprint.

Endpoints:
- GET /api/system/features
- GET /api/ha_logs
- POST /api/browser-errors
- GET /api/browser-errors
- POST /api/addon/restart
"""

import json
import logging
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__)

# Mutable shared state — imported by reference so mutations are shared
from api import _browser_console_errors


def _get(attr):
    """Helper to read module-level variables from api at call time (avoids circular import issues with immutables)."""
    import api
    return getattr(api, attr)


@system_bp.route('/api/system/features', methods=['GET'])
def api_system_features():
    """Get list of available advanced features."""
    import api as _api
    features = {
        "mcp_support": _api.MCP_AVAILABLE,
        "fallback_chain": _api.FALLBACK_AVAILABLE,
        "semantic_cache": _api.SEMANTIC_CACHE_AVAILABLE,
        "tool_optimizer": _api.TOOL_OPTIMIZER_AVAILABLE,
        "quality_metrics": _api.QUALITY_METRICS_AVAILABLE,
        "prompt_caching": _api.ANTHROPIC_PROMPT_CACHING if _api.ANTHROPIC_PROMPT_CACHING else False,
        "file_memory": _api.MEMORY_AVAILABLE if _api.MEMORY_AVAILABLE else False,
        "image_support": _api.IMAGE_SUPPORT_AVAILABLE,
        "scheduled_tasks": _api.SCHEDULED_TASKS_AVAILABLE,
        "voice_transcription": _api.VOICE_TRANSCRIPTION_AVAILABLE,
        "scheduler_agent": _api.SCHEDULER_AGENT_AVAILABLE,
    }

    # SDK availability for the current provider
    provider_sdk_ok, provider_sdk_msg = _api._check_provider_sdk(_api.AI_PROVIDER)
    pkg_status = _api._check_optional_sdks()
    missing = [k for k, v in pkg_status.items() if not v]

    return jsonify({
        "status": "success",
        "features": features,
        "enabled_count": sum(1 for v in features.values() if v),
        "provider_sdk_available": provider_sdk_ok,
        "provider_sdk_message": provider_sdk_msg,
        "missing_packages": missing,
    }), 200


@system_bp.route('/api/ha_logs')
def api_ha_logs():
    """Proxy GET /api/error_log from Home Assistant — used by the bubble for log context."""
    import api as _api
    level_filter = request.args.get('level', 'warning')
    limit = min(int(request.args.get('limit', 100)), 500)
    keyword = request.args.get('keyword', '').strip().lower()

    try:
        resp = requests.get(
            f"{_api.HA_URL}/api/error_log",
            headers=_api.get_ha_headers(),
            timeout=15
        )
        if not resp.ok:
            return jsonify({"error": f"HA returned {resp.status_code}"}), resp.status_code

        lines = [l for l in (resp.text or "").splitlines() if l.strip()]

        level_map = {
            "error":   ["ERROR", "CRITICAL"],
            "warning": ["ERROR", "CRITICAL", "WARNING"],
            "info":    ["ERROR", "CRITICAL", "WARNING", "INFO"],
            "all":     [],
        }
        allowed = level_map.get(level_filter, [])
        if allowed:
            lines = [l for l in lines if any(lv in l for lv in allowed)]
        if keyword:
            lines = [l for l in lines if keyword in l.lower()]

        lines = lines[-limit:]
        return jsonify({"logs": lines, "total": len(lines)})
    except Exception as e:
        logger.error(f"ha_logs proxy error: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route('/api/browser-errors', methods=['POST'])
def api_browser_errors_post():
    """Receive browser console errors from frontend JS."""
    try:
        # sendBeacon sends text/plain, so try get_json first, then fall back to raw data
        data = request.get_json(silent=True)
        if data is None:
            try:
                raw = request.get_data(as_text=True)
                if raw:
                    data = json.loads(raw)
            except Exception:
                data = {}
        if not isinstance(data, dict):
            data = {}
        errors = data.get("errors", [])
        if not isinstance(errors, list):
            errors = [errors]
        for err in errors:
            if isinstance(err, dict):
                err.setdefault("timestamp", datetime.now().isoformat())
                _browser_console_errors.append(err)
        # Keep only last 200
        while len(_browser_console_errors) > 200:
            _browser_console_errors.pop(0)
        return jsonify({"status": "ok", "stored": len(errors)}), 200
    except Exception as e:
        logger.error(f"Browser errors endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@system_bp.route('/api/browser-errors', methods=['GET'])
def api_browser_errors_get():
    """Get stored browser console errors."""
    return jsonify({"errors": _browser_console_errors, "count": len(_browser_console_errors)}), 200


@system_bp.route('/api/addon/restart', methods=['POST'])
def api_addon_restart():
    """Restart this add-on via the HA Supervisor API."""
    import api as _api
    token = _api.SUPERVISOR_TOKEN
    if not token:
        return jsonify({"success": False, "error": "No Supervisor token available"}), 500
    try:
        import requests as req_lib
        resp = req_lib.post(
            "http://supervisor/addons/self/restart",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": f"Supervisor returned {resp.status_code}"}), 502
    except Exception as e:
        logger.error(f"Addon restart failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
