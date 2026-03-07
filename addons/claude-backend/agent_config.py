"""Agent Configuration — multi-agent system with per-agent model/tools/identity.

Inspired by OpenClaw's agent-scope.ts + identity.ts:
- Each agent has its own model, fallback chain, tools, identity
- Agents are defined in a JSON config file
- Session → agent resolution with defaults
- Agent identity (name, emoji, message prefix)
- Model override chain: agent → defaults → global

The user keeps selecting provider+model from the two cascade dropdowns.
When an agent is selected, its configured model becomes the default but
the user can still override via the dropdown.

Usage:
    from agent_config import get_agent_manager, AgentIdentity

    mgr = get_agent_manager()
    agent = mgr.resolve_agent("coder")
    print(agent.identity.name, agent.identity.emoji)
    print(agent.model_primary)  # "anthropic/claude-opus-4-6"
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Persistent agent config file (editable by user or API)
AGENT_CONFIG_FILE = "/config/amira/agents.json"

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@dataclass
class AgentIdentity:
    """Visual identity of an agent (name, emoji, message prefix)."""
    name: str = "Amira"
    emoji: str = "🤖"
    description: str = ""

    @property
    def prefix(self) -> str:
        """Message prefix e.g. '[Amira]'."""
        return f"[{self.name}]" if self.name else ""

    @property
    def ack_reaction(self) -> str:
        """Reaction emoji for acknowledging a message."""
        return self.emoji or "👀"


@dataclass
class ModelRef:
    """A provider/model reference."""
    provider: str
    model: str

    @classmethod
    def from_string(cls, raw: str, default_provider: str = "anthropic") -> "ModelRef":
        """Parse 'provider/model' or just 'model' (uses default_provider)."""
        raw = raw.strip()
        if "/" in raw:
            parts = raw.split("/", 1)
            return cls(provider=parts[0].strip(), model=parts[1].strip())
        return cls(provider=default_provider, model=raw)

    def to_string(self) -> str:
        return f"{self.provider}/{self.model}"

    def __str__(self) -> str:
        return self.to_string()


@dataclass
class AgentModelConfig:
    """Model configuration with fallback chain."""
    primary: Optional[ModelRef] = None
    fallbacks: List[ModelRef] = field(default_factory=list)

    def get_all_candidates(self) -> List[ModelRef]:
        """Return primary + fallbacks in order."""
        result = []
        if self.primary:
            result.append(self.primary)
        result.extend(self.fallbacks)
        return result


@dataclass
class AgentEntry:
    """Full configuration for a single agent.

    Serialisable to/from JSON so users can edit agents.json.
    """
    id: str
    name: str = ""
    identity: AgentIdentity = field(default_factory=AgentIdentity)
    model_config: AgentModelConfig = field(default_factory=AgentModelConfig)
    # Tool control
    tools: Optional[List[str]] = None       # allowed tool names (None = all)
    tools_blocked: List[str] = field(default_factory=list)  # explicitly blocked tools
    # Behaviour
    system_prompt_override: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    thinking_level: Optional[str] = None    # off, low, medium, high, adaptive
    # Flags
    is_default: bool = False
    enabled: bool = True
    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to JSON-friendly dict."""
        d: Dict[str, Any] = {"id": self.id}
        if self.name:
            d["name"] = self.name
        d["identity"] = {"name": self.identity.name, "emoji": self.identity.emoji}
        if self.identity.description:
            d["identity"]["description"] = self.identity.description
        # Model
        mc: Dict[str, Any] = {}
        if self.model_config.primary:
            mc["primary"] = self.model_config.primary.to_string()
        if self.model_config.fallbacks:
            mc["fallbacks"] = [f.to_string() for f in self.model_config.fallbacks]
        if mc:
            d["model"] = mc
        # Tools
        if self.tools is not None:
            d["tools"] = self.tools
        if self.tools_blocked:
            d["tools_blocked"] = self.tools_blocked
        # Behaviour
        if self.system_prompt_override:
            d["system_prompt"] = self.system_prompt_override
        if self.temperature is not None:
            d["temperature"] = self.temperature
        if self.max_tokens is not None:
            d["max_tokens"] = self.max_tokens
        if self.thinking_level:
            d["thinking_level"] = self.thinking_level
        # Flags
        if self.is_default:
            d["default"] = True
        if not self.enabled:
            d["enabled"] = False
        if self.description:
            d["description"] = self.description
        if self.tags:
            d["tags"] = self.tags
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentEntry":
        """Deserialise from JSON dict."""
        agent_id = str(data.get("id", "")).strip()
        if not agent_id:
            raise ValueError("Agent entry missing 'id'")

        identity_data = data.get("identity") or {}
        identity = AgentIdentity(
            name=str(identity_data.get("name", data.get("name", ""))).strip() or agent_id,
            emoji=str(identity_data.get("emoji", "🤖")).strip(),
            description=str(identity_data.get("description", "")).strip(),
        )

        # Model config
        model_data = data.get("model") or {}
        model_config = AgentModelConfig()
        if isinstance(model_data, str):
            # Simple string: "anthropic/claude-opus-4-6"
            model_config.primary = ModelRef.from_string(model_data)
        elif isinstance(model_data, dict):
            primary_raw = model_data.get("primary", "")
            if primary_raw:
                model_config.primary = ModelRef.from_string(str(primary_raw))
            for fb_raw in (model_data.get("fallbacks") or []):
                if fb_raw:
                    model_config.fallbacks.append(ModelRef.from_string(str(fb_raw)))
        
        return cls(
            id=agent_id,
            name=str(data.get("name", "")).strip() or identity.name,
            identity=identity,
            model_config=model_config,
            tools=data.get("tools"),  # None means "all"
            tools_blocked=list(data.get("tools_blocked") or []),
            system_prompt_override=data.get("system_prompt") or None,
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            thinking_level=data.get("thinking_level"),
            is_default=bool(data.get("default", False)),
            enabled=bool(data.get("enabled", True)),
            description=str(data.get("description", "")).strip(),
            tags=list(data.get("tags") or []),
        )


