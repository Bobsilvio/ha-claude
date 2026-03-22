"""Gemini Web provider — unofficial session-based access to gemini.google.com.

⚠️  UNSTABLE: uses the private Gemini web API which can change at any time
    and is not endorsed by Google. Use the official Google Gemini API key
    provider for production use.

Authentication:
  1. Click the 🔑 button → "Connect Gemini Web"
  2. Open https://gemini.google.com in your browser and log in
  3. Open DevTools (F12) → Application → Cookies → gemini.google.com
  4. Copy the values of __Secure-1PSID and __Secure-1PSIDTS
  5. Paste them in the Amira modal and click Connect

The session is stored in /data/session_gemini_web.json and reused until
it expires or is revoked.
"""

import json
import asyncio
import logging
import os
import random
import re
import threading
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Tuple

from .enhanced import EnhancedProvider
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.error("httpx not installed — required for Gemini Web")

try:
    from gemini_webapi import GeminiClient
    GEMINI_WEBAPI_AVAILABLE = True
except Exception:
    try:
        from gemini_webapi.client import GeminiClient  # type: ignore
        GEMINI_WEBAPI_AVAILABLE = True
    except Exception:
        GeminiClient = None
        GEMINI_WEBAPI_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_GEMINI_BASE  = "https://gemini.google.com"
_GEMINI_BATCH = f"{_GEMINI_BASE}/_/BardChatUi/data/batchexecute"
_GEMINI_GENERATE = (
    f"{_GEMINI_BASE}/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
)
_TOKEN_FILE   = "/data/session_gemini_web.json"

_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "X-Same-Domain": "1",
    "Origin": _GEMINI_BASE,
    "Referer": f"{_GEMINI_BASE}/",
}

# ---------------------------------------------------------------------------
# Module-level session state
# ---------------------------------------------------------------------------
_stored_session: Optional[Dict[str, Any]] = None
_sdk_client: Optional[Any] = None
_sdk_client_fingerprint: str = ""

# Model headers aligned with the reverse-engineered Gemini web flow used by
# HanaokaYuzu/Gemini-API (legacy name gemini-3.0-pro maps to gemini-3.1-pro).
_MODEL_HEADERS: Dict[str, Dict[str, str]] = {
    "gemini-3.1-pro": {
        "x-goog-ext-525001261-jspb": '[1,null,null,null,"e6fa609c3fa255c0",null,null,0,[4],null,null,2]',
        "x-goog-ext-73010989-jspb": "[0]",
        "x-goog-ext-73010990-jspb": "[0]",
    },
    "gemini-3.0-pro": {
        "x-goog-ext-525001261-jspb": '[1,null,null,null,"e6fa609c3fa255c0",null,null,0,[4],null,null,2]',
        "x-goog-ext-73010989-jspb": "[0]",
        "x-goog-ext-73010990-jspb": "[0]",
    },
    "gemini-3.0-flash": {
        "x-goog-ext-525001261-jspb": '[1,null,null,null,"fbb127bbb056c959",null,null,0,[4],null,null,1]',
        "x-goog-ext-73010989-jspb": "[0]",
        "x-goog-ext-73010990-jspb": "[0]",
    },
    "gemini-3.0-flash-thinking": {
        "x-goog-ext-525001261-jspb": '[1,null,null,null,"5bf011840784117a",null,null,0,[4],null,null,1]',
        "x-goog-ext-73010989-jspb": "[0]",
        "x-goog-ext-73010990-jspb": "[0]",
    },
}


def _lang() -> str:
    l = (os.getenv("LANGUAGE", "en") or "en").lower()
    return l if l in ("en", "it", "es", "fr") else "en"


def _t(en: str, it: str, es: str, fr: str, **kwargs) -> str:
    m = {"en": en, "it": it, "es": es, "fr": fr}
    txt = m.get(_lang(), en)
    try:
        return txt.format(**kwargs) if kwargs else txt
    except Exception:
        return txt


