"""Skills routes blueprint.

Endpoints:
- GET  /api/skills              — list installed skills
- GET  /api/skills/store        — list available skills from GitHub registry
- POST /api/skills/install      — install a skill from store
- DELETE /api/skills/<name>     — uninstall a skill
"""

import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

skills_bp = Blueprint("skills", __name__)


@skills_bp.route("/api/skills", methods=["GET"])
def api_skills_list():
    """List all installed skills."""
    try:
        import skills as _skills
        return jsonify({"success": True, "skills": _skills.list_skills()}), 200
    except Exception as e:
        logger.error(f"Skills list error: {e}")
        return jsonify({"error": str(e)}), 500


@skills_bp.route("/api/skills/store", methods=["GET"])
def api_skills_store():
    """Fetch available skills from GitHub registry."""
    try:
        import skills as _skills
        installed = {s["name"] for s in _skills.list_skills()}
        store = _skills.fetch_store_index(installed_names=installed)
        return jsonify({"success": True, "skills": store}), 200
    except Exception as e:
        logger.warning(f"Skills store fetch error: {e}")
        return jsonify({"error": str(e), "skills": []}), 200


@skills_bp.route("/api/skills/install", methods=["POST"])
def api_skills_install():
    """Install a skill from the store."""
    try:
        import skills as _skills
        body = request.get_json(silent=True) or {}
        name = (body.get("name") or "").strip().lower()
        raw_url = (body.get("raw_url") or "").strip()

        if not name:
            return jsonify({"error": "name is required"}), 400
        if not raw_url:
            return jsonify({"error": "raw_url is required"}), 400

        content = _skills.fetch_skill_md(raw_url)
        result = _skills.install_skill(name, content)
        if result.get("success"):
            return jsonify(result), 200
        return jsonify(result), 400
    except Exception as e:
        logger.error(f"Skills install error: {e}")
        return jsonify({"error": str(e)}), 500


@skills_bp.route("/api/skills/<name>", methods=["DELETE"])
def api_skills_delete(name):
    """Uninstall a skill."""
    try:
        import skills as _skills
        deleted = _skills.delete_skill(name)
        if deleted:
            return jsonify({"success": True, "name": name}), 200
        return jsonify({"error": f"Skill '{name}' not found"}), 404
    except Exception as e:
        logger.error(f"Skills delete error: {e}")
        return jsonify({"error": str(e)}), 500
