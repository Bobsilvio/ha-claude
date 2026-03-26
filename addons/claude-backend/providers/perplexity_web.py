"""Perplexity Web provider — unofficial cookie/session access to perplexity.ai.

⚠️ UNSTABLE: this uses private web endpoints and may break without notice.
Use official Perplexity API key provider for production workloads.
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
except Exception:
    HTTPX_AVAILABLE = False
    logger.error("httpx not installed — required for Perplexity Web")

_BASE_URL = "https://www.perplexity.ai"
_AUTH_SESSION_URL = f"{_BASE_URL}/api/auth/session"
_SSE_ASK_URL = f"{_BASE_URL}/rest/sse/perplexity_ask"
_TOKEN_FILE = "/data/session_perplexity_web.json"

_HEADERS = {
    "Accept": "text/event-stream",
    "Content-Type": "application/json",
    "Origin": _BASE_URL,
    "Referer": f"{_BASE_URL}/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
}

_stored_session: Optional[Dict[str, Any]] = None


def _load_session() -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(_TOKEN_FILE):
            with open(_TOKEN_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"PerplexityWeb: could not load session: {e}")
    return None


def _save_session(data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_TOKEN_FILE), exist_ok=True)
        with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"PerplexityWeb: could not save session: {e}")


def _make_cookies(csrf_token: str, session_token: str) -> Dict[str, str]:
    return {
        "next-auth.csrf-token": csrf_token,
        "next-auth.session-token": session_token,
    }


_stored_session = _load_session()


def store_session(csrf_token: str, session_token: str) -> Dict[str, Any]:
    """Validate and persist Perplexity Web cookies."""
    global _stored_session
    csrf_token = (csrf_token or "").strip()
    session_token = (session_token or "").strip()
    if not csrf_token or not session_token:
        raise ValueError("Missing csrf_token or session_token")

    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx not installed")

    cookies = _make_cookies(csrf_token, session_token)
    try:
        r = httpx.get(
            _AUTH_SESSION_URL,
            headers={k: v for k, v in _HEADERS.items() if k not in ("Accept", "Content-Type")},
            cookies=cookies,
            timeout=15.0,
            follow_redirects=True,
        )
    except Exception as e:
        raise RuntimeError(f"Perplexity Web unreachable: {e}") from e

    if r.status_code != 200:
        raise RuntimeError(f"Perplexity Web auth check failed (HTTP {r.status_code}).")

    try:
        j = r.json() if r.content else {}
    except Exception:
        j = {}

    user = j.get("user") if isinstance(j, dict) else None
    if not user:
        raise RuntimeError("Cookies rejected by Perplexity Web. Copy fresh cookies from your browser.")

    data = {
        "csrf_token": csrf_token,
        "session_token": session_token,
        "stored_at": int(time.time()),
        "email": user.get("email", "") if isinstance(user, dict) else "",
        "ok": True,
    }
    _stored_session = data
    _save_session(data)
    logger.info("PerplexityWeb: session stored")
    return data


def get_session_status() -> Dict[str, Any]:
    s = _stored_session
    if not s:
        return {"configured": False}
    age_days = (int(time.time()) - s.get("stored_at", 0)) // 86400
    return {
        "configured": True,
        "age_days": age_days,
        "email": s.get("email", ""),
    }


def clear_session() -> None:
    global _stored_session
    _stored_session = None
    try:
        if os.path.exists(_TOKEN_FILE):
            os.remove(_TOKEN_FILE)
    except Exception:
        pass


class PerplexityWebProvider(EnhancedProvider):
    """Unofficial Perplexity Web provider (cookie/session based)."""

    _MODEL_ROUTE = {
        # Auto/deep-research
        "pplx_auto": ("concise", "turbo"),
        "pplx_deep_research": ("copilot", "pplx_alpha"),
        # Pro lane
        "pplx_pro": ("copilot", "pplx_pro"),
        "sonar-pro": ("copilot", "pplx_pro"),
        "sonar": ("copilot", "experimental"),
        "gpt-5.2": ("copilot", "gpt52"),
        "gpt-5.4": ("copilot", "gpt54"),
        "claude-4.5-sonnet": ("copilot", "claude45sonnet"),
        "claude-4.6-sonnet": ("copilot", "claude46sonnet"),
        "claude-4.6-opus": ("copilot", "claude46opus"),
        "grok-4-1": ("copilot", "grok41nonreasoning"),
        "gemini-3.1-pro": ("copilot", "gemini31pro"),
        "nemotron-3-super": ("copilot", "nemotron3super"),
        # Reasoning lane
        "pplx_reasoning": ("copilot", "pplx_reasoning"),
        "sonar-reasoning": ("copilot", "pplx_reasoning"),
        "sonar-reasoning-pro": ("copilot", "pplx_reasoning"),
        "gpt-5.2-thinking": ("copilot", "gpt52_thinking"),
        "claude-4.5-sonnet-thinking": ("copilot", "claude45sonnetthinking"),
        "gemini-3.0-pro": ("copilot", "gemini30pro"),
        "kimi-k2-thinking": ("copilot", "kimik2thinking"),
        "grok-4.1-reasoning": ("copilot", "grok41reasoning"),
    }

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key, model)
        self.rate_limiter = get_rate_limit_coordinator().get_limiter("perplexity_web")

    @staticmethod
    def get_provider_name() -> str:
        return "perplexity_web"

    def validate_credentials(self) -> bool:
        s = _stored_session
        return bool(s and s.get("csrf_token") and s.get("session_token"))

    def get_available_models(self) -> List[str]:
        return [
            "sonar",
            "gpt-5.2",
            "gpt-5.4",
            "claude-4.5-sonnet",
            "claude-4.6-sonnet",
            "claude-4.6-opus",
            "grok-4-1",
            "gemini-3.1-pro",
            "nemotron-3-super",
            "gpt-5.2-thinking",
            "claude-4.5-sonnet-thinking",
            "gemini-3.0-pro",
            "kimi-k2-thinking",
            "grok-4.1-reasoning",
            # Compatibility aliases
            "pplx_pro",
            "pplx_reasoning",
            "pplx_auto",
            "pplx_deep_research",
        ]

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        yield from self.stream_chat(messages, intent_info)

    def _resolve_mode_and_pref(self) -> tuple[str, str]:
        m = (self.model or "grok-4-1").strip().lower()
        return self._MODEL_ROUTE.get(m, ("copilot", "grok41nonreasoning"))

    @staticmethod
    def _extract_answer(payload: Dict[str, Any]) -> str:
        if not isinstance(payload, dict):
            return ""
        direct = payload.get("answer")
        if isinstance(direct, str) and direct.strip():
            return direct
        if isinstance(direct, dict):
            a = direct.get("answer")
            if isinstance(a, str) and a.strip():
                return a.strip()

        out_text = payload.get("output")
        if isinstance(out_text, str) and out_text.strip():
            return out_text.strip()

        text_field = payload.get("text")
        if not isinstance(text_field, str) or not text_field:
            return ""
        try:
            parsed = json.loads(text_field)
        except Exception:
            # Some frames may carry plain text deltas in "text".
            return text_field.strip()
        if not isinstance(parsed, list):
            return text_field.strip()
        for step in parsed:
            if not isinstance(step, dict):
                continue
            if step.get("step_type") != "FINAL":
                continue
            content = step.get("content") or {}
            if not isinstance(content, dict):
                continue
            ans_json = content.get("answer")
            if not isinstance(ans_json, str) or not ans_json:
                continue
            try:
                ans = json.loads(ans_json)
            except Exception:
                continue
            if isinstance(ans, dict):
                answer = ans.get("answer")
                if isinstance(answer, str):
                    return answer
        return ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        if not HTTPX_AVAILABLE:
            yield {"type": "error", "message": "httpx not installed"}
            return

        s = _stored_session
        if not s or not s.get("csrf_token") or not s.get("session_token"):
            yield {
                "type": "error",
                "message": "Perplexity Web: not authenticated. Use the 🔑 button to connect.",
            }
            return

        can_req, wait = self.rate_limiter.can_request()
        if not can_req:
            raise RuntimeError(f"Rate limited. Wait {wait:.0f}s")
        self.rate_limiter.record_request()

        from providers.tool_simulator import flatten_tool_messages
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
            user_text = "Ciao"

        # Align with claude_web behavior: inject ToolSimulator instructions
        # so no-tool web providers emit <tool_call> blocks instead of plain prose.
        try:
            intent_name_local = (intent_info or {}).get("intent", "")
            tool_schemas = (intent_info or {}).get("tool_schemas") or []
            intent_base_prompt = (intent_info or {}).get("prompt", "")
            from providers.tool_simulator import get_simulator_system_prompt
            sim_prompt = get_simulator_system_prompt(tool_schemas)
            if (intent_info or {}).get("active_skill"):
                # Skill mode: only SKILL.md instructions needed — no tool simulator.
                prepend = (intent_base_prompt.strip() + "\n\n") if intent_base_prompt else ""
            elif intent_name_local == "create_html_dashboard":
                # Keep HTML flow raw text in this provider (auto-save handled in api.py).
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
                    "[SYSTEM INSTRUCTIONS — MUST FOLLOW]\n"
                    + prepend.strip()
                    + "\n[/SYSTEM INSTRUCTIONS]\n\n"
                    + user_text
                ).strip()
        except Exception as _sim_err:
            logger.debug(f"PerplexityWeb: simulator prompt injection skipped: {_sim_err}")
        mode, model_pref = self._resolve_mode_and_pref()

        json_data = {
            "query_str": user_text,
            "params": {
                "attachments": [],
                "frontend_context_uuid": str(uuid.uuid4()),
                "frontend_uuid": str(uuid.uuid4()),
                "is_incognito": False,
                "language": "it-IT",
                "last_backend_uuid": None,
                "mode": mode,
                "model_preference": model_pref,
                "source": "default",
                "sources": ["web"],
                "version": "2.18",
            },
        }

        cookies = _make_cookies(s["csrf_token"], s["session_token"])
        last_answer = ""
        _started = time.time()
        _events = 0
        _content_chunks = 0
        _read_timeout = float(os.getenv("PERPLEXITY_WEB_READ_TIMEOUT", "25"))
        _timeout = httpx.Timeout(connect=15.0, read=_read_timeout, write=30.0, pool=15.0)
        logger.info(
            "PerplexityWeb: request start (model=%s mode=%s pref=%s qlen=%s)",
            (self.model or "grok-4-1"),
            mode,
            model_pref,
            len(user_text),
        )
        try:
            with httpx.Client(headers=_HEADERS, cookies=cookies, timeout=_timeout, follow_redirects=True) as client:
                with client.stream("POST", _SSE_ASK_URL, json=json_data) as resp:
                    logger.info("PerplexityWeb: stream opened (http=%s)", resp.status_code)
                    if resp.status_code == 401:
                        logger.warning("PerplexityWeb: unauthorized session (401)")
                        yield {
                            "type": "error",
                            "message": "Perplexity Web: unauthorized session. Reconnect with fresh cookies.",
                        }
                        return
                    if resp.status_code >= 400:
                        body = ""
                        try:
                            body = resp.read().decode("utf-8", errors="ignore")
                        except Exception:
                            body = ""
                        logger.warning("PerplexityWeb: HTTP %s error body=%s", resp.status_code, body[:220])
                        yield {
                            "type": "error",
                            "message": f"Perplexity Web HTTP {resp.status_code}: {body[:220]}",
                        }
                        return

                    event_type = ""
                    data_lines: List[str] = []
                    for line in resp.iter_lines():
                        if line is None:
                            continue
                        _events += 1
                        line = line.strip()
                        if line == "":
                            if event_type == "message" and data_lines:
                                try:
                                    payload = json.loads("\n".join(data_lines))
                                except Exception:
                                    payload = {}
                                answer = self._extract_answer(payload)
                                if answer and answer != last_answer:
                                    delta = answer[len(last_answer):] if answer.startswith(last_answer) else answer
                                    if delta:
                                        _content_chunks += 1
                                        # Use "text" events so API stream normalization
                                        # converts them to UI "token" chunks.
                                        yield {"type": "text", "text": delta, "content": delta}
                                    last_answer = answer
                            elif event_type == "end_of_stream":
                                break
                            event_type = ""
                            data_lines = []
                            continue
                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            continue
                        if line.startswith("data:"):
                            data_lines.append(line[5:].strip())
                            continue
                    logger.info(
                        "PerplexityWeb: stream done (events=%s chunks=%s chars=%s elapsed=%.2fs)",
                        _events,
                        _content_chunks,
                        len(last_answer or ""),
                        (time.time() - _started),
                    )
                    yield {"type": "done", "usage": None}
        except Exception as e:
            logger.warning(
                "PerplexityWeb: stream error (%s) after %.2fs, events=%s chunks=%s",
                type(e).__name__,
                (time.time() - _started),
                _events,
                _content_chunks,
            )
            if isinstance(e, httpx.ReadTimeout):
                yield {
                    "type": "error",
                    "message": (
                        f"Perplexity Web timeout after {_read_timeout:.0f}s without stream progress. "
                        "Retry or switch model."
                    ),
                }
                return
            yield {"type": "error", "message": f"Perplexity Web error: {e}"}
