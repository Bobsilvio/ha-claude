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
import logging
import os
import random
import re
import time
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_GEMINI_BASE  = "https://gemini.google.com"
_GEMINI_BATCH = f"{_GEMINI_BASE}/_/BardChatUi/data/batchexecute"
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
    if resp.status_code == 401 or "accounts.google.com" in str(resp.url):
        raise RuntimeError(
            "Cookies rejected by Google — please copy fresh cookies from your browser."
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
    try:
        if os.path.exists(_TOKEN_FILE):
            os.remove(_TOKEN_FILE)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Core request / response
# ---------------------------------------------------------------------------

def _send_message(s: Dict[str, Any], prompt: str) -> str:
    """Send a prompt and return the text response."""
    psid    = s["psid"]
    psidts  = s["psidts"]
    snlm0e  = _ensure_snlm0e(s)
    bl      = s.get("bl", "boq_assistant-bard-web-server_20240514.20_p0")
    cookies = _make_cookies(psid, psidts)

    # Build batchexecute body
    msg_struct = [[prompt], None, None]
    freq = json.dumps([[["CoYgR8", json.dumps(msg_struct), None, "generic"]]])

    params = {
        "bl":      bl,
        "_reqid":  str(random.randint(10000, 999999)),
        "rt":      "c",
    }
    data = {"f.req": freq, "at": snlm0e}

    resp = httpx.post(
        _GEMINI_BATCH,
        headers=_HEADERS,
        cookies=cookies,
        params=params,
        data=data,
        timeout=60.0,
    )

    if resp.status_code in (401, 403):
        clear_session()
        raise RuntimeError(
            "Gemini session expired — please reconnect via the 🔑 button."
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini returned HTTP {resp.status_code}")

    return _parse_response(resp.text)


def _parse_response(raw: str) -> str:
    """Parse Gemini batchexecute response and extract the answer text."""
    # Strip the ")]}'" safety prefix Google adds
    text = raw
    if text.startswith(")]}'"):
        text = text[5:]

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
                return extracted

    raise RuntimeError(
        "Could not parse Gemini response — the web API format may have changed."
    )


def _extract_text(inner: Any) -> Optional[str]:
    """Try multiple known paths to get the response text from Gemini's inner JSON."""
    # Path 1 — canonical: inner[4][0][1][0]
    try:
        text = inner[4][0][1][0]
        if isinstance(text, str) and len(text) > 5:
            return text
    except (IndexError, TypeError, KeyError):
        pass

    # Path 2 — sometimes the text lives at inner[0][0]
    try:
        text = inner[0][0]
        if isinstance(text, str) and len(text) > 5:
            return text
    except (IndexError, TypeError):
        pass

    # Path 3 — recursive: find the longest string in the first 3 levels
    def _find_longest(obj, depth=0) -> str:
        if depth > 3:
            return ""
        if isinstance(obj, str) and len(obj) > 20:
            return obj
        if isinstance(obj, list):
            candidates = [_find_longest(x, depth + 1) for x in obj]
            candidates = [c for c in candidates if c]
            return max(candidates, key=len) if candidates else ""
        return ""

    result = _find_longest(inner)
    if result:
        return result

    return None


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class GeminiWebProvider(EnhancedProvider):
    """Gemini Web unofficial provider — uses browser session cookies (UNSTABLE)."""

    _MODELS = [
        "gemini-2.0-flash",
        "gemini-2.5-pro",
        "gemini-2.0-pro-exp",
        "gemini-1.5-pro",
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
        if not HTTPX_AVAILABLE:
            yield {"type": "error", "message": "httpx not installed — required for Gemini Web"}
            return

        s = _stored_session
        if not s or not s.get("psid"):
            yield {
                "type": "error",
                "message": "Gemini Web: not authenticated. Use the 🔑 button to connect.",
            }
            return

        can_req, wait = self.rate_limiter.can_request()
        if not can_req:
            raise RuntimeError(f"Rate limited. Wait {wait:.0f}s")
        self.rate_limiter.record_request()

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
            response_text = _send_message(s, full_prompt)
            if response_text:
                yield {"type": "text", "text": response_text}
            yield {"type": "done", "finish_reason": "stop"}
        except Exception as e:
            logger.error(f"GeminiWeb: error during request: {e}")
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
