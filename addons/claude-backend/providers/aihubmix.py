"""AiHubMix provider - Universal API gateway for all major LLM providers.

AiHubMix aggregates access to models from OpenAI, Anthropic, Gemini, etc.
through a single unified OpenAI-compatible interface.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class AiHubMixProvider(OpenAICompatibleProvider):
    """Provider adapter for AiHubMix gateway."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize AiHubMix provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="aihubmix",
            api_base="https://aihubmix.com/v1"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "aihubmix"

    def get_available_models(self) -> List[str]:
        """Return list of available AiHubMix models (sample)."""
        return [
            "gpt-4o",
            "gpt-4-turbo",
            "claude-opus-4-6",
            "claude-sonnet",
            "gemini-2.0-flash",
        ]
