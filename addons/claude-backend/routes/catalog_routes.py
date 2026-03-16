"""Catalog routes blueprint.

Endpoints:
- GET /api/catalog/stats
- GET /api/catalog/models
- GET /api/get_models
"""

import logging
import os
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

catalog_bp = Blueprint('catalog', __name__)


@catalog_bp.route('/api/catalog/stats', methods=['GET'])
def api_catalog_stats():
    """Get model catalog statistics."""
    import api as _api
    if not _api.MODEL_CATALOG_AVAILABLE:
        return jsonify({"success": False, "error": "Model catalog not available"}), 501
    try:
        cat = _api.model_catalog.get_catalog()
        return jsonify({"success": True, "catalog": cat.stats()}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@catalog_bp.route('/api/catalog/models', methods=['GET'])
def api_catalog_models():
    """Get all catalog models (optionally filtered by provider or capability)."""
    import api as _api
    if not _api.MODEL_CATALOG_AVAILABLE:
        return jsonify({"success": False, "error": "Model catalog not available"}), 501
    try:
        cat = _api.model_catalog.get_catalog()
        provider = request.args.get("provider")
        capability = request.args.get("capability")
        include_deprecated = request.args.get("include_deprecated", "false").lower() == "true"

        entries = cat.get_all(provider, include_deprecated=include_deprecated)
        if capability:
            try:
                cap_enum = _api.model_catalog.ModelCapability[capability.upper()]
                entries = [e for e in entries if cap_enum in e.capabilities]
            except KeyError:
                pass

        result = []
        for e in entries:
            result.append({
                "id": e.id,
                "provider": e.provider,
                "name": e.name or e.id,
                "capabilities": [c.name.lower() for c in e.capabilities],
                "context_window": e.context_window,
                "max_output_tokens": e.max_output_tokens,
                "reasoning": e.reasoning,
                "pricing_tier": e.pricing_tier.value,
                "deprecated": e.deprecated,
            })
        return jsonify({"success": True, "models": result, "count": len(result)}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@catalog_bp.route('/api/get_models', methods=['GET'])
def api_get_models():
    """Get available models (chat + HA settings) without duplicate routes."""
    import api as _api
    try:
        # --- Providers disponibili (per HA settings) ---
        available_providers = []
        if _api.ANTHROPIC_API_KEY:
            available_providers.append({"id": "anthropic", "name": "Anthropic Claude"})
        if _api.OPENAI_API_KEY:
            available_providers.append({"id": "openai", "name": "OpenAI"})
        if _api.GOOGLE_API_KEY:
            available_providers.append({"id": "google", "name": "Google Gemini"})
        if _api.NVIDIA_API_KEY:
            available_providers.append({"id": "nvidia", "name": "NVIDIA NIM"})
        if _api.GITHUB_TOKEN:
            available_providers.append({"id": "github", "name": "GitHub Models"})
        if _api.GROQ_API_KEY:
            available_providers.append({"id": "groq", "name": "Groq"})
        if _api.MISTRAL_API_KEY:
            available_providers.append({"id": "mistral", "name": "Mistral"})
        if _api.OPENROUTER_API_KEY:
            available_providers.append({"id": "openrouter", "name": "OpenRouter"})
        if _api.DEEPSEEK_API_KEY:
            available_providers.append({"id": "deepseek", "name": "DeepSeek"})
        if _api.MINIMAX_API_KEY:
            available_providers.append({"id": "minimax", "name": "MiniMax"})
        if _api.AIHUBMIX_API_KEY:
            available_providers.append({"id": "aihubmix", "name": "AiHubMix"})
        if _api.SILICONFLOW_API_KEY:
            available_providers.append({"id": "siliconflow", "name": "SiliconFlow"})
        if _api.VOLCENGINE_API_KEY:
            available_providers.append({"id": "volcengine", "name": "VolcEngine"})
        if _api.DASHSCOPE_API_KEY:
            available_providers.append({"id": "dashscope", "name": "DashScope (Qwen)"})
        if _api.MOONSHOT_API_KEY:
            available_providers.append({"id": "moonshot", "name": "Moonshot (Kimi)"})
        if _api.ZHIPU_API_KEY:
            available_providers.append({"id": "zhipu", "name": "Zhipu (GLM)"})
        if _api.PERPLEXITY_API_KEY:
            available_providers.append({"id": "perplexity", "name": "Perplexity (Sonar)"})
        if _api.CUSTOM_API_BASE:
            available_providers.append({"id": "custom", "name": "Custom Endpoint"})
        # Ollama: sempre disponibile se ha un URL configurato (è locale)
        if _api.OLLAMA_BASE_URL:
            available_providers.append({"id": "ollama", "name": "Ollama (Local)"})
        # GitHub Copilot: sempre visibile nel selettore; il banner OAuth guida l'autenticazione
        available_providers.append({"id": "github_copilot", "name": "GitHub Copilot", "web": True})
        # OpenAI Codex: sempre visibile nel selettore; il banner OAuth guida l'autenticazione
        available_providers.append({"id": "openai_codex", "name": "OpenAI Codex", "web": True})
        # Provider web non ufficiali — sempre visibili; il token di sessione guida l'autenticazione
        available_providers.append({"id": "claude_web", "name": "Claude.ai Web", "web": True})
        # chatgpt_web: in standby — Cloudflare blocca le richieste da server nel 2026
        # available_providers.append({"id": "chatgpt_web", "name": "ChatGPT Web [UNSTABLE]"})

        # --- Tutti i modelli per provider (come li vuole la chat: display/prefissi) ---
        models_display = {}
        models_technical = {}
        nvidia_models_tested_display: list[str] = []
        nvidia_models_to_test_display: list[str] = []

        # Get list of configured providers (only those with API keys)
        configured_providers = {p["id"] for p in available_providers}

        for provider, models in _api.PROVIDER_MODELS.items():
            # ONLY include models for providers that have API keys configured
            if provider not in configured_providers:
                continue

            filtered_models = list(models)

            # Live discovery for GitHub Copilot (models depend on subscription)
            # Live discovery for GitHub Copilot: use cache only on regular loads.
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
                live_models = _api.get_nvidia_models_cached(_api.NVIDIA_API_KEY)
                if live_models:
                    filtered_models = list(live_models)
                if _api.NVIDIA_MODEL_BLOCKLIST:
                    filtered_models = [m for m in filtered_models if m not in _api.NVIDIA_MODEL_BLOCKLIST]

                # Partition into tested vs not-yet-tested (keep only currently available models)
                tested_ok = [m for m in filtered_models if m in _api.NVIDIA_MODEL_TESTED_OK]
                to_test = [m for m in filtered_models if m not in _api.NVIDIA_MODEL_TESTED_OK]
                filtered_models = tested_ok + to_test

            models_technical[provider] = list(filtered_models)
            # Use per-provider display mapping to avoid cross-provider conflicts
            prov_map = _api.PROVIDER_DISPLAY.get(provider, {})
            models_display[provider] = [prov_map.get(m, m) for m in filtered_models]

            if provider == "nvidia":
                # Provide explicit groups for UI (display names)
                nvidia_models_tested_display = [prov_map.get(m, m) for m in filtered_models if m in _api.NVIDIA_MODEL_TESTED_OK]
                nvidia_models_to_test_display = [prov_map.get(m, m) for m in filtered_models if m not in _api.NVIDIA_MODEL_TESTED_OK]

        # --- Current model (sia tech che display) ---
        current_model_tech = _api.get_active_model()
        # Use provider-specific display to avoid cross-provider collisions
        # (e.g. "openai/gpt-4o" exists in both GitHub and OpenRouter with different display names)
        current_model_display = (
            _api.PROVIDER_DISPLAY.get(_api.AI_PROVIDER, {}).get(current_model_tech)
            or _api.MODEL_DISPLAY_MAPPING.get(current_model_tech)
            or current_model_tech
        )

        # --- Modelli del provider corrente (per HA settings: lista con flag current) ---
        provider_models = models_technical.get(_api.AI_PROVIDER, _api.PROVIDER_MODELS.get(_api.AI_PROVIDER, []))
        available_models = []
        for tech_name in provider_models:
            available_models.append({
                "technical_name": tech_name,
                "display_name": _api.MODEL_DISPLAY_MAPPING.get(tech_name, tech_name),
                "is_current": tech_name == current_model_tech
            })

        # --- Agent info for UI ---
        agents_info = []
        active_agent_id = None
        active_agent_identity = None
        if _api.AGENT_CONFIG_AVAILABLE:
            try:
                mgr = _api.agent_config.get_agent_manager()
                agents_info = mgr.get_agents_for_api()
                active = mgr.get_active_agent()
                if active:
                    active_agent_id = active.id
                    active_agent_identity = {
                        "name": active.identity.name,
                        "emoji": active.identity.emoji,
                        "description": active.identity.description or active.description,
                    }
            except Exception as _e:
                logger.debug(f"Agent info for get_models: {_e}")

        # --- Catalog capability badges per model ---
        model_capabilities = {}
        if _api.MODEL_CATALOG_AVAILABLE:
            try:
                cat = _api.model_catalog.get_catalog()
                for prov_key in models_technical:
                    for mid in models_technical[prov_key]:
                        entry = cat.get_entry(prov_key, mid)
                        if entry:
                            model_capabilities[f"{prov_key}/{mid}"] = {
                                "caps": [c.name.lower() for c in entry.capabilities
                                         if c not in (_api.model_catalog.ModelCapability.TEXT,
                                                      _api.model_catalog.ModelCapability.STREAMING)],
                                "ctx": entry.context_window,
                                "out": entry.max_output_tokens,
                                "tier": entry.pricing_tier.value,
                                "reasoning": entry.reasoning,
                            }
            except Exception as _e:
                logger.debug(f"Catalog info for get_models: {_e}")

        return jsonify({
            "success": True,

            # First-run onboarding: chat should prompt user to pick an agent once
            "needs_first_selection": not os.path.isfile(_api.RUNTIME_SELECTION_FILE),

            # compat chat (quello che già usa il tuo JS)
            "current_provider": _api.AI_PROVIDER,
            "current_model": current_model_display,
            "models": models_display,

            # NVIDIA UI grouping: tested models first, then not-yet-tested
            "nvidia_models_tested": nvidia_models_tested_display,
            "nvidia_models_to_test": nvidia_models_to_test_display,

            # extra per HA (più completo)
            "current_model_technical": current_model_tech,
            "models_technical": models_technical,
            "available_providers": available_providers,
            "available_models": available_models,

            # Agent system
            "agents": agents_info,
            "active_agent": active_agent_id,
            "active_agent_identity": active_agent_identity,
            "channel_agents": _api.agent_config.get_agent_manager().get_all_channel_agents() if _api.AGENT_CONFIG_AVAILABLE else {},

            # Model catalog capabilities (keyed by "provider/model")
            "model_capabilities": model_capabilities,
        }), 200
    except Exception as e:
        logger.error(f"api_get_models error: {e}")
        return jsonify({"success": False, "error": str(e), "models": {}, "available_providers": []}), 500
