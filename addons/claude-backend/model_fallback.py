"""Model Fallback — intelligent multi-model fallback with provider health.

Inspired by OpenClaw's model-fallback.ts:
- Builds a candidate chain: primary → agent fallbacks → global defaults
- Tries each candidate in order; on failure moves to next
- Context-overflow errors abort immediately (smaller fallback would be worse)
- Rate-limit errors use cooldown with periodic probe recovery
- Auth errors permanently skip the provider
- Full attempt log for diagnostics

Integrates with:
- agent_config.AgentManager: for building the candidate chain
- model_catalog.ModelCatalog: for capability checks and context window info
- fallback.ProviderHealth: for health tracking (reuses existing module)

Usage:
    from model_fallback import run_with_model_fallback

    result = await run_with_model_fallback(
        provider="anthropic", model="claude-opus-4-6",
        agent_id="coder",
        run=lambda prov, mdl: my_chat_fn(prov, mdl, messages),
    )
    print(result.provider, result.model, result.result)
"""

from __future__ import annotations

import logging
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Error Classification
# ---------------------------------------------------------------------------

class FailoverReason(Enum):
    """Why we moved to the next candidate."""
    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    AUTH_PERMANENT = "auth_permanent"
    BILLING = "billing"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    MODEL_NOT_FOUND = "model_not_found"
    CONTEXT_OVERFLOW = "context_overflow"
    UNKNOWN = "unknown"


def classify_error(err: Exception) -> FailoverReason:
    """Classify an exception into a FailoverReason."""
    msg = str(err).lower()

    # Context overflow — NEVER fallback (smaller model = worse)
    if any(x in msg for x in ["context_length", "context window", "too many tokens",
                                "maximum context", "prompt is too long",
                                "prompt too large", "request too large"]):
        return FailoverReason.CONTEXT_OVERFLOW

    # Auth
    if any(x in msg for x in ["401", "unauthorized", "invalid.*key", "invalid.*token",
                                "authentication"]):
        return FailoverReason.AUTH
    if "403" in msg or "forbidden" in msg:
        return FailoverReason.AUTH_PERMANENT

    # Billing
    if any(x in msg for x in ["402", "insufficient", "quota", "billing", "credits"]):
        return FailoverReason.BILLING

    # Rate limit
    if any(x in msg for x in ["429", "rate limit", "rate_limit", "too many requests",
                                "overloaded"]):
        return FailoverReason.RATE_LIMIT

    # Model not found
    if any(x in msg for x in ["404", "model not found", "unknown_model",
                                "model_not_found", "model_not_supported"]):
        return FailoverReason.MODEL_NOT_FOUND

    # Timeout
    if any(x in msg for x in ["timeout", "timed out", "deadline"]):
        return FailoverReason.TIMEOUT

    # Server error
    if any(x in msg for x in ["500", "502", "503", "504", "internal", "gateway"]):
        return FailoverReason.SERVER_ERROR

    return FailoverReason.UNKNOWN


def is_context_overflow(err: Exception) -> bool:
    return classify_error(err) == FailoverReason.CONTEXT_OVERFLOW


# ---------------------------------------------------------------------------
# Cooldown tracking (per provider)
# ---------------------------------------------------------------------------

@dataclass
class _CooldownState:
    """Tracks cooldown for a single provider."""
    until: float = 0.0       # time.time() when cooldown expires
    reason: FailoverReason = FailoverReason.UNKNOWN
    permanent: bool = False  # True for auth/billing errors

_cooldowns: Dict[str, _CooldownState] = {}
_cooldowns_lock = threading.Lock()

# Probe: periodically test the primary even during cooldown
_PROBE_INTERVAL_SEC = 30.0
_last_probe: Dict[str, float] = {}


def _set_cooldown(provider: str, reason: FailoverReason, duration_sec: float = 300.0) -> None:
    """Put a provider in cooldown."""
    with _cooldowns_lock:
        permanent = reason in (FailoverReason.AUTH, FailoverReason.AUTH_PERMANENT, FailoverReason.BILLING)
        _cooldowns[provider] = _CooldownState(
            until=time.time() + duration_sec if not permanent else float("inf"),
            reason=reason,
            permanent=permanent,
        )
    logger.warning(f"ModelFallback: {provider} in cooldown ({reason.value}, "
                   f"{'permanent' if permanent else f'{duration_sec}s'})")


