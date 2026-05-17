"""Messaging routes blueprint.

Endpoints:
- GET /api/messaging/stats
- POST /api/telegram/message
- POST /api/discord/message
- GET /api/messaging/chats
- GET /api/messaging/chat/<channel>/<user_id>
- DELETE /api/messaging/chat/<channel>/<user_id>
- POST /api/whatsapp/webhook
"""

import logging
import os
import re

from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

messaging_bp = Blueprint('messaging', __name__)


def _ai_banner() -> str:
    """Return a short intro line showing the active AI provider and model."""
    import api
    provider = api.AI_PROVIDER
    model = api.get_active_model()
    display = api.MODEL_DISPLAY_MAPPING.get(model, model)
    if display and any(display.startswith(p) for p in ("Claude", "OpenAI", "Google", "GitHub", "NVIDIA", "Groq", "Mistral", "DeepSeek", "Ollama")):
        label = display
    else:
        label = f"{provider.replace('_', ' ').title()} • {display or model}"
    return f"🤖 Amira • {label}"


def _strip_markdown_for_telegram(text: str) -> str:
    """Strip Markdown formatting for plain-text Telegram messages."""
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'```[a-z]*\n?', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    return text.strip()


@messaging_bp.route('/api/messaging/stats', methods=['GET'])
def api_messaging_stats():
    """Get messaging system statistics."""
    try:
        from messaging import get_messaging_manager
        mgr = get_messaging_manager()
        stats = mgr.get_stats()
        return jsonify({
            "status": "success",
            "messaging_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Messaging stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@messaging_bp.route('/api/telegram/message', methods=['POST'])
def api_telegram_message():
    """Process incoming Telegram message and return AI response."""
    import api
    if not api.ENABLE_TELEGRAM:
        return jsonify({"status": "error", "message": "Telegram is disabled"}), 503
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        text = data.get("text", "").strip()
        logger.info(f"Telegram from user {user_id}: {text[:60]}")

        if not text:
            return jsonify({"status": "error", "message": "Empty message"}), 400

        response_text = ""
        try:
            with api._apply_channel_agent("telegram"):
                response_text = api.chat_with_ai(text, f"telegram_{user_id}")
        except Exception as e:
            logger.error(f"Telegram AI response error: {e}")
            response_text = api.tr(
                "telegram_error_prefix",
                "⚠️ Error: {error}",
                error=str(e)[:100],
            )

        response_text = _strip_markdown_for_telegram(response_text)
        response_text = response_text[:4096]

        return jsonify({
            "status": "success",
            "response": response_text
        }), 200
    except Exception as e:
        logger.error(f"Telegram message error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@messaging_bp.route('/api/discord/message', methods=['POST'])
def api_discord_message():
    """Process incoming Discord message and return AI response."""
    import api
    if not api.ENABLE_DISCORD:
        return jsonify({"status": "error", "message": "Discord is disabled"}), 503
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id")
        channel_id = data.get("channel_id")
        text = str(data.get("text", "")).strip()
        logger.info(f"Discord from user {user_id} in channel {channel_id}: {text[:60]}")

        if not text:
            return jsonify({"status": "error", "message": "Empty message"}), 400

        response_text = ""
        try:
            with api._apply_channel_agent("discord"):
                response_text = api.chat_with_ai(text, f"discord_{user_id}")
        except Exception as e:
            logger.error(f"Discord AI response error: {e}")
            response_text = f"⚠️ Error: {str(e)[:120]}"

        response_text = response_text[:2000]
        return jsonify({"status": "success", "response": response_text}), 200
    except Exception as e:
        logger.error(f"Discord message error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@messaging_bp.route('/api/messaging/chats', methods=['GET'])
def api_messaging_chats():
    """Get all messaging chats grouped by channel."""
    try:
        from messaging import get_messaging_manager
        mgr = get_messaging_manager()
        chats = mgr.get_all_chats()
        return jsonify({
            "status": "success",
            "chats": chats
        }), 200
    except Exception as e:
        logger.error(f"Get messaging chats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@messaging_bp.route('/api/messaging/chat/<channel>/<user_id>', methods=['GET'])
def api_messaging_chat_get(channel, user_id):
    """Get chat history for a user."""
    try:
        from messaging import get_messaging_manager
        mgr = get_messaging_manager()
        history = mgr.get_chat_history(channel, user_id, limit=50)
        return jsonify({
            "status": "success",
            "channel": channel,
            "user_id": user_id,
            "messages": history
        }), 200
    except Exception as e:
        logger.error(f"Chat get error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@messaging_bp.route('/api/messaging/chat/<channel>/<user_id>', methods=['DELETE'])
def api_messaging_chat_delete(channel, user_id):
    """Delete chat history for a user."""
    try:
        from messaging import get_messaging_manager
        mgr = get_messaging_manager()
        mgr.clear_chat(channel, user_id)
        return jsonify({
            "status": "success",
            "message": f"Chat {channel}:{user_id} cleared"
        }), 200
    except Exception as e:
        logger.error(f"Chat delete error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@messaging_bp.route('/api/whatsapp/webhook', methods=['POST'])
def api_whatsapp_webhook():
    """Handle incoming WhatsApp messages via Twilio webhook."""
    import api
    if not api.ENABLE_WHATSAPP:
        return jsonify({"status": "error", "message": "WhatsApp is disabled"}), 503
    try:
        from whatsapp_bot import get_whatsapp_bot
        from messaging import get_messaging_manager

        whatsapp = get_whatsapp_bot(
            os.getenv("TWILIO_ACCOUNT_SID", ""),
            os.getenv("TWILIO_AUTH_TOKEN", ""),
            os.getenv("TWILIO_WHATSAPP_FROM", "")
        )

        if not whatsapp or not whatsapp.enabled:
            return jsonify({"status": "error", "message": "WhatsApp not configured"}), 501

        signature = request.headers.get("X-Twilio-Signature", "")
        fwd_proto = request.headers.get("X-Forwarded-Proto", "")
        fwd_host  = request.headers.get("X-Forwarded-Host", "")
        if fwd_proto and fwd_host:
            public_url = (
                f"{fwd_proto}://{fwd_host}"
                f"{request.path}"
                + (f"?{request.query_string.decode()}" if request.query_string else "")
            )
        else:
            public_url = request.url
        try:
            from services.settings_service import _load_settings
            _sandbox = _load_settings().get("twilio_sandbox_mode", False)
        except Exception:
            _sandbox = False
        if not whatsapp.validate_webhook_signature(
            public_url,
            request.form.to_dict(),
            signature,
            skip_if_empty=bool(_sandbox),
        ):
            logger.warning(f"WhatsApp webhook signature invalid (url tried: {public_url!r})")
            return jsonify({"status": "error", "message": "Signature invalid"}), 403

        msg = whatsapp.parse_webhook(request.form.to_dict())
        if not msg or not msg.get("text"):
            return jsonify({"status": "ok"}), 200

        from_number = msg.get("from")
        text = msg.get("text")

        logger.info(f"WhatsApp from {from_number}: {text[:50]}...")

        mgr = get_messaging_manager()
        is_first = len(mgr.get_chat_history("whatsapp", from_number, limit=1)) == 0

        mgr.add_message("whatsapp", from_number, text, role="user")

        response_text = ""
        try:
            with api._apply_channel_agent("whatsapp"):
                response_text = api.chat_with_ai(text, f"whatsapp_{from_number}")
        except Exception as e:
            logger.error(f"WhatsApp AI response error: {e}")
            response_text = f"⚠️ Error: {str(e)[:100]}"

        if is_first:
            response_text = f"{_ai_banner()}\n\n{response_text}"

        response_text = response_text[:1600]

        mgr.add_message("whatsapp", from_number, response_text, role="assistant")
        whatsapp.send_message(from_number, response_text)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
