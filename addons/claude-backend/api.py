"""Amira AI Assistant API with multi-provider support for Home Assistant."""

import os
import json
import logging
import queue
import re
import time
import threading
import uuid
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
LANGUAGE = os.getenv("LANGUAGE", "en").lower()  # Supported: en, it, es, fr
LOG_LEVEL = os.getenv("LOG_LEVEL", "normal").lower()  # Supported: normal, verbose, debug
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "False").lower() == "true"
ENABLE_FILE_UPLOAD = os.getenv("ENABLE_FILE_UPLOAD", "False").lower() == "true"
ENABLE_RAG = os.getenv("ENABLE_RAG", "False").lower() == "true"
ENABLE_CHAT_BUBBLE = os.getenv("ENABLE_CHAT_BUBBLE", "False").lower() == "true"
COST_CURRENCY = os.getenv("COST_CURRENCY", "USD").upper()

SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN", "") or os.getenv("HASSIO_TOKEN", "")

# Persisted runtime selection (preferred over add-on configuration).
# This enables choosing the agent/model from the chat dropdown only.
RUNTIME_SELECTION_FILE = "/config/amira/runtime_selection.json"

# Custom system prompt override (can be set dynamically via API)
CUSTOM_SYSTEM_PROMPT = None

# Agent defaults (hardcoded)
AGENT_NAME = "Amira"
AGENT_AVATAR = "🤖"
AGENT_INSTRUCTIONS = ""
HTML_DASHBOARD_FOOTER = ""
MAX_CONVERSATIONS = max(1, min(100, int(os.getenv("MAX_CONVERSATIONS", "10") or "10")))
MAX_SNAPSHOTS_PER_FILE = max(1, min(50, int(os.getenv("MAX_SNAPSHOTS_PER_FILE", "5") or "5")))

# Persist system prompt override across restarts
CUSTOM_SYSTEM_PROMPT_FILE = "/config/amira/custom_system_prompt.txt"

_LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO



class _ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\x1b[36m",     # cyan
        "INFO": "\x1b[32m",      # green
        "WARNING": "\x1b[33m",   # yellow
        "ERROR": "\x1b[31m",     # red
        "CRITICAL": "\x1b[35m",  # magenta
    }
    ICONS = {
        "DEBUG": "🔵",
        "INFO": "🟢",
        "WARNING": "🟡",
        "ERROR": "🔴",
        "CRITICAL": "🟣",
    }
    RESET = "\x1b[0m"

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
            # Format: [HH:MM:SS] [CONTEXT] 🟢 INFO:api: messaggio
            return f"[{ts}] [{context}] {clevel}:{record.name}:{record.getMessage()}"
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


