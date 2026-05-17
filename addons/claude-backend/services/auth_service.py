"""Auth service: API token management for Amira."""

import json
import logging
import os
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

_SETTINGS_FILE = "/config/amira/settings.json"
_TOKEN_KEY = "amira_api_token"

# Emergency bypass: AUTH_ENFORCED=false disables token check entirely
_AUTH_ENFORCED = os.environ.get("AUTH_ENFORCED", "true").lower() not in ("false", "0", "no")

# Paths always exempt from token auth (these have own auth mechanisms)
_AUTH_EXEMPT_PATHS = frozenset([
    "/api/whatsapp/webhook",  # Twilio HMAC-SHA1 signature
])

_cached_token: Optional[str] = None


def _load_raw() -> dict:
    try:
        if os.path.isfile(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_raw(data: dict) -> None:
    os.makedirs(os.path.dirname(_SETTINGS_FILE), exist_ok=True)
    tmp = _SETTINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _SETTINGS_FILE)


def get_or_create_token() -> str:
    """Return stored API token or generate + persist a new one."""
    global _cached_token
    if _cached_token:
        return _cached_token
    settings = _load_raw()
    token = settings.get(_TOKEN_KEY, "")
    if not token:
        token = secrets.token_urlsafe(32)
        settings[_TOKEN_KEY] = token
        try:
            _save_raw(settings)
            logger.info("Amira: new API token generated and saved")
        except Exception as e:
            logger.warning(f"Amira: could not persist API token: {e}")
    _cached_token = token
    return token


def invalidate_cache() -> None:
    """Force next get_or_create_token() to re-read disk (call after settings save)."""
    global _cached_token
    _cached_token = None


def validate_token(token: Optional[str]) -> bool:
    """Return True if token matches stored API token."""
    if not _AUTH_ENFORCED:
        return True
    if not token:
        return False
    stored = _load_raw().get(_TOKEN_KEY, "")
    if not stored:
        return True  # no token configured → open (migration path for existing installs)
    return secrets.compare_digest(token, stored)


def is_ingress_request(request) -> bool:
    """Return True if request comes through HA ingress proxy (trusted)."""
    return bool(request.headers.get("X-Ingress-Path"))


def is_exempt_path(path: str) -> bool:
    """Return True if path is exempt from token auth."""
    return path in _AUTH_EXEMPT_PATHS
