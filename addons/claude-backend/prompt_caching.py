"""Anthropic Prompt Caching System.

Implements efficient prompt caching for Anthropic Claude models using
ephemeral cache control headers. This reduces costs and latency for
repeated systems prompts and large context blocks.

Features:
- Automatic cache control header injection
- Multi-intent caching strategies
- Cache statistics and monitoring
- Cost tracking (cache reads vs compute)
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheStatistics:
    """Statistics about cache usage."""
    cache_hits: int = 0
    cache_writes: int = 0
    cache_read_tokens: int = 0  # Tokens read from cache (cheaper)
    cache_write_tokens: int = 0  # Tokens written to cache (1x cost)
    compute_tokens: int = 0  # Tokens computed normally
    total_cost_saving: float = 0.0
    last_hit_time: float = 0.0
    last_write_time: float = 0.0


class PromptCacheManager:
    """Manages prompt caching for Anthropic models."""

    def __init__(self):
        """Initialize cache manager."""
        self.cache_enabled = True
        self.stats = CacheStatistics()
        self.cacheable_intents = {
            "config_edit": {
                "cache_horizon": 3600,  # Cache for 1 hour
                "priority": "high",
                "description": "YAML configuration editing prompts",
            },
            "config_read": {
                "cache_horizon": 1800,
                "priority": "high",
                "description": "YAML configuration read prompts",
            },
            "entity_query": {
                "cache_horizon": 900,
                "priority": "medium",
                "description": "Entity information query prompts",
            },
            "automation_create": {
                "cache_horizon": 1800,
                "priority": "medium",
                "description": "Automation creation prompts",
            },
        }

    def should_cache_intent(self, intent_name: Optional[str]) -> bool:
        """Check if intent should use prompt caching."""
        if not self.cache_enabled or not intent_name:
            return False
        return intent_name in self.cacheable_intents

    def get_cache_config(self, intent_name: str) -> Dict[str, Any]:
        """Get cache configuration for an intent.
        
        Returns:
            Dictionary with cache control settings
        """
        if intent_name not in self.cacheable_intents:
            return {}

        config = self.cacheable_intents[intent_name]
        return {
            "type": "ephemeral",  # Ephemeral: lives for 5 minutes (ideal for repeated queries)
            "priority": config["priority"],  # high/medium/low
        }

    def wrap_system_prompt_for_caching(
        self,
        system_prompt: str,
        intent_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Convert system prompt to cached format.
        
        Anthropic caching works by wrapping the system prompt in a special format:
        
        ```python
        [
            {
                "type": "text",
                "text": "system prompt here",
                "cache_control": {"type": "ephemeral"}
            }
        ]
        ```
        
        Args:
            system_prompt: The system prompt text
            intent_name: Optional intent for logging
            
        Returns:
            List with cache-wrapped system prompt
        """
        cache_config = self.get_cache_config(intent_name or "unknown")

        if not cache_config:
            # No caching for this intent
            return system_prompt  # Return as-is

        logger.info(
            f"PromptCacheManager: wrapping system prompt for caching (intent={intent_name})"
        )

        return [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": cache_config,
            }
        ]

    def wrap_user_context_for_caching(
        self,
        content: str,
        cache_last_block: bool = False,
        intent_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Wrap large user context blocks for caching.
        
        For large documents (config files, entity lists), we can cache them
        to avoid re-processing on repeated queries.
        
        Args:
            content: The content to potentially cache
            cache_last_block: If True, mark this block as cacheable
            intent_name: Optional intent for context
            
        Returns:
            List with wrapped content (may include cache control)
        """
        if not self.should_cache_intent(intent_name):
            return [{"type": "text", "text": content}]

        # Only cache large blocks (>1000 chars) to avoid overhead
        if len(content) < 1000:
            return [{"type": "text", "text": content}]

        cache_config = self.get_cache_config(intent_name or "unknown")

        if cache_last_block:
            logger.info(
                f"PromptCacheManager: caching large context block ({len(content)} chars, intent={intent_name})"
            )
            return [
                {
                    "type": "text",
                    "text": content,
                    "cache_control": cache_config,
                }
            ]
        else:
            return [{"type": "text", "text": content}]

    def add_cache_control_to_call_kwargs(
        self,
        call_kwargs: Dict[str, Any],
        system_prompt: str,
        intent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add cache control to OpenAI-style API call kwargs.
        
        Modifies call_kwargs in-place to add Anthropic cache control
        to the system prompt.
        
        Args:
            call_kwargs: The API call kwargs dict (will be modified)
            system_prompt: The system prompt to cache
            intent_name: Optional intent name
            
        Returns:
            Modified call_kwargs dict
        """
        if not self.should_cache_intent(intent_name):
            return call_kwargs

        # Replace system prompt with cached version
        call_kwargs["system"] = self.wrap_system_prompt_for_caching(
            system_prompt, intent_name
        )

        logger.debug(
            f"PromptCacheManager: added cache control to system prompt (intent={intent_name})"
        )

        return call_kwargs

    def record_cache_usage(
        self,
        cache_creation_input_tokens: int = 0,
        cache_read_input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = "",
    ):
        """Record cache usage from API response.
        
        Anthropic returns usage breakdown:
        - input_tokens: Regular input tokens (normal cost)
        - cache_creation_input_tokens: Tokens written to cache (1x cost)
        - cache_read_input_tokens: Tokens read from cache (0.1x cost, 90% savings)
        
        Args:
            cache_creation_input_tokens: Tokens written to cache
            cache_read_input_tokens: Tokens read from cache
            output_tokens: Output tokens (normal cost)
            model: Model name for logging
        """
        if cache_read_input_tokens > 0:
            self.stats.cache_hits += 1
            self.stats.cache_read_tokens += cache_read_input_tokens

            # Calculate cost savings: cache reads cost 10% of regular tokens
            cache_saving = cache_read_input_tokens * 0.9 * (0.003 / 1000)  # Approx cost
            self.stats.total_cost_saving += cache_saving

            logger.info(
                f"PromptCacheManager: cache hit! {cache_read_input_tokens} tokens from cache "
                f"(~${cache_saving:.6f} savings, model={model})"
            )
            self.stats.last_hit_time = time.time()

        if cache_creation_input_tokens > 0:
            self.stats.cache_writes += 1
            self.stats.cache_write_tokens += cache_creation_input_tokens
            logger.info(
                f"PromptCacheManager: cache write {cache_creation_input_tokens} tokens "
                f"(model={model})"
            )
            self.stats.last_write_time = time.time()

        if cache_read_input_tokens == 0 and cache_creation_input_tokens == 0:
            self.stats.compute_tokens += (
                output_tokens  # Rough estimate for input (proper tracking needs API data)
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics."""
        return {
            "cache_enabled": self.cache_enabled,
            "hits": self.stats.cache_hits,
            "writes": self.stats.cache_writes,
            "tokens_from_cache": self.stats.cache_read_tokens,
            "tokens_to_cache": self.stats.cache_write_tokens,
            "tokens_computed": self.stats.compute_tokens,
            "total_cost_saving": f"${self.stats.total_cost_saving:.4f}",
            "last_hit": self.stats.last_hit_time,
            "last_write": self.stats.last_write_time,
            "cacheable_intents": list(self.cacheable_intents.keys()),
        }

    def reset_statistics(self):
        """Reset cache statistics."""
        self.stats = CacheStatistics()
        logger.info("PromptCacheManager: statistics reset")


# Global instance
_cache_manager: Optional[PromptCacheManager] = None


def get_cache_manager() -> PromptCacheManager:
    """Get or create the global prompt cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = PromptCacheManager()
    return _cache_manager


def should_use_caching(intent_name: Optional[str]) -> bool:
    """Check if caching should be used for intent."""
    return get_cache_manager().should_cache_intent(intent_name)
