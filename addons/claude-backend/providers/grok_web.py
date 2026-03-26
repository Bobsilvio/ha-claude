"""Grok Web provider - unofficial session-based access to grok.com.

⚠️ UNSTABLE: uses private web endpoints and may break without notice.
Use the official xAI API provider for production workloads.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, Generator, List, Optional

from .enhanced import EnhancedProvider
from .rate_limiter import get_rate_limit_coordinator
try:
    from .grok_web_advanced import (
        init_handshake as _adv_init_handshake,
        build_conversation_headers as _adv_build_conversation_headers,
        available as _adv_available,
    )
    ADVANCED_AVAILABLE = bool(_adv_available())
except Exception:
    _adv_init_handshake = None
    _adv_build_conversation_headers = None
    ADVANCED_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    HTTPX_AVAILABLE = False
    logger.error("httpx not installed - required for Grok Web")

try:
    from curl_cffi import requests as cffi_requests
    CFFI_AVAILABLE = True
except Exception:
    cffi_requests = None
    CFFI_AVAILABLE = False

_BASE_URL = "https://grok.com"
_CHAT_URL = f"{_BASE_URL}/rest/app-chat/conversations/new"
_CONV_LIST_URL = f"{_BASE_URL}/rest/app-chat/conversations"
_RATE_LIMITS_URL = f"{_BASE_URL}/rest/rate-limits"
_TOKEN_FILE = "/data/session_grok_web.json"

_HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Priority": "u=4",
    "Origin": _BASE_URL,
    "Referer": f"{_BASE_URL}/",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Site": "same-origin",
    "DNT": "1",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) "
        "Gecko/20100101 Firefox/148.0"
    ),
}

_stored_session: Optional[Dict[str, Any]] = None
_discovery_cache: Dict[str, Any] = {"models": [], "ts": 0.0}
_DISCOVERY_TTL_SECONDS = 3600
_warned_missing_advanced = False

# Candidate models for session-scoped discovery via /rest/rate-limits.
# Keep web aliases first because they are what users pick in the UI.
_DISCOVERY_CANDIDATES: List[str] = [
    "grok-3",
    "grok-3-mini",
    "grok-3-thinking",
    "grok-4",
    "grok-4-thinking",
    "grok-4-heavy",
    "grok-4.1-mini",
    "grok-4.1-fast",
    "grok-4.1-expert",
    "grok-4.1-thinking",
    "grok-4.20-beta",
    "grok-code-fast-1",
    # Compatibility candidates
    "grok-4.20-multi-agent-0309",
    "grok-4.20-0309-reasoning",
    "grok-4.20-0309-non-reasoning",
    "grok-4-fast-reasoning",
    "grok-4-fast-non-reasoning",
    "grok-4-1-fast-reasoning",
    "grok-4-1-fast-non-reasoning",
    "grok-4-0709",
]
_DISCOVERY_MAX_PROBES = 10
_IMPERSONATE_TARGETS = [
    # Prefer Firefox first (matches your browser flow better)
    "firefox135",
    "firefox133",
    "firefox131",
    # Fallbacks
    "chrome136",
    "chrome131",
    "chrome124",
    "chrome120",
    "safari18_0",
]


def _advanced_missing_deps() -> List[str]:
    missing: List[str] = []
    if not CFFI_AVAILABLE:
        missing.append("curl_cffi")
    if not ADVANCED_AVAILABLE:
        missing.extend(["beautifulsoup4", "coincurve"])
    out: List[str] = []
    seen = set()
    for m in missing:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _parse_cookie_string(raw: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not raw:
        return out
    for part in raw.split(";"):
        p = (part or "").strip()
        if not p or "=" not in p:
            continue
        k, v = p.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k:
            out[k] = v
    return out


def _load_session() -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(_TOKEN_FILE):
            with open(_TOKEN_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"GrokWeb: could not load session: {e}")
    return None


def _save_session(data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_TOKEN_FILE), exist_ok=True)
        with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"GrokWeb: could not save session: {e}")


def _cookie_header(sso_token: str, cf_clearance: str = "", cf_cookies: str = "") -> str:
    token = (sso_token or "").strip()
    if token.startswith("sso="):
        token = token[4:]
    if ";" in token and "=" in token:
        pairs = _parse_cookie_string(token)
        token = (pairs.get("sso") or pairs.get("sso-rw") or "").strip()
    cookie = f"sso={token}; sso-rw={token}"

    # Prefer full cookie fragment when available.
    full = (cf_cookies or "").strip()
    if full:
        pairs = _parse_cookie_string(full)
        # Never duplicate/override sso cookies from external fragment.
        pairs.pop("sso", None)
        pairs.pop("sso-rw", None)
        if pairs:
            cookie += "; " + "; ".join(f"{k}={v}" for k, v in pairs.items())
            return cookie

    cf = (cf_clearance or "").strip()
    if cf:
        if ";" in cf and "=" in cf:
            pairs = _parse_cookie_string(cf)
            pairs.pop("sso", None)
            pairs.pop("sso-rw", None)
            if pairs:
                cookie += "; " + "; ".join(f"{k}={v}" for k, v in pairs.items())
        elif "=" in cf:
            cookie += f"; {cf.lstrip('; ')}"
        else:
            cookie += f"; cf_clearance={cf}"
    return cookie


def _auth_headers(sso_token: str, cf_clearance: str = "", cf_cookies: str = "") -> Dict[str, str]:
    h = dict(_HEADERS)
    h["x-statsig-id"] = str(uuid.uuid4())
    h["x-xai-request-id"] = str(uuid.uuid4())
    h["Cookie"] = _cookie_header(sso_token, cf_clearance, cf_cookies)
    return h


_stored_session = _load_session()


def store_session(sso_token: str, cf_clearance: str = "", cf_cookies: str = "") -> Dict[str, Any]:
    """Validate and persist Grok Web session token."""
    global _stored_session, _warned_missing_advanced

    sso_token = (sso_token or "").strip()
    cf_clearance = (cf_clearance or "").strip()
    cf_cookies = (cf_cookies or "").strip()

    # Allow pasting full cookie header in either field.
    merged_pairs: Dict[str, str] = {}
    if ";" in sso_token and "=" in sso_token:
        merged_pairs.update(_parse_cookie_string(sso_token))
    if ";" in cf_clearance and "=" in cf_clearance:
        merged_pairs.update(_parse_cookie_string(cf_clearance))
    if cf_cookies:
        merged_pairs.update(_parse_cookie_string(cf_cookies))
    if merged_pairs:
        sso_token = (merged_pairs.get("sso") or merged_pairs.get("sso-rw") or sso_token).strip()
        if "cf_clearance" in merged_pairs:
            cf_clearance = merged_pairs["cf_clearance"].strip()
        # Keep all non-SSO cookies (cf + any additional anti-bot cookies).
        merged_pairs.pop("sso", None)
        merged_pairs.pop("sso-rw", None)
        cf_cookies = "; ".join(f"{k}={v}" for k, v in merged_pairs.items())

    if not sso_token:
        raise ValueError("Missing sso_token")

    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx not installed")
    if not ADVANCED_AVAILABLE and not _warned_missing_advanced:
        missing = _advanced_missing_deps()
        logger.warning(
            "GrokWeb: advanced handshake deps missing. Install: %s",
            ", ".join(missing or ["curl_cffi", "beautifulsoup4", "coincurve"]),
        )
        _warned_missing_advanced = True

    # NOTE:
    # /rest/rate-limits is sensitive to modelName and can return 404 "Model not found"
    # even with a valid session. Probe multiple known model ids and accept the first 200.
    probe_models = [
        # Web-style first
        "grok-4.1-fast",
        "grok-4",
        "grok-3",
        "grok-3-mini",
        # API/internals as compatibility probes
        "grok-4-1-fast-non-reasoning",
        "grok-4-0709",
    ]
    last_status = 0
    last_body = ""
    saw_model_not_found = False
    try:
        for _m in probe_models:
            payload = {"requestKind": "DEFAULT", "modelName": _m}
            r = httpx.post(
                _RATE_LIMITS_URL,
                headers=_auth_headers(sso_token, cf_clearance, cf_cookies),
                json=payload,
                timeout=15.0,
                follow_redirects=True,
            )
            last_status = r.status_code
            try:
                last_body = (r.text or "")[:240]
            except Exception:
                last_body = ""

            if r.status_code == 200:
                break
            # Explicit auth failures: stop early
            if r.status_code in (401, 403):
                raise RuntimeError(
                    f"Grok Web auth check failed (HTTP {r.status_code}). {last_body}"
                )
            # 404 on model: token may still be valid with a different account/model set
            if r.status_code == 404:
                body_l = (last_body or "").lower()
                if "model not found" in body_l or '"code":5' in body_l:
                    saw_model_not_found = True
            # keep trying next probe model
        else:
            # If we only got model-not-found across probes (no 401/403), accept session.
            # Actual model resolution is retried in stream_chat across aliases/candidates.
            if not saw_model_not_found:
                raise RuntimeError(
                    f"Grok Web auth check failed (HTTP {last_status}). {last_body}"
                )
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(f"Grok Web unreachable: {e}") from e

    # Second-stage validation: ensure chat endpoint is actually usable.
    # Some sessions can pass /rate-limits but still fail /app-chat with 403.
    chat_ok, chat_msg = _probe_chat_access(sso_token, cf_clearance, cf_cookies, probe_models)
    if not chat_ok:
        raise RuntimeError(chat_msg)

    data = {
        "sso_token": sso_token,
        "cf_clearance": cf_clearance,
        "cf_cookies": cf_cookies,
        "stored_at": int(time.time()),
        "ok": True,
    }
    _stored_session = data
    _save_session(data)
    try:
        discover_available_models(force=True)
    except Exception:
        pass
    logger.info("GrokWeb: session stored")
    return data


def get_session_status() -> Dict[str, Any]:
    s = _stored_session
    if not s:
        return {"configured": False}
    age_days = (int(time.time()) - s.get("stored_at", 0)) // 86400
    dedup_missing = _advanced_missing_deps()
    return {
        "configured": True,
        "age_days": age_days,
        "has_cf_clearance": bool(s.get("cf_clearance")),
        "has_cf_cookies": bool(s.get("cf_cookies")),
        "advanced_ready": bool(ADVANCED_AVAILABLE),
        "missing_deps": dedup_missing,
    }


def clear_session() -> None:
    global _stored_session, _discovery_cache
    _stored_session = None
    _discovery_cache = {"models": [], "ts": 0.0}
    try:
        if os.path.exists(_TOKEN_FILE):
            os.remove(_TOKEN_FILE)
    except Exception:
        pass


def _build_probe_payload(user_text: str, model: str) -> Dict[str, Any]:
    return {
        "deviceEnvInfo": {
            "darkModeEnabled": False,
            "devicePixelRatio": 2,
            "screenHeight": 1080,
            "screenWidth": 1920,
            "viewportHeight": 900,
            "viewportWidth": 1200,
        },
        "disableMemory": False,
        "disableSearch": False,
        "disableSelfHarmShortCircuit": False,
        "disableTextFollowUps": False,
        "enableImageGeneration": False,
        "enableImageStreaming": False,
        "enableSideBySide": False,
        "fileAttachments": [],
        "forceConcise": True,
        "forceSideBySide": False,
        "imageAttachments": [],
        "imageGenerationCount": 1,
        "isAsyncChat": False,
        "isReasoning": False,
        "message": user_text,
        "modelMode": None,
        "modelName": model,
        "responseMetadata": {"requestModelDetails": {"modelId": model}},
        "returnImageBytes": False,
        "returnRawGrokInXaiRequest": False,
        "sendFinalMetadata": False,
        "temporary": True,
        "toolOverrides": {},
    }


def _probe_chat_access(
    sso_token: str,
    cf_clearance: str,
    cf_cookies: str,
    models: List[str],
) -> tuple[bool, str]:
    """Validate that /rest/app-chat endpoint accepts current session."""
    headers = _auth_headers(sso_token, cf_clearance, cf_cookies)
    impersonate_targets = _IMPERSONATE_TARGETS

    if ADVANCED_AVAILABLE and _adv_init_handshake and _adv_build_conversation_headers:
        try:
            cookie_hdr = _cookie_header(sso_token, cf_clearance, cf_cookies)
            adv_state = None
            for _imp in ("chrome136", "firefox133"):
                adv_state = _adv_init_handshake(cookie_hdr, impersonate=_imp)
                if adv_state:
                    logger.info("GrokWeb: advanced probe handshake initialized via %s", _imp)
                    break
            if adv_state:
                payload = _build_probe_payload("ping", models[0] if models else "grok-4")
                path = "/rest/app-chat/conversations/new"
                adv_headers = _adv_build_conversation_headers(adv_state, path)
                r = adv_state.session.post(f"{_BASE_URL}{path}", headers=adv_headers, json=payload, timeout=45)
                if getattr(r, "status_code", 0) == 200:
                    return True, ""
                logger.warning(
                    "GrokWeb: advanced probe returned HTTP %s",
                    getattr(r, "status_code", 0),
                )
        except Exception:
            pass

    if CFFI_AVAILABLE:
        saw_403 = False
        last_status = 0
        last_body = ""
        try:
            for model in models:
                payload = _build_probe_payload("ping", model)
                for imp in impersonate_targets:
                    session = None
                    try:
                        session = cffi_requests.Session(impersonate=imp)
                        resp = session.post(_CHAT_URL, headers=headers, json=payload, timeout=30)
                    except Exception:
                        continue
                    finally:
                        if session and hasattr(session, "close"):
                            try:
                                session.close()
                            except Exception:
                                pass

                    last_status = getattr(resp, "status_code", 0) or 0
                    try:
                        last_body = (resp.text or "")[:240]
                    except Exception:
                        last_body = ""

                    if last_status == 200:
                        return True, ""
                    if last_status == 401:
                        return False, "Grok Web chat auth failed (HTTP 401). Reconnect with fresh cookies."
                    if last_status == 403:
                        saw_403 = True
                        continue
                    low = (last_body or "").lower()
                    if last_status == 404 and ("model not found" in low or '"code":5' in low):
                        break
            if saw_403:
                ok_existing = _probe_existing_conversation_access(headers)
                if ok_existing:
                    return True, ""
                return False, (
                    "Grok Web chat blocked (HTTP 403). Cloudflare/browser fingerprint rejected. "
                    "Reconnect with fresh sso + cf_clearance from the same network as Home Assistant "
                    "(you can paste full Cloudflare cookies in cf_clearance/cf_cookies)."
                )
            return False, f"Grok Web chat probe failed (HTTP {last_status}). {last_body}"
        except Exception as e:
            return False, f"Grok Web chat probe unreachable: {e}"

    if not HTTPX_AVAILABLE:
        return False, "Neither curl_cffi nor httpx is available"

    timeout = httpx.Timeout(connect=12.0, read=20.0, write=20.0, pool=10.0)
    last_status = 0
    last_body = ""
    try:
        with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
            for model in models:
                payload = _build_probe_payload("ping", model)
                with client.stream("POST", _CHAT_URL, json=payload) as resp:
                    last_status = resp.status_code
                    if resp.status_code == 200:
                        return True, ""
                    try:
                        last_body = resp.read().decode("utf-8", errors="ignore")[:240]
                    except Exception:
                        last_body = ""
                    if resp.status_code == 403:
                        # /conversations/new can be blocked while existing-conversation
                        # endpoints still work for some sessions.
                        if _probe_existing_conversation_access(headers):
                            return True, ""
                    if resp.status_code in (401, 403):
                        hint = (
                            "Grok Web chat auth failed (HTTP "
                            f"{resp.status_code}). Session/cookies not sufficient for chat. "
                            "Try reconnecting with fresh sso and cf_clearance from the same browser session."
                        )
                        if resp.status_code == 403 and not CFFI_AVAILABLE:
                            hint += (
                                " Also: curl_cffi is not installed, so browser-fingerprint fallback is unavailable. "
                                "Rebuild/update the addon to install curl_cffi."
                            )
                        return False, hint
                    low = (last_body or "").lower()
                    if resp.status_code == 404 and ("model not found" in low or '"code":5' in low):
                        continue
        return False, f"Grok Web chat probe failed (HTTP {last_status}). {last_body}"
    except Exception as e:
        return False, f"Grok Web chat probe unreachable: {e}"


def _probe_existing_conversation_access(headers: Dict[str, str]) -> bool:
    """Check if session can access an existing conversation flow."""
    if not HTTPX_AVAILABLE:
        return False
    timeout = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=8.0)
    try:
        with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
            r = client.get(_CONV_LIST_URL, params={"pageSize": 1})
            return r.status_code == 200
    except Exception:
        return False


def _resolve_existing_conversation_context(
    client: "httpx.Client",
) -> tuple[Optional[str], Optional[str], str]:
    """Return (conversation_id, parent_response_id, error_message)."""
    try:
        r = client.get(_CONV_LIST_URL, params={"pageSize": 1})
        if r.status_code != 200:
            body = (r.text or "")[:240]
            return None, None, f"Grok Web conversations list failed (HTTP {r.status_code}): {body}"
        data = r.json() if r.text else {}
        conversations = data.get("conversations") or []
        if not conversations:
            return None, None, (
                "Grok Web has no existing conversations. Open grok.com and send one message first."
            )
        conv_id = (conversations[0] or {}).get("conversationId")
        if not conv_id:
            return None, None, "Grok Web conversation id missing in list response."

        rn_url = f"{_BASE_URL}/rest/app-chat/conversations/{conv_id}/response-node"
        rr = client.get(rn_url, params={"includeThreads": "true"})
        if rr.status_code != 200:
            body = (rr.text or "")[:240]
            return None, None, f"Grok Web response-node failed (HTTP {rr.status_code}): {body}"
        rr_data = rr.json() if rr.text else {}
        nodes = rr_data.get("responseNodes") or []
        if not nodes:
            return None, None, "Grok Web response-node list is empty."

        parent_id = None
        for n in reversed(nodes):
            if (n or {}).get("sender") == "assistant" and (n or {}).get("responseId"):
                parent_id = n.get("responseId")
                break
        if not parent_id:
            parent_id = (nodes[-1] or {}).get("responseId")
        if not parent_id:
            return None, None, "Grok Web parent response id missing."
        return conv_id, parent_id, ""
    except Exception as e:
        return None, None, f"Grok Web conversation context error: {e}"


def _build_existing_response_payload(user_text: str, parent_response_id: str) -> Dict[str, Any]:
    """Build payload for /conversations/{id}/responses endpoint."""
    return {
        "message": user_text,
        "parentResponseId": parent_response_id,
        "disableSearch": False,
        "enableImageGeneration": True,
        "imageAttachments": [],
        "returnImageBytes": False,
        "returnRawGrokInXaiRequest": False,
        "fileAttachments": [],
        "enableImageStreaming": True,
        "imageGenerationCount": 2,
        "forceConcise": False,
        "toolOverrides": {},
        "enableSideBySide": True,
        "sendFinalMetadata": True,
        "isReasoning": False,
        "metadata": {"request_metadata": {}},
        "disableTextFollowUps": False,
        "isFromGrokFiles": False,
        "disableMemory": False,
        "forceSideBySide": False,
        "isAsyncChat": False,
        "skipCancelCurrentInflightRequests": False,
        "isRegenRequest": False,
        "disableSelfHarmShortCircuit": False,
        "deviceEnvInfo": {
            "darkModeEnabled": False,
            "devicePixelRatio": 2,
            "screenWidth": 1920,
            "screenHeight": 1080,
            "viewportWidth": 1200,
            "viewportHeight": 900,
        },
        "modeId": "auto",
        "enable420": False,
    }


def discover_available_models(force: bool = False) -> List[str]:
    """Discover models available for current Grok Web session.

    Best-effort approach:
    - Probes /rest/rate-limits for each candidate model.
    - Keeps models that return HTTP 200.
    - Treats 404 'Model not found' as unavailable and skips.
    - Aborts on 401/403 (invalid/expired session).
    """
    global _discovery_cache

    if not HTTPX_AVAILABLE:
        return []
    s = _stored_session
    if not s or not s.get("sso_token"):
        return []

    now = time.time()
    cached_models = list(_discovery_cache.get("models") or [])
    cached_ts = float(_discovery_cache.get("ts") or 0.0)
    if not force and cached_models and (now - cached_ts) < _DISCOVERY_TTL_SECONDS:
        return cached_models

    headers = _auth_headers(
        s["sso_token"],
        s.get("cf_clearance", ""),
        s.get("cf_cookies", ""),
    )
    timeout = httpx.Timeout(connect=8.0, read=12.0, write=10.0, pool=8.0)
    found: List[str] = []
    try:
        with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
            for idx, model in enumerate(_DISCOVERY_CANDIDATES):
                if idx >= _DISCOVERY_MAX_PROBES:
                    break
                payload = {"requestKind": "DEFAULT", "modelName": model}
                try:
                    resp = client.post(_RATE_LIMITS_URL, json=payload)
                except Exception:
                    continue

                if resp.status_code in (401, 403):
                    logger.warning("GrokWeb discovery: unauthorized session")
                    break
                if resp.status_code == 200:
                    found.append(model)
                    continue
                if resp.status_code == 404:
                    body = ""
                    try:
                        body = (resp.text or "").lower()
                    except Exception:
                        body = ""
                    if "model not found" in body or '"code":5' in body:
                        continue
                # Other statuses are ignored and not considered available.
    except Exception as e:
        logger.debug(f"GrokWeb discovery failed: {e}")

    # Deduplicate preserving order
    deduped: List[str] = []
    seen = set()
    for m in found:
        if m not in seen:
            seen.add(m)
            deduped.append(m)

    # Cache result; if discovery fails keep previous cache as fallback.
    if deduped:
        _discovery_cache = {"models": deduped, "ts": now}
        return deduped
    if cached_models:
        return cached_models
    return []


class GrokWebProvider(EnhancedProvider):
    """Unofficial Grok Web provider (session-token based)."""

    # Web/UI model aliases -> candidate IDs to try on grok.com reverse endpoint.
    # First item should be the literal user-facing name for best compatibility.
    _MODEL_CANDIDATES: Dict[str, List[str]] = {
        # Web-style names (from reverse projects / UI)
        "grok-3-thinking": ["grok-3-thinking", "grok-3"],
        "grok-4": ["grok-4", "grok-4-0709"],
        "grok-4-thinking": ["grok-4-thinking", "grok-4-fast-reasoning", "grok-4.20-0309-reasoning"],
        "grok-4-heavy": ["grok-4-heavy", "grok-4.20-multi-agent-0309"],
        "grok-4.1-mini": ["grok-4.1-mini", "grok-3-mini"],
        "grok-4.1-fast": ["grok-4.1-fast", "grok-4-1-fast-non-reasoning"],
        "grok-4.1-expert": ["grok-4.1-expert", "grok-4.20-multi-agent-0309"],
        "grok-4.1-thinking": ["grok-4.1-thinking", "grok-4-1-fast-reasoning"],
        "grok-4.20-beta": ["grok-4.20-beta", "grok-4.20-0309-non-reasoning", "grok-4.20-multi-agent-0309"],
        # API-style names (already supported)
        "grok-code-fast-1": ["grok-code-fast-1"],
        "grok-4.20-multi-agent-0309": ["grok-4.20-multi-agent-0309"],
        "grok-4.20-0309-reasoning": ["grok-4.20-0309-reasoning"],
        "grok-4.20-0309-non-reasoning": ["grok-4.20-0309-non-reasoning"],
        "grok-4-fast-reasoning": ["grok-4-fast-reasoning"],
        "grok-4-fast-non-reasoning": ["grok-4-fast-non-reasoning"],
        "grok-4-1-fast-reasoning": ["grok-4-1-fast-reasoning"],
        "grok-4-1-fast-non-reasoning": ["grok-4-1-fast-non-reasoning"],
        "grok-4-0709": ["grok-4-0709"],
        "grok-3-mini": ["grok-3-mini"],
        "grok-3": ["grok-3"],
        # Dot/dash alias normalization helpers
        "grok-4-1-fast": ["grok-4.1-fast", "grok-4-1-fast-non-reasoning"],
        "grok-4-1-thinking": ["grok-4.1-thinking", "grok-4-1-fast-reasoning"],
        "grok-4-1-mini": ["grok-4.1-mini", "grok-3-mini"],
        "grok-4-1-expert": ["grok-4.1-expert", "grok-4.20-multi-agent-0309"],
    }

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key, model)
        self.rate_limiter = get_rate_limit_coordinator().get_limiter("grok_web")

    @staticmethod
    def get_provider_name() -> str:
        return "grok_web"

    def validate_credentials(self) -> bool:
        s = _stored_session
        return bool(s and s.get("sso_token"))

    def get_available_models(self) -> List[str]:
        discovered = discover_available_models(force=False)
        if discovered:
            return discovered

        return [
            # Web-style aliases
            "grok-3-thinking",
            "grok-4",
            "grok-4-thinking",
            "grok-4-heavy",
            "grok-4.1-mini",
            "grok-4.1-fast",
            "grok-4.1-expert",
            "grok-4.1-thinking",
            "grok-4.20-beta",
            # API-style ids
            "grok-code-fast-1",
            "grok-4.20-multi-agent-0309",
            "grok-4.20-0309-reasoning",
            "grok-4.20-0309-non-reasoning",
            "grok-4-fast-reasoning",
            "grok-4-fast-non-reasoning",
            "grok-4-1-fast-reasoning",
            "grok-4-1-fast-non-reasoning",
            "grok-4-0709",
            "grok-3-mini",
            "grok-3",
        ]

    def _resolve_model_candidates(self) -> List[str]:
        selected = (self.model or "grok-4.1-fast").strip()
        candidates = list(self._MODEL_CANDIDATES.get(selected, [selected]))
        # Last-resort fallback to a known good modern default
        if "grok-4-1-fast-non-reasoning" not in candidates:
            candidates.append("grok-4-1-fast-non-reasoning")
        # Deduplicate preserving order
        out: List[str] = []
        seen = set()
        for m in candidates:
            key = (m or "").strip()
            if key and key not in seen:
                seen.add(key)
                out.append(key)
        return out

    @staticmethod
    def _build_payload(user_text: str, model: str) -> Dict[str, Any]:
        return {
            "deviceEnvInfo": {
                "darkModeEnabled": False,
                "devicePixelRatio": 2,
                "screenHeight": 1080,
                "screenWidth": 1920,
                "viewportHeight": 900,
                "viewportWidth": 1200,
            },
            "disableMemory": False,
            "disableSearch": False,
            "disableSelfHarmShortCircuit": False,
            "disableTextFollowUps": False,
            "enableImageGeneration": True,
            "enableImageStreaming": False,
            "enableSideBySide": True,
            "fileAttachments": [],
            "forceConcise": False,
            "forceSideBySide": False,
            "imageAttachments": [],
            "imageGenerationCount": 1,
            "isAsyncChat": False,
            "isReasoning": False,
            "message": user_text,
            "modelMode": None,
            "modelName": model,
            "responseMetadata": {"requestModelDetails": {"modelId": model}},
            "returnImageBytes": False,
            "returnRawGrokInXaiRequest": False,
            "sendFinalMetadata": True,
            "temporary": True,
            "toolOverrides": {},
        }

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        yield from self.stream_chat(messages, intent_info)

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        if not HTTPX_AVAILABLE:
            yield {"type": "error", "message": "httpx not installed"}
            return

        s = _stored_session
        if not s or not s.get("sso_token"):
            yield {
                "type": "error",
                "message": "Grok Web: not authenticated. Use the 🔑 button to connect.",
            }
            return

        can_req, wait = self.rate_limiter.can_request()
        if not can_req:
            raise RuntimeError(f"Rate limited. Wait {wait:.0f}s")
        self.rate_limiter.record_request()

        from providers.tool_simulator import flatten_tool_messages, get_simulator_system_prompt

        msgs = flatten_tool_messages(messages)
        user_text = ""
        for m in reversed(msgs):
            if (m.get("role") or "") == "user":
                c = m.get("content")
                if isinstance(c, str):
                    user_text = c.strip()
                elif isinstance(c, list):
                    parts = []
                    for p in c:
                        if isinstance(p, dict) and p.get("type") == "text":
                            t = p.get("text")
                            if isinstance(t, str) and t.strip():
                                parts.append(t.strip())
                    user_text = "\n".join(parts).strip()
                break
        if not user_text:
            user_text = "Hi"

        try:
            intent_name_local = (intent_info or {}).get("intent", "")
            tool_schemas = (intent_info or {}).get("tool_schemas") or []
            intent_base_prompt = (intent_info or {}).get("prompt", "")
            sim_prompt = get_simulator_system_prompt(tool_schemas)
            if (intent_info or {}).get("active_skill"):
                # Skill mode: only SKILL.md instructions needed — no tool simulator.
                prepend = (intent_base_prompt.strip() + "\n\n") if intent_base_prompt else ""
            elif intent_name_local == "create_html_dashboard":
                prepend = (
                    (intent_base_prompt.strip() + "\n\n") if intent_base_prompt else ""
                ) + (
                    "HTML DASHBOARD MODE:\n"
                    "- Return a COMPLETE HTML page in one response (prefer fenced ```html block).\n"
                    "- Do NOT output YAML/Lovelace card configs.\n"
                )
            else:
                prepend = ((intent_base_prompt.strip() + "\n\n") if intent_base_prompt else "") + sim_prompt
            if prepend.strip():
                user_text = (
                    "[SYSTEM INSTRUCTIONS - MUST FOLLOW]\n"
                    + prepend.strip()
                    + "\n[/SYSTEM INSTRUCTIONS]\n\n"
                    + user_text
                ).strip()
        except Exception as _sim_err:
            logger.debug(f"GrokWeb: simulator prompt injection skipped: {_sim_err}")

        model_candidates = self._resolve_model_candidates()
        headers = _auth_headers(
            s["sso_token"],
            s.get("cf_clearance", ""),
            s.get("cf_cookies", ""),
        )

        last_text = ""
        streamed = False
        chosen_model = ""
        last_http_status = 0
        last_http_body = ""
        _timeout = httpx.Timeout(connect=15.0, read=40.0, write=30.0, pool=20.0)
        impersonate_targets = _IMPERSONATE_TARGETS
        cookie_header_for_adv = _cookie_header(
            s["sso_token"],
            s.get("cf_clearance", ""),
            s.get("cf_cookies", ""),
        )
        adv_state = None
        if ADVANCED_AVAILABLE and _adv_init_handshake and _adv_build_conversation_headers:
            try:
                for _imp in ("chrome136", "firefox133"):
                    adv_state = _adv_init_handshake(cookie_header_for_adv, impersonate=_imp)
                    if adv_state:
                        logger.info("GrokWeb: advanced handshake initialized via %s", _imp)
                        break
                if not adv_state:
                    logger.warning("GrokWeb: advanced handshake unavailable for current session, using fallback flow")
            except Exception as _adv_e:
                logger.warning(f"GrokWeb: advanced handshake init failed: {_adv_e}")
        else:
            missing = _advanced_missing_deps()
            logger.warning(
                "GrokWeb: advanced handshake dependencies unavailable (missing: %s)",
                ", ".join(missing or ["curl_cffi", "beautifulsoup4", "coincurve"]),
            )
        try:
            with httpx.Client(headers=headers, timeout=_timeout, follow_redirects=True) as client:
                for model in model_candidates:
                    payload = self._build_payload(user_text, model)
                    logger.info("GrokWeb: trying model candidate '%s'", model)

                    if adv_state and _adv_build_conversation_headers:
                        try:
                            adv_path = "/rest/app-chat/conversations/new"
                            adv_headers = _adv_build_conversation_headers(adv_state, adv_path)
                            adv_resp = adv_state.session.post(
                                f"{_BASE_URL}{adv_path}",
                                headers=adv_headers,
                                json=payload,
                                stream=True,
                                timeout=90,
                            )
                            last_http_status = getattr(adv_resp, "status_code", 0) or 0
                            if last_http_status == 200:
                                chosen_model = model
                                for line in adv_resp.iter_lines():
                                    if line is None:
                                        continue
                                    if isinstance(line, bytes):
                                        line = line.decode("utf-8", errors="ignore")
                                    raw = line.strip()
                                    if not raw:
                                        continue
                                    try:
                                        data = json.loads(raw)
                                    except Exception:
                                        continue
                                    response = ((data or {}).get("result") or {}).get("response") or {}
                                    token = response.get("token")
                                    if isinstance(token, str) and token:
                                        streamed = True
                                        yield {"type": "text", "text": token, "content": token}
                                    model_response = response.get("modelResponse") or {}
                                    full_msg = model_response.get("message")
                                    if isinstance(full_msg, str) and full_msg:
                                        if full_msg != last_text:
                                            delta = full_msg[len(last_text):] if full_msg.startswith(last_text) else full_msg
                                            if delta:
                                                streamed = True
                                                yield {"type": "text", "text": delta, "content": delta}
                                            last_text = full_msg
                                break
                        except Exception as _adv_req_err:
                            logger.debug(f"GrokWeb: advanced request failed: {_adv_req_err}")

                    used_cffi = False
                    if CFFI_AVAILABLE:
                        for imp in impersonate_targets:
                            session = None
                            resp = None
                            try:
                                session = cffi_requests.Session(impersonate=imp)
                                resp = session.post(
                                    _CHAT_URL,
                                    headers=headers,
                                    json=payload,
                                    stream=True,
                                    timeout=75,
                                )
                            except Exception:
                                continue

                            last_http_status = getattr(resp, "status_code", 0) or 0
                            if last_http_status == 403:
                                logger.warning("GrokWeb: %s got 403, trying next fingerprint", imp)
                                if session and hasattr(session, "close"):
                                    try:
                                        session.close()
                                    except Exception:
                                        pass
                                continue

                            used_cffi = True
                            if last_http_status in (401,):
                                if session and hasattr(session, "close"):
                                    try:
                                        session.close()
                                    except Exception:
                                        pass
                                yield {
                                    "type": "error",
                                    "message": "Grok Web unauthorized (401). Reconnect with fresh cookies.",
                                }
                                return

                            if last_http_status >= 400:
                                try:
                                    last_http_body = (resp.text or "")[:240]
                                except Exception:
                                    last_http_body = ""
                                low = (last_http_body or "").lower()
                                if last_http_status == 404 and ("model not found" in low or '"code":5' in low):
                                    if session and hasattr(session, "close"):
                                        try:
                                            session.close()
                                        except Exception:
                                            pass
                                    logger.warning("GrokWeb: model '%s' not found, trying next candidate", model)
                                    break
                                if session and hasattr(session, "close"):
                                    try:
                                        session.close()
                                    except Exception:
                                        pass
                                yield {
                                    "type": "error",
                                    "message": f"Grok Web HTTP {last_http_status}: {last_http_body}",
                                }
                                return

                            chosen_model = model
                            for line in resp.iter_lines():
                                if line is None:
                                    continue
                                if isinstance(line, bytes):
                                    line = line.decode("utf-8", errors="ignore")
                                raw = line.strip()
                                if not raw:
                                    continue
                                try:
                                    data = json.loads(raw)
                                except Exception:
                                    continue

                                response = ((data or {}).get("result") or {}).get("response") or {}
                                token = response.get("token")
                                if isinstance(token, str) and token:
                                    streamed = True
                                    yield {"type": "text", "text": token, "content": token}

                                model_response = response.get("modelResponse") or {}
                                full_msg = model_response.get("message")
                                if isinstance(full_msg, str) and full_msg:
                                    if full_msg != last_text:
                                        delta = full_msg[len(last_text):] if full_msg.startswith(last_text) else full_msg
                                        if delta:
                                            streamed = True
                                            yield {"type": "text", "text": delta, "content": delta}
                                        last_text = full_msg

                            if session and hasattr(session, "close"):
                                try:
                                    session.close()
                                except Exception:
                                    pass
                            break
                        if used_cffi and chosen_model:
                            break

                    if used_cffi:
                        # CFFI path already handled current model, go to next candidate when needed.
                        continue

                    with client.stream("POST", _CHAT_URL, json=payload) as resp:
                        last_http_status = resp.status_code
                        if resp.status_code in (401, 403):
                            if resp.status_code == 403:
                                conv_id, parent_id, ctx_err = _resolve_existing_conversation_context(client)
                                if conv_id and parent_id:
                                    fb_url = f"{_BASE_URL}/rest/app-chat/conversations/{conv_id}/responses"
                                    fb_payload = _build_existing_response_payload(user_text, parent_id)
                                    logger.info(
                                        "GrokWeb: /conversations/new blocked (403), trying existing conversation %s",
                                        conv_id,
                                    )
                                    with client.stream("POST", fb_url, json=fb_payload) as fb_resp:
                                        if fb_resp.status_code >= 400:
                                            fb_body = ""
                                            try:
                                                fb_body = fb_resp.read().decode("utf-8", errors="ignore")[:240]
                                            except Exception:
                                                fb_body = ""
                                            yield {
                                                "type": "error",
                                                "message": (
                                                    f"Grok Web existing-conversation fallback failed "
                                                    f"(HTTP {fb_resp.status_code}): {fb_body}"
                                                ),
                                            }
                                            return

                                        chosen_model = model
                                        for line in fb_resp.iter_lines():
                                            if line is None:
                                                continue
                                            raw = line.strip()
                                            if not raw:
                                                continue
                                            try:
                                                data = json.loads(raw)
                                            except Exception:
                                                continue

                                            result = (data or {}).get("result") or {}
                                            token = result.get("token")
                                            if isinstance(token, str) and token:
                                                streamed = True
                                                yield {"type": "text", "text": token, "content": token}

                                            model_response = result.get("modelResponse") or {}
                                            full_msg = model_response.get("message")
                                            if isinstance(full_msg, str) and full_msg:
                                                if full_msg != last_text:
                                                    delta = full_msg[len(last_text):] if full_msg.startswith(last_text) else full_msg
                                                    if delta:
                                                        streamed = True
                                                        yield {"type": "text", "text": delta, "content": delta}
                                                    last_text = full_msg
                                    break
                                logger.warning("GrokWeb: existing conversation fallback unavailable: %s", ctx_err)
                            yield {
                                "type": "error",
                                "message": "Grok Web: unauthorized session. Reconnect with a fresh token.",
                            }
                            return
                        if resp.status_code >= 400:
                            try:
                                last_http_body = resp.read().decode("utf-8", errors="ignore")[:240]
                            except Exception:
                                last_http_body = ""
                            low = (last_http_body or "").lower()
                            if resp.status_code == 404 and ("model not found" in low or '"code":5' in low):
                                logger.warning("GrokWeb: model '%s' not found, trying next candidate", model)
                                continue
                            yield {
                                "type": "error",
                                "message": f"Grok Web HTTP {resp.status_code}: {last_http_body}",
                            }
                            return

                        chosen_model = model
                        for line in resp.iter_lines():
                            if line is None:
                                continue
                            raw = line.strip()
                            if not raw:
                                continue
                            try:
                                data = json.loads(raw)
                            except Exception:
                                continue

                            response = ((data or {}).get("result") or {}).get("response") or {}
                            token = response.get("token")
                            if isinstance(token, str) and token:
                                streamed = True
                                yield {"type": "text", "text": token, "content": token}

                            model_response = response.get("modelResponse") or {}
                            full_msg = model_response.get("message")
                            if isinstance(full_msg, str) and full_msg:
                                if full_msg != last_text:
                                    delta = full_msg[len(last_text):] if full_msg.startswith(last_text) else full_msg
                                    if delta:
                                        streamed = True
                                        yield {"type": "text", "text": delta, "content": delta}
                                    last_text = full_msg
                        break

                if not chosen_model:
                    yield {
                        "type": "error",
                        "message": f"Grok Web model resolution failed (HTTP {last_http_status}): {last_http_body}",
                    }
                    return

                if chosen_model and chosen_model != (self.model or "").strip():
                    logger.info("GrokWeb: using resolved model '%s' for selected '%s'", chosen_model, self.model)

            if not streamed:
                logger.debug("GrokWeb: request completed without streamed tokens")
            yield {"type": "done", "usage": {}}
        except Exception as e:
            logger.warning(f"GrokWeb stream error: {e}")
            yield {"type": "error", "message": f"Grok Web error: {e}"}
