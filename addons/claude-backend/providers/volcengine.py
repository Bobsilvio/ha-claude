"""VolcEngine provider - Aliyun's enterprise LLM gateway.

VolcEngine (火山引擎) is Aliyun's cloud service for accessing multiple LLM
models with enterprise-grade reliability and support.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class VolcEngineProvider(OpenAICompatibleProvider):
    """Provider adapter for VolcEngine gateway."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize VolcEngine provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="volcengine",
            api_base="https://ark.cn-beijing.volces.com/api/v3"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "volcengine"

    def get_available_models(self) -> List[str]:
        """Return list of available VolcEngine models."""
        return [
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-32B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            "meta-llama/Llama-3.1-70B-Instruct",
        ]
