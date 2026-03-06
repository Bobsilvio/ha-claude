"""Centralized Tool Registry — inspired by OpenClaw's tool pipeline.

Provides:
 - ToolDefinition: bundles schema + executor in a single unit (like OpenClaw's ToolDefinition)
 - ToolPolicy: cascading filter rules (profile → provider → intent → tier)
 - ToolRegistry: central manager for tool collection, filtering, formatting
 - Provider adapters: to_anthropic(), to_openai(), to_gemini() with per-provider schema normalization
 - Hooks: before_tool_call / after_tool_call interception (read-only, logging, abort)

Architecture mirrors OpenClaw's 8-step pipeline:
 1. Collect base tools (HA tools: entities, services, automations, ...)
 2. Add platform-specific tools (MCP tools, dashboard tools, ...)
 3. Filter by policy (read-only, file_access, ...)
 4. Filter by provider tier (compact/extended/full)
 5. Filter by intent (focused tool subsets)
 6. Normalize JSON Schema per provider
 7. Wrap with before_tool_call hooks
 8. Execute with result normalization

Usage:
    from tool_registry import get_registry

    registry = get_registry()
    registry.register(ToolDefinition(
        name="get_entities",
        description="Get HA entity states",
        parameters={...},
        execute=my_function,
        category="query",
    ))

    # Get tools for a specific provider + intent
    formatted = registry.get_tools_for_provider("anthropic", intent_tools=["get_entities"])

    # Execute with hooks
    result = registry.execute("get_entities", {"domain": "light"}, context=ctx)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Union,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 1. ToolDefinition — bundles schema + executor (OpenClaw-style)
# ============================================================================


class ToolCategory(str, Enum):
    """Tool categories for policy-based filtering."""
    QUERY = "query"           # Read-only: get_entities, search_entities, get_history, ...
    CONTROL = "control"       # Device control: call_service, activate_scene, ...
    AUTOMATION = "automation" # Automation CRUD: create/update/delete automation, script, ...
    DASHBOARD = "dashboard"   # Dashboard CRUD: create/update/delete dashboard, HTML dashboard, ...
    CONFIG = "config"         # Config file access: read/write config files, check_config, ...
    SYSTEM = "system"         # System: backup, repairs, logs, users, events, ...
    MCP = "mcp"               # MCP protocol tools (dynamic)
    HELPER = "helper"         # Helper management: manage_helpers, manage_areas, ...
    NOTIFICATION = "notification"  # Notifications: send_notification, ...
    MEDIA = "media"           # Media: browse_media, ...


@dataclass
class ToolDefinition:
    """A single tool definition — bundles schema + executor.

    Mirrors OpenClaw's ToolDefinition interface:
    - name: unique tool identifier
    - description: human-readable purpose
    - parameters: JSON Schema for input validation
    - execute: async-compatible callable (name, args) → str result
    - category: for policy filtering
    - read_only: True if tool has no side effects
    - labels: arbitrary tags for fine-grained filtering
    - user_description: Italian user-friendly label for UI status messages
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    execute: Callable[[Dict[str, Any]], str]
    category: ToolCategory = ToolCategory.QUERY
    read_only: bool = True
    labels: Set[str] = field(default_factory=set)
    user_description: str = ""
    # Tier membership (for compact/extended filtering)
    tier_compact: bool = False   # Included in compact (6-tool) set
    tier_extended: bool = False  # Included in extended (12-tool) set
    # If True, description is shortened for compact tier
    compact_description: str = ""

    def __post_init__(self):
        if not self.user_description:
            self.user_description = self.name.replace("_", " ").title()
        # Ensure labels is a set
        if isinstance(self.labels, (list, tuple)):
            self.labels = set(self.labels)


# ============================================================================
# 2. ToolPolicy — cascading filter (OpenClaw: profile → provider → global → agent)
# ============================================================================