def _get_base_timeout() -> int:
    """Read backend timeout setting with sane bounds."""
    try:
        import api as _api  # type: ignore
        _base_timeout = int(getattr(_api, "TIMEOUT", 30) or 30)
    except Exception:
        _base_timeout = 30
    return max(30, min(300, _base_timeout))


def _load_session() -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(_TOKEN_FILE):
            with open(_TOKEN_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"GeminiWeb: could not load session: {e}")
    return None


def _save_session(data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_TOKEN_FILE), exist_ok=True)
        with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"GeminiWeb: could not save session: {e}")


_stored_session = _load_session()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_cookies(psid: str, psidts: str) -> Dict[str, str]:
    return {"__Secure-1PSID": psid, "__Secure-1PSIDTS": psidts}


def _session_fingerprint(psid: str, psidts: str) -> str:
    return f"{psid[:12]}::{psidts[:12]}"


async def _close_sdk_client() -> None:
    global _sdk_client, _sdk_client_fingerprint
    client = _sdk_client
    _sdk_client = None
    _sdk_client_fingerprint = ""
    if not client:
        return
    try:
        close_fn = getattr(client, "close", None)
        if callable(close_fn):
            maybe_await = close_fn()
            if asyncio.iscoroutine(maybe_await):
                await maybe_await
    except Exception:
        pass


def _run_async(coro):
    """Run async coroutine from sync code."""
    try:
        asyncio.get_running_loop()
        _has_loop = True
    except RuntimeError:
        _has_loop = False

    if not _has_loop:
        return asyncio.run(coro)

    # Running loop in this thread: execute coroutine in a worker thread.
    _box: Dict[str, Any] = {}

    def _runner():
        try:
            _box["result"] = asyncio.run(coro)
        except Exception as e:
            _box["error"] = e

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()
    if "error" in _box:
        raise _box["error"]
    return _box.get("result")


def _fetch_page_tokens(psid: str, psidts: str) -> Tuple[str, str]:
    """Fetch SNlM0e token and BL param from the Gemini homepage.

    Returns (snlm0e, bl).
    Raises RuntimeError if cookies are invalid.
    """
    cookies = _make_cookies(psid, psidts)
    get_headers = {k: v for k, v in _HEADERS.items() if k != "Content-Type"}
    resp = httpx.get(
        _GEMINI_BASE + "/app",
        headers=get_headers,
        cookies=cookies,
        timeout=15.0,
        follow_redirects=True,
    )
    final_url = str(resp.url)
    if (
        resp.status_code == 401
        or "accounts.google.com" in final_url
        or "consent.google.com" in final_url
    ):
        raise RuntimeError(
            "Cookies rejected by Google (login/consent required) — please copy fresh cookies from your browser."
        )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Could not access Gemini (HTTP {resp.status_code}) — check your cookies."
        )

    snlm0e_match = re.search(r'"SNlM0e":"(.*?)"', resp.text)
    if not snlm0e_match:
        raise RuntimeError(
            "Could not find SNlM0e token — cookies may be invalid or Gemini changed its API."
        )
    snlm0e = snlm0e_match.group(1)

    # BL param (boq_ build label) — extract from page or fall back to known value
    bl_match = re.search(r'"cfb2h":"(.*?)"', resp.text)
    bl = bl_match.group(1) if bl_match else "boq_assistant-bard-web-server_20240514.20_p0"

    return snlm0e, bl


def _ensure_snlm0e(s: Dict[str, Any]) -> str:
    """Return SNlM0e from session, refreshing if older than 1 hour."""
    global _stored_session
    age = int(time.time()) - s.get("snlm0e_fetched_at", 0)
    if age > 3600:
        try:
            snlm0e, bl = _fetch_page_tokens(s["psid"], s["psidts"])
            s["snlm0e"] = snlm0e
            s["bl"] = bl
            s["snlm0e_fetched_at"] = int(time.time())
            _stored_session = s
            _save_session(s)
            logger.debug("GeminiWeb: SNlM0e refreshed")
        except Exception as e:
            logger.warning(f"GeminiWeb: could not refresh SNlM0e: {e}")
    return s.get("snlm0e", "")


# ---------------------------------------------------------------------------
# Public auth helpers
# ---------------------------------------------------------------------------

