"""MiniMax provider - Advanced Chinese LLM with multimodal support.

MiniMax offers LLM services with strong performance on reasoning and
multimodal tasks, primarily for Asian markets.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class MinimaxProvider(OpenAICompatibleProvider):
    """Provider adapter for MiniMax API."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize MiniMax provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="minimax",
            api_base="https://api.minimax.io/v1"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "minimax"

    def get_available_models(self) -> List[str]:
        """Return list of available MiniMax models."""
        return [
            "MiniMax-M2.1",
            "MiniMax-M2",
            "MiniMax-M3",
        ]
