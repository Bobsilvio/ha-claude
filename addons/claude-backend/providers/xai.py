"""xAI provider - Grok models via xAI API."""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class XAIProvider(OpenAICompatibleProvider):
    """Provider adapter for xAI API."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize xAI provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="xai",
            api_base="https://api.x.ai/v1"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "xai"

    def get_available_models(self) -> List[str]:
        """Return common xAI model IDs."""
        return [
            "grok-code-fast-1",
            "grok-4.20-multi-agent-0309",
            "grok-4.20-0309-reasoning",
            "grok-4.20-0309-non-reasoning",
            "grok-4-fast-reasoning",
            "grok-4-fast-non-reasoning",
            "grok-4-1-fast-reasoning",
            "grok-4-1-fast-non-reasoning",
            "grok-4-0709",
            "grok-3-mini",
            "grok-3",
        ]