def store_session(psid: str, psidts: str) -> Dict[str, Any]:
    """Validate cookies, fetch tokens, and persist session to disk."""
    global _stored_session
    psid   = psid.strip()
    psidts = psidts.strip()
    if not psid or not psidts:
        raise ValueError("Both __Secure-1PSID and __Secure-1PSIDTS are required.")

    snlm0e, bl = _fetch_page_tokens(psid, psidts)

    data = {
        "psid":               psid,
        "psidts":             psidts,
        "snlm0e":             snlm0e,
        "bl":                 bl,
        "snlm0e_fetched_at":  int(time.time()),
        "stored_at":          int(time.time()),
        "ok":                 True,
    }
    _stored_session = data
    _save_session(data)
    if GEMINI_WEBAPI_AVAILABLE:
        _run_async(_close_sdk_client())
    logger.info("GeminiWeb: session stored successfully")
    return data


def get_session_status() -> Dict[str, Any]:
    s = _stored_session
    if not s:
        return {"configured": False}
    age_days = (int(time.time()) - s.get("stored_at", 0)) // 86400
    return {"configured": True, "age_days": age_days}


def clear_session() -> None:
    global _stored_session
    _stored_session = None
    if GEMINI_WEBAPI_AVAILABLE:
        _run_async(_close_sdk_client())
    try:
        if os.path.exists(_TOKEN_FILE):
            os.remove(_TOKEN_FILE)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Core request / response
# ---------------------------------------------------------------------------

async def _send_message_sdk_async(s: Dict[str, Any], prompt: str, model: str = "") -> str:
    """Primary path via gemini_webapi SDK (HanaokaYuzu/Gemini-API)."""
    if not GEMINI_WEBAPI_AVAILABLE or GeminiClient is None:
        raise RuntimeError("gemini_webapi SDK not installed")

    psid = s["psid"]
    psidts = s["psidts"]
    _ctor_errors: List[str] = []
    _client = None
    # Try multiple constructor styles for compatibility across gemini_webapi versions.
    # Official docs use positional args first: GeminiClient(Secure_1PSID, Secure_1PSIDTS, ...).
    _ctor_variants = [
        {"args": (psid, psidts), "kwargs": {"proxy": None}},
        {"args": (), "kwargs": {"Secure_1PSID": psid, "Secure_1PSIDTS": psidts, "proxy": None}},
        {"args": (), "kwargs": {"cookies": {"__Secure-1PSID": psid, "__Secure-1PSIDTS": psidts}}},
        {"args": (), "kwargs": {"psid": psid, "psidts": psidts}},
        {"args": (), "kwargs": {"secure_1psid": psid, "secure_1psidts": psidts}},
    ]
    for _variant in _ctor_variants:
        try:
            _client = GeminiClient(*_variant["args"], **_variant["kwargs"])
            break
        except Exception as _ce:
            _ctor_errors.append(f"{type(_ce).__name__}: {_ce}")
    if _client is None:
        raise RuntimeError(
            "Gemini SDK client init failed (cookie ctor variants exhausted): "
            + " | ".join(_ctor_errors[:3])
        )

    _base_timeout = _get_base_timeout()
    await _client.init(
        timeout=float(max(45, _base_timeout * 2)),
        auto_close=True,
        close_delay=120.0,
        auto_refresh=True,
    )

    model_name = (model or "").strip() or "gemini-3.0-flash"
    # Keep compatibility with our internal alias used in UI.
    if model_name == "gemini-3.0-pro":
        model_name = "gemini-3.1-pro"
    _sdk_deadline = float(max(70, _base_timeout * 2))

    try:
        # Prefer SDK streaming for long HTML/tool payloads.
        # This reduces truncation risk and aligns with gemini_webapi examples:
        #   async for chunk in client.generate_content_stream(...)
        text_parts: List[str] = []
        _stream_fn = getattr(_client, "generate_content_stream", None)
        if callable(_stream_fn):
            async def _run_stream() -> None:
                async for chunk in _stream_fn(prompt, model=model_name):
                    # Compatible with multiple SDK versions/fields.
                    _delta = (
                        getattr(chunk, "text_delta", None)
                        or getattr(chunk, "text", None)
                        or ""
                    )
                    if _delta:
                        text_parts.append(str(_delta))

            await asyncio.wait_for(_run_stream(), timeout=_sdk_deadline)
            _streamed = "".join(text_parts).strip()
            if _streamed:
                return _streamed
            # If stream yields no text, fall through to non-stream call.

        response = await asyncio.wait_for(
            _client.generate_content(prompt, model=model_name),
            timeout=_sdk_deadline,
        )
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
        raise RuntimeError("Gemini SDK returned empty response")
    except asyncio.TimeoutError as _te:
        raise RuntimeError(
            f"Gemini SDK timeout after {_sdk_deadline:.0f}s (model={model_name})"
        ) from _te
    finally:
        try:
            close_fn = getattr(_client, "close", None)
            if callable(close_fn):
                maybe_await = close_fn()
                if asyncio.iscoroutine(maybe_await):
                    await maybe_await
        except Exception:
            pass


