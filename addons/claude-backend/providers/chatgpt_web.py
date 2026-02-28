"""ChatGPT Web provider — unofficial session-based access to ChatGPT.

⚠️  UNSTABLE: this uses the private ChatGPT web API which can change at any time
    and is not endorsed by OpenAI. Use the official OpenAI API key provider for
    production use.

Authentication:
  1. Click the 🔑 button → "Connect ChatGPT Web"
  2. Log in at https://chatgpt.com in your browser
  3. Navigate to https://chatgpt.com/api/auth/session in the same tab
  4. Copy the value of the "accessToken" field from the JSON response
  5. Paste it in the Amira modal and click Connect

The session token expires periodically (typically ~30 days). When ChatGPT
returns 401, reconnect using the same procedure.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, Generator, List, Optional

from .enhanced import EnhancedProvider
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)

try:
    from curl_cffi import requests as cffi_requests
    CFFI_AVAILABLE = True
except ImportError:
    CFFI_AVAILABLE = False
    logger.warning("curl_cffi not installed — ChatGPT Web provider will not work. Run: pip install curl_cffi")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
_CHATGPT_CONV_URL      = "https://chatgpt.com/backend-api/conversation"
_CHATGPT_MSG_URL       = "https://chatgpt.com/backend-api/conversation/{conv_id}/continue"
_CHATGPT_SENTINEL_URL  = "https://chatgpt.com/backend-api/sentinel/chat-requirements"
_TOKEN_FILE            = "/data/session_chatgpt_web.json"

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_stored_session: Optional[Dict[str, Any]] = None   # {access_token, stored_at}


def _load_session() -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(_TOKEN_FILE):
            with open(_TOKEN_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"ChatGPTWeb: could not load session: {e}")
    return None


def _save_session(data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_TOKEN_FILE), exist_ok=True)
        with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"ChatGPTWeb: could not save session: {e}")


_stored_session = _load_session()


# ---------------------------------------------------------------------------
# Public auth helpers
# ---------------------------------------------------------------------------

def store_access_token(access_token: str, cf_clearance: str = "") -> Dict[str, Any]:
    """Validate and persist ChatGPT access token + optional Cloudflare cookie.

    Accepts either:
    - A bare JWT string (starts with 'eyJ')
    - The full JSON from https://chatgpt.com/api/auth/session
      (extracts 'accessToken' AND 'sessionToken' automatically — recommended)

    cf_clearance: optional value of the cf_clearance Cloudflare cookie (fixes 403).

    Returns the stored session dict.
    Raises ValueError if the token appears invalid.
    """
    global _stored_session
    token = access_token.strip()
    if not token:
        raise ValueError("Empty access token")

    session_token: Optional[str] = None

    # Accept full JSON from chatgpt.com/api/auth/session
    if token.startswith("{"):
        try:
            parsed = json.loads(token)
            jwt = parsed.get("accessToken") or parsed.get("access_token") or ""
            if not jwt:
                raise ValueError("Campo 'accessToken' non trovato nel JSON. "
                                 "Hai incollato il contenuto corretto di https://chatgpt.com/api/auth/session?")
            token = jwt.strip()
            session_token = (parsed.get("sessionToken") or "").strip() or None
            logger.info(f"ChatGPTWeb: extracted accessToken from full session JSON "
                        f"(sessionToken={'yes' if session_token else 'no'}).")
        except json.JSONDecodeError:
            raise ValueError("Il testo incollato sembra JSON ma non è valido. "
                             "Copia il contenuto completo della pagina https://chatgpt.com/api/auth/session")

    if not token.startswith("eyJ"):
        raise ValueError("Access token should be a JWT (starts with 'eyJ'). "
                         "Paste the full JSON from https://chatgpt.com/api/auth/session")

    data: Dict[str, Any] = {
        "access_token": token,
        "stored_at": int(time.time()),
        "ok": True,
    }
    if session_token:
        data["session_token"] = session_token
    cf = cf_clearance.strip() if cf_clearance else ""
    if cf:
        data["cf_clearance"] = cf
    # Keep a stable device-id so Cloudflare fingerprint stays consistent
    data["device_id"] = str(uuid.uuid4())
    _stored_session = data
    _save_session(data)
    logger.info(f"ChatGPTWeb: session stored "
                f"(sessionToken={'yes' if session_token else 'no'}, "
                f"cf_clearance={'yes' if cf else 'no'}).")
    data["has_session_token"] = bool(session_token)
    data["has_cf_clearance"] = bool(cf)
    return data


def get_session_status() -> Dict[str, Any]:
    """Return current session status."""
    s = _stored_session
    if not s:
        return {"configured": False}
    age_days = (int(time.time()) - s.get("stored_at", 0)) // 86400
    return {"configured": True, "age_days": age_days}


def clear_session() -> None:
    """Remove stored session."""
    global _stored_session
    _stored_session = None
    try:
        if os.path.exists(_TOKEN_FILE):
            os.remove(_TOKEN_FILE)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_headers(access_token: str, device_id: Optional[str] = None, accept: str = "text/event-stream") -> Dict[str, str]:
    """Minimal headers — curl_cffi handles TLS/browser headers automatically."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": accept,
        "Referer": "https://chatgpt.com/",
        "Origin": "https://chatgpt.com",
        "oai-language": "en-US",
        "oai-device-id": device_id or str(uuid.uuid4()),
    }


