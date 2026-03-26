"""Chat UI HTML generation for Home Assistant AI assistant."""

import json
import api
from core.translations import get_current_language


def get_chat_ui():
    """Generate the chat UI with image upload support."""
    ui_lang = (get_current_language() or getattr(api, "LANGUAGE", "en") or "en").lower()
    if ui_lang not in ("en", "it", "es", "fr"):
        ui_lang = "en"

    agent_name = getattr(api, "AGENT_NAME", "Amira") or "Amira"
    agent_avatar = getattr(api, "AGENT_AVATAR", "🤖") or "🤖"

    # Fallback for null/invalid provider
    ai_provider = getattr(api, "AI_PROVIDER", "anthropic") or "anthropic"
    provider_name = api.PROVIDER_DEFAULTS.get(ai_provider, {}).get("name", ai_provider or "Unknown")
    model_name = api.get_active_model() or "Not configured"
    configured = bool(api.get_api_key())
    status_color = "#4caf50" if configured else "#ff9800"
    status_text = provider_name if configured else f"{provider_name} (no key)"

    # Generic thinking message — works for any provider/model combination.
    analyzing_by_lang = {
        "en": "🤖 Amira is thinking...",
        "it": "🤖 Amira sta elaborando...",
        "es": "🤖 Amira está procesando...",
        "fr": "🤖 Amira réfléchit...",
    }
    analyzing_msg = analyzing_by_lang.get(ui_lang, analyzing_by_lang["en"])

    ui_messages = {
        "en": {
            "welcome": f"{agent_avatar} Hi! I'm {agent_name}, your AI assistant for Home Assistant.",
            "provider_model": f"Provider: <strong>{provider_name}</strong> | Model: <strong>{model_name}</strong>",
            "capabilities": "I can control devices, create automations, and manage your smart home.",
            "vision_feature": "",
            "o4mini_tokens_hint": "ℹ️ Note: o4-mini has a ~4000 token limit. Context and history are reduced automatically.",
            "analyzing": analyzing_msg
        },
        "it": {
            "welcome": f"{agent_avatar} Ciao! Sono {agent_name}, il tuo assistente AI per Home Assistant.",
            "provider_model": f"Provider: <strong>{provider_name}</strong> | Modello: <strong>{model_name}</strong>",
            "capabilities": "Posso controllare dispositivi, creare automazioni e gestire la tua casa smart.",
            "vision_feature": "",
            "o4mini_tokens_hint": "ℹ️ Nota: o4-mini ha un limite di ~4000 token. Contesto e cronologia vengono ridotti automaticamente.",
            "analyzing": analyzing_msg
        },
        "es": {
            "welcome": f"{agent_avatar} ¡Hola! Soy {agent_name}, tu asistente AI para Home Assistant.",
            "provider_model": f"Proveedor: <strong>{provider_name}</strong> | Modelo: <strong>{model_name}</strong>",
            "capabilities": "Puedo controlar dispositivos, crear automatizaciones y gestionar tu hogar inteligente.",
            "vision_feature": "",
            "o4mini_tokens_hint": "ℹ️ Nota: o4-mini tiene un límite de ~4000 tokens. El contexto y el historial se reducen automáticamente.",
            "analyzing": analyzing_msg
        },
        "fr": {
            "welcome": f"{agent_avatar} Salut ! Je suis {agent_name}, votre assistant IA pour Home Assistant.",
            "provider_model": f"Fournisseur: <strong>{provider_name}</strong> | Modèle: <strong>{model_name}</strong>",
            "capabilities": "Je peux contrôler des appareils, créer des automatisations et gérer votre maison intelligente.",
            "vision_feature": "",
            "o4mini_tokens_hint": "ℹ️ Note : o4-mini a une limite d’environ 4000 tokens. Le contexte et l’historique sont réduits automatiquement.",
            "analyzing": analyzing_msg
        }
    }

    # Get messages for current language
    msgs = ui_messages.get(ui_lang, ui_messages["en"])

    o4mini_tokens_hint_js = json.dumps(msgs.get("o4mini_tokens_hint", ""))

    # --- Comprehensive UI strings for JS (multilingual) ---
    ui_js_all = {
        "en": {
            "change_model": "Change model",
            "nvidia_test_title": "Quick NVIDIA test (may take a few seconds)",
            "nvidia_test_btn": "Test NVIDIA",
            "new_chat_title": "New conversation",
            "new_chat_btn": "New chat",
            "conversations": "Conversations",
            "drag_resize": "Drag to resize",
            "remove_image": "Remove image",
            "upload_image": "Upload image",
            "input_placeholder": "Write a message...",
            "image_too_large": "Image is too large. Max 5MB.",
            "restore_backup": "Restore backup",
            "restore_backup_title": "Restore backup (snapshot: {id})",
            "confirm_restore": "Do you want to restore the backup? This will undo the last change.",
            "restoring": "Restoring...",
            "restored": "Restored",
            "backup_restored": "Backup restored. If needed, refresh the Lovelace page or check the automation/script.",
            "restore_failed": "Restore failed.",
            "error_restore": "Restore error: ",
            "copy_btn": "Copy",
            "copied": "Copied!",
            "request_failed": "Request failed ({status}): {body}",
            "rate_limit_error": "Rate limit exceeded. Please wait a moment before trying again.",
            "unexpected_response": "Unexpected response from server.",
            "error_prefix": "Error: ",
            "connection_lost": "Connection lost. Try again.",
            "messages_count": "messages",
            "delete_chat": "Delete chat",
            "no_conversations": "No conversations",
            "confirm_delete": "Delete this conversation?",
            "select_agent": "Select an agent from the top menu to start. You can change it at any time.",
            "nvidia_tested": "Tested",
            "nvidia_to_test": "To test",
            "no_models": "No models available",
            "models_load_error": "Error loading models: ",
            "nvidia_test_result": "NVIDIA Test: OK {ok}, removed {removed}, tested {tested}/{total}",
            "nvidia_remaining": "remaining: {n} (press again to continue)",
            "nvidia_test_failed": "NVIDIA test failed",
            "switched_to": "Switched to {provider} \u2192 {model}",
            "provider_label": "Provider",
            "model_label": "Model",
            "web_html_warn": "⚠️ Unofficial web provider: HTML dashboard creation may be incomplete or malformed. Always verify the generated file.",
            # Suggestions
            "sug_lights": "Show all lights",
            "sug_sensors": "Sensor status",
            "sug_areas": "Rooms and areas",
            "sug_temperature": "Temperature history",
            "sug_scenes": "Available scenes",
            "sug_automations": "List automations",
            # Read-only mode
            "readonly_title": "Read-only mode: show code without executing",
            "readonly_on": "ON",
            "readonly_off": "OFF",
            "readonly_label": "Read-only",
            # Confirmation buttons
            "confirm_yes": "Yes, confirm",
            "confirm_no": "No, cancel",
            "confirm_yes_value": "yes",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Delete",
            "today": "Today",
            "yesterday": "Yesterday",
            "days_ago": "{n} days ago",
            "sending_request": "Sending request",
            "connected": "Connected",
            "waiting_response": "Waiting for response",
            "remove_document": "Remove document",
            "file_too_large": "File too large (max 10MB)",
            "uploading_document": "Uploading document...",
            "upload_failed": "Upload failed",
            "upload_error": "Upload error",
            "unknown_error": "Unknown error",
            "document_uploaded": "Document uploaded",
            "mic_not_supported": "Browser does not support audio recording. Use HTTPS or a compatible browser.",
            "mic_needs_https": "Microphone requires HTTPS. Quick fix for Chrome: open chrome://flags/#unsafely-treat-insecure-origin-as-secure, add your HA address (e.g. http://192.168.x.x:8123), set Enabled, restart Chrome. Otherwise configure SSL in HA or use localhost.",
            "mic_denied_settings": "Microphone access denied. Go to browser settings to enable it.",
            "mic_denied_icon": "Microphone denied. Click the 🔒 icon in the browser bar to enable it.",
            "mic_not_found": "No microphone found. Connect a microphone and try again.",
            "mic_in_use": "Microphone in use by another app. Close other apps and try again.",
            "mic_error": "Microphone error",
            # Voice mode
            "voice_mode": "Voice mode",
            "voice_listening": "Listening...",
            "voice_processing": "Processing audio...",
            "voice_tts_no_provider": "Voice output unavailable. Edge TTS or a Groq/OpenAI API key is needed.",
            "voice_transcription_error": "Transcription failed. Try again.",
            "voice_speaking": "Speaking...",
            "voice_stop_speaking": "Stop speaking",
            "wake_word_detected": "Amira activated! Speak now...",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
            "tab_amira": "Card",
            "tab_backups": "Backups",
            "tab_devices": "Bubble Devices",
            "tab_messaging": "📱 Messaging",
            "tab_files": "\U0001f4c1 Files",
            "files_loading": "Loading...",
            "files_empty": "Empty directory",
            "files_error": "Error loading",
            "files_close_panel": "Close file panel",
            "files_context_label": "File context:",
            "messaging_no_chats": "No messaging chats yet",
            "messaging_messages": "Messages",
            "messaging_delete": "Delete",
            "messaging_confirm_delete": "Delete this chat?",
            "no_backups": "No backups yet",
            "restore": "Restore",
            "confirm_restore_backup": "Restore this backup? The current file will be replaced.",
            "delete_backup": "Delete",
            "confirm_delete_backup": "Delete this backup permanently?",
            "download_backup": "Download",
            # Device manager
            "no_devices": "No devices registered yet",
            "enable_device": "Enable",
            "disable_device": "Disable",
            "rename_device": "Rename",
            "delete_device": "Delete",
            "confirm_delete_device": "Delete this device permanently?",
            "device_deleted": "Device deleted",
            "device_updated": "Device updated",
            # Dark mode
            "dark_mode": "Dark mode",
            # Skills tab
            "tab_skills": "🧩 Skills",
            "skills_installed": "Installed",
            "skills_store": "Store",
            "skills_install_btn": "Install",
            "skills_installed_badge": "Installed",
            "skills_delete_btn": "Remove",
            "skills_delete_confirm": "Remove this skill?",
            "skills_empty": "No skills installed. Browse the store below.",
            "skills_store_empty": "No skills available in the store.",
            "skills_store_loading": "Loading store...",
            "skills_store_error": "Could not load the store. Check your internet connection.",
            "skills_unavailable": "Skills not available. Please restart the add-on.",
            "skills_update_banner": "Skill update available:",
            "skills_update_go": "Go to Skills",
            "skills_update_btn": "Update",
            "skills_refresh": "Refresh",
            "skills_by": "by",
            "skills_requires_version": "Requires Amira v{version}",
            "skills_hint": "Type /skill-name in the chat to use a skill",
            # Costs tab
            "tab_costs": "Costs",
            "costs_today": "Today",
            "costs_by_model": "By model",
            "costs_by_provider": "By provider",
            "costs_history": "Last 7 days",
            "costs_no_data": "No usage data yet",
            "costs_reset": "Reset",
            "costs_reset_confirm": "Reset all usage statistics? This cannot be undone.",
            "costs_requests": "requests",
            # Config tab
            "tab_config": "\U0001f527 Config",
            "config_loading": "Loading...",
            "config_save": "Save",
            "config_cancel": "Cancel",
            "config_saved": "Saved!",
            "config_save_error": "Save failed",
            "config_file_not_found": "File not found (will be created on save)",
            "config_agents_title": "Agent Profiles",
            "config_mcp_title": "MCP Configuration",
            "config_prompt_title": "Custom System Prompt",
            "config_memory_title": "Memory (MEMORY.md)",
            "config_llm_title": "LLM Priority",
            "config_model_cache_title": "Model Cache",
            "llm_fallback_label": "Auto Fallback",
            "llm_priority_label": "Priority order",
            "llm_no_key": "no key",
            "llm_saved": "Saved!",
            "llm_fallback_on": "If the primary provider fails, the system will try the next one in the list.",
            "llm_fallback_off": "Fallback disabled. Only the primary provider will be used.",
            "fallback_notice": "Fallback: {{from}} → {{to}}",
            # Settings
            "config_settings_title": "Settings",
            "settings_saved": "Settings saved!",
            "settings_clear_models_cache": "Clear Models Cache",
            "settings_clear_models_cache_confirm": "Clear cached dynamic provider models now? Fixed models stay available.",
            "settings_clear_models_cache_done": "Models cache cleared!",
            "settings_clear_models_cache_error": "Failed to clear models cache",
            "settings_refresh_models_cache": "Refresh Models Cache",
            "settings_refresh_models_cache_done": "Models cache refreshed!",
            "settings_refresh_models_cache_error": "Failed to refresh models cache",
            "settings_model_cache_title": "Model Cache",
            "settings_model_cache_loading": "Loading model cache...",
            "settings_model_cache_updated_at": "Updated",
            "settings_model_cache_fixed": "Fixed Models",
            "settings_model_cache_dynamic": "Dynamic Models (cache)",
            "settings_model_cache_blocklist": "Blocked Models",
            "settings_model_cache_uncertain": "Uncertain Test Results",
            "settings_model_cache_nvidia_tested": "NVIDIA Tested OK",
            "settings_model_cache_empty": "No models",
            "restart_confirm": "Some changes require a restart to take effect. Restart the add-on now?",
            "restart_in_progress": "Restarting add-on...",
            "restart_failed": "Restart failed",
            "settings_language": "Language",
            "settings_enable_memory": "Memory",
            "settings_enable_file_access": "File Access",
            "settings_enable_file_upload": "File Upload",
            "settings_enable_voice_input": "Voice Input",
            "settings_enable_rag": "RAG",
            "settings_enable_chat_bubble": "Chat Bubble",
            "settings_enable_amira_card_button": "Amira Card Button",
            "settings_enable_amira_automation_button": "Amira Automation Button",
            "settings_enable_mcp": "MCP Servers",
            "settings_fallback_enabled": "Auto Fallback",
            "settings_anthropic_thinking": "Anthropic Thinking",
            "settings_anthropic_caching": "Prompt Caching",
            "settings_openai_thinking": "OpenAI Thinking",
            "settings_nvidia_thinking": "NVIDIA Thinking",
            "settings_tts_voice": "TTS Voice",
            "settings_enable_telegram": "Telegram",
            "settings_telegram_token": "Telegram Bot Token",
            "settings_telegram_allowed_ids": "Allowed User IDs",
            "settings_enable_whatsapp": "WhatsApp",
            "settings_twilio_sid": "Twilio Account SID",
            "settings_twilio_token": "Twilio Auth Token",
            "settings_twilio_from": "WhatsApp From Number",
            "settings_enable_discord": "Discord",
            "settings_discord_token": "Discord Bot Token",
            "settings_discord_allowed_channels": "Allowed Channel IDs",
            "settings_discord_allowed_users": "Allowed User IDs",
            "settings_timeout": "Timeout (s)",
            "settings_max_retries": "Max Retries",
            "settings_max_conversations": "Max Conversations",
            "settings_max_snapshots": "Max Snapshots/File",
            "settings_cost_currency": "Currency",
            "settings_section_language": "Language",
            "settings_section_features": "Features",
            "settings_section_ai": "AI",
            "settings_section_voice": "Voice",
            "settings_section_messaging": "Messaging",
            "settings_section_advanced": "Advanced",
            "settings_section_costs": "Costs",
            # Settings descriptions
            "settings_desc_language": "AI response language (English, Italian, Spanish, or French)",
            "settings_desc_enable_memory": "[EXPERIMENTAL] Persistent memory \u2013 the AI only remembers what you write in MEMORY.md across sessions. Past conversations are NEVER injected into the prompt.",
            "settings_desc_enable_file_access": "Allow AI to read/write Home Assistant config files (automations, scripts, YAML)",
            "settings_desc_enable_file_upload": "[EXPERIMENTAL] Allow uploading documents (PDF, DOCX, TXT, MD, YAML) for AI analysis",
            "settings_desc_enable_voice_input": "Enable microphone button for voice messages (Groq Whisper, with OpenAI/Google fallback) \u2013 requires HTTPS",
            "settings_desc_enable_rag": "[EXPERIMENTAL] Enable RAG (Retrieval-Augmented Generation) for document search and context injection",
            "settings_desc_enable_chat_bubble": "Show a floating AI chat bubble on every HA page.",
            "settings_desc_enable_amira_card_button": "Show the Amira button inside the Lovelace card editor dialog for AI-assisted card editing.",
            "settings_desc_enable_amira_automation_button": "Show the Amira button and flowchart helper in the Home Assistant automation editor.",
            "settings_desc_enable_mcp": "Enable MCP (Model Context Protocol) support. When disabled, Amira skips MCP server connections at startup.",
            "mcp_config_path": "Config File",
            "settings_desc_mcp_config_file": "Path to MCP configuration JSON file",
            "settings_desc_fallback_enabled": "If the primary provider fails, automatically try the next one in the priority list",
            "settings_desc_anthropic_extended_thinking": "Enable Claude extended thinking for complex reasoning tasks (slower, uses more tokens)",
            "settings_desc_anthropic_prompt_caching": "Cache long repetitive instructions to save costs and improve response speed",
            "settings_desc_openai_extended_thinking": "Enable o1/o3 reasoning mode for complex problem-solving (slower, uses more tokens)",
            "settings_desc_nvidia_thinking_mode": "Enable thinking mode to see AI reasoning process (slower but more transparent)",
            "settings_desc_tts_voice": "Voice for AI spoken responses \u2013 automatically matched to your language (Edge TTS, free)",
            "settings_desc_enable_telegram": "Enable or disable the Telegram bot entirely. When disabled, incoming messages are rejected with a 503 error.",
            "settings_desc_telegram_bot_token": "Telegram bot token from @BotFather \u2013 leave empty to disable",
            "settings_desc_telegram_allowed_ids": "Comma-separated list of Telegram user IDs allowed to use the bot (e.g. 123456789,987654321). Leave empty to allow everyone \u2013 not recommended.",
            "settings_desc_enable_whatsapp": "Enable or disable the WhatsApp (Twilio) bot entirely. When disabled, incoming webhooks are rejected with a 503 error.",
            "settings_desc_twilio_account_sid": "Your Twilio Account SID for WhatsApp integration \u2013 get from console.twilio.com",
            "settings_desc_twilio_auth_token": "Your Twilio Auth Token for WhatsApp integration \u2013 get from console.twilio.com",
            "settings_desc_twilio_whatsapp_from": "Your Twilio WhatsApp number (e.g. +1234567890) \u2013 leave empty to disable",
            "settings_desc_enable_discord": "Enable or disable the Discord bot entirely. When disabled, incoming Discord messages are ignored.",
            "settings_desc_discord_bot_token": "Discord Bot token from Discord Developer Portal \u2013 leave empty to disable",
            "settings_desc_discord_allowed_channel_ids": "Comma-separated Discord channel IDs allowed to use the bot. Leave empty to allow all channels.",
            "settings_desc_discord_allowed_user_ids": "Comma-separated Discord user IDs allowed to use the bot. Leave empty to allow all users.",
            "settings_desc_timeout": "API request timeout in seconds (default 30, increase if responses are slow)",
            "settings_desc_max_retries": "Maximum retry attempts for failed API calls (default 3)",
            "settings_desc_max_conversations": "Maximum number of chat conversations to keep in history (1\u2013100)",
            "settings_desc_max_snapshots_per_file": "Maximum backup snapshots per file. Oldest backups are auto-deleted when the limit is reached.",
            "settings_desc_cost_currency": "Currency for token cost display",
            "models_group_fixed": "Fixed",
            "models_group_dynamic_cache": "Dynamic (cache)",
            # Agent form
            "agent_add": "New Agent",
            "agent_new": "\U0001f916 New Agent",
            "agent_none": "No agents configured. Click \"New Agent\" to get started.",
            "agent_back": "Back",
            "agent_name": "Name",
            "agent_desc": "Description",
            "agent_tools": "Allowed Tools",
            "agent_enabled": "Enabled",
            "agent_id_label": "ID (unique)",
            "agent_id_invalid": "ID must contain only lowercase letters, numbers, - and _",
            "agent_sysprompt_label": "Agent Instructions",
            "agent_sysprompt_hint": "Optional instructions prepended to the default system prompt. Example: Your name is Jarvis. The user is called John.",
            "agent_delete_confirm": "Delete agent",
            "agent_protected": "Protected (built-in)",
            "agent_fallbacks": "Fallback Models",
            "agent_temperature": "Temperature (0-2)",
            "agent_thinking": "Thinking",
            "agent_maxtokens": "Max Tokens",
            "agent_default_flag": "Default",
            "agent_tools_hint": "empty = all",
            # Agent form tooltips
            "tip_agent_id": "Unique identifier. Use lowercase, no spaces (e.g. home, coder, energy).",
            "tip_agent_name": "Display name shown in the agent selector.",
            "tip_agent_emoji": "Icon shown next to the agent name.",
            "tip_agent_desc": "Short description of what this agent specializes in.",
            "tip_agent_provider": "AI provider (e.g. Anthropic, OpenAI). Leave empty to use the default.",
            "tip_agent_model": "Specific model to use. Leave empty to use the provider default.",
            "tip_agent_fallbacks": "Comma-separated fallback models if the primary is unavailable.",
            "tip_agent_temperature": "Controls randomness (0=deterministic, 2=creative). Default: 0.7.",
            "tip_agent_thinking": "Reasoning depth: off, low, medium, high, or adaptive.",
            "tip_agent_maxtokens": "Maximum tokens for each response. Default: 4096.",
            "tip_agent_sysprompt": "Instructions prepended to the default HA system prompt. The AI retains full HA context plus your custom info.",
            "tip_agent_tools": "Select which tools this agent can use. None selected = all tools available.",
            "tip_agent_default": "The default agent is used when no specific agent is selected.",
            "tip_agent_enabled": "Disabled agents are hidden from the agent selector.",
            # MCP form
            "mcp_add_server": "Add Server",
            "mcp_server_name": "Server Name",
            "mcp_command": "Command",
            "mcp_args": "Arguments",
            "mcp_env": "Environment Variables",
            "mcp_pip_section": "Install pip packages",
            "mcp_install_btn": "Install",
            "mcp_no_packages": "No packages specified.",
            "mcp_installing": "Installing...",
            "mcp_done": "Done.",
            "mcp_error": "Error.",
            "mcp_start_failed": "MCP start failed",
            "mcp_stop_failed": "MCP stop failed",
            "mcp_no_servers": "No MCP servers configured. Click \"Add Server\" to connect external tools.",
            "tip_mcp_name": "Unique name for this MCP server (e.g. filesystem, web_search).",
            "tip_mcp_command": "Command to start the server (e.g. python, uvx, npx).",
            "tip_mcp_args": "One argument per line. E.g. -m, mcp.server.stdio.",
            "tip_mcp_env": "One per line: KEY=VALUE. Environment variables for the server.",
            # System prompt form
            "prompt_chars": "characters",
            "prompt_reset": "Clear",
            "prompt_hint": "Write custom instructions here. They will be prepended to the default system prompt.\nExample: The user's name is John Smith. Always respond in English.",
            # Memory form
            "memory_hint": "Markdown notes the AI will remember across conversations...",
            "memory_lines": "lines",
            # Channel association
            "agent_channels": "Channel Assignment",
            "agent_channel_telegram": "Telegram",
            "agent_channel_whatsapp": "WhatsApp",
            "agent_channel_discord": "Discord",
            "agent_channel_taken": "Already assigned to",
            "tip_agent_channels": "Assign this agent to a messaging channel. Each channel can have one agent.",
        },
        "it": {
            "change_model": "Cambia modello",
            "nvidia_test_title": "Test veloce NVIDIA (può richiedere qualche secondo)",
            "nvidia_test_btn": "Test NVIDIA",
            "new_chat_title": "Nuova conversazione",
            "new_chat_btn": "Nuova chat",
            "conversations": "Conversazioni",
            "drag_resize": "Trascina per ridimensionare",
            "remove_image": "Rimuovi immagine",
            "upload_image": "Carica immagine",
            "input_placeholder": "Scrivi un messaggio...",
            "image_too_large": "L'immagine è troppo grande. Massimo 5MB.",
            "restore_backup": "Ripristina backup",
            "restore_backup_title": "Ripristina il backup (snapshot: {id})",
            "confirm_restore": "Vuoi ripristinare il backup? Questa operazione annulla la modifica appena fatta.",
            "restoring": "Ripristino...",
            "restored": "Ripristinato",
            "backup_restored": "Backup ripristinato. Se necessario, aggiorna la pagina Lovelace o verifica l'automazione/script.",
            "restore_failed": "Ripristino fallito.",
            "error_restore": "Errore ripristino: ",
            "copy_btn": "Copia",
            "copied": "Copiato!",
            "request_failed": "Richiesta fallita ({status}): {body}",
            "rate_limit_error": "Limite di velocit\u00e0 superato. Attendi un momento prima di riprovare.",
            "unexpected_response": "Risposta inattesa dal server.",
            "error_prefix": "Errore: ",
            "connection_lost": "Connessione interrotta. Riprova.",
            "messages_count": "messaggi",
            "delete_chat": "Elimina chat",
            "no_conversations": "Nessuna conversazione",
            "confirm_delete": "Eliminare questa conversazione?",
            "select_agent": "Seleziona un agente dal menu in alto per iniziare. Potrai cambiarlo in qualsiasi momento.",
            "nvidia_tested": "Testati",
            "nvidia_to_test": "Da testare",
            "no_models": "Nessun modello disponibile",
            "models_load_error": "Errore nel caricamento dei modelli: ",
            "nvidia_test_result": "Test NVIDIA: OK {ok}, rimossi {removed}, testati {tested}/{total}",
            "nvidia_remaining": "restanti: {n} (ripremi per continuare)",
            "nvidia_test_failed": "Test NVIDIA fallito",
            "switched_to": "Passato a {provider} \u2192 {model}",
            "provider_label": "Provider",
            "model_label": "Modello",
            "web_html_warn": "⚠️ Provider web non ufficiale: la creazione di dashboard HTML può risultare incompleta o malformata. Verifica sempre il file generato.",
            # Suggestions
            "sug_lights": "Mostra tutte le luci",
            "sug_sensors": "Stato sensori",
            "sug_areas": "Stanze e aree",
            "sug_temperature": "Storico temperatura",
            "sug_scenes": "Scene disponibili",
            "sug_automations": "Lista automazioni",
            # Read-only mode
            "readonly_title": "Modalit\u00e0 sola lettura: mostra il codice senza eseguire",
            "readonly_on": "ON",
            "readonly_off": "OFF",
            "readonly_label": "Sola lettura",
            # Confirmation buttons
            "confirm_yes": "S\u00ec, conferma",
            "confirm_no": "No, annulla",
            "confirm_yes_value": "si",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Elimina",
            "today": "Oggi",
            "yesterday": "Ieri",
            "days_ago": "{n} giorni fa",
            "sending_request": "Invio richiesta",
            "connected": "Connesso",
            "waiting_response": "In attesa della risposta",
            "remove_document": "Rimuovi documento",
            "file_too_large": "File troppo grande (max 10MB)",
            "uploading_document": "Caricamento documento...",
            "upload_failed": "Upload fallito",
            "upload_error": "Errore upload",
            "unknown_error": "Errore sconosciuto",
            "document_uploaded": "Documento caricato",
            "mic_not_supported": "Il browser non supporta la registrazione audio. Usa HTTPS o un browser compatibile.",
            "mic_needs_https": "Il microfono richiede HTTPS. Soluzione rapida per Chrome: apri chrome://flags/#unsafely-treat-insecure-origin-as-secure, aggiungi il tuo indirizzo HA (es. http://192.168.x.x:8123), imposta Enabled, riavvia Chrome. Altrimenti configura SSL in HA o usa localhost.",
            "mic_denied_settings": "Accesso al microfono negato. Vai nelle impostazioni del browser per abilitarlo.",
            "mic_denied_icon": "Permesso microfono negato. Clicca l'icona 🔒 nella barra del browser per abilitarlo.",
            "mic_not_found": "Nessun microfono trovato. Collega un microfono e riprova.",
            "mic_in_use": "Microfono in uso da un'altra app. Chiudi le altre app e riprova.",
            "mic_error": "Errore microfono",
            # Voice mode
            "voice_mode": "Modalità voce",
            "voice_listening": "In ascolto...",
            "voice_processing": "Elaborazione audio...",
            "voice_tts_no_provider": "Voce in uscita non disponibile. Serve Edge TTS o una API key Groq/OpenAI.",
            "voice_transcription_error": "Trascrizione fallita. Riprova.",
            "voice_speaking": "Sto parlando...",
            "voice_stop_speaking": "Ferma riproduzione",
            "wake_word_detected": "Amira attivata! Parla ora...",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
            "tab_amira": "Card",
            "tab_backups": "Backup",
            "tab_devices": "Bubble Devices",
            "tab_messaging": "📱 Messaggi",
            "tab_files": "\U0001f4c1 File",
            "files_loading": "Caricamento...",
            "files_empty": "Cartella vuota",
            "files_error": "Errore caricamento",
            "files_close_panel": "Chiudi pannello file",
            "files_context_label": "File di contesto:",
            "messaging_no_chats": "Nessuna chat di messaggi",
            "messaging_messages": "Messaggi",
            "messaging_delete": "Elimina",
            "messaging_confirm_delete": "Eliminare questa chat?",
            "no_backups": "Nessun backup",
            "restore": "Ripristina",
            "confirm_restore_backup": "Ripristinare questo backup? Il file attuale verrà sostituito.",
            "delete_backup": "Elimina",
            "confirm_delete_backup": "Eliminare questo backup definitivamente?",
            "download_backup": "Scarica",
            # Device manager
            "no_devices": "Nessun dispositivo registrato",
            "enable_device": "Abilita",
            "disable_device": "Disabilita",
            "rename_device": "Rinomina",
            "delete_device": "Elimina",
            "confirm_delete_device": "Eliminare questo dispositivo definitivamente?",
            "device_deleted": "Dispositivo eliminato",
            "device_updated": "Dispositivo aggiornato",
            # Dark mode
            "dark_mode": "Tema scuro",
            # Skills tab
            "tab_skills": "🧩 Skill",
            "skills_installed": "Installate",
            "skills_store": "Store",
            "skills_install_btn": "Installa",
            "skills_installed_badge": "Installata",
            "skills_delete_btn": "Rimuovi",
            "skills_delete_confirm": "Rimuovere questa skill?",
            "skills_empty": "Nessuna skill installata. Sfoglia lo store qui sotto.",
            "skills_store_empty": "Nessuna skill disponibile nello store.",
            "skills_store_loading": "Caricamento store...",
            "skills_store_error": "Impossibile caricare lo store. Controlla la connessione internet.",
            "skills_unavailable": "Skills non disponibili. Riavvia l'add-on.",
            "skills_update_banner": "Aggiornamento skill disponibile:",
            "skills_update_go": "Vai alle Skill",
            "skills_update_btn": "Aggiorna",
            "skills_refresh": "Aggiorna",
            "skills_by": "di",
            "skills_requires_version": "Richiede Amira v{version}",
            "skills_hint": "Scrivi /nome-skill nella chat per usare una skill",
            # Costs tab
            "tab_costs": "Costi",
            "costs_today": "Oggi",
            "costs_by_model": "Per modello",
            "costs_by_provider": "Per provider",
            "costs_history": "Ultimi 7 giorni",
            "costs_no_data": "Nessun dato di utilizzo",
            "costs_reset": "Azzera",
            "costs_reset_confirm": "Azzerare tutte le statistiche di utilizzo? Non si può annullare.",
            "costs_requests": "richieste",
            # Config tab
            "tab_config": "\U0001f527 Config",
            "config_loading": "Caricamento...",
            "config_save": "Salva",
            "config_cancel": "Annulla",
            "config_saved": "Salvato!",
            "config_save_error": "Errore nel salvataggio",
            "config_file_not_found": "File non trovato (verrà creato al salvataggio)",
            "config_agents_title": "Profili Agente",
            "config_mcp_title": "Configurazione MCP",
            "config_prompt_title": "System Prompt Personalizzato",
            "config_memory_title": "Memoria (MEMORY.md)",
            "config_llm_title": "Priorita LLM",
            "config_model_cache_title": "Cache Modelli",
            "llm_fallback_label": "Fallback automatico",
            "llm_priority_label": "Ordine di priorita",
            "llm_no_key": "senza chiave",
            "llm_saved": "Salvato!",
            "llm_fallback_on": "Se il provider primario fallisce, il sistema provera il prossimo nella lista.",
            "llm_fallback_off": "Fallback disattivato. Verra usato solo il provider primario.",
            "fallback_notice": "Fallback: {{from}} → {{to}}",
            # Settings
            "config_settings_title": "Impostazioni",
            "settings_saved": "Impostazioni salvate!",
            "settings_clear_models_cache": "Cancella Cache Modelli",
            "settings_clear_models_cache_confirm": "Vuoi cancellare ora la cache dei modelli dinamici? I modelli fissi restano disponibili.",
            "settings_clear_models_cache_done": "Cache modelli cancellata!",
            "settings_clear_models_cache_error": "Errore cancellazione cache modelli",
            "settings_refresh_models_cache": "Aggiorna Cache Modelli",
            "settings_refresh_models_cache_done": "Cache modelli aggiornata!",
            "settings_refresh_models_cache_error": "Errore aggiornamento cache modelli",
            "settings_model_cache_title": "Cache Modelli",
            "settings_model_cache_loading": "Caricamento cache modelli...",
            "settings_model_cache_updated_at": "Aggiornata",
            "settings_model_cache_fixed": "Modelli Fissi",
            "settings_model_cache_dynamic": "Modelli Dinamici (cache)",
            "settings_model_cache_blocklist": "Modelli Bloccati",
            "settings_model_cache_uncertain": "Test Incerti",
            "settings_model_cache_nvidia_tested": "NVIDIA Testati OK",
            "settings_model_cache_empty": "Nessun modello",
            "restart_confirm": "Alcune modifiche richiedono un riavvio per essere applicate. Riavviare l'add-on ora?",
            "restart_in_progress": "Riavvio add-on in corso...",
            "restart_failed": "Riavvio fallito",
            "settings_language": "Lingua",
            "settings_enable_memory": "Memoria",
            "settings_enable_file_access": "Accesso File",
            "settings_enable_file_upload": "Upload File",
            "settings_enable_voice_input": "Input Vocale",
            "settings_enable_rag": "RAG",
            "settings_enable_chat_bubble": "Bolla Chat",
            "settings_enable_amira_card_button": "Pulsante Amira Card",
            "settings_enable_amira_automation_button": "Pulsante Amira Automazioni",
            "settings_enable_mcp": "Server MCP",
            "settings_fallback_enabled": "Fallback Automatico",
            "settings_anthropic_thinking": "Pensiero Anthropic",
            "settings_anthropic_caching": "Cache Prompt",
            "settings_openai_thinking": "Pensiero OpenAI",
            "settings_nvidia_thinking": "Pensiero NVIDIA",
            "settings_tts_voice": "Voce TTS",
            "settings_enable_telegram": "Telegram",
            "settings_telegram_token": "Token Bot Telegram",
            "settings_enable_whatsapp": "WhatsApp",
            "settings_twilio_sid": "Twilio Account SID",
            "settings_twilio_token": "Twilio Auth Token",
            "settings_twilio_from": "Numero WhatsApp",
            "settings_enable_discord": "Discord",
            "settings_discord_token": "Token Bot Discord",
            "settings_discord_allowed_channels": "ID Canali Autorizzati",
            "settings_discord_allowed_users": "ID Utenti Autorizzati",
            "settings_timeout": "Timeout (s)",
            "settings_max_retries": "Tentativi Max",
            "settings_max_conversations": "Conversazioni Max",
            "settings_max_snapshots": "Max Snapshot/File",
            "settings_cost_currency": "Valuta",
            "settings_section_language": "Lingua",
            "settings_section_features": "Funzionalita",
            "settings_section_ai": "AI",
            "settings_section_voice": "Voce",
            "settings_section_messaging": "Messaggistica",
            "settings_section_advanced": "Avanzate",
            "settings_section_costs": "Costi",
            # Settings descriptions
            "settings_desc_language": "Lingua delle risposte AI (Inglese, Italiano, Spagnolo o Francese)",
            "settings_desc_enable_memory": "[SPERIMENTALE] Memoria persistente \u2013 l'AI ricorda solo ci\u00f2 che scrivi in MEMORY.md tra le sessioni. Le conversazioni passate NON vengono mai iniettate nel prompt.",
            "settings_desc_enable_file_access": "Permetti all'AI di leggere/scrivere file di configurazione Home Assistant (automazioni, script, YAML)",
            "settings_desc_enable_file_upload": "[SPERIMENTALE] Permetti di caricare documenti (PDF, DOCX, TXT, MD, YAML) per l'analisi AI",
            "settings_desc_enable_voice_input": "Abilita il pulsante microfono per messaggi vocali (Groq Whisper, con fallback OpenAI/Google) \u2013 richiede HTTPS",
            "settings_desc_enable_rag": "[SPERIMENTALE] Abilita RAG (Retrieval-Augmented Generation) per ricerca documenti e iniezione contesto",
            "settings_desc_enable_chat_bubble": "Mostra una bolla chat AI flottante su ogni pagina di HA.",
            "settings_desc_enable_amira_card_button": "Mostra il pulsante Amira nel dialog dell'editor card Lovelace per la modifica assistita dall'AI.",
            "settings_desc_enable_amira_automation_button": "Mostra il pulsante Amira e l'aiuto flowchart nell'editor automazioni di Home Assistant.",
            "settings_desc_enable_mcp": "Abilita il supporto MCP (Model Context Protocol). Se disattivato, Amira non si connette agli MCP server all'avvio.",
            "mcp_config_path": "File di Configurazione",
            "settings_desc_mcp_config_file": "Percorso del file JSON di configurazione MCP",
            "settings_desc_fallback_enabled": "Se il provider primario fallisce, prova automaticamente il prossimo nella lista di priorit\u00e0",
            "settings_desc_anthropic_extended_thinking": "Abilita il pensiero esteso di Claude per compiti di ragionamento complesso (pi\u00f9 lento, usa pi\u00f9 token)",
            "settings_desc_anthropic_prompt_caching": "Memorizza nella cache istruzioni lunghe e ripetitive per risparmiare costi e migliorare la velocit\u00e0",
            "settings_desc_openai_extended_thinking": "Abilita modalit\u00e0 ragionamento o1/o3 per problemi complessi (pi\u00f9 lento, usa pi\u00f9 token)",
            "settings_desc_nvidia_thinking_mode": "Abilita modalit\u00e0 thinking per vedere il ragionamento dell'AI (pi\u00f9 lento ma pi\u00f9 trasparente)",
            "settings_desc_tts_voice": "Voce per le risposte parlate \u2013 selezionata automaticamente per la tua lingua (Edge TTS, gratis)",
            "settings_desc_enable_telegram": "Abilita o disabilita completamente il bot Telegram. Se disabilitato, i messaggi in arrivo vengono rifiutati con errore 503.",
            "settings_desc_telegram_bot_token": "Token bot Telegram da @BotFather \u2013 lascia vuoto per disabilitare",
            "settings_telegram_allowed_ids": "ID Utenti Autorizzati",
            "settings_desc_telegram_allowed_ids": "Lista di ID utente Telegram autorizzati, separati da virgola (es. 123456789,987654321). Lascia vuoto per permettere a tutti \u2013 sconsigliato.",
            "settings_desc_enable_whatsapp": "Abilita o disabilita completamente il bot WhatsApp (Twilio). Se disabilitato, i webhook in arrivo vengono rifiutati con errore 503.",
            "settings_desc_twilio_account_sid": "Tuo SID Account Twilio per l'integrazione WhatsApp \u2013 ottieni da console.twilio.com",
            "settings_desc_twilio_auth_token": "Tuo Token Auth Twilio per l'integrazione WhatsApp \u2013 ottieni da console.twilio.com",
            "settings_desc_twilio_whatsapp_from": "Tuo numero WhatsApp Twilio (es. +1234567890) \u2013 lascia vuoto per disabilitare",
            "settings_desc_enable_discord": "Abilita o disabilita completamente il bot Discord. Se disabilitato, i messaggi Discord in arrivo vengono ignorati.",
            "settings_desc_discord_bot_token": "Token bot Discord dal Discord Developer Portal \u2013 lascia vuoto per disabilitare",
            "settings_desc_discord_allowed_channel_ids": "Lista ID canali Discord autorizzati separati da virgola. Lascia vuoto per permettere tutti i canali.",
            "settings_desc_discord_allowed_user_ids": "Lista ID utenti Discord autorizzati separati da virgola. Lascia vuoto per permettere tutti gli utenti.",
            "settings_desc_timeout": "Timeout richieste API in secondi (predefinito 30, aumenta se le risposte sono lente)",
            "settings_desc_max_retries": "Numero massimo di tentativi per chiamate API fallite (predefinito 3)",
            "settings_desc_max_conversations": "Numero massimo di conversazioni da mantenere nello storico (1\u2013100)",
            "settings_desc_max_snapshots_per_file": "Numero massimo di backup per file. I pi\u00f9 vecchi vengono eliminati automaticamente al raggiungimento del limite.",
            "settings_desc_cost_currency": "Valuta per la visualizzazione dei costi token",
            "models_group_fixed": "Fissi",
            "models_group_dynamic_cache": "Dinamici (cache)",
            # Agent form
            "agent_add": "Nuovo Agent",
            "agent_new": "\U0001f916 Nuovo Agent",
            "agent_none": "Nessun agent configurato. Clicca \"Nuovo Agent\" per iniziare.",
            "agent_back": "Indietro",
            "agent_name": "Nome",
            "agent_desc": "Descrizione",
            "agent_tools": "Tools Consentiti",
            "agent_enabled": "Abilitato",
            "agent_id_label": "ID (univoco)",
            "agent_id_invalid": "L'ID deve contenere solo lettere minuscole, numeri, - e _",
            "agent_sysprompt_label": "Istruzioni Agente",
            "agent_sysprompt_hint": "Istruzioni opzionali aggiunte PRIMA del prompt di sistema predefinito. Esempio: Ti chiami Jarvis. L'utente si chiama Silvio.",
            "agent_delete_confirm": "Eliminare agent",
            "agent_protected": "Protetto (predefinito)",
            "agent_fallbacks": "Modelli di Fallback",
            "agent_temperature": "Temperatura (0-2)",
            "agent_thinking": "Ragionamento",
            "agent_maxtokens": "Max Token",
            "agent_default_flag": "Predefinito",
            "agent_tools_hint": "vuoto = tutti",
            # Tooltips agente
            "tip_agent_id": "Identificatore univoco. Usa minuscole, senza spazi (es. home, coder, energy).",
            "tip_agent_name": "Nome visualizzato nel selettore agente.",
            "tip_agent_emoji": "Icona mostrata accanto al nome dell'agente.",
            "tip_agent_desc": "Breve descrizione della specializzazione dell'agente.",
            "tip_agent_provider": "Provider AI (es. Anthropic, OpenAI). Lascia vuoto per usare quello predefinito.",
            "tip_agent_model": "Modello specifico da usare. Lascia vuoto per usare il predefinito del provider.",
            "tip_agent_fallbacks": "Modelli di riserva separati da virgola se il principale non \u00e8 disponibile.",
            "tip_agent_temperature": "Controlla la casualit\u00e0 (0=deterministico, 2=creativo). Default: 0.7.",
            "tip_agent_thinking": "Profondit\u00e0 del ragionamento: off, low, medium, high o adaptive.",
            "tip_agent_maxtokens": "Numero massimo di token per ogni risposta. Default: 4096.",
            "tip_agent_sysprompt": "Istruzioni aggiunte prima del prompt HA predefinito. L'AI mantiene tutto il contesto HA più le tue info personalizzate.",
            "tip_agent_tools": "Seleziona quali strumenti pu\u00f2 usare questo agente. Nessuno selezionato = tutti disponibili.",
            "tip_agent_default": "L'agente predefinito viene usato quando non ne viene selezionato uno specifico.",
            "tip_agent_enabled": "Gli agenti disabilitati sono nascosti dal selettore.",
            # MCP form
            "mcp_add_server": "Aggiungi Server",
            "mcp_server_name": "Nome Server",
            "mcp_command": "Comando",
            "mcp_args": "Argomenti",
            "mcp_env": "Variabili d'Ambiente",
            "mcp_pip_section": "Installa pacchetti pip",
            "mcp_install_btn": "Installa",
            "mcp_no_packages": "Nessun pacchetto specificato.",
            "mcp_installing": "Installazione in corso...",
            "mcp_done": "Completato.",
            "mcp_error": "Errore.",
            "mcp_start_failed": "Avvio MCP fallito",
            "mcp_stop_failed": "Arresto MCP fallito",
            "mcp_no_servers": "Nessun server MCP configurato. Clicca \"Aggiungi Server\" per connettere strumenti esterni.",
            "tip_mcp_name": "Nome univoco per il server MCP (es. filesystem, web_search).",
            "tip_mcp_command": "Comando per avviare il server (es. python, uvx, npx).",
            "tip_mcp_args": "Un argomento per riga. Es. -m, mcp.server.stdio.",
            "tip_mcp_env": "Uno per riga: CHIAVE=VALORE. Variabili d'ambiente per il server.",
            # System prompt form
            "prompt_chars": "caratteri",
            "prompt_reset": "Cancella",
            "prompt_hint": "Scrivi istruzioni personalizzate qui. Verranno aggiunte PRIMA del prompt di sistema predefinito.\nEsempio: Il nome dell'utente è Silvio Rossi. Rispondi sempre in italiano.",
            # Memory form
            "memory_hint": "Note in formato Markdown che l'AI ricorder\u00e0 tra le conversazioni...",
            "memory_lines": "righe",
            # Channel association
            "agent_channels": "Associazione Canali",
            "agent_channel_telegram": "Telegram",
            "agent_channel_whatsapp": "WhatsApp",
            "agent_channel_discord": "Discord",
            "agent_channel_taken": "Già assegnato a",
            "tip_agent_channels": "Associa questo agent a un canale di messaggistica. Ogni canale pu\u00f2 avere un solo agent.",
        },
        "es": {
            "change_model": "Cambiar modelo",
            "nvidia_test_title": "Test rápido NVIDIA (puede tardar unos segundos)",
            "nvidia_test_btn": "Test NVIDIA",
            "new_chat_title": "Nueva conversación",
            "new_chat_btn": "Nuevo chat",
            "conversations": "Conversaciones",
            "drag_resize": "Arrastra para redimensionar",
            "remove_image": "Eliminar imagen",
            "upload_image": "Subir imagen",
            "input_placeholder": "Escribe un mensaje...",
            "image_too_large": "La imagen es demasiado grande. Máximo 5MB.",
            "restore_backup": "Restaurar backup",
            "restore_backup_title": "Restaurar backup (snapshot: {id})",
            "confirm_restore": "¿Deseas restaurar el backup? Esta operación deshace el último cambio.",
            "restoring": "Restaurando...",
            "restored": "Restaurado",
            "backup_restored": "Backup restaurado. Si es necesario, actualiza la página Lovelace o verifica la automatización/script.",
            "restore_failed": "Restauración fallida.",
            "error_restore": "Error de restauración: ",
            "copy_btn": "Copiar",
            "copied": "¡Copiado!",
            "request_failed": "Solicitud fallida ({status}): {body}",
            "rate_limit_error": "Límite de velocidad superado. Espera un momento antes de reintentar.",
            "unexpected_response": "Respuesta inesperada del servidor.",
            "error_prefix": "Error: ",
            "connection_lost": "Conexión interrumpida. Inténtalo de nuevo.",
            "messages_count": "mensajes",
            "delete_chat": "Eliminar chat",
            "no_conversations": "Sin conversaciones",
            "confirm_delete": "¿Eliminar esta conversación?",
            "select_agent": "Selecciona un agente del menú superior para empezar. Puedes cambiarlo en cualquier momento.",
            "nvidia_tested": "Probados",
            "nvidia_to_test": "Por probar",
            "no_models": "Sin modelos disponibles",
            "models_load_error": "Error al cargar los modelos: ",
            "nvidia_test_result": "Test NVIDIA: OK {ok}, eliminados {removed}, probados {tested}/{total}",
            "nvidia_remaining": "restantes: {n} (pulsa de nuevo para continuar)",
            "nvidia_test_failed": "Test NVIDIA fallido",
            "switched_to": "Cambiado a {provider} \u2192 {model}",
            "provider_label": "Proveedor",
            "model_label": "Modelo",
            "web_html_warn": "⚠️ Proveedor web no oficial: la creación de dashboards HTML puede ser incompleta o malformada. Verifica siempre el archivo generado.",
            # Suggestions
            "sug_lights": "Mostrar todas las luces",
            "sug_sensors": "Estado de sensores",
            "sug_areas": "Habitaciones y áreas",
            "sug_temperature": "Historial de temperatura",
            "sug_scenes": "Escenas disponibles",
            "sug_automations": "Lista de automatizaciones",
            # Read-only mode
            "readonly_title": "Modo solo lectura: mostrar c\u00f3digo sin ejecutar",
            "readonly_on": "ON",
            "readonly_off": "OFF",
            "readonly_label": "Solo lectura",
            # Confirmation buttons
            "confirm_yes": "S\u00ed, confirma",
            "confirm_no": "No, cancela",
            "confirm_yes_value": "si",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Eliminar",
            "today": "Hoy",
            "yesterday": "Ayer",
            "days_ago": "hace {n} d\u00edas",
            "sending_request": "Enviando solicitud",
            "connected": "Conectado",
            "waiting_response": "Esperando respuesta",
            "remove_document": "Eliminar documento",
            "file_too_large": "Archivo demasiado grande (máx 10MB)",
            "uploading_document": "Subiendo documento...",
            "upload_failed": "Subida fallida",
            "upload_error": "Error de subida",
            "unknown_error": "Error desconocido",
            "document_uploaded": "Documento subido",
            "mic_not_supported": "El navegador no soporta grabación de audio. Usa HTTPS o un navegador compatible.",
            "mic_needs_https": "El micrófono requiere HTTPS. Solución rápida para Chrome: abre chrome://flags/#unsafely-treat-insecure-origin-as-secure, añade tu dirección HA (ej. http://192.168.x.x:8123), pon Enabled, reinicia Chrome. Si no, configura SSL en HA o usa localhost.",
            "mic_denied_settings": "Acceso al micrófono denegado. Ve a los ajustes del navegador para habilitarlo.",
            "mic_denied_icon": "Permiso de micrófono denegado. Haz clic en el icono 🔒 en la barra del navegador.",
            "mic_not_found": "No se encontró micrófono. Conecta un micrófono e inténtalo de nuevo.",
            "mic_in_use": "Micrófono en uso por otra app. Cierra las otras apps e inténtalo de nuevo.",
            "mic_error": "Error de micrófono",
            # Voice mode
            "voice_mode": "Modo voz",
            "voice_listening": "Escuchando...",
            "voice_processing": "Procesando audio...",
            "voice_tts_no_provider": "Salida de voz no disponible. Se necesita Edge TTS o una API key de Groq/OpenAI.",
            "voice_transcription_error": "Transcripción fallida. Inténtalo de nuevo.",
            "voice_speaking": "Hablando...",
            "voice_stop_speaking": "Detener reproducción",
            "wake_word_detected": "¡Amira activada! Habla ahora...",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
            "tab_amira": "Card",
            "tab_backups": "Copias",
            "tab_devices": "Bubble Devices",
            "tab_messaging": "📱 Mensajes",
            "tab_files": "\U0001f4c1 Archivos",
            "files_loading": "Cargando...",
            "files_empty": "Directorio vacío",
            "files_error": "Error al cargar",
            "files_close_panel": "Cerrar panel de archivo",
            "files_context_label": "Archivo de contexto:",
            "messaging_no_chats": "Sin chats de mensajes",
            "messaging_messages": "Mensajes",
            "messaging_delete": "Eliminar",
            "messaging_confirm_delete": "¿Eliminar este chat?",
            "no_backups": "Sin copias de seguridad",
            "restore": "Restaurar",
            "confirm_restore_backup": "¿Restaurar esta copia? El archivo actual será reemplazado.",
            "delete_backup": "Eliminar",
            "confirm_delete_backup": "¿Eliminar esta copia de seguridad permanentemente?",
            "download_backup": "Descargar",
            # Device manager
            "no_devices": "Sin dispositivos registrados",
            "enable_device": "Habilitar",
            "disable_device": "Deshabilitar",
            "rename_device": "Renombrar",
            "delete_device": "Eliminar",
            "confirm_delete_device": "¿Eliminar este dispositivo permanentemente?",
            "device_deleted": "Dispositivo eliminado",
            "device_updated": "Dispositivo actualizado",
            # Dark mode
            "dark_mode": "Tema oscuro",
            # Skills tab
            "tab_skills": "🧩 Skills",
            "skills_installed": "Instaladas",
            "skills_store": "Tienda",
            "skills_install_btn": "Instalar",
            "skills_installed_badge": "Instalada",
            "skills_delete_btn": "Eliminar",
            "skills_delete_confirm": "¿Eliminar esta skill?",
            "skills_empty": "No hay skills instaladas. Explora la tienda a continuación.",
            "skills_store_empty": "No hay skills disponibles en la tienda.",
            "skills_store_loading": "Cargando tienda...",
            "skills_store_error": "No se pudo cargar la tienda. Comprueba tu conexión a internet.",
            "skills_unavailable": "Skills no disponibles. Reinicia el add-on.",
            "skills_update_banner": "Actualización de skill disponible:",
            "skills_update_go": "Ir a Skills",
            "skills_update_btn": "Actualizar",
            "skills_refresh": "Actualizar",
            "skills_by": "por",
            "skills_requires_version": "Requiere Amira v{version}",
            "skills_hint": "Escribe /nombre-skill en el chat para usar una skill",
            # Costs tab
            "tab_costs": "Costes",
            "costs_today": "Hoy",
            "costs_by_model": "Por modelo",
            "costs_by_provider": "Por proveedor",
            "costs_history": "Últimos 7 días",
            "costs_no_data": "Sin datos de uso",
            "costs_reset": "Restablecer",
            "costs_reset_confirm": "¿Restablecer todas las estadísticas? No se puede deshacer.",
            "costs_requests": "solicitudes",
            # Config tab
            "tab_config": "\U0001f527 Config",
            "config_loading": "Cargando...",
            "config_save": "Guardar",
            "config_cancel": "Cancelar",
            "config_saved": "Guardado!",
            "config_save_error": "Error al guardar",
            "config_file_not_found": "Archivo no encontrado (se creará al guardar)",
            "config_agents_title": "Perfiles de Agente",
            "config_mcp_title": "Configuración MCP",
            "config_prompt_title": "Prompt de Sistema",
            "config_memory_title": "Memoria (MEMORY.md)",
            "config_llm_title": "Prioridad LLM",
            "config_model_cache_title": "Cache de Modelos",
            "llm_fallback_label": "Respaldo automatico",
            "llm_priority_label": "Orden de prioridad",
            "llm_no_key": "sin clave",
            "llm_saved": "Guardado!",
            "llm_fallback_on": "Si el proveedor principal falla, el sistema intentara el siguiente en la lista.",
            "llm_fallback_off": "Respaldo desactivado. Solo se usara el proveedor principal.",
            "fallback_notice": "Respaldo: {{from}} → {{to}}",
            # Settings
            "config_settings_title": "Configuracion",
            "settings_saved": "Configuracion guardada!",
            "settings_clear_models_cache": "Limpiar Cache de Modelos",
            "settings_clear_models_cache_confirm": "Quieres borrar ahora la cache de modelos dinamicos? Los modelos fijos seguiran disponibles.",
            "settings_clear_models_cache_done": "Cache de modelos limpiada!",
            "settings_clear_models_cache_error": "Error al limpiar la cache de modelos",
            "settings_refresh_models_cache": "Actualizar Cache de Modelos",
            "settings_refresh_models_cache_done": "Cache de modelos actualizada!",
            "settings_refresh_models_cache_error": "Error al actualizar la cache de modelos",
            "settings_model_cache_title": "Cache de Modelos",
            "settings_model_cache_loading": "Cargando cache de modelos...",
            "settings_model_cache_updated_at": "Actualizada",
            "settings_model_cache_fixed": "Modelos Fijos",
            "settings_model_cache_dynamic": "Modelos Dinamicos (cache)",
            "settings_model_cache_blocklist": "Modelos Bloqueados",
            "settings_model_cache_uncertain": "Resultados Inciertos",
            "settings_model_cache_nvidia_tested": "NVIDIA Probados OK",
            "settings_model_cache_empty": "Sin modelos",
            "restart_confirm": "Algunos cambios requieren un reinicio para aplicarse. \u00bfReiniciar el add-on ahora?",
            "restart_in_progress": "Reiniciando add-on...",
            "restart_failed": "Reinicio fallido",
            "settings_language": "Idioma",
            "settings_enable_memory": "Memoria",
            "settings_enable_file_access": "Acceso a Archivos",
            "settings_enable_file_upload": "Carga de Archivos",
            "settings_enable_voice_input": "Entrada de Voz",
            "settings_enable_rag": "RAG",
            "settings_enable_chat_bubble": "Burbuja Chat",
            "settings_enable_amira_card_button": "Bot\u00f3n Amira Card",
            "settings_enable_mcp": "Servidores MCP",
            "settings_fallback_enabled": "Respaldo Automatico",
            "settings_anthropic_thinking": "Pensamiento Anthropic",
            "settings_anthropic_caching": "Cache de Prompt",
            "settings_openai_thinking": "Pensamiento OpenAI",
            "settings_nvidia_thinking": "Pensamiento NVIDIA",
            "settings_tts_voice": "Voz TTS",
            "settings_enable_telegram": "Telegram",
            "settings_telegram_token": "Token Bot Telegram",
            "settings_enable_whatsapp": "WhatsApp",
            "settings_twilio_sid": "Twilio Account SID",
            "settings_twilio_token": "Twilio Auth Token",
            "settings_twilio_from": "Numero WhatsApp",
            "settings_enable_discord": "Discord",
            "settings_discord_token": "Token Bot Discord",
            "settings_discord_allowed_channels": "IDs Canales Autorizados",
            "settings_discord_allowed_users": "IDs Usuarios Autorizados",
            "settings_timeout": "Timeout (s)",
            "settings_max_retries": "Reintentos Max",
            "settings_max_conversations": "Conversaciones Max",
            "settings_max_snapshots": "Max Snapshots/Archivo",
            "settings_cost_currency": "Moneda",
            "settings_section_language": "Idioma",
            "settings_section_features": "Funcionalidades",
            "settings_section_ai": "IA",
            "settings_section_voice": "Voz",
            "settings_section_messaging": "Mensajeria",
            "settings_section_advanced": "Avanzado",
            "settings_section_costs": "Costos",
            # Settings descriptions
            "settings_desc_language": "Idioma de las respuestas de la IA (Ingl\u00e9s, Italiano, Espa\u00f1ol o Franc\u00e9s)",
            "settings_desc_enable_memory": "[EXPERIMENTAL] Memoria persistente \u2013 la IA solo recuerda lo que escribes en MEMORY.md entre sesiones. Las conversaciones pasadas NUNCA se inyectan en el prompt.",
            "settings_desc_enable_file_access": "Permitir a la IA leer/escribir archivos de configuraci\u00f3n de Home Assistant (automatizaciones, scripts, YAML)",
            "settings_desc_enable_file_upload": "[EXPERIMENTAL] Permitir subir documentos (PDF, DOCX, TXT, MD, YAML) para an\u00e1lisis de la IA",
            "settings_desc_enable_voice_input": "Habilitar bot\u00f3n de micr\u00f3fono para mensajes de voz (Groq Whisper, con fallback OpenAI/Google) \u2013 requiere HTTPS",
            "settings_desc_enable_rag": "[EXPERIMENTAL] Habilitar RAG (Generaci\u00f3n Aumentada por Recuperaci\u00f3n) para b\u00fasqueda de documentos e inyecci\u00f3n de contexto",
            "settings_desc_enable_chat_bubble": "Mostrar una burbuja de chat AI flotante en cada p\u00e1gina de HA.",
            "settings_desc_enable_amira_card_button": "Mostrar el bot\u00f3n Amira dentro del di\u00e1logo del editor de tarjetas Lovelace para edici\u00f3n asistida por AI.",
            "settings_desc_enable_mcp": "Habilitar soporte MCP (Model Context Protocol). Si est\u00e1 desactivado, Amira no se conecta a servidores MCP al inicio.",
            "mcp_config_path": "Archivo de Configuraci\u00f3n",
            "settings_desc_mcp_config_file": "Ruta al archivo JSON de configuraci\u00f3n MCP",
            "settings_desc_fallback_enabled": "Si el proveedor principal falla, intentar autom\u00e1ticamente el siguiente en la lista de prioridad",
            "settings_desc_anthropic_extended_thinking": "Habilitar pensamiento extendido de Claude para razonamiento complejo (m\u00e1s lento, usa m\u00e1s tokens)",
            "settings_desc_anthropic_prompt_caching": "Cachear instrucciones largas y repetitivas para ahorrar costes y mejorar la velocidad",
            "settings_desc_openai_extended_thinking": "Habilitar modo razonamiento o1/o3 para problemas complejos (m\u00e1s lento, usa m\u00e1s tokens)",
            "settings_desc_nvidia_thinking_mode": "Habilitar modo thinking para ver el razonamiento de la IA (m\u00e1s lento pero m\u00e1s transparente)",
            "settings_desc_tts_voice": "Voz para las respuestas habladas \u2013 seleccionada autom\u00e1ticamente seg\u00fan tu idioma (Edge TTS, gratis)",
            "settings_desc_enable_telegram": "Habilitar o deshabilitar el bot de Telegram. Cuando est\u00e1 desactivado, los mensajes entrantes se rechazan con error 503.",
            "settings_desc_telegram_bot_token": "Token bot Telegram de @BotFather \u2013 dejar vac\u00edo para desactivar",
            "settings_telegram_allowed_ids": "IDs de Usuarios Autorizados",
            "settings_desc_telegram_allowed_ids": "Lista de IDs de usuario de Telegram autorizados, separados por coma (ej. 123456789,987654321). Dejar vac\u00edo para permitir a todos \u2013 no recomendado.",
            "settings_desc_enable_whatsapp": "Habilitar o deshabilitar el bot de WhatsApp (Twilio). Cuando est\u00e1 desactivado, los webhooks entrantes se rechazan con error 503.",
            "settings_desc_twilio_account_sid": "Tu SID de Cuenta Twilio para la integraci\u00f3n WhatsApp \u2013 obt\u00e9n de console.twilio.com",
            "settings_desc_twilio_auth_token": "Tu Auth Token de Twilio para la integraci\u00f3n WhatsApp \u2013 obt\u00e9n de console.twilio.com",
            "settings_desc_twilio_whatsapp_from": "Tu n\u00famero WhatsApp Twilio (ej. +1234567890) \u2013 dejar vac\u00edo para desactivar",
            "settings_desc_enable_discord": "Habilitar o deshabilitar completamente el bot de Discord. Cuando est\u00e1 desactivado, los mensajes entrantes de Discord se ignoran.",
            "settings_desc_discord_bot_token": "Token del bot de Discord desde Discord Developer Portal \u2013 dejar vac\u00edo para desactivar",
            "settings_desc_discord_allowed_channel_ids": "Lista de IDs de canales de Discord permitidos, separados por coma. Dejar vac\u00edo para permitir todos los canales.",
            "settings_desc_discord_allowed_user_ids": "Lista de IDs de usuarios de Discord permitidos, separados por coma. Dejar vac\u00edo para permitir todos los usuarios.",
            "settings_desc_timeout": "Tiempo de espera de solicitudes API en segundos (predeterminado 30, aumentar si las respuestas son lentas)",
            "settings_desc_max_retries": "N\u00famero m\u00e1ximo de intentos para llamadas API fallidas (predeterminado 3)",
            "settings_desc_max_conversations": "N\u00famero m\u00e1ximo de conversaciones en el historial (1\u2013100)",
            "settings_desc_max_snapshots_per_file": "N\u00famero m\u00e1ximo de copias de seguridad por archivo. Las m\u00e1s antiguas se eliminan autom\u00e1ticamente.",
            "settings_desc_cost_currency": "Moneda para mostrar los costes de tokens",
            "models_group_fixed": "Fijos",
            "models_group_dynamic_cache": "Dinamicos (cache)",
            # Agent form
            "agent_add": "Nuevo Agente",
            "agent_new": "\U0001f916 Nuevo Agente",
            "agent_none": "No hay agentes configurados. Haz clic en \"Nuevo Agente\" para empezar.",
            "agent_back": "Atrás",
            "agent_name": "Nombre",
            "agent_desc": "Descripción",
            "agent_tools": "Herramientas Permitidas",
            "agent_enabled": "Habilitado",
            "agent_id_label": "ID (único)",
            "agent_id_invalid": "El ID solo puede contener letras minúsculas, números, - y _",
            "agent_sysprompt_label": "Instrucciones del Agente",
            "agent_sysprompt_hint": "Instrucciones opcionales añadidas ANTES del prompt de sistema. Ejemplo: Tu nombre es Jarvis. El usuario se llama Silvio.",
            "agent_delete_confirm": "Eliminar agente",
            "agent_protected": "Protegido (predeterminado)",
            "agent_fallbacks": "Modelos de Respaldo",
            "agent_temperature": "Temperatura (0-2)",
            "agent_thinking": "Razonamiento",
            "agent_maxtokens": "Max Tokens",
            "agent_default_flag": "Predeterminado",
            "agent_tools_hint": "vacío = todos",
            # Tooltips
            "tip_agent_id": "Identificador único. Usa minúsculas, sin espacios (ej. home, coder, energy).",
            "tip_agent_name": "Nombre que se muestra en el selector de agentes.",
            "tip_agent_emoji": "Icono junto al nombre del agente.",
            "tip_agent_desc": "Breve descripción de la especialidad del agente.",
            "tip_agent_provider": "Proveedor de IA (ej. Anthropic, OpenAI). Vacío = predeterminado.",
            "tip_agent_model": "Modelo específico. Vacío = modelo predeterminado del proveedor.",
            "tip_agent_fallbacks": "Modelos de respaldo separados por coma si el principal no está disponible.",
            "tip_agent_temperature": "Controla la aleatoriedad (0=determinista, 2=creativo). Default: 0.7.",
            "tip_agent_thinking": "Profundidad de razonamiento: off, low, medium, high o adaptive.",
            "tip_agent_maxtokens": "Número máximo de tokens por respuesta. Default: 4096.",
            "tip_agent_sysprompt": "Instrucciones añadidas antes del prompt HA predefinido. La IA mantiene todo el contexto HA más tu info personalizada.",
            "tip_agent_tools": "Selecciona las herramientas que puede usar. Ninguna = todas disponibles.",
            "tip_agent_default": "El agente predeterminado se usa cuando no se selecciona otro.",
            "tip_agent_enabled": "Los agentes deshabilitados se ocultan del selector.",
            # MCP form
            "mcp_add_server": "Añadir Servidor",
            "mcp_server_name": "Nombre del Servidor",
            "mcp_command": "Comando",
            "mcp_args": "Argumentos",
            "mcp_env": "Variables de Entorno",
            "mcp_pip_section": "Instalar paquetes pip",
            "mcp_install_btn": "Instalar",
            "mcp_no_packages": "No se especificaron paquetes.",
            "mcp_installing": "Instalando...",
            "mcp_done": "Hecho.",
            "mcp_error": "Error.",
            "mcp_start_failed": "Error al iniciar MCP",
            "mcp_stop_failed": "Error al detener MCP",
            "mcp_no_servers": "No hay servidores MCP. Haz clic en \"Añadir Servidor\" para conectar herramientas.",
            "tip_mcp_name": "Nombre único para el servidor MCP (ej. filesystem, web_search).",
            "tip_mcp_command": "Comando para iniciar el servidor (ej. python, uvx, npx).",
            "tip_mcp_args": "Un argumento por línea. Ej. -m, mcp.server.stdio.",
            "tip_mcp_env": "Uno por línea: CLAVE=VALOR. Variables de entorno del servidor.",
            # System prompt form
            "prompt_chars": "caracteres",
            "prompt_reset": "Limpiar",
            "prompt_hint": "Escribe instrucciones personalizadas aquí. Se añadirán al prompt de sistema enviado a la IA...",
            # Memory form
            "memory_hint": "Notas en Markdown que la IA recordará entre conversaciones...",
            "memory_lines": "líneas",
            # Channel association
            "agent_channels": "Asignación de Canal",
            "agent_channel_telegram": "Telegram",
            "agent_channel_whatsapp": "WhatsApp",
            "agent_channel_discord": "Discord",
            "agent_channel_taken": "Ya asignado a",
            "tip_agent_channels": "Asigna este agente a un canal de mensajería. Cada canal puede tener un único agente.",
        },
        "fr": {
            "change_model": "Changer de modèle",
            "nvidia_test_title": "Test rapide NVIDIA (peut prendre quelques secondes)",
            "nvidia_test_btn": "Test NVIDIA",
            "new_chat_title": "Nouvelle conversation",
            "new_chat_btn": "Nouveau chat",
            "conversations": "Conversations",
            "drag_resize": "Glisser pour redimensionner",
            "remove_image": "Supprimer l'image",
            "upload_image": "Télécharger une image",
            "input_placeholder": "Écris un message...",
            "image_too_large": "L'image est trop volumineuse. Maximum 5 Mo.",
            "restore_backup": "Restaurer la sauvegarde",
            "restore_backup_title": "Restaurer la sauvegarde (snapshot : {id})",
            "confirm_restore": "Veux-tu restaurer la sauvegarde ? Cette opération annule la dernière modification.",
            "restoring": "Restauration...",
            "restored": "Restauré",
            "backup_restored": "Sauvegarde restaurée. Si nécessaire, actualise la page Lovelace ou vérifie l'automatisation/script.",
            "restore_failed": "Restauration échouée.",
            "error_restore": "Erreur de restauration : ",
            "copy_btn": "Copier",
            "copied": "Copié !",
            "request_failed": "Requête échouée ({status}) : {body}",
            "rate_limit_error": "Limite de débit dépassée. Veuillez attendre un moment avant de réessayer.",
            "unexpected_response": "Réponse inattendue du serveur.",
            "error_prefix": "Erreur : ",
            "connection_lost": "Connexion interrompue. Réessaie.",
            "messages_count": "messages",
            "delete_chat": "Supprimer le chat",
            "no_conversations": "Aucune conversation",
            "confirm_delete": "Supprimer cette conversation ?",
            "select_agent": "Sélectionne un agent dans le menu en haut pour commencer. Tu pourras le changer à tout moment.",
            "nvidia_tested": "Testés",
            "nvidia_to_test": "À tester",
            "no_models": "Aucun modèle disponible",
            "models_load_error": "Erreur lors du chargement des modèles : ",
            "nvidia_test_result": "Test NVIDIA : OK {ok}, supprimés {removed}, testés {tested}/{total}",
            "nvidia_remaining": "restants : {n} (appuie à nouveau pour continuer)",
            "nvidia_test_failed": "Test NVIDIA échoué",
            "switched_to": "Passé à {provider} \u2192 {model}",
            "provider_label": "Fournisseur",
            "model_label": "Modèle",
            "web_html_warn": "⚠️ Fournisseur web non officiel : la création de dashboards HTML peut être incomplète ou malformée. Vérifie toujours le fichier généré.",
            # Suggestions
            "sug_lights": "Afficher toutes les lumières",
            "sug_sensors": "État des capteurs",
            "sug_areas": "Pièces et zones",
            "sug_temperature": "Historique température",
            "sug_scenes": "Scènes disponibles",
            "sug_automations": "Liste des automatisations",
            # Read-only mode
            "readonly_title": "Mode lecture seule : afficher le code sans ex\u00e9cuter",
            "readonly_on": "ON",
            "readonly_off": "OFF",
            "readonly_label": "Lecture seule",
            # Confirmation buttons
            "confirm_yes": "Oui, confirme",
            "confirm_no": "Non, annule",
            "confirm_yes_value": "oui",
            "confirm_no_value": "non",
            "confirm_delete_yes": "Supprimer",
            "today": "Aujourd'hui",
            "yesterday": "Hier",
            "days_ago": "il y a {n} jours",
            "sending_request": "Envoi de la requ\u00eate",
            "connected": "Connect\u00e9",
            "waiting_response": "En attente de r\u00e9ponse",
            "remove_document": "Supprimer le document",
            "file_too_large": "Fichier trop volumineux (max 10 Mo)",
            "uploading_document": "T\u00e9l\u00e9chargement du document...",
            "upload_failed": "T\u00e9l\u00e9chargement \u00e9chou\u00e9",
            "upload_error": "Erreur de t\u00e9l\u00e9chargement",
            "unknown_error": "Erreur inconnue",
            "document_uploaded": "Document t\u00e9l\u00e9charg\u00e9",
            "mic_not_supported": "Le navigateur ne prend pas en charge l'enregistrement audio. Utilisez HTTPS ou un navigateur compatible.",
            "mic_needs_https": "Le microphone nécessite HTTPS. Solution rapide pour Chrome : ouvrez chrome://flags/#unsafely-treat-insecure-origin-as-secure, ajoutez votre adresse HA (ex. http://192.168.x.x:8123), mettez Enabled, redémarrez Chrome. Sinon configurez SSL dans HA ou utilisez localhost.",
            "mic_denied_settings": "Acc\u00e8s au microphone refus\u00e9. Allez dans les param\u00e8tres du navigateur pour l'activer.",
            "mic_denied_icon": "Microphone refus\u00e9. Cliquez sur l'ic\u00f4ne \ud83d\udd12 dans la barre du navigateur.",
            "mic_not_found": "Aucun microphone trouv\u00e9. Connectez un microphone et r\u00e9essayez.",
            "mic_in_use": "Microphone utilis\u00e9 par une autre app. Fermez les autres apps et r\u00e9essayez.",
            "mic_error": "Erreur de microphone",
            # Voice mode
            "voice_mode": "Mode vocal",
            "voice_listening": "Écoute en cours...",
            "voice_processing": "Traitement audio...",
            "voice_tts_no_provider": "Sortie vocale indisponible. Edge TTS ou une clé API Groq/OpenAI est nécessaire.",
            "voice_transcription_error": "Échec de la transcription. Réessayez.",
            "voice_speaking": "En train de parler...",
            "voice_stop_speaking": "Arrêter la lecture",
            "wake_word_detected": "Amira activée ! Parlez maintenant...",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bulle",
            "tab_amira": "Card",
            "tab_backups": "Sauvegardes",
            "tab_devices": "Bubble Devices",
            "tab_messaging": "📱 Messages",
            "tab_files": "\U0001f4c1 Fichiers",
            "files_loading": "Chargement...",
            "files_empty": "Dossier vide",
            "files_error": "Erreur de chargement",
            "files_close_panel": "Fermer le panneau",
            "files_context_label": "Fichier de contexte:",
            "messaging_no_chats": "Pas de chats de messages",
            "messaging_messages": "Messages",
            "messaging_delete": "Supprimer",
            "messaging_confirm_delete": "Supprimer ce chat ?",
            "no_backups": "Aucune sauvegarde",
            "restore": "Restaurer",
            "confirm_restore_backup": "Restaurer cette sauvegarde ? Le fichier actuel sera remplacé.",
            "delete_backup": "Supprimer",
            "confirm_delete_backup": "Supprimer cette sauvegarde définitivement ?",
            "download_backup": "Télécharger",
            # Device manager
            "no_devices": "Aucun appareil enregistré",
            "enable_device": "Activer",
            "disable_device": "Désactiver",
            "rename_device": "Renommer",
            "delete_device": "Supprimer",
            "confirm_delete_device": "Supprimer définitivement cet appareil ?",
            "device_deleted": "Appareil supprimé",
            "device_updated": "Appareil mis à jour",
            # Dark mode
            "dark_mode": "Mode sombre",
            # Skills tab
            "tab_skills": "🧩 Skills",
            "skills_installed": "Installées",
            "skills_store": "Boutique",
            "skills_install_btn": "Installer",
            "skills_installed_badge": "Installée",
            "skills_delete_btn": "Supprimer",
            "skills_delete_confirm": "Supprimer cette skill ?",
            "skills_empty": "Aucune skill installée. Parcourez la boutique ci-dessous.",
            "skills_store_empty": "Aucune skill disponible dans la boutique.",
            "skills_store_loading": "Chargement de la boutique...",
            "skills_store_error": "Impossible de charger la boutique. Vérifiez votre connexion internet.",
            "skills_unavailable": "Skills non disponibles. Redémarrez l'add-on.",
            "skills_update_banner": "Mise à jour de skill disponible :",
            "skills_update_go": "Aller aux Skills",
            "skills_update_btn": "Mettre à jour",
            "skills_refresh": "Actualiser",
            "skills_by": "par",
            "skills_requires_version": "Nécessite Amira v{version}",
            "skills_hint": "Tapez /nom-skill dans le chat pour utiliser une skill",
            # Costs tab
            "tab_costs": "Coûts",
            "costs_today": "Aujourd'hui",
            "costs_by_model": "Par modèle",
            "costs_by_provider": "Par fournisseur",
            "costs_history": "7 derniers jours",
            "costs_no_data": "Aucune donnée d'utilisation",
            "costs_reset": "Réinitialiser",
            "costs_reset_confirm": "Réinitialiser toutes les statistiques ? Cette action est irréversible.",
            "costs_requests": "requêtes",
            # Config tab
            "tab_config": "\U0001f527 Config",
            "config_loading": "Chargement...",
            "config_save": "Enregistrer",
            "config_cancel": "Annuler",
            "config_saved": "Enregistré !",
            "config_save_error": "Erreur lors de l'enregistrement",
            "config_file_not_found": "Fichier non trouvé (sera créé à l'enregistrement)",
            "config_agents_title": "Profils d'Agent",
            "config_mcp_title": "Configuration MCP",
            "config_prompt_title": "Prompt Système Personnalisé",
            "config_memory_title": "Mémoire (MEMORY.md)",
            "config_llm_title": "Priorite LLM",
            "config_model_cache_title": "Cache Modeles",
            "llm_fallback_label": "Repli automatique",
            "llm_priority_label": "Ordre de priorite",
            "llm_no_key": "sans cle",
            "llm_saved": "Enregistre!",
            "llm_fallback_on": "Si le fournisseur principal echoue, le systeme essaiera le suivant dans la liste.",
            "llm_fallback_off": "Repli desactive. Seul le fournisseur principal sera utilise.",
            "fallback_notice": "Repli: {{from}} → {{to}}",
            # Settings
            "config_settings_title": "Parametres",
            "settings_saved": "Parametres enregistres!",
            "settings_clear_models_cache": "Vider le Cache Modeles",
            "settings_clear_models_cache_confirm": "Vider maintenant le cache des modeles dynamiques ? Les modeles fixes restent disponibles.",
            "settings_clear_models_cache_done": "Cache modeles vide !",
            "settings_clear_models_cache_error": "Echec du vidage du cache modeles",
            "settings_refresh_models_cache": "Rafraichir le Cache Modeles",
            "settings_refresh_models_cache_done": "Cache modeles rafraichi !",
            "settings_refresh_models_cache_error": "Echec du rafraichissement du cache modeles",
            "settings_model_cache_title": "Cache Modeles",
            "settings_model_cache_loading": "Chargement du cache modeles...",
            "settings_model_cache_updated_at": "Mis a jour",
            "settings_model_cache_fixed": "Modeles Fixes",
            "settings_model_cache_dynamic": "Modeles Dynamiques (cache)",
            "settings_model_cache_blocklist": "Modeles Bloques",
            "settings_model_cache_uncertain": "Resultats Incertains",
            "settings_model_cache_nvidia_tested": "NVIDIA Testes OK",
            "settings_model_cache_empty": "Aucun modele",
            "restart_confirm": "Certains changements n\u00e9cessitent un red\u00e9marrage. Red\u00e9marrer l'add-on maintenant ?",
            "restart_in_progress": "Red\u00e9marrage de l'add-on...",
            "restart_failed": "\u00c9chec du red\u00e9marrage",
            "settings_language": "Langue",
            "settings_enable_memory": "Memoire",
            "settings_enable_file_access": "Acces Fichiers",
            "settings_enable_file_upload": "Telechargement",
            "settings_enable_voice_input": "Entree Vocale",
            "settings_enable_rag": "RAG",
            "settings_enable_chat_bubble": "Bulle Chat",
            "settings_enable_amira_card_button": "Bouton Amira Card",
            "settings_enable_mcp": "Serveurs MCP",
            "settings_fallback_enabled": "Repli Automatique",
            "settings_anthropic_thinking": "Reflexion Anthropic",
            "settings_anthropic_caching": "Cache Prompt",
            "settings_openai_thinking": "Reflexion OpenAI",
            "settings_nvidia_thinking": "Reflexion NVIDIA",
            "settings_tts_voice": "Voix TTS",
            "settings_enable_telegram": "Telegram",
            "settings_telegram_token": "Token Bot Telegram",
            "settings_enable_whatsapp": "WhatsApp",
            "settings_twilio_sid": "Twilio Account SID",
            "settings_twilio_token": "Twilio Auth Token",
            "settings_twilio_from": "Numero WhatsApp",
            "settings_enable_discord": "Discord",
            "settings_discord_token": "Token Bot Discord",
            "settings_discord_allowed_channels": "IDs Canaux Autorisés",
            "settings_discord_allowed_users": "IDs Utilisateurs Autorisés",
            "settings_timeout": "Timeout (s)",
            "settings_max_retries": "Tentatives Max",
            "settings_max_conversations": "Conversations Max",
            "settings_max_snapshots": "Max Snapshots/Fichier",
            "settings_cost_currency": "Devise",
            "settings_section_language": "Langue",
            "settings_section_features": "Fonctionnalites",
            "settings_section_ai": "IA",
            "settings_section_voice": "Voix",
            "settings_section_messaging": "Messagerie",
            "settings_section_advanced": "Avance",
            "settings_section_costs": "Couts",
            # Settings descriptions
            "settings_desc_language": "Langue des r\u00e9ponses de l'IA (Anglais, Italien, Espagnol ou Fran\u00e7ais)",
            "settings_desc_enable_memory": "[EXP\u00c9RIMENTAL] M\u00e9moire persistante \u2013 l'IA ne retient que ce que vous \u00e9crivez dans MEMORY.md entre les sessions. Les conversations pass\u00e9es ne sont JAMAIS inject\u00e9es dans le prompt.",
            "settings_desc_enable_file_access": "Autoriser l'IA \u00e0 lire/\u00e9crire les fichiers de configuration Home Assistant (automatisations, scripts, YAML)",
            "settings_desc_enable_file_upload": "[EXP\u00c9RIMENTAL] Autoriser le t\u00e9l\u00e9chargement de documents (PDF, DOCX, TXT, MD, YAML) pour l'analyse IA",
            "settings_desc_enable_voice_input": "Activer le bouton microphone pour les messages vocaux (Groq Whisper, avec fallback OpenAI/Google) \u2013 n\u00e9cessite HTTPS",
            "settings_desc_enable_rag": "[EXP\u00c9RIMENTAL] Activer RAG (G\u00e9n\u00e9ration Augment\u00e9e par R\u00e9cup\u00e9ration) pour la recherche de documents et l'injection de contexte",
            "settings_desc_enable_chat_bubble": "Afficher une bulle de chat IA flottante sur chaque page HA.",
            "settings_desc_enable_amira_card_button": "Afficher le bouton Amira dans la bo\u00eete de dialogue de l'\u00e9diteur de cartes Lovelace pour l'\u00e9dition assist\u00e9e par IA.",
            "settings_desc_enable_mcp": "Activer le support MCP (Model Context Protocol). Si d\u00e9sactiv\u00e9, Amira ne se connecte pas aux serveurs MCP au d\u00e9marrage.",
            "settings_desc_fallback_enabled": "Si le fournisseur principal \u00e9choue, essayer automatiquement le suivant dans la liste de priorit\u00e9",
            "settings_desc_anthropic_extended_thinking": "Activer la pens\u00e9e \u00e9tendue de Claude pour le raisonnement complexe (plus lent, utilise plus de tokens)",
            "settings_desc_anthropic_prompt_caching": "Mettre en cache les instructions longues et r\u00e9p\u00e9titives pour \u00e9conomiser les co\u00fbts et am\u00e9liorer la vitesse",
            "settings_desc_openai_extended_thinking": "Activer le mode raisonnement o1/o3 pour les probl\u00e8mes complexes (plus lent, utilise plus de tokens)",
            "settings_desc_nvidia_thinking_mode": "Activer le mode thinking pour voir le raisonnement de l'IA (plus lent mais plus transparent)",
            "settings_desc_tts_voice": "Voix pour les r\u00e9ponses parl\u00e9es \u2013 s\u00e9lectionn\u00e9e automatiquement selon votre langue (Edge TTS, gratuit)",
            "settings_desc_enable_telegram": "Activer ou d\u00e9sactiver enti\u00e8rement le bot Telegram. Quand d\u00e9sactiv\u00e9, les messages entrants sont rejet\u00e9s avec erreur 503.",
            "settings_desc_telegram_bot_token": "Token bot Telegram de @BotFather \u2013 laisser vide pour d\u00e9sactiver",
            "settings_telegram_allowed_ids": "IDs Utilisateurs Autoris\u00e9s",
            "settings_desc_telegram_allowed_ids": "Liste d'IDs utilisateur Telegram autoris\u00e9s, s\u00e9par\u00e9s par virgule (ex. 123456789,987654321). Laisser vide pour autoriser tout le monde \u2013 d\u00e9conseill\u00e9.",
            "settings_desc_enable_whatsapp": "Activer ou d\u00e9sactiver enti\u00e8rement le bot WhatsApp (Twilio). Quand d\u00e9sactiv\u00e9, les webhooks entrants sont rejet\u00e9s avec erreur 503.",
            "settings_desc_twilio_account_sid": "Votre SID de Compte Twilio pour l'int\u00e9gration WhatsApp \u2013 obtenez de console.twilio.com",
            "settings_desc_twilio_auth_token": "Votre Auth Token Twilio pour l'int\u00e9gration WhatsApp \u2013 obtenez de console.twilio.com",
            "settings_desc_twilio_whatsapp_from": "Votre num\u00e9ro WhatsApp Twilio (ex. +1234567890) \u2013 laisser vide pour d\u00e9sactiver",
            "settings_desc_enable_discord": "Activer ou d\u00e9sactiver enti\u00e8rement le bot Discord. Quand d\u00e9sactiv\u00e9, les messages Discord entrants sont ignor\u00e9s.",
            "settings_desc_discord_bot_token": "Token du bot Discord depuis Discord Developer Portal \u2013 laisser vide pour d\u00e9sactiver",
            "settings_desc_discord_allowed_channel_ids": "Liste d'IDs de canaux Discord autoris\u00e9s, s\u00e9par\u00e9s par virgule. Laisser vide pour autoriser tous les canaux.",
            "settings_desc_discord_allowed_user_ids": "Liste d'IDs d'utilisateurs Discord autoris\u00e9s, s\u00e9par\u00e9s par virgule. Laisser vide pour autoriser tous les utilisateurs.",
            "settings_desc_timeout": "D\u00e9lai d'attente des requ\u00eates API en secondes (par d\u00e9faut 30, augmenter si les r\u00e9ponses sont lentes)",
            "settings_desc_max_retries": "Nombre maximal de tentatives pour les appels API \u00e9chou\u00e9s (par d\u00e9faut 3)",
            "settings_desc_max_conversations": "Nombre maximal de conversations dans l'historique (1\u2013100)",
            "settings_desc_max_snapshots_per_file": "Nombre maximal de sauvegardes par fichier. Les plus anciennes sont supprim\u00e9es automatiquement.",
            "settings_desc_cost_currency": "Devise pour l'affichage des co\u00fbts de tokens",
            "models_group_fixed": "Fixes",
            "models_group_dynamic_cache": "Dynamiques (cache)",
            # Agent form
            "agent_add": "Nouvel Agent",
            "agent_new": "\U0001f916 Nouvel Agent",
            "agent_none": "Aucun agent configuré. Cliquez sur \"Nouvel Agent\" pour commencer.",
            "agent_back": "Retour",
            "agent_name": "Nom",
            "agent_desc": "Description",
            "agent_tools": "Outils Autorisés",
            "agent_enabled": "Activé",
            "agent_id_label": "ID (unique)",
            "agent_id_invalid": "L'ID ne doit contenir que des lettres minuscules, chiffres, - et _",
            "agent_sysprompt_label": "Instructions de l'Agent",
            "agent_sysprompt_hint": "Instructions optionnelles ajoutées AVANT le prompt système par défaut. Exemple : Tu t'appelles Jarvis. L'utilisateur s'appelle Silvio.",
            "agent_delete_confirm": "Supprimer l'agent",
            "agent_protected": "Protégé (intégré)",
            "agent_fallbacks": "Modèles de Repli",
            "agent_temperature": "Température (0-2)",
            "agent_thinking": "Raisonnement",
            "agent_maxtokens": "Max Tokens",
            "agent_default_flag": "Par Défaut",
            "agent_tools_hint": "vide = tous",
            # Tooltips
            "tip_agent_id": "Identifiant unique. Minuscules, sans espaces (ex. home, coder, energy).",
            "tip_agent_name": "Nom affiché dans le sélecteur d'agent.",
            "tip_agent_emoji": "Icône à côté du nom de l'agent.",
            "tip_agent_desc": "Brève description de la spécialité de l'agent.",
            "tip_agent_provider": "Fournisseur IA (ex. Anthropic, OpenAI). Vide = par défaut.",
            "tip_agent_model": "Modèle spécifique. Vide = modèle par défaut du fournisseur.",
            "tip_agent_fallbacks": "Modèles de secours séparés par des virgules si le principal est indisponible.",
            "tip_agent_temperature": "Contrôle l'aléatoire (0=déterministe, 2=créatif). Défaut : 0.7.",
            "tip_agent_thinking": "Profondeur de raisonnement : off, low, medium, high ou adaptive.",
            "tip_agent_maxtokens": "Nombre max de tokens par réponse. Défaut : 4096.",
            "tip_agent_sysprompt": "Instructions ajoutées avant le prompt HA par défaut. L'IA conserve tout le contexte HA plus vos infos personnalisées.",
            "tip_agent_tools": "Sélectionnez les outils autorisés. Aucun = tous disponibles.",
            "tip_agent_default": "L'agent par défaut est utilisé quand aucun n'est sélectionné.",
            "tip_agent_enabled": "Les agents désactivés sont masqués du sélecteur.",
            # MCP form
            "mcp_add_server": "Ajouter Serveur",
            "mcp_server_name": "Nom du Serveur",
            "mcp_command": "Commande",
            "mcp_args": "Arguments",
            "mcp_env": "Variables d'Environnement",
            "mcp_pip_section": "Installer des paquets pip",
            "mcp_install_btn": "Installer",
            "mcp_no_packages": "Aucun paquet specifie.",
            "mcp_installing": "Installation en cours...",
            "mcp_done": "Termine.",
            "mcp_error": "Erreur.",
            "mcp_start_failed": "Demarrage MCP echoue",
            "mcp_stop_failed": "Arret MCP echoue",
            "mcp_no_servers": "Aucun serveur MCP configuré. Cliquez sur \"Ajouter Serveur\" pour connecter des outils.",
            "tip_mcp_name": "Nom unique pour le serveur MCP (ex. filesystem, web_search).",
            "tip_mcp_command": "Commande pour démarrer le serveur (ex. python, uvx, npx).",
            "tip_mcp_args": "Un argument par ligne. Ex. -m, mcp.server.stdio.",
            "tip_mcp_env": "Un par ligne : CLÉ=VALEUR. Variables d'environnement du serveur.",
            # System prompt form
            "prompt_chars": "caractères",
            "prompt_reset": "Effacer",
            "prompt_hint": "Écrivez des instructions personnalisées ici. Elles seront ajoutées au prompt système envoyé à l'IA...",
            # Memory form
            "memory_hint": "Notes en Markdown que l'IA retiendra entre les conversations...",
            "memory_lines": "lignes",
            # Channel association
            "agent_channels": "Attribution de Canal",
            "agent_channel_telegram": "Telegram",
            "agent_channel_whatsapp": "WhatsApp",
            "agent_channel_discord": "Discord",
            "agent_channel_taken": "Déjà assigné à",
            "tip_agent_channels": "Attribuez cet agent à un canal de messagerie. Chaque canal ne peut avoir qu'un seul agent.",
        },
    }
    ui_js = ui_js_all.get(ui_lang, ui_js_all["en"])
    ui_js_json = json.dumps(ui_js, ensure_ascii=False)

    # Tool descriptions for agent form (i18n)
    _tool_descs_all = {
        "en": {
            "update_automation": "Edit automation",
            "get_automations": "Load automations",
            "trigger_automation": "Trigger automation",
            "delete_automation": "Delete automation",
            "create_automation": "Create automation",
            "get_available_services": "Load available services",
            "get_events": "Load events",
            "get_history": "Load history",
            "get_scenes": "Load scenes",
            "activate_scene": "Activate scene",
            "get_scripts": "Load scripts",
            "run_script": "Run script",
            "update_script": "Edit script",
            "create_script": "Create script",
            "delete_script": "Delete script",
            "get_areas": "Load areas/rooms",
            "manage_areas": "Manage areas/rooms",
            "manage_entity": "Manage entity",
            "get_devices": "Load devices",
            "send_notification": "Send notification",
            "get_dashboards": "Load dashboards",
            "create_dashboard": "Create dashboard",
            "delete_dashboard": "Delete dashboard",
            "create_html_dashboard": "Create HTML dashboard",
            "read_config_file": "Read config file",
            "write_config_file": "Write config file",
            "list_config_files": "List config files",
            "manage_statistics": "Manage statistics",
            "get_entities": "Load entities",
            "get_entity_state": "Read entity state",
            "call_service": "Call service",
            "search_entities": "Search entities",
            "get_integration_entities": "Search integration entities",
        },
        "it": {
            "update_automation": "Modifica automazione",
            "get_automations": "Carica automazioni",
            "trigger_automation": "Avvia automazione",
            "delete_automation": "Elimina automazione",
            "create_automation": "Crea automazione",
            "get_available_services": "Carica servizi disponibili",
            "get_events": "Carica eventi",
            "get_history": "Carica storico",
            "get_scenes": "Carica scene",
            "activate_scene": "Attiva scena",
            "get_scripts": "Carica script",
            "run_script": "Esegui script",
            "update_script": "Modifica script",
            "create_script": "Crea script",
            "delete_script": "Elimina script",
            "get_areas": "Carica stanze",
            "manage_areas": "Gestisci stanze",
            "manage_entity": "Gestisci entità",
            "get_devices": "Carica dispositivi",
            "send_notification": "Invia notifica",
            "get_dashboards": "Carica dashboard",
            "create_dashboard": "Crea dashboard",
            "delete_dashboard": "Elimina dashboard",
            "create_html_dashboard": "Crea dashboard HTML",
            "read_config_file": "Leggi file config",
            "write_config_file": "Salva file config",
            "list_config_files": "Elenco file config",
            "manage_statistics": "Gestisci statistiche",
            "get_entities": "Carica dispositivi",
            "get_entity_state": "Leggi stato dispositivo",
            "call_service": "Esegui comando",
            "search_entities": "Cerca dispositivi",
            "get_integration_entities": "Cerca entità integrazione",
        },
        "es": {
            "update_automation": "Editar automatización",
            "get_automations": "Cargar automatizaciones",
            "trigger_automation": "Ejecutar automatización",
            "delete_automation": "Eliminar automatización",
            "create_automation": "Crear automatización",
            "get_available_services": "Cargar servicios disponibles",
            "get_events": "Cargar eventos",
            "get_history": "Cargar historial",
            "get_scenes": "Cargar escenas",
            "activate_scene": "Activar escena",
            "get_scripts": "Cargar scripts",
            "run_script": "Ejecutar script",
            "update_script": "Editar script",
            "create_script": "Crear script",
            "delete_script": "Eliminar script",
            "get_areas": "Cargar áreas/habitaciones",
            "manage_areas": "Gestionar áreas",
            "manage_entity": "Gestionar entidad",
            "get_devices": "Cargar dispositivos",
            "send_notification": "Enviar notificación",
            "get_dashboards": "Cargar dashboards",
            "create_dashboard": "Crear dashboard",
            "delete_dashboard": "Eliminar dashboard",
            "create_html_dashboard": "Crear dashboard HTML",
            "read_config_file": "Leer archivo config",
            "write_config_file": "Guardar archivo config",
            "list_config_files": "Listar archivos config",
            "manage_statistics": "Gestionar estadísticas",
            "get_entities": "Cargar entidades",
            "get_entity_state": "Leer estado entidad",
            "call_service": "Llamar servicio",
            "search_entities": "Buscar entidades",
            "get_integration_entities": "Buscar entidades integración",
        },
        "fr": {
            "update_automation": "Modifier automatisation",
            "get_automations": "Charger automatisations",
            "trigger_automation": "Déclencher automatisation",
            "delete_automation": "Supprimer automatisation",
            "create_automation": "Créer automatisation",
            "get_available_services": "Charger services disponibles",
            "get_events": "Charger événements",
            "get_history": "Charger historique",
            "get_scenes": "Charger scènes",
            "activate_scene": "Activer scène",
            "get_scripts": "Charger scripts",
            "run_script": "Exécuter script",
            "update_script": "Modifier script",
            "create_script": "Créer script",
            "delete_script": "Supprimer script",
            "get_areas": "Charger pièces/zones",
            "manage_areas": "Gérer pièces/zones",
            "manage_entity": "Gérer entité",
            "get_devices": "Charger appareils",
            "send_notification": "Envoyer notification",
            "get_dashboards": "Charger tableaux de bord",
            "create_dashboard": "Créer tableau de bord",
            "delete_dashboard": "Supprimer tableau de bord",
            "create_html_dashboard": "Créer tableau de bord HTML",
            "read_config_file": "Lire fichier config",
            "write_config_file": "Écrire fichier config",
            "list_config_files": "Lister fichiers config",
            "manage_statistics": "Gérer statistiques",
            "get_entities": "Charger entités",
            "get_entity_state": "Lire état entité",
            "call_service": "Appeler service",
            "search_entities": "Rechercher entités",
            "get_integration_entities": "Rechercher entités intégration",
        },
    }
    _tool_descs = _tool_descs_all.get(ui_lang, _tool_descs_all["en"])
    _tool_descs_json = json.dumps(_tool_descs, ensure_ascii=False)

    # Feature flags for UI elements
    file_upload_enabled = api.ENABLE_FILE_UPLOAD
    file_upload_display = "block" if file_upload_enabled else "none"
    voice_enabled = getattr(api, 'ENABLE_VOICE_INPUT', True)
    voice_display = "flex" if voice_enabled else "none"
    cost_currency = getattr(api, 'COST_CURRENCY', 'USD')

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{agent_name} - Home Assistant</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; height: 100vh; height: 100svh; display: flex; flex-direction: column; overflow-x: hidden; }}
        .main-container {{ display: flex; flex: 1; overflow: hidden; min-width: 0; }}
        .sidebar {{ width: 250px; min-width: 140px; max-width: 500px; background: white; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; overflow-y: auto; overflow-x: hidden; position: relative; }}
        .splitter {{ width: 8px; flex: 0 0 8px; cursor: col-resize; background: transparent; touch-action: none; }}
        .splitter:hover {{ background: rgba(0,0,0,0.08); }}
        @media (pointer: coarse) {{
            .splitter {{ width: 14px; flex: 0 0 14px; background: rgba(0,0,0,0.04); }}
            .splitter:active {{ background: rgba(0,0,0,0.12); }}
        }}
        body.resizing, body.resizing * {{ cursor: col-resize !important; user-select: none !important; }}
        .sidebar-header {{ padding: 12px; border-bottom: 1px solid #e0e0e0; font-weight: 600; font-size: 14px; color: #666; }}
        .sidebar-tabs {{ display: flex; flex-wrap: wrap; border-bottom: 1px solid #e0e0e0; background: #f8f9fa; }}
        .sidebar-tab {{ flex: 1 1 33%; min-width: 0; padding: 6px 2px; font-size: 11px; text-align: center; cursor: pointer; border: none; background: none; color: #666; transition: all 0.2s; border-bottom: 2px solid transparent; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .sidebar-tab.primary-tab {{ flex-basis: 25%; }}
        .sidebar-tab:hover {{ background: #f0f0f0; }}
        .sidebar-tab.active {{ color: #667eea; border-bottom-color: #667eea; font-weight: 600; }}
        .sidebar-tab-row-sep {{ width: 100%; height: 1px; background: #e0e0e0; flex-shrink: 0; }}
        .sidebar-content {{ flex: 1; overflow-y: auto; display: none; }}
        .sidebar-content.active {{ display: block; }}
        .chat-list {{ flex: 1; overflow-y: auto; }}
        .chat-item {{ padding: 14px 16px; margin: 4px 8px; border-radius: 12px; cursor: pointer; transition: all 0.25s ease; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%); border: 1px solid rgba(102, 126, 234, 0.08); position: relative; overflow: hidden; }}
        .chat-item::before {{ content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: linear-gradient(180deg, #667eea, #764ba2); border-radius: 0 4px 4px 0; opacity: 0; transition: opacity 0.25s; }}
        .chat-item:hover {{ background: linear-gradient(135deg, #eef1ff 0%, #e8edff 100%); transform: translateX(2px); box-shadow: 0 2px 12px rgba(102, 126, 234, 0.12); }}
        .chat-item:hover::before {{ opacity: 1; }}
        .chat-item.active {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-color: transparent; box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3); }}
        .chat-item.active::before {{ opacity: 0; }}
        .chat-item-title {{ font-size: 13px; color: #2d3748; font-weight: 500; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.4; }}
        .chat-item.active .chat-item-title {{ color: #ffffff; }}
        .chat-item-info {{ font-size: 11px; color: #8b95a5; font-weight: 400; }}
        .chat-item.active .chat-item-info {{ color: rgba(255,255,255,0.75); }}
        .chat-item-delete {{ color: #c53030; font-size: 16px; padding: 6px; opacity: 0.45; transition: all 0.25s ease; cursor: pointer; flex-shrink: 0; background: rgba(254, 226, 226, 0.5); border: 1.5px solid rgba(229, 62, 62, 0.15); border-radius: 8px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; }}
        .chat-item:hover .chat-item-delete {{ opacity: 1; background: rgba(254, 226, 226, 0.85); border-color: rgba(229, 62, 62, 0.3); }}
        .chat-item.active .chat-item-delete {{ color: #fff; background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.25); opacity: 0.7; }}
        .chat-item.active:hover .chat-item-delete {{ opacity: 1; }}
        .chat-item-delete:hover {{ color: #fff; background: #e53e3e; border-color: #e53e3e; transform: scale(1.12); opacity: 1 !important; box-shadow: 0 2px 8px rgba(229, 62, 62, 0.35); }}
        .chat-group-title {{ padding: 12px 16px 6px; font-size: 10px; color: #a0aec0; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }}
        .backup-list {{ padding: 0; }}
        .backup-item {{ padding: 10px 12px; border-bottom: 1px solid #f0f0f0; display: flex; flex-direction: column; gap: 4px; }}
        .backup-item:hover {{ background: #f8f9fa; }}
        .backup-file {{ font-size: 12px; color: #333; font-family: monospace; word-break: break-all; }}
        .backup-meta {{ display: flex; justify-content: space-between; align-items: center; }}
        .backup-date {{ font-size: 11px; color: #999; }}
        .backup-restore {{ font-size: 11px; color: #667eea; cursor: pointer; padding: 2px 8px; border-radius: 4px; border: 1px solid #667eea; background: none; transition: all 0.2s; }}
        .backup-restore:hover {{ background: #667eea; color: white; }}
        .backup-download {{ font-size: 11px; color: #48bb78; cursor: pointer; padding: 2px 8px; border-radius: 4px; border: 1px solid #48bb78; background: none; transition: all 0.2s; }}
        .backup-download:hover {{ background: #48bb78; color: white; }}
        .backup-delete {{ font-size: 11px; color: #e53e3e; cursor: pointer; padding: 2px 8px; border-radius: 4px; border: 1px solid #e53e3e; background: none; transition: all 0.2s; margin-left: 4px; }}
        .backup-delete:hover {{ background: #e53e3e; color: white; }}
        /* Device Manager Styles */
        .device-list {{ padding: 0; }}
        .device-item {{ padding: 10px 12px; border-bottom: 1px solid #f0f0f0; display: flex; flex-direction: column; gap: 6px; }}
        .device-item:hover {{ background: #f8f9fa; }}
        .device-name {{ font-size: 12px; font-weight: 500; color: #333; }}
        .device-meta {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
        .device-type {{ font-size: 11px; color: #666; background: #e8f0ff; padding: 2px 8px; border-radius: 3px; }}
        .device-status {{ font-size: 11px; }}
        .device-last-seen {{ font-size: 10px; color: #999; }}
        .device-buttons {{ display: flex; gap: 4px; }}
        .device-toggle {{ font-size: 11px; color: white; cursor: pointer; padding: 4px 10px; border-radius: 4px; border: none; background: #4caf50; transition: all 0.2s; }}
        .device-toggle:hover {{ opacity: 0.8; }}
        .device-rename {{ font-size: 11px; color: #667eea; cursor: pointer; padding: 4px 10px; border-radius: 4px; border: 1px solid #667eea; background: none; transition: all 0.2s; }}
        .device-rename:hover {{ background: #667eea; color: white; }}
        .device-delete {{ font-size: 11px; color: #e53e3e; cursor: pointer; padding: 4px 10px; border-radius: 4px; border: 1px solid #e53e3e; background: none; transition: all 0.2s; }}
        .device-delete:hover {{ background: #e53e3e; color: white; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; min-height: 0; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); min-width: 0; overflow-x: hidden; }}
        .header h1 {{ font-size: 18px; font-weight: 600; }}
        .header .badge {{ font-size: 11px; opacity: 1; background: rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 10px; font-weight: 500; letter-spacing: 0.3px; }}
        .header .new-chat {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 12px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
        .header .new-chat:hover {{ background: rgba(255,255,255,0.35); }}
        .model-selector {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 10px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; max-width: 160px; min-width: 0; }}
        .model-selector:hover {{ background: rgba(255,255,255,0.35); }}
        #modelSelectWrap {{ display: flex; gap: 5px; align-items: center; min-width: 0; }}
        #providerSelect {{ max-width: 130px; }}
        #modelSelect {{ max-width: 160px; }}
        #agentSelect {{ max-width: 120px; background: rgba(255,255,255,0.25); border: 1px solid rgba(255,255,255,0.5); color: white; padding: 4px 8px; border-radius: 14px; font-size: 11px; cursor: pointer; transition: background 0.2s; min-width: 0; }}
        #agentSelect:hover {{ background: rgba(255,255,255,0.4); }}
        .agent-indicator {{ display: none; font-size: 13px; padding: 2px 8px; border-radius: 10px; background: rgba(255,255,255,0.15); white-space: nowrap; }}
        .agent-indicator.active {{ display: inline-block; }}

        .model-selector option {{ background: #2c3e50; color: white; }}
        .model-selector optgroup {{ background: #1a252f; color: #aaa; font-style: normal; font-weight: 600; padding: 4px 0; }}
        .header .status {{ margin-left: auto; font-size: 12px; display: flex; align-items: center; gap: 6px; }}
        .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: {status_color}; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        #codexOAuthBanner {{ display:none; background:#fff3cd; border-bottom:2px solid #ffc107; padding:10px 20px; font-size:13px; color:#856404; align-items:center; gap:10px; flex-wrap:wrap; }}
        #codexOAuthBanner button {{ background:#ffc107; color:#333; border:none; border-radius:8px; padding:6px 14px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #codexOAuthBanner button:hover {{ background:#e0a800; }}
        #codexOAuthConnectedBanner {{ display:none; background:#d4edda; border-bottom:2px solid #28a745; padding:8px 20px; font-size:13px; color:#155724; align-items:center; gap:10px; flex-wrap:wrap; }}
        #codexOAuthConnectedBanner .codex-conn-info {{ display:flex; align-items:center; gap:8px; flex:1; min-width:0; }}
        #codexOAuthConnectedBanner .codex-conn-dot {{ width:8px; height:8px; border-radius:50%; background:#28a745; flex-shrink:0; }}
        #codexOAuthConnectedBanner .codex-conn-text {{ font-weight:600; }}
        #codexOAuthConnectedBanner .codex-conn-detail {{ opacity:0.75; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
        #codexOAuthConnectedBanner button {{ background:transparent; color:#155724; border:1px solid #28a745; border-radius:8px; padding:4px 12px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #codexOAuthConnectedBanner button:hover {{ background:#c3e6cb; }}
        #codexOAuthModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center; }}
        #codexOAuthModal.open {{ display:flex; }}
        .codex-modal-box {{ background:#fff; border-radius:16px; padding:28px 32px; max-width:520px; width:92%; box-shadow:0 8px 32px rgba(0,0,0,0.25); font-size:14px; color:#333; }}
        .codex-modal-box h3 {{ margin:0 0 16px; font-size:18px; color:#222; }}
        .codex-modal-step {{ background:#f7f7f7; border-radius:10px; padding:14px 16px; margin-bottom:14px; }}
        .codex-modal-step strong {{ display:block; margin-bottom:8px; color:#444; }}
        .codex-modal-step button {{ background:#667eea; color:#fff; border:none; border-radius:8px; padding:8px 18px; cursor:pointer; font-size:13px; font-weight:600; }}
        .codex-modal-step button:hover {{ background:#5a6fd6; }}
        .codex-modal-step textarea {{ width:100%; box-sizing:border-box; height:70px; padding:8px; border-radius:8px; border:1px solid #ddd; font-size:12px; font-family:monospace; resize:vertical; }}
        #codexOAuthStatus {{ margin-top:10px; padding:8px 12px; border-radius:8px; font-size:13px; display:none; }}
        #codexOAuthStatus.ok {{ background:#d4edda; color:#155724; display:block; }}
        #codexOAuthStatus.err {{ background:#f8d7da; color:#721c24; display:block; }}
        .codex-modal-actions {{ display:flex; gap:10px; justify-content:flex-end; margin-top:16px; }}
        .codex-modal-actions button {{ padding:8px 20px; border-radius:8px; border:none; cursor:pointer; font-size:13px; font-weight:600; }}
        .codex-modal-actions .btn-primary {{ background:#667eea; color:#fff; }}
        .codex-modal-actions .btn-primary:hover {{ background:#5a6fd6; }}
        .codex-modal-actions .btn-secondary {{ background:#e0e0e0; color:#333; }}
        .codex-modal-actions .btn-secondary:hover {{ background:#c8c8c8; }}
        #copilotOAuthBanner {{ display:none; background:#dbeafe; border-bottom:2px solid #0969da; padding:10px 20px; font-size:13px; color:#0a3069; align-items:center; gap:10px; flex-wrap:wrap; }}
        #copilotOAuthBanner button {{ background:#0969da; color:#fff; border:none; border-radius:8px; padding:6px 14px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #copilotOAuthBanner button:hover {{ background:#0758b8; }}
        #copilotOAuthConnectedBanner {{ display:none; background:#d4edda; border-bottom:2px solid #28a745; padding:8px 20px; font-size:13px; color:#155724; align-items:center; gap:10px; flex-wrap:wrap; }}
        #copilotOAuthConnectedBanner .copilot-conn-info {{ display:flex; align-items:center; gap:8px; flex:1; min-width:0; }}
        #copilotOAuthConnectedBanner .copilot-conn-dot {{ width:8px; height:8px; border-radius:50%; background:#28a745; flex-shrink:0; }}
        #copilotOAuthConnectedBanner .copilot-conn-text {{ font-weight:600; }}
        #copilotOAuthConnectedBanner .copilot-conn-detail {{ opacity:0.75; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
        #copilotOAuthConnectedBanner button {{ background:transparent; color:#155724; border:1px solid #28a745; border-radius:8px; padding:4px 12px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #copilotOAuthConnectedBanner button:hover {{ background:#c3e6cb; }}
        #copilotOAuthModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center; }}
        #copilotOAuthModal.open {{ display:flex; }}
        .copilot-modal-box {{ background:#fff; border-radius:16px; padding:28px 32px; max-width:480px; width:92%; box-shadow:0 8px 32px rgba(0,0,0,0.25); font-size:14px; color:#333; }}
        .copilot-modal-box h3 {{ margin:0 0 16px; font-size:18px; color:#222; }}
        .copilot-user-code {{ font-size:28px; font-weight:700; letter-spacing:4px; color:#0969da; text-align:center; padding:18px 0 10px; }}
        .copilot-poll-hint {{ font-size:12px; color:#666; text-align:center; margin-bottom:8px; }}
        #copilotOAuthStatus {{ margin-top:10px; padding:8px 12px; border-radius:8px; font-size:13px; display:none; }}
        #copilotOAuthStatus.ok {{ background:#d4edda; color:#155724; display:block; }}
        #copilotOAuthStatus.err {{ background:#f8d7da; color:#721c24; display:block; }}
        #copilotOAuthStatus.pending {{ background:#e8f4f8; color:#0a5e8a; display:block; }}
        .copilot-modal-actions {{ display:flex; gap:10px; justify-content:flex-end; margin-top:16px; }}
        .copilot-modal-actions button {{ padding:8px 20px; border-radius:8px; border:none; cursor:pointer; font-size:13px; font-weight:600; }}
        .copilot-modal-actions .btn-primary {{ background:#0969da; color:#fff; }}
        .copilot-modal-actions .btn-primary:hover {{ background:#0758b8; }}
        .copilot-modal-actions .btn-secondary {{ background:#e0e0e0; color:#333; }}
        .copilot-modal-actions .btn-secondary:hover {{ background:#c8c8c8; }}
        /* Claude Web session banner/modal */
        #claudeWebBanner {{ display:none; background:#fde8d8; border-bottom:2px solid #e07042; padding:10px 20px; font-size:13px; color:#7b3010; align-items:center; gap:10px; flex-wrap:wrap; }}
        #claudeWebBanner button {{ background:#e07042; color:#fff; border:none; border-radius:8px; padding:6px 14px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #claudeWebBanner button:hover {{ background:#c45e32; }}
        #claudeWebConnectedBanner {{ display:none; background:#d4edda; border-bottom:2px solid #28a745; padding:8px 20px; font-size:13px; color:#155724; align-items:center; gap:10px; flex-wrap:wrap; }}
        #claudeWebConnectedBanner .cw-conn-info {{ display:flex; align-items:center; gap:8px; flex:1; min-width:0; }}
        #claudeWebConnectedBanner .cw-conn-dot {{ width:8px; height:8px; border-radius:50%; background:#28a745; flex-shrink:0; }}
        #claudeWebConnectedBanner .cw-conn-text {{ font-weight:600; }}
        #claudeWebConnectedBanner .cw-conn-detail {{ opacity:0.75; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
        #claudeWebConnectedBanner button {{ background:transparent; color:#155724; border:1px solid #28a745; border-radius:8px; padding:4px 12px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #claudeWebConnectedBanner button:hover {{ background:#c3e6cb; }}
        #claudeWebModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center; }}
        #claudeWebModal.open {{ display:flex; }}
        .claudeweb-modal-box {{ background:#fff; border-radius:16px; padding:28px 32px; max-width:520px; width:92%; box-shadow:0 8px 32px rgba(0,0,0,0.25); font-size:14px; color:#333; }}
        .claudeweb-modal-box h3 {{ margin:0 0 16px; font-size:18px; color:#222; }}
        .claudeweb-modal-step {{ background:#f7f7f7; border-radius:10px; padding:14px 16px; margin-bottom:14px; }}
        .claudeweb-modal-step strong {{ display:block; margin-bottom:8px; color:#444; }}
        .claudeweb-modal-step textarea {{ width:100%; box-sizing:border-box; height:70px; padding:8px; border-radius:8px; border:1px solid #ddd; font-size:12px; font-family:monospace; resize:vertical; }}
        #claudeWebStatus {{ margin-top:10px; padding:8px 12px; border-radius:8px; font-size:13px; display:none; }}
        #claudeWebStatus.ok {{ background:#d4edda; color:#155724; display:block; }}
        #claudeWebStatus.err {{ background:#f8d7da; color:#721c24; display:block; }}
        .claudeweb-modal-actions {{ display:flex; gap:10px; justify-content:flex-end; margin-top:16px; }}
        .claudeweb-modal-actions button {{ padding:8px 20px; border-radius:8px; border:none; cursor:pointer; font-size:13px; font-weight:600; }}
        .claudeweb-modal-actions .btn-primary {{ background:#e07042; color:#fff; }}
        .claudeweb-modal-actions .btn-primary:hover {{ background:#c45e32; }}
        .claudeweb-modal-actions .btn-secondary {{ background:#e0e0e0; color:#333; }}
        .claudeweb-modal-actions .btn-secondary:hover {{ background:#c8c8c8; }}
        /* ChatGPT Web session banner/modal */
        #chatgptWebBanner {{ display:none; background:#fff8e1; border-bottom:2px solid #f59e0b; padding:10px 20px; font-size:13px; color:#7c4a00; align-items:center; gap:10px; flex-wrap:wrap; }}
        #chatgptWebBanner.configured {{ background:#e8f5e9; border-color:#4caf50; color:#1b5e20; }}
        #chatgptWebBanner button {{ background:#f59e0b; color:#fff; border:none; border-radius:8px; padding:6px 14px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #chatgptWebBanner.configured button {{ background:#4caf50; }}
        #chatgptWebBanner.configured button:hover {{ background:#388e3c; }}
        #chatgptWebBanner button:hover {{ background:#d97706; }}
        #geminiWebBanner {{ display:none; background:#e8f4fd; border-bottom:2px solid #4a90c2; padding:10px 20px; font-size:13px; color:#0f4c75; align-items:center; gap:10px; flex-wrap:wrap; }}
        #geminiWebBanner button {{ background:#4a90c2; color:#fff; border:none; border-radius:8px; padding:6px 14px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #geminiWebBanner button:hover {{ background:#3e7aa6; }}
        #geminiWebConnectedBanner {{ display:none; background:#d4edda; border-bottom:2px solid #28a745; padding:8px 20px; font-size:13px; color:#155724; align-items:center; gap:10px; flex-wrap:wrap; }}
        #geminiWebConnectedBanner .gw-conn-info {{ display:flex; align-items:center; gap:8px; flex:1; min-width:0; }}
        #geminiWebConnectedBanner .gw-conn-dot {{ width:8px; height:8px; border-radius:50%; background:#28a745; flex-shrink:0; }}
        #geminiWebConnectedBanner .gw-conn-text {{ font-weight:600; }}
        #geminiWebConnectedBanner .gw-conn-detail {{ opacity:0.75; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
        #geminiWebConnectedBanner button {{ background:transparent; color:#155724; border:1px solid #28a745; border-radius:8px; padding:4px 12px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #geminiWebConnectedBanner button:hover {{ background:#c3e6cb; }}
        #perplexityWebBanner {{ display:none; background:#efe8fb; border-bottom:2px solid #8a63d2; padding:10px 20px; font-size:13px; color:#4d2f74; align-items:center; gap:10px; flex-wrap:wrap; }}
        #perplexityWebBanner button {{ background:#8a63d2; color:#fff; border:none; border-radius:8px; padding:6px 14px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #perplexityWebBanner button:hover {{ background:#744fba; }}
        #perplexityWebConnectedBanner {{ display:none; background:#d4edda; border-bottom:2px solid #28a745; padding:8px 20px; font-size:13px; color:#155724; align-items:center; gap:10px; flex-wrap:wrap; }}
        #perplexityWebConnectedBanner .gw-conn-info {{ display:flex; align-items:center; gap:8px; flex:1; min-width:0; }}
        #perplexityWebConnectedBanner .gw-conn-dot {{ width:8px; height:8px; border-radius:50%; background:#28a745; flex-shrink:0; }}
        #perplexityWebConnectedBanner .gw-conn-text {{ font-weight:600; }}
        #perplexityWebConnectedBanner .gw-conn-detail {{ opacity:0.75; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
        #perplexityWebConnectedBanner button {{ background:transparent; color:#155724; border:1px solid #28a745; border-radius:8px; padding:4px 12px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }}
        #perplexityWebConnectedBanner button:hover {{ background:#c3e6cb; }}
        #chatgptWebModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center; }}
        #chatgptWebModal.open {{ display:flex; }}
        #geminiWebModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center; }}
        #geminiWebModal.open {{ display:flex; }}
        #perplexityWebModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center; }}
        #perplexityWebModal.open {{ display:flex; }}
        .gemini-web-modal-box {{ background:#fff; border-radius:16px; padding:28px 32px; max-width:500px; width:92%; box-shadow:0 8px 32px rgba(0,0,0,0.25); font-size:14px; color:#333; }}
        .gemini-web-modal-box h3 {{ margin:0 0 16px; font-size:18px; color:#222; }}
        .modal-step {{ background:#f7f7f7; border-radius:10px; padding:14px 16px; margin-bottom:14px; }}
        .chatgptweb-modal-box {{ background:#fff; border-radius:16px; padding:28px 32px; max-width:520px; width:92%; box-shadow:0 8px 32px rgba(0,0,0,0.25); font-size:14px; color:#333; }}
        .chatgptweb-modal-box h3 {{ margin:0 0 16px; font-size:18px; color:#222; }}
        .chatgptweb-modal-step {{ background:#f7f7f7; border-radius:10px; padding:14px 16px; margin-bottom:14px; }}
        .chatgptweb-modal-step strong {{ display:block; margin-bottom:8px; color:#444; }}
        .chatgptweb-modal-step textarea {{ width:100%; box-sizing:border-box; height:70px; padding:8px; border-radius:8px; border:1px solid #ddd; font-size:12px; font-family:monospace; resize:vertical; }}
        #chatgptWebStatus {{ margin-top:10px; padding:8px 12px; border-radius:8px; font-size:13px; display:none; }}
        #chatgptWebStatus.ok {{ background:#d4edda; color:#155724; display:block; }}
        #chatgptWebStatus.err {{ background:#f8d7da; color:#721c24; display:block; }}
        .chatgptweb-modal-actions {{ display:flex; gap:10px; justify-content:flex-end; margin-top:16px; }}
        .chatgptweb-modal-actions button {{ padding:8px 20px; border-radius:8px; border:none; cursor:pointer; font-size:13px; font-weight:600; }}
        .chatgptweb-modal-actions .btn-primary {{ background:#19c37d; color:#fff; }}
        .chatgptweb-modal-actions .btn-primary:hover {{ background:#13a068; }}
        .chatgptweb-modal-actions .btn-secondary {{ background:#e0e0e0; color:#333; }}
        .chatgptweb-modal-actions .btn-secondary:hover {{ background:#c8c8c8; }}
        /* Messaging chat modal */
        #messagingChatModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.55); z-index:9999; align-items:center; justify-content:center; }}
        #messagingChatModal.open {{ display:flex; }}
        .msg-modal-box {{ background:#fff; border-radius:16px; width:min(600px,96vw); max-height:80vh; display:flex; flex-direction:column; box-shadow:0 8px 40px rgba(0,0,0,0.3); overflow:hidden; }}
        .msg-modal-header {{ display:flex; align-items:center; justify-content:space-between; padding:14px 20px; border-bottom:1px solid #eee; font-size:15px; font-weight:600; background:#f9f9f9; }}
        .msg-modal-header button {{ background:none; border:none; font-size:20px; cursor:pointer; color:#666; line-height:1; padding:2px 6px; border-radius:6px; }}
        .msg-modal-header button:hover {{ background:#eee; }}
        .msg-modal-body {{ flex:1; overflow-y:auto; padding:16px 18px; display:flex; flex-direction:column; gap:10px; }}
        .msg-bubble {{ max-width:80%; padding:10px 14px; border-radius:16px; font-size:13px; line-height:1.5; word-wrap:break-word; overflow-wrap:anywhere; white-space:pre-wrap; }}
        .msg-bubble.user {{ align-self:flex-end; background:#2196F3; color:#fff; border-bottom-right-radius:4px; }}
        .msg-bubble.assistant {{ align-self:flex-start; background:#f0f0f0; color:#222; border-bottom-left-radius:4px; }}
        .msg-bubble.assistant.error {{ background:#fde8e8; color:#b71c1c; }}
        .msg-bubble-label {{ font-size:10px; font-weight:600; opacity:0.65; margin-bottom:3px; }}
        .theme-dark .msg-modal-box {{ background:#1e1e1e; color:#e8e8e8; }}
        .theme-dark .msg-modal-header {{ background:#2a2a2a; border-bottom:1px solid #444; }}
        .theme-dark .msg-modal-header button {{ color:#aaa; }}
        .theme-dark .msg-modal-header button:hover {{ background:#333; }}
        .theme-dark .msg-bubble.assistant {{ background:#2c2c2c; color:#ddd; }}
        .theme-dark .msg-bubble.assistant.error {{ background:#3c1e1e; color:#f48; }}
        /* Messaging chat list cards */
        .messaging-list {{ display:flex; flex-direction:column; gap:8px; padding:10px 8px; }}
        .messaging-card {{ background:#fff; border:1px solid #e8e8e8; border-radius:14px; padding:12px 14px; cursor:pointer; transition:box-shadow 0.15s,border-color 0.15s; display:flex; flex-direction:column; gap:6px; }}
        .messaging-card:hover {{ box-shadow:0 3px 14px rgba(0,0,0,0.1); border-color:#bbb; }}
        .messaging-card-header {{ display:flex; align-items:center; justify-content:space-between; gap:8px; }}
        .messaging-card-channel {{ display:flex; align-items:center; gap:6px; }}
        .messaging-card-badge {{ display:inline-flex; align-items:center; gap:4px; font-size:11px; font-weight:700; padding:3px 8px; border-radius:20px; letter-spacing:0.3px; }}
        .messaging-card-badge.telegram {{ background:#e3f2fd; color:#1565c0; }}
        .messaging-card-badge.whatsapp {{ background:#e8f5e9; color:#2e7d32; }}
        .messaging-card-badge.discord {{ background:#ecebff; color:#4b57d6; }}
        .messaging-card-uid {{ font-size:11px; color:#999; font-family:monospace; }}
        .messaging-card-delete {{ background:none; border:none; cursor:pointer; color:#bbb; font-size:14px; padding:2px 6px; border-radius:6px; line-height:1; transition:color 0.15s,background 0.15s; }}
        .messaging-card-delete:hover {{ color:#e53935; background:#fde8e8; }}
        .messaging-card-preview {{ font-size:12px; color:#555; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height:1.4; }}
        .messaging-card-footer {{ display:flex; align-items:center; justify-content:space-between; }}
        .messaging-card-count {{ font-size:11px; color:#888; display:flex; align-items:center; gap:3px; }}
        .messaging-card-time {{ font-size:10px; color:#bbb; }}
        .theme-dark .messaging-card {{ background:#252525; border-color:#3a3a3a; }}
        .theme-dark .messaging-card:hover {{ box-shadow:0 3px 14px rgba(0,0,0,0.35); border-color:#555; }}
        .theme-dark .messaging-card-uid {{ color:#666; }}
        .theme-dark .messaging-card-preview {{ color:#999; }}
        .theme-dark .messaging-card-count {{ color:#666; }}
        .theme-dark .messaging-card-time {{ color:#555; }}
        .theme-dark .messaging-card-badge.telegram {{ background:#1a2a3a; color:#64b5f6; }}
        .theme-dark .messaging-card-badge.whatsapp {{ background:#1a2e1a; color:#81c784; }}
        .theme-dark .messaging-card-badge.discord {{ background:#25233c; color:#a8b2ff; }}
        .theme-dark .messaging-card-delete {{ color:#555; }}
        .theme-dark .messaging-card-delete:hover {{ color:#ef9a9a; background:#3c1e1e; }}
        .chat-container {{ flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }}
        .message {{ max-width: 85%; padding: 12px 16px; border-radius: 16px; line-height: 1.5; font-size: 14px; word-wrap: break-word; overflow-wrap: anywhere; animation: fadeIn 0.3s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .message.user {{ background: #667eea; color: white; align-self: flex-end; border-bottom-right-radius: 4px; white-space: pre-wrap; tab-size: 2; }}
        .message.user.long {{ max-height: 320px; overflow: auto; }}
        .message.user .user-text {{ white-space: pre-wrap; }}
        .message.user .user-code-block {{ margin-top: 8px; background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.35); border-radius: 10px; overflow: hidden; }}
        .message.user .user-code-label {{ padding: 4px 8px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; background: rgba(0,0,0,0.2); }}
        .message.user .user-code-block pre {{ margin: 0; padding: 10px; max-height: 260px; overflow: auto; white-space: pre; font-size: 12px; line-height: 1.4; font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
        .message.user img {{ max-width: 200px; max-height: 200px; border-radius: 8px; margin-top: 8px; display: block; }}
        .message.assistant {{ background: white; color: #333; align-self: flex-start; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .code-block {{ position: relative; margin: 8px 0; max-height: 340px; overflow: hidden; }}
        .code-block .copy-button {{ position: absolute; top: 8px; right: 8px; background: #667eea; color: white; border: none; border-radius: 6px; padding: 4px 10px; font-size: 11px; cursor: pointer; opacity: 0.8; transition: all 0.2s; z-index: 1; }}
        .code-block .copy-button:hover {{ opacity: 1; background: #5a6fd6; }}
        .code-block .copy-button.copied {{ background: #10b981; }}
        .code-block pre {{ max-height: 320px !important; overflow: auto !important; display: block; }}
        .message.assistant pre {{ background: #f5f5f5; padding: 10px; border-radius: 8px; max-height: 320px; overflow: auto; margin: 0; font-size: 13px; white-space: pre; word-break: normal; overflow-wrap: normal; }}
        .message.assistant code {{ background: #f0f0f0; padding: 1px 5px; border-radius: 4px; font-size: 13px; }}
        .message.assistant pre code {{ background: none; padding: 0; }}
        /* Collapsible details blocks */
        .message.assistant details {{ margin: 8px 0; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }}
        .message.assistant details summary {{ cursor: pointer; padding: 8px 12px; font-weight: 600; font-size: 14px; background: #f5f5f5; user-select: none; }}
        .message.assistant details summary:hover {{ background: #667eea; color: #fff; }}
        .message.assistant details > div {{ max-height: 200px; overflow-y: auto; padding: 8px 12px; font-size: 13px; line-height: 1.6; }}
        .message.assistant details code {{ background: rgba(0,0,0,0.06); padding: 1px 4px; border-radius: 3px; font-size: 12px; }}
        .diff-side {{ overflow-x: auto; margin: 10px 0; border-radius: 8px; border: 1px solid #e1e4e8; }}
        .diff-table {{ width: 100%; border-collapse: collapse; font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace; font-size: 11px; table-layout: fixed; }}
        .diff-table th {{ padding: 6px 10px; background: #f6f8fa; border-bottom: 1px solid #e1e4e8; text-align: left; font-size: 11px; font-weight: 600; width: 50%; }}
        .diff-th-old {{ color: #cb2431; }}
        .diff-th-new {{ color: #22863a; border-left: 1px solid #e1e4e8; }}
        .diff-table td {{ padding: 1px 8px; white-space: pre-wrap; word-break: break-all; vertical-align: top; font-size: 11px; line-height: 1.5; }}
        .diff-eq {{ color: #586069; }}
        .diff-del {{ background: #ffeef0; color: #cb2431; }}
        .diff-add {{ background: #e6ffec; color: #22863a; }}
        .diff-empty {{ background: #fafbfc; }}
        .diff-table td + td {{ border-left: 1px solid #e1e4e8; }}
        .diff-collapse {{ text-align: center; color: #6a737d; background: #f1f8ff; font-style: italic; font-size: 11px; padding: 2px 10px; }}
        .ha-entity-link {{ display: inline-block; margin: 10px 0 4px; padding: 6px 16px; background: #4361ee; color: white !important; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 500; cursor: pointer; transition: background 0.2s; }}
        .ha-entity-link:hover {{ background: #3a56d4; }}
        .message.assistant strong {{ color: #333; }}
        .message.assistant ul, .message.assistant ol {{ margin: 6px 0 6px 20px; }}
        .message.assistant p {{ margin: 4px 0; }}
        .message.system {{ background: #fff3cd; color: #856404; align-self: center; text-align: center; font-size: 13px; border-radius: 8px; max-width: 90%; }}
        .message.system-error {{ background: #fee2e2; color: #991b1b; align-self: center; text-align: center; font-size: 13px; border-radius: 8px; max-width: 90%; border: 1px solid #fecaca; }}
        .message.thinking {{ background: #f8f9fa; color: #999; align-self: flex-start; border-bottom-left-radius: 4px; font-style: italic; }}
        .message.thinking .dots span {{ animation: blink 1.4s infinite both; }}
        .message.thinking .dots span:nth-child(2) {{ animation-delay: 0.2s; }}
        .message.thinking .dots span:nth-child(3) {{ animation-delay: 0.4s; }}
        .message.thinking .thinking-steps {{ margin-top: 6px; font-style: normal; font-size: 12px; color: #888; line-height: 1.35; }}
        .message.thinking .thinking-steps div {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .message.assistant .progress-steps {{ margin-bottom: 8px; font-size: 12px; color: #888; line-height: 1.35; }}
        .message.assistant .progress-steps div {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
        .input-area {{ padding: 12px 16px; background: white; border-top: 1px solid #e0e0e0; display: flex; flex-direction: column; gap: 8px; }}
        .image-preview-container {{ display: none; padding: 8px; background: #f8f9fa; border-radius: 8px; position: relative; }}
        .image-preview-container.visible {{ display: block; }}
        .image-preview {{ max-width: 150px; max-height: 150px; border-radius: 8px; border: 2px solid #667eea; }}
        .remove-image-btn {{ position: absolute; top: 4px; right: 4px; background: #ef4444; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; }}
        .doc-preview-container {{ display: none; padding: 8px 12px; background: #f0f4ff; border-radius: 8px; position: relative; align-items: center; gap: 8px; }}
        .doc-preview-container.visible {{ display: flex; }}
        .doc-preview-icon {{ font-size: 24px; flex-shrink: 0; }}
        .doc-preview-info {{ flex: 1; min-width: 0; }}
        .doc-preview-name {{ font-weight: 600; font-size: 13px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .doc-preview-size {{ font-size: 11px; color: #888; }}
        .remove-doc-btn {{ background: #ef4444; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
        .input-toolbar {{ display: flex; gap: 6px; align-items: center; }}
        .input-toolbar .fmt-btn {{ border: 1px solid #d6d6e7; background: #f7f8ff; color: #4b5563; border-radius: 8px; width: 32px; height: 28px; padding: 0; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }}
        .input-toolbar .fmt-btn:hover {{ background: #edf0ff; border-color: #c7cdef; }}
        .input-toolbar .fmt-btn svg {{ width: 15px; height: 15px; stroke: currentColor; fill: none; stroke-width: 2; }}
        .input-row {{ display: flex; gap: 8px; align-items: flex-end; }}
        .input-row > * {{ min-width: 0; }}
        .input-area textarea {{ flex: 1; border: 1px solid #ddd; border-radius: 20px; padding: 10px 16px; font-size: 14px; font-family: inherit; resize: none; max-height: 120px; outline: none; transition: border-color 0.2s; }}
        .input-area textarea:focus {{ border-color: #667eea; }}
        .input-area button {{ background: #667eea; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; }}
        .input-area button:hover {{ background: #5a6fd6; }}
        .input-area button:disabled {{ background: #ccc; cursor: not-allowed; }}
        .input-area button.stop-btn {{ background: #ef4444; animation: pulse-stop 1s infinite; }}
        .input-area button.stop-btn:hover {{ background: #dc2626; }}
        .input-area button.image-btn {{ background: #10b981; }}
        .input-area button.image-btn:hover {{ background: #059669; }}
        .input-area button.file-btn {{ background: #f59e0b; }}
        .input-area button.file-btn:hover {{ background: #d97706; }}
        .input-area button.mic-btn {{ background: #8b5cf6; }}
        .input-area button.mic-btn:hover {{ background: #7c3aed; }}
        .input-area button.mic-btn.recording {{ background: #ef4444; animation: mic-pulse 1s infinite; }}
        .input-area button.mic-btn.processing {{ background: #f59e0b; animation: mic-pulse 1.5s infinite; }}
        @keyframes mic-pulse {{ 0%, 100% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: 0.7; transform: scale(1.1); }} }}
        .voice-toggle {{ display: flex; align-items: center; gap: 6px; padding: 0; font-size: 12px; color: #888; margin-left: auto; }}
        .voice-toggle label {{ cursor: pointer; display: flex; align-items: center; gap: 6px; user-select: none; }}
        .voice-toggle input[type="checkbox"] {{ display: none; }}
        .voice-toggle .toggle-track {{ width: 36px; height: 20px; background: #ccc; border-radius: 10px; position: relative; transition: background 0.2s; flex-shrink: 0; }}
        .voice-toggle input:checked + .toggle-track {{ background: #8b5cf6; }}
        .voice-toggle .toggle-thumb {{ width: 16px; height: 16px; background: white; border-radius: 50%; position: absolute; top: 2px; left: 2px; transition: left 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }}
        .voice-toggle input:checked + .toggle-track .toggle-thumb {{ left: 18px; }}
        .voice-toggle .toggle-label {{ font-size: 12px; }}
        .voice-speaking-bar {{ display: none; align-items: center; gap: 8px; padding: 6px 16px; background: #f3e8ff; border-radius: 8px; margin: 0 16px 4px; font-size: 12px; color: #7c3aed; cursor: pointer; }}
        .voice-speaking-bar.active {{ display: flex; }}
        .voice-speaking-bar .wave {{ display: flex; gap: 2px; align-items: center; }}
        .voice-speaking-bar .wave span {{ display: inline-block; width: 3px; background: #8b5cf6; border-radius: 2px; animation: wave-bar 0.6s ease-in-out infinite; }}
        .voice-speaking-bar .wave span:nth-child(1) {{ height: 8px; animation-delay: 0s; }}
        .voice-speaking-bar .wave span:nth-child(2) {{ height: 14px; animation-delay: 0.1s; }}
        .voice-speaking-bar .wave span:nth-child(3) {{ height: 10px; animation-delay: 0.2s; }}
        .voice-speaking-bar .wave span:nth-child(4) {{ height: 16px; animation-delay: 0.3s; }}
        .voice-speaking-bar .wave span:nth-child(5) {{ height: 8px; animation-delay: 0.4s; }}
        @keyframes wave-bar {{ 0%, 100% {{ transform: scaleY(1); }} 50% {{ transform: scaleY(0.4); }} }}
        .suggestions {{ display: flex; gap: 8px; padding: 0 16px 8px; flex-wrap: wrap; }}
        .suggestion {{ background: white; border: 1px solid #ddd; border-radius: 16px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }}
        .suggestion:hover {{ background: #667eea; color: white; border-color: #667eea; }}
        .entity-picker {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }}
        .entity-picker .suggestion {{ padding: 8px 12px; font-size: 13px; }}
        .entity-manual {{ display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap; }}
        .entity-input {{ background: white; border: 1px solid #ddd; border-radius: 12px; padding: 8px 10px; font-size: 13px; min-width: 220px; max-width: 100%; outline: none; }}
        .entity-input:focus {{ border-color: #667eea; }}
        .tool-badge {{ display: inline-block; background: #e8f0fe; color: #1967d2; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
        .status-badge {{ display: inline-block; background: #fef3c7; color: #92400e; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
        .message-usage {{ font-size: 11px; color: #999; text-align: right; margin-top: 4px; padding-top: 4px; border-top: 1px solid rgba(150,150,150,0.15); }}
        .conversation-usage {{ font-size: 11px; color: #aaa; text-align: center; padding: 4px 8px; background: rgba(0,0,0,0.05); border-radius: 8px; margin: 4px 12px; }}
        .costs-panel {{ padding: 12px; font-size: 12px; color: #555; }}
        .costs-panel h3 {{ font-size: 13px; color: #333; margin: 0 0 8px; font-weight: 600; }}
        .costs-panel .cost-card {{ background: #f8f9fa; border-radius: 10px; padding: 10px 12px; margin-bottom: 10px; }}
        .costs-panel .cost-card-title {{ font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
        .costs-panel .cost-card-value {{ font-size: 20px; font-weight: 700; color: #333; }}
        .costs-panel .cost-card-sub {{ font-size: 11px; color: #999; margin-top: 2px; }}
        .costs-panel .cost-row {{ display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }}
        .costs-panel .cost-row:last-child {{ border-bottom: none; }}
        .costs-panel .cost-row-name {{ font-size: 12px; color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 60%; }}
        .costs-panel .cost-row-value {{ font-size: 12px; color: #333; font-weight: 600; white-space: nowrap; }}
        .costs-panel .cost-section {{ margin-top: 12px; }}
        .costs-panel .cost-section-title {{ font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #eee; }}
        .costs-panel .cost-reset-btn {{ display: block; width: 100%; margin-top: 16px; padding: 8px; background: #fee2e2; color: #991b1b; border: none; border-radius: 8px; font-size: 12px; cursor: pointer; transition: background 0.2s; }}
        .costs-panel .cost-reset-btn:hover {{ background: #fecaca; }}
        .costs-panel .cost-month-group {{ border: none; }}
        .costs-panel .cost-month-summary {{ display: flex; justify-content: space-between; align-items: center; padding: 5px 0; cursor: pointer; list-style: none; border-bottom: 1px solid rgba(0,0,0,0.06); }}
        .costs-panel .cost-month-summary::-webkit-details-marker {{ display: none; }}
        .costs-panel .cost-month-summary::marker {{ display: none; }}
        .costs-panel .cost-month-label {{ font-size: 12px; font-weight: 600; color: #444; display: flex; align-items: center; gap: 5px; }}
        .costs-panel .cost-month-label::before {{ content: '▶'; font-size: 9px; color: #aaa; transition: transform 0.15s; display: inline-block; }}
        .costs-panel details[open] > .cost-month-summary .cost-month-label::before {{ transform: rotate(90deg); }}
        .costs-panel .cost-month-total {{ font-size: 12px; font-weight: 600; color: #333; }}
        .costs-panel .cost-day-row {{ padding-left: 14px; }}
        .costs-panel .cost-today-row .cost-row-name {{ color: #667eea; font-weight: 600; }}
        .undo-button {{ display: inline-block; background: #fef3c7; color: #92400e; border: none; padding: 6px 12px; border-radius: 12px; font-size: 12px; margin-top: 8px; cursor: pointer; transition: opacity 0.2s; }}
        .undo-button:hover {{ opacity: 0.9; }}
        .undo-button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        .readonly-toggle {{ display: flex; align-items: center; gap: 5px; cursor: pointer; margin-left: 8px; user-select: none; background: rgba(255,255,255,0.1); padding: 3px 10px; border-radius: 16px; transition: background 0.3s; }}
        .readonly-toggle:hover {{ background: rgba(255,255,255,0.2); }}
        .readonly-toggle.active {{ background: rgba(251,191,36,0.25); }}
        .readonly-toggle input {{ display: none; }}
        .readonly-icon {{ font-size: 14px; line-height: 1; }}
        .readonly-name {{ font-size: 11px; color: rgba(255,255,255,0.9); white-space: nowrap; font-weight: 500; }}
        .readonly-slider {{ width: 32px; height: 18px; background: rgba(255,255,255,0.3); border-radius: 9px; position: relative; transition: background 0.3s; flex-shrink: 0; }}
        .readonly-slider::before {{ content: ''; position: absolute; top: 2px; left: 2px; width: 14px; height: 14px; background: white; border-radius: 50%; transition: transform 0.3s; }}
        .readonly-toggle input:checked + .readonly-slider {{ background: #fbbf24; }}
        .readonly-toggle input:checked + .readonly-slider::before {{ transform: translateX(14px); }}
        .readonly-label {{ font-size: 10px; color: rgba(255,255,255,0.7); white-space: nowrap; min-width: 20px; }}
        .confirm-buttons {{ display: flex; gap: 10px; margin-top: 12px; }}
        .confirm-btn {{ padding: 8px 24px; border-radius: 20px; border: 2px solid; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
        .confirm-yes {{ background: #10b981; border-color: #10b981; color: white; }}
        .confirm-yes:hover {{ background: #059669; border-color: #059669; }}
        .confirm-no {{ background: white; border-color: #ef4444; color: #ef4444; }}
        .confirm-no:hover {{ background: #fef2f2; }}
        .confirm-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .confirm-btn.selected {{ opacity: 1; transform: scale(1.05); }}
        .confirm-buttons.answered .confirm-btn:not(.selected) {{ opacity: 0.3; }}

        .mobile-only {{ display: none; }}

        /* Mobile layout */
        /* Mobile: <600px - sidebar hidden, toggle */
        @media (max-width: 599px) {{
            .mobile-only {{ display: inline-flex; }}

            .header {{ flex-wrap: wrap; padding: 10px 12px; gap: 8px; }}
            .header h1 {{ font-size: 16px; }}
            .header .status {{ order: 99; width: 100%; margin-left: 0; justify-content: flex-end; }}
            #modelSelectWrap {{ flex: 1 1 100%; width: 100%; }}
            .model-selector {{ flex: 1 1 0; max-width: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
            #providerSelect {{ max-width: none; }}
            #modelSelect {{ max-width: none; }}

            .header .new-chat {{ display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 6px 10px; border-radius: 16px; }}
            #testNvidiaBtn {{ flex: 1 1 160px; }}
            .header .new-chat:not(.mobile-only) {{ flex: 1 1 160px; }}

            .readonly-toggle {{ margin-left: 0; flex: 1 1 100%; justify-content: space-between; }}

            .main-container {{ flex-direction: column; }}
            .sidebar {{ display: none; width: 100%; min-width: 0; max-width: none; resize: none; border-right: none; border-bottom: 1px solid #e0e0e0; }}
            .sidebar.mobile-open {{ display: flex; }}
            .splitter {{ display: none; }}
            .chat-list {{ max-height: 28svh; }}

            .chat-container {{ padding: 12px; }}
            .message {{ max-width: 92%; padding: 10px 12px; }}

            .suggestions {{ padding: 0 12px 8px; overflow-x: auto; flex-wrap: nowrap; -webkit-overflow-scrolling: touch; }}
            .suggestion {{ flex: 0 0 auto; }}

            .input-area {{ padding: 10px 12px calc(10px + env(safe-area-inset-bottom)); }}
            .input-row {{ gap: 6px; }}
            .input-area button {{ width: 38px; height: 38px; }}
            .input-area textarea {{ padding: 10px 14px; }}
        }}

        /* Tablet: 600px - 1199px - sidebar visible and resizable */
        @media (min-width: 600px) and (max-width: 1199px) {{
            .mobile-only {{ display: none; }}
            .sidebar {{ width: 220px; min-width: 140px; max-width: min(520px, 45vw); }}
            .header {{ flex-wrap: wrap; padding: 10px 12px; gap: 8px; }}
            .header h1 {{ font-size: 16px; }}
            #modelSelectWrap {{ flex: 1 1 auto; }}
            .model-selector {{ flex: 1 1 auto; font-size: 11px; }}
            #providerSelect {{ max-width: 110px; }}
            #modelSelect {{ max-width: 140px; }}
            .chat-list {{ max-height: 35svh; }}
            .message {{ max-width: 90%; padding: 10px 12px; }}
            .input-area {{ padding: 10px 12px calc(10px + env(safe-area-inset-bottom)); }}
            .input-row {{ gap: 6px; }}
        }}

        /* Desktop: 1200px+ - full layout */
        @media (min-width: 1200px) {{
            .mobile-only {{ display: none; }}
            .sidebar {{ width: 250px; }}
        }}

        @media (max-width: 360px) {{
            .header .badge {{ display: none; }}
        }}

        /* ===== FILE EXPLORER (sidebar tree) ===== */
        .file-tree {{ padding: 0; overflow-y: auto; flex: 1; }}
        .file-tree-item {{
            display: flex; align-items: center; gap: 6px;
            padding: 7px 12px; font-size: 12px; cursor: pointer;
            border-bottom: 1px solid #f0f0f0; color: #333;
            transition: background 0.15s; user-select: none;
        }}
        .file-tree-item:hover {{ background: #f5f5f5; }}
        .file-tree-item.file-active {{ background: #e8f0fe; color: #1967d2; }}
        .file-tree-item.file-selected {{ background: #d2e3fc; color: #1967d2; font-weight: 600; }}
        .file-tree-item .file-icon {{ font-size: 14px; flex-shrink: 0; }}
        .file-tree-item .file-name {{ flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .file-tree-item .file-size {{ font-size: 10px; color: #999; flex-shrink: 0; }}
        .file-tree-breadcrumb {{
            padding: 6px 12px; font-size: 11px; color: #667eea;
            cursor: pointer; border-bottom: 1px solid #e0e0e0;
            background: #f8f9fa; display: flex; align-items: center; gap: 4px;
        }}
        .file-tree-breadcrumb:hover {{ background: #eff0ff; }}
        .file-tree-status {{ padding: 16px 12px; font-size: 12px; color: #999; text-align: center; }}

        /* ===== CONFIG EDITOR (sidebar list + file panel editor) ===== */
        .config-list {{ padding: 8px; overflow-y: auto; flex: 1; }}
        .config-item {{
            padding: 10px 12px; margin-bottom: 6px; background: #f8f9fa;
            border-radius: 8px; cursor: pointer; transition: background 0.15s;
            display: flex; align-items: center; gap: 8px;
        }}
        .config-item:hover {{ background: #eef0f4; }}
        .config-item.active {{ background: #e8ebff; border-left: 3px solid #667eea; }}
        .config-item-icon {{ font-size: 18px; flex-shrink: 0; }}
        .config-item-info {{ flex: 1; min-width: 0; }}
        .config-item-title {{ font-size: 13px; font-weight: 600; color: #333; }}
        .config-item-desc {{ font-size: 11px; color: #888; margin-top: 2px; }}
        .llm-priority-list {{ list-style: none; padding: 0; margin: 8px 0; }}
        .llm-priority-item {{ display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 4px; background: #fafafa; }}
        .llm-priority-item .llm-idx {{ font-size: 12px; font-weight: 600; color: #999; min-width: 18px; text-align: center; }}
        .llm-priority-item .llm-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
        .llm-priority-item .llm-dot.on {{ background: #4caf50; }}
        .llm-priority-item .llm-dot.off {{ background: #ccc; }}
        .llm-priority-item .llm-name {{ flex: 1; font-size: 13px; }}
        .llm-priority-item .llm-nokey {{ font-size: 11px; color: #999; font-style: italic; }}
        .llm-priority-btn {{ background: none; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; padding: 2px 6px; font-size: 11px; line-height: 1; }}
        .llm-priority-btn:hover {{ background: #eee; }}
        .llm-priority-btn:disabled {{ opacity: 0.3; cursor: default; }}
        .llm-toggle-row {{ display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-bottom: 1px solid #e0e0e0; }}
        .llm-toggle-label {{ flex: 1; font-size: 13px; font-weight: 500; }}
        .llm-toggle-desc {{ font-size: 12px; color: #888; padding: 8px 14px; }}
        .config-editor {{ display: flex; flex-direction: column; height: 100%; }}
        .config-editor-header {{
            padding: 10px 14px; border-bottom: 1px solid #e0e0e0;
            display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
        }}
        .config-editor-title {{ font-size: 14px; font-weight: 600; }}
        .config-editor-body {{ flex: 1; display: flex; flex-direction: column; min-height: 0; }}
        .config-editor-body textarea {{
            width: 100%; flex: 1; border: none; resize: none; padding: 12px;
            font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
            font-size: 12px; line-height: 1.5;
            background: #f8f9fa; color: #1e1e2e; outline: none;
            box-sizing: border-box;
        }}
        .config-editor-footer {{
            padding: 8px 14px; border-top: 1px solid #e0e0e0;
            display: flex; gap: 8px; justify-content: flex-end; align-items: center; flex-shrink: 0;
        }}
        .config-editor-footer button {{
            padding: 6px 16px; border-radius: 6px; border: none;
            cursor: pointer; font-size: 12px; font-weight: 500;
        }}
        .config-save-btn {{ background: #667eea; color: white; }}
        .config-save-btn:hover {{ background: #5a6fd6; }}
        .config-cancel-btn {{ background: #e0e0e0; color: #333; }}
        .config-cancel-btn:hover {{ background: #d0d0d0; }}
        .config-status {{ font-size: 11px; padding: 4px 8px; border-radius: 4px; transition: opacity 0.3s; }}
        .config-status.success {{ background: #dcfce7; color: #166534; }}
        .config-status.error {{ background: #fce8e8; color: #991b1b; }}

        /* ===== SETTINGS FORM ===== */
        .settings-section {{ margin-bottom: 2px; }}
        .settings-section-header {{
            display: flex; align-items: center; justify-content: space-between;
            padding: 10px 14px; cursor: pointer; user-select: none;
            font-size: 12px; font-weight: 700; color: #555; letter-spacing: 0.5px;
            background: #f5f6f8; border-bottom: 1px solid #e8e8e8;
        }}
        .settings-section-header:hover {{ background: #eef0f4; }}
        .settings-section-arrow {{ font-size: 10px; color: #999; }}
        .settings-section-body {{ padding: 6px 0; }}
        .settings-subsection {{
            margin: 8px 10px 12px;
            border: 1px solid #e8e8e8;
            border-radius: 10px;
            overflow: hidden;
            background: #fff;
        }}
        .settings-subsection-title {{
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 700;
            color: #555;
            background: #f8f9fb;
            border-bottom: 1px solid #ececec;
            letter-spacing: 0.2px;
        }}
        .settings-row {{
            display: flex; align-items: center; justify-content: space-between;
            padding: 8px 14px; min-height: 36px;
        }}
        .settings-row:hover {{ background: #f8f9fb; }}
        .settings-label {{ font-size: 13px; color: #444; flex: 1; }}
        .settings-desc {{
            font-size: 11px; color: #999; padding: 0 14px 6px; line-height: 1.4;
        }}
        .settings-toggle {{
            position: relative; display: inline-block; width: 42px; height: 24px; flex-shrink: 0;
        }}
        .settings-toggle input {{ opacity: 0; width: 0; height: 0; }}
        .settings-slider {{
            position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
            background: #ccc; border-radius: 24px; transition: .3s;
        }}
        .settings-slider:before {{
            content: ""; position: absolute; height: 18px; width: 18px;
            left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: .3s;
        }}
        .settings-toggle input:checked + .settings-slider {{ background: #667eea; }}
        .settings-toggle input:checked + .settings-slider:before {{ transform: translateX(18px); }}
        .settings-select {{
            padding: 5px 8px; border: 1px solid #ddd; border-radius: 6px;
            font-size: 13px; background: #fff; color: #333; min-width: 120px;
            outline: none; cursor: pointer;
        }}
        .settings-select:focus {{ border-color: #667eea; }}
        .settings-input {{
            padding: 5px 8px; border: 1px solid #ddd; border-radius: 6px;
            font-size: 13px; background: #fff; color: #333; width: 220px;
            outline: none; box-sizing: border-box;
        }}
        .settings-input:focus {{ border-color: #667eea; }}
        .settings-input[type="number"] {{ width: 80px; text-align: center; }}
        .settings-pw-wrap {{ display: flex; align-items: center; gap: 4px; }}
        .settings-password {{ width: 260px; font-family: monospace; }}
        .settings-eye-btn {{
            background: none; border: none; cursor: pointer; font-size: 14px;
            padding: 2px 4px; opacity: 0.6;
        }}
        .settings-eye-btn:hover {{ opacity: 1; }}
        .model-cache-toolbar {{
            display:flex; gap:8px; flex-wrap:wrap; align-items:center; padding:10px 14px;
            border-bottom:1px solid #eceff3;
        }}
        .model-cache-status {{ font-size:12px; color:#4caf50; }}
        .model-cache-grid {{
            display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap:10px; padding:10px 14px 12px;
        }}
        .model-cache-box {{
            border:1px solid #e5e7eb; border-radius:8px; background:#fafbfc; overflow:hidden;
        }}
        .model-cache-box h5 {{
            margin:0; padding:8px 10px; font-size:12px; letter-spacing:.3px; text-transform:uppercase;
            color:#555; background:#f1f3f6; border-bottom:1px solid #e5e7eb;
        }}
        .model-cache-box pre {{
            margin:0; padding:10px; max-height:220px; overflow:auto;
            font-size:12px; line-height:1.5; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            color:#2f3542; background:#fafbfc;
        }}

        /* ===== AGENT FORM ===== */
        .agent-list-header {{
            display: flex; align-items: center; justify-content: space-between;
            padding: 10px 14px; border-bottom: 1px solid #e0e0e0;
        }}
        .agent-list-header h3 {{ margin: 0; font-size: 14px; font-weight: 600; }}
        .agent-add-btn {{
            background: #667eea; color: white; border: none; border-radius: 6px;
            padding: 5px 12px; font-size: 12px; cursor: pointer; font-weight: 500;
        }}
        .agent-add-btn:hover {{ background: #5a6fd6; }}
        .agent-card {{
            padding: 10px 14px; border-bottom: 1px solid #f0f0f0; cursor: pointer;
            display: flex; align-items: center; gap: 10px; transition: background 0.15s;
        }}
        .agent-card:hover {{ background: #f5f5ff; }}
        .agent-card.active {{ background: #e8ebff; border-left: 3px solid #667eea; }}
        .agent-card-emoji {{ font-size: 22px; flex-shrink: 0; }}
        .agent-card-info {{ flex: 1; min-width: 0; }}
        .agent-card-name {{ font-size: 13px; font-weight: 600; color: #333; }}
        .agent-card-model {{ font-size: 11px; color: #888; margin-top: 1px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .agent-card-badges {{ display: flex; gap: 4px; margin-top: 3px; flex-wrap: wrap; }}
        .agent-badge {{ font-size: 9px; padding: 1px 5px; border-radius: 3px; background: #eef0f4; color: #666; }}
        .agent-badge.default {{ background: #dcfce7; color: #166534; }}
        .agent-badge.channel {{ background: #dbeafe; color: #1e40af; }}
        .agent-card-actions {{ display: flex; gap: 4px; flex-shrink: 0; }}
        .agent-card-actions button {{
            background: none; border: none; cursor: pointer; padding: 3px; border-radius: 4px;
            font-size: 14px; opacity: 0.5; transition: opacity 0.15s;
        }}
        .agent-card:hover .agent-card-actions button {{ opacity: 1; }}
        .agent-card-actions button:hover {{ background: rgba(0,0,0,0.08); }}
        .agent-card-actions button.delete:hover {{ background: #fce8e8; }}
        .agent-form {{ padding: 14px; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; flex: 1; }}
        .agent-form-group {{ display: flex; flex-direction: column; gap: 4px; }}
        .agent-form-group label {{ font-size: 11px; font-weight: 600; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
        .agent-form-row {{ display: flex; gap: 8px; }}
        .agent-form-row > * {{ flex: 1; }}
        .agent-form-group input, .agent-form-group select, .agent-form-group textarea {{
            padding: 7px 10px; border: 1px solid #d0d0d0; border-radius: 6px;
            font-size: 13px; background: #fff; color: #333; outline: none;
            transition: border-color 0.15s;
        }}
        .agent-form-group input:focus, .agent-form-group select:focus, .agent-form-group textarea:focus {{
            border-color: #667eea;
        }}
        .agent-form-group textarea {{ min-height: 60px; resize: vertical; font-family: inherit; }}
        .emoji-dropdown {{ position: relative; display: inline-block; }}
        .emoji-dropdown-btn {{
            display: flex; align-items: center; gap: 4px; padding: 4px 8px;
            font-size: 18px; border: 2px solid #ddd; border-radius: 8px;
            background: #f5f5f5; cursor: pointer; min-width: 56px;
            transition: border-color 0.15s;
        }}
        .emoji-dropdown-btn:hover {{ border-color: #667eea; }}
        .emoji-dropdown-btn .edrop-arrow {{ font-size: 10px; color: #888; margin-left: 2px; }}
        .emoji-dropdown-panel {{
            display: none; position: absolute; top: calc(100% + 4px); left: 0; z-index: 9999;
            background: var(--bg-card, #fff); border: 1px solid #ddd; border-radius: 10px;
            padding: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            display: none; flex-wrap: wrap; gap: 3px; width: 196px;
        }}
        .emoji-dropdown-panel.open {{ display: flex; }}
        .agent-form-group .emoji-btn {{
            width: 30px; height: 30px; border: 2px solid transparent; border-radius: 6px;
            cursor: pointer; font-size: 17px; background: transparent; display: flex;
            align-items: center; justify-content: center; transition: all 0.15s;
        }}
        .agent-form-group .emoji-btn:hover {{ background: #e8e8ff; }}
        .agent-form-group .emoji-btn.selected {{ border-color: #667eea; background: #e8ebff; }}
        .agent-tools-grid {{
            display: flex; flex-wrap: wrap; gap: 4px; max-height: 200px; overflow-y: auto;
        }}
        .agent-tool-chip {{
            font-size: 11px; padding: 3px 8px; border-radius: 4px; cursor: pointer;
            background: #f0f0f0; color: #666; border: 1px solid transparent;
            transition: all 0.15s; user-select: none;
        }}
        .agent-tool-chip:hover {{ background: #e8ebff; }}
        .agent-tool-chip.selected {{ background: #667eea; color: white; border-color: #5a6fd6; }}
        .agent-form-actions {{
            display: flex; gap: 8px; justify-content: flex-end; padding: 8px 0 0;
            border-top: 1px solid #e0e0e0;
        }}
        .agent-form-actions button {{
            padding: 6px 16px; border-radius: 6px; border: none;
            cursor: pointer; font-size: 12px; font-weight: 500;
        }}
        .agent-card.protected {{ opacity: 0.92; }}
        .agent-card.protected .agent-card-actions {{ display: none; }}
        .agent-protected-badge {{
            font-size: 9px; background: #dbeafe; color: #1e40af; padding: 1px 6px;
            border-radius: 8px; font-weight: 600; white-space: nowrap;
        }}

        /* Tooltip info icons */
        .field-tip {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 15px; height: 15px; border-radius: 50%; background: #e0e0e0;
            color: #555; font-size: 10px; font-weight: 700; cursor: help;
            margin-left: 4px; position: relative; vertical-align: middle;
            font-style: italic; font-family: Georgia, serif; line-height: 1;
        }}
        .field-tip:hover {{ background: #667eea; color: white; }}
        .field-tip .tip-text {{
            display: none; position: absolute; bottom: 120%; left: 50%;
            transform: translateX(-50%); background: #333; color: #fff;
            font-size: 11px; font-weight: 400; font-style: normal; font-family: inherit;
            padding: 6px 10px; border-radius: 6px; white-space: normal;
            min-width: 180px; max-width: 260px; z-index: 100;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25); line-height: 1.35;
            text-align: left; letter-spacing: 0;
        }}
        .field-tip .tip-text::after {{
            content: ''; position: absolute; top: 100%; left: 50%;
            transform: translateX(-50%); border: 5px solid transparent;
            border-top-color: #333;
        }}
        .field-tip:hover .tip-text {{ display: block; }}

        /* MCP server cards */
        .mcp-server-card {{
            border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 8px;
            overflow: hidden; background: white;
        }}
        .mcp-server-header {{
            display: flex; align-items: center; gap: 8px; padding: 10px 12px;
            background: #f5f5ff; cursor: pointer; user-select: none;
        }}
        .mcp-server-header:hover {{ background: #ebebff; }}
        .mcp-server-name {{ flex: 1; font-weight: 600; font-size: 13px; color: #333; }}
        .mcp-server-status-badge {{
            font-size: 11px; color: #666; display: inline-flex;
            align-items: center; gap: 5px; margin-right: 6px;
        }}
        .mcp-status-dot {{
            width: 9px; height: 9px; border-radius: 999px; display: inline-block;
            background: #9e9e9e;
        }}
        .mcp-status-dot.running {{ background: #2e7d32; }}
        .mcp-status-dot.stopped {{ background: #9e9e9e; }}
        .mcp-server-toggle {{ font-size: 12px; color: #888; transition: transform 0.2s; }}
        .mcp-server-toggle.open {{ transform: rotate(90deg); }}
        .mcp-server-body {{ padding: 12px; display: none; border-top: 1px solid #e8e8f0; }}
        .mcp-server-body.open {{ display: block; }}
        .mcp-server-actions {{ display: flex; gap: 4px; }}
        .mcp-server-actions button {{
            background: none; border: none; cursor: pointer; font-size: 14px;
            padding: 2px 4px; border-radius: 4px; opacity: 0.6;
        }}
        .mcp-server-actions button:disabled {{
            opacity: 0.3; cursor: not-allowed;
        }}
        .mcp-server-actions button:hover {{ opacity: 1; background: rgba(0,0,0,0.05); }}
        .mcp-server-actions button.delete:hover {{ background: #fce8e8; }}

        /* Enhanced text editor (system prompt / memory) */
        .enhanced-editor-stats {{
            display: flex; gap: 12px; align-items: center; padding: 6px 12px;
            background: #f8f9fa; border-bottom: 1px solid #e8e8f0;
            font-size: 11px; color: #888;
        }}
        .enhanced-editor-stats span {{ font-weight: 600; color: #555; }}

        /* ===== FILE PREVIEW PANEL (middle column) ===== */
        .file-panel {{
            width: 0; min-width: 0;
            background: #fafafa; border-right: 1px solid #e0e0e0;
            display: flex; flex-direction: column; overflow: hidden;
            transition: width 0.22s ease; flex-shrink: 0;
        }}
        .file-panel.open {{ width: 320px; min-width: 180px; }}
        .file-panel-header {{
            display: flex; align-items: center;
            background: #f0f0f0; border-bottom: 1px solid #ddd;
            flex-shrink: 0; min-width: 0;
        }}
        .file-panel-tabs {{
            display: flex; flex: 1; overflow-x: auto; min-width: 0;
            scrollbar-width: none;
        }}
        .file-panel-tabs::-webkit-scrollbar {{ display: none; }}
        .file-panel-tab {{
            display: flex; align-items: center; gap: 4px;
            padding: 6px 8px; font-size: 11px; cursor: pointer;
            border: none; background: transparent; color: #666;
            white-space: nowrap; border-bottom: 2px solid transparent;
            flex-shrink: 0; max-width: 150px; min-width: 0;
        }}
        .file-panel-tab.active {{
            color: #667eea; border-bottom-color: #667eea;
            background: #fafafa; font-weight: 500;
        }}
        .file-panel-tab .tab-name {{
            max-width: 100px; overflow: hidden; text-overflow: ellipsis;
        }}
        .file-panel-tab .tab-close {{
            font-size: 14px; line-height: 1; color: #bbb;
            padding: 0 2px; border-radius: 3px;
            transition: color 0.15s, background 0.15s; flex-shrink: 0;
        }}
        .file-panel-tab .tab-close:hover {{ color: #e53e3e; background: #fde8e8; }}
        .file-panel-close-all {{
            padding: 4px 8px; font-size: 16px; color: #999;
            cursor: pointer; border: none; background: none; flex-shrink: 0;
        }}
        .file-panel-close-all:hover {{ color: #333; }}
        .file-panel-content {{
            flex: 1; overflow-y: auto; overflow-x: auto;
        }}
        .file-panel-loading {{
            padding: 24px 12px; text-align: center; color: #999; font-size: 13px;
        }}
        .file-panel-error {{
            padding: 16px 12px; color: #c0392b; font-size: 12px;
        }}
        .file-panel-truncated {{
            padding: 4px 12px; font-size: 10px; color: #e07042;
            background: #fff8f5; border-bottom: 1px solid #fdd; flex-shrink: 0;
        }}
        .file-load-more {{
            display: block; width: calc(100% - 24px); margin: 8px 12px 12px;
            padding: 6px 12px; font-size: 12px; cursor: pointer;
            background: #f0f4ff; color: #667eea; border: 1px solid #c5d0ff;
            border-radius: 6px; text-align: center; transition: background 0.2s;
        }}
        .file-load-more:hover {{ background: #e0e8ff; }}
        .file-load-more:disabled {{ opacity: 0.6; cursor: default; }}

        /* YAML syntax highlight */
        .yaml-viewer {{
            font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
            font-size: 11.5px; line-height: 1.6; padding: 10px 14px;
            white-space: pre; overflow-x: auto; min-width: 0;
            color: #333;
        }}
        .yaml-key {{ color: #7c3aed; }}
        .yaml-string {{ color: #059669; }}
        .yaml-number {{ color: #d97706; }}
        .yaml-bool {{ color: #0369a1; font-weight: 600; }}
        .yaml-comment {{ color: #9ca3af; font-style: italic; }}

        /* File panel splitter */
        .file-splitter {{
            width: 8px; flex: 0 0 8px; cursor: col-resize;
            background: transparent; display: none;
        }}
        .file-splitter.visible {{ display: block; }}
        .file-splitter:hover {{ background: rgba(0,0,0,0.08); }}
        @media (pointer: coarse) {{
            .file-splitter {{ width: 14px; flex: 0 0 14px; background: rgba(0,0,0,0.04); }}
            .file-splitter:active {{ background: rgba(0,0,0,0.12); }}
        }}

        /* File context bar (above input) */
        .file-context-bar {{
            display: none; padding: 5px 12px;
            background: #eff6ff; border-top: 1px solid #bfdbfe;
            font-size: 11px; color: #1e40af;
            gap: 6px; align-items: center; flex-wrap: wrap;
        }}
        .file-context-bar.visible {{ display: flex; }}
        .file-context-chip {{
            display: inline-flex; align-items: center; gap: 4px;
            background: #dbeafe; border-radius: 10px;
            padding: 2px 8px; font-size: 10px; color: #1e40af;
        }}

        /* Mobile: hide file panel */
        @media (max-width: 599px) {{
            .file-panel {{ display: none !important; }}
            .file-splitter {{ display: none !important; }}
        }}

        /* Dark Mode Styles */
        body.dark-mode {{
            background: #1a1a1a;
        }}

        body.dark-mode .sidebar {{
            background: #242424;
            border-right-color: #3a3a3a;
        }}

        body.dark-mode .sidebar-header {{
            border-bottom-color: #3a3a3a;
            color: #e0e0e0;
        }}

        body.dark-mode .sidebar-tabs {{
            background: #1f1f1f;
            border-bottom-color: #3a3a3a;
        }}

        body.dark-mode .sidebar-tab {{
            color: #a0a0a0;
        }}

        body.dark-mode .sidebar-tab:hover {{
            background: #2f2f2f;
        }}

        body.dark-mode .sidebar-tab.active {{
            color: #8ab4f8;
            border-bottom-color: #8ab4f8;
        }}

        body.dark-mode .chat-item {{
            background: linear-gradient(135deg, #1e2030 0%, #252840 100%);
            border-color: rgba(138, 180, 248, 0.08);
        }}

        body.dark-mode .chat-item:hover {{
            background: linear-gradient(135deg, #262a45 0%, #2d3258 100%);
            box-shadow: 0 2px 12px rgba(138, 180, 248, 0.1);
        }}

        body.dark-mode .chat-item.active {{
            background: linear-gradient(135deg, #3b5bdb 0%, #5f3dc4 100%);
            border-color: transparent;
            box-shadow: 0 4px 16px rgba(138, 180, 248, 0.2);
        }}

        body.dark-mode .chat-item-title {{
            color: #e2e8f0;
        }}
        body.dark-mode .chat-item.active .chat-item-title {{
            color: #ffffff;
        }}

        body.dark-mode .chat-item-info {{
            color: #718096;
        }}
        body.dark-mode .chat-item.active .chat-item-info {{
            color: rgba(255,255,255,0.7);
        }}

        body.dark-mode .chat-item-delete {{
            color: #fc8181;
            background: rgba(254, 178, 178, 0.12);
            border-color: rgba(252, 129, 129, 0.2);
            opacity: 0.5;
        }}
        body.dark-mode .chat-item:hover .chat-item-delete {{
            opacity: 1;
            background: rgba(254, 178, 178, 0.22);
            border-color: rgba(252, 129, 129, 0.35);
        }}
        body.dark-mode .chat-item.active .chat-item-delete {{
            color: #fed7d7;
            background: rgba(255,255,255,0.15);
            border-color: rgba(255,255,255,0.2);
        }}
        body.dark-mode .chat-item-delete:hover {{
            color: #fff;
            background: #e53e3e;
            border-color: #e53e3e;
            box-shadow: 0 2px 10px rgba(229, 62, 62, 0.4);
        }}

        body.dark-mode .chat-group-title {{
            color: #5a6580;
        }}

        body.dark-mode .backup-item,
        body.dark-mode .device-item {{
            border-bottom-color: #2a2a2a;
        }}

        body.dark-mode .backup-item:hover,
        body.dark-mode .device-item:hover {{
            background: #2a2a2a;
        }}

        body.dark-mode .backup-file,
        body.dark-mode .device-name {{
            color: #e0e0e0;
        }}

        body.dark-mode .backup-date,
        body.dark-mode .device-last-seen {{
            color: #808080;
        }}

        body.dark-mode .device-type {{
            background: #1e3a8a;
            color: #8ab4f8;
        }}

        body.dark-mode .splitter:hover {{
            background: rgba(255,255,255,0.08);
        }}

        body.dark-mode .file-panel {{
            background: #1e1e1e; border-right-color: #3a3a3a;
        }}
        body.dark-mode .file-panel-header {{ background: #252525; border-bottom-color: #3a3a3a; }}
        body.dark-mode .file-panel-tab {{ color: #a0a0a0; }}
        body.dark-mode .file-panel-tab.active {{
            color: #8ab4f8; background: #1e1e1e; border-bottom-color: #8ab4f8;
        }}
        body.dark-mode .file-panel-close-all {{ color: #666; }}
        body.dark-mode .file-panel-close-all:hover {{ color: #ccc; }}
        body.dark-mode .file-tree-item {{ color: #d0d0d0; border-bottom-color: #2a2a2a; }}
        body.dark-mode .file-tree-item:hover {{ background: #2a2a2a; }}
        body.dark-mode .file-tree-item.file-active {{ background: #1e3a8a; color: #8ab4f8; }}
        body.dark-mode .file-tree-item.file-selected {{ background: #1a3568; color: #93c5fd; font-weight: 600; }}
        body.dark-mode .file-tree-breadcrumb {{ background: #1a1a1a; color: #8ab4f8; border-bottom-color: #3a3a3a; }}
        body.dark-mode .file-tree-breadcrumb:hover {{ background: #222; }}
        body.dark-mode .yaml-viewer {{ color: #d0d0d0; }}
        body.dark-mode .yaml-key {{ color: #c084fc; }}
        body.dark-mode .yaml-string {{ color: #34d399; }}
        body.dark-mode .yaml-number {{ color: #fbbf24; }}
        body.dark-mode .yaml-bool {{ color: #38bdf8; }}
        body.dark-mode .yaml-comment {{ color: #6b7280; }}
        body.dark-mode .file-splitter:hover {{ background: rgba(255,255,255,0.08); }}
        body.dark-mode .file-context-bar {{ background: #1e3a5f; border-top-color: #2563eb; color: #93c5fd; }}
        body.dark-mode .file-context-chip {{ background: #1e3a8a; color: #93c5fd; }}

        body.dark-mode .message.assistant {{
            background: #2a2a2a;
            color: #e0e0e0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.5);
        }}

        body.dark-mode .message.user {{
            background: #6366f1;
        }}

        body.dark-mode .message.thinking {{
            background: #1f1f1f;
            color: #909090;
        }}

        body.dark-mode .message.system {{
            background: #5d4037;
            color: #ffb74d;
        }}
        body.dark-mode .message.system-error {{
            background: #4a1515;
            color: #fca5a5;
            border-color: #7f1d1d;
        }}

        body.dark-mode .message.assistant pre {{
            background: #1a1a1a;
            color: #e0e0e0;
        }}

        body.dark-mode .message.assistant code {{
            background: #2a2a2a;
            color: #8ab4f8;
        }}

        body.dark-mode .message.assistant pre code {{
            background: none;
            color: #e0e0e0;
        }}

        body.dark-mode .message.assistant details {{
            border-color: #444;
        }}
        body.dark-mode .message.assistant details summary {{
            background: #2a2a2a;
            color: #e0e0e0;
        }}
        body.dark-mode .message.assistant details summary:hover {{
            background: #667eea;
            color: #fff;
        }}
        body.dark-mode .message.assistant details > div {{
            background: #1a1a1a;
            color: #e0e0e0;
        }}
        body.dark-mode .message.assistant details code {{
            background: rgba(255,255,255,0.1);
            color: #8ab4f8;
        }}

        body.dark-mode .message.assistant strong,
        body.dark-mode .message.assistant b {{
            color: #ffffff;
        }}

        body.dark-mode .message.assistant em,
        body.dark-mode .message.assistant i {{
            color: #c9d1d9;
        }}

        body.dark-mode .message.assistant h1,
        body.dark-mode .message.assistant h2,
        body.dark-mode .message.assistant h3,
        body.dark-mode .message.assistant h4,
        body.dark-mode .message.assistant h5,
        body.dark-mode .message.assistant h6 {{
            color: #e0e0e0;
        }}

        body.dark-mode .chat-container {{
            background: #1a1a1a;
        }}

        body.dark-mode .input-area {{
            background: #242424;
            border-top-color: #3a3a3a;
        }}

        body.dark-mode .input-area textarea {{
            background: #2a2a2a;
            color: #e0e0e0;
            border-color: #3a3a3a;
        }}

        body.dark-mode .input-area textarea:focus {{
            border-color: #8ab4f8;
        }}

        body.dark-mode .input-area textarea::placeholder {{
            color: #707070;
        }}
        body.dark-mode .message.user .user-code-block {{ background: rgba(0,0,0,0.28); border-color: rgba(255,255,255,0.24); }}
        body.dark-mode .message.user .user-code-label {{ background: rgba(255,255,255,0.08); color: #dbe4ff; }}
        body.dark-mode .input-toolbar .fmt-btn {{ background: #2a2a44; border-color: #3d3d62; color: #d7daf0; }}
        body.dark-mode .input-toolbar .fmt-btn:hover {{ background: #34345a; border-color: #54548a; }}

        body.dark-mode .voice-toggle {{ color: #888; }}
        body.dark-mode .voice-toggle .toggle-track {{ background: #444; }}
        body.dark-mode .voice-toggle input:checked + .toggle-track {{ background: #8b5cf6; }}
        body.dark-mode .voice-speaking-bar {{ background: #2d1f4e; color: #c4b5fd; }}

        body.dark-mode .suggestion {{
            background: #2a2a2a;
            border-color: #3a3a3a;
            color: #e0e0e0;
        }}

        body.dark-mode .suggestion:hover {{
            background: #3d5a80;
            border-color: #8ab4f8;
            color: white;
        }}

        body.dark-mode .model-selector {{
            background: rgba(255,255,255,0.1);
            border-color: rgba(255,255,255,0.2);
        }}

        body.dark-mode .model-selector option {{
            background: #2a2a2a;
            color: #e0e0e0;
        }}

        body.dark-mode .tool-badge {{
            background: #1e3a8a;
            color: #8ab4f8;
        }}

        body.dark-mode .status-badge {{
            background: #5d4037;
            color: #ffb74d;
        }}

        body.dark-mode .message-usage {{
            color: #808080;
            border-top-color: rgba(128,128,128,0.2);
        }}

        body.dark-mode .conversation-usage {{
            background: rgba(0,0,0,0.3);
            color: #a0a0a0;
        }}

        body.dark-mode .costs-panel {{ color: #c0c0c0; }}
        body.dark-mode .costs-panel h3 {{ color: #e0e0e0; }}
        body.dark-mode .costs-panel .cost-card {{ background: #2a2a2a; }}
        body.dark-mode .costs-panel .cost-card-value {{ color: #e0e0e0; }}
        body.dark-mode .costs-panel .cost-card-sub {{ color: #808080; }}
        body.dark-mode .costs-panel .cost-row {{ border-bottom-color: rgba(255,255,255,0.05); }}
        body.dark-mode .costs-panel .cost-row-name {{ color: #c0c0c0; }}
        body.dark-mode .costs-panel .cost-row-value {{ color: #e0e0e0; }}
        body.dark-mode .costs-panel .cost-section-title {{ color: #808080; border-bottom-color: #3a3a3a; }}
        body.dark-mode .costs-panel .cost-reset-btn {{ background: #3b1a1a; color: #fca5a5; }}
        body.dark-mode .costs-panel .cost-reset-btn:hover {{ background: #4a2020; }}
        body.dark-mode .costs-panel .cost-month-summary {{ border-bottom-color: rgba(255,255,255,0.05); }}
        body.dark-mode .costs-panel .cost-month-label {{ color: #c0c0c0; }}
        body.dark-mode .costs-panel .cost-month-total {{ color: #e0e0e0; }}
        body.dark-mode .costs-panel .cost-today-row .cost-row-name {{ color: #8ab4f8; }}

        body.dark-mode .entity-input {{
            background: #2a2a2a;
            color: #e0e0e0;
            border-color: #3a3a3a;
        }}

        body.dark-mode .entity-input:focus {{
            border-color: #8ab4f8;
        }}

        body.dark-mode .entity-input::placeholder {{
            color: #707070;
        }}

        body.dark-mode .diff-side {{
            background: #1a1a1a;
            border-color: #3a3a3a;
        }}

        body.dark-mode .diff-table {{
            background: #1a1a1a;
        }}

        body.dark-mode .diff-table th {{
            background: #2a2a2a;
            border-bottom-color: #3a3a3a;
            color: #e0e0e0;
        }}

        body.dark-mode .diff-eq {{
            color: #a0a0a0;
        }}

        body.dark-mode .diff-del {{
            background: #4a1616;
            color: #ff9b9b;
        }}

        body.dark-mode .diff-add {{
            background: #164a1a;
            color: #9bff9b;
        }}

        body.dark-mode .diff-empty {{
            background: #0f0f0f;
        }}

        body.dark-mode .diff-table td {{
            border-left-color: #2a2a2a;
        }}

        body.dark-mode .diff-collapse {{
            background: #1e3a8a;
            color: #8ab4f8;
        }}
        body.dark-mode .ha-entity-link {{ background: #5a6fd6; }}
        body.dark-mode .ha-entity-link:hover {{ background: #6b7ee0; }}

        body.dark-mode .image-preview-container {{
            background: #2a2a2a;
        }}

        body.dark-mode .image-preview {{
            border-color: #3d5a80;
        }}

        body.dark-mode .doc-preview-container {{
            background: #1e3a8a;
        }}

        body.dark-mode .doc-preview-name {{
            color: #e0e0e0;
        }}

        body.dark-mode .doc-preview-size {{
            color: #a0a0a0;
        }}

        body.dark-mode .undo-button {{
            background: #5d4037;
            color: #ffb74d;
        }}

        body.dark-mode .undo-button:hover {{
            opacity: 0.8;
        }}

        body.dark-mode .dark-mode-toggle {{
            color: #e0e0e0;
        }}

        body.dark-mode .dark-mode-toggle:hover {{
            background: rgba(255,255,255,0.15);
        }}

        body.dark-mode .dark-mode-toggle.active {{
            background: #ffb340;
        }}

        /* ===== CONFIG EDITOR DARK MODE ===== */
        body.dark-mode .config-item {{ background: #2a2a3a; border-bottom-color: #3a3a4a; }}
        body.dark-mode .config-item:hover {{ background: #33334a; }}
        body.dark-mode .config-item.active {{ background: #2e2e5a; border-left-color: #8899ff; }}
        body.dark-mode .llm-priority-item {{ background: #2a2a3a; border-color: #3a3a4a; }}
        body.dark-mode .llm-priority-item .llm-name {{ color: #ddd; }}
        body.dark-mode .llm-priority-btn {{ border-color: #555; color: #ccc; }}
        body.dark-mode .llm-priority-btn:hover {{ background: #3a3a4a; }}
        body.dark-mode .llm-toggle-row {{ border-bottom-color: #3a3a4a; }}
        body.dark-mode .llm-toggle-desc {{ color: #777; }}
        body.dark-mode .config-item-title {{ color: #e0e0e0; }}
        body.dark-mode .config-item-desc {{ color: #808090; }}
        body.dark-mode .config-editor-header {{ border-bottom-color: #3a3a4a; }}
        body.dark-mode .config-editor-title {{ color: #e0e0e0; }}
        body.dark-mode .config-editor-body textarea {{
            background: #1e1e2e; color: #cdd6f4;
        }}
        body.dark-mode .config-editor-footer {{ border-top-color: #3a3a4a; }}
        body.dark-mode .config-save-btn {{ background: #5a6fd6; }}
        body.dark-mode .config-save-btn:hover {{ background: #4e60c4; }}
        body.dark-mode .config-cancel-btn {{ background: #3a3a4a; color: #ccc; }}
        body.dark-mode .config-cancel-btn:hover {{ background: #4a4a5a; }}
        body.dark-mode .config-status.success {{ background: #1a3a2a; color: #6ee7b7; }}
        body.dark-mode .config-status.error {{ background: #3a1a1a; color: #fca5a5; }}

        /* Settings dark mode */
        body.dark-mode .settings-section-header {{ background: #252535; color: #aaa; border-bottom-color: #3a3a4a; }}
        body.dark-mode .settings-section-header:hover {{ background: #2e2e40; }}
        body.dark-mode .settings-section-arrow {{ color: #777; }}
        body.dark-mode .settings-subsection {{ background:#232334; border-color:#3a3a4a; }}
        body.dark-mode .settings-subsection-title {{ background:#2a2a3a; border-bottom-color:#3a3a4a; color:#bfc6d6; }}
        body.dark-mode .settings-row:hover {{ background: #2a2a3a; }}
        body.dark-mode .settings-label {{ color: #ccc; }}
        body.dark-mode .settings-desc {{ color: #777; }}
        body.dark-mode .settings-select {{ background: #2a2a3a; color: #ddd; border-color: #4a4a5a; }}
        body.dark-mode .settings-select:focus {{ border-color: #8899ff; }}
        body.dark-mode .settings-input {{ background: #2a2a3a; color: #ddd; border-color: #4a4a5a; }}
        body.dark-mode .settings-input:focus {{ border-color: #8899ff; }}
        body.dark-mode .settings-eye-btn {{ color: #aaa; }}
        body.dark-mode .model-cache-toolbar {{ border-bottom-color:#3a3a4a; }}
        body.dark-mode .model-cache-status {{ color:#8fd19e; }}
        body.dark-mode .model-cache-box {{ background:#232334; border-color:#3a3a4a; }}
        body.dark-mode .model-cache-box h5 {{ background:#2a2a3a; border-bottom-color:#3a3a4a; color:#b8c0d0; }}
        body.dark-mode .model-cache-box pre {{ background:#232334; color:#d7dbe6; }}

        /* Agent form dark mode */
        body.dark-mode .agent-add-btn {{ background: #5a6fd6; }}
        body.dark-mode .agent-add-btn:hover {{ background: #4e60c4; }}
        body.dark-mode .agent-list-header {{ border-bottom-color: #3a3a4a; }}
        body.dark-mode .agent-list-header h3 {{ color: #e0e0e0; }}
        body.dark-mode .agent-card {{ border-bottom-color: #3a3a4a; }}
        body.dark-mode .agent-card:hover {{ background: #2e2e4a; }}
        body.dark-mode .agent-card.active {{ background: #2e2e5a; border-left-color: #8899ff; }}
        body.dark-mode .agent-card-name {{ color: #e0e0e0; }}
        body.dark-mode .agent-card-model {{ color: #808090; }}
        body.dark-mode .agent-badge {{ background: #3a3a4a; color: #aaa; }}
        body.dark-mode .agent-badge.default {{ background: #1a3a2a; color: #6ee7b7; }}
        body.dark-mode .agent-badge.channel {{ background: #1e3a5f; color: #93c5fd; }}
        body.dark-mode .agent-card-actions button:hover {{ background: rgba(255,255,255,0.1); }}
        body.dark-mode .agent-form-group label {{ color: #999; }}
        body.dark-mode .agent-form-group input,
        body.dark-mode .agent-form-group select,
        body.dark-mode .agent-form-group textarea {{
            background: #2a2a3a; color: #e0e0e0; border-color: #4a4a5a;
        }}
        body.dark-mode .emoji-dropdown-btn {{ background: #2a2a3a; border-color: #4a4a5a; }}
        body.dark-mode .emoji-dropdown-panel {{ background: #1e1e2e; border-color: #4a4a5a; }}
        body.dark-mode .agent-form-group .emoji-btn {{ background: transparent; }}
        body.dark-mode .agent-form-group .emoji-btn:hover {{ background: #3a3a5a; }}
        body.dark-mode .agent-form-group .emoji-btn.selected {{ background: #2e2e5a; border-color: #8899ff; }}
        body.dark-mode .agent-tool-chip {{ background: #3a3a4a; color: #aaa; }}
        body.dark-mode .agent-tool-chip:hover {{ background: #3a3a5a; }}
        body.dark-mode .agent-tool-chip.selected {{ background: #667eea; color: white; }}
        body.dark-mode .agent-form-actions {{ border-top-color: #3a3a4a; }}
        body.dark-mode .agent-protected-badge {{ background: #1e3a5a; color: #93c5fd; }}
        body.dark-mode .field-tip {{ background: #4a4a5a; color: #ccc; }}
        body.dark-mode .field-tip:hover {{ background: #8899ff; color: white; }}
        body.dark-mode .field-tip .tip-text {{ background: #1a1a2a; color: #e0e0e0; }}
        body.dark-mode .field-tip .tip-text::after {{ border-top-color: #1a1a2a; }}
        body.dark-mode .mcp-server-card {{ border-color: #3a3a4a; background: #1e1e2e; }}
        body.dark-mode .mcp-server-header {{ background: #2a2a3a; }}
        body.dark-mode .mcp-server-header:hover {{ background: #333350; }}
        body.dark-mode .mcp-server-name {{ color: #e0e0e0; }}
        body.dark-mode .mcp-server-body {{ border-top-color: #3a3a4a; }}
        body.dark-mode .mcp-settings-bar {{ border-bottom-color: #3a3a4a; }}
        body.dark-mode .enhanced-editor-stats {{ background: #2a2a3a; border-bottom-color: #3a3a4a; }}
        body.dark-mode .enhanced-editor-stats span {{ color: #aaa; }}

    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px;">\U0001f916</span>
        <h1>{agent_name}</h1>
        <span class="badge">v{api.get_version()}</span>
        <button id="sidebarToggleBtn" class="new-chat mobile-only" title="{ui_js['conversations']}">\u2630</button>
        <div id="modelSelectWrap">
          <select id="agentSelect" title="Agent" style="display:none"></select>
          <select id="providerSelect" class="model-selector" title="{ui_js['change_model']}"></select>
          <select id="modelSelect" class="model-selector" title="{ui_js['change_model']}"></select>
        </div>
        <button id="testNvidiaBtn" class="new-chat" title="{ui_js['nvidia_test_title']}" style="display:none">\U0001f50d {ui_js['nvidia_test_btn']}</button>
        <!-- Populated by JavaScript -->
        <button id="newChatBtn" class="new-chat" onclick="newChat()" title="{ui_js['new_chat_title']}">\u2728 {ui_js['new_chat_btn']}</button>
        <label class="readonly-toggle" title="{ui_js['readonly_title']}">
            <span class="readonly-icon">\U0001f441</span>
            <span class="readonly-name">{ui_js['readonly_label']}</span>
            <input type="checkbox" id="readOnlyToggle" onchange="toggleReadOnly(this.checked)">
            <span class="readonly-slider"></span>
            <span class="readonly-label" id="readOnlyLabel">{ui_js['readonly_off']}</span>
        </label>
        <label class="readonly-toggle dark-mode-toggle" title="{ui_js.get('dark_mode', 'Dark mode')}">
            <span class="readonly-icon" id="themeIcon">\U0001f319</span>
            <input type="checkbox" id="darkModeToggle" onchange="toggleDarkMode(this.checked)">
            <span class="readonly-slider"></span>
            <span class="readonly-label" id="darkModeLabel">OFF</span>
        </label>
        <div class="status">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">{status_text}</span>
        </div>
    </div>

    <div id="codexOAuthBanner">
        <span>&#128273; <strong>OpenAI Codex</strong> requires authentication.</span>
        <button id="codexOAuthConnectBtn">Connect OpenAI Codex</button>
        <button id="codexOAuthDismissBtn" style="background:#e0e0e0;color:#666;">Dismiss</button>
    </div>

    <div id="codexOAuthConnectedBanner">
        <div class="codex-conn-info">
            <div class="codex-conn-dot"></div>
            <span class="codex-conn-text">&#128273; OpenAI Codex</span>
            <span class="codex-conn-detail" id="codexConnDetail">connected</span>
        </div>
        <button onclick="revokeCodexOAuth()">Disconnect</button>
    </div>

    <div id="codexOAuthModal">
        <div class="codex-modal-box">
            <h3>&#128273; Connect OpenAI Codex</h3>
            <div class="codex-modal-step">
                <strong>Step 1 &#8212; Open the OpenAI login page</strong>
                <button id="codexOpenLoginBtn">Open login page &#x2197;</button>
                <p style="margin:8px 0 0;font-size:12px;color:#666;">A new tab will open. Log in with your OpenAI account (ChatGPT Plus/Pro required).</p>
            </div>
            <div class="codex-modal-step">
                <strong>Step 2 &#8212; Paste the redirect URL</strong>
                <p style="margin:0 0 8px;font-size:12px;color:#666;">After logging in, the browser redirects to a page that fails to load (localhost:1455). <strong>Copy the full URL</strong> from your browser bar and paste it here:</p>
                <textarea id="codexRedirectUrl" placeholder="http://localhost:1455/auth/callback?code=...&amp;state=..."></textarea>
            </div>
            <div id="codexOAuthStatus"></div>
            <div class="codex-modal-actions">
                <button class="btn-secondary" id="codexModalCancelBtn">Cancel</button>
                <button class="btn-primary" id="codexModalConnectBtn">&#10004; Connect</button>
            </div>
        </div>
    </div>

    <div id="copilotOAuthBanner">
        <span>&#128273; <strong>GitHub Copilot</strong> requires authentication.</span>
        <button id="copilotOAuthConnectBtn">Connect GitHub Copilot</button>
        <button id="copilotOAuthDismissBtn" style="background:#c9d1fb;color:#0a3069;">Dismiss</button>
    </div>

    <div id="copilotOAuthConnectedBanner">
        <div class="copilot-conn-info">
            <div class="copilot-conn-dot"></div>
            <span class="copilot-conn-text">&#128273; GitHub Copilot</span>
            <span class="copilot-conn-detail" id="copilotConnDetail">connected</span>
        </div>
        <button onclick="revokeCopilotOAuth()">Disconnect</button>
    </div>

    <div id="copilotOAuthModal">
        <div class="copilot-modal-box">
            <h3>&#128273; Connect GitHub Copilot</h3>
            <p style="margin:0 0 12px;font-size:13px;color:#555;">Open <a href="https://github.com/login/device" target="_blank" id="copilotVerifyLink">github.com/login/device</a> and enter this code:</p>
            <div class="copilot-user-code" id="copilotUserCode">&#8230;</div>
            <p class="copilot-poll-hint" id="copilotPollHint">Waiting for you to authorize on GitHub&#8230;</p>
            <div id="copilotOAuthStatus"></div>
            <div class="copilot-modal-actions">
                <button class="btn-secondary" id="copilotModalCancelBtn">Cancel</button>
            </div>
        </div>
    </div>

    <div id="claudeWebBanner">
        <span>&#9888;&#65039; <strong>Claude.ai Web [UNSTABLE]</strong> &mdash; session token required.</span>
        <button id="claudeWebConnectBtn">Set Session Token</button>
        <button id="claudeWebDismissBtn" style="background:#f0ded4;color:#7b3010;">Dismiss</button>
    </div>

    <div id="claudeWebConnectedBanner">
        <div class="cw-conn-info">
            <div class="cw-conn-dot"></div>
            <span class="cw-conn-text">&#128279; Claude.ai Web</span>
            <span class="cw-conn-detail" id="claudeWebConnDetail">connected</span>
        </div>
        <button onclick="disconnectClaudeWeb()">Disconnect</button>
    </div>

    <div id="claudeWebModal">
        <div class="claudeweb-modal-box">
            <h3>&#128273; Claude.ai Web &mdash; Session Token</h3>
            <div class="claudeweb-modal-step">
                <strong>Step 1 &mdash; Get your sessionKey cookie</strong>
                <p style="margin:0 0 8px;font-size:12px;color:#666;">Open <strong>claude.ai</strong>, press <kbd>F12</kbd> to open DevTools, then find the cookie:<br>&bull; <strong>Chrome / Edge:</strong> Application &rarr; Cookies &rarr; claude.ai<br>&bull; <strong>Firefox:</strong> Storage &rarr; Cookies &rarr; https://claude.ai<br>Copy the value of <code>sessionKey</code> (starts with <code>sk-ant-sid01-</code>).</p>
            </div>
            <div class="claudeweb-modal-step">
                <strong>Step 2 &mdash; Paste the session key here</strong>
                <textarea id="claudeWebSessionKeyInput" placeholder="sk-ant-sid01-..."></textarea>
            </div>
            <div id="claudeWebStatus"></div>
            <div class="claudeweb-modal-actions">
                <button class="btn-secondary" id="claudeWebModalCancelBtn">Cancel</button>
                <button class="btn-primary" id="claudeWebModalConnectBtn">&#10004; Save</button>
            </div>
        </div>
    </div>

    <div id="chatgptWebBanner">
        <span>&#9888;&#65039; <strong>ChatGPT Web [UNSTABLE]</strong> &mdash; access token required.</span>
        <button id="chatgptWebConnectBtn">Set Access Token</button>
        <button id="chatgptWebDismissBtn" style="background:#c8f0e0;color:#0d5c3a;">Dismiss</button>
    </div>

    <!-- Gemini Web session banners -->
    <div id="geminiWebBanner">
        <span>&#9888;&#65039; <strong>Gemini Web</strong> &mdash; browser cookies required.</span>
        <button id="geminiWebConnectBtn">Connect Gemini Web</button>
        <button id="geminiWebDismissBtn" style="background:#d6e8f5;color:#0f4c75;">Dismiss</button>
    </div>
    <div id="geminiWebConnectedBanner">
        <div class="gw-conn-info">
            <div class="gw-conn-dot"></div>
            <span class="gw-conn-text">&#128273; Gemini Web</span>
            <span class="gw-conn-detail" id="geminiWebConnDetail">connected</span>
        </div>
        <button id="geminiWebDisconnectBtn">Disconnect</button>
    </div>

    <!-- Gemini Web modal -->
    <div id="geminiWebModal">
        <div class="gemini-web-modal-box">
            <h3>&#128273; Gemini Web &mdash; Connessione</h3>
            <div class="modal-step">
                <strong>Step 1 &mdash; Apri DevTools su gemini.google.com</strong>
                <p style="margin:0 0 8px;font-size:12px;color:#666;">
                    Fai login su <a href="https://gemini.google.com" target="_blank"><strong>gemini.google.com</strong></a>,
                    poi premi <strong>F12</strong> &rarr; <em>Application</em> &rarr; <em>Cookies</em> &rarr; <em>gemini.google.com</em>
                </p>
            </div>
            <div class="modal-step">
                <strong>Step 2 &mdash; Copia il cookie __Secure-1PSID</strong>
                <input type="password" id="geminiWebPsidInput" placeholder="__Secure-1PSID (inizia con g.a…)" style="width:100%;box-sizing:border-box;margin-top:6px;padding:7px 10px;border:1px solid #ccc;border-radius:6px;font-size:13px;font-family:monospace;" />
            </div>
            <div class="modal-step">
                <strong>Step 3 &mdash; Copia il cookie __Secure-1PSIDTS</strong>
                <input type="password" id="geminiWebPsidtsInput" placeholder="__Secure-1PSIDTS" style="width:100%;box-sizing:border-box;margin-top:6px;padding:7px 10px;border:1px solid #ccc;border-radius:6px;font-size:13px;font-family:monospace;" />
            </div>
            <div id="geminiWebStatus" style="min-height:18px;font-size:12px;margin:6px 0;"></div>
            <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;">
                <button id="geminiWebModalCancelBtn" style="background:#eee;color:#333;border:none;padding:7px 16px;border-radius:6px;cursor:pointer;">Annulla</button>
                <button id="geminiWebModalConnectBtn" class="btn-primary">&#10004; Connetti</button>
            </div>
        </div>
    </div>

    <!-- Perplexity Web session banners -->
    <div id="perplexityWebBanner">
        <span>&#9888;&#65039; <strong>Perplexity Web</strong> &mdash; browser cookies required.</span>
        <button id="perplexityWebConnectBtn">Connect Perplexity Web</button>
        <button id="perplexityWebDismissBtn" style="background:#eadcf9;color:#4d2f74;">Dismiss</button>
    </div>
    <div id="perplexityWebConnectedBanner">
        <div class="gw-conn-info">
            <div class="gw-conn-dot"></div>
            <span class="gw-conn-text">&#128273; Perplexity Web</span>
            <span class="gw-conn-detail" id="perplexityWebConnDetail">connected</span>
        </div>
        <button id="perplexityWebDisconnectBtn">Disconnect</button>
    </div>

    <!-- Perplexity Web modal -->
    <div id="perplexityWebModal">
        <div class="gemini-web-modal-box">
            <h3>&#128273; Perplexity Web &mdash; Connection</h3>
            <div class="modal-step">
                <strong>Step 1 &mdash; Open DevTools on perplexity.ai</strong>
                <p style="margin:0 0 8px;font-size:12px;color:#666;">
                    Login on <a href="https://www.perplexity.ai" target="_blank"><strong>perplexity.ai</strong></a>,
                    then press <strong>F12</strong> &rarr; <em>Application</em> &rarr; <em>Cookies</em> &rarr; <em>www.perplexity.ai</em>
                </p>
            </div>
            <div class="modal-step">
                <strong>Step 2 &mdash; Copy cookie next-auth.csrf-token</strong>
                <input type="password" id="perplexityWebCsrfInput" placeholder="next-auth.csrf-token"
                    style="width:100%;box-sizing:border-box;margin-top:6px;padding:7px 10px;border:1px solid #ccc;border-radius:6px;font-size:13px;font-family:monospace;" />
            </div>
            <div class="modal-step">
                <strong>Step 3 &mdash; Copy cookie next-auth.session-token</strong>
                <input type="password" id="perplexityWebSessionInput" placeholder="next-auth.session-token"
                    style="width:100%;box-sizing:border-box;margin-top:6px;padding:7px 10px;border:1px solid #ccc;border-radius:6px;font-size:13px;font-family:monospace;" />
            </div>
            <div id="perplexityWebStatus" style="min-height:18px;font-size:12px;margin:6px 0;"></div>
            <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;">
                <button id="perplexityWebModalCancelBtn" style="background:#eee;color:#333;border:none;padding:7px 16px;border-radius:6px;cursor:pointer;">Cancel</button>
                <button id="perplexityWebModalConnectBtn" class="btn-primary">&#10004; Connect</button>
            </div>
        </div>
    </div>

    <div id="chatgptWebModal">
        <div class="chatgptweb-modal-box">
            <h3>&#128273; ChatGPT Web &mdash; Connessione</h3>
            <div class="chatgptweb-modal-step">
                <strong>Step 1 &mdash; Copia il JSON di sessione</strong>
                <p style="margin:0 0 8px;font-size:12px;color:#666;">
                    Da browser loggato su ChatGPT, apri una nuova scheda e vai su:<br>
                    <a href="https://chatgpt.com/api/auth/session" target="_blank"><strong>chatgpt.com/api/auth/session</strong></a><br><br>
                    Seleziona tutto (<strong>Ctrl+A</strong>) e incolla qui sotto.
                </p>
                <textarea id="chatgptWebTokenInput" placeholder="Incolla qui il JSON completo..." rows="4"></textarea>
            </div>
            <div id="chatgptWebPreview" style="display:none;background:#f0faf4;border:1px solid #b2dfcc;border-radius:8px;padding:10px 13px;margin-bottom:10px;font-size:12px;">
                <div style="font-weight:600;color:#1a7a45;margin-bottom:6px;">&#10003; Chiavi estratte:</div>
                <div style="margin-bottom:4px;">&#128272; <strong>accessToken:</strong> <span id="previewAccessToken" style="font-family:monospace;color:#333;"></span></div>
                <div>&#127850; <strong>sessionToken:</strong> <span id="previewSessionToken" style="font-family:monospace;color:#333;"></span></div>
            </div>
            <div class="chatgptweb-modal-step" style="background:#fff8f0;border-color:#f59e0b;">
                <strong>&#8505; Opzionale: cf_clearance (fix 403)</strong>
                <p style="margin:4px 0 6px;font-size:12px;color:#7c4a00;">
                    Se ricevi errori 403 e HA è sulla <strong>stessa rete del tuo browser</strong> (stesso IP pubblico),
                    incolla qui il cookie <code>cf_clearance</code> da chatgpt.com:<br>
                    DevTools (F12) → Application → Cookies → chatgpt.com → <code>cf_clearance</code>
                </p>
                <input type="text" id="chatgptWebCfClearance" placeholder="cf_clearance (opzionale — lascia vuoto se non necessario)"
                    style="width:100%;box-sizing:border-box;padding:6px 8px;border:1px solid #f59e0b;border-radius:6px;font-size:12px;font-family:monospace;">
            </div>
            <div id="chatgptWebStatus"></div>
            <div class="chatgptweb-modal-actions">
                <button class="btn-secondary" id="chatgptWebModalCancelBtn">Annulla</button>
                <button class="btn-primary" id="chatgptWebModalConnectBtn">&#10004; Salva</button>
            </div>
        </div>
    </div>

    <div id="messagingChatModal">
        <div class="msg-modal-box">
            <div class="msg-modal-header">
                <span id="msgModalTitle">💬 Chat</span>
                <button id="msgModalCloseBtn" title="Close">✕</button>
            </div>
            <div class="msg-modal-body" id="msgModalBody"></div>
        </div>
    </div>

    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-tabs">
                <button class="sidebar-tab primary-tab active" data-tab="chat" onclick="switchSidebarTab('chat')">\U0001f4ac {ui_js['tab_chat']}</button>
                <button class="sidebar-tab primary-tab" data-tab="bubble" onclick="switchSidebarTab('bubble')">\U0001f4ad {ui_js['tab_bubble']}</button>
                <button class="sidebar-tab primary-tab" data-tab="amira" onclick="switchSidebarTab('amira')">\U0001f916 {ui_js.get('tab_amira', 'Amira')}</button>
                <button class="sidebar-tab primary-tab" data-tab="messaging" onclick="switchSidebarTab('messaging')">{ui_js['tab_messaging']}</button>
                <div class="sidebar-tab-row-sep"></div>
                <button class="sidebar-tab" data-tab="files" onclick="switchSidebarTab('files')">{ui_js['tab_files']}</button>
                <button class="sidebar-tab" data-tab="backups" onclick="switchSidebarTab('backups')">\U0001f4be {ui_js['tab_backups']}</button>
                <button class="sidebar-tab" data-tab="devices" onclick="switchSidebarTab('devices')">⚙️ {ui_js['tab_devices']}</button>
                <button class="sidebar-tab" data-tab="costs" onclick="switchSidebarTab('costs')">💰 {ui_js['tab_costs']}</button>
                <button class="sidebar-tab" data-tab="skills" onclick="switchSidebarTab('skills')">{ui_js['tab_skills']}</button>
                <button class="sidebar-tab" data-tab="config" onclick="switchSidebarTab('config')">{ui_js['tab_config']}</button>
            </div>
            <div class="sidebar-content active" id="tabChat">
                <div class="chat-list" id="chatList"></div>
            </div>
            <div class="sidebar-content" id="tabBubble">
                <div class="chat-list" id="bubbleList"></div>
            </div>
            <div class="sidebar-content" id="tabAmira">
                <div class="chat-list" id="amiraList"></div>
            </div>
            <div class="sidebar-content" id="tabBackups">
                <div class="backup-list" id="backupList"></div>
            </div>
            <div class="sidebar-content" id="tabDevices">
                <div class="device-list" id="deviceList"></div>
            </div>
            <div class="sidebar-content" id="tabMessaging">
                <div class="messaging-list" id="messagingList"></div>
            </div>
            <div class="sidebar-content" id="tabFiles">
                <div class="file-tree" id="fileTree"></div>
            </div>
            <div class="sidebar-content" id="tabCosts">
                <div class="costs-panel" id="costsPanel"></div>
            </div>
            <div class="sidebar-content" id="tabSkills">
                <div id="skillsPanel" style="padding:10px 12px;"></div>
            </div>
            <div class="sidebar-content" id="tabConfig">
                <div class="config-list" id="configList"></div>
            </div>
        </div>
        <div class="splitter" id="sidebarSplitter" title="{ui_js['drag_resize']}"></div>
        <div class="file-panel" id="filePanel">
            <div class="file-panel-header">
                <div class="file-panel-tabs" id="filePanelTabs"></div>
                <button class="file-panel-close-all" id="filePanelCloseAll" title="{ui_js['files_close_panel']}">&#x2715;</button>
            </div>
            <div class="file-panel-content" id="filePanelContent"></div>
        </div>
        <div class="file-splitter" id="fileSplitter"></div>
        <div class="main-content">
            <div id="skillsUpdateBanner" style="display:none;align-items:center;gap:8px;background:#fff8e1;border-bottom:1px solid #ffe082;padding:7px 14px;font-size:12px;color:#5d4037;flex-shrink:0;">
                <span style="font-size:15px;">🔔</span>
                <span id="skillsUpdateText" style="flex:1;"></span>
                <button id="skillsUpdateGoBtn" onclick="switchSidebarTab('skills')" style="background:#ff9800;color:#fff;border:none;border-radius:5px;padding:3px 10px;font-size:11px;cursor:pointer;white-space:nowrap;">{ui_js.get('skills_update_go','Vai alle Skill')}</button>
                <button onclick="document.getElementById('skillsUpdateBanner').style.display='none'" style="background:none;border:none;font-size:15px;cursor:pointer;color:#888;line-height:1;">&#x2715;</button>
            </div>
            <div class="chat-container" id="chat">
        <div class="message system">
            {msgs['welcome']}<br>
            {msgs['provider_model']}<br>
            {msgs['capabilities']}<br>
            {msgs['vision_feature']}
        </div>
    </div>

    <div class="suggestions" id="suggestions">
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f4a1 {ui_js['sug_lights']}</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f321 {ui_js['sug_sensors']}</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f3e0 {ui_js['sug_areas']}</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f4c8 {ui_js['sug_temperature']}</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f3ac {ui_js['sug_scenes']}</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\u2699\ufe0f {ui_js['sug_automations']}</div>
    </div>

    <div class="input-area">
        <div class="file-context-bar" id="fileContextBar">
            <span id="fileContextLabel">{ui_js['files_context_label']}</span>
            <span id="fileContextChips"></span>
        </div>
        <div id="imagePreviewContainer" class="image-preview-container">
            <img id="imagePreview" class="image-preview" />
            <button class="remove-image-btn" title="{ui_js['remove_image']}">×</button>
        </div>
        <div id="docPreviewContainer" class="doc-preview-container">
            <span class="doc-preview-icon" id="docPreviewIcon">📄</span>
            <div class="doc-preview-info">
                <div class="doc-preview-name" id="docPreviewName"></div>
                <div class="doc-preview-size" id="docPreviewSize"></div>
            </div>
            <button class="remove-doc-btn" id="removeDocBtn" title="">×</button>
        </div>
        <div class="input-toolbar" id="inputToolbar">
            <button class="fmt-btn" id="fmtCodeBtn" type="button" title="Code" onclick="window.__amiraInputFormat && window.__amiraInputFormat('code')">
                <svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            </button>
            <button class="fmt-btn" id="fmtHtmlBtn" type="button" title="HTML" onclick="window.__amiraInputFormat && window.__amiraInputFormat('html')">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 3h16l-2 18-6 2-6-2z"/><polyline points="8 8 10 12 8 16"/><polyline points="16 8 14 12 16 16"/></svg>
            </button>
            <button class="fmt-btn" id="fmtLinkBtn" type="button" title="Link" onclick="window.__amiraInputFormat && window.__amiraInputFormat('link')">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L10 5"/><path d="M14 11a5 5 0 0 0-7.07 0L4.1 13.83a5 5 0 0 0 7.07 7.07L14 19"/></svg>
            </button>
            <div class="voice-toggle" id="voiceToggle" style="display: {voice_display};">
                <label>
                    <input type="checkbox" id="voiceModeCheckbox" />
                    <span class="toggle-track"><span class="toggle-thumb"></span></span>
                    <span class="toggle-label">{ui_js['voice_mode']}</span>
                </label>
            </div>
        </div>
        <div class="input-row">
            <input type="file" id="imageInput" accept="image/*" style="display: none;" />
            <button class="image-btn" title="{ui_js['upload_image']}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
            </button>
            <input type="file" id="documentInput" accept=".pdf,.docx,.doc,.txt,.md,.yaml,.yml,.odt" style="display: none;" />
            <button class="file-btn" title="Upload Document (PDF, DOCX, TXT, MD, YAML)" style="display: {file_upload_display};" id="fileUploadBtn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
            </button>
            <button class="mic-btn" title="{ui_js['voice_mode']}" style="display: {voice_display};" id="micBtn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
            </button>

            <textarea id="input" rows="1" placeholder="{ui_js['input_placeholder']}"></textarea>
            <button id="sendBtn">
                <svg id="sendIcon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                <svg id="stopIcon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="display:none"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
            </button>
        </div>
        <div class="voice-speaking-bar" id="voiceSpeakingBar" title="{ui_js['voice_stop_speaking']}">
            <div class="wave"><span></span><span></span><span></span><span></span><span></span></div>
            <span id="voiceSpeakingLabel">{ui_js['voice_speaking']}</span>
        </div>
    </div>
        </div>
    </div>

    <script>
        // Global error handler — shows JS errors as visible banner + sends to backend
        if (!window.__AMIRA_ERROR_HANDLER) {{
            window.__AMIRA_ERROR_HANDLER = true;
            window.__AMIRA_BROWSER_ERRORS = [];
            function _amiraSendError(entry) {{
                window.__AMIRA_BROWSER_ERRORS.push(entry);
                if (window.__AMIRA_BROWSER_ERRORS.length > 100) window.__AMIRA_BROWSER_ERRORS.shift();
                try {{
                    var bp = (window.location.pathname || '/').endsWith('/') ? window.location.pathname : (window.location.pathname + '/');
                    var url = window.location.origin.replace(/\\/$/, '') + bp + 'api/browser-errors';
                    navigator.sendBeacon(url, JSON.stringify({{ errors: [entry] }}));
                }} catch(e) {{}}
            }}
            window.onerror = function(msg, src, line, col, err) {{
                console.error('[Amira JS Error]', msg, 'at', src, line + ':' + col, err);
                _amiraSendError({{ level: 'error', message: String(msg), source: src || '', line: line, col: col, stack: err && err.stack || '', timestamp: new Date().toISOString(), ui: 'chat_ui' }});
                var d = document.createElement('div');
                d.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:#b00020;color:#fff;padding:12px 16px;font:13px/1.4 monospace;max-height:30vh;overflow:auto;cursor:pointer;';
                d.textContent = '[JS Error] ' + msg + ' (line ' + line + ':' + col + ')';
                d.title = 'Click per chiudere';
                d.onclick = function() {{ d.remove(); }};
                document.body ? document.body.prepend(d) : document.addEventListener('DOMContentLoaded', function() {{ document.body.prepend(d); }});
            }};
            window.addEventListener('unhandledrejection', function(ev) {{
                console.error('[Amira Promise Error]', ev.reason);
                var reason = ev.reason && ev.reason.message || ev.reason || 'Unknown';
                _amiraSendError({{ level: 'error', message: '[Promise] ' + reason, source: '', stack: ev.reason && ev.reason.stack || '', timestamp: new Date().toISOString(), ui: 'chat_ui' }});
                var d = document.createElement('div');
                d.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:#b00020;color:#fff;padding:12px 16px;font:13px/1.4 monospace;max-height:30vh;overflow:auto;cursor:pointer;';
                d.textContent = '[Promise Error] ' + reason;
                d.title = 'Click per chiudere';
                d.onclick = function() {{ d.remove(); }};
                document.body ? document.body.prepend(d) : document.addEventListener('DOMContentLoaded', function() {{ document.body.prepend(d); }});
            }});
            // Also intercept console.error/console.warn to capture card/component errors
            var _origError = console.error, _origWarn = console.warn;
            console.error = function() {{
                var msg = Array.prototype.slice.call(arguments).map(function(a) {{ return typeof a === 'object' ? JSON.stringify(a) : String(a); }}).join(' ');
                if (msg.indexOf('_amiraSendError') === -1 && msg.indexOf('[Amira') === -1) {{
                    _amiraSendError({{ level: 'error', message: msg.substring(0, 1000), source: 'console.error', timestamp: new Date().toISOString(), ui: 'chat_ui' }});
                }}
                _origError.apply(console, arguments);
            }};
            console.warn = function() {{
                var msg = Array.prototype.slice.call(arguments).map(function(a) {{ return typeof a === 'object' ? JSON.stringify(a) : String(a); }}).join(' ');
                if (msg.indexOf('_amiraSendError') === -1) {{
                    _amiraSendError({{ level: 'warning', message: msg.substring(0, 1000), source: 'console.warn', timestamp: new Date().toISOString(), ui: 'chat_ui' }});
                }}
                _origWarn.apply(console, arguments);
            }};
        }}
        if (window.__UI_MAIN_INITIALIZED) {{
            console.log('[ui] main already initialized');
        }} else {{
        window.__UI_MAIN_INITIALIZED = true;
        const T = {ui_js_json};
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('sendBtn');
        const sendIcon = document.getElementById('sendIcon');
        const stopIcon = document.getElementById('stopIcon');
        const suggestionsEl = document.getElementById('suggestions');
        const chatList = document.getElementById('chatList');
        const imageInput = document.getElementById('imageInput');
        const imagePreview = document.getElementById('imagePreview');
        const imagePreviewContainer = document.getElementById('imagePreviewContainer');
        const sidebarEl = document.querySelector('.sidebar');
        const splitterEl = document.getElementById('sidebarSplitter');

        // ---- File Explorer state ----
        const filePanelEl       = document.getElementById('filePanel');
        const fileSplitterEl    = document.getElementById('fileSplitter');
        const fileTreeEl        = document.getElementById('fileTree');
        const filePanelTabsEl   = document.getElementById('filePanelTabs');
        const filePanelContentEl= document.getElementById('filePanelContent');
        const filePanelCloseAllEl = document.getElementById('filePanelCloseAll');
        const fileContextBarEl  = document.getElementById('fileContextBar');
        const fileContextChipsEl= document.getElementById('fileContextChips');
        let fileCurrentPath = '';
        let fileOpenTabs    = [];   // [{{path, name, content, truncated, loading, error}}]
        let fileActiveTabIdx= -1;

        let sending = false;
        let currentReader = null;

        // ---- Voice Mode State ----
        const micBtn = document.getElementById('micBtn');
        const voiceModeCheckbox = document.getElementById('voiceModeCheckbox');
        const voiceSpeakingBar = document.getElementById('voiceSpeakingBar');
        const voiceSpeakingLabel = document.getElementById('voiceSpeakingLabel');
        let voiceModeActive = safeLocalStorageGet('amira_voice_mode') === 'true';
        let isRecording = false;
        let mediaRecorder = null;
        let audioChunks = [];
        let currentAudio = null;
        let voiceTriggeredMessage = false;
        let audioContextUnlocked = false;
        let sharedAudioContext = null;
        let _silenceDetectorId = null;
        let _voiceAudioCtx = null;
        let _wakeWordTriggered = false;  // true when recording was started by wake word

        // Polyfill: navigator.mediaDevices for older browsers / insecure iframe contexts
        (function() {{
            if (navigator.mediaDevices === undefined) {{
                navigator.mediaDevices = {{}};
            }}
            if (navigator.mediaDevices.getUserMedia === undefined) {{
                navigator.mediaDevices.getUserMedia = function(constraints) {{
                    const legacy = navigator.getUserMedia || navigator.webkitGetUserMedia ||
                                   navigator.mozGetUserMedia || navigator.msGetUserMedia;
                    if (!legacy) {{
                        return Promise.reject(new Error('getUserMedia not supported by this browser'));
                    }}
                    return new Promise(function(resolve, reject) {{
                        legacy.call(navigator, constraints, resolve, reject);
                    }});
                }};
            }}
        }})();

        // Unlock AudioContext on any user gesture (required for mobile autoplay)
        function unlockAudioContext() {{
            if (audioContextUnlocked) return;
            try {{
                sharedAudioContext = new (window.AudioContext || window.webkitAudioContext)();
                // Play a silent buffer to unlock
                const buf = sharedAudioContext.createBuffer(1, 1, 22050);
                const src = sharedAudioContext.createBufferSource();
                src.buffer = buf;
                src.connect(sharedAudioContext.destination);
                src.start(0);
                audioContextUnlocked = true;
                console.log('AudioContext unlocked for TTS playback');
            }} catch(e) {{ console.warn('AudioContext unlock failed:', e); }}
        }}

        // Restore voice mode toggle state
        if (voiceModeCheckbox) {{
            voiceModeCheckbox.checked = voiceModeActive;
            voiceModeCheckbox.addEventListener('change', async function() {{
                voiceModeActive = this.checked;
                safeLocalStorageSet('amira_voice_mode', voiceModeActive ? 'true' : 'false');
                unlockAudioContext();  // Unlock on toggle interaction
                // Check TTS providers when enabling voice mode
                if (voiceModeActive) {{
                    try {{
                        const provResp = await fetch(apiUrl('api/voice/tts/providers'));
                        if (provResp.ok) {{
                            const provData = await provResp.json();
                            if (!provData.providers || provData.providers.length === 0) {{
                                showNotification(T.voice_tts_no_provider || 'Voice output unavailable. Edge TTS or a Groq/OpenAI API key is needed.', 'warning');
                            }} else {{
                                console.log('[TTS] Available providers:', provData.providers);
                            }}
                        }}
                    }} catch(e) {{ console.warn('[TTS] Could not check providers:', e); }}
                }}
            }});
        }}

        // Stop TTS playback when clicking the speaking bar
        if (voiceSpeakingBar) {{
            voiceSpeakingBar.addEventListener('click', function() {{
                stopTTSPlayback();
            }});
        }}

        function stopTTSPlayback() {{
            if (currentAudio) {{
                currentAudio.pause();
                currentAudio.currentTime = 0;
                currentAudio = null;
            }}
            if (voiceSpeakingBar) voiceSpeakingBar.classList.remove('active');
        }}

        async function startVoiceRecording() {{
            if (isRecording) {{
                stopVoiceRecording();
                return;
            }}
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                audioChunks = [];
                // Prefer webm/opus, fall back to whatever browser supports
                const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                    ? 'audio/webm;codecs=opus'
                    : (MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '');
                const options = mimeType ? {{ mimeType }} : {{}};
                mediaRecorder = new MediaRecorder(stream, options);
                mediaRecorder.ondataavailable = function(e) {{
                    if (e.data.size > 0) audioChunks.push(e.data);
                }};
                mediaRecorder.onstop = async function() {{
                    stream.getTracks().forEach(t => t.stop());
                    if (audioChunks.length === 0) return;
                    const audioBlob = new Blob(audioChunks, {{ type: mediaRecorder.mimeType || 'audio/webm' }});
                    await transcribeAndSend(audioBlob);
                }};
                mediaRecorder.start();
                isRecording = true;
                if (micBtn) {{
                    micBtn.classList.add('recording');
                    micBtn.title = T.voice_listening || 'Listening...';
                }}
                if (input) {{
                    input.placeholder = T.voice_listening || 'Listening...';
                }}
                // --- Silence detection (only for wake-word triggered recordings) ---
                if (_wakeWordTriggered) {{
                    _startSilenceDetector(stream);
                }}
            }} catch (err) {{
                console.error('Mic error:', err);
                let msg = T.mic_error || 'Microphone error';
                if (err.name === 'NotAllowedError') {{
                    msg = T.mic_denied_settings || msg;
                }} else if (err.name === 'NotFoundError') {{
                    msg = T.mic_not_found || msg;
                }} else if (err.name === 'NotReadableError') {{
                    msg = T.mic_in_use || msg;
                }}
                addMessage('\u274c ' + msg, 'system');
            }}
        }}

        function _startSilenceDetector(stream) {{
            // Dynamic silence detection: calibrates ambient noise, then stops
            // when audio drops back to noise floor after speech.
            const CALIBRATION_MS = 400;   // measure noise floor for 400ms
            const SPEECH_MARGIN  = 8;     // RMS above floor to count as speech
            const SILENCE_DURATION = 1200; // 1.2s silence after speech = stop
            const MAX_RECORD_MS = 10000;   // 10s absolute max
            const CHECK_MS = 80;           // poll interval
            try {{
                _voiceAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const source = _voiceAudioCtx.createMediaStreamSource(stream);
                const analyser = _voiceAudioCtx.createAnalyser();
                analyser.fftSize = 512;
                source.connect(analyser);
                const buf = new Uint8Array(analyser.fftSize);
                let calSamples = [];
                let noiseFloor = 0;
                let speechDetected = false;
                let silenceStart = 0;
                const t0 = Date.now();
                _silenceDetectorId = setInterval(() => {{
                    if (!isRecording) {{ _stopSilenceDetector(); return; }}
                    const elapsed = Date.now() - t0;
                    if (elapsed > MAX_RECORD_MS) {{
                        console.log('[Voice] Max recording time — auto-stop');
                        stopVoiceRecording(); return;
                    }}
                    analyser.getByteTimeDomainData(buf);
                    let sum = 0;
                    for (let i = 0; i < buf.length; i++) {{
                        const v = buf[i] - 128; sum += v * v;
                    }}
                    const rms = Math.sqrt(sum / buf.length);
                    // Phase 1: calibrate the ambient noise level
                    if (elapsed < CALIBRATION_MS) {{ calSamples.push(rms); return; }}
                    if (!noiseFloor && calSamples.length) {{
                        noiseFloor = calSamples.reduce((a,b)=>a+b,0) / calSamples.length;
                        console.log('[Voice] Noise floor calibrated:', noiseFloor.toFixed(1));
                    }}
                    const threshold = noiseFloor + SPEECH_MARGIN;
                    // Phase 2: detect speech then silence
                    if (rms > threshold) {{
                        speechDetected = true;
                        silenceStart = 0;
                    }} else if (speechDetected) {{
                        if (!silenceStart) silenceStart = Date.now();
                        else if (Date.now() - silenceStart >= SILENCE_DURATION) {{
                            console.log('[Voice] Silence detected — auto-stop');
                            stopVoiceRecording(); return;
                        }}
                    }}
                }}, CHECK_MS);
            }} catch(e) {{
                console.warn('[Voice] Silence detector init failed:', e);
            }}
        }}

        function _stopSilenceDetector() {{
            if (_silenceDetectorId) {{ clearInterval(_silenceDetectorId); _silenceDetectorId = null; }}
            if (_voiceAudioCtx) {{ try {{ _voiceAudioCtx.close(); }} catch(e) {{}} _voiceAudioCtx = null; }}
        }}

        function stopVoiceRecording() {{
            _stopSilenceDetector();
            _wakeWordTriggered = false;
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
            }}
            isRecording = false;
            if (micBtn) {{
                micBtn.classList.remove('recording');
                micBtn.classList.add('processing');
                micBtn.title = T.voice_processing || 'Processing...';
            }}
        }}

        async function transcribeAndSend(audioBlob) {{
            try {{
                if (input) input.placeholder = T.voice_processing || 'Processing audio...';
                const formData = new FormData();
                const ext = (audioBlob.type || '').includes('webm') ? 'webm' : 'wav';
                formData.append('file', audioBlob, `voice.${{ext}}`);
                const resp = await fetch(apiUrl('api/voice/transcribe'), {{
                    method: 'POST',
                    body: formData
                }});
                const data = await resp.json();
                if (data.status === 'success' && data.text) {{
                    if (input) input.value = data.text;
                    voiceTriggeredMessage = true;
                    await sendMessage();
                }} else {{
                    addMessage('\u274c ' + (data.message || T.voice_transcription_error || 'Transcription failed'), 'system');
                }}
            }} catch (err) {{
                console.error('Transcription error:', err);
                addMessage('\u274c ' + (T.voice_transcription_error || 'Transcription failed'), 'system');
            }} finally {{
                if (micBtn) {{
                    micBtn.classList.remove('recording', 'processing');
                    micBtn.title = T.voice_mode || 'Voice';
                }}
                if (input) input.placeholder = '{ui_js['input_placeholder']}';
            }}
        }}

        async function playTTSResponse(text) {{
            if (!text || !voiceModeActive) return;
            // Strip markdown + technical info for cleaner speech
            let cleanText = text
                .replace(/```[\\s\\S]*?```/g, '')   // remove code blocks
                .replace(/`[^`]+`/g, '')            // remove inline code
                .replace(/\\[([^\\]]+)\\]\\([^)]+\\)/g, '$1')  // [text](url) -> text
                .replace(/^[\\s]*[-*]\\s*(?:switch|light|sensor|binary_sensor|automation|script|input_boolean|climate|cover|fan|media_player|vacuum|lock|alarm)\\.[^\\n]*/gim, '')  // remove full lines: - sensor.xxx = value
                .replace(/\\([^)]*(?:switch|light|sensor|binary_sensor|automation|script|input_boolean|climate|cover|fan|media_player|vacuum|lock|alarm)[^)]*\\)/gi, '')  // remove (entity_id: state) patterns
                .replace(/\\b(?:switch|light|sensor|binary_sensor|automation|script|input_boolean|climate|cover|fan|media_player|vacuum|lock|alarm)\\.[a-z0-9_]+(?:\\s*[:=]\\s*[^\\n,)]*)?/gi, '')  // remove entity_id and optional = value
                .replace(/\\p{{Emoji_Presentation}}|\\p{{Extended_Pictographic}}/gu, '')  // remove emoji
                .replace(/[#*_~>|]/g, '')            // remove markdown chars (keep -)
                .replace(/\\/{2,}/g, ' ')            // remove multiple slashes
                .replace(/(?<=\\s)\\/(?=\\s)/g, ' ')  // remove isolated /
                .replace(/\\n+/g, '. ')              // newlines to pauses
                .replace(/\\s*\\.\\s*\\.\\s*/g, '. ')  // collapse multiple dots
                .replace(/\\s+/g, ' ')               // collapse whitespace
                .trim();
            if (!cleanText || cleanText.length < 2) return;
            // Limit length for TTS (avoid very long responses)
            if (cleanText.length > 1000) cleanText = cleanText.substring(0, 1000) + '...';
            try {{
                if (voiceSpeakingBar) {{
                    voiceSpeakingBar.classList.add('active');
                    if (voiceSpeakingLabel) voiceSpeakingLabel.textContent = T.voice_speaking || 'Speaking...';
                }}
                console.log('[TTS] Fetching audio for', cleanText.length, 'chars...');
                const ttsUrl = apiUrl('api/voice/tts');
                console.log('[TTS] URL:', ttsUrl);
                const resp = await fetch(ttsUrl, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ text: cleanText }})
                }});
                console.log('[TTS] Response status:', resp.status, resp.statusText);
                if (!resp.ok) {{
                    const errBody = await resp.text().catch(() => '');
                    console.error('[TTS] Error body:', errBody);
                    throw new Error('TTS response ' + resp.status + ': ' + errBody);
                }}
                const audioBlob = await resp.blob();
                console.log('[TTS] Got audio blob:', audioBlob.size, 'bytes, type:', audioBlob.type);
                if (audioBlob.size < 100) {{
                    console.error('[TTS] Audio blob too small, likely an error');
                    throw new Error('TTS returned empty/invalid audio');
                }}
                const audioUrl = URL.createObjectURL(audioBlob);
                stopTTSPlayback();  // stop any previous audio

                // Ensure AudioContext is initialized even if not unlocked yet
                if (!sharedAudioContext) {{
                    try {{
                        sharedAudioContext = new (window.AudioContext || window.webkitAudioContext)();
                        console.log('[TTS] Created AudioContext, state:', sharedAudioContext.state);
                    }} catch(e) {{ console.warn('[TTS] AudioContext creation failed:', e); }}
                }}

                // Try Web Audio API first (works best after user gesture unlock)
                if (sharedAudioContext) {{
                    try {{
                        if (sharedAudioContext.state === 'suspended') {{
                            await sharedAudioContext.resume();
                            console.log('[TTS] AudioContext resumed, state:', sharedAudioContext.state);
                        }}
                        const arrayBuffer = await audioBlob.arrayBuffer();
                        const audioBuffer = await sharedAudioContext.decodeAudioData(arrayBuffer.slice(0));
                        const source = sharedAudioContext.createBufferSource();
                        source.buffer = audioBuffer;
                        source.connect(sharedAudioContext.destination);
                        source.onended = function() {{
                            URL.revokeObjectURL(audioUrl);
                            currentAudio = null;
                            if (voiceSpeakingBar) voiceSpeakingBar.classList.remove('active');
                        }};
                        source.start(0);
                        currentAudio = {{ _source: source, pause: function() {{ try {{ source.stop(); }} catch(e) {{}} }}, currentTime: 0 }};
                        console.log('[TTS] Playing via Web Audio API');
                        return;
                    }} catch(webAudioErr) {{
                        console.warn('[TTS] Web Audio API failed, trying HTML5 Audio:', webAudioErr);
                    }}
                }}

                // Fallback: standard HTML5 Audio
                console.log('[TTS] Trying HTML5 Audio fallback...');
                currentAudio = new Audio(audioUrl);
                currentAudio.onended = function() {{
                    URL.revokeObjectURL(audioUrl);
                    currentAudio = null;
                    if (voiceSpeakingBar) voiceSpeakingBar.classList.remove('active');
                }};
                currentAudio.onerror = function(e) {{
                    console.error('[TTS] HTML5 Audio error:', e);
                    URL.revokeObjectURL(audioUrl);
                    currentAudio = null;
                    if (voiceSpeakingBar) voiceSpeakingBar.classList.remove('active');
                }};
                await currentAudio.play();
                console.log('[TTS] Playing via HTML5 Audio');
            }} catch (err) {{
                console.error('[TTS] Error:', err);
                if (voiceSpeakingBar) voiceSpeakingBar.classList.remove('active');
            }}
        }}

        // Mic button click handler
        if (micBtn) {{
            micBtn.addEventListener('click', async function() {{
                unlockAudioContext();  // Unlock audio on user gesture (mobile)
                // Check if getUserMedia is possible
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                    const isSecure = window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
                    if (!isSecure) {{
                        const origin = location.origin || (location.protocol + '//' + location.host);
                        const msg = '\u274c ' + (T.mic_needs_https || 'Microphone requires HTTPS.')
                            + '\\n\\n\ud83d\udca1 Indirizzo corrente: ' + origin
                            + '\\nCopia questo indirizzo nel flag Chrome per abilitare il microfono.';
                        addMessage(msg, 'system');
                    }} else {{
                        addMessage('\u274c ' + (T.mic_not_supported || 'Browser does not support audio recording'), 'system');
                    }}
                    return;
                }}
                // On first click, try to get mic permission to detect issues early
                if (!isRecording && !mediaRecorder) {{
                    try {{
                        const testStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        testStream.getTracks().forEach(t => t.stop());
                    }} catch (permErr) {{
                        console.error('[Mic] Permission/access error:', permErr.name, permErr.message);
                        if (permErr.name === 'NotAllowedError') {{
                            addMessage('\u274c ' + (T.mic_denied_icon || 'Microphone denied. Check browser permissions.'), 'system');
                        }} else if (permErr.name === 'NotFoundError') {{
                            addMessage('\u274c ' + (T.mic_not_found || 'No microphone found.'), 'system');
                        }} else if (permErr.name === 'NotReadableError' || permErr.name === 'AbortError') {{
                            addMessage('\u274c ' + (T.mic_in_use || 'Microphone in use by another app.'), 'system');
                        }} else {{
                            // Likely insecure context (HTTP without localhost)
                            const isSecure = window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
                            if (!isSecure) {{
                                const origin = location.origin || (location.protocol + '//' + location.host);
                                const msg = '\u274c ' + (T.mic_needs_https || 'Microphone requires HTTPS.')
                                    + '\\n\\n\ud83d\udca1 Indirizzo corrente: ' + origin
                                    + '\\nCopia questo indirizzo nel flag Chrome per abilitare il microfono.';
                                addMessage(msg, 'system');
                            }} else {{
                                addMessage('\u274c ' + (T.mic_error || 'Microphone error') + ': ' + permErr.message, 'system');
                            }}
                        }}
                        return;
                    }}
                }}
                if (isRecording) {{
                    stopVoiceRecording();
                }} else {{
                    startVoiceRecording();
                }}
            }});
        }}

        // ---- Wake Word Detection ("Ok Amira") ----
        // Uses Web Speech API in continuous mode to listen for the wake word.
        // When detected, automatically starts MediaRecorder to capture the command.
        let wakeWordRecognition = null;
        let wakeWordActive = false;
        const WAKE_PHRASES = ['ok amira', 'okay amira', 'ehi amira', 'hey amira', 'amira'];

        function startWakeWordListener() {{
            if (wakeWordActive || !voiceModeActive) return;
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRec) return;

            wakeWordRecognition = new SpeechRec();
            wakeWordRecognition.lang = '{ui_lang}' === 'it' ? 'it-IT' : '{ui_lang}' === 'es' ? 'es-ES' : '{ui_lang}' === 'fr' ? 'fr-FR' : 'en-US';
            wakeWordRecognition.continuous = true;
            wakeWordRecognition.interimResults = true;

            wakeWordRecognition.onresult = function(event) {{
                for (let i = event.resultIndex; i < event.results.length; i++) {{
                    const transcript = event.results[i][0].transcript.toLowerCase().trim();
                    const detected = WAKE_PHRASES.some(p => transcript.includes(p));
                    if (detected) {{
                        // Stop wake word listener immediately
                        stopWakeWordListener();
                        // Visual feedback
                        if (micBtn) {{
                            micBtn.classList.add('recording');
                            micBtn.title = T.wake_word_detected || 'Amira activated! Speak now...';
                        }}
                        if (input) input.placeholder = T.wake_word_detected || 'Amira activated! Speak now...';
                        // Start recording after a tiny delay to avoid capturing the wake word itself
                        setTimeout(function() {{
                            _wakeWordTriggered = true;
                            startVoiceRecording();
                        }}, 300);
                        return;
                    }}
                }}
            }};

            wakeWordRecognition.onend = function() {{
                // Auto-restart if voice mode is still active (browser may stop it)
                wakeWordActive = false;
                if (voiceModeActive && !isRecording && !sending) {{
                    setTimeout(function() {{ startWakeWordListener(); }}, 500);
                }}
            }};

            wakeWordRecognition.onerror = function(e) {{
                // 'no-speech' and 'aborted' are normal — just restart
                if (e.error !== 'no-speech' && e.error !== 'aborted') {{
                    console.warn('Wake word error:', e.error);
                }}
                wakeWordActive = false;
            }};

            try {{
                wakeWordRecognition.start();
                wakeWordActive = true;
                console.log('Wake word listener started — say "Ok Amira"');
            }} catch (err) {{
                console.warn('Wake word start failed:', err);
                wakeWordActive = false;
            }}
        }}

        function stopWakeWordListener() {{
            if (wakeWordRecognition) {{
                try {{ wakeWordRecognition.abort(); }} catch(e) {{}}
                wakeWordRecognition = null;
            }}
            wakeWordActive = false;
        }}

        // Start/stop wake word listener when voice mode is toggled
        if (voiceModeCheckbox) {{
            voiceModeCheckbox.addEventListener('change', function() {{
                if (voiceModeActive) {{
                    startWakeWordListener();
                }} else {{
                    stopWakeWordListener();
                }}
            }});
            // Auto-start on page load if voice mode was previously enabled
            if (voiceModeActive) {{
                setTimeout(function() {{ startWakeWordListener(); }}, 1000);
            }}
        }}

        // Restart wake word listener after TTS finishes playing
        const _origOnEnded = function() {{
            // Re-enable wake word after response is read aloud
            if (voiceModeActive && !isRecording) {{
                setTimeout(function() {{ startWakeWordListener(); }}, 500);
            }}
        }};

        // Patch playTTSResponse to restart wake word after TTS playback
        const _originalPlayTTS = playTTSResponse;
        playTTSResponse = async function(text) {{
            stopWakeWordListener();  // Pause wake word during TTS playback
            await _originalPlayTTS(text);
            // The onended handler in the audio will trigger _origOnEnded indirectly;
            // but as a safety net, restart after a delay
            setTimeout(function() {{
                if (voiceModeActive && !isRecording && !currentAudio) {{
                    startWakeWordListener();
                }}
            }}, 2000);
        }};

        function safeLocalStorageGet(key) {{
            try {{
                return localStorage.getItem(key);
            }} catch (e) {{
                return null;
            }}
        }}

        function safeLocalStorageSet(key, value) {{
            try {{
                localStorage.setItem(key, value);
            }} catch (e) {{
                // ignore
            }}
        }}

        let currentSessionId = safeLocalStorageGet('currentSessionId') || Date.now().toString();
        // If the stored session belongs to the bubble, start a fresh chat-UI conversation
        if (currentSessionId.startsWith('bubble_')) {{
            currentSessionId = Date.now().toString();
            safeLocalStorageSet('currentSessionId', currentSessionId);
        }}
        let currentImage = null;  // Stores base64 image data
        let pendingDocument = null;  // Stores {{file, name, size}} for upload on send
        let readOnlyMode = safeLocalStorageGet('readOnlyMode') === 'true';
        let darkMode = safeLocalStorageGet('darkMode') === 'true';
        let currentProviderId = '{ai_provider}' || 'anthropic';
        let currentModelDisplay = '{model_name}';  // Updated by loadModels() and changeModel()
        const WEB_DASH_WARN_PROVIDERS = new Set(['claude_web', 'chatgpt_web', 'gemini_web', 'perplexity_web', 'github_copilot']);
        const _webDashWarnShown = {{}};

        const ANALYZING_MSG = {json.dumps(analyzing_msg)};

        function maybeWarnWebDashboard(providerId) {{
            try {{
                const pid = String(providerId || '');
                if (!WEB_DASH_WARN_PROVIDERS.has(pid)) return;
                if (_webDashWarnShown[pid]) return;
                _webDashWarnShown[pid] = true;
                addMessage(
                    (T.web_html_warn || '⚠️ Unofficial web provider: HTML dashboard creation may be incomplete or malformed. Always verify the generated file.'),
                    'system-error'
                );
            }} catch (e) {{}}
        }}

        function _appendSystemRaw(text) {{
            try {{
                const container = document.getElementById('chat');
                if (!container) return;
                const div = document.createElement('div');
                div.className = 'message system';
                div.textContent = String(text || '');
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }} catch (e) {{}}
        }}

        // Show JS runtime errors directly in chat (useful on mobile where console isn't visible)
        window.addEventListener('error', function (evt) {{
            try {{
                const msg = (evt && evt.message) ? evt.message : 'Unknown error';
                _appendSystemRaw('❌ UI error: ' + msg);
            }} catch (e) {{}}
        }});
        window.addEventListener('unhandledrejection', function (evt) {{
            try {{
                const r = evt && evt.reason;
                const msg = r && r.message ? r.message : String(r || 'Unknown rejection');
                _appendSystemRaw('❌ UI error: ' + msg);
            }} catch (e) {{}}
        }});

        function getAnalyzingMsg() {{
            return ANALYZING_MSG;
        }}

        function initSidebarResize() {{
            if (!sidebarEl || !splitterEl) return;

            // On mobile (<600px), sidebar is stacked/hidden — skip resize.
            // On tablet (600-1199px) and desktop (1200px+), allow resize with mouse AND touch.
            const isMobileLayout = window.matchMedia('(max-width: 599px)').matches;
            if (isMobileLayout) return;

            const minWidth = 140;
            const MIN_CHAT = 320; // keep chat area readable
            function getMaxWidth() {{
                // Leave room for splitter + chat area, but allow wider sidebars on tablet.
                const byViewport = window.innerWidth - MIN_CHAT - splitterEl.getBoundingClientRect().width - 8;
                return Math.max(minWidth, Math.min(520, byViewport));
            }}
            const storageKey = 'chatSidebarWidth';

            const saved = parseInt(safeLocalStorageGet(storageKey) || '', 10);
            if (!Number.isNaN(saved)) {{
                const w = Math.max(minWidth, Math.min(getMaxWidth(), saved));
                sidebarEl.style.width = w + 'px';
            }}

            let dragging = false;
            let startX = 0;
            let startWidth = 0;

            function startDrag(x) {{
                dragging = true;
                startX = x;
                startWidth = sidebarEl.getBoundingClientRect().width;
                document.body.classList.add('resizing');
            }}

            function moveDrag(x) {{
                if (!dragging) return;
                const dx = x - startX;
                let next = Math.max(minWidth, Math.min(getMaxWidth(), startWidth + dx));
                sidebarEl.style.width = next + 'px';
            }}

            function endDrag() {{
                if (!dragging) return;
                dragging = false;
                document.body.classList.remove('resizing');
                const finalW = Math.round(sidebarEl.getBoundingClientRect().width);
                safeLocalStorageSet(storageKey, String(finalW));
            }}

            // Mouse events
            splitterEl.addEventListener('mousedown', (e) => {{ startDrag(e.clientX); e.preventDefault(); }});
            window.addEventListener('mousemove', (e) => moveDrag(e.clientX));
            window.addEventListener('mouseup', endDrag);

            // Touch events (tablet)
            splitterEl.addEventListener('touchstart', (e) => {{
                if (e.touches.length === 1) {{ startDrag(e.touches[0].clientX); e.preventDefault(); }}
            }}, {{ passive: false }});
            window.addEventListener('touchmove', (e) => {{
                if (dragging && e.touches.length === 1) {{
                    e.preventDefault();
                    moveDrag(e.touches[0].clientX);
                }}
            }}, {{ passive: false }});
            window.addEventListener('touchend', endDrag);

            // Keep width valid after orientation/viewport changes.
            window.addEventListener('resize', () => {{
                const currentW = Math.round(sidebarEl.getBoundingClientRect().width);
                const clamped = Math.max(minWidth, Math.min(getMaxWidth(), currentW));
                if (clamped !== currentW) sidebarEl.style.width = clamped + 'px';
            }});
        }}

        // ===== FILE PANEL RESIZE (mirrors initSidebarResize) =====
        function initFilePanelResize() {{
            if (!filePanelEl || !fileSplitterEl) return;
            if (window.matchMedia('(max-width: 599px)').matches) return;

            const minW = 180;
            const MIN_CHAT = 300; // always leave at least 300px for the chat area
            const storageKey = 'chatFilePanelWidth';

            let dragging = false, startX = 0, startWidth = 0;

            function getMaxW() {{
                // Available width = window minus sidebar minus splitters, leave MIN_CHAT for chat
                const sidebarW = sidebarEl ? sidebarEl.getBoundingClientRect().width : 240;
                return Math.max(minW, window.innerWidth - sidebarW - 10 - MIN_CHAT);
            }}

            function startDrag(x) {{
                dragging = true; startX = x;
                startWidth = filePanelEl.getBoundingClientRect().width;
                document.body.classList.add('resizing');
                // Remove transition during drag for smooth feel
                filePanelEl.style.transition = 'none';
            }}
            function moveDrag(x) {{
                if (!dragging) return;
                const next = Math.max(minW, Math.min(getMaxW(), startWidth + (x - startX)));
                filePanelEl.style.width = next + 'px';
            }}
            function endDrag() {{
                if (!dragging) return;
                dragging = false;
                document.body.classList.remove('resizing');
                filePanelEl.style.transition = '';
                safeLocalStorageSet(storageKey, String(Math.round(filePanelEl.getBoundingClientRect().width)));
            }}

            fileSplitterEl.addEventListener('mousedown', (e) => {{ startDrag(e.clientX); e.preventDefault(); }});
            window.addEventListener('mousemove', (e) => moveDrag(e.clientX));
            window.addEventListener('mouseup', endDrag);
            fileSplitterEl.addEventListener('touchstart', (e) => {{
                if (e.touches.length === 1) {{ startDrag(e.touches[0].clientX); e.preventDefault(); }}
            }}, {{ passive: false }});
            window.addEventListener('touchmove', (e) => {{
                if (dragging && e.touches.length === 1) moveDrag(e.touches[0].clientX);
            }}, {{ passive: true }});
            window.addEventListener('touchend', endDrag);
        }}

        // ===== FILE EXPLORER — directory tree =====
        async function loadFileTree(path) {{
            path = path || '';
            fileCurrentPath = path;
            if (!fileTreeEl) return;
            fileTreeEl.innerHTML = '<div class="file-tree-status">' + (T.files_loading || 'Loading...') + '</div>';
            try {{
                const url = apiUrl('api/files/list') + (path ? '?path=' + encodeURIComponent(path) : '');
                const resp = await fetch(url, {{credentials:'same-origin'}});
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                if (data.error) throw new Error(data.error);
                renderFileTree(data.entries || [], path);
            }} catch(e) {{
                fileTreeEl.innerHTML = '<div class="file-tree-status">' + (T.files_error || 'Error') + ': ' + (e.message || '') + '</div>';
            }}
        }}

        function renderFileTree(entries, curPath) {{
            fileTreeEl.innerHTML = '';
            if (curPath) {{
                const parts = curPath.split('/').filter(Boolean);
                const back = document.createElement('div');
                back.className = 'file-tree-breadcrumb';
                back.innerHTML = '\u2190 ' + parts.join(' / ');
                back.title = 'Back to parent';
                back.onclick = () => loadFileTree(parts.slice(0, -1).join('/'));
                fileTreeEl.appendChild(back);
            }}
            if (!entries.length) {{
                const em = document.createElement('div');
                em.className = 'file-tree-status';
                em.textContent = T.files_empty || 'Empty';
                fileTreeEl.appendChild(em);
                return;
            }}
            const dirs  = entries.filter(e => e.type === 'directory');
            const files = entries.filter(e => e.type === 'file');
            // The currently visible tab path (for selected highlight)
            const activeTabPath = fileActiveTabIdx >= 0 && fileOpenTabs[fileActiveTabIdx]
                ? fileOpenTabs[fileActiveTabIdx].path : null;
            [...dirs, ...files].forEach(entry => {{
                const item = document.createElement('div');
                item.className = 'file-tree-item';
                if (!entry.type || entry.type === 'file') {{
                    if (entry.path === activeTabPath) {{
                        item.classList.add('file-selected'); // currently shown in panel
                    }} else if (fileOpenTabs.some(t => t.path === entry.path)) {{
                        item.classList.add('file-active'); // open in background tab
                    }}
                }}
                const icon = document.createElement('span');
                icon.className = 'file-icon';
                icon.textContent = entry.type === 'directory' ? '\U0001f4c1' : getFileIcon(entry.name);
                const name = document.createElement('span');
                name.className = 'file-name';
                name.textContent = entry.name;
                item.appendChild(icon);
                item.appendChild(name);
                if (entry.type !== 'directory' && entry.size !== undefined) {{
                    const sz = document.createElement('span');
                    sz.className = 'file-size';
                    sz.textContent = formatFileSize(entry.size);
                    item.appendChild(sz);
                }}
                item.onclick = () => entry.type === 'directory'
                    ? loadFileTree(entry.path)
                    : openFileInPanel(entry.path, entry.name);
                fileTreeEl.appendChild(item);
            }});
        }}

        function getFileIcon(name) {{
            if (!name) return '\U0001f4c4';
            const ext = name.split('.').pop().toLowerCase();
            if (ext === 'yaml' || ext === 'yml') return '\U0001f4c4';
            if (ext === 'json') return '\U0001f4cb';
            if (ext === 'py')   return '\U0001f40d';
            if (ext === 'sh')   return '\u26a1';
            if (ext === 'txt' || ext === 'md') return '\U0001f4dd';
            return '\U0001f4c4';
        }}

        function formatFileSize(bytes) {{
            if (!bytes) return '';
            if (bytes < 1024) return bytes + 'B';
            if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + 'KB';
            return (bytes / (1024 * 1024)).toFixed(1) + 'MB';
        }}

        // ===== FILE PANEL — open / close / tabs =====
        const FILE_CHUNK = 40000; // chars per page (matches server default)

        async function openFileInPanel(path, name) {{
            if (window.matchMedia('(max-width: 599px)').matches) return; // mobile: skip
            const existing = fileOpenTabs.findIndex(t => t.path === path);
            if (existing !== -1) {{ setActivePanelTab(existing); openFilePanel(); return; }}
            if (fileOpenTabs.length >= 3) {{
                fileOpenTabs.shift();
                if (fileActiveTabIdx > 0) fileActiveTabIdx--;
            }}
            fileOpenTabs.push({{ path, name, content: null, loading: true, offset: 0, hasMore: false, size: 0 }});
            const newIdx = fileOpenTabs.length - 1;
            setActivePanelTab(newIdx);
            openFilePanel();
            renderPanelTabs();
            filePanelContentEl.innerHTML = '<div class="file-panel-loading">Loading...</div>';
            try {{
                const url = apiUrl('api/files/read') + '?file=' + encodeURIComponent(path) + '&chunk=' + FILE_CHUNK;
                const resp = await fetch(url, {{credentials:'same-origin'}});
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                if (data.error) throw new Error(data.error);
                fileOpenTabs[newIdx].content  = data.content;
                fileOpenTabs[newIdx].offset   = data.chunk_size || data.content.length;
                fileOpenTabs[newIdx].hasMore  = data.has_more || false;
                fileOpenTabs[newIdx].size     = data.size || 0;
                fileOpenTabs[newIdx].loading  = false;
            }} catch(e) {{
                fileOpenTabs[newIdx].error   = e.message || 'Error';
                fileOpenTabs[newIdx].loading = false;
            }}
            renderPanelTabs();
            renderActivePanelContent();
            updateFileContextBar();
            if (fileTreeEl.children.length > 0) loadFileTree(fileCurrentPath);
        }}

        async function loadMoreFileContent(idx) {{
            const tab = fileOpenTabs[idx];
            if (!tab || !tab.hasMore) return;
            const loadMoreBtn = filePanelContentEl.querySelector('.file-load-more');
            if (loadMoreBtn) {{ loadMoreBtn.disabled = true; loadMoreBtn.textContent = 'Loading...'; }}
            try {{
                const url = apiUrl('api/files/read') + '?file=' + encodeURIComponent(tab.path)
                          + '&chunk=' + FILE_CHUNK + '&offset=' + tab.offset;
                const resp = await fetch(url, {{credentials:'same-origin'}});
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                if (data.error) throw new Error(data.error);
                tab.content  += data.content;
                tab.offset   += data.chunk_size || data.content.length;
                tab.hasMore   = data.has_more || false;
            }} catch(e) {{
                if (loadMoreBtn) {{ loadMoreBtn.disabled = false; loadMoreBtn.textContent = '⬇ Load more'; }}
                return;
            }}
            renderActivePanelContent();
            // Scroll to where new content starts (approx)
            if (filePanelContentEl) {{
                const viewer = filePanelContentEl.querySelector('.yaml-viewer');
                if (viewer) {{
                    const newBtn = filePanelContentEl.querySelector('.file-load-more');
                    if (newBtn) newBtn.scrollIntoView({{behavior:'smooth', block:'center'}});
                }}
            }}
        }}

        function openFilePanel() {{
            if (!filePanelEl || !fileSplitterEl) return;
            filePanelEl.classList.add('open');
            fileSplitterEl.classList.add('visible');
            const saved = parseInt(safeLocalStorageGet('chatFilePanelWidth') || '', 10);
            if (!Number.isNaN(saved) && saved >= 180) filePanelEl.style.width = saved + 'px';
        }}

        function closeFilePanel() {{
            if (!filePanelEl || !fileSplitterEl) return;
            fileOpenTabs = []; fileActiveTabIdx = -1;
            filePanelEl.classList.remove('open');
            fileSplitterEl.classList.remove('visible');
            filePanelEl.style.width = '0';
            if (filePanelTabsEl)   filePanelTabsEl.innerHTML = '';
            if (filePanelContentEl) filePanelContentEl.innerHTML = '';
            updateFileContextBar();
            if (fileTreeEl.children.length > 0) loadFileTree(fileCurrentPath);
        }}

        function closeFilePanelTab(idx) {{
            fileOpenTabs.splice(idx, 1);
            if (fileOpenTabs.length === 0) {{ closeFilePanel(); return; }}
            if (fileActiveTabIdx >= fileOpenTabs.length) fileActiveTabIdx = fileOpenTabs.length - 1;
            renderPanelTabs();
            renderActivePanelContent();
            updateFileContextBar();
        }}

        function setActivePanelTab(idx) {{
            fileActiveTabIdx = idx;
            renderPanelTabs();
            renderActivePanelContent();
        }}

        function renderPanelTabs() {{
            if (!filePanelTabsEl) return;
            filePanelTabsEl.innerHTML = '';
            fileOpenTabs.forEach((tab, idx) => {{
                const tabEl = document.createElement('button');
                tabEl.className = 'file-panel-tab' + (idx === fileActiveTabIdx ? ' active' : '');
                const nm = document.createElement('span'); nm.className = 'tab-name'; nm.textContent = tab.name; nm.title = tab.path;
                const cl = document.createElement('span'); cl.className = 'tab-close'; cl.textContent = '\u00d7'; cl.title = 'Close';
                cl.onclick = (e) => {{ e.stopPropagation(); closeFilePanelTab(idx); }};
                tabEl.appendChild(nm); tabEl.appendChild(cl);
                tabEl.onclick = () => setActivePanelTab(idx);
                filePanelTabsEl.appendChild(tabEl);
            }});
        }}

        function renderActivePanelContent() {{
            if (!filePanelContentEl) return;
            if (fileActiveTabIdx < 0 || fileActiveTabIdx >= fileOpenTabs.length) {{
                filePanelContentEl.innerHTML = ''; return;
            }}
            const tab = fileOpenTabs[fileActiveTabIdx];
            if (tab.loading) {{ filePanelContentEl.innerHTML = '<div class="file-panel-loading">Loading...</div>'; return; }}
            if (tab.error)   {{ filePanelContentEl.innerHTML = '<div class="file-panel-error">Error: ' + tab.error + '</div>'; return; }}
            filePanelContentEl.innerHTML = '';
            const viewer = document.createElement('div');
            viewer.className = 'yaml-viewer';
            viewer.innerHTML = syntaxHighlightYaml(tab.content || '');
            filePanelContentEl.appendChild(viewer);
            if (tab.hasMore) {{
                const loaded = tab.offset || 0;
                const total  = tab.size || 0;
                const pct    = total > 0 ? Math.round(loaded / total * 100) : '';
                const btn = document.createElement('button');
                btn.className = 'file-load-more';
                btn.textContent = '\u2b07 Load more' + (pct ? ' (' + pct + '% loaded)' : '');
                btn.onclick = () => loadMoreFileContent(fileActiveTabIdx);
                filePanelContentEl.appendChild(btn);
            }}
        }}

        // ===== YAML SYNTAX HIGHLIGHT (lightweight, line-by-line) =====
        function syntaxHighlightYaml(text) {{
            if (!text) return '';
            return text.split('\\n').map(line => {{
                const esc = line.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
                if (/^\\s*#/.test(line)) return '<span class="yaml-comment">' + esc + '</span>';
                const m = esc.match(/^(\\s*)([^#:][^:]*)(:\\s*)(.*)$/);
                if (m) {{
                    const [, indent, key, colon, val] = m;
                    let v = val;
                    if (/^(true|false|yes|no|on|off)$/i.test(val.trim())) v = '<span class="yaml-bool">' + val + '</span>';
                    else if (/^-?[0-9]+(\\.[0-9]+)?$/.test(val.trim())) v = '<span class="yaml-number">' + val + '</span>';
                    else if (val.trim()) v = '<span class="yaml-string">' + val + '</span>';
                    return indent + '<span class="yaml-key">' + key + '</span>' + colon + v;
                }}
                return esc;
            }}).join('\\n');
        }}

        // ===== FILE CONTEXT BAR =====
        function updateFileContextBar() {{
            if (!fileContextBarEl || !fileContextChipsEl) return;
            if (fileOpenTabs.length === 0) {{
                fileContextBarEl.classList.remove('visible');
                fileContextChipsEl.innerHTML = '';
                return;
            }}
            fileContextBarEl.classList.add('visible');
            fileContextChipsEl.innerHTML = fileOpenTabs
                .map(t => '<span class="file-context-chip">\U0001f4c4 ' + t.name + '</span>')
                .join('');
        }}

        // ===== BUILD FILE CONTEXT STRING for sendMessage =====
        function buildFileContext() {{
            if (fileOpenTabs.length === 0) return '';
            const MAX = 3000;
            return fileOpenTabs
                .filter(t => t.content)
                .map(t => {{
                    const c = t.content.length > MAX ? t.content.slice(0, MAX) + '\\n... [TRUNCATED]' : t.content;
                    return '[FILE: ' + t.path + ']\\n' + c + '\\n[/FILE]';
                }})
                .join('\\n\\n');
        }}

        // ===== CONFIG EDITOR =====
        const CONFIG_FILES = [
            {{ file: 'amira/agents.json', icon: '\U0001f916', title: T.config_agents_title || 'Agent Profiles', desc: 'agents.json', formBased: 'agents' }},
            {{ file: 'amira/mcp_config.json', icon: '\U0001f50c', title: T.config_mcp_title || 'MCP Configuration', desc: 'mcp_config.json', formBased: 'mcp' }},
            {{ file: 'amira/custom_system_prompt.txt', icon: '\U0001f4dd', title: T.config_prompt_title || 'Custom System Prompt', desc: 'custom_system_prompt.txt', formBased: 'prompt' }},
            {{ file: 'amira/memory/MEMORY.md', icon: '\U0001f9e0', title: T.config_memory_title || 'Memory (MEMORY.md)', desc: 'memory/MEMORY.md', formBased: 'memory' }},
            {{ file: 'amira/fallback_config.json', icon: '\U0001f504', title: T.config_llm_title || 'LLM Priority', desc: 'fallback_config.json', formBased: 'llm_priority' }},
            {{ file: 'amira_models_cache.json', icon: '\U0001f5c3\ufe0f', title: T.config_model_cache_title || 'Model Cache', desc: '/data/amira_models_cache.json', formBased: 'model_cache' }},
            {{ file: 'amira/settings.json', icon: '\u2699\ufe0f', title: T.config_settings_title || 'Settings', desc: 'settings.json', formBased: 'settings' }},
            {{ file: 'amira/uninstall_cleanup', icon: '\U0001f9f9', title: 'Uninstall Cleanup', desc: 'remove persisted Amira data', formBased: 'uninstall_cleanup' }},
        ];
        let configActiveFile = null;
        let configOriginalContent = '';

        // Known tools with i18n descriptions for the agent form multi-select
        const KNOWN_TOOLS = {_tool_descs_json};
        const AGENT_EMOJIS = ['\U0001f916', '\U0001f3e0', '\U0001f4bb', '\U0001f9e0', '\U0001f525', '\U0001f4a1', '\U0001f527', '\U0001f6e0\ufe0f', '\U0001f30d', '\U0001f3af', '\u2699\ufe0f', '\U0001f4ca', '\U0001f4dd', '\U0001f50d', '\U0001f680', '\U0001f6a8'];
        const THINKING_LEVELS = ['off', 'low', 'medium', 'high', 'adaptive'];

        // Cached providers/models data from loadModels
        let _cachedProviders = [];
        let _cachedModels = {{}};

        function loadConfigList() {{
            const listEl = document.getElementById('configList');
            if (!listEl) return;
            listEl.innerHTML = '';
            CONFIG_FILES.forEach(cf => {{
                const item = document.createElement('div');
                item.className = 'config-item' + (configActiveFile === cf.file ? ' active' : '');
                item.innerHTML = '<span class="config-item-icon">' + cf.icon + '</span>'
                    + '<div class="config-item-info"><div class="config-item-title">' + cf.title + '</div>'
                    + '<div class="config-item-desc">' + cf.desc + '</div></div>';
                item.addEventListener('click', () => openConfigEditor(cf));
                listEl.appendChild(item);
            }});
        }}

        async function openConfigEditor(cf) {{
            configActiveFile = cf.file;
            loadConfigList();

            // Open the file panel
            if (filePanelEl) filePanelEl.classList.add('open');
            if (fileSplitterEl) fileSplitterEl.classList.add('visible');
            const saved = parseInt(safeLocalStorageGet('chatFilePanelWidth') || '', 10);
            if (filePanelEl && !Number.isNaN(saved) && saved >= 180) filePanelEl.style.width = saved + 'px';

            if (filePanelTabsEl) filePanelTabsEl.innerHTML = '<span style="padding:6px 10px;font-size:12px;font-weight:600;color:#667eea;">' + cf.icon + ' ' + cf.title + '</span>';
            if (filePanelContentEl) filePanelContentEl.innerHTML = '<div style="padding:20px;color:#999;">' + (T.config_loading || 'Loading...') + '</div>';

            fileOpenTabs = [];
            fileActiveTabIdx = -1;
            updateFileContextBar();

            // Form-based editors per type
            if (cf.formBased === 'agents') {{
                await openAgentFormUI();
                return;
            }}
            if (cf.formBased === 'mcp') {{
                await openMcpFormUI();
                return;
            }}
            if (cf.formBased === 'prompt') {{
                await openEnhancedTextEditor(cf, 'prompt');
                return;
            }}
            if (cf.formBased === 'memory') {{
                await openEnhancedTextEditor(cf, 'memory');
                return;
            }}
            if (cf.formBased === 'llm_priority') {{
                await openLlmPriorityUI();
                return;
            }}
            if (cf.formBased === 'settings') {{
                await openSettingsUI();
                return;
            }}
            if (cf.formBased === 'model_cache') {{
                await openModelCacheUI();
                return;
            }}
            if (cf.formBased === 'uninstall_cleanup') {{
                await openUninstallCleanupUI();
                return;
            }}

            // Other config files: textarea editor
            try {{
                const resp = await fetch(apiUrl('api/config/read') + '?file=' + encodeURIComponent(cf.file), {{credentials:'same-origin'}});
                const data = await resp.json();
                if (!data.success) throw new Error(data.error || 'Read failed');

                configOriginalContent = data.content || '';
                const exists = data.exists !== false;

                if (!filePanelContentEl) return;
                filePanelContentEl.innerHTML = '';

                const editor = document.createElement('div');
                editor.className = 'config-editor';

                const header = document.createElement('div');
                header.className = 'config-editor-header';
                header.innerHTML = '<span class="config-editor-title">' + cf.icon + ' ' + cf.title + '</span><span id="configStatus" class="config-status"></span>';

                const body = document.createElement('div');
                body.className = 'config-editor-body';
                const ta = document.createElement('textarea');
                ta.id = 'configTextarea';
                ta.value = configOriginalContent;
                ta.spellcheck = false;
                if (!exists) {{
                    if (cf.file.endsWith('.json')) {{
                        ta.placeholder = '{{}}\\n\\n' + (T.config_file_not_found || 'File not found (will be created on save)');
                    }} else {{
                        ta.placeholder = T.config_file_not_found || 'File not found (will be created on save)';
                    }}
                }}
                ta.addEventListener('keydown', function(e) {{
                    if (e.key === 'Tab') {{
                        e.preventDefault();
                        const start = this.selectionStart;
                        const end = this.selectionEnd;
                        this.value = this.value.substring(0, start) + '  ' + this.value.substring(end);
                        this.selectionStart = this.selectionEnd = start + 2;
                    }}
                }});
                body.appendChild(ta);

                const footer = document.createElement('div');
                footer.className = 'config-editor-footer';
                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'config-cancel-btn';
                cancelBtn.textContent = T.config_cancel || 'Cancel';
                cancelBtn.addEventListener('click', () => {{
                    ta.value = configOriginalContent;
                    setConfigStatus('', '');
                }});
                const saveBtn = document.createElement('button');
                saveBtn.className = 'config-save-btn';
                saveBtn.textContent = T.config_save || 'Save';
                saveBtn.addEventListener('click', () => saveConfigFile(cf.file, ta.value));
                footer.appendChild(cancelBtn);
                footer.appendChild(saveBtn);

                editor.appendChild(header);
                editor.appendChild(body);
                editor.appendChild(footer);
                filePanelContentEl.appendChild(editor);
            }} catch(e) {{
                if (filePanelContentEl) filePanelContentEl.innerHTML = '<div style="padding:20px;color:#ef4444;">Error: ' + (e.message || '') + '</div>';
            }}
        }}

        // ===== AGENT FORM-BASED UI =====
        let _agentEditId = null;

        async function _fetchProviderModels() {{
            if (_cachedProviders.length > 0) return;
            try {{
                const resp = await fetch(apiUrl('api/get_models'), {{credentials:'same-origin'}});
                const data = await resp.json();
                if (data && data.available_providers) {{
                    _cachedProviders = data.available_providers;
                    _cachedModels = {{}};
                    const techModels = data.models_technical || data.models || {{}};
                    data.available_providers.forEach(p => {{
                        _cachedModels[p.id] = techModels[p.id] || [];
                    }});
                }}
            }} catch(e) {{ console.warn('Failed to fetch providers/models', e); }}
        }}

        async function openAgentFormUI() {{
            if (!filePanelContentEl) return;
            filePanelContentEl.innerHTML = '<div style="padding:20px;color:#999;">' + (T.config_loading || 'Loading...') + '</div>';

            // Fetch agents + providers + channel assignments in parallel
            await _fetchProviderModels();
            let agents = [];
            let activeAgentId = null;
            let channelAgents = {{}};  // channel -> agent_id
            try {{
                const [agentResp, chResp] = await Promise.all([
                    fetch(apiUrl('api/agents') + '?include_disabled=true', {{credentials:'same-origin'}}),
                    fetch(apiUrl('api/agents/channels'), {{credentials:'same-origin'}})
                ]);
                const data = await agentResp.json();
                if (data.success) {{
                    agents = data.agents || [];
                    activeAgentId = data.active_agent;
                }}
                const chData = await chResp.json();
                if (chData.success) {{
                    const ca = chData.channel_agents || {{}};
                    Object.keys(ca).forEach(ch => {{ channelAgents[ch] = ca[ch].agent_id || ca[ch]; }});
                }}
            }} catch(e) {{ console.warn('Failed to fetch agents/channels', e); }}
            // Store channel mapping for the form
            window._channelAgents = channelAgents;

            filePanelContentEl.innerHTML = '';
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;flex-direction:column;height:100%;';

            // Header with add button
            const hdr = document.createElement('div');
            hdr.className = 'agent-list-header';
            hdr.innerHTML = '<h3>\U0001f916 ' + (T.config_agents_title || 'Agent Profiles') + '</h3>';
            const addBtn = document.createElement('button');
            addBtn.className = 'agent-add-btn';
            addBtn.textContent = '+ ' + (T.agent_add || 'Nuovo Agent');
            addBtn.addEventListener('click', () => showAgentForm(null, wrap));
            hdr.appendChild(addBtn);
            wrap.appendChild(hdr);

            // Agent cards
            const listWrap = document.createElement('div');
            listWrap.style.cssText = 'flex:1;overflow-y:auto;';
            listWrap.id = 'agentCardList';

            if (agents.length === 0) {{
                listWrap.innerHTML = '<div style="padding:20px;text-align:center;color:#999;">'
                    + (T.agent_none || 'Nessun agent configurato. Clicca "Nuovo Agent" per iniziare.')
                    + '</div>';
            }} else {{
                agents.forEach(a => {{
                    const isProtected = (a.id === 'amira');
                    const card = document.createElement('div');
                    card.className = 'agent-card' + (a.id === activeAgentId ? ' active' : '') + (isProtected ? ' protected' : '');
                    const model = typeof a.model === 'string' ? a.model : (a.model && a.model.primary ? a.model.primary : '');
                    const badges = [];
                    if (isProtected) badges.push('<span class="agent-protected-badge">\U0001f512 ' + (T.agent_protected || 'Protected') + '</span>');
                    if (a.is_default) badges.push('<span class="agent-badge default">default</span>');
                    if (a.thinking_level) badges.push('<span class="agent-badge">' + a.thinking_level + '</span>');
                    // Channel badges
                    Object.keys(channelAgents).forEach(ch => {{
                        if (channelAgents[ch] === a.id) {{
                            const icon = ch === 'telegram' ? '\U0001f4e9' : ch === 'whatsapp' ? '\U0001f4f1' : ch === 'discord' ? '\U0001f579\ufe0f' : '\U0001f4ac';
                            badges.push('<span class="agent-badge channel">' + icon + ' ' + ch + '</span>');
                        }}
                    }});

                    card.innerHTML = '<span class="agent-card-emoji">' + (a.emoji || '\U0001f916') + '</span>'
                        + '<div class="agent-card-info">'
                        + '<div class="agent-card-name">' + (a.name || a.id) + '</div>'
                        + '<div class="agent-card-model">' + model + '</div>'
                        + (badges.length ? '<div class="agent-card-badges">' + badges.join('') + '</div>' : '')
                        + '</div>'
                        + (isProtected ? '' : '<div class="agent-card-actions">'
                        + '<button class="edit" title="Edit">\u270f\ufe0f</button>'
                        + '<button class="delete" title="Delete"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg></button>'
                        + '</div>');

                    if (!isProtected) {{
                        card.querySelector('.edit').addEventListener('click', (e) => {{
                            e.stopPropagation();
                            showAgentForm(a, wrap);
                        }});
                        card.querySelector('.delete').addEventListener('click', async (e) => {{
                            e.stopPropagation();
                            if (!confirm((T.agent_delete_confirm || 'Delete agent') + ' "' + (a.name || a.id) + '"?')) return;
                            try {{
                                const resp = await fetch(apiUrl('api/agents/' + encodeURIComponent(a.id)), {{
                                    method: 'DELETE', credentials: 'same-origin'
                                }});
                                const d = await resp.json();
                                if (!d.success) throw new Error(d.error || 'Delete failed');
                                openAgentFormUI();
                            }} catch(err) {{ console.error('[Agent Delete] ' + err.message); }}
                        }});
                        card.addEventListener('click', () => showAgentForm(a, wrap));
                    }}
                    listWrap.appendChild(card);
                }});
            }}
            wrap.appendChild(listWrap);
            filePanelContentEl.appendChild(wrap);
        }}

        function showAgentForm(agentData, parentWrap) {{
            // agentData is null for new agent, or the existing agent dict
            const isNew = !agentData;
            _agentEditId = isNew ? null : agentData.id;

            const formWrap = document.createElement('div');
            formWrap.style.cssText = 'display:flex;flex-direction:column;height:100%;';

            // Header
            const hdr = document.createElement('div');
            hdr.className = 'agent-list-header';
            hdr.innerHTML = '<h3>' + (isNew ? (T.agent_new || '\U0001f916 Nuovo Agent') : ('\u270f\ufe0f ' + (agentData.name || agentData.id))) + '</h3>';
            const backBtn = document.createElement('button');
            backBtn.className = 'config-cancel-btn';
            backBtn.textContent = '\u2190 ' + (T.agent_back || 'Indietro');
            backBtn.style.cssText = 'padding:4px 10px;font-size:11px;';
            backBtn.addEventListener('click', () => openAgentFormUI());
            hdr.appendChild(backBtn);
            formWrap.appendChild(hdr);

            // Form
            const form = document.createElement('div');
            form.className = 'agent-form';

            // Helper: label with tooltip
            function _lbl(text, tipKey) {{
                const tip = T[tipKey] || '';
                if (!tip) return text;
                return text + ' <span class="field-tip">i<span class="tip-text">' + _escHtml(tip) + '</span></span>';
            }}

            // ID (only for new)
            if (isNew) {{
                form.innerHTML += '<div class="agent-form-group"><label>' + _lbl(T.agent_id_label || 'ID (unique)', 'tip_agent_id') + '</label>'
                    + '<input type="text" id="af_id" placeholder="es. home, coder, energy..." '
                    + 'pattern="[a-z0-9_-]+" style="font-family:monospace;"></div>';
            }}

            // Name + Emoji row
            const nameRow = document.createElement('div');
            nameRow.className = 'agent-form-row';
            nameRow.innerHTML = '<div class="agent-form-group" style="flex:2;"><label>' + _lbl(T.agent_name || 'Name', 'tip_agent_name') + '</label>'
                + '<input type="text" id="af_name" value="' + _escAttr(agentData ? (agentData.name || '') : 'Amira') + '" placeholder="Amira"></div>'
                + '<div class="agent-form-group" style="flex:1;"><label>' + _lbl('Emoji', 'tip_agent_emoji') + '</label>'
                + '<div class="emoji-dropdown" id="af_emoji_picker">'
                + '<button type="button" class="emoji-dropdown-btn" id="af_emoji_btn">'
                + '<span id="af_emoji_val">\U0001f916</span><span class="edrop-arrow">▾</span>'
                + '</button>'
                + '<div class="emoji-dropdown-panel" id="af_emoji_panel"></div>'
                + '</div></div>';
            form.appendChild(nameRow);

            // Description
            form.innerHTML += '<div class="agent-form-group"><label>' + _lbl(T.agent_desc || 'Description', 'tip_agent_desc') + '</label>'
                + '<input type="text" id="af_desc" value="' + _escAttr(agentData ? (agentData.description || '') : '') + '" '
                + 'placeholder="Home automation expert..."></div>';

            // Provider + Model row
            const modelRow = document.createElement('div');
            modelRow.className = 'agent-form-row';
            modelRow.innerHTML = '<div class="agent-form-group"><label>' + _lbl('Provider', 'tip_agent_provider') + '</label>'
                + '<select id="af_provider"><option value="">-- auto --</option></select></div>'
                + '<div class="agent-form-group"><label>' + _lbl('Model', 'tip_agent_model') + '</label>'
                + '<select id="af_model"><option value="">-- default --</option></select></div>';
            form.appendChild(modelRow);

            // Fallback models (simple text input)
            form.innerHTML += '<div class="agent-form-group"><label>' + _lbl(T.agent_fallbacks || 'Fallback Models', 'tip_agent_fallbacks') + '</label>'
                + '<input type="text" id="af_fallbacks" value="' + _escAttr(agentData && agentData.fallbacks ? agentData.fallbacks.join(', ') : '') + '" '
                + 'placeholder="provider/model, provider/model, ..."></div>';

            // Temperature + Thinking row
            const behavRow = document.createElement('div');
            behavRow.className = 'agent-form-row';
            const tempVal = agentData && agentData.temperature != null ? agentData.temperature : '';
            behavRow.innerHTML = '<div class="agent-form-group"><label>' + _lbl(T.agent_temperature || 'Temperature (0-2)', 'tip_agent_temperature') + '</label>'
                + '<input type="number" id="af_temp" min="0" max="2" step="0.1" value="' + tempVal + '" placeholder="0.7"></div>'
                + '<div class="agent-form-group"><label>' + _lbl(T.agent_thinking || 'Thinking', 'tip_agent_thinking') + '</label>'
                + '<select id="af_thinking"><option value="">-- default --</option>'
                + THINKING_LEVELS.map(lv => '<option value="' + lv + '"' + (agentData && agentData.thinking_level === lv ? ' selected' : '') + '>' + lv + '</option>').join('')
                + '</select></div>';
            form.appendChild(behavRow);

            // Max tokens
            const maxTok = agentData && agentData.max_tokens != null ? agentData.max_tokens : '';
            form.innerHTML += '<div class="agent-form-group"><label>' + _lbl(T.agent_maxtokens || 'Max Tokens', 'tip_agent_maxtokens') + '</label>'
                + '<input type="number" id="af_maxtokens" min="256" max="200000" step="256" value="' + maxTok + '" placeholder="4096"></div>';

            // System prompt
            form.innerHTML += '<div class="agent-form-group"><label>' + _lbl(T.agent_sysprompt_label || 'System Prompt Override', 'tip_agent_sysprompt') + '</label>'
                + '<textarea id="af_sysprompt" rows="3" placeholder="' + _escAttr(T.agent_sysprompt_hint || 'Leave empty to use the default system prompt...') + '">'
                + _escHtml(agentData && (agentData.instructions || agentData.system_prompt) ? (agentData.instructions || agentData.system_prompt) : '') + '</textarea></div>';

            // Tools (multiselect chips)
            form.innerHTML += '<div class="agent-form-group"><label>' + _lbl(T.agent_tools || 'Allowed Tools', 'tip_agent_tools')
                + ' <span style="font-weight:normal;font-size:10px;color:#999;">(' + (T.agent_tools_hint || 'empty = all') + ')</span></label>'
                + '<div class="agent-tools-grid" id="af_tools"></div></div>';

            // Default + Enabled checkboxes
            const isDefault = agentData ? agentData.is_default : false;
            const isEnabled = agentData ? (agentData.enabled !== false) : true;
            form.innerHTML += '<div class="agent-form-row">'
                + '<div class="agent-form-group"><label style="display:flex;align-items:center;gap:6px;cursor:pointer;">'
                + '<input type="checkbox" id="af_default"' + (isDefault ? ' checked' : '') + '> ' + (T.agent_default_flag || 'Default')
                + '</label> <span class="field-tip">i<span class="tip-text">' + _escHtml(T.tip_agent_default || '') + '</span></span></div>'
                + '<div class="agent-form-group"><label style="display:flex;align-items:center;gap:6px;cursor:pointer;">'
                + '<input type="checkbox" id="af_enabled"' + (isEnabled ? ' checked' : '') + '> ' + (T.agent_enabled || 'Enabled')
                + '</label> <span class="field-tip">i<span class="tip-text">' + _escHtml(T.tip_agent_enabled || '') + '</span></span></div>'
                + '</div>';

            // Channel assignment (Telegram / WhatsApp)
            const chMap = window._channelAgents || {{}};
            const agentId = agentData ? agentData.id : null;
            const CHANNELS = ['telegram', 'whatsapp', 'discord'];
            let chHtml = '<div class="agent-form-group"><label>' + _lbl(T.agent_channels || 'Channel Assignment', 'tip_agent_channels') + '</label>'
                + '<div class="agent-form-row">';
            CHANNELS.forEach(ch => {{
                const isAssigned = agentId && chMap[ch] === agentId;
                const otherAgent = chMap[ch] && chMap[ch] !== agentId ? chMap[ch] : null;
                const label = ch === 'telegram'
                    ? (T.agent_channel_telegram || 'Telegram')
                    : ch === 'whatsapp'
                        ? (T.agent_channel_whatsapp || 'WhatsApp')
                        : (T.agent_channel_discord || 'Discord');
                const icon = ch === 'telegram' ? '\U0001f4e9' : ch === 'whatsapp' ? '\U0001f4f1' : '\U0001f579\ufe0f';
                const chDisabled = !!otherAgent;
                chHtml += '<div class="agent-form-group" style="flex:1;">'
                    + '<label style="display:flex;align-items:center;gap:6px;font-size:12px;'
                    + (chDisabled ? 'cursor:not-allowed;opacity:0.5;' : 'cursor:pointer;') + '">'
                    + '<input type="checkbox" class="af_channel" data-channel="' + ch + '"'
                    + (isAssigned ? ' checked' : '')
                    + (chDisabled ? ' disabled' : '') + '> '
                    + icon + ' ' + label + '</label>'
                    + (chDisabled
                        ? '<div style="font-size:10px;margin-top:2px;padding:2px 6px;border-radius:4px;'
                          + 'background:rgba(255,160,0,0.15);color:#e65100;display:inline-flex;align-items:center;gap:3px;">'
                          + '\U0001F512 ' + (T.agent_channel_taken || 'Used by') + ': <b>' + otherAgent + '</b></div>'
                        : '')
                    + '</div>';
            }});
            chHtml += '</div></div>';
            form.innerHTML += chHtml;

            // Action buttons
            form.innerHTML += '<div class="agent-form-actions">'
                + '<button class="config-cancel-btn" id="af_cancel">' + (T.config_cancel || 'Annulla') + '</button>'
                + '<button class="config-save-btn" id="af_save">' + (T.config_save || 'Salva') + '</button>'
                + '</div>';

            formWrap.appendChild(form);

            // Replace panel content
            filePanelContentEl.innerHTML = '';
            filePanelContentEl.appendChild(formWrap);

            // ---- Post-render: populate dynamic parts ----

            // Emoji picker
            // --- Emoji dropdown ---
            const currentEmoji = agentData ? (agentData.emoji || '\U0001f916') : '\U0001f916';
            const emojiValEl = document.getElementById('af_emoji_val');
            const emojiBtn   = document.getElementById('af_emoji_btn');
            const emojiPanel = document.getElementById('af_emoji_panel');
            if (emojiValEl) emojiValEl.textContent = currentEmoji;

            // Populate panel grid
            AGENT_EMOJIS.forEach(em => {{
                const btn = document.createElement('button');
                btn.className = 'emoji-btn' + (em === currentEmoji ? ' selected' : '');
                btn.textContent = em;
                btn.type = 'button';
                btn.addEventListener('click', () => {{
                    emojiPanel.querySelectorAll('.emoji-btn').forEach(b => b.classList.remove('selected'));
                    btn.classList.add('selected');
                    if (emojiValEl) emojiValEl.textContent = em;
                    emojiPanel.classList.remove('open');
                }});
                emojiPanel.appendChild(btn);
            }});

            // Toggle panel on button click
            if (emojiBtn) {{
                emojiBtn.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    emojiPanel.classList.toggle('open');
                }});
            }}
            // Close on outside click
            document.addEventListener('click', function _closeEmojiPanel(e) {{
                if (!e.target.closest('#af_emoji_picker')) {{
                    emojiPanel.classList.remove('open');
                    document.removeEventListener('click', _closeEmojiPanel);
                }}
            }});

            // Provider/Model dropdowns
            const provSel = document.getElementById('af_provider');
            const modSel = document.getElementById('af_model');
            let currentProv = '';
            let currentMod = '';
            if (agentData && agentData.model) {{
                const _mStr = typeof agentData.model === 'string' ? agentData.model : (agentData.model.primary || '');
                const parts = _mStr.split('/');
                if (parts.length >= 2) {{
                    currentProv = parts[0];
                    currentMod = parts.slice(1).join('/');
                }}
            }}
            _cachedProviders.forEach(p => {{
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name || p.id;
                if (p.id === currentProv) opt.selected = true;
                provSel.appendChild(opt);
            }});
            function _populateModels(prov) {{
                modSel.innerHTML = '<option value="">-- default --</option>';
                const models = _cachedModels[prov] || [];
                models.forEach(m => {{
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m;
                    if (m === currentMod) opt.selected = true;
                    modSel.appendChild(opt);
                }});
            }}
            if (currentProv) _populateModels(currentProv);
            provSel.addEventListener('change', () => {{ currentMod = ''; _populateModels(provSel.value); }});

            // Tools chips
            const toolsGrid = document.getElementById('af_tools');
            const selectedTools = new Set(agentData && Array.isArray(agentData.tools) ? agentData.tools : []);
            const hasToolFilter = agentData && Array.isArray(agentData.tools);
            Object.entries(KNOWN_TOOLS).forEach(([t, desc]) => {{
                const chip = document.createElement('span');
                chip.className = 'agent-tool-chip' + (hasToolFilter && selectedTools.has(t) ? ' selected' : '');
                chip.dataset.tool = t;
                chip.textContent = desc;
                chip.title = t;
                chip.addEventListener('click', () => chip.classList.toggle('selected'));
                toolsGrid.appendChild(chip);
            }});

            // Save handler
            document.getElementById('af_save').addEventListener('click', async () => {{
                const body = _buildAgentPayload(isNew);
                if (!body) return;
                try {{
                    let resp;
                    if (isNew) {{
                        resp = await fetch(apiUrl('api/agents'), {{
                            method: 'POST', headers: {{'Content-Type':'application/json'}},
                            credentials: 'same-origin', body: JSON.stringify(body)
                        }});
                    }} else {{
                        resp = await fetch(apiUrl('api/agents/' + encodeURIComponent(_agentEditId)), {{
                            method: 'PUT', headers: {{'Content-Type':'application/json'}},
                            credentials: 'same-origin', body: JSON.stringify(body)
                        }});
                    }}
                    const d = await resp.json();
                    if (!d.success) throw new Error(d.error || 'Save failed');

                    // Save channel assignments
                    const savedAgentId = isNew ? body.id : _agentEditId;
                    const channelUpdate = {{}};
                    const chMap = window._channelAgents || {{}};
                    document.querySelectorAll('.af_channel').forEach(cb => {{
                        const ch = cb.dataset.channel;
                        if (cb.checked) {{
                            channelUpdate[ch] = savedAgentId;
                        }} else if (chMap[ch] === savedAgentId) {{
                            // Was assigned to this agent, now unchecked → clear
                            channelUpdate[ch] = null;
                        }}
                    }});
                    if (Object.keys(channelUpdate).length > 0) {{
                        try {{
                            await fetch(apiUrl('api/agents/channels'), {{
                                method: 'PUT', headers: {{'Content-Type':'application/json'}},
                                credentials: 'same-origin', body: JSON.stringify(channelUpdate)
                            }});
                        }} catch(chErr) {{ console.warn('Channel save warning:', chErr); }}
                    }}

                    // Reload models to pick up agent changes
                    loadModels();
                    openAgentFormUI();
                }} catch(err) {{
                    const _saveErr = (T.config_save_error || 'Save error') + ': ' + err.message;
                    alert(_saveErr);
                    console.error('[Agent Save] ' + _saveErr);
                }}
            }});

            // Cancel handler
            document.getElementById('af_cancel').addEventListener('click', () => openAgentFormUI());
        }}

        function _buildAgentPayload(isNew) {{
            const payload = {{}};
            if (isNew) {{
                const rawId = ((document.getElementById('af_id') || {{}}).value || '').trim().toLowerCase();
                if (!rawId || !/^[a-z0-9_-]+$/.test(rawId)) {{
                    const _idErr = T.agent_id_invalid || 'ID must contain only lowercase letters, numbers, - and _';
                    alert(_idErr);
                    return null;
                }}
                payload.id = rawId;
            }}

            const name = (document.getElementById('af_name') || {{}}).value || '';
            const emojiValSpan = document.getElementById('af_emoji_val');
            const emoji = (emojiValSpan && emojiValSpan.textContent.trim()) || '\U0001f916';
            const desc = (document.getElementById('af_desc') || {{}}).value || '';

            payload.identity = {{ name: name.trim() || 'Agent', emoji: emoji, description: desc.trim() }};
            payload.name = name.trim() || 'Agent';

            // Model
            const prov = (document.getElementById('af_provider') || {{}}).value || '';
            const mod = (document.getElementById('af_model') || {{}}).value || '';
            if (prov && mod) {{
                payload.model = {{ primary: prov + '/' + mod }};
            }} else if (prov || mod) {{
                payload.model = {{ primary: (prov || 'anthropic') + '/' + (mod || 'claude-sonnet-4-6') }};
            }}

            // Fallbacks
            const fbText = (document.getElementById('af_fallbacks') || {{}}).value || '';
            if (fbText.trim()) {{
                const fbs = fbText.split(',').map(s => s.trim()).filter(Boolean);
                if (fbs.length) {{
                    payload.model = payload.model || {{}};
                    payload.model.fallbacks = fbs;
                }}
            }}

            // Temperature
            const tempVal = (document.getElementById('af_temp') || {{}}).value;
            if (tempVal !== '' && !isNaN(tempVal)) payload.temperature = parseFloat(tempVal);

            // Thinking
            const thinkVal = (document.getElementById('af_thinking') || {{}}).value;
            if (thinkVal) payload.thinking_level = thinkVal;

            // Max tokens
            const mtVal = (document.getElementById('af_maxtokens') || {{}}).value;
            if (mtVal !== '' && !isNaN(mtVal)) payload.max_tokens = parseInt(mtVal);

            // System prompt
            const sp = (document.getElementById('af_sysprompt') || {{}}).value || '';
            if (sp.trim()) payload.instructions = sp.trim();

            // Tools — only include if at least one chip selected
            const toolChips = document.querySelectorAll('#af_tools .agent-tool-chip.selected');
            if (toolChips.length > 0) {{
                payload.tools = Array.from(toolChips).map(c => c.dataset.tool);
            }}

            // Default + enabled
            payload.default = !!(document.getElementById('af_default') || {{}}).checked;
            payload.enabled = !!(document.getElementById('af_enabled') || {{}}).checked;

            return payload;
        }}

        function _escAttr(s) {{ return (s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;'); }}
        function _escHtml(s) {{ return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}
        function _tipSpan(tipKey) {{
            const tip = T[tipKey] || '';
            if (!tip) return '';
            return ' <span class="field-tip">i<span class="tip-text">' + _escHtml(tip) + '</span></span>';
        }}

        // ===== MCP FORM-BASED UI =====
        async function openMcpFormUI() {{
            if (!filePanelContentEl) return;
            filePanelContentEl.innerHTML = '<div style="padding:20px;color:#999;">' + (T.config_loading || 'Loading...') + '</div>';

            // Load current MCP settings (enable_mcp + mcp_config_file)
            let mcpEnabled = true;
            let mcpFilePath = '/config/amira/mcp_config.json';
            try {{
                const sResp = await fetch(apiUrl('api/settings'), {{credentials:'same-origin'}});
                const sData = await sResp.json();
                if (sData.success) {{
                    mcpEnabled = sData.settings.enable_mcp !== false;
                    mcpFilePath = sData.settings.mcp_config_file || mcpFilePath;
                }}
            }} catch(e) {{}}

            let mcpConfig = {{}};
            try {{
                const resp = await fetch(apiUrl('api/config/read') + '?file=amira/mcp_config.json', {{credentials:'same-origin'}});
                const data = await resp.json();
                if (data.success && data.content) {{
                    mcpConfig = JSON.parse(data.content);
                }}
            }} catch(e) {{ console.warn('Failed to load MCP config', e); }}

            const servers = mcpConfig.mcpServers || mcpConfig.mcpservers || {{}};
            let mcpRuntimeByName = {{}};

            async function _refreshMcpRuntime() {{
                try {{
                    const resp = await fetch(apiUrl('api/mcp/servers'), {{ credentials: 'same-origin' }});
                    const data = await resp.json();
                    if (data.status === 'success' && Array.isArray(data.servers)) {{
                        mcpRuntimeByName = {{}};
                        data.servers.forEach(s => {{
                            if (s && s.name) mcpRuntimeByName[s.name] = s;
                        }});
                    }}
                }} catch (e) {{
                    console.warn('Failed to load MCP runtime status', e);
                }}
            }}

            function _renderAllMcpCards() {{
                _renderMcpCards(listWrap, servers, mcpRuntimeByName, _refreshAndRenderMcpCards);
            }}

            async function _refreshAndRenderMcpCards() {{
                await _refreshMcpRuntime();
                _renderAllMcpCards();
            }}

            filePanelContentEl.innerHTML = '';
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;flex-direction:column;height:100%;';

            // Header
            const hdr = document.createElement('div');
            hdr.className = 'agent-list-header';
            hdr.innerHTML = '<h3>\U0001f50c ' + (T.config_mcp_title || 'MCP Configuration') + '</h3>';
            const addBtn = document.createElement('button');
            addBtn.className = 'agent-add-btn';
            addBtn.textContent = '+ ' + (T.mcp_add_server || 'Add Server');
            addBtn.addEventListener('click', () => {{
                const newName = prompt(T.mcp_server_name || 'Server Name', 'my_server');
                if (!newName || !newName.trim()) return;
                const name = newName.trim().replace(/[^a-zA-Z0-9_-]/g, '_');
                servers[name] = {{ command: '', args: [], env: {{}} }};
                _renderAllMcpCards();
                // auto expand the new one
                const lastCard = listWrap.querySelector('.mcp-server-card:last-child');
                if (lastCard) {{
                    lastCard.querySelector('.mcp-server-body').classList.add('open');
                    lastCard.querySelector('.mcp-server-toggle').classList.add('open');
                }}
            }});
            hdr.appendChild(addBtn);
            wrap.appendChild(hdr);

            // ── MCP Settings bar (enable toggle + config path) ──
            const mcpBar = document.createElement('div');
            mcpBar.className = 'mcp-settings-bar';
            mcpBar.style.cssText = 'padding:10px 14px;border-bottom:1px solid #eee;';
            // Toggle row
            const toggleRow = document.createElement('div');
            toggleRow.className = 'settings-row';
            const toggleLbl = document.createElement('label');
            toggleLbl.className = 'settings-label';
            toggleLbl.textContent = T.settings_enable_mcp || 'MCP Servers';
            toggleRow.appendChild(toggleLbl);
            const toggleSw = document.createElement('label');
            toggleSw.className = 'settings-toggle';
            const toggleInp = document.createElement('input');
            toggleInp.type = 'checkbox';
            toggleInp.checked = mcpEnabled;
            const toggleSl = document.createElement('span');
            toggleSl.className = 'settings-slider';
            toggleSw.appendChild(toggleInp);
            toggleSw.appendChild(toggleSl);
            toggleRow.appendChild(toggleSw);
            mcpBar.appendChild(toggleRow);
            const toggleDesc = document.createElement('div');
            toggleDesc.className = 'settings-desc';
            toggleDesc.textContent = T.settings_desc_enable_mcp || 'Enable MCP (Model Context Protocol) support.';
            mcpBar.appendChild(toggleDesc);
            // File path row
            const pathRow = document.createElement('div');
            pathRow.className = 'settings-row';
            pathRow.style.marginTop = '6px';
            const pathLbl = document.createElement('label');
            pathLbl.className = 'settings-label';
            pathLbl.textContent = T.mcp_config_path || 'Config File';
            pathRow.appendChild(pathLbl);
            const pathInp = document.createElement('input');
            pathInp.type = 'text';
            pathInp.className = 'settings-input';
            pathInp.value = mcpFilePath;
            pathInp.style.width = '260px';
            pathRow.appendChild(pathInp);
            mcpBar.appendChild(pathRow);
            const pathDesc = document.createElement('div');
            pathDesc.className = 'settings-desc';
            pathDesc.textContent = T.settings_desc_mcp_config_file || 'Path to MCP configuration JSON file';
            mcpBar.appendChild(pathDesc);
            // Dim server list when MCP off
            function _updateMcpDim() {{
                const on = toggleInp.checked;
                listWrap.style.opacity = on ? '1' : '0.45';
                listWrap.style.pointerEvents = on ? 'auto' : 'none';
                addBtn.style.opacity = on ? '1' : '0.45';
                addBtn.style.pointerEvents = on ? 'auto' : 'none';
            }}
            toggleInp.addEventListener('change', _updateMcpDim);
            wrap.appendChild(mcpBar);

            // ── Sezione installa pacchetti pip ──────────────────────────────
            const installSection = document.createElement('div');
            installSection.style.cssText = 'padding:10px 14px;border-bottom:1px solid #eee;';
            installSection.innerHTML =
                '<div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">📦 ' + (T.mcp_pip_section || 'Installa pacchetti pip') + '</div>'
                + '<div style="display:flex;gap:6px;align-items:flex-start;">'
                + '<textarea id="mcpPipInput" rows="2" style="flex:1;font-size:12px;padding:5px 8px;border:1px solid #ddd;border-radius:6px;resize:vertical;" placeholder="mcp-server-sqlite&#10;un-altro-pacchetto"></textarea>'
                + '<button id="mcpPipBtn" onclick="mcpInstallPkgs()" style="padding:5px 12px;font-size:12px;border:none;border-radius:6px;background:#4f6ef7;color:white;cursor:pointer;white-space:nowrap;">⬇ ' + (T.mcp_install_btn || 'Install') + '</button>'
                + '</div>'
                + '<pre id="mcpPipLog" style="display:none;margin-top:6px;padding:8px;background:#1a1a2a;color:#a0d8a0;font-size:11px;border-radius:6px;white-space:pre-wrap;max-height:140px;overflow-y:auto;"></pre>';
            wrap.appendChild(installSection);

            const listWrap = document.createElement('div');
            listWrap.style.cssText = 'flex:1;overflow-y:auto;padding:8px;';
            await _refreshMcpRuntime();
            _renderAllMcpCards();
            wrap.appendChild(listWrap);
            _updateMcpDim();

            // Footer with save
            const footer = document.createElement('div');
            footer.className = 'config-editor-footer';
            footer.innerHTML = '<span id="mcpStatus" class="config-status"></span>';
            const saveBtn = document.createElement('button');
            saveBtn.className = 'config-save-btn';
            saveBtn.textContent = T.config_save || 'Save';
            saveBtn.addEventListener('click', async () => {{
                const st = document.getElementById('mcpStatus');
                try {{
                    // 1. Save enable_mcp + mcp_config_file via settings API
                    const settResp = await fetch(apiUrl('api/settings'), {{
                        method: 'POST', headers: {{'Content-Type':'application/json'}},
                        credentials: 'same-origin',
                        body: JSON.stringify({{ enable_mcp: toggleInp.checked, mcp_config_file: pathInp.value }})
                    }});
                    const settData = await settResp.json();
                    if (!settData.success) throw new Error(settData.error || 'Settings save failed');
                    // 2. Save MCP servers JSON to config file
                    const result = _collectMcpData(listWrap);
                    const json = JSON.stringify({{ mcpServers: result }}, null, 2);
                    const resp = await fetch(apiUrl('api/config/save'), {{
                        method: 'POST', headers: {{'Content-Type':'application/json'}},
                        credentials: 'same-origin',
                        body: JSON.stringify({{ file: 'amira/mcp_config.json', content: json }})
                    }});
                    const d = await resp.json();
                    if (!d.success) throw new Error(d.error || 'Save failed');
                    if (st) {{ st.textContent = T.config_saved || 'Saved!'; st.className = 'config-status success'; }}
                    setTimeout(() => {{ if (st) {{ st.textContent = ''; st.className = 'config-status'; }} }}, 3000);
                    await _askRestartAddon(st);
                }} catch(err) {{
                    if (st) {{ st.textContent = (T.config_save_error || 'Error') + ': ' + err.message; st.className = 'config-status error'; }}
                }}
            }});
            footer.appendChild(saveBtn);
            wrap.appendChild(footer);

            filePanelContentEl.appendChild(wrap);
        }}

        function _renderMcpCards(container, servers, runtimeByName, onRuntimeChanged) {{
            container.innerHTML = '';
            const names = Object.keys(servers);
            if (names.length === 0) {{
                container.innerHTML = '<div style="padding:20px;text-align:center;color:#999;">'
                    + (T.mcp_no_servers || 'No MCP servers configured.') + '</div>';
                return;
            }}
            names.forEach(name => {{
                const srv = servers[name] || {{}};
                const rt = (runtimeByName && runtimeByName[name]) || {{}};
                const isRunning = rt.running === true || rt.connected === true || rt.state === 'running';
                const autostart = !!rt.autostart;
                const card = document.createElement('div');
                card.className = 'mcp-server-card';
                card.dataset.serverName = name;

                const header = document.createElement('div');
                header.className = 'mcp-server-header';
                header.innerHTML = '<span class="mcp-server-toggle">\u25b6</span>'
                    + '<span class="mcp-server-name">' + _escHtml(name) + '</span>'
                    + '<span class="mcp-server-status-badge">'
                    + '<span class="mcp-status-dot ' + (isRunning ? 'running' : 'stopped') + '"></span>'
                    + (isRunning ? 'attivo' : 'fermo')
                    + (autostart ? ' • auto' : '')
                    + '</span>'
                    + '<div class="mcp-server-actions">'
                    + '<button class="mcp-start" title="Avvia" style="font-size:13px;background:none;border:none;cursor:pointer;padding:2px 5px;">▶</button>'
                    + '<button class="mcp-stop" title="Ferma" style="font-size:13px;background:none;border:none;cursor:pointer;padding:2px 5px;">⏹</button>'
                    + '<button class="delete" title="Delete">\U0001f5d1\ufe0f</button></div>';
                const startBtn = header.querySelector('.mcp-start');
                const stopBtn = header.querySelector('.mcp-stop');
                startBtn.disabled = isRunning;
                stopBtn.disabled = !isRunning;

                startBtn.addEventListener('click', async (e) => {{
                    e.stopPropagation();
                    startBtn.disabled = true;
                    startBtn.textContent = '…';
                    try {{
                        const resp = await fetch(apiUrl('api/mcp/server/' + encodeURIComponent(name) + '/start'), {{
                            method: 'POST', credentials: 'same-origin'
                        }});
                        const data = await resp.json();
                        if (data.status !== 'success') throw new Error(data.message || 'errore');
                        if (typeof onRuntimeChanged === 'function') await onRuntimeChanged();
                    }} catch(err) {{
                        alert((T.mcp_start_failed || 'MCP start failed') + ' (' + name + '): ' + err.message);
                    }} finally {{
                        startBtn.textContent = '▶';
                    }}
                }});

                stopBtn.addEventListener('click', async (e) => {{
                    e.stopPropagation();
                    stopBtn.disabled = true;
                    stopBtn.textContent = '…';
                    try {{
                        const resp = await fetch(apiUrl('api/mcp/server/' + encodeURIComponent(name) + '/stop'), {{
                            method: 'POST', credentials: 'same-origin'
                        }});
                        const data = await resp.json();
                        if (data.status !== 'success') throw new Error(data.message || 'errore');
                        if (typeof onRuntimeChanged === 'function') await onRuntimeChanged();
                    }} catch(err) {{
                        alert((T.mcp_stop_failed || 'MCP stop failed') + ' (' + name + '): ' + err.message);
                    }} finally {{
                        stopBtn.textContent = '⏹';
                    }}
                }});

                header.querySelector('.delete').addEventListener('click', (e) => {{
                    e.stopPropagation();
                    delete servers[name];
                    _renderMcpCards(container, servers, runtimeByName, onRuntimeChanged);
                }});

                // Toggle body
                header.addEventListener('click', () => {{
                    const body = card.querySelector('.mcp-server-body');
                    const tog = card.querySelector('.mcp-server-toggle');
                    body.classList.toggle('open');
                    tog.classList.toggle('open');
                }});

                const body = document.createElement('div');
                body.className = 'mcp-server-body';

                body.innerHTML = '<div class="agent-form-group"><label>'
                    + (T.mcp_command || 'Command') + _tipSpan('tip_mcp_command')
                    + '</label><input type="text" class="mcp-cmd" value="'
                    + _escAttr(srv.command || '') + '" placeholder="python3, uvx, npx..."></div>'
                    + '<div class="agent-form-group"><label>'
                    + (T.mcp_args || 'Arguments') + _tipSpan('tip_mcp_args')
                    + '</label><textarea class="mcp-args" rows="2" placeholder="-m\\nmcp.server.stdio">'
                    + _escHtml((srv.args || []).join('\\n')) + '</textarea></div>'
                    + '<div class="agent-form-group"><label>'
                    + (T.mcp_env || 'Environment Variables') + _tipSpan('tip_mcp_env')
                    + '</label><textarea class="mcp-env" rows="2" placeholder="API_KEY=your_key_here">'
                    + _escHtml(Object.entries(srv.env || {{}}).map(([k,v]) => k + '=' + v).join('\\n'))
                    + '</textarea></div>';

                card.appendChild(header);
                card.appendChild(body);
                container.appendChild(card);
            }});
        }}

        function _collectMcpData(container) {{
            const result = {{}};
            container.querySelectorAll('.mcp-server-card').forEach(card => {{
                const name = card.dataset.serverName;
                const cmd = (card.querySelector('.mcp-cmd') || {{}}).value || '';
                const argsText = (card.querySelector('.mcp-args') || {{}}).value || '';
                const envText = (card.querySelector('.mcp-env') || {{}}).value || '';
                const args = argsText.split('\\n').map(s => s.trim()).filter(Boolean);
                const env = {{}};
                envText.split('\\n').forEach(line => {{
                    const idx = line.indexOf('=');
                    if (idx > 0) env[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
                }});
                const entry = {{ command: cmd.trim(), args: args, env: env }};
                result[name] = entry;
            }});
            return result;
        }}

        // ===== ENHANCED TEXT EDITOR (System Prompt / Memory) =====
        async function openEnhancedTextEditor(cf, editorType) {{
            if (!filePanelContentEl) return;
            filePanelContentEl.innerHTML = '<div style="padding:20px;color:#999;">' + (T.config_loading || 'Loading...') + '</div>';

            let content = '';
            let exists = true;
            try {{
                const resp = await fetch(apiUrl('api/config/read') + '?file=' + encodeURIComponent(cf.file), {{credentials:'same-origin'}});
                const data = await resp.json();
                if (data.success) {{ content = data.content || ''; exists = data.exists !== false; }}
            }} catch(e) {{ console.warn('Failed to load', cf.file, e); }}

            configOriginalContent = content;

            filePanelContentEl.innerHTML = '';
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;flex-direction:column;height:100%;';

            // Header
            const hdr = document.createElement('div');
            hdr.className = 'config-editor-header';
            hdr.innerHTML = '<span class="config-editor-title">' + cf.icon + ' ' + cf.title + '</span>'
                + '<span id="configStatus" class="config-status"></span>';
            wrap.appendChild(hdr);

            // Stats bar
            const statsBar = document.createElement('div');
            statsBar.className = 'enhanced-editor-stats';
            const charLabel = editorType === 'memory' ? (T.memory_lines || 'lines') : (T.prompt_chars || 'characters');
            statsBar.innerHTML = '<span id="editorStatCount">0</span> ' + charLabel;
            wrap.appendChild(statsBar);

            // Textarea
            const bodyDiv = document.createElement('div');
            bodyDiv.className = 'config-editor-body';
            const ta = document.createElement('textarea');
            ta.id = 'configTextarea';
            ta.value = content;
            ta.spellcheck = false;

            const placeholder = editorType === 'memory'
                ? (T.memory_hint || 'Markdown notes the AI will remember...')
                : (T.prompt_hint || 'Write custom instructions here...');
            if (!exists) ta.placeholder = (T.config_file_not_found || 'File not found') + '\\n\\n' + placeholder;
            else ta.placeholder = placeholder;

            function updateStats() {{
                const el = document.getElementById('editorStatCount');
                if (!el) return;
                if (editorType === 'memory') {{
                    el.textContent = (ta.value || '').split('\\n').length;
                }} else {{
                    el.textContent = (ta.value || '').length;
                }}
            }}
            ta.addEventListener('input', updateStats);
            ta.addEventListener('keydown', function(e) {{
                if (e.key === 'Tab') {{
                    e.preventDefault();
                    const start = this.selectionStart;
                    this.value = this.value.substring(0, start) + '  ' + this.value.substring(this.selectionEnd);
                    this.selectionStart = this.selectionEnd = start + 2;
                }}
            }});
            bodyDiv.appendChild(ta);
            wrap.appendChild(bodyDiv);

            // Footer
            const footer = document.createElement('div');
            footer.className = 'config-editor-footer';

            const clearBtn = document.createElement('button');
            clearBtn.className = 'config-cancel-btn';
            clearBtn.textContent = editorType === 'memory' ? (T.prompt_reset || 'Clear') : (T.prompt_reset || 'Clear');
            clearBtn.addEventListener('click', () => {{
                if (ta.value && !confirm((T.costs_reset_confirm || 'Are you sure?').split('?')[0] + '?')) return;
                ta.value = '';
                updateStats();
            }});

            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'config-cancel-btn';
            cancelBtn.textContent = T.config_cancel || 'Cancel';
            cancelBtn.addEventListener('click', () => {{
                ta.value = configOriginalContent;
                updateStats();
                setConfigStatus('', '');
            }});

            const saveBtn = document.createElement('button');
            saveBtn.className = 'config-save-btn';
            saveBtn.textContent = T.config_save || 'Save';
            saveBtn.addEventListener('click', () => saveConfigFile(cf.file, ta.value));

            footer.appendChild(clearBtn);
            footer.appendChild(cancelBtn);
            footer.appendChild(saveBtn);
            wrap.appendChild(footer);

            filePanelContentEl.appendChild(wrap);
            updateStats();
        }}

        // ── LLM Priority UI ──────────────────────────────────────────
        async function openLlmPriorityUI() {{
            if (!filePanelContentEl) return;
            filePanelContentEl.innerHTML = '<div style="padding:20px;color:#999;">' + (T.config_loading || 'Loading...') + '</div>';

            let fbData = {{ enabled: true, providers: [], provider_models: {{}} }};
            let modelsByProvider = {{}};
            const normalizeFallbackModels = (payload) => {{
                const out = {{}};
                if (!payload || typeof payload !== 'object') return out;

                const secTech = payload.models_sections_technical || {{}};
                const secDisp = payload.models_sections || {{}};
                const allTech = payload.models_technical || {{}};
                const allDisp = payload.models || {{}};

                const providers = new Set([
                    ...Object.keys(secTech || {{}}),
                    ...Object.keys(secDisp || {{}}),
                    ...Object.keys(allTech || {{}}),
                    ...Object.keys(allDisp || {{}}),
                ]);

                const toModelObjs = (arrTech, arrDisp) => {{
                    const techArr = Array.isArray(arrTech) ? arrTech : [];
                    const dispArr = Array.isArray(arrDisp) ? arrDisp : [];
                    const res = [];
                    for (let i = 0; i < techArr.length; i++) {{
                        const tech = String(techArr[i] || '').trim();
                        if (!tech) continue;
                        const name = String(dispArr[i] || tech).trim() || tech;
                        res.push({{ tech, name }});
                    }}
                    return res;
                }};

                providers.forEach((prov) => {{
                    const st = secTech && secTech[prov];
                    const sd = secDisp && secDisp[prov];
                    let fixed = [];
                    let dynamic = [];

                    // Preferred shape from /api/get_models:
                    // models_sections_technical[provider] = {{ fixed: [...], dynamic: [...] }}
                    if (st && typeof st === 'object' && (Array.isArray(st.fixed) || Array.isArray(st.dynamic))) {{
                        fixed = toModelObjs(st.fixed, (sd && sd.fixed) || []);
                        dynamic = toModelObjs(st.dynamic, (sd && sd.dynamic) || []);
                    }} else {{
                        // Backward-compatible fallback:
                        // models_technical[provider] + models[provider]
                        fixed = toModelObjs((allTech && allTech[prov]) || [], (allDisp && allDisp[prov]) || []);
                        dynamic = [];
                    }}

                    out[prov] = {{ fixed, dynamic }};
                }});

                return out;
            }};
            try {{
                const resp = await fetch(apiUrl('api/fallback_config'), {{credentials:'same-origin'}});
                const data = await resp.json();
                if (data.success) fbData = data;
            }} catch(e) {{ console.warn('Failed to load fallback config', e); }}
            try {{
                const resp = await fetch(apiUrl('api/get_models'), {{credentials:'same-origin'}});
                const data = await resp.json();
                modelsByProvider = normalizeFallbackModels(data);
            }} catch(e) {{ console.warn('Failed to load models for fallback UI', e); }}

            filePanelContentEl.innerHTML = '';
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;flex-direction:column;height:100%;';

            // Header
            const hdr = document.createElement('div');
            hdr.className = 'agent-list-header';
            hdr.innerHTML = '<h3>\U0001f504 ' + (T.config_llm_title || 'LLM Priority') + '</h3>';
            wrap.appendChild(hdr);

            const body = document.createElement('div');
            body.style.cssText = 'flex:1;overflow-y:auto;padding:12px 14px;';

            // Toggle row
            const toggleRow = document.createElement('div');
            toggleRow.className = 'llm-toggle-row';
            const toggleLabel = document.createElement('div');
            toggleLabel.className = 'llm-toggle-label';
            toggleLabel.textContent = T.llm_fallback_label || 'Auto Fallback';
            const toggleDesc = document.createElement('div');
            toggleDesc.className = 'llm-toggle-desc';
            toggleDesc.textContent = fbData.enabled
                ? (T.llm_fallback_on || 'ON \u2013 if primary fails, try next provider')
                : (T.llm_fallback_off || 'OFF \u2013 only the selected provider is used');
            const toggleSwitch = document.createElement('label');
            toggleSwitch.style.cssText = 'position:relative;display:inline-block;width:42px;height:24px;flex-shrink:0;';
            const toggleInput = document.createElement('input');
            toggleInput.type = 'checkbox';
            toggleInput.checked = fbData.enabled;
            toggleInput.style.cssText = 'opacity:0;width:0;height:0;';
            const slider = document.createElement('span');
            slider.style.cssText = 'position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:'
                + (fbData.enabled ? '#667eea' : '#ccc')
                + ';border-radius:24px;transition:.3s;';
            const knob = document.createElement('span');
            knob.style.cssText = 'position:absolute;content:"";height:18px;width:18px;left:'
                + (fbData.enabled ? '20px' : '3px')
                + ';bottom:3px;background:#fff;border-radius:50%;transition:.3s;';
            slider.appendChild(knob);
            toggleSwitch.appendChild(toggleInput);
            toggleSwitch.appendChild(slider);
            toggleInput.addEventListener('change', () => {{
                const on = toggleInput.checked;
                slider.style.background = on ? '#667eea' : '#ccc';
                knob.style.left = on ? '20px' : '3px';
                toggleDesc.textContent = on
                    ? (T.llm_fallback_on || 'ON \u2013 if primary fails, try next provider')
                    : (T.llm_fallback_off || 'OFF \u2013 only the selected provider is used');
                listEl.style.opacity = on ? '1' : '0.45';
                listEl.style.pointerEvents = on ? 'auto' : 'none';
            }});
            const toggleTop = document.createElement('div');
            toggleTop.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:10px;';
            toggleTop.appendChild(toggleLabel);
            toggleTop.appendChild(toggleSwitch);
            toggleRow.appendChild(toggleTop);
            toggleRow.appendChild(toggleDesc);
            body.appendChild(toggleRow);

            // Priority label
            const priLabel = document.createElement('div');
            priLabel.style.cssText = 'font-size:12px;font-weight:600;color:#888;margin:14px 0 6px;text-transform:uppercase;letter-spacing:.5px;';
            priLabel.textContent = T.llm_priority_label || 'Priority order';
            body.appendChild(priLabel);

            // Provider list
            const listEl = document.createElement('ul');
            listEl.className = 'llm-priority-list';
            listEl.style.opacity = fbData.enabled ? '1' : '0.45';
            listEl.style.pointerEvents = fbData.enabled ? 'auto' : 'none';

            let providers = fbData.providers || [];
            providers = providers.map(p => {{
                const selected = (fbData.provider_models && fbData.provider_models[p.id]) || p.model || '';
                return {{ ...p, model: selected }};
            }});

            function renderList() {{
                listEl.innerHTML = '';
                providers.forEach((p, i) => {{
                    const li = document.createElement('li');
                    li.className = 'llm-priority-item';
                    const num = document.createElement('span');
                    num.style.cssText = 'font-size:11px;color:#999;width:18px;text-align:center;flex-shrink:0;';
                    num.textContent = (i + 1) + '.';
                    const dot = document.createElement('span');
                    dot.className = 'llm-dot ' + (p.configured ? 'on' : 'off');
                    const name = document.createElement('span');
                    name.className = 'llm-name';
                    const provLabel = PROVIDER_LABELS[p.id] || p.label || p.id;
                    name.textContent = provLabel;
                    if (!p.configured) {{
                        const nokey = document.createElement('span');
                        nokey.className = 'llm-nokey';
                        nokey.textContent = ' (' + (T.llm_no_key || 'no key') + ')';
                        name.appendChild(nokey);
                    }}
                    const modelSel = document.createElement('select');
                    modelSel.className = 'settings-select';
                    modelSel.style.cssText = 'max-width:280px;min-width:180px;font-size:12px;padding:4px 8px;';
                    const modelDefaultOpt = document.createElement('option');
                    modelDefaultOpt.value = '';
                    modelDefaultOpt.textContent = (T.none || 'Default provider model');
                    modelSel.appendChild(modelDefaultOpt);
                    const fixed = (modelsByProvider[p.id] && Array.isArray(modelsByProvider[p.id].fixed)) ? modelsByProvider[p.id].fixed : [];
                    const dynamic = (modelsByProvider[p.id] && Array.isArray(modelsByProvider[p.id].dynamic)) ? modelsByProvider[p.id].dynamic : [];
                    const allModels = [...fixed, ...dynamic];
                    const seenModels = new Set();
                    allModels.forEach(m => {{
                        const tech = (typeof m === 'string') ? m : ((m && m.tech) || '');
                        const label = (typeof m === 'string') ? m : ((m && m.name) || tech);
                        if (!tech || seenModels.has(tech)) return;
                        seenModels.add(tech);
                        const opt = document.createElement('option');
                        opt.value = tech;
                        opt.textContent = label + ' (' + tech + ')';
                        modelSel.appendChild(opt);
                    }});
                    if (p.model && !seenModels.has(p.model)) {{
                        const opt = document.createElement('option');
                        opt.value = p.model;
                        opt.textContent = p.model + ' (' + (T.config_current || 'current') + ')';
                        modelSel.appendChild(opt);
                    }}
                    modelSel.value = p.model || '';
                    modelSel.addEventListener('change', () => {{
                        p.model = modelSel.value || '';
                    }});
                    const btnWrap = document.createElement('span');
                    btnWrap.style.cssText = 'display:flex;gap:2px;flex-shrink:0;';
                    const upBtn = document.createElement('button');
                    upBtn.className = 'llm-priority-btn';
                    upBtn.textContent = '\u25B2';
                    upBtn.disabled = (i === 0);
                    upBtn.addEventListener('click', () => {{
                        if (i === 0) return;
                        [providers[i - 1], providers[i]] = [providers[i], providers[i - 1]];
                        renderList();
                    }});
                    const downBtn = document.createElement('button');
                    downBtn.className = 'llm-priority-btn';
                    downBtn.textContent = '\u25BC';
                    downBtn.disabled = (i === providers.length - 1);
                    downBtn.addEventListener('click', () => {{
                        if (i >= providers.length - 1) return;
                        [providers[i], providers[i + 1]] = [providers[i + 1], providers[i]];
                        renderList();
                    }});
                    btnWrap.appendChild(upBtn);
                    btnWrap.appendChild(downBtn);
                    li.appendChild(num);
                    li.appendChild(dot);
                    li.appendChild(name);
                    li.appendChild(modelSel);
                    li.appendChild(btnWrap);
                    listEl.appendChild(li);
                }});
            }}
            renderList();
            body.appendChild(listEl);

            // Save button
            const saveRow = document.createElement('div');
            saveRow.style.cssText = 'margin-top:16px;display:flex;align-items:center;gap:10px;';
            const saveBtn = document.createElement('button');
            saveBtn.className = 'config-save-btn';
            saveBtn.style.cssText = 'padding:8px 22px;font-size:13px;';
            saveBtn.textContent = '\U0001f4be ' + (T.config_save || 'Save');
            const saveStatus = document.createElement('span');
            saveStatus.style.cssText = 'font-size:12px;color:#4caf50;';
            saveBtn.addEventListener('click', async () => {{
                saveBtn.disabled = true;
                saveBtn.textContent = '\u23F3 ...';
                try {{
                    const providerModels = {{}};
                    providers.forEach(p => {{
                        if (p.model) providerModels[p.id] = p.model;
                    }});
                    const payload = {{
                        enabled: toggleInput.checked,
                        priority: providers.map(p => p.id),
                        provider_models: providerModels,
                    }};
                    const resp = await fetch(apiUrl('api/fallback_config'), {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        credentials: 'same-origin',
                        body: JSON.stringify(payload)
                    }});
                    const data = await resp.json();
                    if (!data.success) throw new Error(data.error || 'Save failed');
                    saveStatus.textContent = '\u2705 ' + (T.llm_saved || 'Saved!');
                    setTimeout(() => {{ saveStatus.textContent = ''; }}, 3000);
                }} catch(e) {{
                    saveStatus.textContent = '\u274C ' + (e.message || 'Error');
                    saveStatus.style.color = '#f44336';
                    setTimeout(() => {{ saveStatus.textContent = ''; saveStatus.style.color = '#4caf50'; }}, 4000);
                }} finally {{
                    saveBtn.disabled = false;
                    saveBtn.textContent = '\U0001f4be ' + (T.config_save || 'Save');
                }}
            }});
            saveRow.appendChild(saveBtn);
            saveRow.appendChild(saveStatus);
            body.appendChild(saveRow);

            wrap.appendChild(body);
            filePanelContentEl.appendChild(wrap);
        }}

        async function openModelCacheUI() {{
            if (!filePanelContentEl) return;
            filePanelContentEl.innerHTML = '<div style="padding:20px;color:#999;">' + (T.settings_model_cache_loading || 'Loading model cache...') + '</div>';

            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;flex-direction:column;height:100%;';
            const hdr = document.createElement('div');
            hdr.className = 'agent-list-header';
            hdr.innerHTML = '<h3>\U0001f5c3\ufe0f ' + (T.settings_model_cache_title || 'Model Cache') + '</h3>';
            wrap.appendChild(hdr);

            const body = document.createElement('div');
            body.style.cssText = 'flex:1;overflow-y:auto;padding:0;';

            function _cacheMapToText(mp) {{
                const lines = [];
                const keys = Object.keys(mp || {{}}).sort();
                if (!keys.length) return (T.settings_model_cache_empty || 'No models');
                keys.forEach(k => {{
                    const arr = Array.isArray(mp[k]) ? mp[k] : [];
                    lines.push(`[${{k}}] (${{arr.length}})`);
                    arr.forEach(m => lines.push('  - ' + m));
                    lines.push('');
                }});
                return lines.join('\\n').trim() || (T.settings_model_cache_empty || 'No models');
            }}

            async function _render() {{
                body.innerHTML = '<div style="padding:8px 14px;color:#999;">' + (T.settings_model_cache_loading || 'Loading model cache...') + '</div>';
                try {{
                    const resp = await fetch(apiUrl('api/models/cache/status'), {{credentials:'same-origin'}});
                    const data = await resp.json().catch(() => ({{}}));
                    if (!resp.ok || !data || !data.success) throw new Error((data && (data.error || data.message)) || ('HTTP ' + resp.status));
                    const fmtUpdatedAt = (raw) => {{
                        try {{
                            const d = new Date(raw);
                            if (Number.isNaN(d.getTime())) return String(raw || '');
                            return d.toLocaleString([], {{ dateStyle: 'short', timeStyle: 'medium' }});
                        }} catch(_e) {{
                            return String(raw || '');
                        }}
                    }};

                    const toolbar = document.createElement('div');
                    toolbar.className = 'model-cache-toolbar';
                    const refreshBtn = document.createElement('button');
                    refreshBtn.className = 'config-save-btn';
                    refreshBtn.style.cssText = 'padding:6px 12px;font-size:12px;background:#1976d2;';
                    refreshBtn.textContent = '\U0001F504 ' + (T.settings_refresh_models_cache || 'Refresh Models Cache');
                    const clearBtn = document.createElement('button');
                    clearBtn.className = 'config-save-btn';
                    clearBtn.style.cssText = 'padding:6px 12px;font-size:12px;background:#d32f2f;';
                    clearBtn.textContent = '\U0001F5D1\uFE0F ' + (T.settings_clear_models_cache || 'Clear Models Cache');
                    const cacheStatus = document.createElement('span');
                    cacheStatus.className = 'model-cache-status';
                    const updated = data.updated_at ? (' — ' + (T.settings_model_cache_updated_at || 'Updated') + ': ' + fmtUpdatedAt(data.updated_at)) : '';
                    cacheStatus.textContent = updated || '';

                    refreshBtn.addEventListener('click', async () => {{
                        refreshBtn.disabled = true;
                        refreshBtn.textContent = '\u23F3 ...';
                        try {{
                            const r = await fetch(apiUrl('api/models/cache/refresh'), {{method:'POST', headers:{{'Content-Type':'application/json'}}, credentials:'same-origin'}});
                            const d = await r.json();
                            if (!d.success) throw new Error(d.error || 'Refresh failed');
                            cacheStatus.textContent = '\u2705 ' + (T.settings_refresh_models_cache_done || 'Models cache refreshed!');
                            try {{ _cachedProviders = []; _cachedModels = {{}}; }} catch(_e) {{}}
                            await _render();
                        }} catch(e) {{
                            cacheStatus.textContent = '\u274C ' + ((T.settings_refresh_models_cache_error || 'Failed to refresh models cache') + ': ' + (e.message || 'Error'));
                        }} finally {{
                            refreshBtn.disabled = false;
                            refreshBtn.textContent = '\U0001F504 ' + (T.settings_refresh_models_cache || 'Refresh Models Cache');
                        }}
                    }});

                    clearBtn.addEventListener('click', async () => {{
                        const msg = T.settings_clear_models_cache_confirm || 'Clear cached dynamic provider models now?';
                        if (!window.confirm(msg)) return;
                        clearBtn.disabled = true;
                        clearBtn.textContent = '\u23F3 ...';
                        try {{
                            const r = await fetch(apiUrl('api/models/cache/clear'), {{method:'POST', headers:{{'Content-Type':'application/json'}}, credentials:'same-origin'}});
                            const d = await r.json();
                            if (!d.success) throw new Error(d.error || 'Clear failed');
                            cacheStatus.textContent = '\u2705 ' + (T.settings_clear_models_cache_done || 'Models cache cleared!');
                            try {{ _cachedProviders = []; _cachedModels = {{}}; }} catch(_e) {{}}
                            await _render();
                        }} catch(e) {{
                            cacheStatus.textContent = '\u274C ' + ((T.settings_clear_models_cache_error || 'Failed to clear models cache') + ': ' + (e.message || 'Error'));
                        }} finally {{
                            clearBtn.disabled = false;
                            clearBtn.textContent = '\U0001F5D1\uFE0F ' + (T.settings_clear_models_cache || 'Clear Models Cache');
                        }}
                    }});

                    toolbar.appendChild(refreshBtn);
                    toolbar.appendChild(clearBtn);
                    toolbar.appendChild(cacheStatus);

                    const grid = document.createElement('div');
                    grid.className = 'model-cache-grid';
                    const mkBox = (title, text) => {{
                        const box = document.createElement('div');
                        box.className = 'model-cache-box';
                        const h = document.createElement('h5');
                        h.textContent = title;
                        const pre = document.createElement('pre');
                        pre.textContent = text || (T.settings_model_cache_empty || 'No models');
                        box.appendChild(h);
                        box.appendChild(pre);
                        return box;
                    }};
                    grid.appendChild(mkBox(T.settings_model_cache_fixed || 'Fixed Models', _cacheMapToText(data.fixed || {{}})));
                    grid.appendChild(mkBox(T.settings_model_cache_dynamic || 'Dynamic Models (cache)', _cacheMapToText(data.dynamic || {{}})));
                    grid.appendChild(mkBox(T.settings_model_cache_blocklist || 'Blocked Models', _cacheMapToText(data.blocklist || {{}})));
                    grid.appendChild(mkBox(T.settings_model_cache_uncertain || 'Uncertain Test Results', _cacheMapToText(data.uncertain || {{}})));
                    grid.appendChild(mkBox(T.settings_model_cache_nvidia_tested || 'NVIDIA Tested OK', (Array.isArray(data.nvidia_tested_ok) && data.nvidia_tested_ok.length) ? data.nvidia_tested_ok.map(m => '- ' + m).join('\\n') : (T.settings_model_cache_empty || 'No models')));

                    body.innerHTML = '';
                    body.appendChild(toolbar);
                    body.appendChild(grid);
                }} catch(e) {{
                    body.innerHTML = '<div style="padding:8px 14px;color:#f44336;">' + _escHtml(String(e && e.message ? e.message : e)) + '</div>';
                }}
            }}

            await _render();
            wrap.appendChild(body);
            filePanelContentEl.innerHTML = '';
            filePanelContentEl.appendChild(wrap);
        }}

        async function openUninstallCleanupUI() {{
            if (!filePanelContentEl) return;
            filePanelContentEl.innerHTML = '<div style="padding:20px;color:#999;">' + (T.config_loading || 'Loading...') + '</div>';

            filePanelContentEl.innerHTML = '';
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;flex-direction:column;height:100%;';

            const hdr = document.createElement('div');
            hdr.className = 'agent-list-header';
            hdr.innerHTML = '<h3>\U0001f9f9 Uninstall Cleanup</h3>';
            wrap.appendChild(hdr);

            const body = document.createElement('div');
            body.style.cssText = 'flex:1;overflow-y:auto;padding:14px;';

            const info = document.createElement('div');
            info.style.cssText = 'font-size:13px;line-height:1.6;color:#666;padding:12px;border:1px solid #e6e6e6;border-radius:10px;background:#fafafa;';
            info.innerHTML =
                '<b>Use this before uninstalling the addon.</b><br>' +
                'It removes Amira persisted data in <code>/config/amira</code> and cleans chat bubble resources/files.';
            body.appendChild(info);

            const dashRow = document.createElement('label');
            dashRow.style.cssText = 'display:flex;align-items:center;gap:8px;margin-top:12px;font-size:12px;color:#666;';
            const dashCheck = document.createElement('input');
            dashCheck.type = 'checkbox';
            dashCheck.checked = false;
            dashRow.appendChild(dashCheck);
            const dashTxt = document.createElement('span');
            dashTxt.textContent = 'Also remove /config/www/dashboards (generated dashboards)';
            dashRow.appendChild(dashTxt);
            body.appendChild(dashRow);

            const actionRow = document.createElement('div');
            actionRow.style.cssText = 'margin-top:14px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;';
            const runBtn = document.createElement('button');
            runBtn.className = 'config-save-btn';
            runBtn.style.cssText = 'background:#c62828;padding:8px 16px;font-size:13px;';
            runBtn.textContent = '🧹 Run Cleanup';
            const st = document.createElement('span');
            st.style.cssText = 'font-size:12px;color:#777;white-space:pre-wrap;';
            actionRow.appendChild(runBtn);
            actionRow.appendChild(st);
            body.appendChild(actionRow);

            runBtn.addEventListener('click', async () => {{
                const targets = [
                    '- Risorse Lovelace e file JS della chat bubble',
                    '- Tutta la cartella /config/amira (chat, conversazioni, impostazioni, agenti, snapshot, documenti, ecc.)',
                ];
                if (dashCheck.checked) {{
                    targets.push('- Cartella /config/www/dashboards (dashboard generate)');
                }}
                targets.push('');
                targets.push('This operation is irreversible.');
                targets.push('Continue?');
                const confirm1 = window.confirm('The following will be removed:\\n\\n' + targets.join('\\n'));
                if (!confirm1) return;
                const confirmText = window.prompt('Type DELETE to confirm pre-uninstall cleanup:');
                if ((confirmText || '').trim().toUpperCase() !== 'DELETE') {{
                    st.style.color = '#f44336';
                    st.textContent = 'Invalid confirmation. Cleanup canceled.';
                    return;
                }}

                runBtn.disabled = true;
                runBtn.textContent = '⏳ ...';
                st.style.color = '#777';
                st.textContent = 'Cleanup in progress...';

                try {{
                    const resp = await fetch(apiUrl('api/uninstall_cleanup'), {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        credentials: 'same-origin',
                        body: JSON.stringify({{ include_dashboards: !!dashCheck.checked }})
                    }});
                    const data = await resp.json().catch(() => ({{}}));
                    const removed = Array.isArray(data.removed) ? data.removed : [];
                    const errors = Array.isArray(data.errors) ? data.errors : [];
                    if (resp.ok && (!errors.length)) {{
                        st.style.color = '#2e7d32';
                        st.textContent = 'Cleanup completed. You can now uninstall the add-on safely.\\nRemoved: ' + (removed.join(', ') || 'n/a');
                    }} else {{
                        st.style.color = '#ef6c00';
                        st.textContent = 'Partial cleanup.\\nRemoved: ' + (removed.join(', ') || 'n/a') + '\\nErrors: ' + (errors.join(' | ') || 'n/a');
                    }}
                }} catch(e) {{
                    st.style.color = '#f44336';
                    st.textContent = 'Cleanup error: ' + (e.message || 'Unknown');
                }} finally {{
                    runBtn.disabled = false;
                    runBtn.textContent = '🧹 Run Cleanup';
                }}
            }});

            wrap.appendChild(body);
            filePanelContentEl.appendChild(wrap);
        }}

        async function openSettingsUI() {{
            if (!filePanelContentEl) return;
            filePanelContentEl.innerHTML = '<div style="padding:20px;color:#999;">' + (T.config_loading || 'Loading...') + '</div>';

            let settingsData = {{ settings: {{}}, sections: [] }};
            try {{
                const resp = await fetch(apiUrl('api/settings'), {{credentials:'same-origin'}});
                const data = await resp.json();
                if (data.success) settingsData = data;
            }} catch(e) {{ console.warn('Failed to load settings', e); }}

            filePanelContentEl.innerHTML = '';
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;flex-direction:column;height:100%;';

            // Header
            const hdr = document.createElement('div');
            hdr.className = 'agent-list-header';
            hdr.innerHTML = '<h3>\u2699\ufe0f ' + (T.config_settings_title || 'Settings') + '</h3>';
            wrap.appendChild(hdr);

            const body = document.createElement('div');
            body.style.cssText = 'flex:1;overflow-y:auto;padding:12px 14px;';

            const values = {{ ...settingsData.settings }};

            // i18n labels for setting keys
            const LABELS = {{
                language: T.settings_language || 'Language',
                enable_memory: T.settings_enable_memory || 'Memory',
                enable_file_access: T.settings_enable_file_access || 'File Access',
                enable_file_upload: T.settings_enable_file_upload || 'File Upload',
                enable_voice_input: T.settings_enable_voice_input || 'Voice Input',
                enable_rag: T.settings_enable_rag || 'RAG',
                enable_chat_bubble: T.settings_enable_chat_bubble || 'Chat Bubble',
                enable_amira_card_button: T.settings_enable_amira_card_button || 'Amira Card Button',
                enable_amira_automation_button: T.settings_enable_amira_automation_button || 'Amira Automation Button',
                enable_mcp: T.settings_enable_mcp || 'MCP Servers',
                anthropic_extended_thinking: T.settings_anthropic_thinking || 'Anthropic Thinking',
                anthropic_prompt_caching: T.settings_anthropic_caching || 'Prompt Caching',
                openai_extended_thinking: T.settings_openai_thinking || 'OpenAI Thinking',
                nvidia_thinking_mode: T.settings_nvidia_thinking || 'NVIDIA Thinking',
                tts_voice: T.settings_tts_voice || 'TTS Voice',
                enable_telegram: T.settings_enable_telegram || 'Telegram',
                telegram_bot_token: T.settings_telegram_token || 'Telegram Bot Token',
                telegram_allowed_ids: T.settings_telegram_allowed_ids || 'Allowed User IDs',
                enable_whatsapp: T.settings_enable_whatsapp || 'WhatsApp',
                twilio_account_sid: T.settings_twilio_sid || 'Twilio Account SID',
                twilio_auth_token: T.settings_twilio_token || 'Twilio Auth Token',
                twilio_whatsapp_from: T.settings_twilio_from || 'WhatsApp From Number',
                enable_discord: T.settings_enable_discord || 'Discord',
                discord_bot_token: T.settings_discord_token || 'Discord Bot Token',
                discord_allowed_channel_ids: T.settings_discord_allowed_channels || 'Allowed Channel IDs',
                discord_allowed_user_ids: T.settings_discord_allowed_users || 'Allowed User IDs',
                timeout: T.settings_timeout || 'Timeout (s)',
                max_retries: T.settings_max_retries || 'Max Retries',
                max_conversations: T.settings_max_conversations || 'Max Conversations',
                max_snapshots_per_file: T.settings_max_snapshots || 'Max Snapshots/File',
                cost_currency: T.settings_cost_currency || 'Currency',
            }};

            // i18n descriptions for setting keys
            const DESCS = {{}};
            Object.keys(LABELS).forEach(k => {{
                const tKey = 'settings_desc_' + k;
                if (T[tKey]) DESCS[k] = T[tKey];
            }});

            // Section labels
            const SECTION_LABELS = {{
                language: T.settings_section_language || 'Language',
                features: T.settings_section_features || 'Features',
                ai: T.settings_section_ai || 'AI',
                voice: T.settings_section_voice || 'Voice',
                messaging: T.settings_section_messaging || 'Messaging',
                advanced: T.settings_section_advanced || 'Advanced',
                costs: T.settings_section_costs || 'Costs',
            }};

            (settingsData.sections || []).forEach(section => {{
                const sec = document.createElement('div');
                sec.className = 'settings-section';

                const secHeader = document.createElement('div');
                secHeader.className = 'settings-section-header';
                const secTitle = document.createElement('span');
                secTitle.textContent = section.icon + ' ' + (SECTION_LABELS[section.id] || section.id).toUpperCase();
                secHeader.appendChild(secTitle);
                const arrow = document.createElement('span');
                arrow.className = 'settings-section-arrow';
                arrow.textContent = '\u25BC';
                secHeader.appendChild(arrow);

                const secBody = document.createElement('div');
                secBody.className = 'settings-section-body';

                secHeader.addEventListener('click', () => {{
                    const isOpen = secBody.style.display !== 'none';
                    secBody.style.display = isOpen ? 'none' : 'block';
                    arrow.textContent = isOpen ? '\u25B6' : '\u25BC';
                }});

                function appendField(field, targetBody) {{
                    const row = document.createElement('div');
                    row.className = 'settings-row';
                    const lbl = document.createElement('label');
                    lbl.className = 'settings-label';
                    lbl.textContent = LABELS[field.key] || field.key;
                    row.appendChild(lbl);

                    if (field.type === 'toggle') {{
                        const sw = document.createElement('label');
                        sw.className = 'settings-toggle';
                        const inp = document.createElement('input');
                        inp.type = 'checkbox';
                        inp.checked = !!values[field.key];
                        inp.addEventListener('change', () => {{ values[field.key] = inp.checked; }});
                        const sl = document.createElement('span');
                        sl.className = 'settings-slider';
                        sw.appendChild(inp);
                        sw.appendChild(sl);
                        row.appendChild(sw);
                    }} else if (field.type === 'select') {{
                        const sel = document.createElement('select');
                        sel.className = 'settings-select';
                        (field.options || []).forEach(opt => {{
                            const o = document.createElement('option');
                            o.value = opt.value;
                            o.textContent = opt.label;
                            if (String(values[field.key]).toLowerCase() === String(opt.value).toLowerCase()) o.selected = true;
                            sel.appendChild(o);
                        }});
                        sel.addEventListener('change', () => {{ values[field.key] = sel.value; }});
                        row.appendChild(sel);
                    }} else if (field.type === 'number') {{
                        const inp = document.createElement('input');
                        inp.type = 'number';
                        inp.className = 'settings-input';
                        inp.value = values[field.key] != null ? values[field.key] : (field.min || 0);
                        if (field.min !== undefined) inp.min = field.min;
                        if (field.max !== undefined) inp.max = field.max;
                        if (field.step !== undefined) inp.step = field.step;
                        inp.addEventListener('change', () => {{ values[field.key] = parseInt(inp.value) || 0; }});
                        row.appendChild(inp);
                    }} else if (field.type === 'password') {{
                        const pwWrap = document.createElement('div');
                        pwWrap.className = 'settings-pw-wrap';
                        const inp = document.createElement('input');
                        inp.type = 'password';
                        inp.className = 'settings-input settings-password';
                        inp.value = values[field.key] || '';
                        inp.placeholder = '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022';
                        inp.addEventListener('input', () => {{ values[field.key] = inp.value; }});
                        const eyeBtn = document.createElement('button');
                        eyeBtn.type = 'button';
                        eyeBtn.className = 'settings-eye-btn';
                        eyeBtn.textContent = '\U0001f441\ufe0f';
                        eyeBtn.addEventListener('click', () => {{
                            inp.type = inp.type === 'password' ? 'text' : 'password';
                        }});
                        pwWrap.appendChild(eyeBtn);
                        pwWrap.appendChild(inp);
                        row.appendChild(pwWrap);
                    }} else {{
                        const inp = document.createElement('input');
                        inp.type = 'text';
                        inp.className = 'settings-input';
                        inp.value = values[field.key] || '';
                        inp.addEventListener('input', () => {{ values[field.key] = inp.value; }});
                        row.appendChild(inp);
                    }}

                    targetBody.appendChild(row);
                    if (DESCS[field.key]) {{
                        const desc = document.createElement('div');
                        desc.className = 'settings-desc';
                        desc.textContent = DESCS[field.key];
                        targetBody.appendChild(desc);
                    }}
                }}

                const sectionFields = section.fields || [];
                if (section.id === 'messaging') {{
                    const groups = [
                        {{
                            title: '\U0001f916 Telegram',
                            keys: ['enable_telegram', 'telegram_bot_token', 'telegram_allowed_ids']
                        }},
                        {{
                            title: '\U0001f4ac WhatsApp',
                            keys: ['enable_whatsapp', 'twilio_account_sid', 'twilio_auth_token', 'twilio_whatsapp_from']
                        }},
                        {{
                            title: '\U0001f579\ufe0f Discord',
                            keys: ['enable_discord', 'discord_bot_token', 'discord_allowed_channel_ids', 'discord_allowed_user_ids']
                        }},
                    ];

                    groups.forEach(group => {{
                        const available = group.keys
                            .map(key => sectionFields.find(f => f.key === key))
                            .filter(Boolean);
                        if (!available.length) return;

                        const sub = document.createElement('div');
                        sub.className = 'settings-subsection';
                        const subTitle = document.createElement('div');
                        subTitle.className = 'settings-subsection-title';
                        subTitle.textContent = group.title;
                        sub.appendChild(subTitle);

                        available.forEach(field => appendField(field, sub));
                        secBody.appendChild(sub);
                    }});
                }} else {{
                    sectionFields.forEach(field => appendField(field, secBody));
                }}

                sec.appendChild(secHeader);
                sec.appendChild(secBody);
                body.appendChild(sec);
            }});

            // Save button
            const saveRow = document.createElement('div');
            saveRow.style.cssText = 'margin-top:16px;display:flex;align-items:center;gap:10px;padding-bottom:20px;';
            const saveBtn = document.createElement('button');
            saveBtn.className = 'config-save-btn';
            saveBtn.style.cssText = 'padding:8px 22px;font-size:13px;';
            saveBtn.textContent = '\U0001f4be ' + (T.config_save || 'Save');
            const saveStatus = document.createElement('span');
            saveStatus.style.cssText = 'font-size:12px;color:#4caf50;';
            saveBtn.addEventListener('click', async () => {{
                saveBtn.disabled = true;
                saveBtn.textContent = '\u23F3 ...';
                try {{
                    const resp = await fetch(apiUrl('api/settings'), {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        credentials: 'same-origin',
                        body: JSON.stringify(values)
                    }});
                    const data = await resp.json();
                    if (!data.success) throw new Error(data.error || 'Save failed');
                    saveStatus.textContent = '\u2705 ' + (T.settings_saved || 'Settings saved!');
                    setTimeout(() => {{ saveStatus.textContent = ''; }}, 3000);
                    await _askRestartAddon(saveStatus);
                }} catch(e) {{
                    saveStatus.textContent = '\u274C ' + (e.message || 'Error');
                    saveStatus.style.color = '#f44336';
                    setTimeout(() => {{ saveStatus.textContent = ''; saveStatus.style.color = '#4caf50'; }}, 4000);
                }} finally {{
                    saveBtn.disabled = false;
                    saveBtn.textContent = '\U0001f4be ' + (T.config_save || 'Save');
                }}
            }});
            saveRow.appendChild(saveBtn);
            saveRow.appendChild(saveStatus);
            body.appendChild(saveRow);

            // ---- Bubble Diagnostics panel ----
            const diagSec = document.createElement('div');
            diagSec.className = 'settings-section';
            const diagHdr = document.createElement('div');
            diagHdr.className = 'settings-section-header';
            const diagTitle = document.createElement('span');
            diagTitle.textContent = '\U0001f50d BUBBLE DIAGNOSTICS';
            diagHdr.appendChild(diagTitle);
            const diagArrow = document.createElement('span');
            diagArrow.className = 'settings-section-arrow';
            diagArrow.textContent = '\u25B6';
            diagHdr.appendChild(diagArrow);
            const diagBody = document.createElement('div');
            diagBody.className = 'settings-section-body';
            diagBody.style.display = 'none';
            diagHdr.addEventListener('click', async () => {{
                const isVis = diagBody.style.display !== 'none';
                diagBody.style.display = isVis ? 'none' : 'block';
                diagArrow.textContent = isVis ? '\u25B6' : '\u25BC';
                if (!isVis) {{
                    diagBody.innerHTML = '<div style="padding:8px;color:#999;">Loading...</div>';
                    try {{
                        const r = await fetch(apiUrl('api/bubble/status'), {{credentials:'same-origin'}});
                        const d = await r.json();
                        let html = '<div style="padding:8px;font-size:12px;font-family:monospace;line-height:1.8;">';
                        const ok = '\u2705', no = '\u274C', warn = '\u26A0\uFE0F';
                        html += '<div>' + (d.bubble_enabled ? ok : no) + ' Chat Bubble: <b>' + (d.bubble_enabled ? 'ON' : 'OFF') + '</b></div>';
                        html += '<div>' + (d.card_button_enabled ? ok : no) + ' Card Button: <b>' + (d.card_button_enabled ? 'ON' : 'OFF') + '</b></div>';
                        html += '<div>' + ((d.automation_button_enabled !== false) ? ok : no) + ' Automation Button: <b>' + ((d.automation_button_enabled !== false) ? 'ON' : 'OFF') + '</b></div>';
                        html += '<div>' + (d.registered_flag ? ok : warn) + ' Registered flag: <b>' + d.registered_flag + '</b></div>';
                        html += '<div>' + (d.ingress_url && d.ingress_url !== '(empty)' ? ok : no) + ' Ingress URL: <b>' + (d.ingress_url || '(empty)') + '</b></div>';
                        const mods = d.module_files || {{}};
                        const loader = mods.loader || d.js_file || {{}};
                        const bubble = mods.bubble || {{}};
                        const card = mods.card || {{}};
                        const automation = mods.automation || {{}};
                        html += '<div>' + (loader.exists ? ok : no) + ' Loader JS: <b>' + (loader.exists ? (loader.size_bytes + ' bytes') : 'NOT FOUND') + '</b></div>';
                        html += '<div>' + (bubble.exists ? ok : no) + ' Module Bubble: <b>' + (bubble.exists ? (bubble.size_bytes + ' bytes') : 'NOT FOUND') + '</b></div>';
                        html += '<div>' + (card.exists ? ok : no) + ' Module Card: <b>' + (card.exists ? (card.size_bytes + ' bytes') : 'NOT FOUND') + '</b></div>';
                        html += '<div>' + (automation.exists ? ok : no) + ' Module Automation: <b>' + (automation.exists ? (automation.size_bytes + ' bytes') : 'NOT FOUND') + '</b></div>';
                        const lr = d.lovelace_resource || {{}};
                        if (lr.error) {{
                            html += '<div>' + warn + ' Lovelace: <b>' + lr.error + '</b></div>';
                        }} else {{
                            html += '<div>' + (lr.registered ? ok : no) + ' Lovelace: <b>' + (lr.registered ? 'Registered' : 'NOT registered') + '</b>';
                            if (lr.entries && lr.entries.length) {{
                                lr.entries.forEach(e => {{ html += '<br>&nbsp;&nbsp;id=' + e.id + ' url=' + e.url; }});
                            }}
                            html += '</div>';
                        }}
                        html += '<div style="margin-top:8px;color:var(--secondary-text-color,#888);">' + (d.hint || '') + '</div>';
                        html += '<div style="margin-top:10px;"><button id="_diagReRegBtn" style="padding:6px 14px;font-size:12px;cursor:pointer;border:1px solid var(--divider-color,#ddd);border-radius:6px;background:var(--primary-color,#03a9f4);color:#fff;">Force Re-Register</button></div>';
                        html += '</div>';
                        diagBody.innerHTML = html;
                        const reRegBtn = document.getElementById('_diagReRegBtn');
                        if (reRegBtn) {{
                            reRegBtn.addEventListener('click', async () => {{
                                reRegBtn.disabled = true;
                                reRegBtn.textContent = '...';
                                try {{
                                    const rr = await fetch(apiUrl('api/bubble/register'), {{method:'POST', credentials:'same-origin'}});
                                    const rd = await rr.json();
                                    reRegBtn.textContent = rd.ok ? '\u2705 Done — reload HA page' : '\u274C Failed';
                                }} catch(ex) {{ reRegBtn.textContent = '\u274C ' + ex.message; }}
                            }});
                        }}
                    }} catch(ex) {{
                        diagBody.innerHTML = '<div style="padding:8px;color:#f44336;">Error: ' + ex.message + '</div>';
                    }}
                }}
            }});
            diagSec.appendChild(diagHdr);
            diagSec.appendChild(diagBody);
            body.appendChild(diagSec);

            wrap.appendChild(body);
            filePanelContentEl.appendChild(wrap);
        }}

        function setConfigStatus(text, cls) {{
            const el = document.getElementById('configStatus');
            if (!el) return;
            el.textContent = text;
            el.className = 'config-status' + (cls ? ' ' + cls : '');
            if (text) setTimeout(() => {{ el.textContent = ''; el.className = 'config-status'; }}, 3000);
        }}

        async function saveConfigFile(filePath, content) {{
            try {{
                const resp = await fetch(apiUrl('api/config/save'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    credentials: 'same-origin',
                    body: JSON.stringify({{ file: filePath, content: content }})
                }});
                const data = await resp.json();
                if (!data.success) throw new Error(data.error || 'Save failed');
                configOriginalContent = content;
                setConfigStatus(T.config_saved || 'Saved!', 'success');
            }} catch(e) {{
                setConfigStatus((T.config_save_error || 'Save failed') + ': ' + (e.message || ''), 'error');
            }}
        }}

        function isMobileLayout() {{
            return window.matchMedia('(max-width: 768px)').matches || window.matchMedia('(pointer: coarse)').matches;
        }}

        function toggleSidebar() {{
            if (!sidebarEl) return;
            const wasOpen = sidebarEl.classList.contains('mobile-open');
            sidebarEl.classList.toggle('mobile-open');
            // Refresh conversation list when opening on mobile
            if (!wasOpen) {{
                const activeTab = document.querySelector('.sidebar-tab.active');
                const tabName = activeTab ? activeTab.dataset.tab : 'chat';
                if (tabName === 'chat') loadChatList();
                else if (tabName === 'bubble') loadBubbleList();
                else if (tabName === 'amira') loadAmiraList();
                else if (tabName === 'backups') loadBackupList();
                else if (tabName === 'devices') loadDeviceList();
            }}
        }}

        function closeSidebarMobile() {{
            if (!sidebarEl) return;
            if (!isMobileLayout()) return;
            sidebarEl.classList.remove('mobile-open');
        }}

        function handleImageSelect(event) {{
            const file = event.target.files[0];
            if (!file) return;

            // Check file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {{
                alert(T.image_too_large);
                return;
            }}

            const reader = new FileReader();
            reader.onload = (e) => {{
                currentImage = e.target.result;
                imagePreview.src = currentImage;
                imagePreviewContainer.classList.add('visible');
            }};
            reader.readAsDataURL(file);
        }}

        function removeImage() {{
            currentImage = null;
            imageInput.value = '';
            imagePreviewContainer.classList.remove('visible');
        }}

        const docPreviewContainer = document.getElementById('docPreviewContainer');
        const docPreviewName = document.getElementById('docPreviewName');
        const docPreviewSize = document.getElementById('docPreviewSize');
        const docPreviewIcon = document.getElementById('docPreviewIcon');

        const DOC_ICONS = {{
            'pdf': '📕', 'docx': '📘', 'doc': '📘',
            'txt': '📝', 'md': '📝', 'markdown': '📝',
            'yaml': '📋', 'yml': '📋', 'odt': '📗'
        }};

        function showDocPreview(file) {{
            const ext = file.name.split('.').pop().toLowerCase();
            docPreviewIcon.textContent = DOC_ICONS[ext] || '📄';
            docPreviewName.textContent = file.name;
            const sizeKB = file.size / 1024;
            docPreviewSize.textContent = sizeKB > 1024
                ? `${{(sizeKB / 1024).toFixed(2)}} MB`
                : `${{sizeKB.toFixed(1)}} KB`;
            docPreviewContainer.classList.add('visible');
        }}

        function removeDocument() {{
            pendingDocument = null;
            document.getElementById('documentInput').value = '';
            docPreviewContainer.classList.remove('visible');
        }}

        function handleDocumentSelect(event) {{
            const file = event.target.files[0];
            if (!file) return;

            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {{
                alert(T.file_too_large || 'File too large (max 10MB)');
                document.getElementById('documentInput').value = '';
                return;
            }}

            pendingDocument = file;
            showDocPreview(file);
            // Focus the input so the user can type a message
            if (input) input.focus();
        }}

        function toggleReadOnly(checked) {{
            readOnlyMode = checked;
            safeLocalStorageSet('readOnlyMode', checked ? 'true' : 'false');
            const label = document.getElementById('readOnlyLabel');
            if (label) label.textContent = checked ? T.readonly_on : T.readonly_off;
            const wrapper = document.querySelector('.readonly-toggle');
            if (wrapper) wrapper.classList.toggle('active', checked);
        }}

        function toggleDarkMode(checked) {{
            darkMode = checked;
            safeLocalStorageSet('darkMode', checked ? 'true' : 'false');
            if (checked) {{
                document.body.classList.add('dark-mode');
                document.getElementById('themeIcon').textContent = '\u2600';  // sun emoji
                document.getElementById('darkModeLabel').textContent = 'ON';
            }} else {{
                document.body.classList.remove('dark-mode');
                document.getElementById('themeIcon').textContent = '\U0001f319';  // moon emoji
                document.getElementById('darkModeLabel').textContent = 'OFF';
            }}
            const wrapper = document.querySelector('.dark-mode-toggle');
            if (wrapper) wrapper.classList.toggle('active', checked);
        }}

        // Initialize dark mode on page load
        (function() {{
            const darkModeStored = safeLocalStorageGet('darkMode', 'false') === 'true';
            darkMode = darkModeStored;
            const toggle = document.getElementById('darkModeToggle');
            if (toggle) {{
                toggle.checked = darkMode;
                if (darkMode) {{
                    document.body.classList.add('dark-mode');
                    document.getElementById('themeIcon').textContent = '\u2600';
                    document.getElementById('darkModeLabel').textContent = 'ON';
                }} else {{
                    document.getElementById('themeIcon').textContent = '\U0001f319';
                    document.getElementById('darkModeLabel').textContent = 'OFF';
                }}
                const wrapper = document.querySelector('.dark-mode-toggle');
                if (wrapper) wrapper.classList.toggle('active', darkMode);
            }}
        }})();

        // Initialize read-only toggle on page load
        (function() {{
            const toggle = document.getElementById('readOnlyToggle');
            if (toggle) {{
                toggle.checked = readOnlyMode;
                const label = document.getElementById('readOnlyLabel');
                if (label) label.textContent = readOnlyMode ? T.readonly_on : T.readonly_off;
                const wrapper = document.querySelector('.readonly-toggle');
                if (wrapper) wrapper.classList.toggle('active', readOnlyMode);
            }}
        }})();

        function injectConfirmButtons(div, fullText) {{
            if (!div || !fullText) return;
            if (div.querySelector('.confirm-buttons')) return;

            // If the message contains a numbered entity selection (e.g., "1) light.kitchen"),
            // do NOT show confirm/cancel buttons.
            try {{
                const numbered = extractNumberedEntityOptions(fullText);
                if (numbered && numbered.length) return;
            }} catch (e) {{}}

            // If the AI is asking the user to pick an entity/device first, do NOT show confirm/cancel buttons.
            if (isEntityPickingPrompt(fullText)) return;

            const CONFIRM_PATTERNS = [
                /confermi.*?\\?/i,
                /scrivi\\s+s[i\u00ec]\\s+o\\s+no/i,
                /digita\\s+['"\u2018\u2019]?elimina['"\u2018\u2019]?\\s+per\\s+confermare/i,
                /vuoi\\s+(eliminare|procedere|continuare|applic).*?\\?/i,
                /vuoi\\s+che\\s+(applic|esegu|salv|scriva|modifich).*?\\?/i,
                /appl[io]+.*?\\?/i,
                /(?:la|lo)?\\s+(?:applic|corregg|modific|cambi|salv).*?\\?/i,
                /s[i\u00ec]\\s*\\/\\s*no/i,
                /confirm.*?\\?\\s*(yes.*no)?/i,
                /type\\s+['"]?yes['"]?\\s+or\\s+['"]?no['"]?/i,
                /do\\s+you\\s+want\\s+(me\\s+to\\s+)?(apply|proceed|continue|delete|save|write).*?\\?/i,
                /should\\s+i\\s+(apply|proceed|write|save).*?\\?/i,
                /confirma.*?\\?/i,
                /escribe\\s+s[i\u00ed]\\s+o\\s+no/i,
                /\\u00bfquieres\\s+que\\s+(apliqu|proceda|guard).*?\\?/i,
                /confirme[sz]?.*?\\?/i,
                /tape[sz]?\\s+['"]?oui['"]?\\s+ou\\s+['"]?non['"]?/i,
                /veux-tu\\s+que\\s+(j['\u2019]appliqu|je\\s+proc[eè]d|je\\s+sauvegard).*?\\?/i,
                // Patterns generati dai no-tool prompt (claude_web, chatgpt_web, ecc.)
                /conferma\\s+con\\s+s[i\u00ec]/i,
                /s[i\u00ec]\\s*\\/\\s*yes\\s*\\/\\s*ok/i,
                /perfetto\\?/i,
                /salvo\\s+per\\s+te/i,
                /creo\\s+per\\s+te/i,
                /procedo\\s+con\\s+la\\s+creazione/i,
                /posso\\s+(creare|salvare|procedere|confermare).*?\\?/i,
                /ok\\s+per\\s+te\\??/i,
                /va\\s+bene.*?\\?/i,
            ];

            const isConfirmation = CONFIRM_PATTERNS.some(function(p) {{ return p.test(fullText); }});
            if (!isConfirmation) return;

            const isDeleteConfirm = /digita\\s+['"\u2018\u2019]?elimina['"\u2018\u2019]?/i.test(fullText) ||
                                    /type\\s+['"]?delete['"]?/i.test(fullText);

            const btnContainer = document.createElement('div');
            btnContainer.className = 'confirm-buttons';

            const yesBtn = document.createElement('button');
            yesBtn.className = 'confirm-btn confirm-yes';
            yesBtn.textContent = isDeleteConfirm ? ('\U0001f5d1 ' + T.confirm_delete_yes) : ('\u2705 ' + T.confirm_yes);

            const noBtn = document.createElement('button');
            noBtn.className = 'confirm-btn confirm-no';
            noBtn.textContent = '\u274c ' + T.confirm_no;

            yesBtn.onclick = function() {{
                yesBtn.disabled = true;
                noBtn.disabled = true;
                btnContainer.classList.add('answered');
                yesBtn.classList.add('selected');
                const answer = isDeleteConfirm ? 'elimina' : T.confirm_yes_value;
                input.value = answer;
                sendMessage();
            }};

            noBtn.onclick = function() {{
                yesBtn.disabled = true;
                noBtn.disabled = true;
                btnContainer.classList.add('answered');
                noBtn.classList.add('selected');
                input.value = T.confirm_no_value;
                sendMessage();
            }};

            btnContainer.appendChild(yesBtn);
            btnContainer.appendChild(noBtn);
            div.appendChild(btnContainer);
        }}

        function isEntityPickingPrompt(fullText) {{
            if (!fullText || typeof fullText !== 'string') return false;

            // If we can extract numbered entity options, this is almost certainly a selection prompt.
            try {{
                const numbered = extractNumberedEntityOptions(fullText);
                if (numbered && numbered.length) return true;
            }} catch (e) {{}}

            const PICK_PATTERNS = [
                /quale\\s+(dispositivo|entit[aà]|entity)/i,
                /scegli/i,
                /seleziona/i,
                /rispondi\\s+con\\s+il\\s+numero/i,
                /scrivi\\s+il\\s+numero/i,
                /inserisci\\s+il\\s+numero/i,
                /digita\\s+il\\s+numero/i,
                /rispondi\\s+con\\s+(?:il\\s+)?\\d+/i,
                /scrivi\\s+(?:il\\s+)?\\d+/i,
                /inserisci\\s+(?:il\\s+)?\\d+/i,
                /digita\\s+(?:il\\s+)?\\d+/i,
                /\\b\\d+\\s*(?:o|oppure|or)\\s*\\d+\\b/i,
                /numero\\s+o\\s+con\\s+l['’]?entity_id/i,
                /which\\s+(device|entity)/i,
                /choose/i,
                /select/i,
                /pick/i,
                /reply\\s+with\\s+the\\s+(number|entity_id)/i,
            ];
            return PICK_PATTERNS.some(function(p) {{ return p.test(fullText); }});
        }}

        function extractEntityIds(text) {{
            if (!text || typeof text !== 'string') return [];
            const re = /\\b[a-z_]+\\.[a-z0-9_]+\\b/g;
            const found = text.match(re) || [];
            const uniq = [];
            const seen = new Set();
            for (const eid of found) {{
                const v = String(eid).trim();
                if (!v) continue;
                if (seen.has(v)) continue;
                seen.add(v);
                uniq.push(v);
            }}
            return uniq;
        }}

        function _stripCodeBlocks(text) {{
            // Remove fenced code blocks (``` ... ```) to avoid false-positive entity parsing
            // inside YAML / Jinja2 snippets shown by the AI
            return String(text || '').replace(/```[\\s\\S]*?```/g, '').replace(/`[^`\\n]+`/g, '');
        }}

        function extractNumberedEntityOptions(text) {{
            if (!text || typeof text !== 'string') return [];
            // Strip fenced code blocks first — numbered lines inside YAML/Jinja are not entity picks
            const stripped = _stripCodeBlocks(text);
            // Handles formats like: 1) light.kitchen — Kitchen, 1. `light.kitchen`, option 1) device name
            const lines = String(stripped).split(/\\r?\\n/);
            const out = [];
            const seenNum = new Set();

            function findEntityIdInLine(line) {{
                if (!line) return '';
                const m = String(line).match(/`?\\b([a-z_]+\\.[a-z0-9_]+)\\b`?/i);
                return m ? String(m[1] || '').trim() : '';
            }}

            for (let i = 0; i < lines.length; i++) {{
                const line = lines[i];
                const m = String(line).match(/^\\s*(?:[-*]\\s*)?(\\d+)\\s*[\\)\\.:\\-]\\s*(.*)$/);
                if (!m) continue;

                const num = String(m[1] || '').trim();
                if (!num || seenNum.has(num)) continue;

                const rest = String(m[2] || '');
                let entityId = findEntityIdInLine(rest);
                let label = '';

                if (entityId) {{
                    // Remove the entity_id from the line to get a label, if present
                    label = rest
                        .replace(new RegExp('`?\\b' + entityId.replace(/[.*+?^$()|[\\]\\\\]/g, '\\\\$&') + '\\b`?', 'i'), '')
                        .replace(/^[\\s:—–\\-]+/, '')
                        .trim();
                }} else {{
                    // Look ahead a few lines for an entity_id (common when formatted as YAML)
                    for (let j = i + 1; j < Math.min(lines.length, i + 4); j++) {{
                        const candidate = findEntityIdInLine(lines[j]);
                        if (candidate) {{
                            entityId = candidate;
                            label = rest.trim();
                            break;
                        }}
                    }}
                }}

                if (!entityId) continue;
                seenNum.add(num);
                out.push({{ num, entity_id: entityId, label }});
            }}

            return out;
        }}

        function _escapeHtml(s) {{
            return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }}

        function renderStepLines(steps) {{
            if (!steps || !steps.length) return '';
            return steps.map(s => '<div>• ' + _escapeHtml(s) + '</div>').join('');
        }}

        function injectEntityPicker(div, fullText) {{
            if (!div || !fullText) return;
            if (div.querySelector('.entity-picker') || div.querySelector('.entity-manual')) return;
            // Do not activate picker if the response is primarily a code answer
            // (contains fenced code blocks with YAML/Jinja content)
            if (new RegExp('```[\\s\\S]*?```').test(fullText)) return;

            const numbered = extractNumberedEntityOptions(fullText);
            const entityIds = extractEntityIds(fullText);
            const isPicking = (numbered && numbered.length) || isEntityPickingPrompt(fullText);
            if (!isPicking) return;
            if ((!numbered || numbered.length < 1) && (!entityIds || entityIds.length < 1)) return;

            // Click/tap list
            const picker = document.createElement('div');
            picker.className = 'entity-picker';

            const maxButtons = 10;
            if (numbered && numbered.length) {{
                numbered.slice(0, maxButtons).forEach(function(opt) {{
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'suggestion';
                    btn.textContent = opt.num + ' • ' + (opt.entity_id || '');
                    if (opt.label) btn.title = opt.label;
                    btn.onclick = function() {{
                        // The AI asked for the number.
                        input.value = String(opt.num);
                        sendMessage();
                    }};
                    picker.appendChild(btn);
                }});
            }} else {{
                entityIds.slice(0, maxButtons).forEach(function(eid) {{
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'suggestion';
                    btn.textContent = eid;
                    btn.onclick = function() {{
                        input.value = eid;
                        sendMessage();
                    }};
                    picker.appendChild(btn);
                }});
            }}

            // Manual entry
            const manual = document.createElement('div');
            manual.className = 'entity-manual';

            const field = document.createElement('input');
            field.className = 'entity-input';
            field.placeholder = 'entity_id…';
            field.autocomplete = 'off';
            field.spellcheck = false;

            const useBtn = document.createElement('button');
            useBtn.type = 'button';
            useBtn.className = 'suggestion';
            useBtn.textContent = 'Select';

            function submitManual() {{
                const v = (field.value || '').trim();
                if (!v) return;
                input.value = v;
                sendMessage();
            }}

            useBtn.onclick = submitManual;
            field.addEventListener('keydown', function(e) {{
                if (e.key === 'Enter') {{
                    e.preventDefault();
                    submitManual();
                }}
            }});

            manual.appendChild(field);
            manual.appendChild(useBtn);

            div.appendChild(picker);
            div.appendChild(manual);
        }}

        function apiUrl(path) {{
            // Build URLs robustly for Home Assistant Ingress.
            // If the current page URL doesn't end with '/', browsers treat the last segment as a file
            // and relative fetches may drop it (breaking requests).
            const cleanPath = (path || '').startsWith('/') ? (path || '').slice(1) : (path || '');
            // Use origin+pathname (not href) to avoid hash/query edge cases.
            const basePath = (window.location.pathname || '/').endsWith('/')
                ? (window.location.pathname || '/')
                : ((window.location.pathname || '/') + '/');
            return window.location.origin.replace(/\\/$/, '') + basePath + cleanPath;
        }}

        async function _askRestartAddon(statusEl) {{
            if (!confirm(T.restart_confirm || 'Some changes require a restart to take effect. Restart the add-on now?')) return;
            if (statusEl) {{
                statusEl.textContent = '\u267b\ufe0f ' + (T.restart_in_progress || 'Restarting add-on...');
                statusEl.style.color = '#ff9800';
            }}
            try {{
                await fetch(apiUrl('api/addon/restart'), {{
                    method: 'POST',
                    headers: {{'Content-Type':'application/json'}},
                    credentials: 'same-origin'
                }});
            }} catch(e) {{
                if (statusEl) {{
                    statusEl.textContent = '\u274c ' + (T.restart_failed || 'Restart failed');
                    statusEl.style.color = '#f44336';
                }}
            }}
        }}

        function setStopMode(active) {{
            if (active) {{
                sendBtn.classList.add('stop-btn');
                sendBtn.disabled = false;
                sendIcon.style.display = 'none';
                stopIcon.style.display = 'block';
            }} else {{
                sendBtn.classList.remove('stop-btn');
                sendIcon.style.display = 'block';
                stopIcon.style.display = 'none';
            }}
        }}

        async function handleButtonClick() {{
            if (sending) {{
                try {{
                    await fetch(apiUrl('api/chat/abort'), {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: '{{}}' }});
                    if (currentReader) {{ currentReader.cancel(); currentReader = null; }}
                }} catch(e) {{ console.error('Abort error:', e); }}
                removeThinking();
                sending = false;
                setStopMode(false);
                sendBtn.disabled = false;
            }} else {{
                try {{
                    await sendMessage();
                }} catch (e) {{
                    addMessage('\u274c ' + (e && e.message ? e.message : String(e)), 'system');
                }}
            }}
        }}

        function autoResize(el) {{
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        }}

        function _wrapInputSelection(prefix, suffix, placeholder = '') {{
            if (!input) return;
            const start = input.selectionStart || 0;
            const end = input.selectionEnd || 0;
            const before = input.value.slice(0, start);
            const selected = input.value.slice(start, end);
            const after = input.value.slice(end);
            const body = selected || placeholder;
            input.value = before + prefix + body + suffix + after;
            const cursorPos = before.length + prefix.length + body.length;
            input.focus();
            input.selectionStart = cursorPos;
            input.selectionEnd = cursorPos;
            autoResize(input);
        }}

        function insertCodeFence(lang) {{
            const safeLang = String(lang || '').trim();
            const header = safeLang ? ('```' + safeLang + '\\n') : '```\\n';
            _wrapInputSelection(header, '\\n```', 'incolla qui il codice');
        }}

        function insertLinkTemplate() {{
            if (!input) return;
            const start = input.selectionStart || 0;
            const end = input.selectionEnd || 0;
            const selected = input.value.slice(start, end);
            const label = selected || 'testo';
            _wrapInputSelection('[', '](https://)', label);
        }}

        function bindInputToolbarButtons() {{
            const fmtCodeBtn = document.getElementById('fmtCodeBtn');
            const fmtHtmlBtn = document.getElementById('fmtHtmlBtn');
            const fmtLinkBtn = document.getElementById('fmtLinkBtn');
            if (fmtCodeBtn && !fmtCodeBtn._amiraBound) {{
                fmtCodeBtn._amiraBound = true;
                fmtCodeBtn.onclick = () => insertCodeFence('yaml');
            }}
            if (fmtHtmlBtn && !fmtHtmlBtn._amiraBound) {{
                fmtHtmlBtn._amiraBound = true;
                fmtHtmlBtn.onclick = () => insertCodeFence('html');
            }}
            if (fmtLinkBtn && !fmtLinkBtn._amiraBound) {{
                fmtLinkBtn._amiraBound = true;
                fmtLinkBtn.onclick = () => insertLinkTemplate();
            }}
        }}

        window.__amiraInputFormat = function(kind) {{
            try {{
                if (kind === 'code') return insertCodeFence('yaml');
                if (kind === 'html') return insertCodeFence('html');
                if (kind === 'link') return insertLinkTemplate();
            }} catch (e) {{
                console.warn('[ui] __amiraInputFormat failed', e);
            }}
        }};

        function handleKeyDown(e) {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                handleButtonClick();
            }}
        }}

        function renderDiff(diffText) {{
            if (!diffText) return;
            const wrapper = document.createElement('details');
            wrapper.style.cssText = 'margin:8px 0;font-size:12px;border:1px solid #334155;border-radius:6px;overflow:hidden;';
            const summary = document.createElement('summary');
            summary.style.cssText = 'padding:6px 10px;cursor:pointer;background:#1e293b;color:#94a3b8;user-select:none;';
            summary.textContent = '📝 Diff modifiche';
            wrapper.appendChild(summary);
            const pre = document.createElement('pre');
            pre.style.cssText = 'margin:0;padding:8px;overflow-x:auto;background:#0f172a;font-size:11px;line-height:1.5;';
            diffText.split('\\n').forEach(function(line) {{
                const span = document.createElement('span');
                span.style.cssText = 'display:block;white-space:pre;';
                if (line.startsWith('+') && !line.startsWith('+++')) {{
                    span.style.background = 'rgba(34,197,94,0.15)';
                    span.style.color = '#86efac';
                }} else if (line.startsWith('-') && !line.startsWith('---')) {{
                    span.style.background = 'rgba(239,68,68,0.15)';
                    span.style.color = '#fca5a5';
                }} else if (line.startsWith('@@')) {{
                    span.style.color = '#7dd3fc';
                }} else if (line.startsWith('---') || line.startsWith('+++')) {{
                    span.style.color = '#64748b';
                }} else {{
                    span.style.color = '#94a3b8';
                }}
                span.textContent = line;
                pre.appendChild(span);
            }});
            wrapper.appendChild(pre);
            return wrapper;
        }}

        function _fmtTokens(n) {{
            if (!n || n <= 0) return '0';
            if (n >= 1000000) return (n/1000000).toFixed(1) + 'm';
            if (n >= 10000)  return (n/1000).toFixed(0) + 'k';
            if (n >= 1000)   return (n/1000).toFixed(1) + 'k';
            return String(Math.round(n));
        }}

        function _currSym(currency) {{
            const c = (currency || 'USD').toUpperCase().trim();
            if (c === 'EUR') return '\u20ac';
            if (c === 'GBP') return '\u00a3';
            if (c === 'JPY') return '\u00a5';
            return '$';
        }}

        function _fmtCost(val) {{
            if (val === undefined || val === null) return null;
            if (val >= 0.01) return val.toFixed(2);
            if (val > 0) return val.toFixed(4);
            return '0.00';
        }}

        function formatUsage(usage) {{
            if (!usage || (!usage.input_tokens && !usage.output_tokens)) return '';
            const inp = _fmtTokens(usage.input_tokens || 0);
            const out = _fmtTokens(usage.output_tokens || 0);
            let tokens = inp + ' in / ' + out + ' out';
            // Show cache tokens if present
            const cacheR = usage.cache_read_tokens || 0;
            const cacheW = usage.cache_write_tokens || 0;
            if (cacheR > 0 || cacheW > 0) {{
                let cacheParts = [];
                if (cacheR > 0) cacheParts.push(_fmtTokens(cacheR) + ' cache\u2193');
                if (cacheW > 0) cacheParts.push(_fmtTokens(cacheW) + ' cache\u2191');
                tokens += ' (' + cacheParts.join(', ') + ')';
            }}
            if (usage.cost !== undefined && usage.cost !== null) {{
                const sym = _currSym(usage.currency);
                if (usage.cost > 0) {{
                    tokens += ' \u2022 ' + sym + _fmtCost(usage.cost);
                    // Tooltip with breakdown if available
                    if (usage.cost_breakdown) {{
                        const bd = usage.cost_breakdown;
                        let tip = [];
                        if (bd.input > 0)       tip.push('Input: ' + sym + _fmtCost(bd.input));
                        if (bd.output > 0)      tip.push('Output: ' + sym + _fmtCost(bd.output));
                        if (bd.cache_read > 0)  tip.push('Cache read: ' + sym + _fmtCost(bd.cache_read));
                        if (bd.cache_write > 0) tip.push('Cache write: ' + sym + _fmtCost(bd.cache_write));
                        if (tip.length > 1) {{
                            return '<div class="message-usage" title="' + tip.join('\\n') + '">' + tokens + '</div>';
                        }}
                    }}
                }} else {{
                    tokens += ' \u2022 free';
                }}
            }}
            return '<div class="message-usage">' + tokens + '</div>';
        }}

        const COST_CURRENCY = '{cost_currency}';
        let conversationUsage = {{ input_tokens: 0, output_tokens: 0, cache_read_tokens: 0, cache_write_tokens: 0, cost: 0, currency: COST_CURRENCY }};

        function updateConversationUsage(usage) {{
            if (!usage) return;
            conversationUsage.input_tokens += (usage.input_tokens || 0);
            conversationUsage.output_tokens += (usage.output_tokens || 0);
            conversationUsage.cache_read_tokens += (usage.cache_read_tokens || 0);
            conversationUsage.cache_write_tokens += (usage.cache_write_tokens || 0);
            conversationUsage.cost += (usage.cost || 0);
            conversationUsage.currency = usage.currency || COST_CURRENCY;
            renderConversationTotal();
        }}

        function resetConversationUsage() {{
            conversationUsage = {{ input_tokens: 0, output_tokens: 0, cache_read_tokens: 0, cache_write_tokens: 0, cost: 0, currency: COST_CURRENCY }};
            renderConversationTotal();
        }}

        function renderConversationTotal() {{
            let el = document.getElementById('conversation-usage-total');
            if (!el) {{
                el = document.createElement('div');
                el.id = 'conversation-usage-total';
                el.className = 'conversation-usage';
                // Insert before input area
                const inputArea = document.querySelector('.input-area');
                if (inputArea) inputArea.parentNode.insertBefore(el, inputArea);
            }}
            if (conversationUsage.input_tokens === 0 && conversationUsage.output_tokens === 0) {{
                el.style.display = 'none';
                return;
            }}
            el.style.display = 'block';
            const inp = _fmtTokens(conversationUsage.input_tokens);
            const out = _fmtTokens(conversationUsage.output_tokens);
            const sym = _currSym(conversationUsage.currency);
            let text = 'Usage: ' + inp + ' in / ' + out + ' out';
            // Cache tokens in session total
            const cR = conversationUsage.cache_read_tokens;
            const cW = conversationUsage.cache_write_tokens;
            if (cR > 0 || cW > 0) {{
                let cp = [];
                if (cR > 0) cp.push(_fmtTokens(cR) + ' cache\u2193');
                if (cW > 0) cp.push(_fmtTokens(cW) + ' cache\u2191');
                text += ' (' + cp.join(', ') + ')';
            }}
            if (conversationUsage.cost > 0) {{
                text += ' \u2022 ' + sym + _fmtCost(conversationUsage.cost) + ' total';
            }}
            el.textContent = text;
        }}

        function addMessage(text, role, imageData = null, metadata = null) {{
            const div = document.createElement('div');
            div.className = 'message ' + role;
            if (role === 'assistant') {{
                let content = formatMarkdown(text);
                // Add model badge if metadata is available
                if (metadata && (metadata.model || metadata.provider)) {{
                    const modelBadge = `<div style="font-size: 11px; color: #999; margin-bottom: 6px; opacity: 0.8;">🤖 ${{metadata.provider || 'AI'}} | ${{metadata.model || 'unknown'}}</div>`;
                    content = modelBadge + content;
                }}
                // Append usage info from history
                if (metadata && metadata.usage) {{
                    content += formatUsage(metadata.usage);
                    updateConversationUsage(metadata.usage);
                }}
                div.innerHTML = content;

                // If this assistant message contains a snapshot id, add an undo button
                const snap = extractSnapshotId(text);
                if (snap) {{
                    appendUndoButton(div, snap);
                }}

                // If the assistant is asking to choose an entity_id, provide tap-to-select UI
                injectEntityPicker(div, text);
            }} else {{
                const userText = stripContextInjections(text);
                const rendered = formatUserInputDisplay(userText);
                if (rendered.hasCode) {{
                    div.innerHTML = rendered.html;
                }} else {{
                    div.textContent = userText;
                }}
                const lineCount = userText ? userText.split('\\n').length : 0;
                if (!rendered.hasCode && (lineCount >= 12 || userText.length >= 1200)) {{
                    div.classList.add('long');
                }}
                if (imageData) {{
                    const img = document.createElement('img');
                    img.src = imageData;
                    div.appendChild(img);
                }}
            }}
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
            return div;
        }}

        function formatUserInputDisplay(text) {{
            const src = String(text || '');
            const esc = (s) => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            const fence = /```([a-zA-Z0-9_-]*)\\n([\\s\\S]*?)```/g;
            let out = '';
            let last = 0;
            let hasCode = false;
            let m;
            while ((m = fence.exec(src)) !== null) {{
                hasCode = true;
                const before = src.slice(last, m.index);
                if (before) {{
                    out += '<div class="user-text">' + esc(before).replace(/\\n/g, '<br>') + '</div>';
                }}
                const lang = (m[1] || '').trim().toLowerCase();
                const label = lang || 'code';
                const code = m[2] || '';
                out += '<div class="user-code-block"><div class="user-code-label">' + esc(label) + '</div><pre><code>' + esc(code) + '</code></pre></div>';
                last = fence.lastIndex;
            }}
            const tail = src.slice(last);
            if (tail) {{
                out += '<div class="user-text">' + esc(tail).replace(/\\n/g, '<br>') + '</div>';
            }}
            return {{ hasCode, html: out }};
        }}

        function extractSnapshotId(text) {{
            if (!text || typeof text !== 'string') return '';
            // Matches: "Snapshot creato: `SNAPSHOT_ID`"
            const m = text.match(/Snapshot creato:\\s*`([^`]+)`/i);
            return m ? (m[1] || '').trim() : '';
        }}

        /**
         * Remove technical context injections from user messages before display.
         * These blocks are added by intent.py / chat_bubble.py for AI context but should not
         * be visible to users when viewing past conversation messages.
         *
         * Patterns stripped:
         *   [CURRENT_DASHBOARD_HTML]...[/CURRENT_DASHBOARD_HTML]   (large HTML block)
         *   [CONTEXT: ...(single-line content)...]                  (bracket context tag)
         *   --- CONTEXT: ... ---                                    (separator-style context)
         */
        function stripContextInjections(text) {{
            if (!text || typeof text !== 'string') return text;
            let t = text;
            // 0. Strip [FILE: path]...content...[/FILE] blocks injected by file explorer
            t = t.replace(/\\[FILE:[^\\]]*\\][\\s\\S]*?\\[\\/FILE\\]\\n?/g, '');
            // 1. Strip [CURRENT_DASHBOARD_HTML]...[/CURRENT_DASHBOARD_HTML] (may be very large)
            t = t.replace(/\\[CURRENT_DASHBOARD_HTML\\][\\s\\S]*?\\[\\/CURRENT_DASHBOARD_HTML\\]\\n?/g, '');
            // 2. Strip [CONTEXT: ... ] blocks — handle nested brackets like [TOOL RESULT]
            while (t.indexOf('[CONTEXT:') !== -1) {{
                const idx = t.indexOf('[CONTEXT:');
                let depth = 0, end = t.length - 1;
                for (let i = idx; i < t.length; i++) {{
                    if (t[i] === '[') depth++;
                    else if (t[i] === ']') {{ depth--; if (depth === 0) {{ end = i; break; }} }}
                }}
                let after = end + 1;
                while (after < t.length && (t[after] === ' ' || t[after] === '\\n')) after++;
                t = t.substring(0, idx) + t.substring(after);
            }}
            // 3. Strip --- CONTEXT: ... --- separator sections
            t = t.replace(/---\\s*CONTEXT:[\\s\\S]*?---\\s*/g, '');
            // 4. Clean up excess blank lines left behind
            t = t.replace(/\\n{{3,}}/g, '\\n\\n').trim();
            return t;
        }}

        function appendUndoButton(div, snapshotId) {{
            if (!div || !snapshotId) return;
            if (div.querySelector('.undo-button')) return;

            const btn = document.createElement('button');
            btn.className = 'undo-button';
            btn.textContent = '\u21a9\ufe0e ' + T.restore_backup;
            btn.title = T.restore_backup_title.replace('{{id}}', snapshotId);
            btn.onclick = () => restoreSnapshot(snapshotId, btn);
            div.appendChild(btn);
        }}

        async function restoreSnapshot(snapshotId, btn) {{
            if (!snapshotId) return;
            if (!confirm(T.confirm_restore)) return;

            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = '\u23f3 ' + T.restoring;
            try {{
                const resp = await fetch(apiUrl('api/snapshots/restore'), {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ snapshot_id: snapshotId }})
                }});
                const data = await resp.json().catch(() => ({{}}));
                if (resp.ok && data && data.status === 'success') {{
                    btn.textContent = '\u2713 ' + T.restored;
                    addMessage('\u2705 ' + T.backup_restored, 'system');
                }} else {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    const msg = (data && (data.error || data.message)) ? (data.error || data.message) : T.restore_failed;
                    addMessage('❌ ' + msg, 'system');
                }}
            }} catch (e) {{
                btn.disabled = false;
                btn.textContent = originalText;
                addMessage('\u274c ' + T.error_restore + e.message, 'system');
            }}
        }}

        function formatMarkdown(text) {{
            // 1. Extract raw HTML diff blocks BEFORE any markdown processing
            var diffBlocks = [];
            text = text.replace(/<!--DIFF-->([\\s\\S]*?)<!--\\/DIFF-->/g, function(m, html) {{
                diffBlocks.push(html);
                return '%%DIFF_' + (diffBlocks.length - 1) + '%%';
            }});

            // 1b. Extract <details> blocks before markdown escaping
            var detailsBlocks = [];
            text = text.replace(/<details[^>]*>[\\s\\S]*?<\\/details>/gi, function(m) {{
                var safe = m.replace(/<script[\\s\\S]*?<\\/script>/gi, '')
                            .replace(/\\bon\\w+\\s*=\\s*["'][^"']*["']/gi, '');
                detailsBlocks.push(safe);
                return '%%DETAILS_' + (detailsBlocks.length - 1) + '%%';
            }});

            // 1b. Auto-detect Home Assistant YAML blocks that arrive without ``` fences.
            // Some models return YAML as plain text; wrap the first YAML-looking block
            // so it renders as a code block with the existing copy button.
            if (!text.includes('```')) {{
                let start = -1;
                if (text.startsWith('alias:') || text.startsWith('id:')) {{
                    start = 0;
                }} else {{
                    start = text.indexOf('\\nalias:');
                    if (start >= 0) start += 1;
                    if (start < 0) {{
                        start = text.indexOf('\\nid:');
                        if (start >= 0) start += 1;
                    }}
                }}

                if (start >= 0) {{
                    let end = text.indexOf('\\n\\n', start);
                    if (end < 0) end = text.length;
                    const block = text.slice(start, end).trimEnd();
                    const looksLikeYaml = block.includes('\\ntrigger:') && block.includes('\\naction:');
                    if (looksLikeYaml) {{
                        text = text.slice(0, start) + '```yaml\\n' + block + '\\n```' + text.slice(end);
                    }}
                }}
            }}

            // 2. Code blocks
            text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<div class="code-block"><button class="copy-button" type="button">\U0001F4CB ' + T.copy_btn + '</button><pre><code>$2</code></pre></div>');
            // 3. Inline code, bold, newlines
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            text = text.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
            text = text.replace(/\\n/g, '<br>');
            // 4. Restore diff HTML blocks (untouched by markdown transforms)
            for (var i = 0; i < diffBlocks.length; i++) {{
                text = text.replace('%%DIFF_' + i + '%%', diffBlocks[i]);
            }}
            // 4b. Restore <details> blocks
            for (var i = 0; i < detailsBlocks.length; i++) {{
                text = text.replace('%%DETAILS_' + i + '%%', detailsBlocks[i]);
            }}
            return text;
        }}

        function copyCode(button) {{
            let wrap = null;
            try {{
                wrap = button && button.closest ? button.closest('.code-block') : null;
            }} catch(e) {{}}
            if (!wrap) wrap = button && button.parentElement ? button.parentElement : null;
            const codeElement = wrap ? wrap.querySelector('pre code, code') : null;
            let code = codeElement ? (codeElement.textContent || codeElement.innerText || '') : '';
            if (codeElement && codeElement.innerHTML) {{
                try {{
                    const _tmp = document.createElement('div');
                    _tmp.innerHTML = String(codeElement.innerHTML || '').replace(/<br[^>]*>/gi, '\\n');
                    const _htmlCode = _tmp.textContent || _tmp.innerText || '';
                    if (_htmlCode && _htmlCode.trim()) code = _htmlCode;
                }} catch (_) {{}}
            }}
            if (!code && wrap) {{
                const pre = wrap.querySelector('pre');
                code = pre ? (pre.textContent || pre.innerText || '') : '';
            }}
            code = String(code || '').replace(/\\u00A0/g, ' ').replace(/\\r\\n/g, '\\n').replace(/\\r/g, '\\n');
            if (!code.trim()) {{
                addMessage('⚠️ Nothing to copy from this code block.', 'system');
                return;
            }}

            const showSuccess = () => {{
                const originalText = button.textContent;
                button.textContent = '\u2713 ' + T.copied;
                button.classList.add('copied');
                setTimeout(() => {{
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }}, 2000);
            }};

            // Try multiple clipboard contexts (iframe/HA shell can differ).
            const clipboards = [];
            if (navigator && navigator.clipboard && navigator.clipboard.writeText) clipboards.push(navigator.clipboard);
            try {{
                if (window.parent && window.parent.navigator && window.parent.navigator.clipboard && window.parent.navigator.clipboard.writeText) {{
                    clipboards.push(window.parent.navigator.clipboard);
                }}
            }} catch(e) {{}}
            try {{
                if (window.top && window.top.navigator && window.top.navigator.clipboard && window.top.navigator.clipboard.writeText) {{
                    clipboards.push(window.top.navigator.clipboard);
                }}
            }} catch(e) {{}}

            const tryNextClipboard = (idx) => {{
                if (idx >= clipboards.length) {{
                    // Final fallback for HTTP / restricted webviews
                    const ok = fallbackCopy(code, showSuccess);
                    if (!ok) {{
                        addMessage('⚠️ Copy failed in this browser context. Try selecting the code manually.', 'system');
                    }}
                    return;
                }}
                clipboards[idx].writeText(code).then(showSuccess).catch(() => tryNextClipboard(idx + 1));
            }};
            tryNextClipboard(0);
        }}

        function fallbackCopy(text, callback) {{
            function fallbackWithDoc(doc) {{
                try {{
                    if (!doc || !doc.body) return false;
                    const textarea = doc.createElement('textarea');
                    textarea.value = text;
                    textarea.style.position = 'fixed';
                    textarea.style.opacity = '0';
                    textarea.style.left = '-9999px';
                    textarea.style.top = '-9999px';
                    textarea.setAttribute('readonly', '');
                    doc.body.appendChild(textarea);
                    textarea.focus();
                    textarea.select();
                    if (textarea.setSelectionRange) textarea.setSelectionRange(0, textarea.value.length);
                    let ok = false;
                    try {{ ok = !!doc.execCommand('copy'); }} catch(_) {{ ok = false; }}
                    doc.body.removeChild(textarea);
                    return ok;
                }} catch (_) {{
                    return false;
                }}
            }}

            if (fallbackWithDoc(document)) {{
                callback();
                return true;
            }}
            try {{
                if (window.parent && window.parent.document && fallbackWithDoc(window.parent.document)) {{
                    callback();
                    return true;
                }}
            }} catch (_) {{}}
            try {{
                if (window.top && window.top.document && fallbackWithDoc(window.top.document)) {{
                    callback();
                    return true;
                }}
            }} catch (_) {{}}
            return false;
        }}

        function showThinking() {{
            const div = document.createElement('div');
            div.className = 'message thinking';
            div.id = 'thinking';
            div.innerHTML = getAnalyzingMsg() + ' <span class="thinking-elapsed" id="thinkingElapsed"></span><span class="dots"><span>.</span><span>.</span><span>.</span></span>'
                + '<div class="thinking-steps" id="thinkingSteps"></div>';
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}

        let _thinkingStart = 0;
        let _thinkingTimer = null;
        let _thinkingBaseText = '';
        let _thinkingSteps = [];

        function addThinkingStep(stepText) {{
            const t = String(stepText || '').trim();
            if (!t) return;
            // Deduplicate consecutive identical steps
            const last = _thinkingSteps.length ? _thinkingSteps[_thinkingSteps.length - 1] : '';
            if (t === last) return;
            _thinkingSteps.push(t);
            // Keep last 4 steps to avoid clutter
            if (_thinkingSteps.length > 4) _thinkingSteps = _thinkingSteps.slice(-4);
            const stepsEl = document.getElementById('thinkingSteps');
            if (!stepsEl) return;
            stepsEl.innerHTML = _thinkingSteps.map(s => '<div>• ' + s.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>').join('');
        }}

        function _formatElapsed(ms) {{
            const s = Math.max(0, Math.floor(ms / 1000));
            const m = Math.floor(s / 60);
            const r = s % 60;
            return m > 0 ? (m + ':' + String(r).padStart(2, '0')) : (r + 's');
        }}

        function startThinkingTicker(baseText) {{
            _thinkingStart = Date.now();
            _thinkingBaseText = baseText || getAnalyzingMsg();
            _thinkingSteps = [];

            const el = document.getElementById('thinking');
            if (el) {{
                // Ensure base text is visible in case showThinking wasn't called yet
                if (!el.innerHTML || !el.innerHTML.trim()) {{
                    el.innerHTML = _thinkingBaseText + ' <span class="thinking-elapsed" id="thinkingElapsed"></span><span class="dots"><span>.</span><span>.</span><span>.</span></span>'
                        + '<div class="thinking-steps" id="thinkingSteps"></div>';
                }}
            }}

            stopThinkingTicker();
            _thinkingTimer = setInterval(() => {{
                const elapsedEl = document.getElementById('thinkingElapsed');
                if (!elapsedEl) return;
                elapsedEl.textContent = '(' + _formatElapsed(Date.now() - _thinkingStart) + ')';
            }}, 1000);
        }}

        function updateThinkingBaseText(text) {{
            _thinkingBaseText = text || _thinkingBaseText || getAnalyzingMsg();
            const el = document.getElementById('thinking');
            if (!el) return;
            const safe = String(_thinkingBaseText);
            el.innerHTML = safe + ' <span class="thinking-elapsed" id="thinkingElapsed"></span><span class="dots"><span>.</span><span>.</span><span>.</span></span>'
                + '<div class="thinking-steps" id="thinkingSteps"></div>';
            // Re-render steps after rewriting innerHTML
            if (_thinkingSteps && _thinkingSteps.length) {{
                const stepsEl = document.getElementById('thinkingSteps');
                if (stepsEl) stepsEl.innerHTML = _thinkingSteps.map(s => '<div>• ' + s.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>').join('');
            }}
        }}

        function stopThinkingTicker() {{
            if (_thinkingTimer) {{
                clearInterval(_thinkingTimer);
                _thinkingTimer = null;
            }}
        }}

        function removeThinking() {{
            const el = document.getElementById('thinking');
            if (el) el.remove();
            stopThinkingTicker();
            _thinkingSteps = [];
        }}

        function sendSuggestion(el) {{
            input.value = el.textContent.replace(/^.{{2}}/, '').trim();
            sendMessage();
        }}

        async function sendMessage() {{
            const text = (input && input.value ? input.value : '').trim();
            const hasDoc = !!pendingDocument;
            if ((!text && !hasDoc) || sending) return;

            sending = true;
            setStopMode(true);

            // Capture pending document before clearing
            const docToSend = pendingDocument;
            pendingDocument = null;

            try {{
                if (input) {{
                    input.value = '';
                    input.style.height = 'auto';
                }}
                if (suggestionsEl && suggestionsEl.style) {{
                    suggestionsEl.style.display = 'none';
                }}

                // Upload document if attached
                let docUploaded = false;
                if (docToSend) {{
                    removeDocument();
                    const docLabel = `📎 ${{docToSend.name}}`;
                    const displayText = text ? `${{text}}\n\n${{docLabel}}` : docLabel;
                    const imageToSendDoc = currentImage;
                    addMessage(displayText, 'user', imageToSendDoc);
                    showThinking();
                    startThinkingTicker(getAnalyzingMsg());
                    addThinkingStep(`📤 ${{T.uploading_document || 'Uploading document...'}}`);
                    try {{
                        const formData = new FormData();
                        formData.append('file', docToSend);
                        formData.append('note', `Uploaded: ${{new Date().toLocaleString()}}`);
                        const upResp = await fetch(apiUrl('/api/documents/upload'), {{
                            method: 'POST',
                            body: formData
                        }});
                        if (upResp.ok) {{
                            docUploaded = true;
                        }} else {{
                            const err = await upResp.json().catch(() => ({{}}));
                            addMessage(`❌ ${{T.upload_failed || 'Upload failed'}}: ${{err.error || T.unknown_error || 'Unknown error'}}`, 'system');
                            sending = false;
                            setStopMode(false);
                            removeThinking();
                            return;
                        }}
                    }} catch (upErr) {{
                        addMessage(`❌ ${{T.upload_error || 'Upload error'}}: ${{upErr.message}}`, 'system');
                        sending = false;
                        setStopMode(false);
                        removeThinking();
                        return;
                    }}
                }}

                // Show user message with image if present (only if no doc already shown)
                const imageToSend = currentImage;
                if (!docToSend) {{
                    addMessage(text, 'user', imageToSend);
                    showThinking();
                    startThinkingTicker(getAnalyzingMsg());
                }}
                // Clear the preview immediately (keep imageToSend for the request payload)
                removeImage();
                addThinkingStep(T.sending_request || 'Sending request');

                // If the backend is retrying (e.g., 429) and no status/tool events are sent,
                // add a small fallback step so the UI doesn't look "stuck".
                setTimeout(() => {{
                    try {{
                        if (sending && document.getElementById('thinking')) {{
                            addThinkingStep(T.waiting_response || 'Waiting for response');
                        }}
                    }} catch (e) {{}}
                }}, 8000);

                // Prepend file context blocks if any files are open
                const fileCtx = buildFileContext();
                const _baseMsg = text || `[${{T.document_uploaded || 'Document uploaded'}}: ${{docToSend ? docToSend.name : ''}}]`;
                const payload = {{
                    message: fileCtx ? fileCtx + '\\n\\n' + _baseMsg : _baseMsg,
                    session_id: currentSessionId,
                    read_only: readOnlyMode,
                    voice_mode: !!voiceModeActive
                }};
                if (imageToSend) {{
                    payload.image = imageToSend;
                }}

                const resp = await fetch(apiUrl('api/chat/stream'), {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});

                if (!resp.ok) {{
                    const bodyText = await resp.text().catch(() => '');
                    let errMsg = '';
                    if (resp.status === 429) {{
                        errMsg = T.rate_limit_error || 'Rate limit exceeded. Please wait a moment before trying again.';
                    }} else {{
                        errMsg = T.request_failed.replace('{{status}}', resp.status).replace('{{body}}', bodyText ? bodyText.slice(0, 100) : '');
                    }}
                    throw new Error(errMsg);
                }}

                const contentType = (resp.headers.get('content-type') || '').toLowerCase();
                if (contentType.includes('text/event-stream')) {{
                    await handleStream(resp);
                }} else {{
                    const data = await resp.json().catch(() => ({{}}));
                    if (data && data.response) {{
                        addMessage(data.response, 'assistant');
                    }} else if (data && data.error) {{
                        addMessage('\u274c ' + data.error, 'system');
                    }} else {{
                        addMessage('\u274c ' + T.unexpected_response, 'system');
                    }}
                }}
            }} catch (err) {{
                removeThinking();
                if (err && err.name !== 'AbortError') {{
                    addMessage('\u274c ' + T.error_prefix + (err.message || String(err)), 'system');
                }}
            }} finally {{
                sending = false;
                setStopMode(false);
                if (sendBtn) sendBtn.disabled = false;
                currentReader = null;
                loadChatList();
                if (input) input.focus();
            }}
        }}

        async function handleStream(resp) {{
            const reader = resp.body.getReader();
            currentReader = reader;
            const decoder = new TextDecoder();
            let div = null;
            let fullText = '';
            let buffer = '';
            let hasTools = false;
            let gotAnyEvent = false;
            let gotAnyToken = false;
            let pendingSteps = null;
            let shouldStop = false;
            addThinkingStep(T.connected || 'Connected');
            try {{
            while (true) {{
                const {{ done, value }} = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, {{ stream: true }});
                while (buffer.includes('\\n\\n')) {{
                    const idx = buffer.indexOf('\\n\\n');
                    const chunk = buffer.substring(0, idx);
                    buffer = buffer.substring(idx + 2);
                    for (const line of chunk.split('\\n')) {{
                        if (!line.startsWith('data: ')) continue;
                        try {{
                            const evt = JSON.parse(line.slice(6));
                            gotAnyEvent = true;
                            if (evt.type === 'tool' || evt.type === 'tool_call') {{
                                // Show tool progress in the thinking bubble (no assistant message yet)
                                const desc = evt.description || evt.name;
                                updateThinkingBaseText('\U0001f527 ' + desc);
                                addThinkingStep(desc);
                            }} else if (evt.type === 'clear') {{
                                // Keep thinking visible; reset streamed text state
                                if (div) {{ div.innerHTML = ''; }}
                                fullText = '';
                                hasTools = false;
                            }} else if (evt.type === 'status') {{
                                // Update thinking bubble with current status and keep timer running
                                const msg = evt.message || evt.content || evt.status || evt.text || '';
                                updateThinkingBaseText('\u23f3 ' + msg);
                                addThinkingStep(msg);
                            }} else if (evt.type === 'fallback_notice') {{
                                // Provider fallback notification — show system message
                                const origProv = (PROVIDER_LABELS[evt.original_provider] || evt.original_provider || '?');
                                const actualProv = (PROVIDER_LABELS[evt.actual_provider] || evt.actual_provider || '?');
                                addMessage('\u26A0\uFE0F ' + (T.fallback_notice || 'Fallback: {{from}} \u2192 {{to}}').replace('{{from}}', origProv).replace('{{to}}', actualProv), 'system');
                            }} else if (evt.type === 'token') {{
                                if (!gotAnyToken) {{
                                    gotAnyToken = true;
                                    try {{
                                        pendingSteps = (_thinkingSteps && _thinkingSteps.length) ? _thinkingSteps.slice(0) : null;
                                    }} catch (e) {{ pendingSteps = null; }}
                                    removeThinking();
                                }}
                                if (hasTools && div) {{ div.innerHTML = ''; fullText = ''; hasTools = false; }}
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                fullText += evt.content;
                                const prefix = (pendingSteps && pendingSteps.length)
                                    ? ('<div class="progress-steps">' + renderStepLines(pendingSteps) + '</div>')
                                    : '';
                                div.innerHTML = prefix + formatMarkdown(fullText);
                            }} else if (evt.type === 'diff') {{
                                // Show colored diff block in the assistant message div
                                if (div && evt.content) {{
                                    const diffEl = renderDiff(evt.content);
                                    if (diffEl) div.appendChild(diffEl);
                                }}
                                // If the modified file is currently open in the file panel, reload it
                                if (evt.file && fileOpenTabs.length > 0) {{
                                    const tabIdx = fileOpenTabs.findIndex(t => t.path === evt.file);
                                    if (tabIdx !== -1) {{
                                        const tab = fileOpenTabs[tabIdx];
                                        tab.loading = true; tab.content = null; tab.offset = 0; tab.hasMore = false;
                                        if (tabIdx === fileActiveTabIdx) renderActivePanelContent();
                                        fetch(apiUrl('api/files/read') + '?file=' + encodeURIComponent(evt.file) + '&chunk=40000', {{credentials:'same-origin'}})
                                            .then(r => r.json())
                                            .then(data => {{
                                                if (data.error) {{ tab.error = data.error; }} else {{
                                                    tab.content = data.content; tab.error = null;
                                                    tab.offset = data.chunk_size || data.content.length;
                                                    tab.hasMore = data.has_more || false;
                                                    tab.size = data.size || 0;
                                                }}
                                                tab.loading = false;
                                                if (tabIdx === fileActiveTabIdx) renderActivePanelContent();
                                            }})
                                            .catch(e => {{ tab.error = e.message; tab.loading = false;
                                                if (tabIdx === fileActiveTabIdx) renderActivePanelContent(); }});
                                    }}
                                }}
                            }} else if (evt.type === 'diff_html') {{
                                // Formatted write-tool response with side-by-side diff view
                                if (!gotAnyToken) {{
                                    gotAnyToken = true;
                                    try {{
                                        pendingSteps = (_thinkingSteps && _thinkingSteps.length) ? _thinkingSteps.slice(0) : null;
                                    }} catch (e) {{ pendingSteps = null; }}
                                    removeThinking();
                                }}
                                hasTools = false;
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                fullText += evt.content + '\\n\\n';
                                const prefix = (pendingSteps && pendingSteps.length)
                                    ? ('<div class="progress-steps">' + renderStepLines(pendingSteps) + '</div>')
                                    : '';
                                div.innerHTML = prefix + formatMarkdown(fullText);
                            }} else if (evt.type === 'error') {{
                                removeThinking();
                                addMessage('\u274c ' + evt.message, 'system');
                                // If web session expired server-side, refresh banner immediately
                                if (currentProviderId === 'chatgpt_web') checkChatGPTWebSession();
                                else if (currentProviderId === 'claude_web') checkClaudeWebSession();
                                else if (currentProviderId === 'gemini_web') checkGeminiWebSession();
                            }} else if (evt.type === 'done') {{
                                removeThinking();

                                // After streaming completes, attach undo button if snapshot id is present
                                if (div && fullText) {{
                                    const snap = extractSnapshotId(fullText);
                                    if (snap) {{
                                        appendUndoButton(div, snap);
                                    }}
                                    // Inject YES/NO confirmation buttons if AI is asking for confirmation
                                    injectConfirmButtons(div, fullText);
                                    // Inject entity picker UI if AI is asking the user to pick an entity
                                    injectEntityPicker(div, fullText);
                                }}
                                // Append token usage info
                                if (div && evt.usage) {{
                                    const usageHtml = formatUsage(evt.usage);
                                    if (usageHtml) {{
                                        div.insertAdjacentHTML('beforeend', usageHtml);
                                    }}
                                    updateConversationUsage(evt.usage);
                                }}
                                // TTS: read response aloud if voice mode is active
                                if (voiceModeActive && fullText) {{
                                    playTTSResponse(fullText);
                                }}
                                shouldStop = true;
                                try {{ reader.cancel(); }} catch (e) {{}}
                            }}
                            chat.scrollTop = chat.scrollHeight;
                        }} catch(e) {{}}
                    }}
                    if (shouldStop) break;
                }}
                if (shouldStop) break;
            }}
            }} catch(streamErr) {{
                if (streamErr.name !== 'AbortError') {{
                    console.error('Stream error:', streamErr);
                }}
            }}
            removeThinking();
            if (!gotAnyEvent) {{
                addMessage('\u274c ' + T.connection_lost, 'system');
            }}
        }}

        // ---- Sidebar tab management ----
        function switchSidebarTab(tabName) {{
            document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.sidebar-content').forEach(c => c.classList.remove('active'));
            document.querySelector(`.sidebar-tab[data-tab="${{tabName}}"]`)?.classList.add('active');
            if (tabName === 'chat') {{
                document.getElementById('tabChat').classList.add('active');
                loadChatList();
            }} else if (tabName === 'bubble') {{
                document.getElementById('tabBubble').classList.add('active');
                loadBubbleList();
            }} else if (tabName === 'amira') {{
                document.getElementById('tabAmira').classList.add('active');
                loadAmiraList();
            }} else if (tabName === 'backups') {{
                document.getElementById('tabBackups').classList.add('active');
                loadBackupList();
            }} else if (tabName === 'devices') {{
                document.getElementById('tabDevices').classList.add('active');
                loadDeviceList();
            }} else if (tabName === 'messaging') {{
                document.getElementById('tabMessaging').classList.add('active');
                loadMessagingList();
            }} else if (tabName === 'files') {{
                document.getElementById('tabFiles').classList.add('active');
                loadFileTree(fileCurrentPath);
            }} else if (tabName === 'costs') {{
                document.getElementById('tabCosts').classList.add('active');
                loadCostsPanel();
            }} else if (tabName === 'skills') {{
                document.getElementById('tabSkills').classList.add('active');
                loadSkillsPanel();
            }} else if (tabName === 'config') {{
                document.getElementById('tabConfig').classList.add('active');
                loadConfigList();
            }}
        }}

        async function mcpInstallPkgs() {{
            const input = document.getElementById('mcpPipInput');
            const btn   = document.getElementById('mcpPipBtn');
            const log   = document.getElementById('mcpPipLog');
            if (!input || !log) return;
            const pkgs = input.value.split('\\n').map(s => s.trim()).filter(Boolean);
            if (!pkgs.length) {{ log.style.display = 'block'; log.textContent = '⚠ ' + (T.mcp_no_packages || 'No packages specified.'); return; }}
            log.style.display = 'block';
            log.textContent = '⏳ ' + (T.mcp_installing || 'Installing...');
            if (btn) btn.disabled = true;
            try {{
                const resp = await fetch(apiUrl('api/mcp/install'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{packages: pkgs}})
                }});
                const data = await resp.json();
                log.textContent = data.output || (resp.ok ? ('✔ ' + (T.mcp_done || 'Done.')) : ('❌ ' + (T.mcp_error || 'Error.')));
            }} catch(e) {{
                log.textContent = '❌ ' + e.message;
            }} finally {{
                if (btn) btn.disabled = false;
            }}
        }}

        // ---- Skills panel ----
        let _installedSkills = [];

        function _semverGt(a, b) {{
            const pa = String(a || '0').split('.').map(Number);
            const pb = String(b || '0').split('.').map(Number);
            for (let i = 0; i < Math.max(pa.length, pb.length); i++) {{
                const x = pa[i] || 0, y = pb[i] || 0;
                if (x > y) return true;
                if (x < y) return false;
            }}
            return false;
        }}

        async function checkSkillsUpdatesOnLoad() {{
            try {{
                const [instResp, storeResp] = await Promise.all([
                    fetch(apiUrl('api/skills')),
                    fetch(apiUrl('api/skills/store'))
                ]);
                if (!instResp.ok || !storeResp.ok) return;
                const installed = (await instResp.json()).skills || [];
                const store     = (await storeResp.json()).skills || [];
                if (!installed.length || !store.length) return;
                const instMap = new Map(installed.map(s => [s.name, s.version || '0']));
                const updates = store.filter(s => instMap.has(s.name) && _semverGt(s.version || '0', instMap.get(s.name)));
                if (updates.length > 0) {{
                    const banner = document.getElementById('skillsUpdateBanner');
                    const text   = document.getElementById('skillsUpdateText');
                    if (banner && text) {{
                        text.textContent = (T.skills_update_banner || 'Skill update available:') + ' ' + updates.map(s => '/' + s.name + ' v' + s.version).join(', ');
                        banner.style.display = 'flex';
                    }}
                }}
            }} catch(e) {{}}
        }}

        async function loadSkillsPanel() {{
            const panel = document.getElementById('skillsPanel');
            if (!panel) return;
            panel.innerHTML = '<div style="padding:16px;text-align:center;color:#999;">' + (T.skills_store_loading || 'Loading...') + '</div>';
            try {{
                const [instResp, storeResp] = await Promise.all([
                    fetch(apiUrl('api/skills')),
                    fetch(apiUrl('api/skills/store'))
                ]);
                const instData  = instResp.ok  ? await instResp.json()  : {{}};
                const storeData = storeResp.ok ? await storeResp.json() : {{}};
                const installed = instData.skills  || [];
                const store     = storeData.skills || [];
                _installedSkills = installed;
                const instNames      = new Set(installed.map(s => s.name));
                const instVersionMap = new Map(installed.map(s => [s.name, s.version || '0']));

                const lang = '{ui_lang}';
                function _sdesc(s) {{
                    if (s.description && typeof s.description === 'object') {{
                        return s.description[lang] || s.description['en'] || '';
                    }}
                    return s.description || '';
                }}

                // ---- installed section ----
                let html = '<div style="font-size:12px;color:#888;margin-bottom:6px;">' + (T.skills_hint || '') + '</div>';
                html += '<div style="font-weight:600;font-size:13px;margin-bottom:8px;color:#444;">📦 ' + (T.skills_installed || 'Installed') + '</div>';
                if (installed.length === 0) {{
                    html += '<div style="color:#999;font-size:12px;margin-bottom:12px;">' + (T.skills_empty || 'No skills installed.') + '</div>';
                }} else {{
                    installed.forEach(s => {{
                        html += `<div style="background:#f0f4ff;border-radius:8px;padding:9px 11px;margin-bottom:7px;">
                            <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;">
                                <div>
                                    <span style="font-weight:600;font-size:13px;">/${{s.name}}</span>
                                    <span style="font-size:11px;color:#888;margin-left:6px;">v${{s.version || ''}}</span>
                                    ${{s.author ? '<span style="font-size:11px;color:#aaa;margin-left:4px;">' + (T.skills_by||'by') + ' ' + s.author + '</span>' : ''}}
                                </div>
                                <button class="sak-del-btn" data-name="${{s.name}}" style="background:#fee2e2;color:#991b1b;border:none;border-radius:5px;padding:3px 9px;font-size:11px;cursor:pointer;">${{T.skills_delete_btn||'Remove'}}</button>
                            </div>
                            <div style="font-size:12px;color:#555;margin-top:4px;">${{_sdesc(s)}}</div>
                            ${{(s.tags||[]).map(t=>`<span style="background:#e8f0fe;color:#1a73e8;border-radius:4px;padding:1px 5px;font-size:10px;margin-right:3px;">${{t}}</span>`).join('')}}
                        </div>`;
                    }});
                }}

                // ---- store section ----
                html += '<div style="display:flex;align-items:center;justify-content:space-between;margin:14px 0 8px;">';
                html += '<div style="font-weight:600;font-size:13px;color:#444;">🏪 ' + (T.skills_store||'Store') + '</div>';
                html += '<button onclick="loadSkillsPanel()" style="background:#f0f0f0;border:none;border-radius:5px;padding:3px 9px;font-size:11px;cursor:pointer;">' + (T.skills_refresh||'Refresh') + '</button>';
                html += '</div>';

                if (storeData.error === 'skills_unavailable') {{
                    html += '<div style="color:#888;font-size:12px;">' + (T.skills_unavailable||'Skills not available. Restart the add-on to activate.') + '</div>';
                }} else if (storeData.error && store.length === 0) {{
                    html += '<div style="color:#c62828;font-size:12px;">' + (T.skills_store_error||'Could not load store.') + '</div>';
                    html += '<div style="color:#999;font-size:11px;margin-top:4px;font-family:monospace;">' + (storeData.error||'') + '</div>';
                }} else if (store.length === 0) {{
                    html += '<div style="color:#999;font-size:12px;">' + (T.skills_store_empty||'No skills available.') + '</div>';
                }} else {{
                    const storeVisible = store.filter(s => {{
                        const isInst = instNames.has(s.name);
                        const hasUpd = isInst && _semverGt(s.version || '0', instVersionMap.get(s.name) || '0');
                        return !isInst || hasUpd;
                    }});
                    if (storeVisible.length === 0) {{
                        html += '<div style="color:#999;font-size:12px;">' + (T.skills_store_empty||'No new skills available.') + '</div>';
                    }} else {{
                        storeVisible.forEach(s => {{
                            const isInst   = instNames.has(s.name);
                            const hasUpd   = isInst && _semverGt(s.version || '0', instVersionMap.get(s.name) || '0');
                            const actionEl = hasUpd
                                ? `<button class="sak-inst-btn" data-name="${{s.name}}" data-url="${{s.raw_url||''}}" style="background:#ff9800;color:#fff;border:none;border-radius:5px;padding:3px 9px;font-size:11px;cursor:pointer;">⬆ ${{T.skills_update_btn||'Update'}}</button>`
                                : `<button class="sak-inst-btn" data-name="${{s.name}}" data-url="${{s.raw_url||''}}" style="background:#4caf50;color:#fff;border:none;border-radius:5px;padding:3px 9px;font-size:11px;cursor:pointer;">${{T.skills_install_btn||'Install'}}</button>`;
                            html += `<div style="background:#fafafa;border:1px solid ${{hasUpd?'#ffe082':'#e8e8e8'}};border-radius:8px;padding:9px 11px;margin-bottom:7px;">
                                <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;">
                                    <div>
                                        <span style="font-weight:600;font-size:13px;">/${{s.name}}</span>
                                        <span style="font-size:11px;color:#888;margin-left:6px;">v${{s.version||''}}</span>
                                        ${{hasUpd ? `<span style="font-size:10px;color:#e65100;margin-left:4px;">(v${{instVersionMap.get(s.name)}} → v${{s.version}})</span>` : ''}}
                                        ${{s.author ? '<span style="font-size:11px;color:#aaa;margin-left:4px;">' + (T.skills_by||'by') + ' ' + s.author + '</span>' : ''}}
                                    </div>
                                    ${{actionEl}}
                                </div>
                                <div style="font-size:12px;color:#555;margin-top:4px;">${{_sdesc(s)}}</div>
                                ${{(s.tags||[]).map(t=>`<span style="background:#e8f0fe;color:#1a73e8;border-radius:4px;padding:1px 5px;font-size:10px;margin-right:3px;">${{t}}</span>`).join('')}}
                            </div>`;
                        }});
                    }}
                }}
                panel.innerHTML = html;
                panel.querySelectorAll('.sak-del-btn').forEach(btn => {{
                    btn.onclick = () => deleteSkill(btn.dataset.name);
                }});
                panel.querySelectorAll('.sak-inst-btn').forEach(btn => {{
                    btn.onclick = () => installSkill(btn.dataset.name, btn.dataset.url);
                }});
            }} catch(e) {{
                panel.innerHTML = '<div style="color:#c62828;padding:12px;">' + (T.skills_store_error||'Error loading skills.') + '</div>';
            }}
        }}

        async function installSkill(name, rawUrl) {{
            try {{
                const resp = await fetch(apiUrl('api/skills/install'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{name, raw_url: rawUrl}})
                }});
                const data = await resp.json();
                if (data.success) {{
                    await loadSkillsPanel();
                }} else {{
                    alert('❌ ' + (data.error || 'Install failed'));
                }}
            }} catch(e) {{
                alert('❌ ' + e.message);
            }}
        }}

        async function deleteSkill(name) {{
            if (!confirm((T.skills_delete_confirm||'Remove this skill?') + ' /' + name)) return;
            try {{
                const resp = await fetch(apiUrl('api/skills/' + encodeURIComponent(name)), {{method: 'DELETE'}});
                if (resp.ok) {{
                    await loadSkillsPanel();
                }} else {{
                    const data = await resp.json();
                    alert('❌ ' + (data.error || 'Delete failed'));
                }}
            }} catch(e) {{
                alert('❌ ' + e.message);
            }}
        }}

        // ---- Skills autocomplete ----
        (function() {{
            const textarea = document.getElementById('input');
            if (!textarea) return;

            const dropdown = document.createElement('div');
            dropdown.id = 'skillsAutocomplete';
            dropdown.style.cssText = 'display:none;position:absolute;bottom:100%;left:0;right:0;background:#fff;border:1px solid #e0e0e0;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.12);z-index:1000;max-height:220px;overflow-y:auto;margin-bottom:4px;';
            textarea.parentElement.style.position = 'relative';
            textarea.parentElement.appendChild(dropdown);

            let _acIdx = -1;
            let _acItems = [];

            function _renderDropdown(matches) {{
                _acItems = matches;
                _acIdx = -1;
                if (!matches.length) {{ dropdown.style.display = 'none'; return; }}
                dropdown.innerHTML = matches.map((s, i) => {{
                    const lang = '{ui_lang}';
                    const desc = (s.description && typeof s.description === 'object')
                        ? (s.description[lang] || s.description['en'] || '')
                        : (s.description || '');
                    return `<div class="skill-ac-item" data-idx="${{i}}" style="padding:8px 12px;cursor:pointer;border-bottom:1px solid #f0f0f0;">
                        <span style="font-weight:600;color:#667eea;">/${{s.name}}</span>
                        <span style="font-size:11px;color:#888;margin-left:6px;">${{desc}}</span>
                    </div>`;
                }}).join('');
                dropdown.querySelectorAll('.skill-ac-item').forEach(el => {{
                    el.addEventListener('mousedown', e => {{
                        e.preventDefault();
                        const idx = parseInt(el.dataset.idx);
                        _applyItem(idx);
                    }});
                    el.addEventListener('mouseenter', () => {{
                        _acIdx = parseInt(el.dataset.idx);
                        _highlight();
                    }});
                }});
                dropdown.style.display = 'block';
            }}

            function _highlight() {{
                dropdown.querySelectorAll('.skill-ac-item').forEach((el, i) => {{
                    el.style.background = i === _acIdx ? '#f0f4ff' : '';
                }});
            }}

            function _applyItem(idx) {{
                if (idx < 0 || idx >= _acItems.length) return;
                textarea.value = '/' + _acItems[idx].name + ' ';
                dropdown.style.display = 'none';
                textarea.focus();
                // Move cursor to end
                textarea.selectionStart = textarea.selectionEnd = textarea.value.length;
            }}

            textarea.addEventListener('input', function() {{
                const val = textarea.value;
                if (!val.startsWith('/') || val.includes(' ')) {{ dropdown.style.display = 'none'; return; }}
                const partial = val.slice(1).toLowerCase();
                const matches = _installedSkills.filter(s => s.name.startsWith(partial));
                _renderDropdown(matches);
            }});

            textarea.addEventListener('keydown', function(e) {{
                if (dropdown.style.display === 'none') return;
                if (e.key === 'ArrowDown') {{
                    e.preventDefault();
                    _acIdx = Math.min(_acIdx + 1, _acItems.length - 1);
                    _highlight();
                }} else if (e.key === 'ArrowUp') {{
                    e.preventDefault();
                    _acIdx = Math.max(_acIdx - 1, 0);
                    _highlight();
                }} else if (e.key === 'Tab' || (e.key === 'Enter' && _acIdx >= 0)) {{
                    if (_acIdx >= 0) {{
                        e.preventDefault();
                        _applyItem(_acIdx);
                    }}
                }} else if (e.key === 'Escape') {{
                    dropdown.style.display = 'none';
                }}
            }});

            document.addEventListener('click', function(e) {{
                if (!dropdown.contains(e.target) && e.target !== textarea) {{
                    dropdown.style.display = 'none';
                }}
            }});
        }})();

        async function loadCostsPanel() {{
            const panel = document.getElementById('costsPanel');
            if (!panel) return;
            panel.innerHTML = '<div style="padding:16px;text-align:center;color:#999;">' + T.files_loading + '</div>';
            try {{
                const resp = await fetch(apiUrl('api/usage_stats?days=35'));
                if (!resp.ok) throw new Error(resp.statusText);
                const data = await resp.json();
                const sym = _currSym(COST_CURRENCY);
                let html = '';

                // daily is an array of {{date, input_tokens, output_tokens, total_cost, requests, ...}}
                const dailyArr = Array.isArray(data.daily) ? data.daily : [];
                // Find today's entry from the daily array
                const todayStr = new Date().toISOString().slice(0, 10);
                const todayEntry = dailyArr.find(d => d.date === todayStr) || {{}};
                const todayTokensIn = todayEntry.input_tokens || 0;
                const todayTokensOut = todayEntry.output_tokens || 0;
                const todayCost = todayEntry.total_cost || 0;
                const todayReqs = todayEntry.requests || 0;

                // Today card
                html += '<div class="cost-card">';
                html += '<div class="cost-card-title">' + T.costs_today + '</div>';
                if (todayCost > 0) {{
                    html += '<div class="cost-card-value">' + sym + _fmtCost(todayCost) + '</div>';
                }} else {{
                    html += '<div class="cost-card-value" style="font-size:16px;color:#999;">—</div>';
                }}
                html += '<div class="cost-card-sub">' + _fmtTokens(todayTokensIn) + ' in / ' + _fmtTokens(todayTokensOut) + ' out';
                if (todayReqs > 0) html += ' &middot; ' + todayReqs + ' ' + T.costs_requests;
                html += '</div></div>';

                // By model
                const byModel = data.by_model || {{}};
                const modelEntries = Object.entries(byModel).sort((a,b) => (b[1].total_cost||0) - (a[1].total_cost||0));
                if (modelEntries.length > 0) {{
                    html += '<div class="cost-section">';
                    html += '<div class="cost-section-title">' + T.costs_by_model + '</div>';
                    for (const [model, stats] of modelEntries) {{
                        const mc = stats.total_cost || 0;
                        html += '<div class="cost-row">';
                        html += '<div class="cost-row-name" title="' + model + '">' + model.split('/').pop() + '</div>';
                        html += '<div class="cost-row-value">' + (mc > 0 ? sym + _fmtCost(mc) : 'free') + '</div>';
                        html += '</div>';
                    }}
                    html += '</div>';
                }}

                // By provider
                const byProvider = data.by_provider || {{}};
                const provEntries = Object.entries(byProvider).sort((a,b) => (b[1].total_cost||0) - (a[1].total_cost||0));
                if (provEntries.length > 0) {{
                    html += '<div class="cost-section">';
                    html += '<div class="cost-section-title">' + T.costs_by_provider + '</div>';
                    for (const [prov, stats] of provEntries) {{
                        const pc = stats.total_cost || 0;
                        const pr = stats.requests || 0;
                        html += '<div class="cost-row">';
                        html += '<div class="cost-row-name">' + prov + '</div>';
                        html += '<div class="cost-row-value">' + (pc > 0 ? sym + _fmtCost(pc) : 'free') + ' &middot; ' + pr + ' ' + T.costs_requests + '</div>';
                        html += '</div>';
                    }}
                    html += '</div>';
                }}

                // History — grouped by month, collapsible; current month open by default
                if (dailyArr.length > 0) {{
                    const currentMonth = todayStr.slice(0, 7);
                    // Group days by YYYY-MM
                    const byMonth = {{}};
                    for (const d of dailyArr) {{
                        const m = (d.date || '').slice(0, 7);
                        if (!m) continue;
                        if (!byMonth[m]) byMonth[m] = {{ days: [], total: 0 }};
                        byMonth[m].days.push(d);
                        byMonth[m].total += d.total_cost || 0;
                    }}
                    const sortedMonths = Object.keys(byMonth).sort().reverse();
                    html += '<div class="cost-section">';
                    html += '<div class="cost-section-title">' + T.costs_history + '</div>';
                    for (const month of sortedMonths) {{
                        const mg = byMonth[month];
                        const isOpen = month === currentMonth;
                        const [yr, mo] = month.split('-');
                        const monthLabel = new Date(+yr, +mo - 1, 1).toLocaleString(undefined, {{ month: 'long', year: 'numeric' }});
                        html += '<details class="cost-month-group"' + (isOpen ? ' open' : '') + '>';
                        html += '<summary class="cost-month-summary cost-row">';
                        html += '<span class="cost-month-label">' + monthLabel + '</span>';
                        html += '<span class="cost-month-total">' + (mg.total > 0 ? sym + _fmtCost(mg.total) : '—') + '</span>';
                        html += '</summary>';
                        const daysDesc = [...mg.days].sort((a, b) => (b.date > a.date ? 1 : -1));
                        for (const dayObj of daysDesc) {{
                            const dc = dayObj.total_cost || 0;
                            const isToday = dayObj.date === todayStr;
                            const dayNum = (dayObj.date || '').slice(8); // DD
                            html += '<div class="cost-row cost-day-row' + (isToday ? ' cost-today-row' : '') + '">';
                            html += '<div class="cost-row-name">' + dayNum + (isToday ? ' ●' : '') + '</div>';
                            html += '<div class="cost-row-value">' + (dc > 0 ? sym + _fmtCost(dc) : '—') + '</div>';
                            html += '</div>';
                        }}
                        html += '</details>';
                    }}
                    html += '</div>';
                }}

                if (!modelEntries.length && !provEntries.length && todayReqs === 0) {{
                    html = '<div style="padding:24px;text-align:center;color:#999;">' + T.costs_no_data + '</div>';
                }}

                // Reset button
                html += '<button class="cost-reset-btn" onclick="resetUsageStats()">' + T.costs_reset + '</button>';

                panel.innerHTML = html;
            }} catch (e) {{
                panel.innerHTML = '<div style="padding:16px;text-align:center;color:#e53e3e;">' + T.files_error + ': ' + e.message + '</div>';
            }}
        }}

        async function resetUsageStats() {{
            if (!confirm(T.costs_reset_confirm)) return;
            try {{
                await fetch(apiUrl('api/usage_stats/reset'), {{ method: 'POST' }});
                loadCostsPanel();
            }} catch (e) {{}}
        }}

        function renderConversationList(convs, listEl, source) {{
            listEl.innerHTML = '';
            if (!convs || convs.length === 0) {{
                listEl.innerHTML = '<div style="padding: 12px; text-align: center; color: #999; font-size: 12px;">' + T.no_conversations + '</div>';
                return;
            }}

            function parseConvTs(conv) {{
                try {{
                    const raw = (conv && (conv.last_updated || conv.id)) ? (conv.last_updated || conv.id) : '';
                    if (typeof raw === 'number') return raw;
                    const s = String(raw || '').trim();
                    if (!s) return 0;
                    const n = parseInt(s, 10);
                    if (!Number.isNaN(n) && n > 0) return n;
                    const p = Date.parse(s);
                    return Number.isNaN(p) ? 0 : p;
                }} catch (e) {{ return 0; }}
            }}

            function formatGroupLabel(ts) {{
                try {{
                    if (!ts || ts === 0) return '';
                    const d = new Date(ts);
                    if (Number.isNaN(d.getTime())) return '';
                    const now = new Date();
                    const startToday = new Date(now);
                    startToday.setHours(0, 0, 0, 0);
                    const startD = new Date(d);
                    startD.setHours(0, 0, 0, 0);
                    const diffDays = Math.floor((startToday.getTime() - startD.getTime()) / 86400000);
                    if (diffDays === 0) return (T.today || 'Today');
                    if (diffDays === 1) return (T.yesterday || 'Yesterday');
                    if (diffDays >= 2 && diffDays <= 6) return (T.days_ago || '{{n}} days ago').replace('{{n}}', String(diffDays));
                    const sameYear = d.getFullYear() === now.getFullYear();
                    const opts = sameYear ? {{ day: '2-digit', month: 'short' }} : {{ day: '2-digit', month: 'short', year: 'numeric' }};
                    return d.toLocaleDateString(undefined, opts);
                }} catch (e) {{ return ''; }}
            }}

            const sorted = convs.slice().sort((a, b) => parseConvTs(b) - parseConvTs(a));
            let lastLabel = null;
            sorted.forEach((conv) => {{
                const ts = parseConvTs(conv);
                const label = formatGroupLabel(ts);
                if (label && label !== lastLabel) {{
                    const header = document.createElement('div');
                    header.className = 'chat-group-title';
                    header.textContent = label;
                    listEl.appendChild(header);
                    lastLabel = label;
                }}
                const item = document.createElement('div');
                item.className = 'chat-item' + (conv.id === currentSessionId ? ' active' : '');
                const left = document.createElement('div');
                left.style.cssText = 'flex:1;min-width:0;overflow:hidden;';
                left.addEventListener('click', () => loadConversation(conv.id));
                const title = document.createElement('div');
                title.className = 'chat-item-title';
                // Strip any residual [CONTEXT: ...] from the title
                let cleanTitle = conv.title || '';
                if (cleanTitle.indexOf('[CONTEXT:') !== -1) {{
                    const ci = cleanTitle.indexOf('[CONTEXT:');
                    let d = 0, e = cleanTitle.length - 1;
                    for (let i = ci; i < cleanTitle.length; i++) {{
                        if (cleanTitle[i] === '[') d++;
                        else if (cleanTitle[i] === ']') {{ d--; if (d === 0) {{ e = i; break; }} }}
                    }}
                    let a = e + 1;
                    while (a < cleanTitle.length && (cleanTitle[a] === ' ' || cleanTitle[a] === '\\n')) a++;
                    cleanTitle = (cleanTitle.substring(0, ci) + cleanTitle.substring(a)).trim();
                }}
                title.textContent = cleanTitle || 'Chat...';
                const info = document.createElement('div');
                info.className = 'chat-item-info';
                info.textContent = String(conv.message_count || 0) + ' ' + (T.messages_count || 'messages');
                left.appendChild(title);
                left.appendChild(info);
                const del = document.createElement('span');
                del.className = 'chat-item-delete';
                del.title = T.delete_chat || 'Delete chat';
                del.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>';
                del.addEventListener('click', (evt) => deleteConversation(evt, conv.id));
                item.appendChild(left);
                item.appendChild(del);
                listEl.appendChild(item);
            }});
        }}

        let _allConversations = [];

        async function loadChatList() {{
            try {{
                const resp = await fetch(apiUrl('api/conversations'));
                if (!resp.ok) throw new Error('conversations failed: ' + resp.status);
                const data = await resp.json();
                _allConversations = data.conversations || [];
                const chatConvs = _allConversations.filter(c => c.source === 'chat');
                renderConversationList(chatConvs, document.getElementById('chatList'), 'chat');
            }} catch(e) {{
                console.error('Error loading chat list:', e);
            }}
        }}

        async function loadBubbleList() {{
            try {{
                const resp = await fetch(apiUrl('api/conversations'));
                if (!resp.ok) throw new Error('conversations failed: ' + resp.status);
                const data = await resp.json();
                _allConversations = data.conversations || [];
                const bubbleConvs = _allConversations.filter(c => c.source === 'bubble');
                renderConversationList(bubbleConvs, document.getElementById('bubbleList'), 'bubble');
            }} catch(e) {{
                console.error('Error loading bubble list:', e);
            }}
        }}

        async function loadAmiraList() {{
            try {{
                const resp = await fetch(apiUrl('api/conversations'));
                if (!resp.ok) throw new Error('conversations failed: ' + resp.status);
                const data = await resp.json();
                _allConversations = data.conversations || [];
                const amiraConvs = _allConversations.filter(c => c.source === 'card');
                renderConversationList(amiraConvs, document.getElementById('amiraList'), 'amira');
            }} catch(e) {{
                console.error('Error loading Amira list:', e);
            }}
        }}

        async function loadBackupList() {{
            const listEl = document.getElementById('backupList');
            try {{
                const resp = await fetch(apiUrl('api/snapshots'));
                if (!resp.ok) throw new Error('snapshots failed: ' + resp.status);
                const data = await resp.json();
                listEl.innerHTML = '';
                if (!data.snapshots || data.snapshots.length === 0) {{
                    listEl.innerHTML = '<div style="padding: 12px; text-align: center; color: #999; font-size: 12px;">' + (T.no_backups || 'No backups') + '</div>';
                    return;
                }}
                data.snapshots.forEach(snap => {{
                    const item = document.createElement('div');
                    item.className = 'backup-item';
                    const fileDiv = document.createElement('div');
                    fileDiv.className = 'backup-file';
                    fileDiv.textContent = snap.original_file || snap.id;
                    const metaDiv = document.createElement('div');
                    metaDiv.className = 'backup-meta';
                    const dateSpan = document.createElement('span');
                    dateSpan.className = 'backup-date';
                    dateSpan.textContent = snap.formatted_date || snap.timestamp;
                    const restoreBtn = document.createElement('button');
                    restoreBtn.className = 'backup-restore';
                    restoreBtn.textContent = T.restore || 'Restore';
                    restoreBtn.addEventListener('click', () => restoreBackup(snap.id));
                    const dlBtn = document.createElement('button');
                    dlBtn.className = 'backup-download';
                    dlBtn.textContent = T.download_backup || 'Download';
                    dlBtn.addEventListener('click', () => downloadBackup(snap.id));
                    const delBtn = document.createElement('button');
                    delBtn.className = 'backup-delete';
                    delBtn.textContent = T.delete_backup || 'Delete';
                    delBtn.addEventListener('click', () => deleteBackup(snap.id));
                    metaDiv.appendChild(dateSpan);
                    const btns = document.createElement('div');
                    btns.style.display = 'flex'; btns.style.gap = '4px';
                    btns.appendChild(restoreBtn);
                    btns.appendChild(dlBtn);
                    btns.appendChild(delBtn);
                    metaDiv.appendChild(btns);
                    item.appendChild(fileDiv);
                    item.appendChild(metaDiv);
                    listEl.appendChild(item);
                }});
            }} catch(e) {{
                console.error('Error loading backups:', e);
                listEl.innerHTML = '<div style="padding: 12px; color: #ef4444;">\u26a0\ufe0f Error loading backups</div>';
            }}
        }}

        async function restoreBackup(snapshotId) {{
            if (!confirm(T.confirm_restore_backup || 'Restore this backup?')) return;
            try {{
                const resp = await fetch(apiUrl('api/snapshots/restore'), {{ 
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ snapshot_id: snapshotId }})
                }});
                const data = await resp.json();
                if (resp.ok && data.status === 'success') {{
                    addMessage('\u2705 ' + (T.backup_restored || 'Backup restored'), 'system');
                    loadBackupList();
                }} else {{
                    addMessage('\u274c ' + (data.error || 'Restore failed'), 'system');
                }}
            }} catch(e) {{
                addMessage('\u274c ' + (T.error_restore || 'Restore error: ') + e.message, 'system');
            }}
        }}

        function downloadBackup(snapshotId) {{
            const downloadUrl = apiUrl('api/snapshots/' + encodeURIComponent(snapshotId) + '/download');
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = '';  // Let the server set the filename via Content-Disposition
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }}

        async function deleteBackup(snapshotId) {{
            if (!confirm(T.confirm_delete_backup || 'Delete this backup permanently?')) return;
            try {{
                const resp = await fetch(apiUrl('api/snapshots/' + encodeURIComponent(snapshotId)), {{ method: 'DELETE' }});
                if (resp.ok) loadBackupList();
            }} catch(e) {{
                console.error('Error deleting backup:', e);
            }}
        }}

        // Device Manager Functions
        async function loadDeviceList() {{
            const listEl = document.getElementById('deviceList');
            try {{
                const resp = await fetch(apiUrl('api/bubble/devices'));
                if (!resp.ok) throw new Error('devices failed: ' + resp.status);
                const data = await resp.json();
                listEl.innerHTML = '';
                if (!data.devices || Object.keys(data.devices).length === 0) {{
                    listEl.innerHTML = '<div style="padding: 12px; text-align: center; color: #999; font-size: 12px;">' + (T.no_devices || 'No devices') + '</div>';
                    return;
                }}
                Object.entries(data.devices).forEach(([deviceId, device]) => {{
                    const item = document.createElement('div');
                    item.className = 'device-item';
                    
                    const nameDiv = document.createElement('div');
                    nameDiv.className = 'device-name';
                    nameDiv.textContent = device.name || deviceId;
                    
                    const metaDiv = document.createElement('div');
                    metaDiv.className = 'device-meta';
                    
                    const typeSpan = document.createElement('span');
                    typeSpan.className = 'device-type';
                    typeSpan.textContent = (device.device_type || 'unknown').charAt(0).toUpperCase() + (device.device_type || 'unknown').slice(1);
                    
                    const statusSpan = document.createElement('span');
                    statusSpan.className = 'device-status';
                    statusSpan.textContent = device.enabled ? '✅' : '⛔';
                    
                    const lastSeenSpan = document.createElement('span');
                    lastSeenSpan.className = 'device-last-seen';
                    lastSeenSpan.textContent = 'Last: ' + (device.last_seen ? new Date(device.last_seen).toLocaleDateString() : 'never');
                    
                    metaDiv.appendChild(typeSpan);
                    metaDiv.appendChild(statusSpan);
                    metaDiv.appendChild(lastSeenSpan);
                    
                    const btnDiv = document.createElement('div');
                    btnDiv.className = 'device-buttons';
                    
                    const toggleBtn = document.createElement('button');
                    toggleBtn.className = 'device-toggle';
                    toggleBtn.textContent = device.enabled ? (T.disable_device || 'Disable') : (T.enable_device || 'Enable');
                    toggleBtn.style.backgroundColor = device.enabled ? '#ef4444' : '#4caf50';
                    toggleBtn.addEventListener('click', () => toggleDevice(deviceId));
                    
                    const renameBtn = document.createElement('button');
                    renameBtn.className = 'device-rename';
                    renameBtn.textContent = T.rename_device || 'Rename';
                    renameBtn.addEventListener('click', () => renameDevice(deviceId, device.name));
                    
                    const deleteBtn = document.createElement('button');
                    deleteBtn.className = 'device-delete';
                    deleteBtn.textContent = T.delete_device || 'Delete';
                    deleteBtn.addEventListener('click', () => deleteDevice(deviceId));
                    
                    btnDiv.appendChild(toggleBtn);
                    btnDiv.appendChild(renameBtn);
                    btnDiv.appendChild(deleteBtn);
                    
                    item.appendChild(nameDiv);
                    item.appendChild(metaDiv);
                    item.appendChild(btnDiv);
                    listEl.appendChild(item);
                }});
            }} catch(e) {{
                console.error('Error loading devices:', e);
                listEl.innerHTML = '<div style="padding: 12px; color: #ef4444;">⚠️ Error loading devices</div>';
            }}
        }}

        async function toggleDevice(deviceId) {{
            try {{
                const resp = await fetch(apiUrl('api/bubble/devices/' + encodeURIComponent(deviceId)), {{
                    method: 'PATCH',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ enabled: null }})  // null = toggle
                }});
                if (resp.ok) {{
                    addMessage('✅ ' + (T.device_updated || 'Device updated'), 'system');
                    loadDeviceList();
                }}
            }} catch(e) {{
                console.error('Error toggling device:', e);
            }}
        }}

        async function renameDevice(deviceId, currentName) {{
            const newName = prompt(T.rename_device + ':', currentName);
            if (!newName || newName === currentName) return;
            try {{
                const resp = await fetch(apiUrl('api/bubble/devices/' + encodeURIComponent(deviceId)), {{
                    method: 'PATCH',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name: newName }})
                }});
                if (resp.ok) {{
                    addMessage('✅ ' + (T.device_updated || 'Device updated'), 'system');
                    loadDeviceList();
                }}
            }} catch(e) {{
                console.error('Error renaming device:', e);
            }}
        }}

        async function deleteDevice(deviceId) {{
            if (!confirm(T.confirm_delete_device || 'Delete this device permanently?')) return;
            try {{
                const resp = await fetch(apiUrl('api/bubble/devices/' + encodeURIComponent(deviceId)), {{ method: 'DELETE' }});
                if (resp.ok) {{
                    addMessage('✅ ' + (T.device_deleted || 'Device deleted'), 'system');
                    loadDeviceList();
                }}
            }} catch(e) {{
                console.error('Error deleting device:', e);
            }}
        }}

        // Messaging Functions
        async function loadMessagingList() {{
            const listEl = document.getElementById('messagingList');
            try {{
                const resp = await fetch(apiUrl('api/messaging/chats'));
                if (!resp.ok) throw new Error('messaging failed: ' + resp.status);
                const data = await resp.json();
                listEl.innerHTML = '';
                
                const chats = data.chats || {{}};
                const allChats = [
                    ...(chats.telegram || []).map(c => ({{...c, channel: 'telegram'}})),
                    ...(chats.whatsapp || []).map(c => ({{...c, channel: 'whatsapp'}})),
                    ...(chats.discord || []).map(c => ({{...c, channel: 'discord'}}))
                ];
                // Sort by most recent message first
                allChats.sort((a, b) => {{
                    const ta = a.last_timestamp ? new Date(a.last_timestamp).getTime() : 0;
                    const tb = b.last_timestamp ? new Date(b.last_timestamp).getTime() : 0;
                    return tb - ta;
                }});

                if (allChats.length === 0) {{
                    listEl.innerHTML = '<div style="padding: 12px; text-align: center; color: #999; font-size: 12px;">' + (T.messaging_no_chats || 'No messaging chats') + '</div>';
                    return;
                }}
                
                allChats.forEach(chat => {{
                    const isTg = chat.channel === 'telegram';
                    const isWa = chat.channel === 'whatsapp';
                    const badgeLabel = isTg ? '✈️ Telegram' : isWa ? '💬 WhatsApp' : '🕹️ Discord';
                    const badgeCls   = isTg ? 'telegram' : isWa ? 'whatsapp' : 'discord';
                    const timeStr    = chat.last_timestamp
                        ? new Date(chat.last_timestamp).toLocaleString([], {{dateStyle:'short', timeStyle:'short'}})
                        : '';
                    const preview = (chat.last_message || '').slice(0, 80);
                    const msgCount = chat.message_count || 0;

                    const card = document.createElement('div');
                    card.className = 'messaging-card';
                    card.onclick = () => loadMessagesPreview(chat.channel, chat.user_id);
                    card.innerHTML = `
                        <div class="messaging-card-header">
                            <div class="messaging-card-channel">
                                <span class="messaging-card-badge ${{badgeCls}}">${{badgeLabel}}</span>
                                <span class="messaging-card-uid">${{chat.user_id}}</span>
                            </div>
                            <button class="messaging-card-delete" title="${{T.messaging_delete || 'Delete'}}">🗑</button>
                        </div>
                        <div class="messaging-card-preview">${{preview || '—'}}</div>
                        <div class="messaging-card-footer">
                            <span class="messaging-card-count">💬 ${{msgCount}} ${{T.messaging_messages || 'messages'}}</span>
                            <span class="messaging-card-time">${{timeStr}}</span>
                        </div>`;

                    card.querySelector('.messaging-card-delete').addEventListener('click', e => {{
                        e.stopPropagation();
                        deleteMessagingChat(chat.channel, chat.user_id);
                    }});
                    listEl.appendChild(card);
                }});
            }} catch(e) {{
                console.error('Error loading messaging chats:', e);
                listEl.innerHTML = '<div style="padding: 12px; color: #f00;">Error loading chats</div>';
            }}
        }}

        async function loadMessagesPreview(channel, userId) {{
            try {{
                const resp = await fetch(apiUrl(`api/messaging/chat/${{encodeURIComponent(channel)}}/${{encodeURIComponent(userId)}}`));
                if (!resp.ok) throw new Error('Failed to load messages');
                const data = await resp.json();
                const messages = data.messages || [];

                const channelLabel = channel === 'telegram' ? '🤖 Telegram' : channel === 'whatsapp' ? '💬 WhatsApp' : '🕹️ Discord';
                document.getElementById('msgModalTitle').textContent = `${{channelLabel}} · ${{userId}}`;

                const body = document.getElementById('msgModalBody');
                body.innerHTML = '';
                if (messages.length === 0) {{
                    body.innerHTML = '<div style="text-align:center;color:#999;padding:20px;font-size:13px;">Nessun messaggio</div>';
                }} else {{
                    messages.forEach(msg => {{
                        const isUser = msg.role === 'user';
                        const isError = (msg.text || '').startsWith('⚠️') || (msg.text || '').startsWith('❌');
                        const wrap = document.createElement('div');
                        wrap.style.display = 'flex';
                        wrap.style.flexDirection = 'column';
                        wrap.style.alignItems = isUser ? 'flex-end' : 'flex-start';

                        const label = document.createElement('div');
                        label.className = 'msg-bubble-label';
                        label.textContent = isUser ? '👤 Tu' : '🤖 Bot';
                        label.style.textAlign = isUser ? 'right' : 'left';

                        const bubble = document.createElement('div');
                        bubble.className = 'msg-bubble ' + (isUser ? 'user' : 'assistant') + (isError ? ' error' : '');
                        bubble.textContent = isUser ? stripContextInjections(msg.text || '') : (msg.text || '');

                        wrap.appendChild(label);
                        wrap.appendChild(bubble);
                        body.appendChild(wrap);
                    }});
                    // scroll to bottom
                    setTimeout(() => {{ body.scrollTop = body.scrollHeight; }}, 50);
                }}

                document.getElementById('messagingChatModal').classList.add('open');
            }} catch(e) {{
                console.error('Error loading messages:', e);
                addMessage('❌ Error loading messages', 'system');
            }}
        }}

        async function deleteMessagingChat(channel, userId) {{
            if (!confirm(T.messaging_confirm_delete || 'Delete this chat?')) return;
            try {{
                const resp = await fetch(apiUrl(`api/messaging/chat/${{encodeURIComponent(channel)}}/${{encodeURIComponent(userId)}}`), {{ method: 'DELETE' }});
                if (resp.ok) {{
                    addMessage('✅ Chat deleted', 'system');
                    loadMessagingList();
                }}
            }} catch(e) {{
                console.error('Error deleting chat:', e);
                addMessage('❌ Error deleting chat', 'system');
            }}
        }}

        async function deleteConversation(event, sessionId) {{
            event.stopPropagation();
            if (!confirm(T.confirm_delete)) return;
            try {{
                const resp = await fetch(apiUrl(`api/conversations/${{sessionId}}`), {{ method: 'DELETE' }});
                if (resp.ok) {{
                    if (sessionId === currentSessionId) {{
                        newChat();
                    }} else {{
                        loadChatList();
                    }}
                }}
            }} catch(e) {{ console.error('Error deleting conversation:', e); }}
        }}

        async function loadConversation(sessionId) {{
            currentSessionId = sessionId;
            // Only persist non-bubble sessions so reopening the page won't resume a bubble chat
            if (!sessionId.startsWith('bubble_')) {{
                safeLocalStorageSet('currentSessionId', sessionId);
            }}
            try {{
                const resp = await fetch(apiUrl(`api/conversations/${{sessionId}}`));
                if (resp.status === 404) {{
                    console.log('Session not found, creating new session');
                    newChat();
                    return;
                }}
                const data = await resp.json();
                chat.innerHTML = '';
                resetConversationUsage();
                if (data.messages && data.messages.length > 0) {{
                    suggestionsEl.style.display = 'none';
                    data.messages.forEach(m => {{
                        if (m.role === 'user' || m.role === 'assistant') {{
                            const metadata = (m.role === 'assistant' && (m.model || m.provider || m.usage))
                                ? {{ model: m.model, provider: m.provider, usage: m.usage }} : null;
                            addMessage(m.content, m.role, null, metadata);
                        }}
                    }});
                }} else {{
                    chat.innerHTML = `<div class="message system">
                        {msgs['welcome']}<br>
                        ${{getProviderModelLine()}}<br>
                        {msgs['capabilities']}<br>
                        {msgs['vision_feature']}
                    </div>`;
                    suggestionsEl.style.display = 'flex';
                }}
                // Re-render active tab to update selection highlight
                const activeTab = document.querySelector('.sidebar-tab.active');
                const tabName = activeTab ? activeTab.dataset.tab : 'chat';
                if (tabName === 'bubble') loadBubbleList();
                else loadChatList();
                closeSidebarMobile();
            }} catch(e) {{ console.error('Error loading conversation:', e); }}
        }}

        async function loadHistory() {{
            await loadConversation(currentSessionId);
        }}

        async function newChat() {{
            currentSessionId = Date.now().toString();
            safeLocalStorageSet('currentSessionId', currentSessionId);
            resetConversationUsage();
            chat.innerHTML = `<div class="message system">
                {msgs['welcome']}<br>
                ${{getProviderModelLine()}}<br>
                {msgs['capabilities']}<br>
                {msgs['vision_feature']}
            </div>`;
            suggestionsEl.style.display = 'flex';
            removeImage();
            loadChatList();
            closeSidebarMobile();
        }}

        // Provider name mapping for optgroups
        const PROVIDER_LABELS = {{
            'anthropic': '🧠 Anthropic Claude',
            'openai': '⚡ OpenAI',
            'google': '✨ Google Gemini',
            'nvidia': '🎯 NVIDIA NIM',
            'github': '🚀 GitHub Models',
            'groq': '⚡ Groq',
            'mistral': '🌊 Mistral',
            'ollama': '🦙 Ollama',
            'openrouter': '🔀 OpenRouter',
            'deepseek': '🔍 DeepSeek',
            'xai': '🧠 xAI (Grok)',
            'minimax': '🎭 MiniMax',
            'aihubmix': '🌐 AiHubMix',
            'siliconflow': '💎 SiliconFlow',
            'volcengine': '🌋 VolcEngine',
            'dashscope': '☁️ DashScope (Qwen)',
            'moonshot': '🌙 Moonshot (Kimi)',
            'zhipu': '🧬 Zhipu (GLM)',
            'perplexity': '🔎 Perplexity',
            'perplexity_web': '⚠️ Perplexity Web',
            'custom': '🛠️ Custom Endpoint',
            'github_copilot': '⚠️ GitHub Copilot (Web)',
            'openai_codex': '⚠️ OpenAI Codex (Web)',
            'claude_web': '⚠️ Claude.ai (Web)',
            'chatgpt_web': '⚠️ ChatGPT (Web)',
            'gemini_web': '⚠️ Gemini Web'
        }};
        const TESTABLE_BATCH_PROVIDERS = new Set(['nvidia', 'openrouter', 'mistral']);

        function updateBatchTestButton() {{
            const btn = document.getElementById('testNvidiaBtn');
            if (!btn) return;
            const enabled = TESTABLE_BATCH_PROVIDERS.has(currentProviderId);
            btn.style.display = enabled ? 'inline-flex' : 'none';
            if (!enabled) return;
            if (currentProviderId === 'nvidia') {{
                btn.textContent = '\U0001f50d ' + (T.nvidia_test_btn || 'Test NVIDIA');
                btn.title = T.nvidia_test_title || 'Quick NVIDIA test (may take a few seconds)';
            }} else {{
                const pName = (PROVIDER_LABELS[currentProviderId] || currentProviderId || '').replace(/^[^\\w]+/u, '').trim();
                btn.textContent = '\U0001f50d Test ' + pName;
                btn.title = 'Batch test models for ' + pName;
            }}
        }}

        // Build the welcome provider/model line dynamically (always reflects current selection)
        function getProviderModelLine() {{
            const provName = PROVIDER_LABELS[currentProviderId] || currentProviderId || '';
            return `${{T.provider_label}}: <strong>${{provName}}</strong> | ${{T.model_label}}: <strong>${{currentModelDisplay}}</strong>`;
        }}

        function updateHeaderProviderStatus(providerId, availableProviders) {{
            const statusTextEl = document.getElementById('statusText');
            const statusDotEl = document.getElementById('statusDot');
            if (!statusTextEl || !statusDotEl) return;

            const providerName = PROVIDER_LABELS[providerId] || providerId || '';
            const ids = Array.isArray(availableProviders)
                ? availableProviders.map(p => (p && p.id) ? String(p.id) : '').filter(Boolean)
                : [];
            const configured = providerId ? ids.includes(String(providerId)) : false;

            statusTextEl.textContent = configured ? providerName : (providerName ? (providerName + ' (no key)') : '');
            statusDotEl.style.background = configured ? '#4caf50' : '#ff9800';
        }}



        // Load models and populate dropdown with ALL providers
        // Stores full models data for use by populateModelSelect()
        let _modelsData = null;
        // Prevent loadModels() from resetting dropdowns while user has one open
        let _selectOpen = false;

        function _stripProviderPrefix(model) {{
            return model.replace(/^(Claude|OpenAI|Google|NVIDIA|GitHub Models|GitHub Copilot|OpenAI Codex|Claude Web|ChatGPT Web|Gemini Web|Perplexity Web|GitHub|Groq|Mistral|Ollama|OpenRouter|DeepSeek|xAI|MiniMax|AiHubMix|SiliconFlow|VolcEngine|DashScope|Moonshot|Zhipu):\\s*/, '');
        }}

        // Capability badge helper
        function _capBadges(model, providerId) {{
            if (!_modelsData || !_modelsData.model_capabilities) return '';
            const key = providerId + '/' + model;
            const caps = _modelsData.model_capabilities[key];
            if (!caps || !caps.capabilities) return '';
            const badges = [];
            if (caps.capabilities.includes('vision'))    badges.push('\U0001f441\ufe0f');
            if (caps.capabilities.includes('reasoning')) badges.push('\U0001f9e0');
            if (caps.capabilities.includes('tool_use'))  badges.push('\U0001f527');
            if (caps.capabilities.includes('code'))      badges.push('\U0001f4bb');
            return badges.length ? ' ' + badges.join('') : '';
        }}

        // Populate the model <select> based on selected provider
        function populateModelSelect(providerId, currentModel) {{
            const modelSel = document.getElementById('modelSelect');
            if (!modelSel || !_modelsData) return;
            modelSel.innerHTML = '';

            const models = (_modelsData.models || {{}})[providerId] || [];
            const modelSections = ((_modelsData.models_sections || {{}})[providerId]) || null;

            // NVIDIA: split into tested / to-test groups
            if (providerId === 'nvidia' && (Array.isArray(_modelsData.nvidia_models_tested) || Array.isArray(_modelsData.nvidia_models_to_test))) {{
                const tested = Array.isArray(_modelsData.nvidia_models_tested) ? _modelsData.nvidia_models_tested : [];
                const toTest = Array.isArray(_modelsData.nvidia_models_to_test) ? _modelsData.nvidia_models_to_test : [];
                [
                    {{ label: '\u2705 ' + T.nvidia_tested, models: tested }},
                    {{ label: T.nvidia_to_test, models: toTest }},
                ].filter(g => g.models.length).forEach(g => {{
                    const grp = document.createElement('optgroup');
                    grp.label = g.label;
                    g.models.forEach(m => {{
                        const opt = document.createElement('option');
                        opt.value = m;
                        opt.textContent = _stripProviderPrefix(m) + _capBadges(m, providerId);
                        if (m === currentModel) opt.selected = true;
                        grp.appendChild(opt);
                    }});
                    modelSel.appendChild(grp);
                }});
            }} else {{
                const fixed = modelSections && Array.isArray(modelSections.fixed) ? modelSections.fixed : [];
                const dynamic = modelSections && Array.isArray(modelSections.dynamic) ? modelSections.dynamic : [];

                if (fixed.length || dynamic.length) {{
                    if (fixed.length) {{
                        const grpFixed = document.createElement('optgroup');
                        grpFixed.label = T.models_group_fixed || 'Fixed';
                        fixed.forEach(m => {{
                            const opt = document.createElement('option');
                            opt.value = m;
                            opt.textContent = _stripProviderPrefix(m) + _capBadges(m, providerId);
                            if (m === currentModel) opt.selected = true;
                            grpFixed.appendChild(opt);
                        }});
                        modelSel.appendChild(grpFixed);
                    }}
                    if (dynamic.length) {{
                        const grpDyn = document.createElement('optgroup');
                        grpDyn.label = T.models_group_dynamic_cache || 'Dynamic (cache)';
                        dynamic.forEach(m => {{
                            const opt = document.createElement('option');
                            opt.value = m;
                            opt.textContent = _stripProviderPrefix(m) + _capBadges(m, providerId);
                            if (m === currentModel) opt.selected = true;
                            grpDyn.appendChild(opt);
                        }});
                        modelSel.appendChild(grpDyn);
                    }}
                }} else {{
                    models.forEach(m => {{
                        const opt = document.createElement('option');
                        opt.value = m;
                        opt.textContent = _stripProviderPrefix(m) + _capBadges(m, providerId);
                        if (m === currentModel) opt.selected = true;
                        modelSel.appendChild(opt);
                    }});
                }}
            }}

            if (!modelSel.options.length) {{
                const opt = document.createElement('option');
                opt.textContent = T.no_models;
                opt.disabled = true;
                opt.selected = true;
                modelSel.appendChild(opt);
            }}
        }}

        async function loadModels() {{
            try {{
                const response = await fetch(apiUrl('api/get_models'));
                if (!response.ok) throw new Error('get_models failed: ' + response.status);
                const data = await response.json();
                _modelsData = data;
                console.log('[loadModels] API response:', data);

                // If a select is currently open (user is browsing options), skip all DOM
                // manipulation to avoid closing/resetting the dropdown mid-interaction.
                if (_selectOpen) {{
                    console.log('[loadModels] select open — skipping DOM update');
                    return;
                }}

                const providerSel = document.getElementById('providerSelect');
                const currentProvider = data.current_provider;
                const currentModel = data.current_model;

                if (data.needs_first_selection && !window._firstSelectionPrompted) {{
                    addMessage('\U0001f446 ' + T.select_agent, 'system');
                    window._firstSelectionPrompted = true;
                }}
                if (currentProvider) currentProviderId = currentProvider;
                if (currentModel) currentModelDisplay = currentModel;

                updateHeaderProviderStatus(currentProviderId, data.available_providers);
                updateBatchTestButton();

                // Build ordered provider list
                let availableProviders = data.available_providers && data.available_providers.length
                    ? data.available_providers.map(p => p.id)
                    : Object.keys(data.models || {{}});
                if (!availableProviders.length && currentProvider) availableProviders = [currentProvider];

                const providerOrder = [
                    'anthropic', 'openai', 'google', 'nvidia', 'github',
                    'groq', 'mistral', 'ollama', 'openrouter',
                    'deepseek', 'xai', 'minimax', 'aihubmix', 'siliconflow', 'volcengine',
                    'dashscope', 'moonshot', 'zhipu',
                    // --- Web providers (always last) ---
                    'github_copilot', 'openai_codex', 'claude_web', 'chatgpt_web', 'gemini_web', 'perplexity_web'
                ];
                for (const p of availableProviders) {{
                    if (!providerOrder.includes(p)) providerOrder.push(p);
                }}

                // Populate provider select
                providerSel.innerHTML = '';
                let anyProvider = false;
                for (const pid of providerOrder) {{
                    if (!availableProviders.includes(pid)) continue;
                    if (!data.models || !data.models[pid] || !data.models[pid].length) continue;
                    const opt = document.createElement('option');
                    opt.value = pid;
                    opt.textContent = PROVIDER_LABELS[pid] || pid;
                    if (pid === currentProvider) opt.selected = true;
                    providerSel.appendChild(opt);
                    anyProvider = true;
                }}

                const wrap = document.getElementById('modelSelectWrap');
                if (!anyProvider) {{
                    if (wrap) wrap.style.display = 'none';
                    console.log('[loadModels] No providers available, hiding selectors');
                }} else {{
                    if (wrap) wrap.style.display = '';
                    // Populate model select for current provider
                    const activeProv = providerSel.value || currentProvider;
                    populateModelSelect(activeProv, currentModel);
                }}

                // --- Agent selector population ---
                const agentSel = document.getElementById('agentSelect');
                if (agentSel && Array.isArray(data.agents) && data.agents.length >= 1) {{
                    agentSel.innerHTML = '';
                    // Determine target agent: localStorage > explicit change > server active
                    const storedAgent = localStorage.getItem('ha_claude_active_agent');
                    const targetAgent = _lastExplicitAgent || storedAgent || data.active_agent;
                    data.agents.forEach(a => {{
                        const opt = document.createElement('option');
                        opt.value = a.id;
                        const ident = a.identity || {{}};
                        opt.textContent = (ident.emoji || a.emoji || '\U0001f916') + ' ' + (ident.name || a.name || a.id);
                        // Show agent ID in tooltip so user knows which agent is which
                        opt.title = `Agent ID: ${{a.id}}`;
                        if (targetAgent && a.id === targetAgent) opt.selected = true;
                        agentSel.appendChild(opt);
                    }});
                    // Sync server active agent if localStorage selection differs
                    if (storedAgent && storedAgent !== data.active_agent && data.agents.some(a => a.id === storedAgent)) {{
                        fetch(apiUrl('api/agents/set'), {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{agent_id: storedAgent}})
                        }}).catch(() => {{}});
                    }}
                    agentSel.style.display = '';
                }} else if (agentSel) {{
                    agentSel.style.display = 'none';
                }}

                // --- Update header identity from selected agent ---
                {{
                    const selAgentId = agentSel ? agentSel.value : data.active_agent;
                    const selAgentData = (data.agents || []).find(a => a.id === selAgentId);
                    if (selAgentData) {{
                        const h1 = document.querySelector('.header h1');
                        if (h1) h1.textContent = selAgentData.name || selAgentId;
                        const emojiSpan = document.querySelector('.header > span');
                        if (emojiSpan) emojiSpan.textContent = selAgentData.emoji || '\U0001f916';
                    }} else if (data.active_agent_identity) {{
                        const ident = data.active_agent_identity;
                        if (ident.name) {{
                            const h1 = document.querySelector('.header h1');
                            if (h1) h1.textContent = ident.name;
                        }}
                        if (ident.emoji) {{
                            const emojiSpan = document.querySelector('.header > span');
                            if (emojiSpan) emojiSpan.textContent = ident.emoji;
                        }}
                    }}
                }}

                console.log('[loadModels] Loaded models for', availableProviders.length, 'providers');
            }} catch (error) {{
                console.error('[loadModels] Error loading models:', error);
                if (!window._modelsErrorNotified) {{
                    const isAuthErr = error.message && (error.message.includes('401') || error.message.includes('403') || error.message.includes('Failed to fetch'));
                    const hint = isAuthErr ? ' — Prova a fare un hard refresh (Ctrl+Shift+R) dalla sidebar di HA.' : '';
                    addMessage('\u26a0\ufe0f ' + T.models_load_error + (error.message || error) + hint, 'system');
                    window._modelsErrorNotified = true;
                }}
            }}
        }}

        async function testNvidiaModel() {{
            const btn = document.getElementById('testNvidiaBtn');
            if (!btn) return;
            if (window.__batchTestRunning) {{
                // Toggle behavior: second click requests stop.
                window.__batchTestStopRequested = true;
                return;
            }}
            const provider = currentProviderId || 'nvidia';
            if (!TESTABLE_BATCH_PROVIDERS.has(provider)) return;
            const isNvidia = provider === 'nvidia';
            const providerLabel = (PROVIDER_LABELS[provider] || provider).replace(/^[^\\w]+/u, '').trim();

            // Small bounded batches => frequent progress updates in chat UI.
            // The loop continues until completion, so all models are still covered.
            const BATCH = 10;
            let cursor = 0;
            let totalOk = 0, totalRemoved = 0, totalTested = 0, grandTotal = 0;
            let anyBlocklisted = false;
            let batchNum = 0;
            let progressMsgEl = null;
            let progressEvents = [];

            const appendEvents = (eventsArr) => {{
                if (!Array.isArray(eventsArr) || !eventsArr.length) return;
                for (const ev of eventsArr) {{
                    const line = String(ev || '').trim();
                    if (!line) continue;
                    const last = progressEvents.length ? progressEvents[progressEvents.length - 1] : '';
                    if (line === last) continue;
                    progressEvents.push(line);
                }}
                if (progressEvents.length > 12) progressEvents = progressEvents.slice(-12);
            }};

            const renderProgressMessage = (headline) => {{
                if (!progressMsgEl) return;
                const safeHeadline = _escapeHtml(headline || '');
                const recent = progressEvents.slice(-6);
                if (!recent.length) {{
                    progressMsgEl.textContent = headline || '';
                    return;
                }}
                const eventsHtml = recent.map(e => '\u2022 ' + _escapeHtml(e)).join('<br>');
                progressMsgEl.innerHTML = safeHeadline
                    + '<br><span style="display:block; margin-top:6px; opacity:.92; font-size:12px; line-height:1.35;">'
                    + eventsHtml
                    + '</span>';
            }};

            const oldText = btn.textContent;
            window.__batchTestRunning = true;
            window.__batchTestStopRequested = false;
            btn.disabled = false;
            btn.textContent = '⏹ Stop test';
            progressMsgEl = addMessage('\U0001f50d Test started: ' + providerLabel, 'system');

            try {{
                while (true) {{
                    if (window.__batchTestStopRequested) {{
                        const stopByUserMsg = `⏹ Test ${{providerLabel}} stopped by user • tested ${{totalTested}}/${{grandTotal || '?'}} • ok ${{totalOk}} • removed ${{totalRemoved}}`;
                        if (progressMsgEl) renderProgressMessage(stopByUserMsg);
                        else addMessage(stopByUserMsg, 'system');
                        break;
                    }}
                    batchNum++;
                    btn.textContent = `⏹ Stop test (${{batchNum}})`;

                    const response = await fetch(apiUrl(isNvidia ? 'api/nvidia/test_models' : 'api/provider/test_models'), {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(isNvidia
                            ? {{max_models: BATCH, cursor: cursor}}
                            : {{provider: provider, max_models: BATCH, cursor: cursor}})
                    }});
                    const data = await response.json().catch(() => ({{}}));

                    if (!response.ok || !data || !data.success) {{
                        const fallbackErr = isNvidia ? (T.nvidia_test_failed || 'NVIDIA test failed') : ('Test ' + providerLabel + ' failed');
                        const msg = (data && (data.message || data.error)) || (fallbackErr + ' (' + response.status + ')');
                        addMessage('\u26a0\ufe0f ' + msg, 'system');
                        break;
                    }}

                    totalOk += (data.ok || 0);
                    totalRemoved += (data.removed || 0);
                    grandTotal = data.total || grandTotal;
                    const testedDelta = (data.tested || 0);
                    totalTested += testedDelta;
                    if (grandTotal > 0) totalTested = Math.min(totalTested, grandTotal);
                    if (data.blocklisted) anyBlocklisted = true;
                    const batchTested = Array.isArray(data.tested_models) ? data.tested_models : [];
                    const currentModel = batchTested.length ? batchTested[batchTested.length - 1] : '';
                    appendEvents(data.events);

                    // Progress in chat (single live message, non-spam)
                    try {{
                        if (progressMsgEl) {{
                            const totalLabel = grandTotal > 0 ? grandTotal : '?';
                            const modelPart = currentModel ? ` • LLM: ${{currentModel}}` : '';
                            renderProgressMessage(
                                `\u23f3 Test ${{providerLabel}}: batch ${{batchNum}} • tested ${{totalTested}}/${{totalLabel}} • ok ${{totalOk}} • removed ${{totalRemoved}}${{modelPart}}`
                            );
                        }}
                    }} catch (_) {{}}

                    // Any stopped_reason means backend asked us to stop this run.
                    // (e.g. rate-limit, auth, network, HTTP 500, timeout, etc.)
                    if (data.stopped_reason) {{
                        const parts = [];
                        const tpl = isNvidia
                            ? (T.nvidia_test_result || 'NVIDIA Test: OK {{ok}}, removed {{removed}}, tested {{tested}}/{{total}}')
                            : ('Test ' + providerLabel + ': OK {{ok}}, removed {{removed}}, tested {{tested}}/{{total}}');
                        parts.push(tpl.replace('{{ok}}', totalOk).replace('{{removed}}', totalRemoved).replace('{{tested}}', totalTested).replace('{{total}}', grandTotal));
                        parts.push(`(${{data.stopped_reason}})`);
                        if (typeof data.remaining === 'number' && data.remaining > 0) parts.push('\u2014 ' + T.nvidia_remaining.replace('{{n}}', data.remaining));
                        const stopMsg = '\U0001f50d ' + parts.join(' ');
                        if (progressMsgEl) renderProgressMessage(stopMsg);
                        else addMessage(stopMsg, 'system');
                        break;
                    }}

                    // Aggiorna cursor
                    const prevCursor = cursor;
                    if (typeof data.next_cursor === 'number') {{
                        cursor = data.next_cursor;
                    }}
                    // Defensive guard: if cursor doesn't advance, stop to avoid infinite loop.
                    if (typeof data.next_cursor === 'number' && data.next_cursor === prevCursor && typeof data.remaining === 'number' && data.remaining > 0) {{
                        const loopMsg = `⚠️ Test ${{providerLabel}} fermato: cursor bloccato su ${{cursor}} (remaining=${{data.remaining}})`;
                        if (progressMsgEl) renderProgressMessage(loopMsg);
                        else addMessage(loopMsg, 'system');
                        break;
                    }}

                    // Se non ci sono più modelli da testare, fine
                    if (typeof data.remaining !== 'number' || data.remaining <= 0) {{
                        break;
                    }}

                    // Piccola pausa per non saturare NVIDIA
                    await new Promise(r => setTimeout(r, 500));
                }}

                // Messaggio riepilogo finale
                const parts = [];
                const tpl = isNvidia
                    ? (T.nvidia_test_result || 'NVIDIA Test: OK {{ok}}, removed {{removed}}, tested {{tested}}/{{total}}')
                    : ('Test ' + providerLabel + ': OK {{ok}}, removed {{removed}}, tested {{tested}}/{{total}}');
                parts.push(tpl.replace('{{ok}}', totalOk).replace('{{removed}}', totalRemoved).replace('{{tested}}', totalTested).replace('{{total}}', grandTotal));
                if (totalTested >= grandTotal) parts.push('\u2705 Completato!');
                const finalMsg = '\U0001f50d ' + parts.join(' ');
                if (progressMsgEl) renderProgressMessage(finalMsg);
                else addMessage(finalMsg, 'system');

                if (anyBlocklisted) await loadModels();
            }} catch (e) {{
                const errLbl = isNvidia ? (T.nvidia_test_failed || 'NVIDIA test failed') : ('Test ' + providerLabel + ' failed');
                const errMsg = '\u26a0\ufe0f ' + errLbl + ': ' + (e && e.message ? e.message : String(e));
                if (progressMsgEl) renderProgressMessage(errMsg);
                else addMessage(errMsg, 'system');
            }} finally {{
                btn.disabled = false;
                btn.textContent = oldText;
                window.__batchTestRunning = false;
                window.__batchTestStopRequested = false;
            }}
        }}

        // Change model (with automatic provider switch)
        async function changeModel(value) {{
            try {{
                // value can be a JSON string (legacy) or plain model name (new two-select)
                let parsed;
                try {{ parsed = JSON.parse(value); }} catch(e) {{
                    // New style: model name from #modelSelect, provider from #providerSelect
                    const provSel = document.getElementById('providerSelect');
                    parsed = {{ model: value, provider: provSel ? provSel.value : currentProviderId }};
                }}
                const response = await fetch(apiUrl('api/set_model'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{model: parsed.model, provider: parsed.provider}})
                }});
                if (response.ok) {{
                    const data = await response.json();
                    console.log('Model changed to:', parsed.model, 'Provider:', parsed.provider);
                    const O4MINI_TOKENS_HINT = {o4mini_tokens_hint_js};
                    // Keep UI state in sync so the thinking message matches the selected provider
                    currentProviderId = parsed.provider;
                    currentModelDisplay = parsed.model;
                    updateBatchTestButton();
                    // Show notification
                    const providerName = PROVIDER_LABELS[parsed.provider] || parsed.provider;
                    addMessage('\U0001f504 ' + T.switched_to.replace('{{provider}}', providerName).replace('{{model}}', parsed.model), 'system');
                    maybeWarnWebDashboard(parsed.provider);
                    const modelLower = String(parsed.model || '').toLowerCase();
                    if (parsed.provider === 'github' && modelLower.includes('o4-mini') && O4MINI_TOKENS_HINT) {{
                        addMessage(O4MINI_TOKENS_HINT, 'system');
                    }}
                    // Refresh dropdown state from server (ensures UI stays consistent)
                    loadModels();
                    // Show OAuth banners for providers that need authentication
                    const _allSessionBanners = [
                        'codexOAuthBanner','codexOAuthConnectedBanner',
                        'copilotOAuthBanner','copilotOAuthConnectedBanner',
                        'claudeWebBanner','claudeWebConnectedBanner',
                        'chatgptWebBanner',
                        'geminiWebBanner','geminiWebConnectedBanner',
                        'perplexityWebBanner','perplexityWebConnectedBanner',
                    ];
                    // Hide all session banners, then show only the relevant ones
                    _allSessionBanners.forEach(id => {{ const el=document.getElementById(id); if(el) el.style.display='none'; }});
                    if (parsed.provider === 'openai_codex') {{
                        checkCodexOAuth();
                    }} else if (parsed.provider === 'github_copilot') {{
                        checkCopilotOAuth();
                    }} else if (parsed.provider === 'claude_web') {{
                        checkClaudeWebSession();
                    }} else if (parsed.provider === 'chatgpt_web') {{
                        checkChatGPTWebSession();
                    }} else if (parsed.provider === 'gemini_web') {{
                        checkGeminiWebSession();
                    }} else if (parsed.provider === 'perplexity_web') {{
                        checkPerplexityWebSession();
                    }}
                }}
            }} catch (error) {{
                console.error('Error changing model:', error);
            }}
        }}

        // Track last explicitly selected agent (survives loadModels rebuilds)
        let _lastExplicitAgent = null;

        // Change active agent
        async function changeAgent(agentId) {{
            if (!agentId) return;
            _lastExplicitAgent = agentId;
            localStorage.setItem('ha_claude_active_agent', agentId);
            try {{
                const response = await fetch(apiUrl('api/agents/set'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{agent_id: agentId}})
                }});
                if (response.ok) {{
                    const data = await response.json();
                    console.log('[changeAgent] Switched to agent:', agentId, data);
                    // Update header identity
                    const identity = data.identity || {{}};
                    if (identity.name) {{
                        const h1 = document.querySelector('.header h1');
                        if (h1) h1.textContent = identity.name;
                    }}
                    if (identity.emoji) {{
                        const emojiSpan = document.querySelector('.header > span');
                        if (emojiSpan) emojiSpan.textContent = identity.emoji;
                    }}
                    // Notify user
                    const agentLabel = (identity.emoji || '') + ' ' + (identity.name || agentId);
                    addMessage('\U0001f916 ' + T.switched_to.replace('{{provider}}', 'Agent').replace('{{model}}', agentLabel.trim()), 'system');
                    // Refresh dropdowns (agent may have changed provider/model)
                    await loadModels();
                }} else {{
                    console.error('[changeAgent] Failed:', response.status);
                }}
            }} catch (error) {{
                console.error('[changeAgent] Error:', error);
            }}
        }}

        // ---- OpenAI Codex OAuth helpers ----
        let _codexOAuthState = null;

        async function checkCodexOAuth() {{
            try {{
                const r = await fetch(apiUrl('api/oauth/codex/status'));
                const d = await r.json();
                const banner        = document.getElementById('codexOAuthBanner');
                const connBanner    = document.getElementById('codexOAuthConnectedBanner');
                const connDetail    = document.getElementById('codexConnDetail');
                if (d.configured) {{
                    if (banner)     banner.style.display = 'none';
                    if (connBanner) {{
                        // Build detail string: account id + expiry
                        let detail = 'connected';
                        if (d.account_id) detail = d.account_id;
                        if (d.expires_in_seconds != null) {{
                            const h = Math.floor(d.expires_in_seconds / 3600);
                            const m = Math.floor((d.expires_in_seconds % 3600) / 60);
                            const expStr = h > 0 ? `expires in ${{h}}h ${{m}}m` : `expires in ${{m}}m`;
                            detail += (d.account_id ? ' · ' : '') + expStr;
                        }}
                        if (connDetail) connDetail.textContent = detail;
                        connBanner.style.display = 'flex';
                    }}
                }} else {{
                    if (banner)     banner.style.display = 'flex';
                    if (connBanner) connBanner.style.display = 'none';
                }}
            }} catch (e) {{ /* silently ignore */ }}
        }}

        async function revokeCodexOAuth() {{
            if (!confirm('Disconnect OpenAI Codex? You will need to log in again to use it.')) return;
            try {{
                await fetch(apiUrl('api/oauth/codex/revoke'), {{ method: 'POST' }});
            }} catch (e) {{ /* ignore if endpoint missing */ }}
            // Hide connected banner, will show login banner next time Codex is selected
            const connBanner = document.getElementById('codexOAuthConnectedBanner');
            if (connBanner) connBanner.style.display = 'none';
            addMessage('🔒 OpenAI Codex disconnected. Select Codex provider to reconnect.', 'system');
            checkCodexOAuth();
        }}

        async function openCodexOAuthModal() {{
            // Reset state
            const statusEl = document.getElementById('codexOAuthStatus');
            const urlEl    = document.getElementById('codexRedirectUrl');
            if (statusEl) {{ statusEl.className = ''; statusEl.textContent = ''; }}
            if (urlEl)    urlEl.value = '';
            // Start OAuth flow → get authorize URL + state
            try {{
                const r = await fetch(apiUrl('api/oauth/codex/start'));
                const d = await r.json();
                if (!d.authorize_url) throw new Error(d.error || 'No URL returned');
                _codexOAuthState = d.state;
                const loginBtn = document.getElementById('codexOpenLoginBtn');
                if (loginBtn) {{
                    loginBtn.onclick = () => window.open(d.authorize_url, '_blank');
                }}
            }} catch (e) {{
                if (statusEl) {{
                    statusEl.className = 'err';
                    statusEl.textContent = 'Error starting OAuth: ' + (e.message || String(e));
                }}
            }}
            const modal = document.getElementById('codexOAuthModal');
            if (modal) modal.classList.add('open');
        }}

        function closeCodexOAuthModal() {{
            const modal = document.getElementById('codexOAuthModal');
            if (modal) modal.classList.remove('open');
            _codexOAuthState = null;
        }}

        async function submitCodexCode() {{
            const urlEl    = document.getElementById('codexRedirectUrl');
            const statusEl = document.getElementById('codexOAuthStatus');
            const btn      = document.getElementById('codexModalConnectBtn');
            if (!urlEl || !statusEl || !btn) return;
            const redirectUrl = urlEl.value.trim();
            if (!redirectUrl) {{
                statusEl.className = 'err';
                statusEl.textContent = 'Please paste the redirect URL first.';
                return;
            }}
            if (!_codexOAuthState) {{
                statusEl.className = 'err';
                statusEl.textContent = 'Session expired — please close and try again.';
                return;
            }}
            btn.disabled = true;
            btn.textContent = 'Connecting...';
            statusEl.className = '';
            statusEl.textContent = '';
            try {{
                const r = await fetch(apiUrl('api/oauth/codex/exchange'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ redirect_url: redirectUrl, state: _codexOAuthState }})
                }});
                const d = await r.json();
                if (d.ok) {{
                    statusEl.className = 'ok';
                    statusEl.textContent = '\u2714 Connected! Token saved.';
                    setTimeout(() => {{
                        closeCodexOAuthModal();
                        checkCodexOAuth();
                        addMessage('\u2705 OpenAI Codex authenticated successfully.', 'system');
                    }}, 1500);
                }} else {{
                    throw new Error(d.error || 'Exchange failed');
                }}
            }} catch (e) {{
                statusEl.className = 'err';
                statusEl.textContent = '\u26a0\ufe0f ' + (e.message || String(e));
            }} finally {{
                btn.disabled = false;
                btn.textContent = '\u2714 Connect';
            }}
        }}
        // ---- GitHub Copilot OAuth helpers ----
        let _copilotPollTimer = null;
        let _copilotPollInterval = 5;

        async function checkCopilotOAuth() {{
            try {{
                const r = await fetch(apiUrl('api/oauth/copilot/status'));
                const d = await r.json();
                const banner     = document.getElementById('copilotOAuthBanner');
                const connBanner = document.getElementById('copilotOAuthConnectedBanner');
                const connDetail = document.getElementById('copilotConnDetail');
                if (d.configured) {{
                    if (banner)     banner.style.display = 'none';
                    if (connBanner) {{
                        let detail = 'connected';
                        if (d.age_days != null) detail = 'connected ' + d.age_days + 'd ago';
                        if (connDetail) connDetail.textContent = detail;
                        connBanner.style.display = 'flex';
                    }}
                }} else {{
                    if (banner)     banner.style.display = 'flex';
                    if (connBanner) connBanner.style.display = 'none';
                }}
            }} catch (e) {{ /* ignore */ }}
        }}

        async function revokeCopilotOAuth() {{
            if (!confirm('Disconnect GitHub Copilot? You will need to re-authenticate to use it.')) return;
            try {{
                await fetch(apiUrl('api/oauth/copilot/revoke'), {{ method: 'POST' }});
            }} catch (e) {{ /* ignore */ }}
            const connBanner = document.getElementById('copilotOAuthConnectedBanner');
            if (connBanner) connBanner.style.display = 'none';
            addMessage('\U0001F512 GitHub Copilot disconnected. Select Copilot provider to reconnect.', 'system');
            checkCopilotOAuth();
        }}

        async function openCopilotOAuthModal() {{
            const statusEl  = document.getElementById('copilotOAuthStatus');
            const codeEl    = document.getElementById('copilotUserCode');
            const hintEl    = document.getElementById('copilotPollHint');
            const linkEl    = document.getElementById('copilotVerifyLink');
            if (statusEl) {{ statusEl.className = ''; statusEl.textContent = ''; }}
            if (codeEl)   codeEl.textContent = '\u2026';
            if (hintEl)   hintEl.textContent = 'Starting\u2026';
            _stopCopilotPoll();
            try {{
                const r = await fetch(apiUrl('api/oauth/copilot/start'));
                const d = await r.json();
                if (d.error) throw new Error(d.error);
                if (codeEl)  codeEl.textContent = d.user_code || '?';
                if (hintEl)  hintEl.textContent = 'Waiting for you to authorize on GitHub\u2026';
                if (linkEl)  linkEl.href = d.verification_uri || 'https://github.com/login/device';
                _copilotPollInterval = d.interval || 5;
                const modal = document.getElementById('copilotOAuthModal');
                if (modal) modal.classList.add('open');
                _startCopilotPoll();
            }} catch (e) {{
                if (statusEl) {{ statusEl.className = 'err'; statusEl.textContent = 'Error: ' + (e.message || String(e)); }}
                const modal = document.getElementById('copilotOAuthModal');
                if (modal) modal.classList.add('open');
            }}
        }}

        function closeCopilotOAuthModal() {{
            _stopCopilotPoll();
            const modal = document.getElementById('copilotOAuthModal');
            if (modal) modal.classList.remove('open');
        }}

        function _startCopilotPoll() {{
            _copilotPollTimer = setInterval(_doCopilotPoll, _copilotPollInterval * 1000);
        }}

        function _stopCopilotPoll() {{
            if (_copilotPollTimer) {{ clearInterval(_copilotPollTimer); _copilotPollTimer = null; }}
        }}

        async function _doCopilotPoll() {{
            try {{
                const r = await fetch(apiUrl('api/oauth/copilot/poll'));
                const d = await r.json();
                const statusEl = document.getElementById('copilotOAuthStatus');
                const hintEl   = document.getElementById('copilotPollHint');
                if (d.status === 'success') {{
                    _stopCopilotPoll();
                    if (statusEl) {{ statusEl.className = 'ok'; statusEl.textContent = '\u2714 Connected! Token saved.'; }}
                    if (hintEl)   hintEl.textContent = '';
                    setTimeout(() => {{
                        closeCopilotOAuthModal();
                        checkCopilotOAuth();
                        addMessage('\u2705 GitHub Copilot authenticated successfully.', 'system');
                    }}, 1500);
                }} else if (d.status === 'error') {{
                    _stopCopilotPoll();
                    if (statusEl) {{ statusEl.className = 'err'; statusEl.textContent = '\u26a0\ufe0f ' + (d.message || 'Error'); }}
                    if (hintEl)   hintEl.textContent = '';
                }} else if (d.slow_down) {{
                    _copilotPollInterval = Math.min(_copilotPollInterval + 5, 30);
                    _stopCopilotPoll();
                    _startCopilotPoll();
                }}
            }} catch (e) {{ /* ignore transient network errors during polling */ }}
        }}

        // ---- Claude Web session helpers ----
        async function checkClaudeWebSession() {{
            try {{
                const r = await fetch(apiUrl('api/session/claude_web/status'));
                const d = await r.json();
                const banner     = document.getElementById('claudeWebBanner');
                const connBanner = document.getElementById('claudeWebConnectedBanner');
                const connDetail = document.getElementById('claudeWebConnDetail');
                if (d.configured) {{
                    if (banner)     banner.style.display = 'none';
                    if (connBanner) {{
                        let detail = 'connected';
                        if (d.age_days != null) detail = 'connected ' + d.age_days + 'd ago';
                        if (d.org_uuid) detail += ' \u00b7 org ' + d.org_uuid;
                        if (connDetail) connDetail.textContent = detail;
                        connBanner.style.display = 'flex';
                    }}
                }} else {{
                    if (banner)     banner.style.display = 'flex';
                    if (connBanner) connBanner.style.display = 'none';
                }}
            }} catch (e) {{ /* ignore */ }}
        }}

        async function disconnectClaudeWeb() {{
            if (!confirm('Disconnect Claude.ai Web? You will need to re-enter the session token to use it.')) return;
            try {{
                await fetch(apiUrl('api/session/claude_web/clear'), {{ method: 'POST' }});
            }} catch (e) {{ /* ignore */ }}
            const connBanner = document.getElementById('claudeWebConnectedBanner');
            if (connBanner) connBanner.style.display = 'none';
            addMessage('\U0001F512 Claude.ai Web disconnected.', 'system');
            checkClaudeWebSession();
        }}

        function openClaudeWebModal() {{
            const statusEl = document.getElementById('claudeWebStatus');
            const inputEl  = document.getElementById('claudeWebSessionKeyInput');
            if (statusEl) {{ statusEl.className = ''; statusEl.textContent = ''; }}
            if (inputEl)  inputEl.value = '';
            const modal = document.getElementById('claudeWebModal');
            if (modal) modal.classList.add('open');
        }}

        function closeClaudeWebModal() {{
            const modal = document.getElementById('claudeWebModal');
            if (modal) modal.classList.remove('open');
        }}

        async function submitClaudeWebToken() {{
            const inputEl  = document.getElementById('claudeWebSessionKeyInput');
            const statusEl = document.getElementById('claudeWebStatus');
            const btn      = document.getElementById('claudeWebModalConnectBtn');
            if (!inputEl || !statusEl || !btn) return;
            const sessionKey = inputEl.value.trim();
            if (!sessionKey) {{ statusEl.className = 'err'; statusEl.textContent = 'Please paste the session key first.'; return; }}
            btn.disabled = true; btn.textContent = 'Saving...';
            statusEl.className = ''; statusEl.textContent = '';
            try {{
                const r = await fetch(apiUrl('api/session/claude_web/store'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ session_key: sessionKey }})
                }});
                const d = await r.json();
                if (d.ok || d.configured) {{
                    statusEl.className = 'ok'; statusEl.textContent = '\u2714 Session saved!';
                    setTimeout(() => {{ closeClaudeWebModal(); checkClaudeWebSession(); addMessage('\u2705 Claude.ai Web session token saved.', 'system'); }}, 1200);
                }} else {{
                    throw new Error(d.error || 'Save failed');
                }}
            }} catch (e) {{
                statusEl.className = 'err'; statusEl.textContent = '\u26a0\ufe0f ' + (e.message || String(e));
            }} finally {{
                btn.disabled = false; btn.textContent = '\u2714 Save';
            }}
        }}

        // ---- ChatGPT Web session helpers ----
        async function checkChatGPTWebSession() {{
            try {{
                const r = await fetch(apiUrl('api/session/chatgpt_web/status'));
                const d = await r.json();
                const banner = document.getElementById('chatgptWebBanner');
                if (!banner) return;
                if (d.configured) {{
                    // Show compact green banner with reconfigure button
                    banner.className = 'configured';
                    banner.style.display = 'flex';
                    banner.innerHTML = '&#9989; <strong>ChatGPT Web</strong> &mdash; Token configurato' +
                        (d.age_days ? ` (${{d.age_days}}g fa)` : '') +
                        ' &nbsp;<button id="chatgptWebConnectBtn">&#128273; Riconfigura</button>' +
                        '<button id="chatgptWebDismissBtn" style="background:#c8e6c9;color:#1b5e20;">Nascondi</button>';
                    document.getElementById('chatgptWebConnectBtn')?.addEventListener('click', openChatGPTWebModal);
                    document.getElementById('chatgptWebDismissBtn')?.addEventListener('click', () => {{ banner.style.display='none'; }});
                }} else {{
                    banner.className = '';
                    banner.style.display = 'flex';
                    banner.innerHTML = '&#9888;&#65039; <strong>ChatGPT Web [UNSTABLE]</strong> &mdash; access token required.' +
                        ' <button id="chatgptWebConnectBtn">Set Access Token</button>' +
                        '<button id="chatgptWebDismissBtn" style="background:#fff3e0;color:#7c4a00;">Dismiss</button>';
                    document.getElementById('chatgptWebConnectBtn')?.addEventListener('click', openChatGPTWebModal);
                    document.getElementById('chatgptWebDismissBtn')?.addEventListener('click', () => {{ banner.style.display='none'; }});
                }}
            }} catch (e) {{ /* ignore */ }}
        }}

        function openChatGPTWebModal() {{
            const statusEl = document.getElementById('chatgptWebStatus');
            const inputEl  = document.getElementById('chatgptWebTokenInput');
            if (statusEl) {{ statusEl.className = ''; statusEl.textContent = ''; }}
            if (inputEl)  inputEl.value = '';
            const modal = document.getElementById('chatgptWebModal');
            if (modal) modal.classList.add('open');
        }}

        function closeChatGPTWebModal() {{
            const modal = document.getElementById('chatgptWebModal');
            if (modal) modal.classList.remove('open');
        }}

        function previewChatGPTTokens() {{
            const raw = (document.getElementById('chatgptWebTokenInput')?.value || '').trim();
            const preview = document.getElementById('chatgptWebPreview');
            if (!raw.startsWith('{{')) {{ if (preview) preview.style.display = 'none'; return; }}
            try {{
                const parsed = JSON.parse(raw);
                const at = parsed.accessToken || parsed.access_token || '';
                const st = parsed.sessionToken || '';
                if (!at) {{ if (preview) preview.style.display = 'none'; return; }}
                document.getElementById('previewAccessToken').textContent = at.slice(0,12) + '...' + at.slice(-6);
                document.getElementById('previewSessionToken').textContent = st ? st.slice(0,12) + '...' + st.slice(-6) : '(non trovato)';
                if (preview) preview.style.display = 'block';
            }} catch(e) {{ if (preview) preview.style.display = 'none'; }}
        }}

        async function submitChatGPTWebToken() {{
            const inputEl  = document.getElementById('chatgptWebTokenInput');
            const statusEl = document.getElementById('chatgptWebStatus');
            const btn      = document.getElementById('chatgptWebModalConnectBtn');
            const cfEl     = document.getElementById('chatgptWebCfClearance');
            if (!inputEl || !statusEl || !btn) return;
            const accessToken  = inputEl.value.trim();
            const cfClearance  = cfEl ? cfEl.value.trim() : '';
            if (!accessToken) {{ statusEl.className = 'err'; statusEl.textContent = 'Incolla prima il JSON o il token.'; return; }}
            btn.disabled = true; btn.textContent = 'Salvataggio...';
            statusEl.className = ''; statusEl.textContent = '';
            try {{
                const payload = {{ access_token: accessToken }};
                if (cfClearance) payload.cf_clearance = cfClearance;
                const r = await fetch(apiUrl('api/session/chatgpt_web/store'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(payload)
                }});
                const d = await r.json();
                if (d.ok || d.configured) {{
                    const hasSession = d.has_session_token ? ' + sessionToken' : '';
                    const hasCf = d.has_cf_clearance ? ' + cf_clearance' : '';
                    statusEl.className = 'ok'; statusEl.textContent = `\u2714 Salvato! accessToken${{hasSession}}${{hasCf}}`;
                    setTimeout(() => {{ closeChatGPTWebModal(); checkChatGPTWebSession(); addMessage('\u2705 ChatGPT Web connesso.', 'system'); }}, 1400);
                }} else {{
                    throw new Error(d.error || 'Salvataggio fallito');
                }}
            }} catch (e) {{
                statusEl.className = 'err'; statusEl.textContent = '\u26a0\ufe0f ' + (e.message || String(e));
            }} finally {{
                btn.disabled = false; btn.textContent = '\u2714 Save';
            }}
        }}

        // ── Gemini Web session helpers ────────────────────────────────────────
        async function checkGeminiWebSession() {{
            try {{
                const r = await fetch(apiUrl('api/session/gemini_web/status'));
                const d = await r.json();
                const banner = document.getElementById('geminiWebBanner');
                const connBanner = document.getElementById('geminiWebConnectedBanner');
                if (!banner) return;
                if (d.configured) {{
                    if (banner) banner.style.display = 'none';
                    if (connBanner) {{
                        connBanner.style.display = 'flex';
                        const det = document.getElementById('geminiWebConnDetail');
                        if (det) det.textContent = d.age_days ? `connesso (${{d.age_days}}g fa)` : 'connesso';
                    }}
                }} else {{
                    if (connBanner) connBanner.style.display = 'none';
                    banner.style.display = 'flex';
                }}
            }} catch (e) {{ /* ignore */ }}
        }}

        function openGeminiWebModal() {{
            const statusEl = document.getElementById('geminiWebStatus');
            const psidEl   = document.getElementById('geminiWebPsidInput');
            const psidtsEl = document.getElementById('geminiWebPsidtsInput');
            if (statusEl) {{ statusEl.className = ''; statusEl.textContent = ''; }}
            if (psidEl)   psidEl.value = '';
            if (psidtsEl) psidtsEl.value = '';
            const modal = document.getElementById('geminiWebModal');
            if (modal) modal.classList.add('open');
        }}

        function closeGeminiWebModal() {{
            const modal = document.getElementById('geminiWebModal');
            if (modal) modal.classList.remove('open');
        }}

        async function submitGeminiWebCookies() {{
            const psidEl   = document.getElementById('geminiWebPsidInput');
            const psidtsEl = document.getElementById('geminiWebPsidtsInput');
            const statusEl = document.getElementById('geminiWebStatus');
            const btn      = document.getElementById('geminiWebModalConnectBtn');
            if (!psidEl || !psidtsEl || !statusEl || !btn) return;
            const psid   = psidEl.value.trim();
            const psidts = psidtsEl.value.trim();
            if (!psid || !psidts) {{
                statusEl.className = 'err';
                statusEl.textContent = 'Incolla entrambi i cookie (__Secure-1PSID e __Secure-1PSIDTS).';
                return;
            }}
            btn.disabled = true; btn.textContent = 'Connessione...';
            statusEl.className = ''; statusEl.textContent = '';
            try {{
                const r = await fetch(apiUrl('api/session/gemini_web/store'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ psid, psidts }})
                }});
                const d = await r.json();
                if (d.ok || d.psid) {{
                    statusEl.className = 'ok'; statusEl.textContent = '\u2714 Cookie salvati e sessione validata!';
                    setTimeout(() => {{ closeGeminiWebModal(); checkGeminiWebSession(); addMessage('\u2705 Gemini Web connesso.', 'system'); }}, 1400);
                }} else {{
                    throw new Error(d.error || 'Salvataggio fallito');
                }}
            }} catch (e) {{
                statusEl.className = 'err'; statusEl.textContent = '\u26a0\ufe0f ' + (e.message || String(e));
            }} finally {{
                btn.disabled = false; btn.textContent = '\u2714 Connetti';
            }}
        }}

        // ── Perplexity Web session helpers ───────────────────────────────────
        async function checkPerplexityWebSession() {{
            try {{
                const r = await fetch(apiUrl('api/session/perplexity_web/status'));
                const d = await r.json();
                const banner = document.getElementById('perplexityWebBanner');
                const connBanner = document.getElementById('perplexityWebConnectedBanner');
                if (!banner) return;
                if (d.configured) {{
                    if (banner) banner.style.display = 'none';
                    if (connBanner) {{
                        connBanner.style.display = 'flex';
                        const det = document.getElementById('perplexityWebConnDetail');
                        let detail = d.age_days ? `connected (${{d.age_days}}d ago)` : 'connected';
                        if (d.email) detail += ` · ${{d.email}}`;
                        if (det) det.textContent = detail;
                    }}
                }} else {{
                    if (connBanner) connBanner.style.display = 'none';
                    banner.style.display = 'flex';
                }}
            }} catch (e) {{ /* ignore */ }}
        }}

        function openPerplexityWebModal() {{
            const statusEl = document.getElementById('perplexityWebStatus');
            const csrfEl   = document.getElementById('perplexityWebCsrfInput');
            const sessEl   = document.getElementById('perplexityWebSessionInput');
            if (statusEl) {{ statusEl.className = ''; statusEl.textContent = ''; }}
            if (csrfEl) csrfEl.value = '';
            if (sessEl) sessEl.value = '';
            const modal = document.getElementById('perplexityWebModal');
            if (modal) modal.classList.add('open');
        }}

        function closePerplexityWebModal() {{
            const modal = document.getElementById('perplexityWebModal');
            if (modal) modal.classList.remove('open');
        }}

        async function submitPerplexityWebCookies() {{
            const csrfEl = document.getElementById('perplexityWebCsrfInput');
            const sessEl = document.getElementById('perplexityWebSessionInput');
            const statusEl = document.getElementById('perplexityWebStatus');
            const btn = document.getElementById('perplexityWebModalConnectBtn');
            if (!csrfEl || !sessEl || !statusEl || !btn) return;
            const csrfToken = csrfEl.value.trim();
            const sessionToken = sessEl.value.trim();
            if (!csrfToken || !sessionToken) {{
                statusEl.className = 'err';
                statusEl.textContent = 'Paste both cookies first.';
                return;
            }}
            btn.disabled = true; btn.textContent = 'Connecting...';
            statusEl.className = ''; statusEl.textContent = '';
            try {{
                const r = await fetch(apiUrl('api/session/perplexity_web/store'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ csrf_token: csrfToken, session_token: sessionToken }})
                }});
                const d = await r.json();
                if (d.ok || d.configured || d.csrf_token) {{
                    statusEl.className = 'ok';
                    statusEl.textContent = '\u2714 Cookies saved and validated!';
                    setTimeout(() => {{
                        closePerplexityWebModal();
                        checkPerplexityWebSession();
                        addMessage('\u2705 Perplexity Web connected.', 'system');
                    }}, 1300);
                }} else {{
                    throw new Error(d.error || 'Save failed');
                }}
            }} catch (e) {{
                statusEl.className = 'err';
                statusEl.textContent = '\u26a0\ufe0f ' + (e.message || String(e));
            }} finally {{
                btn.disabled = false; btn.textContent = '\u2714 Connect';
            }}
        }}

        // Load history on page load
        function bindCspSafeHandlers() {{
            try {{
                // Bind controls without relying on inline handlers (CSP blocks onclick/onchange in HA Ingress)
                const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
                if (sidebarToggleBtn) sidebarToggleBtn.addEventListener('click', toggleSidebar);

                // Provider select: repopulate model select, then apply change
                const providerSelect = document.getElementById('providerSelect');
                const modelSelect = document.getElementById('modelSelect');
                const agentSelect = document.getElementById('agentSelect');

                // Track open/closed state so loadModels() skips DOM reset while user browses
                [providerSelect, modelSelect, agentSelect].forEach(sel => {{
                    if (!sel) return;
                    sel.addEventListener('mousedown', () => {{ _selectOpen = true; }});
                    sel.addEventListener('focus',     () => {{ _selectOpen = true; }});
                    sel.addEventListener('blur',      () => {{ _selectOpen = false; }});
                    sel.addEventListener('change',    () => {{ _selectOpen = false; }});
                    sel.addEventListener('keydown', (e) => {{
                        // Escape or Tab closes without selecting — clear flag
                        if (e.key === 'Escape' || e.key === 'Tab') _selectOpen = false;
                    }});
                }});

                // Agent select: switch active agent
                if (agentSelect) agentSelect.addEventListener('change', (e) => changeAgent(e.target.value));

                if (providerSelect) providerSelect.addEventListener('change', (e) => {{
                    const pid = e.target.value;
                    // Repopulate models for this provider, pre-select first
                    if (_modelsData) {{
                        const models = (_modelsData.models || {{}})[pid] || [];
                        populateModelSelect(pid, models[0] || '');
                    }}
                    // Auto-apply: switch to first model of selected provider
                    if (modelSelect && modelSelect.value) changeModel(modelSelect.value);
                }});

                // Model select: apply change on selection
                if (modelSelect) modelSelect.addEventListener('change', (e) => changeModel(e.target.value));

                const testBtn = document.getElementById('testNvidiaBtn');
                if (testBtn) testBtn.addEventListener('click', testNvidiaModel);

                const newChatBtn = document.getElementById('newChatBtn');
                if (newChatBtn) newChatBtn.addEventListener('click', newChat);

                // Codex OAuth banner/modal bindings
                const codexConnectBtn  = document.getElementById('codexOAuthConnectBtn');
                const codexDismissBtn  = document.getElementById('codexOAuthDismissBtn');
                const codexCancelBtn   = document.getElementById('codexModalCancelBtn');
                const codexSubmitBtn   = document.getElementById('codexModalConnectBtn');
                if (codexConnectBtn)  codexConnectBtn.addEventListener('click', openCodexOAuthModal);
                if (codexDismissBtn)  codexDismissBtn.addEventListener('click', () => {{
                    const banner = document.getElementById('codexOAuthBanner');
                    if (banner) banner.style.display = 'none';
                }});
                if (codexCancelBtn)   codexCancelBtn.addEventListener('click', closeCodexOAuthModal);
                if (codexSubmitBtn)   codexSubmitBtn.addEventListener('click', submitCodexCode);

                // Copilot OAuth banner/modal bindings
                const copilotConnectBtn = document.getElementById('copilotOAuthConnectBtn');
                const copilotDismissBtn = document.getElementById('copilotOAuthDismissBtn');
                const copilotCancelBtn  = document.getElementById('copilotModalCancelBtn');
                if (copilotConnectBtn) copilotConnectBtn.addEventListener('click', openCopilotOAuthModal);
                if (copilotDismissBtn) copilotDismissBtn.addEventListener('click', () => {{
                    const banner = document.getElementById('copilotOAuthBanner');
                    if (banner) banner.style.display = 'none';
                }});
                if (copilotCancelBtn)  copilotCancelBtn.addEventListener('click', closeCopilotOAuthModal);

                // Claude Web session banner/modal bindings
                const claudeWebConnectBtn  = document.getElementById('claudeWebConnectBtn');
                const claudeWebDismissBtn  = document.getElementById('claudeWebDismissBtn');
                const claudeWebCancelBtn   = document.getElementById('claudeWebModalCancelBtn');
                const claudeWebSubmitBtn   = document.getElementById('claudeWebModalConnectBtn');
                if (claudeWebConnectBtn) claudeWebConnectBtn.addEventListener('click', openClaudeWebModal);
                if (claudeWebDismissBtn) claudeWebDismissBtn.addEventListener('click', () => {{
                    const banner = document.getElementById('claudeWebBanner');
                    if (banner) banner.style.display = 'none';
                }});
                if (claudeWebCancelBtn) claudeWebCancelBtn.addEventListener('click', closeClaudeWebModal);
                if (claudeWebSubmitBtn) claudeWebSubmitBtn.addEventListener('click', submitClaudeWebToken);

                // ChatGPT Web session banner/modal bindings
                const chatgptWebConnectBtn  = document.getElementById('chatgptWebConnectBtn');
                const chatgptWebDismissBtn  = document.getElementById('chatgptWebDismissBtn');
                const chatgptWebCancelBtn   = document.getElementById('chatgptWebModalCancelBtn');
                const chatgptWebSubmitBtn   = document.getElementById('chatgptWebModalConnectBtn');
                if (chatgptWebConnectBtn) chatgptWebConnectBtn.addEventListener('click', openChatGPTWebModal);
                if (chatgptWebDismissBtn) chatgptWebDismissBtn.addEventListener('click', () => {{
                    const banner = document.getElementById('chatgptWebBanner');
                    if (banner) banner.style.display = 'none';
                }});
                if (chatgptWebCancelBtn) chatgptWebCancelBtn.addEventListener('click', closeChatGPTWebModal);
                if (chatgptWebSubmitBtn) chatgptWebSubmitBtn.addEventListener('click', submitChatGPTWebToken);

                // Gemini Web session banner/modal bindings
                const geminiWebConnectBtn  = document.getElementById('geminiWebConnectBtn');
                const geminiWebDismissBtn  = document.getElementById('geminiWebDismissBtn');
                const geminiWebDisconnBtn  = document.getElementById('geminiWebDisconnectBtn');
                const geminiWebCancelBtn   = document.getElementById('geminiWebModalCancelBtn');
                const geminiWebSubmitBtn   = document.getElementById('geminiWebModalConnectBtn');
                if (geminiWebConnectBtn) geminiWebConnectBtn.addEventListener('click', openGeminiWebModal);
                if (geminiWebDismissBtn) geminiWebDismissBtn.addEventListener('click', () => {{
                    const banner = document.getElementById('geminiWebBanner');
                    if (banner) banner.style.display = 'none';
                }});
                if (geminiWebDisconnBtn) geminiWebDisconnBtn.addEventListener('click', async () => {{
                    await fetch(apiUrl('api/session/gemini_web/clear'), {{method:'POST'}});
                    checkGeminiWebSession();
                    addMessage('\u26a0\ufe0f Gemini Web disconnesso.', 'system');
                }});
                if (geminiWebCancelBtn) geminiWebCancelBtn.addEventListener('click', closeGeminiWebModal);
                if (geminiWebSubmitBtn) geminiWebSubmitBtn.addEventListener('click', submitGeminiWebCookies);

                // Perplexity Web session banner/modal bindings
                const perplexityWebConnectBtn = document.getElementById('perplexityWebConnectBtn');
                const perplexityWebDismissBtn = document.getElementById('perplexityWebDismissBtn');
                const perplexityWebDisconnBtn = document.getElementById('perplexityWebDisconnectBtn');
                const perplexityWebCancelBtn  = document.getElementById('perplexityWebModalCancelBtn');
                const perplexityWebSubmitBtn  = document.getElementById('perplexityWebModalConnectBtn');
                if (perplexityWebConnectBtn) perplexityWebConnectBtn.addEventListener('click', openPerplexityWebModal);
                if (perplexityWebDismissBtn) perplexityWebDismissBtn.addEventListener('click', () => {{
                    const banner = document.getElementById('perplexityWebBanner');
                    if (banner) banner.style.display = 'none';
                }});
                if (perplexityWebDisconnBtn) perplexityWebDisconnBtn.addEventListener('click', async () => {{
                    await fetch(apiUrl('api/session/perplexity_web/clear'), {{method:'POST'}});
                    checkPerplexityWebSession();
                    addMessage('\u26a0\ufe0f Perplexity Web disconnected.', 'system');
                }});
                if (perplexityWebCancelBtn) perplexityWebCancelBtn.addEventListener('click', closePerplexityWebModal);
                if (perplexityWebSubmitBtn) perplexityWebSubmitBtn.addEventListener('click', submitPerplexityWebCookies);

                // Messaging chat modal close
                const msgModalCloseBtn = document.getElementById('msgModalCloseBtn');
                if (msgModalCloseBtn) msgModalCloseBtn.addEventListener('click', () => {{
                    document.getElementById('messagingChatModal').classList.remove('open');
                }});
                const msgChatModal = document.getElementById('messagingChatModal');
                if (msgChatModal) msgChatModal.addEventListener('click', (e) => {{
                    if (e.target === msgChatModal) msgChatModal.classList.remove('open');
                }});

                // ChatGPT Web token live preview
                const cgptInput = document.getElementById('chatgptWebTokenInput');
                if (cgptInput) cgptInput.addEventListener('input', previewChatGPTTokens);

                const readOnlyToggle = document.getElementById('readOnlyToggle');
                if (readOnlyToggle) readOnlyToggle.addEventListener('change', (e) => toggleReadOnly(!!e.target.checked));

                if (imageInput) imageInput.addEventListener('change', handleImageSelect);
                const imageBtn = document.querySelector('.image-btn');
                if (imageBtn) imageBtn.addEventListener('click', () => imageInput && imageInput.click());

                const removeBtn = document.querySelector('.remove-image-btn');
                if (removeBtn) removeBtn.addEventListener('click', (e) => {{ e.preventDefault(); removeImage(); }});

                const documentInput = document.getElementById('documentInput');
                if (documentInput) documentInput.addEventListener('change', handleDocumentSelect);
                const fileBtn = document.getElementById('fileUploadBtn');
                if (fileBtn) fileBtn.addEventListener('click', () => documentInput && documentInput.click());

                const removeDocBtn = document.getElementById('removeDocBtn');
                if (removeDocBtn) {{
                    removeDocBtn.title = T.remove_document || 'Remove document';
                    removeDocBtn.addEventListener('click', (e) => {{ e.preventDefault(); removeDocument(); }});
                }}

                if (input) {{
                    input.addEventListener('keydown', handleKeyDown);
                    input.addEventListener('input', () => autoResize(input));
                }}
                bindInputToolbarButtons();

                // Suggestions: make clickable via JS (inline onclick may be blocked)
                document.querySelectorAll('.suggestion').forEach((el) => {{
                    el.addEventListener('click', () => sendSuggestion(el));
                }});

                // Sidebar tabs: bind click handlers (inline onclick blocked by CSP)
                document.querySelectorAll('.sidebar-tab').forEach((tab) => {{
                    tab.addEventListener('click', () => {{
                        const tabName = tab.dataset.tab;
                        if (tabName) switchSidebarTab(tabName);
                    }});
                }});

                // Copy buttons inside chat: use event delegation (inline onclick may be blocked)
                if (chat && !chat._copyDelegateBound) {{
                    chat._copyDelegateBound = true;
                    chat.addEventListener('click', (evt) => {{
                        const btn = evt && evt.target && evt.target.closest ? evt.target.closest('.copy-button') : null;
                        if (btn) {{
                            evt.preventDefault();
                            copyCode(btn);
                        }}
                    }});
                }}
            }} catch (e) {{
                console.warn('[ui] bindCspSafeHandlers failed', e);
            }}
        }}

        (async function bootUI() {{
            try {{
                // Initialize dark mode before anything else
                if (darkMode) {{
                    document.body.classList.add('dark-mode');
                }}

                // Reinforce click handler assignment (helps when inline onclick gets lost/cached)
                if (sendBtn) {{
                    sendBtn.onclick = () => handleButtonClick();
                }}

                bindCspSafeHandlers();
                bindInputToolbarButtons();

                initSidebarResize();
                initFilePanelResize();
                if (filePanelCloseAllEl) filePanelCloseAllEl.onclick = () => closeFilePanel();
                loadModels();
                loadChatList();
                loadHistory();
                setTimeout(checkSkillsUpdatesOnLoad, 3000);
                if (currentProviderId === 'openai_codex') checkCodexOAuth();
                if (currentProviderId === 'github_copilot') checkCopilotOAuth();
                if (currentProviderId === 'claude_web') checkClaudeWebSession();
                if (currentProviderId === 'chatgpt_web') checkChatGPTWebSession();
                if (currentProviderId === 'gemini_web') checkGeminiWebSession();
                if (currentProviderId === 'perplexity_web') checkPerplexityWebSession();
                if (input) input.focus();

                // ── Immediate SDK check on page load ──
                try {{
                    const _initStatus = await fetch(apiUrl('api/system/features'), {{credentials:'same-origin'}});
                    if (_initStatus.ok) {{
                        const _sf = await _initStatus.json();
                        if (_sf.provider_sdk_available === false) {{
                            const _m = _sf.provider_sdk_message || 'SDK mancante per il provider corrente';
                            const _mp = (_sf.missing_packages || []).join(', ');
                            let _w = '⚠️ ' + _m;
                            if (_mp) _w += '<br><small>Pacchetti mancanti: ' + _mp + '</small>';
                            _appendSystemRaw(_w);
                        }}
                    }}
                }} catch(_e) {{ /* ignore on boot */ }}

                // Poll every 10s for model/provider changes made from other UIs (e.g. bubble)
                let _statusFailures = 0;
                let _sdkWarningShown = false;
                const _webSessionInterval = setInterval(async () => {{
                    if (currentProviderId === 'chatgpt_web') checkChatGPTWebSession();
                    else if (currentProviderId === 'claude_web') checkClaudeWebSession();
                    else if (currentProviderId === 'gemini_web') checkGeminiWebSession();
                    else if (currentProviderId === 'perplexity_web') checkPerplexityWebSession();
                }}, 30000);
                const _statusInterval = setInterval(async () => {{
                    try {{
                        const r = await fetch(apiUrl('api/status'), {{credentials:'same-origin'}});
                        if (!r.ok) {{ _statusFailures++; }} else {{ _statusFailures = 0; }}
                        if (_statusFailures >= 1) {{
                            clearInterval(_statusInterval);
                            clearInterval(_webSessionInterval);
                            _appendSystemRaw('⚠️ Server non raggiungibile. Ricarica la pagina per riconnetterti.');
                            return;
                        }}
                        if (!r.ok) return;
                        const d = await r.json();
                        // ── SDK missing warning ──
                        if (d.provider_sdk_available === false && !_sdkWarningShown) {{
                            _sdkWarningShown = true;
                            const msg = d.provider_sdk_message || ('SDK mancante per il provider ' + d.provider);
                            const missing = (d.missing_packages || []).join(', ');
                            let warn = '⚠️ ' + msg;
                            if (missing) warn += '<br><small>Pacchetti mancanti: ' + missing + '</small>';
                            warn += '<br><small>Piattaforma: ' + (d.platform || '?') + '</small>';
                            _appendSystemRaw(warn);
                        }}
                        if (d.provider_sdk_available !== false) {{ _sdkWarningShown = false; }}
                        const sp = d.provider || '';
                        const sm = d.model || '';
                        if (sp && sm && (sp !== currentProviderId || sm !== currentModelDisplay)) {{
                            await loadModels();
                        }}
                    }} catch(e) {{
                        _statusFailures++;
                        if (_statusFailures >= 1) {{
                            clearInterval(_statusInterval);
                            clearInterval(_webSessionInterval);
                            _appendSystemRaw('⚠️ Server non raggiungibile. Ricarica la pagina per riconnetterti.');
                        }}
                    }}
                }}, 10000);
                // Poll session status every 30s for web providers so the banner reappears when token expires
                // (interval stored above as _webSessionInterval for cleanup on server disconnect)
            }} catch (e) {{
                const msg = (e && e.message) ? e.message : String(e);
                _appendSystemRaw('❌ UI boot error: ' + msg);
            }}
        }})();
        
        // Export global functions for onclick handlers
        window.handleDocumentSelect = handleDocumentSelect;
        window.removeDocument = removeDocument;
        window.changeModel = changeModel;
        window.handleButtonClick = handleButtonClick;
        window.switchSidebarTab = switchSidebarTab;
        window.installSkill = installSkill;
        window.deleteSkill  = deleteSkill;
        window.loadSkillsPanel = loadSkillsPanel;
        window.newChat = newChat;
        window.toggleSidebar = toggleSidebar;
        window.sendSuggestion = sendSuggestion;
        window.testNvidiaModel = testNvidiaModel;
        window.revokeCodexOAuth = revokeCodexOAuth;
        window.revokeCopilotOAuth = revokeCopilotOAuth;
        window.disconnectClaudeWeb = disconnectClaudeWeb;
        window.toggleDarkMode = toggleDarkMode;
        window.toggleReadOnly = toggleReadOnly;
        // MCP exports
        window.mcpInstallPkgs = mcpInstallPkgs;
        // File explorer exports
        window.loadFileTree = loadFileTree;
        window.openFileInPanel = openFileInPanel;
        window.closeFilePanelTab = closeFilePanelTab;
        window.closeFilePanel = closeFilePanel;
        }}
        
    </script>
</body>
</html>"""
