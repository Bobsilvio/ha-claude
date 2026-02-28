"""WSGI entrypoint for the add-on.

Runs the Flask app using Waitress by importing `api` as a module.
This avoids duplicate module instances (__main__ vs api) that can desync globals
like AI_PROVIDER/AI_MODEL between the main app and provider modules.
"""

from __future__ import annotations

import api


def main() -> None:
    api.logger.info(f"Provider: {api.AI_PROVIDER} | Model: {api.get_active_model()}")
    api.logger.info(f"API Key: {'configured' if api.get_api_key() else 'NOT configured'}")
    api.logger.info(f"HA Token: {'available' if api.get_ha_token() else 'NOT available'}")
    api.logger.info(f"Log Level: {api.LOG_LEVEL.upper()} | Colored Logs: {api.COLORED_LOGS} | Debug Mode: {api.DEBUG_MODE}")
    api.logger.info(
        f"Features: Memory={api.ENABLE_MEMORY} | "
        f"FileUpload={api.ENABLE_FILE_UPLOAD} | RAG={api.ENABLE_RAG} | "
        f"ChatBubble={api.ENABLE_CHAT_BUBBLE}"
    )

    # Validate provider/model compatibility
    is_valid, error_msg = api.validate_model_provider_compatibility()
    if not is_valid:
        api.logger.warning(error_msg)
        # Auto-fix: reset to provider default model
        default_model = api.PROVIDER_DEFAULTS.get(api.AI_PROVIDER, {}).get("model", "")
        if default_model:
            api.AI_MODEL = default_model
            fix_msgs = {
                "en": f"✅ AUTO-FIX: Model automatically changed to '{api.MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (default for {api.AI_PROVIDER})",
                "it": f"✅ AUTO-FIX: Modello cambiato automaticamente a '{api.MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (default per {api.AI_PROVIDER})",
                "es": f"✅ AUTO-FIX: Modelo cambiado automáticamente a '{api.MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (predeterminado para {api.AI_PROVIDER})",
                "fr": f"✅ AUTO-FIX: Modèle changé automatiquement en '{api.MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (par défaut pour {api.AI_PROVIDER})",
            }
            api.logger.warning(fix_msgs.get(api.LANGUAGE, fix_msgs["en"]))

    # Register floating chat bubble (if enabled)
    api.setup_chat_bubble()

    # Start Telegram / WhatsApp bots if configured
    api.start_messaging_bots()

    # Initialize MCP servers if configured
    api.initialize_mcp()

    from waitress import serve

    api.logger.info(f"Starting production server on 0.0.0.0:{api.API_PORT}")
    serve(api.app, host="0.0.0.0", port=api.API_PORT, threads=6)


if __name__ == "__main__":
    main()
