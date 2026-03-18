"""Model service: manage model blocklists and NVIDIA model caching."""

import json
import os
import logging
import time
from typing import Optional

try:
    import model_catalog
    MODEL_CATALOG_AVAILABLE = True
except ImportError:
    MODEL_CATALOG_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---- NVIDIA Model Blocklist ----

# NVIDIA models that are known to fail (API errors, etc.)
NVIDIA_MODEL_BLOCKLIST: set[str] = set()

# NVIDIA models that have been successfully chat-tested (per current key)
NVIDIA_MODEL_TESTED_OK: set[str] = set()

# Generic provider tested-ok sets (for batch-tested API providers).
# Example: {"openrouter": {"openai/gpt-4o", ...}, "mistral": {...}}
PROVIDER_MODEL_TESTED_OK: dict[str, set[str]] = {}
# Generic provider uncertain sets (models returning transient/ambiguous errors
# during batch tests: timeouts, 5xx, non-invalid 4xx, auth/rate-limit, etc.).
PROVIDER_MODEL_UNCERTAIN: dict[str, set[str]] = {}

# NVIDIA models with uncertain test results.
NVIDIA_MODEL_UNCERTAIN: set[str] = set()

MODEL_BLOCKLIST_FILE = "/config/amira/model_blocklist.json"

# Cache for NVIDIA /v1/models discovery (to keep UI in sync with what's available for the current key)
_NVIDIA_MODELS_CACHE: dict[str, object] = {"ts": 0.0, "models": []}
_NVIDIA_MODELS_CACHE_TTL_SECONDS = 10 * 60


def load_model_blocklists() -> None:
    """Load persistent NVIDIA model blocklist from disk."""
    global NVIDIA_MODEL_BLOCKLIST, NVIDIA_MODEL_TESTED_OK, NVIDIA_MODEL_UNCERTAIN, PROVIDER_MODEL_TESTED_OK, PROVIDER_MODEL_UNCERTAIN
    try:
        if os.path.isfile(MODEL_BLOCKLIST_FILE):
            with open(MODEL_BLOCKLIST_FILE, "r") as f:
                data = json.load(f) or {}
            for provider, payload in (data.items() if isinstance(data, dict) else []):
                # Backward-compatible formats:
                # - {"provider": [blocked...]} legacy blocked-only
                # - {"provider": {"blocked": [...], "tested_ok": [...]} } preferred
                blocked: list[str] = []
                tested_ok: list[str] = []
                uncertain: list[str] = []
                if isinstance(payload, dict):
                    b = payload.get("blocked") or []
                    t = payload.get("tested_ok") or []
                    u = payload.get("uncertain") or []
                    if isinstance(b, list):
                        blocked = [m for m in b if isinstance(m, str) and m.strip()]
                    if isinstance(t, list):
                        tested_ok = [m for m in t if isinstance(m, str) and m.strip()]
                    if isinstance(u, list):
                        uncertain = [m for m in u if isinstance(m, str) and m.strip()]
                elif isinstance(payload, list):
                    blocked = [m for m in payload if isinstance(m, str) and m.strip()]

                if provider == "nvidia":
                    NVIDIA_MODEL_BLOCKLIST.update(blocked)
                    NVIDIA_MODEL_TESTED_OK.update(tested_ok)
                    NVIDIA_MODEL_UNCERTAIN.update(uncertain)
                else:
                    if tested_ok:
                        PROVIDER_MODEL_TESTED_OK.setdefault(provider, set()).update(tested_ok)
                    if uncertain:
                        PROVIDER_MODEL_UNCERTAIN.setdefault(provider, set()).update(uncertain)

            if NVIDIA_MODEL_BLOCKLIST or NVIDIA_MODEL_TESTED_OK or NVIDIA_MODEL_UNCERTAIN or PROVIDER_MODEL_TESTED_OK or PROVIDER_MODEL_UNCERTAIN:
                logger.debug(
                    "Loaded model lists: nvidia_blocked=%s nvidia_tested_ok=%s nvidia_uncertain=%s providers_tested_ok=%s providers_uncertain=%s",
                    len(NVIDIA_MODEL_BLOCKLIST),
                    len(NVIDIA_MODEL_TESTED_OK),
                    len(NVIDIA_MODEL_UNCERTAIN),
                    len(PROVIDER_MODEL_TESTED_OK),
                    len(PROVIDER_MODEL_UNCERTAIN),
                )
    except Exception as e:
        logger.warning(f"Could not load model blocklists: {e}")