class ToolPolicy(ABC):
    """Abstract tool policy filter.

    Policies are evaluated in order. A tool must pass ALL active policies
    to be included. This mirrors OpenClaw's cascading policy chain.
    """

    @abstractmethod
    def allows(self, tool: ToolDefinition, context: Dict[str, Any]) -> bool:
        """Return True if this policy allows the tool in the given context."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class FileAccessPolicy(ToolPolicy):
    """Block config_edit tools when ENABLE_FILE_ACCESS is False.
    
    Mirrors OpenClaw's owner-only policy for privileged operations.
    """

    def allows(self, tool: ToolDefinition, context: Dict[str, Any]) -> bool:
        if tool.category == ToolCategory.CONFIG:
            return context.get("enable_file_access", False)
        return True


class ReadOnlyPolicy(ToolPolicy):
    """Block write tools when session is in read-only mode.

    Unlike OpenClaw's policy that short-circuits, this one still allows
    the tool to be sent but marks it — the execute hook returns a preview.
    We only block at execution time, not at schema level, so the LLM
    can still "see" the tool and generate the YAML preview.
    """

    def allows(self, tool: ToolDefinition, context: Dict[str, Any]) -> bool:
        # Read-only policy doesn't filter tools at schema level —
        # it intercepts at execution time via BeforeToolHook.
        return True


class TierPolicy(ToolPolicy):
    """Filter tools based on provider tier (compact/extended/full).

    compact  → only tools with tier_compact=True (6 tools)
    extended → only tools with tier_extended=True (12 tools)
    full     → all tools
    """

    def allows(self, tool: ToolDefinition, context: Dict[str, Any]) -> bool:
        tier = context.get("tier", "full")
        if tier == "compact":
            return tool.tier_compact
        elif tier == "extended":
            return tool.tier_extended or tool.tier_compact
        return True  # full tier: everything


class IntentPolicy(ToolPolicy):
    """Filter tools based on detected intent.

    intent_tools=None → all tools (LLM-first mode)
    intent_tools=[]   → no tools (chat mode)
    intent_tools=["get_entities", ...] → only listed tools
    """

    def allows(self, tool: ToolDefinition, context: Dict[str, Any]) -> bool:
        intent_tools = context.get("intent_tools")
        if intent_tools is None:
            return True  # LLM-first: all tools
        return tool.name in intent_tools


class CategoryPolicy(ToolPolicy):
    """Block/allow entire tool categories.

    context["blocked_categories"] = {ToolCategory.CONFIG, ToolCategory.SYSTEM}
    """

    def allows(self, tool: ToolDefinition, context: Dict[str, Any]) -> bool:
        blocked: Set[ToolCategory] = context.get("blocked_categories", set())
        return tool.category not in blocked


class AgentToolPolicy(ToolPolicy):
    """Filter tools based on the active agent's allow/block lists.

    Reads from agent_config.AgentEntry.tools (allow-list) and
    agent_config.AgentEntry.tools_blocked (deny-list).

    context keys:
        agent_id: str | None  — active agent id (None = no filtering)

    Logic (mirrors OpenClaw's agent → tools.allow pipeline step):
      - If agent has a non-empty `tools` list → only those tools are allowed
      - If agent has a non-empty `tools_blocked` list → those tools are denied
      - If both are empty → all tools pass (no agent-level restriction)
    """

    def allows(self, tool: ToolDefinition, context: Dict[str, Any]) -> bool:
        agent_id = context.get("agent_id")
        if not agent_id:
            return True

        try:
            import agent_config
            mgr = agent_config.get_agent_manager()
            agent = mgr.get_agent(agent_id)
        except Exception:
            return True  # agent_config unavailable → no filtering

        if agent is None:
            return True

        # Allow-list takes precedence (like OpenClaw's tools.allow)
        if agent.tools:
            return tool.name in agent.tools

        # Deny-list
        if agent.tools_blocked:
            return tool.name not in agent.tools_blocked

        return True


# ============================================================================
# 3. Hooks — before_tool_call / after_tool_call (OpenClaw-style)
# ============================================================================


@dataclass
class ToolCallContext:
    """Context passed to hooks during tool execution."""
    tool_name: str
    arguments: Dict[str, Any]
    session_id: str = "default"
    read_only: bool = False
    round_number: int = 0
    call_history: Set[str] = field(default_factory=set)
    # Mutable: hooks can modify arguments or set abort/result
    modified_arguments: Optional[Dict[str, Any]] = None
    abort: bool = False
    abort_reason: str = ""
    override_result: Optional[str] = None


class BeforeToolHook(ABC):
    """Hook called before tool execution.
    
    Can:
    - Modify arguments (set ctx.modified_arguments)
    - Block execution (set ctx.abort = True)
    - Provide cached/override result (set ctx.override_result)
    """
    
    @property
    def priority(self) -> int:
        """Lower = runs first. Default 100."""
        return 100

    @abstractmethod
    def before(self, ctx: ToolCallContext, tool: ToolDefinition) -> None:
        """Called before tool execution. Modify ctx to affect behavior."""
        ...


class AfterToolHook(ABC):
    """Hook called after tool execution.

    Can:
    - Transform the result
    - Log/record metrics
    - Trigger side effects
    """

    @property
    def priority(self) -> int:
        return 100

    @abstractmethod
    def after(
        self,
        ctx: ToolCallContext,
        tool: ToolDefinition,
        result: str,
        execution_time_ms: float,
    ) -> str:
        """Called after tool execution. Return (possibly modified) result."""
        ...


class ReadOnlyHook(BeforeToolHook):
    """Block write tools in read-only mode, returning YAML preview.

    OpenClaw equivalent: owner-only policy hook that prevents mutation.
    """

    @property
    def priority(self) -> int:
        return 10  # Run early

    def before(self, ctx: ToolCallContext, tool: ToolDefinition) -> None:
        if not ctx.read_only:
            return
        if tool.read_only:
            return
        # Write tool in read-only session → override with YAML preview
        try:
            import yaml
            yaml_output = yaml.dump(
                ctx.arguments,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        except ImportError:
            yaml_output = json.dumps(ctx.arguments, indent=2, ensure_ascii=False)
        try:
            import api as _api
            read_only_note = _api.tr("read_only_instruction") + _api.tr("read_only_note")
        except Exception:
            read_only_note = "Read-only mode: operation not executed."
        ctx.override_result = json.dumps(
            {
                "status": "read_only",
                "message": f"Read-only mode: '{tool.name}' was NOT executed.",
                "yaml_preview": yaml_output,
                "tool_name": tool.name,
                "IMPORTANT": read_only_note,
            },
            ensure_ascii=False,
            default=str,
        )
        logger.info(f"Read-only mode: blocked write tool '{tool.name}'")


class DuplicateCallHook(BeforeToolHook):
    """Detect and block duplicate tool calls within the same session.

    OpenClaw equivalent: loop detection in runEmbeddedPiAgent.
    """

    @property
    def priority(self) -> int:
        return 20

    def before(self, ctx: ToolCallContext, tool: ToolDefinition) -> None:
        sig = f"{ctx.tool_name}:{json.dumps(ctx.arguments, sort_keys=True)}"
        if sig in ctx.call_history:
            # Read-only tools: return cached result (handled by caller)
            # Write tools: block with message
            if not tool.read_only:
                ctx.abort = True
                ctx.abort_reason = (
                    f"[DUPLICATE] Tool '{tool.name}' already called with same arguments. "
                    "Use the results you already received."
                )
                logger.warning(f"Blocked duplicate write call: {tool.name}")


class LoggingHook(AfterToolHook):
    """Log tool execution results and timing."""

    @property
    def priority(self) -> int:
        return 100

    def after(
        self,
        ctx: ToolCallContext,
        tool: ToolDefinition,
        result: str,
        execution_time_ms: float,
    ) -> str:
        truncated = result[:300] + ("..." if len(result) > 300 else "")
        logger.info(
            f"Tool [{tool.name}] ({execution_time_ms:.0f}ms, "
            f"{'RO' if tool.read_only else 'RW'}): {truncated}"
        )
        return result


class EntityValidationHook(BeforeToolHook):
    """Validate entity_ids before executing tools that reference HA entities.
    
    Prevents hallucinated entity IDs from reaching the HA API.
    """

    @property
    def priority(self) -> int:
        return 50

    def before(self, ctx: ToolCallContext, tool: ToolDefinition) -> None:
        # Only validate for tools that reference entities
        entity_id = ctx.arguments.get("entity_id")
        if not entity_id or not isinstance(entity_id, str):
            return
        # Basic format validation
        if "." not in entity_id:
            ctx.abort = True
            ctx.abort_reason = (
                f"Invalid entity_id format: '{entity_id}'. "
                "Must be in 'domain.name' format (e.g., 'light.living_room')."
            )


# ============================================================================
# 4. Provider Schema Adapters (OpenClaw: toToolDefinitions)
# ============================================================================


class ProviderAdapter(ABC):
    """Converts ToolDefinition[] → provider-specific format.

    OpenClaw equivalent: toToolDefinitions() + pi-tool-definition-adapter.ts
    Each provider may need different JSON Schema transformations.
    """

    @abstractmethod
    def format_tool(self, tool: ToolDefinition) -> Dict[str, Any]:
        """Convert a single ToolDefinition to provider-specific format."""
        ...

    def format_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert multiple ToolDefinitions. Override for batch operations."""
        return [self.format_tool(t) for t in tools]


class AnthropicAdapter(ProviderAdapter):
    """Format tools for Anthropic Claude API.

    Format: {name, description, input_schema}
    Schema: Keeps all JSON Schema constraints (Anthropic handles them well).
    """

    def format_tool(self, tool: ToolDefinition) -> Dict[str, Any]:
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.parameters,
        }