# ---------------------------------------------------------------------------
# Defaults config — global fallback for all agents
# ---------------------------------------------------------------------------

@dataclass
class AgentDefaults:
    """Global defaults applied when an agent doesn't specify something."""
    model: AgentModelConfig = field(default_factory=AgentModelConfig)
    thinking_default: str = "off"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        mc: Dict[str, Any] = {}
        if self.model.primary:
            mc["primary"] = self.model.primary.to_string()
        if self.model.fallbacks:
            mc["fallbacks"] = [f.to_string() for f in self.model.fallbacks]
        if mc:
            d["model"] = mc
        d["thinking_default"] = self.thinking_default
        d["temperature"] = self.temperature
        d["max_tokens"] = self.max_tokens
        if self.system_prompt:
            d["system_prompt"] = self.system_prompt
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentDefaults":
        model_config = AgentModelConfig()
        model_data = data.get("model") or {}
        if isinstance(model_data, str):
            model_config.primary = ModelRef.from_string(model_data)
        elif isinstance(model_data, dict):
            if model_data.get("primary"):
                model_config.primary = ModelRef.from_string(str(model_data["primary"]))
            for fb in (model_data.get("fallbacks") or []):
                if fb:
                    model_config.fallbacks.append(ModelRef.from_string(str(fb)))
        return cls(
            model=model_config,
            thinking_default=str(data.get("thinking_default", "off")),
            temperature=float(data.get("temperature", 0.7)),
            max_tokens=int(data.get("max_tokens", 4096)),
            system_prompt=data.get("system_prompt"),
        )


# ---------------------------------------------------------------------------
# AgentManager — loads, resolves, persists agents
# ---------------------------------------------------------------------------

