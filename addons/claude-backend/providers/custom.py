"""Custom OpenAI-compatible endpoint provider.

Lets users point the add-on at any OpenAI-compatible API
(LM Studio, vLLM, LocalAI, Together.ai, Perplexity, GLM/z.ai, etc.)
by configuring a base URL and API key in the add-on settings.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class CustomProvider(OpenAICompatibleProvider):
    """Provider adapter for a user-configured OpenAI-compatible endpoint."""

    def __init__(self, api_key: str = "", model: str = "", api_base: str = ""):
        """Initialize custom provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="custom",
            api_base=api_base,
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "custom"

    def get_available_models(self) -> List[str]:
        """No fixed model list — user configures the model name freely."""
        return []
