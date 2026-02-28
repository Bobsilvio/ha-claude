"""OpenAI Codex provider - access to advanced reasoning models via OAuth Bearer token.

Authentication flow:
  1. Use the 🔑 button in the Amira chat UI to start OAuth →
     opens the OpenAI login page in a new tab.
  2. After login, the browser redirects to localhost:1455 (which fails to load)
     → copy the full URL from the browser bar and paste it into the Amira modal.
  3. The token is exchanged automatically and stored in /data/oauth_codex.json.
  4. Auto-refresh: the token is silently renewed using the refresh_token before
     it expires — no manual action needed until the refresh_token is revoked.

Alternatively, set a static token in Amira config under 'OpenAI Codex Token'
(takes priority over the stored OAuth token). Requires ChatGPT Plus or Pro.
"""

import base64
import hashlib
import json
import logging
import os
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Generator, Tuple

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.error("httpx not installed - required for Codex streaming")

# ---------------------------------------------------------------------------
# OAuth constants (from oauth-cli-kit / OpenAI Codex CLI)
# ---------------------------------------------------------------------------
_OAUTH_CLIENT_ID   = "app_EMoamEEZ73f0CkXaXp7hrann"
_OAUTH_AUTHORIZE   = "https://auth.openai.com/oauth/authorize"
_OAUTH_TOKEN_URL   = "https://auth.openai.com/oauth/token"
_OAUTH_REDIRECT    = "http://localhost:1455/auth/callback"
_OAUTH_SCOPE       = "openid profile email offline_access"
_OAUTH_JWT_PATH    = "https://api.openai.com/auth"
_OAUTH_ACCOUNT_CL  = "chatgpt_account_id"

# Path where the token is persisted across restarts
_TOKEN_FILE = "/data/oauth_codex.json"

# ---------------------------------------------------------------------------
# Module-level token cache and pending-flow store
# (keyed by state string so concurrent flows are safe)
# ---------------------------------------------------------------------------
_stored_token: Optional[Dict[str, Any]] = None   # {access, refresh, expires, account_id}
_pending_flows: Dict[str, Dict[str, str]] = {}   # state → {verifier, challenge}

# Load token from disk once at import time
def _load_token_from_disk() -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(_TOKEN_FILE):
            with open(_TOKEN_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Codex: could not load token from disk: {e}")
    return None

_stored_token = _load_token_from_disk()


def _save_token_to_disk(token: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_TOKEN_FILE), exist_ok=True)
        with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(token, f)
    except Exception as e:
        logger.warning(f"Codex: could not save token: {e}")


# ---------------------------------------------------------------------------
# PKCE helpers (no external dependency)
# ---------------------------------------------------------------------------
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _generate_pkce() -> Tuple[str, str]:
    """Return (verifier, challenge)."""
    verifier  = _b64url(os.urandom(32))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge

def _create_state() -> str:
    return _b64url(os.urandom(16))

def _decode_account_id(access_token: str) -> Optional[str]:
    try:
        parts = access_token.split(".")
        if len(parts) != 3:
            return None
        pad = "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        auth = payload.get(_OAUTH_JWT_PATH) or {}
        val = auth.get(_OAUTH_ACCOUNT_CL)
        return str(val) if val else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public OAuth flow helpers (called by api.py endpoints)
# ---------------------------------------------------------------------------
def start_oauth_flow() -> str:
    """Generate PKCE + state, register pending flow, return authorize URL."""
    global _pending_flows
    verifier, challenge = _generate_pkce()
    state = _create_state()
    _pending_flows[state] = {"verifier": verifier, "challenge": challenge}
    params = {
        "response_type": "code",
        "client_id": _OAUTH_CLIENT_ID,
        "redirect_uri": _OAUTH_REDIRECT,
        "scope": _OAUTH_SCOPE,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "id_token_add_organizations": "true",
        "codex_cli_simplified_flow": "true",
        "originator": "ha-amira",
    }
    return f"{_OAUTH_AUTHORIZE}?{urllib.parse.urlencode(params)}", state