def _send_message_sdk(s: Dict[str, Any], prompt: str, model: str = "") -> str:
    return _run_async(_send_message_sdk_async(s, prompt, model))


def _send_message(s: Dict[str, Any], prompt: str, model: str = "") -> str:
    """Send a prompt and return the text response.

    Uses StreamGenerate-style request (newer Gemini web flow), then falls back
    to legacy batchexecute shape if needed.
    """
    global _stored_session
    _base_timeout = _get_base_timeout()
    _http_timeout = float(max(90, _base_timeout * 4))
    psid = s["psid"]
    psidts = s["psidts"]
    cookies = _make_cookies(psid, psidts)

    for attempt in range(2):
        snlm0e = _ensure_snlm0e(s)
        bl = s.get("bl", "boq_assistant-bard-web-server_20240514.20_p0")
        reqid = str(random.randint(10000, 999999))

        # Newer request shape (aligned with Gemini-API project).
        message_content = [prompt, 0, None, None, None, None, 0]
        inner_req = [None] * 69
        inner_req[0] = message_content
        inner_req[2] = ["", "", "", None, None, None, None, None, None, ""]
        inner_req[7] = 1
        inner_req[1] = ["en"]
        inner_req[6] = [0]
        inner_req[10] = 1
        inner_req[11] = 0
        inner_req[17] = [[0]]
        inner_req[18] = 0
        inner_req[27] = 1
        inner_req[30] = [4]
        inner_req[41] = [1]
        inner_req[53] = 0
        inner_req[61] = []
        inner_req[68] = 1

        uuid_val = str(uuid.uuid4())
        inner_req[59] = uuid_val
        model_headers = _MODEL_HEADERS.get((model or "").strip(), {})

        req_headers = {
            **_HEADERS,
            **model_headers,
            "x-goog-ext-525005358-jspb": f'["{uuid_val}",1]',
        }
        params = {"bl": bl, "_reqid": reqid, "rt": "c"}
        if s.get("sid"):
            params["f.sid"] = s["sid"]
        data = {"at": snlm0e, "f.req": json.dumps([None, json.dumps(inner_req)])}

        resp = httpx.post(
            _GEMINI_GENERATE,
            headers=req_headers,
            cookies=cookies,
            params=params,
            data=data,
            timeout=_http_timeout,
        )

        # Gemini web is frequently unstable with transient 502s.
        # Do not attempt parser fallbacks on gateway failures.
        if resp.status_code == 502:
            raise RuntimeError("Gemini Web temporary 502 (gateway). Try again shortly.")

        # Legacy fallback for compatibility if Google returns a hard reject.
        if resp.status_code == 400 and attempt == 0:
            msg_struct = [[prompt], None, None]
            legacy_freq = json.dumps([[["CoYgR8", json.dumps(msg_struct), None, "generic"]]])
            legacy_resp = httpx.post(
                _GEMINI_BATCH,
                headers=_HEADERS,
                cookies=cookies,
                params={"bl": bl, "_reqid": reqid, "rt": "c"},
                data={"f.req": legacy_freq, "at": snlm0e},
                timeout=_http_timeout,
            )
            if legacy_resp.status_code == 200:
                return _parse_response(legacy_resp.text)
            resp = legacy_resp

        if resp.status_code in (401, 403):
            clear_session()
            raise RuntimeError(
                "Gemini session expired — please reconnect via the 🔑 button."
            )

        if resp.status_code == 400 and attempt == 0:
            # Token/BL can become stale quickly on Gemini web; refresh once then retry.
            try:
                snlm0e, new_bl = _fetch_page_tokens(psid, psidts)
                s["snlm0e"] = snlm0e
                s["bl"] = new_bl
                s["snlm0e_fetched_at"] = int(time.time())
                _stored_session = s
                _save_session(s)
                continue
            except Exception:
                clear_session()
                raise RuntimeError(
                    "Gemini cookies/token invalid (Google login or consent required) — reconnect via the 🔑 button."
                )

        if resp.status_code != 200:
            logger.debug(
                "GeminiWeb raw non-200 response (status=%s, chars=%s): %s",
                resp.status_code,
                len(resp.text or ""),
                resp.text,
            )
            raise RuntimeError(f"Gemini returned HTTP {resp.status_code}")

        logger.debug(
            "GeminiWeb raw response (%s chars): %s",
            len(resp.text or ""),
            resp.text,
        )

        return _parse_response(resp.text)

    raise RuntimeError("Gemini request failed after retry")


