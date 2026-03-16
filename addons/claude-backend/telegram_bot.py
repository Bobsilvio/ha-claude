"""Telegram Bot Integration.

Uses polling to receive messages and send responses.
Integrates with Home Assistant Amira assistant.
"""

import logging
import requests
import json
from typing import Optional, Dict, Any
from threading import Thread
import time

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramBot:
    """Telegram bot handler."""

    def __init__(self, token: str, api_base_url: str = "http://localhost:5010"):
        """Initialize Telegram bot.
        
        Args:
            token: Telegram bot token from @BotFather
            api_base_url: Base URL of ha-claude API
        """
        self.token = token
        self.api_base = api_base_url
        self.running = False
        self.offset = 0
        self.poll_thread: Optional[Thread] = None

    def send_message(self, chat_id: int, text: str) -> bool:
        """Send message to Telegram user, falling back to plain text if parse fails."""
        if not text or not text.strip():
            logger.warning(f"Telegram: attempted to send empty message to {chat_id}")
            return False
        try:
            url = TELEGRAM_API.format(token=self.token, method="sendMessage")
            # First attempt: plain text (always safe — avoids parse_mode entity errors)
            data = {
                "chat_id": chat_id,
                "text": text[:4096],
            }
            resp = requests.post(url, json=data, timeout=10)
            result = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            if result.get("ok"):
                return True
            logger.error(f"Telegram sendMessage failed: {result.get('description', resp.text[:200])}")
            return False
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False

    def get_updates(self, timeout: int = 30) -> Dict[str, Any]:
        """Poll for new messages using long polling.

        Args:
            timeout: Long poll timeout in seconds

        Returns:
            Telegram API response dict
        """
        try:
            url = TELEGRAM_API.format(token=self.token, method="getUpdates")
            params = {
                "offset": self.offset,
                "timeout": timeout,
                "allowed_updates": ["message"]
            }
            resp = requests.get(url, params=params, timeout=timeout + 5)
            if resp.status_code == 200:
                return resp.json()
            # Include HTTP status and body in the error description
            try:
                body = resp.json()
                description = body.get("description", resp.text[:200])
            except Exception:
                description = resp.text[:200] or f"HTTP {resp.status_code}"
            return {"ok": False, "description": f"HTTP {resp.status_code}: {description}"}
        except Exception as e:
            return {"ok": False, "description": str(e)}

    def _poll_messages(self) -> None:
        """Poll loop for messages with exponential backoff on errors."""
        logger.info("Telegram bot polling started")
        _backoff = 5       # seconds, doubles on repeated failures (max 300)
        _fail_count = 0

        while self.running:
            try:
                result = self.get_updates(timeout=30)
                if not result.get("ok"):
                    err = result.get("description", "unknown error")
                    _fail_count += 1
                    # Log first failure at WARNING, then only every 12 attempts (~1 min) to avoid spam
                    if _fail_count == 1 or _fail_count % 12 == 0:
                        logger.warning(f"Telegram getUpdates not OK (attempt {_fail_count}): {err}")
                    wait = min(_backoff * (2 ** min(_fail_count - 1, 5)), 300)
                    time.sleep(wait)
                    continue

                # Success — reset backoff
                _fail_count = 0
                _backoff = 5

                updates = result.get("result", [])
                for update in updates:
                    self.offset = update.get("update_id", self.offset) + 1
                    self._handle_update(update)

            except Exception as e:
                _fail_count += 1
                if _fail_count == 1 or _fail_count % 12 == 0:
                    logger.error(f"Telegram polling error (attempt {_fail_count}): {e}")
                time.sleep(min(5 * (2 ** min(_fail_count - 1, 5)), 300))

        logger.info("Telegram bot polling stopped")

    def _handle_update(self, update: Dict[str, Any]) -> None:
        """Handle incoming message update."""
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        text = message.get("text", "").strip()

        if not text or not chat_id:
            return

        # --- Whitelist check ---
        try:
            import api as _api
            allowed = _api.TELEGRAM_ALLOWED_IDS
        except Exception:
            allowed = set()

        if allowed and user_id not in allowed:
            logger.warning(
                f"Telegram: BLOCKED message from unauthorized user_id={user_id} "
                f"(chat_id={chat_id}). Add to telegram_allowed_ids to grant access."
            )
            _UNAUTHORIZED_MSG = {
                "it": "⛔ Non sei autorizzato a usare questo bot.",
                "es": "⛔ No estás autorizado a usar este bot.",
                "fr": "⛔ Vous n'êtes pas autorisé à utiliser ce bot.",
                "en": "⛔ You are not authorized to use this bot.",
            }
            try:
                lang = (_api.LANGUAGE or "en")[:2].lower()
            except Exception:
                lang = "en"
            self.send_message(chat_id, _UNAUTHORIZED_MSG.get(lang, _UNAUTHORIZED_MSG["en"]))
            return
        # -----------------------

        logger.info(f"Telegram: incoming message from user {user_id} in chat {chat_id}: {text[:80]}")
        
        # Import here to avoid circular dependency
        from messaging import get_messaging_manager
        mgr = get_messaging_manager()
        
        # Add to chat history
        mgr.add_message("telegram", str(user_id), text, role="user")
        
        # Get chat history for context
        history = mgr.get_chat_history("telegram", str(user_id), limit=5)
        
        # Send to API for processing
        try:
            api_url = f"{self.api_base}/api/telegram/message"
            logger.info(f"Telegram: calling {api_url}")
            payload = {
                "user_id": user_id,
                "chat_id": chat_id,
                "text": text,
                "history": history
            }
            resp = requests.post(api_url, json=payload, timeout=60)
            logger.info(f"Telegram: API response status {resp.status_code}")
            
            if resp.status_code == 200:
                response_data = resp.json()
                response_text = response_data.get("response", "I couldn't process that.").strip()
                if not response_text:
                    response_text = "(nessuna risposta)"
                mgr.add_message("telegram", str(user_id), response_text, role="assistant")
                sent = self.send_message(chat_id, response_text)
                if sent:
                    logger.info(f"Telegram: reply sent to chat {chat_id}")
                else:
                    logger.error(f"Telegram: failed to deliver reply to chat {chat_id}")
            else:
                logger.error(f"Telegram: API error {resp.status_code}: {resp.text[:200]}")
                self.send_message(chat_id, "⚠️ API error, please try again")
                
        except Exception as e:
            logger.error(f"Telegram message processing error: {e}")
            self.send_message(chat_id, "❌ Error processing message")

    def start(self) -> None:
        """Start bot polling in background thread."""
        if self.running:
            logger.warning("Telegram bot already running")
            return
        
        self.running = True
        self.poll_thread = Thread(target=self._poll_messages, daemon=True)
        self.poll_thread.start()
        logger.info("Telegram bot started")

    def stop(self) -> None:
        """Stop bot polling."""
        self.running = False
        if self.poll_thread:
            self.poll_thread.join(timeout=5)
        logger.info("Telegram bot stopped")


# Global instance
_bot: Optional[TelegramBot] = None


def get_telegram_bot(token: str, api_base: str = "http://localhost:5010") -> Optional[TelegramBot]:
    """Get or create Telegram bot instance."""
    global _bot
    if token and not _bot:
        _bot = TelegramBot(token, api_base)
    return _bot