class AgentManager:
    """Manages agent configuration lifecycle.

    Config file format (agents.json):
    {
        "defaults": {
            "model": {"primary": "anthropic/claude-opus-4-6", "fallbacks": ["openai/gpt-4o"]},
            "thinking_default": "adaptive",
            "temperature": 0.7,
            "max_tokens": 4096
        },
        "agents": [
            {
                "id": "amira",
                "name": "Amira",
                "identity": {"name": "Amira", "emoji": "🤖"},
                "model": {"primary": "anthropic/claude-opus-4-6", "fallbacks": ["openai/gpt-4o"]},
                "default": true
            },
            {
                "id": "coder",
                "name": "Coder",
                "identity": {"name": "CodeBot", "emoji": "💻"},
                "model": {"primary": "anthropic/claude-opus-4-6"},
                "tools": ["read_config_file", "write_config_file", "list_config_files"],
                "thinking_level": "high"
            }
        ]
    }
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._agents: Dict[str, AgentEntry] = {}
        self._defaults = AgentDefaults()
        self._active_agent_id: Optional[str] = None
        self._channel_agents: Dict[str, str] = {}   # channel → agent_id
        self._config_path = AGENT_CONFIG_FILE
        self._last_load_ts: float = 0.0
        self._load_config()

    # -- config I/O --

    def _load_config(self) -> None:
        """Load agent config from disk (or create default)."""
        try:
            if os.path.isfile(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                self._parse_config(data)
                self._last_load_ts = time.time()
                logger.info(f"AgentManager: loaded {len(self._agents)} agents from {self._config_path}")
            else:
                self._create_default_config()
        except Exception as e:
            logger.warning(f"AgentManager: could not load config ({e}), using defaults")
            self._create_default_config()

    def _parse_config(self, data: Dict[str, Any]) -> None:
        """Parse raw JSON config into agents + defaults.

        Supports multiple formats:
        1. Canonical: {"defaults": {...}, "agents": [ {id, name, ...}, ... ]}
        2. Legacy dict: {"agents": {"home": {...}, "coder": {...}}, "active": "home"}
        3. Flat dict (README shorthand): {"home": {...}, "coder": {...}}
        """
        # Defaults
        defaults_data = data.get("defaults") or {}
        self._defaults = AgentDefaults.from_dict(defaults_data)

        # Agents — detect format
        agents_raw = data.get("agents")
        self._agents.clear()

        if isinstance(agents_raw, list):
            # Format 1: canonical array
            for agent_data in agents_raw:
                try:
                    entry = AgentEntry.from_dict(agent_data)
                    self._agents[entry.id] = entry
                except Exception as e:
                    logger.warning(f"AgentManager: skipping invalid agent entry: {e}")
        elif isinstance(agents_raw, dict):
            # Format 2: legacy dict keyed by agent id
            for agent_id, agent_data in agents_raw.items():
                try:
                    if isinstance(agent_data, dict):
                        agent_data.setdefault("id", agent_id)
                        entry = AgentEntry.from_dict(agent_data)
                        self._agents[entry.id] = entry
                except Exception as e:
                    logger.warning(f"AgentManager: skipping agent '{agent_id}': {e}")
        else:
            # Format 3: flat dict — top-level keys are agent ids (skip known meta keys)
            _meta_keys = {"defaults", "active", "channel_agents", "agents"}
            for key, val in data.items():
                if key in _meta_keys or not isinstance(val, dict):
                    continue
                try:
                    val.setdefault("id", key)
                    entry = AgentEntry.from_dict(val)
                    self._agents[entry.id] = entry
                except Exception as e:
                    logger.warning(f"AgentManager: skipping flat agent '{key}': {e}")

        # Set active agent to default
        default_agent = self._find_default_agent()
        if default_agent:
            self._active_agent_id = default_agent.id

        # Channel → agent assignments
        self._channel_agents = {}
        for ch, aid in (data.get("channel_agents") or {}).items():
            ch = str(ch).strip().lower()
            aid = str(aid).strip()
            if ch and aid and aid in self._agents:
                self._channel_agents[ch] = aid

    def _create_default_config(self) -> None:
        """Create the default Amira agent."""
        default_agent = AgentEntry(
            id="amira",
            name="Amira",
            identity=AgentIdentity(name="Amira", emoji="🤖",
                                   description="Your AI assistant for Home Assistant"),
            is_default=True,
            enabled=True,
        )
        self._agents = {"amira": default_agent}
        self._defaults = AgentDefaults()
        self._active_agent_id = "amira"
        self._channel_agents = {}
        # Don't persist yet — let save_config() be explicit
        logger.debug("AgentManager: created default Amira agent")

    def save_config(self) -> bool:
        """Persist current agent config to disk."""
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            data = {
                "defaults": self._defaults.to_dict(),
                "agents": [a.to_dict() for a in self._agents.values()],
            }
            if self._channel_agents:
                data["channel_agents"] = dict(self._channel_agents)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"AgentManager: saved {len(self._agents)} agents to {self._config_path}")
            return True
        except Exception as e:
            logger.error(f"AgentManager: could not save config: {e}")
            return False

    def reload_config(self) -> None:
        """Reload config from disk."""
        with self._lock:
            self._load_config()

    # -- agent resolution --

    def _find_default_agent(self) -> Optional[AgentEntry]:
        """Find the first agent marked as default, or the first enabled one."""
        for a in self._agents.values():
            if a.is_default and a.enabled:
                return a
        # Fallback: first enabled agent
        for a in self._agents.values():
            if a.enabled:
                return a
        return None

    def resolve_agent(self, agent_id: Optional[str] = None) -> Optional[AgentEntry]:
        """Resolve an agent by ID, or return the active/default agent."""
        with self._lock:
            if agent_id:
                agent = self._agents.get(agent_id)
                if agent and agent.enabled:
                    return agent
                return None
            # Active agent
            if self._active_agent_id:
                agent = self._agents.get(self._active_agent_id)
                if agent and agent.enabled:
                    return agent
            # Default
            return self._find_default_agent()

    def get_active_agent(self) -> Optional[AgentEntry]:
        """Get the currently active agent."""
        return self.resolve_agent()

    def set_active_agent(self, agent_id: str) -> bool:
        """Switch the active agent."""
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent or not agent.enabled:
                return False
            self._active_agent_id = agent_id
        logger.info(f"AgentManager: active agent set to '{agent_id}'")
        return True

    # -- model resolution (OpenClaw-style cascade) --

    def resolve_model(self, agent_id: Optional[str] = None,
                      provider_override: Optional[str] = None,
                      model_override: Optional[str] = None) -> ModelRef:
        """Resolve the effective model for a conversation.

        Priority chain:
        1. Explicit override (from UI dropdown / API) — highest priority
        2. Agent's configured primary model
        3. Global defaults model
        4. Hardcoded fallback: anthropic/claude-opus-4-6
        """
        # 1. Explicit overrides (UI selection)
        if provider_override and model_override:
            return ModelRef(provider=provider_override, model=model_override)

        # 2. Agent-level model
        agent = self.resolve_agent(agent_id)
        if agent and agent.model_config.primary:
            return agent.model_config.primary

        # 3. Global defaults
        with self._lock:
            if self._defaults.model.primary:
                return self._defaults.model.primary

        # 4. Hardcoded fallback
        return ModelRef(provider="anthropic", model="claude-opus-4-6")

    def resolve_fallback_chain(self, agent_id: Optional[str] = None,
                               provider_override: Optional[str] = None,
                               model_override: Optional[str] = None) -> List[ModelRef]:
        """Build the full fallback chain for a request.

        Returns: list of ModelRef in priority order (primary first).
        """
        chain: List[ModelRef] = []
        seen: Set[str] = set()

        def _add(ref: ModelRef) -> None:
            key = ref.to_string()
            if key not in seen:
                seen.add(key)
                chain.append(ref)

        # Primary (resolved)
        primary = self.resolve_model(agent_id, provider_override, model_override)
        _add(primary)

        # Agent fallbacks
        agent = self.resolve_agent(agent_id)
        if agent:
            for fb in agent.model_config.fallbacks:
                _add(fb)

        # Global defaults fallbacks
        with self._lock:
            for fb in self._defaults.model.fallbacks:
                _add(fb)

        return chain

    # -- identity resolution --

    def resolve_identity(self, agent_id: Optional[str] = None) -> AgentIdentity:
        """Resolve the identity for the current/specified agent."""
        agent = self.resolve_agent(agent_id)
        if agent:
            return agent.identity
        return AgentIdentity()  # default Amira

    # -- tool filtering --

    def resolve_allowed_tools(self, agent_id: Optional[str] = None,
                              all_tools: Optional[List[str]] = None) -> Optional[List[str]]:
        """Resolve which tools this agent can use.

        Returns None if all tools are allowed, or a filtered list.
        """
        agent = self.resolve_agent(agent_id)
        if not agent:
            return all_tools

        # If agent has explicit allowed tools, filter
        if agent.tools is not None and all_tools is not None:
            allowed_set = set(agent.tools)
            return [t for t in all_tools if t in allowed_set]

        # If agent has blocked tools, remove them
        if agent.tools_blocked and all_tools is not None:
            blocked_set = set(agent.tools_blocked)
            return [t for t in all_tools if t not in blocked_set]

        return all_tools

    # -- CRUD for agents --

    def list_agents(self, include_disabled: bool = False) -> List[AgentEntry]:
        """Return all agents, always including Amira as enabled and default."""
        with self._lock:
            agents = list(self._agents.values())
            # Ensure Amira is always present, enabled, and default
            amira = next((a for a in agents if a.id == "amira"), None)
            if not amira:
                amira = AgentEntry(
                    id="amira",
                    name="Amira",
                    identity=AgentIdentity(name="Amira", emoji="🤖", description="Your AI assistant for Home Assistant"),
                    is_default=True,
                    enabled=True,
                )
                agents.append(amira)
            else:
                amira.enabled = True
                amira.is_default = True
        if not include_disabled:
            agents = [a for a in agents if a.enabled]
        # Always sort Amira first
        return sorted(agents, key=lambda a: (a.id != "amira", a.name or a.id))

    def get_agent(self, agent_id: str) -> Optional[AgentEntry]:
        """Get a specific agent by ID."""
        with self._lock:
            return self._agents.get(agent_id)

    def add_agent(self, agent: AgentEntry) -> bool:
        """Add or replace an agent."""
        with self._lock:
            self._agents[agent.id] = agent
        logger.info(f"AgentManager: added agent '{agent.id}'")
        return True

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent."""
        with self._lock:
            if agent_id not in self._agents:
                return False
            del self._agents[agent_id]
            if self._active_agent_id == agent_id:
                default = self._find_default_agent()
                self._active_agent_id = default.id if default else None
        logger.info(f"AgentManager: removed agent '{agent_id}'")
        return True

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[AgentEntry]:
        """Update specific fields of an existing agent."""
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return None

            # Apply updates
            if "name" in updates:
                agent.name = str(updates["name"])
            if "identity" in updates:
                id_data = updates["identity"]
                if isinstance(id_data, dict):
                    if "name" in id_data:
                        agent.identity.name = str(id_data["name"])
                    if "emoji" in id_data:
                        agent.identity.emoji = str(id_data["emoji"])
                    if "description" in id_data:
                        agent.identity.description = str(id_data["description"])
            if "model" in updates:
                model_data = updates["model"]
                if isinstance(model_data, str):
                    agent.model_config.primary = ModelRef.from_string(model_data)
                elif isinstance(model_data, dict):
                    if "primary" in model_data:
                        agent.model_config.primary = ModelRef.from_string(str(model_data["primary"]))
                    if "fallbacks" in model_data:
                        agent.model_config.fallbacks = [
                            ModelRef.from_string(str(f)) for f in model_data["fallbacks"] if f
                        ]
            if "tools" in updates:
                agent.tools = updates["tools"]
            if "tools_blocked" in updates:
                agent.tools_blocked = list(updates["tools_blocked"] or [])
            if "system_prompt" in updates:
                agent.system_prompt_override = updates["system_prompt"] or None
            if "temperature" in updates:
                agent.temperature = updates["temperature"]
            if "max_tokens" in updates:
                agent.max_tokens = updates["max_tokens"]
            if "thinking_level" in updates:
                agent.thinking_level = updates["thinking_level"]
            if "default" in updates:
                agent.is_default = bool(updates["default"])
            if "enabled" in updates:
                agent.enabled = bool(updates["enabled"])
            if "description" in updates:
                agent.description = str(updates["description"])

            return agent

    # -- API response helpers --

    def get_agents_for_api(self) -> List[Dict[str, Any]]:
        """Return agent list suitable for the API/UI. Amira is always present, enabled, and default."""
        agents = self.list_agents()
        result = []
        for a in agents:
            # Force Amira always enabled/default in API
            if a.id == "amira":
                a.enabled = True
                a.is_default = True
            d = {
                "id": a.id,
                "name": a.identity.name or a.name or a.id,
                "emoji": a.identity.emoji,
                "description": a.identity.description or a.description,
                "is_default": a.is_default,
                "is_active": a.id == self._active_agent_id,
            }
            if a.model_config.primary:
                d["model"] = a.model_config.primary.to_string()
            if a.model_config.fallbacks:
                d["fallbacks"] = [f.to_string() for f in a.model_config.fallbacks]
            if a.thinking_level:
                d["thinking_level"] = a.thinking_level
            if a.tags:
                d["tags"] = a.tags
            result.append(d)
        # Always sort Amira first
        return sorted(result, key=lambda d: (d["id"] != "amira", d["name"]))

    def get_defaults(self) -> AgentDefaults:
        """Return global defaults."""
        with self._lock:
            return self._defaults

    def update_defaults(self, updates: Dict[str, Any]) -> AgentDefaults:
        """Update global defaults."""
        with self._lock:
            if "model" in updates:
                model_data = updates["model"]
                if isinstance(model_data, str):
                    self._defaults.model.primary = ModelRef.from_string(model_data)
                elif isinstance(model_data, dict):
                    if "primary" in model_data:
                        self._defaults.model.primary = ModelRef.from_string(str(model_data["primary"]))
                    if "fallbacks" in model_data:
                        self._defaults.model.fallbacks = [
                            ModelRef.from_string(str(f)) for f in model_data["fallbacks"] if f
                        ]
            if "thinking_default" in updates:
                self._defaults.thinking_default = str(updates["thinking_default"])
            if "temperature" in updates:
                self._defaults.temperature = float(updates["temperature"])
            if "max_tokens" in updates:
                self._defaults.max_tokens = int(updates["max_tokens"])
            if "system_prompt" in updates:
                self._defaults.system_prompt = updates["system_prompt"] or None
            return self._defaults

    # -- channel → agent assignments --

    def get_channel_agent(self, channel: str) -> Optional[str]:
        """Get the agent_id assigned to a channel (telegram, whatsapp, alexa…)."""
        with self._lock:
            return self._channel_agents.get(channel.strip().lower())

    def set_channel_agent(self, channel: str, agent_id: Optional[str]) -> bool:
        """Assign an agent to a channel.  Pass agent_id=None to clear."""
        channel = channel.strip().lower()
        if not channel:
            return False
        with self._lock:
            if agent_id is None or agent_id == "":
                self._channel_agents.pop(channel, None)
            else:
                agent = self._agents.get(agent_id)
                if not agent or not agent.enabled:
                    return False
                self._channel_agents[channel] = agent_id
        return True

    def get_all_channel_agents(self) -> Dict[str, str]:
        """Return all channel → agent_id assignments."""
        with self._lock:
            return dict(self._channel_agents)

    # -- stats --

    def stats(self) -> Dict[str, Any]:
        """Return manager statistics."""
        with self._lock:
            return {
                "total_agents": len(self._agents),
                "enabled_agents": len([a for a in self._agents.values() if a.enabled]),
                "active_agent": self._active_agent_id,
                "default_agent": next(
                    (a.id for a in self._agents.values() if a.is_default), None
                ),
                "channel_agents": dict(self._channel_agents),
                "config_path": self._config_path,
                "last_loaded": self._last_load_ts or None,
            }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_manager: Optional[AgentManager] = None
_manager_lock = threading.Lock()


def get_agent_manager() -> AgentManager:
    """Return the global AgentManager singleton (lazy-init, thread-safe)."""
    global _manager
    if _manager is not None:
        return _manager
    with _manager_lock:
        if _manager is None:
            _manager = AgentManager()
    return _manager
