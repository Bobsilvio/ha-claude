"""Model Catalog — centralised model metadata with capabilities.

Inspired by OpenClaw's model-catalog.ts: every model known to the system 
gets a ModelCatalogEntry with provider, capabilities (vision, reasoning, 
document upload), context window, max output tokens and pricing tier.

The catalog is:
1. Built from a rich static table (always available, zero network calls).
2. Optionally enriched at runtime by /v1/models discovery (NVIDIA, Ollama, 
   GitHub Copilot …).
3. Queried by the agent system, the fallback engine and the UI to make 
   informed decisions (e.g. "pick the cheapest model that supports vision").

Usage:
    from model_catalog import get_catalog, ModelCapability

    catalog = get_catalog()
    entry = catalog.get_entry("anthropic", "claude-opus-4-6")
    if entry and ModelCapability.VISION in entry.capabilities:
        ...  # model supports images
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class ModelCapability(Enum):
    """What a model can accept / produce."""
    TEXT = auto()
    VISION = auto()       # image input
    DOCUMENT = auto()     # PDF / file input
    REASONING = auto()    # extended thinking / chain-of-thought
    TOOL_USE = auto()     # native function calling
    CODE = auto()         # code-optimised
    STREAMING = auto()    # supports streaming responses


class PricingTier(Enum):
    """Rough cost bucket — used for fallback ordering."""
    FREE = "free"
    CHEAP = "cheap"         # < $1 / 1M tokens
    STANDARD = "standard"   # $1-$10 / 1M tokens
    PREMIUM = "premium"     # $10-$30 / 1M tokens
    ULTRA = "ultra"         # > $30 / 1M tokens


class ThinkingLevel(Enum):
    """Extended-thinking / reasoning budget."""
    OFF = "off"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ADAPTIVE = "adaptive"


@dataclass
class ModelCatalogEntry:
    """Rich metadata for a single model."""
    id: str                       # technical model id (e.g. "claude-opus-4-6")
    provider: str                 # provider key (e.g. "anthropic")
    name: str = ""                # human-friendly display name
    capabilities: Set[ModelCapability] = field(default_factory=lambda: {ModelCapability.TEXT, ModelCapability.STREAMING})
    context_window: int = 0       # 0 = unknown
    max_output_tokens: int = 0    # 0 = unknown / unlimited
    reasoning: bool = False       # supports extended thinking
    pricing_tier: PricingTier = PricingTier.STANDARD
    thinking_default: ThinkingLevel = ThinkingLevel.OFF
    aliases: List[str] = field(default_factory=list)  # shorthand names
    deprecated: bool = False
    # Additional metadata
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def supports_vision(self) -> bool:
        return ModelCapability.VISION in self.capabilities

    @property
    def supports_tools(self) -> bool:
        return ModelCapability.TOOL_USE in self.capabilities

    @property
    def supports_reasoning(self) -> bool:
        return self.reasoning or ModelCapability.REASONING in self.capabilities

    def key(self) -> str:
        return f"{self.provider}/{self.id}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _caps(*args: ModelCapability) -> Set[ModelCapability]:
    """Shorthand to build a capabilities set (always includes TEXT + STREAMING)."""
    return {ModelCapability.TEXT, ModelCapability.STREAMING} | set(args)

_T  = ModelCapability.TOOL_USE
_V  = ModelCapability.VISION
_R  = ModelCapability.REASONING
_D  = ModelCapability.DOCUMENT
_C  = ModelCapability.CODE

# ---------------------------------------------------------------------------
# Static catalog — the authoritative baseline
# ---------------------------------------------------------------------------

_STATIC_CATALOG: List[ModelCatalogEntry] = [
    # ========================  ANTHROPIC  ========================
    ModelCatalogEntry("claude-opus-4-6", "anthropic", "Claude Opus 4.6",
        _caps(_T, _V, _R, _D), 200_000, 32_000, True, PricingTier.ULTRA,
        ThinkingLevel.ADAPTIVE, ["opus-4.6"]),
    ModelCatalogEntry("claude-sonnet-4-6", "anthropic", "Claude Sonnet 4.6",
        _caps(_T, _V, _R, _D), 200_000, 16_000, True, PricingTier.PREMIUM,
        ThinkingLevel.ADAPTIVE, ["sonnet-4.6"]),
    ModelCatalogEntry("claude-haiku-4-5-20251001", "anthropic", "Claude Haiku 4.5",
        _caps(_T, _V, _D), 200_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, ["haiku-4.5"]),
    ModelCatalogEntry("claude-sonnet-4-5-20250929", "anthropic", "Claude Sonnet 4.5",
        _caps(_T, _V, _R, _D), 200_000, 16_000, True, PricingTier.PREMIUM,
        ThinkingLevel.LOW, ["sonnet-4.5"], deprecated=True),
    ModelCatalogEntry("claude-opus-4-5-20251101", "anthropic", "Claude Opus 4.5",
        _caps(_T, _V, _R, _D), 200_000, 32_000, True, PricingTier.ULTRA,
        ThinkingLevel.LOW, ["opus-4.5"], deprecated=True),
    ModelCatalogEntry("claude-opus-4-1-20250805", "anthropic", "Claude Opus 4.1",
        _caps(_T, _V, _R, _D), 200_000, 32_000, True, PricingTier.ULTRA,
        ThinkingLevel.LOW, ["opus-4.1"], deprecated=True),
    ModelCatalogEntry("claude-sonnet-4-20250514", "anthropic", "Claude Sonnet 4",
        _caps(_T, _V, _R, _D), 200_000, 16_000, True, PricingTier.STANDARD,
        ThinkingLevel.LOW, ["sonnet-4"], deprecated=True),
    ModelCatalogEntry("claude-opus-4-20250514", "anthropic", "Claude Opus 4",
        _caps(_T, _V, _R, _D), 200_000, 32_000, True, PricingTier.ULTRA,
        ThinkingLevel.LOW, ["opus-4"], deprecated=True),

    # ========================  OPENAI  ========================
    ModelCatalogEntry("gpt-5.2", "openai", "GPT-5.2",
        _caps(_T, _V, _R), 200_000, 32_000, True, PricingTier.ULTRA,
        ThinkingLevel.ADAPTIVE, ["gpt5.2"]),
    ModelCatalogEntry("gpt-5.2-mini", "openai", "GPT-5.2 Mini",
        _caps(_T, _V, _R), 128_000, 16_000, True, PricingTier.STANDARD,
        ThinkingLevel.LOW, ["gpt5.2-mini"]),
    ModelCatalogEntry("gpt-5", "openai", "GPT-5",
        _caps(_T, _V, _R), 128_000, 16_000, True, PricingTier.PREMIUM,
        ThinkingLevel.LOW, ["gpt5"]),
    ModelCatalogEntry("gpt-4o", "openai", "GPT-4o",
        _caps(_T, _V), 128_000, 16_384, False, PricingTier.STANDARD,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("gpt-4o-mini", "openai", "GPT-4o Mini",
        _caps(_T, _V), 128_000, 16_384, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("gpt-4-turbo", "openai", "GPT-4 Turbo",
        _caps(_T, _V), 128_000, 4_096, False, PricingTier.STANDARD,
        ThinkingLevel.OFF, [], deprecated=True),
    ModelCatalogEntry("o3", "openai", "o3",
        _caps(_T, _R), 200_000, 100_000, True, PricingTier.ULTRA,
        ThinkingLevel.HIGH, []),
    ModelCatalogEntry("o3-mini", "openai", "o3-mini",
        _caps(_T, _R), 200_000, 65_536, True, PricingTier.PREMIUM,
        ThinkingLevel.MEDIUM, []),
    ModelCatalogEntry("o1", "openai", "o1",
        _caps(_T, _R), 200_000, 100_000, True, PricingTier.ULTRA,
        ThinkingLevel.HIGH, [], deprecated=True),

    # ========================  GOOGLE  ========================
    ModelCatalogEntry("gemini-2.0-flash", "google", "Gemini 2.0 Flash",
        _caps(_T, _V, _D), 1_000_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, ["flash-2.0"]),
    ModelCatalogEntry("gemini-2.5-pro", "google", "Gemini 2.5 Pro",
        _caps(_T, _V, _R, _D), 1_000_000, 65_536, True, PricingTier.PREMIUM,
        ThinkingLevel.LOW, ["gemini-pro"]),
    ModelCatalogEntry("gemini-2.5-flash", "google", "Gemini 2.5 Flash",
        _caps(_T, _V, _R, _D), 1_000_000, 65_536, True, PricingTier.STANDARD,
        ThinkingLevel.LOW, ["gemini-flash"]),

    # ========================  GROQ  ========================
    ModelCatalogEntry("llama-3.3-70b-versatile", "groq", "Llama 3.3 70B",
        _caps(_T), 128_000, 32_768, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("llama-3.1-8b-instant", "groq", "Llama 3.1 8B Instant",
        _caps(_T), 128_000, 8_000, False, PricingTier.FREE,
        ThinkingLevel.OFF, []),

    # ========================  MISTRAL  ========================
    ModelCatalogEntry("mistral-large-latest", "mistral", "Mistral Large",
        _caps(_T, _V), 128_000, 8_192, False, PricingTier.STANDARD,
        ThinkingLevel.OFF, ["mistral-large"]),
    ModelCatalogEntry("mistral-medium", "mistral", "Mistral Medium",
        _caps(_T), 32_000, 8_192, False, PricingTier.STANDARD,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("mistral-small-latest", "mistral", "Mistral Small",
        _caps(_T), 32_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, ["mistral-small"]),

    # ========================  DEEPSEEK  ========================
    ModelCatalogEntry("deepseek-chat", "deepseek", "DeepSeek Chat (V3)",
        _caps(_T), 128_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, ["deepseek-v3"]),
    ModelCatalogEntry("deepseek-r1", "deepseek", "DeepSeek R1",
        _caps(_T, _R), 128_000, 8_192, True, PricingTier.CHEAP,
        ThinkingLevel.LOW, []),

    # ========================  MOONSHOT  ========================
    ModelCatalogEntry("kimi-k2.5", "moonshot", "Kimi K2.5",
        _caps(_T), 128_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("kimi-k2", "moonshot", "Kimi K2",
        _caps(_T), 128_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),

    # ========================  PERPLEXITY  ========================
    ModelCatalogEntry("sonar-pro", "perplexity", "Sonar Pro",
        _caps(), 128_000, 8_192, False, PricingTier.STANDARD,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("sonar", "perplexity", "Sonar",
        _caps(), 128_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("sonar-reasoning-pro", "perplexity", "Sonar Reasoning Pro",
        _caps(_R), 128_000, 8_192, True, PricingTier.PREMIUM,
        ThinkingLevel.LOW, []),

    # ========================  MINIMAX  ========================
    ModelCatalogEntry("MiniMax-M2.1", "minimax", "MiniMax M2.1",
        _caps(_T), 128_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("MiniMax-M2", "minimax", "MiniMax M2",
        _caps(_T), 128_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),

    # ========================  ZHIPU  ========================
    ModelCatalogEntry("glm-4-flash", "zhipu", "GLM-4 Flash",
        _caps(_T), 128_000, 4_096, False, PricingTier.FREE,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("glm-4-plus", "zhipu", "GLM-4 Plus",
        _caps(_T, _V), 128_000, 4_096, False, PricingTier.STANDARD,
        ThinkingLevel.OFF, []),

    # ========================  DASHSCOPE  ========================
    ModelCatalogEntry("qwen-max", "dashscope", "Qwen Max",
        _caps(_T, _V), 128_000, 8_192, False, PricingTier.STANDARD,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("qwen-plus", "dashscope", "Qwen Plus",
        _caps(_T), 128_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),
    ModelCatalogEntry("qwen-turbo", "dashscope", "Qwen Turbo",
        _caps(_T), 128_000, 8_192, False, PricingTier.CHEAP,
        ThinkingLevel.OFF, []),
]


# ---------------------------------------------------------------------------
# Provider model routing — UI dropdown model lists.
#
# OpenClaw-style: API providers populate their list dynamically via their own
# get_available_models() at startup.  Only providers that lack a standard
# discovery API keep a static fallback here.
#
# To add/remove models for an API provider → edit that provider's
# get_available_models() in providers/<name>.py — NOT this dict.
# ---------------------------------------------------------------------------

_PROVIDER_MODELS: Dict[str, List[str]] = {
    # --- Dynamic providers (populated at runtime from providers/*.py) ---
    # They start empty; api.py patches them with get_available_models() results.
    "anthropic": [],
    "openai": [],
    "google": [],
    "nvidia": [],
    "github": [],
    "groq": [],
    "mistral": [],
    "openrouter": [],
    "deepseek": [],
    "minimax": [],
    "aihubmix": [],
    "siliconflow": [],
    "volcengine": [],
    "dashscope": [],
    "moonshot": [],
    "zhipu": [],
    "perplexity": [],

    # --- Ollama: populated live from /api/tags ---
    "ollama": [],

    # --- Web / special providers (no standard discovery API) ---
    # GitHub Copilot (direct OAuth → api.githubcopilot.com)
    "github_copilot": [
        # Claude (via Copilot)
        "claude-opus-4.6-fast", "claude-opus-4.6",
        "claude-sonnet-4.6", "claude-sonnet-4.5", "claude-sonnet-4",
        "claude-haiku-4.5", "claude-opus-4.5",
        # GPT-5 family
        "gpt-5.3-codex", "gpt-5.2-codex", "gpt-5.1-codex-max", "gpt-5.1-codex",
        "gpt-5.1-codex-mini", "gpt-5.1", "gpt-5.2", "gpt-5-mini",
        # GPT-4o family
        "gpt-4o", "gpt-4o-mini", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06",
        "gpt-4o-mini-2024-07-18", "gpt-4o-2024-05-13", "gpt-4-o-preview",
        "gpt-41-copilot",
        # GPT-4.1 / GPT-4 legacy
        "gpt-4.1", "gpt-4.1-2025-04-14", "gpt-4", "gpt-4-0613",
        "gpt-4-0125-preview", "gpt-3.5-turbo", "gpt-3.5-turbo-0613",
        # Gemini (via Copilot)
        "gemini-3.1-pro-preview", "gemini-3-pro-preview", "gemini-3-flash-preview",
        "gemini-2.5-pro",
        # Grok
        "grok-code-fast-1",
        # OSWE (internal Copilot agents)
        "oswe-vscode-prime", "oswe-vscode-secondary",
    ],

    # Claude.ai Web (browser session, no API key)
    "claude_web": [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-opus-4-5-20251101",
        "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5-20251001",
    ],

    # ChatGPT Web (browser session, no API key)
    "chatgpt_web": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.5",
        "gpt-5",
        "gpt-5.2",
        "chatgpt-4o-latest",
        "o1",
        "o3",
        "o3-mini",
        "o4-mini",
    ],

    # Gemini Web (browser session cookies, no API key)
    "gemini_web": [
        "gemini-2.0-flash",
        "gemini-2.5-pro",
        "gemini-2.0-pro-exp",
        "gemini-1.5-pro",
    ],

    # Custom: model name from CUSTOM_MODEL_NAME env var
    "custom": [],
}


# ---------------------------------------------------------------------------
# Alias index — quick lookup by alias
# ---------------------------------------------------------------------------

def _build_alias_index(entries: List[ModelCatalogEntry]) -> Dict[str, Tuple[str, str]]:
    """Map lowercase alias → (provider, model_id)."""
    idx: Dict[str, Tuple[str, str]] = {}
    for e in entries:
        for a in e.aliases:
            idx[a.lower()] = (e.provider, e.id)
    return idx


# ---------------------------------------------------------------------------
# ModelCatalog class
# ---------------------------------------------------------------------------

_CATALOG_BLOCKLIST_FILE = "/config/amira/model_blocklist.json"


class ModelCatalog:
    """Thread-safe model catalog with static + dynamic entries."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # keyed by "provider/model_id"
        self._entries: Dict[str, ModelCatalogEntry] = {}
        self._alias_index: Dict[str, Tuple[str, str]] = {}
        # Provider → [model_ids] for UI dropdown (single source of truth)
        self._provider_models: Dict[str, List[str]] = {
            k: list(v) for k, v in _PROVIDER_MODELS.items()
        }
        self._dynamic_ts: float = 0.0  # last dynamic refresh timestamp
        # Persistent blocklist: models removed at runtime (survive refreshes and restarts)
        # keyed by "provider/model_id"
        self._blocklisted: set = set()
        self._load_static()
        self._restore_blocklist()  # re-apply blocklist persisted in previous sessions

    # -- bootstrap --

    def _load_static(self) -> None:
        """Load the built-in static catalog + auto-populate from provider routing."""
        for e in _STATIC_CATALOG:
            self._entries[e.key()] = e
        self._alias_index = _build_alias_index(_STATIC_CATALOG)
        # Auto-create minimal entries for models in _PROVIDER_MODELS not yet
        # covered by the rich _STATIC_CATALOG.
        auto = 0
        for provider, model_ids in _PROVIDER_MODELS.items():
            for mid in model_ids:
                key = f"{provider}/{mid}"
                if key not in self._entries:
                    self._entries[key] = ModelCatalogEntry(
                        id=mid, provider=provider, name=mid,
                        capabilities={ModelCapability.TEXT, ModelCapability.STREAMING},
                    )
                    auto += 1
        logger.debug(
            f"ModelCatalog: {len(_STATIC_CATALOG)} rich + {auto} auto entries "
            f"across {len(self._provider_models)} providers"
        )

    # -- blocklist persistence --

    def _restore_blocklist(self) -> None:
        """Re-apply the blocklist persisted from previous sessions.

        Reads the shared /config/amira/model_blocklist.json file and,
        for every provider key that is NOT "nvidia" (managed by api.py),
        calls remove_model() to purge each entry from the catalog.
        Safe to call at startup before any threads are active.
        """
        try:
            if not os.path.isfile(_CATALOG_BLOCKLIST_FILE):
                return
            with open(_CATALOG_BLOCKLIST_FILE, "r") as fh:
                data = json.load(fh) or {}
            restored = 0
            for provider, model_ids in data.items():
                if provider == "nvidia":
                    continue  # managed exclusively by api.py
                if not isinstance(model_ids, list):
                    continue
                for mid in model_ids:
                    if isinstance(mid, str) and mid.strip():
                        self.remove_model(provider, mid.strip(), _persist=False)
                        restored += 1
            if restored:
                logger.info(f"ModelCatalog: restored {restored} blocklisted model(s) from disk")
        except Exception as exc:
            logger.warning(f"ModelCatalog: could not restore blocklist: {exc}")

    def _persist_blocklist(self) -> None:
        """Write the in-memory blocklist (excluding nvidia) to disk.

        Reads the existing file first so the nvidia section managed by
        api.py is preserved.  Called under self._lock — must not block.
        """
        try:
            # Build {provider: [model_id, ...]} from _blocklisted, skip nvidia
            by_provider: Dict[str, List[str]] = {}
            for key in self._blocklisted:
                if "/" not in key:
                    continue
                provider, model_id = key.split("/", 1)
                if provider == "nvidia":
                    continue
                by_provider.setdefault(provider, []).append(model_id)

            # Load existing file to preserve the nvidia section
            existing: Dict = {}
            if os.path.isfile(_CATALOG_BLOCKLIST_FILE):
                try:
                    with open(_CATALOG_BLOCKLIST_FILE, "r") as fh:
                        existing = json.load(fh) or {}
                except Exception:
                    pass

            # Merge: keep nvidia unchanged, overwrite our providers
            payload = dict(existing)
            for provider, model_ids in by_provider.items():
                payload[provider] = sorted(set(model_ids))

            os.makedirs(os.path.dirname(_CATALOG_BLOCKLIST_FILE), exist_ok=True)
            with open(_CATALOG_BLOCKLIST_FILE, "w") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(f"ModelCatalog: could not persist blocklist: {exc}")

    # -- queries --

    def get_entry(self, provider: str, model_id: str) -> Optional[ModelCatalogEntry]:
        """Look up a model by provider + id (exact or alias)."""
        key = f"{provider}/{model_id}"
        with self._lock:
            entry = self._entries.get(key)
            if entry:
                return entry
            # Try alias
            alias_hit = self._alias_index.get(model_id.lower())
            if alias_hit:
                return self._entries.get(f"{alias_hit[0]}/{alias_hit[1]}")
        return None

    def resolve_alias(self, raw: str) -> Optional[Tuple[str, str]]:
        """Resolve a model alias to (provider, model_id), or None."""
        with self._lock:
            hit = self._alias_index.get(raw.lower().strip())
            return hit

    def get_all(self, provider: Optional[str] = None, *, 
                include_deprecated: bool = False) -> List[ModelCatalogEntry]:
        """Return all catalog entries, optionally filtered by provider."""
        with self._lock:
            entries = list(self._entries.values())
        if provider:
            entries = [e for e in entries if e.provider == provider]
        if not include_deprecated:
            entries = [e for e in entries if not e.deprecated]
        return sorted(entries, key=lambda e: (e.provider, e.name or e.id))

    def get_providers(self) -> List[str]:
        """Return set of unique providers in the catalog."""
        with self._lock:
            return sorted({e.provider for e in self._entries.values()})

    def find_by_capability(self, cap: ModelCapability, 
                           provider: Optional[str] = None) -> List[ModelCatalogEntry]:
        """Find models with a specific capability."""
        return [e for e in self.get_all(provider) if cap in e.capabilities]

    def find_cheapest_with(self, *caps: ModelCapability,
                           provider: Optional[str] = None) -> Optional[ModelCatalogEntry]:
        """Find the cheapest non-deprecated model supporting all given capabilities."""
        tier_order = [PricingTier.FREE, PricingTier.CHEAP, PricingTier.STANDARD,
                      PricingTier.PREMIUM, PricingTier.ULTRA]
        for tier in tier_order:
            for e in self.get_all(provider):
                if e.pricing_tier == tier and all(c in e.capabilities for c in caps):
                    return e
        return None

    # -- dynamic enrichment --

    def get_provider_models(self) -> Dict[str, List[str]]:
        """Return {provider: [model_ids]} for UI dropdown population.

        This is a deep copy — callers can mutate without affecting the catalog.
        Dynamic patching (Ollama, model_fetcher cache) should use
        merge_provider_models() so the catalog stays in sync.
        """
        with self._lock:
            return {k: list(v) for k, v in self._provider_models.items()}

    def merge_provider_models(self, provider: str, model_ids: List[str]) -> None:
        """Replace the model list for a provider (e.g. after live /api/tags).

        Also creates minimal catalog entries for any new model IDs.
        Blocklisted models are silently skipped so they are never re-added.
        """
        with self._lock:
            filtered = [mid for mid in model_ids
                        if f"{provider}/{mid}" not in self._blocklisted]
            self._provider_models[provider] = filtered
            added = 0
            for mid in filtered:
                key = f"{provider}/{mid}"
                if key not in self._entries:
                    self._entries[key] = ModelCatalogEntry(
                        id=mid, provider=provider, name=mid,
                        capabilities={ModelCapability.TEXT, ModelCapability.STREAMING},
                    )
                    added += 1
            self._dynamic_ts = time.time()
        if added:
            logger.debug(f"ModelCatalog: +{added} entries for {provider} via merge")

    def merge_dynamic(self, provider: str, model_ids: List[str]) -> int:
        """Merge dynamically-discovered model IDs into the catalog.

        Models already present keep their rich metadata.  New models get a
        minimal entry (capabilities = TEXT + STREAMING).  Returns count of
        newly added entries.  Blocklisted models are silently skipped.
        """
        added = 0
        with self._lock:
            for mid in model_ids:
                key = f"{provider}/{mid}"
                if key in self._blocklisted:
                    continue
                if key not in self._entries:
                    self._entries[key] = ModelCatalogEntry(
                        id=mid,
                        provider=provider,
                        name=mid,
                        capabilities={ModelCapability.TEXT, ModelCapability.STREAMING},
                    )
                    added += 1
            self._dynamic_ts = time.time()
        if added:
            logger.debug(f"ModelCatalog: added {added} dynamic entries for {provider}")
        return added

    def remove_model(self, provider: str, model_id: str, _persist: bool = True) -> bool:
        """Remove a single model and add it to the persistent blocklist.

        The blocklist ensures the model is not re-added by subsequent
        merge_provider_models() or merge_dynamic() calls (e.g. auto-refresh).
        Set _persist=False when called from _restore_blocklist() to avoid
        a redundant disk write during startup.
        """
        key = f"{provider}/{model_id}"
        with self._lock:
            self._blocklisted.add(key)
            # Remove from the UI dropdown list
            if provider in self._provider_models:
                try:
                    self._provider_models[provider].remove(model_id)
                except ValueError:
                    pass
            removed = self._entries.pop(key, None) is not None
            if _persist:
                self._persist_blocklist()
        logger.info(f"ModelCatalog: blocklisted {key} (will survive refreshes and restarts)")
        return removed

    # -- thinking defaults --

    def resolve_thinking_default(self, provider: str, model_id: str) -> ThinkingLevel:
        """Resolve the recommended thinking level for a model."""
        entry = self.get_entry(provider, model_id)
        if entry:
            return entry.thinking_default
        # Heuristic fallbacks
        ml = model_id.lower()
        if "o3" in ml or "o1" in ml:
            return ThinkingLevel.HIGH
        if "r1" in ml or "reasoning" in ml:
            return ThinkingLevel.LOW
        return ThinkingLevel.OFF

    # -- stats --

    def stats(self) -> Dict[str, Any]:
        """Return catalog statistics."""
        with self._lock:
            entries = list(self._entries.values())
        providers: Dict[str, int] = {}
        for e in entries:
            providers[e.provider] = providers.get(e.provider, 0) + 1
        return {
            "total_models": len(entries),
            "providers": providers,
            "vision_models": len([e for e in entries if e.supports_vision]),
            "reasoning_models": len([e for e in entries if e.supports_reasoning]),
            "tool_use_models": len([e for e in entries if e.supports_tools]),
            "dynamic_last_refresh": self._dynamic_ts or None,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_catalog: Optional[ModelCatalog] = None
_catalog_lock = threading.Lock()


def get_catalog() -> ModelCatalog:
    """Return the global ModelCatalog singleton (lazy-init, thread-safe)."""
    global _catalog
    if _catalog is not None:
        return _catalog
    with _catalog_lock:
        if _catalog is None:
            _catalog = ModelCatalog()
    return _catalog
