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
from core.translations import LANGUAGE_TEXT, get_lang_text, tr, set_current_language
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
    import skills
    SKILLS_AVAILABLE = True
except ImportError:
    SKILLS_AVAILABLE = False

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
    import discord_bot
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
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "")
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
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_ALLOWED_CHANNEL_IDS = os.getenv("DISCORD_ALLOWED_CHANNEL_IDS", "")
DISCORD_ALLOWED_USER_IDS = os.getenv("DISCORD_ALLOWED_USER_IDS", "")
# Clean bashio 'null' values for messaging tokens
for _msg_key in (
    "TELEGRAM_BOT_TOKEN",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_WHATSAPP_FROM",
    "DISCORD_BOT_TOKEN",
    "DISCORD_ALLOWED_CHANNEL_IDS",
    "DISCORD_ALLOWED_USER_IDS",
):
    if globals()[_msg_key] in ("null", "None", "none", "NULL"):
        globals()[_msg_key] = ""
# Per-channel enable/disable toggle (Telegram / WhatsApp / Discord)
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "true").lower() not in ("false", "0", "no")
ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "true").lower() not in ("false", "0", "no")
ENABLE_DISCORD = os.getenv("ENABLE_DISCORD", "true").lower() not in ("false", "0", "no")

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
DISCORD_ALLOWED_CHANNELS: set = _parse_allowed_ids(DISCORD_ALLOWED_CHANNEL_IDS)
DISCORD_ALLOWED_USERS: set = _parse_allowed_ids(DISCORD_ALLOWED_USER_IDS)
ENABLE_MCP = os.getenv("ENABLE_MCP", "true").lower() not in ("false", "0", "")
MCP_CONFIG_FILE = os.getenv("MCP_CONFIG_FILE", "/config/amira/mcp_config.json")
FALLBACK_ENABLED = os.getenv("FALLBACK_ENABLED", "true").lower() not in ("false", "0", "no")
CHAT_INTERACTION_MODE = os.getenv("CHAT_INTERACTION_MODE", "strict").strip().lower()


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
        elif key == "interaction_mode":
            value = str(value).lower().strip()
            if value not in ("strict", "lean"):
                value = "strict"
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
        elif key in ("discord_allowed_channel_ids", "discord_allowed_user_ids"):
            raw_str = str(value)
            _g[gvar] = raw_str
            os.environ[gvar] = raw_str
            if key == "discord_allowed_channel_ids":
                _g["DISCORD_ALLOWED_CHANNELS"] = _parse_allowed_ids(raw_str)
            else:
                _g["DISCORD_ALLOWED_USERS"] = _parse_allowed_ids(raw_str)
            continue
        # Set Python global
        _g[gvar] = value
        if key == "language":
            # Keep core.translations runtime language aligned with API runtime config
            set_current_language(value)
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
        # Backward compatibility: runtime_selection may contain display labels
        # (e.g. "NVIDIA: Llama 3.3 70B Instruct"). Normalize to technical IDs.
        model = normalize_model_name(model)
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
            # Ollama needs the user-configured base_url to reach the server.
            # Skip entirely if no URL is configured — avoids a useless connection attempt.
            if _pid == "ollama":
                if not OLLAMA_BASE_URL:
                    continue
                import logging as _log2
                _log2.getLogger(__name__).info(f"Ollama: probing {OLLAMA_BASE_URL} ...")
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
            elif _pid == "ollama":
                import logging as _log2
                _log2.getLogger(__name__).warning(
                    f"Ollama: no models found at {OLLAMA_BASE_URL} — server unreachable or no models installed"
                )
        except Exception as _e:
            _dynamic_fail.append(f"{_pid}:{_e.__class__.__name__}:{_e}")
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
# Pending confirmation/follow-up context per session (lightweight state machine)
session_pending_context: Dict[str, Dict[str, Any]] = {}
# Active skill per session — re-injected on follow-up messages so the LLM keeps the skill context
session_active_skill: Dict[str, str] = {}
_PREVIEW_MATCH_TTL_SECONDS = 3600
_PENDING_CONTEXT_TTL_SECONDS = 7200

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
        # Keep only last N sessions (configurable), 50 messages each.
        # Sort by session timestamp so all sources (bubble, card, chat) are treated
        # equally and older sessions are evicted regardless of insertion order.
        def _session_ts(sid: str) -> int:
            if sid.startswith(("bubble_", "card_")) and "_" in sid:
                try:
                    return int(sid.split("_")[1], 36)
                except Exception:
                    pass
            try:
                return int(sid)
            except Exception:
                return 0
        sorted_sessions = sorted(conversations.items(), key=lambda x: _session_ts(x[0]))
        trimmed: Dict[str, List[Dict]] = {}
        for sid, msgs in sorted_sessions[-MAX_CONVERSATIONS:]:
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
        system_instruction=tools.get_system_prompt(),
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
        elif lang == "es":
            warning = f"\n\n⚠️ **Atención: algunos entity ID podrían no existir.**\n"
            warning += f"No encontrados: {inv_list}\n"
        elif lang == "fr":
            warning = f"\n\n⚠️ **Attention : certains entity ID pourraient ne pas exister.**\n"
            warning += f"Non trouvés : {inv_list}\n"
        else:
            warning = f"\n\n⚠️ **Warning: some entity IDs may not exist.**\n"
            warning += f"Not found: {inv_list}\n"

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


# ── Conversation history compaction ───────────────────────────────────────────
# Tool results can be enormous (e.g. get_dashboard_config returns the full
# Lovelace YAML — easily 300k+ chars).  Storing the raw result in conversation
# history means every subsequent turn re-sends that blob to the model, quickly
# overflowing the context window and forcing the model to re-fetch.
#
# Solution: when saving messages to conversations[session_id], replace tool
# results larger than MAX_TOOL_RESULT_HISTORY_CHARS with a smart condensed
# summary.  The FULL result is still used in the current round (the model works
# on the real data); only what goes into history is condensed.

MAX_TOOL_RESULT_HISTORY_CHARS = 3000


def _condense_tool_result_for_history(tool_name: str, result_str: str) -> str:
    """Return a condensed version of a large tool result for history storage."""
    if len(result_str) <= MAX_TOOL_RESULT_HISTORY_CHARS:
        return result_str
    note = f"[history-condensed — full result was {len(result_str)} chars; re-call the tool only if you need the complete data]"
    try:
        data = json.loads(result_str)
    except Exception:
        return result_str[:MAX_TOOL_RESULT_HISTORY_CHARS] + f" … {note}"

    if tool_name == "get_dashboard_config":
        views = data.get("views", [])
        all_types: set = set()
        view_info = []
        for v in views:
            cards = v.get("cards", [])
            types = {c.get("type", "?") for c in cards if isinstance(c, dict)}
            all_types |= types
            view_info.append(f"{v.get('title', '?')} ({v.get('cards_count', len(cards))} cards)")
        return json.dumps({
            "url_path": data.get("url_path", "?"),
            "views_count": len(views),
            "views": view_info,
            "card_types_used": sorted(all_types),
            "_note": note,
        }, ensure_ascii=False)

    if tool_name in ("get_entities", "search_entities", "get_integration_entities"):
        items = data if isinstance(data, list) else data.get("entities", data.get("result", []))
        if isinstance(items, list):
            return json.dumps({
                "count": len(items),
                "entity_ids": [e.get("entity_id", str(e)) for e in items[:40]],
                "_note": note,
            }, ensure_ascii=False)

    if tool_name == "get_automations":
        items = data if isinstance(data, list) else []
        return json.dumps({
            "count": len(items),
            "automations": [a.get("alias", a.get("id", "?")) for a in items[:40]],
            "_note": note,
        }, ensure_ascii=False)

    # Generic fallback: truncate
    return result_str[:MAX_TOOL_RESULT_HISTORY_CHARS] + f" … {note}"


