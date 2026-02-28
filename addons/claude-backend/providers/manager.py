"""Provider manager for orchestrating multi-provider support in chat completions.

This manager handles:
- Provider selection and fallback
- Stream adaptation from provider-specific to standardized format
- Error handling and retry logic
- Provider statistics and monitoring
- Rate-aware provider selection (v3.17.12+)
"""

import os
import logging
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manager for orchestrating LLM provider selection and streaming.
    
    Supports both legacy and enhanced (v3.17.12+) implementations.
    Use stream_chat_enhanced() for intelligent rate-aware fallback.
    """

    def __init__(self):
        """Initialize the provider manager."""
        self.last_error = ""
        self.last_error_time = 0.0
        self.provider_stats = {}  # per-provider statistics
        self._enhanced_manager = None
    
    def _get_enhanced_manager(self):
        """Get or create enhanced manager instance."""
        if self._enhanced_manager is None:
            try:
                from .manager_enhanced import EnhancedProviderManager
                self._enhanced_manager = EnhancedProviderManager()
                logger.info("Using enhanced provider manager (v3.17.12+)")
            except ImportError:
                logger.warning("Enhanced provider manager not available, using legacy fallback")
                self._enhanced_manager = False  # Sentinel for unavailable
        return self._enhanced_manager if self._enhanced_manager is not False else None
    
    def stream_chat_enhanced(
        self,
        provider: str,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
        fallback_providers: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat with enhanced (v3.17.12+) features.
        
        Features:
        - Rate-aware provider selection
        - Intelligent fallback coordination
        - Provider failure tracking with decay
        - Automatic exponential backoff
        
        Falls back to legacy implementation if enhanced manager unavailable.
        """
        enhanced = self._get_enhanced_manager()
        if enhanced:
            logger.debug("Using enhanced provider orchestration")
            yield from enhanced.stream_chat_unified(provider, messages, intent_info, fallback_providers, model=model)
        else:
            logger.debug("Falling back to legacy provider orchestration")
            yield from self.stream_chat_unified(provider, messages, intent_info, fallback_providers, model=model)
    
    def get_provider_dashboard(self) -> Dict[str, Any]:
        """Get provider status dashboard (v3.17.12+ feature).
        
        Returns: {
            "timestamp": float,
            "providers": {
                "provider_name": {
                    "stats": {...},
                    "rate_limit": {...},
                    "success_rate": float,
                    "failure_priority": int
                }
            }
        }
        """
        enhanced = self._get_enhanced_manager()
        if enhanced and hasattr(enhanced, 'get_provider_dashboard'):
            return enhanced.get_provider_dashboard()
        else:
            # Fallback: return basic stats
            return {
                "timestamp": time.time(),
                "providers": self.provider_stats,
                "note": "Legacy stats - use enhanced manager for detailed dashboard"
            }

    def stream_chat_unified(
        self,
        provider: str,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
        fallback_providers: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream a chat completion with automatic fallback on error.
        
        Args:
            provider: Primary provider name ('openai', 'anthropic', 'google', etc.)
            messages: Conversation messages in OpenAI format
            intent_info: Optional intent information for focused responses
            fallback_providers: List of fallback provider names, in order
            model: Optional model override (if None, reads from env)
            
        Yields:
            Standardized event dictionaries
        """
        if not fallback_providers:
            fallback_providers = []

        providers_to_try = [provider] + fallback_providers
        last_exception = None
        last_event = None

        for prov in providers_to_try:
            try:
                logger.info(f"ProviderManager: streaming with {prov}")
                event_count = 0
                content_started = False  # True after first content/text event
                last_error_event = None

                for event in self._stream_with_provider(prov, messages, intent_info, model=model):
                    event_count += 1
                    last_event = event

                    # Track whether content has started
                    if event.get("type") in ("content", "text", "delta"):
                        content_started = True

                    # If this is an error event from the provider:
                    #  - before content → treat as failure, try fallback (don't forward yet)
                    #  - after content  → partial stream, forward immediately
                    if event.get("type") == "error":
                        if content_started:
                            yield event  # already sent text, must show error
                        else:
                            last_error_event = event
                            logger.warning(
                                f"ProviderManager: {prov} returned error before content: "
                                f"{event.get('message', '')}"
                            )
                        self._record_failure(prov, event.get("message", "provider error event"))
                        last_exception = Exception(event.get("message", "provider error event"))
                        break  # stop iterating this provider, try next

                    yield event

                    # If we got a done event, mark success and return
                    if event.get("type") == "done":
                        self._record_success(prov, event_count)
                        return

                else:
                    # for-loop completed without break: stream ended without done
                    if event_count > 0:
                        logger.warning(
                            f"ProviderManager: {prov} stream ended without done event "
                            f"({event_count} events)"
                        )
                        self._record_failure(prov, "stream ended without done")
                        last_exception = Exception("stream ended without done event")

            except Exception as e:
                logger.warning(f"ProviderManager: {prov} failed: {e}")
                self._record_failure(prov, str(e))
                last_exception = e
                # Continue to next provider in fallback chain

        # All providers failed
        error_msg = str(last_exception) if last_exception else "All providers failed"
        logger.error(f"ProviderManager: all {len(providers_to_try)} providers failed: {error_msg}")
        self.last_error = error_msg
        self.last_error_time = time.time()

        # Forward the last provider error event if available, else craft one
        if last_error_event:
            yield last_error_event
        else:
            yield {
                "type": "error",
                "message": f"All providers failed: {error_msg}",
            }

    def _stream_with_provider(
        self,
        provider: str,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream with a specific provider using new provider classes.
        
        Dynamically loads provider class and instantiates with env variables.
        """
        from . import get_provider_class
        
        # Get the provider class
        try:
            provider_class = get_provider_class(provider)
        except ValueError as e:
            raise ValueError(f"Unknown provider: {provider}") from e
        
        # Map provider names to environment variable prefixes
        env_prefix_map = {
            "openai": "OPENAI",
            "nvidia": "NVIDIA",
            "anthropic": "ANTHROPIC",
            "google": "GOOGLE",
            "github": "GITHUB",
            "groq": "GROQ",
            "mistral": "MISTRAL",
            "ollama": "OLLAMA",
            "openrouter": "OPENROUTER",
            "deepseek": "DEEPSEEK",
            "minimax": "MINIMAX",
            "aihubmix": "AIHUBMIX",
            "siliconflow": "SILICONFLOW",
            "volcengine": "VOLCENGINE",
            "dashscope": "DASHSCOPE",
            "moonshot": "MOONSHOT",
            "zhipu": "ZHIPU",
            "perplexity": "PERPLEXITY",
            "github_copilot": "GITHUB_COPILOT",
            "openai_codex": "OPENAI_CODEX",
            "claude_web": "CLAUDE_WEB",
            "chatgpt_web": "CHATGPT_WEB",
        }
        
        env_prefix = env_prefix_map.get(provider, provider.upper())
        
        # Get API key from environment (handle special cases)
        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_API_KEY", "")
        elif provider == "github":
            # config.yaml usa github_token → env var GITHUB_TOKEN
            api_key = os.getenv("GITHUB_TOKEN", "") or os.getenv("GITHUB_API_KEY", "")
        elif provider == "github_copilot":
            api_key = os.getenv("GITHUB_COPILOT_TOKEN", "")
        elif provider == "openai_codex":
            api_key = os.getenv("OPENAI_CODEX_TOKEN", "")
        elif provider in ("claude_web", "chatgpt_web"):
            api_key = ""  # session-based, no API key
        else:
            api_key = os.getenv(f"{env_prefix}_API_KEY", "")
        
        # Model: usa l'override passato esplicitamente, altrimenti legge env
        if not model:
            model = os.getenv(f"{env_prefix}_MODEL", "")
        
        # Instantiate provider with credentials
        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            provider_instance = provider_class(api_key=api_key, model=model, base_url=base_url)
        elif provider == "custom":
            api_base = os.getenv("CUSTOM_API_BASE", "")
            # Model from env var if not passed explicitly
            if not model:
                model = os.getenv("CUSTOM_MODEL_NAME", "")
            provider_instance = provider_class(api_key=api_key, model=model, api_base=api_base)
        else:
            provider_instance = provider_class(api_key=api_key, model=model)
        
        # Stream from the provider
        # Strip internal metadata fields (model, provider, usage) that are stored
        # in conversation history but rejected by most provider APIs as extra inputs.
        _ALLOWED_MSG_KEYS = {"role", "content", "name", "tool_calls", "tool_call_id"}
        clean_messages = [
            {k: v for k, v in m.items() if k in _ALLOWED_MSG_KEYS}
            for m in messages
        ]
        for event in provider_instance.stream_chat(clean_messages, intent_info=intent_info):
            yield event

    def _record_success(self, provider: str, event_count: int):
        """Record a successful provider call."""
        if provider not in self.provider_stats:
            self.provider_stats[provider] = {
                "successes": 0,
                "failures": 0,
                "total_events": 0,
                "last_error": "",
                "last_success": 0.0,
            }
        stats = self.provider_stats[provider]
        stats["successes"] += 1
        stats["total_events"] += event_count
        stats["last_success"] = time.time()
        logger.debug(f"ProviderManager: {provider} success (total: {stats['successes']})")

    def _record_failure(self, provider: str, error: str):
        """Record a failed provider call."""
        if provider not in self.provider_stats:
            self.provider_stats[provider] = {
                "successes": 0,
                "failures": 0,
                "total_events": 0,
                "last_error": "",
                "last_success": 0.0,
            }
        stats = self.provider_stats[provider]
        stats["failures"] += 1
        stats["last_error"] = error
        logger.debug(f"ProviderManager: {provider} failure: {error} (total: {stats['failures']})")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about provider usage."""
        return {
            "last_error": self.last_error,
            "last_error_time": self.last_error_time,
            "provider_stats": self.provider_stats,
            "timestamp": time.time(),
        }


# Global manager instance
_manager: Optional[ProviderManager] = None


def get_manager() -> ProviderManager:
    """Get or create the global provider manager."""
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager


def stream_chat(
    provider: str,
    messages: List[Dict[str, Any]],
    intent_info: Optional[Dict[str, Any]] = None,
    fallback_chain: Optional[List[str]] = None,
    model: Optional[str] = None,
) -> Generator[Dict[str, Any], None, None]:
    """Convenience function: stream chat with automatic fallback.
    
    Usage:
        for event in stream_chat("anthropic", messages, model="claude-opus-4-6"):
            process_event(event)
    """
    manager = get_manager()
    yield from manager.stream_chat_unified(provider, messages, intent_info, fallback_chain, model=model)


def get_manager_stats() -> Dict[str, Any]:
    """Get provider manager statistics."""
    return get_manager().get_stats()