class OpenAIAdapter(ProviderAdapter):
    """Format tools for OpenAI-compatible APIs (OpenAI, GitHub, NVIDIA, Groq, Mistral, ...).

    Format: {type: "function", function: {name, description, parameters}}
    Schema: Standard JSON Schema — normalizes union types if provider requires.
    """

    def format_tool(self, tool: ToolDefinition) -> Dict[str, Any]:
        # For compact tier, use shorter description if available
        desc = tool.compact_description if tool.compact_description else tool.description
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": desc,
                "parameters": tool.parameters,
            },
        }


class XaiAdapter(ProviderAdapter):
    """Format tools for xAI/Grok models.

    Format: same as OpenAI (function calling).
    Schema: Must strip validation keywords unsupported by xAI that cause 400 errors.
    This is OpenClaw's stripXaiUnsupportedKeywords() equivalent.

    xAI models can appear:
      - directly (provider 'xai')
      - behind OpenRouter (model id prefix 'x-ai/')
      - behind Venice (model id contains 'grok')
    """

    _BLOCKED_KEYS = {
        "minLength", "maxLength", "minItems", "maxItems",
        "minContains", "maxContains", "minProperties", "maxProperties",
    }

    @classmethod
    def _strip_unsupported(cls, obj: Any) -> Any:
        """Recursively strip xAI-unsupported JSON Schema keywords."""
        if isinstance(obj, dict):
            return {
                k: cls._strip_unsupported(v)
                for k, v in obj.items()
                if k not in cls._BLOCKED_KEYS
            }
        if isinstance(obj, list):
            return [cls._strip_unsupported(v) for v in obj]
        return obj

    def format_tool(self, tool: ToolDefinition) -> Dict[str, Any]:
        desc = tool.compact_description if tool.compact_description else tool.description
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": desc,
                "parameters": self._strip_unsupported(tool.parameters),
            },
        }


