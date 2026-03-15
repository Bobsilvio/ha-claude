"""Settings service: manage application settings and runtime state."""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ---- Settings files and defaults ----

RUNTIME_SELECTION_FILE = "/config/amira/runtime_selection.json"
SETTINGS_FILE = "/config/amira/settings.json"
MCP_RUNTIME_FILE = "/config/amira/mcp_runtime.json"

SETTINGS_DEFAULTS = {
    "language": "en",
    "enable_memory": False,
    "enable_file_access": False,
    "enable_file_upload": True,
    "enable_voice_input": True,
    "enable_rag": False,
    "enable_chat_bubble": True,
    "enable_amira_card_button": True,
    "enable_mcp": False,
    "fallback_enabled": False,
    "anthropic_extended_thinking": False,
    "anthropic_prompt_caching": False,
    "openai_extended_thinking": False,
    "nvidia_thinking_mode": False,
    "tts_voice": "female",
    "telegram_bot_token": "",
    "twilio_account_sid": "",
    "twilio_auth_token": "",
    "twilio_whatsapp_from": "",
    "timeout": 30,
    "max_retries": 3,
    "max_conversations": 10,
    "max_snapshots_per_file": 5,
    "cost_currency": "USD",
    "mcp_config_file": "/config/amira/mcp_config.json",
}

# Maps settings key → Python global variable name
_SETTINGS_GLOBAL_MAP = {
    "language": "LANGUAGE",
    "enable_memory": "ENABLE_MEMORY",
    "enable_file_access": "ENABLE_FILE_ACCESS",
    "enable_file_upload": "ENABLE_FILE_UPLOAD",
    "enable_voice_input": "ENABLE_VOICE_INPUT",
    "enable_rag": "ENABLE_RAG",
    "enable_chat_bubble": "ENABLE_CHAT_BUBBLE",
    "enable_amira_card_button": "ENABLE_AMIRA_CARD_BUTTON",
    "enable_mcp": "ENABLE_MCP",
    "fallback_enabled": "FALLBACK_ENABLED",
    "anthropic_extended_thinking": "ANTHROPIC_EXTENDED_THINKING",
    "anthropic_prompt_caching": "ANTHROPIC_PROMPT_CACHING",
    "openai_extended_thinking": "OPENAI_EXTENDED_THINKING",
    "nvidia_thinking_mode": "NVIDIA_THINKING_MODE",
    "tts_voice": "TTS_VOICE",
    "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
    "twilio_account_sid": "TWILIO_ACCOUNT_SID",
    "twilio_auth_token": "TWILIO_AUTH_TOKEN",
    "twilio_whatsapp_from": "TWILIO_WHATSAPP_FROM",
    "timeout": "TIMEOUT",
    "max_retries": "MAX_RETRIES",
    "max_conversations": "MAX_CONVERSATIONS",
    "max_snapshots_per_file": "MAX_SNAPSHOTS_PER_FILE",
    "cost_currency": "COST_CURRENCY",
    "mcp_config_file": "MCP_CONFIG_FILE",
}


def _load_settings() -> dict:
    """Load settings.json, return empty dict if file missing or invalid."""
    try:
        if os.path.isfile(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load settings.json: {e}")
    return {}


def _save_settings(data: dict) -> None:
    """Atomic write to settings.json."""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    tmp = SETTINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, SETTINGS_FILE)


def _load_mcp_runtime_state() -> dict:
    """Load MCP runtime state (autostart servers)."""
    try:
        if os.path.isfile(MCP_RUNTIME_FILE):
            with open(MCP_RUNTIME_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
                servers = data.get("autostart_servers", [])
                if isinstance(servers, list):
                    data["autostart_servers"] = [str(s) for s in servers if isinstance(s, str) and s.strip()]
                else:
                    data["autostart_servers"] = []
                return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load MCP runtime state: {e}")
    return {"autostart_servers": []}


def _save_mcp_runtime_state(data: dict) -> None:
    """Atomic write to MCP runtime state file."""
    os.makedirs(os.path.dirname(MCP_RUNTIME_FILE), exist_ok=True)
    tmp = MCP_RUNTIME_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, MCP_RUNTIME_FILE)


def _set_mcp_server_autostart(server_name: str, enabled: bool) -> None:
    """Persist whether a specific MCP server should auto-start on addon boot."""
    state = _load_mcp_runtime_state()
    current = set(state.get("autostart_servers", []))
    if enabled:
        current.add(server_name)
    else:
        current.discard(server_name)
    state["autostart_servers"] = sorted(current)
    _save_mcp_runtime_state(state)


def load_runtime_selection() -> tuple[str, str]:
    """Load persisted provider/model selection from disk.

    Returns tuple (provider, model). Returns ("", "") if not found or invalid.
    """
    try:
        if not os.path.isfile(RUNTIME_SELECTION_FILE):
            return ("", "")
        with open(RUNTIME_SELECTION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        provider = (data.get("provider") or "").strip().lower()
        model = (data.get("model") or "").strip()
        if not provider or not model:
            return ("", "")

        # Accept only known providers; model is expected to be a technical id.
        _known = {
            "anthropic", "openai", "google", "nvidia", "github",
            "groq", "mistral", "openrouter", "deepseek", "minimax",
            "aihubmix", "siliconflow", "volcengine", "dashscope",
            "moonshot", "zhipu", "ollama", "github_copilot", "openai_codex",
            "claude_web", "chatgpt_web",
        }
        if provider not in _known:
            return ("", "")

        return (provider, model)
    except Exception as e:
        logger.warning(f"Could not load runtime selection: {e}")
        return ("", "")


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
