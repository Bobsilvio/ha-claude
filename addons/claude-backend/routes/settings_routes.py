"""Settings routes blueprint.

Endpoints:
- GET /api/config
- POST /api/config
- GET /api/system_prompt
- POST /api/system_prompt
- GET /api/config/read
- POST /api/config/save
- GET /api/fallback_config
- POST /api/fallback_config
- GET /api/settings
- POST /api/settings
- POST /api/uninstall_cleanup
"""

import json
import logging
import os
import shutil
from typing import List

from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)

# Default provider priority
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


@settings_bp.route('/api/config', methods=['GET'])
def api_config_get():
    """Get current runtime configuration."""
    import api
    return jsonify({
        "success": True,
        "config": {
            "ai_provider": api.AI_PROVIDER,
            "ai_model": api.get_active_model(),
            "language": api.LANGUAGE,
            "debug_mode": api.DEBUG_MODE,
            "enable_file_access": api.ENABLE_FILE_ACCESS,
            "version": api.VERSION
        }
    })


@settings_bp.route('/api/config', methods=['POST'])
def api_config_post():
    """Update runtime configuration dynamically."""
    import api
    from core.translations import set_current_language
    try:
        data = request.get_json()
        updated = []

        if 'language' in data:
            new_lang = data['language'].lower()
            if new_lang in ['en', 'it', 'es', 'fr']:
                api.LANGUAGE = new_lang
                set_current_language(new_lang)
                updated.append(f"language={api.LANGUAGE}")
                logger.info(f"Language changed to: {api.LANGUAGE}")
            else:
                return jsonify({"success": False, "error": f"Invalid language: {new_lang}. Supported: en, it, es, fr"}), 400

        if 'debug_mode' in data:
            api.DEBUG_MODE = bool(data['debug_mode'])
            updated.append(f"debug_mode={api.DEBUG_MODE}")
            logger.info(f"Debug mode changed to: {api.DEBUG_MODE}")
            import logging as _logging
            _logging.getLogger().setLevel(_logging.DEBUG if api.DEBUG_MODE else _logging.INFO)

        if 'enable_file_access' in data:
            api.ENABLE_FILE_ACCESS = bool(data['enable_file_access'])
            updated.append(f"enable_file_access={api.ENABLE_FILE_ACCESS}")
            logger.info(f"File access changed to: {api.ENABLE_FILE_ACCESS}")

        return jsonify({
            "success": True,
            "message": f"Configuration updated: {', '.join(updated)}",
            "config": {
                "language": api.LANGUAGE,
                "debug_mode": api.DEBUG_MODE,
                "enable_file_access": api.ENABLE_FILE_ACCESS
            }
        })
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('/api/system_prompt', methods=['GET'])
def api_system_prompt_get():
    """Get the current system prompt."""
    try:
        import tools
        prompt = tools.get_system_prompt()
        return jsonify({
            "success": True,
            "system_prompt": prompt,
            "length": len(prompt)
        })
    except Exception as e:
        logger.error(f"Error getting system prompt: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('/api/system_prompt', methods=['POST'])
def api_system_prompt_post():
    """Override the system prompt dynamically. Use 'reset' to restore default."""
    import api
    from services.prompt_service import _persist_custom_system_prompt_to_disk, _load_custom_system_prompt_from_disk
    try:
        data = request.get_json()
        new_prompt = data.get('system_prompt')

        if not new_prompt:
            return jsonify({"success": False, "error": "system_prompt parameter required"}), 400

        if new_prompt.lower() == 'reset':
            api.CUSTOM_SYSTEM_PROMPT = None
            _persist_custom_system_prompt_to_disk(None)
            logger.info("System prompt reset to default")
            import tools
            return jsonify({
                "success": True,
                "message": "System prompt reset to default",
                "system_prompt": tools.get_system_prompt()
            })

        api.CUSTOM_SYSTEM_PROMPT = new_prompt
        _persist_custom_system_prompt_to_disk(api.CUSTOM_SYSTEM_PROMPT)
        logger.info(f"System prompt overridden ({len(new_prompt)} chars)")

        return jsonify({
            "success": True,
            "message": "System prompt updated successfully",
            "system_prompt": api.CUSTOM_SYSTEM_PROMPT,
            "length": len(api.CUSTOM_SYSTEM_PROMPT)
        })
    except Exception as e:
        logger.error(f"Error setting system prompt: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('/api/config/read', methods=['GET'])
def api_config_read():
    """Read a whitelisted config file for the in-app editor."""
    import api
    from services.prompt_service import CONFIG_EDITABLE_FILES
    filepath = (request.args.get("file") or "").strip()
    if not filepath or filepath not in CONFIG_EDITABLE_FILES:
        return jsonify({"success": False, "error": "File not accessible"}), 403

    full_path = os.path.join(api.HA_CONFIG_DIR, filepath)
    if not os.path.isfile(full_path):
        return jsonify({"success": True, "file": filepath, "content": "", "exists": False})

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"success": True, "file": filepath, "content": content, "exists": True, "size": len(content)})
    except Exception as e:
        logger.error(f"api_config_read error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('/api/config/save', methods=['POST'])
def api_config_save():
    """Save content to a whitelisted config file."""
    import api
    from services.prompt_service import CONFIG_EDITABLE_FILES, _load_custom_system_prompt_from_disk

    data = request.get_json() or {}
    filepath = (data.get("file") or "").strip()
    content = data.get("content")

    if content is None:
        return jsonify({"success": False, "error": "content is required"}), 400
    if not filepath:
        return jsonify({"success": False, "error": "file path is required"}), 400

    if filepath not in CONFIG_EDITABLE_FILES:
        return jsonify({"success": False, "error": f"File '{filepath}' is not editable"}), 403

    if filepath.endswith(".json") and content.strip():
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            return jsonify({"success": False, "error": f"Invalid JSON: {e}"}), 400

    if len(content) > 500_000:
        return jsonify({"success": False, "error": "Content too large (max 500KB)"}), 413

    full_path = os.path.join(api.HA_CONFIG_DIR, filepath)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        if filepath == "amira/agents.json":
            api.load_agents_config()
        elif filepath == "amira/custom_system_prompt.txt":
            loaded = _load_custom_system_prompt_from_disk()
            api.CUSTOM_SYSTEM_PROMPT = loaded

        logger.info(f"Config file saved: {filepath} ({len(content)} chars)")
        return jsonify({"success": True, "file": filepath, "size": len(content)})
    except Exception as e:
        logger.error(f"api_config_save error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('/api/fallback_config', methods=['GET'])
def api_fallback_config_get():
    """Return current fallback configuration."""
    import api
    from core.model_utils import normalize_model_name

    _FALLBACK_CONFIG_FILE = os.path.join(api.HA_CONFIG_DIR, "amira", "fallback_config.json")
    enabled = os.getenv("FALLBACK_ENABLED", "true").lower() not in ("false", "0", "no")

    custom_priority = []
    provider_models = {}
    try:
        if os.path.isfile(_FALLBACK_CONFIG_FILE):
            with open(_FALLBACK_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            custom_priority = data.get("priority", [])
            pm = data.get("provider_models", {})
            if isinstance(pm, dict):
                provider_models = {}
                for k, v in pm.items():
                    if not isinstance(k, str) or not isinstance(v, str):
                        continue
                    prov = str(k).strip().lower()
                    mdl_raw = str(v).strip()
                    if not prov or not mdl_raw:
                        continue
                    provider_models[prov] = normalize_model_name(mdl_raw)
            if not provider_models:
                mp = data.get("model_priority", [])
                if isinstance(mp, list):
                    for item in mp:
                        if not isinstance(item, dict):
                            continue
                        prov = str(item.get("provider") or "").strip().lower()
                        mdl = str(item.get("model") or "").strip()
                        if prov and mdl:
                            provider_models[prov] = normalize_model_name(mdl)
            if "enabled" in data:
                enabled = bool(data["enabled"])
    except Exception:
        pass

    if isinstance(custom_priority, list) and custom_priority:
        priority = [str(p).strip().lower() for p in custom_priority if isinstance(p, str) and str(p).strip()]
    else:
        priority = list(_FALLBACK_PRIORITY_DEFAULT)

    providers = []
    seen = set()
    for prov in priority:
        env_var = _FALLBACK_KEY_ENV.get(prov, "")
        has_key = bool(env_var and os.getenv(env_var, ""))
        label = api.PROVIDER_DEFAULTS.get(prov, {}).get("name", prov)
        providers.append({
            "id": prov,
            "configured": has_key,
            "label": label,
            "model": provider_models.get(prov, ""),
        })
        seen.add(prov)

    for prov in _FALLBACK_PRIORITY_DEFAULT:
        if prov not in seen:
            env_var = _FALLBACK_KEY_ENV.get(prov, "")
            has_key = bool(env_var and os.getenv(env_var, ""))
            label = api.PROVIDER_DEFAULTS.get(prov, {}).get("name", prov)
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


@settings_bp.route('/api/fallback_config', methods=['POST'])
def api_fallback_config_post():
    """Save fallback configuration."""
    import api
    from core.model_utils import normalize_model_name

    _FALLBACK_CONFIG_FILE = os.path.join(api.HA_CONFIG_DIR, "amira", "fallback_config.json")
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
        mdl = normalize_model_name(str(v).strip())
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


@settings_bp.route('/api/settings', methods=['GET'])
def api_settings_get():
    """Return all runtime settings with current values."""
    import api
    from services.settings_service import SETTINGS_DEFAULTS, _SETTINGS_GLOBAL_MAP, _load_settings
    saved = _load_settings()
    _g = vars(api)
    current = {}
    for key, default in SETTINGS_DEFAULTS.items():
        if key in saved:
            current[key] = saved[key]
        else:
            gvar = _SETTINGS_GLOBAL_MAP.get(key)
            if gvar and gvar in _g:
                val = _g[gvar]
                if isinstance(val, set):
                    val = ",".join(str(i) for i in sorted(val))
                current[key] = val
            else:
                current[key] = default

    sections = [
        {
            "id": "language", "icon": "\U0001F30D", "fields": [
                {"key": "language", "type": "select",
                 "options": [
                     {"value": "en", "label": "English"},
                     {"value": "it", "label": "Italiano"},
                     {"value": "es", "label": "Español"},
                     {"value": "fr", "label": "Français"},
                     {"value": "hu", "label": "Magyar"},
                 ]},
                {"key": "interaction_mode", "type": "select",
                 "options": [
                     {"value": "strict", "label": "Strict (Safe)"},
                     {"value": "lean", "label": "Lean (Natural)"},
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
                {"key": "enable_discord", "type": "toggle"},
                {"key": "discord_bot_token", "type": "password"},
                {"key": "discord_allowed_channel_ids", "type": "text"},
                {"key": "discord_allowed_user_ids", "type": "text"},
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


@settings_bp.route('/api/settings', methods=['POST'])
def api_settings_post():
    """Save runtime settings, apply immediately, persist to settings.json."""
    import api
    from services.settings_service import SETTINGS_DEFAULTS, _load_settings, _save_settings
    data = request.get_json() or {}
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    clean = {}
    for key in SETTINGS_DEFAULTS:
        if key in data:
            clean[key] = data[key]

    try:
        existing = _load_settings()
        existing.update(clean)
        _save_settings(existing)
        api._apply_settings(existing)
        logger.info(f"Settings saved and applied: {list(clean.keys())}")

        if "enable_chat_bubble" in clean or "enable_amira_card_button" in clean or "enable_amira_automation_button" in clean:
            api._chat_bubble_registered = False
            api.setup_chat_bubble()
            logger.info(f"Chat bubble: bubble={api.ENABLE_CHAT_BUBBLE}, card={api.ENABLE_AMIRA_CARD_BUTTON}, automation={api.ENABLE_AMIRA_AUTOMATION_BUTTON}")

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('/api/ollama/test', methods=['GET'])
def api_ollama_test():
    """Test Ollama server connectivity and return available models."""
    import api as _api
    url = (request.args.get('url') or '').strip() or _api.OLLAMA_BASE_URL
    url = url.rstrip('/')
    try:
        import requests as _req
        r = _req.get(f"{url}/api/tags", timeout=4)
        if r.status_code == 200:
            models = [m.get('name', '') for m in r.json().get('models', [])]
            return jsonify({"success": True, "url": url, "models": models})
        return jsonify({"success": False, "error": f"HTTP {r.status_code}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@settings_bp.route('/api/uninstall_cleanup', methods=['POST'])
def api_uninstall_cleanup():
    """Cleanup persisted Amira artifacts before uninstall."""
    import api
    data = request.get_json(silent=True) or {}
    include_dashboards = bool(data.get("include_dashboards", False))

    removed: List[str] = []
    errors: List[str] = []

    try:
        api.cleanup_chat_bubble()
        removed.append("bubble_resources_and_js")
    except Exception as e:
        errors.append(f"bubble_cleanup: {e}")

    try:
        api.conversations.clear()
        api.abort_streams.clear()
        api.read_only_sessions.clear()
        api.session_last_intent.clear()
        api.session_last_preview.clear()
        api.session_pending_context.clear()
        api.session_active_skill.clear()
        removed.append("runtime_memory_state")
    except Exception as e:
        errors.append(f"runtime_state: {e}")

    amira_dir = os.path.join(api.HA_CONFIG_DIR, "amira")
    try:
        if os.path.isdir(amira_dir):
            shutil.rmtree(amira_dir)
            removed.append(amira_dir)
    except Exception as e:
        errors.append(f"{amira_dir}: {e}")

    if include_dashboards:
        dashboards_dir = os.path.join(api.HA_CONFIG_DIR, "www", "dashboards")
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
