"""Model fetcher — fetch and cache model lists from official provider APIs.

Supports:
- OpenAI-compatible /v1/models (OpenAI, Groq, Mistral, NVIDIA, DeepSeek, OpenRouter,
  SiliconFlow, Moonshot, Zhipu, MiniMax, AiHubMix, VolcEngine, DashScope, Custom)
- Anthropic      /v1/models
- Google         /v1beta/models
- Ollama         /api/tags
- GitHub Copilot api.githubcopilot.com/models (OAuth token from /data/oauth_copilot.json)

Providers without a public models endpoint (GitHub Models, OpenAI Codex,
Claude Web, ChatGPT Web) are skipped silently; their static lists remain in use.

Usage:
    from providers.model_fetcher import refresh_all_providers, load_cache
    results = refresh_all_providers(provider_keys, extra_config)
    # results["updated"] -> {provider: [model_id, ...]}
    # results["errors"]  -> {provider: "error message"}
    # results["skipped"] -> [provider, ...]
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

CACHE_FILE = "/data/amira_models_cache.json"
TIMEOUT = 10.0

# Keywords identifying non-chat models (embeddings, TTS, image, moderation, etc.)
_EXCLUDE = {
    "embedding", "embed", "whisper", "dall-e", "davinci-edit",
    "moderation", "search", "similarity", "tts", "image", "vision-preview",
    "babbage", "ada-002", "curie", "davinci-002", "realtime",
    "instruct-beta", "text-", "code-search",
}

# Providers that have no public /models endpoint — skip without error
_NO_ENDPOINT = {
    "github", "openai_codex",
    "claude_web", "chatgpt_web",
}

# Official base URLs for OpenAI-compatible providers
_BASE_URLS: Dict[str, str] = {
    "openai":      "https://api.openai.com/v1",
    "groq":        "https://api.groq.com/openai/v1",
    "mistral":     "https://api.mistral.ai/v1",
    "nvidia":      "https://integrate.api.nvidia.com/v1",
    "deepseek":    "https://api.deepseek.com/v1",
    "openrouter":  "https://openrouter.ai/api/v1",
    "zhipu":       "https://open.bigmodel.cn/api/paas/v4",
    "siliconflow": "https://api.siliconflow.cn/v1",
    "moonshot":    "https://api.moonshot.cn/v1",
    "minimax":     "https://api.minimax.chat/v1",
    "aihubmix":    "https://aihubmix.com/v1",
    "volcengine":  "https://ark.cn-beijing.volces.com/api/v3",
    "dashscope":   "https://dashscope-compatible-openai.aliyuncs.com/compatible-mode/v1",
    "perplexity":  "https://api.perplexity.ai",
}


def _is_chat_model(model_id: str) -> bool:
    """Return True if the model ID looks like a chat/completion model."""
    m = model_id.lower()
    return not any(kw in m for kw in _EXCLUDE)


# ---------------------------------------------------------------------------
# Per-provider fetch functions
# ---------------------------------------------------------------------------

def _fetch_openai_compat(base_url: str, api_key: str) -> List[str]:
    """Fetch models from an OpenAI-compatible /models endpoint."""
    url = base_url.rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = httpx.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    ids = [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
    return sorted(m for m in ids if m and _is_chat_model(m))


def _fetch_anthropic(api_key: str) -> List[str]:
    """Fetch models from Anthropic /v1/models."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    resp = httpx.get("https://api.anthropic.com/v1/models", headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return sorted(m.get("id", "") for m in data.get("data", []) if isinstance(m, dict) and m.get("id"))


def _fetch_google(api_key: str) -> List[str]:
    """Fetch Gemini models from Google Generative AI /v1beta/models."""
    resp = httpx.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": api_key},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    models = []
    for m in data.get("models", []):
        name = m.get("name", "")
        if name.startswith("models/"):
            name = name[7:]
        if "generateContent" in m.get("supportedGenerationMethods", []):
            models.append(name)
    return sorted(models)


def _fetch_ollama(base_url: str) -> List[str]:
    """Fetch models from local Ollama /api/tags."""
    url = base_url.rstrip("/") + "/api/tags"
    resp = httpx.get(url, timeout=5.0)
    resp.raise_for_status()
    data = resp.json()
    return sorted(m.get("name", "") for m in data.get("models", []) if m.get("name"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_provider_models(
    provider: str,
    api_key: str,
    extra: Optional[Dict[str, str]] = None,
) -> Optional[List[str]]:
    """Fetch model list for a single provider.

    Returns a sorted list of model IDs, or None on failure / unsupported provider.
    """
    extra = extra or {}
    try:
        if provider == "anthropic":
            return _fetch_anthropic(api_key)
        if provider == "google":
            return _fetch_google(api_key)
        if provider == "ollama":
            return _fetch_ollama(extra.get("ollama_base_url", "http://localhost:11434"))
        if provider == "github_copilot":
            # Uses OAuth token stored in /data/oauth_copilot.json — no config API key
            from .github_copilot import _load_token_from_disk, _fetch_models_from_api
            token_data = _load_token_from_disk()
            if not token_data:
                return None
            copilot_token = token_data.get("access_token") or token_data.get("token", "")
            if not copilot_token:
                return None
            return _fetch_models_from_api(copilot_token)
        if provider == "custom":
            base = extra.get("custom_api_base", "")
            if not base or not api_key:
                return None
            return _fetch_openai_compat(base, api_key)
        if provider in _BASE_URLS:
            return _fetch_openai_compat(_BASE_URLS[provider], api_key)
    except Exception as e:
        logger.warning(f"model_fetcher [{provider}]: {e}")
    return None


def refresh_all_providers(
    provider_keys: Dict[str, str],
    extra: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Fetch latest model lists for all configured providers.

    Args:
        provider_keys: mapping of {provider_name: api_key}
        extra:         extra config values like ollama_base_url, custom_api_base

    Returns:
        {
            "updated": {provider: [model_id, ...]},
            "errors":  {provider: "error description"},
            "skipped": [provider, ...]
        }
    """
    extra = extra or {}
    updated: Dict[str, List[str]] = {}
    errors: Dict[str, str] = {}
    skipped: List[str] = []

    for provider, api_key in provider_keys.items():
        if provider in _NO_ENDPOINT:
            skipped.append(provider)
            continue
        if not api_key and provider != "ollama":
            skipped.append(provider)
            continue

        models = fetch_provider_models(provider, api_key, extra)
        if models is not None:
            updated[provider] = models
            logger.info(f"model_fetcher [{provider}]: {len(models)} models")
        else:
            errors[provider] = "fetch failed or endpoint not available"

    if updated:
        cache = load_cache()
        cache.update(updated)
        save_cache(cache)

    return {"updated": updated, "errors": errors, "skipped": skipped}


def load_cache() -> Dict[str, List[str]]:
    """Load persisted model lists from disk."""
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(data: Dict[str, List[str]]) -> None:
    """Persist model lists to disk."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"model_fetcher: cache save failed: {e}")
