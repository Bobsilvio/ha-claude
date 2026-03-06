"""AI model pricing table for token cost estimation.

Prices are per 1 million tokens (USD). Updated each release.
Free providers (NVIDIA, Ollama) always return cost 0.

Inspired by OpenClaw's ModelCostConfig: each model can specify
input / output / cache_read / cache_write rates separately.
Cache reads are typically 90% cheaper, cache writes 25% more expensive.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Prices per 1M tokens (USD)
# Keys: input, output, cache_read (opt), cache_write (opt)
# When cache_read / cache_write are omitted the default rule applies:
#   cache_read  = input * 0.10  (90% discount)
#   cache_write = input * 1.25  (25% surcharge)
# ---------------------------------------------------------------------------
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # ------------------------------------------------------------------ Anthropic
    # Anthropic cache: reads = 10% of input, writes = 125% of input
    "claude-opus-4-20250514":     {"input": 15.00, "output": 75.00, "cache_read": 1.50,  "cache_write": 18.75},
    "claude-opus-4":              {"input": 15.00, "output": 75.00, "cache_read": 1.50,  "cache_write": 18.75},
    "claude-sonnet-4-20250514":   {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    "claude-sonnet-4":            {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    "claude-haiku-4-20250514":    {"input": 0.80,  "output": 4.00,  "cache_read": 0.08,  "cache_write": 1.00},
    "claude-haiku-4":             {"input": 0.80,  "output": 4.00,  "cache_read": 0.08,  "cache_write": 1.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    "claude-3-5-sonnet-20240620": {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    "claude-3-5-sonnet":          {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    "claude-3-5-haiku-20241022":  {"input": 0.80,  "output": 4.00,  "cache_read": 0.08,  "cache_write": 1.00},
    "claude-3-5-haiku":           {"input": 0.80,  "output": 4.00,  "cache_read": 0.08,  "cache_write": 1.00},
    "claude-3-opus-20240229":     {"input": 15.00, "output": 75.00, "cache_read": 1.50,  "cache_write": 18.75},
    "claude-3-opus":              {"input": 15.00, "output": 75.00, "cache_read": 1.50,  "cache_write": 18.75},
    "claude-3-sonnet-20240229":   {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    "claude-3-haiku-20240307":    {"input": 0.25,  "output": 1.25,  "cache_read": 0.03,  "cache_write": 0.30},
    "claude-3-haiku":             {"input": 0.25,  "output": 1.25,  "cache_read": 0.03,  "cache_write": 0.30},
    # ------------------------------------------------------------------ OpenAI
    # OpenAI: cached input = 50% of input (no separate write cost)
    "gpt-5.2":          {"input": 2.50,  "output": 10.00, "cache_read": 1.25},
    "gpt-5.2-mini":     {"input": 0.40,  "output": 1.60,  "cache_read": 0.20},
    "gpt-5":            {"input": 2.00,  "output": 8.00,  "cache_read": 1.00},
    "gpt-4o":           {"input": 2.50,  "output": 10.00, "cache_read": 1.25},
    "gpt-4o-mini":      {"input": 0.15,  "output": 0.60,  "cache_read": 0.075},
    "gpt-4-turbo":      {"input": 10.00, "output": 30.00},
    "o3":               {"input": 2.00,  "output": 8.00,  "cache_read": 1.00},
    "o3-mini":          {"input": 1.10,  "output": 4.40,  "cache_read": 0.55},
    "o4-mini":          {"input": 1.10,  "output": 4.40,  "cache_read": 0.55},
    "o1":               {"input": 15.00, "output": 60.00, "cache_read": 7.50},
    "o1-mini":          {"input": 1.10,  "output": 4.40,  "cache_read": 0.55},
    "o1-preview":       {"input": 15.00, "output": 60.00, "cache_read": 7.50},
    # ------------------------------------------------------------------ Google
    # Gemini: context caching = 25% of input (free tier has no cache cost)
    "gemini-2.5-pro":              {"input": 1.25,  "output": 10.00, "cache_read": 0.3125},
    "gemini-2.5-pro-preview":      {"input": 1.25,  "output": 10.00, "cache_read": 0.3125},
    "gemini-2.5-flash":            {"input": 0.15,  "output": 0.60,  "cache_read": 0.0375},
    "gemini-2.5-flash-preview":    {"input": 0.15,  "output": 0.60,  "cache_read": 0.0375},
    "gemini-2.0-flash":            {"input": 0.10,  "output": 0.40,  "cache_read": 0.025},
    "gemini-2.0-flash-lite":       {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro":              {"input": 1.25,  "output": 5.00,  "cache_read": 0.3125},
    "gemini-1.5-flash":            {"input": 0.075, "output": 0.30,  "cache_read": 0.01875},
    # ------------------------------------------------------------------ Groq
    "llama-3.3-70b-versatile":    {"input": 0.59, "output": 0.79},
    "llama-3.1-70b-versatile":    {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant":       {"input": 0.05, "output": 0.08},
    "llama3-70b-8192":            {"input": 0.59, "output": 0.79},
    "llama3-8b-8192":             {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768":         {"input": 0.24, "output": 0.24},
    "gemma2-9b-it":               {"input": 0.20, "output": 0.20},
    "gemma-7b-it":                {"input": 0.07, "output": 0.07},
    # ------------------------------------------------------------------ Mistral
    "mistral-large-latest":    {"input": 2.00, "output": 6.00},
    "mistral-large-2411":      {"input": 2.00, "output": 6.00},
    "mistral-medium-3":        {"input": 0.40, "output": 2.00},
    "mistral-small-latest":    {"input": 0.10, "output": 0.30},
    "mistral-small-2503":      {"input": 0.10, "output": 0.30},
    "codestral-latest":        {"input": 0.30, "output": 0.90},
    "codestral-2501":          {"input": 0.30, "output": 0.90},
    "pixtral-large-latest":    {"input": 2.00, "output": 6.00},
    "pixtral-large-2411":      {"input": 2.00, "output": 6.00},
    "ministral-8b-latest":     {"input": 0.10, "output": 0.10},
    "ministral-3b-latest":     {"input": 0.04, "output": 0.04},
    "open-mistral-nemo":       {"input": 0.15, "output": 0.15},
    "open-mixtral-8x7b":       {"input": 0.70, "output": 0.70},
    "open-mixtral-8x22b":      {"input": 2.00, "output": 6.00},
    "pixtral-12b-2409":        {"input": 0.15, "output": 0.15},
    # ------------------------------------------------------------------ DeepSeek
    # DeepSeek: cache hit = ~10% of input
    "deepseek-chat":        {"input": 0.27, "output": 1.10, "cache_read": 0.07},
    "deepseek-v3":          {"input": 0.27, "output": 1.10, "cache_read": 0.07},
    "deepseek-reasoner":    {"input": 0.55, "output": 2.19, "cache_read": 0.14},
    "deepseek-r1":          {"input": 0.55, "output": 2.19, "cache_read": 0.14},
    # ------------------------------------------------------------------ Moonshot / Kimi
    "moonshot-v1-8k":   {"input": 1.00, "output": 3.00},
    "moonshot-v1-32k":  {"input": 1.60, "output": 3.00},
    "moonshot-v1-128k": {"input": 3.00, "output": 10.00},
    "kimi-k2.5":        {"input": 0.50, "output": 2.50},
}

FREE_PROVIDERS = {"nvidia", "ollama"}

CURRENCY_RATES = {"USD": 1.0, "EUR": 0.92}


# ---------------------------------------------------------------------------
# Usage normalizer (inspired by OpenClaw UsageLike)
# Handles 20+ naming variants from different providers.
# ---------------------------------------------------------------------------

def normalize_usage(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw provider usage dict into a canonical form.

    Returns a dict with canonical keys:
        input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
        model, provider  (pass-through if present)

    Handles naming variants:
        input:  input_tokens, prompt_tokens, promptTokens, inputTokens
        output: output_tokens, completion_tokens, completionTokens, outputTokens
        cache_read:  cache_read_input_tokens, cached_tokens,
                     prompt_tokens_details.cached_tokens, cache_read_tokens
        cache_write: cache_creation_input_tokens, cache_write_tokens
    """
    if not raw:
        return {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0}

    # --- input tokens ---
    inp = (
        raw.get("input_tokens")
        or raw.get("prompt_tokens")
        or raw.get("promptTokens")
        or raw.get("inputTokens")
        or 0
    )

    # --- output tokens ---
    out = (
        raw.get("output_tokens")
        or raw.get("completion_tokens")
        or raw.get("completionTokens")
        or raw.get("outputTokens")
        or 0
    )

    # --- cache read tokens ---
    # Anthropic: cache_read_input_tokens
    # OpenAI:    prompt_tokens_details.cached_tokens  (nested)
    # Generic:   cached_tokens, cache_read_tokens, cacheRead
    cache_read = (
        raw.get("cache_read_input_tokens")
        or raw.get("cache_read_tokens")
        or raw.get("cached_tokens")
        or raw.get("cacheRead")
        or 0
    )
    # OpenAI nests cache info in prompt_tokens_details
    if not cache_read:
        ptd = raw.get("prompt_tokens_details") or {}
        cache_read = ptd.get("cached_tokens", 0) if isinstance(ptd, dict) else 0

    # --- cache write tokens ---
    # Anthropic: cache_creation_input_tokens
    # Generic:   cache_write_tokens, cacheWrite
    cache_write = (
        raw.get("cache_creation_input_tokens")
        or raw.get("cache_write_tokens")
        or raw.get("cacheWrite")
        or 0
    )

    result: Dict[str, Any] = {
        "input_tokens": int(inp),
        "output_tokens": int(out),
        "cache_read_tokens": int(cache_read),
        "cache_write_tokens": int(cache_write),
    }

    # Pass through metadata if present
    for key in ("model", "provider"):
        if key in raw:
            result[key] = raw[key]

    return result


