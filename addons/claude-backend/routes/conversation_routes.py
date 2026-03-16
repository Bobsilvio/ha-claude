"""Conversation routes blueprint.

Endpoints:
- GET /api/conversations
- GET /api/conversations/<session_id>
- DELETE /api/conversations/<session_id>
- GET /api/snapshots
- POST /api/snapshots/restore
- DELETE /api/snapshots/<snapshot_id>
- GET /api/snapshots/<snapshot_id>/download
- POST /api/conversation/process
"""

import json
import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

logger = logging.getLogger(__name__)

conversation_bp = Blueprint('conversations', __name__)

# Mutable shared state imported by reference
from api import conversations, session_last_intent


@conversation_bp.route('/api/conversation/process', methods=['POST'])
def api_conversation_process():
    """HA Conversation Agent compatible endpoint.

    Expects:
        {"text": "...", "language": "it", "conversation_id": "..."}
    Returns:
        {"response": {"speech": {"plain": {"speech": "...", "extra_data": null}},
                       "card": {}, "language": "it"}, "conversation_id": "..."}
    """
    import api as _api
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    lang = data.get("language", _api.LANGUAGE)
    conv_id = data.get("conversation_id") or "conversation_agent"

    if not text:
        return jsonify({"error": "Empty text"}), 400

    logger.info(f"[ConversationAgent] ({lang}) {text[:80]}")

    try:
        response_text = _api.chat_with_ai(text, conv_id)
    except Exception as e:
        logger.error(f"[ConversationAgent] Error: {e}")
        response_text = f"Mi dispiace, si e' verificato un errore: {str(e)[:100]}"

    # Return in HA conversation agent response format
    return jsonify({
        "response": {
            "speech": {
                "plain": {
                    "speech": response_text,
                    "extra_data": None,
                }
            },
            "card": {},
            "language": lang,
        },
        "conversation_id": conv_id,
    }), 200


@conversation_bp.route('/api/conversations', methods=['GET'])
def api_conversations_list():
    """List all conversation sessions with metadata.
    Optional query param ?source=card|bubble|chat to filter by source."""
    import api as _api
    source_filter = request.args.get("source", "").strip().lower()
    result = []
    for sid, msgs in conversations.items():
        if not msgs:
            continue
        # Exclude messaging sessions — they have their own dedicated UI section
        if sid.startswith(("whatsapp_", "telegram_")):
            continue
        # Extract first user message as title (strip [CONTEXT: ...] blocks)
        title = "Nuova conversazione"
        for msg in msgs:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    clean = _api._strip_context_blocks(content)
                    if clean:
                        title = clean[:50] + ("..." if len(clean) > 50 else "")
                    break
        # Determine source: bubble_, card_ or chat
        source = "bubble" if sid.startswith("bubble_") else ("card" if sid.startswith("card_") else "chat")

        # Extract timestamp for sorting/date grouping
        if source in ("bubble", "card") and "_" in sid:
            # Parse bubble session_id: bubble_<base36_timestamp>_<random>
            try:
                parts = sid.split("_")
                if len(parts) >= 2:
                    timestamp_b36 = parts[1]
                    last_updated = int(timestamp_b36, 36)  # Decode base36 timestamp
                else:
                    last_updated = sid
            except Exception:
                last_updated = sid
        else:
            # For chat: ID is typically a numeric timestamp
            try:
                last_updated = int(sid) if sid.isdigit() else sid
            except Exception:
                last_updated = sid if msgs else 0

        # Apply source filter if requested
        if source_filter and source != source_filter:
            continue
        result.append({
            "id": sid,
            "title": title,
            "message_count": len(msgs),
            "last_updated": last_updated,
            "source": source
        })
    # Sort by last_updated descending
    result.sort(key=lambda x: (x["last_updated"] if isinstance(x["last_updated"], (int, float)) else 0), reverse=True)
    return jsonify({"conversations": result[:_api.MAX_CONVERSATIONS]}), 200


@conversation_bp.route('/api/snapshots', methods=['GET'])
def api_snapshots_list():
    """List all file snapshots (backups) created by Amira."""
    import api as _api
    if not os.path.isdir(_api.SNAPSHOTS_DIR):
        return jsonify({"snapshots": []}), 200

    snapshots = []
    for filename in os.listdir(_api.SNAPSHOTS_DIR):
        if filename.endswith(".meta"):
            continue
        meta_path = os.path.join(_api.SNAPSHOTS_DIR, filename + ".meta")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                # Parse timestamp from snapshot_id: YYYYMMDD_HHMMSS_filename
                ts_str = meta.get("timestamp", "")
                try:
                    ts_dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    formatted_date = ts_dt.strftime("%d/%m/%Y %H:%M:%S")
                    sort_key = ts_dt.timestamp()
                except Exception:
                    formatted_date = ts_str
                    sort_key = 0
                snapshots.append({
                    "id": meta.get("snapshot_id", filename),
                    "original_file": meta.get("original_file", filename),
                    "timestamp": ts_str,
                    "formatted_date": formatted_date,
                    "size": meta.get("size", 0),
                    "sort_key": sort_key
                })
            except Exception as e:
                logger.debug(f"Error reading snapshot meta {filename}: {e}")

    # Sort by timestamp descending (newest first)
    snapshots.sort(key=lambda x: x.get("sort_key", 0), reverse=True)
    # Remove sort_key from output
    for s in snapshots:
        s.pop("sort_key", None)

    return jsonify({"snapshots": snapshots}), 200


