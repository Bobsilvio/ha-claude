"""GitHub Copilot provider - access to advanced models via GitHub Copilot subscription.

Authentication flow (Device Code OAuth):
  1. Use the 🔑 button in the Amira chat UI to start the GitHub Device Code flow.
  2. A code like "ABCD-1234" is shown — go to github.com/login/device and enter it.
  3. The backend polls automatically until the token is received and stored.
  4. The GitHub OAuth token is stored in /data/oauth_copilot.json and exchanged
     on each request for a short-lived Copilot session token.

Alternatively, set a static GitHub PAT (with 'copilot' scope) in Amira config
under 'GitHub Copilot Token' (takes priority over the stored OAuth token).
Requires an active GitHub Copilot subscription (Individual, Business, or Enterprise).
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator
from model_catalog import get_catalog

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.error("httpx not installed - required for GitHub Copilot streaming")

# ---------------------------------------------------------------------------
# GitHub Device Code OAuth constants
# ---------------------------------------------------------------------------
_GH_CLIENT_ID       = "Iv1.b507a08c87ecfe98"       # GitHub Copilot Vim/Neovim client
_GH_DEVICE_CODE_URL = "https://github.com/login/device/code"
_GH_TOKEN_URL       = "https://github.com/login/oauth/access_token"
_GH_SCOPE           = "copilot"
_GH_DEVICE_GRANT    = "urn:ietf:params:oauth:grant-type:device_code"

# GitHub Copilot API endpoints
_COPILOT_SESSION_URL  = "https://api.github.com/copilot_internal/v2/token"
_COPILOT_CHAT_URL     = "https://api.githubcopilot.com/chat/completions"
_COPILOT_MODELS_URL   = "https://api.githubcopilot.com/models"

# Persistence
_TOKEN_FILE = "/data/oauth_copilot.json"

# Reasoning / special models that do NOT accept temperature/top_p
_REASONING_MODEL_PREFIXES = ("o1", "o3", "oswe-")

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_stored_gh_token: Optional[Dict[str, Any]] = None   # {access_token, stored_at}
_pending_device: Optional[Dict[str, Any]] = None    # active device flow
_copilot_session: Optional[Dict[str, Any]] = None   # {token, expires_at_s}
_cached_models: Optional[List[str]] = None          # models discovered from API


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


def _load_token_from_disk() -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(_TOKEN_FILE):
            with open(_TOKEN_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Copilot: could not load token from disk: {e}")
    return None


def _save_token_to_disk(token: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_TOKEN_FILE), exist_ok=True)
        with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(token, f)
    except Exception as e:
        logger.warning(f"Copilot: could not save token: {e}")


_stored_gh_token = _load_token_from_disk()


# ---------------------------------------------------------------------------
# Dynamic model discovery
# ---------------------------------------------------------------------------

def get_copilot_models_cached() -> Optional[List[str]]:
    """Return the last-known list of Copilot models, or None if not yet discovered."""
    return list(_cached_models) if _cached_models else None


def _fetch_models_from_api(copilot_token: str) -> Optional[List[str]]:
    """Query the Copilot /models endpoint and return a list of chat-capable model IDs."""
    global _cached_models
    if not HTTPX_AVAILABLE:
        return None
    # Models that use a different API (e.g. /responses) and are NOT compatible
    # with the /chat/completions endpoint used by Amira.
    _INCOMPATIBLE_KEYWORDS = ("codex",)
    headers = {
        "Authorization": f"Bearer {copilot_token}",
        "Accept": "application/json",
        "Editor-Version": "vscode/1.100.0",
        "Editor-Plugin-Version": "copilot-chat/0.26.7",
        "User-Agent": "GitHubCopilotChat/0.26.7",
        "Copilot-Integration-Id": "vscode-chat",
        "X-GitHub-Api-Version": "2025-04-01",
    }
    try:
        resp = httpx.get(_COPILOT_MODELS_URL, headers=headers, timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            # Response: {"data": [{"id": "...", "capabilities": {"type": "chat"}}, ...]}
            models = [
                m["id"]
                for m in data.get("data", [])
                if isinstance(m, dict) and m.get("id")
                and not any(kw in m["id"].lower() for kw in _INCOMPATIBLE_KEYWORDS)
            ]
            if models:
                logger.info(f"GitHub Copilot: discovered {len(models)} models from API")
                _cached_models = sorted(models)
                return _cached_models
    except Exception as e:
        logger.debug(f"GitHub Copilot: model discovery failed: {e}")
    return None


# ---------------------------------------------------------------------------
# Public Device Code Flow helpers (called by api.py endpoints)
# ---------------------------------------------------------------------------

def start_device_flow() -> Dict[str, Any]:
    """Start GitHub Device Code flow. Returns {user_code, verification_uri, interval}."""
    global _pending_device
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx not installed")

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            _GH_DEVICE_CODE_URL,
            data={"client_id": _GH_CLIENT_ID, "scope": _GH_SCOPE},
            headers={"Accept": "application/json"},
        )
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub device code request failed ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    device_code  = data.get("device_code")
    user_code    = data.get("user_code")
    verification = data.get("verification_uri", "https://github.com/login/device")
    expires_in   = data.get("expires_in", 900)
    interval     = data.get("interval", 5)

    if not device_code or not user_code:
        raise RuntimeError("Incomplete device code response from GitHub.")

    _pending_device = {
        "device_code": device_code,
        "user_code": user_code,
        "verification_uri": verification,
        "interval": interval,
        "expires_at": int(time.time()) + expires_in,
    }
    logger.info(f"Copilot: Device flow started, user_code={user_code}")
    return {"user_code": user_code, "verification_uri": verification, "interval": interval, "expires_in": expires_in}


def poll_device_flow() -> Dict[str, Any]:
    """Poll GitHub for the access token. Returns {status: pending|success|error}."""
    global _pending_device, _stored_gh_token, _copilot_session
    if not _pending_device:
        return {"status": "error", "message": "No pending device flow — please restart."}
    if int(time.time()) > _pending_device["expires_at"]:
        _pending_device = None
        return {"status": "error", "message": "Device code expired — please restart."}
    if not HTTPX_AVAILABLE:
        return {"status": "error", "message": "httpx not installed"}

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                _GH_TOKEN_URL,
                data={
                    "client_id": _GH_CLIENT_ID,
                    "device_code": _pending_device["device_code"],
                    "grant_type": _GH_DEVICE_GRANT,
                },
                headers={"Accept": "application/json"},
            )
        data = resp.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    error = data.get("error")
    if error == "authorization_pending":
        return {"status": "pending"}
    if error == "slow_down":
        return {"status": "pending", "slow_down": True}
    if error in ("expired_token", "device_flow_disabled"):
        _pending_device = None
        return {"status": "error", "message": "Code expired or flow disabled — please restart."}
    if error == "access_denied":
        _pending_device = None
        return {"status": "error", "message": "Access denied by user."}
    if error:
        return {"status": "error", "message": f"GitHub error: {error}"}

    access_token = data.get("access_token")
    if not access_token:
        return {"status": "pending"}

    stored = {"access_token": access_token, "stored_at": int(time.time())}
    _stored_gh_token = stored
    _copilot_session = None   # invalidate cached session
    _save_token_to_disk(stored)
    _pending_device = None
    logger.info("Copilot: GitHub OAuth token stored successfully.")
    return {"status": "success"}


def get_token_status() -> Dict[str, Any]:
    """Return current token status (for the API status endpoint)."""
    t = _stored_gh_token
    if not t:
        return {"configured": False}
    age_days = (int(time.time()) - t.get("stored_at", 0)) // 86400
    return {"configured": True, "age_days": age_days}


def clear_token() -> None:
    """Clear the stored GitHub OAuth token (disconnect)."""
    global _stored_gh_token, _copilot_session
    _stored_gh_token = None
    _copilot_session = None
    try:
        if os.path.exists(_TOKEN_FILE):
            os.remove(_TOKEN_FILE)
    except Exception as e:
        logger.warning(f"Copilot: could not delete token file: {e}")
    logger.info("Copilot: GitHub OAuth token cleared.")


def _get_best_gh_token(config_api_key: str = "") -> Optional[str]:
    """Return the best available GitHub token (config PAT > stored OAuth)."""
    if config_api_key:
        return config_api_key
    t = _stored_gh_token
    return t.get("access_token") if t else None


def _get_copilot_session_token(gh_token: str) -> str:
    """Exchange GitHub token for a short-lived Copilot session token (cached ~25 min)."""
    global _copilot_session
    now = int(time.time())

    if _copilot_session and _copilot_session.get("expires_at_s", 0) - now > 60:
        return _copilot_session["token"]

    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx not installed")

    with httpx.Client(timeout=15.0) as client:
        resp = client.get(
            _COPILOT_SESSION_URL,
            headers={
                "Authorization": f"Bearer {gh_token}",
                "Accept": "application/json",
                "Editor-Version": "vscode/1.100.0",
                "Editor-Plugin-Version": "copilot-chat/0.26.7",
                "User-Agent": "GitHubCopilotChat/0.26.7",
                "X-GitHub-Api-Version": "2025-04-01",
            },
        )
    if resp.status_code == 401:
        raise RuntimeError("GitHub Copilot: token not authorized. Re-authenticate via the 🔑 button.")
    if resp.status_code == 403:
        raise RuntimeError("GitHub Copilot: access denied — requires an active Copilot subscription.")
    if resp.status_code != 200:
        raise RuntimeError(f"Copilot session token failed ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    token = data.get("token")
    if not token:
        raise RuntimeError("Empty session token returned by GitHub.")

    expires_at_s = now + 1500  # 25 min default
    expires_str = data.get("expires_at", "")
    if expires_str:
        try:
            import datetime
            dt = datetime.datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            expires_at_s = int(dt.timestamp())
        except Exception:
            pass

    _copilot_session = {"token": token, "expires_at_s": expires_at_s}
    logger.debug(f"Copilot: session token refreshed, valid for {expires_at_s - now}s")
    return token


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class GitHubCopilotProvider(EnhancedProvider):
    """Provider adapter for GitHub Copilot (Device Code OAuth + session token)."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize GitHub Copilot provider.

        Args:
            api_key: (optional) GitHub PAT with 'copilot' scope; if empty
                     the module-level stored OAuth token is used instead.
            model: Model identifier (e.g., gpt-5.3-codex)
        """
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "github_copilot"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate that a GitHub token is available."""
        if not HTTPX_AVAILABLE:
            return False, "httpx not installed (pip install httpx)"
        gh_token = _get_best_gh_token(self.api_key)
        if not gh_token:
            return False, (
                "GitHub Copilot: no token configured. "
                "Use the 🔑 button in Amira chat to authenticate, or set a PAT in config."
            )
        return True, ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat using GitHub Copilot API."""
        if not HTTPX_AVAILABLE:
            yield {
                "type": "error",
                "message": _t(
                    "httpx not installed (pip install httpx)",
                    "httpx non installato (pip install httpx)",
                    "httpx no instalado (pip install httpx)",
                    "httpx non installe (pip install httpx)",
                ),
            }
            return

        gh_token = _get_best_gh_token(self.api_key)
        if not gh_token:
            yield {
                "type": "error",
                "message": _t(
                    "GitHub Copilot: not authenticated. Use the 🔑 button in Amira chat to log in.",
                    "GitHub Copilot: non autenticato. Usa il pulsante 🔑 nella chat Amira per accedere.",
                    "GitHub Copilot: no autenticado. Usa el boton 🔑 en el chat de Amira para iniciar sesion.",
                    "GitHub Copilot : non authentifie. Utilise le bouton 🔑 dans le chat Amira pour te connecter.",
                ),
            }
            return

        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter("github_copilot")
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        self.rate_limiter.record_request()

        try:
            copilot_token = _get_copilot_session_token(gh_token)

            # Normalise tool-call history → plain user/assistant messages.
            # GitHub Copilot requires conversations to end with a user turn,
            # so after flattening we inject a continuation prompt if the last
            # message is an assistant turn (i.e. after a tool result round).
            from providers.tool_simulator import flatten_tool_messages
            # Use a smaller result limit to keep payloads manageable for Copilot
            messages = flatten_tool_messages(messages, max_result_chars=2000)
            if messages and messages[-1].get("role") == "assistant":
                messages = list(messages) + [{
                    "role": "user",
                    "content": (
                        "Continue. Use the tool results above to provide "
                        "the final answer to the user's original request."
                    ),
                }]

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
                    "• Poll HA states via: fetch('/api/states/ENTITY_ID', {headers:{Authorization:'Bearer '+tok}})\n"
                    "  where tok = JSON.parse(localStorage.getItem('hassTokens')||'{}').access_token || ''\n"
                    "• Refresh every 5 seconds with setInterval\n"
                    "• Include ALL the entity_ids provided in the CONTEXT section of the user message\n"
                    "• The HTML is automatically saved — no tool call, no explanation needed\n"
                )
                messages = self._inject_system(messages, no_tool_html)
            elif intent_name_local:
                from providers.tool_simulator import get_simulator_system_prompt
                sim_prompt = get_simulator_system_prompt(tool_schemas)
                intent_base_prompt = (intent_info or {}).get("prompt", "")
                combined = sim_prompt
                if intent_base_prompt:
                    combined = intent_base_prompt + "\n\n" + combined
                messages = self._inject_system(messages, combined)
            # ─────────────────────────────────────────────────────────────────────

            yield from self._do_stream(copilot_token, messages)
        except Exception as e:
            err_msg = str(e)
            logger.error(f"GitHub Copilot: Error during streaming: {e}")
            # If model is not chat-compatible for Copilot, remove it and show clear hint
            if ("model_not_supported" in err_msg) or ("unsupported_api_for_model" in err_msg):
                model_name = self._resolve_model()
                get_catalog().remove_model("github_copilot", model_name)
                yield {
                    "type": "error",
                    "message": _t(
                        "⚠️ Model '{model_name}' is not compatible with GitHub Copilot chat and was automatically removed from the list. Select another model.",
                        "⚠️ Il modello '{model_name}' non e' compatibile con la chat di GitHub Copilot ed e' stato rimosso automaticamente dalla lista. Seleziona un altro modello.",
                        "⚠️ El modelo '{model_name}' no es compatible con el chat de GitHub Copilot y se elimino automaticamente de la lista. Selecciona otro modelo.",
                        "⚠️ Le modele '{model_name}' n'est pas compatible avec le chat GitHub Copilot et a ete supprime automatiquement de la liste. Selectionne un autre modele.",
                        model_name=model_name,
                    ),
                }
            else:
                yield {"type": "error", "message": self.normalize_error_message(e)}

    def _do_stream(
        self, copilot_token: str, messages: List[Dict[str, Any]]
    ) -> Generator[Dict[str, Any], None, None]:
        """Low-level streaming call to GitHub Copilot chat API."""
        headers = {
            "Authorization": f"Bearer {copilot_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Editor-Version": "vscode/1.100.0",
            "Editor-Plugin-Version": "copilot-chat/0.26.7",
            "Copilot-Integration-Id": "vscode-chat",
            "Openai-Intent": "conversation-panel",
            "User-Agent": "GitHubCopilotChat/0.26.7",
            "X-GitHub-Api-Version": "2025-04-01",
        }
        resolved_model = self._resolve_model()
        # Guard: Codex models use the /responses API, not /chat/completions
        if "codex" in resolved_model.lower():
            raise RuntimeError(
                _t(
                    "Model '{resolved_model}' uses OpenAI /responses API and is not compatible with chat. Select another model (e.g. gpt-4o, claude-sonnet-4).",
                    "Il modello '{resolved_model}' usa l'API /responses di OpenAI e non e' compatibile con la chat. Seleziona un altro modello (es. gpt-4o, claude-sonnet-4).",
                    "El modelo '{resolved_model}' usa la API /responses de OpenAI y no es compatible con chat. Selecciona otro modelo (p. ej. gpt-4o, claude-sonnet-4).",
                    "Le modele '{resolved_model}' utilise l'API /responses d'OpenAI et n'est pas compatible avec le chat. Selectionne un autre modele (ex. gpt-4o, claude-sonnet-4).",
                    resolved_model=resolved_model,
                )
            )
        body: Dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
            "n": 1,
        }
        # Reasoning models (o1*, o3*) don't accept temperature / top_p
        if not resolved_model.startswith(_REASONING_MODEL_PREFIXES):
            body["temperature"] = 0.1
            body["top_p"] = 1
        _timeout = httpx.Timeout(connect=15.0, read=180.0, write=15.0, pool=10.0)
        # Log approximate payload size for debugging timeout issues
        _payload_chars = sum(len(m.get("content", "") or "") for m in messages)
        logger.debug(f"Copilot payload: {len(messages)} msgs, ~{_payload_chars} chars, model={resolved_model}")
        with httpx.stream(
            "POST", _COPILOT_CHAT_URL, headers=headers, json=body, timeout=_timeout
        ) as response:
            if response.status_code == 401:
                raise RuntimeError(
                    _t(
                        "GitHub Copilot: session token rejected. Re-authenticate via the 🔑 button.",
                        "GitHub Copilot: token di sessione rifiutato. Riautenticati con il pulsante 🔑.",
                        "GitHub Copilot: token de sesion rechazado. Vuelve a autenticarte con el boton 🔑.",
                        "GitHub Copilot : jeton de session rejete. Re-authentifie-toi via le bouton 🔑.",
                    )
                )
            if response.status_code == 403:
                raise RuntimeError(
                    _t(
                        "GitHub Copilot: access forbidden - check your Copilot subscription.",
                        "GitHub Copilot: accesso negato - controlla il tuo abbonamento Copilot.",
                        "GitHub Copilot: acceso denegado - revisa tu suscripcion de Copilot.",
                        "GitHub Copilot : acces refuse - verifie ton abonnement Copilot.",
                    )
                )
            if response.status_code != 200:
                error_text = response.read().decode("utf-8", errors="ignore")
                if response.status_code == 400 and "model_not_supported" in error_text:
                    logger.warning(f"GitHub Copilot: model '{resolved_model}' not supported")
                raise RuntimeError(f"HTTP {response.status_code}: {error_text[:400]}")

            captured_usage = None
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str or data_str == "[DONE]":
                    if data_str == "[DONE]":
                        done_event: dict = {"type": "done", "finish_reason": "stop"}
                        if captured_usage:
                            done_event["usage"] = captured_usage
                        yield done_event
                    continue
                try:
                    event = json.loads(data_str)
                    # Capture usage if present (some Copilot models include it)
                    if event.get("usage"):
                        captured_usage = event["usage"]
                    choices = event.get("choices", [])
                    if not choices:
                        continue
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield {"type": "text", "text": content}
                    finish = choice.get("finish_reason")
                    if finish:
                        done_event2: dict = {"type": "done", "finish_reason": finish}
                        if captured_usage:
                            done_event2["usage"] = captured_usage
                        yield done_event2
                except json.JSONDecodeError:
                    continue

    @staticmethod
    def _inject_system(messages: List[Dict[str, Any]], system_text: str) -> List[Dict[str, Any]]:
        """Prepend or merge a system prompt into the message list."""
        if not system_text:
            return messages
        # If there's already a system message, prepend to it
        for m in messages:
            if m.get("role") == "system":
                existing = m.get("content", "")
                if isinstance(existing, str):
                    m = dict(m)
                    m["content"] = system_text + "\n\n" + existing
                return [m if msg.get("role") == "system" else msg for msg in messages]
        # No system message — insert one at the beginning
        return [{"role": "system", "content": system_text}] + list(messages)

    def _resolve_model(self) -> str:
        """Normalize model name (strip provider prefix if present)."""
        m = self.model or "gpt-4o"
        for prefix in ("github_copilot/", "github-copilot/"):
            if m.startswith(prefix):
                return m[len(prefix):]
        return m

    # Static fallback — full known model list (replaces after first token-based refresh)
    _FALLBACK_MODELS = [
        # Claude
        "claude-opus-4.6-fast", "claude-opus-4.6",
        "claude-sonnet-4.6", "claude-sonnet-4.5", "claude-sonnet-4",
        "claude-haiku-4.5", "claude-opus-4.5",
        # GPT-5 family (chat-compatible only — codex models use /responses API)
        "gpt-5.1", "gpt-5.2", "gpt-5-mini",
        # GPT-4o family
        "gpt-4o", "gpt-4o-mini",
        # GPT-4.1
        "gpt-4.1",
        # Gemini
        "gemini-3.1-pro-preview", "gemini-3-pro-preview", "gemini-3-flash-preview",
        "gemini-2.5-pro",
        # Grok
        "grok-code-fast-1",
    ]

    def get_available_models(self) -> List[str]:
        """Return list of available GitHub Copilot models.

        Uses dynamic discovery from the /models endpoint when a valid session
        token is already cached, otherwise returns the safe static fallback.
        """
        global _cached_models
        # Use already-cached list if available
        if _cached_models:
            return list(_cached_models)
        # Try to get a session token (uses cached one if still valid)
        try:
            token = _get_copilot_session_token()
            if token:
                discovered = _fetch_models_from_api(token)
                if discovered:
                    return discovered
        except Exception:
            pass
        return list(self._FALLBACK_MODELS)

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get GitHub Copilot-specific error translations."""
        return {
            "auth_error": {
                "en": "GitHub Copilot: authentication failed. Re-authenticate via the 🔑 button.",
                "it": "GitHub Copilot: autenticazione non riuscita. Ri-autentica tramite il pulsante 🔑.",
                "es": "GitHub Copilot: fallo de autenticación. Re-autentícate con el botón 🔑.",
                "fr": "GitHub Copilot: échec d'authentification. Re-authentifiez-vous via 🔑.",
            },
            "no_subscription": {
                "en": "GitHub Copilot: Requires an active GitHub Copilot subscription.",
                "it": "GitHub Copilot: Richiede un abbonamento GitHub Copilot attivo.",
                "es": "GitHub Copilot: Requiere una suscripción activa a GitHub Copilot.",
                "fr": "GitHub Copilot: Nécessite un abonnement GitHub Copilot actif.",
            },
            "rate_limit": {
                "en": "GitHub Copilot: Rate limit exceeded. Please retry in a moment.",
                "it": "GitHub Copilot: Limite di velocità superato. Riprova tra un momento.",
                "es": "GitHub Copilot: Límite de velocidad excedido. Vuelva a intentarlo.",
                "fr": "GitHub Copilot: Limite de débit dépassée. Réessayez dans un instant.",
            },
        }

    def normalize_error_message(self, error: Exception) -> str:
        """Convert GitHub Copilot API error to user-friendly message."""
        msg = str(error).lower()
        if "401" in msg or "unauthorized" in msg or "token rejected" in msg:
            return "GitHub Copilot: token invalid or expired. Re-authenticate via the 🔑 button."
        if "403" in msg or "forbidden" in msg or "subscription" in msg:
            return "GitHub Copilot: access denied — check your active Copilot subscription."
        if "429" in msg or "rate limit" in msg:
            return "GitHub Copilot: rate limit exceeded. Please retry in a moment."
        return f"GitHub Copilot error: {error}"
