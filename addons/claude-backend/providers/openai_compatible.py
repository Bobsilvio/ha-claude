"""Generic OpenAI-compatible provider for any API gateway.

This provider works with any OpenAI-compatible API:
- OpenRouter (gateway)
- DeepSeek (SDK compatible)
- Mistral (OpenAI-compatible)
- Groq (OpenAI-compatible)
- Any others (custom api_base)
"""

import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(EnhancedProvider):
    """Generic provider for OpenAI-compatible APIs (gateways, aggregators, etc.)."""

    def __init__(self, api_key: str = "", model: str = "", provider_name: str = "generic", api_base: str = ""):
        """Initialize OpenAI-compatible provider.
        
        Args:
            api_key: API key for the provider
            model: Model identifier
            provider_name: Provider identifier (e.g., 'openrouter', 'deepseek')
            api_base: API base URL (if different from default)
        """
        super().__init__(api_key, model)
        self._provider_name = provider_name
        self.api_base = api_base
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return generic provider identifier - override in subclasses."""
        return "openai_compatible"

    def get_provider_name_override(self) -> str:
        """Get the actual provider name (may differ from OpenAI)."""
        return self._provider_name

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate API key is configured."""
        if not self.api_key:
            return False, f"{self._provider_name} API key not configured"
        if self.api_key.strip() == "":
            return False, f"{self._provider_name} API key is empty"
        return True, ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat using OpenAI-compatible API.
        
        Works with any OpenAI-compatible endpoint by setting api_base.
        """
        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.get_provider_name_override())
        
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        
        self.rate_limiter.record_request()
        
        try:
            yield from self.stream_chat_with_caching(messages, intent_info, max_retries=3)
        except Exception as e:
            logger.error(f"{self.get_provider_name_override()}: Error during streaming: {e}")
            raise

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Generic OpenAI-compatible API call via httpx."""
        if not self.api_base:
            raise RuntimeError(f"{self._provider_name}: api_base URL not configured")
        model = self.model or ""
        msgs = self._prepare_messages(messages, intent_info)
        tool_schemas = self._get_intent_tools(intent_info)
        # Generic custom endpoints may not support stream_options
        yield from self._openai_compat_stream(
            self.api_base, self.api_key, model, msgs,
            tools=tool_schemas or None,
            include_usage=False,
        )

    def get_available_models(self) -> List[str]:
        """Return list of available models for this provider."""
        # Return empty list - provider-specific implementations should override
        return []
