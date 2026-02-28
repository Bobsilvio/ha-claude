"""AI model pricing table for token cost estimation.

Prices are per 1 million tokens (USD). Updated each release.
Free providers (GitHub, NVIDIA, Ollama) always return cost 0.
"""

# Prices per 1M tokens (USD)
MODEL_PRICING = {
    # ------------------------------------------------------------------ Anthropic
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-opus-4":          {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4":          {"input": 3.00, "output": 15.00},
    "claude-haiku-4-20250514":  {"input": 0.80, "output": 4.00},
    "claude-haiku-4":           {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet":          {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022":  {"input": 0.80, "output": 4.00},
    "claude-3-5-haiku":           {"input": 0.80, "output": 4.00},
    "claude-3-opus-20240229":     {"input": 15.00, "output": 75.00},
    "claude-3-opus":              {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229":   {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307":    {"input": 0.25, "output": 1.25},
    "claude-3-haiku":             {"input": 0.25, "output": 1.25},
    # ------------------------------------------------------------------ OpenAI
    "gpt-5.2":          {"input": 2.50, "output": 10.00},
    "gpt-5.2-mini":     {"input": 0.40, "output": 1.60},
    "gpt-5":            {"input": 2.00, "output": 8.00},
    "gpt-4o":           {"input": 2.50, "output": 10.00},
    "gpt-4o-mini":      {"input": 0.15, "output": 0.60},
    "gpt-4-turbo":      {"input": 10.00, "output": 30.00},
    "o3":               {"input": 2.00, "output": 8.00},
    "o3-mini":          {"input": 1.10, "output": 4.40},
    "o4-mini":          {"input": 1.10, "output": 4.40},
    "o1":               {"input": 15.00, "output": 60.00},
    "o1-mini":          {"input": 1.10, "output": 4.40},
    "o1-preview":       {"input": 15.00, "output": 60.00},
    # ------------------------------------------------------------------ Google
    "gemini-2.5-pro":              {"input": 1.25, "output": 10.00},
    "gemini-2.5-pro-preview":      {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash":            {"input": 0.15, "output": 0.60},
    "gemini-2.5-flash-preview":    {"input": 0.15, "output": 0.60},
    "gemini-2.0-flash":            {"input": 0.10, "output": 0.40},
    "gemini-2.0-flash-lite":       {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro":              {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash":            {"input": 0.075, "output": 0.30},
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
    "deepseek-chat":        {"input": 0.27, "output": 1.10},
    "deepseek-v3":          {"input": 0.27, "output": 1.10},
    "deepseek-reasoner":    {"input": 0.55, "output": 2.19},
    "deepseek-r1":          {"input": 0.55, "output": 2.19},
    # ------------------------------------------------------------------ Moonshot / Kimi
    "moonshot-v1-8k":   {"input": 1.00, "output": 3.00},
    "moonshot-v1-32k":  {"input": 1.60, "output": 3.00},
    "moonshot-v1-128k": {"input": 3.00, "output": 10.00},
    "kimi-k2.5":        {"input": 0.50, "output": 2.50},
}

FREE_PROVIDERS = {"github", "nvidia", "ollama"}

CURRENCY_RATES = {"USD": 1.0, "EUR": 0.92}


def _lookup_pricing(model: str):
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


def calculate_cost(model: str, provider: str, input_tokens: int, output_tokens: int, currency: str = "USD") -> float:
    """Calculate cost in the specified currency. Returns 0.0 for free providers."""
    if provider in FREE_PROVIDERS:
        return 0.0
    pricing = _lookup_pricing(model)
    if not pricing:
        return 0.0
    cost_usd = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
    return round(cost_usd * CURRENCY_RATES.get(currency, 1.0), 6)