@conversation_bp.route('/api/conversations/<session_id>', methods=['GET'])
def api_conversation_get(session_id):
    """Get a specific conversation session."""
    import api as _api
    if session_id in conversations:
        # Filter to only return displayable messages (user/assistant with non-empty string content)
        msgs = conversations.get(session_id, [])
        display_msgs = []
        for m in msgs:
            role = m.get("role", "")
            content = m.get("content", "")
            # For multimodal messages, extract text content
            if isinstance(content, list):
                # Extract text from content blocks (Anthropic format: [{type:text, text:...}])
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block.get("text"), str):
                            text_parts.append(block["text"])
                        # Skip tool_use / tool_result blocks — not user-facing
                content = "\n".join(text_parts) if text_parts else ""

            if role in ("user", "assistant") and isinstance(content, str) and content.strip():
                # Skip internal tool-call artifact messages
                if role == "assistant" and _api._is_tool_call_artifact(content, m):
                    continue
                # Strip [CONTEXT: ...] blocks from user messages for clean display
                if role == "user":
                    content = _api._strip_context_blocks(content)
                    if not content.strip():
                        continue
                msg_data = {"role": role, "content": content}
                # Include model/provider metadata for assistant messages
                if role == "assistant":
                    if m.get("model"):
                        msg_data["model"] = m["model"]
                    if m.get("provider"):
                        msg_data["provider"] = m["provider"]
                display_msgs.append(msg_data)
        return jsonify({"session_id": session_id, "messages": display_msgs}), 200
    return jsonify({"error": "Conversation not found"}), 404


@conversation_bp.route('/api/conversations/<session_id>', methods=['DELETE'])
def api_conversation_delete(session_id):
    """Clear a conversation session."""
    if session_id in conversations:
        del conversations[session_id]
        import api as _api
        _api.save_conversations()
    session_last_intent.pop(session_id, None)
    return jsonify({"status": "ok", "message": f"Session '{session_id}' cleared."}), 200


@conversation_bp.route('/api/snapshots/restore', methods=['POST'])
def api_snapshots_restore():
    """Restore a snapshot created by the add-on (undo).

    The frontend uses this to provide a one-click "Ripristina backup" under write-tool messages.
    """
    import api as _api
    try:
        data = request.get_json(force=True, silent=True) or {}
        snapshot_id = (data.get("snapshot_id") or "").strip()
        if not snapshot_id:
            return jsonify({"error": "snapshot_id is required"}), 400

        raw = _api.tools.execute_tool("restore_snapshot", {"snapshot_id": snapshot_id, "reload": True})
        try:
            result = json.loads(raw) if isinstance(raw, str) else {"status": "success", "result": raw}
        except Exception:
            result = {"error": raw}

        if isinstance(result, dict) and result.get("status") == "success":
            return jsonify(result), 200
        return jsonify(result if isinstance(result, dict) else {"error": str(result)}), 400
    except Exception as e:
        logger.error(f"Snapshot restore error: {e}")
        return jsonify({"error": str(e)}), 500


@conversation_bp.route('/api/snapshots/<snapshot_id>', methods=['DELETE'])
def api_delete_snapshot(snapshot_id):
    """Delete a specific snapshot (backup file + metadata)."""
    import api as _api
    try:
        if not snapshot_id or ".." in snapshot_id or "/" in snapshot_id:
            return jsonify({"error": "Invalid snapshot_id"}), 400

        snap_path = os.path.join(_api.SNAPSHOTS_DIR, snapshot_id)
        meta_path = snap_path + ".meta"
        deleted = False
        if os.path.isfile(snap_path):
            os.remove(snap_path)
            deleted = True
        if os.path.isfile(meta_path):
            os.remove(meta_path)
            deleted = True

        if deleted:
            logger.info(f"Snapshot deleted: {snapshot_id}")
            return jsonify({"status": "success", "message": f"Snapshot '{snapshot_id}' deleted"}), 200
        return jsonify({"error": f"Snapshot '{snapshot_id}' not found"}), 404
    except Exception as e:
        logger.error(f"Snapshot delete error: {e}")
        return jsonify({"error": str(e)}), 500


@conversation_bp.route('/api/snapshots/<snapshot_id>/download', methods=['GET'])
def api_download_snapshot(snapshot_id):
    """Download a backup snapshot file."""
    import api as _api
    try:
        if not snapshot_id or ".." in snapshot_id or "/" in snapshot_id:
            return jsonify({"error": "Invalid snapshot_id"}), 400

        snap_path = os.path.join(_api.SNAPSHOTS_DIR, snapshot_id)
        meta_path = snap_path + ".meta"

        if not os.path.isfile(snap_path):
            return jsonify({"error": f"Snapshot '{snapshot_id}' not found"}), 404

        # Read metadata to get original filename
        original_filename = snapshot_id  # default fallback
        timestamp = ""
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    original_filename = meta.get("original_file", snapshot_id)
                    timestamp = meta.get("timestamp", "")
            except Exception:
                pass

        # Generate download filename: original_name.YYYYMMDD_HHMMSS.ext
        # E.g.: automations.20260220_143022.yaml
        base_name = os.path.basename(original_filename)
        if "." in base_name:
            name_parts = base_name.rsplit(".", 1)
            dl_filename = f"{name_parts[0]}.{timestamp}.{name_parts[1]}"
        else:
            dl_filename = f"{base_name}.{timestamp}"

        logger.info(f"Snapshot download: {snapshot_id} as {dl_filename}")
        return send_file(
            snap_path,
            as_attachment=True,
            download_name=dl_filename,
            mimetype="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Snapshot download error: {e}")
        return jsonify({"error": str(e)}), 500
