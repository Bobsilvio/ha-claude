"""Moonshot provider - Kimi LLM from Moonshot AI.

Moonshot's Kimi models excel at reasoning and are particularly optimized
for Chinese language understanding and processing.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class MoonshotProvider(OpenAICompatibleProvider):
    """Provider adapter for Moonshot Kimi models."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize Moonshot/Kimi provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="moonshot",
            api_base="https://api.moonshot.cn/v1"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "moonshot"

    def get_available_models(self) -> List[str]:
        """Return list of available Moonshot/Kimi models."""
        return [
            "kimi-k2.5",
            "kimi-k2",
            "kimi-k1.5",
            "kimi-k1",
        ]