class GeminiAdapter(ProviderAdapter):
    """Format tools for Google Gemini API.

    Format: types.Tool(function_declarations=[...])
    Schema: Must strip validation keywords that cause Gemini SDK errors:
    minimum, maximum, format, pattern, minItems, maxItems, etc.

    This is OpenClaw's _sanitize_gemini_schema equivalent.
    """

    _BLOCKED_KEYS = {
        "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
        "multipleOf", "minItems", "maxItems", "minLength", "maxLength",
        "pattern", "format", "examples", "default",
    }

    @classmethod
    def _sanitize_schema(cls, obj: Any) -> Any:
        """Recursively strip blocked JSON Schema keywords for Gemini."""
        if isinstance(obj, dict):
            return {
                k: cls._sanitize_schema(v)
                for k, v in obj.items()
                if k not in cls._BLOCKED_KEYS
            }
        if isinstance(obj, list):
            return [cls._sanitize_schema(v) for v in obj]
        return obj

    def format_tool(self, tool: ToolDefinition) -> Dict[str, Any]:
        """Return dict suitable for types.FunctionDeclaration()."""
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters_json_schema": self._sanitize_schema(tool.parameters),
        }

    def format_tools_as_gemini_type(self, tools_iterable: List[ToolDefinition]):
        """Convert to actual Gemini types.Tool object (requires google SDK)."""
        from google.genai import types
        declarations = []
        for t in tools_iterable:
            formatted = self.format_tool(t)
            declarations.append(
                types.FunctionDeclaration(
                    name=formatted["name"],
                    description=formatted["description"],
                    parameters_json_schema=formatted["parameters_json_schema"],
                )
            )
        return types.Tool(function_declarations=declarations)