def _compact_messages_for_history(messages: list) -> list:
    """Condense large tool results in a message list before storing in history.

    Handles both Anthropic format (role=user, content=[{type:tool_result}])
    and OpenAI/OpenRouter format (role=tool, content=str).
    """
    # Build tool_use_id → tool_name map from assistant messages
    tool_id_to_name: dict = {}
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_id_to_name[block.get("id", "")] = block.get("name", "")
            for tc in msg.get("tool_calls", []):
                if isinstance(tc, dict):
                    fn = tc.get("function", {})
                    tool_id_to_name[tc.get("id", "")] = fn.get("name", "")

    compacted = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Anthropic format: role=user, content=[{type:tool_result, ...}]
        if role == "user" and isinstance(content, list):
            new_blocks = []
            changed = False
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    rc = block.get("content", "")
                    if isinstance(rc, str) and len(rc) > MAX_TOOL_RESULT_HISTORY_CHARS:
                        tname = tool_id_to_name.get(block.get("tool_use_id", ""), "")
                        block = {**block, "content": _condense_tool_result_for_history(tname, rc)}
                        changed = True
                new_blocks.append(block)
            if changed:
                msg = {**msg, "content": new_blocks}

        # OpenAI/OpenRouter format: role=tool, content=str
        elif role == "tool" and isinstance(content, str) and len(content) > MAX_TOOL_RESULT_HISTORY_CHARS:
            tname = msg.get("name", tool_id_to_name.get(msg.get("tool_call_id", ""), ""))
            msg = {**msg, "content": _condense_tool_result_for_history(tname, content)}

        compacted.append(msg)
    return compacted


