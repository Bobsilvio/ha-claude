"""Chat UI HTML generation for Home Assistant AI assistant."""

import json
import api


def get_chat_ui():
    """Generate the chat UI with image upload support."""
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
    analyzing_msg = analyzing_by_lang.get(api.LANGUAGE, analyzing_by_lang["en"])

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
    msgs = ui_messages.get(api.LANGUAGE, ui_messages["en"])

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
            "no_models_msg": "No models available. Check the provider API keys.",
            "models_load_error": "Error loading models: ",
            "nvidia_test_result": "NVIDIA Test: OK {ok}, removed {removed}, tested {tested}/{total}",
            "nvidia_timeout": "timeout: {n}",
            "nvidia_remaining": "remaining: {n} (press again to continue)",
            "nvidia_test_failed": "NVIDIA test failed",
            "switched_to": "Switched to {provider} \u2192 {model}",
            "provider_label": "Provider",
            "model_label": "Model",
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
            "mic_needs_https_short": "Microphone blocked (HTTP). See message above for Chrome workaround.",
            "mic_denied_settings": "Microphone access denied. Go to browser settings to enable it.",
            "mic_denied_icon": "Microphone denied. Click the 🔒 icon in the browser bar to enable it.",
            "mic_not_found": "No microphone found. Connect a microphone and try again.",
            "mic_in_use": "Microphone in use by another app. Close other apps and try again.",
            "mic_error": "Microphone error",
            # Voice mode
            "voice_mode": "Voice mode",
            "voice_mode_on": "Voice ON – responses will be read aloud",
            "voice_mode_off": "Voice OFF",
            "voice_listening": "Listening...",
            "voice_processing": "Processing audio...",
            "voice_tts_error": "Could not play voice response",
            "voice_tts_no_provider": "Voice output unavailable. Edge TTS or a Groq/OpenAI API key is needed.",
            "voice_transcription_error": "Transcription failed. Try again.",
            "voice_speaking": "Speaking...",
            "voice_stop_speaking": "Stop speaking",
            "wake_word_active": "Listening for 'Ok Amira'...",
            "wake_word_detected": "Amira activated! Speak now...",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
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
            "messaging_user": "User",
            "messaging_messages": "Messages",
            "messaging_last": "Last message",
            "messaging_delete": "Delete",
            "messaging_confirm_delete": "Delete this chat?",
            "no_backups": "No backups yet",
            "backup_file": "File",
            "backup_date": "Date",
            "restore": "Restore",
            "confirm_restore_backup": "Restore this backup? The current file will be replaced.",
            "delete_backup": "Delete",
            "confirm_delete_backup": "Delete this backup permanently?",
            "download_backup": "Download",
            # Device manager
            "no_devices": "No devices registered yet",
            "device_id": "Device ID",
            "device_name": "Name",
            "device_type": "Type",
            "device_enabled": "Enabled",
            "device_last_seen": "Last Seen",
            "enable_device": "Enable",
            "disable_device": "Disable",
            "rename_device": "Rename",
            "delete_device": "Delete",
            "confirm_delete_device": "Delete this device permanently?",
            "device_deleted": "Device deleted",
            "device_updated": "Device updated",
            # Dark mode
            "dark_mode": "Dark mode",
            "light_mode": "Light mode",
            # Costs tab
            "tab_costs": "Costs",
            "costs_today": "Today",
            "costs_total_tokens": "Total tokens",
            "costs_total_cost": "Total cost",
            "costs_by_model": "By model",
            "costs_by_provider": "By provider",
            "costs_history": "Last 7 days",
            "costs_no_data": "No usage data yet",
            "costs_reset": "Reset",
            "costs_reset_confirm": "Reset all usage statistics? This cannot be undone.",
            "costs_reset_done": "Usage data cleared",
            "costs_requests": "requests",
            "costs_tokens": "tokens",
            # Config tab
            "tab_config": "\U0001f527 Config",
            "config_loading": "Loading...",
            "config_save": "Save",
            "config_cancel": "Cancel",
            "config_saved": "Saved!",
            "config_save_error": "Save failed",
            "config_invalid_json": "Invalid JSON",
            "config_file_not_found": "File not found (will be created on save)",
            "config_agents_title": "Agent Profiles",
            "config_mcp_title": "MCP Configuration",
            "config_prompt_title": "Custom System Prompt",
            "config_memory_title": "Memory (MEMORY.md)",
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
            "agent_sysprompt_label": "System Prompt Override",
            "agent_sysprompt_hint": "Leave empty to use the default system prompt...",
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
            "tip_agent_sysprompt": "Custom instructions that override the default system prompt.",
            "tip_agent_tools": "Select which tools this agent can use. None selected = all tools available.",
            "tip_agent_default": "The default agent is used when no specific agent is selected.",
            "tip_agent_enabled": "Disabled agents are hidden from the agent selector.",
            # MCP form
            "mcp_add_server": "Add Server",
            "mcp_server_name": "Server Name",
            "mcp_command": "Command",
            "mcp_args": "Arguments",
            "mcp_env": "Environment Variables",
            "mcp_no_servers": "No MCP servers configured. Click \"Add Server\" to connect external tools.",
            "tip_mcp_name": "Unique name for this MCP server (e.g. filesystem, web_search).",
            "tip_mcp_command": "Command to start the server (e.g. python, uvx, npx).",
            "tip_mcp_args": "One argument per line. E.g. -m, mcp.server.stdio.",
            "tip_mcp_env": "One per line: KEY=VALUE. Environment variables for the server.",
            # System prompt form
            "prompt_chars": "characters",
            "prompt_reset": "Clear",
            "prompt_hint": "Write custom instructions here. They will be added to the default system prompt sent to the AI...",
            # Memory form
            "memory_hint": "Markdown notes the AI will remember across conversations...",
            "memory_lines": "lines",
            # Channel association
            "agent_channels": "Channel Assignment",
            "agent_channel_telegram": "Telegram",
            "agent_channel_whatsapp": "WhatsApp",
            "agent_channel_none": "-- none --",
            "tip_agent_channels": "Assign this agent to a messaging channel. Each channel can have one agent.",
            "agent_channel_badge": "Channel",
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
            "no_models_msg": "Nessun modello disponibile. Verifica le API key dei provider.",
            "models_load_error": "Errore nel caricamento dei modelli: ",
            "nvidia_test_result": "Test NVIDIA: OK {ok}, rimossi {removed}, testati {tested}/{total}",
            "nvidia_timeout": "timeout: {n}",
            "nvidia_remaining": "restanti: {n} (ripremi per continuare)",
            "nvidia_test_failed": "Test NVIDIA fallito",
            "switched_to": "Passato a {provider} \u2192 {model}",
            "provider_label": "Provider",
            "model_label": "Modello",
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
            "mic_needs_https_short": "Microfono bloccato (HTTP). Vedi il messaggio sopra per la soluzione Chrome.",
            "mic_denied_settings": "Accesso al microfono negato. Vai nelle impostazioni del browser per abilitarlo.",
            "mic_denied_icon": "Permesso microfono negato. Clicca l'icona 🔒 nella barra del browser per abilitarlo.",
            "mic_not_found": "Nessun microfono trovato. Collega un microfono e riprova.",
            "mic_in_use": "Microfono in uso da un'altra app. Chiudi le altre app e riprova.",
            "mic_error": "Errore microfono",
            # Voice mode
            "voice_mode": "Modalità voce",
            "voice_mode_on": "Voce ON – le risposte verranno lette ad alta voce",
            "voice_mode_off": "Voce OFF",
            "voice_listening": "In ascolto...",
            "voice_processing": "Elaborazione audio...",
            "voice_tts_error": "Impossibile riprodurre la risposta vocale",
            "voice_tts_no_provider": "Voce in uscita non disponibile. Serve Edge TTS o una API key Groq/OpenAI.",
            "voice_transcription_error": "Trascrizione fallita. Riprova.",
            "voice_speaking": "Sto parlando...",
            "voice_stop_speaking": "Ferma riproduzione",
            "wake_word_active": "In ascolto per 'Ok Amira'...",
            "wake_word_detected": "Amira attivata! Parla ora...",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
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
            "messaging_user": "Utente",
            "messaging_messages": "Messaggi",
            "messaging_last": "Ultimo messaggio",
            "messaging_delete": "Elimina",
            "messaging_confirm_delete": "Eliminare questa chat?",
            "no_backups": "Nessun backup",
            "backup_file": "File",
            "backup_date": "Data",
            "restore": "Ripristina",
            "confirm_restore_backup": "Ripristinare questo backup? Il file attuale verrà sostituito.",
            "delete_backup": "Elimina",
            "confirm_delete_backup": "Eliminare questo backup definitivamente?",
            "download_backup": "Scarica",
            # Device manager
            "no_devices": "Nessun dispositivo registrato",
            "device_id": "ID Dispositivo",
            "device_name": "Nome",
            "device_type": "Tipo",
            "device_enabled": "Abilitato",
            "device_last_seen": "Visto l'ultima volta",
            "enable_device": "Abilita",
            "disable_device": "Disabilita",
            "rename_device": "Rinomina",
            "delete_device": "Elimina",
            "confirm_delete_device": "Eliminare questo dispositivo definitivamente?",
            "device_deleted": "Dispositivo eliminato",
            "device_updated": "Dispositivo aggiornato",
            # Dark mode
            "dark_mode": "Tema scuro",
            "light_mode": "Tema chiaro",
            # Costs tab
            "tab_costs": "Costi",
            "costs_today": "Oggi",
            "costs_total_tokens": "Token totali",
            "costs_total_cost": "Costo totale",
            "costs_by_model": "Per modello",
            "costs_by_provider": "Per provider",
            "costs_history": "Ultimi 7 giorni",
            "costs_no_data": "Nessun dato di utilizzo",
            "costs_reset": "Azzera",
            "costs_reset_confirm": "Azzerare tutte le statistiche di utilizzo? Non si può annullare.",
            "costs_reset_done": "Dati di utilizzo azzerati",
            "costs_requests": "richieste",
            "costs_tokens": "token",
            # Config tab
            "tab_config": "\U0001f527 Config",
            "config_loading": "Caricamento...",
            "config_save": "Salva",
            "config_cancel": "Annulla",
            "config_saved": "Salvato!",
            "config_save_error": "Errore nel salvataggio",
            "config_invalid_json": "JSON non valido",
            "config_file_not_found": "File non trovato (verrà creato al salvataggio)",
            "config_agents_title": "Profili Agente",
            "config_mcp_title": "Configurazione MCP",
            "config_prompt_title": "System Prompt Personalizzato",
            "config_memory_title": "Memoria (MEMORY.md)",
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
            "agent_sysprompt_label": "System Prompt Personalizzato",
            "agent_sysprompt_hint": "Lascia vuoto per usare il prompt di sistema predefinito...",
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
            "tip_agent_sysprompt": "Istruzioni personalizzate che sostituiscono il prompt di sistema predefinito.",
            "tip_agent_tools": "Seleziona quali strumenti pu\u00f2 usare questo agente. Nessuno selezionato = tutti disponibili.",
            "tip_agent_default": "L'agente predefinito viene usato quando non ne viene selezionato uno specifico.",
            "tip_agent_enabled": "Gli agenti disabilitati sono nascosti dal selettore.",
            # MCP form
            "mcp_add_server": "Aggiungi Server",
            "mcp_server_name": "Nome Server",
            "mcp_command": "Comando",
            "mcp_args": "Argomenti",
            "mcp_env": "Variabili d'Ambiente",
            "mcp_no_servers": "Nessun server MCP configurato. Clicca \"Aggiungi Server\" per connettere strumenti esterni.",
            "tip_mcp_name": "Nome univoco per il server MCP (es. filesystem, web_search).",
            "tip_mcp_command": "Comando per avviare il server (es. python, uvx, npx).",
            "tip_mcp_args": "Un argomento per riga. Es. -m, mcp.server.stdio.",
            "tip_mcp_env": "Uno per riga: CHIAVE=VALORE. Variabili d'ambiente per il server.",
            # System prompt form
            "prompt_chars": "caratteri",
            "prompt_reset": "Cancella",
            "prompt_hint": "Scrivi istruzioni personalizzate qui. Verranno aggiunte al prompt di sistema predefinito inviato all'AI...",
            # Memory form
            "memory_hint": "Note in formato Markdown che l'AI ricorder\u00e0 tra le conversazioni...",
            "memory_lines": "righe",
            # Channel association
            "agent_channels": "Associazione Canali",
            "agent_channel_telegram": "Telegram",
            "agent_channel_whatsapp": "WhatsApp",
            "agent_channel_none": "-- nessuno --",
            "tip_agent_channels": "Associa questo agent a un canale di messaggistica. Ogni canale pu\u00f2 avere un solo agent.",
            "agent_channel_badge": "Canale",
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
            "no_models_msg": "Sin modelos disponibles. Verifica las API keys de los proveedores.",
            "models_load_error": "Error al cargar los modelos: ",
            "nvidia_test_result": "Test NVIDIA: OK {ok}, eliminados {removed}, probados {tested}/{total}",
            "nvidia_timeout": "timeout: {n}",
            "nvidia_remaining": "restantes: {n} (pulsa de nuevo para continuar)",
            "nvidia_test_failed": "Test NVIDIA fallido",
            "switched_to": "Cambiado a {provider} \u2192 {model}",
            "provider_label": "Proveedor",
            "model_label": "Modelo",
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
            "mic_needs_https_short": "Micrófono bloqueado (HTTP). Ver el mensaje anterior para la solución Chrome.",
            "mic_denied_settings": "Acceso al micrófono denegado. Ve a los ajustes del navegador para habilitarlo.",
            "mic_denied_icon": "Permiso de micrófono denegado. Haz clic en el icono 🔒 en la barra del navegador.",
            "mic_not_found": "No se encontró micrófono. Conecta un micrófono e inténtalo de nuevo.",
            "mic_in_use": "Micrófono en uso por otra app. Cierra las otras apps e inténtalo de nuevo.",
            "mic_error": "Error de micrófono",
            # Voice mode
            "voice_mode": "Modo voz",
            "voice_mode_on": "Voz ON – las respuestas se leerán en voz alta",
            "voice_mode_off": "Voz OFF",
            "voice_listening": "Escuchando...",
            "voice_processing": "Procesando audio...",
            "voice_tts_error": "No se pudo reproducir la respuesta de voz",
            "voice_tts_no_provider": "Salida de voz no disponible. Se necesita Edge TTS o una API key de Groq/OpenAI.",
            "voice_transcription_error": "Transcripción fallida. Inténtalo de nuevo.",
            "voice_speaking": "Hablando...",
            "voice_stop_speaking": "Detener reproducción",
            "wake_word_active": "Escuchando 'Ok Amira'...",
            "wake_word_detected": "¡Amira activada! Habla ahora...",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
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
            "messaging_user": "Usuario",
            "messaging_messages": "Mensajes",
            "messaging_last": "Último mensaje",
            "messaging_delete": "Eliminar",
            "messaging_confirm_delete": "¿Eliminar este chat?",
            "no_backups": "Sin copias de seguridad",
            "backup_file": "Archivo",
            "backup_date": "Fecha",
            "restore": "Restaurar",
            "confirm_restore_backup": "¿Restaurar esta copia? El archivo actual será reemplazado.",
            "delete_backup": "Eliminar",
            "confirm_delete_backup": "¿Eliminar esta copia de seguridad permanentemente?",
            "download_backup": "Descargar",
            # Device manager
            "no_devices": "Sin dispositivos registrados",
            "device_id": "ID del dispositivo",
            "device_name": "Nombre",
            "device_type": "Tipo",
            "device_enabled": "Habilitado",
            "device_last_seen": "Última vez visto",
            "enable_device": "Habilitar",
            "disable_device": "Deshabilitar",
            "rename_device": "Renombrar",
            "delete_device": "Eliminar",
            "confirm_delete_device": "¿Eliminar este dispositivo permanentemente?",
            "device_deleted": "Dispositivo eliminado",
            "device_updated": "Dispositivo actualizado",
            # Dark mode
            "dark_mode": "Tema oscuro",
            "light_mode": "Tema claro",
            # Costs tab
            "tab_costs": "Costes",
            "costs_today": "Hoy",
            "costs_total_tokens": "Tokens totales",
            "costs_total_cost": "Coste total",
            "costs_by_model": "Por modelo",
            "costs_by_provider": "Por proveedor",
            "costs_history": "Últimos 7 días",
            "costs_no_data": "Sin datos de uso",
            "costs_reset": "Restablecer",
            "costs_reset_confirm": "¿Restablecer todas las estadísticas? No se puede deshacer.",
            "costs_reset_done": "Datos de uso borrados",
            "costs_requests": "solicitudes",
            "costs_tokens": "tokens",
            # Config tab
            "tab_config": "\U0001f527 Config",
            "config_loading": "Cargando...",
            "config_save": "Guardar",
            "config_cancel": "Cancelar",
            "config_saved": "Guardado!",
            "config_save_error": "Error al guardar",
            "config_invalid_json": "JSON no válido",
            "config_file_not_found": "Archivo no encontrado (se creará al guardar)",
            "config_agents_title": "Perfiles de Agente",
            "config_mcp_title": "Configuración MCP",
            "config_prompt_title": "Prompt de Sistema",
            "config_memory_title": "Memoria (MEMORY.md)",
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
            "agent_sysprompt_label": "Prompt de Sistema Personalizado",
            "agent_sysprompt_hint": "Dejar vacío para usar el prompt de sistema predeterminado...",
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
            "tip_agent_sysprompt": "Instrucciones personalizadas que reemplazan el prompt de sistema.",
            "tip_agent_tools": "Selecciona las herramientas que puede usar. Ninguna = todas disponibles.",
            "tip_agent_default": "El agente predeterminado se usa cuando no se selecciona otro.",
            "tip_agent_enabled": "Los agentes deshabilitados se ocultan del selector.",
            # MCP form
            "mcp_add_server": "Añadir Servidor",
            "mcp_server_name": "Nombre del Servidor",
            "mcp_command": "Comando",
            "mcp_args": "Argumentos",
            "mcp_env": "Variables de Entorno",
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
            "agent_channel_none": "-- ninguno --",
            "tip_agent_channels": "Asigna este agente a un canal de mensajería. Cada canal puede tener un único agente.",
            "agent_channel_badge": "Canal",
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
            "no_models_msg": "Aucun modèle disponible. Vérifie les clés API des fournisseurs.",
            "models_load_error": "Erreur lors du chargement des modèles : ",
            "nvidia_test_result": "Test NVIDIA : OK {ok}, supprimés {removed}, testés {tested}/{total}",
            "nvidia_timeout": "timeout : {n}",
            "nvidia_remaining": "restants : {n} (appuie à nouveau pour continuer)",
            "nvidia_test_failed": "Test NVIDIA échoué",
            "switched_to": "Passé à {provider} \u2192 {model}",
            "provider_label": "Fournisseur",
            "model_label": "Modèle",
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
            "mic_needs_https_short": "Microphone bloqué (HTTP). Voir le message ci-dessus pour la solution Chrome.",
            "mic_denied_settings": "Acc\u00e8s au microphone refus\u00e9. Allez dans les param\u00e8tres du navigateur pour l'activer.",
            "mic_denied_icon": "Microphone refus\u00e9. Cliquez sur l'ic\u00f4ne \ud83d\udd12 dans la barre du navigateur.",
            "mic_not_found": "Aucun microphone trouv\u00e9. Connectez un microphone et r\u00e9essayez.",
            "mic_in_use": "Microphone utilis\u00e9 par une autre app. Fermez les autres apps et r\u00e9essayez.",
            "mic_error": "Erreur de microphone",
            # Voice mode
            "voice_mode": "Mode vocal",
            "voice_mode_on": "Voix ON – les réponses seront lues à haute voix",
            "voice_mode_off": "Voix OFF",
            "voice_listening": "Écoute en cours...",
            "voice_processing": "Traitement audio...",
            "voice_tts_error": "Impossible de lire la réponse vocale",
            "voice_tts_no_provider": "Sortie vocale indisponible. Edge TTS ou une clé API Groq/OpenAI est nécessaire.",
            "voice_transcription_error": "Échec de la transcription. Réessayez.",
            "voice_speaking": "En train de parler...",
            "voice_stop_speaking": "Arrêter la lecture",
            "wake_word_active": "Écoute de 'Ok Amira'...",
            "wake_word_detected": "Amira activée ! Parlez maintenant...",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bulle",
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
            "messaging_user": "Utilisateur",
            "messaging_messages": "Messages",
            "messaging_last": "Dernier message",
            "messaging_delete": "Supprimer",
            "messaging_confirm_delete": "Supprimer ce chat ?",
            "no_backups": "Aucune sauvegarde",
            "backup_file": "Fichier",
            "backup_date": "Date",
            "restore": "Restaurer",
            "confirm_restore_backup": "Restaurer cette sauvegarde ? Le fichier actuel sera remplacé.",
            "delete_backup": "Supprimer",
            "confirm_delete_backup": "Supprimer cette sauvegarde définitivement ?",
            "download_backup": "Télécharger",
            # Device manager
            "no_devices": "Aucun appareil enregistré",
            "device_id": "ID de l'appareil",
            "device_name": "Nom",
            "device_type": "Type",
            "device_enabled": "Activé",
            "device_last_seen": "Dernière visite",
            "enable_device": "Activer",
            "disable_device": "Désactiver",
            "rename_device": "Renommer",
            "delete_device": "Supprimer",
            "confirm_delete_device": "Supprimer définitivement cet appareil ?",
            "device_deleted": "Appareil supprimé",
            "device_updated": "Appareil mis à jour",
            # Costs tab
            "tab_costs": "Coûts",
            "costs_today": "Aujourd'hui",
            "costs_total_tokens": "Tokens totaux",
            "costs_total_cost": "Coût total",
            "costs_by_model": "Par modèle",
            "costs_by_provider": "Par fournisseur",
            "costs_history": "7 derniers jours",
            "costs_no_data": "Aucune donnée d'utilisation",
            "costs_reset": "Réinitialiser",
            "costs_reset_confirm": "Réinitialiser toutes les statistiques ? Cette action est irréversible.",
            "costs_reset_done": "Données d'utilisation effacées",
            "costs_requests": "requêtes",
            "costs_tokens": "tokens",
            # Config tab
            "tab_config": "\U0001f527 Config",
            "config_loading": "Chargement...",
            "config_save": "Enregistrer",
            "config_cancel": "Annuler",
            "config_saved": "Enregistré !",
            "config_save_error": "Erreur lors de l'enregistrement",
            "config_invalid_json": "JSON invalide",
            "config_file_not_found": "Fichier non trouvé (sera créé à l'enregistrement)",
            "config_agents_title": "Profils d'Agent",
            "config_mcp_title": "Configuration MCP",
            "config_prompt_title": "Prompt Système Personnalisé",
            "config_memory_title": "Mémoire (MEMORY.md)",
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
            "agent_sysprompt_label": "Prompt Système Personnalisé",
            "agent_sysprompt_hint": "Laisser vide pour utiliser le prompt système par défaut...",
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
            "tip_agent_sysprompt": "Instructions personnalisées qui remplacent le prompt système.",
            "tip_agent_tools": "Sélectionnez les outils autorisés. Aucun = tous disponibles.",
            "tip_agent_default": "L'agent par défaut est utilisé quand aucun n'est sélectionné.",
            "tip_agent_enabled": "Les agents désactivés sont masqués du sélecteur.",
            # MCP form
            "mcp_add_server": "Ajouter Serveur",
            "mcp_server_name": "Nom du Serveur",
            "mcp_command": "Commande",
            "mcp_args": "Arguments",
            "mcp_env": "Variables d'Environnement",
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
            "agent_channel_none": "-- aucun --",
            "tip_agent_channels": "Attribuez cet agent à un canal de messagerie. Chaque canal ne peut avoir qu'un seul agent.",
            "agent_channel_badge": "Canal",
        },
    }
    ui_js = ui_js_all.get(api.LANGUAGE, ui_js_all["en"])
    ui_js_json = json.dumps(ui_js, ensure_ascii=False)
    
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
        .splitter {{ width: 8px; flex: 0 0 8px; cursor: col-resize; background: transparent; }}
        .splitter:hover {{ background: rgba(0,0,0,0.08); }}
        @media (pointer: coarse) {{
            .splitter {{ width: 14px; flex: 0 0 14px; background: rgba(0,0,0,0.04); }}
            .splitter:active {{ background: rgba(0,0,0,0.12); }}
        }}
        body.resizing, body.resizing * {{ cursor: col-resize !important; user-select: none !important; }}
        .sidebar-header {{ padding: 12px; border-bottom: 1px solid #e0e0e0; font-weight: 600; font-size: 14px; color: #666; }}
        .sidebar-tabs {{ display: flex; flex-wrap: wrap; border-bottom: 1px solid #e0e0e0; background: #f8f9fa; }}
        .sidebar-tab {{ flex: 1 1 33%; min-width: 0; padding: 6px 2px; font-size: 11px; text-align: center; cursor: pointer; border: none; background: none; color: #666; transition: all 0.2s; border-bottom: 2px solid transparent; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
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
        #chatgptWebModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center; }}
        #chatgptWebModal.open {{ display:flex; }}
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
        .msg-bubble {{ max-width:80%; padding:10px 14px; border-radius:16px; font-size:13px; line-height:1.5; word-wrap:break-word; }}
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
        .theme-dark .messaging-card-delete {{ color:#555; }}
        .theme-dark .messaging-card-delete:hover {{ color:#ef9a9a; background:#3c1e1e; }}
        .chat-container {{ flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }}
        .message {{ max-width: 85%; padding: 12px 16px; border-radius: 16px; line-height: 1.5; font-size: 14px; word-wrap: break-word; overflow-wrap: anywhere; animation: fadeIn 0.3s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .message.user {{ background: #667eea; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }}
        .message.user img {{ max-width: 200px; max-height: 200px; border-radius: 8px; margin-top: 8px; display: block; }}
        .message.assistant {{ background: white; color: #333; align-self: flex-start; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .code-block {{ position: relative; margin: 8px 0; }}
        .code-block .copy-button {{ position: absolute; top: 8px; right: 8px; background: #667eea; color: white; border: none; border-radius: 6px; padding: 4px 10px; font-size: 11px; cursor: pointer; opacity: 0.8; transition: all 0.2s; z-index: 1; }}
        .code-block .copy-button:hover {{ opacity: 1; background: #5a6fd6; }}
        .code-block .copy-button.copied {{ background: #10b981; }}
        .message.assistant pre {{ background: #f5f5f5; padding: 10px; border-radius: 8px; overflow-x: auto; margin: 0; font-size: 13px; }}
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
        .message.assistant strong {{ color: #333; }}
        .message.assistant ul, .message.assistant ol {{ margin: 6px 0 6px 20px; }}
        .message.assistant p {{ margin: 4px 0; }}
        .message.system {{ background: #fff3cd; color: #856404; align-self: center; text-align: center; font-size: 13px; border-radius: 8px; max-width: 90%; }}
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
        .voice-toggle {{ display: flex; align-items: center; gap: 6px; padding: 0 16px 4px; font-size: 12px; color: #888; }}
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

        /* Tablet: 600px - 1199px - sidebar visible but narrow */
        @media (min-width: 600px) and (max-width: 1199px) {{
            .mobile-only {{ display: none; }}
            .sidebar {{ width: 160px; min-width: 140px; max-width: 180px; }}
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
        .agent-form-group .emoji-picker {{
            display: flex; gap: 4px; flex-wrap: wrap;
        }}
        .agent-form-group .emoji-btn {{
            width: 32px; height: 32px; border: 2px solid transparent; border-radius: 6px;
            cursor: pointer; font-size: 18px; background: #f5f5f5; display: flex;
            align-items: center; justify-content: center; transition: all 0.15s;
        }}
        .agent-form-group .emoji-btn:hover {{ background: #e8e8ff; }}
        .agent-form-group .emoji-btn.selected {{ border-color: #667eea; background: #e8ebff; }}
        .agent-tools-grid {{
            display: flex; flex-wrap: wrap; gap: 4px; max-height: 120px; overflow-y: auto;
        }}
        .agent-tool-chip {{
            font-size: 11px; padding: 3px 8px; border-radius: 4px; cursor: pointer;
            background: #f0f0f0; color: #666; border: 1px solid transparent;
            transition: all 0.15s; user-select: none;
        }}
        .agent-tool-chip:hover {{ background: #e8ebff; }}
        .agent-tool-chip.selected {{ background: #667eea; color: white; border-color: #5a6fd6; }}
        .agent-form-actions {{
            display: flex; gap: 8px; justify-content: flex-end; padding-top: 8px;
            border-top: 1px solid #e0e0e0;
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
        .mcp-server-toggle {{ font-size: 12px; color: #888; transition: transform 0.2s; }}
        .mcp-server-toggle.open {{ transform: rotate(90deg); }}
        .mcp-server-body {{ padding: 12px; display: none; border-top: 1px solid #e8e8f0; }}
        .mcp-server-body.open {{ display: block; }}
        .mcp-server-actions {{ display: flex; gap: 4px; }}
        .mcp-server-actions button {{
            background: none; border: none; cursor: pointer; font-size: 14px;
            padding: 2px 4px; border-radius: 4px; opacity: 0.6;
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
        body.dark-mode .config-item-title {{ color: #e0e0e0; }}
        body.dark-mode .config-item-desc {{ color: #808090; }}
        body.dark-mode .config-editor-header {{ border-bottom-color: #3a3a4a; }}
        body.dark-mode .config-editor-title {{ color: #e0e0e0; }}
        body.dark-mode .config-editor-body textarea {{
            background: #1e1e2e; color: #cdd6f4;
        }}
        body.dark-mode .config-editor-footer {{ border-top-color: #3a3a4a; }}
        body.dark-mode .config-cancel-btn {{ background: #3a3a4a; color: #ccc; }}
        body.dark-mode .config-cancel-btn:hover {{ background: #4a4a5a; }}
        body.dark-mode .config-status.success {{ background: #1a3a2a; color: #6ee7b7; }}
        body.dark-mode .config-status.error {{ background: #3a1a1a; color: #fca5a5; }}

        /* Agent form dark mode */
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
        body.dark-mode .agent-form-group .emoji-btn {{ background: #2a2a3a; }}
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
        <button id="testNvidiaBtn" class="new-chat" onclick="testNvidiaModel()" title="{ui_js['nvidia_test_title']}" style="display:none">\U0001f50d {ui_js['nvidia_test_btn']}</button>
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
                <button class="sidebar-tab active" data-tab="chat" onclick="switchSidebarTab('chat')">\U0001f4ac {ui_js['tab_chat']}</button>
                <button class="sidebar-tab" data-tab="bubble" onclick="switchSidebarTab('bubble')">\U0001f4ad {ui_js['tab_bubble']}</button>
                <button class="sidebar-tab" data-tab="messaging" onclick="switchSidebarTab('messaging')">{ui_js['tab_messaging']}</button>
                <div class="sidebar-tab-row-sep"></div>
                <button class="sidebar-tab" data-tab="files" onclick="switchSidebarTab('files')">{ui_js['tab_files']}</button>
                <button class="sidebar-tab" data-tab="backups" onclick="switchSidebarTab('backups')">\U0001f4be {ui_js['tab_backups']}</button>
                <button class="sidebar-tab" data-tab="devices" onclick="switchSidebarTab('devices')">⚙️ {ui_js['tab_devices']}</button>
                <button class="sidebar-tab" data-tab="costs" onclick="switchSidebarTab('costs')">💰 {ui_js['tab_costs']}</button>
                <button class="sidebar-tab" data-tab="config" onclick="switchSidebarTab('config')">{ui_js['tab_config']}</button>
            </div>
            <div class="sidebar-content active" id="tabChat">
                <div class="chat-list" id="chatList"></div>
            </div>
            <div class="sidebar-content" id="tabBubble">
                <div class="chat-list" id="bubbleList"></div>
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
        <div class="voice-toggle" id="voiceToggle" style="display: {voice_display};">
            <label>
                <input type="checkbox" id="voiceModeCheckbox" />
                <span class="toggle-track"><span class="toggle-thumb"></span></span>
                <span class="toggle-label">{ui_js['voice_mode']}</span>
            </label>
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
            wakeWordRecognition.lang = '{api.LANGUAGE}' === 'it' ? 'it-IT' : '{api.LANGUAGE}' === 'es' ? 'es-ES' : '{api.LANGUAGE}' === 'fr' ? 'fr-FR' : 'en-US';
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

        const ANALYZING_MSG = {json.dumps(analyzing_msg)};

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
            const maxWidth = 500;
            const storageKey = 'chatSidebarWidth';

            const saved = parseInt(safeLocalStorageGet(storageKey) || '', 10);
            if (!Number.isNaN(saved)) {{
                const w = Math.max(minWidth, Math.min(maxWidth, saved));
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
                let next = Math.max(minWidth, Math.min(maxWidth, startWidth + dx));
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
                if (dragging && e.touches.length === 1) moveDrag(e.touches[0].clientX);
            }}, {{ passive: true }});
            window.addEventListener('touchend', endDrag);
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
        ];
        let configActiveFile = null;
        let configOriginalContent = '';

        // Known tool names for the agent form multi-select
        const KNOWN_TOOLS = [
            'get_entities', 'get_entity_state', 'call_service', 'search_entities',
            'get_integration_entities', 'create_automation', 'update_automation',
            'get_automations', 'trigger_automation', 'delete_automation',
            'get_available_services', 'get_events', 'get_history', 'get_scenes',
            'activate_scene', 'get_scripts', 'run_script', 'update_script',
            'create_script', 'delete_script', 'get_areas', 'manage_areas',
            'manage_entity', 'get_devices', 'send_notification', 'get_dashboards',
            'create_dashboard', 'delete_dashboard', 'create_html_dashboard',
            'read_config_file', 'write_config_file', 'list_config_files',
            'manage_statistics',
        ];
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
                    const model = a.model || '';
                    const badges = [];
                    if (isProtected) badges.push('<span class="agent-protected-badge">\U0001f512 ' + (T.agent_protected || 'Protected') + '</span>');
                    if (a.is_default) badges.push('<span class="agent-badge default">default</span>');
                    if (a.thinking_level) badges.push('<span class="agent-badge">' + a.thinking_level + '</span>');
                    // Channel badges
                    Object.keys(channelAgents).forEach(ch => {{
                        if (channelAgents[ch] === a.id) {{
                            const icon = ch === 'telegram' ? '\U0001f4e9' : ch === 'whatsapp' ? '\U0001f4f1' : '\U0001f4ac';
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
                        + '<button class="delete" title="Delete">\U0001f5d1\ufe0f</button>'
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
                + '<div class="emoji-picker" id="af_emoji_picker"></div></div>';
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
                + _escHtml(agentData && agentData.system_prompt ? agentData.system_prompt : '') + '</textarea></div>';

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
            const CHANNELS = ['telegram', 'whatsapp'];
            let chHtml = '<div class="agent-form-group"><label>' + _lbl(T.agent_channels || 'Channel Assignment', 'tip_agent_channels') + '</label>'
                + '<div class="agent-form-row">';
            CHANNELS.forEach(ch => {{
                const isAssigned = agentId && chMap[ch] === agentId;
                const otherAgent = chMap[ch] && chMap[ch] !== agentId ? chMap[ch] : null;
                const label = ch === 'telegram' ? (T.agent_channel_telegram || 'Telegram')
                    : (T.agent_channel_whatsapp || 'WhatsApp');
                const icon = ch === 'telegram' ? '\U0001f4e9' : '\U0001f4f1';
                chHtml += '<div class="agent-form-group" style="flex:1;">'
                    + '<label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;">'
                    + '<input type="checkbox" class="af_channel" data-channel="' + ch + '"'
                    + (isAssigned ? ' checked' : '')
                    + (otherAgent ? ' title="Currently: ' + otherAgent + '"' : '') + '> '
                    + icon + ' ' + label + '</label></div>';
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
            const emojiPicker = document.getElementById('af_emoji_picker');
            const currentEmoji = agentData ? (agentData.emoji || '\U0001f916') : '\U0001f916';
            AGENT_EMOJIS.forEach(em => {{
                const btn = document.createElement('button');
                btn.className = 'emoji-btn' + (em === currentEmoji ? ' selected' : '');
                btn.textContent = em;
                btn.type = 'button';
                btn.addEventListener('click', () => {{
                    emojiPicker.querySelectorAll('.emoji-btn').forEach(b => b.classList.remove('selected'));
                    btn.classList.add('selected');
                }});
                emojiPicker.appendChild(btn);
            }});

            // Provider/Model dropdowns
            const provSel = document.getElementById('af_provider');
            const modSel = document.getElementById('af_model');
            let currentProv = '';
            let currentMod = '';
            if (agentData && agentData.model) {{
                const parts = agentData.model.split('/');
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
            KNOWN_TOOLS.forEach(t => {{
                const chip = document.createElement('span');
                chip.className = 'agent-tool-chip' + (hasToolFilter && selectedTools.has(t) ? ' selected' : '');
                chip.textContent = t;
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
            const selectedEmoji = document.querySelector('#af_emoji_picker .emoji-btn.selected');
            const emoji = selectedEmoji ? selectedEmoji.textContent : '\U0001f916';
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
            if (sp.trim()) payload.system_prompt = sp.trim();

            // Tools — only include if at least one chip selected
            const toolChips = document.querySelectorAll('#af_tools .agent-tool-chip.selected');
            if (toolChips.length > 0) {{
                payload.tools = Array.from(toolChips).map(c => c.textContent);
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

            let mcpConfig = {{}};
            try {{
                const resp = await fetch(apiUrl('api/config/read') + '?file=amira/mcp_config.json', {{credentials:'same-origin'}});
                const data = await resp.json();
                if (data.success && data.content) {{
                    mcpConfig = JSON.parse(data.content);
                }}
            }} catch(e) {{ console.warn('Failed to load MCP config', e); }}

            const servers = mcpConfig.mcpServers || mcpConfig.mcpservers || {{}};

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
                _renderMcpCards(listWrap, servers);
                // auto expand the new one
                const lastCard = listWrap.querySelector('.mcp-server-card:last-child');
                if (lastCard) {{
                    lastCard.querySelector('.mcp-server-body').classList.add('open');
                    lastCard.querySelector('.mcp-server-toggle').classList.add('open');
                }}
            }});
            hdr.appendChild(addBtn);
            wrap.appendChild(hdr);

            const listWrap = document.createElement('div');
            listWrap.style.cssText = 'flex:1;overflow-y:auto;padding:8px;';
            _renderMcpCards(listWrap, servers);
            wrap.appendChild(listWrap);

            // Footer with save
            const footer = document.createElement('div');
            footer.className = 'agent-form-actions';
            footer.style.cssText = 'padding:12px;';
            footer.innerHTML = '<span id="mcpStatus" class="config-status"></span>';
            const saveBtn = document.createElement('button');
            saveBtn.className = 'config-save-btn';
            saveBtn.textContent = T.config_save || 'Save';
            saveBtn.addEventListener('click', async () => {{
                // Collect data from cards
                const result = _collectMcpData(listWrap);
                const json = JSON.stringify({{ mcpServers: result }}, null, 2);
                try {{
                    const resp = await fetch(apiUrl('api/config/save'), {{
                        method: 'POST', headers: {{'Content-Type':'application/json'}},
                        credentials: 'same-origin',
                        body: JSON.stringify({{ file: 'amira/mcp_config.json', content: json }})
                    }});
                    const d = await resp.json();
                    if (!d.success) throw new Error(d.error || 'Save failed');
                    const st = document.getElementById('mcpStatus');
                    if (st) {{ st.textContent = T.config_saved || 'Saved!'; st.className = 'config-status success'; }}
                    setTimeout(() => {{ if (st) {{ st.textContent = ''; st.className = 'config-status'; }} }}, 3000);
                }} catch(err) {{
                    const st = document.getElementById('mcpStatus');
                    if (st) {{ st.textContent = (T.config_save_error || 'Error') + ': ' + err.message; st.className = 'config-status error'; }}
                }}
            }});
            footer.appendChild(saveBtn);
            wrap.appendChild(footer);

            filePanelContentEl.appendChild(wrap);
        }}

        function _renderMcpCards(container, servers) {{
            container.innerHTML = '';
            const names = Object.keys(servers);
            if (names.length === 0) {{
                container.innerHTML = '<div style="padding:20px;text-align:center;color:#999;">'
                    + (T.mcp_no_servers || 'No MCP servers configured.') + '</div>';
                return;
            }}
            names.forEach(name => {{
                const srv = servers[name] || {{}};
                const card = document.createElement('div');
                card.className = 'mcp-server-card';
                card.dataset.serverName = name;

                const header = document.createElement('div');
                header.className = 'mcp-server-header';
                header.innerHTML = '<span class="mcp-server-toggle">\u25b6</span>'
                    + '<span class="mcp-server-name">' + _escHtml(name) + '</span>'
                    + '<div class="mcp-server-actions">'
                    + '<button class="delete" title="Delete">\U0001f5d1\ufe0f</button></div>';

                header.querySelector('.delete').addEventListener('click', (e) => {{
                    e.stopPropagation();
                    delete servers[name];
                    _renderMcpCards(container, servers);
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
                    + _escAttr(srv.command || '') + '" placeholder="python, uvx, npx..."></div>'
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
                result[name] = {{ command: cmd.trim(), args: args, env: env }};
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
            useBtn.textContent = 'Seleziona';

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
            let text = '\ud83d\udcca ' + inp + ' in / ' + out + ' out';
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
                div.textContent = stripContextInjections(text);
                if (imageData) {{
                    const img = document.createElement('img');
                    img.src = imageData;
                    div.appendChild(img);
                }}
            }}
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
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
            const codeBlock = button.nextElementSibling;
            const codeElement = codeBlock.querySelector('code');
            const code = codeElement ? (codeElement.innerText || codeElement.textContent) : codeBlock.textContent;

            const showSuccess = () => {{
                const originalText = button.textContent;
                button.textContent = '\u2713 ' + T.copied;
                button.classList.add('copied');
                setTimeout(() => {{
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }}, 2000);
            }};

            // Try modern clipboard API first (requires HTTPS)
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(code).then(showSuccess).catch(() => {{
                    // Fallback to older method for HTTP
                    fallbackCopy(code, showSuccess);
                }});
            }} else {{
                // Fallback for older browsers or HTTP
                fallbackCopy(code, showSuccess);
            }}
        }}

        function fallbackCopy(text, callback) {{
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {{
                document.execCommand('copy');
                callback();
            }} catch (err) {{
                console.error('Copy failed:', err);
            }}
            document.body.removeChild(textarea);
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
                            }} else if (evt.type === 'error') {{
                                removeThinking();
                                addMessage('\u274c ' + evt.message, 'system');
                                // If web session expired server-side, refresh banner immediately
                                if (currentProviderId === 'chatgpt_web') checkChatGPTWebSession();
                                else if (currentProviderId === 'claude_web') checkClaudeWebSession();
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
            }} else if (tabName === 'config') {{
                document.getElementById('tabConfig').classList.add('active');
                loadConfigList();
            }}
        }}

        async function loadCostsPanel() {{
            const panel = document.getElementById('costsPanel');
            if (!panel) return;
            panel.innerHTML = '<div style="padding:16px;text-align:center;color:#999;">' + T.files_loading + '</div>';
            try {{
                const resp = await fetch(apiUrl('api/usage_stats?days=7'));
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

                // History (last 7 days) — dailyArr is already sorted ascending by date
                if (dailyArr.length > 0) {{
                    html += '<div class="cost-section">';
                    html += '<div class="cost-section-title">' + T.costs_history + '</div>';
                    const reversed = [...dailyArr].reverse();
                    for (const dayObj of reversed) {{
                        const dc = dayObj.total_cost || 0;
                        html += '<div class="cost-row">';
                        html += '<div class="cost-row-name">' + (dayObj.date || '?') + '</div>';
                        html += '<div class="cost-row-value">' + (dc > 0 ? sym + _fmtCost(dc) : '—') + '</div>';
                        html += '</div>';
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
                left.style.flex = '1';
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
                const chatConvs = _allConversations.filter(c => c.source !== 'bubble');
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
                    ...(chats.whatsapp || []).map(c => ({{...c, channel: 'whatsapp'}}))
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
                    const badgeLabel = isTg ? '✈️ Telegram' : '💬 WhatsApp';
                    const badgeCls   = isTg ? 'telegram' : 'whatsapp';
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

                const channelLabel = channel === 'telegram' ? '🤖 Telegram' : '💬 WhatsApp';
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
                addMessage('❌ Errore nel caricare i messaggi', 'system');
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
            'ollama': '🦙 Ollama (Local)',
            'openrouter': '🔀 OpenRouter',
            'deepseek': '🔍 DeepSeek',
            'minimax': '🎭 MiniMax',
            'aihubmix': '🌐 AiHubMix',
            'siliconflow': '💎 SiliconFlow',
            'volcengine': '🌋 VolcEngine',
            'dashscope': '☁️ DashScope (Qwen)',
            'moonshot': '🌙 Moonshot (Kimi)',
            'zhipu': '🧬 Zhipu (GLM)',
            'github_copilot': '⚠️ GitHub Copilot (Web)',
            'openai_codex': '⚠️ OpenAI Codex (Web)',
            'claude_web': '⚠️ Claude.ai (Web)',
            'chatgpt_web': '⚠️ ChatGPT (Web)'
        }};

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
            return model.replace(/^(Claude|OpenAI|Google|NVIDIA|GitHub Models|GitHub Copilot|OpenAI Codex|GitHub|Groq|Mistral|Ollama|OpenRouter|DeepSeek|MiniMax|AiHubMix|SiliconFlow|VolcEngine|DashScope|Moonshot|Zhipu):\\s*/, '');
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
                models.forEach(m => {{
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = _stripProviderPrefix(m) + _capBadges(m, providerId);
                    if (m === currentModel) opt.selected = true;
                    modelSel.appendChild(opt);
                }});
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
                const testBtn = document.getElementById('testNvidiaBtn');
                if (testBtn) testBtn.style.display = (currentProviderId === 'nvidia') ? 'inline-flex' : 'none';

                // Build ordered provider list
                let availableProviders = data.available_providers && data.available_providers.length
                    ? data.available_providers.map(p => p.id)
                    : Object.keys(data.models || {{}});
                if (!availableProviders.length && currentProvider) availableProviders = [currentProvider];

                const providerOrder = [
                    'anthropic', 'openai', 'google', 'nvidia', 'github',
                    'groq', 'mistral', 'ollama', 'openrouter',
                    'deepseek', 'minimax', 'aihubmix', 'siliconflow', 'volcengine',
                    'dashscope', 'moonshot', 'zhipu',
                    // --- Web providers (always last) ---
                    'github_copilot', 'openai_codex', 'claude_web', 'chatgpt_web'
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
                    data.agents.forEach(a => {{
                        const opt = document.createElement('option');
                        opt.value = a.id;
                        const ident = a.identity || {{}};
                        opt.textContent = (ident.emoji || '\U0001f916') + ' ' + (ident.name || a.id);
                        if (data.active_agent && a.id === data.active_agent) opt.selected = true;
                        agentSel.appendChild(opt);
                    }});
                    agentSel.style.display = '';
                }} else if (agentSel) {{
                    agentSel.style.display = 'none';
                }}

                // --- Update header identity from active agent ---
                if (data.active_agent_identity) {{
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

            const BATCH = 50;
            let cursor = 0;
            let totalOk = 0, totalRemoved = 0, totalTested = 0, grandTotal = 0;
            let anyBlocklisted = false;
            let batchNum = 0;

            const oldText = btn.textContent;
            btn.disabled = true;

            try {{
                while (true) {{
                    batchNum++;
                    btn.textContent = `\u23f3 Test batch ${{batchNum}}...`;

                    const response = await fetch(apiUrl('api/nvidia/test_models'), {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{max_models: BATCH, cursor: cursor}})
                    }});
                    const data = await response.json().catch(() => ({{}}));

                    if (!response.ok || !data || !data.success) {{
                        const msg = (data && (data.message || data.error)) || (T.nvidia_test_failed + ' (' + response.status + ')');
                        addMessage('\u26a0\ufe0f ' + msg, 'system');
                        break;
                    }}

                    totalOk += (data.ok || 0);
                    totalRemoved += (data.removed || 0);
                    totalTested += (data.tested || 0);
                    grandTotal = data.total || grandTotal;
                    if (data.blocklisted) anyBlocklisted = true;

                    // Se rate limit o errore di rete, ferma e mostra parziale
                    if (data.stopped_reason && (data.stopped_reason.includes('rate') || data.stopped_reason.includes('auth') || data.stopped_reason.includes('errore'))) {{
                        const parts = [];
                        parts.push(T.nvidia_test_result.replace('{{ok}}', totalOk).replace('{{removed}}', totalRemoved).replace('{{tested}}', totalTested).replace('{{total}}', grandTotal));
                        parts.push(`(${{data.stopped_reason}})`);
                        if (typeof data.remaining === 'number' && data.remaining > 0) parts.push('\u2014 ' + T.nvidia_remaining.replace('{{n}}', data.remaining));
                        addMessage('\U0001f50d ' + parts.join(' '), 'system');
                        break;
                    }}

                    // Aggiorna cursor
                    if (typeof data.next_cursor === 'number') {{
                        cursor = data.next_cursor;
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
                parts.push(T.nvidia_test_result.replace('{{ok}}', totalOk).replace('{{removed}}', totalRemoved).replace('{{tested}}', totalTested).replace('{{total}}', grandTotal));
                if (totalTested >= grandTotal) parts.push('\u2705 Completato!');
                addMessage('\U0001f50d ' + parts.join(' '), 'system');

                if (anyBlocklisted) await loadModels();
            }} catch (e) {{
                addMessage('\u26a0\ufe0f ' + T.nvidia_test_failed + ': ' + (e && e.message ? e.message : String(e)), 'system');
            }} finally {{
                btn.disabled = false;
                btn.textContent = oldText;
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
                    const testBtn = document.getElementById('testNvidiaBtn');
                    if (testBtn) {{
                        testBtn.style.display = (currentProviderId === 'nvidia') ? 'inline-flex' : 'none';
                    }}
                    // Show notification
                    const providerName = PROVIDER_LABELS[parsed.provider] || parsed.provider;
                    addMessage('\U0001f504 ' + T.switched_to.replace('{{provider}}', providerName).replace('{{model}}', parsed.model), 'system');
                    const modelLower = String(parsed.model || '').toLowerCase();
                    if (parsed.provider === 'github' && modelLower.includes('o4-mini') && O4MINI_TOKENS_HINT) {{
                        addMessage(O4MINI_TOKENS_HINT, 'system');
                    }}
                    // Refresh dropdown state from server (ensures UI stays consistent)
                    loadModels();
                    // Show OAuth banners for providers that need authentication
                    if (parsed.provider === 'openai_codex') {{
                        checkCodexOAuth();
                        const cb = document.getElementById('copilotOAuthBanner');
                        if (cb) cb.style.display = 'none';
                        ['claudeWebBanner','chatgptWebBanner'].forEach(id => {{ const el=document.getElementById(id); if(el) el.style.display='none'; }});
                    }} else if (parsed.provider === 'github_copilot') {{
                        checkCopilotOAuth();
                        ['codexOAuthBanner','codexOAuthConnectedBanner','claudeWebBanner','chatgptWebBanner'].forEach(id => {{ const el=document.getElementById(id); if(el) el.style.display='none'; }});
                    }} else if (parsed.provider === 'claude_web') {{
                        checkClaudeWebSession();
                        ['codexOAuthBanner','codexOAuthConnectedBanner','copilotOAuthBanner','chatgptWebBanner'].forEach(id => {{ const el=document.getElementById(id); if(el) el.style.display='none'; }});
                    }} else if (parsed.provider === 'chatgpt_web') {{
                        checkChatGPTWebSession();
                        ['codexOAuthBanner','codexOAuthConnectedBanner','copilotOAuthBanner','claudeWebBanner'].forEach(id => {{ const el=document.getElementById(id); if(el) el.style.display='none'; }});
                    }} else {{
                        const codexBanner   = document.getElementById('codexOAuthBanner');
                        const copilotBanner = document.getElementById('copilotOAuthBanner');
                        const codexConnBanner = document.getElementById('codexOAuthConnectedBanner');
                        if (codexBanner)     codexBanner.style.display = 'none';
                        if (copilotBanner)   copilotBanner.style.display = 'none';
                        if (codexConnBanner) codexConnBanner.style.display = 'none';
                        ['claudeWebBanner','chatgptWebBanner'].forEach(id => {{ const el=document.getElementById(id); if(el) el.style.display='none'; }});
                    }}
                }}
            }} catch (error) {{
                console.error('Error changing model:', error);
            }}
        }}

        // Change active agent
        async function changeAgent(agentId) {{
            if (!agentId) return;
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
                const banner = document.getElementById('copilotOAuthBanner');
                if (!banner) return;
                banner.style.display = d.configured ? 'none' : 'flex';
            }} catch (e) {{ /* ignore */ }}
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
                const banner = document.getElementById('claudeWebBanner');
                if (!banner) return;
                banner.style.display = d.configured ? 'none' : 'flex';
            }} catch (e) {{ /* ignore */ }}
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

                initSidebarResize();
                initFilePanelResize();
                if (filePanelCloseAllEl) filePanelCloseAllEl.onclick = () => closeFilePanel();
                loadModels();
                loadChatList();
                loadHistory();
                if (currentProviderId === 'openai_codex') checkCodexOAuth();
                if (currentProviderId === 'github_copilot') checkCopilotOAuth();
                if (currentProviderId === 'claude_web') checkClaudeWebSession();
                if (currentProviderId === 'chatgpt_web') checkChatGPTWebSession();
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
                const _statusInterval = setInterval(async () => {{
                    try {{
                        const r = await fetch(apiUrl('api/status'), {{credentials:'same-origin'}});
                        if (!r.ok) {{ _statusFailures++; }} else {{ _statusFailures = 0; }}
                        if (_statusFailures >= 3) {{
                            clearInterval(_statusInterval);
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
                        if (_statusFailures >= 3) {{
                            clearInterval(_statusInterval);
                            _appendSystemRaw('⚠️ Server non raggiungibile. Ricarica la pagina per riconnetterti.');
                        }}
                    }}
                }}, 10000);
                // Poll session status every 30s for web providers so the banner reappears when token expires
                setInterval(async () => {{
                    if (currentProviderId === 'chatgpt_web') checkChatGPTWebSession();
                    else if (currentProviderId === 'claude_web') checkClaudeWebSession();
                }}, 30000);
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
        window.newChat = newChat;
        window.toggleSidebar = toggleSidebar;
        window.sendSuggestion = sendSuggestion;
        window.testNvidiaModel = testNvidiaModel;
        window.revokeCodexOAuth = revokeCodexOAuth;
        window.toggleDarkMode = toggleDarkMode;
        window.toggleReadOnly = toggleReadOnly;
        // File explorer exports
        window.loadFileTree = loadFileTree;
        window.openFileInPanel = openFileInPanel;
        window.closeFilePanelTab = closeFilePanelTab;
        window.closeFilePanel = closeFilePanel;
        }}
        
    </script>
</body>
</html>"""