def _parse_response(raw: str) -> str:
    """Parse Gemini batchexecute response and extract the answer text."""
    # Strip the ")]}'" safety prefix Google adds
    text = raw
    if text.startswith(")]}'"):
        text = text[5:]

    candidates: List[str] = []

    # Iterate lines looking for a parseable JSON array that contains the reply
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            outer = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(outer, list):
            continue

        for item in outer:
            if not isinstance(item, list) or len(item) < 3:
                continue
            payload = item[2]
            if not isinstance(payload, str) or not payload:
                continue
            try:
                inner = json.loads(payload)
            except json.JSONDecodeError:
                continue

            extracted = _extract_text(inner)
            if extracted:
                candidates.append(extracted)

    # Pick the best candidate instead of the first one: StreamGenerate payloads
    # can contain partial chunks and side metadata before final text.
    unique_candidates: List[str] = []
    seen = set()
    for c in candidates:
        k = c.strip()
        if not k or k in seen:
            continue
        seen.add(k)
        unique_candidates.append(k)

    if unique_candidates:
        logger.debug(
            "GeminiWeb parsed candidates (%s): %s",
            len(unique_candidates),
            unique_candidates,
        )

        def _score(c: str, idx: int) -> int:
            score = 0
            score += min(len(c), 500)
            if re.search(r"[.!?…]$", c):
                score += 18
            if re.search(r"\s", c):
                score += 12
            if re.search(r"\b(ciao|hello|sono|assistant|posso|help|aiut)\b", c, re.IGNORECASE):
                score += 25
            # Prefer later chunks in streamed payloads (usually more complete).
            score += idx * 2
            # Penalize location-like snippets often found in metadata.
            if re.fullmatch(
                r"[A-Za-zÀ-ÖØ-öø-ÿ'’.\- ]+,\s*[A-Za-zÀ-ÖØ-öø-ÿ'’.\- ]+(?:,\s*[A-Za-zÀ-ÖØ-öø-ÿ'’.\- ]+)?",
                c,
            ):
                score -= 80
            return score

        best_idx = 0
        best_score = _score(unique_candidates[0], 0)
        for i, c in enumerate(unique_candidates[1:], start=1):
            s = _score(c, i)
            if s > best_score:
                best_score = s
                best_idx = i
        return unique_candidates[best_idx]

    raise RuntimeError(
        "Could not parse Gemini response — the web API format may have changed."
    )


