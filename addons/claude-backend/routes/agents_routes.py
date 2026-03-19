"""Agents routes blueprint.

Endpoints:
- GET /api/agents
- POST /api/agents
- GET /api/agents/<agent_id>
- PUT /api/agents/<agent_id>
- DELETE /api/agents/<agent_id>
- POST /api/agents/set
- GET /api/agents/channels
- PUT /api/agents/channels
- GET /api/agents/defaults
- PUT /api/agents/defaults
"""

import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

agents_bp = Blueprint('agents', __name__)


@agents_bp.route('/api/agents', methods=['GET'])
def api_agents_list():
    """List all agents with their configuration."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        mgr = _api.agent_config.get_agent_manager()
        include_disabled = request.args.get("include_disabled", "false").lower() == "true"
        agents = mgr.get_agents_for_api() if not include_disabled else [
            a.to_dict() for a in mgr.list_agents(include_disabled=True)
        ]
        active = mgr.get_active_agent()
        return jsonify({
            "success": True,
            "agents": agents,
            "active_agent": active.id if active else None,
            "stats": mgr.stats(),
        }), 200
    except Exception as e:
        logger.error(f"api_agents_list error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents', methods=['POST'])
def api_agents_create():
    """Create a new agent."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        data = request.get_json() or {}
        if not data.get("id"):
            return jsonify({"success": False, "error": "Agent 'id' is required"}), 400
        entry = _api.agent_config.AgentEntry.from_dict(data)
        mgr = _api.agent_config.get_agent_manager()
        mgr.add_agent(entry)
        mgr.save_config()
        return jsonify({"success": True, "agent": entry.to_dict()}), 201
    except Exception as e:
        logger.error(f"api_agents_create error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents/<agent_id>', methods=['GET'])
def api_agent_get(agent_id):
    """Get a single agent by ID."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        mgr = _api.agent_config.get_agent_manager()
        agent = mgr.get_agent(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        return jsonify({"success": True, "agent": agent.to_dict()}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents/<agent_id>', methods=['PUT'])
def api_agent_update(agent_id):
    """Update an existing agent."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        data = request.get_json() or {}
        mgr = _api.agent_config.get_agent_manager()
        updated = mgr.update_agent(agent_id, data)
        if not updated:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        mgr.save_config()
        return jsonify({"success": True, "agent": updated.to_dict()}), 200
    except Exception as e:
        logger.error(f"api_agent_update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents/<agent_id>', methods=['DELETE'])
def api_agent_delete(agent_id):
    """Delete an agent."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        mgr = _api.agent_config.get_agent_manager()
        if not mgr.remove_agent(agent_id):
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        mgr.save_config()
        return jsonify({"success": True, "message": f"Agent '{agent_id}' deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents/set', methods=['POST'])
def api_agent_set_active():
    """Switch the active agent."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        data = request.get_json() or {}
        agent_id = (data.get("agent_id") or "").strip()
        if not agent_id:
            return jsonify({"success": False, "error": "agent_id is required"}), 400
        mgr = _api.agent_config.get_agent_manager()
        if not mgr.set_active_agent(agent_id):
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found or disabled"}), 404

        # Sync agent identity/instructions and (if configured) model/provider.
        _api._sync_active_agent_globals(
            apply_model=True,
            persist_selection=True,
            reinitialize_client=True,
        )

        agent = mgr.resolve_agent(agent_id)
        if agent and agent.model_config.primary:
            ref = agent.model_config.primary
            logger.info(f"Agent '{agent_id}' activated -> model {ref.provider}/{ref.model}")

        identity = mgr.resolve_identity(agent_id)
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "identity": {"name": identity.name, "emoji": identity.emoji},
            "provider": _api.AI_PROVIDER,
            "model": _api.AI_MODEL,
        }), 200
    except Exception as e:
        logger.error(f"api_agent_set_active error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents/channels', methods=['GET'])
def api_agent_channels_get():
    """Get channel -> agent assignments (telegram, whatsapp, alexa...)."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        mgr = _api.agent_config.get_agent_manager()
        mapping = mgr.get_all_channel_agents()
        # Enrich with agent identity for the UI
        enriched = {}
        for ch, aid in mapping.items():
            identity = mgr.resolve_identity(aid)
            enriched[ch] = {
                "agent_id": aid,
                "name": identity.name,
                "emoji": identity.emoji,
            }
        return jsonify({
            "success": True,
            "channel_agents": enriched,
            "available_channels": ["telegram", "whatsapp", "alexa"],
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents/channels', methods=['PUT'])
def api_agent_channels_set():
    """Set channel -> agent assignments.

    Body: {"telegram": "agent_id_or_null", "whatsapp": "agent_id_or_null"}
    Pass null/empty string to remove the assignment for a channel.
    """
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        data = request.get_json() or {}
        mgr = _api.agent_config.get_agent_manager()
        errors = []
        for channel, agent_id in data.items():
            channel = str(channel).strip().lower()
            if not channel:
                continue
            aid = str(agent_id).strip() if agent_id else None
            if not mgr.set_channel_agent(channel, aid or None):
                errors.append(f"Agent '{aid}' not found or disabled for channel '{channel}'")
        mgr.save_config()
        mapping = mgr.get_all_channel_agents()
        resp = {"success": True, "channel_agents": mapping}
        if errors:
            resp["warnings"] = errors
        return jsonify(resp), 200
    except Exception as e:
        logger.error(f"api_agent_channels_set error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents/defaults', methods=['GET'])
def api_agent_defaults_get():
    """Get global agent defaults."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        mgr = _api.agent_config.get_agent_manager()
        return jsonify({"success": True, "defaults": mgr.get_defaults().to_dict()}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/api/agents/defaults', methods=['PUT'])
def api_agent_defaults_update():
    """Update global agent defaults."""
    import api as _api
    if not _api.AGENT_CONFIG_AVAILABLE:
        return jsonify({"success": False, "error": "Agent system not available"}), 501
    try:
        data = request.get_json() or {}
        mgr = _api.agent_config.get_agent_manager()
        updated = mgr.update_defaults(data)
        mgr.save_config()
        return jsonify({"success": True, "defaults": updated.to_dict()}), 200
    except Exception as e:
        logger.error(f"api_agent_defaults_update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
