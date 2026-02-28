"""Messaging Integration - WhatsApp & Telegram Bot Support.

Nanobot-inspired: Minimal, practical multi-channel messaging support.
- Telegram: Real-time polling or webhook
- WhatsApp: Twilio-based integration
- Unified interface for all channels
"""

import logging
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Chat history storage
CHATS_DB = Path("/config/amira/messaging_chats.json")
CHATS_DB.parent.mkdir(parents=True, exist_ok=True)


class MessagingManager:
    """Unified messaging interface for Telegram and WhatsApp."""

    def __init__(self):
        """Initialize messaging manager."""
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.whatsapp_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.whatsapp_account = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "")
        
        self.telegram_running = False
        self.telegram_offset = 0
        self.chats = self._load_chats()
        
        logger.info(f"MessagingManager initialized. Telegram: {bool(self.telegram_token)}, WhatsApp: {bool(self.whatsapp_token)}")

    def _load_chats(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load chat history from storage."""
        if CHATS_DB.exists():
            try:
                with open(CHATS_DB) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load chats: {e}")
        return {}

    def _save_chats(self) -> None:
        """Save chat history to storage."""
        try:
            with open(CHATS_DB, 'w') as f:
                json.dump(self.chats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save chats: {e}")

    def add_message(self, channel: str, user_id: str, text: str, role: str = "user") -> None:
        """Add message to chat history.
        
        Args:
            channel: 'telegram' or 'whatsapp'
            user_id: User identifier (Telegram ID or WhatsApp number)
            text: Message content
            role: 'user' or 'assistant'
        """
        key = f"{channel}:{user_id}"
        if key not in self.chats:
            self.chats[key] = []
        
        self.chats[key].append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "text": text
        })
        
        # Keep last 50 messages per chat
        self.chats[key] = self.chats[key][-50:]
        self._save_chats()

    def get_chat_history(self, channel: str, user_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent chat history for a user.
        
        Args:
            channel: 'telegram' or 'whatsapp'
            user_id: User identifier
            limit: Max messages to return
            
        Returns:
            List of {role, text} dicts
        """
        key = f"{channel}:{user_id}"
        messages = self.chats.get(key, [])[-limit:]
        return [{"role": m["role"], "text": m["text"]} for m in messages]

    def clear_chat(self, channel: str, user_id: str) -> None:
        """Clear chat history for a user."""
        key = f"{channel}:{user_id}"
        if key in self.chats:
            del self.chats[key]
            self._save_chats()

    def get_stats(self) -> Dict[str, Any]:
        """Get messaging system statistics."""
        total_chats = len(self.chats)
        total_messages = sum(len(msgs) for msgs in self.chats.values())
        
        channels = {"telegram": 0, "whatsapp": 0}
        for key in self.chats:
            channel = key.split(":")[0]
            channels[channel] += 1
        
        return {
            "total_chats": total_chats,
            "total_messages": total_messages,
            "channels": channels,
            "services_enabled": {
                "telegram": bool(self.telegram_token),
                "whatsapp": bool(self.whatsapp_token)
            }
        }

    def get_all_chats(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all chats grouped by channel.
        
        Returns:
            Dict: {'telegram': [...], 'whatsapp': [...]}
        """
        result = {"telegram": [], "whatsapp": []}
        
        for key, messages in self.chats.items():
            channel = key.split(":")[0]
            user_id = key.split(":", 1)[1]
            
            if messages:
                result[channel].append({
                    "user_id": user_id,
                    "channel": channel,
                    "message_count": len(messages),
                    "last_message": messages[-1].get("text", "")[:100],
                    "last_timestamp": messages[-1].get("timestamp", "")
                })
        
        return result

    def get_channel_chats(self, channel: str) -> List[Dict[str, Any]]:
        """Get all chats for a specific channel.
        
        Args:
            channel: 'telegram' or 'whatsapp'
            
        Returns:
            List of chat summaries
        """
        all_chats = self.get_all_chats()
        return all_chats.get(channel, [])


# Global instance
_manager: Optional[MessagingManager] = None


def get_messaging_manager() -> MessagingManager:
    """Get or create global messaging manager."""
    global _manager
    if _manager is None:
        _manager = MessagingManager()
    return _manager
