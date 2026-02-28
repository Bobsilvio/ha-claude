"""Zhipu provider - GLM models from Zhipu AI.

Zhipu offers advanced reasoning models (GLM family) with strong performance
on Chinese text understanding and multimodal tasks.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class ZhipuProvider(OpenAICompatibleProvider):
    """Provider adapter for Zhipu GLM models."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize Zhipu/GLM provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="zhipu",
            api_base="https://open.bigmodel.cn/api/paas/v4"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "zhipu"

    def get_available_models(self) -> List[str]:
        """Return list of available Zhipu GLM models."""
        return [
            # Flash (free tier — generous limits)
            "glm-4-flash",
            "glm-4-flash-250414",
            # Air (balanced)
            "glm-4-air",
            "glm-4-airx",
            # Plus / Long context
            "glm-4-plus",
            "glm-4-long",
            # Reasoning models (Z1 series)
            "glm-z1-flash",
            "glm-z1-air",
            "glm-z1-airx",
            # Legacy
            "glm-4",
            "glm-4v",
        ]
