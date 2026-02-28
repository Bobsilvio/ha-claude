"""OpenRouter provider - Gateway to 100+ LLM models.

OpenRouter provides a unified API to access models from all major providers
(Claude, GPT, Llama, Mistral, PaLM, etc.) through a single interface.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(OpenAICompatibleProvider):
    """Provider adapter for OpenRouter gateway."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize OpenRouter provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="openrouter",
            api_base="https://openrouter.ai/api/v1"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "openrouter"

    def get_available_models(self) -> List[str]:
        """Return list of available OpenRouter models (sample)."""
        return [
            "anthropic/claude-opus-4-6",
            "anthropic/claude-sonnet-4-6",
            "openai/gpt-4o",
            "openai/gpt-5",
            "meta-llama/llama-3.1-405b",
            "mistralai/mistral-large",
        ]