def _is_in_cooldown(provider: str) -> bool:
    """Check if a provider is in cooldown."""
    with _cooldowns_lock:
        state = _cooldowns.get(provider)
        if not state:
            return False
        if state.permanent:
            return True
        if time.time() >= state.until:
            # Cooldown expired
            del _cooldowns[provider]
            logger.info(f"ModelFallback: {provider} cooldown expired, re-enabling")
            return False
        return True


def _should_probe(provider: str) -> bool:
    """Should we probe a cooled-down primary to see if it recovered?"""
    now = time.time()
    last = _last_probe.get(provider, 0.0)
    if now - last < _PROBE_INTERVAL_SEC:
        return False
    with _cooldowns_lock:
        state = _cooldowns.get(provider)
        if not state or state.permanent:
            return False
    return True


def _mark_probe(provider: str) -> None:
    _last_probe[provider] = time.time()


def clear_cooldown(provider: str) -> None:
    """Manually clear cooldown for a provider (e.g. after config change)."""
    with _cooldowns_lock:
        _cooldowns.pop(provider, None)
    _last_probe.pop(provider, None)


def clear_all_cooldowns() -> None:
    """Clear all cooldowns."""
    with _cooldowns_lock:
        _cooldowns.clear()
    _last_probe.clear()


def get_cooldown_status() -> Dict[str, Any]:
    """Get cooldown status for all providers."""
    now = time.time()
    with _cooldowns_lock:
        result = {}
        for prov, state in _cooldowns.items():
            result[prov] = {
                "reason": state.reason.value,
                "permanent": state.permanent,
                "remaining_sec": max(0, state.until - now) if not state.permanent else None,
            }
        return result


# ---------------------------------------------------------------------------
# Fallback attempt tracking
# ---------------------------------------------------------------------------

@dataclass
class FallbackAttempt:
    """Record of a single attempt."""
    provider: str
    model: str
    error: str = ""
    reason: FailoverReason = FailoverReason.UNKNOWN
    elapsed_ms: float = 0.0
    skipped: bool = False  # True if skipped due to cooldown


@dataclass
class FallbackResult:
    """Result of a fallback-wrapped execution."""
    result: Any = None
    provider: str = ""
    model: str = ""
    success: bool = False
    attempts: List[FallbackAttempt] = field(default_factory=list)
    error: Optional[Exception] = None


# ---------------------------------------------------------------------------
# Candidate resolution
# ---------------------------------------------------------------------------

@dataclass
class ModelCandidate:
    """A provider/model pair in the fallback chain."""
    provider: str
    model: str

    def key(self) -> str:
        return f"{self.provider}/{self.model}"


def resolve_candidates(
    provider: str,
    model: str,
    agent_id: Optional[str] = None,
    fallbacks_override: Optional[List[str]] = None,
) -> List[ModelCandidate]:
    """Build the ordered candidate list.

    Priority:
    1. The requested provider/model (always first)
    2. Agent-configured fallbacks (if agent_id provided)
    3. Global defaults fallbacks
    4. Global defaults primary (as last resort)
    """
    seen: set = set()
    candidates: List[ModelCandidate] = []

    def _add(p: str, m: str) -> None:
        key = f"{p}/{m}"
        if key not in seen and p and m:
            seen.add(key)
            candidates.append(ModelCandidate(p, m))

    # 1. Primary
    _add(provider, model)

    # 2. Explicit overrides
    if fallbacks_override is not None:
        for raw in fallbacks_override:
            raw = raw.strip()
            if "/" in raw:
                parts = raw.split("/", 1)
                _add(parts[0], parts[1])
            else:
                _add(provider, raw)  # same provider, different model
        return candidates

    # 3. Agent fallbacks
    if agent_id:
        try:
            from agent_config import get_agent_manager
            mgr = get_agent_manager()
            agent = mgr.resolve_agent(agent_id)
            if agent:
                for fb in agent.model_config.fallbacks:
                    _add(fb.provider, fb.model)
        except Exception:
            pass

    # 4. Global defaults fallbacks
    try:
        from agent_config import get_agent_manager
        mgr = get_agent_manager()
        defaults = mgr.get_defaults()
        for fb in defaults.model.fallbacks:
            _add(fb.provider, fb.model)
        if defaults.model.primary:
            _add(defaults.model.primary.provider, defaults.model.primary.model)
    except Exception:
        pass

    return candidates


# ---------------------------------------------------------------------------
# Core: run_with_model_fallback
# ---------------------------------------------------------------------------