def _load_custom_system_prompt_from_disk() -> Optional[str]:
    try:
        if not os.path.isfile(CUSTOM_SYSTEM_PROMPT_FILE):
            return None
        with open(CUSTOM_SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            prompt = (f.read() or "").strip()
        # Guardrail: ignore absurdly large prompts
        if len(prompt) > 200_000:
            logger.warning(f"Custom system prompt file too large ({len(prompt)} chars) - ignoring")
            return None
        return prompt or None
    except Exception as e:
        logger.warning(f"Could not load custom system prompt from disk: {e}")
        return None


def _persist_custom_system_prompt_to_disk(prompt: Optional[str]) -> None:
    try:
        os.makedirs(os.path.dirname(CUSTOM_SYSTEM_PROMPT_FILE), exist_ok=True)
        if not prompt:
            if os.path.isfile(CUSTOM_SYSTEM_PROMPT_FILE):
                os.remove(CUSTOM_SYSTEM_PROMPT_FILE)
            return
        with open(CUSTOM_SYSTEM_PROMPT_FILE, "w", encoding="utf-8") as f:
            f.write(str(prompt))
    except Exception as e:
        logger.warning(f"Could not persist custom system prompt to disk: {e}")


# Load persisted system prompt override (if any)
_persisted_prompt = _load_custom_system_prompt_from_disk()
if _persisted_prompt:
    CUSTOM_SYSTEM_PROMPT = _persisted_prompt
    logger.info(f"Loaded custom system prompt from disk ({len(CUSTOM_SYSTEM_PROMPT)} chars)")


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


def _extract_http_error_code(error_text: str) -> Optional[int]:
    if not error_text:
        return None
    # "Error code: 429" (Anthropic/OpenAI style)
    m = re.search(r"Error code:\s*(\d{3})", error_text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    # "429 RESOURCE_EXHAUSTED" (google-genai style) or "'code': 429"
    m = re.search(r"^(\d{3})\s", error_text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    m = re.search(r"['\"]code['\"]\s*:\s*(\d{3})", error_text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    return None


def _extract_remote_message(error_text: str) -> str:
    """Best-effort extraction of a remote 'message' field from error strings."""
    if not error_text:
        return ""
    # Common shapes:
    # - {'error': {'message': '...'}}
    # - {"error": {"message": "..."}}
    for pat in (
        r"['\"]message['\"]\s*:\s*['\"]([^'\"]+)['\"]",
    ):
        m = re.search(pat, error_text)
        if m:
            return (m.group(1) or "").strip()
    return ""


def humanize_provider_error(err: Exception, provider: str) -> str:
    """Turn provider exceptions into short, user-friendly UI messages."""
    raw = str(err) if err is not None else ""
    code = _extract_http_error_code(raw)
    remote_msg = _extract_remote_message(raw)
    low = (remote_msg or raw).lower()

    if provider == "github" and code == 403 and ("budget limit" in low or "reached its budget" in low):
        return get_lang_text("err_github_budget_limit") or (
            "GitHub Models: budget limit reached. Increase budget/credit or switch model/provider."
        )

    if provider == "github" and (code == 413 or "tokens_limit_reached" in low or "request body too large" in low):
        m = re.search(r"max size:\s*(\d+)\s*tokens", (remote_msg or raw), flags=re.IGNORECASE)
        limit = m.group(1) if m else ""
        limit_part = f" (max {limit} token)" if limit else ""
        tpl = get_lang_text("err_github_request_too_large")
        if tpl:
            try:
                return tpl.format(limit_part=limit_part)
            except Exception:
                return tpl
        return "GitHub Models: request too long for selected model." + limit_part

    _CREDITS_URLS = {
        "openrouter": "https://openrouter.ai/settings/credits",
        "openai": "https://platform.openai.com/settings/billing",
        "anthropic": "https://console.anthropic.com/settings/plans",
        "deepseek": "https://platform.deepseek.com",
        "groq": "https://console.groq.com",
        "mistral": "https://console.mistral.ai",
        "minimax": "https://platform.minimaxi.com",
        "aihubmix": "https://aihubmix.com",
        "siliconflow": "https://cloud.siliconflow.cn",
        "nvidia": "https://developer.nvidia.com/nim",
    }
    if code == 400 and ("usage limits" in low or "regain access on" in low or "api usage limits" in low):
        date_m = re.search(r"regain access on\s+(\S+)", raw, re.IGNORECASE)
        date_str = date_m.group(1) if date_m else ""
        tpl = get_lang_text("err_api_usage_limits")
        if tpl:
            return tpl.format(date=date_str) if date_str else tpl
        return f"❌ API usage limits reached. Access will be restored on {date_str or '?'}. Switch to another provider in the meantime."
    if code == 402 or "insufficient credits" in low or "insufficient balance" in low or "out of credits" in low:
        base = get_lang_text("err_http_402") or "❌ Insufficient balance. Top up your account credits for this provider."
        url = _CREDITS_URLS.get(provider)
        return f"{base}\n⚠️ {url}" if url else base
    if code == 401:
        return get_lang_text("err_http_401") or "Authentication failed (401)."
    if code == 403:
        return get_lang_text("err_http_403") or "Access denied (403)."
    if code == 429 and ("insufficient_quota" in low or "insufficient quota" in low or "exceeded your current quota" in low or "run out of credits" in low):
        base = get_lang_text("err_openai_quota") or "❌ Quota exceeded. Your account has run out of credits. Check your billing details."
        url = _CREDITS_URLS.get(provider)
        return f"{base}\n⚠️ {url}" if url else base
    if code == 429 and provider == "google" and "resource_exhausted" in low:
        return get_lang_text("err_google_quota") or "Google Gemini: quota exhausted (429). Wait a minute and retry, or switch to another model/provider."
    if code == 429:
        return get_lang_text("err_http_429") or "Rate limit (429)."

    if code == 413:
        return get_lang_text("err_http_413") or "Request too large (413)."

    # Fallback: keep the remote message if present, otherwise the raw error
    return remote_msg or raw


def load_runtime_selection() -> bool:
    """Load persisted provider/model selection from disk.

    Returns True if a valid selection was loaded.
    """
    global AI_PROVIDER, AI_MODEL, SELECTED_MODEL, SELECTED_PROVIDER
    try:
        if not os.path.isfile(RUNTIME_SELECTION_FILE):
            return False
        with open(RUNTIME_SELECTION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        provider = (data.get("provider") or "").strip().lower()
        model = (data.get("model") or "").strip()
        if not provider or not model:
            return False

        # Accept only known providers; model is expected to be a technical id.
        _known = {
            "anthropic", "openai", "google", "nvidia", "github",
            "groq", "mistral", "openrouter", "deepseek", "minimax",
            "aihubmix", "siliconflow", "volcengine", "dashscope",
            "moonshot", "zhipu", "ollama", "github_copilot", "openai_codex",
            "claude_web", "chatgpt_web",
        }
        if provider not in _known:
            return False

        AI_PROVIDER = provider
        AI_MODEL = model
        SELECTED_PROVIDER = provider
        SELECTED_MODEL = model
        logger.info(f"Loaded runtime selection: {AI_PROVIDER} / {AI_MODEL}")
        return True
    except Exception as e:
        logger.warning(f"Could not load runtime selection: {e}")
        return False


def save_runtime_selection(provider: str, model: str) -> bool:
    """Persist provider/model selection to disk."""
    try:
        os.makedirs(os.path.dirname(RUNTIME_SELECTION_FILE), exist_ok=True)
        payload = {
            "provider": (provider or "").strip().lower(),
            "model": (model or "").strip(),
            "updated_at": datetime.now().isoformat(),
        }
        with open(RUNTIME_SELECTION_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        return True
    except Exception as e:
        logger.warning(f"Could not save runtime selection: {e}")
        return False

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
LANGUAGE_TEXT = {
    "en": {
        "before": "Before",
        "after": "After",
        "respond_instruction": "Respond in English.",
        "show_yaml_rule": "CRITICAL: After CREATING or MODIFYING automations/scripts/dashboards, you MUST show the YAML code to the user in your response. Never skip this step.",
        "confirm_entity_rule": "CRITICAL: Before creating automations, ALWAYS use search_entities first to find the correct entity_id, then confirm with the user if multiple matches are found.",
        "confirm_delete_rule": "CRITICAL DESTRUCTIVE: Before DELETING or MODIFYING an automation/script/dashboard, you MUST:\n1. Use get_automations/get_scripts/get_dashboards to list all options\n2. Identify with CERTAINTY which one the user wants to delete/modify (by name/alias)\n3. Show the user WHICH ONE you will delete/modify\n4. ASK for EXPLICIT CONFIRMATION before proceeding\n5. NEVER delete/modify without confirmation - it's an IRREVERSIBLE operation",
        "example_vs_create_rule": "CRITICAL INTENT: Distinguish between 'show example' vs 'actually create':\n- If user asks for an \"example\", \"show me\", \"how to\", \"demo\" → respond with YAML code ONLY, do NOT call create_automation/create_script\n- If user explicitly asks to \"create\", \"save\", \"add\", \"make it real\" → call create_automation/create_script\n- When in doubt, show the YAML code first and ask if they want to create it",

        "err_github_budget_limit": "GitHub Models: budget limit reached for this account. Increase your GitHub budget/credit or pick another provider/model from the dropdown.",
        "err_github_request_too_large": "GitHub Models: the request is too long for the selected model{limit_part}. Try a shorter question or pick a larger model from the dropdown.",
        "err_api_usage_limits": "❌ API usage limits reached. Your access will be restored on {date}. Switch to another provider in the meantime.",
        "err_http_402": "❌ Insufficient balance. Top up your account credits at the provider's website, or switch to another provider.",
        "err_http_401": "Authentication failed (401). Check the provider API key/token.",
        "err_http_403": "Access denied (403). The model may not be available for this account/token.",
        "err_http_413": "Request too large (413). Reduce message/context length or switch model.",
        "err_http_429": "Rate limit (429). Wait a few seconds and retry, or switch model/provider.",
        "err_google_quota": "Google Gemini: quota exhausted (429). Wait a minute and retry, or switch to another model/provider.",
        "err_openai_quota": "❌ OpenAI quota exceeded. Your account has run out of credits. Check your plan and billing at platform.openai.com.",
        "err_loop_exhausted": "❌ The AI did not respond (request limit reached or repeated errors). Try again or switch model/provider.",

        "status_request_sent": "{provider}: sending request to the model...",
        "status_response_received": "{provider}: response received, processing...",
        "status_generating": "{provider}: generating the response...",
        "status_still_working": "{provider}: still working...",
        "status_actions_received": "Actions requested, executing...",
        "status_executing_tool": "{provider}: running tool {tool}...",
        "status_rate_limit_wait": "{provider}: rate limit reached, waiting..."
        ,
        "status_rate_limit_wait_seconds": "{provider}: rate limit, waiting {seconds}s...",

        "err_api_key_not_configured": "⚠️ API key for {provider_name} not configured. Set it in the add-on settings.",
        "err_provider_not_supported": "❌ Provider '{provider}' not supported. Choose: anthropic, openai, google, nvidia, github.",
        "err_provider_generic": "❌ Error {provider_name}: {error}",
        "err_api_key_not_configured_short": "API key not configured",
        "err_invalid_image_format": "Invalid image format",
        "err_nvidia_api_key": "NVIDIA API key not configured.",
        "err_nvidia_model_invalid": "Invalid NVIDIA model.",
        "err_nvidia_model_removed": "NVIDIA model {reason}: {model_id}. Removed from model list.",
        "err_response_blocked": "{provider}: response blocked by safety filters. Try rephrasing your request.",

        "status_image_processing": "Processing image...",
        "status_context_preloaded": "Context preloaded...",
        "status_nvidia_model_removed": "⚠️ NVIDIA model not available (404). Removed from model list.",
        "status_tool_repair_retry": "Repaired tool state, retrying...",
        "status_token_params_retry": "Token parameters incompatible with model, retrying.",
        "status_github_format_retry": "GitHub model not recognized, retrying with alternative format.",
        "status_github_model_fallback": "Model not available on GitHub, switching to GPT-4o.",
        "status_rate_limit_waiting": "Rate limit reached, waiting...",
        "status_prompt_too_large": "Selected model has a low limit (prompt too large). Reducing context and retrying...",
        "status_user_cancelled": "Cancelled by user.",

        "write_op_success": "✅ Operation completed successfully!",
        "write_no_changes": "\nNo changes detected (content is identical).",
        "write_yaml_updated": "\n**Updated YAML:**",
        "write_yaml_created": "\n**Created YAML:**",
        "write_snapshot_created": "\n💾 Snapshot created: `{snapshot_id}`",

        "intent_modify_automation": "Modify automation",
        "intent_modify_script": "Modify script",
        "intent_create_automation": "Create automation",
        "intent_create_script": "Create script",
        "intent_create_dashboard": "Create dashboard",
        "intent_modify_dashboard": "Modify dashboard",
        "intent_control_device": "Device control",
        "intent_query_state": "Device state",
        "intent_query_history": "Data history",
        "intent_delete": "Delete",
        "intent_config_edit": "Edit configuration",
        "intent_areas": "Room management",
        "intent_notifications": "Notification",
        "intent_helpers": "Helper management",
        "intent_chat": "Chat",
        "intent_generic": "Analyzing request",
        "intent_default": "Processing",

        "read_only_note": "**Read-only mode — no files were modified.**",

        "smart_context_script_found": "## YAML SCRIPT FOUND: \"{alias}\" (id: {sid})\n```yaml\n{yaml}```\nTo modify it use update_script with script_id='{sid}' and the fields to change.",
        "read_only_instruction": "READ-ONLY MODE: Show the user the complete YAML code in a yaml code block. At the end add the note: ",

        "dashboard_created_successfully": "Dashboard created successfully! Your ",
        "dashboard_sidebar_ready": "dashboard appears in the sidebar at /{path}",
        "dashboard_sidebar_failed": "HTML file is ready but sidebar integration failed",
    },
    "it": {
        "before": "Prima",
        "after": "Dopo",
        "respond_instruction": "Rispondi sempre in Italiano.",
        "show_yaml_rule": "CRITICO: Dopo aver CREATO o MODIFICATO automazioni/script/dashboard, DEVI sempre mostrare il codice YAML al usuario in tua risposta. Nunca omitas este paso.",
        "confirm_entity_rule": "CRITICO: Antes de crear automazioni, USA SIEMPRE search_entities per trovare il corretto entity_id, poi confirma con l'utente se ci sono più risultati.",
        "confirm_delete_rule": "CRITICO DISTRUTTIVO: Antes de ELIMINARE o MODIFICARE un'automazione/script/dashboard, DEVI:\n1. Usar get_automations/get_scripts/get_dashboards per elencare tutte le opzioni\n2. Identificare con CERTEZZA quale l'utente vuole eliminare/modificare (per nome/alias)\n3. Mostrare al usuario CUÁL eliminarás/modificarás\n4. PEDIR CONFIRMACIÓN EXPLÍCITA antes de procedere\n5. NUNCA eliminar/modificare MAI senza conferma - è un'operazione IRREVERSIBILE",
        "example_vs_create_rule": "CRITICO INTENTO: Distingue tra 'mostra esempio' e 'crea effettivamente':\n- Se l'utente chiede un \"esempio\", \"mostrami\", \"come si fa\", \"demo\" → rispondi con il codice YAML SOLAMENTE, NON chiamare create_automation/create_script\n- Se l'utente chiede esplicitamente di \"creare\", \"salvare\", \"aggiungere\", \"rendilo reale\" → chiamare create_automation/create_script\n- En caso di dubbio, mostra prima il codice YAML e chiedi se vuole crearlo effettivamente",

        "err_github_budget_limit": "GitHub Models: limite budget raggiunto per questo account. Aumenta il budget/crédito su GitHub oppure seleziona un altro provider/modello dal menu in alto.",
        "err_github_request_too_large": "GitHub Models: richiesta troppo lunga per il modello selezionato{limit_part}. Prova a fare una domanda più corta, oppure scegli un modello più grande dal menu in alto.",
        "err_api_usage_limits": "❌ Limiti di utilizzo API raggiunti. Il tuo accesso verrà ripristinato il {date}. Nel frattempo passa a un altro provider.",
        "err_http_402": "❌ Credito insufficiente. Ricarica il saldo sul sito del provider, oppure passa a un altro provider.",
        "err_http_401": "Autenticazione fallita (401). Verifica la chiave/token del provider selezionato.",
        "err_http_403": "Accesso negato (403). Il modello potrebbe non essere disponibile per questo account/token.",
        "err_http_413": "Richiesta troppo grande (413). Riduci la lunghezza del messaggio/contesto o cambia modello.",
        "err_http_429": "Limite di velocità (429). Attendi qualche secondo e riprova, oppure cambia modello/provider.",
        "err_google_quota": "Google Gemini: quota esaurita (429). Attendi un minuto e riprova, oppure cambia modello/provider.",
        "err_openai_quota": "❌ Quota OpenAI esaurita. Il tuo account ha esaurito i crediti. Controlla il tuo piano e la fatturazione su platform.openai.com.",
        "err_loop_exhausted": "❌ L'IA non ha risposto (limite di round raggiunto o errori ripetuti). Riprova o cambia modello/provider.",

        "status_request_sent": "{provider}: invio richiesta al modello...",
        "status_response_received": "{provider}: risposta ricevuta, elaboro...",
        "status_generating": "{provider}: generando la risposta...",
        "status_still_working": "{provider}: ancora in elaborazione...",
        "status_actions_received": "Ho ricevuto una richiesta di azioni, eseguo...",
        "status_executing_tool": "{provider}: eseguo tool {tool}...",
        "status_rate_limit_wait": "{provider}: limite di velocità raggiunto, attendo...",
        "status_rate_limit_wait_seconds": "{provider}: limite di velocità, attendo {seconds}s...",

        "err_api_key_not_configured": "⚠️ Chiave API per {provider_name} non configurata. Impostala nelle impostazioni del componente aggiuntivo.",
        "err_provider_not_supported": "❌ Provider '{provider}' non supportato. Scegli tra: anthropic, openai, google, nvidia, github e altri.",
        "err_provider_generic": "❌ Errore {provider_name}: {error}",
        "err_api_key_not_configured_short": "Chiave API non configurata",
        "err_invalid_image_format": "Formato immagine non valido",
        "err_nvidia_api_key": "Chiave API NVIDIA non configurata.",
        "err_nvidia_model_invalid": "Modello NVIDIA non valido.",
        "err_nvidia_model_removed": "Modello NVIDIA {reason}: {model_id}. Rimosso dalla lista.",
        "err_response_blocked": "{provider}: risposta bloccata dai filtri di sicurezza. Prova a riformulare la richiesta.",

        "status_image_processing": "Elaboro immagine...",
        "status_context_preloaded": "Contesto precaricato...",
        "status_nvidia_model_removed": "⚠️ Modello NVIDIA non disponibile (404). Rimosso dalla lista modelli.",
        "status_tool_repair_retry": "Stato strumenti ripristinato, nuovo tentativo...",
        "status_token_params_retry": "Parametri token incompatibili con il modello, nuovo tentativo.",
        "status_github_format_retry": "Modello GitHub non riconosciuto, nuovo tentativo con formato alternativo.",
        "status_github_model_fallback": "Modello non disponibile su GitHub, passaggio a GPT-4o.",
        "status_rate_limit_waiting": "Limite di velocità raggiunto, attendo...",
        "status_prompt_too_large": "Il modello selezionato ha un limite basso (prompt troppo grande). Riduco il contesto e riprovo...",
        "status_user_cancelled": "Annullato dall'utente.",

        "write_op_success": "✅ Operazione completata con successo!",
        "write_no_changes": "\nNessuna modifica rilevata (il contenuto è identico).",
        "write_yaml_updated": "\n**YAML aggiornato:**",
        "write_yaml_created": "\n**YAML creato:**",
        "write_snapshot_created": "\n💾 Snapshot creato: `{snapshot_id}`",

        "intent_modify_automation": "Modifica automazione",
        "intent_modify_script": "Modifica script",
        "intent_create_automation": "Crea automazione",
        "intent_create_script": "Crea script",
        "intent_create_dashboard": "Crea dashboard",
        "intent_modify_dashboard": "Modifica dashboard",
        "intent_control_device": "Controllo dispositivo",
        "intent_query_state": "Stato dispositivo",
        "intent_query_history": "Storico dati",
        "intent_delete": "Eliminazione",
        "intent_config_edit": "Modifica configurazione",
        "intent_areas": "Gestione stanze",
        "intent_notifications": "Notifica",
        "intent_helpers": "Gestione helper",
        "intent_chat": "Chat",
        "intent_generic": "Analisi richiesta",
        "intent_default": "Elaborazione",

        "read_only_note": "**Modalità sola lettura — nessun file è stato modificato.**",

        "smart_context_script_found": "## YAML SCRIPT TROVATO: \"{alias}\" (id: {sid})\n```yaml\n{yaml}```\nPer modificarlo usa update_script con script_id='{sid}' e i campi da cambiare.",
        "read_only_instruction": "MODALITÀ SOLA LETTURA: Mostra all'utente il codice YAML completo in un code block yaml. Alla fine aggiungi la nota: ",
        "dashboard_created_successfully": "Dashboard creata con successo! ",
        "dashboard_sidebar_ready": "Il dashboard appare nella sidebar a /{path}",
        "dashboard_sidebar_failed": "File HTML pronto ma integrazione sidebar fallita",
    },
    "es": {
        "before": "Antes",
        "after": "Después",
        "respond_instruction": "Responde siempre en Español.",
        "show_yaml_rule": "CRÍTICO: Después de CREAR o MODIFICAR automatizaciones/scripts/dashboards, DEBES mostrar el código YAML al usuario en tu respuesta. Nunca omitas este paso.",
        "confirm_entity_rule": "CRÍTICO: Antes de crear automatizaciones, USA SIEMPRE search_entities para encontrar el entity_id correcto, luego confirma con el usuario si hay múltiples resultados.",
        "confirm_delete_rule": "CRÍTICO DESTRUCTIVO: Antes de ELIMINAR o MODIFICAR una automatización/script/dashboard, DEBES:\n1. Usar get_automations/get_scripts/get_dashboards para listar todas las opciones\n2. Identificar con CERTEZZA cuál quiere eliminar/modificar el usuario (por nombre/alias)\n3. Mostrar al usuario CUÁL eliminarás/modificarás\n4. PEDIR CONFIRMACIÓN EXPLÍCITA antes de proceder\n5. NUNCA eliminar/modificar sin confirmación - es una operación IRREVERSIBLE",
        "example_vs_create_rule": "CRÍTICO INTENCIÓN: Distingue entre 'mostrar ejemplo' y 'crear realmente':\n- Si el usuario pide un \"esempio\", \"mostrami\", \"cómo se hace\", \"demo\" → responde con el código YAML SOLAMENTE, NO llames create_automation/create_script\n- Si el usuario pide esplicitamente di \"crear\", \"guardar\", \"añadir\", \"hazlo real\" → llama create_automation/create_script\n- En caso de duda, muestra primero el código YAML y pregunta si quiere crearlo realmente",

        "err_github_budget_limit": "GitHub Models: se ha alcanzado el límite de presupuesto de esta cuenta. Aumenta el presupuesto/crédito en GitHub o elige otro proveedor/modelo en el desplegable.",
        "err_github_request_too_large": "GitHub Models: la solicitud es demasiado larga para el modelo seleccionado{limit_part}. Prueba con una pregunta más corta o elige un modelo más grande en el desplegable.",
        "err_http_401": "Autenticación fallida (401). Verifica la clave/token del proveedor.",
        "err_http_403": "Acceso negado (403). El modelo puede no estar disponible para este cuenta/token.",
        "err_api_usage_limits": "❌ Límites de uso de API alcanzados. Tu acceso se restablecerá el {date}. Cambia a otro proveedor mientras tanto.",
        "err_http_413": "Solicitud demasiado grande (413). Reduce el mensaje/contexto o cambia de modelo.",
        "err_http_429": "Límite de tasa (429). Espera unos segundos y reintenta, o cambia de modelo/proveedor.",
        "err_google_quota": "Google Gemini: cuota agotada (429). Espera un minuto y reintenta, o cambia de modelo/proveedor.",
        "err_openai_quota": "❌ Quota de OpenAI agotada. Tu cuenta se ha quedado sin créditos. Revisa tu plan y facturación en platform.openai.com.",
        "err_loop_exhausted": "❌ La IA no respondió (limite de rondas alcanzado o errores repetidos). Inténtalo de nuevo o cambia de modelo/proveedor.",

        "status_request_sent": "{provider} : envoi de la requête au modèle...",
        "status_response_received": "{provider} : réponse reçue, traitement...",
        "status_generating": "{provider} : génération de la réponse...",
        "status_still_working": "{provider} : toujours en cours...",
        "status_actions_received": "Acciones solicitadas, ejecutando...",
        "status_executing_tool": "{provider} : exécution de l’outil {tool}...",
        "status_rate_limit_wait": "{provider} : limite de débit alcanzado, attente..."
        ,
        "status_rate_limit_wait_seconds": "{provider} : limite de débit, attente {seconds}s...",

        "err_api_key_not_configured": "⚠️ Clé API pour {provider_name} non configurée. Configurez-la dans les paramètres de l'add-on.",
        "err_provider_not_supported": "❌ Proveedor '{provider}' non soportado. Elige: anthropic, openai, google, nvidia, github.",
        "err_provider_generic": "❌ Errore {provider_name}: {error}",
        "err_api_key_not_configured_short": "Clé API non configurée",
        "err_invalid_image_format": "Formato de imagen no válido",
        "err_nvidia_api_key": "Clé API NVIDIA non configurée.",
        "err_nvidia_model_invalid": "Modèle NVIDIA non valide.",
        "err_nvidia_model_removed": "Modèle NVIDIA {reason}: {model_id}. Eliminado de la lista.",
        "err_response_blocked": "{provider}: risposta bloccata dai filtri di sicurezza. Prova a riformulare la richiesta.",

        "status_image_processing": "Procesando imagen...",
        "status_context_preloaded": "Contesto precargado...",
        "status_nvidia_model_removed": "⚠️ Modèle NVIDIA non disponible (404). Eliminado de la liste des modèles.",
        "status_tool_repair_retry": "État des outils réparé, nouvelle tentative...",
        "status_token_params_retry": "Paramètres de token incompatibles avec le modèle, nouvelle tentative.",
        "status_github_format_retry": "Modèle GitHub non riconosciuto, nouvelle tentative avec format alternatif.",
        "status_github_model_fallback": "Modèle non disponible su GitHub, passage à GPT-4o.",
        "status_rate_limit_waiting": "Límite de débit alcanzado, en attente...",
        "status_prompt_too_large": "Il modello selezionato ha un limite basso (prompt troppo grande). Riduco il contesto e riprovo...",
        "status_user_cancelled": "Annulé par l'utilisateur.",

        "write_op_success": "✅ Operazione completata con successo!",
        "write_no_changes": "\nNessuna modifica rilevata (il contenuto è identico).",
        "write_yaml_updated": "\n**YAML aggiornato:**",
        "write_yaml_created": "\n**YAML creato:**",
        "write_snapshot_created": "\n💾 Snapshot creato: `{snapshot_id}`",

        "intent_modify_automation": "Modificar automazione",
        "intent_modify_script": "Modificar script",
        "intent_create_automation": "Crear automazione",
        "intent_create_script": "Crear script",
        "intent_create_dashboard": "Crear dashboard",
        "intent_modify_dashboard": "Modificar dashboard",
        "intent_control_device": "Controllo dispositivo",
        "intent_query_state": "Stato dispositivo",
        "intent_query_history": "Storico dati",
        "intent_delete": "Eliminazione",
        "intent_config_edit": "Modifica configurazione",
        "intent_areas": "Gestione stanze",
        "intent_notifications": "Notifica",
        "intent_helpers": "Gestione helper",
        "intent_chat": "Chat",
        "intent_generic": "Analisi richiesta",
        "intent_default": "Procesando",

        "read_only_note": "**Modalità sola lettura — nessun file è stato modificato.**",

        "smart_context_script_found": "## YAML SCRIPT TROVATO: \"{alias}\" (id: {sid})\n```yaml\n{yaml}```\nPer modificarlo usa update_script con script_id='{sid}' e i campi a cambiar.",
        "read_only_instruction": "MODE LECTURE SEULE: Muestra al usuario el código YAML completo en un code block yaml. Al final añade la nota: ",

        "dashboard_created_successfully": "Dashboard creata con successo! ",
        "dashboard_sidebar_ready": "Il dashboard appare nella sidebar a /{path}",
        "dashboard_sidebar_failed": "File HTML pronto ma integrazione sidebar fallita",
    },
    "fr": {
        "before": "Avant",
        "after": "Après",
        "respond_instruction": "Réponds toujours en Français.",
        "show_yaml_rule": "CRITIQUE: Après avoir CRÉÉ ou MODIFIÉ des automatisations/scripts/dashboards, tu DOIS toujours montrer le code YAML à l'utilisateur dans ta réponse. Ne saute jamais cette étape.",
        "confirm_entity_rule": "CRITIQUE: Avant de créer des automatisations, UTILISE TOUJOURS search_entities pour trouver le bon entity_id, puis confirme avec l'utilisateur s'il y a plusieurs résultats.",
        "confirm_delete_rule": "CRITIQUE DESTRUCTIF: Avant de SUPPRIMER ou MODIFIER une automatisation/script/dashboard, tu DOIS:\n1. Utiliser get_automations/get_scripts/get_dashboards pour lister toutes les options\n2. Identifier avec CERTITUDE laquelle l'utilisateur veut supprimer/modifier (par nom/alias)\n3. Montrer à l'utilisateur LAQUELLE tu vas supprimer/modifier\n4. DEMANDER une CONFIRMACIÓN EXPLÍCITA avant de proceder\n5. NUNCA supprimer/modifier sans confirmation - c'est une opération IRRÉVERSIBLE",
        "example_vs_create_rule": "CRITIQUE INTENTION: Distingue entre 'mostrar ejemplo' et 'créer réellement':\n- Si l'utilisateur demande un \"exemple\", \"mostrami\", \"comment faire\", \"demo\" → réponds avec le code YAML SOLAMENTE, NON chiamare create_automation/create_script\n- Si l'utilisateur demande esplicitement de \"créer\", \"sauvegarder\", \"ajouter\", \"rends-le réel\" → chiamare create_automation/create_script\n- En cas de doute, montre d'abord le code YAML et demande s'il veut le créer réellement",

        "err_github_budget_limit": "GitHub Models : limite de budget atteinte pour ce compte. Augmente le budget/crédit GitHub ou choisis un autre fournisseur/modello dans la liste déroulante.",
        "err_github_request_too_large": "GitHub Models : la requête est trop longue pour le modèle sélectionné{limit_part}. Essaie une question plus courte ou choisis un modèle plus grand dans la liste déroulante.",
        "err_http_401": "Échec d'authentification (401). Vérifie la clé/le jeton du fournisseur.",
        "err_http_403": "Accès refusé (403). Le modèle peut ne pas être disponible pour ce compte/jeton.",
        "err_api_usage_limits": "❌ Limites d'utilisation API atteintes. Votre accès sera rétabli le {date}. Changez de fournisseur en attendant.",
        "err_http_413": "Requête trop volumineuse (413). Réduis le message/le contexte ou change de modèle.",
        "err_http_429": "Limite de débit (429). Attends quelques secondes et réessaie, ou change de modèle/fournisseur.",
        "err_google_quota": "Google Gemini : quota épuisé (429). Attends une minute et réessaie, ou change de modèle/fournisseur.",
        "err_openai_quota": "❌ Quota OpenAI épuisée. Ton compte n'a plus de crédits. Vérifie ton plan et ta facturation sur platform.openai.com.",
        "err_loop_exhausted": "❌ L'IA n'a pas répondu (limite de rounds atteinte ou erreurs répétées). Réessaie ou change de modèle/fournisseur.",

        "status_request_sent": "{provider} : envoi de la requête au modèle...",
        "status_response_received": "{provider} : réponse reçue, traitement...",
        "status_generating": "{provider} : génération de la réponse...",
        "status_still_working": "{provider} : toujours en cours...",
        "status_actions_received": "Acciones solicitadas, ejecutando...",
        "status_executing_tool": "{provider} : exécution de l’outil {tool}...",
        "status_rate_limit_wait": "{provider} : limite de débit alcanzado, attente..."
        ,
        "status_rate_limit_wait_seconds": "{provider} : limite de débit, attente {seconds}s...",

        "err_api_key_not_configured": "⚠️ Clé API pour {provider_name} non configurée. Configurez-la dans les paramètres de l'add-on.",
        "err_provider_not_supported": "❌ Fournisseur '{provider}' non pris en charge. Choisissez : anthropic, openai, google, nvidia, github.",
        "err_provider_generic": "❌ Erreur {provider_name} : {error}",
        "err_api_key_not_configured_short": "Clé API non configurée",
        "err_invalid_image_format": "Format d'image non valide",
        "err_nvidia_api_key": "Clé API NVIDIA non configurée.",
        "err_nvidia_model_invalid": "Modèle NVIDIA non valide.",
        "err_nvidia_model_removed": "Modèle NVIDIA {reason} : {model_id}. Retiré de la liste.",
        "err_response_blocked": "{provider}: risposta bloccata dai filtri di sicurezza. Prova a riformulare la richiesta.",

        "status_image_processing": "Procesando imagen...",
        "status_context_preloaded": "Contesto precargado...",
        "status_nvidia_model_removed": "⚠️ Modèle NVIDIA non disponible (404). Retiré de la liste des modèles.",
        "status_tool_repair_retry": "État des outils réparé, nouvelle tentative...",
        "status_token_params_retry": "Paramètres de token incompatibles avec le modèle, nouvelle tentative.",
        "status_github_format_retry": "Modèle GitHub non riconosciuto, nouvelle tentative avec format alternatif.",
        "status_github_model_fallback": "Modèle non disponible su GitHub, passage à GPT-4o.",
        "status_rate_limit_waiting": "Límite de débit alcanzado, en attente...",
        "status_prompt_too_large": "Il modello selezionato ha un limite basso (prompt troppo grande). Riduco il contesto e riprovo...",
        "status_user_cancelled": "Annulé par l'utilisateur.",

        "write_op_success": "✅ Opération réalisée avec succès !",
        "write_no_changes": "\nAucun changement détecté (le contenu est identique).",
        "write_yaml_updated": "\n**YAML mis à jour :**",
        "write_yaml_created": "\n**YAML créé :**",
        "write_snapshot_created": "\n💾 Snapshot créé : `{snapshot_id}`",

        "intent_modify_automation": "Modifier une automatisation",
        "intent_modify_script": "Modifier un script",
        "intent_create_automation": "Créer une automatisation",
        "intent_create_script": "Créer un script",
        "intent_create_dashboard": "Créer un dashboard",
        "intent_modify_dashboard": "Modifier un dashboard",
        "intent_control_device": "Contrôle d'appareil",
        "intent_query_state": "État de l'appareil",
        "intent_query_history": "Historique des données",
        "intent_delete": "Suppression",
        "intent_config_edit": "Modifier la configuration",
        "intent_areas": "Gestion des pièces",
        "intent_notifications": "Notification",
        "intent_helpers": "Gestion des helpers",
        "intent_chat": "Chat",
        "intent_generic": "Analyse de la demande",
        "intent_default": "Traitement",

        "read_only_note": "**Mode lecture seule — aucun fichier n'a été modifié.**",

        "smart_context_script_found": "## YAML SCRIPT TROUVÉ : \"{alias}\" (id: {sid})\n```yaml\n{yaml}```\nPour le modifier, utilise update_script avec script_id='{sid}' et les champs à changer.",
        "read_only_instruction": "MODE LECTURE SEULE : Montre à l'utilisateur le code YAML complet dans un code block yaml. À la fin ajoute la note : ",
        "dashboard_created_successfully": "Dashboard créé avec succès ! Ton ",
        "dashboard_sidebar_ready": "dashboard apparaît dans la barre latérale à /{path}",
        "dashboard_sidebar_failed": "Le fichier HTML est prêt mais l'intégration dans la barre latérale a échoué",
    }
}

def get_lang_text(key: str) -> str:
    """Get language-specific text."""
    return LANGUAGE_TEXT.get(LANGUAGE, LANGUAGE_TEXT["en"]).get(key, "")


def tr(key: str, default: str = "", **kwargs) -> str:
    """Translate a key and apply simple str.format() interpolation."""
    txt = get_lang_text(key) or default
    if not kwargs:
        return txt
    try:
        return txt.format(**kwargs)
    except Exception:
        return txt

# ---- Image handling helpers (v3.0.0) ----

def parse_image_data(data_uri: str) -> tuple:
    """
    Parse data URI to extract media type and base64 data.
    Example: 'data:image/jpeg;base64,/9j/4AAQ...' -> ('image/jpeg', '/9j/4AAQ...')
    """
    if not data_uri or not data_uri.startswith('data:'):
        return None, None

    try:
        # Format: data:image/jpeg;base64,<base64_data>
        header, data = data_uri.split(',', 1)
        media_type = header.split(';')[0].split(':')[1]
        return media_type, data
    except:
        return None, None


def format_message_with_image_anthropic(text: str, media_type: str, base64_data: str) -> list:
    """
    Format message with image for Anthropic Claude.
    Returns content array with text and image blocks.
    """
    return [
        {"type": "text", "text": text},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64_data
            }
        }
    ]


def format_message_with_image_openai(text: str, data_uri: str) -> list:
    """
    Format message with image for OpenAI/GitHub.
    Returns content array with text and image_url blocks.
    """
    return [
        {"type": "text", "text": text},
        {
            "type": "image_url",
            "image_url": {"url": data_uri}
        }
    ]


def format_message_with_image_google(text: str, media_type: str, base64_data: str) -> list:
    """
    Format message with image for Google Gemini.
    Returns parts array for Gemini format.
    """
    # Gemini uses inline_data format
    return [
        {"text": text},
        {
            "inline_data": {
                "mime_type": media_type,
                "data": base64_data
            }
        }
    ]


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
}

# GitHub models that returned unknown_model at runtime (per current token)
GITHUB_MODEL_BLOCKLIST: set[str] = set()

# NVIDIA models that returned 404/unknown at runtime (per current key)
NVIDIA_MODEL_BLOCKLIST: set[str] = set()
GITHUB_MODEL_BLOCKLIST: set[str] = set()  # may be used by providers

# NVIDIA models that have been successfully chat-tested (per current key)
NVIDIA_MODEL_TESTED_OK: set[str] = set()

MODEL_BLOCKLIST_FILE = "/config/amira/model_blocklist.json"


def load_model_blocklists() -> None:
    """Load persistent model blocklists from disk."""
    global NVIDIA_MODEL_BLOCKLIST, GITHUB_MODEL_BLOCKLIST, NVIDIA_MODEL_TESTED_OK
    try:
        if os.path.isfile(MODEL_BLOCKLIST_FILE):
            with open(MODEL_BLOCKLIST_FILE, "r") as f:
                data = json.load(f) or {}
            nvidia = data.get("nvidia") or []
            github = data.get("github") or []

            # Backward compatible formats:
            # - {"nvidia": [..]} (legacy blocked-only)
            # - {"nvidia": {"blocked": [..], "tested_ok": [..]}}
            if isinstance(nvidia, dict):
                blocked = nvidia.get("blocked") or []
                tested_ok = nvidia.get("tested_ok") or []
                if isinstance(blocked, list):
                    NVIDIA_MODEL_BLOCKLIST.update([m for m in blocked if isinstance(m, str) and m.strip()])
                if isinstance(tested_ok, list):
                    NVIDIA_MODEL_TESTED_OK.update([m for m in tested_ok if isinstance(m, str) and m.strip()])
            elif isinstance(nvidia, list):
                NVIDIA_MODEL_BLOCKLIST.update([m for m in nvidia if isinstance(m, str) and m.strip()])
            if isinstance(github, list):
                GITHUB_MODEL_BLOCKLIST.update([m for m in github if isinstance(m, str) and m.strip()])
            if NVIDIA_MODEL_BLOCKLIST or GITHUB_MODEL_BLOCKLIST or NVIDIA_MODEL_TESTED_OK:
                logger.info(
                    f"Loaded model lists: nvidia_blocked={len(NVIDIA_MODEL_BLOCKLIST)}, nvidia_tested_ok={len(NVIDIA_MODEL_TESTED_OK)}, github_blocked={len(GITHUB_MODEL_BLOCKLIST)}"
                )
    except Exception as e:
        logger.warning(f"Could not load model blocklists: {e}")


def save_model_blocklists() -> None:
    """Persist model blocklists to disk."""
    try:
        os.makedirs(os.path.dirname(MODEL_BLOCKLIST_FILE), exist_ok=True)
        payload = {
            "nvidia": {
                "blocked": sorted(NVIDIA_MODEL_BLOCKLIST),
                "tested_ok": sorted(NVIDIA_MODEL_TESTED_OK),
            },
            "github": sorted(GITHUB_MODEL_BLOCKLIST),
        }
        with open(MODEL_BLOCKLIST_FILE, "w") as f:
            json.dump(payload, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Could not save model blocklists: {e}")


def mark_nvidia_model_tested_ok(model_id: str) -> None:
    """Mark a NVIDIA model as successfully tested and persist it."""
    if not isinstance(model_id, str) or not model_id.strip():
        return
    model_id = model_id.strip()
    if model_id in NVIDIA_MODEL_BLOCKLIST:
        return
    NVIDIA_MODEL_TESTED_OK.add(model_id)
    save_model_blocklists()


def blocklist_nvidia_model(model_id: str) -> None:
    """Add a model to NVIDIA blocklist, persist it, and drop it from cache."""
    if not isinstance(model_id, str) or not model_id.strip():
        return
    model_id = model_id.strip()
    NVIDIA_MODEL_BLOCKLIST.add(model_id)
    if model_id in NVIDIA_MODEL_TESTED_OK:
        NVIDIA_MODEL_TESTED_OK.discard(model_id)
    try:
        cached = _NVIDIA_MODELS_CACHE.get("models") or []
        if isinstance(cached, list) and model_id in cached:
            _NVIDIA_MODELS_CACHE["models"] = [m for m in cached if m != model_id]
    except Exception:
        pass
    save_model_blocklists()

# Cache for NVIDIA /v1/models discovery (to keep UI in sync with what's available for the current key)
_NVIDIA_MODELS_CACHE: dict[str, object] = {"ts": 0.0, "models": []}
_NVIDIA_MODELS_CACHE_TTL_SECONDS = 10 * 60


def _fetch_nvidia_models_live() -> Optional[list[str]]:
    """Fetch available NVIDIA models from the OpenAI-compatible endpoint.

    Returns a sorted list of model IDs, or None if unavailable.
    """
    if not NVIDIA_API_KEY:
        return None
    try:
        url = "https://integrate.api.nvidia.com/v1/models"
        headers = {"Authorization": f"Bearer {NVIDIA_API_KEY}"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        models: list[str] = []
        for item in (data.get("data") or []):
            if isinstance(item, dict):
                mid = item.get("id") or item.get("model")
                if isinstance(mid, str) and mid.strip():
                    models.append(mid.strip())
        models = sorted(set(models))
        return models or None
    except Exception as e:
        logger.warning(f"NVIDIA: unable to fetch /v1/models ({type(e).__name__}): {e}")
        return None


def get_nvidia_models_cached() -> Optional[list[str]]:
    """Return cached NVIDIA model IDs, refreshing periodically."""
    if not NVIDIA_API_KEY:
        return None

    now = time.time()
    ts = float(_NVIDIA_MODELS_CACHE.get("ts") or 0.0)
    cached_models = _NVIDIA_MODELS_CACHE.get("models") or []
    if cached_models and (now - ts) < _NVIDIA_MODELS_CACHE_TTL_SECONDS:
        if NVIDIA_MODEL_BLOCKLIST:
            return [m for m in list(cached_models) if m not in NVIDIA_MODEL_BLOCKLIST]
        return list(cached_models)

    live = _fetch_nvidia_models_live()
    if live:
        _NVIDIA_MODELS_CACHE["ts"] = now
        _NVIDIA_MODELS_CACHE["models"] = list(live)
        if NVIDIA_MODEL_BLOCKLIST:
            return [m for m in live if m not in NVIDIA_MODEL_BLOCKLIST]
        return live

    # Fallback to stale cache if present
    if cached_models:
        if NVIDIA_MODEL_BLOCKLIST:
            return [m for m in list(cached_models) if m not in NVIDIA_MODEL_BLOCKLIST]
        return list(cached_models)
    return None

# ---------------------------------------------------------------------------
# PROVIDER_MODELS — single source of truth is each provider's get_available_models().
# The static dict below is the authoritative fallback; at startup it is patched
# with the live list from each provider so edits to provider files take effect
# immediately without touching api.py.
# To update models for a provider → edit ONLY that provider's get_available_models().
# ---------------------------------------------------------------------------
_PROVIDER_MODELS_STATIC = {
    "anthropic": [
        # Ultimi (correnti)
        "claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001",
        # Legacy (ancora disponibili)
        "claude-sonnet-4-5-20250929", "claude-opus-4-5-20251101", "claude-opus-4-1-20250805",
        "claude-sonnet-4-20250514", "claude-opus-4-20250514",
    ],
    "openai": ["gpt-5.2", "gpt-5.2-mini", "gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3", "o3-mini", "o1"],
    "google": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
    "nvidia": [
        "moonshotai/kimi-k2.5",
        "meta/llama-3.1-70b-instruct",
        "meta/llama-3.1-405b-instruct",
        "mistralai/mistral-large-2-instruct",
        "microsoft/phi-4",
        "nvidia/llama-3.1-nemotron-70b-instruct",
    ],
    "github": [
        # OpenAI (via Azure) - gpt-4o and gpt-4o-mini are the stable defaults
        "openai/gpt-4o", "openai/gpt-4o-mini",
        "openai/gpt-4.1", "openai/gpt-4.1-mini", "openai/gpt-4.1-nano",
        "openai/o1", "openai/o1-mini", "openai/o1-preview",
        "openai/o3", "openai/o3-mini", "openai/o4-mini",
        # Preview / may not be available on all accounts
        "openai/gpt-5.2", "openai/gpt-5.2-mini",
        "openai/gpt-5", "openai/gpt-5-chat", "openai/gpt-5-mini", "openai/gpt-5-nano",
        # Meta Llama
        "meta/meta-llama-3.1-405b-instruct", "meta/meta-llama-3.1-8b-instruct",
        "meta/llama-3.3-70b-instruct",
        "meta/llama-4-scout-17b-16e-instruct", "meta/llama-4-maverick-17b-128e-instruct-fp8",
        "meta/llama-3.2-11b-vision-instruct", "meta/llama-3.2-90b-vision-instruct",
        # Mistral
        "mistral-ai/mistral-small-2503", "mistral-ai/mistral-medium-2505",
        "mistral-ai/ministral-3b", "mistral-ai/codestral-2501",
        # Cohere
        "cohere/cohere-command-r-plus-08-2024", "cohere/cohere-command-r-08-2024",
        "cohere/cohere-command-a",
        # DeepSeek
        "deepseek/deepseek-r1", "deepseek/deepseek-r1-0528", "deepseek/deepseek-v3-0324",
        # Microsoft
        "microsoft/mai-ds-r1", "microsoft/phi-4", "microsoft/phi-4-mini-instruct",
        "microsoft/phi-4-reasoning", "microsoft/phi-4-mini-reasoning",
        "microsoft/phi-4-multimodal-instruct",
        # AI21
        "ai21-labs/ai21-jamba-1.5-large",
        # xAI
        "xai/grok-3", "xai/grok-3-mini",
    ],
    "groq": [
        # Production models
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        # Production systems (agentic)
        "groq/compound",
        "groq/compound-mini",
        # Preview models
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
        "moonshotai/kimi-k2-instruct-0905",
    ],
    "mistral": [
        "mistral-large-latest",
        "mistral-medium",
        "mistral-small-latest",
        "open-mixtral-8x7b",
        "open-mixtral-8x22b",
    ],
    "ollama": [
        "mistral",
        "llama2",
        "neural-chat",
        "orca-mini",
        "dolphin-mixtral",
        "openchat",
    ],
    "openrouter": [
        "anthropic/claude-opus-4.6", "anthropic/claude-sonnet-4.6",
        "openai/gpt-4o", "openai/gpt-4o-mini",
        "meta-llama/llama-3.1-405b-instruct",
        "mistralai/mistral-large-2512",
        "google/gemini-2.0-flash-001",
        "openrouter/auto",
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-r1",
        "deepseek-v3",
    ],
    "minimax": [
        "MiniMax-M2.1",
        "MiniMax-M2",
        "MiniMax-M3",
    ],
    "aihubmix": [
        "gpt-4o", "gpt-4-turbo",
        "claude-opus-4-6", "claude-sonnet-4-6",
        "gemini-2.0-flash",
        "llama-3.1-405b",
    ],
    "siliconflow": [
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
        "meta-llama/Llama-3.1-70B-Instruct",
        "mistral/Mistral-7B-Instruct-v0.3",
    ],
    "volcengine": [
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
        "meta-llama/Llama-3.1-70B-Instruct",
    ],
    "dashscope": [
        "qwen-max",
        "qwen-plus",
        "qwen-turbo",
        "qwen-long",
        "qwen-vl-plus",
    ],
    "moonshot": [
        "kimi-k2.5",
        "kimi-k2",
        "kimi-k1.5",
        "kimi-k1",
    ],
    "zhipu": [
        "glm-4-flash",
        "glm-4-flash-250414",
        "glm-4-air",
        "glm-4-airx",
        "glm-4-plus",
        "glm-4-long",
        "glm-z1-flash",
        "glm-z1-air",
        "glm-z1-airx",
        "glm-4",
        "glm-4v",
    ],
    "perplexity": [
        "sonar-pro",
        "sonar",
        "sonar-reasoning-pro",
        "sonar-reasoning",
        "r1-1776",
    ],
    "custom": [],  # model name comes from CUSTOM_MODEL_NAME env var
}

# Build PROVIDER_MODELS: start from static fallback, then patch each provider
# with its own get_available_models() so the provider file is the single source
# of truth. Providers that fail to import (missing deps at import time) keep
# the static fallback silently.
PROVIDER_MODELS = dict(_PROVIDER_MODELS_STATIC)

try:
    from providers import _PROVIDER_CLASSES, get_provider_class as _get_provider_class
    for _pid in list(_PROVIDER_CLASSES):
        try:
            _cls = _get_provider_class(_pid)
            _live = _cls().get_available_models()
            if _live:  # only replace if the provider returned something
                PROVIDER_MODELS[_pid] = _live
        except Exception:
            pass  # keep static fallback for this provider
except Exception:
    pass

# Load persisted model cache from disk (populated by /api/refresh_models).
# Overlay on PROVIDER_MODELS so the UI shows dynamically-fetched models.
try:
    from providers.model_fetcher import load_cache as _load_model_cache
    _model_cache = _load_model_cache()
    for _p, _ml in _model_cache.items():
        if _ml:
            PROVIDER_MODELS[_p] = _ml
    if _model_cache:
        import logging as _log
        _log.getLogger(__name__).info(f"Loaded model cache for {len(_model_cache)} providers")
except Exception as _mc_err:
    pass  # cache optional — dynamic lists remain


# Mapping user-friendly names (with prefixes) to technical model names
MODEL_NAME_MAPPING = {
    "Claude: Opus 4.6": "claude-opus-4-6",
    "Claude: Sonnet 4.6": "claude-sonnet-4-6",
    "Claude: Haiku 4.5": "claude-haiku-4-5-20251001",
    "Claude: Sonnet 4.5": "claude-sonnet-4-5-20250929",
    "Claude: Opus 4.5": "claude-opus-4-5-20251101",
    "Claude: Opus 4.1": "claude-opus-4-1-20250805",
    "Claude: Sonnet 4": "claude-sonnet-4-20250514",
    "Claude: Opus 4": "claude-opus-4-20250514",
    "OpenAI: GPT-5.2": "gpt-5.2",
    "OpenAI: GPT-5.2-mini": "gpt-5.2-mini",
    "OpenAI: GPT-5": "gpt-5",
    "OpenAI: GPT-4o": "gpt-4o",
    "OpenAI: GPT-4o-mini": "gpt-4o-mini",
    "OpenAI: GPT-4-turbo": "gpt-4-turbo",
    "OpenAI: o3": "o3",
    "OpenAI: o3-mini": "o3-mini",
    "OpenAI: o1": "o1",
    "Google: Gemini 2.0 Flash": "gemini-2.0-flash",
    "Google: Gemini 2.5 Pro": "gemini-2.5-pro",
    "Google: Gemini 2.5 Flash": "gemini-2.5-flash",
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
    
    "GitHub Copilot: GPT-4o": "gpt-4o",
    "GitHub Copilot: GPT-4o-mini": "gpt-4o-mini",
    "GitHub Copilot: o3-mini": "o3-mini",
    "GitHub Copilot: o1": "o1",
    "GitHub Copilot: o1-mini": "o1-mini",
    "GitHub Copilot: Claude 3.7 Sonnet": "claude-3.7-sonnet",
    "GitHub Copilot: Claude 3.5 Sonnet": "claude-3.5-sonnet",
    "GitHub Copilot: Gemini 2.0 Flash": "gemini-2.0-flash",
    "GitHub Copilot: Gemini 1.5 Pro": "gemini-1.5-pro",

    "OpenAI Codex: gpt-5.3-codex": "gpt-5.3-codex",
    "OpenAI Codex: gpt-5.3-codex-spark": "gpt-5.3-codex-spark",
    "OpenAI Codex: gpt-5.2-codex": "gpt-5.2-codex",
    "OpenAI Codex: gpt-5.1-codex-max": "gpt-5.1-codex-max",
    "OpenAI Codex: gpt-5.1-codex": "gpt-5.1-codex",
    "OpenAI Codex: gpt-5-codex": "gpt-5-codex",
    "OpenAI Codex: gpt-5-codex-mini": "gpt-5-codex-mini",
    "Claude Web: claude-opus-4-5-20251101": "claude-opus-4-5-20251101",
    "Claude Web: claude-sonnet-4-5-20250929": "claude-sonnet-4-5-20250929",
    "Claude Web: claude-haiku-4-5-20251001": "claude-haiku-4-5-20251001",
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


def normalize_model_name(model_name: str) -> str:
    """Convert user-friendly model name to technical name.
    Handles legacy names with emoji badges (🆓, 🧪) for backward compatibility."""
    # Direct lookup
    if model_name in MODEL_NAME_MAPPING:
        return MODEL_NAME_MAPPING[model_name]
    
    # Try stripping emoji badges (🆓, 🧪) for backward compat with old configs
    import re
    cleaned = re.sub(r'[\s]*[🆓🧪]+[\s]*$', '', model_name).strip()
    if cleaned and cleaned in MODEL_NAME_MAPPING:
        return MODEL_NAME_MAPPING[cleaned]
    
    # Not found, return as-is (assume it's already a technical name)
    return model_name


def get_model_provider(model_name: str) -> str:
    """Get the provider prefix from a model name."""
    if model_name.startswith("Claude:"):
        return "anthropic"
    elif model_name.startswith("OpenAI:"):
        return "openai"
    elif model_name.startswith("Google:"):
        return "google"
    elif model_name.startswith("NVIDIA:"):
        return "nvidia"
    elif model_name.startswith("GitHub:"):
        return "github"
    # Try to infer from technical name
    tech_name = normalize_model_name(model_name)
    # GitHub Models uses fully-qualified IDs with a 'vendor/' prefix (openai/, meta/, mistral-ai/, etc.)
    # All of these belong to GitHub — not to the individual vendor's direct API.
    _GITHUB_VENDOR_PREFIXES = (
        "openai/", "meta/", "mistral-ai/", "mistralai/", "microsoft/",
        "deepseek/", "cohere/", "ai21-labs/", "xai/",
    )
    if any(tech_name.startswith(p) for p in _GITHUB_VENDOR_PREFIXES):
        return "github"
    if tech_name.startswith("claude-"):
        return "anthropic"
    elif tech_name in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o3-mini"]:
        return "openai"
    elif tech_name.startswith("gemini-"):
        return "google"
    elif tech_name.startswith(("moonshotai/", "nvidia/")):
        return "nvidia"
    return "unknown"


def validate_model_provider_compatibility() -> tuple[bool, str]:
    """Validate that the selected model is compatible with the selected provider."""
    if not AI_MODEL:
        return True, ""  # No model selected, use default

    # Solo provider "stretti" hanno modelli esclusivi — skip check per tutti gli altri
    _STRICT_PROVIDERS = {"anthropic", "openai", "google"}
    if AI_PROVIDER not in _STRICT_PROVIDERS:
        return True, ""

    model_provider = get_model_provider(AI_MODEL)
    if model_provider == "unknown":
        return True, ""  # Can't determine, allow it

    if model_provider != AI_PROVIDER:
        # Multilingual warning messages
        warnings = {
            "en": f"⚠️ WARNING: You selected model '{AI_MODEL}' which is not compatible with provider '{AI_PROVIDER}'. Change provider or model.",
            "it": f"⚠️ ATTENZIONE: Hai selezionato un modello '{AI_MODEL}' che non è compatibile con il provider '{AI_PROVIDER}'. Cambia provider o modello.",
            "es": f"⚠️ ADVERTENCIA: Has seleccionado el modelo '{AI_MODEL}' que no es compatible con el proveedor '{AI_PROVIDER}'. Cambia proveedor o modelo.",
            "fr": f"⚠️ ATTENTION: Vous avez sélectionné le modèle '{AI_MODEL}' qui n'est pas compatible avec le fournisseur '{AI_PROVIDER}'. Changez de fournisseur ou de modèle."
        }
        error_msg = warnings.get(LANGUAGE, warnings["en"])
        return False, error_msg

    return True, ""


def get_active_model() -> str:
    """Get the active model name (technical format).
    Prefers the user's selected model/provider if set, else falls back to global AI_MODEL."""
    # Solo Anthropic, OpenAI e Google hanno modelli esclusivi — per tutti gli altri provider
    # (gateway multi-vendor: NVIDIA, GitHub, OpenRouter, Groq, ecc.) accettiamo qualsiasi modello.
    _STRICT_PROVIDERS = {"anthropic", "openai", "google"}

    def _model_ok(model: str) -> bool:
        """Return True if model is compatible with current provider (or check is N/A)."""
        if AI_PROVIDER not in _STRICT_PROVIDERS:
            return True  # gateway provider: never reject
        mp = get_model_provider(model)
        return mp in (AI_PROVIDER, "unknown")

    # Use SELECTED_MODEL if the user has made a selection AND provider matches
    if SELECTED_MODEL and SELECTED_PROVIDER == AI_PROVIDER:
        model = normalize_model_name(SELECTED_MODEL)
        if _model_ok(model):
            if AI_PROVIDER == "openai" and model.startswith("openai/"):
                return model.split("/", 1)[1]
            return model

    # Fall back to AI_MODEL (from config/env)
    if AI_MODEL:
        model = normalize_model_name(AI_MODEL)
        if _model_ok(model):
            if AI_PROVIDER == "openai" and model.startswith("openai/"):
                return model.split("/", 1)[1]
            return model

    # Custom provider: fall back to configured model name
    if AI_PROVIDER == "custom" and CUSTOM_MODEL_NAME:
        return CUSTOM_MODEL_NAME

    # Last resort: use provider default
    return PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("model", "unknown")


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
        "o1", "o3", "o4", "gpt-5", "grok-3"
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


# Cache for addon ingress URL (doesn't change at runtime)
_ingress_url_cache: Optional[str] = None


def get_addon_ingress_url() -> str:
    """Get the Ingress URL path for this addon from the Supervisor API.
    
    Returns the ingress_url (e.g., '/api/hassio_ingress/<token>') that can be
    used as prefix for iframe URLs so HA frontend proxies to the addon.
    Result is cached since it doesn't change at runtime.
    """
    global _ingress_url_cache
    if _ingress_url_cache is not None:
        return _ingress_url_cache

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
                # Remove trailing slash if present
                _ingress_url_cache = ingress_url.rstrip("/")
                logger.info(f"🔗 Addon Ingress URL: {_ingress_url_cache}")
                return _ingress_url_cache
            else:
                logger.warning("⚠️ ingress_url not found in Supervisor addon info")
        else:
            logger.error(f"❌ Supervisor API returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"❌ Failed to get addon ingress URL: {e}")

    # Fallback: empty string (URL will be relative, may 404)
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
        # Ollama è locale, non ha API key — il provider viene gestito da providers/manager.py
        logger.info(f"Ollama provider selected (local, no API key required). Model: {get_active_model()}")
        ai_client = None
    elif AI_PROVIDER in (
        "groq", "mistral", "openrouter", "deepseek", "minimax",
        "aihubmix", "siliconflow", "volcengine", "dashscope",
        "moonshot", "zhipu", "github_copilot", "openai_codex",
        "claude_web", "chatgpt_web",
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
        else:
            logger.warning(f"AI provider '{AI_PROVIDER}' not configured - set the API key in addon settings")
        ai_client = None
    else:
        logger.warning(f"AI provider '{AI_PROVIDER}' not configured - set the API key in addon settings")
        ai_client = None

    return ai_client


ai_client = None
# Prefer persisted selection (set by /api/set_model) over add-on configuration
load_runtime_selection()
initialize_ai_client()

import pathlib

# Conversation history
conversations: Dict[str, List[Dict]] = {}

# Abort flag per session (for stop button)
abort_streams: Dict[str, bool] = {}

# Read-only mode per session
read_only_sessions: Dict[str, bool] = {}

# Last intent per session (for confirmation continuity)
session_last_intent: Dict[str, str] = {}

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
                # Still unknown after variants: blocklist canonical ID (the one shown in UI)
                if bad_model:
                    GITHUB_MODEL_BLOCKLIST.add(bad_model)

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
    i = 0
    while i < len(messages):
        m = messages[i]
        role = m.get("role", "")
        skip = False

        # Skip tool-role messages for Anthropic (it uses tool_result inside user messages)
        if AI_PROVIDER == "anthropic" and role == "tool":
            skip = True

        # Skip assistant messages with tool_calls format (OpenAI format) for Anthropic
        elif AI_PROVIDER == "anthropic" and role == "assistant" and m.get("tool_calls"):
            skip = True

        # For Anthropic: Skip assistant messages with tool_use blocks if not followed by tool_result
        elif AI_PROVIDER == "anthropic" and role == "assistant":
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

        # Skip Anthropic-format tool_result messages for OpenAI/GitHub
        elif AI_PROVIDER in ("openai", "github") and role == "user" and isinstance(m.get("content"), list):
            if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in m.get("content", [])):
                skip = True

        # For OpenAI/GitHub: Skip assistant messages with tool_calls if tool responses are missing
        elif AI_PROVIDER in ("openai", "github") and role == "assistant" and m.get("tool_calls"):
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

        # Keep user/assistant/tool messages if not skipped
        if not skip:
            if role in ("user", "assistant"):
                content = m.get("content", "")
                # Accept strings or arrays (arrays can contain images)
                if isinstance(content, str) and content:
                    clean.append({"role": role, "content": content})
                elif isinstance(content, list) and content:
                    clean.append({"role": role, "content": content})
            elif AI_PROVIDER in ("openai", "github") and role == "tool":
                # Pass through tool responses for OpenAI/GitHub (required after tool_calls)
                clean.append(m)

        i += 1
    
    # Limit total messages: keep only last 10
    if len(clean) > 10:
        clean = clean[-10:]
    
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
            clean[i] = {"role": clean[i]["role"], "content": content}
    
    return clean


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
    parts: list[str] = []
    for event in stream_chat_with_ai(user_message, session_id):
        event_type = event.get("type")
        if event_type == "token":
            # stream_chat_with_ai normalizes "text" → "token" with field "content"
            parts.append(event.get("content", ""))
        elif event_type == "text":
            # fallback: some paths might still yield "text" directly
            parts.append(event.get("text", ""))
        elif event_type == "error":
            return "❌ " + event.get("message", "Errore sconosciuto")
    result = "".join(parts).strip()
    result = _clean_unnecessary_comments(result)
    return result


def chat_with_ai(user_message: str, session_id: str = "default") -> str:
    """Send a message to the configured AI provider with HA tools."""
    # Legacy providers use ai_client directly; manager.py providers have ai_client=None (normal).
    _LEGACY_PROVIDERS = {"anthropic", "openai", "google", "nvidia", "github"}

    if not ai_client and AI_PROVIDER in _LEGACY_PROVIDERS:
        provider_name = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("name", AI_PROVIDER)
        return tr("err_api_key_not_configured", provider_name=provider_name)

    # Provider managed by providers/manager.py (groq, mistral, claude_web, chatgpt_web, etc.)
    if AI_PROVIDER not in _LEGACY_PROVIDERS:
        return _collect_from_stream(user_message, session_id)

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


def _inject_proposal_diff(text: str, cached_originals: dict) -> str:
    """For config_edit proposal phase: replace ```yaml blocks with side-by-side diff views.
    Returns the display text (for streaming to user). The caller should keep the original
    text intact in message history so the model can reference the proposed YAML later.
    Only replaces when a non-empty original exists (i.e. editing, not creating a new file)."""
    import re as _re
    if not cached_originals:
        return text
    original = list(cached_originals.values())[-1]
    if not original.strip():
        return text  # New file — show full code, no diff
    yaml_block_re = _re.compile(r'```yaml\n([\s\S]*?)\n?```')
    matches = list(yaml_block_re.finditer(text))
    if not matches:
        return text
    result = text
    for match in reversed(matches):
        proposed_yaml = match.group(1).strip()
        diff_html = _build_side_by_side_diff_html(original, proposed_yaml)
        if diff_html:
            result = result[:match.start()] + f"<!--DIFF-->{diff_html}<!--/DIFF-->" + result[match.end():]
    return result


def _format_write_tool_response(tool_name: str, result_data: dict) -> str:
    """Format a human-readable response from a successful write tool result.
    This avoids needing another API round just to format the response.
    For UPDATE operations, shows a side-by-side diff (red/green)."""
    parts = []

    msg = result_data.get("message", "")
    if msg:
        parts.append(f"\u2705 {msg}")
    else:
        parts.append(tr("write_op_success"))

    # Show diff for update tools (only for updates, not creates)
    old_yaml = result_data.get("old_yaml", "")
    new_yaml = result_data.get("new_yaml", "") or result_data.get("yaml", "")

    update_tools = ("update_automation", "update_script", "update_dashboard", "write_config_file")

    if old_yaml and new_yaml and tool_name in update_tools:
        diff_html = _build_side_by_side_diff_html(old_yaml, new_yaml)
        if diff_html:
            # Wrap in marker so chat_ui.formatMarkdown passes it through as raw HTML
            parts.append(f"\n<!--DIFF-->{diff_html}<!--/DIFF-->")
        else:
            parts.append(tr("write_no_changes"))

        # Also show the updated YAML (required by show_yaml_rule)
        parts.append(tr("write_yaml_updated"))
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

    return "\n".join(parts)



def stream_chat_with_ai(user_message: str, session_id: str = "default", image_data: str = None, read_only: bool = False):
    """Stream chat events for all providers with optional image support. Yields SSE event dicts.
    Uses LOCAL intent detection + smart context to minimize tokens sent to AI API."""
    global current_session_id
    
    # Strip context blocks from user_message for saving in conversation history
    # This prevents [CONTEXT:...] and [CURRENT_DASHBOARD_HTML]... from cluttering the history
    saved_user_message = user_message
    import re
    saved_user_message = re.sub(r'\[CONTEXT:.*?\]\[CURRENT_DASHBOARD_HTML\].*?\[/CURRENT_DASHBOARD_HTML\]\n*', '', saved_user_message, flags=re.DOTALL)
    saved_user_message = saved_user_message.strip()
    
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

    # Step 1: LOCAL intent detection FIRST (need this BEFORE building smart context)
    # We do a preliminary detect to know if user is creating or modifying
    intent_info = intent.detect_intent(user_message, "", previous_intent=prev_intent)  # Empty context for first pass
    intent_name = intent_info["intent"]

    # Step 2: Build smart context NOW that we know the intent
    # If user is creating new automation/script, skip fuzzy matching to avoid false automation injection
    # When the message contains [CURRENT_DASHBOARD_HTML] the HTML is extracted and will be injected
    # as a SEPARATE earlier turn in the conversation (user: HTML, assistant: "ok, letto"), so the
    # actual user message sent to the model is only the clean request text + normal smart context.
    # This avoids token overflow without losing entity awareness.
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

    smart_context = intent.build_smart_context(
        user_message,
        intent=intent_name,
        # Use normal cap — the HTML will be a separate turn, not part of this message
    )

    # Step 2.5: Inject memory context if enabled (nanobot style: reads MEMORY.md once, no cross-session search)
    memory_context = ""
    if ENABLE_MEMORY and MEMORY_AVAILABLE:
        memory_context = memory.get_memory_context()
        if memory_context:
            logger.info(f"Memory context (MEMORY.md) injected for session {session_id}")
            smart_context = memory_context + "\n\n" + smart_context

    # Step 3: Re-detect intent WITH full smart context for accuracy
    intent_info = intent.detect_intent(user_message, smart_context, previous_intent=prev_intent)
    intent_name = intent_info["intent"]

    # Store this intent for next message's confirmation continuity
    session_last_intent[session_id] = intent_name
    tool_count = len(intent_info.get("tools") or [])
    all_tools_count = len(tools.HA_TOOLS_DESCRIPTION)
    logger.info(f"Intent detected: {intent_name} (specific_target={intent_info['specific_target']}, tools={tool_count if tool_count else all_tools_count})")
    
    # Show intent to user (translated)
    INTENT_KEYS = {
        "modify_automation": "intent_modify_automation",
        "modify_script": "intent_modify_script",
        "create_automation": "intent_create_automation",
        "create_script": "intent_create_script",
        "create_dashboard": "intent_create_dashboard",
        "modify_dashboard": "intent_modify_dashboard",
        "control_device": "intent_control_device",
        "query_state": "intent_query_state",
        "query_history": "intent_query_history",
        "delete": "intent_delete",
        "config_edit": "intent_config_edit",
        "areas": "intent_areas",
        "notifications": "intent_notifications",
        "helpers": "intent_helpers",
        "chat": "intent_chat",
        "generic": "intent_generic",
    }
    intent_key = INTENT_KEYS.get(intent_name, "intent_default")
    intent_label = tr(intent_key)
    yield {"type": "status", "message": f"{intent_label}... ({tool_count if tool_count else all_tools_count} tools)"}

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
                api_content = f"{user_message}\n\n---\nCONTEXT:\n{smart_context}\n---\nDo NOT request data already provided above. ONE tool call only, then respond."
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
                api_content = (
                    f"{clean_user_message}\n\n---\nCONTEXT:\n{smart_context}\n---\n"
                    "Use the entity_ids listed above directly in your HTML. "
                    "Output ONLY the complete <!DOCTYPE html>…</html> page, nothing else."
                )
            else:
                api_content = f"{clean_user_message}\n\n---\nCONTEXT:\n{smart_context}\n---\nDo NOT request data already provided above. ONE tool call only, then respond."
            # Log estimated token count
            est_tokens = len(api_content) // 4  # ~4 chars per token
            logger.info(f"Smart context: {len(smart_context)} chars, est. ~{est_tokens} tokens for user message")
            yield {"type": "status", "message": tr("status_context_preloaded")}
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
        _html_turn_assistant = (
            f"Ho letto la dashboard corrente{_name_label}. "
            "Dimmi cosa vuoi modificare o aggiungere."
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
        # Remember current conversation length to avoid duplicates
        conv_length_before = len(conversations[session_id])
        last_usage = None  # Will capture usage from done event
        _streamed_text_parts: list = []  # accumulate streamed tokens for saving

        # Clean messages for specific providers that need it
        if AI_PROVIDER in ("anthropic", "google"):
            clean_messages = sanitize_messages_for_provider(messages)
            messages = clean_messages

        # Inject tool schemas into intent_info so providers can pass them to the API.
        # This enables tool calling for all OpenAI-compatible providers (Mistral, Groq, etc.)
        # and for the Anthropic SDK provider.
        if intent_info is not None:
            intent_info["tool_schemas"] = tools.get_openai_tools()

        # Tool execution loop: providers surface tool_calls in the done event;
        # we execute them here and loop until the model produces a final answer.
        _MAX_TOOL_ROUNDS = 8
        _tool_round = 0
        _tool_cache: dict = {}
        _read_only_tools = {
            "get_automations", "get_scripts", "get_dashboards",
            "get_dashboard_config", "read_config_file",
            "list_config_files", "get_frontend_resources",
            "search_entities", "get_entity_state", "get_entities",
        }

        while _tool_round < _MAX_TOOL_ROUNDS:
            _tool_round += 1

            # Use unified provider interface (replaces old provider_*.py functions)
            # Passa il modello attivo esplicitamente così il provider non usa default errati
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
            _NO_TOOL_PROVIDERS = {"claude_web", "chatgpt_web", "github_copilot", "openai_codex"}
            _is_no_tool_provider = AI_PROVIDER in _NO_TOOL_PROVIDERS
            _text_buffer: list = []

            # Stream events, intercepting 'done' to enrich with cost or detect tool calls
            for event in provider_gen:
                if event.get("type") == "done":
                    _pending_tool_calls = event.get("tool_calls") or []
                    if not _pending_tool_calls:
                        full_buf = "".join(_text_buffer)

                        # ── Tool Simulator: extract <tool_call> blocks from buffered text ──
                        if _is_no_tool_provider and full_buf and not _is_html_dash:
                            from providers.tool_simulator import extract_tool_calls, clean_response_text
                            _sim_calls = extract_tool_calls(full_buf)
                            if _sim_calls:
                                # Inject as pending tool calls — the normal loop below handles them
                                _pending_tool_calls = _sim_calls
                                # For read-only tool calls, suppress the introductory text:
                                # the model will respond properly once it sees the tool results.
                                # For write tool calls, show the confirmation text to the user.
                                _all_read_only = all(
                                    tc.get("name", "") in _read_only_tools
                                    for tc in _sim_calls
                                )
                                if not _all_read_only:
                                    cleaned = clean_response_text(full_buf)
                                    if cleaned:
                                        yield {"type": "token", "content": cleaned}
                                _text_buffer = []
                                # Do NOT yield done yet — let the tool loop continue
                                break
                            # No tool_calls found → plain text response, flush as-is
                            if full_buf:
                                yield {"type": "token", "content": full_buf}
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
                                # Emit a short confirmation — the full HTML will be auto-saved
                                yield {"type": "token", "content": "✨ Dashboard salvata!"}
                            else:
                                # No HTML found → clarifying question or tool-capable provider;
                                # flush the buffer normally so the user sees the response.
                                for buffered_chunk in _text_buffer:
                                    yield {"type": "token", "content": buffered_chunk}
                            _text_buffer = []

                        # Normal completion — enrich with cost and forward to client
                        if event.get("usage"):
                            raw_usage = event["usage"]
                            input_tokens = raw_usage.get("input_tokens") or raw_usage.get("prompt_tokens", 0)
                            output_tokens = raw_usage.get("output_tokens") or raw_usage.get("completion_tokens", 0)
                            model_name = raw_usage.get("model") or get_active_model()
                            provider_name = raw_usage.get("provider") or AI_PROVIDER
                            cost = pricing.calculate_cost(
                                model_name, provider_name, input_tokens, output_tokens, COST_CURRENCY,
                            )
                            usage = {
                                **raw_usage,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "cost": cost,
                                "currency": COST_CURRENCY,
                            }
                            event = {**event, "usage": usage}
                            last_usage = usage
                        if not _pending_tool_calls:
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
                    else:
                        yield {"type": "token", "content": chunk}
                elif event.get("type") == "token":
                    # Some providers yield token events directly — accumulate those too
                    content = event.get("content", "")
                    _streamed_text_parts.append(content)
                    if _is_html_dash or _is_no_tool_provider:
                        _text_buffer.append(content)  # buffer: process after done
                    else:
                        yield event
                else:
                    yield event

            if not _pending_tool_calls:
                break  # No tool calls → conversation complete

            # --- Execute tool calls and prepare next round ---
            text_so_far = "".join(_streamed_text_parts)
            _streamed_text_parts = []

            # Append assistant message with tool_calls (OpenAI format)
            messages.append({
                "role": "assistant",
                "content": text_so_far or None,
                "tool_calls": [
                    {
                        "id": tc.get("id", f"call_{i}"),
                        "type": "function",
                        "function": {
                            "name": tc.get("name", ""),
                            "arguments": tc.get("arguments", "{}"),
                        },
                    }
                    for i, tc in enumerate(_pending_tool_calls)
                ],
            })

            # Execute each tool and append its result
            for tc in _pending_tool_calls:
                fn_name = tc.get("name", "")
                try:
                    tc_args = json.loads(tc.get("arguments", "{}") or "{}")
                except Exception:
                    tc_args = {}

                # Show status to user
                _status_label = tools.TOOL_DESCRIPTIONS.get(fn_name, fn_name)
                yield {"type": "status", "message": f"🔧 {_status_label}..."}
                logger.info(f"Tool (round {_tool_round}): {fn_name} {list(tc_args.keys())}")

                _sig = f"{fn_name}:{json.dumps(tc_args, sort_keys=True)}"
                if fn_name in _read_only_tools and _sig in _tool_cache:
                    logger.debug(f"Tool cache hit: {fn_name}")
                    result = _tool_cache[_sig]
                else:
                    result = tools.execute_tool(fn_name, tc_args)
                    if fn_name in _read_only_tools:
                        _tool_cache[_sig] = result

                # Extract diff for UI rendering (strip before feeding to model)
                try:
                    _result_obj = json.loads(result)
                    if isinstance(_result_obj, dict) and "diff" in _result_obj:
                        _diff_content = _result_obj.pop("diff")
                        result = json.dumps(_result_obj, ensure_ascii=False)
                        yield {"type": "diff", "content": _diff_content}
                except Exception:
                    pass

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_{fn_name}"),
                    "content": result,
                })

        # Sync new assistant messages to conversation history.
        # New-path providers (Mistral, Groq, openai_compatible, etc.) stream text as
        # events but do NOT append to `messages`, so we use _streamed_text_parts.
        # Old-path providers (legacy Anthropic/OpenAI agentic loop) append directly
        # to `messages` — handle both cases without duplicating.
        is_anthropic_or_google = AI_PROVIDER in ("anthropic", "google")
        new_msgs_from_provider = [
            msg for msg in messages[conv_length_before:]
            if msg.get("role") == "assistant"
            and not (is_anthropic_or_google and isinstance(msg.get("content", ""), list))
        ]
        if new_msgs_from_provider:
            # Old-path: provider appended messages directly, use those
            for msg in new_msgs_from_provider:
                msg["model"] = get_active_model()
                msg["provider"] = AI_PROVIDER
                if last_usage:
                    msg["usage"] = last_usage
                conversations[session_id].append(msg)
        elif _streamed_text_parts:
            # New-path: assemble streamed tokens and save as assistant message
            assembled = "".join(_streamed_text_parts).strip()
            if assembled:
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
                    # 1. ```html ... ``` closed block (with or without DOCTYPE)
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
                            _save_result = tools.execute_tool("create_html_dashboard", {
                                "title": _title,
                                "name": _slug,
                                "entities": _entities,
                                "html": html_block,
                            })
                            logger.info(
                                f"Auto-saved HTML dashboard '{_slug}' "
                                f"(entities={len(_entities)}): {str(_save_result)[:200]}"
                            )
                            yield {"type": "status", "message": f"✅ Dashboard HTML '{_slug}.html' salvata!"}
                        except Exception as _e:
                            logger.warning(f"Auto-save HTML dashboard failed: {_e}")
                            yield {"type": "status", "message": f"⚠️ Salvataggio HTML fallito: {_e}"}
                # ──────────────────────────────────────────────────────────
                # NOTE: sentinel-based auto-execute blocks (CONFIRM_CREATE_AUTOMATION etc.)
                # have been removed. No-tool providers now use the universal Tool Simulator
                # (<tool_call> XML blocks) which are handled by the streaming loop above.

        # Trim and save
        if len(conversations[session_id]) > 50:
            conversations[session_id] = conversations[session_id][-40:]
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
        return
    if not ENABLE_CHAT_BUBBLE:
        cleanup_chat_bubble()
        return

    try:
        import chat_bubble

        ingress_url = get_addon_ingress_url()
        if not ingress_url:
            logger.warning("Chat bubble: Cannot register — ingress URL not available")
            return

        js_content = chat_bubble.get_chat_bubble_js(
            ingress_url=ingress_url,
            language=LANGUAGE,

        )

        # Save to /config/www/ (served by HA at /local/)
        www_dir = os.path.join(HA_CONFIG_DIR, "www")
        os.makedirs(www_dir, exist_ok=True)
        js_path = os.path.join(www_dir, "ha-claude-chat-bubble.js")
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        logger.info(f"Chat bubble: JS saved to {js_path} ({len(js_content)} chars)")

        # Register as Lovelace resource via websocket
        # Use timestamp for aggressive cache-busting (browser ignores ?v=version)
        import hashlib
        content_hash = hashlib.md5(js_content.encode()).hexdigest()[:8]
        resource_url = "/local/ha-claude-chat-bubble.js"
        cache_bust_url = f"{resource_url}?v={VERSION}&h={content_hash}"
        try:
            ws_result = call_ha_websocket("lovelace/resources/list")
            # WS returns {"type":"result","success":true,"result":[...]}
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
                                call_ha_websocket(
                                    "lovelace/resources/update",
                                    resource_id=res["id"],
                                    url=cache_bust_url,
                                    res_type="js",
                                )
                                logger.info(f"Chat bubble: Updated Lovelace resource ({cache_bust_url})")
                            except Exception as e:
                                logger.warning(f"Chat bubble: Could not update resource: {e}")
                        else:
                            duplicates.append(res)
                # Clean up duplicate registrations
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
                logger.info(f"Chat bubble: Registered Lovelace resource ({cache_bust_url}) -> {create_result}")
        except Exception as e:
            logger.warning(f"Chat bubble: Could not register Lovelace resource: {e}")
            logger.info(f"Chat bubble: Add manually in HA -> Settings -> Dashboards -> Resources: {resource_url}")

        _chat_bubble_registered = True

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

        js_path = os.path.join(HA_CONFIG_DIR, "www", "ha-claude-chat-bubble.js")
        if os.path.isfile(js_path):
            os.remove(js_path)
            logger.info(f"Chat bubble cleanup: Deleted {js_path}")

        if removed or os.path.isfile(js_path):
            logger.info("Chat bubble cleanup: Done")
    except Exception as e:
        logger.warning(f"Chat bubble cleanup failed: {e}")


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

    return jsonify({
        "success": True,
        "provider": AI_PROVIDER,
        "model": AI_MODEL
    })


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
        
        # Generate device ID if not provided
        if not device_id:
            import hashlib
            import uuid
            # Create stable device ID from browser fingerprint
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
        
        if not device_id or len(device_id) < 4:
            return jsonify({"success": False, "error": "Invalid device_id"}), 400
        
        if device_type not in ("phone", "tablet", "desktop"):
            device_type = "desktop"
        
        devices = load_device_config()
        
        # If device doesn't exist yet, add it with default enabled state based on mode
        if device_id not in devices:
            # Device always enabled by default (management from UI)
            devices[device_id] = {
                "name": device_name or f"{device_type.capitalize()}",
                "device_type": device_type,
                "enabled": True,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
            }
        else:
            # Update last_seen and name if provided
            devices[device_id]["last_seen"] = datetime.now().isoformat()
            if device_name:
                devices[device_id]["name"] = device_name
        
        save_device_config(devices)
        logger.info(f"Device registered: {device_id} ({device_type})")
        
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
    logger.info(f"Chat [{AI_PROVIDER}]: {message}")
    response_text = chat_with_ai(message, session_id)
    return jsonify({"response": response_text}), 200


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
    if not message:
        return jsonify({"error": "Empty message"}), 400
    if image_data:
        logger.info(f"Stream [{AI_PROVIDER}] with image: {message[:50]}...")
    else:
        log_msg = message if len(message) <= 500 else message[:250] + f"... [{len(message)} chars] ..." + message[-100:]
        logger.info(f"Stream [{AI_PROVIDER}]: {log_msg}")
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
                for event in stream_chat_with_ai(message, session_id, image_data, read_only=read_only):
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


@app.route('/api/memory/clear', methods=['POST'])
def api_memory_clear():
    """Clear file memory cache (Layer 2)."""
    try:
        file_cache = memory.get_config_file_cache()
        old_stats = file_cache.stats()
        file_cache.clear()
        logger.info(f"Memory cache cleared: was {old_stats['cached_files']} files, {old_stats['total_bytes']} bytes")
        return jsonify({
            "status": "success",
            "message": f"Cleared {old_stats['cached_files']} files",
            "freed_bytes": old_stats['total_bytes'],
        }), 200
    except Exception as e:
        logger.error(f"Memory clear error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============ MCP (Model Context Protocol) Endpoints ============

@app.route('/api/mcp/servers', methods=['GET'])
def api_mcp_servers_list():
    """List all configured MCP servers and their connection status."""
    try:
        if not MCP_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "MCP support not available"
            }), 501
        
        manager = mcp.get_mcp_manager()
        servers = []
        for name, server in manager.servers.items():
            tools_count = len(server.tools) if server.is_connected() else 0
            servers.append({
                "name": name,
                "connected": server.is_connected(),
                "transport": server.transport_type,
                "tools_count": tools_count,
                "tools": list(server.tools.keys()) if server.is_connected() else [],
            })
        
        return jsonify({
            "status": "success",
            "servers": servers,
            "total_servers": len(servers),
        }), 200
    except Exception as e:
        logger.error(f"MCP list servers error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mcp/server/<server_name>/status', methods=['GET'])
def api_mcp_server_status(server_name):
    """Get status of a specific MCP server."""
    try:
        if not MCP_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "MCP support not available"
            }), 501
        
        manager = mcp.get_mcp_manager()
        if server_name not in manager.servers:
            return jsonify({
                "status": "error",
                "message": f"Server '{server_name}' not found"
            }), 404
        
        server = manager.servers[server_name]
        return jsonify({
            "status": "success",
            "server_name": server_name,
            "connected": server.is_connected(),
            "transport": server.transport_type,
            "tools": {name: {"description": tool.get("description", "")} 
                     for name, tool in server.tools.items()},
            "tools_count": len(server.tools),
        }), 200
    except Exception as e:
        logger.error(f"MCP server status error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mcp/server/<server_name>/reconnect', methods=['POST'])
def api_mcp_server_reconnect(server_name):
    """Reconnect to a specific MCP server."""
    try:
        if not MCP_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "MCP support not available"
            }), 501
        
        manager = mcp.get_mcp_manager()
        if server_name not in manager.servers:
            return jsonify({
                "status": "error",
                "message": f"Server '{server_name}' not found"
            }), 404
        
        server = manager.servers[server_name]
        server.disconnect()
        server.connect()
        
        return jsonify({
            "status": "success",
            "message": f"Reconnected to '{server_name}'",
            "connected": server.is_connected(),
            "tools_count": len(server.tools),
        }), 200
    except Exception as e:
        logger.error(f"MCP server reconnect error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mcp/tools', methods=['GET'])
def api_mcp_all_tools():
    """List all available tools from all connected MCP servers."""
    try:
        if not MCP_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "MCP support not available"
            }), 501
        
        manager = mcp.get_mcp_manager()
        all_tools = manager.get_all_tools()
        
        tools_by_server = {}
        for tool_name, tool_info in all_tools.items():
            server_name = tool_info.get("server", "unknown")
            if server_name not in tools_by_server:
                tools_by_server[server_name] = []
            tools_by_server[server_name].append({
                "name": tool_name,
                "tool_name": tool_info.get("tool_name", ""),
                "description": tool_info.get("description", ""),
            })
        
        return jsonify({
            "status": "success",
            "tools": all_tools,
            "tools_by_server": tools_by_server,
            "total_tools": len(all_tools),
        }), 200
    except Exception as e:
        logger.error(f"MCP all tools error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mcp/diagnostics', methods=['GET'])
def api_mcp_diagnostics():
    """Get detailed diagnostics for all MCP servers."""
    try:
        if not MCP_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "MCP support not available"
            }), 501
        
        manager = mcp.get_mcp_manager()
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "servers": {},
            "stats": manager.stats() if hasattr(manager, 'stats') else {},
        }
        
        for name, server in manager.servers.items():
            server_diag = {
                "name": name,
                "connected": server.is_connected(),
                "transport": server.transport_type,
                "tools_count": len(server.tools),
                "tools": list(server.tools.keys()),
                "config": {
                    "transport": server.transport_type,
                    "command": server.config.get("command", "") if server.transport_type == "stdio" else "",
                    "url": server.config.get("url", "") if server.transport_type == "http" else "",
                }
            }
            diagnostics["servers"][name] = server_diag
        
        return jsonify(diagnostics), 200
    except Exception as e:
        logger.error(f"MCP diagnostics error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mcp/test/<server_name>/<tool_name>', methods=['POST'])
def api_mcp_test_tool(server_name, tool_name):
    """Test a specific MCP tool with provided arguments."""
    try:
        if not MCP_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "MCP support not available"
            }), 501
        
        data = request.get_json() or {}
        arguments = data.get("arguments", {})
        
        manager = mcp.get_mcp_manager()
        if server_name not in manager.servers:
            return jsonify({
                "status": "error",
                "message": f"Server '{server_name}' not found"
            }), 404
        
        server = manager.servers[server_name]
        if not server.is_connected():
            return jsonify({
                "status": "error",
                "message": f"Server '{server_name}' is not connected"
            }), 503
        
        # Execute tool and measure time
        start_time = time.time()
        try:
            result = server.call_tool(tool_name, arguments)
            elapsed = time.time() - start_time
            
            # Parse result if it's JSON
            try:
                result_obj = json.loads(result) if isinstance(result, str) else result
            except (json.JSONDecodeError, TypeError):
                result_obj = {"result": result}
            
            return jsonify({
                "status": "success",
                "server": server_name,
                "tool": tool_name,
                "arguments": arguments,
                "result": result_obj,
                "execution_time_ms": round(elapsed * 1000, 2),
            }), 200
        except Exception as e:
            elapsed = time.time() - start_time
            return jsonify({
                "status": "error",
                "server": server_name,
                "tool": tool_name,
                "error": str(e),
                "execution_time_ms": round(elapsed * 1000, 2),
            }), 500
    except Exception as e:
        logger.error(f"MCP test tool error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mcp/server/<server_name>/tools', methods=['GET'])
def api_mcp_server_tools(server_name):
    """Get tools for a specific MCP server."""
    try:
        if not MCP_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "MCP support not available"
            }), 501
        
        manager = mcp.get_mcp_manager()
        if server_name not in manager.servers:
            return jsonify({
                "status": "error",
                "message": f"Server '{server_name}' not found"
            }), 404
        
        server = manager.servers[server_name]
        tools_list = []
        
        for tool_name, tool_info in server.tools.items():
            tools_list.append({
                "name": tool_name,
                "description": tool_info.get("description", ""),
                "inputSchema": tool_info.get("inputSchema", {}),
            })
        
        return jsonify({
            "status": "success",
            "server": server_name,
            "connected": server.is_connected(),
            "tools": tools_list,
            "total_tools": len(tools_list),
        }), 200
    except Exception as e:
        logger.error(f"MCP server tools error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============ Nanobot-Inspired Features Endpoints ============

@app.route('/api/fallback/stats', methods=['GET'])
def api_fallback_stats():
    """Get multi-provider fallback chain statistics."""
    try:
        if not FALLBACK_AVAILABLE:
            return jsonify({"status": "error", "message": "Fallback not available"}), 501
        
        chain = fallback.get_fallback_chain()
        if not chain:
            return jsonify({"status": "error", "message": "Fallback chain not initialized"}), 503
        
        stats = chain.get_stats()
        return jsonify({
            "status": "success",
            "fallback_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Fallback stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/cache/semantic/stats', methods=['GET'])
def api_semantic_cache_stats():
    """Get semantic cache statistics."""
    try:
        if not SEMANTIC_CACHE_AVAILABLE:
            return jsonify({"status": "error", "message": "Semantic cache not available"}), 501
        
        cache = semantic_cache.get_semantic_cache()
        if not cache:
            return jsonify({"status": "error", "message": "Semantic cache not initialized"}), 503
        
        stats = cache.stats()
        return jsonify({
            "status": "success",
            "cache_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Semantic cache stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/cache/semantic/clear', methods=['POST'])
def api_semantic_cache_clear():
    """Clear semantic cache."""
    try:
        if not SEMANTIC_CACHE_AVAILABLE:
            return jsonify({"status": "error", "message": "Semantic cache not available"}), 501
        
        cache = semantic_cache.get_semantic_cache()
        if not cache:
            return jsonify({"status": "error", "message": "Semantic cache not initialized"}), 503
        
        cache.clear()
        return jsonify({
            "status": "success",
            "message": "Semantic cache cleared",
        }), 200
    except Exception as e:
        logger.error(f"Semantic cache clear error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/tools/optimizer/stats', methods=['GET'])
def api_tool_optimizer_stats():
    """Get tool execution optimizer statistics."""
    try:
        if not TOOL_OPTIMIZER_AVAILABLE:
            return jsonify({"status": "error", "message": "Tool optimizer not available"}), 501
        
        optimizer = tool_optimizer.get_tool_optimizer()
        stats = optimizer.stats()
        return jsonify({
            "status": "success",
            "optimizer_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Tool optimizer stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/quality/stats', methods=['GET'])
def api_quality_metrics_stats():
    """Get response quality metrics statistics."""
    try:
        if not QUALITY_METRICS_AVAILABLE:
            return jsonify({"status": "error", "message": "Quality metrics not available"}), 501
        
        analyzer = quality_metrics.get_quality_analyzer()
        stats = analyzer.get_stats()
        return jsonify({
            "status": "success",
            "quality_stats": stats,
        }), 200
    except Exception as e:
        logger.error(f"Quality metrics stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============ Image Support Endpoints ============

@app.route('/api/image/stats', methods=['GET'])
def api_image_stats():
    """Get image analyzer statistics."""
    try:
        if not IMAGE_SUPPORT_AVAILABLE:
            return jsonify({"status": "error", "message": "Image support not available"}), 501
        analyzer = image_support.get_image_analyzer()
        return jsonify({"status": "success", "image_stats": analyzer.get_stats()}), 200
    except Exception as e:
        logger.error(f"Image stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/image/analyze', methods=['POST'])
def api_image_analyze():
    """Analyze an image file using vision models with automatic fallback.
    
    JSON body: { "image_path": "/config/amira/images/photo.jpg", "prompt": "Describe this image" }
    """
    try:
        if not IMAGE_SUPPORT_AVAILABLE:
            return jsonify({"status": "error", "message": "Image support not available"}), 501
        data = request.json or {}
        image_path = data.get("image_path", "")
        prompt = data.get("prompt", "Describe this image in detail.")
        if not image_path:
            return jsonify({"status": "error", "message": "image_path is required"}), 400
        analyzer = image_support.get_image_analyzer()
        success, analysis, provider = analyzer.analyze_with_fallback(image_path, prompt)
        if success:
            return jsonify({"status": "success", "analysis": analysis, "provider": provider}), 200
        else:
            return jsonify({"status": "error", "message": analysis}), 502
    except Exception as e:
        logger.error(f"Image analyze error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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


# ============ Agent Discovery ============

@app.route('/api/agents', methods=['GET'])
def api_agents_list():
    """List all available agents with their capabilities and endpoint info."""
    agents = [
        {
            "id": "main",
            "name": "Home Assistant AI",
            "description": "Main AI agent: home automation, devices, automations, scripts, dashboards.",
            "endpoint": "/api/chat",
            "method": "POST",
            "available": True,
            "builtin": True,
            "icon": "🏠",
        },
    ]
    if SCHEDULER_AGENT_AVAILABLE:
        agents.append({
            "id": "scheduler",
            "name": "SchedulerAgent",
            "description": "Create, list, enable/disable and delete scheduled tasks using natural language.",
            "endpoint": "/api/agent/scheduler",
            "method": "POST",
            "available": True,
            "builtin": False,
            "icon": "🗓️",
            "extra_endpoints": {
                "sessions": "GET /api/agent/scheduler/sessions",
                "clear_session": "DELETE /api/agent/scheduler/session/<session_id>",
            },
        })
    return jsonify({
        "status": "success",
        "agents": agents,
        "count": len(agents),
    }), 200


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


# ============ Voice Transcription Endpoints ============

@app.route('/api/voice/stats', methods=['GET'])
def api_voice_stats():
    """Get voice transcription statistics."""
    try:
        if not VOICE_TRANSCRIPTION_AVAILABLE:
            return jsonify({"status": "error", "message": "Voice transcription not available"}), 501
        transcriber = voice_transcription.get_voice_transcriber()
        return jsonify({"status": "success", "voice_stats": transcriber.get_stats()}), 200
    except Exception as e:
        logger.error(f"Voice stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/voice/transcribe', methods=['POST'])
def api_voice_transcribe():
    """Transcribe uploaded audio file to text (Groq Whisper → OpenAI → Google fallback).
    
    Multipart: audio file in field 'file'
    """
    try:
        if not VOICE_TRANSCRIPTION_AVAILABLE:
            return jsonify({"status": "error", "message": "Voice transcription not available"}), 501
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No audio file in request (field: 'file')"}), 400
        audio_file = request.files['file']
        # Save to a temporary path
        import tempfile, os as _os
        suffix = _os.path.splitext(audio_file.filename or 'audio.wav')[1] or '.wav'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name
        try:
            transcriber = voice_transcription.get_voice_transcriber()
            success, text, provider = transcriber.transcribe_with_fallback(tmp_path)
        finally:
            _os.unlink(tmp_path)
        if success:
            return jsonify({"status": "success", "text": text, "provider": provider}), 200
        else:
            return jsonify({"status": "error", "message": text}), 502
    except Exception as e:
        logger.error(f"Voice transcribe error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/voice/tts', methods=['POST'])
def api_voice_tts():
    """Convert text to speech (OpenAI → Google fallback).
    
    JSON body: { "text": "..." }
    Returns: audio/mpeg binary or JSON error
    """
    try:
        if not VOICE_TRANSCRIPTION_AVAILABLE:
            return jsonify({"status": "error", "message": "Voice transcription not available"}), 501
        data = request.json or {}
        text = data.get("text", "")
        if not text:
            return jsonify({"status": "error", "message": "text is required"}), 400
        tts = voice_transcription.get_text_to_speech()
        success, audio_bytes = tts.speak_with_fallback(text)
        if success and audio_bytes:
            from flask import Response as FlaskResponse
            return FlaskResponse(audio_bytes, mimetype="audio/mpeg")
        else:
            return jsonify({"status": "error", "message": "TTS failed — no provider available"}), 502
    except Exception as e:
        logger.error(f"Voice TTS error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        chat_id = data.get("chat_id")
        text = data.get("text", "").strip()
        logger.info(f"Telegram API: message from user {user_id}: {text[:60]}")

        if not text:
            return jsonify({"status": "error", "message": "Empty message"}), 400

        # Get AI response — session history is already managed by chat_with_ai
        response_text = ""
        try:
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
        
        logger.debug(f"WhatsApp message from {from_number}: {text[:50]}...")

        # Check if first message BEFORE adding to history
        mgr = get_messaging_manager()
        is_first = len(mgr.get_chat_history("whatsapp", from_number, limit=1)) == 0

        # Add to chat history
        mgr.add_message("whatsapp", from_number, text, role="user")
        
        # Get AI response — chat_with_ai reuses the persistent whatsapp_{number}
        # session which already accumulates history; no need to inject "Recent context:"
        response_text = ""
        try:
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


@app.route('/api/system/features', methods=['GET'])
def api_system_features():
    """Get list of available advanced features."""
    features = {
        "mcp_support": MCP_AVAILABLE,
        "fallback_chain": FALLBACK_AVAILABLE,
        "semantic_cache": SEMANTIC_CACHE_AVAILABLE,
        "tool_optimizer": TOOL_OPTIMIZER_AVAILABLE,
        "quality_metrics": QUALITY_METRICS_AVAILABLE,
        "prompt_caching": ANTHROPIC_PROMPT_CACHING if ANTHROPIC_PROMPT_CACHING else False,
        "file_memory": MEMORY_AVAILABLE if MEMORY_AVAILABLE else False,
        "image_support": IMAGE_SUPPORT_AVAILABLE,
        "scheduled_tasks": SCHEDULED_TASKS_AVAILABLE,
        "voice_transcription": VOICE_TRANSCRIPTION_AVAILABLE,
        "scheduler_agent": SCHEDULER_AGENT_AVAILABLE,
    }
    
    return jsonify({
        "status": "success",
        "features": features,
        "enabled_count": sum(1 for v in features.values() if v),
    }), 200


@app.route('/api/mcp/conversations/<session_id>/messages', methods=['GET'])
def api_conversation_messages(session_id):
    """Get all messages for a conversation session."""
    msgs = conversations.get(session_id, [])
    # Return only user/assistant text messages for UI display (filter empty content)
    display_msgs = []
    for m in msgs:
        content = m.get("content", "")
        # Skip messages with empty content or only whitespace
        if m.get("role") in ("user", "assistant") and isinstance(content, str) and content.strip():
            msg_data = {"role": m["role"], "content": content}
            # Include model/provider/usage info for assistant messages
            if m.get("role") == "assistant":
                if "model" in m:
                    msg_data["model"] = m["model"]
                if "provider" in m:
                    msg_data["provider"] = m["provider"]
                if "usage" in m:
                    msg_data["usage"] = m["usage"]
            display_msgs.append(msg_data)
    return jsonify({"session_id": session_id, "messages": display_msgs}), 200


@app.route('/api/conversations', methods=['GET'])
def api_conversations_list():
    """List all conversation sessions with metadata."""
    result = []
    for sid, msgs in conversations.items():
        if not msgs:
            continue
        # Exclude messaging sessions — they have their own dedicated UI section
        if sid.startswith(("whatsapp_", "telegram_")):
            continue
        # Extract first user message as title
        title = "Nuova conversazione"
        for msg in msgs:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    title = content[:50] + ("..." if len(content) > 50 else "")
                    break
        # Determine source: bubble sessions start with "bubble_"
        source = "bubble" if sid.startswith("bubble_") else "chat"
        
        # Extract timestamp for sorting/date grouping
        if source == "bubble" and sid.startswith("bubble_"):
            # Parse bubble session_id: bubble_<base36_timestamp>_<random>
            try:
                parts = sid.split("_")
                if len(parts) >= 2:
                    timestamp_b36 = parts[1]
                    last_updated = int(timestamp_b36, 36)  # Decode base36 timestamp
                else:
                    last_updated = sid
            except:
                last_updated = sid
        else:
            # For chat: ID is typically a numeric timestamp
            try:
                last_updated = int(sid) if sid.isdigit() else sid
            except:
                last_updated = sid if msgs else 0
        
        result.append({
            "id": sid,
            "title": title,
            "message_count": len(msgs),
            "last_updated": last_updated,
            "source": source
        })
    # Sort by last_updated descending
    result.sort(key=lambda x: (x["last_updated"] if isinstance(x["last_updated"], (int, float)) else 0), reverse=True)
    return jsonify({"conversations": result[:MAX_CONVERSATIONS]}), 200


@app.route('/api/snapshots', methods=['GET'])
def api_snapshots_list():
    """List all file snapshots (backups) created by Amira."""
    if not os.path.isdir(SNAPSHOTS_DIR):
        return jsonify({"snapshots": []}), 200
    
    snapshots = []
    for filename in os.listdir(SNAPSHOTS_DIR):
        if filename.endswith(".meta"):
            continue
        meta_path = os.path.join(SNAPSHOTS_DIR, filename + ".meta")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                # Parse timestamp from snapshot_id: YYYYMMDD_HHMMSS_filename
                ts_str = meta.get("timestamp", "")
                try:
                    ts_dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    formatted_date = ts_dt.strftime("%d/%m/%Y %H:%M:%S")
                    sort_key = ts_dt.timestamp()
                except:
                    formatted_date = ts_str
                    sort_key = 0
                snapshots.append({
                    "id": meta.get("snapshot_id", filename),
                    "original_file": meta.get("original_file", filename),
                    "timestamp": ts_str,
                    "formatted_date": formatted_date,
                    "size": meta.get("size", 0),
                    "sort_key": sort_key
                })
            except Exception as e:
                logger.debug(f"Error reading snapshot meta {filename}: {e}")
    
    # Sort by timestamp descending (newest first)
    snapshots.sort(key=lambda x: x.get("sort_key", 0), reverse=True)
    # Remove sort_key from output
    for s in snapshots:
        s.pop("sort_key", None)
    
    return jsonify({"snapshots": snapshots}), 200


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


@app.route('/api/conversations/<session_id>', methods=['GET'])
def api_conversation_get(session_id):
    """Get a specific conversation session."""
    if session_id in conversations:
        # Filter to only return displayable messages (user/assistant with non-empty string content)
        msgs = conversations.get(session_id, [])
        display_msgs = []
        for m in msgs:
            role = m.get("role", "")
            content = m.get("content", "")
            # For multimodal messages, extract text content
            if isinstance(content, list):
                # Extract text from content blocks (Anthropic format: [{type:text, text:...}])
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block.get("text"), str):
                            text_parts.append(block["text"])
                        # Skip tool_use / tool_result blocks — not user-facing
                content = "\n".join(text_parts) if text_parts else ""

            if role in ("user", "assistant") and isinstance(content, str) and content.strip():
                # Skip internal tool-call artifact messages
                if role == "assistant" and _is_tool_call_artifact(content, m):
                    continue
                msg_data = {"role": role, "content": content}
                # Include model/provider metadata for assistant messages
                if role == "assistant":
                    if m.get("model"):
                        msg_data["model"] = m["model"]
                    if m.get("provider"):
                        msg_data["provider"] = m["provider"]
                display_msgs.append(msg_data)
        return jsonify({"session_id": session_id, "messages": display_msgs}), 200
    return jsonify({"error": "Conversation not found"}), 404


@app.route('/api/conversations/<session_id>', methods=['DELETE'])
def api_conversation_delete(session_id):
    """Clear a conversation session."""
    if session_id in conversations:
        del conversations[session_id]
        save_conversations()
    session_last_intent.pop(session_id, None)
    return jsonify({"status": "ok", "message": f"Session '{session_id}' cleared."}), 200

@app.route('/api/get_models', methods=['GET'])
def api_get_models():
    """Get available models (chat + HA settings) without duplicate routes."""
    try:
        # --- Providers disponibili (per HA settings) ---
        available_providers = []
        if ANTHROPIC_API_KEY:
            available_providers.append({"id": "anthropic", "name": "Anthropic Claude"})
        if OPENAI_API_KEY:
            available_providers.append({"id": "openai", "name": "OpenAI"})
        if GOOGLE_API_KEY:
            available_providers.append({"id": "google", "name": "Google Gemini"})
        if NVIDIA_API_KEY:
            available_providers.append({"id": "nvidia", "name": "NVIDIA NIM"})
        if GITHUB_TOKEN:
            available_providers.append({"id": "github", "name": "GitHub Models"})
        if GROQ_API_KEY:
            available_providers.append({"id": "groq", "name": "Groq"})
        if MISTRAL_API_KEY:
            available_providers.append({"id": "mistral", "name": "Mistral"})
        if OPENROUTER_API_KEY:
            available_providers.append({"id": "openrouter", "name": "OpenRouter"})
        if DEEPSEEK_API_KEY:
            available_providers.append({"id": "deepseek", "name": "DeepSeek"})
        if MINIMAX_API_KEY:
            available_providers.append({"id": "minimax", "name": "MiniMax"})
        if AIHUBMIX_API_KEY:
            available_providers.append({"id": "aihubmix", "name": "AiHubMix"})
        if SILICONFLOW_API_KEY:
            available_providers.append({"id": "siliconflow", "name": "SiliconFlow"})
        if VOLCENGINE_API_KEY:
            available_providers.append({"id": "volcengine", "name": "VolcEngine"})
        if DASHSCOPE_API_KEY:
            available_providers.append({"id": "dashscope", "name": "DashScope (Qwen)"})
        if MOONSHOT_API_KEY:
            available_providers.append({"id": "moonshot", "name": "Moonshot (Kimi)"})
        if ZHIPU_API_KEY:
            available_providers.append({"id": "zhipu", "name": "Zhipu (GLM)"})
        if PERPLEXITY_API_KEY:
            available_providers.append({"id": "perplexity", "name": "Perplexity (Sonar)"})
        if CUSTOM_API_BASE:
            available_providers.append({"id": "custom", "name": "Custom Endpoint"})
        # Ollama: sempre disponibile se ha un URL configurato (è locale)
        if OLLAMA_BASE_URL:
            available_providers.append({"id": "ollama", "name": "Ollama (Local)"})
        # GitHub Copilot: sempre visibile nel selettore; il banner OAuth guida l'autenticazione
        available_providers.append({"id": "github_copilot", "name": "GitHub Copilot"})
        # OpenAI Codex: sempre visibile nel selettore; il banner OAuth guida l'autenticazione
        available_providers.append({"id": "openai_codex", "name": "OpenAI Codex"})
        # Provider web non ufficiali — sempre visibili; il token di sessione guida l'autenticazione
        available_providers.append({"id": "claude_web", "name": "Claude.ai Web [UNSTABLE]"})
        # chatgpt_web: in standby — Cloudflare blocca le richieste da server nel 2026
        # available_providers.append({"id": "chatgpt_web", "name": "ChatGPT Web [UNSTABLE]"})

        # --- Tutti i modelli per provider (come li vuole la chat: display/prefissi) ---
        models_display = {}
        models_technical = {}
        nvidia_models_tested_display: list[str] = []
        nvidia_models_to_test_display: list[str] = []
        
        # Get list of configured providers (only those with API keys)
        configured_providers = {p["id"] for p in available_providers}
        
        for provider, models in PROVIDER_MODELS.items():
            # ONLY include models for providers that have API keys configured
            if provider not in configured_providers:
                continue

            filtered_models = list(models)

            # Live discovery for GitHub Copilot (models depend on subscription)
            # Live discovery for GitHub Copilot: use cache only on regular loads.
            # The full network discovery (token + /models) runs exclusively via
            # the manual "Refresh models" button (api/refresh_models endpoint).
            # This avoids automatic HTTP calls on every UI startup/reload.
            if provider == "github_copilot":
                try:
                    from providers.github_copilot import get_copilot_models_cached
                    live = get_copilot_models_cached()
                    if live:
                        filtered_models = live
                except Exception as _e:
                    logger.debug(f"Copilot model discovery skipped: {_e}")

            # Live discovery for NVIDIA (per-key availability)
            if provider == "nvidia":
                live_models = get_nvidia_models_cached()
                if live_models:
                    filtered_models = list(live_models)
                if NVIDIA_MODEL_BLOCKLIST:
                    filtered_models = [m for m in filtered_models if m not in NVIDIA_MODEL_BLOCKLIST]

                # Partition into tested vs not-yet-tested (keep only currently available models)
                tested_ok = [m for m in filtered_models if m in NVIDIA_MODEL_TESTED_OK]
                to_test = [m for m in filtered_models if m not in NVIDIA_MODEL_TESTED_OK]
                filtered_models = tested_ok + to_test

            if provider == "github" and GITHUB_MODEL_BLOCKLIST:
                filtered_models = [m for m in filtered_models if m not in GITHUB_MODEL_BLOCKLIST]
            models_technical[provider] = list(filtered_models)
            # Use per-provider display mapping to avoid cross-provider conflicts
            prov_map = PROVIDER_DISPLAY.get(provider, {})
            models_display[provider] = [prov_map.get(m, m) for m in filtered_models]

            if provider == "nvidia":
                # Provide explicit groups for UI (display names)
                nvidia_models_tested_display = [prov_map.get(m, m) for m in filtered_models if m in NVIDIA_MODEL_TESTED_OK]
                nvidia_models_to_test_display = [prov_map.get(m, m) for m in filtered_models if m not in NVIDIA_MODEL_TESTED_OK]

        # --- Current model (sia tech che display) ---
        current_model_tech = get_active_model()
        # Use provider-specific display to avoid cross-provider collisions
        # (e.g. "openai/gpt-4o" exists in both GitHub and OpenRouter with different display names)
        current_model_display = (
            PROVIDER_DISPLAY.get(AI_PROVIDER, {}).get(current_model_tech)
            or MODEL_DISPLAY_MAPPING.get(current_model_tech)
            or current_model_tech
        )

        # --- Modelli del provider corrente (per HA settings: lista con flag current) ---
        provider_models = models_technical.get(AI_PROVIDER, PROVIDER_MODELS.get(AI_PROVIDER, []))
        available_models = []
        for tech_name in provider_models:
            available_models.append({
                "technical_name": tech_name,
                "display_name": MODEL_DISPLAY_MAPPING.get(tech_name, tech_name),
                "is_current": tech_name == current_model_tech
            })

        return jsonify({
            "success": True,

            # First-run onboarding: chat should prompt user to pick an agent once
            "needs_first_selection": not os.path.isfile(RUNTIME_SELECTION_FILE),

            # compat chat (quello che già usa il tuo JS)
            "current_provider": AI_PROVIDER,
            "current_model": current_model_display,
            "models": models_display,

            # NVIDIA UI grouping: tested models first, then not-yet-tested
            "nvidia_models_tested": nvidia_models_tested_display,
            "nvidia_models_to_test": nvidia_models_to_test_display,

            # extra per HA (più completo)
            "current_model_technical": current_model_tech,
            "models_technical": models_technical,
            "available_providers": available_providers,
            "available_models": available_models
        }), 200
    except Exception as e:
        logger.error(f"api_get_models error: {e}")
        return jsonify({"success": False, "error": str(e), "models": {}, "available_providers": []}), 500


@app.route('/api/refresh_models', methods=['POST'])
def api_refresh_models():
    """Fetch latest model lists from official provider APIs and update the cache.

    Calls the /v1/models (or equivalent) endpoint for each configured provider,
    filters out non-chat models, saves results to /data/amira_models_cache.json,
    and updates the in-memory PROVIDER_MODELS dict so /api/get_models returns
    the fresh lists immediately.
    """
    try:
        from providers.model_fetcher import refresh_all_providers

        provider_keys = {
            "openai":      OPENAI_API_KEY,
            "anthropic":   ANTHROPIC_API_KEY,
            "google":      GOOGLE_API_KEY,
            "groq":        GROQ_API_KEY,
            "mistral":     MISTRAL_API_KEY,
            "nvidia":      NVIDIA_API_KEY,
            "deepseek":    DEEPSEEK_API_KEY,
            "openrouter":  OPENROUTER_API_KEY,
            "zhipu":       ZHIPU_API_KEY,
            "siliconflow": SILICONFLOW_API_KEY,
            "moonshot":    MOONSHOT_API_KEY,
            "dashscope":   DASHSCOPE_API_KEY,
            "minimax":     MINIMAX_API_KEY,
            "aihubmix":    AIHUBMIX_API_KEY,
            "volcengine":  VOLCENGINE_API_KEY,
            "custom":      CUSTOM_API_KEY,
            "ollama":      "",  # key-less, uses base URL
        }
        extra = {
            "ollama_base_url": OLLAMA_BASE_URL,
            "custom_api_base": CUSTOM_API_BASE,
        }

        results = refresh_all_providers(provider_keys, extra)

        # Update in-memory model lists so the UI reflects the fresh data immediately
        for provider, models in results["updated"].items():
            PROVIDER_MODELS[provider] = models

        # GitHub Copilot: full live discovery (token + /models) runs ONLY here,
        # triggered by the manual refresh button — never on automatic get_models calls.
        if os.path.exists("/data/oauth_copilot.json"):
            try:
                from providers.github_copilot import (
                    _fetch_models_from_api,
                    _get_copilot_session_token,
                    _get_best_gh_token,
                )
                gh_tok = _get_best_gh_token(GITHUB_COPILOT_TOKEN)
                if gh_tok:
                    session_tok = _get_copilot_session_token(gh_tok)
                    copilot_models = _fetch_models_from_api(session_tok)
                    if copilot_models:
                        PROVIDER_MODELS["github_copilot"] = copilot_models
                        results["updated"]["github_copilot"] = copilot_models
                        logger.info(f"refresh_models: github_copilot discovered {len(copilot_models)} models")
            except Exception as _ce:
                logger.debug(f"refresh_models: github_copilot discovery failed: {_ce}")
                results["errors"]["github_copilot"] = str(_ce)

        logger.info(
            f"refresh_models: updated={list(results['updated'].keys())} "
            f"errors={list(results['errors'].keys())} "
            f"skipped={results['skipped']}"
        )
        return jsonify({
            "success": True,
            "updated": {p: len(m) for p, m in results["updated"].items()},
            "errors":  results["errors"],
            "skipped": results["skipped"],
        }), 200

    except Exception as e:
        logger.error(f"refresh_models error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/snapshots/restore', methods=['POST'])
def api_snapshots_restore():
    """Restore a snapshot created by the add-on (undo).

    The frontend uses this to provide a one-click "Ripristina backup" under write-tool messages.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        snapshot_id = (data.get("snapshot_id") or "").strip()
        if not snapshot_id:
            return jsonify({"error": "snapshot_id is required"}), 400

        raw = tools.execute_tool("restore_snapshot", {"snapshot_id": snapshot_id, "reload": True})
        try:
            result = json.loads(raw) if isinstance(raw, str) else {"status": "success", "result": raw}
        except Exception:
            result = {"error": raw}

        if isinstance(result, dict) and result.get("status") == "success":
            return jsonify(result), 200
        return jsonify(result if isinstance(result, dict) else {"error": str(result)}), 400
    except Exception as e:
        logger.error(f"Snapshot restore error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/snapshots/<snapshot_id>', methods=['DELETE'])
def api_delete_snapshot(snapshot_id):
    """Delete a specific snapshot (backup file + metadata)."""
    try:
        if not snapshot_id or ".." in snapshot_id or "/" in snapshot_id:
            return jsonify({"error": "Invalid snapshot_id"}), 400

        snap_path = os.path.join(SNAPSHOTS_DIR, snapshot_id)
        meta_path = snap_path + ".meta"
        deleted = False
        if os.path.isfile(snap_path):
            os.remove(snap_path)
            deleted = True
        if os.path.isfile(meta_path):
            os.remove(meta_path)
            deleted = True

        if deleted:
            logger.info(f"Snapshot deleted: {snapshot_id}")
            return jsonify({"status": "success", "message": f"Snapshot '{snapshot_id}' deleted"}), 200
        return jsonify({"error": f"Snapshot '{snapshot_id}' not found"}), 404
    except Exception as e:
        logger.error(f"Snapshot delete error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/snapshots/<snapshot_id>/download', methods=['GET'])
def api_download_snapshot(snapshot_id):
    """Download a backup snapshot file."""
    try:
        if not snapshot_id or ".." in snapshot_id or "/" in snapshot_id:
            return jsonify({"error": "Invalid snapshot_id"}), 400

        snap_path = os.path.join(SNAPSHOTS_DIR, snapshot_id)
        meta_path = snap_path + ".meta"
        
        if not os.path.isfile(snap_path):
            return jsonify({"error": f"Snapshot '{snapshot_id}' not found"}), 404

        # Read metadata to get original filename
        original_filename = snapshot_id  # default fallback
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    original_filename = meta.get("original_file", snapshot_id)
                    timestamp = meta.get("timestamp", "")
            except Exception:
                pass

        # Generate download filename: original_name.YYYYMMDD_HHMMSS.bak
        # E.g.: automations.yaml.20260220_143022.bak
        base_name = os.path.basename(original_filename)
        if "." in base_name:
            name_parts = base_name.rsplit(".", 1)
            dl_filename = f"{name_parts[0]}.{timestamp}.bak"
        else:
            dl_filename = f"{base_name}.{timestamp}.bak"

        logger.info(f"Snapshot download: {snapshot_id} as {dl_filename}")
        return send_file(
            snap_path,
            as_attachment=True,
            download_name=dl_filename,
            mimetype="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Snapshot download error: {e}")
        return jsonify({"error": str(e)}), 500


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
    try:
        max_models = int(body.get("max_models") or 0)
    except Exception:
        max_models = 0

    try:
        cursor = int(body.get("cursor") or 0)
    except Exception:
        cursor = 0

    # Safety defaults: keep the request reasonably fast.
    if max_models <= 0:
        max_models = 20
    max_models = max(1, min(50, max_models))

    max_seconds = 25.0
    per_model_timeout = 10

    # Use a fresh live list when possible.
    all_models = _fetch_nvidia_models_live() or get_nvidia_models_cached() or PROVIDER_MODELS.get("nvidia", [])
    all_models = [m for m in (all_models or []) if isinstance(m, str) and m.strip()]
    # Remove already known-bad models.
    candidates = [m for m in all_models if m not in NVIDIA_MODEL_BLOCKLIST]

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
    stopped_reason = None
    timeouts = 0
    errors = 0

    idx = cursor

    while idx < len(candidates):
        model_id = candidates[idx]
        if len(tested) >= max_models:
            stopped_reason = f"limit modelli ({max_models})"
            break
        if (time.time() - started) > max_seconds:
            stopped_reason = f"timeout ({int(max_seconds)}s)"
            break

        tested.append(model_id)
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
            timeouts += 1
            tested.append(model_id)
            idx += 1
            continue
        except Exception as e:
            errors += 1
            tested.append(model_id)
            idx += 1
            # If we see repeated unknown network errors, stop to avoid looping forever.
            if errors >= 3:
                stopped_reason = f"errore rete: {type(e).__name__}"
                break
            continue

        if resp.status_code == 200:
            ok.append(model_id)
            mark_nvidia_model_tested_ok(model_id)
            idx += 1
            continue

        if resp.status_code in (404, 400, 422):
            blocklist_nvidia_model(model_id)
            removed.append(model_id)
            idx += 1
            continue

        if resp.status_code == 429:
            stopped_reason = "rate limit (429)"
            break

        if resp.status_code in (401, 403):
            stopped_reason = f"auth/permessi (HTTP {resp.status_code})"
            break

        stopped_reason = f"HTTP {resp.status_code}"
        break

    next_cursor = idx
    remaining = max(0, len(candidates) - next_cursor)
    return jsonify({
        "success": True,
        "tested": len(tested),
        "total": len(candidates),
        "ok": len(ok),
        "removed": len(removed),
        "blocklisted": bool(removed),
        "stopped_reason": stopped_reason,
        "remaining": remaining,
        "next_cursor": next_cursor,
        "timeouts": timeouts,
    }), 200

# ---- Memory API Endpoints ----

@app.route('/api/memory', methods=['GET'])
def api_get_memory():
    """Get recent saved conversations from memory."""
    if not ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400
    
    try:
        limit = request.args.get('limit', default=10, type=int)
        days_back = request.args.get('days_back', default=30, type=int)
        provider = request.args.get('provider', default=None, type=str)
        
        conversations = memory.get_past_conversations(limit=limit, days_back=days_back, provider=provider)
        
        return jsonify({
            "success": True,
            "count": len(conversations),
            "conversations": conversations
        }), 200
    except Exception as e:
        logger.error(f"Memory retrieval error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory/search', methods=['GET'])
def api_search_memory():
    """Search past conversations by query."""
    if not ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400
    
    query = request.args.get('q', default='', type=str)
    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400
    
    try:
        limit = request.args.get('limit', default=5, type=int)
        days_back = request.args.get('days_back', default=30, type=int)
        
        results = memory.search_memory(query, limit=limit, days_back=days_back)
        conversations = [{"conversation": conv, "score": score} for conv, score in results]
        
        return jsonify({
            "success": True,
            "query": query,
            "count": len(conversations),
            "results": conversations
        }), 200
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory/stats', methods=['GET'])
def api_memory_stats():
    """Get statistics about stored memories."""
    if not ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400
    
    try:
        stats = memory.get_memory_stats()
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
    except Exception as e:
        logger.error(f"Memory stats error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory/<conversation_id>', methods=['DELETE'])
def api_delete_memory(conversation_id):
    """Delete a conversation from memory."""
    if not ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400
    
    try:
        deleted = memory.delete_conversation(conversation_id)
        if deleted:
            return jsonify({
                "success": True,
                "message": f"Conversation {conversation_id} deleted"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
    except Exception as e:
        logger.error(f"Memory delete error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory/cleanup', methods=['POST'])
def api_cleanup_memory():
    """Clean up old conversations from memory."""
    if not ENABLE_MEMORY:
        return jsonify({"error": "Memory feature not enabled"}), 400
    
    try:
        body = request.get_json(silent=True) or {}
        days = int(body.get('days', 90))
        
        deleted_count = memory.clear_old_memories(days=days)
        return jsonify({
            "success": True,
            "deleted": deleted_count,
            "message": f"Deleted {deleted_count} conversations older than {days} days"
        }), 200
    except Exception as e:
        logger.error(f"Memory cleanup error: {e}")
        return jsonify({"error": str(e)}), 500



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
@app.route("/api/documents/upload", methods=["POST"])
def upload_document():
    """Upload a document (PDF, DOCX, TXT, MD, etc.)."""
    if not ENABLE_FILE_UPLOAD or not FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503
    
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    
    try:
        file_content = file.read()
        note = request.form.get("note", "")
        tags = request.form.getlist("tags")
        
        doc_id = file_upload.process_uploaded_file(
            file_content, 
            file.filename,
            note=note,
            tags=tags
        )
        
        # Auto-index in RAG if available AND enabled
        rag_indexed = False
        if RAG_AVAILABLE and ENABLE_RAG:
            try:
                doc_info = file_upload.get_document(doc_id)
                if doc_info:
                    rag_indexed = rag.index_document(
                        doc_id,
                        doc_info.get("content", ""),
                        {
                            "filename": doc_info.get("filename"),
                            "uploaded_at": doc_info.get("uploaded_at"),
                            "tags": doc_info.get("tags", []),
                            "note": doc_info.get("note")
                        }
                    )
            except Exception as e:
                logger.error(f"RAG indexing failed (non-fatal): {e}")
        
        return jsonify({
            "status": "uploaded",
            "doc_id": doc_id,
            "filename": file.filename,
            "indexed_in_rag": rag_indexed
        }), 201
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """List uploaded documents."""
    if not ENABLE_FILE_UPLOAD or not FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503
    
    try:
        tags_filter = request.args.getlist("tags")
        docs = file_upload.list_documents(tags=tags_filter)
        return jsonify({"documents": docs}), 200
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<doc_id>", methods=["GET"])
def get_document(doc_id):
    """Get a specific document."""
    if not ENABLE_FILE_UPLOAD or not FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503
    
    try:
        doc = file_upload.get_document(doc_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        return jsonify(doc), 200
    except Exception as e:
        logger.error(f"Get document error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/search", methods=["GET"])
def search_documents():
    """Search documents by query."""
    if not ENABLE_FILE_UPLOAD or not FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503
    
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400
    
    try:
        results = file_upload.search_documents(query)
        return jsonify({"query": query, "results": results}), 200
    except Exception as e:
        logger.error(f"Search documents error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Delete a document."""
    if not ENABLE_FILE_UPLOAD or not FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503
    
    try:
        # Remove from RAG index if available
        if RAG_AVAILABLE:
            rag.delete_indexed_document(doc_id)
        
        success = file_upload.delete_document(doc_id)
        if not success:
            return jsonify({"error": "Document not found"}), 404
        return jsonify({"status": "deleted", "doc_id": doc_id}), 200
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/stats", methods=["GET"])
def document_stats():
    """Get document upload statistics."""
    if not ENABLE_FILE_UPLOAD or not FILE_UPLOAD_AVAILABLE:
        return jsonify({"error": "File upload feature not available"}), 503
    
    try:
        stats = file_upload.get_upload_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({"error": str(e)}), 500


# ===== RAG / SEMANTIC SEARCH ENDPOINTS =====
@app.route("/api/rag/index", methods=["POST"])
def rag_index():
    """Index a document for semantic search."""
    if not RAG_AVAILABLE:
        return jsonify({"error": "RAG feature not available"}), 503
    
    data = request.get_json()
    doc_id = data.get("doc_id")
    content = data.get("content", "")
    metadata = data.get("metadata", {})
    
    if not doc_id or not content:
        return jsonify({"error": "doc_id and content required"}), 400
    
    try:
        rag.index_document(doc_id, content, metadata)
        return jsonify({
            "status": "indexed",
            "doc_id": doc_id,
        }), 201
    except Exception as e:
        logger.error(f"RAG index error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rag/search", methods=["GET"])
def rag_search():
    """Semantic search in indexed documents."""
    if not RAG_AVAILABLE:
        return jsonify({"error": "RAG feature not available"}), 503
    
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400
    
    try:
        limit = int(request.args.get("limit", "5"))
        threshold = float(request.args.get("threshold", "0.0"))
        
        results = rag.semantic_search(query, limit=limit, threshold=threshold)
        return jsonify({
            "query": query,
            "results": results
        }), 200
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return jsonify({"error": str(e)}), 500


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


@app.route("/api/rag/stats", methods=["GET"])
def rag_stats():
    """Get RAG indexing statistics."""
    if not RAG_AVAILABLE:
        return jsonify({"error": "RAG feature not available"}), 503
    
    try:
        stats = rag.get_rag_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"RAG stats error: {e}")
        return jsonify({"error": str(e)}), 500




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
    if os.getenv("ENABLE_MCP", "true").lower() in ("false", "0", ""):
        logger.info("🔌 MCP disabled (enable_mcp: false in addon config)")
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

        # Priority 2: /config/amira/mcp_config.json (user-editable file on HA)
        if not mcp_config:
            mcp_json_path = "/config/amira/mcp_config.json"
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

        # Initialize servers
        if mcp_config and isinstance(mcp_config, dict) and mcp_config:
            connected = mcp.initialize_mcp_servers(mcp_config)
            logger.info(f"🔌 MCP: Initialized {connected} server(s)")
        else:
            logger.debug("MCP servers not configured (no mcp_config.json or MCP_SERVERS env var)")
    except Exception as e:
        logger.warning(f"⚠️ MCP initialization error: {e}")


if __name__ == "__main__":
    logger.info(f"Provider: {AI_PROVIDER} | Model: {get_active_model()}")
    _OAUTH_PROVIDERS = {"openai_codex", "claude_web", "chatgpt_web"}
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

    # Initialize fallback chain if available
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
