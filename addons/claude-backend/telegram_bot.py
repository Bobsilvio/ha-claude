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
            return {"ok": False}
        except Exception as e:
            logger.error(f"Telegram getUpdates error: {e}")
            return {"ok": False}

    def _poll_messages(self) -> None:
        """Poll loop for messages."""
        logger.info("Telegram bot polling started")
        
        while self.running:
            try:
                result = self.get_updates(timeout=30)
                if not result.get("ok"):
                    err = result.get("description", "unknown error")
                    logger.warning(f"Telegram getUpdates not OK: {err}")
                    time.sleep(5)
                    continue
                
                updates = result.get("result", [])
                for update in updates:
                    self.offset = update.get("update_id", self.offset) + 1
                    self._handle_update(update)
                    
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                time.sleep(5)
        
        logger.info("Telegram bot polling stopped")

    def _handle_update(self, update: Dict[str, Any]) -> None:
        """Handle incoming message update."""
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        text = message.get("text", "").strip()
        
        if not text or not chat_id:
            return
        
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