def run_with_model_fallback(
    provider: str,
    model: str,
    run: Callable[[str, str], T],
    agent_id: Optional[str] = None,
    fallbacks_override: Optional[List[str]] = None,
    on_error: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_fallback: Optional[Callable[[str, str, str, str], None]] = None,
) -> FallbackResult:
    """Execute `run(provider, model)` with automatic model fallback.

    Args:
        provider: Initial provider ID
        model: Initial model ID
        run: Callable(provider, model) → result
        agent_id: Optional agent for fallback chain
        fallbacks_override: Explicit fallback list (overrides agent/defaults)
        on_error: Callback({provider, model, error, attempt, total})
        on_fallback: Callback(from_provider, from_model, to_provider, to_model)

    Returns:
        FallbackResult with .result, .provider, .model, .success, .attempts
    """
    candidates = resolve_candidates(provider, model, agent_id, fallbacks_override)

    if not candidates:
        return FallbackResult(
            error=Exception("No model candidates configured"),
            attempts=[],
        )

    attempts: List[FallbackAttempt] = []
    last_error: Optional[Exception] = None
    has_fallbacks = len(candidates) > 1

    for i, candidate in enumerate(candidates):
        is_primary = (i == 0)

        # Check cooldown
        if _is_in_cooldown(candidate.provider):
            if is_primary and has_fallbacks and _should_probe(candidate.provider):
                # Probe: try the primary anyway
                _mark_probe(candidate.provider)
                logger.info(f"ModelFallback: probing cooled-down primary {candidate.key()}")
            else:
                # Skip this candidate
                reason_str = "cooldown"
                with _cooldowns_lock:
                    state = _cooldowns.get(candidate.provider)
                    if state:
                        reason_str = state.reason.value
                attempts.append(FallbackAttempt(
                    provider=candidate.provider,
                    model=candidate.model,
                    error=f"Provider {candidate.provider} in cooldown ({reason_str})",
                    reason=FailoverReason.RATE_LIMIT,
                    skipped=True,
                ))
                continue

        # Try execution
        t0 = time.time()
        try:
            result = run(candidate.provider, candidate.model)

            # Success! Clear cooldown if this was a probe
            if _is_in_cooldown(candidate.provider):
                clear_cooldown(candidate.provider)

            elapsed_ms = (time.time() - t0) * 1000
            attempts.append(FallbackAttempt(
                provider=candidate.provider,
                model=candidate.model,
                elapsed_ms=elapsed_ms,
            ))

            return FallbackResult(
                result=result,
                provider=candidate.provider,
                model=candidate.model,
                success=True,
                attempts=attempts,
            )

        except Exception as err:
            elapsed_ms = (time.time() - t0) * 1000
            reason = classify_error(err)

            attempts.append(FallbackAttempt(
                provider=candidate.provider,
                model=candidate.model,
                error=str(err)[:500],
                reason=reason,
                elapsed_ms=elapsed_ms,
            ))

            last_error = err

            # Notify
            if on_error:
                try:
                    on_error({
                        "provider": candidate.provider,
                        "model": candidate.model,
                        "error": err,
                        "attempt": i + 1,
                        "total": len(candidates),
                        "reason": reason.value,
                    })
                except Exception:
                    pass

            # Context overflow: NEVER fallback — smaller model would fail worse
            if reason == FailoverReason.CONTEXT_OVERFLOW:
                logger.warning(f"ModelFallback: context overflow on {candidate.key()}, aborting fallback")
                raise err

            # Set cooldown based on error type
            if reason == FailoverReason.RATE_LIMIT:
                _set_cooldown(candidate.provider, reason, duration_sec=300)
            elif reason in (FailoverReason.AUTH, FailoverReason.AUTH_PERMANENT):
                _set_cooldown(candidate.provider, reason)
            elif reason == FailoverReason.BILLING:
                _set_cooldown(candidate.provider, reason)
            elif reason == FailoverReason.SERVER_ERROR:
                _set_cooldown(candidate.provider, reason, duration_sec=60)

            # Notify fallback
            if i + 1 < len(candidates) and on_fallback:
                next_c = candidates[i + 1]
                try:
                    on_fallback(candidate.provider, candidate.model,
                                next_c.provider, next_c.model)
                except Exception:
                    pass

            # Continue to next candidate
            logger.info(f"ModelFallback: {candidate.key()} failed ({reason.value}), "
                        f"trying next candidate ({i+1}/{len(candidates)})")

    # All candidates exhausted
    summary = _build_failure_summary(attempts, candidates)
    logger.error(f"ModelFallback: all candidates exhausted: {summary}")

    return FallbackResult(
        error=last_error or Exception(f"All models failed: {summary}"),
        attempts=attempts,
    )