# Adapter instances (singletons)
_ADAPTERS: Dict[str, ProviderAdapter] = {
    "anthropic": AnthropicAdapter(),
    "openai": OpenAIAdapter(),
    "gemini": GeminiAdapter(),
    "xai": XaiAdapter(),
}

# OpenAI-compatible providers share the same adapter
for _p in ("github", "nvidia", "groq", "mistral", "deepseek", "openrouter",
           "perplexity", "siliconflow", "dashscope", "moonshot", "zhipu",
           "minimax", "volcengine", "ollama", "openai_compatible", "aihubmix",
           "openai_codex"):
    _ADAPTERS[_p] = _ADAPTERS["openai"]


def get_adapter(provider: str, model: str = "") -> ProviderAdapter:
    """Get the schema adapter for a provider.

    Falls back to OpenAI adapter for unknown providers (most common format).
    Detects xAI/Grok models behind OpenRouter or other gateways.
    """
    # Detect xAI behind OpenRouter/gateways (OpenClaw pattern)
    model_lower = model.lower() if model else ""
    if model_lower.startswith("x-ai/") or "grok" in model_lower:
        return _ADAPTERS["xai"]
    return _ADAPTERS.get(provider, _ADAPTERS["openai"])


# ============================================================================
# 5. ToolRegistry — central manager (OpenClaw: collectTools + pipeline)
# ============================================================================