def _compact_messages_inflight(messages: list, start_idx: int = 0) -> None:
    """Condense large tool results in-place to reduce context size before each API call.

    Only operates on messages[start_idx:] (messages added during this request),
    so that stored history dicts are never mutated.

    All tool results exceeding MAX_TOOL_RESULT_HISTORY_CHARS are condensed,
    including those from the most recent round — the model has already processed
    them to produce the current round's tool calls, so full data is not needed again.
    Small results (below the threshold) are always kept intact.

    Operates in-place (mutates dicts in messages).  start_idx should be
    conv_length_before so that stored history dicts are never touched.
    """
    new_msgs = messages[start_idx:]
    _total_saved = 0

    for msg in new_msgs:
        role = msg.get("role", "")

        # OpenAI/OpenRouter format: role=tool
        if role == "tool":
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > MAX_TOOL_RESULT_HISTORY_CHARS:
                tname = msg.get("name", "")
                condensed = _condense_tool_result_for_history(tname, content)
                if condensed != content:
                    _total_saved += len(content) - len(condensed)
                    msg["content"] = condensed

        # Anthropic format: role=user, content=[{type:tool_result}]
        elif role == "user" and isinstance(msg.get("content"), list):
            changed = False
            new_blocks = []
            for block in msg["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    rc = block.get("content", "")
                    if isinstance(rc, str) and len(rc) > MAX_TOOL_RESULT_HISTORY_CHARS:
                        condensed = _condense_tool_result_for_history("", rc)
                        if condensed != rc:
                            _total_saved += len(rc) - len(condensed)
                            block = {**block, "content": condensed}
                            changed = True
                new_blocks.append(block)
            if changed:
                msg["content"] = new_blocks

    if _total_saved > 0:
        logger.info(
            f"🗜️ In-flight context compaction: freed ~{_total_saved // 1000}k chars"
        )


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
            return "❌ " + event.get("message", tr("err_unknown_error", "Unknown error"))
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


def _find_invalid_response_variable_in_conditions(tool_name: str, raw_args: dict) -> str:
    """Return offending response_variable name if used inside conditions templates.

    In Home Assistant, conditions are evaluated before actions. Variables created by
    action steps (e.g. response_variable from weather.get_forecasts) are not available
    in conditions.
    """
    if not isinstance(raw_args, dict):
        return ""

    if tool_name in {"preview_automation_change", "update_automation"}:
        payload = (_normalize_automation_change_args(raw_args) or {}).get("changes", {}) or {}
    else:
        payload = raw_args
    if not isinstance(payload, dict):
        return ""

    actions = payload.get("actions", payload.get("action", []))
    if isinstance(actions, dict):
        actions = [actions]
    if not isinstance(actions, list):
        actions = []

    response_vars = set()
    for step in actions:
        if not isinstance(step, dict):
            continue
        rv = step.get("response_variable")
        if isinstance(rv, str) and rv.strip():
            response_vars.add(rv.strip())

    if not response_vars:
        return ""

    conditions = payload.get("conditions", payload.get("condition", []))
    if isinstance(conditions, dict):
        conditions = [conditions]
    if not isinstance(conditions, list):
        conditions = []

    template_blobs = []

    def _collect_templates(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and k in {"value_template", "template"} and isinstance(v, str):
                    template_blobs.append(v)
                _collect_templates(v)
        elif isinstance(node, list):
            for it in node:
                _collect_templates(it)

    _collect_templates(conditions)
    if not template_blobs:
        return ""

    for rv in response_vars:
        pat = re.compile(rf"\b{re.escape(rv)}\b")
        if any(pat.search(tpl or "") for tpl in template_blobs):
            return rv
    return ""


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
    logger.chat(f"📨 [{AI_PROVIDER}]: {_strip_context_for_log(user_message)}")
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


def _normalize_user_message_for_routing(user_message: str) -> str:
    """Remove synthetic context/html blocks and return a normalized lowercase text."""
    try:
        msg = _strip_context_blocks(user_message or "")
        msg = re.sub(r'\[CURRENT_DASHBOARD_HTML\][\s\S]*?\[/CURRENT_DASHBOARD_HTML\]', '', msg, flags=re.IGNORECASE)
        msg = re.sub(r'\s+', ' ', msg).strip().lower()
        return msg
    except Exception:
        return str(user_message or "").strip().lower()


def _all_lang_keywords(key: str) -> set[str]:
    """Collect keyword entries across all configured languages."""
    out: set[str] = set()
    try:
        for _lang_data in (KEYWORDS or {}).values():
            vals = _lang_data.get(key, []) if isinstance(_lang_data, dict) else []
            if isinstance(vals, list):
                for v in vals:
                    if isinstance(v, str) and v.strip():
                        out.add(v.strip().lower())
    except Exception:
        pass
    return out


def _looks_like_new_automation_request(user_message: str) -> bool:
    msg = _normalize_user_message_for_routing(user_message)
    automation_markers = (
        "automaz", "automation", "automatiz", "automatisation", "automatización", "automatisation"
    )
    if not any(m in msg for m in automation_markers):
        return False
    create_signals = {
        "nuova automazione", "nuove automazioni", "new automation", "new automations",
        "crea automazione", "creare automazione", "create automation", "add automation",
        "aggiungi automazione", "un'altra automazione", "un altra automazione", "altra automazione",
        "nueva automatización", "nuevas automatizaciones", "crear automatización", "añadir automatización",
        "nouvelle automatisation", "nouvelles automatisations", "créer automatisation", "ajouter automatisation",
        "új automatizálás", "új automatizálást", "automatizálás létrehozása", "hozz létre automatizálást",
    }
    modify_signals = set(_all_lang_keywords("modify")) | {
        "modifica automazione", "modify automation", "update automation",
        "aggiorna automazione", "cambia automazione",
        "modificar automatización", "actualizar automatización",
        "modifier automatisation", "mettre à jour automatisation",
        "módosítsd az automatizálást", "automatizálás módosítása", "változtasd az automatizálást",
    }
    has_create = any(s in msg for s in create_signals)
    has_modify = any(s in msg for s in modify_signals)
    return bool(has_create and not has_modify)


def _has_explicit_automation_target(user_message: str) -> bool:
    """True only when user clearly targets an existing automation."""
    raw = str(user_message or "")
    msg = _normalize_user_message_for_routing(raw)
    raw_lower = raw.lower()
    # Bubble context explicitly scoped to one automation
    if re.search(r'\[context:[^\]]*automation\s+id=["\']*\d+', raw, re.IGNORECASE):
        return True
    # Explicit automation entity/id references
    if re.search(r'\bautomation\.[a-z0-9_]+\b', msg):
        return True
    if re.search(r'\b(?:id|automation_id)\s*[:=]?\s*\d{4,}\b', msg):
        return True
    # Bare numeric automation ID (10+ digits) with automation/automatizmus context
    if re.search(r'\d{10,}', msg) and any(m in msg for m in (
        "automaz", "automation", "automatiz", "automatismus", "automatizmust",
    )):
        return True
    # Pending-context booster: check the RAW message (including [CONTEXT:...] blocks)
    # because _normalize strips them. The booster only fires on confirmation replies,
    # so the presence of [CONTEXT:] + a numeric automation ID is reliable enough.
    if "[CONTEXT:" in raw and re.search(r'\d{10,}', raw_lower):
        return True
    # Quoted automation name + modify intent is explicit enough
    quoted_name = re.search(r'["“][^"”]{3,}["”]', raw)
    modify_terms = sorted(_all_lang_keywords("modify") | {
        "modifica", "modify", "update", "aggiorna", "cambia", "edit",
        "modificar", "actualizar", "modifier", "changer", "mettre à jour",
        "módosítsd", "módosít", "változtasd", "szerkeszd", "frissítsd",
    }, key=len, reverse=True)
    has_modify_intent = any(t and t in msg for t in modify_terms)
    return bool(quoted_name and has_modify_intent)


def _extract_pending_context_from_assistant(text: str) -> Optional[str]:
    """Extract a compact actionable context when assistant asks for confirmation."""
    t = str(text or "").strip()
    if not t:
        return None
    tl = t.lower()
    ask_terms = (
        "confermi", "conferma", "procedo", "procedi", "confermi e",
        "confirm", "confirm?", "proceed", "apply", "shall i",
        "confirma", "confirmas", "proceder", "procedo con",
        "confirme", "procède", "appliquer",
        "jóváhagyod", "alkalmazzam", "módosítsam", "végrehajtom", "mehet",
    )
    if "?" not in t and not any(k in tl for k in ask_terms):
        return None
    summary = re.sub(r"\s+", " ", t).strip()
    if len(summary) > 420:
        summary = summary[:420].rstrip() + "..."
    return summary


def _is_short_followup_reply(user_message: str) -> bool:
    txt = _normalize_user_message_for_routing(user_message)
    if not txt:
        return False
    words = [w for w in txt.split(" ") if w]
    if len(words) <= 8 and len(txt) <= 80:
        return True
    followup_markers = ("manca", "seconda", "2", "continua", "vai avanti", "next", "missing", "folytasd", "tovább", "következő", "most próbáld", "hiányzik")
    return any(m in txt for m in followup_markers)


def _is_confirmation_reply(user_message: str) -> bool:
    txt = _normalize_user_message_for_routing(user_message)
    if not txt:
        return False
    confirms = _all_lang_keywords("confirm") | {"yes", "ok", "okay", "si", "sì", "oui", "vale", "igen", "rendben", "oké", "mehet", "csináld", "rajta", "persze", "próbáld", "tovább"}
    return txt in confirms


def stream_chat_with_ai(user_message: str, session_id: str = "default", image_data: str = None, read_only: bool = False, voice_mode: bool = False, req_language: str = None):
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
    from routes.ui_routes import _check_provider_sdk
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

    if image_data:
        logger.chat(f"📨 [{AI_PROVIDER}] with image: {_strip_context_for_log(user_message)[:50]}...")
    else:
        logger.chat(f"📨 [{AI_PROVIDER}]: {_strip_context_for_log(user_message)}")

    _lean_mode = str(CHAT_INTERACTION_MODE).lower().strip() == "lean"

    # Reinforce short follow-ups (e.g. "yes", "manca la 2") with pending context
    # captured from the previous assistant confirmation question.
    if not _lean_mode:
        _pending = session_pending_context.get(session_id)
        if _pending:
            try:
                _age = time.time() - float(_pending.get("ts", 0))
            except Exception:
                _age = _PENDING_CONTEXT_TTL_SECONDS + 1
            if _age > _PENDING_CONTEXT_TTL_SECONDS:
                session_pending_context.pop(session_id, None)
                _pending = None
        if _pending and (_is_confirmation_reply(user_message) or _is_short_followup_reply(user_message)):
            _summary = str(_pending.get("summary", "") or "").strip()
            if _summary:
                user_message = (
                    f"{user_message}\n\n"
                    f"[CONTEXT: Pending request from previous assistant turn]\n"
                    f"{_summary}\n"
                    f"[/CONTEXT]"
                )
                logger.info(f"Pending-context booster injected for session {session_id}")

    # Get previous intent for confirmation continuity
    prev_intent = session_last_intent.get(session_id)

    # Step 1: LOCAL intent detection (preliminary — for bubble contexts and chat)
    # Simplified LLM-first approach: most intents are "auto" (all tools, LLM decides)
    intent_info = intent.detect_intent(user_message, "", previous_intent=prev_intent)
    intent_name = intent_info["intent"]

    # Per-request language override: if the caller (e.g. bubble) specifies a language
    # that differs from the global LANGUAGE, patch language-specific prompt snippets
    # so the LLM replies in the user's own language regardless of the server setting.
    _eff_language = (req_language or "").lower()[:2]
    if _eff_language and _eff_language != LANGUAGE and _eff_language in LANGUAGE_TEXT:
        _cur_lang_text = LANGUAGE_TEXT.get(LANGUAGE, {})
        _req_lang_text = LANGUAGE_TEXT.get(_eff_language, {})
        _language_prompt_keys = (
            "respond_instruction",
            "strict_language_lock",
            "show_yaml_rule",
            "confirm_entity_rule",
            "confirm_delete_rule",
            "example_vs_create_rule",
        )
        if intent_info.get("prompt"):
            _prompt = intent_info["prompt"]
            for _k in _language_prompt_keys:
                _cur_txt = _cur_lang_text.get(_k, "")
                _req_txt = _req_lang_text.get(_k, "")
                if _cur_txt and _req_txt and _cur_txt in _prompt:
                    _prompt = _prompt.replace(_cur_txt, _req_txt)
            # Ensure the request-specific language lock is present even if the source
            # prompt did not include the global-language snippet.
            _req_lang_lock = _req_lang_text.get("strict_language_lock", "")
            if _req_lang_lock and _req_lang_lock not in _prompt:
                _prompt = _prompt + "\n\n" + _req_lang_lock
            intent_info["prompt"] = _prompt
        logger.info(f"Per-request language override: {LANGUAGE} → {_eff_language}")

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

    import re as _re_skill
    _is_skill_msg = bool(_re_skill.match(r"^/[a-z][a-z0-9_-]+", user_message.strip().lower()))

    if intent_name != "chat" or _is_skill_msg:
        if _lean_mode and intent_name == "auto" and not _is_skill_msg:
            # Lean mode: keep conversation natural and avoid heavy preloaded
            # context that often makes replies feel templated.
            smart_context = ""
            logger.info("Lean mode: smart context preload skipped for auto intent")
        else:
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

        # Step 3: Re-detect intent WITH full smart context — but skip for skill commands
        # to avoid overriding the chat intent we just set.
        if not _is_skill_msg:
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
    _has_explicit_auto_target = _has_explicit_automation_target(user_message)
    _looks_new_auto_req = _looks_like_new_automation_request(user_message)
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
            "- NEVER put technical info in parentheses like '(switch.kitchen_light: off)' or '(sensor.temp: 22)'.\n"
            "- NEVER list all entities/devices/switches — just summarize (e.g. 'You have 5 lights on' instead of listing them).\n"
            "- Do NOT use markdown, bullet points, numbered lists, code blocks, or special formatting.\n"
            "- ABSOLUTELY NO EMOJI — never use 😊🎉👍 or any emoji/emoticon. The TTS will try to read them.\n"
            "- Do NOT use slashes '/' in the response.\n"
            "- Use natural spoken language matching the configured language, as if talking to a person.\n"
            "- For temperatures: 'Living room is 22 degrees' (no entity IDs).\n"
            "- For states: 'Bedroom light is on' (no technical names).\n"
            "- For actions: confirm briefly: 'Done, I turned off the bedroom light'.\n"
            "- For queries about multiple items: give a summary count and mention only the most relevant ones by their friendly name.\n"
            "- Never use generic preambles like 'here are the results' — go straight to the answer.\n"
        )
        intent_info["prompt"] = intent_info["prompt"] + voice_instruction

    # Inject skill instructions into system prompt.
    # - If message starts with /skill-name: activate/update the skill for this session.
    # - If no /command but a skill is already active for this session: re-inject it so
    #   follow-up messages (e.g. "si", "add a chart") keep the full skill context.
    if SKILLS_AVAILABLE:
        _skill_name, _remaining = skills.parse_skill_command(user_message)
        if _skill_name:
            # Explicit skill command — activate
            _enriched_prompt = skills.inject_skill_into_prompt(
                _skill_name, intent_info.get("prompt") or ""
            )
            if _enriched_prompt is not None:
                intent_info["prompt"] = _enriched_prompt
                intent_info["active_skill"] = _skill_name
                session_active_skill[session_id] = _skill_name
                if _remaining:
                    user_message = _remaining
                yield {"type": "status", "message": f"Skill: {_skill_name}"}
                yield {"type": "skill_active", "name": _skill_name}
                logger.info(f"Skill '{_skill_name}' injected into system prompt")
            else:
                session_active_skill.pop(session_id, None)
                yield {"type": "status", "message": tr("skill_not_found").format(name=_skill_name)}
        elif session_id in session_active_skill:
            # Follow-up message — re-inject the active skill silently
            _active_skill = session_active_skill[session_id]
            _enriched_prompt = skills.inject_skill_into_prompt(
                _active_skill, intent_info.get("prompt") or ""
            )
            if _enriched_prompt is not None:
                intent_info["prompt"] = _enriched_prompt
                intent_info["active_skill"] = _active_skill
                yield {"type": "skill_active", "name": _active_skill}
                logger.info(f"Skill '{_active_skill}' re-injected for follow-up in session {session_id}")

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
            # Skip injection for chat intent (tools=[]) — no tools should be available.
            if intent_info.get("tools") != []:
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
                            _desc = _tool_info.get('description', '')
                            _server_name = _tool_info.get('server', 'unknown')
                            # For filesystem tools, add root path hint so the LLM
                            # doesn't double-prefix paths (e.g. /config/config).
                            if "filesystem" in _tool_name:
                                _srv_obj = (_mgr.servers or {}).get(_server_name)
                                if _srv_obj:
                                    _srv_args = _srv_obj.config.get("args", [])
                                    _fs_root = next(
                                        (a for a in reversed(_srv_args)
                                         if isinstance(a, str) and a.startswith("/")),
                                        None
                                    )
                                    if _fs_root:
                                        _desc = (
                                            f"{_desc} "
                                            f"[filesystem root: '{_fs_root}'; "
                                            f"pass paths relative to this root, "
                                            f"e.g. '/packages' NOT '{_fs_root}/packages']"
                                        )
                            _mcp_dynamic.append({
                                "type": "function",
                                "function": {
                                    "name": _tool_name,
                                    "description": f"{_desc} (MCP: {_server_name})",
                                    "parameters": _tool_info.get("inputSchema", {"type": "object", "properties": {}}),
                                }
                            })
                        if _mcp_dynamic:
                            intent_info["tool_schemas"] = _schemas + _mcp_dynamic
                            logger.info(f"MCP tools injected into tool_schemas: +{len(_mcp_dynamic)}")
                except Exception as _mcp_inject_err:
                    logger.warning(f"MCP tool schema injection failed: {_mcp_inject_err}")

            # When a skill is active the model only needs to generate content (YAML cards,
            # HTML, etc.) — HA control tools are irrelevant and waste tokens.
            if intent_info.get("active_skill"):
                intent_info["tool_schemas"] = []
                intent_info["tools"] = []
                logger.debug(f"Skill '{intent_info['active_skill']}' active — tool_schemas cleared")

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

        # Pass session_id to providers so they can maintain native conversation state
        # (e.g. claude_web reuses the same claude.ai conversation across turns).
        if intent_info is not None:
            intent_info["session_id"] = session_id

        # Tool execution loop: providers surface tool_calls in the done event;
        # we execute them here and loop until the model produces a final answer.
        _MAX_TOOL_ROUNDS = 8
        _tool_round = 0
        _tool_cache: dict = {}
        _tool_call_history: set = set()  # tracks all (name, args_json) to detect loops
        _duplicate_count = 0             # how many consecutive duplicate rounds
        _deferred_done_event = None      # postpone done for HTML autosave flows
        _skip_tool_extraction = False    # after dedup, skip ToolSimulator next round
        _no_tool_continuation_used = False  # one-shot continuation for max_tokens truncation
        _skill_yaml_repair_used = False  # one-shot format repair for skill card YAML
        _last_write_result = None        # last WRITE tool result (for fallback display)
        _last_success_read_tool = None   # last successful read tool snapshot for loop fallback
        _preview_round_done = False      # True after preview_automation_change executes
        _preview_generated_this_turn = False  # Successful preview generated in this request
        _html_draft_pending_name = ""    # create_html_dashboard draft name pending finalize
        _html_dashboard_saved_this_turn = False
        _write_tools_executed: list = []  # names of write tools actually called this turn
        _html_force_execute_retry_used = False
        _successful_read_tools_count = 0
        _successful_channel_deliveries: set[str] = set()
        _delivery_request_needs_data = bool(
            re.search(
                r"\b(report|riepilogo|summary|produzione|consumo|fotovoltaic|solar|kwh|kw)\b",
                (user_message or "").lower(),
            )
        )

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

        def _build_readonly_loop_fallback(snapshot: dict | None) -> str:
            """Create a deterministic final answer when model loops on read-only tools."""
            if not snapshot:
                return ""
            name = str(snapshot.get("name", "") or "")
            args = snapshot.get("args", {}) or {}
            raw = snapshot.get("result")
            parsed = raw
            try:
                if isinstance(raw, str):
                    parsed = json.loads(raw)
            except Exception:
                parsed = raw

            if name == "get_entities" and isinstance(parsed, list):
                query = str((args or {}).get("query", "") or "").lower()
                want_temp = ("temp" in query) or ("temperat" in query)
                lines = []
                for item in parsed:
                    if not isinstance(item, dict):
                        continue
                    attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
                    device_class = str(attrs.get("device_class", "") or "").lower()
                    if want_temp and device_class != "temperature":
                        continue
                    state = str(item.get("state", "") or "").strip()
                    if state in ("", "unknown", "unavailable", "none", "null"):
                        continue
                    friendly = str(item.get("friendly_name") or item.get("entity_id") or "").strip()
                    unit = str(attrs.get("unit_of_measurement") or "")
                    lines.append(f"- {friendly}: {state}{unit}")
                if lines:
                    return tr(
                        "read_loop_fallback_notice",
                        "⚠️ I collected the data, but the model got stuck in a tool loop. Here are the results found:",
                    ) + "\n" + "\n".join(lines[:12])

            if name == "get_entity_state" and isinstance(parsed, dict):
                eid = str(parsed.get("entity_id") or "")
                friendly = str(parsed.get("friendly_name") or eid)
                state = str(parsed.get("state", "") or "").strip()
                attrs = parsed.get("attributes") if isinstance(parsed.get("attributes"), dict) else {}
                unit = str(attrs.get("unit_of_measurement") or "")
                if state and state not in ("unknown", "unavailable", "none", "null"):
                    return tr(
                        "read_loop_fallback_notice",
                        "⚠️ I collected the data, but the model got stuck in a tool loop. Here are the results found:",
                    ) + "\n" + f"- {friendly}: {state}{unit}"

            return tr(
                "read_loop_fallback_empty",
                "⚠️ I collected data, but there are no usable results to show.",
            )

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

            # Compact tool results from earlier rounds to prevent context overflow.
            # Keeps the most recent batch intact; condenses all older ones.
            # Only kicks in from round 2 onwards (nothing to compact on first call).
            if _tool_round > 1:
                _compact_messages_inflight(messages, conv_length_before)

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
                    logger.warning(
                        tr(
                            "log_fallback_engine_error_try_direct",
                            "Fallback engine error, trying direct: {error}",
                            error=_fb_err,
                        )
                    )
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
            _finish_reason_done = ""

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
                            logger.warning(
                                tr(
                                    "log_html_retry_malformed_tool_call",
                                    "HTML dashboard retry: malformed_function_call with no tool_calls, forcing strict tool call",
                                )
                            )
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
                                    yield {"type": "status", "message": tr("status_html_received_saving", "💾 HTML received, trying to save...")}
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
                            _msg_malformed = tr(
                                "html_malformed_tool_call",
                                "⚠️ The model returned a malformed, non-executable tool call. No dashboard was created.",
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
                                yield {"type": "status", "message": tr("status_html_received_saving", "💾 HTML received, trying to save...")}
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
                            # Skill-mode YAML guardrail (one-shot):
                            # weaker models may ignore fenced YAML or emit malformed card YAML.
                            _active_skill = (intent_info or {}).get("active_skill")
                            if _active_skill and not _skill_yaml_repair_used:
                                _assembled_skill = "".join(_streamed_text_parts).strip()
                                _needs_skill_repair = False
                                try:
                                    import re as _re_skill_yaml
                                    import yaml as _yaml_skill
                                    _m_skill_yaml = _re_skill_yaml.search(
                                        r"```yaml\s*([\s\S]*?)```",
                                        _assembled_skill,
                                        _re_skill_yaml.IGNORECASE,
                                    )
                                    _yaml_text = (_m_skill_yaml.group(1).strip() if _m_skill_yaml else "")
                                    if not _yaml_text:
                                        _needs_skill_repair = True
                                    else:
                                        _parsed = _yaml_skill.safe_load(_yaml_text)
                                        if not isinstance(_parsed, dict):
                                            _needs_skill_repair = True
                                        else:
                                            _tval = str(_parsed.get("type", "") or "").strip().lower()
                                            if _active_skill == "mushroom":
                                                if not _tval.startswith("custom:mushroom-"):
                                                    _needs_skill_repair = True
                                            elif _active_skill == "html-js-card":
                                                if _tval != "custom:html-js-card":
                                                    _needs_skill_repair = True
                                except Exception:
                                    _needs_skill_repair = True

                                if _needs_skill_repair:
                                    _skill_yaml_repair_used = True
                                    _repair_prompt = (
                                        "[SKILL FORMAT REPAIR]\n"
                                        f"Your previous output for skill '{_active_skill}' was not valid/usable YAML.\n"
                                        "Regenerate from scratch and output ONLY one valid Lovelace YAML block.\n"
                                        "- MUST be wrapped in ```yaml ... ``` fences.\n"
                                        "- Do NOT add explanations before or after the code block.\n"
                                        "- Use only entity_ids from CONTEXT/DATA.\n"
                                    )
                                    if _active_skill == "mushroom":
                                        _repair_prompt += "- Card type MUST start with: type: custom:mushroom-\n"
                                    if _active_skill == "html-js-card":
                                        _repair_prompt += "- Card type MUST be exactly: type: custom:html-js-card\n"
                                    if _assembled_skill:
                                        messages.append({"role": "assistant", "content": _assembled_skill})
                                    messages.append({"role": "user", "content": _repair_prompt})
                                    _streamed_text_parts = []
                                    logger.warning(
                                        f"Skill YAML repair retry triggered for skill='{_active_skill}'"
                                    )
                                    yield {
                                        "type": "status",
                                        "message": tr(
                                            "status_skill_format_repair",
                                            "⚠️ Fixing card format automatically...",
                                        ),
                                    }
                                    continue

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
                    yield {"type": "status", "message": tr("status_html_auto_finalizing", "💾 Auto-finalizing HTML draft dashboard...")}
                    _auto_final = tools.execute_tool("create_html_dashboard", {"name": _html_draft_pending_name})
                    _auto_obj = json.loads(_auto_final) if isinstance(_auto_final, str) else _auto_final
                    if isinstance(_auto_obj, dict) and str(_auto_obj.get("status", "")).lower() == "success":
                        _html_dashboard_saved_this_turn = True
                        _html_draft_pending_name = ""
                        _saved_url = _auto_obj.get("dashboard_url") or _auto_obj.get("url") or ""
                        if _saved_url:
                            yield {"type": "status", "message": tr("status_html_dashboard_saved_url", "✅ Dashboard saved: {url}", url=_saved_url)}
                        else:
                            yield {"type": "status", "message": tr("status_html_dashboard_saved_ok", "✅ HTML dashboard saved successfully.")}
                        logger.info("HTML draft auto-finalized successfully")
                    else:
                        logger.warning(
                            tr(
                                "log_html_auto_finalize_failed",
                                "HTML draft auto-finalize failed: {error}",
                                error=_auto_final,
                            )
                        )
                        yield {"type": "status", "message": tr("status_html_auto_finalize_skipped", "⚠️ Draft dashboard was not auto-finalized.")}
                except Exception as _df_err:
                    logger.warning(
                        tr(
                            "log_html_auto_finalize_error",
                            "HTML draft auto-finalize error: {error}",
                            error=_df_err,
                        )
                    )
                    yield {"type": "status", "message": tr("status_html_auto_finalize_error", "⚠️ Draft auto-finalize error: {error}", error=_df_err)}

            # No-tool providers can return finish_reason=max_tokens/length with partial
            # YAML/code output (especially after an internal fallback). Retry once with
            # a strict continuation instruction to complete the response.
            if (
                not _pending_tool_calls
                and _is_no_tool_provider
                and not _no_tool_continuation_used
                and _finish_reason_done in {"max_tokens", "length"}
            ):
                _no_tool_continuation_used = True
                _partial_answer = "".join(_streamed_text_parts).strip()
                if _partial_answer:
                    try:
                        from providers.tool_simulator import clean_response_text as _crt_cont
                        _partial_answer = _crt_cont(_partial_answer)
                    except Exception:
                        pass
                _cont_user_msg = (
                    "[AUTO-CONTINUE]\n"
                    "Your previous answer was cut due to token limit.\n"
                    "Continue EXACTLY from the last line.\n"
                    "- Do NOT repeat any previous text.\n"
                    "- If you were writing a YAML code block, continue from where it stopped and close fences.\n"
                    "- Output only the missing continuation."
                )
                if _partial_answer:
                    messages.append({"role": "assistant", "content": _partial_answer})
                messages.append({"role": "user", "content": _cont_user_msg})
                _streamed_text_parts = []
                logger.warning(
                    tr(
                        "log_no_tool_truncated_retry",
                        "No-tool provider output truncated (finish_reason={reason}) — running one auto-continue round",
                        reason=_finish_reason_done,
                    )
                )
                yield {
                    "type": "status",
                    "message": tr(
                        "status_response_truncated_continuing",
                        "⚠️ Response was truncated, continuing automatically...",
                    ),
                }
                continue

            if not _pending_tool_calls:
                break  # No tool calls → conversation complete

            # --- Execute tool calls and prepare next round ---
            text_so_far = "".join(_streamed_text_parts)
            _streamed_text_parts = []
            if text_so_far.strip():
                _preview = text_so_far.strip()[:120].replace("\n", " ")
                logger.chat(f"💬 {_preview}")

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
                            yield {"type": "status", "message": tr("status_html_draft_loop_finalize", "💾 Draft loop detected: auto-finalizing HTML dashboard...")}
                            _auto_final = tools.execute_tool("create_html_dashboard", {"name": _draft_name})
                            _auto_obj = json.loads(_auto_final) if isinstance(_auto_final, str) else _auto_final
                            if isinstance(_auto_obj, dict) and str(_auto_obj.get("status", "")).lower() == "success":
                                _html_dashboard_saved_this_turn = True
                                _html_draft_pending_name = ""
                                _url = _auto_obj.get("dashboard_url") or _auto_obj.get("url") or ""
                                _msg = (
                                    tr("status_html_dashboard_created_url", "HTML dashboard created successfully: {url}", url=_url)
                                    if _url else
                                    tr("status_html_dashboard_created_ok", "HTML dashboard created successfully.")
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
                    tr(
                        "log_tool_loop_detected",
                        "Tool loop detected (round {round}, dup #{dup}): all {count} call(s) are duplicates - forcing final answer",
                        round=_tool_round,
                        dup=_duplicate_count,
                        count=len(_pending_tool_calls),
                    )
                )

                # ── No-tool providers (github_copilot, etc.): the model ignores
                # ── [DUPLICATE] messages and keeps generating <tool_call> XML.
                # ── Strategy: give it ONE more round but disable ToolSimulator
                # ── extraction so any <tool_call> in its text is stripped and the
                # ── response is treated as plain text → loop ends naturally.
                if _is_no_tool_provider:
                    if _duplicate_count >= 2:
                        # Already tried once — force-break now
                        logger.warning(
                            tr(
                                "log_no_tool_provider_second_duplicate_break",
                                "No-tool provider: 2nd duplicate -> breaking loop",
                            )
                        )
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
                    logger.warning(
                        tr(
                            "log_native_provider_second_duplicate_break",
                            "Native provider: 2nd duplicate -> breaking loop",
                        )
                    )
                    _fallback_text = _build_readonly_loop_fallback(_last_success_read_tool)
                    if _fallback_text:
                        yield {"type": "token", "content": _fallback_text}
                        _streamed_text_parts = [_fallback_text]
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

            # Additional safety: preview/update of existing automations requires
            # explicit target context (bubble/id/name+modify). When user asks for
            # NEW automations, block update flow and force create/disambiguation.
            _target_blocked = []
            _TARGET_GUARDED_AUTOMATION_TOOLS = {"preview_automation_change", "update_automation"}
            for _tc in list(_pending_tool_calls):
                _nm = _tc.get("name")
                if _nm not in _TARGET_GUARDED_AUTOMATION_TOOLS:
                    continue
                if _looks_new_auto_req:
                    _pending_tool_calls.remove(_tc)
                    _tc["_block_reason"] = (
                        "[BLOCKED by automation-target guard] "
                        "The user asked to create NEW automation(s), but this tool modifies an existing one. "
                        "Use create_automation for new automations. "
                        "If ambiguous, ask: 'Vuoi creare nuove automazioni o modificare un'automazione esistente?'"
                    )
                    _target_blocked.append(_tc)
                    logger.warning(f"Automation-target guard: blocked {_nm} due to new-automation request")
                    continue
                if not _has_explicit_auto_target:
                    _pending_tool_calls.remove(_tc)
                    _tc["_block_reason"] = (
                        "[BLOCKED by automation-target guard] "
                        "No explicit target automation was provided for a modify flow. "
                        "Do not infer from fuzzy smart-context matches. "
                        "Ask user to choose: create new automation(s) OR modify a specific existing automation (name/id)."
                    )
                    _target_blocked.append(_tc)
                    logger.warning(f"Automation-target guard: blocked {_nm} (missing explicit target)")

            # Preview guard: preview_automation_change must include actual changes.
            # Empty previews create a broken UX (double-confirm loops with no diff intent).
            _preview_arg_blocked = []
            for _tc in list(_pending_tool_calls):
                if _tc.get("name") != "preview_automation_change":
                    continue
                try:
                    _pa_args = json.loads(_tc.get("arguments", "{}") or "{}")
                except Exception:
                    _pa_args = {}
                if not isinstance(_pa_args, dict):
                    _pa_args = {}
                _preview_norm = _normalize_automation_change_args(_pa_args)
                _has_changes = bool(_preview_norm.get("changes")) or bool(_preview_norm.get("add_condition"))
                if _has_changes:
                    continue
                _pending_tool_calls.remove(_tc)
                _blocked_aid = _preview_norm.get("automation_id", "")
                _tc["_block_reason"] = (
                    "[BLOCKED by preview-args guard] "
                    "preview_automation_change was called without actual changes. "
                    "Provide non-empty changes (for example changes={\"action\": [...]}), "
                    "then show the preview and ask for confirmation."
                )
                _preview_arg_blocked.append(_tc)
                logger.warning(
                    f"Preview-args guard: blocked preview_automation_change with empty changes "
                    f"(automation_id={_blocked_aid!r})"
                )

            # Condition-dependency guard:
            # block automations where conditions reference response_variable values
            # created in actions (invalid execution order in Home Assistant).
            _cond_dep_blocked = []
            _COND_DEP_GUARDED = {"create_automation", "preview_automation_change", "update_automation"}
            for _tc in list(_pending_tool_calls):
                _nm = _tc.get("name")
                if _nm not in _COND_DEP_GUARDED:
                    continue
                try:
                    _raw = json.loads(_tc.get("arguments", "{}") or "{}")
                except Exception:
                    _raw = {}
                if not isinstance(_raw, dict):
                    _raw = {}
                _offending = _find_invalid_response_variable_in_conditions(_nm, _raw)
                if not _offending:
                    continue
                _pending_tool_calls.remove(_tc)
                _tc["_block_reason"] = (
                    "[BLOCKED by automation condition-dependency guard] "
                    f"Condition templates reference '{_offending}', but that value is created in actions "
                    "(response_variable). In Home Assistant, conditions run before actions, so this is invalid. "
                    "Move that check into actions (choose/if) after the data-fetch step, or remove the condition."
                )
                _cond_dep_blocked.append(_tc)
                logger.warning(
                    f"Condition-dependency guard: blocked {_nm} due to response_variable "
                    f"reference in conditions ({_offending})"
                )

            # Mark that a preview has been generated only if a valid preview call
            # remains pending after safety guards.
            if any(tc.get("name") == "preview_automation_change" for tc in _pending_tool_calls):
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
            for _tb_idx, _tb_item in enumerate(_target_blocked):
                if not _tb_item.get("id"):
                    _tb_item["id"] = f"call_{_tb_item.get('name', 'blocked')}_{_tb_idx}_tgt"
            for _ab_idx, _ab_item in enumerate(_preview_arg_blocked):
                if not _ab_item.get("id"):
                    _ab_item["id"] = f"call_{_ab_item.get('name', 'blocked')}_{_ab_idx}_parg"

            # Append assistant message with tool_calls (OpenAI format)
            # Include both executed and blocked tool calls so history stays well-formed
            _all_tcs_for_msg = _pending_tool_calls + _pg_blocked + _sig_blocked + _target_blocked + _preview_arg_blocked
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
            for _pb_tc in (_pg_blocked + _sig_blocked + _target_blocked + _preview_arg_blocked):
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
            _round_success_write_tools: list[str] = []
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

                _sig = f"{fn_name}:{json.dumps(tc_args, sort_keys=True)}"

                # Guardrail for direct channel messages:
                # - For "report-like" requests, require at least one successful data-read tool
                #   before allowing delivery (prevents sending placeholder prompts as final message).
                # - Prevent duplicate delivery to the same channel/recipient within the same turn.
                if fn_name == "send_channel_message":
                    _channel = str(tc_args.get("channel", "") or "").strip().lower()
                    _recipient = str(tc_args.get("recipient", "") or "").strip()
                    _delivery_key = f"{_channel}:{_recipient}"
                    _block_reason = ""
                    if _delivery_request_needs_data and _successful_read_tools_count == 0:
                        _block_reason = (
                            "send_channel_message blocked: this looks like a report request, "
                            "but no data was collected yet. First call read tools (for example "
                            "search_entities/get_entity_state/get_entities), then send exactly one "
                            "final message."
                        )
                    elif _delivery_key in _successful_channel_deliveries:
                        _block_reason = (
                            "send_channel_message blocked: duplicate delivery to the same "
                            "channel/recipient in this request. Do not send again."
                        )
                    if _block_reason:
                        result = json.dumps({
                            "status": "error",
                            "channel": _channel,
                            "recipient": _recipient,
                            "error": _block_reason,
                        }, ensure_ascii=False)
                        logger.warning(f"Tool guard: {_block_reason} ({_delivery_key})")
                        _tool_call_history.add(_sig)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": fn_name,
                            "content": result,
                        })
                        _log_result = result[:300] + ('...' if len(result) > 300 else '')
                        logger.info(f"Tool result [{fn_name}]: {_log_result}")
                        continue

                # Show localized status to user (runtime language aware).
                _status_label = tools.get_tool_status_label(fn_name, LANGUAGE)
                yield {"type": "status", "message": f"🔧 {_status_label}..."}
                logger.info(f"Tool (round {_tool_round}): {fn_name} {list(tc_args.keys())}")

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

                _parsed_result = None
                _result_obj = None
                try:
                    _parsed_result = json.loads(result) if isinstance(result, str) else result
                    if isinstance(_parsed_result, dict):
                        _result_obj = _parsed_result
                except Exception:
                    _parsed_result = result
                    _result_obj = None

                _read_tool_ok = False
                if _is_read_only_call(tc):
                    if isinstance(_parsed_result, dict):
                        _r_status = str(_parsed_result.get("status", "")).lower().strip()
                        _read_tool_ok = not (
                            _r_status in {"error", "failed", "invalid"}
                            or bool(_parsed_result.get("error"))
                        )
                    elif isinstance(_parsed_result, list):
                        _read_tool_ok = True
                    elif isinstance(_parsed_result, str):
                        _s = _parsed_result.strip().lower()
                        _read_tool_ok = bool(_s) and not _s.startswith('{"error"')

                if _result_obj is not None:
                    _status = str(_result_obj.get("status", "")).lower().strip()
                    _is_err = (
                        _status in {"error", "failed", "invalid"}
                        or bool(_result_obj.get("error"))
                    )
                    _is_ok = bool(_result_obj) and not _is_err

                    if not _is_read_only_call(tc) and _is_ok:
                        _any_successful_write_this_round = True
                        _round_success_write_tools.append(fn_name)
                        _write_tools_executed.append(fn_name)
                        if fn_name == "send_channel_message":
                            _ch = str(tc_args.get("channel", "") or "").strip().lower()
                            _rcp = str(tc_args.get("recipient", "") or "").strip()
                            if _ch and _rcp:
                                _successful_channel_deliveries.add(f"{_ch}:{_rcp}")
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
                                _round_write_confirms.append(tr("status_service_executed_on", "✅ Executed `{service}` on `{entity}`.", service=_svc_full, entity=_eid))
                            else:
                                _round_write_confirms.append(tr("status_service_executed", "✅ Executed `{service}`.", service=_svc_full))
                        else:
                            _msg = str(_result_obj.get("message") or "").strip()
                            if _msg:
                                _round_write_confirms.append(f"✅ {_msg}")

                    if fn_name == "preview_automation_change" and _status == "preview":
                        _preview_generated_this_turn = True
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
                                or tr(
                                    "html_dashboard_saved_file",
                                    "✅ HTML dashboard '{filename}' saved.",
                                    filename=_result_obj.get("filename", _dash_name or "dashboard"),
                                )
                            )
                        elif bool(_result_obj.get("error")):
                            # If finalize call failed, clear pending draft name to avoid
                            # redundant auto-finalize attempts with empty payload.
                            if not bool(tc_args.get("draft", False)):
                                _html_draft_pending_name = ""
                            _err_text = str(_result_obj.get("error", "") or "")
                            if "INLINE_HTML_BLOCKED" in _err_text:
                                _stop_after_html_dashboard_error = True
                                _html_dashboard_error_message = tr(
                                    "html_dashboard_not_created_inline_blocked",
                                    "❌ Dashboard not created: provider keeps sending inline HTML not compliant with file-safe format.",
                                )
                                # Break current tool-call batch immediately to avoid looping
                                # over the remaining duplicate create_html_dashboard calls.
                                break

                if _read_tool_ok:
                    _successful_read_tools_count += 1
                    _last_success_read_tool = {
                        "name": fn_name,
                        "args": dict(tc_args or {}),
                        "result": result,
                    }

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

            # Fast-path for direct action tools:
            # avoid an extra LLM round that often loops/duplicates after a successful action.
            _FAST_CONFIRM_WRITE_TOOLS = {
                "call_service",
                "trigger_automation",
                "activate_scene",
                "run_script",
                "send_notification",
                "send_channel_message",
            }
            if (
                _round_write_confirms
                and _round_success_write_tools
                and set(_round_success_write_tools).issubset(_FAST_CONFIRM_WRITE_TOOLS)
                and intent_name != "create_html_dashboard"
            ):
                _final_conf = "\n".join(dict.fromkeys([c for c in _round_write_confirms if c]))
                if _final_conf:
                    yield {"type": "token", "content": _final_conf}
                    _streamed_text_parts = [_final_conf]
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
            # Condense large tool results before storing in history so subsequent
            # turns don't re-send huge YAML blobs and overflow the context window.
            _msgs_for_history = _compact_messages_for_history(new_msgs_from_provider)
            for msg in _msgs_for_history:
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
            # Strip [FILE:...]...[/FILE] blocks before checking — YAML/JSON files
            # often contain keywords like enable/disable/open that are not user actions.
            _um_for_action_check = re.sub(
                r'\[FILE:[^\]]*\][\s\S]*?\[/FILE\]', '', str(user_message or ''),
                flags=re.IGNORECASE
            )
            _user_asked_action = bool(_ACTION_REQUEST_RE.search(_um_for_action_check))
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
                                assembled = tr("status_service_executed_on", "✅ Executed `{service}` on `{entity}`.", service=f"{_dom}.{_svc}", entity=_best_eid)
                                _write_tools_executed.append("call_service")
                                logger.info(
                                    "No-tool fallback action executed: %s on %s (provider=%s)",
                                    f"{_dom}.{_svc}", _best_eid, AI_PROVIDER
                                )
                    except Exception as _fb_e:
                        logger.warning(f"No-tool fallback action failed: {_fb_e}")

            _looks_like_fake_success = any(p in assembled.lower() for p in _HALLUCINATED_SUCCESS_PHRASES)
            # A response containing a code block is code generation, never a fake action.
            _assembled_has_code = '```' in assembled
            if (
                _is_no_tool_provider
                and assembled
                and not _write_tools_executed
                and not _preview_generated_this_turn
                and not _lean_mode
                and not _assembled_has_code
                and intent_name not in ("chat", "create_html_dashboard", "card_editor")
                and (_looks_like_fake_success or _user_asked_action)
            ):
                _warn = get_lang_text("warn_no_tool_called_with_guidance") or get_lang_text("warn_no_tool_called") or (
                    "⚠️ Action NOT executed: this provider replied in text without calling Home Assistant tools. "
                    "No changes were applied. "
                    "Try a provider with tool-calling support or confirm guided execution."
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
                _pending_summary = _extract_pending_context_from_assistant(assembled)
                if _pending_summary:
                    session_pending_context[session_id] = {
                        "summary": _pending_summary,
                        "ts": time.time(),
                    }
                elif _write_tools_executed:
                    # Once a write action is actually executed, pending confirmation
                    # context is no longer relevant.
                    session_pending_context.pop(session_id, None)
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
                            yield {"type": "status", "message": tr("status_html_saving", "💾 Saving HTML dashboard...")}
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
                                yield {"type": "status", "message": tr(
                                    "html_dashboard_saved_status",
                                    "✅ HTML dashboard '{filename}' saved!",
                                    filename=_saved_filename,
                                )}
                                _saved_url = _save_obj.get("html_url") or f"/local/dashboards/{_saved_filename}"
                                _user_msg = tr(
                                    "html_dashboard_created_open_here",
                                    "✨ Dashboard **{title}** created! Open it here: `{url}`",
                                    title=_title,
                                    url=_saved_url,
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
                                yield {"type": "status", "message": tr(
                                    "html_dashboard_save_failed",
                                    "⚠️ HTML save failed: {error}",
                                    error=_err_msg,
                                )}
                                # Emit a persistent assistant message too (status is transient)
                                yield {"type": "token", "content": tr(
                                    "html_dashboard_save_failed",
                                    "⚠️ HTML save failed: {error}",
                                    error=_err_msg,
                                )}
                        except Exception as _e:
                            logger.warning(f"Auto-save HTML dashboard failed: {_e}")
                            yield {"type": "status", "message": tr(
                                "html_dashboard_save_failed",
                                "⚠️ HTML save failed: {error}",
                                error=_e,
                            )}
                            # Emit a persistent assistant message too (status is transient)
                            yield {"type": "token", "content": tr(
                                "html_dashboard_save_failed",
                                "⚠️ HTML save failed: {error}",
                                error=_e,
                            )}
                    if _deferred_done_event is not None:
                        yield _deferred_done_event
                        _deferred_done_event = None
                # ──────────────────────────────────────────────────────────
                # NOTE: sentinel-based auto-execute blocks (CONFIRM_CREATE_AUTOMATION etc.)
                # have been removed. No-tool providers now use the universal Tool Simulator
                # (<tool_call> XML blocks) which are handled by the streaming loop above.
        elif _preview_generated_this_turn:
            # Fallback: some no-tool provider/model combinations can produce
            # an empty final assistant round right after preview generation.
            # Ensure the user still receives a confirmation prompt.
            _preview_msg = (
                get_lang_text("preview_change_message")
                or tr("preview_change_message", "Preview of the change. Confirm to apply.")
                or "Preview of the change. Confirm to apply."
            )
            yield {"type": "token", "content": _preview_msg}
            logger.chat(f"📤 [{AI_PROVIDER}/{get_active_model()}]: {_preview_msg}")
            _assistant_preview_msg = {
                "role": "assistant",
                "content": _preview_msg,
                "model": get_active_model(),
                "provider": AI_PROVIDER,
            }
            if last_usage:
                _assistant_preview_msg["usage"] = last_usage
            conversations[session_id].append(_assistant_preview_msg)

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


# moved to routes/ui_routes.py: index
# moved to routes/ui_routes.py: ui_bootstrap_js
# moved to routes/ui_routes.py: ui_main_js
# moved to routes/ui_routes.py: _PROVIDER_SDK_MAP
# moved to routes/ui_routes.py: _check_optional_sdks
# moved to routes/ui_routes.py: _check_provider_sdk
# moved to routes/ui_routes.py: api_ui_ping
# moved to routes/ui_routes.py: api_status




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


# moved to routes/bubble_routes.py: api_bubble_status


# moved to routes/bubble_routes.py: api_bubble_register


# moved to routes/bubble_routes.py: api_set_model


# moved to routes/bubble_routes.py: api_bubble_device_id
# moved to routes/bubble_routes.py: api_bubble_config


# moved to routes/bubble_routes.py: api_bubble_devices_list
# moved to routes/bubble_routes.py: api_bubble_devices_register
# moved to routes/bubble_routes.py: api_bubble_device_update
# moved to routes/bubble_routes.py: api_bubble_device_delete


# moved to routes/settings_routes.py: api_get_config
# moved to routes/settings_routes.py: api_set_config
# moved to routes/settings_routes.py: api_get_system_prompt
# moved to routes/settings_routes.py: api_set_system_prompt


# moved to routes/chat_routes.py: api_chat
# moved to routes/chat_routes.py: api_chat_stream
# moved to routes/chat_routes.py: api_chat_abort
# moved to routes/chat_routes.py: api_skill_deactivate


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

# moved to routes/scheduled_routes.py: api_scheduled_stats
# moved to routes/scheduled_routes.py: api_scheduled_tasks_list
# moved to routes/scheduled_routes.py: api_scheduled_tasks_create
# moved to routes/scheduled_routes.py: api_scheduled_task_delete
# moved to routes/scheduled_routes.py: api_scheduled_task_toggle

# ============ SchedulerAgent Endpoints ============

# moved to routes/scheduled_routes.py: api_scheduler_agent_chat
# moved to routes/scheduled_routes.py: api_scheduler_agent_sessions
# moved to routes/scheduled_routes.py: api_scheduler_agent_clear_session


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

# moved to routes/messaging_routes.py: api_messaging_stats
# moved to routes/messaging_routes.py: _ai_banner
# moved to routes/messaging_routes.py: _strip_markdown_for_telegram


# moved to routes/messaging_routes.py: api_telegram_message
# moved to routes/messaging_routes.py: api_discord_message
# moved to routes/messaging_routes.py: api_messaging_chats
# moved to routes/messaging_routes.py: api_messaging_chat


# moved to routes/messaging_routes.py: api_whatsapp_webhook


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

# moved to routes/messaging_routes.py: api_alexa_webhook


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


# moved to routes/nvidia_routes.py: api_nvidia_test_model


# moved to routes/nvidia_routes.py: api_nvidia_test_models


# moved to routes/nvidia_routes.py: api_provider_test_models

# ---- Memory API Endpoints ----

# moved to routes/memory_routes.py: api_get_memory, api_search_memory, api_memory_stats,
# api_delete_memory, api_cleanup_memory



# moved to routes/legacy_routes.py: health
# moved to routes/legacy_routes.py: get_entities_route
# moved to routes/legacy_routes.py: get_entity_state_route
# moved to routes/legacy_routes.py: send_message_legacy
# moved to routes/legacy_routes.py: call_service_route
# moved to routes/legacy_routes.py: execute_automation
# moved to routes/legacy_routes.py: execute_script
# moved to routes/legacy_routes.py: clear_conversation


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

# moved to routes/dashboard_routes.py: dashboard_api_states
# moved to routes/dashboard_routes.py: dashboard_api_history
# moved to routes/dashboard_routes.py: dashboard_api_service

# ===== CUSTOM HTML DASHBOARDS =====
# moved to routes/dashboard_routes.py: serve_html_dashboard
# moved to routes/dashboard_routes.py: api_get_dashboard_html
# moved to routes/dashboard_routes.py: list_html_dashboards


# moved to routes/document_routes.py: rag_stats


# ---------------------------------------------------------------------------
# Usage / cost tracking endpoints (inspired by OpenClaw)
# ---------------------------------------------------------------------------

# moved to routes/usage_routes.py: usage_stats, usage_stats_today, usage_stats_reset


# moved to routes/oauth_routes.py: oauth_codex_start
# moved to routes/oauth_routes.py: oauth_codex_exchange
# moved to routes/oauth_routes.py: oauth_codex_status
# moved to routes/oauth_routes.py: oauth_codex_revoke
# moved to routes/oauth_routes.py: oauth_copilot_start
# moved to routes/oauth_routes.py: oauth_copilot_poll
# moved to routes/oauth_routes.py: oauth_copilot_status
# moved to routes/oauth_routes.py: oauth_copilot_revoke
# moved to routes/oauth_routes.py: session_claude_web_store
# moved to routes/oauth_routes.py: session_claude_web_status
# moved to routes/oauth_routes.py: session_claude_web_clear
# moved to routes/oauth_routes.py: session_chatgpt_web_store
# moved to routes/oauth_routes.py: session_chatgpt_web_status
# moved to routes/oauth_routes.py: session_chatgpt_web_clear
# moved to routes/oauth_routes.py: session_grok_web_store
# moved to routes/oauth_routes.py: session_grok_web_status
# moved to routes/oauth_routes.py: session_grok_web_clear
# moved to routes/oauth_routes.py: session_gemini_web_store
# moved to routes/oauth_routes.py: session_gemini_web_status
# moved to routes/oauth_routes.py: session_gemini_web_clear
# moved to routes/oauth_routes.py: session_perplexity_web_store
# moved to routes/oauth_routes.py: session_perplexity_web_status
# moved to routes/oauth_routes.py: session_perplexity_web_clear


def start_messaging_bots() -> None:
    """Initialize and start Telegram, WhatsApp and Discord bots if configured.
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

        try:
            if not ENABLE_DISCORD:
                logger.info("Discord bot disabled via configuration (enable_discord: false)")
            else:
                d_token = _env("DISCORD_BOT_TOKEN")
                d_channels = _env("DISCORD_ALLOWED_CHANNEL_IDS")
                d_users = _env("DISCORD_ALLOWED_USER_IDS")
                if d_token:
                    bot = discord_bot.get_discord_bot(
                        d_token,
                        allowed_channel_ids=d_channels,
                        allowed_user_ids=d_users,
                    )
                    if bot:
                        bot.start()
                        logger.info("✅ Discord bot started")
                else:
                    logger.info("Discord bot not configured (no token)")
        except Exception as e:
            logger.warning(f"⚠️ Discord bot initialization error: {e}")


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


# moved to routes/settings_routes.py: api_config_read
# moved to routes/settings_routes.py: api_config_save


# moved to routes/settings_routes.py: _FALLBACK_CONFIG_FILE
# moved to routes/settings_routes.py: _FALLBACK_PRIORITY_DEFAULT
# moved to routes/settings_routes.py: _FALLBACK_KEY_ENV
# moved to routes/settings_routes.py: api_fallback_config_get


# moved to routes/settings_routes.py: api_fallback_config_post


# moved to routes/settings_routes.py: api_settings_get


# moved to routes/system_routes.py: api_addon_restart


# moved to routes/settings_routes.py: api_settings_post
# moved to routes/settings_routes.py: api_uninstall_cleanup


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