def _build_failure_summary(attempts: List[FallbackAttempt],
                           candidates: List[ModelCandidate]) -> str:
    """Build a human-readable failure summary."""
    if not attempts:
        return "no attempts"
    parts = []
    for a in attempts:
        status = "skipped" if a.skipped else a.reason.value
        parts.append(f"{a.provider}/{a.model}: {a.error[:100]} ({status})")
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Streaming variant
# ---------------------------------------------------------------------------

def run_with_model_fallback_streaming(
    provider: str,
    model: str,
    run: Callable[[str, str], Any],
    agent_id: Optional[str] = None,
    fallbacks_override: Optional[List[str]] = None,
    on_error: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_fallback: Optional[Callable[[str, str, str, str], None]] = None,
) -> FallbackResult:
    """Same as run_with_model_fallback but for streaming generators.

    The `run` callable should return a generator. We consume the first
    chunk to verify connectivity, then return the generator as the result.
    If the first chunk fails, we fallback to the next candidate.
    """
    candidates = resolve_candidates(provider, model, agent_id, fallbacks_override)

    if not candidates:
        return FallbackResult(error=Exception("No model candidates configured"))

    attempts: List[FallbackAttempt] = []
    last_error: Optional[Exception] = None
    has_fallbacks = len(candidates) > 1

    for i, candidate in enumerate(candidates):
        is_primary = (i == 0)

        if _is_in_cooldown(candidate.provider):
            if is_primary and has_fallbacks and _should_probe(candidate.provider):
                _mark_probe(candidate.provider)
            else:
                attempts.append(FallbackAttempt(
                    provider=candidate.provider, model=candidate.model,
                    error=f"cooldown", reason=FailoverReason.RATE_LIMIT, skipped=True,
                ))
                continue

        t0 = time.time()
        try:
            gen = run(candidate.provider, candidate.model)
            # Peek at the first event to verify the generator is alive
            first_event = next(gen)

            def _chain_gen(first, remaining):
                yield first
                yield from remaining

            elapsed_ms = (time.time() - t0) * 1000
            attempts.append(FallbackAttempt(
                provider=candidate.provider, model=candidate.model,
                elapsed_ms=elapsed_ms,
            ))

            return FallbackResult(
                result=_chain_gen(first_event, gen),
                provider=candidate.provider,
                model=candidate.model,
                success=True,
                attempts=attempts,
            )

        except StopIteration:
            # Empty generator — treat as success with no content
            elapsed_ms = (time.time() - t0) * 1000
            attempts.append(FallbackAttempt(
                provider=candidate.provider, model=candidate.model,
                elapsed_ms=elapsed_ms,
            ))
            return FallbackResult(
                result=iter([]),
                provider=candidate.provider,
                model=candidate.model,
                success=True,
                attempts=attempts,
            )

        except Exception as err:
            elapsed_ms = (time.time() - t0) * 1000
            reason = classify_error(err)

            attempts.append(FallbackAttempt(
                provider=candidate.provider, model=candidate.model,
                error=str(err)[:500], reason=reason, elapsed_ms=elapsed_ms,
            ))
            last_error = err

            if on_error:
                try:
                    on_error({"provider": candidate.provider, "model": candidate.model,
                              "error": err, "attempt": i + 1, "total": len(candidates),
                              "reason": reason.value})
                except Exception:
                    pass

            if reason == FailoverReason.CONTEXT_OVERFLOW:
                raise err

            if reason == FailoverReason.RATE_LIMIT:
                _set_cooldown(candidate.provider, reason, 300)
            elif reason in (FailoverReason.AUTH, FailoverReason.AUTH_PERMANENT, FailoverReason.BILLING):
                _set_cooldown(candidate.provider, reason)

            if i + 1 < len(candidates) and on_fallback:
                next_c = candidates[i + 1]
                try:
                    on_fallback(candidate.provider, candidate.model, next_c.provider, next_c.model)
                except Exception:
                    pass

            logger.info(f"ModelFallback: streaming {candidate.key()} failed ({reason.value})")

    summary = _build_failure_summary(attempts, candidates)
    return FallbackResult(error=last_error or Exception(f"All models failed: {summary}"), attempts=attempts)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_fallback_stats() -> Dict[str, Any]:
    """Return fallback system statistics."""
    return {
        "cooldowns": get_cooldown_status(),
        "probe_interval_sec": _PROBE_INTERVAL_SEC,
    }