class ToolRegistry:
    """Central tool registry managing the full tool lifecycle.

    Mirrors OpenClaw's tool pipeline:
    1. register() — collect tools
    2. get_tools() — filter by policy chain
    3. format_for_provider() — normalize schema per provider
    4. execute() — run with hooks (before/after)

    Usage:
        registry = ToolRegistry()
        registry.register(my_tool)
        registry.add_policy(FileAccessPolicy())
        registry.add_before_hook(ReadOnlyHook())

        # Get formatted tools for Anthropic
        tools = registry.format_for_provider("anthropic", context={...})

        # Execute a tool
        result = registry.execute("get_entities", {"domain": "light"}, context)
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._policies: List[ToolPolicy] = []
        self._before_hooks: List[BeforeToolHook] = []
        self._after_hooks: List[AfterToolHook] = []
        # Tool call metrics
        self._call_count: Dict[str, int] = {}
        self._total_time_ms: Dict[str, float] = {}

    # ── Registration ──────────────────────────────────────────────────

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered — overwriting")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name} (category={tool.category.value})")

    def register_many(self, tools: List[ToolDefinition]) -> None:
        """Register multiple tools at once."""
        for tool in tools:
            self.register(tool)

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        self._tools.pop(name, None)

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self._tools.get(name)

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    @property
    def all_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    # ── Policies ──────────────────────────────────────────────────────

    def add_policy(self, policy: ToolPolicy) -> None:
        """Add a policy to the filter chain."""
        self._policies.append(policy)
        logger.debug(f"Added policy: {policy.name}")

    def clear_policies(self) -> None:
        """Remove all policies."""
        self._policies.clear()

    # ── Hooks ─────────────────────────────────────────────────────────

    def add_before_hook(self, hook: BeforeToolHook) -> None:
        """Add a before-execution hook."""
        self._before_hooks.append(hook)
        self._before_hooks.sort(key=lambda h: h.priority)

    def add_after_hook(self, hook: AfterToolHook) -> None:
        """Add an after-execution hook."""
        self._after_hooks.append(hook)
        self._after_hooks.sort(key=lambda h: h.priority)

    # ── Filtering (OpenClaw's policy pipeline) ────────────────────────

    def get_tools(self, context: Optional[Dict[str, Any]] = None) -> List[ToolDefinition]:
        """Get tools filtered through the policy pipeline.

        Context keys used by built-in policies:
        - tier: "compact" | "extended" | "full" (default: "full")
        - intent_tools: None (all) | [] (none) | ["name", ...] (subset)
        - enable_file_access: bool
        - blocked_categories: Set[ToolCategory]
        """
        ctx = context or {}
        result = []
        for tool in self._tools.values():
            allowed = all(p.allows(tool, ctx) for p in self._policies)
            if allowed:
                result.append(tool)
        return result

    def get_tools_by_category(
        self,
        category: ToolCategory,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ToolDefinition]:
        """Get tools in a specific category, filtered by policies."""
        return [t for t in self.get_tools(context) if t.category == category]

    def get_tools_by_label(
        self,
        label: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ToolDefinition]:
        """Get tools with a specific label, filtered by policies."""
        return [t for t in self.get_tools(context) if label in t.labels]

    # ── Provider formatting (OpenClaw's toToolDefinitions) ────────────

    def format_for_provider(
        self,
        provider: str,
        context: Optional[Dict[str, Any]] = None,
        model: str = "",
    ) -> List[Dict[str, Any]]:
        """Get tools formatted for a specific provider, after policy filtering.

        This is the main entry point for getting tool schemas to send to the LLM.
        Equivalent to OpenClaw's full pipeline: collect → filter → normalize.

        Args:
            provider: Provider name ('anthropic', 'openai', 'openrouter', ...)
            context: Policy context dict
            model: Model ID (used to detect xAI/Grok behind gateways like OpenRouter)
        """
        filtered = self.get_tools(context)
        adapter = get_adapter(provider, model)
        return adapter.format_tools(filtered)

    def format_for_gemini(
        self,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Get tools formatted as a Gemini types.Tool object."""
        filtered = self.get_tools(context)
        adapter = _ADAPTERS.get("gemini")
        if isinstance(adapter, GeminiAdapter):
            return adapter.format_tools_as_gemini_type(filtered)
        raise RuntimeError("Gemini adapter not available")

    # ── Execution (OpenClaw's execute with hooks) ─────────────────────

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[ToolCallContext] = None,
    ) -> str:
        """Execute a tool with before/after hooks.

        OpenClaw pipeline:
        1. Run before_tool_call hooks (can modify args, abort, override)
        2. Execute the tool function
        3. Run after_tool_call hooks (can transform result)
        4. Return result string

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments dict
            context: Optional execution context (session, read-only, etc.)

        Returns:
            Result string (JSON) from tool execution
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        # Build context if not provided
        if context is None:
            context = ToolCallContext(tool_name=tool_name, arguments=arguments)
        else:
            context.tool_name = tool_name
            context.arguments = arguments

        # --- Before hooks ---
        for hook in self._before_hooks:
            try:
                hook.before(context, tool)
            except Exception as e:
                logger.error(f"Before hook {hook.__class__.__name__} failed: {e}")
            if context.abort:
                logger.info(f"Tool '{tool_name}' aborted by hook: {context.abort_reason}")
                return json.dumps({"error": context.abort_reason})
            if context.override_result is not None:
                return context.override_result

        # Use modified arguments if a hook changed them
        final_args = context.modified_arguments or context.arguments

        # --- Execute ---
        start_time = time.time()
        try:
            result = tool.execute(final_args)
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution error: {e}")
            result = json.dumps({"error": str(e)})
        execution_time_ms = (time.time() - start_time) * 1000

        # Track metrics
        self._call_count[tool_name] = self._call_count.get(tool_name, 0) + 1
        self._total_time_ms[tool_name] = (
            self._total_time_ms.get(tool_name, 0) + execution_time_ms
        )

        # --- After hooks ---
        for hook in self._after_hooks:
            try:
                result = hook.after(context, tool, result, execution_time_ms)
            except Exception as e:
                logger.error(f"After hook {hook.__class__.__name__} failed: {e}")

        return result

    # ── User-friendly descriptions ────────────────────────────────────

    def get_user_description(self, tool_name: str) -> str:
        """Get Italian user-friendly label for UI status messages."""
        tool = self._tools.get(tool_name)
        if tool:
            return tool.user_description
        return tool_name.replace("_", " ").title()

    def get_user_descriptions(self) -> Dict[str, str]:
        """Get all user descriptions as a dict (tool_name → description)."""
        return {
            name: tool.user_description
            for name, tool in self._tools.items()
        }

    # ── Metrics ───────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        return {
            "registered_tools": len(self._tools),
            "policies": len(self._policies),
            "before_hooks": len(self._before_hooks),
            "after_hooks": len(self._after_hooks),
            "call_counts": dict(self._call_count),
            "total_time_ms": dict(self._total_time_ms),
            "categories": {
                cat.value: len([t for t in self._tools.values() if t.category == cat])
                for cat in ToolCategory
                if any(t.category == cat for t in self._tools.values())
            },
        }

    # ── Bulk registration from legacy format ──────────────────────────

    @staticmethod
    def from_legacy_tools(
        tool_descriptions: List[Dict[str, Any]],
        execute_fn: Callable[[str, Dict[str, Any]], str],
        user_descriptions: Optional[Dict[str, str]] = None,
        write_tools: Optional[Set[str]] = None,
        compact_tools: Optional[Set[str]] = None,
        extended_tools: Optional[Set[str]] = None,
        category_map: Optional[Dict[str, ToolCategory]] = None,
    ) -> "ToolRegistry":
        """Create a ToolRegistry from the legacy HA_TOOLS_DESCRIPTION format.

        This is the migration bridge: takes the existing flat list of tool dicts
        and wraps them in ToolDefinition objects with proper categories and flags.

        Args:
            tool_descriptions: Legacy HA_TOOLS_DESCRIPTION list
            execute_fn: The legacy execute_tool(name, args) function
            user_descriptions: Legacy TOOL_DESCRIPTIONS dict
            write_tools: Set of tool names that perform write operations
            compact_tools: Tools included in compact tier
            extended_tools: Tools included in extended tier
            category_map: Map tool name → ToolCategory
        """
        registry = ToolRegistry()
        user_desc = user_descriptions or {}
        writes = write_tools or set()
        compacts = compact_tools or set()
        extendeds = extended_tools or set()
        cats = category_map or {}

        # Default category inference from tool name
        def _infer_category(name: str) -> ToolCategory:
            if name in cats:
                return cats[name]
            if name.startswith("get_") or name.startswith("search_") or name == "get_entity_state":
                return ToolCategory.QUERY
            if name.startswith("create_automation") or name.startswith("update_automation") or name.startswith("delete_automation"):
                return ToolCategory.AUTOMATION
            if name.startswith("create_script") or name.startswith("update_script") or name.startswith("delete_script"):
                return ToolCategory.AUTOMATION
            if "dashboard" in name:
                return ToolCategory.DASHBOARD
            if name == "call_service" or name == "activate_scene":
                return ToolCategory.CONTROL
            if name in ("read_config_file", "write_config_file", "list_config_files", "check_config"):
                return ToolCategory.CONFIG
            if name in ("send_notification",):
                return ToolCategory.NOTIFICATION
            if name in ("manage_helpers", "manage_areas", "manage_entity"):
                return ToolCategory.HELPER
            if name in ("create_backup", "get_repairs", "dismiss_repair", "get_ha_logs",
                        "fire_event", "get_logged_users", "get_error_log", "manage_statistics"):
                return ToolCategory.SYSTEM
            if name in ("browse_media",):
                return ToolCategory.MEDIA
            if name in ("shopping_list",):
                return ToolCategory.HELPER
            return ToolCategory.QUERY

        for td in tool_descriptions:
            name = td["name"]
            
            # Create a closure that captures the current tool name
            def _make_executor(tool_name: str):
                def _exec(args: Dict[str, Any]) -> str:
                    return execute_fn(tool_name, args)
                return _exec

            cat = _infer_category(name)
            is_read_only = name not in writes

            tool_def = ToolDefinition(
                name=name,
                description=td["description"],
                parameters=td.get("parameters", {"type": "object", "properties": {}}),
                execute=_make_executor(name),
                category=cat,
                read_only=is_read_only,
                user_description=user_desc.get(name, ""),
                tier_compact=name in compacts,
                tier_extended=name in extendeds or name in compacts,
            )
            registry.register(tool_def)

        return registry


# ============================================================================
# 6. Global singleton
# ============================================================================


_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create the global ToolRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        # Add default policies (order mirrors OpenClaw's 7-step pipeline)
        _registry.add_policy(FileAccessPolicy())
        _registry.add_policy(TierPolicy())
        _registry.add_policy(IntentPolicy())
        _registry.add_policy(CategoryPolicy())
        _registry.add_policy(AgentToolPolicy())
        # Add default hooks
        _registry.add_before_hook(ReadOnlyHook())
        _registry.add_before_hook(EntityValidationHook())
        _registry.add_before_hook(DuplicateCallHook())
        _registry.add_after_hook(LoggingHook())
        logger.info("ToolRegistry initialized with default policies and hooks")
    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None


def initialize_from_legacy() -> ToolRegistry:
    """Initialize the global registry from legacy tools.py definitions.

    Call this once at startup to bridge the existing tool system into
    the new registry architecture.

    Returns the populated registry.
    """
    import tools as _tools_module

    write_tools = getattr(_tools_module, "WRITE_TOOLS", set())
    write_when_not_list = getattr(_tools_module, "WRITE_WHEN_NOT_LIST", set())
    all_writes = write_tools | write_when_not_list

    # Extract compact/extended tool names
    compact_names = {t["name"] for t in getattr(_tools_module, "HA_TOOLS_COMPACT", [])}
    extended_names = {t["name"] for t in getattr(_tools_module, "HA_TOOLS_EXTENDED", [])}

    user_desc = getattr(_tools_module, "TOOL_DESCRIPTIONS", {})

    registry = get_registry()

    # Register from legacy format using the bridge
    temp = ToolRegistry.from_legacy_tools(
        tool_descriptions=_tools_module.HA_TOOLS_DESCRIPTION,
        execute_fn=_tools_module.execute_tool,
        user_descriptions=user_desc,
        write_tools=all_writes,
        compact_tools=compact_names,
        extended_tools=extended_names,
    )

    # Move tools into the global registry
    for tool in temp._tools.values():
        registry.register(tool)

    logger.info(
        f"ToolRegistry initialized from legacy: {registry.tool_count} tools, "
        f"{len(compact_names)} compact, {len(extended_names)} extended"
    )
    return registry