def exchange_code(redirect_url_or_code: str, state: str) -> Dict[str, Any]:
    """Exchange auth code for token. Returns token dict on success, raises on error."""
    global _stored_token, _pending_flows
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx not installed")

    flow = _pending_flows.pop(state, None)
    if not flow:
        raise RuntimeError("OAuth session expired or state mismatch — please restart the flow.")

    # Parse code from redirect URL or plain code string
    code: Optional[str] = None
    raw = redirect_url_or_code.strip()
    try:
        parsed = urllib.parse.urlparse(raw)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        url_state = qs.get("state", [None])[0]
        if url_state and url_state != state:
            raise RuntimeError("State mismatch — OAuth flow tampered or expired.")
    except RuntimeError:
        raise
    except Exception:
        pass
    if not code:
        code = raw  # treat raw input as the code itself

    data = {
        "grant_type": "authorization_code",
        "client_id": _OAUTH_CLIENT_ID,
        "code": code,
        "code_verifier": flow["verifier"],
        "redirect_uri": _OAUTH_REDIRECT,
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            _OAUTH_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Token exchange failed ({resp.status_code}): {resp.text[:300]}")

    payload = resp.json()
    access      = payload.get("access_token")
    refresh     = payload.get("refresh_token")
    expires_in  = payload.get("expires_in", 3600)
    if not access or not refresh:
        raise RuntimeError("Incomplete token response from OpenAI.")

    token = {
        "access": access,
        "refresh": refresh,
        "expires": int(time.time() * 1000 + expires_in * 1000),
        "account_id": _decode_account_id(access),
    }
    _stored_token = token
    _save_token_to_disk(token)
    logger.info("Codex: OAuth token stored successfully.")
    return token


def get_token_status() -> Dict[str, Any]:
    """Return current token status (for the API status endpoint)."""
    t = _stored_token
    if not t:
        return {"configured": False}
    now_ms = int(time.time() * 1000)
    expires_in_s = max(0, (t["expires"] - now_ms) // 1000)
    return {
        "configured": True,
        "expires_in_seconds": expires_in_s,
        "account_id": t.get("account_id"),
    }


def _refresh_stored_token() -> Optional[str]:
    """Silently refresh the stored token. Returns new access token or None."""
    global _stored_token
    t = _stored_token
    if not t or not t.get("refresh"):
        return None
    if not HTTPX_AVAILABLE:
        return None
    try:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": t["refresh"],
            "client_id": _OAUTH_CLIENT_ID,
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                _OAUTH_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code != 200:
            logger.warning(f"Codex: refresh failed ({resp.status_code})")
            return None
        payload = resp.json()
        access     = payload.get("access_token")
        refresh    = payload.get("refresh_token", t["refresh"])
        expires_in = payload.get("expires_in", 3600)
        if not access:
            return None
        new_token = {
            "access": access,
            "refresh": refresh,
            "expires": int(time.time() * 1000 + expires_in * 1000),
            "account_id": _decode_account_id(access),
        }
        _stored_token = new_token
        _save_token_to_disk(new_token)
        logger.info("Codex: token refreshed silently.")
        return access
    except Exception as e:
        logger.warning(f"Codex: refresh error: {e}")
        return None


def _get_best_access_token(config_api_key: str = "") -> Optional[str]:
    """Return the best available access token (config key > stored, auto-refresh)."""
    # 1. Static token from Amira config (highest priority)
    if config_api_key:
        return config_api_key

    # 2. Stored OAuth token (auto-refresh if expiring < 60s)
    t = _stored_token
    if not t:
        return None
    now_ms = int(time.time() * 1000)
    if t["expires"] - now_ms < 60_000:
        refreshed = _refresh_stored_token()
        return refreshed or (t["access"] if t["expires"] - now_ms > 0 else None)
    return t["access"]



class OpenAICodexProvider(EnhancedProvider):
    """Provider adapter for OpenAI Codex (OAuth Bearer token)."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize OpenAI Codex provider.

        Args:
            api_key: (optional) static Bearer token from Amira config;
                     if empty the module-level OAuth token is used instead.
            model: Model identifier (e.g., gpt-5.3-codex)
        """
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None
        self.api_url = "https://chatgpt.com/backend-api/codex/responses"
        self.verify_ssl = True

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "openai_codex"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate that a token is available (config key or stored OAuth)."""
        if not HTTPX_AVAILABLE:
            return False, "httpx not installed (pip install httpx)"
        token = _get_best_access_token(self.api_key)
        if token:
            return True, ""
        return False, (
            "OpenAI Codex: no token configured. "
            "Use the 🔑 button in Amira chat to authenticate, or set a static token in config."
        )

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat using OpenAI Codex Bearer token."""
        if not HTTPX_AVAILABLE:
            yield {"type": "error", "message": "httpx not installed (pip install httpx)"}
            return

        # Resolve token: config key (static) > stored OAuth token (auto-refresh)
        bearer = _get_best_access_token(self.api_key)
        if not bearer:
            yield {
                "type": "error",
                "message": "OpenAI Codex: not authenticated. Use the 🔑 button in Amira chat to log in.",
            }
            return

        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter("openai_codex")

        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")

        self.rate_limiter.record_request()

        try:
            # Normalise tool-call history → plain user/assistant messages
            from providers.tool_simulator import flatten_tool_messages
            messages = flatten_tool_messages(messages)

            # ── Inject intent-specific instructions (no native tool support) ──────
            intent_name_local = (intent_info or {}).get("intent", "")
            tool_schemas = (intent_info or {}).get("tool_schemas") or []

            if intent_name_local == "create_html_dashboard":
                no_tool_html = (
                    "You are a creative Home Assistant HTML dashboard designer.\n"
                    "The user wants a UNIQUE, beautiful STANDALONE HTML page — NOT YAML, NOT a Lovelace card.\n\n"
                    "MANDATORY RULES — VIOLATION IS NOT ALLOWED:\n"
                    "• Output a COMPLETE <!DOCTYPE html>...</html> page wrapped in ```html ... ```\n"
                    "• YOUR FIRST LINE OF OUTPUT MUST BE: ```html\n"
                    "• NEVER output YAML, 'vertical-stack', 'type: entities', 'type: custom:'"
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
                messages = self._prepend_system(messages, no_tool_html)
            elif intent_name_local:
                from providers.tool_simulator import get_simulator_system_prompt
                sim_prompt = get_simulator_system_prompt(tool_schemas)
                intent_base_prompt = (intent_info or {}).get("prompt", "")
                combined = sim_prompt
                if intent_base_prompt:
                    combined = intent_base_prompt + "\n\n" + combined
                messages = self._prepend_system(messages, combined)
            # ─────────────────────────────────────────────────────────────────────

            # Convert messages to Codex format
            system_prompt, input_items = self._convert_messages(messages)

            # Build request
            body = {
                "model": self._strip_model_prefix(self.model or "gpt-5.3-codex"),
                "store": False,
                "stream": True,
                "instructions": system_prompt,
                "input": input_items,
                "text": {"verbosity": "medium"},
                "include": ["reasoning.encrypted_content"],
                "prompt_cache_key": self._prompt_cache_key(messages),
                "tool_choice": "auto",
                "parallel_tool_calls": True,
            }

            headers = {
                "Authorization": f"Bearer {bearer}",
                "OpenAI-Beta": "responses=experimental",
                "originator": "ha-amira",
                "User-Agent": "ha-amira (python)",
                "accept": "text/event-stream",
                "content-type": "application/json",
            }
            
            # Stream response
            yield from self._stream_codex_response(headers, body)
            
        except Exception as e:
            logger.error(f"OpenAI Codex: Error during streaming: {e}")
            yield {
                "type": "error",
                "message": f"OpenAI Codex error: {str(e)}",
            }

    def _stream_codex_response(
        self, headers: Dict[str, str], body: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream response from Codex API."""
        try:
            _timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=5.0)
            with httpx.stream("POST", self.api_url, headers=headers, json=body, timeout=_timeout, verify=self.verify_ssl) as response:
                if response.status_code != 200:
                    error_text = response.read().decode("utf-8", errors="ignore")
                    raise RuntimeError(f"HTTP {response.status_code}: {error_text}")
                
                content = ""
                finish_reason = "stop"
                
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    
                    try:
                        data_str = line[5:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        
                        event = json.loads(data_str)
                        event_type = event.get("type")
                        
                        if event_type == "response.output_text.delta":
                            delta = event.get("delta", "")
                            if delta:
                                content += delta
                                yield {
                                    "type": "text",
                                    "text": delta,
                                }
                        
                        elif event_type == "response.completed":
                            status = (event.get("response") or {}).get("status")
                            finish_reason = self._map_finish_reason(status)
                        
                        elif event_type in {"error", "response.failed"}:
                            raise RuntimeError("Codex response failed")
                    
                    except json.JSONDecodeError:
                        continue
                
                yield {
                    "type": "done",
                    "finish_reason": finish_reason,
                }
        
        except Exception as e:
            logger.error(f"Codex streaming error: {e}")
            raise

    def get_available_models(self) -> List[str]:
        """Return list of available OpenAI Codex models.

        These are the model identifiers accepted by the ChatGPT-account Codex
        endpoint (chatgpt.com/backend-api/codex/responses).
        Generic OpenAI reasoning models (o3, o4-mini) are NOT supported here.
        """
        return [
            "gpt-5.3-codex",
            "gpt-5.3-codex-spark",
            "gpt-5.2-codex",
            "gpt-5.1-codex-max",
            "gpt-5.1-codex",
            "gpt-5-codex",
            "gpt-5-codex-mini",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get OpenAI Codex-specific error translations."""
        return {
            "auth_error": {
                "en": "OpenAI Codex: authentication failed. Check the token in Amira config.",
                "it": "OpenAI Codex: autenticazione non riuscita. Controlla il token nella config di Amira.",
                "es": "OpenAI Codex: fallo de autenticación. Verifica el token en la config de Amira.",
                "fr": "OpenAI Codex: échec d'authentification. Vérifiez le token dans la config Amira.",
            },
            "no_subscription": {
                "en": "OpenAI Codex: Requires ChatGPT Plus or Pro subscription",
                "it": "OpenAI Codex: Richiede abbonamento ChatGPT Plus o Pro",
                "es": "OpenAI Codex: Requiere suscripción ChatGPT Plus o Pro",
                "fr": "OpenAI Codex: Nécessite un abonnement ChatGPT Plus ou Pro",
            },
        }

    @staticmethod
    def _prepend_system(messages: List[Dict[str, Any]], system_text: str) -> List[Dict[str, Any]]:
        """Prepend or merge a system prompt into the message list."""
        if not system_text:
            return messages
        for m in messages:
            if m.get("role") == "system":
                existing = m.get("content", "")
                if isinstance(existing, str):
                    new_m = dict(m)
                    new_m["content"] = system_text + "\n\n" + existing
                    return [new_m if msg.get("role") == "system" else msg for msg in messages]
        return [{"role": "system", "content": system_text}] + list(messages)

    @staticmethod
    def _strip_model_prefix(model: str) -> str:
        """Remove prefix from model name."""
        if model.startswith("openai-codex/") or model.startswith("openai_codex/"):
            return model.split("/", 1)[1]
        return model

    @staticmethod
    def _prompt_cache_key(messages: List[Dict[str, Any]]) -> str:
        """Generate cache key for messages."""
        raw = json.dumps(messages, ensure_ascii=True, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _map_finish_reason(status: Optional[str]) -> str:
        """Map Codex status to finish reason."""
        mapping = {
            "completed": "stop",
            "incomplete": "length",
            "failed": "error",
            "cancelled": "error",
        }
        return mapping.get(status or "completed", "stop")

    @staticmethod
    def _convert_messages(messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        """Convert OpenAI format messages to Codex format."""
        system_prompt = ""
        input_items: List[Dict[str, Any]] = []

        for idx, msg in enumerate(messages):
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                system_prompt = content if isinstance(content, str) else ""
                continue

            if role == "user":
                if isinstance(content, str):
                    input_items.append({
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": content}],
                    })
                elif isinstance(content, list):
                    items = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                items.append({"type": "input_text", "text": item.get("text", "")})
                            elif item.get("type") == "image_url":
                                url = (item.get("image_url") or {}).get("url")
                                if url:
                                    items.append({"type": "input_image", "image_url": url})
                    if items:
                        input_items.append({
                            "type": "message",
                            "role": "user",
                            "content": items,
                        })

            elif role == "assistant":
                if isinstance(content, str) and content:
                    input_items.append({
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": content}],
                        "status": "completed",
                    })

        return system_prompt, input_items