def _extract_text(inner: Any) -> Optional[str]:
    """Try multiple known paths to get the response text from Gemini's inner JSON."""
    def _is_plausible_reply(text: Any) -> bool:
        if not isinstance(text, str):
            return False
        t = text.strip()
        if len(t) < 2:
            return False
        # Filter known internal asset/link payloads that are not assistant text.
        if t.startswith(("http://", "https://", "//")):
            return False
        if "google.com/maps/vt/data=" in t:
            return False
        # Replies normally contain some natural language markers.
        has_alpha = bool(re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", t))
        has_space_or_punct = bool(re.search(r"[\s,.;:!?]", t))
        return has_alpha and has_space_or_punct

    # Path 1 — canonical: inner[4][0][1][0]
    try:
        text = inner[4][0][1][0]
        if _is_plausible_reply(text):
            return text
    except (IndexError, TypeError, KeyError):
        pass

    # Path 2 — sometimes the text lives at inner[0][0]
    try:
        text = inner[0][0]
        if _is_plausible_reply(text):
            return text
    except (IndexError, TypeError):
        pass

    # Path 3 — recursive: find the best natural-language candidate.
    def _score_candidate(t: str) -> int:
        score = 0
        score += min(len(t), 300) // 8
        if re.search(r"[.!?]$", t.strip()):
            score += 8
        if re.search(r"\s", t):
            score += 12
        if re.search(r"\b(ciao|hello|hi|sono|I am|how|come|posso)\b", t, re.IGNORECASE):
            score += 18
        return score

    def _find_best(obj, depth=0) -> str:
        if depth > 4:
            return ""
        best = ""
        if isinstance(obj, list):
            for x in obj:
                c = _find_best(x, depth + 1)
                if c and _score_candidate(c) > _score_candidate(best):
                    best = c
            return best
        if isinstance(obj, dict):
            for v in obj.values():
                c = _find_best(v, depth + 1)
                if c and _score_candidate(c) > _score_candidate(best):
                    best = c
            return best
        if isinstance(obj, str) and _is_plausible_reply(obj):
            return obj
        return best

    result = _find_best(inner)
    if result:
        return result

    return None


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class GeminiWebProvider(EnhancedProvider):
    """Gemini Web unofficial provider — uses browser session cookies (UNSTABLE)."""

    _MODELS = [
        "gemini-3.1-pro",
        "gemini-3.0-pro",
        "gemini-3.0-flash",
        "gemini-3.0-flash-thinking",
    ]

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key, model)
        self.rate_limiter = get_rate_limit_coordinator().get_limiter("gemini_web")

    @staticmethod
    def get_provider_name() -> str:
        return "gemini_web"

    def validate_credentials(self) -> bool:
        s = _stored_session
        return bool(s and s.get("psid") and s.get("psidts"))

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
        if not GEMINI_WEBAPI_AVAILABLE and not HTTPX_AVAILABLE:
            yield {
                "type": "error",
                "message": _t(
                    "Gemini Web dependencies not installed (gemini_webapi/httpx).",
                    "Dipendenze Gemini Web non installate (gemini_webapi/httpx).",
                    "Dependencias de Gemini Web no instaladas (gemini_webapi/httpx).",
                    "Dependances Gemini Web non installees (gemini_webapi/httpx).",
                ),
            }
            return

        s = _stored_session
        if not s or not s.get("psid"):
            yield {
                "type": "error",
                "message": _t(
                    "Gemini Web: not authenticated. Use the 🔑 button to connect.",
                    "Gemini Web: non autenticato. Usa il pulsante 🔑 per connetterti.",
                    "Gemini Web: no autenticado. Usa el boton 🔑 para conectarte.",
                    "Gemini Web : non authentifie. Utilise le bouton 🔑 pour te connecter.",
                ),
            }
            return

        can_req, wait = self.rate_limiter.can_request()
        if not can_req:
            raise RuntimeError(f"Rate limited. Wait {wait:.0f}s")
        self.rate_limiter.record_request()

        # Keep original messages in case we need provider fallback.
        _orig_messages = list(messages)
        _is_html_intent = bool(
            isinstance(intent_info, dict)
            and str(intent_info.get("intent", "")).lower() == "create_html_dashboard"
        )

        # For HTML creation on unofficial Gemini Web, prefer the most stable model.
        # 3.1-pro often stalls/queues on long prompts.
        _requested_model = (self.model or "").strip()
        _effective_model = _requested_model
        if _is_html_intent and _requested_model in {"gemini-3.1-pro", "gemini-3.0-pro"}:
            _effective_model = "gemini-3.0-flash"
            logger.warning(
                _t(
                    "GeminiWeb: forcing stable model for HTML intent ({from_model} -> {to_model})",
                    "GeminiWeb: forzo modello stabile per intent HTML ({from_model} -> {to_model})",
                    "GeminiWeb: forzando modelo estable para intent HTML ({from_model} -> {to_model})",
                    "GeminiWeb : forçage d'un modele stable pour l'intention HTML ({from_model} -> {to_model})",
                    from_model=_requested_model,
                    to_model=_effective_model,
                ),
            )

        # Normalise tool-call history → plain turns
        from providers.tool_simulator import flatten_tool_messages, get_simulator_system_prompt
        messages = flatten_tool_messages(messages)
        system_prompt, human_messages = self._split_messages(messages)

        # Build system prompt: tool simulator + intent + agent override
        tool_schemas      = (intent_info or {}).get("tool_schemas") or []
        intent_base_prompt = (intent_info or {}).get("prompt", "")

        sim_prompt = get_simulator_system_prompt(tool_schemas)
        combined_system = sim_prompt
        if intent_base_prompt:
            combined_system = intent_base_prompt + "\n\n" + combined_system
        if system_prompt:
            combined_system = combined_system + "\n\n" + system_prompt

        # Reconstruct conversation history into a single prompt string
        history_parts = []
        last_human = ""
        for m in human_messages:
            role = m.get("role", "")
            c    = m.get("content", "")
            text = c if isinstance(c, str) else (c[0].get("text", "") if c else "")
            if role == "user":
                last_human = text
                history_parts.append(f"Human: {text}")
            elif role == "assistant":
                history_parts.append(f"Assistant: {text}")

        if len(history_parts) > 1:
            history_block = "\n\n".join(history_parts[:-1])
            full_prompt = (
                f"{combined_system}\n\n"
                f"[CONVERSATION HISTORY]\n{history_block}\n[/CONVERSATION HISTORY]\n\n"
                f"Human: {last_human}"
            )
        else:
            full_prompt = f"{combined_system}\n\nHuman: {last_human}"

        try:
            response_text = ""
            sdk_err = None
            if GEMINI_WEBAPI_AVAILABLE:
                try:
                    response_text = _send_message_sdk(s, full_prompt, _effective_model)
                except Exception as e:
                    sdk_err = e
                    logger.warning(
                        _t(
                            "GeminiWeb SDK failed, using legacy fallback: {error}",
                            "SDK GeminiWeb fallito, uso fallback legacy: {error}",
                            "SDK GeminiWeb fallo, usando fallback legacy: {error}",
                            "SDK GeminiWeb en echec, utilisation du fallback legacy : {error}",
                            error=e,
                        )
                    )
                    # gemini-3.1-pro can stall on web SDK. Retry once with 3.0-pro alias
                    # before dropping to legacy HTTP flow.
                    try:
                        if str(_effective_model or "").strip() == "gemini-3.1-pro":
                            logger.warning(
                                _t(
                                    "GeminiWeb SDK retry with gemini-3.0-pro alias after 3.1 failure",
                                    "Retry SDK GeminiWeb con alias gemini-3.0-pro dopo errore 3.1",
                                    "Reintento SDK GeminiWeb con alias gemini-3.0-pro tras fallo 3.1",
                                    "Nouvelle tentative SDK GeminiWeb avec l'alias gemini-3.0-pro apres l'echec 3.1",
                                )
                            )
                            response_text = _send_message_sdk(s, full_prompt, "gemini-3.0-pro")
                    except Exception as _e_alias:
                        logger.warning(
                            _t(
                                "GeminiWeb SDK alias retry failed: {error}",
                                "Retry alias SDK GeminiWeb fallito: {error}",
                                "Reintento alias SDK GeminiWeb fallido: {error}",
                                "La nouvelle tentative d'alias SDK GeminiWeb a echoue : {error}",
                                error=_e_alias,
                            )
                        )

            if not response_text:
                _sdk_err_s = str(sdk_err or "").lower()
                _sdk_unstable = any(k in _sdk_err_s for k in ("timeout", "stalled", "readerror", "gateway", "502"))
                if _sdk_unstable:
                    # Optional fallback to official Google API provider if configured.
                    try:
                        import api as _api  # type: ignore
                        _google_key = str(getattr(_api, "GOOGLE_API_KEY", "") or "").strip()
                    except Exception:
                        _google_key = ""
                    if _google_key:
                        logger.warning(
                            _t(
                                "GeminiWeb unstable -> falling back to official Google provider",
                                "GeminiWeb instabile -> fallback al provider Google ufficiale",
                                "GeminiWeb inestable -> fallback al proveedor oficial de Google",
                                "GeminiWeb instable -> bascule vers le fournisseur Google officiel",
                            )
                        )
                        yield {
                            "type": "status",
                            "message": _t(
                                "⚠️ Gemini Web unstable, switching to official Google API...",
                                "⚠️ Gemini Web instabile, passo alla Google API ufficiale...",
                                "⚠️ Gemini Web inestable, cambiando a la API oficial de Google...",
                                "⚠️ Gemini Web instable, bascule vers l'API Google officielle...",
                            ),
                        }
                        try:
                            from providers.google import GoogleProvider
                            _gp = GoogleProvider(api_key=_google_key, model="gemini-2.5-flash")
                            for _ev in _gp.stream_chat(_orig_messages, intent_info):
                                yield _ev
                            return
                        except Exception as _gerr:
                            logger.warning(
                                _t(
                                    "GeminiWeb->Google fallback failed: {error}",
                                    "Fallback GeminiWeb->Google fallito: {error}",
                                    "Fallback GeminiWeb->Google fallido: {error}",
                                    "Echec du fallback GeminiWeb->Google : {error}",
                                    error=_gerr,
                                )
                            )

                    # No Google fallback available (or failed): return clear instability error.
                    raise RuntimeError(
                        _t(
                            "Gemini Web unstable (timeout/502). Retry or use Google provider with API key.",
                            "Gemini Web instabile (timeout/502). Riprova oppure usa il provider Google con API key.",
                            "Gemini Web inestable (timeout/502). Reintenta o usa el proveedor Google con API key.",
                            "Gemini Web instable (timeout/502). Reessayez ou utilisez le fournisseur Google avec une API key.",
                        )
                    )
                if not HTTPX_AVAILABLE:
                    raise RuntimeError(f"Gemini SDK unavailable and legacy fallback disabled: {sdk_err}")
                response_text = _send_message(s, full_prompt, _effective_model)

            if response_text:
                yield {"type": "text", "text": response_text}
            yield {"type": "done", "finish_reason": "stop"}
        except Exception as e:
            logger.error(
                _t(
                    "GeminiWeb: error during request: {error}",
                    "GeminiWeb: errore durante la richiesta: {error}",
                    "GeminiWeb: error durante la solicitud: {error}",
                    "GeminiWeb : erreur pendant la requete : {error}",
                    error=e,
                )
            )
            yield {"type": "error", "message": str(e)}

    # ------------------------------------------------------------------
    def _split_messages(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Separate system prompt from human/assistant messages."""
        system = ""
        rest: List[Dict[str, Any]] = []
        for m in messages:
            if m.get("role") == "system":
                c = m.get("content", "")
                system = c if isinstance(c, str) else (c[0].get("text", "") if c else "")
            else:
                rest.append(m)
        return system, rest

    def get_available_models(self) -> List[str]:
        return list(self._MODELS)

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        return {
            "auth_error": {
                "en": "Gemini Web: session expired. Reconnect via the 🔑 button.",
                "it": "Gemini Web: sessione scaduta. Riconnetti con il pulsante 🔑.",
                "es": "Gemini Web: sesión expirada. Reconéctate con 🔑.",
                "fr": "Gemini Web: session expirée. Reconnectez-vous via 🔑.",
            },
        }
