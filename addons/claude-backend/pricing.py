"""AI model pricing table for token cost estimation.

Prices are per 1 million tokens (USD). Updated each release.
Free providers (GitHub, NVIDIA) always return cost 0.
"""

# Prices per 1M tokens (USD)
MODEL_PRICING = {
    # Anthropic
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-haiku-4-20250514": {"input": 0.80, "output": 4.00},
    # OpenAI
    "gpt-5.2": {"input": 2.50, "output": 10.00},
    "gpt-5.2-mini": {"input": 0.40, "output": 1.60},
    "gpt-5": {"input": 2.00, "output": 8.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "o3": {"input": 2.00, "output": 8.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
    "o1": {"input": 15.00, "output": 60.00},
    # Google
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
}

FREE_PROVIDERS = {"github", "nvidia"}

CURRENCY_RATES = {"USD": 1.0, "EUR": 0.92}


def calculate_cost(model: str, provider: str, input_tokens: int, output_tokens: int, currency: str = "USD") -> float:
    """Calculate cost in the specified currency. Returns 0.0 for free providers."""
    if provider in FREE_PROVIDERS:
        return 0.0
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0
    cost_usd = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
    return round(cost_usd * CURRENCY_RATES.get(currency, 1.0), 6)
