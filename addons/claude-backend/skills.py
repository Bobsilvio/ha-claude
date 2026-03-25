"""Skills system for Amira.

Skills are stored in /config/amira/skills/<name>/SKILL.md.
Each skill is a Markdown file with YAML frontmatter containing metadata
and a body with LLM instructions.

When the user prefixes a message with /skill-name, the skill body is
injected into the system prompt before the message is processed.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

SKILLS_DIR = "/config/amira/skills"
SKILLS_INDEX_URL = (
    "https://raw.githubusercontent.com/Bobsilvio/ha-claude/main/skills/index.json"
)
_VALID_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")
_RESERVED_NAMES = {"help", "clear", "reset", "debug", "new", "abort"}
_MAX_BODY_CHARS = 8000

# Store cache: avoid hammering GitHub on every panel open
_store_cache: dict = {"ts": 0.0, "data": None}
_store_lock = threading.Lock()
_STORE_TTL = 300  # 5 minutes


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_skill_md(path: str) -> dict:
    """Parse a SKILL.md file. Returns {"meta": {...}, "body": "..."}."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    meta: dict = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            import yaml
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except Exception as e:
                logger.warning(f"Skills: bad frontmatter in {path}: {e}")
            body = parts[2].strip()

    return {"meta": meta, "body": body}


# ---------------------------------------------------------------------------
# List / get installed skills
# ---------------------------------------------------------------------------

def list_skills() -> list[dict]:
    """Return metadata for all installed skills (no body)."""
    skills = []
    if not os.path.isdir(SKILLS_DIR):
        return skills
    for name in sorted(os.listdir(SKILLS_DIR)):
        skill_path = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if not os.path.isfile(skill_path):
            continue
        try:
            parsed = _parse_skill_md(skill_path)
            meta = parsed["meta"]
            meta.setdefault("name", name)
            skills.append({
                "name": name,
                "version": meta.get("version", ""),
                "description": meta.get("description", {}),
                "author": meta.get("author", ""),
                "tags": meta.get("tags", []),
                "min_version": meta.get("min_version", ""),
                "installed": True,
            })
        except Exception as e:
            logger.warning(f"Skills: could not read {skill_path}: {e}")
    return skills


def get_skill(name: str) -> Optional[dict]:
    """Return full skill data (meta + body) or None if not found."""
    skill_path = os.path.join(SKILLS_DIR, name, "SKILL.md")
    if not os.path.isfile(skill_path):
        return None
    try:
        parsed = _parse_skill_md(skill_path)
        parsed["meta"].setdefault("name", name)
        return parsed
    except Exception as e:
        logger.warning(f"Skills: could not read {skill_path}: {e}")
        return None


# ---------------------------------------------------------------------------
# Install / delete
# ---------------------------------------------------------------------------

def _validate_name(name: str) -> Optional[str]:
    """Return error string or None if valid."""
    if not _VALID_NAME_RE.match(name):
        return f"Invalid skill name '{name}'. Use only lowercase letters, digits, hyphens, underscores (2-31 chars, must start with a letter)."
    if name in _RESERVED_NAMES:
        return f"'{name}' is a reserved name and cannot be used as a skill."
    return None


def install_skill(name: str, skill_md_content: str) -> dict:
    """Write a skill to disk. Returns {"success": True, "name": name} or {"error": ...}."""
    err = _validate_name(name)
    if err:
        return {"error": err}

    if len(skill_md_content) > _MAX_BODY_CHARS + 500:
        return {"error": f"Skill content too large (max {_MAX_BODY_CHARS + 500} chars)."}

    skill_dir = os.path.join(SKILLS_DIR, name)
    os.makedirs(skill_dir, exist_ok=True)
    skill_path = os.path.join(skill_dir, "SKILL.md")
    try:
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(skill_md_content)
        logger.info(f"Skills: installed '{name}'")
        return {"success": True, "name": name}
    except Exception as e:
        return {"error": str(e)}


def delete_skill(name: str) -> bool:
    """Remove a skill directory. Returns True if deleted."""
    skill_dir = os.path.join(SKILLS_DIR, name)
    if not os.path.isdir(skill_dir):
        return False
    try:
        shutil.rmtree(skill_dir)
        logger.info(f"Skills: deleted '{name}'")
        return True
    except Exception as e:
        logger.warning(f"Skills: could not delete '{name}': {e}")
        return False


# ---------------------------------------------------------------------------
# Store (GitHub index)
# ---------------------------------------------------------------------------

def fetch_store_index(installed_names: Optional[set] = None) -> list[dict]:
    """Fetch skills index from GitHub (cached 5 min). Raises on failure."""
    with _store_lock:
        now = time.time()
        if _store_cache["data"] is not None and (now - _store_cache["ts"]) < _STORE_TTL:
            skills = _store_cache["data"]
        else:
            import urllib.request
            import json
            req = urllib.request.Request(
                SKILLS_INDEX_URL,
                headers={"User-Agent": "Amira-HA-Addon/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            skills = data.get("skills", [])
            _store_cache["ts"] = now
            _store_cache["data"] = skills

    if installed_names is not None:
        for s in skills:
            s["installed"] = s.get("name", "") in installed_names
    return skills


def fetch_skill_md(raw_url: str) -> str:
    """Fetch raw SKILL.md content from a URL. Raises on failure."""
    import urllib.request
    req = urllib.request.Request(raw_url, headers={"User-Agent": "Amira-HA-Addon/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8")


# ---------------------------------------------------------------------------
# Chat integration
# ---------------------------------------------------------------------------

_COMMAND_RE = re.compile(r"^/([a-z][a-z0-9_-]{1,30})(?:\s+(.*))?$", re.DOTALL | re.IGNORECASE)


def parse_skill_command(message: str) -> tuple[Optional[str], str]:
    """Detect /skill-name prefix. Returns (skill_name, remaining_text) or (None, message)."""
    m = _COMMAND_RE.match(message.strip())
    if m:
        name = m.group(1).lower()
        remaining = (m.group(2) or "").strip()
        return name, remaining
    return None, message


def inject_skill_into_prompt(skill_name: str, base_prompt: str) -> Optional[str]:
    """Return enriched system prompt with skill instructions prepended, or None if skill not found."""
    skill = get_skill(skill_name)
    if skill is None:
        return None
    body = skill["body"].strip()
    if not body:
        return None
    separator = "\n\n---\n\n"
    return f"SKILL INSTRUCTIONS ({skill_name}):\n{body}{separator}{base_prompt}" if base_prompt else f"SKILL INSTRUCTIONS ({skill_name}):\n{body}"
