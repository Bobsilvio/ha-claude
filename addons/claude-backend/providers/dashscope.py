"""DashScope provider - Aliyun's Qwen models API.

DashScope (通义千问) provides access to Aliyun's Qwen family of LLMs
including text, vision, and multimodal variants.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class DashScopeProvider(OpenAICompatibleProvider):
    """Provider adapter for Aliyun DashScope (Qwen models)."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize DashScope provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="dashscope",
            api_base="https://dashscope.aliyuncs.com/api/v1"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "dashscope"

    def get_available_models(self) -> List[str]:
        """Return list of available DashScope/Qwen models."""
        return [
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen-long",
            "qwen-vl-plus",
        ]