def _fetch_sentinel_token(
    access_token: str,
    device_id: Optional[str],
    session_token: Optional[str],
    impersonate: str = "chrome131",
    cf_clearance: Optional[str] = None,
) -> Optional[str]:
    """Fetch the oai-sentinel-chat-requirements-token required by ChatGPT backend-api.
    Returns the token string or None on failure."""
    try:
        headers = _make_headers(access_token, device_id, accept="application/json")
        cookies = _make_cookies(session_token, cf_clearance)
        try:
            sess = cffi_requests.Session(impersonate=impersonate)
        except Exception as e:
            logger.warning(f"ChatGPTWeb: sentinel — {impersonate} not supported by curl_cffi: {e}")
            return None
        resp = sess.post(
            _CHATGPT_SENTINEL_URL,
            headers=headers,
            cookies=cookies,
            json={"conversation_id": None},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("token") or data.get("sentinel_token") or data.get("chat_token") or ""
            if token:
                logger.debug(f"ChatGPTWeb: sentinel token obtained (len={len(token)})")
                return token
            logger.debug(f"ChatGPTWeb: sentinel response keys={list(data.keys())}")
        else:
            logger.warning(f"ChatGPTWeb: sentinel fetch failed HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"ChatGPTWeb: sentinel fetch error: {e}")
    return None


def _make_cookies(session_token: Optional[str] = None, cf_clearance: Optional[str] = None) -> Dict[str, str]:
    """Build cookies for ChatGPT requests.

    cf_clearance is IP-bound: only include it if HA and the user's browser share
    the same public IP (e.g. both on the same home network). If HA is behind NAT
    on the same router as the browser, they appear as the same IP to Cloudflare
    and cf_clearance will work correctly.
    """
    cookies: Dict[str, str] = {}
    if session_token:
        cookies["__Secure-next-auth.session-token"] = session_token
    if cf_clearance:
        cookies["cf_clearance"] = cf_clearance
    return cookies


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class ChatGPTWebProvider(EnhancedProvider):
    """ChatGPT Web unofficial provider (UNSTABLE)."""

    _FALLBACK_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.5",
        "gpt-5",
        "gpt-5.2",
        "chatgpt-4o-latest",
        "o1",
        "o3",
        "o3-mini",
        "o4-mini",
    ]

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key, model)
        self.rate_limiter = get_rate_limit_coordinator().get_limiter("chatgpt_web")

    @staticmethod
    def get_provider_name() -> str:
        return "chatgpt_web"

    def validate_credentials(self) -> bool:
        s = _stored_session
        return bool(s and s.get("access_token"))

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
        if not CFFI_AVAILABLE:
            yield {"type": "error", "message": "curl_cffi non installato. Riavvia l'addon per installarlo automaticamente."}
            return

        s = _stored_session
        if not s or not s.get("access_token"):
            yield {
                "type": "error",
                "message": "ChatGPT Web: not authenticated. Use the 🔑 button to connect.",
            }
            return

        can_req, wait = self.rate_limiter.can_request()
        if not can_req:
            raise RuntimeError(f"Rate limited. Wait {wait:.0f}s")
        self.rate_limiter.record_request()

        access_token  = s["access_token"]
        session_token = s.get("session_token")
        cf_clearance  = s.get("cf_clearance")
        device_id     = s.get("device_id")
        model         = self._resolve_model()

        # Normalise tool-call history → plain user/assistant messages
        from providers.tool_simulator import flatten_tool_messages
        messages = flatten_tool_messages(messages)

        # Build ChatGPT-style messages
        cgpt_messages = []
        for m in messages:
            role = m.get("role", "user")
            if role == "system":
                continue   # system prompt merged into first user message below
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(part.get("text", "") for part in content if isinstance(part, dict))
            cgpt_messages.append({
                "id": str(uuid.uuid4()),
                "author": {"role": role},
                "content": {"content_type": "text", "parts": [content]},
            })

        # Inject system prompt into first user message if present
        system_text = next(
            (c if isinstance(c, str) else (c[0].get("text", "") if c else "")
             for m in messages if m.get("role") == "system"
             for c in [m.get("content", "")]),
            ""
        )

        # ── Inject intent-specific instructions (no tool support in this provider) ──
        intent_name_local = (intent_info or {}).get("intent", "")
        tool_schemas = (intent_info or {}).get("tool_schemas") or []

        if intent_name_local == "create_html_dashboard":
            # HTML dashboard: keep free-form — each model produces a unique, creative page.
            no_tool_html = (
                "You are a creative Home Assistant HTML dashboard designer.\n"
                "The user wants a UNIQUE, beautiful STANDALONE HTML page — NOT YAML, NOT a Lovelace card.\n\n"
                "MANDATORY RULES — VIOLATION IS NOT ALLOWED:\n"
                "• Output a COMPLETE <!DOCTYPE html>...</html> page wrapped in ```html ... ```\n"
                "• YOUR FIRST LINE OF OUTPUT MUST BE: ```html\n"
                "• NEVER output YAML, 'vertical-stack', 'type: entities', 'type: custom:', "
                "  or ANY Lovelace / Home Assistant card format\n"
                "• Do NOT produce JSON, markdown lists, or explanatory text — ONLY the HTML block\n"
                "• Use a modern dark design with CSS animations, gradients, and card-based layout\n"
                "• Auth token + redirect if not logged in (ALWAYS at the start of <script>):\n"
                "    const tok = JSON.parse(localStorage.getItem('hassTokens')||'{}').access_token;\n"
                "    if (!tok) { location.href = '/?redirect=' + encodeURIComponent(location.href); }\n"
                "• Refresh every 5-10 seconds with setInterval\n"
                "• The HTML is automatically saved — no tool call, no explanation needed\n\n"
                "FETCHING ENTITIES — choose the right pattern:\n"
                "  A) Specific entity_ids (listed in CONTEXT/DATA): fetch each with /api/states/ENTITY_ID\n"
                "  B) 'All batteries', 'all lights', 'all temperatures', etc. — ALWAYS use:\n"
                "       fetch('/api/states', {headers:{Authorization:'Bearer '+tok}}).then(r=>r.json())\n"
                "     then filter the full list:\n"
                "       batteries:    states.filter(s => s.attributes?.device_class === 'battery')\n"
                "       temperatures: states.filter(s => s.attributes?.device_class === 'temperature')\n"
                "       lights:       states.filter(s => s.entity_id.startsWith('light.'))\n"
                "       motion:       states.filter(s => s.attributes?.device_class === 'motion')\n"
                "     NEVER hardcode a fixed list of entity_ids for 'all X' requests.\n"
                "     Filtering /api/states ensures ALL devices are shown, even ones not in CONTEXT.\n\n"
                "ENTITY CLICK — MORE INFO DIALOG:\n"
                "Make every entity card clickable (cursor:pointer). On click, call openMoreInfo(entityId).\n"
                "Always implement BOTH methods — native HA dialog + custom modal fallback:\n"
                "  function openMoreInfo(entityId) {\n"
                "    const haEl = document.querySelector('home-assistant') ||\n"
                "                 parent?.document?.querySelector('home-assistant');\n"
                "    if (haEl) {\n"
                "      haEl.dispatchEvent(new CustomEvent('hass-more-info',\n"
                "        { detail: { entityId }, bubbles: true, composed: true }));\n"
                "      return;\n"
                "    }\n"
                "    showHistoryModal(entityId);\n"
                "  }\n"
                "  async function showHistoryModal(entityId) {\n"
                "    const end = new Date().toISOString();\n"
                "    const start = new Date(Date.now()-24*3600*1000).toISOString();\n"
                "    const url = `/api/history/period/${start}?filter_entity_id=${entityId}&end_time=${end}&minimal_response`;\n"
                "    const data = await fetch(url,{headers:{Authorization:'Bearer '+tok}}).then(r=>r.json());\n"
                "    // data[0] = [{state,last_changed},...] — render in a modal overlay with Chart.js line chart\n"
                "    // Show: friendly name, current value+unit, 24h chart, last updated timestamp\n"
                "    // Close on backdrop click or X button\n"
                "  }\n"
            )
            system_text = no_tool_html + ("\n\n" + system_text if system_text else "")

        else:
            # ── Universal Tool Simulator for all other intents ──────────────────────
            from providers.tool_simulator import get_simulator_system_prompt
            sim_prompt = get_simulator_system_prompt(tool_schemas)

            intent_base_prompt = (intent_info or {}).get("prompt", "")

            combined = sim_prompt
            if intent_base_prompt:
                combined = intent_base_prompt + "\n\n" + combined
            system_text = combined + ("\n\n" + system_text if system_text else "")
        # ──────────────────────────────────────────────────────────────────────────────

        if system_text and cgpt_messages:
            first_user = next((m for m in cgpt_messages if m["author"]["role"] == "user"), None)
            if first_user:
                original = first_user["content"]["parts"][0]
                first_user["content"]["parts"][0] = f"{system_text}\n\n{original}"

        body = {
            "action": "next",
            "messages": cgpt_messages,
            "model": model,
            "conversation_id": None,
            "parent_message_id": str(uuid.uuid4()),
            "history_and_training_disabled": True,
            "stream": True,
            "timezone_offset_min": 0,
        }

        try:
            yield from self._stream_response(access_token, body, session_token, cf_clearance, device_id)
        except Exception as e:
            logger.error(f"ChatGPTWeb: Error during streaming: {e}")
            yield {"type": "error", "message": f"ChatGPT Web error: {e}"}

    def _stream_response(
        self, access_token: str, body: Dict[str, Any],
        session_token: Optional[str] = None, cf_clearance: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        # cf_clearance is included if provided — works when HA and browser share the same public IP
        # (e.g. both on the same home LAN behind the same router/NAT)
        cookies = _make_cookies(session_token, cf_clearance)
        if cf_clearance:
            logger.info("ChatGPTWeb: using cf_clearance cookie (same-IP mode)")
        last_text = ""

        # ChatGPT requires a sentinel token (*oai-sentinel-chat-requirements-token*)
        # obtained from /backend-api/sentinel/chat-requirements before every conversation.
        # Without it the conversation endpoint always returns 403 regardless of fingerprint.
        # Only fingerprints confirmed supported by curl_cffi >= 0.7
        # firefox117 removed — raises "Impersonating firefox117 is not supported"
        impersonate_targets = [
            "chrome131", "chrome124", "chrome120", "chrome116", "chrome110",
            "firefox133", "safari18_0",
        ]
        last_status = None
        resp = None

        for impersonate in impersonate_targets:
            # Step 1: fetch sentinel token with this fingerprint
            sentinel_token = _fetch_sentinel_token(access_token, device_id, session_token, impersonate, cf_clearance)

            # Step 2: build headers (include sentinel token if obtained)
            headers = _make_headers(access_token, device_id)
            if sentinel_token:
                headers["oai-sentinel-chat-requirements-token"] = sentinel_token

            # Step 3: send conversation request
            try:
                session = cffi_requests.Session(impersonate=impersonate)
                resp = session.post(
                    _CHATGPT_CONV_URL,
                    headers=headers,
                    cookies=cookies,
                    json=body,
                    stream=True,
                    timeout=90,
                )
            except Exception as imp_err:
                # curl_cffi raises ValueError if the fingerprint is not supported
                # by the installed version — skip and try next
                logger.warning(f"ChatGPTWeb: {impersonate} not supported by curl_cffi: {imp_err}")
                continue
            last_status = resp.status_code
            logger.info(f"ChatGPTWeb: {impersonate} → HTTP {resp.status_code}")
            if resp.status_code != 403:
                break
            # 403 with this fingerprint — try next one immediately
            # (all fingerprints get 403 when Cloudflare blocks the server IP — no point waiting)
            logger.warning(f"ChatGPTWeb: {impersonate} got 403, trying next fingerprint...")
            time.sleep(0.3)

        if last_status == 401:
            clear_session()
            raise RuntimeError(
                "Token scaduto — i JWT di ChatGPT durano poche ore. "
                "Vai su chatgpt.com/api/auth/session e incolla il nuovo accessToken con il pulsante 🔑."
            )
        if last_status == 403:
            cf_hint = (
                "\n• Sei sulla stessa rete di HA? Copia il cookie 'cf_clearance' da chatgpt.com "
                "(DevTools → Application → Cookies) e incollalo nel campo cf_clearance del pulsante 🔑"
            ) if not cf_clearance else (
                "\n• Il cf_clearance potrebbe essere scaduto (dura ~30 min) — ricopialo da DevTools"
            )
            raise RuntimeError(
                "❌ ChatGPT Web bloccato (403) — Cloudflare blocca le richieste dal server HA.\n\n"
                "Soluzioni:\n"
                "• Usa l'API OpenAI ufficiale (platform.openai.com) — stabile e stesso modello"
                + cf_hint +
                "\n• Attendi 10-15 minuti se l'errore è comparso di recente"
            )
        if last_status == 429:
            raise RuntimeError("ChatGPT rate limit. Attendi qualche minuto e riprova.")
        if last_status != 200:
            err = resp.text[:300] if hasattr(resp, 'text') else str(last_status)
            raise RuntimeError(f"HTTP {last_status}: {err}")

        for line in resp.iter_lines():
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="ignore")
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if not data_str or data_str == "[DONE]":
                if data_str == "[DONE]":
                    yield {"type": "done", "finish_reason": "stop"}
                continue
            try:
                event = json.loads(data_str)
                msg = event.get("message", {})
                if not msg:
                    continue

                content = msg.get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    continue

                full_text = parts[0] if isinstance(parts[0], str) else ""
                if full_text and full_text != last_text:
                    delta = full_text[len(last_text):]
                    if delta:
                        yield {"type": "text", "text": delta}
                    last_text = full_text

                status = msg.get("status")
                if status == "finished_successfully":
                    yield {"type": "done", "finish_reason": "stop"}
                    return

            except json.JSONDecodeError:
                continue

        yield {"type": "done", "finish_reason": "stop"}

    def _resolve_model(self) -> str:
        m = self.model or self._FALLBACK_MODELS[0]
        for prefix in ("chatgpt_web/", "chatgpt-web/"):
            if m.startswith(prefix):
                return m[len(prefix):]
        return m

    def get_available_models(self) -> List[str]:
        return list(self._FALLBACK_MODELS)

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        return {
            "auth_error": {
                "en": "ChatGPT Web: session expired. Reconnect via the 🔑 button.",
                "it": "ChatGPT Web: sessione scaduta. Riconnetti con il pulsante 🔑.",
                "es": "ChatGPT Web: sesión expirada. Reconéctate con 🔑.",
                "fr": "ChatGPT Web: session expirée. Reconnectez-vous via 🔑.",
            },
        }