def save_model_blocklists() -> None:
    """Persist NVIDIA model blocklist to disk."""
    try:
        os.makedirs(os.path.dirname(MODEL_BLOCKLIST_FILE), exist_ok=True)
        existing = {}
        if os.path.isfile(MODEL_BLOCKLIST_FILE):
            try:
                with open(MODEL_BLOCKLIST_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f) or {}
            except Exception:
                existing = {}

        payload = dict(existing) if isinstance(existing, dict) else {}
        # NVIDIA section (always dict shape)
        payload["nvidia"] = {
            "blocked": sorted(NVIDIA_MODEL_BLOCKLIST),
            "tested_ok": sorted(NVIDIA_MODEL_TESTED_OK),
            "uncertain": sorted(NVIDIA_MODEL_UNCERTAIN),
        }
        # Preserve blocked lists for non-NVIDIA and update tested_ok / uncertain if tracked.
        provider_union = set(PROVIDER_MODEL_TESTED_OK.keys()) | set(PROVIDER_MODEL_UNCERTAIN.keys())
        for provider in provider_union:
            if not provider or provider == "nvidia":
                continue
            tested_set = PROVIDER_MODEL_TESTED_OK.get(provider, set())
            uncertain_set = PROVIDER_MODEL_UNCERTAIN.get(provider, set())
            prev = payload.get(provider)
            blocked_prev: list[str] = []
            if isinstance(prev, dict):
                b = prev.get("blocked") or []
                if isinstance(b, list):
                    blocked_prev = [m for m in b if isinstance(m, str) and m.strip()]
            elif isinstance(prev, list):
                blocked_prev = [m for m in prev if isinstance(m, str) and m.strip()]
            payload[provider] = {
                "blocked": sorted(set(blocked_prev)),
                "tested_ok": sorted(set(tested_set)),
                "uncertain": sorted(set(uncertain_set)),
            }

        with open(MODEL_BLOCKLIST_FILE, "w") as f:
            json.dump(payload, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Could not save model blocklists: {e}")


def mark_nvidia_model_tested_ok(model_id: str) -> None:
    """Mark a NVIDIA model as successfully tested and persist it."""
    if not isinstance(model_id, str) or not model_id.strip():
        return
    model_id = model_id.strip()
    if model_id in NVIDIA_MODEL_BLOCKLIST:
        return
    NVIDIA_MODEL_TESTED_OK.add(model_id)
    if model_id in NVIDIA_MODEL_UNCERTAIN:
        NVIDIA_MODEL_UNCERTAIN.discard(model_id)
    save_model_blocklists()


def blocklist_nvidia_model(model_id: str) -> None:
    """Add a model to NVIDIA blocklist, persist it, and drop it from cache."""
    if not isinstance(model_id, str) or not model_id.strip():
        return
    model_id = model_id.strip()
    NVIDIA_MODEL_BLOCKLIST.add(model_id)
    if model_id in NVIDIA_MODEL_TESTED_OK:
        NVIDIA_MODEL_TESTED_OK.discard(model_id)
    if model_id in NVIDIA_MODEL_UNCERTAIN:
        NVIDIA_MODEL_UNCERTAIN.discard(model_id)
    try:
        cached = _NVIDIA_MODELS_CACHE.get("models") or []
        if isinstance(cached, list) and model_id in cached:
            _NVIDIA_MODELS_CACHE["models"] = [m for m in cached if m != model_id]
    except Exception:
        pass
    save_model_blocklists()


def blocklist_model(provider: str, model_id: str) -> None:
    """Add a model to the blocklist for a provider.

    NVIDIA: persisted via the dedicated NVIDIA_MODEL_BLOCKLIST mechanism.
    All other providers: delegated to ModelCatalog.remove_model() which
    handles in-memory removal, refresh-survival, and disk persistence.
    """
    if not isinstance(model_id, str) or not model_id.strip():
        return
    model_id = model_id.strip()
    if provider == "nvidia":
        blocklist_nvidia_model(model_id)
    else:
        # If a model becomes blocked, remove it from tested-ok set for this provider.
        if provider in PROVIDER_MODEL_TESTED_OK and model_id in PROVIDER_MODEL_TESTED_OK.get(provider, set()):
            try:
                PROVIDER_MODEL_TESTED_OK[provider].discard(model_id)
            except Exception:
                pass
            save_model_blocklists()
        if provider in PROVIDER_MODEL_UNCERTAIN and model_id in PROVIDER_MODEL_UNCERTAIN.get(provider, set()):
            try:
                PROVIDER_MODEL_UNCERTAIN[provider].discard(model_id)
            except Exception:
                pass
            save_model_blocklists()
        if MODEL_CATALOG_AVAILABLE:
            model_catalog.get_catalog().remove_model(provider, model_id)


def mark_provider_model_tested_ok(provider: str, model_id: str) -> None:
    """Mark a non-NVIDIA provider model as successfully tested and persist."""
    if not isinstance(provider, str) or not provider.strip():
        return
    if not isinstance(model_id, str) or not model_id.strip():
        return
    provider = provider.strip().lower()
    model_id = model_id.strip()
    if provider == "nvidia":
        mark_nvidia_model_tested_ok(model_id)
        return
    PROVIDER_MODEL_TESTED_OK.setdefault(provider, set()).add(model_id)
    if provider in PROVIDER_MODEL_UNCERTAIN and model_id in PROVIDER_MODEL_UNCERTAIN.get(provider, set()):
        PROVIDER_MODEL_UNCERTAIN[provider].discard(model_id)
    save_model_blocklists()


def mark_nvidia_model_uncertain(model_id: str) -> None:
    """Mark a NVIDIA model as uncertain test result and persist."""
    if not isinstance(model_id, str) or not model_id.strip():
        return
    model_id = model_id.strip()
    if model_id in NVIDIA_MODEL_BLOCKLIST:
        return
    if model_id in NVIDIA_MODEL_TESTED_OK:
        return
    NVIDIA_MODEL_UNCERTAIN.add(model_id)
    save_model_blocklists()


def mark_provider_model_uncertain(provider: str, model_id: str) -> None:
    """Mark a non-NVIDIA provider model as uncertain test result and persist."""
    if not isinstance(provider, str) or not provider.strip():
        return
    if not isinstance(model_id, str) or not model_id.strip():
        return
    provider = provider.strip().lower()
    model_id = model_id.strip()
    if provider == "nvidia":
        mark_nvidia_model_uncertain(model_id)
        return
    if model_id in PROVIDER_MODEL_TESTED_OK.get(provider, set()):
        return
    PROVIDER_MODEL_UNCERTAIN.setdefault(provider, set()).add(model_id)
    save_model_blocklists()


def _fetch_nvidia_models_live(nvidia_api_key: str) -> Optional[list[str]]:
    """Fetch available NVIDIA models from the OpenAI-compatible endpoint.

    Returns a sorted list of model IDs, or None if unavailable.
    """
    if not nvidia_api_key:
        return None
    try:
        import requests
        url = "https://integrate.api.nvidia.com/v1/models"
        headers = {"Authorization": f"Bearer {nvidia_api_key}"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        models: list[str] = []
        for item in (data.get("data") or []):
            if isinstance(item, dict):
                mid = item.get("id") or item.get("model")
                if isinstance(mid, str) and mid.strip():
                    models.append(mid.strip())
        models = sorted(set(models))
        return models or None
    except Exception as e:
        logger.warning(f"NVIDIA: unable to fetch /v1/models ({type(e).__name__}): {e}")
        return None


def get_nvidia_models_cached(nvidia_api_key: str) -> Optional[list[str]]:
    """Return cached NVIDIA model IDs, refreshing periodically."""
    if not nvidia_api_key:
        return None

    now = time.time()
    ts = float(_NVIDIA_MODELS_CACHE.get("ts") or 0.0)
    cached_models = _NVIDIA_MODELS_CACHE.get("models") or []
    if cached_models and (now - ts) < _NVIDIA_MODELS_CACHE_TTL_SECONDS:
        if NVIDIA_MODEL_BLOCKLIST:
            return [m for m in list(cached_models) if m not in NVIDIA_MODEL_BLOCKLIST]
        return list(cached_models)

    live = _fetch_nvidia_models_live(nvidia_api_key)
    if live:
        _NVIDIA_MODELS_CACHE["ts"] = now
        _NVIDIA_MODELS_CACHE["models"] = list(live)
        if NVIDIA_MODEL_BLOCKLIST:
            return [m for m in live if m not in NVIDIA_MODEL_BLOCKLIST]
        return live

    # Fallback to stale cache if present
    if cached_models:
        if NVIDIA_MODEL_BLOCKLIST:
            return [m for m in list(cached_models) if m not in NVIDIA_MODEL_BLOCKLIST]
        return list(cached_models)
    return None
