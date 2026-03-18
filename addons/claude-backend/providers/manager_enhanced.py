"""Enhanced Provider Manager with Rate Limiting & Intelligent Fallback

Improvements over base ProviderManager:
- Integrates GlobalRateLimitCoordinator for smart provider selection
- Tracks rate limits for each provider
- Prioritizes non-rate-limited providers for fallback
- Exponential backoff on provider failures
"""

import os
import logging
import time
from typing import Any, Dict, Generator, List, Optional

from .rate_limiter import get_rate_limit_coordinator, RateLimitInfo
from .error_handler import ErrorTranslator, ErrorType

logger = logging.getLogger(__name__)


class EnhancedProviderManager:
    """Provider manager with integrated rate limiting and intelligent fallback."""

    def __init__(self, default_fallback=None):
        """Initialize enhanced manager.
        
        Args:
            default_fallback: Default fallback chain if not specified
                Example: ["anthropic", "google", "groq"]
        """
        self.last_error = ""
        self.last_error_time = 0.0
        self.provider_stats = {}
        self.default_fallback = default_fallback or []
        self.coordinator = get_rate_limit_coordinator()
        self.translator = ErrorTranslator()
        
        # Failure decay strategy: decrease failure count over time
        self.provider_failure_count = {}
        self.provider_failure_reset = {}  # timestamp when to reset count

    def stream_chat_unified(
        self,
        provider: str,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
        fallback_providers: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream with rate-aware fallback.
        
        Args:
            provider: Primary provider
            messages: Chat messages
            intent_info: Intent context
            fallback_providers: Ordered fallback list
            model: Optional model override (only used for the primary provider)
            
        Yields:
            Standardized event dicts
        """
        if not fallback_providers:
            fallback_providers = self.default_fallback

        # Organize providers with rate limiting in mind
        providers_to_try = self._order_providers_by_availability(
            [provider] + fallback_providers
        )
        
        last_exception = None
        last_event = None
        last_error_event = None

        _primary = providers_to_try[0] if providers_to_try else provider
        for prov in providers_to_try:
            try:
                logger.info(
                    f"EnhancedProviderManager: attempting {prov} "
                    f"(priority={self._get_failure_priority(prov)})"
                )

                # Check rate limit before attempting
                limiter = self.coordinator.get_limiter(prov)
                can_request, wait_time = limiter.can_request()

                if not can_request:
                    logger.warning(
                        f"EnhancedProviderManager: {prov} rate limited, "
                        f"skipping (wait {wait_time:.1f}s)"
                    )
                    self._record_rate_limited(prov)
                    last_exception = Exception(f"Rate limited (wait {wait_time:.1f}s)")
                    continue

                event_count = 0
                content_started = False
                _fallback_notice_sent = False

                for event in self._stream_with_provider(
                    prov, messages, intent_info,
                    model=model if prov == provider else None,
                ):
                    event_count += 1
                    last_event = event

                    # Track content start
                    if event.get("type") in ("content", "text", "delta"):
                        content_started = True

                    # Update rate limits from response headers if present
                    if event.get("type") == "response":
                        response_data = event.get("data", {})
                        headers = response_data.get("headers", {})
                        if headers:
                            self._update_rate_limits(prov, headers)

                    # Error event: forward only if content already started, else try fallback
                    if event.get("type") == "error":
                        if content_started:
                            yield event
                        else:
                            last_error_event = event
                            logger.warning(
                                f"EnhancedProviderManager: {prov} returned error before content: "
                                f"{event.get('message', '')}"
                            )
                        self._record_failure(prov, event.get("message", "provider error event"))
                        last_exception = Exception(event.get("message", "provider error event"))
                        break

                    # Emit fallback notice once, before the first content event
                    if prov != _primary and not _fallback_notice_sent:
                        _fallback_notice_sent = True
                        yield {
                            "type": "fallback_notice",
                            "original_provider": _primary,
                            "actual_provider": prov,
                        }

                    yield event

                    # Done with success
                    if event.get("type") == "done":
                        # Guardrail: provider ended without emitting any meaningful content.
                        # Treat as incomplete so we can try fallback provider (or return
                        # explicit error if this was the last one).
                        if not content_started:
                            logger.warning(
                                f"EnhancedProviderManager: {prov} done without content "
                                f"({event_count} events) — treating as empty response"
                            )
                            self._record_failure(prov, "empty_response")
                            last_exception = Exception("Empty response from provider")
                            break
                        self._record_success(prov, event_count)
                        self._clear_failure_count(prov)  # Reset failure tracking
                        return

                else:
                    # for-loop completed without break: stream ended without done
                    if event_count > 0:
                        logger.warning(
                            f"EnhancedProviderManager: {prov} incomplete "
                            f"({event_count} events, no done)"
                        )
                        self._record_failure(prov, "incomplete_stream")
                        last_exception = Exception("Incomplete stream")

            except Exception as e:
                error_msg = str(e)
                error_type = self.translator.classify_error(error_msg, provider=prov)
                is_retryable = self.translator.is_retryable(error_msg)
                
                logger.warning(
                    f"EnhancedProviderManager: {prov} failed "
                    f"({error_type}, retryable={is_retryable}): {error_msg}"
                )
                
                self._record_failure(prov, error_msg)
                if error_type == ErrorType.RATE_LIMIT:
                    self._record_rate_limited(prov)
                
                last_exception = e
                # Continue to next provider

        # All providers exhausted
        error_msg = str(last_exception) if last_exception else "All providers unavailable"
        logger.error(
            f"EnhancedProviderManager: exhausted {len(providers_to_try)} providers: "
            f"{error_msg}"
        )
        self.last_error = error_msg
        self.last_error_time = time.time()

        if last_error_event:
            yield last_error_event
        else:
            language = os.getenv("LANGUAGE", "en").lower()
            failed_prov = providers_to_try[-1] if providers_to_try else "generic"
            yield {
                "type": "error",
                "message": ErrorTranslator.translate_error(
                    error_msg, provider=failed_prov, language=language
                ),
            }

    def _order_providers_by_availability(self, providers: List[str]) -> List[str]:
        """Order providers by rate limit availability and failure history.
        
        Returns:
            Providers ordered from best to worst availability
        """
        scored = []
        
        for prov in providers:
            limiter = self.coordinator.get_limiter(prov)
            
            # Score components (lower is better)
            # 1. Rate limit pressure (0 = available, 100 = critical)
            rate_score = 0
            if limiter.rate_limit_info.requests_remaining is not None:
                remaining = limiter.rate_limit_info.requests_remaining
                if remaining <= limiter.rate_limit_info.critical_threshold:
                    rate_score = 100
                elif remaining <= limiter.rate_limit_info.low_threshold:
                    rate_score = 60
                else:
                    rate_score = (100 - remaining)  # More requests = better
            
            # 2. Failure history (penalize repeated failures)
            failure_priority = self._get_failure_priority(prov)
            
            # 3. Is currently limited
            is_limited = limiter.rate_limit_info.is_limited
            limited_score = 50 if is_limited else 0
            
            total_score = rate_score + failure_priority + limited_score
            scored.append((prov, total_score))
        
        # Sort by score (ascending) and prefer primary provider on ties
        scored.sort(key=lambda x: (x[1], providers.index(x[0])))
        result = [prov for prov, score in scored]
        
        logger.debug(
            f"Provider ordering: {' > '.join(result)} "
            f"(scores: {dict((p, s) for p, s in scored)})"
        )
        return result

    def _get_failure_priority(self, provider: str) -> int:
        """Get failure priority score for a provider (0-100).
        
        0 = no failures, 100 = many recent failures
        """
        now = time.time()
        
        # Check if failure count should be reset
        if provider in self.provider_failure_reset:
            if now > self.provider_failure_reset[provider]:
                self.provider_failure_count[provider] = 0
                del self.provider_failure_reset[provider]
        
        failure_count = self.provider_failure_count.get(provider, 0)
        
        # Map failure count to priority
        if failure_count == 0:
            return 0
        elif failure_count == 1:
            return 10
        elif failure_count == 2:
            return 30
        else:
            return 100  # Max out at 100

    def _clear_failure_count(self, provider: str):
        """Clear failure count after successful request."""
        self.provider_failure_count[provider] = 0
        if provider in self.provider_failure_reset:
            del self.provider_failure_reset[provider]

    def _record_rate_limited(self, provider: str):
        """Record rate limit event."""
        limiter = self.coordinator.get_limiter(provider)
        status = limiter.get_status()
        
        logger.warning(
            f"EnhancedProviderManager: {provider} rate limited "
            f"({status['requests_remaining']}/{status['max_rpm']} requests)"
        )

    def _update_rate_limits(self, provider: str, headers: Dict[str, Any]):
        """Update rate limit info from response headers."""
        limiter = self.coordinator.get_limiter(provider)
        
        limiter.update_from_headers(
            requests_remaining=headers.get("X-RateLimit-Remaining"),
            reset_unix=headers.get("X-RateLimit-Reset"),
            retry_after=headers.get("Retry-After")
        )

    def _stream_with_provider(
        self,
        provider: str,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream with a specific provider using class-based provider loading.

        Uses the same dynamic provider instantiation as ProviderManager
        (reads API key from env, loads provider class from __init__.py registry).
        Also records each request in the rate limiter.
        """
        from . import get_provider_class

        provider_class = get_provider_class(provider)

        # --- resolve API key from env ---
        env_prefix_map = {
            "openai": "OPENAI", "nvidia": "NVIDIA", "anthropic": "ANTHROPIC",
            "google": "GOOGLE", "github": "GITHUB", "groq": "GROQ",
            "mistral": "MISTRAL", "ollama": "OLLAMA", "openrouter": "OPENROUTER",
            "deepseek": "DEEPSEEK", "minimax": "MINIMAX", "aihubmix": "AIHUBMIX",
            "siliconflow": "SILICONFLOW", "volcengine": "VOLCENGINE",
            "dashscope": "DASHSCOPE", "moonshot": "MOONSHOT", "zhipu": "ZHIPU",
            "perplexity": "PERPLEXITY", "github_copilot": "GITHUB_COPILOT",
            "openai_codex": "OPENAI_CODEX", "claude_web": "CLAUDE_WEB",
            "chatgpt_web": "CHATGPT_WEB",
        }
        env_prefix = env_prefix_map.get(provider, provider.upper())

        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_API_KEY", "")
        elif provider == "github":
            api_key = os.getenv("GITHUB_TOKEN", "") or os.getenv("GITHUB_API_KEY", "")
        elif provider == "github_copilot":
            api_key = os.getenv("GITHUB_COPILOT_TOKEN", "")
        elif provider == "openai_codex":
            api_key = os.getenv("OPENAI_CODEX_TOKEN", "")
        elif provider in ("claude_web", "chatgpt_web"):
            api_key = ""
        else:
            api_key = os.getenv(f"{env_prefix}_API_KEY", "")

        if not model:
            model = os.getenv(f"{env_prefix}_MODEL", "")

        # --- instantiate ---
        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            provider_instance = provider_class(api_key=api_key, model=model, base_url=base_url)
        elif provider == "custom":
            api_base = os.getenv("CUSTOM_API_BASE", "")
            if not model:
                model = os.getenv("CUSTOM_MODEL_NAME", "")
            provider_instance = provider_class(api_key=api_key, model=model, api_base=api_base)
        else:
            provider_instance = provider_class(api_key=api_key, model=model)

        # --- strip internal metadata from messages ---
        _ALLOWED_MSG_KEYS = {"role", "content", "name", "tool_calls", "tool_call_id"}
        clean_messages = [
            {k: v for k, v in m.items() if k in _ALLOWED_MSG_KEYS}
            for m in messages
        ]

        # --- stream & record rate-limit events ---
        limiter = self.coordinator.get_limiter(provider)
        limiter.record_request()
        for event in provider_instance.stream_chat(clean_messages, intent_info=intent_info):
            yield event

    def _record_success(self, provider: str, event_count: int):
        """Record successful request."""
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
        
        logger.debug(
            f"EnhancedProviderManager: {provider} success "
            f"(total: {stats['successes']}, "
            f"success_rate: {stats['successes']/max(1, stats['successes']+stats['failures']):.0%})"
        )

    def _record_failure(self, provider: str, error: str):
        """Record failed request."""
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
        
        # Increment failure count with exponential backoff decay
        current_count = self.provider_failure_count.get(provider, 0)
        self.provider_failure_count[provider] = current_count + 1
        
        # Schedule failure count reset in 5-10 minutes
        reset_delay = 300 + (current_count * 60)  # 5m + extra per failure
        self.provider_failure_reset[provider] = time.time() + reset_delay
        
        logger.debug(
            f"EnhancedProviderManager: {provider} failure "
            f"(total: {stats['failures']}, failure_count: {self.provider_failure_count[provider]}): {error}"
        )

    def get_provider_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive provider status dashboard."""
        dashboard = {
            "timestamp": time.time(),
            "providers": {},
        }

        for provider in self.provider_stats:
            limiter = self.coordinator.get_limiter(provider)
            stats = self.provider_stats[provider]
            
            total = stats["successes"] + stats["failures"]
            success_rate = stats["successes"] / total if total > 0 else 0.0
            
            dashboard["providers"][provider] = {
                "stats": stats,
                "rate_limit": limiter.get_status(),
                "success_rate": success_rate,
                "failure_priority": self._get_failure_priority(provider),
            }

        return dashboard
