"""SiliconFlow provider - Chinese gateway to open-source models.

SiliconFlow (硅基流动) provides fast, cost-effective access to open-source
models like Qwen, Llama, Mistral via OpenAI-compatible API.
"""

import logging
from typing import List
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class SiliconFlowProvider(OpenAICompatibleProvider):
    """Provider adapter for SiliconFlow gateway."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize SiliconFlow provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="siliconflow",
            api_base="https://api.siliconflow.cn/v1"
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "siliconflow"

    def get_available_models(self) -> List[str]:
        """Return list of available SiliconFlow models."""
        return [
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-32B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            "meta-llama/Llama-3.1-70B-Instruct",
            "mistral/Mistral-7B-Instruct-v0.3",
        ]