# ---------------------------------------------------------------------------
# Cost breakdown (inspired by OpenClaw CostBreakdown)
# ---------------------------------------------------------------------------

def _lookup_pricing(model: str) -> Optional[Dict[str, float]]:
    """Exact match first, then prefix/substring fallback."""
    if not model:
        return None
    # Exact match
    p = MODEL_PRICING.get(model)
    if p:
        return p
    # Strip provider prefix (e.g. "groq/llama-3.3-70b-versatile" → "llama-3.3-70b-versatile")
    bare = model.split("/", 1)[-1] if "/" in model else model
    if bare != model:
        p = MODEL_PRICING.get(bare)
        if p:
            return p
    # Fuzzy: find a pricing key that the model name starts with
    model_lower = bare.lower()
    for key, val in MODEL_PRICING.items():
        if model_lower.startswith(key.lower()) or key.lower() in model_lower:
            return val
    return None


def calculate_cost_breakdown(
    model: str,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    currency: str = "USD",
) -> Dict[str, float]:
    """Calculate detailed cost breakdown.

    Returns dict with:
        input_cost, output_cost, cache_read_cost, cache_write_cost,
        total_cost, currency
    All values in the requested currency.
    """
    zero = {
        "input_cost": 0.0, "output_cost": 0.0,
        "cache_read_cost": 0.0, "cache_write_cost": 0.0,
        "total_cost": 0.0, "currency": currency,
    }
    if provider in FREE_PROVIDERS:
        return zero

    pricing = _lookup_pricing(model)
    if not pricing:
        return zero

    rate = CURRENCY_RATES.get(currency, 1.0)
    inp_rate = pricing["input"]
    out_rate = pricing["output"]
    # Default cache pricing: read = 10% of input, write = 125% of input
    cr_rate = pricing.get("cache_read", inp_rate * 0.10)
    cw_rate = pricing.get("cache_write", inp_rate * 1.25)

    inp_cost = (input_tokens * inp_rate / 1_000_000) * rate
    out_cost = (output_tokens * out_rate / 1_000_000) * rate
    cr_cost = (cache_read_tokens * cr_rate / 1_000_000) * rate
    cw_cost = (cache_write_tokens * cw_rate / 1_000_000) * rate

    return {
        "input_cost": round(inp_cost, 6),
        "output_cost": round(out_cost, 6),
        "cache_read_cost": round(cr_cost, 6),
        "cache_write_cost": round(cw_cost, 6),
        "total_cost": round(inp_cost + out_cost + cr_cost + cw_cost, 6),
        "currency": currency,
    }


def calculate_cost(
    model: str,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    currency: str = "USD",
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """Calculate total cost in the specified currency. Returns 0.0 for free providers.

    Backward compatible — cache tokens are optional kwargs.
    """
    bd = calculate_cost_breakdown(
        model, provider, input_tokens, output_tokens,
        cache_read_tokens, cache_write_tokens, currency,
    )
    return bd["total_cost"]


# ---------------------------------------------------------------------------
# Formatting helpers (inspired by OpenClaw usage-format.ts)
# ---------------------------------------------------------------------------

def format_token_count(value: Optional[int]) -> str:
    """Human-friendly token count: 1.2k, 3.5m."""
    if value is None or value <= 0:
        return "0"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}m"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k" if value < 10_000 else f"{value / 1_000:.0f}k"
    return str(value)


def format_usd(value: Optional[float]) -> Optional[str]:
    """Smart USD formatting: $1.23, $0.0054."""
    if value is None:
        return None
    if value >= 0.01:
        return f"${value:.2f}"
    if value > 0:
        return f"${value:.4f}"
    return "$0.00"
