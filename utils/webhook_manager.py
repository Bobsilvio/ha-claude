"""Utilities for webhook management."""

import logging
from typing import Any, Dict, Callable

_LOGGER = logging.getLogger(__name__)


class WebhookManager:
    """Manage webhooks for bi-directional communication."""

    def __init__(self):
        """Initialize webhook manager."""
        self.webhooks: Dict[str, Callable] = {}

    def register(self, webhook_id: str, callback: Callable) -> None:
        """Register a webhook handler.
        
        Args:
            webhook_id: Unique ID for the webhook
            callback: Function to call when webhook is triggered
        """
        self.webhooks[webhook_id] = callback
        _LOGGER.info(f"Registered webhook: {webhook_id}")

    def unregister(self, webhook_id: str) -> None:
        """Unregister a webhook handler.
        
        Args:
            webhook_id: ID of the webhook to unregister
        """
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            _LOGGER.info(f"Unregistered webhook: {webhook_id}")

    async def handle(self, webhook_id: str, data: Dict[str, Any]) -> bool:
        """Handle a webhook call.
        
        Args:
            webhook_id: ID of the webhook
            data: Data sent to the webhook
            
        Returns:
            True if handled, False if webhook not found
        """
        if webhook_id not in self.webhooks:
            _LOGGER.warning(f"Webhook not found: {webhook_id}")
            return False

        try:
            callback = self.webhooks[webhook_id]
            if callable(callback):
                await callback(data) if hasattr(callback, '__await__') else callback(data)
                return True
        except Exception as err:
            _LOGGER.error(f"Error handling webhook {webhook_id}: {err}")
            return False

    def list_webhooks(self) -> Dict[str, str]:
        """List all registered webhooks."""
        return {
            webhook_id: str(callback)
            for webhook_id, callback in self.webhooks.items()
        }
