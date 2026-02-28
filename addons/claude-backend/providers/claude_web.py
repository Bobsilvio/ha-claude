"""Claude.ai Web provider — unofficial session-based access to Claude.ai.

⚠️  UNSTABLE: this uses the private Claude.ai web API which can change at any time
    and is not endorsed by Anthropic. Use the official Anthropic API key provider
    for production use.

Authentication:
  1. Click the 🔑 button → "Connect Claude.ai Web"
  2. Open https://claude.ai in your browser and log in
  3. Open DevTools (F12) → Application → Cookies → claude.ai
  4. Copy the value of the 'sessionKey' cookie  (starts with sk-ant-sid01-)
  5. Paste it in the Amira modal and click Connect

The session is stored in /data/session_claude_web.json and reused until it
expires or is revoked.
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
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.error("httpx not installed — required for Claude Web streaming")

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
_CLAUDE_BASE = "https://claude.ai/api"
_ORG_URL     = f"{_CLAUDE_BASE}/organizations"
_TOKEN_FILE  = "/data/session_claude_web.json"

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_stored_session: Optional[Dict[str, Any]] = None   # {session_key, org_uuid, stored_at}


def _load_session() -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(_TOKEN_FILE):
            with open(_TOKEN_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"ClaudeWeb: could not load session: {e}")
    return None


def _save_session(data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_TOKEN_FILE), exist_ok=True)
        with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"ClaudeWeb: could not save session: {e}")


_stored_session = _load_session()


# ---------------------------------------------------------------------------
# Public auth helpers
# ---------------------------------------------------------------------------

def store_session_key(session_key: str) -> Dict[str, Any]:
    """Validate session key, fetch org UUID, and persist to disk.

    Returns the stored session dict.
    Raises RuntimeError if the key is invalid or the API is unreachable.
    """
    global _stored_session
    key = session_key.strip()
    if not key:
        raise ValueError("Empty session key")

    headers = _make_headers(key)
    try:
        resp = httpx.get(_ORG_URL, headers=headers, timeout=10.0)
    except Exception as e:
        raise RuntimeError(f"Claude.ai unreachable: {e}") from e

    if resp.status_code == 403:
        raise RuntimeError("Session key rejected by Claude.ai — please try again with a fresh key.")
    if resp.status_code != 200:
        raise RuntimeError(f"Claude.ai returned HTTP {resp.status_code} when fetching org info.")

    orgs = resp.json()
    if not orgs:
        raise RuntimeError("No organisations found for this account.")

    org_uuid = orgs[0].get("uuid") or orgs[0].get("id")
    if not org_uuid:
        raise RuntimeError("Could not extract organisation UUID from response.")

    data = {
        "session_key": key,
        "org_uuid": org_uuid,
        "stored_at": int(time.time()),
        "ok": True,
    }
    _stored_session = data
    _save_session(data)
    logger.info(f"ClaudeWeb: session stored (org={org_uuid[:8]}...)")
    return data


def get_session_status() -> Dict[str, Any]:
    """Return current session status."""
    s = _stored_session
    if not s:
        return {"configured": False}
    age_days = (int(time.time()) - s.get("stored_at", 0)) // 86400
    return {"configured": True, "age_days": age_days, "org_uuid": s.get("org_uuid", "")[:8] + "..."}


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

def _make_headers(session_key: str) -> Dict[str, str]:
    return {
        "Cookie": f"sessionKey={session_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "anthropic-client-platform": "web_claude_ai",
        "User-Agent": "Mozilla/5.0 (compatible; ha-amira)",
        "Referer": "https://claude.ai/",
        "Origin": "https://claude.ai",
    }


def _create_conversation(session_key: str, org_uuid: str, model: str, system_prompt: str = "") -> str:
    """Create a new conversation and return its UUID."""
    url = f"{_CLAUDE_BASE}/organizations/{org_uuid}/chat_conversations"
    body = {
        "uuid": str(uuid.uuid4()),
        "name": "",
        "model": model,
    }
    # Pass system_prompt at conversation creation — Claude.ai stores it server-side
    # so it never appears as visible text in the conversation history.
    if system_prompt:
        body["system_prompt"] = system_prompt
    resp = httpx.post(url, headers=_make_headers(session_key), json=body, timeout=15.0)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create conversation: HTTP {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    conv_id = data.get("uuid") or data.get("id")
    if not conv_id:
        raise RuntimeError("No conversation UUID in response")
    return conv_id


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class ClaudeWebProvider(EnhancedProvider):
    """Claude.ai Web unofficial provider (UNSTABLE)."""

    _FALLBACK_MODELS = [
        "claude-opus-4-6",               # ✅ rilasciato 5 feb 2026
        "claude-sonnet-4-6",             # ✅ rilasciato 17 feb 2026
        "claude-opus-4-5-20251101",      # ✅ confermato
        "claude-sonnet-4-5-20250929",    # ✅ confermato
        "claude-haiku-4-5-20251001",     # ✅ confermato (Haiku 4.6 non ancora disponibile)
    ]

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key, model)
        self.rate_limiter = get_rate_limit_coordinator().get_limiter("claude_web")

    @staticmethod
    def get_provider_name() -> str:
        return "claude_web"

    def validate_credentials(self) -> bool:
        s = _stored_session
        return bool(s and s.get("session_key") and s.get("org_uuid"))

    # EnhancedProvider calls _do_stream from stream_chat_with_caching
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
        if not s or not s.get("session_key"):
            yield {
                "type": "error",
                "message": "Claude.ai Web: not authenticated. Use the 🔑 button to connect.",
            }
            return

        can_req, wait = self.rate_limiter.can_request()
        if not can_req:
            raise RuntimeError(f"Rate limited. Wait {wait:.0f}s")
        self.rate_limiter.record_request()

        session_key = s["session_key"]
        org_uuid    = s["org_uuid"]
        model       = self._resolve_model()

        # Normalise tool-call history → plain user/assistant messages
        from providers.tool_simulator import flatten_tool_messages
        messages = flatten_tool_messages(messages)

        # Build Claude.ai style message list
        system_prompt, human_messages = self._split_messages(messages)

        # ── Inject intent-specific instructions (no tool support in this provider) ──
        intent_name_local = (intent_info or {}).get("intent", "")
        tool_schemas = (intent_info or {}).get("tool_schemas") or []

        if intent_name_local == "create_html_dashboard":
            # HTML dashboard: keep free-form — each model produces a unique, creative page.
            # No tool_call blocks needed; api.py auto-saves the HTML from the response text.
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
                "• Poll HA states via: fetch('/api/states/ENTITY_ID', {headers:{Authorization:'Bearer '+tok}})\n"
                "  where tok comes from: localStorage.getItem('hassTokens') parsed as JSON .access_token\n"
                "• Refresh every 5 seconds with setInterval\n"
                "• Include ALL the entity_ids provided in the CONTEXT section of the user message\n"
                "• The HTML is automatically saved — no tool call, no explanation needed\n"
            )
            system_prompt = no_tool_html + ("\n\n" + system_prompt if system_prompt else "")

        else:
            # ── Universal Tool Simulator for all other intents ──────────────────────
            from providers.tool_simulator import get_simulator_system_prompt
            sim_prompt = get_simulator_system_prompt(tool_schemas)

            intent_base_prompt = (intent_info or {}).get("prompt", "")

            combined = sim_prompt
            if intent_base_prompt:
                combined = intent_base_prompt + "\n\n" + combined
            system_prompt = combined + ("\n\n" + system_prompt if system_prompt else "")
        # ──────────────────────────────────────────────────────────────────────────────

        # Create conversation now that we have the system_prompt — pass it at creation
        # so Claude.ai stores it server-side and it never appears as visible text.
        try:
            conv_uuid = _create_conversation(session_key, org_uuid, model, system_prompt)
        except Exception as e:
            yield {"type": "error", "message": f"ClaudeWeb: {e}"}
            return

        # Build conversation history + last human message.
        # claude_web creates a fresh conversation each call, so we must
        # reconstruct the full dialogue in the prompt to preserve context.
        # (Tool results are already merged into assistant turns by flatten_tool_messages above.)
        history_parts = []
        last_human = ""

        for m in human_messages:
            role = m.get("role", "")
            c = m.get("content", "")
            text = c if isinstance(c, str) else (c[0].get("text", "") if c else "")

            if role == "user":
                last_human = text
                history_parts.append(f"Human: {text}")

            elif role == "assistant":
                history_parts.append(f"Assistant: {text}")

        # If there is real history (more than just the last turn), prepend it
        if len(history_parts) > 1:
            history_block = "\n\n".join(history_parts[:-1])  # all turns except the last
            conversation_context = (
                f"[CONVERSATION HISTORY]\n{history_block}\n[/CONVERSATION HISTORY]\n\n"
                f"Human: {last_human}"
            )
        else:
            conversation_context = last_human

        # System prompt is passed at conversation creation (server-side) — use plain prompt.
        prompt_text = conversation_context

        body = {
            "prompt": prompt_text,
            "model": model,
            "timezone": "UTC",
            "attachments": [],
            "files": [],
            "rendering_mode": "raw",
        }

        url = f"{_CLAUDE_BASE}/organizations/{org_uuid}/chat_conversations/{conv_uuid}/completion"

        try:
            yield from self._stream_response(url, session_key, body)
        except Exception as e:
            logger.error(f"ClaudeWeb: Error during streaming: {e}")
            yield {"type": "error", "message": f"Claude.ai Web error: {e}"}

    def _stream_response(
        self, url: str, session_key: str, body: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        headers = _make_headers(session_key)
        _timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=5.0)
        with httpx.stream("POST", url, headers=headers, json=body, timeout=_timeout) as resp:
            if resp.status_code == 401:
                clear_session()  # force banner to reappear
                raise RuntimeError("Session expired — please reconnect via the 🔑 button.")
            if resp.status_code == 403:
                raise RuntimeError("Access forbidden — session may be expired or invalid.")
            if resp.status_code != 200:
                err = resp.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"HTTP {resp.status_code}: {err[:300]}")

            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str or data_str == "[DONE]":
                    continue
                try:
                    event = json.loads(data_str)
                    # Classic SSE format: {"type": "completion", "completion": "..."}
                    ev_type = event.get("type")
                    if ev_type == "completion":
                        text = event.get("completion", "")
                        if text:
                            yield {"type": "text", "text": text}
                    elif ev_type == "message_delta":
                        # Newer format
                        delta = event.get("delta", {})
                        text = delta.get("text", "")
                        if text:
                            yield {"type": "text", "text": text}
                    elif ev_type == "content_block_delta":
                        text = (event.get("delta") or {}).get("text", "")
                        if text:
                            yield {"type": "text", "text": text}
                    elif ev_type == "message_stop":
                        yield {"type": "done", "finish_reason": "stop"}
                        return
                    elif ev_type == "error":
                        msg = event.get("error", {}).get("message", "Unknown error")
                        raise RuntimeError(f"Claude.ai error: {msg}")
                except json.JSONDecodeError:
                    continue

        yield {"type": "done", "finish_reason": "stop"}

    def _resolve_model(self) -> str:
        m = self.model or self._FALLBACK_MODELS[0]
        for prefix in ("claude_web/", "claude-web/"):
            if m.startswith(prefix):
                return m[len(prefix):]
        return m

    def _split_messages(self, messages: List[Dict[str, Any]]):
        """Separate system prompt from human/assistant messages."""
        system = ""
        rest = []
        for m in messages:
            if m.get("role") == "system":
                c = m.get("content", "")
                system = c if isinstance(c, str) else (c[0].get("text", "") if c else "")
            else:
                rest.append(m)
        return system, rest

    def get_available_models(self) -> List[str]:
        return list(self._FALLBACK_MODELS)

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        return {
            "auth_error": {
                "en": "Claude.ai Web: session expired. Reconnect via the 🔑 button.",
                "it": "Claude.ai Web: sessione scaduta. Riconnetti con il pulsante 🔑.",
                "es": "Claude.ai Web: sesión expirada. Reconéctate con 🔑.",
                "fr": "Claude.ai Web: session expirée. Reconnectez-vous via 🔑.",
            },
        }
