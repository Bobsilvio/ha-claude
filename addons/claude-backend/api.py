"""Amira AI Assistant API with multi-provider support for Home Assistant."""

import os
import json
import logging
import queue
import re
import shutil
import time
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify, Response, stream_with_context, g, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from werkzeug.exceptions import HTTPException

import tools
import intent
from providers import stream_chat as provider_stream_chat
import pricing
import chat_ui
from core.translations import LANGUAGE_TEXT, get_lang_text, tr
from core.image_helpers import parse_image_data, format_message_with_image_anthropic, format_message_with_image_openai, format_message_with_image_google
from core.model_utils import normalize_model_name, get_model_provider, validate_model_provider_compatibility, get_active_model
from core.error_utils import humanize_provider_error, _extract_http_error_code, _extract_remote_message
from services.model_service import (
    NVIDIA_MODEL_BLOCKLIST, NVIDIA_MODEL_TESTED_OK, MODEL_BLOCKLIST_FILE,
    NVIDIA_MODEL_UNCERTAIN, PROVIDER_MODEL_TESTED_OK, PROVIDER_MODEL_UNCERTAIN,
    _NVIDIA_MODELS_CACHE, _NVIDIA_MODELS_CACHE_TTL_SECONDS,
    load_model_blocklists, save_model_blocklists, mark_nvidia_model_tested_ok,
    mark_nvidia_model_uncertain, mark_provider_model_tested_ok, mark_provider_model_uncertain,
    blocklist_nvidia_model, blocklist_model, _fetch_nvidia_models_live, get_nvidia_models_cached
)
import services.settings_service as settings_service
from services.settings_service import (
    RUNTIME_SELECTION_FILE, SETTINGS_FILE, MCP_RUNTIME_FILE,
    SETTINGS_DEFAULTS, _SETTINGS_GLOBAL_MAP,
    _load_settings, _save_settings, _load_mcp_runtime_state, _save_mcp_runtime_state,
    _set_mcp_server_autostart
)
import services.prompt_service as prompt_service
from services.prompt_service import (
    CUSTOM_SYSTEM_PROMPT_FILE, AGENTS_FILE, CONFIG_EDITABLE_FILES,
    _load_custom_system_prompt_from_disk, _persist_custom_system_prompt_to_disk
)

# Optional feature modules
try:
    import memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    import file_upload
    FILE_UPLOAD_AVAILABLE = True
except ImportError:
    FILE_UPLOAD_AVAILABLE = False
    
try:
    import rag
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    import mcp
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

try:
    import fallback
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False

try:
    import model_catalog
    MODEL_CATALOG_AVAILABLE = True
except ImportError:
    MODEL_CATALOG_AVAILABLE = False

try:
    import agent_config
    AGENT_CONFIG_AVAILABLE = True
except ImportError:
    AGENT_CONFIG_AVAILABLE = False

try:
    import model_fallback
    MODEL_FALLBACK_AVAILABLE = True
except ImportError:
    MODEL_FALLBACK_AVAILABLE = False

try:
    import semantic_cache
    SEMANTIC_CACHE_AVAILABLE = True
except ImportError:
    SEMANTIC_CACHE_AVAILABLE = False

try:
    import tool_optimizer
    TOOL_OPTIMIZER_AVAILABLE = True
except ImportError:
    TOOL_OPTIMIZER_AVAILABLE = False

try:
    import quality_metrics
    QUALITY_METRICS_AVAILABLE = True
except ImportError:
    QUALITY_METRICS_AVAILABLE = False

try:
    import messaging
    import telegram_bot
    import whatsapp_bot
    MESSAGING_AVAILABLE = True
except ImportError:
    MESSAGING_AVAILABLE = False

try:
    import image_support
    IMAGE_SUPPORT_AVAILABLE = True
except ImportError:
    IMAGE_SUPPORT_AVAILABLE = False

try:
    import scheduled_tasks
    SCHEDULED_TASKS_AVAILABLE = True
except ImportError:
    SCHEDULED_TASKS_AVAILABLE = False

try:
    import voice_transcription
    VOICE_TRANSCRIPTION_AVAILABLE = True
except ImportError:
    VOICE_TRANSCRIPTION_AVAILABLE = False

try:
    import scheduler_agent
    SCHEDULER_AGENT_AVAILABLE = True
except ImportError:
    SCHEDULER_AGENT_AVAILABLE = False

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload
CORS(app)

# Register blueprints (will be done after route definitions)
# This will be called at the end of the file before app.run()


# Version: read from config.yaml
def get_version():
    try:
        import yaml
        with open(os.path.join(os.path.dirname(__file__), "config.yaml"), encoding="utf-8") as f:
            return yaml.safe_load(f)["version"]
    except Exception:
        return "unknown"

VERSION = get_version()

# Configuration
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").lower()
if AI_PROVIDER == "grok_web":
    logger.warning("grok_web provider removed; switching runtime provider to xai")
    AI_PROVIDER = "xai"
AI_MODEL = os.getenv("AI_MODEL", "")
# Track the user's currently selected model (persists after set_model changes)
SELECTED_MODEL = ""  # Will be set by /api/set_model and used by stream
SELECTED_PROVIDER = ""  # Will be set by /api/set_model and used by stream
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
AIHUBMIX_API_KEY = os.getenv("AIHUBMIX_API_KEY", "")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
VOLCENGINE_API_KEY = os.getenv("VOLCENGINE_API_KEY", "")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
GITHUB_COPILOT_TOKEN = os.getenv("GITHUB_COPILOT_TOKEN", "")
OPENAI_CODEX_TOKEN = os.getenv("OPENAI_CODEX_TOKEN", "")
CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "")
CUSTOM_API_BASE = os.getenv("CUSTOM_API_BASE", "")
CUSTOM_MODEL_NAME = os.getenv("CUSTOM_MODEL_NAME", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")


def _resolve_ollama_base_url(raw_base_url: str, api_key: str) -> str:
    """Resolve Ollama base URL for local/cloud usage."""
    base = (raw_base_url or "").strip() or "http://localhost:11434"
    key = (api_key or "").strip()
    if key and base in ("http://localhost:11434", "http://127.0.0.1:11434"):
        return "https://ollama.com"
    return base


OLLAMA_BASE_URL = _resolve_ollama_base_url(OLLAMA_BASE_URL, OLLAMA_API_KEY)
NVIDIA_THINKING_MODE = os.getenv("NVIDIA_THINKING_MODE", "False").lower() == "true"
ANTHROPIC_EXTENDED_THINKING = os.getenv("ANTHROPIC_EXTENDED_THINKING", "False").lower() == "true"
ANTHROPIC_PROMPT_CACHING = os.getenv("ANTHROPIC_PROMPT_CACHING", "False").lower() == "true"
OPENAI_EXTENDED_THINKING = os.getenv("OPENAI_EXTENDED_THINKING", "False").lower() == "true"
# Filter out bashio 'null' values
if AI_MODEL in ("null", "None", ""):
    AI_MODEL = ""
API_PORT = int(os.getenv("API_PORT", 5010))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
COLORED_LOGS = os.getenv("COLORED_LOGS", "False").lower() == "true"
ENABLE_FILE_ACCESS = os.getenv("ENABLE_FILE_ACCESS", "False").lower() == "true"
# LANGUAGE moved to core.translations module
LOG_LEVEL = os.getenv("LOG_LEVEL", "normal").lower()  # Supported: normal, verbose, debug
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "False").lower() == "true"
ENABLE_FILE_UPLOAD = os.getenv("ENABLE_FILE_UPLOAD", "False").lower() == "true"
ENABLE_VOICE_INPUT = os.getenv("ENABLE_VOICE_INPUT", "True").lower() == "true"
TTS_VOICE = os.getenv("TTS_VOICE", "female").lower().strip()
ENABLE_RAG = os.getenv("ENABLE_RAG", "False").lower() == "true"
ENABLE_CHAT_BUBBLE = os.getenv("ENABLE_CHAT_BUBBLE", "False").lower() == "true"
ENABLE_AMIRA_CARD_BUTTON = True
ENABLE_AMIRA_AUTOMATION_BUTTON = True
COST_CURRENCY = os.getenv("COST_CURRENCY", "USD").upper()

# Last usage data captured by synchronous chat functions (chat_openai/anthropic/google)
_last_sync_usage: dict = {}

SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN", "") or os.getenv("HASSIO_TOKEN", "")

# Custom system prompt override (can be set dynamically via API)
CUSTOM_SYSTEM_PROMPT = None
# Set when the active agent has a full system_prompt_override (replaces everything)
AGENT_SYSTEM_PROMPT_OVERRIDE = None

# Agent defaults (hardcoded, overridden by agents.json if present)
AGENT_NAME = "Amira"
AGENT_AVATAR = "🤖"
AGENT_INSTRUCTIONS = ""
HTML_DASHBOARD_FOOTER = ""
MAX_CONVERSATIONS = max(1, min(100, int(os.getenv("MAX_CONVERSATIONS", "10") or "10")))
MAX_SNAPSHOTS_PER_FILE = max(1, min(50, int(os.getenv("MAX_SNAPSHOTS_PER_FILE", "5") or "5")))

# New globals for settings previously read only inline
TIMEOUT = int(os.getenv("TIMEOUT", "30") or "30")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3") or "3")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")
# Clean bashio 'null' values for messaging tokens
for _msg_key in ("TELEGRAM_BOT_TOKEN", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM"):
    if globals()[_msg_key] in ("null", "None", "none", "NULL"):
        globals()[_msg_key] = ""
# Per-channel enable/disable toggle (config.yaml: enable_telegram / enable_whatsapp)
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "true").lower() not in ("false", "0", "no")
ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "true").lower() not in ("false", "0", "no")

def _parse_allowed_ids(raw: str) -> set:
    """Parse a comma-separated string of Telegram user IDs into a set of ints."""
    if not raw or raw.strip() in ("", "null", "None", "none"):
        return set()
    ids = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids

_raw_allowed = os.getenv("TELEGRAM_ALLOWED_IDS", "")
TELEGRAM_ALLOWED_IDS: set = _parse_allowed_ids(_raw_allowed)
ENABLE_MCP = os.getenv("ENABLE_MCP", "true").lower() not in ("false", "0", "")
MCP_CONFIG_FILE = os.getenv("MCP_CONFIG_FILE", "/config/amira/mcp_config.json")
FALLBACK_ENABLED = os.getenv("FALLBACK_ENABLED", "true").lower() not in ("false", "0", "no")


def _apply_settings(settings: dict) -> None:
    """Apply settings values to Python globals and os.environ."""
    _g = globals()
    for key, value in settings.items():
        gvar = _SETTINGS_GLOBAL_MAP.get(key)
        if not gvar:
            continue
        default = SETTINGS_DEFAULTS.get(key)
        # Parse value to match default type
        if isinstance(default, bool):
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes")
            else:
                value = bool(value)
        elif isinstance(default, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                value = default
            # Clamp specific ranges
            if key == "max_conversations":
                value = max(1, min(100, value))
            elif key == "max_snapshots_per_file":
                value = max(1, min(50, value))
            elif key == "timeout":
                value = max(5, min(300, value))
            elif key == "max_retries":
                value = max(0, min(10, value))
        else:
            value = str(value)
        # Normalize specific string values
        if key == "language":
            value = str(value).lower()
        elif key == "cost_currency":
            value = str(value).upper()
        elif key == "tts_voice":
            value = str(value).lower().strip()
        elif key == "telegram_allowed_ids":
            # Store as set of ints for fast lookup; os.environ keeps the raw string
            raw_str = str(value)
            _g[gvar] = _parse_allowed_ids(raw_str)
            os.environ[gvar] = raw_str
            continue
        # Set Python global
        _g[gvar] = value
        # Set os.environ for inline os.getenv() calls
        if isinstance(value, bool):
            os.environ[gvar] = "true" if value else "false"
        else:
            os.environ[gvar] = str(value)


# Override env vars with settings.json if present (startup overlay)
# Merge SETTINGS_DEFAULTS first so that any key not yet in settings.json
# still gets its correct default (env vars from run script may disagree).
_startup_settings = _load_settings()
_merged_startup = {k: v for k, v in SETTINGS_DEFAULTS.items() if k in _SETTINGS_GLOBAL_MAP}
_merged_startup.update(_startup_settings)  # user-saved values win
_apply_settings(_merged_startup)

_LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO

# Custom log level for user questions and AI responses — stands out from INFO
CHAT = 25  # between INFO (20) and WARNING (30)
logging.addLevelName(CHAT, "CHAT")


def _log_chat(self, message, *args, **kwargs):
    if self.isEnabledFor(CHAT):
        self._log(CHAT, message, args, **kwargs)


logging.Logger.chat = _log_chat


class _ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\x1b[36m",     # cyan
        "INFO": "\x1b[32m",      # green
        "CHAT": "\x1b[34m",      # blue — distinct from green INFO
        "WARNING": "\x1b[33m",   # yellow
        "ERROR": "\x1b[31m",     # red
        "CRITICAL": "\x1b[35m",  # magenta
    }
    ICONS = {
        "DEBUG": "🔵",
        "INFO": "🟢",
        "CHAT": "💬",
        "WARNING": "🟡",
        "ERROR": "🔴",
        "CRITICAL": "🟣",
    }
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"

    def format(self, record: logging.LogRecord) -> str:
        # Timestamp
        ts = self.formatTime(record, "%H:%M:%S")
        # Context: SYSTEM, REQUEST, RESPONSE (default SYSTEM)
        context = getattr(record, "context", None)
        if not context:
            # Heuristic: logger name or message prefix
            lname = record.name.lower()
            if "request" in lname or "http" in lname:
                context = "REQUEST"
            elif "response" in lname:
                context = "RESPONSE"
            elif "chat_ui" in lname:
                context = "UI"
            else:
                context = "SYSTEM"
        # Color and icon
        original = record.levelname
        try:
            icon = self.ICONS.get(original)
            color = self.COLORS.get(original)
            decorated = f"{icon} {original}" if icon else original
            if color:
                clevel = f"{color}{decorated}{self.RESET}"
            else:
                clevel = decorated
            # Format: [HH:MM:SS] [CONTEXT] 🟢 INFO: providers.manager -> message
            # logger name is bold for readability in dense logs.
            _lname = f"{self.BOLD}{record.name}{self.RESET}"
            return f"[{ts}] [{context}] {clevel}: {_lname} -> {record.getMessage()}"
        finally:
            record.levelname = original


if COLORED_LOGS:
    handler = logging.StreamHandler()
    handler.setFormatter(_ColorFormatter("%(levelname)s:%(name)s:%(message)s"))
    logging.basicConfig(level=_LOG_LEVEL, handlers=[handler], force=True)
else:
    logging.basicConfig(level=_LOG_LEVEL)
logger = logging.getLogger(__name__)

logger.info(f"ENABLE_FILE_ACCESS env var: {os.getenv('ENABLE_FILE_ACCESS', 'NOT SET')}")
logger.info(f"ENABLE_FILE_ACCESS parsed: {ENABLE_FILE_ACCESS}")
logger.info(f"HA_CONFIG_DIR: /config")
logger.info(f"LANGUAGE: {LANGUAGE}")



# Load persisted system prompt override (if any)
_persisted_prompt = _load_custom_system_prompt_from_disk()
if _persisted_prompt:
    CUSTOM_SYSTEM_PROMPT = _persisted_prompt
    logger.info(f"Loaded custom system prompt from disk ({len(CUSTOM_SYSTEM_PROMPT)} chars)")


def _sync_active_agent_globals(
    apply_model: bool = False,
    persist_selection: bool = False,
    reinitialize_client: bool = False,
) -> None:
    """Read the currently active agent from AgentManager and update globals.

    Called every time the active agent changes (set_agent endpoint,
    _apply_channel_agent, load_agents_config).  Keeps AGENT_NAME,
    AGENT_AVATAR, AGENT_INSTRUCTIONS and AGENT_SYSTEM_PROMPT_OVERRIDE
    in sync without reloading the config file from disk.
    """
    global AGENT_NAME, AGENT_AVATAR, AGENT_INSTRUCTIONS, AGENT_SYSTEM_PROMPT_OVERRIDE
    global AI_PROVIDER, AI_MODEL, SELECTED_PROVIDER, SELECTED_MODEL
    if not AGENT_CONFIG_AVAILABLE:
        return
    try:
        mgr = agent_config.get_agent_manager()
        active = mgr.get_active_agent()
        if not active:
            return
        AGENT_NAME = (active.identity.name or active.name or "Amira").strip()
        AGENT_AVATAR = (active.identity.emoji or "\U0001f916").strip()
        AGENT_SYSTEM_PROMPT_OVERRIDE = None
        AGENT_INSTRUCTIONS = (active.instructions or "").strip()

        model_changed = False
        if apply_model and active.model_config and active.model_config.primary:
            ref = active.model_config.primary
            if ref.provider and ref.model:
                if ref.provider != AI_PROVIDER or ref.model != AI_MODEL:
                    AI_PROVIDER = ref.provider
                    AI_MODEL = ref.model
                    SELECTED_PROVIDER = ref.provider
                    SELECTED_MODEL = ref.model
                    model_changed = True
                else:
                    # Keep selected runtime values aligned even if unchanged
                    SELECTED_PROVIDER = ref.provider
                    SELECTED_MODEL = ref.model

        if model_changed and persist_selection:
            try:
                save_runtime_selection(AI_PROVIDER, AI_MODEL)
            except Exception as e:
                logger.warning(f"Could not persist runtime selection from active agent: {e}")

        if model_changed and reinitialize_client:
            try:
                initialize_ai_client()
            except Exception as e:
                logger.warning(f"Could not reinitialize client after active agent sync: {e}")
        try:
            import tools as _tools_mod
            _tools_mod.AI_SIGNATURE = AGENT_NAME
        except Exception:
            pass
        logger.debug(
            f"Agent globals synced → '{active.id}': name={AGENT_NAME}, "
            f"instructions={len(AGENT_INSTRUCTIONS)} chars"
        )
    except Exception as e:
        logger.warning(f"_sync_active_agent_globals error: {e}")


def load_agents_config() -> Optional[Dict]:
    """Reload agent config from disk via AgentManager, then sync globals.

    All format parsing (canonical array, legacy dict, flat dict) is handled
    by AgentManager._parse_config() — no duplicate logic here.
    """
    if not AGENT_CONFIG_AVAILABLE:
        return None
    try:
        mgr = agent_config.get_agent_manager()
        mgr.reload_config()
        _sync_active_agent_globals(apply_model=True, persist_selection=True, reinitialize_client=True)
        active = mgr.get_active_agent()
        if active:
            logger.info(f"Agent '{active.id}': name={AGENT_NAME}, avatar={AGENT_AVATAR}")
        # Return raw config data for callers that need it
        if os.path.isfile(AGENTS_FILE):
            with open(AGENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.warning(f"Could not reload agents config: {e}")
        return None


def _truncate(s: str, max_len: int = 160) -> str:
    if not s:
        return ""
    s = str(s)
    return s if len(s) <= max_len else (s[: max_len - 1] + "…")


def _get_client_ip() -> str:
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",", 1)[0].strip()
    return request.remote_addr or ""


def _safe_request_meta() -> Dict[str, str]:
    # Keep this intentionally small and never log secrets.
    return {
        "ip": _get_client_ip(),
        "ua": _truncate(request.headers.get("User-Agent", ""), 140),
        "origin": _truncate(request.headers.get("Origin", ""), 140),
        "referer": _truncate(request.headers.get("Referer", ""), 140),
        "xf_proto": request.headers.get("X-Forwarded-Proto", ""),
        "xf_host": _truncate(request.headers.get("X-Forwarded-Host", ""), 120),
        "xf_prefix": _truncate(request.headers.get("X-Forwarded-Prefix", ""), 140),
        "ingress_path": _truncate(request.headers.get("X-Ingress-Path", ""), 140),
    }


@app.before_request
def _log_request_start() -> None:
    # Correlation id for log lines belonging to the same request.
    g._req_id = uuid.uuid4().hex[:8]
    g._t0 = time.monotonic()

    # Avoid noisy preflight logs unless debug is enabled.
    if request.method == "OPTIONS" and not DEBUG_MODE:
        return

    # Filter noisy endpoints in normal log level
    if LOG_LEVEL == "normal":
        # Skip logging for health checks and streaming endpoints
        if request.path == "/api/ui_ping" or (request.path == "/api/chat/stream" and request.method == "POST"):
            g._skip_log = True
            return

    g._skip_log = False

    # Only log full request details in verbose/debug mode
    if LOG_LEVEL in ("verbose", "debug"):
        meta = _safe_request_meta()
        logger.info(
            f"[{g._req_id}] → {request.method} {request.path}"
            f" | ip={meta['ip']} ua={meta['ua']}"
            f" | ingress={meta['ingress_path']} xf_prefix={meta['xf_prefix']}",
            extra={"context": "REQUEST"},
        )


@app.after_request
def _log_request_end(response: Response) -> Response:
    try:
        # Allow microphone/camera in HA ingress iframe (Firefox requires this)
        response.headers["Permissions-Policy"] = "microphone=*, camera=*"
        response.headers["Feature-Policy"] = "microphone *; camera *"
        
        if request.method == "OPTIONS" and not DEBUG_MODE:
            return response

        # Skip logging for noisy endpoints in normal log level
        if getattr(g, "_skip_log", False):
            return response

        rid = getattr(g, "_req_id", "")
        t0 = getattr(g, "_t0", None)
        dur_ms = int((time.monotonic() - t0) * 1000) if t0 else -1
        
        # Only log response details in verbose/debug mode
        if LOG_LEVEL in ("verbose", "debug"):
            logger.info(
                f"[{rid}] ← {request.method} {request.path}"
                f" | {response.status_code} | {dur_ms}ms",
                extra={"context": "RESPONSE"},
            )
    except Exception:
        # Never fail a request due to logging.
        pass
    return response


@app.errorhandler(HTTPException)
def _log_http_exception(e: HTTPException):
    # Log HTTP errors but preserve their status codes and bodies.
    rid = getattr(g, "_req_id", "")
    meta = _safe_request_meta()
    logger.warning(
        f"[{rid}] HTTP {e.code} during {request.method} {request.path}"
        f" | ip={meta['ip']} ua={meta['ua']} ingress={meta['ingress_path']}: {e}",
        extra={"context": "SYSTEM"},
    )
    return e


@app.errorhandler(Exception)
def _log_unhandled_exception(e: Exception):
    # Log full traceback in add-on logs for cases where the UI can't display anything.
    rid = getattr(g, "_req_id", "")
    meta = _safe_request_meta()
    logger.exception(
        f"[{rid}] Unhandled exception during {request.method} {request.path}"
        f" | ip={meta['ip']} ua={meta['ua']} ingress={meta['ingress_path']}: {type(e).__name__}: {e}",
        extra={"context": "SYSTEM"},
    )

    # Preserve current behavior as much as possible: API routes return JSON, UI returns a minimal text.
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    return "Internal server error", 500


# Error handling functions moved to core.error_utils module

def load_runtime_selection() -> bool:
    """Load persisted provider/model selection from disk.

    Returns True if a valid selection was loaded.
    """
    global AI_PROVIDER, AI_MODEL, SELECTED_MODEL, SELECTED_PROVIDER
    provider, model = settings_service.load_runtime_selection()
    if provider and model:
        if provider == "grok_web":
            provider = "xai"
            if not model:
                model = PROVIDER_DEFAULTS.get("xai", {}).get("model", "grok-4-1-fast-non-reasoning")
        AI_PROVIDER = provider
        AI_MODEL = model
        SELECTED_PROVIDER = provider
        SELECTED_MODEL = model
        logger.info(f"Loaded runtime selection: {AI_PROVIDER} / {AI_MODEL}")
        return True
    return False


def save_runtime_selection(provider: str, model: str) -> bool:
    """Persist provider/model selection to disk."""
    return settings_service.save_runtime_selection(provider, model)

# Load multilingual keywords for intent detection
KEYWORDS = {}
try:
    keywords_file = os.path.join(os.path.dirname(__file__), "keywords.json")
    if os.path.isfile(keywords_file):
        with open(keywords_file, "r", encoding="utf-8") as f:
            keywords_data = json.load(f)
            KEYWORDS = keywords_data.get("keywords", {})
        logger.info(f"Loaded keywords for {len(KEYWORDS)} languages: {list(KEYWORDS.keys())}")
    else:
        logger.warning(f"keywords.json not found at {keywords_file}")
except Exception as e:
    logger.error(f"Error loading keywords.json: {e}")

# Language-specific text
# Translation functions moved to core.translations module

# Image handling helpers moved to core.image_helpers module

# ---- Provider defaults ----

PROVIDER_DEFAULTS = {
    "anthropic": {"model": "claude-opus-4-6", "name": "Claude (Anthropic)"},
    "openai": {"model": "gpt-5.2", "name": "ChatGPT (OpenAI)"},
    "google": {"model": "gemini-2.0-flash", "name": "Gemini (Google)"},
    "github": {"model": "openai/gpt-4o", "name": "GitHub Models"},
    "nvidia": {"model": "moonshotai/kimi-k2.5", "name": "NVIDIA NIM"},
    "groq": {"model": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Groq)"},
    "mistral": {"model": "mistral-large-latest", "name": "Mistral Large"},
    "ollama": {"model": "mistral", "name": "Ollama (Local)"},
    "openrouter": {"model": "anthropic/claude-opus-4.6", "name": "OpenRouter (Gateway)"},
    "deepseek": {"model": "deepseek-chat", "name": "DeepSeek (API)"},
    "xai": {"model": "grok-4-1-fast-non-reasoning", "name": "xAI (Grok)"},
    "minimax": {"model": "MiniMax-M2.1", "name": "MiniMax (API)"},
    "aihubmix": {"model": "gpt-4o", "name": "AiHubMix (Gateway)"},
    "siliconflow": {"model": "Qwen/Qwen2.5-7B-Instruct", "name": "SiliconFlow (Gateway)"},
    "volcengine": {"model": "Qwen/Qwen2.5-7B-Instruct", "name": "VolcEngine (Gateway)"},
    "dashscope": {"model": "qwen-max", "name": "DashScope (Qwen/Aliyun)"},
    "moonshot": {"model": "kimi-k2.5", "name": "Moonshot (Kimi)"},
    "zhipu": {"model": "glm-4-flash", "name": "Zhipu (GLM)"},
    "perplexity": {"model": "sonar-pro", "name": "Perplexity (Sonar)"},
    "custom": {"model": "", "name": "Custom Endpoint"},
    "github_copilot": {"model": "gpt-4o", "name": "GitHub Copilot (OAuth)"},
    "openai_codex": {"model": "gpt-5.3-codex", "name": "OpenAI Codex (OAuth)"},
    "claude_web": {"model": "claude-opus-4-6", "name": "Claude.ai Web ⚠️ [UNSTABLE]"},
    "chatgpt_web": {"model": "gpt-4o", "name": "ChatGPT Web ⚠️ [UNSTABLE]"},
    "gemini_web": {"model": "gemini-3.1-pro", "name": "Gemini Web"},
    "perplexity_web": {"model": "grok-4-1", "name": "Perplexity Web ⚠️ [UNSTABLE]"},
}


# ---------------------------------------------------------------------------
# PROVIDER_MODELS — Single source of truth lives in model_catalog._PROVIDER_MODELS.
# At startup we get a mutable copy, then patch it with live provider discovery
# and the on-disk model cache.  To edit the static model list → edit model_catalog.py.
# ---------------------------------------------------------------------------
if MODEL_CATALOG_AVAILABLE:
    PROVIDER_MODELS = model_catalog.get_catalog().get_provider_models()
else:
    # Bare-minimum fallback if model_catalog is missing
    PROVIDER_MODELS = {"anthropic": ["claude-sonnet-4-6"], "openai": ["gpt-4o"]}

# Immutable baseline from source files (fixed/hardcoded models).
FIXED_PROVIDER_MODELS = deepcopy(PROVIDER_MODELS)

def apply_persistent_model_blocklist() -> Dict[str, Any]:
    """Filter runtime PROVIDER_MODELS using persisted blocklist for all providers.

    Returns stats useful for logs/debug:
    {"removed_total": int, "removed_by_provider": {provider: count}}
    """
    removed_total = 0
    removed_by_provider: Dict[str, int] = {}
    try:
        if not os.path.isfile(MODEL_BLOCKLIST_FILE):
            return {"removed_total": 0, "removed_by_provider": {}}
        with open(MODEL_BLOCKLIST_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh) or {}

        for provider, blocked_cfg in (data.items() if isinstance(data, dict) else []):
            if provider not in PROVIDER_MODELS:
                continue

            blocked_ids: set[str] = set()
            # Backward-compatible shapes:
            # {"provider": [blocked...]}
            # {"provider": {"blocked": [...], "tested_ok": [...]}}
            if isinstance(blocked_cfg, dict):
                raw_blocked = blocked_cfg.get("blocked") or []
                if isinstance(raw_blocked, list):
                    blocked_ids = {m.strip() for m in raw_blocked if isinstance(m, str) and m.strip()}
            elif isinstance(blocked_cfg, list):
                blocked_ids = {m.strip() for m in blocked_cfg if isinstance(m, str) and m.strip()}

            if not blocked_ids:
                continue

            before = list(PROVIDER_MODELS.get(provider) or [])
            after = [m for m in before if m not in blocked_ids]
            delta = len(before) - len(after)
            if delta > 0:
                PROVIDER_MODELS[provider] = after
                removed_total += delta
                removed_by_provider[provider] = delta
    except Exception as _e:
        logger.warning(f"Apply persistent model blocklist failed: {_e}")
    return {"removed_total": removed_total, "removed_by_provider": removed_by_provider}

def _refresh_model_cache_at_startup() -> Dict[str, Any]:
    """Refresh dynamic model cache and overlay runtime model list.

    Returns a small summary dict for diagnostics/UI.
    """
    try:
        from providers.model_fetcher import (
            refresh_all_providers as _refresh_all_model_providers,
            load_dynamic_cache as _load_dynamic_model_cache,
            update_fixed_cache as _update_fixed_model_cache,
        )

        # Persist current hardcoded baseline in cache file (separate "fixed" section).
        _update_fixed_model_cache(FIXED_PROVIDER_MODELS)

        provider_keys: Dict[str, str] = {
            "anthropic": ANTHROPIC_API_KEY,
            "openai": OPENAI_API_KEY,
            "google": GOOGLE_API_KEY,
            "github": GITHUB_TOKEN,
            "nvidia": NVIDIA_API_KEY,
            "groq": GROQ_API_KEY,
            "mistral": MISTRAL_API_KEY,
            "openrouter": OPENROUTER_API_KEY,
            "deepseek": DEEPSEEK_API_KEY,
            "xai": XAI_API_KEY,
            "minimax": MINIMAX_API_KEY,
            "aihubmix": AIHUBMIX_API_KEY,
            "siliconflow": SILICONFLOW_API_KEY,
            "volcengine": VOLCENGINE_API_KEY,
            "dashscope": DASHSCOPE_API_KEY,
            "moonshot": MOONSHOT_API_KEY,
            "zhipu": ZHIPU_API_KEY,
            "perplexity": PERPLEXITY_API_KEY,
            "custom": CUSTOM_API_KEY,
            # OAuth provider, no API key required (fetcher handles token lookup)
            "github_copilot": "__oauth__",
            # Web-session provider, no API key required
            "perplexity_web": "__oauth__",
        }
        # Refresh Ollama models only when Ollama is active to avoid startup stalls.
        if AI_PROVIDER == "ollama":
            provider_keys["ollama"] = OLLAMA_API_KEY or "__local__"
        extra = {
            "ollama_base_url": OLLAMA_BASE_URL,
            "ollama_api_key": OLLAMA_API_KEY,
            "custom_api_base": CUSTOM_API_BASE,
        }
        results = _refresh_all_model_providers(provider_keys, extra)
        _updated = results.get("updated", {}) if isinstance(results, dict) else {}
        if _updated:
            for _p, _ml in _updated.items():
                if _ml:
                    PROVIDER_MODELS[_p] = list(_ml)
            logger.info(f"Model cache startup refresh: updated {len(_updated)} providers")

        # Always re-apply persisted dynamic cache (latest write wins).
        _dyn = _load_dynamic_model_cache()
        if _dyn:
            for _p, _ml in _dyn.items():
                if _ml:
                    if _p == "ollama" and PROVIDER_MODELS.get("ollama"):
                        continue
                    PROVIDER_MODELS[_p] = list(_ml)
            logger.info(f"Model cache startup overlay: dynamic cache for {len(_dyn)} providers")
        block_res = apply_persistent_model_blocklist()
        if block_res.get("removed_total", 0):
            logger.info(
                f"Model blocklist applied after refresh: removed {block_res['removed_total']} model(s) "
                f"across {len(block_res.get('removed_by_provider') or {})} provider(s)"
            )
        return {
            "success": True,
            "updated_count": len(_updated),
            "dynamic_count": len(_dyn),
            "updated": sorted(list(_updated.keys())),
            "blocklist_removed": int(block_res.get("removed_total", 0)),
        }
    except Exception as _e:
        logger.warning(f"Model cache startup refresh failed: {_e}")
        return {"success": False, "error": str(_e), "updated_count": 0, "dynamic_count": 0, "updated": []}

try:
    from providers import _PROVIDER_CLASSES, get_provider_class as _get_provider_class
    _dynamic_ok = []
    _dynamic_fail = []
    for _pid in list(_PROVIDER_CLASSES):
        try:
            _cls = _get_provider_class(_pid)
            # Ollama needs the user-configured base_url to reach the server
            if _pid == "ollama":
                _inst = _cls(base_url=OLLAMA_BASE_URL)
            else:
                _inst = _cls()
            _live = _inst.get_available_models()
            if _live:  # only replace if the provider returned something
                PROVIDER_MODELS[_pid] = _live
                # Seed fixed baseline for runtime-discovered API providers that start empty
                # in model_catalog._PROVIDER_MODELS. This keeps Fixed/Dynamic grouping useful.
                if not FIXED_PROVIDER_MODELS.get(_pid):
                    FIXED_PROVIDER_MODELS[_pid] = list(_live)
                _dynamic_ok.append(f"{_pid}({len(_live)})")
        except Exception as _e:
            _dynamic_fail.append(f"{_pid}:{_e.__class__.__name__}")
    import logging as _log
    _dlog = _log.getLogger(__name__)
    if _dynamic_ok:
        _dlog.info(f"Dynamic model discovery: {', '.join(_dynamic_ok)}")
    if _dynamic_fail:
        _dlog.warning(f"Dynamic model discovery failed: {', '.join(_dynamic_fail)}")
except Exception:
    pass

# Load persisted dynamic model cache from disk and overlay runtime list.
try:
    from providers.model_fetcher import (
        load_dynamic_cache as _load_dynamic_model_cache,
        update_fixed_cache as _update_fixed_model_cache,
    )
    _update_fixed_model_cache(FIXED_PROVIDER_MODELS)
    _model_cache = _load_dynamic_model_cache()
    for _p, _ml in _model_cache.items():
        if _ml:
            # Skip Ollama cache — always use live /api/tags results
            if _p == "ollama" and PROVIDER_MODELS.get("ollama"):
                continue
            PROVIDER_MODELS[_p] = _ml
    if _model_cache:
        import logging as _log
        _log.getLogger(__name__).info(f"Loaded dynamic model cache for {len(_model_cache)} providers")
except Exception:
    pass  # cache optional — dynamic lists remain

# Always refresh dynamic model cache at addon startup.
_refresh_model_cache_at_startup()


# Mapping user-friendly names (with prefixes) to technical model names
MODEL_NAME_MAPPING = {
    "Claude: Opus 4.6": "claude-opus-4-6",
    "Claude: Sonnet 4.6": "claude-sonnet-4-6",
    "Claude: Haiku 4.5": "claude-haiku-4-5-20251001",
    "Claude: Sonnet 4.5": "claude-sonnet-4-5-20250929",
    "Claude: Opus 4.5": "claude-opus-4-5-20251101",
    "Claude: Sonnet 4": "claude-sonnet-4-20250514",
    "Claude: Haiku 4": "claude-haiku-4",
    "Claude: Opus 4": "claude-opus-4-20250514",
    "Claude: Opus 4.1": "claude-opus-4-1-20250805",
    "Claude: Haiku 3": "claude-3-haiku-20240307",
    "OpenAI: GPT-5.2": "gpt-5.2",
    "OpenAI: GPT-5.2-mini": "gpt-5.2-mini",
    "OpenAI: GPT-5": "gpt-5",
    "OpenAI: GPT-4o": "gpt-4o",
    "OpenAI: GPT-4o-mini": "gpt-4o-mini",
    "OpenAI: GPT-4-turbo": "gpt-4-turbo",
    "OpenAI: GPT-4 (Legacy)": "gpt-4",
    "OpenAI: GPT-3.5 Turbo (Legacy)": "gpt-3.5-turbo",
    "OpenAI: GPT-3.5 Turbo-0125 (Legacy)": "gpt-3.5-turbo-0125",
    "OpenAI: GPT-3.5 Turbo-1106 (Legacy)": "gpt-3.5-turbo-1106",
    "OpenAI: GPT-3.5 Turbo 16k (Legacy)": "gpt-3.5-turbo-16k",
    "OpenAI: GPT-3.5 Turbo Instruct (Legacy)": "gpt-3.5-turbo-instruct",
    "OpenAI: GPT-3.5 Turbo Instruct-0914 (Legacy)": "gpt-3.5-turbo-instruct-0914",
    "OpenAI: GPT-4-0125 Preview (Legacy)": "gpt-4-0125-preview",
    "OpenAI: GPT-4-0613 (Legacy)": "gpt-4-0613",
    "OpenAI: GPT-4-1106 Preview (Legacy)": "gpt-4-1106-preview",
    "OpenAI: GPT-4 Turbo Preview (Legacy)": "gpt-4-turbo-preview",
    "OpenAI: GPT-4 Turbo (2024-04-09)": "gpt-4-turbo-2024-04-09",
    "OpenAI: GPT-4.1": "gpt-4.1",
    "OpenAI: GPT-4.1 (2025-04-14)": "gpt-4.1-2025-04-14",
    "OpenAI: GPT-4.1 Mini": "gpt-4.1-mini",
    "OpenAI: GPT-4.1 Mini (2025-04-14)": "gpt-4.1-mini-2025-04-14",
    "OpenAI: GPT-4.1 Nano": "gpt-4.1-nano",
    "OpenAI: GPT-4.1 Nano (2025-04-14)": "gpt-4.1-nano-2025-04-14",
    "OpenAI: GPT-4o (2024-05-13)": "gpt-4o-2024-05-13",
    "OpenAI: GPT-4o (2024-08-06)": "gpt-4o-2024-08-06",
    "OpenAI: GPT-4o (2024-11-20)": "gpt-4o-2024-11-20",
    "OpenAI: GPT-4o Audio Preview": "gpt-4o-audio-preview",
    "OpenAI: GPT-4o Audio Preview (2024-12-17)": "gpt-4o-audio-preview-2024-12-17",
    "OpenAI: GPT-4o Audio Preview (2025-06-03)": "gpt-4o-audio-preview-2025-06-03",
    "OpenAI: GPT-4o Mini (2024-07-18)": "gpt-4o-mini-2024-07-18",
    "OpenAI: GPT-4o Mini Audio Preview": "gpt-4o-mini-audio-preview",
    "OpenAI: GPT-4o Mini Audio Preview (2024-12-17)": "gpt-4o-mini-audio-preview-2024-12-17",
    "OpenAI: GPT-4o Mini Transcribe": "gpt-4o-mini-transcribe",
    "OpenAI: GPT-4o Mini Transcribe (2025-03-20)": "gpt-4o-mini-transcribe-2025-03-20",
    "OpenAI: GPT-4o Mini Transcribe (2025-12-15)": "gpt-4o-mini-transcribe-2025-12-15",
    "OpenAI: GPT-4o Transcribe": "gpt-4o-transcribe",
    "OpenAI: GPT-4o Transcribe Diarize": "gpt-4o-transcribe-diarize",
    "OpenAI: GPT-5": "gpt-5",
    "OpenAI: GPT-5 (2025-08-07)": "gpt-5-2025-08-07",
    "OpenAI: GPT-5 Chat Latest": "gpt-5-chat-latest",
    "OpenAI: GPT-5 Codex": "gpt-5-codex",
    "OpenAI: GPT-5 Mini": "gpt-5-mini",
    "OpenAI: GPT-5 Mini (2025-08-07)": "gpt-5-mini-2025-08-07",
    "OpenAI: GPT-5 Nano": "gpt-5-nano",
    "OpenAI: GPT-5 Nano (2025-08-07)": "gpt-5-nano-2025-08-07",
    "OpenAI: GPT-5 Pro": "gpt-5-pro",
    "OpenAI: GPT-5 Pro (2025-10-06)": "gpt-5-pro-2025-10-06",
    "OpenAI: GPT-5.1": "gpt-5.1",
    "OpenAI: GPT-5.1 (2025-11-13)": "gpt-5.1-2025-11-13",
    "OpenAI: GPT-5.1 Chat Latest": "gpt-5.1-chat-latest",
    "OpenAI: GPT-5.1 Codex": "gpt-5.1-codex",
    "OpenAI: GPT-5.1 Codex Max": "gpt-5.1-codex-max",
    "OpenAI: GPT-5.1 Codex Mini": "gpt-5.1-codex-mini",
    "OpenAI: GPT-5.2 (2025-12-11)": "gpt-5.2-2025-12-11",
    "OpenAI: GPT-5.2 Chat Latest": "gpt-5.2-chat-latest",
    "OpenAI: GPT-5.2 Codex": "gpt-5.2-codex",
    "OpenAI: GPT-5.2 Pro": "gpt-5.2-pro",
    "OpenAI: GPT-5.2 Pro (2025-12-11)": "gpt-5.2-pro-2025-12-11",
    "OpenAI: GPT-5.3 Chat Latest": "gpt-5.3-chat-latest",
    "OpenAI: GPT-5.3 Codex": "gpt-5.3-codex",
    "OpenAI: GPT-5.4": "gpt-5.4",
    "OpenAI: GPT-5.4 (2026-03-05)": "gpt-5.4-2026-03-05",
    "OpenAI: GPT-5.4 Mini": "gpt-5.4-mini",
    "OpenAI: GPT-5.4 Mini (2026-03-17)": "gpt-5.4-mini-2026-03-17",
    "OpenAI: GPT-5.4 Nano": "gpt-5.4-nano",
    "OpenAI: GPT-5.4 Nano (2026-03-17)": "gpt-5.4-nano-2026-03-17",
    "OpenAI: GPT-5.4 Pro": "gpt-5.4-pro",
    "OpenAI: GPT-5.4 Pro (2026-03-05)": "gpt-5.4-pro-2026-03-05",
    "OpenAI: GPT Audio": "gpt-audio",
    "OpenAI: GPT Audio 1.5": "gpt-audio-1.5",
    "OpenAI: GPT Audio (2025-08-28)": "gpt-audio-2025-08-28",
    "OpenAI: GPT Audio Mini": "gpt-audio-mini",
    "OpenAI: GPT Audio Mini (2025-10-06)": "gpt-audio-mini-2025-10-06",
    "OpenAI: GPT Audio Mini (2025-12-15)": "gpt-audio-mini-2025-12-15",
    "OpenAI: o3": "o3",
    "OpenAI: o3-mini": "o3-mini",
    "OpenAI: o1": "o1",
    "OpenAI: o1 (2024-12-17)": "o1-2024-12-17",
    "OpenAI: o1 Pro": "o1-pro",
    "OpenAI: o1 Pro (2025-03-19)": "o1-pro-2025-03-19",
    "OpenAI: o3 (2025-04-16)": "o3-2025-04-16",
    "OpenAI: o3-mini (2025-01-31)": "o3-mini-2025-01-31",
    "OpenAI: o4-mini": "o4-mini",
    "OpenAI: o4-mini (2025-04-16)": "o4-mini-2025-04-16",
    "OpenAI: Sora 2": "sora-2",
    "OpenAI: Sora 2 Pro": "sora-2-pro",
    "Google: Gemini 3 Pro (Preview)": "gemini-3-pro-preview",
    "Google: Gemini 3 Flash (Preview)": "gemini-3-flash-preview",
    "Google: Gemini 2.0 Flash": "gemini-2.0-flash",
    "Google: Gemini 2.5 Pro": "gemini-2.5-pro",
    "Google: Gemini 2.5 Flash": "gemini-2.5-flash",
    "Google: Gemini 2.0 Flash 001": "gemini-2.0-flash-001",
    "Google: Gemini 2.0 Flash Lite": "gemini-2.0-flash-lite",
    "Google: Gemini 2.0 Flash Lite 001": "gemini-2.0-flash-lite-001",
    "Google: Gemini 2.5 Computer Use (Preview 10-2025)": "gemini-2.5-computer-use-preview-10-2025",
    "Google: Gemini 2.5 Flash Image": "gemini-2.5-flash-image",
    "Google: Gemini 2.5 Flash Lite": "gemini-2.5-flash-lite",
    "Google: Gemini 2.5 Flash Lite (Preview 09-2025)": "gemini-2.5-flash-lite-preview-09-2025",
    "Google: Gemini 2.5 Flash Preview TTS": "gemini-2.5-flash-preview-tts",
    "Google: Gemini 2.5 Pro Preview TTS": "gemini-2.5-pro-preview-tts",
    "Google: Gemini 3 Pro Image Preview": "gemini-3-pro-image-preview",
    "Google: Gemini 3.1 Flash Image Preview": "gemini-3.1-flash-image-preview",
    "Google: Gemini 3.1 Flash Lite Preview": "gemini-3.1-flash-lite-preview",
    "Google: Gemini 3.1 Pro Preview": "gemini-3.1-pro-preview",
    "Google: Gemini 3.1 Pro Preview Customtools": "gemini-3.1-pro-preview-customtools",
    "Google: Gemini Flash Latest": "gemini-flash-latest",
    "Google: Gemini Flash Lite Latest": "gemini-flash-lite-latest",
    "Google: Gemini Pro Latest": "gemini-pro-latest",
    "Google: Gemini Robotics ER 1.5 Preview": "gemini-robotics-er-1.5-preview",
    "Google: Gemma 3 1B IT": "gemma-3-1b-it",
    "Google: Gemma 3 4B IT": "gemma-3-4b-it",
    "Google: Gemma 3 12B IT": "gemma-3-12b-it",
    "Google: Gemma 3 27B IT": "gemma-3-27b-it",
    "Google: Gemma 3n E2B IT": "gemma-3n-e2b-it",
    "Google: Gemma 3n E4B IT": "gemma-3n-e4b-it",
    "Google: Nano Banana Pro Preview": "nano-banana-pro-preview",
    "NVIDIA: Kimi K2.5": "moonshotai/kimi-k2.5",
    "NVIDIA: Llama 3.1 70B": "meta/llama-3.1-70b-instruct",
    "NVIDIA: Llama 3.1 405B": "meta/llama-3.1-405b-instruct",
    "NVIDIA: Mistral Large 2": "mistralai/mistral-large-2-instruct",
    "NVIDIA: Phi-4": "microsoft/phi-4",
    "NVIDIA: Nemotron 70B": "nvidia/llama-3.1-nemotron-70b-instruct",
    
    # GitHub Models - IDs use publisher/model-name format
    "GitHub: GPT-5.2": "openai/gpt-5.2",
    "GitHub: GPT-5.2-mini": "openai/gpt-5.2-mini",
    "GitHub: GPT-4o": "openai/gpt-4o",
    "GitHub: GPT-4o-mini": "openai/gpt-4o-mini",
    "GitHub: GPT-5": "openai/gpt-5",
    "GitHub: GPT-5-chat": "openai/gpt-5-chat",
    "GitHub: GPT-5-mini": "openai/gpt-5-mini",
    "GitHub: GPT-5-nano": "openai/gpt-5-nano",
    "GitHub: GPT-4.1": "openai/gpt-4.1",
    "GitHub: GPT-4.1-mini": "openai/gpt-4.1-mini",
    "GitHub: GPT-4.1-nano": "openai/gpt-4.1-nano",
    "GitHub: o1": "openai/o1",
    "GitHub: o1-mini": "openai/o1-mini",
    "GitHub: o1-preview": "openai/o1-preview",
    "GitHub: o3": "openai/o3",
    "GitHub: o3-mini": "openai/o3-mini",
    "GitHub: o4-mini": "openai/o4-mini",
    "GitHub: Llama 3.1 405B": "meta/meta-llama-3.1-405b-instruct",
    "GitHub: Llama 3.1 8B": "meta/meta-llama-3.1-8b-instruct",
    "GitHub: Llama 3.3 70B": "meta/llama-3.3-70b-instruct",
    "GitHub: Llama 4 Scout": "meta/llama-4-scout-17b-16e-instruct",
    "GitHub: Llama 4 Maverick": "meta/llama-4-maverick-17b-128e-instruct-fp8",
    "GitHub: Llama 3.2 11B Vision": "meta/llama-3.2-11b-vision-instruct",
    "GitHub: Llama 3.2 90B Vision": "meta/llama-3.2-90b-vision-instruct",
    "GitHub: Mistral Small 2503": "mistral-ai/mistral-small-2503",
    "GitHub: Mistral Medium 2505": "mistral-ai/mistral-medium-2505",
    "GitHub: Ministral 3B": "mistral-ai/ministral-3b",
    "GitHub: Codestral 2501": "mistral-ai/codestral-2501",
    "GitHub: Cohere Command R+": "cohere/cohere-command-r-plus-08-2024",
    "GitHub: Cohere Command R": "cohere/cohere-command-r-08-2024",
    "GitHub: Cohere Command A": "cohere/cohere-command-a",
    "GitHub: DeepSeek R1": "deepseek/deepseek-r1",
    "GitHub: DeepSeek R1 0528": "deepseek/deepseek-r1-0528",
    "GitHub: DeepSeek V3": "deepseek/deepseek-v3-0324",
    "GitHub: MAI-DS-R1": "microsoft/mai-ds-r1",
    "GitHub: Phi-4": "microsoft/phi-4",
    "GitHub: Phi-4 Mini": "microsoft/phi-4-mini-instruct",
    "GitHub: Phi-4 Reasoning": "microsoft/phi-4-reasoning",
    "GitHub: Phi-4 Mini Reasoning": "microsoft/phi-4-mini-reasoning",
    "GitHub: Phi-4 Multimodal": "microsoft/phi-4-multimodal-instruct",
    "GitHub: Jamba 1.5 Large": "ai21-labs/ai21-jamba-1.5-large",
    "GitHub: Grok-3": "xai/grok-3",
    "GitHub: Grok-3 Mini": "xai/grok-3-mini",
    # GitHub Models - bare model IDs (new API shape)
    "GitHub: GPT-4o": "gpt-4o",
    "GitHub: GPT-4.1": "gpt-4.1",
    "GitHub: GPT-5 Mini": "gpt-5-mini",
    "GitHub: GPT-5.3 Codex": "gpt-5.3-codex",
    "GitHub: GPT-5.4": "gpt-5.4",
    "GitHub: Claude Haiku 4.5": "claude-haiku-4.5",
    "GitHub: Claude Sonnet 4": "claude-sonnet-4",
    "GitHub: Claude Sonnet 4.5": "claude-sonnet-4.5",
    "GitHub: Claude Sonnet 4.6": "claude-sonnet-4.6",
    "GitHub: Claude Opus 4.5": "claude-opus-4.5",
    "GitHub: Claude Opus 4.6": "claude-opus-4.6",
    "GitHub: Gemini 2.5 Pro": "gemini-2.5-pro",
    "GitHub: Gemini 3 Flash (Preview)": "gemini-3-flash-preview",
    "GitHub: Gemini 3 Pro (Preview)": "gemini-3-pro-preview",
    "GitHub: Gemini 3.1 Pro (Preview)": "gemini-3.1-pro-preview",
    
    "Groq: Llama 3.3 70B": "llama-3.3-70b-versatile",
    "Groq: Llama 3.1 8B": "llama-3.1-8b-instant",
    "Groq: GPT OSS 120B": "openai/gpt-oss-120b",
    "Groq: GPT OSS 20B": "openai/gpt-oss-20b",
    "Groq: Compound": "groq/compound",
    "Groq: Compound Mini": "groq/compound-mini",
    "Groq: Llama 4 Maverick": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "Groq: Llama 4 Scout": "meta-llama/llama-4-scout-17b-16e-instruct",
    "Groq: Qwen3 32B": "qwen/qwen3-32b",
    "Groq: Kimi K2": "moonshotai/kimi-k2-instruct-0905",
    # Groq dynamic cache models (raw IDs -> readable names)
    "Groq: Allam 2 7B": "allam-2-7b",
    "Groq: Orpheus Arabic Saudi": "canopylabs/orpheus-arabic-saudi",
    "Groq: Orpheus V1 English": "canopylabs/orpheus-v1-english",
    "Groq: Llama Prompt Guard 2 22M": "meta-llama/llama-prompt-guard-2-22m",
    "Groq: Llama Prompt Guard 2 86M": "meta-llama/llama-prompt-guard-2-86m",
    "Groq: Kimi K2 Instruct": "moonshotai/kimi-k2-instruct",
    "Groq: GPT OSS Safeguard 20B": "openai/gpt-oss-safeguard-20b",
    
    "Mistral: Large": "mistral-large-latest",
    "Mistral: Medium": "mistral-medium",
    "Mistral: Small": "mistral-small-latest",
    "Mistral: Mixtral 8x7B": "open-mixtral-8x7b",
    "Mistral: Mixtral 8x22B": "open-mixtral-8x22b",
    
    "Ollama: Mistral": "mistral",
    "Ollama: Llama2": "llama2",
    "Ollama: Neural Chat": "neural-chat",
    "Ollama: Orca Mini": "orca-mini",
    "Ollama: Dolphin Mixtral": "dolphin-mixtral",
    "Ollama: OpenChat": "openchat",
    
    "OpenRouter: Claude Opus 4.6": "anthropic/claude-opus-4.6",
    "OpenRouter: Claude Sonnet 4.6": "anthropic/claude-sonnet-4.6",
    "OpenRouter: GPT-4o": "openai/gpt-4o",
    "OpenRouter: GPT-4o-mini": "openai/gpt-4o-mini",
    "OpenRouter: Llama 3.1 405B": "meta-llama/llama-3.1-405b-instruct",
    "OpenRouter: Mistral Large": "mistralai/mistral-large-2512",
    "OpenRouter: Gemini 2.0 Flash": "google/gemini-2.0-flash-001",
    "OpenRouter: Auto": "openrouter/auto",
    
    "DeepSeek: Chat": "deepseek-chat",
    "DeepSeek: R1": "deepseek-r1",
    "DeepSeek: V3": "deepseek-v3",
    "xAI: Grok-3": "grok-3",
    "xAI: Grok-3 Mini": "grok-3-mini",
    "xAI: Grok Code Fast 1": "grok-code-fast-1",
    "xAI: Grok 4.20 Multi-Agent 0309": "grok-4.20-multi-agent-0309",
    "xAI: Grok 4.20 0309 Reasoning": "grok-4.20-0309-reasoning",
    "xAI: Grok 4.20 0309 Non-Reasoning": "grok-4.20-0309-non-reasoning",
    "xAI: Grok 4 Fast Reasoning": "grok-4-fast-reasoning",
    "xAI: Grok 4 Fast Non-Reasoning": "grok-4-fast-non-reasoning",
    "xAI: Grok 4.1 Fast Reasoning": "grok-4-1-fast-reasoning",
    "xAI: Grok 4.1 Fast Non-Reasoning": "grok-4-1-fast-non-reasoning",
    "xAI: Grok 4 0709": "grok-4-0709",
    
    "MiniMax: M2.1": "MiniMax-M2.1",
    "MiniMax: M2": "MiniMax-M2",
    "MiniMax: M3": "MiniMax-M3",
    
    "AiHubMix: GPT-4o": "gpt-4o",
    "AiHubMix: GPT-4-turbo": "gpt-4-turbo",
    "AiHubMix: Claude Opus": "claude-opus-4-6",
    "AiHubMix: Claude Sonnet": "claude-sonnet-4-6",
    "AiHubMix: Gemini": "gemini-2.0-flash",
    "AiHubMix: Llama": "llama-3.1-405b",
    
    "SiliconFlow: Qwen 2.5 7B": "Qwen/Qwen2.5-7B-Instruct",
    "SiliconFlow: Qwen 2.5 32B": "Qwen/Qwen2.5-32B-Instruct",
    "SiliconFlow: Llama 3.1 8B": "meta-llama/Llama-3.1-8B-Instruct",
    "SiliconFlow: Llama 3.1 70B": "meta-llama/Llama-3.1-70B-Instruct",
    "SiliconFlow: Mistral 7B": "mistral/Mistral-7B-Instruct-v0.3",
    
    "VolcEngine: Qwen 2.5 7B": "Qwen/Qwen2.5-7B-Instruct",
    "VolcEngine: Qwen 2.5 32B": "Qwen/Qwen2.5-32B-Instruct",
    "VolcEngine: Llama 3.1 8B": "meta-llama/Llama-3.1-8B-Instruct",
    "VolcEngine: Llama 3.1 70B": "meta-llama/Llama-3.1-70B-Instruct",
    
    "DashScope: Qwen Max": "qwen-max",
    "DashScope: Qwen Plus": "qwen-plus",
    "DashScope: Qwen Turbo": "qwen-turbo",
    "DashScope: Qwen Long": "qwen-long",
    "DashScope: Qwen VL+": "qwen-vl-plus",
    
    "Moonshot: Kimi K2.5": "kimi-k2.5",
    "Moonshot: Kimi K2": "kimi-k2",
    "Moonshot: Kimi K1.5": "kimi-k1.5",
    "Moonshot: Kimi K1": "kimi-k1",
    
    "Zhipu: GLM-4-Flash (free)": "glm-4-flash",
    "Zhipu: GLM-4-Flash 250414 (free)": "glm-4-flash-250414",
    "Zhipu: GLM-4-Air": "glm-4-air",
    "Zhipu: GLM-4-AirX": "glm-4-airx",
    "Zhipu: GLM-4-Plus": "glm-4-plus",
    "Zhipu: GLM-4-Long": "glm-4-long",
    "Zhipu: GLM-Z1-Flash (free reasoning)": "glm-z1-flash",
    "Zhipu: GLM-Z1-Air": "glm-z1-air",
    "Zhipu: GLM-Z1-AirX": "glm-z1-airx",
    "Zhipu: GLM-4 (legacy)": "glm-4",
    "Zhipu: GLM-4v (legacy)": "glm-4v",
    
    # GitHub Copilot — legacy display name → model id mappings
    "GitHub Copilot: GPT-4o": "gpt-4o",
    "GitHub Copilot: GPT-4o-mini": "gpt-4o-mini",
    "GitHub Copilot: GPT-4.1": "gpt-4.1",
    "GitHub Copilot: o3-mini": "o3-mini",
    "GitHub Copilot: o1": "o1",
    "GitHub Copilot: o1-mini": "o1-mini",
    "GitHub Copilot: Claude Opus 4.6": "claude-opus-4.6",
    "GitHub Copilot: Claude Opus 4.6 Fast": "claude-opus-4.6-fast",
    "GitHub Copilot: Claude Sonnet 4.6": "claude-sonnet-4.6",
    "GitHub Copilot: Claude Sonnet 4.5": "claude-sonnet-4.5",
    "GitHub Copilot: Claude Opus 4.5": "claude-opus-4.5",
    "GitHub Copilot: Claude Sonnet 4": "claude-sonnet-4",
    "GitHub Copilot: Claude Haiku 4.5": "claude-haiku-4.5",
    "GitHub Copilot: Claude 3.7 Sonnet": "claude-3.7-sonnet",
    "GitHub Copilot: Claude 3.5 Sonnet": "claude-3.5-sonnet",
    # GitHub Copilot — raw model ids normalized to readable labels
    "GitHub Copilot: claude-opus-4-5": "claude-opus-4-5",
    "GitHub Copilot: GPT-4o (2024-11-20)": "gpt-4o-2024-11-20",
    "GitHub Copilot: GPT-4o (2024-08-06)": "gpt-4o-2024-08-06",
    "GitHub Copilot: GPT-4o Mini (2024-07-18)": "gpt-4o-mini-2024-07-18",
    "GitHub Copilot: GPT-4o (2024-05-13)": "gpt-4o-2024-05-13",
    "GitHub Copilot: GPT-4o Preview": "gpt-4-o-preview",
    "GitHub Copilot: GPT-4.1 Copilot": "gpt-41-copilot",
    "GitHub Copilot: GPT-4.1 (2025-04-14)": "gpt-4.1-2025-04-14",
    "GitHub Copilot: GPT-4 (Legacy)": "gpt-4",
    "GitHub Copilot: GPT-4-0613 (Legacy)": "gpt-4-0613",
    "GitHub Copilot: GPT-3.5 Turbo (Legacy)": "gpt-3.5-turbo",
    "GitHub Copilot: GPT-3.5 Turbo-0613 (Legacy)": "gpt-3.5-turbo-0613",
    "GitHub Copilot: Gemini 3.1 Pro": "gemini-3.1-pro-preview",
    "GitHub Copilot: Gemini 3 Pro": "gemini-3-pro-preview",
    "GitHub Copilot: Gemini 3 Flash": "gemini-3-flash-preview",
    "GitHub Copilot: Gemini 2.5 Pro": "gemini-2.5-pro",
    "GitHub Copilot: Gemini 2.0 Flash": "gemini-2.0-flash",
    "GitHub Copilot: Gemini 1.5 Pro": "gemini-1.5-pro",
    "GitHub Copilot: Grok Code Fast": "grok-code-fast-1",
    "GitHub Copilot: GPT-5.3 Codex": "gpt-5.3-codex",
    "GitHub Copilot: GPT-5.2 Codex": "gpt-5.2-codex",
    "GitHub Copilot: GPT-5.1": "gpt-5.1",
    "GitHub Copilot: GPT-5.2": "gpt-5.2",
    "GitHub Copilot: GPT-5-mini": "gpt-5-mini",
    "GitHub Copilot: GPT-5.4": "gpt-5.4",
    "GitHub Copilot: GPT-5.4-mini": "gpt-5.4-mini",

    "OpenAI Codex: GPT-5.3 Codex": "gpt-5.3-codex",
    "OpenAI Codex: GPT-5.3 Codex Spark": "gpt-5.3-codex-spark",
    "OpenAI Codex: GPT-5.2 Codex": "gpt-5.2-codex",
    "OpenAI Codex: GPT-5.1 Codex Max": "gpt-5.1-codex-max",
    "OpenAI Codex: GPT-5.1 Codex": "gpt-5.1-codex",
    "OpenAI Codex: GPT-5 Codex": "gpt-5-codex",
    "OpenAI Codex: GPT-5 Codex Mini": "gpt-5-codex-mini",
    "Claude Web: Claude Opus 4.6": "claude-opus-4-6",
    "Claude Web: Claude Sonnet 4.6": "claude-sonnet-4-6",
    "Claude Web: Claude Opus 4.5": "claude-opus-4-5-20251101",
    "Claude Web: Claude Sonnet 4.5": "claude-sonnet-4-5-20250929",
    "Claude Web: Claude Haiku 4.5": "claude-haiku-4-5-20251001",
    "ChatGPT Web: gpt-4o": "gpt-4o",
    "ChatGPT Web: gpt-4o-mini": "gpt-4o-mini",
    "ChatGPT Web: gpt-4.5": "gpt-4.5",
    "ChatGPT Web: gpt-5": "gpt-5",
    "ChatGPT Web: gpt-5.2": "gpt-5.2",
    "ChatGPT Web: chatgpt-4o-latest": "chatgpt-4o-latest",
    "ChatGPT Web: o1": "o1",
    "ChatGPT Web: o3": "o3",
    "ChatGPT Web: o3-mini": "o3-mini",
    "ChatGPT Web: o4-mini": "o4-mini",
    "Gemini Web: Gemini 3.1 Pro": "gemini-3.1-pro",
    "Gemini Web: Gemini 3.0 Pro": "gemini-3.0-pro",
    "Gemini Web: Gemini 3.0 Flash": "gemini-3.0-flash",
    "Gemini Web: Gemini 3.0 Flash Thinking": "gemini-3.0-flash-thinking",
    "Perplexity Web: Pro": "pplx_pro",
    "Perplexity Web: Reasoning": "pplx_reasoning",
    "Perplexity Web: Auto": "pplx_auto",
    "Perplexity Web: Deep Research": "pplx_deep_research",
    "Perplexity Web: Sonar": "sonar",
    "Perplexity Web: GPT-5.2": "gpt-5.2",
    "Perplexity Web: GPT-5.4": "gpt-5.4",
    "Perplexity Web: Claude 4.5 Sonnet": "claude-4.5-sonnet",
    "Perplexity Web: Claude Sonnet 4.6": "claude-4.6-sonnet",
    "Perplexity Web: Claude Opus 4.6": "claude-4.6-opus",
    "Perplexity Web: Grok 4.1": "grok-4-1",
    "Perplexity Web: Gemini 3.1 Pro": "gemini-3.1-pro",
    "Perplexity Web: Nemotron 3 Super": "nemotron-3-super",
    "Perplexity Web: GPT-5.2 Thinking": "gpt-5.2-thinking",
    "Perplexity Web: Claude 4.5 Sonnet Thinking": "claude-4.5-sonnet-thinking",
    "Perplexity Web: Gemini 3.0 Pro": "gemini-3.0-pro",
    "Perplexity Web: Kimi K2 Thinking": "kimi-k2-thinking",
    "Perplexity Web: Grok 4.1 Reasoning": "grok-4.1-reasoning",
}

# Per-provider reverse mapping: {provider: {technical_name: display_name}}
# This avoids conflicts when same technical model exists in multiple providers (e.g., gpt-4o in OpenAI and GitHub)
PROVIDER_DISPLAY = {}  # provider -> {tech_name -> display_name}
_PREFIX_TO_PROVIDER = {
    "Claude:": "anthropic",
    "OpenAI:": "openai",
    "Google:": "google",
    "NVIDIA:": "nvidia",
    "GitHub:": "github",
    "Groq:": "groq",
    "Mistral:": "mistral",
    "Ollama:": "ollama",
    "OpenRouter:": "openrouter",
    "DeepSeek:": "deepseek",
    "xAI:": "xai",
    "MiniMax:": "minimax",
    "AiHubMix:": "aihubmix",
    "SiliconFlow:": "siliconflow",
    "VolcEngine:": "volcengine",
    "DashScope:": "dashscope",
    "Moonshot:": "moonshot",
    "Zhipu:": "zhipu",
    "GitHub Copilot:": "github_copilot",
    "OpenAI Codex:": "openai_codex",
    "Claude Web:": "claude_web",
    "ChatGPT Web:": "chatgpt_web",
    "Gemini Web:": "gemini_web",
    "Perplexity Web:": "perplexity_web",
}
for _display_name, _tech_name in MODEL_NAME_MAPPING.items():
    for _prefix, _prov in _PREFIX_TO_PROVIDER.items():
        if _display_name.startswith(_prefix):
            if _prov not in PROVIDER_DISPLAY:
                PROVIDER_DISPLAY[_prov] = {}
            # Use a stable display name per provider
            if _tech_name not in PROVIDER_DISPLAY[_prov]:
                PROVIDER_DISPLAY[_prov][_tech_name] = _display_name
            break

# Legacy flat mapping (for backward compatibility)
MODEL_DISPLAY_MAPPING = {}
for _prov_models in PROVIDER_DISPLAY.values():
    for _tech, _disp in _prov_models.items():
        if _tech not in MODEL_DISPLAY_MAPPING:
            MODEL_DISPLAY_MAPPING[_tech] = _disp


def _humanize_nvidia_model_name(model_id: str) -> str:
    """Generate a readable NVIDIA model display label from a technical model ID."""
    raw = str(model_id or "").strip()
    if not raw:
        return "Model"
    core = raw.split("/", 1)[1] if "/" in raw else raw
    core = core.replace("_", "-")
    tokens = [t for t in core.split("-") if t]
    if not tokens:
        return core

    token_map = {
        "ai": "AI",
        "api": "API",
        "oss": "OSS",
        "gpt": "GPT",
        "llama": "Llama",
        "qwen": "Qwen",
        "gemma": "Gemma",
        "deepseek": "DeepSeek",
        "mistral": "Mistral",
        "mistralai": "MistralAI",
        "minimax": "MiniMax",
        "moonshotai": "MoonshotAI",
        "nemotron": "Nemotron",
        "nemoretriever": "NemoRetriever",
        "nemoguard": "NemoGuard",
        "chatqa": "ChatQA",
        "coder": "Coder",
        "instruct": "Instruct",
        "reasoning": "Reasoning",
        "vision": "Vision",
        "flash": "Flash",
        "thinking": "Thinking",
        "content": "Content",
        "safety": "Safety",
        "guard": "Guard",
        "translate": "Translate",
        "mini": "Mini",
        "nano": "Nano",
        "super": "Super",
        "ultra": "Ultra",
        "it": "IT",
        "vl": "VL",
        "pii": "PII",
    }

    out = []
    for tok in tokens:
        low = tok.lower()
        if low in token_map:
            out.append(token_map[low])
            continue
        if re.fullmatch(r"\d+b", low):
            out.append(low[:-1] + "B")
            continue
        if re.fullmatch(r"v\d+(\.\d+)?", low):
            out.append(low)
            continue
        if re.fullmatch(r"\d+(\.\d+)?", low):
            out.append(low)
            continue
        out.append(low.capitalize())
    return " ".join(out)


def get_model_display_name(provider: str, technical_name: str) -> str:
    """Return best-effort human display name for a model ID."""
    prov = (provider or "").strip()
    tech = str(technical_name or "").strip()
    if not tech:
        return tech
    by_provider = PROVIDER_DISPLAY.get(prov, {})
    if tech in by_provider:
        return by_provider[tech]
    if tech in MODEL_DISPLAY_MAPPING:
        return MODEL_DISPLAY_MAPPING[tech]
    if prov == "nvidia":
        return f"NVIDIA: {_humanize_nvidia_model_name(tech)}"
    if prov == "xai":
        return f"xAI: {_humanize_nvidia_model_name(tech)}"
    return tech


# Ensure NVIDIA always has readable names, even for dynamically discovered IDs.
try:
    PROVIDER_DISPLAY.setdefault("nvidia", {})
    for _mid in PROVIDER_MODELS.get("nvidia", []) or []:
        if _mid not in PROVIDER_DISPLAY["nvidia"]:
            PROVIDER_DISPLAY["nvidia"][_mid] = f"NVIDIA: {_humanize_nvidia_model_name(_mid)}"
        if _mid not in MODEL_DISPLAY_MAPPING:
            MODEL_DISPLAY_MAPPING[_mid] = PROVIDER_DISPLAY["nvidia"][_mid]
except Exception as _e:
    logger.debug(f"NVIDIA display name bootstrap skipped: {_e}")


# Model utility functions moved to core.model_utils module

def get_api_key() -> str:
    """Get the API key for the active provider."""
    if AI_PROVIDER == "anthropic":
        return ANTHROPIC_API_KEY
    elif AI_PROVIDER == "openai":
        return OPENAI_API_KEY
    elif AI_PROVIDER == "google":
        return GOOGLE_API_KEY
    elif AI_PROVIDER == "nvidia":
        return NVIDIA_API_KEY
    elif AI_PROVIDER == "github":
        return GITHUB_TOKEN
    elif AI_PROVIDER == "groq":
        return GROQ_API_KEY
    elif AI_PROVIDER == "mistral":
        return MISTRAL_API_KEY
    elif AI_PROVIDER == "openrouter":
        return OPENROUTER_API_KEY
    elif AI_PROVIDER == "deepseek":
        return DEEPSEEK_API_KEY
    elif AI_PROVIDER == "xai":
        return XAI_API_KEY
    elif AI_PROVIDER == "minimax":
        return MINIMAX_API_KEY
    elif AI_PROVIDER == "aihubmix":
        return AIHUBMIX_API_KEY
    elif AI_PROVIDER == "siliconflow":
        return SILICONFLOW_API_KEY
    elif AI_PROVIDER == "volcengine":
        return VOLCENGINE_API_KEY
    elif AI_PROVIDER == "dashscope":
        return DASHSCOPE_API_KEY
    elif AI_PROVIDER == "moonshot":
        return MOONSHOT_API_KEY
    elif AI_PROVIDER == "zhipu":
        return ZHIPU_API_KEY
    elif AI_PROVIDER == "custom":
        return CUSTOM_API_KEY
    elif AI_PROVIDER == "github_copilot":
        return GITHUB_COPILOT_TOKEN
    elif AI_PROVIDER == "openai_codex":
        return OPENAI_CODEX_TOKEN
    elif AI_PROVIDER == "claude_web":
        return ""
    elif AI_PROVIDER == "chatgpt_web":
        return ""
    elif AI_PROVIDER == "gemini_web":
        return ""
    elif AI_PROVIDER == "perplexity_web":
        return ""
    return ""


def get_max_tokens_param(max_tokens_value: int) -> dict:
    """Get the correct max tokens parameter based on the model.

    Newer models (o1, o3, o4, GPT-5, Grok-3) use 'max_completion_tokens' instead of 'max_tokens'.

    Args:
        max_tokens_value: The token limit value

    Returns:
        dict with either {"max_tokens": value} or {"max_completion_tokens": value}
    """
    # NVIDIA's OpenAI-compatible endpoint expects max_tokens.
    if AI_PROVIDER == "nvidia":
        return {"max_tokens": max_tokens_value}

    model = get_active_model().lower()

    # Models that require max_completion_tokens instead of max_tokens
    new_api_models = [
        "o1", "o3", "o4", "gpt-5", "grok-3", "grok-4"
    ]

    # Check if current model uses the new API parameter
    uses_new_api = any(pattern in model for pattern in new_api_models)

    if uses_new_api:
        return {"max_completion_tokens": max_tokens_value}
    else:
        return {"max_tokens": max_tokens_value}


def _retry_with_swapped_max_token_param(kwargs: dict, max_tokens_value: int, api_err: Exception):
    """Retry once by swapping max_tokens/max_completion_tokens when API says it's unsupported.

    Some providers/models (including GitHub Models) require different parameter names depending on model.
    Returns a response object on success, or None if no retry was attempted.
    """
    error_msg = str(api_err)

    wants_max_completion = ("use 'max_completion_tokens'" in error_msg.lower())
    wants_max_tokens = ("use 'max_tokens'" in error_msg.lower())

    if not (wants_max_completion or wants_max_tokens):
        return None

    # Swap parameters
    if wants_max_completion:
        kwargs.pop("max_tokens", None)
        kwargs["max_completion_tokens"] = max_tokens_value
        logger.warning("Retrying after unsupported_parameter: switching to max_completion_tokens")
    elif wants_max_tokens:
        kwargs.pop("max_completion_tokens", None)
        kwargs["max_tokens"] = max_tokens_value
        logger.warning("Retrying after unsupported_parameter: switching to max_tokens")

    return ai_client.chat.completions.create(**kwargs)


def _normalize_tool_args(args: object) -> str:
    """Return a stable string representation for tool-call arguments."""
    try:
        return json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        return str(args)


def _tool_signature(fn_name: str, args: object) -> str:
    return f"{fn_name}:{_normalize_tool_args(args)}"


def _github_model_variants(model: str) -> list[str]:
    """Return model identifier variants for GitHub Models runtime.

    GitHub's public catalog uses fully qualified IDs like 'openai/gpt-4o'.
    Some runtime configurations expect the short form (e.g., 'gpt-4o').
    We try both when we hit unknown_model.
    """
    if not model:
        return []
    variants = [model]
    if "/" in model:
        short = model.split("/", 1)[1]
        if short and short not in variants:
            variants.append(short)
    return variants


def get_ha_token() -> str:
    """Get the Home Assistant supervisor token."""
    return SUPERVISOR_TOKEN


def get_ha_headers() -> dict:
    """Get headers for Home Assistant API calls."""
    token = get_ha_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def _strip_context_for_log(message: str, max_len: int = 500) -> str:
    """Strip [CONTEXT: ...] instruction block from a message for cleaner log output.

    Keeps only the YAML block embedded in the context (if present) and the user
    text that follows. Strategy: the context block always starts with '[CONTEXT:'
    and ends with the LAST ']' before the user message. We find the closing bracket
    by scanning from the end of the first YAML block, or by finding the last ']'
    followed by whitespace+text (the user message).
    """
    if not message.startswith("[CONTEXT:"):
        out = message
    else:
        # Find the YAML block first (```yaml ... ```)
        yaml_match = re.search(r'```yaml\n(.*?)```', message, re.DOTALL)
        # Find the user text: everything after the last '] \n' or '] ' near the end
        # The context block closes with ']' followed by optional whitespace + user text.
        # We find the closing bracket by looking for the pattern:
        #   ...last occurrence of '] \n' or ']\n' followed by non-empty text
        closing = re.search(r'\]\s*\n([\s\S]+)$', message)
        user_text = closing.group(1).strip() if closing else ""
        if yaml_match:
            yaml_content = yaml_match.group(1).strip()
            out = f"[YAML]\n```yaml\n{yaml_content}\n```"
            if user_text:
                out += f"\n{user_text}"
        else:
            out = user_text or message
    return out if len(out) <= max_len else out[:max_len // 2] + f"... [{len(out)} chars] ..." + out[-80:]


# Cache for addon ingress URL (doesn't change at runtime)
_ingress_url_cache: Optional[str] = None


def get_addon_ingress_url() -> str:
    """Get the Ingress URL path for this addon from the Supervisor API.
    
    Returns the ingress_url (e.g., '/api/hassio_ingress/<token>') that can be
    used as prefix for iframe URLs so HA frontend proxies to the addon.
    Result is cached since it doesn't change at runtime.
    Retries up to 3 times with 2s delay if the Supervisor isn't ready yet.
    """
    global _ingress_url_cache
    if _ingress_url_cache is not None:
        return _ingress_url_cache

    import time as _time
    for attempt in range(3):
        try:
            resp = requests.get(
                "http://supervisor/addons/self/info",
                headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                ingress_url = data.get("data", {}).get("ingress_url", "")
                if ingress_url:
                    _ingress_url_cache = ingress_url.rstrip("/")
                    logger.info(f"🔗 Addon Ingress URL: {_ingress_url_cache}")
                    return _ingress_url_cache
                else:
                    logger.warning("⚠️ ingress_url not found in Supervisor addon info")
            else:
                logger.error(f"❌ Supervisor API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"❌ Failed to get addon ingress URL (attempt {attempt + 1}/3): {e}")
        if attempt < 2:
            _time.sleep(2)

    _ingress_url_cache = ""
    return _ingress_url_cache


# ---- Initialize AI client ----

def initialize_ai_client():
    """Initialize or reinitialize the AI client based on current provider."""
    global ai_client

    api_key = get_api_key()

    if AI_PROVIDER == "anthropic" and api_key:
        import anthropic
        ai_client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"Anthropic client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "openai" and api_key:
        from openai import OpenAI
        # Force the official OpenAI API base URL to avoid environment leakage
        # (e.g., OPENAI_BASE_URL configured externally for GitHub Models).
        ai_client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")
        logger.info(f"OpenAI client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "google" and api_key:
        from google import genai
        ai_client = genai.Client(api_key=api_key)
        logger.info(f"Google Gemini client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "nvidia" and api_key:
        from openai import OpenAI
        ai_client = OpenAI(
            api_key=api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        logger.info(f"NVIDIA NIM client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "github" and api_key:
        from openai import OpenAI
        ai_client = OpenAI(
            api_key=api_key,
            base_url="https://models.github.ai/inference",
            default_headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        logger.info(f"GitHub Models client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "ollama":
        # Ollama provider (local or cloud) is handled by providers/manager.py
        _mode = "cloud" if OLLAMA_API_KEY else "local"
        logger.info(f"Ollama provider selected ({_mode}). Model: {get_active_model()}")
        ai_client = None
    elif AI_PROVIDER in (
        "groq", "mistral", "openrouter", "deepseek", "xai", "minimax",
        "aihubmix", "siliconflow", "volcengine", "dashscope",
        "moonshot", "zhipu", "github_copilot", "openai_codex",
        "claude_web", "chatgpt_web", "gemini_web", "perplexity_web",
    ):
        # Questi provider usano providers/manager.py — non serve un ai_client dedicato
        if api_key:
            logger.info(f"{AI_PROVIDER} provider ready (model: {get_active_model()})")
        elif AI_PROVIDER == "github_copilot":
            # GitHub Copilot usa OAuth device flow — nessuna API key necessaria nella config
            _oauth_file = "/data/oauth_copilot.json"
            if os.path.isfile(_oauth_file):
                logger.info(f"github_copilot provider ready via OAuth (model: {get_active_model()})")
            else:
                logger.info(f"github_copilot selected — authenticate via the 🔑 button in the UI")
        elif AI_PROVIDER == "openai_codex":
            # OpenAI Codex usa OAuth — nessuna API key necessaria nella config
            _oauth_file = "/data/oauth_codex.json"
            if os.path.isfile(_oauth_file):
                logger.info(f"openai_codex provider ready via OAuth (model: {get_active_model()})")
            else:
                logger.info(f"openai_codex selected — authenticate via the 🔑 button in the UI")
        elif AI_PROVIDER == "claude_web":
            _session_file = "/data/session_claude_web.json"
            if os.path.isfile(_session_file):
                logger.info(f"claude_web provider ready via session token (model: {get_active_model()})")
            else:
                logger.info("claude_web selected — authenticate via the 🔑 button in the UI")
        elif AI_PROVIDER == "chatgpt_web":
            _session_file = "/data/session_chatgpt_web.json"
            if os.path.isfile(_session_file):
                logger.info(f"chatgpt_web provider ready via session token (model: {get_active_model()})")
            else:
                logger.info("chatgpt_web selected — authenticate via the 🔑 button in the UI")
        elif AI_PROVIDER == "gemini_web":
            _session_file = "/data/session_gemini_web.json"
            if os.path.isfile(_session_file):
                logger.info(f"gemini_web provider ready via session cookies (model: {get_active_model()})")
            else:
                logger.info("gemini_web selected — authenticate via the 🔑 button in the UI")
        elif AI_PROVIDER == "perplexity_web":
            _session_file = "/data/session_perplexity_web.json"
            if os.path.isfile(_session_file):
                logger.info(f"perplexity_web provider ready via session cookies (model: {get_active_model()})")
            else:
                logger.info("perplexity_web selected — authenticate via the 🔑 button in the UI")
        else:
            logger.warning(f"AI provider '{AI_PROVIDER}' not configured - set the API key in addon settings")
        ai_client = None
    else:
        logger.warning(f"AI provider '{AI_PROVIDER}' not configured - set the API key in addon settings")
        ai_client = None

    return ai_client


from contextlib import contextmanager

@contextmanager
def _apply_channel_agent(channel: str):
    """Context manager: temporarily activate the agent assigned to *channel*.

    If the channel has a dedicated agent (configured via /api/agents/channels),
    the global AI_PROVIDER / AI_MODEL / ai_client are switched to that agent's
    model for the duration of the block and restored afterwards.
    If no channel agent is configured, this is a no-op.
    """
    global AI_PROVIDER, AI_MODEL, SELECTED_PROVIDER, SELECTED_MODEL, ai_client

    if not AGENT_CONFIG_AVAILABLE:
        yield
        return

    try:
        mgr = agent_config.get_agent_manager()
        agent_id = mgr.get_channel_agent(channel)
        if not agent_id:
            yield
            return

        agent = mgr.resolve_agent(agent_id)
        if not agent or not agent.model_config.primary:
            yield
            return

        ref = agent.model_config.primary
        # Save current state (including agent globals)
        prev_active = mgr.get_active_agent()
        prev_active_id = prev_active.id if prev_active else None
        saved_globals = (AI_PROVIDER, AI_MODEL, SELECTED_PROVIDER, SELECTED_MODEL, ai_client)

        # Switch to channel agent
        mgr.set_active_agent(agent_id)
        _sync_active_agent_globals()   # update AGENT_SYSTEM_PROMPT_OVERRIDE etc.

        if ref.provider != AI_PROVIDER or ref.model != AI_MODEL:
            AI_PROVIDER = ref.provider
            AI_MODEL = ref.model
            SELECTED_PROVIDER = ref.provider
            SELECTED_MODEL = ref.model
            initialize_ai_client()

        logger.info(f"Channel '{channel}' → agent '{agent_id}' ({ref.provider}/{ref.model})")

        try:
            yield
        finally:
            # Restore previous provider state
            AI_PROVIDER, AI_MODEL, SELECTED_PROVIDER, SELECTED_MODEL, ai_client = saved_globals
            if prev_active_id:
                mgr.set_active_agent(prev_active_id)
                _sync_active_agent_globals()   # restore AGENT_SYSTEM_PROMPT_OVERRIDE
            else:
                initialize_ai_client()
    except Exception as e:
        logger.warning(f"_apply_channel_agent('{channel}') error: {e}")
        yield


ai_client = None
# Prefer persisted selection (set by /api/set_model) over add-on configuration
load_runtime_selection()
initialize_ai_client()

# Sync AGENT_SYSTEM_PROMPT_OVERRIDE and other agent globals from the persisted
# active agent so the first chat request already has the correct system prompt.
if AGENT_CONFIG_AVAILABLE:
    try:
        _sync_active_agent_globals(apply_model=True, persist_selection=True, reinitialize_client=True)
        logger.info("Startup: agent globals synced from persisted active agent")
    except Exception as _e:
        logger.warning(f"Startup agent globals sync failed: {_e}")

import pathlib

# Conversation history
conversations: Dict[str, List[Dict]] = {}

# Abort flag per session (for stop button)
abort_streams: Dict[str, bool] = {}

# Read-only mode per session
read_only_sessions: Dict[str, bool] = {}

# Browser console errors captured from frontend (max 200 entries)
_browser_console_errors: list = []

# Last intent per session (for confirmation continuity)
session_last_intent: Dict[str, str] = {}
# Last preview signature per session (to ensure update matches shown preview)
session_last_preview: Dict[str, Dict[str, Any]] = {}
_PREVIEW_MATCH_TTL_SECONDS = 3600

# Current session ID for thread-safe access in execute_tool (Flask sync workers)
current_session_id: str = "default"

# --- Dynamic config structure scan ---
CONFIG_STRUCTURE_TEXT = ""

def scan_config_structure(root_dir="/config", max_depth=2):
    """Scan the config directory and return a formatted string of its structure."""
    lines = []
    def _scan(path, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(path))
        except Exception:
            return
        for entry in entries:
            if entry.startswith('.'):
                continue
            full = os.path.join(path, entry)
            rel = os.path.relpath(full, root_dir)
            prefix = "  " * depth + ("- " if depth else "")
            if os.path.isdir(full):
                lines.append(f"{prefix}{entry}/")
                _scan(full, depth+1)
            else:
                lines.append(f"{prefix}{entry}")
    _scan(root_dir, 0)
    return "\n".join(lines)

# Scan at startup
try:
    CONFIG_STRUCTURE_TEXT = scan_config_structure()
    logger.info("Config structure scanned for prompt.")
except Exception as e:
    CONFIG_STRUCTURE_TEXT = "(Could not scan config: " + str(e) + ")"
    logger.warning(f"Config structure scan failed: {e}")

def get_config_structure_section():
    return f"\nCurrent Home Assistant config structure (scanned at startup):\n\n{CONFIG_STRUCTURE_TEXT}\n"

# --- Configuration.yaml includes mapping ---
CONFIG_INCLUDES = {}

def parse_configuration_includes():
    """Parse configuration.yaml and extract all !include directives."""
    includes = {}
    config_file = "/config/configuration.yaml"

    if not os.path.isfile(config_file):
        logger.warning("configuration.yaml not found")
        return includes

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Look for patterns like "automation: !include automations.yaml"
            if '!include' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    include_part = parts[1].strip()

                    # Extract the file path after !include
                    if include_part.startswith('!include'):
                        filepath = include_part.replace('!include', '').strip()
                        # Remove quotes if present
                        filepath = filepath.strip('"\'')
                        includes[key] = filepath

        logger.info(f"Parsed configuration.yaml includes: {includes}")
        return includes
    except Exception as e:
        logger.error(f"Error parsing configuration.yaml: {e}")
        return includes

# Parse at startup
CONFIG_INCLUDES = parse_configuration_includes()
if CONFIG_INCLUDES:
    logger.info(f"Configuration includes loaded: {len(CONFIG_INCLUDES)} files mapped")
    for key, path in CONFIG_INCLUDES.items():
        logger.info(f"  - {key}: {path}")
else:
    logger.warning("No includes found in configuration.yaml - using defaults")

def get_config_file_path(key: str, default_filename: str) -> str:
    """Get the full path for a config file using the includes mapping."""
    if key in CONFIG_INCLUDES:
        filepath = CONFIG_INCLUDES[key]
        # Handle relative paths
        if not filepath.startswith('/'):
            filepath = os.path.join(HA_CONFIG_DIR, filepath)
        return filepath
    # Fallback to default
    return os.path.join(HA_CONFIG_DIR, default_filename)

def get_config_includes_text():
    """Generate a formatted text of configuration includes for the AI."""
    if not CONFIG_INCLUDES:
        return ""

    lines = ["## Configuration Files Mapping (from configuration.yaml):"]
    for key, filepath in CONFIG_INCLUDES.items():
        lines.append(f"- **{key}**: {filepath}")

    lines.append("\nIMPORTANT: When working with automations, scripts, scenes, etc., use the file paths above.")
    lines.append("Do NOT search for these files - they are pre-mapped for you.")
    return "\n".join(lines) + "\n"


# Conversation persistence - stored in /config/amira/ for all amira data
CONVERSATIONS_FILE = "/config/amira/conversations.json"

# Backward compatibility: older versions may have used different paths.
LEGACY_CONVERSATIONS_FILES = [
    "/config/.storage/claude_conversations.json",
    "/config/claude_conversations.json",
    "/config/.storage/conversations.json",
    "/data/claude_conversations.json",
    "/data/.storage/claude_conversations.json",
]


def _normalize_conversations_payload(payload: object) -> Dict[str, List[Dict]]:
    """Normalize conversation payload to a dict[session_id] -> list[message]."""
    normalized: Dict[str, List[Dict]] = {}

    if isinstance(payload, dict):
        for sid, msgs in payload.items():
            if not isinstance(sid, str):
                sid = str(sid)
            if not isinstance(msgs, list):
                continue
            cleaned_msgs: List[Dict] = []
            for msg in msgs:
                if isinstance(msg, dict) and msg.get("role"):
                    cleaned_msgs.append(msg)
            if cleaned_msgs:
                normalized[sid] = cleaned_msgs
        return normalized

    # Heuristic for legacy formats: a list of {id/session_id, messages}
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            sid = item.get("id") or item.get("session_id")
            msgs = item.get("messages") or item.get("msgs")
            if isinstance(sid, str) and isinstance(msgs, list):
                cleaned_msgs: List[Dict] = []
                for msg in msgs:
                    if isinstance(msg, dict) and msg.get("role"):
                        cleaned_msgs.append(msg)
                if cleaned_msgs:
                    normalized[sid] = cleaned_msgs
        return normalized

    return normalized


def load_conversations():
    """Load conversations from persistent storage.

    Tries the current path first, then legacy paths. If the current file is
    corrupt, it is backed up and the loader falls back to legacy locations.
    """
    global conversations

    def _try_load(path: str) -> Optional[Dict[str, List[Dict]]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            normalized = _normalize_conversations_payload(payload)
            return normalized if normalized else {}
        except Exception as e:
            logger.warning(f"Could not load conversations from {path}: {e}")
            return None

    candidates = [CONVERSATIONS_FILE] + [p for p in LEGACY_CONVERSATIONS_FILES if p != CONVERSATIONS_FILE]

    for path in candidates:
        if not os.path.isfile(path):
            continue

        loaded = _try_load(path)
        if loaded is None:
            # If the primary file is unreadable, back it up once.
            if path == CONVERSATIONS_FILE:
                try:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup = f"{CONVERSATIONS_FILE}.corrupt.{ts}"
                    os.replace(CONVERSATIONS_FILE, backup)
                    logger.warning(f"Backed up corrupt conversations file to {backup}")
                except Exception as be:
                    logger.warning(f"Could not back up corrupt conversations file: {be}")
            continue

        conversations = loaded
        logger.info(f"Loaded {len(conversations)} conversation(s) from {path}")
        if path != CONVERSATIONS_FILE and conversations:
            # Migrate to the new location.
            save_conversations()
            logger.info(f"Migrated conversations to {CONVERSATIONS_FILE}")
        return


def save_conversations():
    """Save conversations to persistent storage (without image data to save space)."""
    tmp_path = f"{CONVERSATIONS_FILE}.tmp"
    try:
        os.makedirs(os.path.dirname(CONVERSATIONS_FILE), exist_ok=True)
        # Keep only last N sessions (configurable), 50 messages each
        trimmed: Dict[str, List[Dict]] = {}
        for sid, msgs in list(conversations.items())[-MAX_CONVERSATIONS:]:
            if not isinstance(msgs, list):
                continue
            # Strip image data from messages to reduce file size
            cleaned_msgs: List[Dict] = []
            for msg in msgs[-50:]:
                if not isinstance(msg, dict):
                    continue
                cleaned_msg: Dict[str, Any] = {"role": msg.get("role", "")}
                content = msg.get("content", "")

                # If content is an array (with images), extract only text
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    cleaned_msg["content"] = "\n".join(text_parts) if text_parts else "[Image message]"
                else:
                    cleaned_msg["content"] = content

                # Preserve tool_calls and other metadata
                if "tool_calls" in msg:
                    cleaned_msg["tool_calls"] = msg["tool_calls"]

                # Preserve tool_call_id and name for tool response messages
                # (required for pairing with assistant tool_calls on reload)
                if msg.get("role") == "tool":
                    if "tool_call_id" in msg:
                        cleaned_msg["tool_call_id"] = msg["tool_call_id"]
                    if "name" in msg:
                        cleaned_msg["name"] = msg["name"]

                # Preserve model/provider/usage info for assistant messages
                if msg.get("role") == "assistant":
                    if "model" in msg:
                        cleaned_msg["model"] = msg["model"]
                    if "provider" in msg:
                        cleaned_msg["provider"] = msg["provider"]
                    if "usage" in msg:
                        cleaned_msg["usage"] = msg["usage"]

                cleaned_msgs.append(cleaned_msg)

            if cleaned_msgs:
                trimmed[str(sid)] = cleaned_msgs

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, ensure_ascii=False, default=str)
        os.replace(tmp_path, CONVERSATIONS_FILE)
    except Exception as e:
        logger.warning(f"Could not save conversations: {e}")
        try:
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


# Load saved conversations on startup
load_conversations()

# Load persisted model blocklists on startup
load_model_blocklists()

# ---- Snapshot system for safe config editing ----

SNAPSHOTS_DIR = "/config/amira/snapshots"
HA_CONFIG_DIR = "/config"  # Mapped via config.yaml "map: config:rw"

# ---- Device tracking for bubble visibility control ----
DEVICES_CONFIG_FILE = "/config/amira/bubble_devices.json"

def load_device_config() -> dict:
    """Load device visibility configuration from disk."""
    try:
        if os.path.isfile(DEVICES_CONFIG_FILE):
            with open(DEVICES_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            return data
        return {}
    except Exception as e:
        logger.warning(f"Could not load device config: {e}")
        return {}

def save_device_config(config: dict) -> None:
    """Persist device visibility configuration to disk."""
    try:
        os.makedirs(os.path.dirname(DEVICES_CONFIG_FILE), exist_ok=True)
        with open(DEVICES_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Could not save device config: {e}")

def create_snapshot(filename: str) -> dict:
    """Create a snapshot of a file before modifying it. Returns snapshot info."""
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    src_path = os.path.join(HA_CONFIG_DIR, filename)
    if not os.path.isfile(src_path):
        return {"snapshot_id": None, "message": f"File '{filename}' does not exist (new file)"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace("/", "__").replace("\\", "__")
    snapshot_id = f"{timestamp}_{safe_name}"
    snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_id)

    import shutil
    shutil.copy2(src_path, snapshot_path)

    # Save metadata
    meta_path = snapshot_path + ".meta"
    meta = {"original_file": filename, "timestamp": timestamp, "snapshot_id": snapshot_id,
            "size": os.path.getsize(src_path)}
    with open(meta_path, "w") as f:
        json.dump(meta, f)

    # Per-file limit: keep max MAX_SNAPSHOTS_PER_FILE snapshots per original file
    all_snapshots = sorted([f for f in os.listdir(SNAPSHOTS_DIR) if not f.endswith(".meta")])
    # Group by original file (suffix after timestamp_)
    file_snapshots = {}
    for s in all_snapshots:
        parts = s.split("_", 2)  # YYYYMMDD_HHMMSS_filename
        file_key = parts[2] if len(parts) > 2 else s
        file_snapshots.setdefault(file_key, []).append(s)
    for file_key, snaps in file_snapshots.items():
        while len(snaps) > MAX_SNAPSHOTS_PER_FILE:
            oldest = snaps.pop(0)
            try:
                os.remove(os.path.join(SNAPSHOTS_DIR, oldest))
                os.remove(os.path.join(SNAPSHOTS_DIR, oldest + ".meta"))
                logger.debug(f"Snapshot auto-deleted (per-file limit): {oldest}")
            except:
                pass

    logger.info(f"Snapshot created: {snapshot_id}")
    return {"snapshot_id": snapshot_id, "original_file": filename, "timestamp": timestamp}


# ---- Home Assistant API helpers ----


def call_ha_websocket(msg_type: str, **kwargs) -> dict:
    """Send a WebSocket command to Home Assistant and return the result."""
    import websocket as ws_lib
    token = get_ha_token()
    ws_url = HA_URL.replace("http://", "ws://").replace("https://", "wss://") + "/websocket"
    logger.debug(f"WS connect: {ws_url} for {msg_type}")
    try:
        ws = ws_lib.create_connection(ws_url, timeout=15)
        # Wait for auth_required
        auth_req = json.loads(ws.recv())
        logger.debug(f"WS auth_required: {auth_req.get('type')}")
        # Authenticate
        ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth_resp = json.loads(ws.recv())
        if auth_resp.get("type") != "auth_ok":
            ws.close()
            return {"error": f"WS auth failed: {auth_resp}"}
        # Send command
        msg = {"id": 1, "type": msg_type}
        msg.update(kwargs)
        ws.send(json.dumps(msg))
        result = json.loads(ws.recv())
        ws.close()
        logger.debug(f"WS result: {result}")
        return result
    except Exception as e:
        logger.error(f"WS error ({msg_type}): {e}")
        return {"error": str(e)}


def call_ha_api(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
    """Call Home Assistant API."""
    url = f"{HA_URL}/api/{endpoint}"
    headers = get_ha_headers()
    token = get_ha_token()
    logger.debug(f"HA API call: {method} {url} (token present: {bool(token)}, len={len(token)})")
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}

        if response.status_code in [200, 201]:
            return response.json() if response.text else {"status": "success"}
        elif response.status_code == 401:
            logger.error(f"HA API 401 Unauthorized - token might be missing or invalid. HA_URL={HA_URL}, token_len={len(token)}")
            return {"error": "401 Unauthorized - check SUPERVISOR_TOKEN"}
        else:
            logger.error(f"HA API error {response.status_code}: {response.text}")
            return {"error": f"API error {response.status_code}", "details": response.text}
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"error": str(e)}


def get_all_states() -> List[Dict]:
    """Get all entity states from HA."""
    result = call_ha_api("GET", "states")
    return result if isinstance(result, list) else []


# ---- Provider-specific chat implementations ----


def chat_anthropic(messages: List[Dict]) -> tuple:
    """Chat with Anthropic Claude. Returns (response_text, updated_messages)."""
    import anthropic

    response = ai_client.messages.create(
        model=get_active_model(),
        max_tokens=8192,
        system=tools.get_system_prompt(),
        tools=tools.get_anthropic_tools(),
        messages=messages
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        assistant_content = response.content
        for block in response.content:
            if block.type == "tool_use":
                logger.info(f"Tool: {block.name}")
                result = tools.execute_tool(block.name, block.input)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})

        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

        response = ai_client.messages.create(
            model=get_active_model(),
            max_tokens=8192,
            system=tools.get_system_prompt(),
            tools=tools.get_anthropic_tools(),
            messages=messages
        )

    final_text = "".join(block.text for block in response.content if hasattr(block, "text"))
    # Capture usage for non-streaming cost display
    global _last_sync_usage
    try:
        _last_sync_usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0),
            "output_tokens": getattr(response.usage, "output_tokens", 0),
            "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
        }
    except Exception:
        _last_sync_usage = {}
    return final_text, messages


def chat_openai(messages: List[Dict]) -> tuple:
    """Chat with OpenAI/NVIDIA/GitHub. Returns (response_text, updated_messages)."""
    global AI_MODEL
    trimmed = intent.trim_messages(messages)
    system_prompt = tools.get_system_prompt()
    ha_tools = tools.get_openai_tools_for_provider()
    max_tok = 4000 if AI_PROVIDER in ("github", "nvidia") else 4096

    oai_messages = [{"role": "system", "content": system_prompt}] + trimmed

    # NVIDIA Kimi K2.5: use instant mode (thinking mode not yet supported in streaming)
    kwargs = {
        "model": get_active_model(),
        "messages": oai_messages,
        "tools": ha_tools,
        **get_max_tokens_param(max_tok)
    }
    if AI_PROVIDER == "nvidia":
        kwargs["temperature"] = 0.6
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

    try:
        response = ai_client.chat.completions.create(**kwargs)
    except Exception as api_err:
        error_msg = str(api_err)
        if AI_PROVIDER == "github" and (
            "unsupported parameter" in error_msg.lower() or "unsupported_parameter" in error_msg.lower()
        ):
            retry = _retry_with_swapped_max_token_param(kwargs, max_tok, api_err)
            if retry is not None:
                response = retry
            else:
                raise
        elif AI_PROVIDER == "github" and "unknown_model" in error_msg.lower():
            bad_model = kwargs.get("model")

            # Try alternate model formats first (e.g., 'openai/gpt-4o' -> 'gpt-4o')
            tried = []
            for candidate in _github_model_variants(bad_model):
                if candidate in tried:
                    continue
                tried.append(candidate)
                if candidate == bad_model:
                    continue
                try:
                    logger.warning(f"GitHub unknown_model for {bad_model}. Retrying with model={candidate}.")
                    kwargs["model"] = candidate
                    response = ai_client.chat.completions.create(**kwargs)
                    break
                except Exception as retry_err:
                    if "unknown_model" in str(retry_err).lower():
                        continue
                    raise
            else:
                # Still unknown after variants — log and continue
                if bad_model:
                    logger.warning(f"GitHub: all variants of '{bad_model}' returned unknown_model")

                # Final fallback attempts (both qualified and short)
                fallback_candidates = ["openai/gpt-4o", "gpt-4o"]
                for fallback_model in fallback_candidates:
                    if bad_model == fallback_model:
                        continue
                    try:
                        logger.warning(f"GitHub unknown_model: {bad_model}. Falling back to {fallback_model}.")
                        kwargs["model"] = fallback_model
                        response = ai_client.chat.completions.create(**kwargs)
                        break
                    except Exception as fallback_err:
                        if "unknown_model" in str(fallback_err).lower():
                            continue
                        raise
                else:
                    raise
        else:
            raise

    msg = response.choices[0].message

    tool_cache: dict[str, str] = {}
    read_only_tools = {
        "get_automations", "get_scripts", "get_dashboards",
        "get_dashboard_config", "read_config_file",
        "list_config_files", "get_frontend_resources",
        "search_entities", "get_entity_state", "get_entities",
    }

    while msg.tool_calls:
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            logger.info(f"Tool: {tc.function.name}")
            args = json.loads(tc.function.arguments)
            fn_name = tc.function.name
            sig = _tool_signature(fn_name, args)
            if fn_name in read_only_tools and sig in tool_cache:
                logger.warning(f"Reusing cached tool result: {fn_name} {sig}")
                result = tool_cache[sig]
            else:
                result = tools.execute_tool(fn_name, args)
                if fn_name in read_only_tools:
                    tool_cache[sig] = result
            # Truncate tool results for GitHub/NVIDIA to stay within token limits
            if AI_PROVIDER in ("github", "nvidia") and len(result) > 3000:
                result = result[:3000] + '... (truncated)'
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        trimmed = intent.trim_messages(messages)
        oai_messages = [{"role": "system", "content": system_prompt}] + trimmed

        # NVIDIA Kimi K2.5: use instant mode
        kwargs = {
            "model": get_active_model(),
            "messages": oai_messages,
            "tools": ha_tools,
            **get_max_tokens_param(max_tok)
        }
        if AI_PROVIDER == "nvidia":
            kwargs["temperature"] = 0.6
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

        response = ai_client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

    # Capture usage for non-streaming cost display
    global _last_sync_usage
    try:
        _last_sync_usage = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(response.usage, "completion_tokens", 0) or 0,
        }
    except Exception:
        _last_sync_usage = {}
    return msg.content or "", messages


def chat_google(messages: List[Dict]) -> tuple:
    """Chat with Google Gemini. Returns (response_text, updated_messages)."""
    from google.genai import types

    def _to_parts(content: object) -> list[dict]:
        if isinstance(content, str):
            return [{"text": content}]
        if isinstance(content, list):
            parts: list[dict] = []
            for p in content:
                if isinstance(p, str):
                    parts.append({"text": p})
                elif isinstance(p, dict):
                    if "text" in p:
                        parts.append({"text": p.get("text")})
                    elif "inline_data" in p:
                        parts.append({"inline_data": p.get("inline_data")})
            return [pt for pt in parts if pt]
        return []

    contents: list[object] = []
    for m in messages:
        role = m.get("role")
        if role == "assistant":
            role = "model"
        if role not in ("user", "model"):
            continue
        parts = _to_parts(m.get("content"))
        if parts:
            contents.append({"role": role, "parts": parts})

    tool = tools.get_gemini_tools()
    # If ToolRegistry available, use it for Gemini format with policies
    _reg = tools.get_tool_registry()
    if _reg is not None:
        try:
            _ctx = {"tier": tools._get_tool_tier(), "enable_file_access": ENABLE_FILE_ACCESS}
            tool = _reg.format_for_gemini(_ctx)
        except Exception as e:
            logger.debug(f"Registry Gemini format failed, using legacy: {e}")
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[tool],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    while True:
        response = ai_client.models.generate_content(
            model=get_active_model(),
            contents=contents,
            config=config,
        )

        function_calls = getattr(response, "function_calls", None) or []
        if not function_calls:
            # Capture usage for non-streaming cost display
            global _last_sync_usage
            try:
                _usage_meta = getattr(response, "usage_metadata", None)
                if _usage_meta:
                    _last_sync_usage = {
                        "prompt_tokens": getattr(_usage_meta, "prompt_token_count", 0) or 0,
                        "completion_tokens": getattr(_usage_meta, "candidates_token_count", 0) or 0,
                    }
                else:
                    _last_sync_usage = {}
            except Exception:
                _last_sync_usage = {}
            return (response.text or ""), messages

        # Append the model's function-call content, then our tool responses.
        try:
            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)
        except Exception:
            pass

        response_parts: list[types.Part] = []
        for fc in function_calls:
            name = getattr(fc, "name", None)
            args = getattr(fc, "args", None)
            if not name and getattr(fc, "function_call", None):
                name = getattr(fc.function_call, "name", None)
                args = getattr(fc.function_call, "args", None)

            name = (name or "").strip()
            if not name:
                continue

            tool_args = dict(args) if isinstance(args, dict) else (dict(args) if args else {})
            logger.info(f"Tool: {name}")
            result = tools.execute_tool(name, tool_args)
            try:
                parsed = json.loads(result)
            except Exception:
                parsed = result
            response_parts.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": parsed},
                )
            )

        if response_parts:
            contents.append(types.Content(role="tool", parts=response_parts))
        time.sleep(1)


# ---- Main chat function ----


def sanitize_messages_for_provider(messages: List[Dict]) -> List[Dict]:
    """Remove messages incompatible with the current provider.
    Also truncates old messages to reduce token count (critical for rate limits)."""
    clean = []
    _skip_tool_ids: set = set()  # tool_call_ids from skipped assistant messages
    i = 0
    while i < len(messages):
        m = messages[i]
        role = m.get("role", "")
        skip = False

        # NOTE: Anthropic provider now handles tool message conversion internally
        # (see AnthropicProvider._split_system), so we no longer skip tool messages
        # or assistant+tool_calls messages here. The provider converts them to
        # the correct Anthropic format (user+tool_result, assistant+tool_use).

        # For Anthropic: Skip assistant messages with tool_use blocks if not followed by tool_result
        # (only applies to orphaned Anthropic-native tool_use blocks, not OpenAI-format)
        if AI_PROVIDER == "anthropic" and role == "assistant":
            content = m.get("content", "")
            if isinstance(content, list):
                has_tool_use = any(isinstance(c, dict) and c.get("type") == "tool_use" for c in content)
                if has_tool_use:
                    # Check if next message has tool_result
                    next_has_result = False
                    if i + 1 < len(messages):
                        next_msg = messages[i + 1]
                        next_content = next_msg.get("content", "")
                        if next_msg.get("role") == "user" and isinstance(next_content, list):
                            next_has_result = any(isinstance(c, dict) and c.get("type") == "tool_result" for c in next_content)
                    if not next_has_result:
                        # Skip this orphaned tool_use message
                        skip = True

        # Skip Anthropic-format tool_result messages for non-Anthropic providers
        elif AI_PROVIDER != "anthropic" and role == "user" and isinstance(m.get("content"), list):
            if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in m.get("content", [])):
                skip = True

        # Skip orphaned tool responses whose assistant+tool_calls was already skipped
        elif role == "tool" and m.get("tool_call_id") in _skip_tool_ids:
            skip = True

        # For ALL providers: Skip assistant messages with tool_calls if tool responses are missing
        elif role == "assistant" and m.get("tool_calls"):
            tool_call_ids = {tc.get("id") or (tc.get("function", {}).get("name", "")) for tc in m.get("tool_calls", []) if isinstance(tc, dict)}
            # Look ahead for matching tool responses
            found_ids = set()
            for j in range(i + 1, len(messages)):
                if messages[j].get("role") == "tool":
                    found_ids.add(messages[j].get("tool_call_id", ""))
                elif messages[j].get("role") != "tool":
                    break
            if not tool_call_ids.issubset(found_ids):
                skip = True
                # Mark all associated tool IDs so their responses are also skipped
                _skip_tool_ids.update(tool_call_ids)

        # Keep user/assistant/tool messages if not skipped
        if not skip:
            if role in ("user", "assistant"):
                content = m.get("content", "")
                # Accept strings or arrays (arrays can contain images)
                if isinstance(content, str) and content:
                    out_msg = {"role": role, "content": content}
                elif isinstance(content, list) and content:
                    out_msg = {"role": role, "content": content}
                elif role == "assistant" and m.get("tool_calls"):
                    # assistant message may have null/empty content but tool_calls
                    out_msg = {"role": role, "content": content or None}
                else:
                    out_msg = None
                if out_msg is not None:
                    # Preserve tool_calls on assistant messages (required for paired tool responses)
                    if role == "assistant" and m.get("tool_calls"):
                        out_msg["tool_calls"] = m["tool_calls"]
                    clean.append(out_msg)
            elif role == "tool":
                # Pass through tool responses (required after tool_calls for OpenAI-compatible APIs)
                clean.append(m)

        i += 1
    
    # Limit total messages: keep only last MAX_MSGS, but never cut inside
    # an assistant(tool_calls) + tool response group.
    MAX_MSGS = 10
    if len(clean) > MAX_MSGS:
        cut = len(clean) - MAX_MSGS
        # Advance cut past any orphaned tool messages at the start
        while cut < len(clean) and clean[cut].get("role") == "tool":
            cut += 1
        # If we advanced past all messages, fall back to hard cut
        if cut >= len(clean):
            cut = len(clean) - MAX_MSGS
        clean = clean[cut:]
    
    # Final safety: remove any orphaned tool messages that survived truncation.
    # A tool message is valid only if preceded by assistant+tool_calls or another tool.
    validated = []
    for m in clean:
        if m.get("role") == "tool":
            if not validated:
                continue  # orphan at start
            prev = validated[-1]
            if prev.get("role") == "tool" or (prev.get("role") == "assistant" and prev.get("tool_calls")):
                validated.append(m)
            # else: orphaned tool message — skip silently
        else:
            validated.append(m)
    clean = validated

    # Reconstruct missing tool_call_id on tool messages from the preceding
    # assistant+tool_calls message.  Older versions of save_conversations()
    # dropped tool_call_id, causing 400 errors on all providers.
    _tc_id_queue: list = []
    for m in clean:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            _tc_id_queue = [
                tc.get("id") or f"call_{tc.get('function', {}).get('name', 'tool')}_{j}"
                for j, tc in enumerate(m.get("tool_calls", []))
            ]
        elif m.get("role") == "tool":
            if not m.get("tool_call_id"):
                if _tc_id_queue:
                    m["tool_call_id"] = _tc_id_queue.pop(0)
                else:
                    m["tool_call_id"] = f"call_reconstructed_{id(m)}"
        else:
            _tc_id_queue = []

    # Truncate OLD messages to save tokens (keep last 2 messages full)
    MAX_OLD_MSG = 1500
    for i in range(len(clean) - 2):
        content = clean[i].get("content", "")
        # Only truncate string content (skip arrays with images)
        if isinstance(content, str):
            # Strip previously injected smart context from old messages
            if "\n\n---\n\u26a0\ufe0f **CONTESTO PRE-CARICATO" in content:
                # Keep only the user's original message (before the smart context separator)
                content = content.split("\n\n---\n\u26a0\ufe0f **CONTESTO PRE-CARICATO")[0]
            if len(content) > MAX_OLD_MSG:
                content = content[:MAX_OLD_MSG] + "... [old message truncated]"
            truncated = {"role": clean[i]["role"], "content": content}
            # Preserve tool_call_id / name for tool messages (required by all providers)
            if clean[i].get("tool_call_id"):
                truncated["tool_call_id"] = clean[i]["tool_call_id"]
            if clean[i].get("name"):
                truncated["name"] = clean[i]["name"]
            # Preserve tool_calls for assistant messages
            if clean[i].get("tool_calls"):
                truncated["tool_calls"] = clean[i]["tool_calls"]
            clean[i] = truncated
    
    return clean


def _validate_entity_ids_in_response(text: str) -> str:
    """Validate entity IDs mentioned in AI responses against real HA states.

    If the AI hallucinated entity IDs (e.g. invented sensor.epcube_pvpower when
    the real ID is sensor.ep_cube_pv_power), append a warning with the correct
    entity IDs found via keyword matching.

    Only runs when the response contains multiple entity_id references.
    """
    import re

    HA_DOMAINS = (
        "sensor", "binary_sensor", "light", "switch", "climate", "cover",
        "fan", "media_player", "automation", "script", "scene", "group",
        "person", "input_boolean", "input_number", "input_text", "input_select",
        "input_datetime", "button", "number", "select", "text", "lock",
        "alarm_control_panel", "camera", "vacuum", "water_heater", "humidifier",
        "weather", "device_tracker", "timer", "counter", "update", "siren",
        "remote",
        # NOTE: notify, tts, persistent_notification are SERVICES, not entities
    )
    # HA service verbs — patterns like switch.turn_off are service calls, not entity IDs
    _SERVICE_VERBS = {
        "turn_on", "turn_off", "toggle", "reload", "trigger", "press",
        "open_cover", "close_cover", "stop_cover", "lock", "unlock",
        "set_temperature", "set_humidity", "set_hvac_mode", "set_fan_mode",
        "set_value", "set_speed", "set_datetime", "set_position",
        "set_tilt_position", "set_preset_mode", "set_swing_mode",
        "select_option", "select_first", "select_last", "select_next",
        "select_previous", "increment", "decrement",
        "play_media", "media_play", "media_pause", "media_stop",
        "media_next_track", "media_previous_track",
        "volume_up", "volume_down", "volume_mute", "volume_set",
        "start", "stop", "pause", "resume", "open", "close",
        "enable", "disable", "activate", "deactivate",
        "send_message", "notify", "install", "skip",
    }
    domain_pattern = "|".join(re.escape(d) for d in HA_DOMAINS)
    entity_re = re.compile(rf'\b({domain_pattern})\.[a-z0-9][a-z0-9_]*\b')

    found_full = set()
    for m in entity_re.finditer(text):
        candidate = m.group(0)
        suffix = candidate.split(".", 1)[1]
        if suffix not in _SERVICE_VERBS:
            found_full.add(candidate)
    if not found_full or len(found_full) < 2:
        return text

    # Skip generic examples
    EXAMPLE_ENTITIES = {"light.living_room", "switch.living_room", "sensor.temperature",
                        "binary_sensor.motion", "light.soggiorno", "light.camera",
                        "light.xxx", "switch.xxx", "sensor.xxx", "scene.movie_night"}
    if found_full.issubset(EXAMPLE_ENTITIES):
        return text

    try:
        all_states = get_all_states()
        real_eids = {s.get("entity_id", "") for s in all_states}

        invalid = found_full - real_eids
        if not invalid:
            return text

        helper_domains = {
            "input_boolean", "input_number", "input_select",
            "input_text", "input_datetime", "counter",
        }
        invalid_domains = {eid.split(".", 1)[0] for eid in invalid if "." in eid}
        # Helper IDs are often discussed in prose before creation (or mapped fallbacks).
        # Avoid noisy warnings in these cases.
        if invalid_domains and invalid_domains.issubset(helper_domains):
            logger.info(f"Entity validation: skipping helper-only invalid IDs: {invalid}")
            return text

        # Only warn if a significant portion are invalid (>= 2 or majority)
        if len(invalid) < 2 and len(invalid) / max(len(found_full), 1) < 0.5:
            return text

        # Find correct entities via keyword matching from invalid IDs
        suggestions = []
        _keywords = set()
        for eid in invalid:
            parts = eid.split(".")
            if len(parts) == 2:
                for p in parts[1].split("_"):
                    if len(p) >= 4:
                        _keywords.add(p)

        if _keywords:
            seen = set()
            for keyword in list(_keywords)[:3]:
                for s in all_states:
                    s_eid = s.get("entity_id", "")
                    fname = s.get("attributes", {}).get("friendly_name", "")
                    if keyword in s_eid.lower() or keyword in fname.lower():
                        if s_eid not in seen:
                            seen.add(s_eid)
                            state_val = s.get("state", "")
                            unit = s.get("attributes", {}).get("unit_of_measurement", "")
                            suggestions.append(
                                f"- `{s_eid}` ({fname}) = {state_val}{' ' + unit if unit else ''}"
                            )

        suggestions = suggestions[:15]

        lang = LANGUAGE
        inv_list = ", ".join(f"`{e}`" for e in sorted(invalid))
        if lang == "it":
            warning = f"\n\n⚠️ **Attenzione: alcuni entity ID potrebbero non esistere.**\n"
            warning += f"Non trovati su HA: {inv_list}\n"
            if suggestions:
                warning += "\n**Entità reali trovate nel tuo sistema:**\n" + "\n".join(suggestions[:10])
                warning += "\n\n_Usa questi entity ID al posto di quelli suggeriti sopra._"
            else:
                warning += "\nChiedi di nuovo specificando di cercare prima le entità reali."
        elif lang == "es":
            warning = f"\n\n⚠️ **Atención: algunos entity ID podrían no existir.**\n"
            warning += f"No encontrados: {inv_list}\n"
            if suggestions:
                warning += "\n**Entidades reales:**\n" + "\n".join(suggestions[:10])
        elif lang == "fr":
            warning = f"\n\n⚠️ **Attention : certains entity ID pourraient ne pas exister.**\n"
            warning += f"Non trouvés : {inv_list}\n"
            if suggestions:
                warning += "\n**Entités réelles :**\n" + "\n".join(suggestions[:10])
        else:
            warning = f"\n\n⚠️ **Warning: some entity IDs may not exist.**\n"
            warning += f"Not found: {inv_list}\n"
            if suggestions:
                warning += "\n**Real entities found:**\n" + "\n".join(suggestions[:10])

        logger.warning(f"Entity validation: {len(invalid)} invalid IDs in response: {invalid}")
        return text + warning

    except Exception as e:
        logger.warning(f"Entity validation error: {e}")
        return text


def _clean_unnecessary_comments(text: str) -> str:
    """Remove unnecessary comment-only code blocks from AI responses.
    
    Removes patterns like:
    - # (nessun YAML necessario...)
    - # (no YAML needed...)
    - # (ningún YAML necesario...)
    - # (aucun YAML nécessaire...)
    
    These are often added by models for "simple" text responses and should not appear.
    """
    import re
    
    # Strategy: Remove entire code blocks that contain ONLY these filler comments
    # Pattern: ```<optional lang>\n# (comment)\n```
    filler_patterns = [
        r'nessun YAML',    # Italian
        r'no YAML',         # English
        r'ningún YAML',     # Spanish
        r'aucun YAML',      # French
    ]
    
    # Build a regex that matches a code block with only a filler comment
    # ```[lang]\n# (...filler...)\n```
    for filler in filler_patterns:
        # Match: ```[optional lang]\n# (...filler text...)\n```
        block_pattern = rf'```[a-z]*\n\s*#\s*\([^)]*{re.escape(filler)}[^)]*\)\s*\n```\n?'
        text = re.sub(block_pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Also try to remove standalone lines with just these comments
    for filler in filler_patterns:
        line_pattern = rf'^\s*#\s*\([^)]*{re.escape(filler)}[^)]*\)\s*$'
        text = re.sub(line_pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    return text


def _collect_from_stream(user_message: str, session_id: str) -> str:
    """Blocking wrapper: collects all text from stream_chat_with_ai.
    Used by Telegram/WhatsApp for manager.py providers (groq, mistral, claude_web, etc.)."""
    global _last_sync_usage
    parts: list[str] = []
    for event in stream_chat_with_ai(user_message, session_id):
        event_type = event.get("type")
        if event_type == "token":
            # stream_chat_with_ai normalizes "text" → "token" with field "content"
            parts.append(event.get("content", ""))
        elif event_type == "text":
            # fallback: some paths might still yield "text" directly
            parts.append(event.get("text", ""))
        elif event_type == "done":
            # Capture usage for non-streaming cost display
            if event.get("usage"):
                _last_sync_usage = event["usage"]
        elif event_type == "error":
            return "❌ " + event.get("message", "Errore sconosciuto")
    result = "".join(parts).strip()
    result = _clean_unnecessary_comments(result)
    result = _validate_entity_ids_in_response(result)
    return result


def _log_response_preview(response_text: str, session_id: str) -> None:
    """Log a preview of the AI response, stripping code blocks."""
    import re as _re
    preview = _re.sub(r'```[\s\S]*?```', '[code]', response_text)
    preview = _re.sub(r'`[^`]+`', '[code]', preview)
    preview = _re.sub(r'\s+', ' ', preview).strip()
    if len(preview) > 300:
        preview = preview[:300] + '...'
    logger.chat(f"📤 ({session_id}) ({len(response_text)} chars): {preview}")


def _normalize_automation_change_args(raw_args: dict) -> dict:
    """Normalize preview/update_automation arguments to a comparable payload."""
    if not isinstance(raw_args, dict):
        raw_args = {}

    changes = raw_args.get("changes", {})
    # Some models (e.g. Llama via NVIDIA NIM) pass changes as a JSON/YAML string
    if isinstance(changes, str) and changes.strip():
        try:
            changes = json.loads(changes)
        except Exception:
            try:
                import yaml as _yaml_norm
                changes = _yaml_norm.safe_load(changes)
            except Exception:
                changes = {}
    if not isinstance(changes, dict):
        changes = {}

    # Keep compatibility with top-level fields accepted by update_automation
    if not changes:
        allowed_top_level = (
            "alias", "description", "trigger", "triggers",
            "condition", "conditions", "action", "actions", "mode",
        )
        for key in allowed_top_level:
            if key in raw_args:
                changes[key] = raw_args.get(key)

    # Canonicalize plural/singular aliases so trigger==triggers, action==actions, etc.
    _aliases = {"trigger": "triggers", "condition": "conditions", "action": "actions"}
    for singular, plural in _aliases.items():
        if singular in changes and plural not in changes:
            changes[plural] = changes.pop(singular)

    return {
        "automation_id": str(raw_args.get("automation_id", "")).strip(),
        "changes": changes,
        "add_condition": raw_args.get("add_condition", None),
    }


def _automation_change_signature(raw_args: dict) -> str:
    """Stable signature for preview/update argument matching."""
    norm = _normalize_automation_change_args(raw_args)
    return json.dumps(norm, ensure_ascii=False, sort_keys=True, default=str)


def _is_mcp_data_request(text: str) -> bool:
    """Heuristic: detect requests that likely require MCP-backed external data/tools."""
    try:
        t = (text or "").lower()
        if not t:
            return False
        markers = (
            "mcp",
            "sqlite",
            "sqlite3",
            "sqlite_master",
            ".db",
            "database",
            "filesystem",
            "repo",
            "github",
            "slack",
            "postgres",
            "mysql",
            "sql query",
            "query sql",
            "interroga il database",
        )
        if any(m in t for m in markers):
            return True
        # Weak fallback for plain "sql"
        return " sql " in f" {t} "
    except Exception:
        return False


def chat_with_ai(user_message: str, session_id: str = "default") -> str:
    """Send a message to the configured AI provider with HA tools."""
    # Debug: log which system prompt source is active
    _sp_override = AGENT_SYSTEM_PROMPT_OVERRIDE
    _sp_custom   = CUSTOM_SYSTEM_PROMPT
    if _sp_override:
        logger.debug(f"System prompt: AGENT_OVERRIDE ({len(_sp_override)} chars) — {_sp_override[:80]!r}")
    elif _sp_custom:
        logger.debug(f"System prompt: CUSTOM ({len(_sp_custom)} chars)")
    else:
        logger.debug("System prompt: DEFAULT HA prompt")

    # Legacy providers use ai_client directly; manager.py providers have ai_client=None (normal).
    _LEGACY_PROVIDERS = {"anthropic", "openai", "google", "nvidia", "github"}

    if not ai_client and AI_PROVIDER in _LEGACY_PROVIDERS:
        provider_name = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("name", AI_PROVIDER)
        return tr("err_api_key_not_configured", provider_name=provider_name)

    # Provider managed by providers/manager.py (groq, mistral, claude_web, chatgpt_web, etc.)
    if AI_PROVIDER not in _LEGACY_PROVIDERS:
        result = _collect_from_stream(user_message, session_id)
        _log_response_preview(result, session_id)
        return result

    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({"role": "user", "content": user_message})
    messages = sanitize_messages_for_provider(conversations[session_id][-20:])

    try:
        if AI_PROVIDER == "anthropic":
            final_text, messages = chat_anthropic(messages)
        elif AI_PROVIDER == "openai":
            final_text, messages = chat_openai(messages)
        elif AI_PROVIDER == "google":
            final_text, messages = chat_google(messages)
        elif AI_PROVIDER == "nvidia":
            final_text, messages = chat_openai(messages)  # Same format, different base_url
        elif AI_PROVIDER == "github":
            final_text, messages = chat_openai(messages)  # Same format, different base_url
        else:
            return tr("err_provider_not_supported", provider=AI_PROVIDER)

        conversations[session_id] = messages
        conversations[session_id].append({"role": "assistant", "content": final_text})
        save_conversations()
        # Clean unnecessary comments from response before returning
        final_text = _clean_unnecessary_comments(final_text)
        final_text = _validate_entity_ids_in_response(final_text)
        _log_response_preview(final_text, session_id)
        return final_text

    except Exception as e:
        logger.error(f"AI error ({AI_PROVIDER}): {e}")
        return tr("err_provider_generic", provider_name=PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get('name', AI_PROVIDER), error=str(e))


# ---- Streaming chat ----



def _build_side_by_side_diff_html(old_yaml: str, new_yaml: str) -> str:
    """Build an HTML side-by-side diff table (GitHub-style split view).
    Returns empty string if there are no actual changes."""
    import difflib
    import html as html_mod

    old_lines = old_yaml.strip().splitlines()
    new_lines = new_yaml.strip().splitlines()

    sm = difflib.SequenceMatcher(None, old_lines, new_lines)

    # Build row list: (type, left_text, right_text)
    rows = []
    context_lines = 3  # Lines of context around changes

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            chunk = list(zip(old_lines[i1:i2], new_lines[j1:j2]))
            if len(chunk) > context_lines * 2 + 1:
                for left, right in chunk[:context_lines]:
                    rows.append(("equal", left, right))
                rows.append(("collapse", f"... {len(chunk) - context_lines * 2} righe uguali ...", ""))
                for left, right in chunk[-context_lines:]:
                    rows.append(("equal", left, right))
            else:
                for left, right in chunk:
                    rows.append(("equal", left, right))
        elif op == "replace":
            old_chunk = old_lines[i1:i2]
            new_chunk = new_lines[j1:j2]
            max_len = max(len(old_chunk), len(new_chunk))
            old_chunk += [""] * (max_len - len(old_chunk))
            new_chunk += [""] * (max_len - len(new_chunk))
            for o, n in zip(old_chunk, new_chunk):
                rows.append(("replace", o, n))
        elif op == "delete":
            for i in range(i1, i2):
                rows.append(("delete", old_lines[i], ""))
        elif op == "insert":
            for j in range(j1, j2):
                rows.append(("insert", "", new_lines[j]))

    # If no actual changes found, return empty
    if not any(t in ("replace", "delete", "insert") for t, _, _ in rows):
        return ""

    # Build HTML
    h = ['<div class="diff-side"><table class="diff-table">']
    h.append('<thead><tr><th class="diff-th-old">\u274c PRIMA</th>')
    h.append('<th class="diff-th-new">\u2705 DOPO</th></tr></thead><tbody>')

    cls_map = {
        "equal": ("diff-eq", "diff-eq"),
        "replace": ("diff-del", "diff-add"),
        "delete": ("diff-del", "diff-empty"),
        "insert": ("diff-empty", "diff-add"),
    }

    for row_type, left, right in rows:
        le = html_mod.escape(left)
        re = html_mod.escape(right)
        if row_type == "collapse":
            h.append(f'<tr><td class="diff-collapse" colspan="2">{le}</td></tr>')
        else:
            lc, rc = cls_map.get(row_type, ("diff-eq", "diff-eq"))
            h.append(f'<tr><td class="{lc}">{le}</td><td class="{rc}">{re}</td></tr>')

    h.append("</tbody></table></div>")
    return "".join(h)



def _format_write_tool_response(tool_name: str, result_data: dict) -> str:
    """Format a human-readable response from a successful write tool result.
    This avoids needing another API round just to format the response.
    For UPDATE operations, shows a side-by-side diff (red/green)."""
    parts = []
    status = str(result_data.get("status", "")).lower().strip()
    is_error = (
        status in {"error", "failed", "invalid"}
        or ("error" in result_data and result_data.get("error"))
    )

    if is_error:
        _nested = result_data.get("result")
        _nested_err = _nested.get("error") if isinstance(_nested, dict) else None
        err_msg = (
            result_data.get("message")
            or result_data.get("error")
            or _nested_err
            or "Operazione non riuscita."
        )
        parts.append(f"❌ {err_msg}")
        return "\n".join(parts)

    msg = result_data.get("message", "")
    if msg:
        parts.append(f"\u2705 {msg}")
    else:
        parts.append(tr("write_op_success"))

    # Show diff for update tools (only for updates, not creates)
    old_yaml = result_data.get("old_yaml", "")
    new_yaml = result_data.get("new_yaml", "") or result_data.get("yaml", "")

    update_tools = ("update_automation", "update_script", "update_dashboard", "write_config_file",
                    "preview_automation_change")

    if old_yaml and new_yaml and tool_name in update_tools:
        diff_html = _build_side_by_side_diff_html(old_yaml, new_yaml)
        if diff_html:
            # Wrap in marker so chat_ui.formatMarkdown passes it through as raw HTML
            parts.append(f"\n<!--DIFF-->{diff_html}<!--/DIFF-->")
            # Diff already shows all changes — no need to repeat the full YAML
        else:
            parts.append(tr("write_no_changes"))
            # No diff (no changes): show the YAML so the user knows what's there
            parts.append(f"```yaml\n{new_yaml[:2000]}\n```")

    elif new_yaml and tool_name not in update_tools:
        # For CREATE operations, show the new YAML
        parts.append(tr("write_yaml_created"))
        parts.append(f"```yaml\n{new_yaml[:2000]}\n```")

    tip = result_data.get("tip", "")
    if tip:
        parts.append(f"\n\u2139\ufe0f {tip}")

    snapshot = result_data.get("snapshot", "")
    snapshot_id = ""
    if isinstance(snapshot, dict):
        snapshot_id = (snapshot.get("snapshot_id") or "").strip()
    elif isinstance(snapshot, str):
        snapshot_id = snapshot.strip()

    if snapshot_id and snapshot_id != "N/A (REST API)":
        parts.append(tr("write_snapshot_created", snapshot_id=snapshot_id))

    # Add link to entity in HA UI
    _entity_link_id = result_data.get("automation_id") or result_data.get("script_id") or ""
    if _entity_link_id:
        if tool_name in ("create_automation", "update_automation"):
            _link_url = f"/config/automation/edit/{_entity_link_id}"
            _link_label = "Apri automazione"
        elif tool_name in ("create_script", "update_script"):
            _link_url = f"/config/script/edit/{_entity_link_id}"
            _link_label = "Apri script"
        else:
            _link_url = None
        if _link_url:
            parts.append(
                f'\n<!--DIFF--><a class="ha-entity-link" '
                f"onclick=\"window.top.location.href='{_link_url}'\" "
                f'href="javascript:void(0)">\U0001f517 {_link_label} \u2197</a><!--/DIFF-->'
            )

    return "\n".join(parts)



def _strip_context_blocks(text: str) -> str:
    """Strip [CONTEXT: ...] blocks from text, handling nested brackets like [TOOL RESULT]."""
    import re as _re
    result = text
    while '[CONTEXT:' in result:
        idx = result.index('[CONTEXT:')
        depth = 0
        end = len(result) - 1
        for i in range(idx, len(result)):
            if result[i] == '[':
                depth += 1
            elif result[i] == ']':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        after = end + 1
        while after < len(result) and result[after] in (' ', '\n', '\r'):
            after += 1
        result = result[:idx] + result[after:]
    return result.strip()


def stream_chat_with_ai(user_message: str, session_id: str = "default", image_data: str = None, read_only: bool = False, voice_mode: bool = False):
    """Stream chat events for all providers with optional image support. Yields SSE event dicts.
    Uses LOCAL intent detection + smart context to minimize tokens sent to AI API."""
    global current_session_id
    
    # Strip context blocks from user_message for saving in conversation history
    # This prevents [CONTEXT:...] and [CURRENT_DASHBOARD_HTML]... from cluttering the history
    saved_user_message = user_message
    import re
    saved_user_message = re.sub(r'\[CONTEXT:.*?\]\[CURRENT_DASHBOARD_HTML\].*?\[/CURRENT_DASHBOARD_HTML\]\n*', '', saved_user_message, flags=re.DOTALL)
    # Also strip standalone [CONTEXT: ...] blocks (handling nested brackets like [TOOL RESULT])
    saved_user_message = _strip_context_blocks(saved_user_message)
    saved_user_message = saved_user_message.strip()

    # ── Early check: is the SDK for the chosen provider actually installed? ────
    _sdk_ok, _sdk_msg = _check_provider_sdk(AI_PROVIDER)
    if not _sdk_ok:
        yield {"type": "error", "message": f"⚠️ {_sdk_msg}"}
        return

    if not ai_client:
        # Per i provider gestiti da providers/manager.py, ai_client è sempre None (è normale).
        # Il controllo effettivo sulla chiave lo fa il manager stesso.
        # Blocca solo se si tratta di un provider legacy che richiede davvero ai_client.
        _LEGACY_PROVIDERS = {"anthropic", "openai", "google", "nvidia", "github"}
        if AI_PROVIDER in _LEGACY_PROVIDERS:
            yield {"type": "error", "message": tr("err_api_key_not_configured_short")}
            return

    # Store read-only state for this session (accessible by execute_tool)
    read_only_sessions[session_id] = read_only
    current_session_id = session_id

    if session_id not in conversations:
        conversations[session_id] = []

    # Get previous intent for confirmation continuity
    prev_intent = session_last_intent.get(session_id)

    # Step 1: LOCAL intent detection (preliminary — for bubble contexts and chat)
    # Simplified LLM-first approach: most intents are "auto" (all tools, LLM decides)
    intent_info = intent.detect_intent(user_message, "", previous_intent=prev_intent)
    intent_name = intent_info["intent"]

    # Step 2: Build smart context (skip for chat — not needed)
    # When the message contains [CURRENT_DASHBOARD_HTML] the HTML is extracted and will be injected
    # as a SEPARATE earlier turn in the conversation (user: HTML, assistant: "ok, letto"), so the
    # actual user message sent to the model is only the clean request text + normal smart context.
    _dashboard_in_msg = "[CURRENT_DASHBOARD_HTML]" in user_message

    # Extract dashboard HTML block if present (will be injected as a separate history turn below)
    _dashboard_html_block = ""
    _dashboard_html_inner = ""
    _dashboard_name_hint = ""
    if _dashboard_in_msg:
        import re as _re2
        _m = _re2.search(r'\[CURRENT_DASHBOARD_HTML\]([\s\S]*?)\[/CURRENT_DASHBOARD_HTML\]', user_message)
        if _m:
            _dashboard_html_block = _m.group(0)  # includes tags
            _dashboard_html_inner = _m.group(1).strip()
        # Also grab dashboard name from the CONTEXT prefix if present
        _nm = _re2.search(r'\[CONTEXT:[^\]]*?"([^"]+)"', user_message)
        if _nm:
            _dashboard_name_hint = _nm.group(1)
        logger.info(f"Dashboard HTML split: extracted {len(_dashboard_html_block)} chars, name='{_dashboard_name_hint}'")

    if intent_name != "chat":
        smart_context = intent.build_smart_context(
            user_message,
            intent=intent_name,
        )

        # Step 2.5: Inject memory context if enabled
        memory_context = ""
        if ENABLE_MEMORY and MEMORY_AVAILABLE:
            memory_context = memory.get_memory_context()
            if memory_context:
                logger.info(f"Memory context (MEMORY.md) injected for session {session_id}")
                smart_context = memory_context + "\n\n" + smart_context

        # Step 3: Re-detect intent WITH full smart context (for HTML dashboard refs in context)
        intent_info = intent.detect_intent(user_message, smart_context, previous_intent=prev_intent)
        intent_name = intent_info["intent"]
    else:
        smart_context = ""
        # Inject memory even for chat intent (no tools, but memory is still relevant)
        if ENABLE_MEMORY and MEMORY_AVAILABLE:
            memory_context = memory.get_memory_context()
            if memory_context:
                logger.info(f"Memory context (MEMORY.md) injected for chat session {session_id}")
                smart_context = memory_context

    # Store this intent for next message's confirmation continuity
    session_last_intent[session_id] = intent_name
    _intent_tools = intent_info.get("tools")
    # tools=None means "all tools" (LLM-first), tools=[] means "no tools" (chat)
    # Compute ACTUAL tool count (respects provider tier: compact/extended/full)
    if _intent_tools is not None:
        tool_count = len(_intent_tools)
    else:
        _tier = getattr(tools, "_get_tool_tier", lambda: "full")()
        _tier_counts = {"compact": len(tools.HA_TOOLS_COMPACT), "extended": len(tools.HA_TOOLS_EXTENDED)}
        tool_count = _tier_counts.get(_tier, len(tools.HA_TOOLS_DESCRIPTION))
    logger.info(f"Intent detected: {intent_name} (specific_target={intent_info['specific_target']}, tools={tool_count}, tier={_tier if _intent_tools is None else 'filtered'})")
    
    # Show intent to user (translated)
    INTENT_KEYS = {
        "auto": "intent_default",
        "chat": "intent_chat",
        "card_editor": "intent_default",
        "create_html_dashboard": "intent_create_dashboard",
        "manage_statistics": "intent_default",
        "modify_automation": "intent_modify_automation",
        "modify_script": "intent_modify_script",
        "create_dashboard": "intent_create_dashboard",
        "modify_dashboard": "intent_modify_dashboard",
        "config_edit": "intent_config_edit",
        "system_debug": "intent_default",
    }
    intent_key = INTENT_KEYS.get(intent_name, "intent_default")
    intent_label = tr(intent_key)
    _tools_label = f" ({tool_count} tools)" if tool_count > 0 else ""
    yield {"type": "status", "message": f"{intent_label}...{_tools_label}"}

    # Inject read-only instruction into intent prompt if read-only mode is active
    if read_only and intent_info.get("prompt"):
        read_only_note = tr("read_only_note")
        read_only_instruction = (
            "\n\nIMPORTANT - READ-ONLY MODE ACTIVE:\n"
            "The user has enabled read-only mode. You MUST NOT execute any write operations.\n"
            "Instead of calling write tools (create_automation, update_automation, delete_automation, "
            "create_script, update_script, delete_script, create_dashboard, update_dashboard, "
            "delete_dashboard, call_service, write_config_file, manage_areas, send_notification, "
            "manage_entity, manage_helpers), show the user the COMPLETE YAML/code they would need "
            "to manually insert or execute.\n"
            "Format the output as a code block with language 'yaml' so they can copy it.\n"
            f"At the end, add this note: {read_only_note}\n"
            "You CAN still use read-only tools (get_entities, search_entities, get_entity_state, "
            "get_automations, get_scripts, get_dashboards, etc.) to gather information."
        )
        intent_info["prompt"] = intent_info["prompt"] + read_only_instruction

    # Inject voice-mode instruction: force short, spoken-friendly responses
    if voice_mode and intent_info.get("prompt"):
        voice_instruction = (
            "\n\nIMPORTANT - VOICE MODE ACTIVE:\n"
            "The user is interacting via voice. Your response will be read aloud by a TTS engine.\n"
            "You MUST follow these rules strictly:\n"
            "- Be EXTREMELY concise: 1-2 sentences max.\n"
            "- Give only the essential information requested.\n"
            "- NEVER include entity_id, technical identifiers, or HA internal names (e.g. switch.xxx, light.xxx, sensor.xxx).\n"
            "- NEVER put technical info in parentheses like '(switch.luce_cucina: off)' or '(sensor.temp: 22)'.\n"
            "- NEVER list all entities/devices/switches — just summarize (e.g. 'Hai 5 luci accese' instead of listing them).\n"
            "- Do NOT use markdown, bullet points, numbered lists, code blocks, or special formatting.\n"
            "- ABSOLUTELY NO EMOJI — never use 😊🎉👍 or any emoji/emoticon. The TTS will try to read them.\n"
            "- Do NOT use slashes '/' in the response.\n"
            "- Use natural spoken Italian (or the user's language), as if talking to a person.\n"
            "- For temperatures: 'In soggiorno ci sono 22 gradi' (no entity IDs).\n"
            "- For states: 'La luce della cameretta è accesa' (no technical names).\n"
            "- For actions: confirm briefly: 'Fatto, ho spento la luce della cameretta'.\n"
            "- For queries about multiple items: give a summary count and mention only the most relevant ones by their friendly name.\n"
            "- Never say 'ecco i risultati' or similar preambles — go straight to the answer.\n"
        )
        intent_info["prompt"] = intent_info["prompt"] + voice_instruction

    # Step 3: Save original message and build enriched version for API
    if image_data:
        # Parse image data
        media_type, base64_data = parse_image_data(image_data)
        if not media_type or not base64_data:
            yield {"type": "error", "message": tr("err_invalid_image_format")}
            return

        # Save original message with image (without context blocks)
        if AI_PROVIDER == "anthropic":
            saved_content = format_message_with_image_anthropic(saved_user_message, media_type, base64_data)
        elif AI_PROVIDER in ("openai", "github"):
            saved_content = format_message_with_image_openai(saved_user_message, image_data)
        elif AI_PROVIDER == "google":
            saved_content = format_message_with_image_google(saved_user_message, media_type, base64_data)
        else:
            saved_content = saved_user_message

        conversations[session_id].append({"role": "user", "content": saved_content})

        # Build enriched version for API (with context)
        if smart_context:
            if intent_info["specific_target"]:
                api_content = f"{user_message}\n\n---\nDATA:\n{smart_context}"
            else:
                api_content = f"{user_message}\n\n---\nCONTEXT:\n{smart_context}\n---\nDo NOT re-request data already provided above."
        else:
            api_content = user_message

        if AI_PROVIDER == "anthropic":
            api_content = format_message_with_image_anthropic(api_content, media_type, base64_data)
        elif AI_PROVIDER in ("openai", "github"):
            api_content = format_message_with_image_openai(api_content, image_data)
        elif AI_PROVIDER == "google":
            api_content = format_message_with_image_google(api_content, media_type, base64_data)
        else:
            api_content = api_content

        logger.info(f"Message with image: {api_content[:50]}... (media_type: {media_type})")
        yield {"type": "status", "message": tr("status_image_processing")}
    else:
        # No image - save original message (without context blocks)
        conversations[session_id].append({"role": "user", "content": saved_user_message})

        # When the bubble sends [CURRENT_DASHBOARD_HTML], strip it from the actual user message
        # so api_content only contains the clean request text. The HTML will be injected as a
        # separate earlier conversation turn so the model sees it as prior context, not as part
        # of the current user turn. This keeps each individual message small.
        clean_user_message = user_message
        if _dashboard_in_msg and _dashboard_html_block:
            import re as _re3
            # Remove the [CONTEXT:...] prefix (everything up to and including the HTML closing tag)
            clean_user_message = _re3.sub(
                r'\[CONTEXT:[^\]]*\]\s*\[CURRENT_DASHBOARD_HTML\][\s\S]*?\[/CURRENT_DASHBOARD_HTML\]\s*',
                '',
                clean_user_message,
            ).strip()

        # Build enriched version for API (with context)
        if smart_context:
            if intent_info["specific_target"]:
                api_content = f"{clean_user_message}\n\n---\nDATA:\n{smart_context}"
            elif intent_name in ("create_html_dashboard", "modify_dashboard"):
                # For HTML dashboards: use all entity_ids directly — no tool-call instruction
                # (web providers like claude_web/chatgpt_web have no tools and "ONE tool call"
                #  confuses them into producing YAML instead of HTML)
                _prov = (AI_PROVIDER or "").lower()
                _provider_hint = ""
                if _prov in {"nvidia", "github_copilot"}:
                    _provider_hint = (
                        "\nProvider hint: keep output compact and robust. "
                        "Always include at least 2 visible charts in main layout "
                        "(line/area + bar/doughnut), and avoid modal-only charts."
                    )
                api_content = (
                    f"{clean_user_message}\n\n---\nCONTEXT:\n{smart_context}\n---\n"
                    "Use the entity_ids listed above directly in your HTML. "
                    "Output ONLY the complete <!DOCTYPE html>…</html> page, nothing else."
                    f"{_provider_hint}"
                )
            else:
                api_content = f"{clean_user_message}\n\n---\nCONTEXT:\n{smart_context}\n---\nDo NOT re-request data already provided above."
            # Log estimated token count
            est_tokens = len(api_content) // 4  # ~4 chars per token
            logger.info(f"Smart context: {len(smart_context)} chars, est. ~{est_tokens} tokens for user message")
            yield {"type": "status", "message": tr("status_context_preloaded")}
        else:
            # No smart context — but if this is a dashboard HTML edit from a no-tool provider,
            # still add the imperative instruction to output HTML (not conversational text).
            if _dashboard_html_block and intent_name in ("create_html_dashboard", "modify_dashboard"):
                api_content = (
                    f"{clean_user_message}\n\n"
                    "Output ONLY the complete modified <!DOCTYPE html>…</html> page. "
                    "Do NOT ask questions or add explanations — just return the full HTML."
                )
            else:
                api_content = clean_user_message

    # Create a copy of messages for API with enriched last user message.
    # If [CURRENT_DASHBOARD_HTML] was present, inject the HTML as a synthetic earlier turn:
    #   user:      [CURRENT_DASHBOARD_HTML]...(HTML)...[/CURRENT_DASHBOARD_HTML]
    #   assistant: "Ho letto la dashboard corrente."
    # This way the model sees the HTML as prior context while the actual request stays lean.
    if _dashboard_html_block and not image_data:
        _name_label = f' "{_dashboard_name_hint}"' if _dashboard_name_hint else ""
        _html_turn_user = (
            f"[CURRENT_DASHBOARD_HTML]{_dashboard_html_inner}\n[/CURRENT_DASHBOARD_HTML]\n"
            f"(This is the current HTML of dashboard{_name_label}. "
            f"Keep all existing sections intact unless explicitly asked to remove them.)"
        )
        # Synthetic assistant turn: acknowledge HTML receipt with a brief, neutral phrase.
        # IMPORTANT: do NOT use "Dimmi cosa vuoi modificare" — that invites the AI to ask
        # follow-up questions instead of executing the next user request immediately.
        _html_turn_assistant = (
            f"Ho il codice HTML della dashboard{_name_label}. Procedo con la modifica richiesta."
        )
        messages = (
            conversations[session_id][:-1]
            + [
                {"role": "user",      "content": _html_turn_user},
                {"role": "assistant", "content": _html_turn_assistant},
                {"role": "user",      "content": api_content},
            ]
        )
        logger.info(
            f"Dashboard HTML split into separate turn: "
            f"HTML turn={len(_html_turn_user)} chars, request turn={len(api_content)} chars"
        )
    else:
        messages = conversations[session_id][:-1] + [{"role": "user", "content": api_content}]

    # Inject file upload and RAG context if available AND enabled
    if (FILE_UPLOAD_AVAILABLE and ENABLE_FILE_UPLOAD) or (RAG_AVAILABLE and ENABLE_RAG):
        last_user_content = api_content
        context_sections = []
        
        # Inject document context if file upload is available AND enabled
        if FILE_UPLOAD_AVAILABLE and ENABLE_FILE_UPLOAD:
            try:
                doc_context = file_upload.get_document_context()
                if doc_context:
                    context_sections.append(
                        "## UPLOADED USER DOCUMENTS\n"
                        "IMPORTANT: The full content of these files is included below. "
                        "DO NOT use tools like read_config_file to read these files, "
                        "the content is already available.\n\n"
                        f"{doc_context}"
                    )
                    # Auto-cleanup: delete documents after injecting into message
                    try:
                        for doc in file_upload.list_documents():
                            file_upload.delete_document(doc['id'])
                        logger.info("Documents auto-cleaned after injection into chat")
                    except Exception as cleanup_err:
                        logger.debug(f"Document cleanup failed: {cleanup_err}")
            except Exception as e:
                logger.debug(f"Could not get document context: {e}")
        
        # Inject RAG semantic search results if available AND enabled
        if RAG_AVAILABLE and ENABLE_RAG:
            try:
                rag_context = rag.get_rag_context(user_message)
                if rag_context:
                    context_sections.append(f"## RISULTATI RICERCA SEMANTICA:\n{rag_context}")
            except Exception as e:
                logger.debug(f"Could not get RAG context: {e}")
        
        # Add context sections to the last user message if any context was found
        if context_sections:
            enriched_content = last_user_content + "\n\n" + "\n\n".join(context_sections)
            messages[-1]["content"] = enriched_content
            logger.info(f"Injected document/RAG context ({len(''.join(context_sections))} chars)")

    try:
        last_usage = None  # Will capture usage from done event
        _streamed_text_parts: list = []  # accumulate streamed tokens for saving

        # Clean messages for all providers: remove orphaned tool_calls / tool
        # responses that would cause 400 errors on OpenAI-compatible APIs.
        messages = sanitize_messages_for_provider(messages)

        # Remember conversation length AFTER sanitize so new messages
        # appended during the tool loop are captured correctly, even
        # when sanitize truncated the array below the original length.
        conv_length_before = len(messages)

        # Inject tool schemas into intent_info so providers can pass them to the API.
        # This enables tool calling for all OpenAI-compatible providers (Mistral, Groq, etc.)
        # and for the Anthropic SDK provider.
        # tools=None → ALL tools (LLM-first mode), tools=[] → no tools (chat), tools=[...] → subset
        #
        # === OpenClaw-style pipeline (via ToolRegistry) ===
        # When the registry is available, the entire filtering/formatting chain
        # (tier → intent → file_access → category) runs in a single pass via
        # ToolRegistry.get_tools(context) + format_for_provider().  This replaces
        # the manual filtering below with a declarative policy chain.
        _tool_registry = tools.get_tool_registry()
        if intent_info is not None:
            _intent_tool_names = intent_info.get("tools")
            if _tool_registry is not None:
                # Registry path: single-pass policy pipeline
                _registry_ctx = {
                    "tier": tools._get_tool_tier(),
                    "intent_tools": _intent_tool_names,   # None=all, []=none, [names]=subset
                    "enable_file_access": ENABLE_FILE_ACCESS,
                }
                intent_info["tool_schemas"] = _tool_registry.format_for_provider(
                    "openai", _registry_ctx
                )
            else:
                # Legacy path (fallback)
                if _intent_tool_names is None:
                    intent_info["tool_schemas"] = tools.get_openai_tools()
                elif len(_intent_tool_names) == 0:
                    intent_info["tool_schemas"] = []
                else:
                    _allowed = set(_intent_tool_names)
                    intent_info["tool_schemas"] = [
                        t for t in tools.get_openai_tools()
                        if t.get("function", {}).get("name") in _allowed
                    ]

            # Ensure dynamic MCP tools are always visible to the model, even when
            # ToolRegistry is active (registry is initialized from legacy static tools
            # and does not include runtime-discovered MCP tools by default).
            try:
                if MCP_AVAILABLE:
                    _schemas = intent_info.get("tool_schemas") or []
                    _existing_names = {
                        t.get("function", {}).get("name", "")
                        for t in _schemas
                    }
                    _mcp_dynamic = []
                    _mgr = mcp.get_mcp_manager()
                    for _tool_name, _tool_info in (_mgr.get_all_tools() or {}).items():
                        if _tool_name in _existing_names:
                            continue
                        _mcp_dynamic.append({
                            "type": "function",
                            "function": {
                                "name": _tool_name,
                                "description": f"{_tool_info.get('description', '')} (MCP: {_tool_info.get('server', 'unknown')})",
                                "parameters": _tool_info.get("inputSchema", {"type": "object", "properties": {}}),
                            }
                        })
                    if _mcp_dynamic:
                        intent_info["tool_schemas"] = _schemas + _mcp_dynamic
                        logger.info(f"MCP tools injected into tool_schemas: +{len(_mcp_dynamic)}")
            except Exception as _mcp_inject_err:
                logger.warning(f"MCP tool schema injection failed: {_mcp_inject_err}")

            # MCP guidance boost (generic): keep full toolset, but add a strict
            # instruction when the user clearly asks for external data/actions
            # typically served by MCP servers (DB/filesystem/repo/etc.).
            if _is_mcp_data_request(user_message):
                _all_schemas = intent_info.get("tool_schemas") or []
                _mcp_tool_names = [
                    t.get("function", {}).get("name", "")
                    for t in _all_schemas
                    if t.get("function", {}).get("name", "").startswith("mcp_")
                ]
                if _mcp_tool_names:
                    _mcp_rule = (
                        "CRITICAL MCP RULE:\n"
                        "- This request likely needs external data/actions via MCP tools.\n"
                        "- Call the relevant MCP tool(s) first, then answer using real tool results.\n"
                        "- Do NOT refuse without attempting MCP tools.\n"
                        f"- Available MCP tools now: {', '.join(_mcp_tool_names[:12])}"
                    )
                    _cur_prompt = (intent_info.get("prompt") or "").strip()
                    intent_info["prompt"] = (_cur_prompt + "\n\n" + _mcp_rule).strip() if _cur_prompt else _mcp_rule
                    logger.info(f"MCP guidance boost active ({len(_mcp_tool_names)} MCP tool(s) available)")

        # MCP guard: if a request clearly targets MCP-backed data/actions,
        # allow one internal retry when the model answers without any tool call.
        _mcp_guard_maybe_needed = _is_mcp_data_request(user_message)
        _mcp_guard_retry_used = False
        _mcp_tool_count = 0
        try:
            _mcp_tool_count = len([
                t for t in (intent_info or {}).get("tool_schemas", [])
                if (t.get("function", {}).get("name", "").startswith("mcp_"))
            ])
        except Exception:
            _mcp_tool_count = 0
        _mcp_guard_enabled = _mcp_guard_maybe_needed and _mcp_tool_count > 0

        # Tool execution loop: providers surface tool_calls in the done event;
        # we execute them here and loop until the model produces a final answer.
        _MAX_TOOL_ROUNDS = 8
        _tool_round = 0
        _tool_cache: dict = {}
        _tool_call_history: set = set()  # tracks all (name, args_json) to detect loops
        _duplicate_count = 0             # how many consecutive duplicate rounds
        _deferred_done_event = None      # postpone done for HTML autosave flows
        _skip_tool_extraction = False    # after dedup, skip ToolSimulator next round
        _last_write_result = None        # last WRITE tool result (for fallback display)
        _preview_round_done = False      # True after preview_automation_change executes
        _html_draft_pending_name = ""    # create_html_dashboard draft name pending finalize
        _html_dashboard_saved_this_turn = False
        _write_tools_executed: list = []  # names of write tools actually called this turn
        _html_force_execute_retry_used = False

        def _pending_call_signature(_tc: dict) -> str:
            """Build a stable signature for loop detection (name + canonical args)."""
            _name = str(_tc.get("name", "") or "")
            _raw_args = _tc.get("arguments", "{}")
            try:
                _obj = json.loads(_raw_args or "{}")
            except Exception:
                _obj = _raw_args
            if isinstance(_obj, dict):
                _args_sig = json.dumps(_obj, sort_keys=True, ensure_ascii=False)
            else:
                _args_sig = str(_raw_args)
            return f"{_name}:{_args_sig}"

        # Build read-only tool set: from registry (categories) or static fallback
        if _tool_registry is not None:
            from tool_registry import ToolCategory
            _read_only_tools = {
                t.name for t in _tool_registry._tools.values() if t.read_only
            }
        else:
            _read_only_tools = {
                "get_automations", "get_scripts", "get_dashboards",
                "get_dashboard_config", "read_config_file",
                "list_config_files", "get_frontend_resources",
                "search_entities", "get_entity_state", "get_entities",
                "get_integration_entities",
            }

        # Helper: is this tool call read-only? (used for UI suppression + write detection)
        def _is_read_only_call(tc):
            name = tc.get("name", "")
            if name == "create_html_dashboard":
                # HTML dashboard creation writes files + Lovelace config.
                return False
            if name in _read_only_tools:
                return True
            # manage_statistics(action=validate) is read-only
            if name == "manage_statistics":
                try:
                    args = json.loads(tc.get("arguments", "{}") or "{}")
                except Exception:
                    args = {}
                return args.get("action") == "validate"
            return False

        while _tool_round < _MAX_TOOL_ROUNDS:
            _tool_round += 1

            # Use unified provider interface (replaces old provider_*.py functions)
            # Passa il modello attivo esplicitamente così il provider non usa default errati
            #
            # Model Fallback: if enabled, wrap the call through the fallback engine
            # which tries the primary model first, then agent/global fallbacks on error.
            _active_provider = AI_PROVIDER
            _active_model = get_active_model()

            if MODEL_FALLBACK_AVAILABLE and AGENT_CONFIG_AVAILABLE:
                try:
                    _agent_id = None
                    try:
                        _mgr = agent_config.get_agent_manager()
                        _active_ag = _mgr.get_active_agent()
                        if _active_ag:
                            _agent_id = _active_ag.id
                    except Exception:
                        pass

                    _fb_result = model_fallback.run_with_model_fallback_streaming(
                        provider=_active_provider,
                        model=_active_model,
                        # IMPORTANT: disable ProviderManager auto-fallback here.
                        # ModelFallback already resolves the chain (agent -> defaults),
                        # while ProviderManager auto-fallback uses global fallback_config
                        # and can override agent-specific selections.
                        run=lambda p, m: provider_stream_chat(
                            p,
                            messages,
                            intent_info=intent_info,
                            fallback_chain=[],
                            model=m,
                        ),
                        agent_id=_agent_id,
                        on_fallback=lambda fp, fm, tp, tm: logger.warning(
                            f"⚡ Fallback: {fp}/{fm} → {tp}/{tm}"
                        ),
                    )
                    if _fb_result.success:
                        provider_gen = _fb_result.result
                        # Update active provider/model if fallback switched them
                        if _fb_result.provider != _active_provider or _fb_result.model != _active_model:
                            logger.info(f"Fallback active: using {_fb_result.provider}/{_fb_result.model} "
                                        f"instead of {_active_provider}/{_active_model}")
                            _active_provider = _fb_result.provider
                            _active_model = _fb_result.model
                    else:
                        # All candidates failed — re-raise the original error
                        if _fb_result.error:
                            raise _fb_result.error
                        raise Exception("All model candidates exhausted")
                except model_fallback.FailoverReason if False else Exception as _fb_err:
                    # If fallback engine itself fails, fall through to direct call
                    if model_fallback.is_context_overflow(_fb_err):
                        raise  # context overflow: abort immediately
                    logger.warning(f"Fallback engine error, trying direct: {_fb_err}")
                    provider_gen = provider_stream_chat(
                        AI_PROVIDER, messages,
                        intent_info=intent_info,
                        model=get_active_model(),
                    )
            else:
                provider_gen = provider_stream_chat(
                    AI_PROVIDER, messages,
                    intent_info=intent_info,
                    model=get_active_model(),
                )

            _pending_tool_calls: list = []

            # For create_html_dashboard: buffer text instead of streaming it.
            # The model writes the full HTML as plain text — suppress it so the user
            # sees only the tool status + confirmation, not raw HTML in the chat.
            # If no tool call happens (clarifying question), flush the buffer as-is.
            _is_html_dash = (intent_info or {}).get("intent") == "create_html_dashboard"

            # For no-tool providers (claude_web, chatgpt_web, github_copilot, openai_codex):
            # buffer the full response so we can run the tool simulator on it after done.
            _NO_TOOL_PROVIDERS = {"claude_web", "chatgpt_web", "gemini_web", "perplexity_web", "github_copilot", "openai_codex"}
            # Some models on native-tool providers also use the XML simulator
            # (e.g. Kimi K2 on Groq — emits text instead of tool_call deltas).
            _NO_NATIVE_TOOL_MODELS = {
                "moonshotai/kimi-k2-instruct-0905",  # Groq: describes actions but skips tool_call deltas
            }
            _is_no_tool_provider = (
                AI_PROVIDER in _NO_TOOL_PROVIDERS
                or get_active_model().lower() in _NO_NATIVE_TOOL_MODELS
            )
            _text_buffer: list = []
            _mcp_guard_triggered_this_round = False
            _buffer_for_mcp_guard = (
                _mcp_guard_enabled
                and not _mcp_guard_retry_used
                and not _is_no_tool_provider
                and _tool_round == 1
            )
            _mcp_guard_stream_buffer: list = []

            # Stream events, intercepting 'done' to enrich with cost or detect tool calls
            for event in provider_gen:
                if event.get("type") == "done":
                    _pending_tool_calls = event.get("tool_calls") or []
                    _finish_reason_done = str(event.get("finish_reason", "") or "").lower()
                    if not _pending_tool_calls:
                        full_buf = "".join(_text_buffer)
                        # Native-tool providers can occasionally return malformed_function_call
                        # with no executable calls. Retry once with a strict execution hint.
                        if (
                            _is_html_dash
                            and not _is_no_tool_provider
                            and _finish_reason_done == "malformed_function_call"
                            and not _html_force_execute_retry_used
                        ):
                            _html_force_execute_retry_used = True
                            _cur_prompt = ((intent_info or {}).get("prompt") or "").strip()
                            _retry_rule = (
                                "HTML DASHBOARD EXECUTION RULE:\n"
                                "- Return exactly one valid tool call to create_html_dashboard.\n"
                                "- Do NOT output plain HTML in chat.\n"
                                "- Do NOT ask confirmation.\n"
                                "- Arguments must be strict JSON (escaped), with name/title/entities/html."
                            )
                            if intent_info is not None:
                                intent_info["prompt"] = (_cur_prompt + "\n\n" + _retry_rule).strip() if _cur_prompt else _retry_rule
                            logger.warning("HTML dashboard retry: malformed_function_call with no tool_calls, forcing strict tool call")
                            _text_buffer = []
                            _streamed_text_parts = []
                            break

                        # ── Tool Simulator: extract <tool_call> blocks from buffered text ──
                        if _is_no_tool_provider and full_buf and not _skip_tool_extraction:
                            from providers.tool_simulator import extract_tool_calls, clean_response_text
                            _sim_calls = extract_tool_calls(full_buf)
                            if not _sim_calls:
                                # Gemini/Web models often escape tool XML as markdown text:
                                # \<tool\_call\> ... create\_html\_dashboard ...
                                # Normalize common escapes and try extraction again.
                                _sim_norm = (
                                    full_buf
                                    .replace("\\<", "<")
                                    .replace("\\>", ">")
                                    .replace("\\_", "_")
                                    .replace("\\#", "#")
                                )
                                if _sim_norm != full_buf:
                                    _sim_calls = extract_tool_calls(_sim_norm)
                                    if _sim_calls:
                                        full_buf = _sim_norm
                            if _sim_calls:
                                # ── Filter against intent tool set ──
                                # No-tool providers may hallucinate tool names
                                # not in the current intent (e.g. get_repairs
                                # inside a manage_statistics intent).  Drop them.
                                _intent_tools = (intent_info or {}).get("tools")
                                if _intent_tools:
                                    _allowed = set(_intent_tools)
                                    _filtered = [tc for tc in _sim_calls if tc.get("name", "") in _allowed]
                                    _dropped = len(_sim_calls) - len(_filtered)
                                    if _dropped:
                                        logger.warning(
                                            f"ToolSimulator: dropped {_dropped} call(s) not in intent tool set "
                                            f"{_intent_tools}: {[tc.get('name') for tc in _sim_calls if tc.get('name', '') not in _allowed]}"
                                        )
                                    _sim_calls = _filtered
                            if _sim_calls:
                                # Deduplicate tool calls within the same response
                                # (model sometimes emits the same call twice in one turn)
                                _seen_sigs = set()
                                _deduped_calls = []
                                for tc in _sim_calls:
                                    _tc_sig = f"{tc.get('name', '')}:{tc.get('arguments', '{}')}"
                                    if _tc_sig not in _seen_sigs:
                                        _seen_sigs.add(_tc_sig)
                                        _deduped_calls.append(tc)
                                    else:
                                        logger.debug(f"ToolSimulator: skipping duplicate call in same response: {tc.get('name', '')}")
                                _sim_calls = _deduped_calls

                                # ── Limit to ONE call per tool name per round ──
                                # No-tool providers sometimes emit e.g. manage_statistics(validate)
                                # + manage_statistics(clear_orphaned) in one turn. The write action
                                # already validates internally, so running both wastes a round and
                                # confuses the dedup logic.  Keep only the LAST call per tool name
                                # (the model emits validate first, then the action — we want the action).
                                _seen_names: dict = {}
                                for i, tc in enumerate(_sim_calls):
                                    _seen_names[tc.get("name", "")] = i
                                if len(_seen_names) < len(_sim_calls):
                                    # Special case: create_html_dashboard often emits multiple
                                    # chunked calls in one response (draft=true parts + finalize).
                                    # Keep ALL of them in order; collapse only other duplicated tools.
                                    _last_non_dash_idx: dict = {}
                                    for i, tc in enumerate(_sim_calls):
                                        _n = tc.get("name", "")
                                        if _n != "create_html_dashboard":
                                            _last_non_dash_idx[_n] = i
                                    _kept = []
                                    for i, tc in enumerate(_sim_calls):
                                        _n = tc.get("name", "")
                                        if _n == "create_html_dashboard" or _last_non_dash_idx.get(_n) == i:
                                            _kept.append(tc)
                                    _removed_count = len(_sim_calls) - len(_kept)
                                    logger.info(
                                        f"ToolSimulator: collapsed {_removed_count} extra call(s) "
                                        f"to same tool name — keeping dashboard chunks + last non-dashboard per name"
                                    )
                                    _sim_calls = _kept

                                # Inject as pending tool calls — the normal loop below handles them
                                _pending_tool_calls = _sim_calls
                                # For read-only tool calls, suppress the introductory text:
                                # the model will respond properly once it sees the tool results.
                                # For write tool calls, show the confirmation text to the user.
                                _all_read_only = all(
                                    _is_read_only_call(tc)
                                    for tc in _sim_calls
                                )
                                # For HTML dashboard flow, avoid echoing model prose/partial HTML.
                                # We only show tool execution statuses and final save confirmation.
                                if not _all_read_only and not _is_html_dash:
                                    cleaned = clean_response_text(full_buf)
                                    if cleaned:
                                        yield {"type": "token", "content": cleaned}
                                _text_buffer = []
                                # Do NOT yield done yet — let the tool loop continue
                                break
                        # No tool_calls found → plain text response.
                        # For HTML dashboard intent, suppress raw HTML walls and
                        # show a neutral status while auto-save runs later.
                        if full_buf:
                            from providers.tool_simulator import clean_display_text
                            _display = clean_display_text(full_buf)
                            if _is_html_dash:
                                import re as _re_html_nt
                                _has_html_nt = bool(_re_html_nt.search(
                                    r'(?:<!DOCTYPE\s+html|<html[\s>])',
                                    full_buf, _re_html_nt.IGNORECASE
                                ))
                                if _has_html_nt:
                                    yield {"type": "status", "message": "💾 HTML ricevuto, provo a salvarlo..."}
                                elif _display:
                                    yield {"type": "token", "content": _display}
                                # Some models ask "Procedo?" instead of calling the tool.
                                # Retry once with a strict instruction to execute immediately.
                                if (
                                    not _pending_tool_calls
                                    and not _html_force_execute_retry_used
                                    and _display
                                    and any(k in _display.lower() for k in ("procedo", "proceed", "confermi", "confirm"))
                                ):
                                    _html_force_execute_retry_used = True
                                    _cur_prompt = ((intent_info or {}).get("prompt") or "").strip()
                                    _retry_rule = (
                                        "HTML DASHBOARD EXECUTION RULE:\n"
                                        "- Do NOT ask for confirmation.\n"
                                        "- Call create_html_dashboard immediately now.\n"
                                        "- Return only tool_call blocks (chunked draft if needed)."
                                    )
                                    if intent_info is not None:
                                        intent_info["prompt"] = (_cur_prompt + "\n\n" + _retry_rule).strip() if _cur_prompt else _retry_rule
                                    logger.info("HTML dashboard retry: model asked confirmation, forcing immediate tool execution")
                                    _text_buffer = []
                                    break
                            elif _display:
                                yield {"type": "token", "content": _display}
                            _text_buffer = []
                        elif _is_html_dash and _finish_reason_done == "malformed_function_call":
                            _msg_malformed = (
                                "⚠️ Il modello ha restituito una tool-call malformata e non eseguibile. "
                                "Nessuna dashboard è stata creata."
                            )
                            yield {"type": "token", "content": _msg_malformed}
                            _streamed_text_parts.append(_msg_malformed)

                        # No-tool provider with _skip_tool_extraction: flush text
                        # as plain response, stripping any <tool_call> XML the model
                        # may have emitted despite the [DUPLICATE] warning.
                        elif _is_no_tool_provider and full_buf and _skip_tool_extraction:
                            from providers.tool_simulator import clean_display_text as _cdt_skip
                            _display_skip = _cdt_skip(full_buf)
                            if _display_skip:
                                yield {"type": "token", "content": _display_skip}
                            else:
                                # Model generated ONLY <tool_call> XML → empty after stripping.
                                # Build a fallback summary from the last tool result.
                                logger.warning("skip_tool_extraction: cleaned text is empty — generating fallback from tool result")
                                if _last_write_result:
                                    try:
                                        _fb_obj = json.loads(_last_write_result)
                                        if isinstance(_fb_obj, dict):
                                            _fb_status = _fb_obj.get("status", "done")
                                            _fb_msg = _fb_obj.get("message", "")
                                            _fb_removed = _fb_obj.get("removed", [])
                                            _fb_fixed = _fb_obj.get("fixed", [])
                                            _fb_parts = []
                                            if _fb_msg:
                                                _fb_parts.append(f"✅ {_fb_msg}")
                                            elif _fb_status == "success":
                                                _fb_parts.append("✅ Operation completed successfully.")
                                            if _fb_removed:
                                                _ids = [r if isinstance(r, str) else r.get('statistic_id', str(r)) for r in _fb_removed]
                                                _fb_parts.append(
                                                    f'<details><summary>📊 {len(_ids)} entities removed (click to expand)</summary><div>'
                                                    + '<br>'.join(f'<code>{eid}</code>' for eid in _ids)
                                                    + '</div></details>'
                                                )
                                            if _fb_fixed:
                                                _fids = [f.get('statistic_id', str(f)) if isinstance(f, dict) else str(f) for f in _fb_fixed]
                                                _fb_parts.append(
                                                    f'<details><summary>🔧 {len(_fids)} entities fixed (click to expand)</summary><div>'
                                                    + '<br>'.join(f'<code>{eid}</code>' for eid in _fids)
                                                    + '</div></details>'
                                                )
                                            if _fb_parts:
                                                yield {"type": "token", "content": '\n'.join(_fb_parts)}
                                            else:
                                                yield {"type": "token", "content": f"✅ Operation completed. Result: {_last_write_result[:500]}"}
                                        else:
                                            yield {"type": "token", "content": f"✅ {_last_write_result[:500]}"}
                                    except Exception:
                                        yield {"type": "token", "content": f"✅ {_last_write_result[:500]}"}
                                else:
                                    yield {"type": "token", "content": "✅ Operation completed successfully."}
                            _text_buffer = []

                        # Flush buffer for html dashboard (no tool call → clarifying question)
                        elif _is_html_dash and _text_buffer:
                            full_html_buf = "".join(_text_buffer)
                            # For no-tool providers the HTML is streamed as plain text and will
                            # be auto-saved from _streamed_text_parts after this loop. Suppress
                            # the raw HTML from the chat and show a brief confirmation instead.
                            import re as _re_html
                            _has_html = bool(_re_html.search(
                                r'(?:<!DOCTYPE\s+html|<html[\s>])',
                                full_html_buf, _re_html.IGNORECASE
                            ))
                            if _is_no_tool_provider and _has_html:
                                # Do not claim success before the actual save result.
                                yield {"type": "status", "message": "💾 HTML ricevuto, provo a salvarlo..."}
                            else:
                                # No HTML found → clarifying question or tool-capable provider;
                                # flush the buffer normally so the user sees the response.
                                for buffered_chunk in _text_buffer:
                                    yield {"type": "token", "content": buffered_chunk}
                            _text_buffer = []

                        # MCP guard retry (generic, one-shot):
                        # if this looks like an MCP-oriented request and the model
                        # ended without tool calls, retry once with stronger instruction.
                        if _buffer_for_mcp_guard and not _pending_tool_calls:
                            _mcp_guard_retry_used = True
                            _mcp_guard_triggered_this_round = True
                            _mcp_guard_stream_buffer = []  # discard first plain-text attempt
                            _streamed_text_parts = []      # keep only post-retry output
                            _retry_rule = (
                                "MCP RETRY RULE:\n"
                                "- You must call relevant MCP tool(s) before answering.\n"
                                "- Do not refuse without attempting MCP tools.\n"
                                "- Base the final answer on tool results."
                            )
                            _cur_prompt = ((intent_info or {}).get("prompt") or "").strip()
                            if intent_info is not None:
                                intent_info["prompt"] = (_cur_prompt + "\n\n" + _retry_rule).strip() if _cur_prompt else _retry_rule
                            logger.info("MCP guard retry: model answered without tool_calls, retrying once")
                            break

                        # Normal completion — enrich with cost and forward to client
                        if _buffer_for_mcp_guard and _mcp_guard_stream_buffer:
                            _joined = "".join(_mcp_guard_stream_buffer)
                            _streamed_text_parts.append(_joined)
                            yield {"type": "token", "content": _joined}
                            _mcp_guard_stream_buffer = []

                        if event.get("usage"):
                            raw_usage = event["usage"]
                            logger.debug(f"💰 Usage received from provider: {raw_usage}")
                            # Normalize usage from any provider naming convention
                            norm = pricing.normalize_usage(raw_usage)
                            input_tokens = norm["input_tokens"]
                            output_tokens = norm["output_tokens"]
                            cache_read_tokens = norm["cache_read_tokens"]
                            cache_write_tokens = norm["cache_write_tokens"]
                            model_name = raw_usage.get("model") or get_active_model()
                            provider_name = raw_usage.get("provider") or AI_PROVIDER
                            # Full cost breakdown (input/output/cache_read/cache_write)
                            cost_bd = pricing.calculate_cost_breakdown(
                                model_name, provider_name,
                                input_tokens, output_tokens,
                                cache_read_tokens, cache_write_tokens,
                                COST_CURRENCY,
                            )
                            usage = {
                                **raw_usage,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "cache_read_tokens": cache_read_tokens,
                                "cache_write_tokens": cache_write_tokens,
                                "cost": cost_bd["total_cost"],
                                "cost_breakdown": {
                                    "input": cost_bd["input_cost"],
                                    "output": cost_bd["output_cost"],
                                    "cache_read": cost_bd["cache_read_cost"],
                                    "cache_write": cost_bd["cache_write_cost"],
                                },
                                "currency": COST_CURRENCY,
                            }
                            # Persist to disk for daily/model/provider aggregation
                            usage["model"] = model_name
                            usage["provider"] = provider_name
                            # Log cost at INFO level for visibility
                            _cost_val = cost_bd["total_cost"]
                            _sym = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}.get(COST_CURRENCY, COST_CURRENCY)
                            if _cost_val > 0:
                                logger.info(f"💰 {provider_name}/{model_name}: {input_tokens} in + {output_tokens} out → {_sym}{_cost_val:.6f}")
                            else:
                                logger.info(f"💰 {provider_name}/{model_name}: {input_tokens} in + {output_tokens} out → free")
                            try:
                                from usage_tracker import get_tracker
                                get_tracker().record(usage)
                            except Exception:
                                pass  # non-critical — don't break the stream
                            event = {**event, "usage": usage}
                            last_usage = usage
                        else:
                            logger.debug(f"⚠️ Done event without usage: finish_reason={event.get('finish_reason')}")
                        if not _pending_tool_calls:
                            # Validate entity IDs before emitting "done"
                            try:
                                _assembled_for_check = "".join(_streamed_text_parts).strip()
                                _validated_text = _validate_entity_ids_in_response(_assembled_for_check)
                                if _validated_text != _assembled_for_check:
                                    _warning_suffix = _validated_text[len(_assembled_for_check):]
                                    yield {"type": "token", "content": _warning_suffix}
                                    _streamed_text_parts.append(_warning_suffix)
                            except Exception as _val_err:
                                logger.warning(f"Entity validation in stream failed: {_val_err}")
                            if intent_name == "create_html_dashboard":
                                _deferred_done_event = event
                            else:
                                yield event
                    # If tool_calls present: do NOT yield done — execute tools and loop
                    break  # exit inner for-loop regardless
                elif event.get("type") == "error":
                    # Umanizza il messaggio di errore grezzo prima di inviarlo all'utente
                    raw_msg = event.get("message", "")
                    friendly = humanize_provider_error(Exception(raw_msg), AI_PROVIDER)
                    if friendly and friendly != raw_msg:
                        event = dict(event)
                        event["message"] = friendly
                    yield event
                    # Save error as assistant response so it persists when
                    # the conversation is reloaded (otherwise only the user
                    # message is kept and the answer disappears).
                    error_text = event.get("message", raw_msg) or raw_msg
                    if error_text and not _streamed_text_parts:
                        _streamed_text_parts.append("\u274c " + error_text)
                    break  # stop on error
                elif event.get("type") == "text":
                    # Normalize "text" → "token" so the UI receives the expected event format.
                    # All new-path providers (Groq, Mistral, Anthropic SDK, etc.) yield
                    # {"type": "text", "text": "..."} but the chat_ui.js expects
                    # {"type": "token", "content": "..."}.
                    chunk = event.get("text", "")
                    _streamed_text_parts.append(chunk)
                    if _is_html_dash or _is_no_tool_provider:
                        _text_buffer.append(chunk)  # buffer: process after done
                    elif _buffer_for_mcp_guard:
                        _mcp_guard_stream_buffer.append(chunk)  # hold until done decision
                    else:
                        yield {"type": "token", "content": chunk}
                elif event.get("type") == "token":
                    # Some providers yield token events directly — accumulate those too
                    content = event.get("content", "")
                    _streamed_text_parts.append(content)
                    if _is_html_dash or _is_no_tool_provider:
                        _text_buffer.append(content)  # buffer: process after done
                    elif _buffer_for_mcp_guard:
                        _mcp_guard_stream_buffer.append(content)  # hold until done decision
                    else:
                        yield event
                else:
                    yield event

            if _mcp_guard_triggered_this_round:
                continue  # run one internal retry with stronger MCP instruction

            # Fail-safe for chunked HTML dashboard creation:
            # if the model stopped after draft_* calls, finalize automatically.
            if (
                not _pending_tool_calls
                and intent_name == "create_html_dashboard"
                and _html_draft_pending_name
                and not _html_dashboard_saved_this_turn
            ):
                try:
                    yield {"type": "status", "message": "💾 Auto-finalizing HTML draft dashboard..."}
                    _auto_final = tools.execute_tool("create_html_dashboard", {"name": _html_draft_pending_name})
                    _auto_obj = json.loads(_auto_final) if isinstance(_auto_final, str) else _auto_final
                    if isinstance(_auto_obj, dict) and str(_auto_obj.get("status", "")).lower() == "success":
                        _html_dashboard_saved_this_turn = True
                        _html_draft_pending_name = ""
                        _saved_url = _auto_obj.get("dashboard_url") or _auto_obj.get("url") or ""
                        if _saved_url:
                            yield {"type": "status", "message": f"✅ Dashboard saved: {_saved_url}"}
                        else:
                            yield {"type": "status", "message": "✅ HTML dashboard saved successfully."}
                        logger.info("HTML draft auto-finalized successfully")
                    else:
                        logger.warning(f"HTML draft auto-finalize failed: {_auto_final}")
                        yield {"type": "status", "message": "⚠️ Draft dashboard was not auto-finalized."}
                except Exception as _df_err:
                    logger.warning(f"HTML draft auto-finalize error: {_df_err}")
                    yield {"type": "status", "message": f"⚠️ Draft auto-finalize error: {_df_err}"}

            if not _pending_tool_calls:
                break  # No tool calls → conversation complete

            # --- Execute tool calls and prepare next round ---
            text_so_far = "".join(_streamed_text_parts)
            _streamed_text_parts = []

            # For no-tool providers, clean <tool_call> XML from assistant history
            # so the model doesn't see raw XML in its conversation context.
            if _is_no_tool_provider and text_so_far:
                from providers.tool_simulator import clean_response_text as _crt
                text_so_far = _crt(text_so_far)

            # ── Dedup / loop breaker: detect repeated tool calls ──────────
            # If ALL pending tool calls have already been made with identical
            # arguments in a previous round, the model is stuck in a loop.
            # Inject a synthetic tool result telling it to stop and answer.
            _all_dupes = True
            for tc in _pending_tool_calls:
                _sig_dedup = _pending_call_signature(tc)
                if _sig_dedup not in _tool_call_history:
                    _all_dupes = False
                    break
            if _all_dupes and _pending_tool_calls:
                # Special-case breaker: HTML dashboard draft loop.
                # Some models keep calling create_html_dashboard with draft=true forever.
                try:
                    _draft_calls = []
                    for _tc in _pending_tool_calls:
                        if _tc.get("name") != "create_html_dashboard":
                            _draft_calls = []
                            break
                        _a = json.loads(_tc.get("arguments", "{}") or "{}")
                        if not isinstance(_a, dict) or not bool(_a.get("draft", False)):
                            _draft_calls = []
                            break
                        _draft_calls.append(_a)
                    if _draft_calls:
                        _draft_name = str((_draft_calls[0].get("name") or _html_draft_pending_name or "")).strip()
                        if _draft_name:
                            logger.warning(
                                f"HTML draft loop detected for '{_draft_name}' "
                                f"(round {_tool_round}) — forcing finalize now"
                            )
                            yield {"type": "status", "message": "💾 Draft loop detected: auto-finalizing HTML dashboard..."}
                            _auto_final = tools.execute_tool("create_html_dashboard", {"name": _draft_name})
                            _auto_obj = json.loads(_auto_final) if isinstance(_auto_final, str) else _auto_final
                            if isinstance(_auto_obj, dict) and str(_auto_obj.get("status", "")).lower() == "success":
                                _html_dashboard_saved_this_turn = True
                                _html_draft_pending_name = ""
                                _url = _auto_obj.get("dashboard_url") or _auto_obj.get("url") or ""
                                _msg = (
                                    f"HTML dashboard created successfully: {_url}"
                                    if _url else
                                    "HTML dashboard created successfully."
                                )
                                _streamed_text_parts.append(_msg)
                                yield {"type": "token", "content": _msg}
                                yield {"type": "done"}
                                break
                            logger.warning(f"Forced HTML draft finalize failed: {_auto_final}")
                except Exception as _draft_loop_err:
                    logger.warning(f"HTML draft loop breaker error: {_draft_loop_err}")

                _duplicate_count += 1
                logger.warning(
                    f"Tool loop detected (round {_tool_round}, dup #{_duplicate_count}): "
                    f"all {len(_pending_tool_calls)} call(s) are duplicates — forcing final answer"
                )

                # ── No-tool providers (github_copilot, etc.): the model ignores
                # ── [DUPLICATE] messages and keeps generating <tool_call> XML.
                # ── Strategy: give it ONE more round but disable ToolSimulator
                # ── extraction so any <tool_call> in its text is stripped and the
                # ── response is treated as plain text → loop ends naturally.
                if _is_no_tool_provider:
                    if _duplicate_count >= 2:
                        # Already tried once — force-break now
                        logger.warning("No-tool provider: 2nd duplicate → breaking loop")
                        # Emit whatever text the model accumulated (cleaned)
                        if text_so_far:
                            from providers.tool_simulator import clean_display_text as _cdt_brk
                            _cleaned_brk = _cdt_brk(text_so_far)
                            if _cleaned_brk:
                                yield {"type": "token", "content": _cleaned_brk}
                        yield {"type": "done"}
                        break
                    # First duplicate for no-tool provider: inject [DUPLICATE] but
                    # disable tool extraction for the next round so the loop ends.
                    _skip_tool_extraction = True

                # For native-tool providers: after 2 consecutive duplicate rounds
                # the model is truly stuck — force-break as well.
                # text_so_far was already streamed to the client — don't re-yield it.
                elif _duplicate_count >= 2:
                    logger.warning("Native provider: 2nd duplicate → breaking loop")
                    yield {"type": "done"}
                    break

                # Assign stable IDs before building dedup messages
                for _dd_idx, _dd_tc in enumerate(_pending_tool_calls):
                    if not _dd_tc.get("id"):
                        _dd_tc["id"] = f"call_{_dd_tc.get('name', 'tool')}_{_dd_idx}"

                # Append assistant message so the conversation stays well-formed
                messages.append({
                    "role": "assistant",
                    "content": text_so_far or None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc.get("name", ""),
                                "arguments": tc.get("arguments", "{}"),
                            },
                        }
                        for tc in _pending_tool_calls
                    ],
                })
                # Append synthetic tool results telling the model to stop
                for tc in _pending_tool_calls:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tc.get("name", ""),
                        "content": (
                            "[DUPLICATE] You already called this tool with the same arguments. "
                            "Use the results you already received. Do NOT call this tool again. "
                            "Produce your final answer NOW based on the data you already have."
                        ),
                    })
                # Let the loop continue so the model sees the synthetic result
                # and produces a final answer (no tool calls).
                yield {"type": "clear"}
                yield {"type": "status", "message": f"🤖 {tr('status_analyzing')}..."}
                continue

            # NOTE: tool call signatures are recorded in _tool_call_history
            # AFTER each individual tool execution (see below), not here.
            # Pre-recording would cause DuplicateCallHook to block the first call.

            # ── Preview confirmation guard ─────────────────────────────────
            # Block update_automation / update_script if preview_automation_change
            # was called in this round OR a previous round (same request).
            # This prevents the model from auto-applying changes without user
            # confirmation — which would look like "SI was typed automatically".
            _PREVIEW_GUARDED_WRITES = {
                "update_automation", "update_script", "write_config_file",
                "update_dashboard", "create_automation", "create_script",
            }
            _cur_has_preview = any(tc.get("name") == "preview_automation_change"
                                   for tc in _pending_tool_calls)
            _cur_has_write = any(tc.get("name") in _PREVIEW_GUARDED_WRITES
                                 for tc in _pending_tool_calls)
            if (_cur_has_preview and _cur_has_write) or (_preview_round_done and _cur_has_write):
                _pg_blocked = [tc for tc in _pending_tool_calls
                               if tc.get("name") in _PREVIEW_GUARDED_WRITES]
                _pending_tool_calls = [tc for tc in _pending_tool_calls
                                       if tc.get("name") not in _PREVIEW_GUARDED_WRITES]
                for _tc in _pg_blocked:
                    _tc["_block_reason"] = (
                        "[BLOCKED by preview confirmation guard] "
                        "This write operation requires explicit user confirmation. "
                        "A preview (preview_automation_change) was just shown. "
                        "You MUST ask the user to confirm before applying "
                        "(\"sì / yes / ok / procedi\"). "
                        "Do NOT call this tool again until the user confirms."
                    )
                logger.warning(
                    f"Preview guard: blocked {[t.get('name') for t in _pg_blocked]} "
                    "— user confirmation required after preview_automation_change"
                )
            else:
                _pg_blocked = []
            if _cur_has_preview:
                _preview_round_done = True

            # Additional safety: update_automation must match the last shown preview
            # in this session (prevents applying changes different from displayed diff).
            _sig_blocked = []
            _now = time.time()
            _last_preview = session_last_preview.get(session_id)
            if _last_preview and (_now - float(_last_preview.get("ts", 0))) > _PREVIEW_MATCH_TTL_SECONDS:
                session_last_preview.pop(session_id, None)
                _last_preview = None

            for _tc in list(_pending_tool_calls):
                if _tc.get("name") != "update_automation":
                    continue
                try:
                    _ua_args = json.loads(_tc.get("arguments", "{}") or "{}")
                except Exception:
                    _ua_args = {}
                if not isinstance(_ua_args, dict):
                    _ua_args = {}

                _update_sig = _automation_change_signature(_ua_args)
                _update_norm = _normalize_automation_change_args(_ua_args)

                # Early reject: if changes are empty, there's nothing to apply.
                if not _update_norm.get("changes") and not _update_norm.get("add_condition"):
                    _pending_tool_calls.remove(_tc)
                    _blocked_aid = _update_norm.get("automation_id", "")
                    _reason = (
                        "[BLOCKED] update_automation called with empty changes — nothing to apply. "
                        f"First call preview_automation_change with automation_id={_blocked_aid!r} and "
                        "the actual changes you want to make (e.g. changes={\"trigger\": [...]}), "
                        "then ask for confirmation."
                    )
                    _tc["_block_reason"] = _reason
                    _sig_blocked.append(_tc)
                    logger.warning(f"Preview-match guard: blocked update_automation with empty changes (automation_id={_blocked_aid!r})")
                    continue

                _has_preview = bool(_last_preview and _last_preview.get("type") == "automation_preview")
                _same_automation = bool(
                    _has_preview and str(_last_preview.get("automation_id", "")) == _update_norm.get("automation_id", "")
                )
                _same_sig = bool(_has_preview and _last_preview.get("signature") == _update_sig)

                if not (_has_preview and _same_automation and _same_sig):
                    if _has_preview and _same_automation and not _same_sig:
                        # User confirmed after seeing a preview for this automation.
                        # The LLM regenerated slightly different changes — override with
                        # the exact changes that were shown to the user.
                        _stored_norm = _last_preview.get("norm", {})
                        _stored_changes = _stored_norm.get("changes", {}) if _stored_norm else {}
                        if _stored_norm and _stored_changes:
                            # Only allow override if the stored preview had actual (non-empty) changes.
                            _tc["arguments"] = json.dumps({
                                "automation_id": _stored_norm.get("automation_id", _update_norm.get("automation_id")),
                                "changes": _stored_changes,
                                **( {"add_condition": _stored_norm["add_condition"]} if _stored_norm.get("add_condition") else {} ),
                            }, ensure_ascii=False)
                            logger.info("Preview-match guard: overriding LLM args with stored preview changes (same_automation, sig mismatch)")
                            continue  # allow the update with corrected args
                        else:
                            logger.warning("Preview-match guard: stored preview has empty changes — treating as no valid preview")
                    _pending_tool_calls.remove(_tc)
                    _blocked_changes = _update_norm.get("changes", {})
                    _blocked_aid = _update_norm.get("automation_id", "")
                    _reason = (
                        "[BLOCKED by preview-match guard] "
                        "update_automation requires an up-to-date preview_automation_change first. "
                        f"Call preview_automation_change with automation_id={_blocked_aid!r} and "
                        f"changes={json.dumps(_blocked_changes, ensure_ascii=False)} — "
                        "then ask for confirmation before calling update_automation."
                    )
                    _tc["_block_reason"] = _reason
                    _sig_blocked.append(_tc)
                    logger.warning(
                        "Preview-match guard: blocked update_automation "
                        f"(has_preview={_has_preview}, same_automation={_same_automation}, same_sig={_same_sig})"
                    )
            # ─────────────────────────────────────────────────────────────

            # Assign stable IDs to pending tool calls BEFORE building messages.
            # Both the assistant message and tool result messages must reference
            # the same ID — otherwise providers reject the mismatch.
            for _tc_idx, _tc_item in enumerate(_pending_tool_calls):
                if not _tc_item.get("id"):
                    _tc_item["id"] = f"call_{_tc_item.get('name', 'tool')}_{_tc_idx}"
            # Also assign IDs for blocked tool calls (needed for consistent history)
            for _pb_idx, _pb_item in enumerate(_pg_blocked):
                if not _pb_item.get("id"):
                    _pb_item["id"] = f"call_{_pb_item.get('name', 'blocked')}_{_pb_idx}_pg"
            for _sb_idx, _sb_item in enumerate(_sig_blocked):
                if not _sb_item.get("id"):
                    _sb_item["id"] = f"call_{_sb_item.get('name', 'blocked')}_{_sb_idx}_sig"

            # Append assistant message with tool_calls (OpenAI format)
            # Include both executed and blocked tool calls so history stays well-formed
            _all_tcs_for_msg = _pending_tool_calls + _pg_blocked + _sig_blocked
            messages.append({
                "role": "assistant",
                "content": text_so_far or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc.get("name", ""),
                            "arguments": tc.get("arguments", "{}"),
                        },
                    }
                    for tc in _all_tcs_for_msg
                ],
            })
            # Add synthetic "blocked" results for write tools the guard prevented
            for _pb_tc in (_pg_blocked + _sig_blocked):
                messages.append({
                    "role": "tool",
                    "tool_call_id": _pb_tc["id"],
                    "name": _pb_tc.get("name", ""),
                    "content": _pb_tc.get("_block_reason") or (
                        "[BLOCKED] This write operation was blocked by safety guards."
                    ),
                })

            # Execute each tool and append its result
            _round_has_rich_diff = False
            _any_successful_write_this_round = False
            _round_write_confirms: list[str] = []
            _stop_after_html_dashboard_success = False
            _html_dashboard_success_message = ""
            _stop_after_html_dashboard_error = False
            _html_dashboard_error_message = ""
            for tc in _pending_tool_calls:
                fn_name = tc.get("name", "")
                try:
                    _raw_args = tc.get("arguments", "{}") or "{}"
                    if isinstance(_raw_args, dict):
                        tc_args = _raw_args
                    else:
                        try:
                            tc_args = json.loads(_raw_args)
                        except Exception:
                            from providers.enhanced import EnhancedProvider
                            tc_args = json.loads(EnhancedProvider._repair_json(str(_raw_args)))
                except Exception:
                    tc_args = {}
                # Guard: json.loads may return None/list/int from malformed
                # arguments (e.g. "null").  Ensure tc_args is always a dict.
                if not isinstance(tc_args, dict):
                    tc_args = {}

                # Show status to user (registry provides Italian labels)
                if _tool_registry is not None:
                    _status_label = _tool_registry.get_user_description(fn_name)
                else:
                    _status_label = tools.TOOL_DESCRIPTIONS.get(fn_name, fn_name)
                yield {"type": "status", "message": f"🔧 {_status_label}..."}
                logger.info(f"Tool (round {_tool_round}): {fn_name} {list(tc_args.keys())}")

                _sig = f"{fn_name}:{json.dumps(tc_args, sort_keys=True)}"
                if fn_name in _read_only_tools and _sig in _tool_cache:
                    logger.debug(f"Tool cache hit: {fn_name}")
                    result = _tool_cache[_sig]
                elif fn_name.startswith("mcp_"):
                    # MCP tools are runtime-dynamic and are not part of the static
                    # ToolRegistry catalog: execute via direct MCP dispatcher.
                    result = tools.execute_tool(fn_name, tc_args)
                    if fn_name in _read_only_tools:
                        _tool_cache[_sig] = result
                elif _tool_registry is not None:
                    # === OpenClaw-style execution with hooks ===
                    # The registry applies before/after hooks:
                    # - ReadOnlyHook: blocks writes in read-only sessions
                    # - DuplicateCallHook: detects repeated calls
                    # - EntityValidationHook: validates entity_id format
                    # - LoggingHook: logs timing and results
                    from tool_registry import ToolCallContext
                    _exec_ctx = ToolCallContext(
                        tool_name=fn_name,
                        arguments=tc_args,
                        session_id=session_id,
                        read_only=getattr(tools, 'is_read_only_session', lambda s: False)(session_id) if hasattr(tools, 'is_read_only_session') else False,
                        round_number=_tool_round,
                        call_history=_tool_call_history,
                    )
                    result = _tool_registry.execute(fn_name, tc_args, context=_exec_ctx)
                    if fn_name in _read_only_tools:
                        _tool_cache[_sig] = result
                else:
                    # Legacy execution path
                    result = tools.execute_tool(fn_name, tc_args)
                    if fn_name in _read_only_tools:
                        _tool_cache[_sig] = result

                # Record this tool call in history AFTER execution so that
                # DuplicateCallHook won't block the very first invocation.
                _tool_call_history.add(_sig)

                _result_obj = None
                try:
                    _parsed = json.loads(result) if isinstance(result, str) else result
                    if isinstance(_parsed, dict):
                        _result_obj = _parsed
                except Exception:
                    _result_obj = None

                if _result_obj is not None:
                    _status = str(_result_obj.get("status", "")).lower().strip()
                    _is_err = (
                        _status in {"error", "failed", "invalid"}
                        or bool(_result_obj.get("error"))
                    )
                    _is_ok = bool(_result_obj) and not _is_err

                    if not _is_read_only_call(tc) and _is_ok:
                        _any_successful_write_this_round = True
                        _write_tools_executed.append(fn_name)
                        # Deterministic confirmation for no-tool providers:
                        # avoid extra model round that may contradict executed actions.
                        if fn_name == "call_service":
                            _dom = str(tc_args.get("domain") or "").strip()
                            _svc = str(tc_args.get("service") or "").strip()
                            _eid = str(tc_args.get("entity_id") or "").strip()
                            _tgt = tc_args.get("target") if isinstance(tc_args.get("target"), dict) else {}
                            _dat = tc_args.get("data") if isinstance(tc_args.get("data"), dict) else {}
                            _eid = _eid or str(_tgt.get("entity_id") or _dat.get("entity_id") or "").strip()
                            _svc_full = f"{_dom}.{_svc}" if _dom and _svc else (_svc or _dom or "service")
                            if _eid:
                                _round_write_confirms.append(f"✅ Eseguito `{_svc_full}` su `{_eid}`.")
                            else:
                                _round_write_confirms.append(f"✅ Eseguito `{_svc_full}`.")
                        else:
                            _msg = str(_result_obj.get("message") or "").strip()
                            if _msg:
                                _round_write_confirms.append(f"✅ {_msg}")

                    if fn_name == "preview_automation_change" and _status == "preview":
                        _norm = _normalize_automation_change_args(tc_args)
                        session_last_preview[session_id] = {
                            "type": "automation_preview",
                            "automation_id": _norm.get("automation_id", ""),
                            "signature": _automation_change_signature(tc_args),
                            "norm": _norm,  # stored so guard can reuse exact changes on confirm
                            "ts": time.time(),
                        }
                    elif fn_name == "update_automation" and _is_ok:
                        # Clear only after successful apply
                        session_last_preview.pop(session_id, None)
                    elif fn_name == "create_html_dashboard":
                        _dash_name = str((_result_obj.get("name") or tc_args.get("name") or "")).strip()
                        if _status in {"draft_started", "draft_appended"} and _dash_name:
                            _html_draft_pending_name = _dash_name
                        elif _status == "success":
                            _html_dashboard_saved_this_turn = True
                            _html_draft_pending_name = ""
                            _stop_after_html_dashboard_success = True
                            _html_dashboard_success_message = (
                                _result_obj.get("message")
                                or f"✅ Dashboard HTML '{_result_obj.get('filename', _dash_name or 'dashboard')}' salvata."
                            )
                        elif bool(_result_obj.get("error")):
                            # If finalize call failed, clear pending draft name to avoid
                            # redundant auto-finalize attempts with empty payload.
                            if not bool(tc_args.get("draft", False)):
                                _html_draft_pending_name = ""
                            _err_text = str(_result_obj.get("error", "") or "")
                            if "INLINE_HTML_BLOCKED" in _err_text:
                                _stop_after_html_dashboard_error = True
                                _html_dashboard_error_message = (
                                    "❌ Dashboard non creata: il provider continua a inviare HTML inline "
                                    "non conforme al formato file-safe richiesto."
                                )
                                # Break current tool-call batch immediately to avoid looping
                                # over the remaining duplicate create_html_dashboard calls.
                                break

                # Extract diff + modified filename for UI rendering (strip before feeding to model)
                try:
                    if isinstance(_result_obj, dict) and "diff" in _result_obj:
                        _diff_content = _result_obj.pop("diff")
                        _modified_file = _result_obj.get("file", "")  # relative path if set
                        result = json.dumps(_result_obj, ensure_ascii=False)
                        yield {"type": "diff", "content": _diff_content, "file": _modified_file}
                        _round_has_rich_diff = True
                except Exception:
                    pass

                # Log tool result (truncate to 300 chars)
                _log_result = result[:300] + ('...' if len(result) > 300 else '')
                logger.info(f"Tool result [{fn_name}]: {_log_result}")

                # For write tools, emit a formatted diff view to the UI
                _WRITE_TOOLS = {"create_automation", "update_automation", "create_script",
                                "update_script", "write_config_file", "update_dashboard",
                                "preview_automation_change"}
                if fn_name in _WRITE_TOOLS:
                    try:
                        _wr_obj = json.loads(result) if isinstance(result, str) else result
                        if isinstance(_wr_obj, dict):
                            _formatted = _format_write_tool_response(fn_name, _wr_obj)
                            if _formatted:
                                yield {"type": "diff_html", "content": _formatted}
                                _round_has_rich_diff = True
                    except (json.JSONDecodeError, TypeError):
                        pass

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": fn_name,
                    "content": result,
                })

            # Stop immediately after successful HTML dashboard save:
            # avoids pointless extra rounds where no-tool models keep re-emitting
            # the same tool_call and eventually fail on parser/network fallbacks.
            if _stop_after_html_dashboard_success:
                if _html_dashboard_success_message:
                    yield {"type": "token", "content": _html_dashboard_success_message}
                    # Persist final dashboard confirmation in conversation history.
                    # Without this, the user sees it live in stream but loses it
                    # after page reload because no final assistant text is saved.
                    _streamed_text_parts = [_html_dashboard_success_message]
                break
            if _stop_after_html_dashboard_error:
                if _html_dashboard_error_message:
                    yield {"type": "token", "content": _html_dashboard_error_message}
                    _streamed_text_parts = [_html_dashboard_error_message]
                break

            # For no-tool providers: if a write action was executed, finish here
            # with backend-confirmed text (skip another LLM round).
            if _is_no_tool_provider and _round_write_confirms:
                _final_conf = "\n".join(dict.fromkeys([c for c in _round_write_confirms if c]))
                if _final_conf:
                    yield {"type": "token", "content": _final_conf}
                    _streamed_text_parts = [_final_conf]
                break

            # ── After executing a WRITE tool, disable ToolSimulator extraction
            # ── for the next round so the model MUST produce text (not another
            # ── <tool_call> block).  No-tool providers (Copilot) tend to re-call
            # ── the same tool after getting the write result instead of reporting.
            if _is_no_tool_provider:
                if _any_successful_write_this_round:
                    # Capture the last tool result for fallback display
                    for m in reversed(messages):
                        if m.get("role") == "tool":
                            _last_write_result = m.get("content", "")
                            break
                    _skip_tool_extraction = True
                    logger.info("Write tool executed — disabling ToolSimulator for next round")
                    # Inject a user message forcing the model to produce plain text,
                    # not another <tool_call>.  This is the most reliable way to stop
                    # no-tool providers from re-calling the same tool in a loop.
                    messages.append({
                        "role": "user",
                        "content": (
                            "[SYSTEM] The tool executed successfully. "
                            "Now describe the results to the user in plain text. "
                            "List all affected entity IDs. "
                            "Do NOT call any tool. Do NOT use <tool_call>."
                        ),
                    })

            # Signal the UI to reset display and re-show thinking indicator
            # before the next provider API call (which may take time due to rate limits).
            # If a rich diff was just shown, don't clear it before the final assistant text.
            if not _round_has_rich_diff:
                yield {"type": "clear"}
                yield {"type": "status", "message": f"🤖 {tr('status_analyzing')}..."}

        # Sync new assistant messages to conversation history.
        # New-path providers (Mistral, Groq, openai_compatible, etc.) stream text as
        # events but do NOT append to `messages`, so we use _streamed_text_parts.
        # During tool-calling, the tool loop appends intermediate assistant messages
        # (with tool_calls) to `messages`.  These are saved below for history but are
        # hidden from the UI by _is_tool_call_artifact.  The FINAL text response lives
        # in _streamed_text_parts and MUST also be saved — hence the two separate `if`
        # blocks (was `elif` before, which caused the final answer to be lost when tool
        # calls occurred).
        is_anthropic_or_google = AI_PROVIDER in ("anthropic", "google")
        new_msgs_from_provider = [
            msg for msg in messages[conv_length_before:]
            if msg.get("role") in ("assistant", "tool")
            and not (is_anthropic_or_google and isinstance(msg.get("content", ""), list))
        ]
        if new_msgs_from_provider:
            for msg in new_msgs_from_provider:
                if msg.get("role") == "assistant":
                    msg["model"] = get_active_model()
                    msg["provider"] = AI_PROVIDER
                    if last_usage:
                        msg["usage"] = last_usage
                conversations[session_id].append(msg)
        if _streamed_text_parts:
            # Assemble streamed tokens into the final assistant message.
            # This is the main user-facing response — for tool-calling conversations
            # it's the text from the LAST streaming round (after all tools executed).
            assembled = "".join(_streamed_text_parts).strip()
            # Clean any raw <tool_call> XML or [TOOL RESULT] blocks from history
            if _is_no_tool_provider and assembled:
                from providers.tool_simulator import clean_display_text as _cdt_hist
                assembled = _cdt_hist(assembled)

            # ── Safety check: no-tool provider claimed success without calling any write tool ──
            # Detects the "hallucinated success" pattern: the model wrote "aggiornata con successo"
            # but never emitted a <tool_call> block (so nothing was actually executed).
            _HALLUCINATED_SUCCESS_PHRASES = (
                "aggiornata", "applicata", "modificata", "updated successfully", "applied",
                "aggiornato", "creata", "salvata", "success", "✅", "completata", "eseguita",
                "ho acceso", "acceso", "ho spento", "spento", "ho attivato", "attivato",
                "fatto", "done", "completed",
            )
            _ACTION_REQUEST_RE = re.compile(
                r"\b(accendi|spegni|apri|chiudi|attiva|disattiva|riavvia|"
                r"turn\s*on|turn\s*off|switch\s*on|switch\s*off|open|close|enable|disable)\b",
                re.IGNORECASE,
            )
            _user_asked_action = bool(_ACTION_REQUEST_RE.search(str(user_message or "")))
            # Fallback for no-tool providers:
            # if user asked a simple on/off action and the model produced text only,
            # execute via backend tools to avoid "no action performed" dead-ends.
            if (
                _is_no_tool_provider
                and assembled
                and not _write_tools_executed
                and _user_asked_action
            ):
                _um = str(user_message or "")
                _um_l = _um.lower()
                _svc = ""
                if re.search(r"\b(spegni|turn\s*off|switch\s*off|disattiva|off)\b", _um_l):
                    _svc = "turn_off"
                elif re.search(r"\b(accendi|turn\s*on|switch\s*on|attiva|on)\b", _um_l):
                    _svc = "turn_on"

                if _svc:
                    try:
                        _q = re.sub(
                            r"\b(mi|per favore|perfavore|la|il|lo|i|gli|le|un|uno|una|della|del|dello|dei|degli|delle|di|da|in|su|con|e)\b",
                            " ",
                            _um_l,
                            flags=re.IGNORECASE,
                        )
                        _q = re.sub(
                            r"\b(accendi|spegni|attiva|disattiva|turn\s*on|turn\s*off|switch\s*on|switch\s*off|open|close|enable|disable)\b",
                            " ",
                            _q,
                            flags=re.IGNORECASE,
                        )
                        _q = re.sub(r"[^\w\s\.]", " ", _q)
                        _q = re.sub(r"\s+", " ", _q).strip()
                        if not _q:
                            _q = _um_l

                        _sr_raw = tools.execute_tool("search_entities", {"query": _q})
                        _sr = json.loads(_sr_raw) if isinstance(_sr_raw, str) else _sr_raw
                        _matches = _sr if isinstance(_sr, list) else []
                        _best_eid = ""
                        if _matches:
                            _allowed_domains = {"light", "switch", "input_boolean", "fan"}
                            _sorted = sorted(
                                _matches,
                                key=lambda it: (
                                    0 if str((it or {}).get("entity_id", "")).split(".")[0] in _allowed_domains else 1,
                                    -float((it or {}).get("token_coverage", 0) or 0),
                                    0 if str((it or {}).get("match_quality", "")) == "high" else (1 if str((it or {}).get("match_quality", "")) == "medium" else 2),
                                ),
                            )
                            _best_eid = str((_sorted[0] or {}).get("entity_id", "")).strip()

                        if _best_eid and "." in _best_eid:
                            _dom = _best_eid.split(".", 1)[0]
                            _svc_raw = tools.execute_tool(
                                "call_service",
                                {"domain": _dom, "service": _svc, "entity_id": _best_eid},
                            )
                            _svc_obj = json.loads(_svc_raw) if isinstance(_svc_raw, str) else _svc_raw
                            _ok = isinstance(_svc_obj, dict) and str(_svc_obj.get("status", "")).lower() == "success" and not _svc_obj.get("error")
                            if _ok:
                                assembled = f"✅ Eseguito `{_dom}.{_svc}` su `{_best_eid}`."
                                _write_tools_executed.append("call_service")
                                logger.info(
                                    "No-tool fallback action executed: %s on %s (provider=%s)",
                                    f"{_dom}.{_svc}", _best_eid, AI_PROVIDER
                                )
                    except Exception as _fb_e:
                        logger.warning(f"No-tool fallback action failed: {_fb_e}")

            _looks_like_fake_success = any(p in assembled.lower() for p in _HALLUCINATED_SUCCESS_PHRASES)
            if (
                _is_no_tool_provider
                and assembled
                and not _write_tools_executed
                and intent_name not in ("chat", "create_html_dashboard")
                and (_looks_like_fake_success or _user_asked_action)
            ):
                _warn = get_lang_text("warn_no_tool_called") or (
                    "⚠️ Azione NON eseguita: questo provider ha risposto in testo senza chiamare tool di Home Assistant. "
                    "Nessuna modifica è stata applicata. "
                    "Riprova con un provider che supporta tool-calling oppure conferma l'esecuzione guidata."
                )
                logger.warning(
                    "No-tool provider attempted action-like reply without write tool execution "
                    f"(provider={AI_PROVIDER}, intent={intent_name}). Replacing assistant text with safety warning."
                )
                assembled = _warn
            if assembled:
                # Log the AI response for debugging (truncate to 500 chars)
                _log_resp = assembled[:500] + ('...' if len(assembled) > 500 else '')
                logger.chat(f"📤 [{AI_PROVIDER}/{get_active_model()}]: {_log_resp}")
                assistant_msg: dict = {
                    "role": "assistant",
                    "content": assembled,
                    "model": get_active_model(),
                    "provider": AI_PROVIDER,
                }
                if last_usage:
                    assistant_msg["usage"] = last_usage
                conversations[session_id].append(assistant_msg)

                # ── Auto-save HTML dashboard ───────────────────────────────
                # Providers without tool support (claude_web, groq, mistral, …)
                # stream the HTML as plain text. If the intent was
                # create_html_dashboard, extract the HTML block and save it.
                if intent_name == "create_html_dashboard":
                    import re as _re
                    html_block: Optional[str] = None
                    _fenced_blocks = []
                    try:
                        _fenced_blocks = [
                            (m.group(1) or "").strip()
                            for m in _re.finditer(
                                r'```(?:html|htm|xml|javascript|js|css)?\s*\n([\s\S]*?)```',
                                assembled,
                                _re.IGNORECASE,
                            )
                        ]
                    except Exception:
                        _fenced_blocks = []

                    def _score_html_candidate(_s: str) -> int:
                        _l = (_s or "").lower()
                        _score = 0
                        if "<!doctype html" in _l or "<html" in _l:
                            _score += 3
                        if "</html>" in _l:
                            _score += 2
                        if "<head" in _l or "<body" in _l:
                            _score += 1
                        if "<script" in _l or "createapp(" in _l:
                            _score += 1
                        if "/api/websocket" in _l or "/api/states" in _l:
                            _score += 1
                        _score += min(len(_s) // 4000, 2)
                        return _score

                    if _fenced_blocks:
                        _best_block = max(_fenced_blocks, key=_score_html_candidate)
                        _joined_blocks = "\n".join(b for b in _fenced_blocks if b)
                        if _score_html_candidate(_joined_blocks) > _score_html_candidate(_best_block):
                            html_block = _joined_blocks.strip()
                            logger.info(
                                "HTML auto-save extractor: merged %s fenced blocks (%s chars)",
                                len(_fenced_blocks),
                                len(html_block),
                            )
                        else:
                            html_block = _best_block.strip()
                            if len(_fenced_blocks) > 1:
                                logger.info(
                                    "HTML auto-save extractor: selected best fenced block among %s blocks (%s chars)",
                                    len(_fenced_blocks),
                                    len(html_block),
                                )

                    # 1. ```html ... ``` closed block (with or without DOCTYPE)
                    if not html_block:
                        m = _re.search(
                            r'```(?:html)?\s*\n((?:<!DOCTYPE\s+html|<html)[\s\S]*?)```',
                            assembled, _re.IGNORECASE
                        )
                        if m:
                            html_block = m.group(1).strip()
                    if not html_block:
                        # 2. Unclosed/truncated code block (hit token limit)
                        m = _re.search(
                            r'```(?:html)?\s*\n((?:<!DOCTYPE\s+html|<html)[\s\S]*)',
                            assembled, _re.IGNORECASE
                        )
                        if m:
                            html_block = m.group(1).strip()
                    if not html_block:
                        # 3. Bare <!DOCTYPE html> … </html> (no fence)
                        m = _re.search(
                            r'(<!DOCTYPE\s+html[\s\S]*?</html>)',
                            assembled, _re.IGNORECASE
                        )
                        if m:
                            html_block = m.group(1).strip()
                    if not html_block:
                        # 4. Bare <html> … </html> (no DOCTYPE, no fence)
                        m = _re.search(
                            r'(<html[\s>][\s\S]*?</html>)',
                            assembled, _re.IGNORECASE
                        )
                        if m:
                            html_block = m.group(1).strip()

                    if html_block:
                        # ── Derive slug/title ──────────────────────────────────────
                        # Priority 1: use the dashboard name from the bubble context prefix
                        # e.g. [CONTEXT: User is viewing HTML dashboard "ciao-epcube-tigo".]
                        _ctx_dash_m = _re.search(
                            r'\[CONTEXT:[^\]]*HTML\s+dashboard\s+["\x27]([^"\x27\]]+)["\x27]',
                            saved_user_message,
                            _re.IGNORECASE,
                        )
                        if _ctx_dash_m:
                            _slug = _ctx_dash_m.group(1).strip()
                            _title = " ".join(w.capitalize() for w in _slug.replace("-", " ").replace("_", " ").split())
                            logger.info(f"HTML dashboard auto-save: using context name '{_slug}'")
                        else:
                            # Priority 2: derive from user's actual message (strip context blocks)
                            _clean_msg = _re.sub(r'\[CONTEXT:[^\]]*\]', '', saved_user_message)
                            _clean_msg = _re.sub(r'\[CURRENT_DASHBOARD_HTML\][\s\S]*?\[/CURRENT_DASHBOARD_HTML\]', '', _clean_msg)
                            _stop = {"mi", "crei", "crea", "una", "un", "la", "il",
                                     "con", "i", "de", "dei", "degli", "delle", "del", "le",
                                     "sensori", "sensore", "di", "e", "pagina", "html",
                                     "web", "per", "make", "create", "page",
                                     "dashboard", "pannello"}
                            _words = _re.sub(r'[^\w\s]', ' ', _clean_msg.lower()).split()
                            _slug_words = [w for w in _words if w not in _stop and len(w) > 2][:3]
                            _slug = "-".join(_slug_words) or "dashboard"
                            _title = " ".join(w.capitalize() for w in _slug_words) or "Dashboard"

                        # Extract entity ids mentioned in the HTML
                        # Match any domain.entity pattern (covers custom integrations like epcube)
                        _entities = list(dict.fromkeys(_re.findall(
                            r'\b([a-z_][a-z0-9_]*\.[a-z0-9][a-z0-9_]+)\b',
                            html_block
                        )))
                        # Filter out obvious non-entity patterns (CSS, JS, HTML attrs)
                        _skip = {"text.bold", "div.card", "font.size", "margin.top",
                                  "border.radius", "background.color", "flex.wrap",
                                  "font.weight", "padding.top"}
                        # Domains that are never valid HA entity domains
                        _skip_domains = {"icon", "font", "text", "div", "span", "style",
                                         "margin", "border", "background", "padding",
                                         "flex", "color", "width", "height", "display",
                                         "position", "align", "justify", "overflow",
                                         "cursor", "opacity", "transform", "transition"}
                        _entities = [e for e in _entities if
                                     '.' in e and e not in _skip
                                     and e.split('.')[0] not in _skip_domains
                                     and not e.startswith(("http.", "https.", "www.",
                                                           "Math.", "JSON.", "Object.",
                                                           "console.", "window.", "document.",
                                                           "Promise.", "Array.", "String.",
                                                           "Number.", "Boolean.", "Date."))]
                        # Deduplicate preserving order
                        _entities = list(dict.fromkeys(_entities))

                        try:
                            yield {"type": "status", "message": "💾 Salvo la dashboard HTML…"}
                            _save_args = {
                                "title": _title,
                                "name": _slug,
                                "entities": _entities,
                            }
                            # For no-tool providers (web/codex/coplay), avoid passing long
                            # inline HTML through JSON: use base64 channel to prevent parse
                            # corruption and satisfy raw-only mode guard.
                            if _is_no_tool_provider and len(html_block or "") > 1800:
                                import base64 as _b64
                                _save_args["html_base64"] = _b64.b64encode(
                                    (html_block or "").encode("utf-8", errors="ignore")
                                ).decode("ascii")
                                logger.info(
                                    "HTML auto-save: using html_base64 for no-tool provider '%s' (%s chars)",
                                    AI_PROVIDER,
                                    len(html_block or ""),
                                )
                            else:
                                _save_args["html"] = html_block
                            _save_result = tools.execute_tool("create_html_dashboard", _save_args)
                            _save_obj = {}
                            try:
                                _save_obj = json.loads(_save_result) if isinstance(_save_result, str) else (_save_result or {})
                            except Exception:
                                _save_obj = {"raw": str(_save_result)}
                            logger.info(
                                f"Auto-saved HTML dashboard '{_slug}' "
                                f"(entities={len(_entities)}): {str(_save_result)[:200]}"
                            )
                            _save_ok = (
                                isinstance(_save_obj, dict)
                                and _save_obj.get("status") == "success"
                                and bool(_save_obj.get("filename") or _save_obj.get("html_url"))
                            )
                            if _save_ok:
                                _saved_filename = _save_obj.get("filename") or f"{_slug}.html"
                                yield {"type": "status", "message": f"✅ Dashboard HTML '{_saved_filename}' salvata!"}
                                _saved_url = _save_obj.get("html_url") or f"/local/dashboards/{_saved_filename}"
                                _user_msg = (
                                    f"✨ Dashboard **{_title}** creata! "
                                    f"Aprila qui: `{_saved_url}`"
                                )
                                # Emit a normal assistant token so it is visible in chat
                                # (status events are transient and may not appear in history UI).
                                yield {"type": "token", "content": _user_msg}
                                # Strip the raw HTML from conversation history so that
                                # re-opening this chat shows only a short confirmation,
                                # not walls of HTML code.
                                _last_msg = (conversations.get(session_id) or [None])[-1]
                                if (_last_msg and _last_msg.get("role") == "assistant"
                                        and len(_last_msg.get("content", "")) > 500):
                                    conversations[session_id][-1]["content"] = _user_msg
                            else:
                                _err_msg = ""
                                if isinstance(_save_obj, dict):
                                    _err_msg = (
                                        _save_obj.get("error")
                                        or _save_obj.get("message")
                                        or _save_obj.get("raw", "")
                                    )
                                _err_msg = str(_err_msg or "create_html_dashboard did not return success")
                                logger.warning(
                                    "Auto-save HTML dashboard failed for '%s': %s",
                                    _slug,
                                    _err_msg[:500],
                                )
                                yield {"type": "status", "message": f"⚠️ Salvataggio HTML fallito: {_err_msg}"}
                                # Emit a persistent assistant message too (status is transient)
                                yield {"type": "token", "content": f"⚠️ Salvataggio dashboard HTML fallito: {_err_msg}"}
                        except Exception as _e:
                            logger.warning(f"Auto-save HTML dashboard failed: {_e}")
                            yield {"type": "status", "message": f"⚠️ Salvataggio HTML fallito: {_e}"}
                            # Emit a persistent assistant message too (status is transient)
                            yield {"type": "token", "content": f"⚠️ Salvataggio dashboard HTML fallito: {_e}"}
                    if _deferred_done_event is not None:
                        yield _deferred_done_event
                        _deferred_done_event = None
                # ──────────────────────────────────────────────────────────
                # NOTE: sentinel-based auto-execute blocks (CONFIRM_CREATE_AUTOMATION etc.)
                # have been removed. No-tool providers now use the universal Tool Simulator
                # (<tool_call> XML blocks) which are handled by the streaming loop above.

        # Trim and save (respect tool_call/tool boundaries)
        if len(conversations[session_id]) > 50:
            trimmed = conversations[session_id][-40:]
            # Don't start with orphaned tool messages
            while trimmed and trimmed[0].get("role") == "tool":
                trimmed = trimmed[1:]
            # Don't start with assistant+tool_calls whose tool responses were cut
            if trimmed and trimmed[0].get("role") == "assistant" and trimmed[0].get("tool_calls"):
                if len(trimmed) < 2 or trimmed[1].get("role") != "tool":
                    trimmed = trimmed[1:]
            conversations[session_id] = trimmed
        if _deferred_done_event is not None:
            yield _deferred_done_event
            _deferred_done_event = None
        save_conversations()
        
        # Save to persistent memory if enabled
        if ENABLE_MEMORY and MEMORY_AVAILABLE and conversations[session_id]:
            try:
                # Generate title from first user message
                first_user_msg = next(
                    (m.get("content", "")[:60].strip() for m in conversations[session_id] if m.get("role") == "user"),
                    f"Chat #{session_id}"
                )
                title = first_user_msg if first_user_msg else f"Chat on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                memory.save_conversation(
                    session_id=session_id,
                    title=title,
                    messages=conversations[session_id],
                    provider=AI_PROVIDER,
                    model=get_active_model(),
                    metadata={"intent": intent_name, "read_only": read_only}
                )
                logger.info(f"Conversation {session_id} saved to persistent memory")
            except Exception as e:
                logger.warning(f"Failed to save conversation to memory: {e}")
    except Exception as e:
        logger.error(f"Stream error ({AI_PROVIDER}): {e}")
        yield {"type": "error", "message": humanize_provider_error(e, AI_PROVIDER)}



# ---- Flask Routes ----


@app.route('/')
def index():
    """Serve the chat UI."""
    try:
        logger.info("Generating chat UI...")
        html = chat_ui.get_chat_ui()
        logger.info("Chat UI generated successfully")
        
        # Sanitize surrogates that cause UnicodeEncodeError
        html = html.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        
        return Response(
            html,
            mimetype='text/html; charset=utf-8',
            headers={
                'Cache-Control': 'no-store, max-age=0',
                'Pragma': 'no-cache',
                'Expires': '0',
            }
        )
    except Exception as e:
        logger.error(f"Error generating chat UI: {type(e).__name__}: {str(e)}", exc_info=True)
        # Return JSON error instead of HTML to see the actual message
        return {"error": f"Error generating UI: {type(e).__name__}: {str(e)}"}, 500


@app.route('/ui_bootstrap.js')
def ui_bootstrap_js():
    """Small bootstrap script loaded before the main inline UI.

    Purpose: if the large inline script fails to parse/execute (Ingress/CSP/cache/etc.),
    we still get a server log signal and a visible error when pressing Send.
    """
    js = r"""
(function () {
    function appendSystem(text) {
        try {
            var container = document.getElementById('chat');
            if (!container) return;
            var div = document.createElement('div');
            div.className = 'message system';
            div.textContent = String(text || '');
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        } catch (e) {}
    }

    // Lightweight ping so the add-on logs show the browser executed JS.
    try {
        fetch('./api/ui_ping', { cache: 'no-store' }).catch(function () {});
    } catch (e) {}

    function onSendAttempt(evt) {
        try {
            // If the main UI didn't load, explain it directly.
            if (typeof window.handleButtonClick !== 'function') {
                appendSystem('❌ UI error: main script not loaded (handleButtonClick missing).');
                try { fetch('./api/ui_ping?send=1', { cache: 'no-store' }).catch(function () {}); } catch (e) {}
                if (evt && evt.preventDefault) evt.preventDefault();
                return false;
            }
        } catch (e) {}
        return true;
    }

    function bind() {
        try {
            var btn = document.getElementById('sendBtn');
            if (btn && !btn._bootstrapBound) {
                btn._bootstrapBound = true;
                btn.addEventListener('click', onSendAttempt, true);
            }
            var input = document.getElementById('input');
            if (input && !input._bootstrapKeyBound) {
                input._bootstrapKeyBound = true;
                input.addEventListener('keydown', function (e) {
                    if (e && e.key === 'Enter' && !e.shiftKey) {
                        onSendAttempt(e);
                    }
                }, true);
            }
        } catch (e) {}
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else {
        bind();
    }
})();
"""
    return js, 200, {
        'Content-Type': 'application/javascript; charset=utf-8',
        'Cache-Control': 'no-store, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0',
    }


@app.route('/ui_main.js')
def ui_main_js():
    """Serve the main UI script as an external JS file.

    Home Assistant Ingress commonly enforces a strict CSP that blocks inline
    scripts and inline event handlers. Serving the same code as an external
    script allows the UI to boot.

    Implementation detail: we extract the inline `<script>...</script>` from
    the HTML so there's a single source of truth.
    """
    html = chat_ui.get_chat_ui()
    # Use negative lookahead to exclude <script src="..."> tags
    m = re.search(r"<script(?!\s+src\s*=)[^>]*>\s*(.*?)\s*</script>", html, flags=re.S | re.I)
    js = (m.group(1) if m else "")
    if not js:
        logger.error("ui_main.js extraction failed: no inline <script> found")
        return js, 200, {'Content-Type': 'application/javascript; charset=utf-8'}
    
    # Fix newlines that break regex patterns (from Python/source line wrapping)
    # Only collapse newlines within regex delimiters: /...NEWLINE.../
    # Must NOT match across lines with // comments
    lines = js.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if line ends with / and next line could complete it
        if i < len(lines) - 1 and line.rstrip().endswith('/') and not line.rstrip().endswith('//'):
            # This line might be an incomplete regex - the / without closing /
            next_line = lines[i + 1]
            # If the next line starts with potential regex continuation
            if re.match(r'^\s*[^/]*?/[igm]*', next_line):
                # Likely a regex split across lines - join them
                result.append(line.rstrip() + ' ' + next_line.lstrip())
                i += 2
                continue
        result.append(line)
        i += 1
    js = '\n'.join(result)
    
    return js, 200, {
        'Content-Type': 'application/javascript; charset=utf-8',
        'Cache-Control': 'no-store, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0',
    }


# ── SDK availability helpers (used by /api/status, /api/system/features, chat) ──

# Maps provider name → Python package needed to chat.
# Providers not listed here use httpx (already in core).
_PROVIDER_SDK_MAP = {
    "anthropic": "anthropic",
    "openai": "openai",
    "google": None,   # uses httpx directly (no google-genai SDK needed at runtime)
    "nvidia": None,    # OpenAI-compat via httpx
    "github": None,    # OpenAI-compat via httpx
    "groq": None,
    "mistral": None,
    "deepseek": None,
    "xai": None,
    "openrouter": None,
    "ollama": None,
    "custom": None,
    "minimax": None,
    "aihubmix": None,
    "siliconflow": None,
    "volcengine": None,
    "dashscope": None,
    "moonshot": None,
    "zhipu": None,
    "perplexity": None,
    "github_copilot": None,
    "openai_codex": None,
    "claude_web": None,
    "chatgpt_web": None,
    "gemini_web": None,
    "perplexity_web": None,
}

def _check_optional_sdks() -> dict:
    """Quick import-check for every optional dependency. Returns {name: bool}."""
    pkgs = ["anthropic", "openai", "google.genai", "mcp", "telegram", "twilio", "PyPDF2", "docx"]
    out = {}
    for name in pkgs:
        try:
            __import__(name)
            out[name] = True
        except ImportError:
            out[name] = False
    return out


def _check_provider_sdk(provider: str) -> tuple:
    """Check if the SDK needed by the given provider is installed.

    Returns:
        (True, "")           – SDK available or not needed.
        (False, human_msg)   – SDK missing, human_msg explains what to do.
    """
    sdk = _PROVIDER_SDK_MAP.get(provider)
    if sdk is None:
        return (True, "")
    try:
        __import__(sdk)
        return (True, "")
    except ImportError:
        _msgs = {
            "en": f"The '{sdk}' package is not installed. Provider '{provider}' cannot work. "
                  f"This can happen on ARM/Raspberry Pi devices where some packages fail to compile.",
            "it": f"Il pacchetto '{sdk}' non è installato. Il provider '{provider}' non può funzionare. "
                  f"Questo può succedere su dispositivi ARM/Raspberry Pi dove alcuni pacchetti non si compilano.",
            "es": f"El paquete '{sdk}' no está instalado. El proveedor '{provider}' no puede funcionar. "
                  f"Esto puede ocurrir en dispositivos ARM/Raspberry Pi.",
            "fr": f"Le package '{sdk}' n'est pas installé. Le fournisseur '{provider}' ne peut pas fonctionner. "
                  f"Cela peut se produire sur les appareils ARM/Raspberry Pi.",
        }
        return (False, _msgs.get(LANGUAGE, _msgs["en"]))


@app.route('/api/ui_ping', methods=['GET'])
def api_ui_ping():
    """No-op endpoint used only to confirm that the browser executed JS."""
    # Intentionally returns empty 204; request/response are logged by middleware.
    return ("", 204)


@app.route('/api/status')
def api_status():
    """Debug endpoint to check HA connection status."""
    token = get_ha_token()
    ha_ok = False
    ha_msg = ""
    try:
        resp = requests.get(f"{HA_URL}/api/", headers=get_ha_headers(), timeout=10)
        ha_ok = resp.status_code == 200
        ha_msg = f"{resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        ha_msg = str(e)

    # Check optional SDK availability
    pkg_status = _check_optional_sdks()
    missing = [k for k, v in pkg_status.items() if not v]
    provider_sdk_ok, provider_sdk_msg = _check_provider_sdk(AI_PROVIDER)

    return jsonify({
        "version": VERSION,
        "provider": AI_PROVIDER,
        "model": get_active_model(),
        "api_key_set": bool(get_api_key()),
        "ha_url": HA_URL,
        "supervisor_token_present": bool(token),
        "supervisor_token_length": len(token),
        "ha_connection_ok": ha_ok,
        "ha_response": ha_msg,
        "provider_sdk_available": provider_sdk_ok,
        "provider_sdk_message": provider_sdk_msg,
        "optional_packages": pkg_status,
        "missing_packages": missing,
        "platform": __import__('platform').machine(),
    })




# ---- Chat Bubble ----

_chat_bubble_registered = False


def setup_chat_bubble():
    """Register the floating chat bubble JS as a Lovelace frontend resource.

    Saves JS to /config/www/ and registers it via HA websocket so it loads
    on every HA page. Called once at startup if enable_chat_bubble is true.
    """
    global _chat_bubble_registered
    if _chat_bubble_registered:
        logger.debug("Chat bubble: Already registered, skipping")
        return
    logger.info(
        "Chat bubble setup: "
        f"ENABLE_CHAT_BUBBLE={ENABLE_CHAT_BUBBLE}, "
        f"ENABLE_AMIRA_CARD_BUTTON={ENABLE_AMIRA_CARD_BUTTON}, "
        f"ENABLE_AMIRA_AUTOMATION_BUTTON={ENABLE_AMIRA_AUTOMATION_BUTTON}"
    )
    if not ENABLE_CHAT_BUBBLE and not ENABLE_AMIRA_CARD_BUTTON and not ENABLE_AMIRA_AUTOMATION_BUTTON:
        logger.info("Chat bubble: Bubble, card button and automation button disabled, cleaning up")
        cleanup_chat_bubble()
        return

    try:
        import chat_bubble

        ingress_url = get_addon_ingress_url()
        if not ingress_url:
            logger.warning("Chat bubble: Cannot register — ingress URL not available")
            return

        # Build split scripts
        js_content = chat_bubble.get_chat_bubble_js(
            ingress_url=ingress_url,
            language=LANGUAGE,
            show_bubble=ENABLE_CHAT_BUBBLE,
            show_card_button=ENABLE_AMIRA_CARD_BUTTON,
            show_automation_button=ENABLE_AMIRA_AUTOMATION_BUTTON,
        )
        # Phase 1 split artifacts (kept in sync, not primary resource yet).
        # Keep the first loaded module fully featured: the bubble script has a
        # global anti-double-injection guard, so later split modules may not run.
        # If this module disables card/automation buttons, those UIs never appear.
        js_bubble_content = chat_bubble.get_chat_bubble_js(
            ingress_url=ingress_url,
            language=LANGUAGE,
            show_bubble=ENABLE_CHAT_BUBBLE,
            show_card_button=ENABLE_AMIRA_CARD_BUTTON,
            show_automation_button=ENABLE_AMIRA_AUTOMATION_BUTTON,
        )
        js_card_content = chat_bubble.get_chat_bubble_js(
            ingress_url=ingress_url,
            language=LANGUAGE,
            show_bubble=False,
            show_card_button=ENABLE_AMIRA_CARD_BUTTON,
            show_automation_button=False,
        )
        js_auto_content = chat_bubble.get_chat_bubble_js(
            ingress_url=ingress_url,
            language=LANGUAGE,
            show_bubble=False,
            show_card_button=False,
            show_automation_button=ENABLE_AMIRA_AUTOMATION_BUTTON,
        )

        # Save split scripts to /config/www/ (served by HA at /local/)
        www_dir = os.path.join(HA_CONFIG_DIR, "www")
        os.makedirs(www_dir, exist_ok=True)
        split_paths = {
            "bubble": os.path.join(www_dir, "ha-claude-chat-bubble.bubble.js"),
            "card": os.path.join(www_dir, "ha-claude-chat-bubble.card.js"),
            "automation": os.path.join(www_dir, "ha-claude-chat-bubble.automation.js"),
        }
        with open(split_paths["bubble"], "w", encoding="utf-8") as sf:
            sf.write(js_bubble_content)
        with open(split_paths["card"], "w", encoding="utf-8") as sf:
            sf.write(js_card_content)
        with open(split_paths["automation"], "w", encoding="utf-8") as sf:
            sf.write(js_auto_content)
        # Build loader as primary Lovelace resource (stable URL)
        import hashlib
        bubble_h = hashlib.md5(js_bubble_content.encode()).hexdigest()[:8]
        card_h = hashlib.md5(js_card_content.encode()).hexdigest()[:8]
        auto_h = hashlib.md5(js_auto_content.encode()).hexdigest()[:8]
        logger.info(
            "Chat bubble: split modules saved "
            f"(bubble={len(js_bubble_content)} chars h={bubble_h}, "
            f"card={len(js_card_content)} chars h={card_h}, "
            f"automation={len(js_auto_content)} chars h={auto_h})"
        )
        loader_js = f"""(function(){{
  try {{
    if (window.__HA_CLAUDE_BUBBLE_LOADER__) return;
    window.__HA_CLAUDE_BUBBLE_LOADER__ = true;
    var parts = [
      '/local/ha-claude-chat-bubble.bubble.js?v={VERSION}&h={bubble_h}',
      '/local/ha-claude-chat-bubble.card.js?v={VERSION}&h={card_h}',
      '/local/ha-claude-chat-bubble.automation.js?v={VERSION}&h={auto_h}'
    ];
    function loadOne(src) {{
      return new Promise(function(resolve) {{
        var s = document.createElement('script');
        s.src = src;
        s.async = false;
        s.dataset.amiraPart = src;
        s.onload = function() {{ resolve(); }};
        s.onerror = function() {{ resolve(); }};
        (document.head || document.documentElement || document.body).appendChild(s);
      }});
    }}
    (async function() {{
      for (var i = 0; i < parts.length; i++) await loadOne(parts[i]);
    }})();
  }} catch (e) {{
    console.error('[Amira loader] error:', e);
  }}
}})();
"""
        js_path = os.path.join(www_dir, "ha-claude-chat-bubble.js")
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(loader_js)
        logger.info(
            "Chat bubble: loader JS saved "
            f"({js_path}, {len(loader_js)} chars, "
            f"default_ctx=all_modules)"
        )

        # Register as Lovelace resource via websocket
        content_hash = hashlib.md5(loader_js.encode()).hexdigest()[:8]
        resource_url = "/local/ha-claude-chat-bubble.js"
        cache_bust_url = f"{resource_url}?v={VERSION}&h={content_hash}"
        registration_ok = False
        try:
            ws_result = call_ha_websocket("lovelace/resources/list")
            # Check if WS call succeeded
            if isinstance(ws_result, dict) and ws_result.get("success") is False:
                logger.warning(f"Chat bubble: lovelace/resources/list failed: {ws_result}")
                # Might be YAML mode — still set registered to avoid retrying every request
                logger.info(f"Chat bubble: If using YAML mode, add to configuration.yaml: resources: [{{ url: '{resource_url}', type: js }}]")
                registration_ok = True  # JS file is saved, user can add manually
            else:
                resources = ws_result
                if isinstance(ws_result, dict):
                    resources = ws_result.get("result", [])
                already_registered = False
                duplicates = []
                if isinstance(resources, list):
                    for res in resources:
                        if isinstance(res, dict) and res.get("url", "").startswith("/local/ha-claude-chat-bubble"):
                            if not already_registered:
                                already_registered = True
                                logger.info(f"Chat bubble: Found existing resource id={res.get('id')}, url={res.get('url')}")
                                try:
                                    upd = call_ha_websocket(
                                        "lovelace/resources/update",
                                        resource_id=res["id"],
                                        url=cache_bust_url,
                                        res_type="js",
                                    )
                                    if isinstance(upd, dict) and upd.get("success") is False:
                                        logger.warning(f"Chat bubble: resource update failed: {upd}")
                                    else:
                                        logger.info(f"Chat bubble: Updated Lovelace resource ({cache_bust_url})")
                                        registration_ok = True
                                except Exception as e:
                                    logger.warning(f"Chat bubble: Could not update resource: {e}")
                            else:
                                duplicates.append(res)
                    for dup in duplicates:
                        try:
                            call_ha_websocket("lovelace/resources/delete", resource_id=dup["id"])
                            logger.info(f"Chat bubble: Removed duplicate resource id={dup.get('id')}")
                        except Exception:
                            pass

                if not already_registered:
                    create_result = call_ha_websocket(
                        "lovelace/resources/create",
                        url=cache_bust_url,
                        res_type="js",
                    )
                    if isinstance(create_result, dict) and create_result.get("success") is False:
                        logger.error(f"Chat bubble: Failed to create Lovelace resource: {create_result}")
                        logger.info(f"Chat bubble: Add manually in HA -> Settings -> Dashboards -> Resources: {resource_url}")
                        # JS file is saved, user can add manually
                        registration_ok = True
                    else:
                        logger.info(f"Chat bubble: Registered Lovelace resource ({cache_bust_url}) -> {create_result}")
                        registration_ok = True
                elif not registration_ok:
                    # already_registered but update might have failed
                    registration_ok = True
        except Exception as e:
            logger.warning(f"Chat bubble: Could not register Lovelace resource: {e}")
            logger.info(f"Chat bubble: Add manually in HA -> Settings -> Dashboards -> Resources: {resource_url}")

        # Only mark as registered if we succeeded or the file is at least written
        if registration_ok:
            _chat_bubble_registered = True
            logger.info(
                "Chat bubble: Setup complete "
                f"(bubble={ENABLE_CHAT_BUBBLE}, card_btn={ENABLE_AMIRA_CARD_BUTTON}, "
                f"automation_btn={ENABLE_AMIRA_AUTOMATION_BUTTON}, modular_loader=True)"
            )
        else:
            logger.warning("Chat bubble: JS file saved but Lovelace registration may have failed — will retry on next call")

    except Exception as e:
        logger.error(f"Chat bubble setup failed: {e}")


def cleanup_chat_bubble():
    """Remove chat bubble Lovelace resource and JS file.

    Called at startup when ENABLE_CHAT_BUBBLE is False to clean up
    previous registrations, so the bubble disappears after disabling.
    """
    try:
        ws_result = call_ha_websocket("lovelace/resources/list")
        resources = ws_result
        if isinstance(ws_result, dict):
            resources = ws_result.get("result", [])
        removed = 0
        if isinstance(resources, list):
            for res in resources:
                if isinstance(res, dict) and res.get("url", "").startswith("/local/ha-claude-chat-bubble"):
                    try:
                        call_ha_websocket("lovelace/resources/delete", resource_id=res["id"])
                        removed += 1
                        logger.info(f"Chat bubble cleanup: Removed Lovelace resource id={res.get('id')}")
                    except Exception as e:
                        logger.warning(f"Chat bubble cleanup: Could not remove resource: {e}")

        js_files = [
            os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.js"),
            os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.bubble.js"),
            os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.card.js"),
            os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.automation.js"),
        ]
        deleted_any = False
        for js_path in js_files:
            if os.path.isfile(js_path):
                os.remove(js_path)
                deleted_any = True
                logger.info(f"Chat bubble cleanup: Deleted {js_path}")

        if removed or deleted_any:
            logger.info("Chat bubble cleanup: Done")
    except Exception as e:
        logger.warning(f"Chat bubble cleanup failed: {e}")


@app.route('/api/bubble/status', methods=['GET'])
def api_bubble_status():
    """Diagnostic endpoint: check chat bubble registration status."""
    loader_path = os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.js")
    module_paths = {
        "loader": loader_path,
        "bubble": os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.bubble.js"),
        "card": os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.card.js"),
        "automation": os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.automation.js"),
    }
    module_files = {}
    for name, p in module_paths.items():
        ex = os.path.isfile(p)
        module_files[name] = {
            "path": p,
            "exists": ex,
            "size_bytes": (os.path.getsize(p) if ex else 0),
        }

    ingress_url = get_addon_ingress_url()

    # Check Lovelace resource registration
    resource_info = None
    try:
        ws_result = call_ha_websocket("lovelace/resources/list")
        if isinstance(ws_result, dict) and ws_result.get("success") is False:
            resource_info = {"error": "resources API unavailable (YAML mode?)", "raw": str(ws_result)}
        else:
            resources = ws_result
            if isinstance(ws_result, dict):
                resources = ws_result.get("result", [])
            found = []
            if isinstance(resources, list):
                for res in resources:
                    if isinstance(res, dict) and "ha-claude-chat-bubble" in res.get("url", ""):
                        found.append({"id": res.get("id"), "url": res.get("url"), "type": res.get("type")})
            resource_info = {"registered": len(found) > 0, "entries": found, "total_resources": len(resources) if isinstance(resources, list) else 0}
    except Exception as e:
        resource_info = {"error": str(e)}

    return jsonify({
        "bubble_enabled": ENABLE_CHAT_BUBBLE,
        "card_button_enabled": ENABLE_AMIRA_CARD_BUTTON,
        "automation_button_enabled": ENABLE_AMIRA_AUTOMATION_BUTTON,
        "registered_flag": _chat_bubble_registered,
        "ingress_url": ingress_url or "(empty)",
        "js_file": module_files["loader"],  # backward-compat for old UI
        "module_files": module_files,
        "lovelace_resource": resource_info,
        "hint": "After registering, do a FULL browser refresh (Ctrl+Shift+R) on your HA dashboard. Loader + 3 modules must all be present.",
    })


@app.route('/api/bubble/register', methods=['POST'])
def api_bubble_register():
    """Force re-registration of the chat bubble Lovelace resource."""
    global _chat_bubble_registered
    _chat_bubble_registered = False
    # Clear ingress URL cache so it's fetched fresh
    global _ingress_url_cache
    _ingress_url_cache = None
    setup_chat_bubble()
    return jsonify({"ok": _chat_bubble_registered, "message": "Re-registration attempted. Check /api/bubble/status for details."})


@app.route('/api/set_model', methods=['POST'])
def api_set_model():
    global AI_PROVIDER, AI_MODEL, SELECTED_MODEL, SELECTED_PROVIDER, ai_client

    data = request.json or {}

    if "provider" in data:
        AI_PROVIDER = data["provider"]

        # When changing provider without specifying a model: reset selection and use provider default.
        if "model" not in data:
            SELECTED_MODEL = ""
            SELECTED_PROVIDER = ""
            default_model = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("model")
            if default_model:
                AI_MODEL = default_model
            logger.info(f"Provider changed to {AI_PROVIDER}, reset to default model: {AI_MODEL}")

    if "model" in data:
        normalized = normalize_model_name(data["model"])

        # Solo Anthropic, OpenAI e Google hanno modelli esclusivi propri.
        # Tutti gli altri provider (NVIDIA, GitHub, Groq, Mistral, OpenRouter, SiliconFlow, ecc.)
        # ospitano modelli di vendor diversi → accettare qualsiasi modello selezionato dall'utente
        # per quel provider senza checks di compatibilità.
        _STRICT_PROVIDERS = {"anthropic", "openai", "google"}

        # Enforce compatibility only for strict single-vendor providers.
        if "provider" in data and AI_PROVIDER in _STRICT_PROVIDERS:
            model_provider = get_model_provider(normalized)
            if model_provider not in ("unknown", AI_PROVIDER):
                SELECTED_MODEL = ""
                SELECTED_PROVIDER = ""
                default_model = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("model")
                if default_model:
                    AI_MODEL = default_model
                logger.warning(
                    f"Ignoring incompatible model '{normalized}' for provider '{AI_PROVIDER}'. Using default '{AI_MODEL}'."
                )
            else:
                AI_MODEL = normalized
                SELECTED_MODEL = normalized
                SELECTED_PROVIDER = AI_PROVIDER
        else:
            AI_MODEL = normalized
            SELECTED_MODEL = normalized
            SELECTED_PROVIDER = AI_PROVIDER

    logger.info(f"Runtime model changed → {AI_PROVIDER} / {AI_MODEL}")

    # Reinitialize client so provider switches don't keep a stale client instance
    try:
        initialize_ai_client()
    except Exception as e:
        logger.exception(f"Failed to reinitialize AI client after model/provider change: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to initialize AI client for selected provider/model",
            "provider": AI_PROVIDER,
            "model": AI_MODEL,
        }), 500

    # Persist selection so it becomes the single source of truth
    try:
        save_runtime_selection(AI_PROVIDER, AI_MODEL)
    except Exception:
        pass

    # Clear model fallback cooldown for the new provider (fresh start)
    if MODEL_FALLBACK_AVAILABLE:
        try:
            model_fallback.clear_cooldown(AI_PROVIDER)
        except Exception:
            pass

    # Compute tool tier for the new provider/model so the UI can warn the user
    try:
        _tier = tools._get_tool_tier()
        _TIER_MISSING = {
            # compact: includes create/update/preview automation + create_dashboard, but lacks
            # script management, dashboard editing, file access, delete ops, and many advanced tools
            "compact": ["update_dashboard", "delete_automation", "create_script", "update_script",
                        "list_config_files", "read_config_file", "get_scripts", "get_dashboards", "get_areas"],
            # extended: adds file/listing tools over compact but still lacks write-heavy ops
            "extended": ["update_dashboard", "delete_automation", "create_script", "update_script"],
        }
        _missing = _TIER_MISSING.get(_tier, [])
        if _tier in ("compact", "extended") and _missing:
            _tpl = get_lang_text("warn_tier_limited") or "\u26a0\ufe0f Limited mode ({tier}): advanced features not available ({missing}). Switch to a more capable model."
            _tier_warning_msg = _tpl.format(tier=_tier, missing=", ".join(_missing))
        else:
            _tier_warning_msg = ""
    except Exception:
        _tier = "full"
        _missing = []
        _tier_warning_msg = ""

    # Build response with agent identity if available
    resp = {
        "success": True,
        "provider": AI_PROVIDER,
        "model": AI_MODEL,
        "tier": _tier,
        "tier_limited": _tier in ("compact", "extended"),
        "tier_missing_tools": _missing,
        "tier_warning_msg": _tier_warning_msg,
    }
    if AGENT_CONFIG_AVAILABLE:
        try:
            mgr = agent_config.get_agent_manager()
            identity = mgr.resolve_identity()
            resp["agent_identity"] = {
                "name": identity.name,
                "emoji": identity.emoji,
            }
        except Exception:
            pass

    return jsonify(resp)


@app.route('/api/bubble/device-id', methods=['POST'])
def api_bubble_device_id():
    """Set or generate a unique device ID for bubble device-specific configuration.
    
    This endpoint allows storing a device identifier in localStorage so that
    custom bubble visibility rules can identify specific phones/tablets/devices.
    
    Body (optional): {"device_id": "my-phone", "device_name": "Eleonor's iPhone"}
    Returns: {"device_id": "...", "device_type": "phone|tablet|desktop"}
    """
    try:
        data = request.get_json() or {}
        device_id = data.get("device_id", "").strip()
        device_name = data.get("device_name", "").strip()
        fingerprint = str(data.get("fingerprint") or "").strip()
        
        # Generate device ID if not provided
        if not device_id:
            import hashlib
            import uuid
            # Prefer deterministic ID from provided fingerprint
            if fingerprint:
                device_id = hashlib.md5(fingerprint.encode("utf-8")).hexdigest()[:12]
            else:
                device_id = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:12]
        
        # Validate: only allow alphanum, dash, underscore
        if not all(c.isalnum() or c in '-_' for c in device_id):
            return jsonify({"success": False, "error": "Device ID can only contain alphanumeric, dash, and underscore"}), 400
        
        # Log device registration (for admin purposes)
        logger.info(f"Bubble device registered: id={device_id}, name={device_name}")
        
        return jsonify({
            "success": True,
            "device_id": device_id,
            "device_name": device_name or "Device",
            "instruction": "Store this device_id in your browser's localStorage as 'ha-claude-device-id' to enable device-specific bubble control"
        }), 200
    except Exception as e:
        logger.error(f"Error setting device ID: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/bubble/config', methods=['GET'])
def api_bubble_config():
    """Get current bubble configuration and device visibility rules.
    
    Returns information about how the bubble is configured across devices.
    """
    try:
        return jsonify({
            "success": True,
            "enabled": ENABLE_CHAT_BUBBLE
        }), 200
    except Exception as e:
        logger.error(f"Error getting bubble config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/bubble/devices', methods=['GET'])
def api_bubble_devices_list():
    """Get list of discovered devices and their bubble visibility settings.
    
    Returns all devices that have accessed the bubble, with their settings.
    Format: {"device_id": {"name": "...", "device_type": "phone|tablet|desktop", "enabled": true, "last_seen": "..."}}
    """
    try:
        devices = load_device_config()
        return jsonify({
            "success": True,
            "devices": devices
        }), 200
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/bubble/devices', methods=['POST'])
def api_bubble_devices_register():
    """Register or update a device in the bubble tracking system.
    
    Browser calls this on first bubble load to register itself.
    Body: {"device_id": "...", "device_name": "...", "device_type": "phone|tablet|desktop"}
    """
    try:
        data = request.get_json() or {}
        device_id = (data.get("device_id") or "").strip()
        device_name = (data.get("device_name") or "").strip()
        device_type = (data.get("device_type") or "desktop").lower()
        fingerprint = str(data.get("fingerprint") or "").strip()
        if len(fingerprint) > 512:
            fingerprint = fingerprint[:512]
        
        if not device_id or len(device_id) < 4:
            return jsonify({"success": False, "error": "Invalid device_id"}), 400
        
        if device_type not in ("phone", "tablet", "desktop"):
            device_type = "desktop"
        
        devices = load_device_config()

        # Canonicalize by fingerprint to avoid duplicate registrations of same browser/device
        canonical_id = None
        if fingerprint:
            for did, meta in devices.items():
                if not isinstance(meta, dict):
                    continue
                if (meta.get("fingerprint") == fingerprint) and (meta.get("device_type") == device_type):
                    canonical_id = did
                    break
        if canonical_id and canonical_id != device_id:
            logger.info(f"Device dedupe by fingerprint: {device_id} -> {canonical_id}")
            device_id = canonical_id
        
        # If device doesn't exist yet, add it with default enabled state based on mode
        is_new_device = device_id not in devices
        if is_new_device:
            # Device always enabled by default (management from UI)
            devices[device_id] = {
                "name": device_name or f"{device_type.capitalize()}",
                "device_type": device_type,
                "fingerprint": fingerprint,
                "enabled": True,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
            }
        else:
            # Update last_seen and name if provided
            devices[device_id]["last_seen"] = datetime.now().isoformat()
            if device_name:
                devices[device_id]["name"] = device_name
            if fingerprint and not devices[device_id].get("fingerprint"):
                devices[device_id]["fingerprint"] = fingerprint
        
        save_device_config(devices)
        if is_new_device:
            logger.info(f"Device registered: {device_id} ({device_type})")
        else:
            logger.debug(f"Device updated: {device_id}")
        
        # Return whether bubble should be enabled for this device
        is_enabled = devices[device_id].get("enabled", False)
        
        return jsonify({
            "success": True,
            "device_id": device_id,
            "enabled": is_enabled,
            "message": f"Device registered (enabled: {is_enabled})"
        }), 200
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/bubble/devices/<device_id>', methods=['PATCH'])
def api_bubble_device_update(device_id):
    """Enable or disable bubble for a specific device.
    
    Body: {"enabled": true/false, "name": "..."}
    """
    try:
        device_id = device_id.strip()
        data = request.get_json() or {}
        
        devices = load_device_config()
        if device_id not in devices:
            return jsonify({"success": False, "error": "Device not found"}), 404
        
        if "enabled" in data:
            if data["enabled"] is None:
                # Toggle: invert current state
                devices[device_id]["enabled"] = not devices[device_id].get("enabled", False)
            else:
                devices[device_id]["enabled"] = bool(data["enabled"])
        
        if "name" in data and data["name"]:
            devices[device_id]["name"] = str(data["name"]).strip()
        
        save_device_config(devices)
        logger.info(f"Device updated: {device_id} (enabled: {devices[device_id].get('enabled')})")
        
        return jsonify({
            "success": True,
            "device": devices[device_id]
        }), 200
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/bubble/devices/<device_id>', methods=['DELETE'])
def api_bubble_device_delete(device_id):
    """Remove a device from tracking.
    
    The device will re-register on next access.
    """
    try:
        device_id = device_id.strip()
        devices = load_device_config()
        
        if device_id in devices:
            del devices[device_id]
            save_device_config(devices)
            logger.info(f"Device deleted: {device_id}")
            return jsonify({"success": True, "message": f"Device '{device_id}' removed"}), 200
        
        return jsonify({"success": False, "error": "Device not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get current runtime configuration."""
    return jsonify({
        "success": True,
        "config": {
            "ai_provider": AI_PROVIDER,
            "ai_model": get_active_model(),
            "language": LANGUAGE,
            "debug_mode": DEBUG_MODE,
            "enable_file_access": ENABLE_FILE_ACCESS,
            "version": VERSION
        }
    })


@app.route('/api/config', methods=['POST'])
def api_set_config():
    """Update runtime configuration dynamically."""
    global LANGUAGE, DEBUG_MODE, ENABLE_FILE_ACCESS
    
    try:
        data = request.get_json()
        updated = []
        
        # Update language
        if 'language' in data:
            new_lang = data['language'].lower()
            if new_lang in ['en', 'it', 'es', 'fr']:
                LANGUAGE = new_lang
                updated.append(f"language={LANGUAGE}")
                logger.info(f"Language changed to: {LANGUAGE}")
            else:
                return jsonify({"success": False, "error": f"Invalid language: {new_lang}. Supported: en, it, es, fr"}), 400
        
        # Update debug mode
        if 'debug_mode' in data:
            DEBUG_MODE = bool(data['debug_mode'])
            updated.append(f"debug_mode={DEBUG_MODE}")
            logger.info(f"Debug mode changed to: {DEBUG_MODE}")
            logging.getLogger().setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
        
        # Update file access
        if 'enable_file_access' in data:
            ENABLE_FILE_ACCESS = bool(data['enable_file_access'])
            updated.append(f"enable_file_access={ENABLE_FILE_ACCESS}")
            logger.info(f"File access changed to: {ENABLE_FILE_ACCESS}")
        
        return jsonify({
            "success": True,
            "message": f"Configuration updated: {', '.join(updated)}",
            "config": {
                "language": LANGUAGE,
                "debug_mode": DEBUG_MODE,
                "enable_file_access": ENABLE_FILE_ACCESS
            }
        })
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/system_prompt', methods=['GET'])
def api_get_system_prompt():
    """Get the current system prompt."""
    try:
        prompt = tools.get_system_prompt()
        return jsonify({
            "success": True,
            "system_prompt": prompt,
            "length": len(prompt)
        })
    except Exception as e:
        logger.error(f"Error getting system prompt: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/system_prompt', methods=['POST'])
def api_set_system_prompt():
    """Override the system prompt dynamically. Use 'reset' to restore default."""
    global CUSTOM_SYSTEM_PROMPT
    
    try:
        data = request.get_json()
        new_prompt = data.get('system_prompt')
        
        if not new_prompt:
            return jsonify({"success": False, "error": "system_prompt parameter required"}), 400
        
        if new_prompt.lower() == 'reset':
            CUSTOM_SYSTEM_PROMPT = None
            _persist_custom_system_prompt_to_disk(None)
            logger.info("System prompt reset to default")
            return jsonify({
                "success": True,
                "message": "System prompt reset to default",
                "system_prompt": tools.get_system_prompt()
            })
        
        CUSTOM_SYSTEM_PROMPT = new_prompt
        _persist_custom_system_prompt_to_disk(CUSTOM_SYSTEM_PROMPT)
        logger.info(f"System prompt overridden ({len(new_prompt)} chars)")
        
        return jsonify({
            "success": True,
            "message": "System prompt updated successfully",
            "system_prompt": CUSTOM_SYSTEM_PROMPT,
            "length": len(CUSTOM_SYSTEM_PROMPT)
        })
    except Exception as e:
        logger.error(f"Error setting system prompt: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint."""
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        logger.warning(
            f"Invalid JSON body for /api/chat (content_type={request.content_type}, len={request.content_length})",
            extra={"context": "REQUEST"},
        )
        return jsonify({"error": "Invalid JSON"}), 400
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    if not message:
        return jsonify({"error": "Empty message"}), 400
    logger.chat(f"📩 [{AI_PROVIDER}]: {_strip_context_for_log(message)}")
    global _last_sync_usage
    _last_sync_usage = {}  # Reset before call
    response_text = chat_with_ai(message, session_id)
    # Enrich usage data with cost breakdown (same pipeline as streaming)
    usage_data = None
    if _last_sync_usage:
        try:
            norm = pricing.normalize_usage(_last_sync_usage)
            input_tokens = norm["input_tokens"]
            output_tokens = norm["output_tokens"]
            cache_read_tokens = norm["cache_read_tokens"]
            cache_write_tokens = norm["cache_write_tokens"]
            model_name = _last_sync_usage.get("model") or get_active_model()
            provider_name = _last_sync_usage.get("provider") or AI_PROVIDER
            cost_bd = pricing.calculate_cost_breakdown(
                model_name, provider_name,
                input_tokens, output_tokens,
                cache_read_tokens, cache_write_tokens,
                COST_CURRENCY,
            )
            usage_data = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read_tokens,
                "cache_write_tokens": cache_write_tokens,
                "cost": cost_bd["total_cost"],
                "cost_breakdown": {
                    "input": cost_bd["input_cost"],
                    "output": cost_bd["output_cost"],
                    "cache_read": cost_bd["cache_read_cost"],
                    "cache_write": cost_bd["cache_write_cost"],
                },
                "currency": COST_CURRENCY,
                "model": model_name,
                "provider": provider_name,
            }
            # Log cost
            _cost_val = cost_bd["total_cost"]
            _sym = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}.get(COST_CURRENCY, COST_CURRENCY)
            if _cost_val > 0:
                logger.info(f"💰 {provider_name}/{model_name}: {input_tokens} in + {output_tokens} out → {_sym}{_cost_val:.6f}")
            else:
                logger.info(f"💰 {provider_name}/{model_name}: {input_tokens} in + {output_tokens} out → free")
            # Persist to disk
            try:
                from usage_tracker import get_tracker
                get_tracker().record(usage_data)
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Cost enrichment for /api/chat failed: {e}")
    result = {"response": response_text}
    if usage_data:
        result["usage"] = usage_data
    return jsonify(result), 200


@app.route('/api/chat/stream', methods=['POST'])
def api_chat_stream():
    """Streaming chat endpoint using Server-Sent Events with image support."""
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        logger.warning(
            f"Invalid JSON body for /api/chat/stream (content_type={request.content_type}, len={request.content_length})",
            extra={"context": "REQUEST"},
        )
        return jsonify({"error": "Invalid JSON"}), 400
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    image_data = data.get("image", None)  # Base64 image data
    read_only = data.get("read_only", False)  # Read-only mode flag
    voice_mode = data.get("voice_mode", False)  # Voice mode: short spoken responses
    if not message:
        return jsonify({"error": "Empty message"}), 400
    if image_data:
        logger.chat(f"📩 [{AI_PROVIDER}] with image: {message[:50]}...")
    else:
        log_msg = _strip_context_for_log(message)
        logger.chat(f"📩 [{AI_PROVIDER}]: {log_msg}")
    if read_only:
        logger.info(f"Read-only mode active for session {session_id}")
    abort_streams[session_id] = False  # Reset abort flag

    def generate():
        import threading as _threading
        import queue as _queue
        q: _queue.Queue = _queue.Queue()
        _SENTINEL = object()

        def _producer():
            try:
                for event in stream_chat_with_ai(message, session_id, image_data, read_only=read_only, voice_mode=voice_mode):
                    q.put(("event", event))
            except Exception as exc:
                logger.error(
                    f"❌ Stream error in stream_chat_with_ai: {type(exc).__name__}: {exc}",
                    extra={"context": "REQUEST"},
                )
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}", extra={"context": "REQUEST"})
                q.put(("error", exc))
            finally:
                q.put(("done", _SENTINEL))

        t = _threading.Thread(target=_producer, daemon=True)
        t.start()

        while True:
            try:
                kind, val = q.get(timeout=10)
            except _queue.Empty:
                # Keep connection alive while waiting for slow providers (e.g. NVIDIA)
                yield ": keep-alive\n\n"
                continue

            if kind == "event":
                yield f"data: {json.dumps(val, ensure_ascii=False)}\n\n"
            elif kind == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': str(val)}, ensure_ascii=False)}\n\n"
                break
            else:  # "done"
                break

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/api/chat/abort', methods=['POST'])
def api_chat_abort():
    """Abort a running stream."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")
    abort_streams[session_id] = True
    logger.info(f"Abort requested for session {session_id}")
    return jsonify({"status": "abort_requested"}), 200


# moved to routes/memory_routes.py: api_memory_clear


# ============ MCP (Model Context Protocol) Endpoints ============

def _load_mcp_config_servers() -> Dict[str, Dict[str, Any]]:
    """Load MCP server config as a flat dict: {server_name: config}."""
    mcp_json_path = MCP_CONFIG_FILE or "/config/amira/mcp_config.json"
    if not os.path.isfile(mcp_json_path):
        return {}
    with open(mcp_json_path, encoding="utf-8") as f:
        raw_cfg = json.load(f) or {}
    if "mcpServers" in raw_cfg and isinstance(raw_cfg["mcpServers"], dict):
        raw_cfg = raw_cfg["mcpServers"]
    if not isinstance(raw_cfg, dict):
        return {}
    return {str(k): v for k, v in raw_cfg.items() if isinstance(v, dict)}


# moved to routes/mcp_routes.py: api_mcp_servers_list, api_mcp_server_status,
# api_mcp_server_reconnect, api_mcp_server_start, api_mcp_server_stop,
# api_mcp_all_tools, api_mcp_diagnostics, api_mcp_test_tool,
# api_mcp_install, api_mcp_server_tools


# ============ Nanobot-Inspired Features Endpoints ============

# moved to routes/analytics_routes.py: api_semantic_cache_stats, api_semantic_cache_clear,
# api_tool_optimizer_stats, api_quality_metrics_stats, api_image_stats, api_image_analyze


# ============ Scheduled Tasks Endpoints ============

@app.route('/api/scheduled/stats', methods=['GET'])
def api_scheduled_stats():
    """Get scheduled tasks statistics."""
    try:
        if not SCHEDULED_TASKS_AVAILABLE:
            return jsonify({"status": "error", "message": "Scheduled tasks not available"}), 501
        scheduler = scheduled_tasks.get_scheduler()
        return jsonify({"status": "success", "scheduler_stats": scheduler.get_stats()}), 200
    except Exception as e:
        logger.error(f"Scheduled stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/scheduled/tasks', methods=['GET'])
def api_scheduled_tasks_list():
    """List all registered scheduled tasks."""
    try:
        if not SCHEDULED_TASKS_AVAILABLE:
            return jsonify({"status": "error", "message": "Scheduled tasks not available"}), 501
        scheduler = scheduled_tasks.get_scheduler()
        tasks = [
            {
                "task_id": t.task_id,
                "name": t.name,
                "cron": t.cron_expression,
                "description": t.description,
                "enabled": t.enabled,
                "run_count": t.run_count,
                "last_run": t.last_run,
                "next_run": t.next_run,
                "message": t.message,
                "builtin": t.builtin,
            }
            for t in scheduler.tasks.values()
        ]
        return jsonify({"status": "success", "tasks": tasks, "count": len(tasks)}), 200
    except Exception as e:
        logger.error(f"Scheduled tasks list error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/scheduled/tasks', methods=['POST'])
def api_scheduled_tasks_create():
    """Create a new scheduled task (nanobot-style: cron + message inviato all'agente).
    JSON body: { "name": "...", "cron": "0 9 * * *", "message": "...", "description": "...", "enabled": true }
    """
    try:
        if not SCHEDULED_TASKS_AVAILABLE:
            return jsonify({"status": "error", "message": "Scheduled tasks not available"}), 501
        data = request.json or {}
        name = data.get("name", "").strip()
        cron = data.get("cron", "").strip()
        message = data.get("message", "").strip()
        if not name or not cron or not message:
            return jsonify({"status": "error", "message": "name, cron e message sono obbligatori"}), 400
        task_id = data.get("task_id") or f"task_{uuid.uuid4().hex[:8]}"
        scheduler = scheduled_tasks.get_scheduler()
        if task_id in scheduler.tasks:
            return jsonify({"status": "error", "message": f"Task '{task_id}' esiste già"}), 409
        task = scheduler.add_message_task(
            task_id=task_id, name=name, cron_expression=cron, message=message,
            description=data.get("description", ""), enabled=data.get("enabled", True),
        )
        return jsonify({"status": "success", "task_id": task.task_id,
                        "message": f"Task '{name}' creato ({cron})"}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Scheduled task create error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/scheduled/tasks/<task_id>', methods=['DELETE'])
def api_scheduled_task_delete(task_id):
    """Elimina un task pianificato (non built-in)."""
    try:
        if not SCHEDULED_TASKS_AVAILABLE:
            return jsonify({"status": "error", "message": "Scheduled tasks not available"}), 501
        scheduler = scheduled_tasks.get_scheduler()
        t = scheduler.tasks.get(task_id)
        if t and t.builtin:
            return jsonify({"status": "error", "message": "Impossibile eliminare un task built-in"}), 403
        ok = scheduler.remove_task(task_id)
        if not ok:
            return jsonify({"status": "error", "message": f"Task '{task_id}' non trovato"}), 404
        return jsonify({"status": "success", "message": f"Task '{task_id}' eliminato"}), 200
    except Exception as e:
        logger.error(f"Scheduled task delete error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/scheduled/tasks/<task_id>/toggle', methods=['POST'])
def api_scheduled_task_toggle(task_id):
    """Enable or disable a scheduled task."""
    try:
        if not SCHEDULED_TASKS_AVAILABLE:
            return jsonify({"status": "error", "message": "Scheduled tasks not available"}), 501
        data = request.json or {}
        enabled = data.get("enabled", True)
        scheduler = scheduled_tasks.get_scheduler()
        if task_id not in scheduler.tasks:
            return jsonify({"status": "error", "message": f"Task '{task_id}' not found"}), 404
        scheduler.tasks[task_id].enabled = enabled
        scheduler.save_tasks()
        action = "enabled" if enabled else "disabled"
        return jsonify({"status": "success", "message": f"Task '{task_id}' {action}"}), 200
    except Exception as e:
        logger.error(f"Scheduled task toggle error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============ SchedulerAgent Endpoints ============

@app.route('/api/agent/scheduler', methods=['POST'])
def api_scheduler_agent_chat():
    """Chat con lo SchedulerAgent per creare/elencare/gestire task pianificati in linguaggio naturale.

    JSON body: { "message": "...", "session_id": "..." (optional) }
    """
    try:
        if not SCHEDULER_AGENT_AVAILABLE:
            return jsonify({"status": "error", "message": "SchedulerAgent non disponibile"}), 501
        data = request.json or {}
        user_message = (data.get("message") or "").strip()
        if not user_message:
            return jsonify({"status": "error", "message": "Campo 'message' obbligatorio"}), 400
        session_id = data.get("session_id") or "default"
        reply = scheduler_agent.chat(user_message, session_id=session_id)
        history = scheduler_agent.get_session_history(session_id)
        # Conta solo i messaggi role=user/assistant (non tool_result)
        msg_count = sum(
            1 for m in history
            if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)
        )
        return jsonify({
            "status": "success",
            "reply": reply,
            "session_id": session_id,
            "message_count": len(history),
        }), 200
    except Exception as e:
        logger.error(f"SchedulerAgent chat error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/agent/scheduler/sessions', methods=['GET'])
def api_scheduler_agent_sessions():
    """Elenca tutte le sessioni attive dello SchedulerAgent."""
    try:
        if not SCHEDULER_AGENT_AVAILABLE:
            return jsonify({"status": "error", "message": "SchedulerAgent non disponibile"}), 501
        sessions = scheduler_agent.list_sessions()
        return jsonify({"status": "success", "sessions": sessions, "count": len(sessions)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/agent/scheduler/session/<session_id>', methods=['DELETE'])
def api_scheduler_agent_clear_session(session_id):
    """Cancella la cronologia di una sessione SchedulerAgent."""
    try:
        if not SCHEDULER_AGENT_AVAILABLE:
            return jsonify({"status": "error", "message": "SchedulerAgent non disponibile"}), 501
        scheduler_agent.clear_session(session_id)
        return jsonify({"status": "success", "message": f"Sessione '{session_id}' cancellata"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============ Browser Console Errors Endpoint ============

# moved to routes/system_routes.py: api_browser_errors_post, api_browser_errors_get


# ============ Agent / Catalog / Fallback Endpoints ============

# moved to routes/agents_routes.py: api_agents_list, api_agents_create, api_agent_get,
# api_agent_update, api_agent_delete, api_agent_set_active, api_agent_channels_get,
# api_agent_channels_set, api_agent_defaults_get, api_agent_defaults_update


# moved to routes/catalog_routes.py: api_catalog_stats, api_catalog_models


@app.route('/api/fallback/stats', methods=['GET'])
def api_fallback_stats():
    """Get model fallback system statistics (cooldowns, etc.)."""
    if not MODEL_FALLBACK_AVAILABLE:
        return jsonify({"success": False, "error": "Model fallback not available"}), 501
    try:
        stats = model_fallback.get_fallback_stats()
        return jsonify({"success": True, "fallback": stats}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/fallback/clear', methods=['POST'])
def api_fallback_clear():
    """Clear all cooldowns in the model fallback system."""
    if not MODEL_FALLBACK_AVAILABLE:
        return jsonify({"success": False, "error": "Model fallback not available"}), 501
    try:
        provider = (request.get_json() or {}).get("provider")
        if provider:
            model_fallback.clear_cooldown(provider)
            msg = f"Cooldown cleared for '{provider}'"
        else:
            model_fallback.clear_all_cooldowns()
            msg = "All cooldowns cleared"
        logger.info(f"Fallback: {msg}")
        return jsonify({"success": True, "message": msg}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ Voice Transcription Endpoints ============

# moved to routes/voice_routes.py: api_voice_stats, api_voice_transcribe, api_voice_tts, api_voice_tts_providers


# ============ Messaging Integration Endpoints ============

@app.route('/api/messaging/stats', methods=['GET'])
def api_messaging_stats():
    """Get messaging system statistics."""
    try:
        from messaging import get_messaging_manager
        mgr = get_messaging_manager()
        stats = mgr.get_stats()
        return jsonify({
            "status": "success",
            "messaging_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Messaging stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def _ai_banner() -> str:
    """Return a short intro line showing the active AI provider and model."""
    provider = AI_PROVIDER
    model = get_active_model()
    display = MODEL_DISPLAY_MAPPING.get(model, model)
    # Use display name if it contains the provider prefix, else build one
    if display and any(display.startswith(p) for p in ("Claude", "OpenAI", "Google", "GitHub", "NVIDIA", "Groq", "Mistral", "DeepSeek", "Ollama")):
        label = display
    else:
        label = f"{provider.replace('_', ' ').title()} • {display or model}"
    return f"🤖 Amira • {label}"


def _strip_markdown_for_telegram(text: str) -> str:
    """Strip Markdown formatting for plain-text Telegram messages."""
    import re
    # Headers → plain text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Bold/italic: **text**, *text*, __text__, _text_
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    # Inline code → plain
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Fenced code blocks → keep content
    text = re.sub(r'```[a-z]*\n?', '', text)
    # Links [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    return text.strip()


@app.route('/api/telegram/message', methods=['POST'])
def api_telegram_message():
    """Process incoming Telegram message and return AI response."""
    if not ENABLE_TELEGRAM:
        return jsonify({"status": "error", "message": "Telegram is disabled"}), 503
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        chat_id = data.get("chat_id")
        text = data.get("text", "").strip()
        logger.chat(f"📩 Telegram from user {user_id}: {text[:60]}")

        if not text:
            return jsonify({"status": "error", "message": "Empty message"}), 400

        # Get AI response — session history is already managed by chat_with_ai
        response_text = ""
        try:
            with _apply_channel_agent("telegram"):
                response_text = chat_with_ai(text, f"telegram_{user_id}")
        except Exception as e:
            logger.error(f"Telegram AI response error: {e}")
            response_text = f"⚠️ Errore: {str(e)[:100]}"

        # Strip Markdown so Telegram can send plain text without parse errors
        response_text = _strip_markdown_for_telegram(response_text)

        # Trim to Telegram's limit
        response_text = response_text[:4096]

        return jsonify({
            "status": "success",
            "response": response_text
        }), 200
    except Exception as e:
        logger.error(f"Telegram message error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/messaging/chats', methods=['GET'])
def api_messaging_chats():
    """Get all messaging chats grouped by channel."""
    try:
        from messaging import get_messaging_manager
        mgr = get_messaging_manager()
        chats = mgr.get_all_chats()
        return jsonify({
            "status": "success",
            "chats": chats
        }), 200
    except Exception as e:
        logger.error(f"Get messaging chats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/messaging/chat/<channel>/<user_id>', methods=['GET', 'DELETE'])
def api_messaging_chat(channel, user_id):
    """Get or delete chat history for a user."""
    try:
        from messaging import get_messaging_manager
        mgr = get_messaging_manager()
        
        if request.method == 'GET':
            history = mgr.get_chat_history(channel, user_id, limit=50)
            return jsonify({
                "status": "success",
                "channel": channel,
                "user_id": user_id,
                "messages": history
            }), 200
        
        elif request.method == 'DELETE':
            mgr.clear_chat(channel, user_id)
            return jsonify({
                "status": "success",
                "message": f"Chat {channel}:{user_id} cleared"
            }), 200
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/whatsapp/webhook', methods=['POST'])
def api_whatsapp_webhook():
    """Handle incoming WhatsApp messages via Twilio webhook."""
    if not ENABLE_WHATSAPP:
        return jsonify({"status": "error", "message": "WhatsApp is disabled"}), 503
    try:
        from whatsapp_bot import get_whatsapp_bot
        from messaging import get_messaging_manager
        
        # Get WhatsApp bot and manager
        whatsapp = get_whatsapp_bot(
            os.getenv("TWILIO_ACCOUNT_SID", ""),
            os.getenv("TWILIO_AUTH_TOKEN", ""),
            os.getenv("TWILIO_WHATSAPP_FROM", "")
        )
        
        if not whatsapp or not whatsapp.enabled:
            return jsonify({"status": "error", "message": "WhatsApp not configured"}), 501
        
        # Validate signature.
        # Behind a reverse proxy (Nginx, Nabu Casa, ngrok) Flask rebuilds the
        # URL from internal headers which may differ from the public URL that
        # Twilio signed.  Reconstruct the public URL using X-Forwarded-* headers
        # when available so the HMAC check uses the same string Twilio used.
        signature = request.headers.get("X-Twilio-Signature", "")
        fwd_proto = request.headers.get("X-Forwarded-Proto", "")
        fwd_host  = request.headers.get("X-Forwarded-Host", "")
        if fwd_proto and fwd_host:
            public_url = (
                f"{fwd_proto}://{fwd_host}"
                f"{request.path}"
                + (f"?{request.query_string.decode()}" if request.query_string else "")
            )
        else:
            public_url = request.url
        if not whatsapp.validate_webhook_signature(
            public_url,
            request.form.to_dict(),
            signature,
        ):
            logger.warning(
                f"WhatsApp webhook signature invalid (url tried: {public_url!r})"
            )
            return jsonify({"status": "error", "message": "Signature invalid"}), 403
        
        # Parse message
        msg = whatsapp.parse_webhook(request.form.to_dict())
        if not msg or not msg.get("text"):
            # Likely a status update or media message, just acknowledge
            return jsonify({"status": "ok"}), 200
        
        from_number = msg.get("from")
        text = msg.get("text")
        
        logger.chat(f"📩 WhatsApp from {from_number}: {text[:50]}...")

        # Check if first message BEFORE adding to history
        mgr = get_messaging_manager()
        is_first = len(mgr.get_chat_history("whatsapp", from_number, limit=1)) == 0

        # Add to chat history
        mgr.add_message("whatsapp", from_number, text, role="user")
        
        # Get AI response — chat_with_ai reuses the persistent whatsapp_{number}
        # session which already accumulates history; no need to inject "Recent context:"
        response_text = ""
        try:
            with _apply_channel_agent("whatsapp"):
                response_text = chat_with_ai(text, f"whatsapp_{from_number}")
        except Exception as e:
            logger.error(f"WhatsApp AI response error: {e}")
            response_text = f"⚠️ Error: {str(e)[:100]}"

        # Prepend AI banner on first message of this conversation
        if is_first:
            response_text = f"{_ai_banner()}\n\n{response_text}"

        # Trim to WhatsApp limit (1600 chars)
        response_text = response_text[:1600]
        
        # Save response and send
        mgr.add_message("whatsapp", from_number, response_text, role="assistant")
        whatsapp.send_message(from_number, response_text)
        
        # Return OK to Twilio (prevents retry)
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------------------------------------------- #
#  HA Conversation Agent endpoint                                              #
#  Compatible with Home Assistant's conversation/process protocol.             #
#  This allows Alexa (via Nabu Casa) or Google Home to route voice requests    #
#  to Amira as a conversation agent.                                           #
# --------------------------------------------------------------------------- #

# moved to routes/conversation_routes.py: api_conversation_process


# --------------------------------------------------------------------------- #
#  Alexa Custom Skill webhook endpoint                                         #
#  Receives Alexa Skill requests (LaunchRequest, IntentRequest, etc.)          #
#  and responds with Alexa-compatible JSON.                                    #
# --------------------------------------------------------------------------- #

@app.route('/api/alexa/webhook', methods=['POST'])
def api_alexa_webhook():
    """Handle incoming Alexa Custom Skill requests.

    Supports:
    - LaunchRequest: greeting
    - IntentRequest with AskAmiraIntent: pass user speech to Amira
    - AMAZON.HelpIntent, AMAZON.StopIntent, AMAZON.CancelIntent
    - SessionEndedRequest: cleanup
    """
    data = request.get_json(silent=True) or {}
    req = data.get("request", {})
    req_type = req.get("type", "")
    session = data.get("session", {})
    session_id = f"alexa_{session.get('sessionId', 'default')}"

    logger.info(f"[Alexa] {req_type} session={session_id[:30]}")

    def _alexa_response(speech: str, end_session: bool = False, reprompt: str = None) -> dict:
        """Build an Alexa-compatible response envelope."""
        resp = {
            "version": "1.0",
            "sessionAttributes": session.get("attributes", {}),
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": speech,
                },
                "shouldEndSession": end_session,
            }
        }
        if reprompt:
            resp["response"]["reprompt"] = {
                "outputSpeech": {"type": "PlainText", "text": reprompt}
            }
        return resp

    try:
        if req_type == "LaunchRequest":
            greeting = {
                "it": "Ciao! Sono Amira, la tua assistente di casa. Chiedimi qualsiasi cosa!",
                "en": "Hi! I'm Amira, your home assistant. Ask me anything!",
                "es": "¡Hola! Soy Amira, tu asistente del hogar. ¡Pregúntame lo que quieras!",
                "fr": "Salut ! Je suis Amira, ton assistante maison. Demande-moi ce que tu veux !",
            }.get(LANGUAGE, "Hi! I'm Amira. Ask me anything!")
            return jsonify(_alexa_response(greeting, end_session=False, reprompt=greeting)), 200

        elif req_type == "IntentRequest":
            intent_name = req.get("intent", {}).get("name", "")

            if intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
                bye = {
                    "it": "Ciao ciao! A presto!",
                    "en": "Bye bye! See you soon!",
                    "es": "¡Adiós! ¡Hasta pronto!",
                    "fr": "Au revoir ! À bientôt !",
                }.get(LANGUAGE, "Bye!")
                return jsonify(_alexa_response(bye, end_session=True)), 200

            elif intent_name == "AMAZON.HelpIntent":
                help_text = {
                    "it": "Puoi chiedermi di controllare luci, temperatura, elettrodomestici o qualsiasi cosa sulla tua casa. Ad esempio: accendi la luce del salotto, che temperatura c'è in camera?",
                    "en": "You can ask me to control lights, temperature, appliances, or anything about your home. For example: turn on the living room light, what's the bedroom temperature?",
                    "es": "Puedes pedirme que controle luces, temperatura, electrodomésticos o cualquier cosa sobre tu casa.",
                    "fr": "Tu peux me demander de contrôler les lumières, la température, les appareils ou tout ce qui concerne ta maison.",
                }.get(LANGUAGE, "Ask me anything about your home!")
                return jsonify(_alexa_response(help_text, end_session=False)), 200

            elif intent_name == "AMAZON.FallbackIntent":
                # Fallback — try to process as free text if available
                fallback = {
                    "it": "Non ho capito. Puoi ripetere?",
                    "en": "I didn't understand. Can you repeat?",
                    "es": "No entendí. ¿Puedes repetir?",
                    "fr": "Je n'ai pas compris. Peux-tu répéter ?",
                }.get(LANGUAGE, "I didn't understand. Can you repeat?")
                return jsonify(_alexa_response(fallback, end_session=False, reprompt=fallback)), 200

            elif intent_name == "AskAmiraIntent":
                # Get the user's spoken query from the slot
                slots = req.get("intent", {}).get("slots", {})
                user_query = slots.get("query", {}).get("value", "")
                if not user_query:
                    prompt = {
                        "it": "Dimmi pure, cosa vuoi sapere?",
                        "en": "Go ahead, what would you like to know?",
                        "es": "Dime, ¿qué quieres saber?",
                        "fr": "Dis-moi, que veux-tu savoir ?",
                    }.get(LANGUAGE, "What would you like to know?")
                    return jsonify(_alexa_response(prompt, end_session=False, reprompt=prompt)), 200

                logger.chat(f"📩 [Alexa] AskAmiraIntent: {user_query[:80]}")

                # Get AI response (voice_mode for concise answers)
                try:
                    response_text = chat_with_ai(user_query, session_id)
                    # Clean for speech: strip markdown, emoji, etc.
                    import re as _re
                    response_text = _re.sub(r'```[\s\S]*?```', '', response_text)
                    response_text = _re.sub(r'`[^`]+`', '', response_text)
                    response_text = _re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', response_text)
                    response_text = _re.sub(r'[#*_~>|]', '', response_text)
                    response_text = _re.sub(r'\s+', ' ', response_text).strip()
                    # Alexa has a 8000 char speech limit
                    if len(response_text) > 6000:
                        response_text = response_text[:6000] + "... Per il resto, puoi chiedermi di continuare."
                    logger.chat(f"📤 [Alexa] Response ({len(response_text)} chars): {response_text[:200]}")
                except Exception as e:
                    logger.error(f"[Alexa] AI error: {e}")
                    response_text = "Mi dispiace, non sono riuscita a elaborare la risposta."

                return jsonify(_alexa_response(response_text, end_session=False, reprompt="Vuoi chiedermi altro?")), 200

            else:
                # Unknown intent — try to handle as free-form
                logger.warning(f"[Alexa] Unknown intent: {intent_name}")
                return jsonify(_alexa_response("Non ho capito la richiesta.", end_session=False)), 200

        elif req_type == "SessionEndedRequest":
            logger.info(f"[Alexa] Session ended: {req.get('reason', 'unknown')}")
            return jsonify(_alexa_response("", end_session=True)), 200

        else:
            return jsonify(_alexa_response("", end_session=True)), 200

    except Exception as e:
        logger.error(f"[Alexa] Webhook error: {e}")
        return jsonify(_alexa_response("Si è verificato un errore. Riprova tra poco.", end_session=False)), 200


# moved to routes/system_routes.py: api_system_features


# moved to routes/mcp_routes.py: api_conversation_messages


# moved to routes/conversation_routes.py: api_conversations_list


# moved to routes/conversation_routes.py: api_snapshots_list


def _is_tool_call_artifact(content: str, msg: dict) -> bool:
    """Return True if this assistant message content is a raw tool-call artifact
    that should be hidden from the chat history UI.

    This happens when:
    - The message has a 'tool_calls' field (OpenAI format intermediate step)
    - The content is JSON that looks like a tool-call dict serialised by default=str
      e.g. '{"name": "get_current_time", "arguments": {}}'
    - The content is a list-repr of Anthropic SDK content blocks (tool_use blocks)
    - The content is a [TOOL RESULT: ...] block (internal context, not user-facing)
    """
    import re as _re
    if msg.get("tool_calls"):
        return True
    if not content:
        return False
    stripped = content.strip()
    # JSON dict with a "name" key and "arguments"/"input" key → tool call artifact
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict) and "name" in obj and ("arguments" in obj or "input" in obj):
                return True
        except Exception:
            pass
    # Python repr of Anthropic SDK ToolUseBlock: ToolUseBlock(id=..., name=..., ...)
    if "ToolUseBlock(" in stripped or "tool_use" in stripped[:30]:
        return True
    # List repr of content blocks (saved by default=str): "[ToolUseBlock(...)]"
    if stripped.startswith("[") and "ToolUseBlock" in stripped:
        return True
    # Internal [TOOL RESULT: ...] blocks injected by tool_simulator
    if stripped.startswith("[TOOL RESULT:") or stripped.startswith("[Called tools:"):
        return True
    return False


# moved to routes/conversation_routes.py: api_conversation_get, api_conversation_delete

# moved to routes/catalog_routes.py: api_get_models


# moved to routes/conversation_routes.py: api_snapshots_restore, api_delete_snapshot


# moved to routes/conversation_routes.py: api_download_snapshot


@app.route('/api/nvidia/test_model', methods=['POST'])
def api_nvidia_test_model():
    """Quick NVIDIA chat test for the currently selected model.

    Uses a minimal non-streaming /v1/chat/completions call with a short prompt.
    If the model returns 404 (not available) or 400 (not chat-compatible), it is blocklisted.
    """
    if not NVIDIA_API_KEY:
        return jsonify({"success": False, "error": tr("err_nvidia_api_key")}), 400

    model_id = get_active_model()
    if not isinstance(model_id, str) or not model_id.strip():
        return jsonify({"success": False, "error": tr("err_nvidia_model_invalid")}), 400

    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "ciao"}],
        "stream": False,
        "max_tokens": 32,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)

        if resp.status_code >= 400:
            if resp.status_code in (404, 400, 422):
                blocklist_nvidia_model(model_id)
                if resp.status_code == 404:
                    reason = "not available (404)"
                elif resp.status_code == 400:
                    reason = "not chat-compatible (400)"
                else:
                    reason = "not chat-compatible (422)"
                return jsonify({
                    "success": False,
                    "blocklisted": True,
                    "model": model_id,
                    "message": tr("err_nvidia_model_removed", reason=reason, model_id=model_id),
                }), 200

            return jsonify({
                "success": False,
                "blocklisted": False,
                "model": model_id,
                "message": f"Test NVIDIA fallito (HTTP {resp.status_code}).",
            }), 200

        data = resp.json() if resp.content else {}
        ok = bool(isinstance(data, dict) and (data.get("choices") or data.get("id")))
        if ok:
            mark_nvidia_model_tested_ok(model_id)
        return jsonify({"success": ok, "blocklisted": False, "model": model_id}), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "blocklisted": False,
            "model": model_id,
            "message": f"Test NVIDIA errore: {type(e).__name__}: {e}",
        }), 200


@app.route('/api/nvidia/test_models', methods=['POST'])
def api_nvidia_test_models():
    """General NVIDIA model scan.

    Tries multiple model IDs (from /v1/models when available) using a minimal non-streaming
    chat completion. Models that return 404/400 are blocklisted and removed from the list.

    This endpoint is intentionally bounded (time + max models per run) to avoid long UI hangs
    and rate-limit issues. Users can run it again to continue.
    """
    if not NVIDIA_API_KEY:
        return jsonify({"success": False, "error": tr("err_nvidia_api_key")}), 400

    body = request.get_json(silent=True) or {}
    logger.info("NVIDIA test_models invoked")
    try:
        max_models = int(body.get("max_models") or 0)
    except Exception:
        max_models = 0

    try:
        cursor = int(body.get("cursor") or 0)
    except Exception:
        cursor = 0

    # max_models <= 0 => "test all" in one run (bounded by time safety below).
    # Positive value keeps legacy bounded-batch behavior.
    unlimited_scan = max_models <= 0
    if not unlimited_scan:
        max_models = max(1, min(200, max_models))

    # In full scan mode allow longer execution to cover the whole catalog.
    max_seconds = 300.0 if unlimited_scan else 55.0
    per_model_timeout = 10

    # Use a fresh live list when possible.
    all_models = _fetch_nvidia_models_live(NVIDIA_API_KEY) or get_nvidia_models_cached(NVIDIA_API_KEY) or PROVIDER_MODELS.get("nvidia", [])
    all_models = [m for m in (all_models or []) if isinstance(m, str) and m.strip()]
    # Full retest mode: include also previously blocked/tested/uncertain models.
    candidates = list(dict.fromkeys(
        all_models + sorted(NVIDIA_MODEL_BLOCKLIST) + sorted(NVIDIA_MODEL_TESTED_OK) + sorted(NVIDIA_MODEL_UNCERTAIN)
    ))

    if cursor < 0:
        cursor = 0
    if candidates and cursor >= len(candidates):
        cursor = 0

    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    started = time.time()
    tested: list[str] = []
    ok: list[str] = []
    removed: list[str] = []
    uncertain: list[str] = []
    events: list[str] = []
    stopped_reason = None
    timeouts = 0

    idx = cursor

    def _is_model_invalid_4xx(status_code: int, body_text: str) -> bool:
        """Return True only when 4xx clearly indicates model incompatibility."""
        if status_code in (404, 422):
            return True
        if status_code != 400:
            return False
        low = (body_text or "").lower()
        invalid_markers = (
            "model_not_found",
            "unknown model",
            "model not found",
            "unsupported model",
            "model is not supported",
            "invalid model",
            "no such model",
            "not chat-compatible",
        )
        # Do NOT treat billing/auth/rate-limit payloads as invalid model.
        non_model_markers = (
            "insufficient",
            "quota",
            "credit",
            "balance",
            "billing",
            "auth",
            "unauthorized",
            "forbidden",
            "rate limit",
            "too many requests",
        )
        if any(m in low for m in non_model_markers):
            return False
        return any(m in low for m in invalid_markers)

    while idx < len(candidates):
        model_id = candidates[idx]
        if (not unlimited_scan) and (len(tested) >= max_models):
            # Normal end-of-batch (UI paginates in small chunks): do not mark as "stopped".
            break
        if (time.time() - started) > max_seconds:
            stopped_reason = f"timeout ({int(max_seconds)}s)"
            break

        tested.append(model_id)
        logger.info(f"NVIDIA test_models: [{idx + 1}/{len(candidates)}] testing '{model_id}'")
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": "ciao"}],
            "stream": False,
            "max_tokens": 16,
            "temperature": 0.0,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=per_model_timeout)
        except requests.exceptions.ReadTimeout:
            # Don't abort the whole scan on a single slow model.
            logger.info(f"NVIDIA test_models: timeout on '{model_id}'")
            events.append(f"⏱ timeout: {model_id}")
            uncertain.append(model_id)
            mark_nvidia_model_uncertain(model_id)
            timeouts += 1
            idx += 1
            continue
        except Exception as e:
            logger.warning(f"NVIDIA test_models: network error on '{model_id}': {type(e).__name__}: {e}")
            uncertain.append(model_id)
            mark_nvidia_model_uncertain(model_id)
            events.append(f"⚠️ network {type(e).__name__}: {model_id}")
            idx += 1
            continue

        if resp.status_code == 200:
            logger.info(f"NVIDIA test_models: OK '{model_id}'")
            events.append(f"✅ ok: {model_id}")
            ok.append(model_id)
            mark_nvidia_model_tested_ok(model_id)
            idx += 1
            continue

        _resp_text = ""
        try:
            _resp_text = resp.text or ""
        except Exception:
            _resp_text = ""

        if _is_model_invalid_4xx(resp.status_code, _resp_text):
            logger.info(f"NVIDIA test_models: blocklist '{model_id}' (HTTP {resp.status_code})")
            events.append(f"⛔ blocklist (HTTP {resp.status_code}): {model_id}")
            blocklist_nvidia_model(model_id)
            removed.append(model_id)
            idx += 1
            continue

        if resp.status_code == 429:
            logger.warning(f"NVIDIA test_models: rate limit on '{model_id}' (continuing)")
            uncertain.append(model_id)
            mark_nvidia_model_uncertain(model_id)
            events.append(f"⚠️ rate-limit 429: {model_id}")
            idx += 1
            continue

        if resp.status_code in (401, 403):
            logger.warning(f"NVIDIA test_models: auth/perm error on '{model_id}' HTTP {resp.status_code} (continuing)")
            uncertain.append(model_id)
            mark_nvidia_model_uncertain(model_id)
            events.append(f"⚠️ auth {resp.status_code}: {model_id}")
            idx += 1
            continue

        # Other 4xx client errors: do not stop full scan, just skip model.
        # Typical cases: non-chat/embedding-only endpoints exposed in catalog.
        if 400 <= resp.status_code < 500:
            logger.warning(f"NVIDIA test_models: non-fatal client error on '{model_id}' HTTP {resp.status_code} (continuing)")
            uncertain.append(model_id)
            mark_nvidia_model_uncertain(model_id)
            events.append(f"⚠️ client {resp.status_code}: {model_id}")
            idx += 1
            continue

        # Transient provider-side/server errors: skip current model and continue.
        if 500 <= resp.status_code < 600:
            logger.warning(f"NVIDIA test_models: transient server error on '{model_id}' HTTP {resp.status_code} (continuing)")
            uncertain.append(model_id)
            mark_nvidia_model_uncertain(model_id)
            events.append(f"⚠️ server {resp.status_code}: {model_id}")
            idx += 1
            continue

        logger.warning(f"NVIDIA test_models: non-fatal unknown status on '{model_id}' HTTP {resp.status_code} (continuing)")
        uncertain.append(model_id)
        mark_nvidia_model_uncertain(model_id)
        events.append(f"⚠️ status {resp.status_code}: {model_id}")
        idx += 1
        continue

    next_cursor = idx
    remaining = max(0, len(candidates) - next_cursor)
    return jsonify({
        "success": True,
        "tested": len(tested),
        "total": len(candidates),
        "ok": len(ok),
        "removed": len(removed),
        "uncertain": len(uncertain),
        "tested_models": tested,
        "ok_models": ok,
        "removed_models": removed,
        "uncertain_models": uncertain,
        "events": events,
        "blocklisted": bool(removed),
        "stopped_reason": stopped_reason,
        "remaining": remaining,
        "next_cursor": next_cursor,
        "timeouts": timeouts,
    }), 200


@app.route('/api/provider/test_models', methods=['POST'])
def api_provider_test_models():
    """Generic model scan for selected API providers (OpenRouter, Mistral).

    Uses a minimal non-streaming OpenAI-compatible chat completion call.
    Models returning 404/400/422 are blocklisted for that provider.
    """
    body = request.get_json(silent=True) or {}
    provider = str(body.get("provider") or "").strip().lower()
    if provider not in {"openrouter", "mistral"}:
        return jsonify({"success": False, "error": "Unsupported provider for batch test"}), 400

    provider_keys = {
        "openrouter": OPENROUTER_API_KEY,
        "mistral": MISTRAL_API_KEY,
    }
    provider_urls = {
        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
        "mistral": "https://api.mistral.ai/v1/chat/completions",
    }
    api_key = provider_keys.get(provider) or ""
    if not api_key:
        return jsonify({"success": False, "error": f"{provider}: API key not configured"}), 400

    try:
        max_models = int(body.get("max_models") or 0)
    except Exception:
        max_models = 0
    try:
        cursor = int(body.get("cursor") or 0)
    except Exception:
        cursor = 0

    unlimited_scan = max_models <= 0
    if not unlimited_scan:
        max_models = max(1, min(200, max_models))

    max_seconds = 300.0 if unlimited_scan else 55.0
    per_model_timeout = 12

    # Full retest mode: include current provider models + previously blocked + previously tested.
    # This allows users to re-validate old failures after provider-side fixes.
    all_models = [m for m in (PROVIDER_MODELS.get(provider) or []) if isinstance(m, str) and m.strip()]
    blocked_from_file: list[str] = []
    tested_from_file: list[str] = []
    uncertain_from_file: list[str] = []
    try:
        if os.path.isfile(MODEL_BLOCKLIST_FILE):
            with open(MODEL_BLOCKLIST_FILE, "r", encoding="utf-8") as fh:
                _blk = json.load(fh) or {}
            _pv = _blk.get(provider)
            if isinstance(_pv, dict):
                _b = _pv.get("blocked") or []
                _t = _pv.get("tested_ok") or []
                _u = _pv.get("uncertain") or []
                if isinstance(_b, list):
                    blocked_from_file = [m for m in _b if isinstance(m, str) and m.strip()]
                if isinstance(_t, list):
                    tested_from_file = [m for m in _t if isinstance(m, str) and m.strip()]
                if isinstance(_u, list):
                    uncertain_from_file = [m for m in _u if isinstance(m, str) and m.strip()]
            elif isinstance(_pv, list):
                blocked_from_file = [m for m in _pv if isinstance(m, str) and m.strip()]
    except Exception as _e:
        logger.warning(f"{provider} test_models: unable to read blocklist file: {_e}")
    if provider in PROVIDER_MODEL_TESTED_OK:
        tested_from_file.extend([m for m in PROVIDER_MODEL_TESTED_OK.get(provider, set()) if isinstance(m, str) and m.strip()])
    if provider in PROVIDER_MODEL_UNCERTAIN:
        uncertain_from_file.extend([m for m in PROVIDER_MODEL_UNCERTAIN.get(provider, set()) if isinstance(m, str) and m.strip()])
    all_models = list(dict.fromkeys(all_models + blocked_from_file + tested_from_file + uncertain_from_file))
    if cursor < 0:
        cursor = 0
    if all_models and cursor >= len(all_models):
        cursor = 0

    logger.info(f"{provider} test_models invoked")
    url = provider_urls[provider]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    started = time.time()
    tested: list[str] = []
    ok: list[str] = []
    removed: list[str] = []
    uncertain: list[str] = []
    events: list[str] = []
    stopped_reason = None
    timeouts = 0
    idx = cursor

    def _is_model_invalid_4xx(status_code: int, body_text: str) -> bool:
        """Return True only when 4xx clearly indicates model incompatibility."""
        if status_code in (404, 422):
            return True
        if status_code != 400:
            return False
        low = (body_text or "").lower()
        invalid_markers = (
            "model_not_found",
            "unknown model",
            "model not found",
            "unsupported model",
            "model is not supported",
            "invalid model",
            "no such model",
            "unsupported_api_for_model",
            "not accessible via the /chat/completions endpoint",
            "not chat-compatible",
        )
        non_model_markers = (
            "insufficient",
            "quota",
            "credit",
            "balance",
            "billing",
            "auth",
            "unauthorized",
            "forbidden",
            "rate limit",
            "too many requests",
        )
        if any(m in low for m in non_model_markers):
            return False
        return any(m in low for m in invalid_markers)

    while idx < len(all_models):
        model_id = all_models[idx]
        if (not unlimited_scan) and (len(tested) >= max_models):
            # Normal end-of-batch (UI paginates in small chunks): do not mark as "stopped".
            break
        if (time.time() - started) > max_seconds:
            stopped_reason = f"timeout ({int(max_seconds)}s)"
            break

        tested.append(model_id)
        logger.info(f"{provider} test_models: [{idx + 1}/{len(all_models)}] testing '{model_id}'")
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": "ciao"}],
            "stream": False,
            "max_tokens": 16,
            "temperature": 0.0,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=per_model_timeout)
        except requests.exceptions.ReadTimeout:
            logger.info(f"{provider} test_models: timeout on '{model_id}'")
            events.append(f"⏱ timeout: {model_id}")
            uncertain.append(model_id)
            mark_provider_model_uncertain(provider, model_id)
            timeouts += 1
            idx += 1
            continue
        except Exception as e:
            logger.warning(f"{provider} test_models: network error on '{model_id}': {type(e).__name__}: {e}")
            uncertain.append(model_id)
            mark_provider_model_uncertain(provider, model_id)
            events.append(f"⚠️ network {type(e).__name__}: {model_id}")
            idx += 1
            continue

        if resp.status_code == 200:
            logger.info(f"{provider} test_models: OK '{model_id}'")
            events.append(f"✅ ok: {model_id}")
            ok.append(model_id)
            mark_provider_model_tested_ok(provider, model_id)
            idx += 1
            continue

        _resp_text = ""
        try:
            _resp_text = resp.text or ""
        except Exception:
            _resp_text = ""

        if _is_model_invalid_4xx(resp.status_code, _resp_text):
            logger.info(f"{provider} test_models: blocklist '{model_id}' (HTTP {resp.status_code})")
            events.append(f"⛔ blocklist (HTTP {resp.status_code}): {model_id}")
            blocklist_model(provider, model_id)
            removed.append(model_id)
            idx += 1
            continue

        if resp.status_code == 429:
            logger.warning(f"{provider} test_models: rate limit on '{model_id}' (continuing)")
            uncertain.append(model_id)
            mark_provider_model_uncertain(provider, model_id)
            events.append(f"⚠️ rate-limit 429: {model_id}")
            idx += 1
            continue
        if resp.status_code in (401, 403):
            logger.warning(f"{provider} test_models: auth/perm error on '{model_id}' HTTP {resp.status_code} (continuing)")
            uncertain.append(model_id)
            mark_provider_model_uncertain(provider, model_id)
            events.append(f"⚠️ auth {resp.status_code}: {model_id}")
            idx += 1
            continue

        # Other 4xx client errors: do not stop full scan, just skip model.
        if 400 <= resp.status_code < 500:
            logger.warning(f"{provider} test_models: non-fatal client error on '{model_id}' HTTP {resp.status_code} (continuing)")
            uncertain.append(model_id)
            mark_provider_model_uncertain(provider, model_id)
            events.append(f"⚠️ client {resp.status_code}: {model_id}")
            idx += 1
            continue

        # Transient provider-side/server errors: skip current model and continue.
        if 500 <= resp.status_code < 600:
            logger.warning(f"{provider} test_models: transient server error on '{model_id}' HTTP {resp.status_code} (continuing)")
            uncertain.append(model_id)
            mark_provider_model_uncertain(provider, model_id)
            events.append(f"⚠️ server {resp.status_code}: {model_id}")
            idx += 1
            continue

        logger.warning(f"{provider} test_models: non-fatal unknown status on '{model_id}' HTTP {resp.status_code} (continuing)")
        uncertain.append(model_id)
        mark_provider_model_uncertain(provider, model_id)
        events.append(f"⚠️ status {resp.status_code}: {model_id}")
        idx += 1
        continue

    next_cursor = idx
    remaining = max(0, len(all_models) - next_cursor)
    return jsonify({
        "success": True,
        "provider": provider,
        "tested": len(tested),
        "total": len(all_models),
        "ok": len(ok),
        "removed": len(removed),
        "uncertain": len(uncertain),
        "tested_models": tested,
        "ok_models": ok,
        "removed_models": removed,
        "uncertain_models": uncertain,
        "events": events,
        "blocklisted": bool(removed),
        "stopped_reason": stopped_reason,
        "remaining": remaining,
        "next_cursor": next_cursor,
        "timeouts": timeouts,
    }), 200

# ---- Memory API Endpoints ----

# moved to routes/memory_routes.py: api_get_memory, api_search_memory, api_memory_stats,
# api_delete_memory, api_cleanup_memory



@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "ai_provider": AI_PROVIDER,
        "ai_model": get_active_model(),
        "ai_configured": bool(get_api_key()),
        "ha_connected": bool(get_ha_token()),
    }), 200


@app.route("/entities", methods=["GET"])
def get_entities_route():
    """Get all entities."""
    domain = request.args.get("domain", "")
    states = get_all_states()
    if domain:
        states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
    return jsonify({"entities": states, "count": len(states)}), 200


@app.route("/entity/<entity_id>/state", methods=["GET"])
def get_entity_state_route(entity_id: str):
    """Get entity state."""
    return jsonify(call_ha_api("GET", f"states/{entity_id}")), 200


@app.route("/message", methods=["POST"])
def send_message_legacy():
    """Legacy message endpoint."""
    data = request.get_json()
    return jsonify({"status": "success", "response": chat_with_ai(data.get("message", ""))}), 200


@app.route("/service/call", methods=["POST"])
def call_service_route():
    """Call a Home Assistant service."""
    data = request.get_json()
    service = data.get("service", "")
    if not service or "." not in service:
        return jsonify({"error": "Use 'domain.service' format"}), 400
    domain, svc = service.split(".", 1)
    return jsonify(call_ha_api("POST", f"services/{domain}/{svc}", data.get("data", {}))), 200


@app.route("/execute/automation", methods=["POST"])
def execute_automation():
    """Execute an automation."""
    data = request.get_json()
    eid = data.get("entity_id", data.get("automation_id", ""))
    if not eid.startswith("automation."):
        eid = f"automation.{eid}"
    return jsonify(call_ha_api("POST", "services/automation/trigger", {"entity_id": eid})), 200


@app.route("/execute/script", methods=["POST"])
def execute_script():
    """Execute a script."""
    data = request.get_json()
    return jsonify(call_ha_api("POST", f"services/script/{data.get('script_id', '')}", data.get("variables", {}))), 200


@app.route("/conversation/clear", methods=["POST"])
def clear_conversation():
    """Clear conversation history."""
    sid = (request.get_json() or {}).get("session_id", "default")
    conversations.pop(sid, None)
    return jsonify({"status": "cleared"}), 200


# ===== FILE UPLOAD ENDPOINTS =====
# moved to routes/document_routes.py: upload_document, list_documents, get_document,
# search_documents, delete_document, document_stats, rag_index, rag_search


# ===== HA LOGS PROXY =====

# moved to routes/system_routes.py: api_ha_logs



# ===== FILE EXPLORER API =====
# Direct REST endpoints for the chat UI file explorer panel.
# These browse /config (HA_CONFIG_DIR) without going through the AI tool layer,
# so navigation is instant regardless of which AI provider is selected.
# Security: path traversal blocked (no "..", no absolute paths) — same as tools.py.

# moved to routes/file_routes.py: api_files_list, api_files_read


# ===== DASHBOARD API PROXY =====
# These endpoints proxy HA API calls using the SUPERVISOR_TOKEN so that
# dashboard iframes don't need browser-side authentication tokens.

@app.route('/dashboard_api/states')
def dashboard_api_states():
    """Proxy GET /api/states using server-side SUPERVISOR_TOKEN."""
    try:
        resp = requests.get(
            f"{HA_URL}/api/states",
            headers=get_ha_headers(),
            timeout=30
        )
        return resp.json(), resp.status_code, {"Content-Type": "application/json"}
    except Exception as e:
        logger.error(f"Dashboard API proxy /states error: {e}")
        return jsonify({"error": str(e)}), 502


@app.route('/dashboard_api/history')
def dashboard_api_history():
    """Proxy GET /api/history/period using server-side SUPERVISOR_TOKEN."""
    try:
        entity_ids = request.args.get('entity_ids', '')
        hours = min(int(request.args.get('hours', 24)), 168)

        if not entity_ids:
            return jsonify({"error": "entity_ids parameter required"}), 400

        # Validate entity_id format
        for eid in entity_ids.split(','):
            if not re.match(r'^[a-z_]+\.[a-z0-9_]+$', eid.strip()):
                return jsonify({"error": f"Invalid entity_id: {eid}"}), 400

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        url = (f"{HA_URL}/api/history/period/{start_time.isoformat()}Z"
               f"?filter_entity_id={entity_ids}"
               f"&end_time={end_time.isoformat()}Z"
               f"&minimal_response&no_attributes")

        resp = requests.get(url, headers=get_ha_headers(), timeout=30)
        return resp.json(), resp.status_code, {"Content-Type": "application/json"}
    except Exception as e:
        logger.error(f"Dashboard API proxy /history error: {e}")
        return jsonify({"error": str(e)}), 502


@app.route('/dashboard_api/services/<domain>/<service>', methods=['POST'])
def dashboard_api_service(domain, service):
    """Proxy POST /api/services/<domain>/<service> using server-side SUPERVISOR_TOKEN."""
    try:
        # Validate domain and service: only alphanumeric + underscore
        if not re.match(r'^[a-z_]+$', domain) or not re.match(r'^[a-z_]+$', service):
            return jsonify({"error": "Invalid domain or service name"}), 400

        data = request.get_json(silent=True) or {}
        resp = requests.post(
            f"{HA_URL}/api/services/{domain}/{service}",
            headers=get_ha_headers(),
            json=data,
            timeout=30
        )
        return resp.json(), resp.status_code, {"Content-Type": "application/json"}
    except Exception as e:
        logger.error(f"Dashboard API proxy /services/{domain}/{service} error: {e}")
        return jsonify({"error": str(e)}), 502


# ===== CUSTOM HTML DASHBOARDS =====
@app.route('/custom_dashboards/<name>')
def serve_html_dashboard(name):
    """Serve custom HTML dashboards (legacy route, kept for backward compat)."""
    try:
        safe_name = name.lower().replace(" ", "-").replace("_", "-").replace(".", "-")
        if not safe_name.endswith(".html"):
            safe_name += ".html"

        if not all(c.isalnum() or c in '-.' for c in safe_name):
            return jsonify({"error": "Invalid dashboard name"}), 400

        # Load from www/dashboards/ (legacy .html_dashboards/ support removed)
        dashboard_path = os.path.join(HA_CONFIG_DIR, "www", "dashboards", safe_name)

        if not os.path.isfile(dashboard_path):
            return jsonify({"error": f"Dashboard '{name}' not found"}), 404

        with open(dashboard_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        logger.info(f"📊 Serving custom dashboard: {safe_name}")
        return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}

    except Exception as e:
        logger.error(f"❌ Error serving dashboard: {e}")
        return jsonify({"error": f"Failed to serve dashboard: {str(e)}"}), 500


@app.route('/api/dashboard_html/<name>')
def api_get_dashboard_html(name):
    """Return HTML dashboard content as JSON (for bubble context / editing)."""
    try:
        safe_name = name.lower().replace(" ", "-").replace("_", "-").replace(".", "-")
        if not safe_name.endswith(".html"):
            safe_name += ".html"
        for subdir in [os.path.join("www", "dashboards"), ".html_dashboards"]:
            path = os.path.join(HA_CONFIG_DIR, subdir, safe_name)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    html = f.read()
                return jsonify({"name": name, "html": html, "size": len(html)}), 200
        return jsonify({"error": f"Dashboard '{name}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/custom_dashboards')
def list_html_dashboards():
    """List all available custom HTML dashboards."""
    try:
        dashboards = []

        # Scan www/dashboards/ (legacy .html_dashboards/ support removed)
        dashboards_dir = os.path.join(HA_CONFIG_DIR, "www", "dashboards")
        if os.path.isdir(dashboards_dir):
            for filename in os.listdir(dashboards_dir):
                if filename.endswith(".html"):
                    file_path = os.path.join(dashboards_dir, filename)
                    dash_name = filename.replace(".html", "")
                    dashboards.append({
                        "name": dash_name,
                        "filename": filename,
                        "url": f"/local/dashboards/{filename}",
                        "size": os.path.getsize(file_path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })

        logger.info(f"📊 Listed {len(dashboards)} custom dashboards")
        return jsonify({"dashboards": dashboards, "count": len(dashboards)}), 200

    except Exception as e:
        logger.error(f"❌ Error listing dashboards: {e}")
        return jsonify({"error": str(e)}), 500


# moved to routes/document_routes.py: rag_stats


# ---------------------------------------------------------------------------
# Usage / cost tracking endpoints (inspired by OpenClaw)
# ---------------------------------------------------------------------------

# moved to routes/usage_routes.py: usage_stats, usage_stats_today, usage_stats_reset


# ---------------------------------------------------------------------------
# OpenAI Codex OAuth flow endpoints
# ---------------------------------------------------------------------------
@app.route("/api/oauth/codex/start", methods=["GET"])
def oauth_codex_start():
    """Start the OpenAI Codex OAuth flow. Returns the authorization URL."""
    try:
        from providers.openai_codex import start_oauth_flow
        authorize_url, state = start_oauth_flow()
        return jsonify({"authorize_url": authorize_url, "state": state}), 200
    except Exception as e:
        logger.error(f"Codex OAuth start error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/oauth/codex/exchange", methods=["POST"])
def oauth_codex_exchange():
    """Exchange the redirect URL (or code) for an access token."""
    try:
        from providers.openai_codex import exchange_code
        data = request.json or {}
        redirect_url = data.get("redirect_url", "").strip()
        state = data.get("state", "").strip()
        if not redirect_url or not state:
            return jsonify({"error": "Missing redirect_url or state"}), 400
        token = exchange_code(redirect_url, state)
        return jsonify({"ok": True, "account_id": token.get("account_id")}), 200
    except Exception as e:
        logger.error(f"Codex OAuth exchange error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/oauth/codex/status", methods=["GET"])
def oauth_codex_status():
    """Return whether a valid Codex token is available."""
    try:
        from providers.openai_codex import get_token_status
        return jsonify(get_token_status()), 200
    except Exception as e:
        return jsonify({"configured": False, "error": str(e)}), 200


@app.route("/api/oauth/codex/revoke", methods=["POST"])
def oauth_codex_revoke():
    """Delete the stored Codex OAuth token (logout)."""
    try:
        import providers.openai_codex as _codex_mod
        _codex_mod._stored_token = None
        token_file = _codex_mod._TOKEN_FILE
        try:
            import os as _os
            if _os.path.exists(token_file):
                _os.remove(token_file)
        except Exception:
            pass
        logger.info("Codex: OAuth token revoked by user.")
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# GitHub Copilot Device Code OAuth flow endpoints
# ---------------------------------------------------------------------------
@app.route("/api/oauth/copilot/start", methods=["GET"])
def oauth_copilot_start():
    """Start the GitHub Device Code flow. Returns {user_code, verification_uri, interval}."""
    try:
        from providers.github_copilot import start_device_flow
        result = start_device_flow()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Copilot OAuth start error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/oauth/copilot/poll", methods=["GET"])
def oauth_copilot_poll():
    """Poll GitHub for the access token. Returns {status: pending|success|error}."""
    try:
        from providers.github_copilot import poll_device_flow
        return jsonify(poll_device_flow()), 200
    except Exception as e:
        logger.error(f"Copilot OAuth poll error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/oauth/copilot/status", methods=["GET"])
def oauth_copilot_status():
    """Return whether a valid Copilot token is available."""
    try:
        from providers.github_copilot import get_token_status
        return jsonify(get_token_status()), 200
    except Exception as e:
        return jsonify({"configured": False, "error": str(e)}), 200


@app.route("/api/oauth/copilot/revoke", methods=["POST"])
def oauth_copilot_revoke():
    """Clear the stored GitHub Copilot OAuth token."""
    try:
        from providers.github_copilot import clear_token
        clear_token()
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Copilot: revoke error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Claude Web session endpoints
# ---------------------------------------------------------------------------
@app.route("/api/session/claude_web/store", methods=["POST"])
def session_claude_web_store():
    """Store a Claude.ai session key."""
    try:
        from providers.claude_web import store_session_key
        data = request.json or {}
        session_key = data.get("session_key", "").strip()
        if not session_key:
            return jsonify({"error": "Missing session_key"}), 400
        result = store_session_key(session_key)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Claude Web session store error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/session/claude_web/status", methods=["GET"])
def session_claude_web_status():
    """Return Claude Web session status."""
    try:
        from providers.claude_web import get_session_status
        return jsonify(get_session_status()), 200
    except Exception as e:
        return jsonify({"configured": False, "error": str(e)}), 200


@app.route("/api/session/claude_web/clear", methods=["POST"])
def session_claude_web_clear():
    """Clear stored Claude Web session token."""
    try:
        from providers.claude_web import clear_session
        clear_session()
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------------
# ChatGPT Web session endpoints
# ---------------------------------------------------------------------------
@app.route("/api/session/chatgpt_web/store", methods=["POST"])
def session_chatgpt_web_store():
    """Store a ChatGPT Web access token."""
    try:
        from providers.chatgpt_web import store_access_token
        data = request.json or {}
        access_token = data.get("access_token", "").strip()
        cf_clearance = data.get("cf_clearance", "").strip()
        if not access_token:
            return jsonify({"error": "Missing access_token"}), 400
        result = store_access_token(access_token, cf_clearance=cf_clearance)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"ChatGPT Web session store error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/session/chatgpt_web/status", methods=["GET"])
def session_chatgpt_web_status():
    """Return ChatGPT Web session status."""
    try:
        from providers.chatgpt_web import get_session_status
        return jsonify(get_session_status()), 200
    except Exception as e:
        return jsonify({"configured": False, "error": str(e)}), 200


@app.route("/api/session/chatgpt_web/clear", methods=["POST"])
def session_chatgpt_web_clear():
    """Clear stored ChatGPT Web access token."""
    try:
        from providers.chatgpt_web import clear_session
        clear_session()
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------------
# Grok Web session endpoints
# ---------------------------------------------------------------------------
@app.route("/api/session/grok_web/store", methods=["POST"])
def session_grok_web_store():
    return jsonify({"error": "grok_web provider removed"}), 410


@app.route("/api/session/grok_web/status", methods=["GET"])
def session_grok_web_status():
    return jsonify({"configured": False, "removed": True, "error": "grok_web provider removed"}), 200


@app.route("/api/session/grok_web/clear", methods=["POST"])
def session_grok_web_clear():
    return jsonify({"ok": True, "removed": True}), 200


# ---------------------------------------------------------------------------
# Gemini Web session endpoints
# ---------------------------------------------------------------------------
@app.route("/api/session/gemini_web/store", methods=["POST"])
def session_gemini_web_store():
    """Store Gemini Web session cookies (__Secure-1PSID and __Secure-1PSIDTS)."""
    try:
        from providers.gemini_web import store_session
        data = request.json or {}
        psid   = data.get("psid", "").strip()
        psidts = data.get("psidts", "").strip()
        if not psid or not psidts:
            return jsonify({"error": "Missing psid or psidts"}), 400
        result = store_session(psid, psidts)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Gemini Web session store error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/session/gemini_web/status", methods=["GET"])
def session_gemini_web_status():
    """Return Gemini Web session status."""
    try:
        from providers.gemini_web import get_session_status
        return jsonify(get_session_status()), 200
    except Exception as e:
        return jsonify({"configured": False, "error": str(e)}), 200


@app.route("/api/session/gemini_web/clear", methods=["POST"])
def session_gemini_web_clear():
    """Clear stored Gemini Web session."""
    try:
        from providers.gemini_web import clear_session
        clear_session()
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------------
# Perplexity Web session endpoints
# ---------------------------------------------------------------------------
@app.route("/api/session/perplexity_web/store", methods=["POST"])
def session_perplexity_web_store():
    """Store Perplexity Web session cookies (next-auth.csrf-token + next-auth.session-token)."""
    try:
        from providers.perplexity_web import store_session
        data = request.json or {}
        csrf_token = (data.get("csrf_token") or "").strip()
        session_token = (data.get("session_token") or "").strip()
        if not csrf_token or not session_token:
            return jsonify({"error": "Missing csrf_token or session_token"}), 400
        result = store_session(csrf_token, session_token)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Perplexity Web session store error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/session/perplexity_web/status", methods=["GET"])
def session_perplexity_web_status():
    """Return Perplexity Web session status."""
    try:
        from providers.perplexity_web import get_session_status
        return jsonify(get_session_status()), 200
    except Exception as e:
        return jsonify({"configured": False, "error": str(e)}), 200


@app.route("/api/session/perplexity_web/clear", methods=["POST"])
def session_perplexity_web_clear():
    """Clear stored Perplexity Web session."""
    try:
        from providers.perplexity_web import clear_session
        clear_session()
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def start_messaging_bots() -> None:
    """Initialize and start Telegram and WhatsApp bots if configured.
    Called from server.py so it runs regardless of __name__.
    """
    # bashio::config returns the string "null" for unset optional fields
    def _env(key: str) -> str:
        v = os.getenv(key, "")
        return "" if v in ("", "null", "none", "None", "NULL") else v

    if MESSAGING_AVAILABLE:
        try:
            if not ENABLE_TELEGRAM:
                logger.info("Telegram bot disabled via configuration (enable_telegram: false)")
            else:
                t_token = _env("TELEGRAM_BOT_TOKEN")
                if t_token:
                    bot = telegram_bot.get_telegram_bot(t_token)
                    if bot:
                        bot.start()
                        logger.info("✅ Telegram bot started")
                else:
                    logger.info("Telegram bot not configured (no token)")
        except Exception as e:
            logger.warning(f"⚠️ Telegram bot initialization error: {e}")

        try:
            if not ENABLE_WHATSAPP:
                logger.info("WhatsApp bot disabled via configuration (enable_whatsapp: false)")
            else:
                wa_sid   = _env("TWILIO_ACCOUNT_SID")
                wa_token = _env("TWILIO_AUTH_TOKEN")
                wa_from  = _env("TWILIO_WHATSAPP_FROM")
                if wa_sid and wa_token and wa_from:
                    whatsapp_bot.get_whatsapp_bot(wa_sid, wa_token, wa_from)
                    logger.info("✅ WhatsApp bot initialized (webhook mode)")
                else:
                    logger.info("WhatsApp bot not configured (no Twilio credentials)")
        except Exception as e:
            logger.warning(f"⚠️ WhatsApp bot initialization error: {e}")


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


def initialize_mcp() -> None:
    """Initialize MCP servers from config. Called by server.py at startup."""
    if not MCP_AVAILABLE:
        logger.debug("MCP support not available")
        return

    # Skip entirely if MCP is disabled via config toggle
    if not ENABLE_MCP:
        logger.info("🔌 MCP disabled (enable_mcp: false)")
        return

    try:
        mcp_config = None

        # Priority 1: MCP_SERVERS environment variable (JSON string, set by run script)
        mcp_env = os.getenv("MCP_SERVERS", "").strip()
        if mcp_env and mcp_env != "{}":
            try:
                mcp_config = json.loads(mcp_env)
                logger.info("🔌 MCP: config loaded from MCP_SERVERS env var")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ MCP_SERVERS env var is invalid JSON: {e}")

        # Priority 2: mcp_config_file path (user-editable via UI)
        if not mcp_config:
            mcp_json_path = MCP_CONFIG_FILE or "/config/amira/mcp_config.json"
            if os.path.isfile(mcp_json_path):
                try:
                    with open(mcp_json_path, encoding="utf-8") as f:
                        mcp_config = json.load(f)
                    logger.info(f"🔌 MCP: config loaded from {mcp_json_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to read {mcp_json_path}: {e}")

        # Priority 3: config.yaml mcp_servers field (legacy / fallback)
        if not mcp_config:
            try:
                import yaml
                config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
                with open(config_path, encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}
                yaml_mcp = config_data.get("mcp_servers", {})
                if yaml_mcp and yaml_mcp != "{}":
                    mcp_config = json.loads(yaml_mcp) if isinstance(yaml_mcp, str) else yaml_mcp
                    if mcp_config:
                        logger.info("🔌 MCP: config loaded from config.yaml")
            except Exception as e:
                logger.debug(f"MCP config.yaml fallback skipped: {e}")

        # Initialize only servers that were manually started and left running
        # by the user (persisted in MCP runtime state).
        if mcp_config and isinstance(mcp_config, dict) and mcp_config:
            if "mcpServers" in mcp_config and isinstance(mcp_config["mcpServers"], dict):
                mcp_config = mcp_config["mcpServers"]
            autostart = set(_load_mcp_runtime_state().get("autostart_servers", []))
            start_cfg = {
                name: cfg
                for name, cfg in mcp_config.items()
                if isinstance(cfg, dict) and name in autostart
            }
            # Keep runtime state clean if config changed and some names disappeared.
            missing = autostart.difference(set(mcp_config.keys()))
            if missing:
                state = _load_mcp_runtime_state()
                state["autostart_servers"] = sorted(set(state.get("autostart_servers", [])) - missing)
                _save_mcp_runtime_state(state)
            if start_cfg:
                connected = mcp.initialize_mcp_servers(start_cfg)
                logger.info(f"🔌 MCP: Initialized {connected}/{len(start_cfg)} autostart server(s)")
            else:
                logger.info("🔌 MCP: No server marked for autostart")
        else:
            logger.debug("MCP servers not configured (no mcp_config.json or MCP_SERVERS env var)")
    except Exception as e:
        logger.warning(f"⚠️ MCP initialization error: {e}")


# ===== CONFIG FILE EDITOR API =====

@app.route('/api/config/read', methods=['GET'])
def api_config_read():
    """Read a whitelisted config file for the in-app editor."""
    filepath = (request.args.get("file") or "").strip()
    if not filepath or filepath not in CONFIG_EDITABLE_FILES:
        return jsonify({"success": False, "error": "File not accessible"}), 403

    full_path = os.path.join(HA_CONFIG_DIR, filepath)
    if not os.path.isfile(full_path):
        return jsonify({"success": True, "file": filepath, "content": "", "exists": False})

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"success": True, "file": filepath, "content": content, "exists": True, "size": len(content)})
    except Exception as e:
        logger.error(f"api_config_read error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/config/save', methods=['POST'])
def api_config_save():
    """Save content to a whitelisted config file."""
    global CUSTOM_SYSTEM_PROMPT

    data = request.get_json() or {}
    filepath = (data.get("file") or "").strip()
    content = data.get("content")

    if content is None:
        return jsonify({"success": False, "error": "content is required"}), 400
    if not filepath:
        return jsonify({"success": False, "error": "file path is required"}), 400

    # Security: only allow whitelisted files
    if filepath not in CONFIG_EDITABLE_FILES:
        return jsonify({"success": False, "error": f"File '{filepath}' is not editable"}), 403

    # Validate JSON for .json files
    if filepath.endswith(".json") and content.strip():
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            return jsonify({"success": False, "error": f"Invalid JSON: {e}"}), 400

    # Size guard
    if len(content) > 500_000:
        return jsonify({"success": False, "error": "Content too large (max 500KB)"}), 413

    full_path = os.path.join(HA_CONFIG_DIR, filepath)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Post-save hooks
        if filepath == "amira/agents.json":
            load_agents_config()
        elif filepath == "amira/custom_system_prompt.txt":
            loaded = _load_custom_system_prompt_from_disk()
            CUSTOM_SYSTEM_PROMPT = loaded

        logger.info(f"Config file saved: {filepath} ({len(content)} chars)")
        return jsonify({"success": True, "file": filepath, "size": len(content)})
    except Exception as e:
        logger.error(f"api_config_save error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ── Fallback configuration endpoint ─────────────────────────────────
_FALLBACK_CONFIG_FILE = os.path.join(HA_CONFIG_DIR, "amira", "fallback_config.json")

# Default provider priority (same as providers/manager.py)
_FALLBACK_PRIORITY_DEFAULT = [
    "anthropic", "openai", "google", "deepseek", "github",
    "groq", "mistral", "openrouter", "xai", "nvidia", "perplexity",
    "minimax", "aihubmix", "siliconflow", "volcengine",
    "dashscope", "moonshot", "zhipu", "ollama", "custom",
]

# Maps provider → env var for API key detection
_FALLBACK_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY", "github": "GITHUB_TOKEN",
    "nvidia": "NVIDIA_API_KEY", "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY", "openrouter": "OPENROUTER_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY", "xai": "XAI_API_KEY", "perplexity": "PERPLEXITY_API_KEY",
    "minimax": "MINIMAX_API_KEY", "aihubmix": "AIHUBMIX_API_KEY",
    "siliconflow": "SILICONFLOW_API_KEY", "volcengine": "VOLCENGINE_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY", "moonshot": "MOONSHOT_API_KEY",
    "zhipu": "ZHIPU_API_KEY", "custom": "CUSTOM_API_KEY",
    "ollama": "OLLAMA_BASE_URL",
}


@app.route('/api/fallback_config', methods=['GET'])
def api_fallback_config_get():
    """Return current fallback configuration: enabled state, provider priority, model overrides."""
    enabled = os.getenv("FALLBACK_ENABLED", "true").lower() not in ("false", "0", "no")

    # Load custom priority / model overrides or use defaults
    custom_priority = []
    provider_models = {}
    try:
        if os.path.isfile(_FALLBACK_CONFIG_FILE):
            with open(_FALLBACK_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            custom_priority = data.get("priority", [])
            pm = data.get("provider_models", {})
            if isinstance(pm, dict):
                provider_models = {str(k): str(v) for k, v in pm.items() if isinstance(k, str) and isinstance(v, str) and v.strip()}
            # Backward compatibility with old experimental shape:
            # model_priority: [{"provider":"anthropic","model":"claude-opus-4-6"}, ...]
            if not provider_models:
                mp = data.get("model_priority", [])
                if isinstance(mp, list):
                    for item in mp:
                        if not isinstance(item, dict):
                            continue
                        prov = str(item.get("provider") or "").strip().lower()
                        mdl = str(item.get("model") or "").strip()
                        if prov and mdl:
                            provider_models[prov] = mdl
            if "enabled" in data:
                enabled = bool(data["enabled"])
    except Exception:
        pass

    if isinstance(custom_priority, list) and custom_priority:
        priority = [str(p).strip().lower() for p in custom_priority if isinstance(p, str) and str(p).strip()]
    else:
        priority = list(_FALLBACK_PRIORITY_DEFAULT)

    # Build provider list with status
    providers = []
    seen = set()
    for prov in priority:
        env_var = _FALLBACK_KEY_ENV.get(prov, "")
        has_key = bool(env_var and os.getenv(env_var, ""))
        label = PROVIDER_DEFAULTS.get(prov, {}).get("name", prov)
        providers.append({
            "id": prov,
            "configured": has_key,
            "label": label,
            "model": provider_models.get(prov, ""),
        })
        seen.add(prov)

    # Add any configured providers not in the priority list
    for prov in _FALLBACK_PRIORITY_DEFAULT:
        if prov not in seen:
            env_var = _FALLBACK_KEY_ENV.get(prov, "")
            has_key = bool(env_var and os.getenv(env_var, ""))
            label = PROVIDER_DEFAULTS.get(prov, {}).get("name", prov)
            providers.append({
                "id": prov,
                "configured": has_key,
                "label": label,
                "model": provider_models.get(prov, ""),
            })

    return jsonify({
        "success": True,
        "enabled": enabled,
        "providers": providers,
        "priority": priority,
        "provider_models": provider_models,
    })


@app.route('/api/fallback_config', methods=['POST'])
def api_fallback_config_post():
    """Save fallback configuration (priority order, enabled flag, model overrides)."""
    data = request.get_json() or {}
    priority = data.get("priority", [])
    enabled = data.get("enabled", True)
    provider_models = data.get("provider_models", {})

    if not isinstance(priority, list):
        return jsonify({"success": False, "error": "priority must be a list"}), 400
    if provider_models is None:
        provider_models = {}
    if not isinstance(provider_models, dict):
        return jsonify({"success": False, "error": "provider_models must be an object"}), 400

    # Validate provider names
    valid_providers = set(_FALLBACK_PRIORITY_DEFAULT) | set(_FALLBACK_KEY_ENV.keys())
    clean_priority = [p for p in priority if isinstance(p, str) and p in valid_providers]
    clean_provider_models = {}
    for k, v in provider_models.items():
        if not isinstance(k, str):
            continue
        prov = k.strip().lower()
        if prov not in valid_providers:
            continue
        if v is None:
            continue
        mdl = str(v).strip()
        if mdl:
            clean_provider_models[prov] = mdl

    config_data = {
        "priority": clean_priority,
        "enabled": bool(enabled),
        "provider_models": clean_provider_models,
    }

    try:
        os.makedirs(os.path.dirname(_FALLBACK_CONFIG_FILE), exist_ok=True)
        with open(_FALLBACK_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        logger.info(
            f"Fallback config saved: enabled={enabled}, priority={clean_priority}, "
            f"provider_models={list(clean_provider_models.keys())}"
        )
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Failed to save fallback config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ── Settings API ─────────────────────────────────────────────────────
@app.route('/api/settings', methods=['GET'])
def api_settings_get():
    """Return all runtime settings with current values (merged: file > env > defaults)."""
    saved = _load_settings()
    _g = globals()
    current = {}
    for key, default in SETTINGS_DEFAULTS.items():
        # Priority: saved file value > current global > default
        if key in saved:
            current[key] = saved[key]
        else:
            gvar = _SETTINGS_GLOBAL_MAP.get(key)
            if gvar and gvar in _g:
                val = _g[gvar]
                # set is not JSON-serializable — convert back to comma-separated string
                if isinstance(val, set):
                    val = ",".join(str(i) for i in sorted(val))
                current[key] = val
            else:
                current[key] = default

    # Section metadata for UI rendering
    sections = [
        {
            "id": "language", "icon": "\U0001F30D", "fields": [
                {"key": "language", "type": "select",
                 "options": [
                     {"value": "en", "label": "English"},
                     {"value": "it", "label": "Italiano"},
                     {"value": "es", "label": "Español"},
                     {"value": "fr", "label": "Français"},
                 ]},
            ],
        },
        {
            "id": "features", "icon": "\u26A1", "fields": [
                {"key": "enable_memory", "type": "toggle"},
                {"key": "enable_file_access", "type": "toggle"},
                {"key": "enable_file_upload", "type": "toggle"},
                {"key": "enable_voice_input", "type": "toggle"},
                {"key": "enable_rag", "type": "toggle"},
                {"key": "enable_chat_bubble", "type": "toggle"},
                {"key": "enable_amira_card_button", "type": "toggle"},
                {"key": "enable_amira_automation_button", "type": "toggle"},
            ],
        },
        {
            "id": "ai", "icon": "\U0001F9E0", "fields": [
                {"key": "anthropic_extended_thinking", "type": "toggle"},
                {"key": "anthropic_prompt_caching", "type": "toggle"},
                {"key": "openai_extended_thinking", "type": "toggle"},
                {"key": "nvidia_thinking_mode", "type": "toggle"},
            ],
        },
        {
            "id": "voice", "icon": "\U0001F399\uFE0F", "fields": [
                {"key": "tts_voice", "type": "select",
                 "options": [
                     {"value": "female", "label": "Female"},
                     {"value": "male", "label": "Male"},
                 ]},
            ],
        },
        {
            "id": "messaging", "icon": "\U0001F4F1", "fields": [
                {"key": "enable_telegram", "type": "toggle"},
                {"key": "telegram_bot_token", "type": "password"},
                {"key": "telegram_allowed_ids", "type": "text"},
                {"key": "enable_whatsapp", "type": "toggle"},
                {"key": "twilio_account_sid", "type": "text"},
                {"key": "twilio_auth_token", "type": "password"},
                {"key": "twilio_whatsapp_from", "type": "text"},
            ],
        },
        {
            "id": "advanced", "icon": "\u2699\uFE0F", "fields": [
                {"key": "timeout", "type": "number", "min": 5, "max": 300, "step": 5},
                {"key": "max_retries", "type": "number", "min": 0, "max": 10, "step": 1},
                {"key": "max_conversations", "type": "number", "min": 1, "max": 100, "step": 1},
                {"key": "max_snapshots_per_file", "type": "number", "min": 1, "max": 50, "step": 1},
            ],
        },
        {
            "id": "costs", "icon": "\U0001F4B0", "fields": [
                {"key": "cost_currency", "type": "select",
                 "options": [
                     {"value": "USD", "label": "USD ($)"},
                     {"value": "EUR", "label": "EUR (\u20AC)"},
                     {"value": "GBP", "label": "GBP (\u00A3)"},
                     {"value": "JPY", "label": "JPY (\u00A5)"},
                 ]},
            ],
        },
    ]

    return jsonify({"success": True, "settings": current, "sections": sections})


# moved to routes/system_routes.py: api_addon_restart


@app.route('/api/settings', methods=['POST'])
def api_settings_post():
    """Save runtime settings, apply immediately, persist to settings.json."""
    data = request.get_json() or {}
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    # Only accept known keys
    clean = {}
    for key in SETTINGS_DEFAULTS:
        if key in data:
            clean[key] = data[key]

    try:
        # Merge with existing saved settings (partial updates allowed)
        existing = _load_settings()
        existing.update(clean)
        _save_settings(existing)
        _apply_settings(existing)
        logger.info(f"Settings saved and applied: {list(clean.keys())}")

        # React to specific settings that need runtime actions
        if "enable_chat_bubble" in clean or "enable_amira_card_button" in clean or "enable_amira_automation_button" in clean:
            global _chat_bubble_registered
            _chat_bubble_registered = False  # force re-generation with new flag
            setup_chat_bubble()
            if ENABLE_CHAT_BUBBLE:
                logger.info("Chat bubble: activated via settings UI")
            else:
                logger.info("Chat bubble: deactivated via settings UI")
            if ENABLE_AMIRA_CARD_BUTTON:
                logger.info("Amira card button: activated via settings UI")
            else:
                logger.info("Amira card button: deactivated via settings UI")
            if ENABLE_AMIRA_AUTOMATION_BUTTON:
                logger.info("Amira automation button: activated via settings UI")
            else:
                logger.info("Amira automation button: deactivated via settings UI")

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/uninstall_cleanup', methods=['POST'])
def api_uninstall_cleanup():
    """Cleanup persisted Amira artifacts before uninstall.

    Removes:
    - Chat bubble resources/files
    - /config/amira directory (all addon persistent data)
    Optionally removes dashboards generated under /config/www/dashboards.
    """
    data = request.get_json(silent=True) or {}
    include_dashboards = bool(data.get("include_dashboards", False))

    removed: List[str] = []
    errors: List[str] = []

    # 1) Remove bubble resources and JS artifacts.
    try:
        cleanup_chat_bubble()
        removed.append("bubble_resources_and_js")
    except Exception as e:
        errors.append(f"bubble_cleanup: {e}")

    # 2) Clear in-memory conversation/session state.
    try:
        conversations.clear()
        abort_streams.clear()
        read_only_sessions.clear()
        session_last_intent.clear()
        session_last_preview.clear()
        removed.append("runtime_memory_state")
    except Exception as e:
        errors.append(f"runtime_state: {e}")

    # 3) Remove persisted addon data root.
    amira_dir = os.path.join(HA_CONFIG_DIR, "amira")
    try:
        if os.path.isdir(amira_dir):
            shutil.rmtree(amira_dir)
            removed.append(amira_dir)
    except Exception as e:
        errors.append(f"{amira_dir}: {e}")

    # 4) Optional: remove generated dashboards folder.
    if include_dashboards:
        dashboards_dir = os.path.join(HA_CONFIG_DIR, "www", "dashboards")
        try:
            if os.path.isdir(dashboards_dir):
                shutil.rmtree(dashboards_dir)
                removed.append(dashboards_dir)
        except Exception as e:
            errors.append(f"{dashboards_dir}: {e}")

    logger.info(
        f"Uninstall cleanup executed: removed={len(removed)} include_dashboards={include_dashboards} "
        f"errors={len(errors)}"
    )
    return jsonify({
        "success": len(errors) == 0,
        "removed": removed,
        "errors": errors,
        "include_dashboards": include_dashboards,
    }), (200 if len(errors) == 0 else 207)


# Register blueprints
from routes import register_blueprints
register_blueprints(app)

if __name__ == "__main__":
    logger.info(f"Provider: {AI_PROVIDER} | Model: {get_active_model()}")
    _OAUTH_PROVIDERS = {"openai_codex", "claude_web", "chatgpt_web", "gemini_web", "perplexity_web"}
    if AI_PROVIDER in _OAUTH_PROVIDERS:
        logger.info("API Key: OAuth-based (use 🔑 button in UI)")
    else:
        logger.info(f"API Key: {'configured' if get_api_key() else 'NOT configured'}")
    # get_ha_token() è già definita sopra, quindi qui è sicuro
    logger.info(f"HA Token: {'available' if get_ha_token() else 'NOT available'}")
    
    # Log memory system status
    if MEMORY_AVAILABLE:
        try:
            file_cache = memory.get_config_file_cache()
            logger.info("✨ File memory cache (Layer 2) initialized for config_edit")
        except Exception as e:
            logger.warning(f"File memory cache initialization: {e}")
    
    # Log prompt caching status
    if ANTHROPIC_PROMPT_CACHING:
        logger.info("💾 Anthropic prompt caching ENABLED for config_edit (ephemeral)")
    else:
        logger.debug("Anthropic prompt caching disabled")

    # MCP initialization is handled by initialize_mcp() called from server.py
    pass

    # Initialize fallback chain if available (legacy provider-level)
    if FALLBACK_AVAILABLE:
        try:
            provider_order = [AI_PROVIDER]  # Primary provider
            available_providers = []
            if ANTHROPIC_API_KEY:
                available_providers.append("anthropic")
            if OPENAI_API_KEY:
                available_providers.append("openai")
            if GOOGLE_API_KEY:
                available_providers.append("google")
            if GITHUB_TOKEN:
                available_providers.append("github")
            if NVIDIA_API_KEY:
                available_providers.append("nvidia")
            
            if available_providers:
                fallback.initialize_fallback_chain(available_providers[:3])
                logger.info(f"🔄 Fallback chain: {' → '.join(available_providers[:3])}")
        except Exception as e:
            logger.warning(f"Fallback chain initialization: {e}")

    # Initialize Model Catalog (OpenClaw-style)
    if MODEL_CATALOG_AVAILABLE:
        try:
            cat = model_catalog.get_catalog()
            cat_stats = cat.stats()
            logger.info(f"📚 Model Catalog: {cat_stats['total_models']} models, "
                        f"{cat_stats['vision_models']} vision, "
                        f"{cat_stats['reasoning_models']} reasoning, "
                        f"{cat_stats['tool_use_models']} tool_use")
        except Exception as e:
            logger.warning(f"Model catalog initialization: {e}")

    # Initialize Agent Config (OpenClaw-style)
    if AGENT_CONFIG_AVAILABLE:
        try:
            mgr = agent_config.get_agent_manager()
            mgr_stats = mgr.stats()
            active = mgr.get_active_agent()
            active_name = active.identity.name if active else "none"
            logger.info(f"🤖 Agent Manager: {mgr_stats['enabled_agents']} agents, "
                        f"active='{active_name}'")
            # Sync agent identity with global AGENT_NAME/AGENT_AVATAR
            if active:
                AGENT_NAME = active.identity.name
                AGENT_AVATAR = active.identity.emoji
        except Exception as e:
            logger.warning(f"Agent config initialization: {e}")

    # Initialize Model Fallback (OpenClaw-style)
    if MODEL_FALLBACK_AVAILABLE:
        logger.info("⚡ Model Fallback engine ready (per-model cooldowns + probe)")
    
    # Initialize semantic cache if available
    if SEMANTIC_CACHE_AVAILABLE:
        try:
            semantic_cache.initialize_semantic_cache(max_entries=100, threshold=0.85)
            logger.info("💾 Semantic cache initialized (threshold: 85%)")
        except Exception as e:
            logger.warning(f"Semantic cache initialization: {e}")
    
    # Initialize quality metrics if available
    if QUALITY_METRICS_AVAILABLE:
        logger.info("📊 Response quality metrics initialized")

    # Initialize image support if available
    if IMAGE_SUPPORT_AVAILABLE:
        try:
            image_support.initialize_image_analyzer()
            logger.info("🖼 Image analyzer (vision) initialized")
        except Exception as e:
            logger.warning(f"Image support initialization: {e}")

    # Initialize scheduled tasks if available
    if SCHEDULED_TASKS_AVAILABLE:
        try:
            def _scheduled_message_callback(task_id: str, message: str):
                try:
                    port = int(os.getenv("PORT", 7766))
                    requests.post(
                        f"http://127.0.0.1:{port}/api/chat",
                        json={"message": message, "session_id": f"cron_{task_id}", "stream": False},
                        timeout=60,
                    )
                except Exception as _e:
                    logger.warning(f"Scheduled task message delivery failed: {_e}")

            scheduler = scheduled_tasks.initialize_scheduler(
                check_interval=60,
                message_callback=_scheduled_message_callback,
            )

            if MEMORY_AVAILABLE:
                def _memory_trim():
                    try:
                        history_file = getattr(memory, 'HISTORY_FILE', None)
                        if history_file and os.path.exists(history_file):
                            with open(history_file, encoding="utf-8") as f:
                                lines = f.readlines()
                            if len(lines) > 500:
                                with open(history_file, "w", encoding="utf-8") as f:
                                    f.writelines(lines[-500:])
                                logger.info("✂️ HISTORY.md trimmed to last 500 lines")
                    except Exception as _e:
                        logger.warning(f"Memory trim failed: {_e}")

                scheduler.register_task(
                    "memory_trim", "Trim HISTORY.md", "0 0 * * *", _memory_trim,
                    description="Mantiene HISTORY.md sotto 500 righe (esegue a mezzanotte)",
                    builtin=True,
                )

            logger.info("⏰ Task scheduler initialized")
        except Exception as e:
            logger.warning(f"Scheduled tasks initialization: {e}")

    # Initialize voice transcription if available
    if VOICE_TRANSCRIPTION_AVAILABLE:
        try:
            voice_transcription.initialize_voice_system()
            logger.info("🎙 Voice transcription (Whisper) initialized")
        except Exception as e:
            logger.warning(f"Voice transcription initialization: {e}")

    # Validate provider/model compatibility
    is_valid, error_msg = validate_model_provider_compatibility()
    if not is_valid:
        logger.warning(error_msg)
        # Auto-fix: reset to provider default model
        default_model = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("model", "")
        if default_model:
            AI_MODEL = default_model
            fix_msgs = {
                "en": f"✅ AUTO-FIX: Model automatically changed to '{MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (default for {AI_PROVIDER})",
                "it": f"✅ AUTO-FIX: Modello cambiato automaticamente a '{MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (default per {AI_PROVIDER})",
                "es": f"✅ AUTO-FIX: Modelo cambiado automáticamente a '{MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (predeterminado para {AI_PROVIDER})",
                "fr": f"✅ AUTO-FIX: Modèle changé automatiquement en '{MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (par défaut pour {AI_PROVIDER})"
            }
            logger.warning(fix_msgs.get(LANGUAGE, fix_msgs["en"]))

    # --- Migrate old HTML dashboards to /config/www/dashboards/ and fix iframe URLs ---
    def migrate_html_dashboards():
        """Move dashboards from .html_dashboards/ to www/dashboards/ and update Lovelace iframe URLs."""
        try:
            old_dir = os.path.join(HA_CONFIG_DIR, ".html_dashboards")
            new_dir = os.path.join(HA_CONFIG_DIR, "www", "dashboards")

            # Migrate files from old to new location
            migrated_files = set()
            if os.path.isdir(old_dir):
                os.makedirs(new_dir, exist_ok=True)
                import shutil
                for fname in os.listdir(old_dir):
                    if fname.endswith(".html"):
                        src = os.path.join(old_dir, fname)
                        dst = os.path.join(new_dir, fname)
                        if not os.path.exists(dst):
                            shutil.copy2(src, dst)
                            migrated_files.add(fname.replace(".html", ""))
                            logger.info(f"📦 Migrated dashboard: {fname} → www/dashboards/")

            # Collect all dashboard names (both migrated and existing)
            html_names = set()
            for d in [new_dir, old_dir]:
                if os.path.isdir(d):
                    for fname in os.listdir(d):
                        if fname.endswith(".html"):
                            html_names.add(fname.replace(".html", ""))
                    for fname in os.listdir(d):
                        if fname.endswith(".html"):
                            html_names.add(fname.replace(".html", ""))
            if not html_names:
                return

            # Update Lovelace iframe URLs: /api/hassio_ingress/.../custom_dashboards/x → /local/dashboards/x.html
            ws_dashboards = call_ha_websocket("lovelace/dashboards/list")
            if not isinstance(ws_dashboards, list):
                ws_dashboards = ws_dashboards.get("result", []) if isinstance(ws_dashboards, dict) else []

            fixed = 0
            for dash in ws_dashboards:
                url_path = dash.get("url_path", "")
                if url_path not in html_names:
                    continue

                try:
                    config = call_ha_websocket("lovelace/config", url_path=url_path)
                    if isinstance(config, dict) and "result" in config:
                        config = config["result"]
                except Exception:
                    continue

                if url_path not in html_names:
                    continue

                try:
                    config = call_ha_websocket("lovelace/config", url_path=url_path)
                    if isinstance(config, dict) and "result" in config:
                        config = config["result"]
                except Exception:
                    continue

                if not isinstance(config, dict):
                    continue

                views = config.get("views", [])
                changed = False
                for view in views:
                    for card in view.get("cards", []):
                        if card.get("type") != "iframe":
                            continue
                        card_url = card.get("url", "")
                        # Fix old Ingress URLs → stable /local/ URL
                        if "/api/hassio_ingress/" in card_url and "/custom_dashboards/" in card_url:
                            dash_name = card_url.split("/custom_dashboards/")[-1]
                            if not dash_name.endswith(".html"):
                                dash_name += ".html"
                            new_url = f"/local/dashboards/{dash_name}"
                            card["url"] = new_url
                            changed = True

                if changed:
                    try:
                        call_ha_websocket("lovelace/config/save", url_path=url_path, config={"views": views})
                        fixed += 1
                        logger.info(f"🔗 Migrated iframe URL for dashboard: {url_path} → /local/dashboards/")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to update iframe URL for {url_path}: {e}")

            if migrated_files:
                logger.info(f"📦 Migrated {len(migrated_files)} dashboard file(s) to www/dashboards/")
            if fixed:
                logger.info(f"🔗 Updated {fixed} Lovelace iframe URL(s) to /local/dashboards/")
        except Exception as e:
            logger.warning(f"⚠️ Dashboard migration error: {e}")

    migrate_html_dashboards()

    # Initialize messaging bots (Telegram + WhatsApp)
    start_messaging_bots()

    # Use Waitress production WSGI server instead of Flask development server
    from waitress import serve
    logger.info(f"Starting production server on 0.0.0.0:{API_PORT}")
    serve(app, host="0.0.0.0", port=API_PORT, threads=6)
