"""Multi-provider fallback chain with cost optimization.

Inspired by nanobot: Minimal, efficient, practical implementation.
- Automatic fallback to backup providers on failure
- Cost tracking per provider
- Provider health monitoring
- Smart retry logic based on error type
"""

import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types for smart retry decisions."""
    RATE_LIMIT = "rate_limit"          # Quota exceeded
    AUTH_FAILED = "auth_failed"        # Invalid credentials
    INVALID_REQUEST = "invalid_request"  # Bad input (don't retry)
    TIMEOUT = "timeout"                # Network timeout (retry)
    INTERNAL_ERROR = "internal_error"  # Server error (retry)
    UNKNOWN = "unknown"                # Unknown error


class ProviderError:
    """Represents a provider error with classification."""
    
    @staticmethod
    def classify(error: Exception, provider: str) -> ErrorType:
        """Classify error type for smart retry logic."""
        error_str = str(error).lower()
        
        # Auth errors - don't retry
        if any(x in error_str for x in ["invalid", "unauthorized", "forbidden", "apikey", "auth"]):
            return ErrorType.AUTH_FAILED
        
        # Rate limit errors - exponential backoff
        if any(x in error_str for x in ["rate limit", "quota", "too many", "429", "503"]):
            return ErrorType.RATE_LIMIT
        
        # Timeout errors - retry
        if any(x in error_str for x in ["timeout", "timed out", "deadline"]):
            return ErrorType.TIMEOUT
        
        # Invalid request - don't retry
        if any(x in error_str for x in ["invalid", "malformed", "bad request", "400"]):
            return ErrorType.INVALID_REQUEST
        
        # Server errors - retry
        if any(x in error_str for x in ["500", "502", "503", "gateway", "error"]):
            return ErrorType.INTERNAL_ERROR
        
        return ErrorType.UNKNOWN


class ProviderHealth:
    """Tracks provider health and availability."""
    
    def __init__(self, provider_name: str):
        """Initialize provider health tracking."""
        self.provider_name = provider_name
        self.total_requests = 0
        self.failed_requests = 0
        self.success_requests = 0
        self.last_error: Optional[str] = None
        self.last_error_type: Optional[ErrorType] = None
        self.last_error_time: Optional[datetime] = None
        self.consecutive_failures = 0
        self.is_available = True
        self.unavailable_until: Optional[datetime] = None
    
    def record_success(self) -> None:
        """Record successful request."""
        self.total_requests += 1
        self.success_requests += 1
        self.consecutive_failures = 0
        self.is_available = True
    
    def record_failure(self, error: Exception, error_type: ErrorType) -> None:
        """Record failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_error = str(error)
        self.last_error_type = error_type
        self.last_error_time = datetime.now()
        
        # Temporarily disable provider if too many failures
        if error_type == ErrorType.RATE_LIMIT and self.consecutive_failures > 3:
            # 5 minute cooldown for rate limiting
            self.unavailable_until = datetime.now() + timedelta(minutes=5)
            self.is_available = False
            logger.warning(f"{self.provider_name}: Rate limited, temporarily disabled for 5 min")
        elif error_type == ErrorType.AUTH_FAILED:
            # Permanently disable on auth failure
            self.is_available = False
            logger.error(f"{self.provider_name}: Authentication failed, permanently disabled")
        elif self.consecutive_failures > 10:
            # Disable after too many failures
            self.unavailable_until = datetime.now() + timedelta(minutes=10)
            self.is_available = False
            logger.warning(f"{self.provider_name}: Too many failures, disabled for 10 min")
    
    def is_ready(self) -> bool:
        """Check if provider is ready to use."""
        if not self.is_available:
            if self.unavailable_until and datetime.now() > self.unavailable_until:
                self.is_available = True
                self.consecutive_failures = 0
                logger.info(f"{self.provider_name}: Recovered, re-enabling")
                return True
            return False
        return True
    
    def success_rate(self) -> float:
        """Get success rate (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 1.0
        return self.success_requests / self.total_requests
    
    def stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        return {
            "provider": self.provider_name,
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{self.success_rate()*100:.1f}%",
            "consecutive_failures": self.consecutive_failures,
            "available": self.is_available,
            "last_error": self.last_error,
            "last_error_type": self.last_error_type.value if self.last_error_type else None,
        }


class ProviderFallback:
    """Multi-provider fallback chain with health monitoring."""
    
    def __init__(self, provider_order: List[str]):
        """Initialize fallback chain.
        
        Args:
            provider_order: List of provider names in order of preference
                           E.g., ["anthropic", "openai", "google"]
        """
        self.provider_order = provider_order
        self.health: Dict[str, ProviderHealth] = {
            p: ProviderHealth(p) for p in provider_order
        }
        self.costs: Dict[str, float] = {p: 0.0 for p in provider_order}
        self.call_counts: Dict[str, int] = {p: 0 for p in provider_order}
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers in order."""
        available = []
        for provider in self.provider_order:
            if self.health[provider].is_ready():
                available.append(provider)
        
        if not available:
            logger.warning("No providers available, returning all (recovery mode)")
            return self.provider_order
        
        return available
    
    def should_retry(self, error: Exception, provider: str, attempt: int) -> bool:
        """Decide if we should retry with same provider or fallback.
        
        Args:
            error: The exception raised
            provider: Provider that failed
            attempt: Current attempt number
            
        Returns:
            True if should retry
        """
        error_type = ProviderError.classify(error, provider)
        
        # Never retry on auth or invalid request errors
        if error_type in (ErrorType.AUTH_FAILED, ErrorType.INVALID_REQUEST):
            return False
        
        # Retry transient errors up to 3 times
        if error_type in (ErrorType.TIMEOUT, ErrorType.INTERNAL_ERROR):
            return attempt < 3
        
        # Rate limit: limited retries with backoff
        if error_type == ErrorType.RATE_LIMIT:
            return attempt < 2
        
        return False
    
    def execute_with_fallback(self, 
                             execute_fn,
                             *args,
                             timeout_per_provider: float = 30.0,
                             **kwargs) -> Tuple[Optional[Any], str]:
        """Execute function with automatic provider fallback.
        
        Args:
            execute_fn: Callable that takes (provider_name, *args, **kwargs)
            timeout_per_provider: Timeout per provider (for cost tracking)
            *args: Arguments to pass to execute_fn
            **kwargs: Keyword arguments to pass to execute_fn
            
        Returns:
            Tuple of (result, provider_used) or (None, provider_name) on failure
        """
        available_providers = self.get_available_providers()
        last_error = None
        
        for provider in available_providers:
            attempt = 0
            max_attempts = 3
            
            while attempt < max_attempts:
                try:
                    start_time = time.time()
                    result = execute_fn(provider, *args, **kwargs)
                    elapsed = time.time() - start_time
                    
                    # Record success
                    self.health[provider].record_success()
                    self.call_counts[provider] += 1
                    
                    logger.info(f"✅ {provider}: Success in {elapsed:.2f}s (attempt {attempt + 1})")
                    return result, provider
                    
                except Exception as e:
                    elapsed = time.time() - start_time
                    error_type = ProviderError.classify(e, provider)
                    
                    logger.warning(f"⚠️ {provider}: {error_type.value} - {str(e)[:100]}")
                    
                    self.health[provider].record_failure(e, error_type)
                    last_error = (e, error_type)
                    
                    # Decide if we should retry or fallback
                    if self.should_retry(e, provider, attempt):
                        attempt += 1
                        wait_time = 0.5 * (2 ** attempt)  # Exponential backoff
                        logger.debug(f"Retrying {provider} in {wait_time}s ({attempt}/{max_attempts})")
                        time.sleep(wait_time)
                    else:
                        break  # Try next provider
        
        # All providers exhausted
        logger.error(f"❌ All providers exhausted. Last error: {last_error}")
        return None, "failed"
    
    def record_cost(self, provider: str, cost: float) -> None:
        """Record API cost for a provider."""
        if provider in self.costs:
            self.costs[provider] += cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        total_cost = sum(self.costs.values())
        total_calls = sum(self.call_counts.values())
        
        provider_stats = {}
        for provider in self.provider_order:
            health = self.health[provider]
            provider_stats[provider] = {
                **health.stats(),
                "cost": f"${self.costs[provider]:.4f}",
                "calls": self.call_counts[provider],
                "avg_cost_per_call": f"${self.costs[provider] / max(self.call_counts[provider], 1):.6f}",
            }
        
        return {
            "providers": provider_stats,
            "total_cost": f"${total_cost:.4f}",
            "total_calls": total_calls,
            "best_provider": min(
                self.provider_order,
                key=lambda p: self.health[p].success_rate()
            ),
            "available_providers": self.get_available_providers(),
        }


# Global fallback instance
_fallback_chain: Optional[ProviderFallback] = None


def initialize_fallback_chain(provider_order: List[str]) -> ProviderFallback:
    """Initialize global fallback chain."""
    global _fallback_chain
    _fallback_chain = ProviderFallback(provider_order)
    logger.info(f"Fallback chain initialized: {' → '.join(provider_order)}")
    return _fallback_chain


def get_fallback_chain() -> Optional[ProviderFallback]:
    """Get global fallback chain instance."""
    return _fallback_chain


def reset_fallback_chain() -> None:
    """Reset global fallback chain."""
    global _fallback_chain
    _fallback_chain = None
