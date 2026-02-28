"""Unified rate limiting and state management for providers.

Provides:
- Per-provider rate limit tracking
- Distributed rate limit coordination
- Adaptive backoff strategies
- State persistence
"""

import logging
import time
from typing import Dict, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Information about provider rate limit status."""
    # Current state
    is_limited: bool = False
    requests_remaining: Optional[int] = None
    reset_time: Optional[datetime] = None
    retry_after: Optional[float] = None

    # History
    last_limited_time: Optional[datetime] = None
    limit_count: int = 0
    total_waits: int = 0
    total_wait_time: float = 0.0

    # Configuration
    low_threshold: int = 10          # Alert when below this
    critical_threshold: int = 5      # Critical when below this


class ProviderRateLimiter:
    """Manages rate limiting per provider."""

    def __init__(self, provider_name: str, max_requests_per_minute: int = 60):
        """Initialize rate limiter.
        
        Args:
            provider_name: Name of provider
            max_requests_per_minute: Rate limit (requests per minute)
        """
        self.provider = provider_name
        self.max_rpm = max_requests_per_minute
        self.request_times = deque(maxlen=max_requests_per_minute)
        self.rate_limit_info = RateLimitInfo()
        self.last_check_time = time.time()

    def can_request(self) -> Tuple[bool, Optional[float]]:
        """Check if a request can be made.
        
        Returns:
            (can_request, wait_time_if_limited)
        """
        now = time.time()

        # Remove requests older than 1 minute
        while self.request_times and (now - self.request_times[0]) > 60:
            self.request_times.popleft()

        # Check if retry_after is still active
        if self.rate_limit_info.retry_after and self.rate_limit_info.reset_time:
            if datetime.now() < self.rate_limit_info.reset_time:
                return False, self.rate_limit_info.retry_after

        # Check if we're at capacity
        if len(self.request_times) >= self.max_rpm:
            oldest_request = self.request_times[0]
            wait_time = 60 - (now - oldest_request)

            if self.rate_limit_info.retry_after is None:
                self.rate_limit_info.is_limited = True
                self.rate_limit_info.last_limited_time = datetime.now()
                self.rate_limit_info.limit_count += 1
                logger.warning(
                    f"{self.provider}: Rate limit reached. Wait {wait_time:.1f}s"
                )

            return False, wait_time

        # Can request - reset is_limited only if retry_after has expired
        if self.rate_limit_info.is_limited and self.rate_limit_info.retry_after is None:
            logger.info(f"{self.provider}: Rate limit cleared")
            self.rate_limit_info.is_limited = False
            self.rate_limit_info.total_waits += 1

        return True, None

    def record_request(self) -> bool:
        """Record that a request was made.
        
        Returns:
            True if recorded successfully
        """
        can_request, _ = self.can_request()
        if can_request:
            self.request_times.append(time.time())
            return True
        return False

    def update_from_headers(
        self,
        requests_remaining: Optional[int] = None,
        reset_unix: Optional[int] = None,
        retry_after: Optional[int] = None,
    ):
        """Update rate limit info from response headers.
        
        Args:
            requests_remaining: X-RateLimit-Remaining header
            reset_unix: X-RateLimit-Reset header (unix timestamp)
            retry_after: Retry-After header (seconds)
        """
        if requests_remaining is not None:
            self.rate_limit_info.requests_remaining = requests_remaining

            if requests_remaining <= self.rate_limit_info.critical_threshold:
                logger.warning(
                    f"{self.provider}: CRITICAL rate limit ({requests_remaining} requests left)"
                )
            elif requests_remaining <= self.rate_limit_info.low_threshold:
                logger.warning(
                    f"{self.provider}: LOW rate limit ({requests_remaining} requests left)"
                )

        if reset_unix:
            self.rate_limit_info.reset_time = datetime.fromtimestamp(reset_unix)

        if retry_after:
            self.rate_limit_info.retry_after = retry_after
            if retry_after > 0:
                self.rate_limit_info.is_limited = True
                self.rate_limit_info.total_wait_time += retry_after
                logger.warning(
                    f"{self.provider}: Retry-After {retry_after}s"
                )

    def get_status(self) -> Dict:
        """Get current rate limit status."""
        can_request, wait_time = self.can_request()

        return {
            "provider": self.provider,
            "can_request": can_request,
            "wait_time": wait_time,
            "requests_this_minute": len(self.request_times),
            "max_rpm": self.max_rpm,
            "is_limited": self.rate_limit_info.is_limited,
            "requests_remaining": self.rate_limit_info.requests_remaining,
            "reset_time": self.rate_limit_info.reset_time.isoformat() if self.rate_limit_info.reset_time else None,
            "limit_count": self.rate_limit_info.limit_count,
            "total_waits": self.rate_limit_info.total_waits,
            "total_wait_time": self.rate_limit_info.total_wait_time,
        }

    def wait_if_needed(self) -> float:
        """Wait if rate limited, return wait time.
        
        Returns:
            Actual wait time in seconds
        """
        can_request, wait_time = self.can_request()

        if not can_request and wait_time:
            logger.info(f"{self.provider}: Waiting {wait_time:.1f}s for rate limit reset")
            time.sleep(wait_time)
            self.rate_limit_info.total_wait_time += wait_time
            return wait_time

        return 0


class GlobalRateLimitCoordinator:
    """Coordinates rate limiting across all providers."""

    def __init__(self):
        """Initialize coordinator."""
        self.limiters: Dict[str, ProviderRateLimiter] = {}
        self.provider_priorities = {}  # Higher priority providers preferred

    def get_limiter(self, provider: str, max_rpm: int = 60) -> ProviderRateLimiter:
        """Get or create limiter for provider.
        
        Args:
            provider: Provider name
            max_rpm: Requests per minute limit
            
        Returns:
            ProviderRateLimiter instance
        """
        if provider not in self.limiters:
            limiter = ProviderRateLimiter(provider, max_rpm)
            self.limiters[provider] = limiter
            logger.debug(f"GlobalRateLimitCoordinator: Created limiter for {provider} ({max_rpm} req/min)")

        return self.limiters[provider]

    def set_provider_priority(self, provider: str, priority: int):
        """Set priority for provider (higher = prefer this provider).
        
        Args:
            provider: Provider name
            priority: Priority value (0-100)
        """
        self.provider_priorities[provider] = priority
        logger.debug(f"GlobalRateLimitCoordinator: Set {provider} priority to {priority}")

    def get_available_provider(self, candidates: list) -> Optional[str]:
        """Get best available provider from candidates.
        
        Prefers providers that are not rate limited.
        Among available providers, prefers by set priority.
        
        Args:
            candidates: List of provider names
            
        Returns:
            Best available provider name, or None if all limited
        """
        available = []

        for provider in candidates:
            if provider not in self.limiters:
                self.get_limiter(provider)

            can_request, _ = self.limiters[provider].can_request()
            if can_request:
                available.append(provider)

        if not available:
            return None

        # Sort by priority
        available.sort(
            key=lambda p: self.provider_priorities.get(p, 0),
            reverse=True
        )

        return available[0]

    def coordinate_fallback_request(self, primary: str, fallback_chain: list) -> str:
        """Determine best provider for fallback request.
        
        Args:
            primary: Primary provider
            fallback_chain: List of fallback providers
            
        Returns:
            Best available provider to use
        """
        # Try primary first
        if primary not in self.limiters:
            self.get_limiter(primary)

        can_request, _ = self.limiters[primary].can_request()
        if can_request:
            return primary

        # Try fallbacks in order
        best = self.get_available_provider(fallback_chain)
        if best:
            logger.info(f"GlobalRateLimitCoordinator: Switching {primary} → {best} (rate limit)")
            return best

        # All limited, return primary (will wait)
        logger.warning(f"GlobalRateLimitCoordinator: All providers rate limited, using {primary}")
        return primary

    def get_global_status(self) -> Dict:
        """Get status of all tracked providers."""
        return {
            "providers": {
                name: limiter.get_status()
                for name, limiter in self.limiters.items()
            },
            "priorities": self.provider_priorities,
            "total_limiters": len(self.limiters),
        }


# Global instance
_global_coordinator: Optional[GlobalRateLimitCoordinator] = None


def get_rate_limit_coordinator() -> GlobalRateLimitCoordinator:
    """Get or create global rate limit coordinator."""
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = GlobalRateLimitCoordinator()
    return _global_coordinator
