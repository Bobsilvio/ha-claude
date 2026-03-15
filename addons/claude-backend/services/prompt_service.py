"""Prompt service: manage custom system prompts and agent configuration."""

import json
import os
import logging
from typing import Optional, Dict

try:
    import agent_config
    AGENT_CONFIG_AVAILABLE = True
except ImportError:
    AGENT_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)

# Persist system prompt override across restarts
CUSTOM_SYSTEM_PROMPT_FILE = "/config/amira/custom_system_prompt.txt"

# Agent profiles configuration file
AGENTS_FILE = "/config/amira/agents.json"

# Whitelist of config files editable via /api/config/save
CONFIG_EDITABLE_FILES = {
    "amira/agents.json",
    "amira/mcp_config.json",
    "amira/custom_system_prompt.txt",
    "amira/memory/MEMORY.md",
}


def _load_custom_system_prompt_from_disk() -> Optional[str]:
    """Load custom system prompt from disk, or return None if missing/invalid."""
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
    """Persist custom system prompt to disk, or delete if empty."""
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


def load_agents_config() -> Optional[Dict]:
    """Load agent configuration from disk.

    Returns the raw config data as dict, or None if not found/invalid.
    """
    if not os.path.isfile(AGENTS_FILE):
        return None
    try:
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load agents config: {e}")
        return None
