"""Anthropic provider adapter with enhanced error handling and rate limiting.

Extends EnhancedProvider for automatic retry, caching, and MCP auth support.
"""

import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class AnthropicProvider(EnhancedProvider):
    """Enhanced provider adapter for Anthropic Claude models."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize Anthropic provider with enhanced features."""
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "anthropic"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate Anthropic API key is configured."""
        if not self.api_key:
            return False, "Anthropic API key not configured"
        return True, ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat with automatic retry, caching, and rate limiting.
        
        Features:
        - Automatic retry with exponential backoff
        - Integrated prompt caching from v3.17.11
        - Integrated MCP authentication
        - Per-provider rate limit tracking
        """
        # Initialize rate limiter on first use
        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.name)
        
        # Check rate limit before streaming
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        
        # Record request for rate limiting
        self.rate_limiter.record_request()
        
        # Stream with automatic retry and caching integration
        try:
            yield from self.stream_chat_with_caching(messages, intent_info, max_retries=2)
        except Exception as e:
            logger.error(f"{self.name}: Error during streaming: {e}")
            raise

    @staticmethod
    def _split_system(messages: List[Dict[str, Any]]):
        """Split system messages from conversation messages."""
        system = ""
        conv_msgs = []
        for m in messages:
            if m.get("role") == "system":
                c = m.get("content", "")
                system += (c if isinstance(c, str) else "") + "\n"
            else:
                conv_msgs.append(m)
        return system.strip(), conv_msgs

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Actual Anthropic API call via SDK, with tool calling support."""
        import json as _json
        try:
            import anthropic as _anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed (pip install anthropic)")
        model = (self.model or "claude-3-5-haiku-20241022").replace("anthropic/", "")
        client = _anthropic.Anthropic(api_key=self.api_key)
        system, conv_msgs = self._split_system(messages)

        # Convert OpenAI tool schema format → Anthropic format
        tool_schemas = self._get_intent_tools(intent_info)
        anthropic_tools = [
            {
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "input_schema": t["function"].get("parameters", {"type": "object", "properties": {}}),
            }
            for t in tool_schemas
            if "function" in t
        ]

        kwargs: Dict[str, Any] = {"model": model, "messages": conv_msgs, "max_tokens": 8192}
        if system:
            kwargs["system"] = system
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                if text:
                    yield {"type": "text", "text": text}
            final = stream.get_final_message()

        # Build done event
        done_event: Dict[str, Any] = {
            "type": "done",
            "finish_reason": getattr(final, "stop_reason", None) or "stop",
        }
        if getattr(final, "usage", None):
            done_event["usage"] = {
                "input_tokens": final.usage.input_tokens,
                "output_tokens": final.usage.output_tokens,
            }

        # Surface tool_use blocks as tool_calls for the api.py tool loop
        tool_calls = []
        for block in (getattr(final, "content", None) or []):
            if getattr(block, "type", "") == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": _json.dumps(block.input),
                })
        if tool_calls:
            done_event["tool_calls"] = tool_calls

        yield done_event

    def get_available_models(self) -> List[str]:
        return [
            "claude-opus-4-6",
            "claude-opus-4.6",
            "claude-sonnet-4-6",
            "claude-sonnet-4.6",
            "claude-haiku-4-5",
            "claude-haiku-4.5",
            "claude-opus-4-5",
            "claude-sonnet-4-5",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get Anthropic-specific error translations."""
        return {
            "rate_limit": {
                "en": "Anthropic: Rate limit exceeded. Please retry in a moment.",
                "it": "Anthropic: Limite di velocità superato. Riprova tra poco.",
                "es": "Anthropic: Límite de velocidad excedido. Intenta de nuevo en un momento.",
                "fr": "Anthropic: Limite de vitesse dépassée. Réessayez dans un moment.",
            },
            "auth_error": {
                "en": "Anthropic: API key invalid or missing. Check your Anthropic API key in settings.",
                "it": "Anthropic: Chiave API non valida o mancante. Controlla le impostazioni.",
                "es": "Anthropic: Clave API inválida o faltante. Verifica la configuración.",
                "fr": "Anthropic: Clé API invalide ou manquante. Vérifiez les paramètres.",
            },
            "quota_exceeded": {
                "en": "Anthropic: Monthly API limit reached. Switch provider or wait for reset.",
                "it": "Anthropic: Limite mensile raggiunto. Cambia provider o attendi il reset.",
                "es": "Anthropic: Límite mensual alcanzado. Cambia de provider o espera el reset.",
                "fr": "Anthropic: Limite mensuelle atteinte. Changez de provider ou attendez le reset.",
            },
        }
