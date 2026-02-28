"""DeepSeek provider - Fast and cost-effective LLM with advanced reasoning.

DeepSeek specializes in fast inference and economical pricing for models like
DeepSeek-V3, R1, and Chat variants.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(OpenAICompatibleProvider):
    """Provider adapter for DeepSeek API."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize DeepSeek provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="deepseek",
            api_base="https://api.deepseek.com/v1"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "deepseek"

    def get_available_models(self) -> List[str]:
        """Return list of available DeepSeek models."""
        return [
            "deepseek-chat",
            "deepseek-r1",
            "deepseek-v3",
        ]
