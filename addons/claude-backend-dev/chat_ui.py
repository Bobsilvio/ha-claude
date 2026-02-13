"""Chat UI HTML generation for Home Assistant AI assistant."""

import json
import api


def get_chat_ui():
    """Generate the chat UI with image upload support."""
    provider_name = api.PROVIDER_DEFAULTS.get(api.AI_PROVIDER, {}).get("name", api.AI_PROVIDER)
    model_name = api.get_active_model()
    configured = bool(api.get_api_key())
    status_color = "#4caf50" if configured else "#ff9800"
    status_text = provider_name if configured else f"{provider_name} (no key)"

    # NOTE: The "thinking" message is also computed dynamically in the browser,
    # because provider/model can change at runtime via /api/set_model.
    provider_analyzing = {
        "anthropic": {
            "en": "🧠 Claude is thinking deeply...",
            "it": "🧠 Claude sta pensando...",
            "es": "🧠 Claude está pensando...",
            "fr": "🧠 Claude réfléchit...",
        },
        "openai": {
            "en": "⚡ GPT is processing your request...",
            "it": "⚡ GPT sta elaborando...",
            "es": "⚡ GPT está procesando...",
            "fr": "⚡ GPT traite votre demande...",
        },
        "google": {
            "en": "✨ Gemini is analyzing...",
            "it": "✨ Gemini sta analizzando...",
            "es": "✨ Gemini está analizando...",
            "fr": "✨ Gemini analyse...",
        },
        "github": {
            "en": "🚀 GitHub AI is working on it...",
            "it": "🚀 GitHub AI sta lavorando...",
            "es": "🚀 GitHub AI está trabajando...",
            "fr": "🚀 GitHub AI travaille...",
        },
        "nvidia": {
            "en": "🎯 NVIDIA AI is computing...",
            "it": "🎯 NVIDIA AI sta calcolando...",
            "es": "🎯 NVIDIA AI está computando...",
            "fr": "🎯 NVIDIA AI calcule...",
        },
    }

    analyzing_msg = provider_analyzing.get(api.AI_PROVIDER, provider_analyzing["openai"]).get(
        api.LANGUAGE,
        provider_analyzing.get(api.AI_PROVIDER, provider_analyzing["openai"]).get("en"),
    )

    ui_messages = {
        "en": {
            "welcome": "👋 Hi! I'm your AI assistant for Home Assistant.",
            "provider_model": f"Provider: <strong>{provider_name}</strong> | Model: <strong>{model_name}</strong>",
            "capabilities": "I can control devices, create automations, and manage your smart home.",
            "vision_feature": "<strong>🖼 New in v3.0:</strong> Now you can send me images!",
            "o4mini_tokens_hint": "ℹ️ Note: o4-mini has a ~4000 token limit. Context and history are reduced automatically.",
            "analyzing": analyzing_msg
        },
        "it": {
            "welcome": "👋 Ciao! Sono il tuo assistente AI per Home Assistant.",
            "provider_model": f"Provider: <strong>{provider_name}</strong> | Modello: <strong>{model_name}</strong>",
            "capabilities": "Posso controllare dispositivi, creare automazioni e gestire la tua casa smart.",
            "vision_feature": "<strong>🖼 Novità v3.0:</strong> Ora puoi inviarmi immagini!",
            "o4mini_tokens_hint": "ℹ️ Nota: o4-mini ha un limite di ~4000 token. Contesto e cronologia vengono ridotti automaticamente.",
            "analyzing": analyzing_msg
        },
        "es": {
            "welcome": "👋 ¡Hola! Soy tu asistente AI para Home Assistant.",
            "provider_model": f"Proveedor: <strong>{provider_name}</strong> | Modelo: <strong>{model_name}</strong>",
            "capabilities": "Puedo controlar dispositivos, crear automatizaciones y gestionar tu hogar inteligente.",
            "vision_feature": "<strong>🖼 Nuevo en v3.0:</strong> ¡Ahora puedes enviarme imágenes!",
            "o4mini_tokens_hint": "ℹ️ Nota: o4-mini tiene un límite de ~4000 tokens. El contexto y el historial se reducen automáticamente.",
            "analyzing": analyzing_msg
        },
        "fr": {
            "welcome": "👋 Salut ! Je suis votre assistant IA pour Home Assistant.",
            "provider_model": f"Fournisseur: <strong>{provider_name}</strong> | Modèle: <strong>{model_name}</strong>",
            "capabilities": "Je peux contrôler des appareils, créer des automatisations et gérer votre maison intelligente.",
            "vision_feature": "<strong>🖼 Nouveau dans v3.0:</strong> Vous pouvez maintenant m'envoyer des images!",
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
        },
    }
    ui_js = ui_js_all.get(api.LANGUAGE, ui_js_all["en"])
    ui_js_json = json.dumps(ui_js, ensure_ascii=False)
    
    # Feature flags for UI elements
    file_upload_enabled = api.ENABLE_FILE_UPLOAD
    voice_enabled = api.ENABLE_VOICE
    file_upload_display = "block" if file_upload_enabled else "none"
    voice_display = "block" if voice_enabled else "none"

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Assistant - Home Assistant</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; height: 100vh; height: 100svh; display: flex; flex-direction: column; overflow-x: hidden; }}
        .main-container {{ display: flex; flex: 1; overflow: hidden; min-width: 0; }}
        .sidebar {{ width: 250px; min-width: 150px; max-width: 500px; background: white; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; overflow-y: auto; resize: horizontal; overflow-x: hidden; position: relative; }}
        .splitter {{ width: 8px; flex: 0 0 8px; cursor: col-resize; background: transparent; }}
        .splitter:hover {{ background: rgba(0,0,0,0.06); }}
        body.resizing, body.resizing * {{ cursor: col-resize !important; user-select: none !important; }}
        .sidebar-header {{ padding: 12px; border-bottom: 1px solid #e0e0e0; font-weight: 600; font-size: 14px; color: #666; }}
        .chat-list {{ flex: 1; overflow-y: auto; }}
        .chat-item {{ padding: 12px; border-bottom: 1px solid #f0f0f0; cursor: pointer; transition: background 0.2s; display: flex; justify-content: space-between; align-items: center; }}
        .chat-item:hover {{ background: #f8f9fa; }}
        .chat-item.active {{ background: #e8f0fe; border-left: 3px solid #667eea; }}
        .chat-item-title {{ font-size: 13px; color: #333; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .chat-item-info {{ font-size: 11px; color: #999; }}
        .chat-item-delete {{ color: #ef4444; font-size: 16px; padding: 4px 8px; opacity: 0.6; transition: all 0.2s; cursor: pointer; flex-shrink: 0; background: none; border: none; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; }}
        .chat-item:hover .chat-item-delete {{ opacity: 1; }}
        .chat-item-delete:hover {{ color: #dc2626; background: rgba(239,68,68,0.1); }}
        .chat-group-title {{ padding: 10px 12px; font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.04em; border-top: 1px solid #f0f0f0; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; min-height: 0; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); min-width: 0; overflow-x: hidden; }}
        .header h1 {{ font-size: 18px; font-weight: 600; }}
        .header .badge {{ font-size: 11px; opacity: 1; background: rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 10px; font-weight: 500; letter-spacing: 0.3px; }}
        .header .new-chat {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 12px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
        .header .new-chat:hover {{ background: rgba(255,255,255,0.35); }}
        .model-selector {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 10px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; max-width: 240px; min-width: 0; }}
        .model-selector:hover {{ background: rgba(255,255,255,0.35); }}
        .model-selector option {{ background: #2c3e50; color: white; }}
        .model-selector optgroup {{ background: #1a252f; color: #aaa; font-style: normal; font-weight: 600; padding: 4px 0; }}
        .header .status {{ margin-left: auto; font-size: 12px; display: flex; align-items: center; gap: 6px; }}
        .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: {status_color}; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
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
        .input-area button.voice-btn {{ background: #8b5cf6; }}
        .input-area button.voice-btn:hover {{ background: #7c3aed; }}
        .input-area button.voice-btn.recording {{ background: #ef4444; animation: pulse-record 1s infinite; }}
        @keyframes pulse-record {{ 0%, 100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }} 50% {{ box-shadow: 0 0 0 6px rgba(239,68,68,0); }} }}
        @keyframes pulse-stop {{ 0%, 100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }} 50% {{ box-shadow: 0 0 0 6px rgba(239,68,68,0); }} }}
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
        @media (max-width: 768px), (pointer: coarse) {{
            .mobile-only {{ display: inline-flex; }}

            .header {{ flex-wrap: wrap; padding: 10px 12px; gap: 8px; }}
            .header h1 {{ font-size: 16px; }}
            .header .status {{ order: 99; width: 100%; margin-left: 0; justify-content: flex-end; }}
            .model-selector {{ flex: 1 1 100%; max-width: none; width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}

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

        @media (max-width: 360px) {{
            .header .badge {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px;">\U0001f916</span>
        <h1>AI Assistant</h1>
        <span class="badge">v{api.get_version()}</span>
        <button id="sidebarToggleBtn" class="new-chat mobile-only" onclick="toggleSidebar()" title="{ui_js['conversations']}">\u2630</button>
        <select id="modelSelect" class="model-selector" onchange="changeModel(this.value)" title="{ui_js['change_model']}"></select>
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
        <div class="status">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">{status_text}</span>
        </div>
    </div>

    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">\U0001f4dd {ui_js['conversations']}</div>
            <div class="chat-list" id="chatList"></div>
        </div>
        <div class="splitter" id="sidebarSplitter" title="{ui_js['drag_resize']}"></div>
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
            <button class="remove-doc-btn" id="removeDocBtn" title="Rimuovi documento">×</button>
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
            <input type="hidden" id="voiceInput" />
            <button class="voice-btn" title="Record Voice" style="display: {voice_display};" id="voiceRecordBtn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v12a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2m14 0a7 7 0 0 0-14 0v2"/></svg>
            </button>
            <textarea id="input" rows="1" placeholder="{ui_js['input_placeholder']}"></textarea>
            <button id="sendBtn">
                <svg id="sendIcon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                <svg id="stopIcon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="display:none"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
            </button>
        </div>
    </div>
        </div>
    </div>

    <script>
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
        let sending = false;
        let currentReader = null;
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
        let currentImage = null;  // Stores base64 image data
        let pendingDocument = null;  // Stores {file, name, size} for upload on send
        let readOnlyMode = safeLocalStorageGet('readOnlyMode') === 'true';
        let currentProviderId = '{api.AI_PROVIDER}';

        const ANALYZING_BY_PROVIDER = {{
            'anthropic': {json.dumps(provider_analyzing['anthropic'].get(api.LANGUAGE, provider_analyzing['anthropic']['en']))},
            'openai': {json.dumps(provider_analyzing['openai'].get(api.LANGUAGE, provider_analyzing['openai']['en']))},
            'google': {json.dumps(provider_analyzing['google'].get(api.LANGUAGE, provider_analyzing['google']['en']))},
            'github': {json.dumps(provider_analyzing['github'].get(api.LANGUAGE, provider_analyzing['github']['en']))},
            'nvidia': {json.dumps(provider_analyzing['nvidia'].get(api.LANGUAGE, provider_analyzing['nvidia']['en']))}
        }};

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
            return ANALYZING_BY_PROVIDER[currentProviderId] || ANALYZING_BY_PROVIDER['openai'];
        }}

        function initSidebarResize() {{
            if (!sidebarEl || !splitterEl) return;

            // On mobile/touch, the sidebar becomes a stacked section and resize handle
            // is hidden via CSS. Skip width persistence and mouse drag handlers.
            const mobileLayout = window.matchMedia('(max-width: 768px)').matches || window.matchMedia('(pointer: coarse)').matches;
            if (mobileLayout) return;

            const minWidth = 150;
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

            splitterEl.addEventListener('mousedown', (e) => {{
                dragging = true;
                startX = e.clientX;
                startWidth = sidebarEl.getBoundingClientRect().width;
                document.body.classList.add('resizing');
                e.preventDefault();
            }});

            window.addEventListener('mousemove', (e) => {{
                if (!dragging) return;
                const dx = e.clientX - startX;
                let next = startWidth + dx;
                next = Math.max(minWidth, Math.min(maxWidth, next));
                sidebarEl.style.width = next + 'px';
            }});

            window.addEventListener('mouseup', () => {{
                if (!dragging) return;
                dragging = false;
                document.body.classList.remove('resizing');
                const finalW = Math.round(sidebarEl.getBoundingClientRect().width);
                safeLocalStorageSet(storageKey, String(finalW));
            }});
        }}

        function isMobileLayout() {{
            return window.matchMedia('(max-width: 768px)').matches || window.matchMedia('(pointer: coarse)').matches;
        }}

        function toggleSidebar() {{
            if (!sidebarEl) return;
            sidebarEl.classList.toggle('mobile-open');
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

            const maxSize = 50 * 1024 * 1024; // 50MB
            if (file.size > maxSize) {{
                alert('File troppo grande (max 50MB)');
                document.getElementById('documentInput').value = '';
                return;
            }}

            pendingDocument = file;
            showDocPreview(file);
            // Focus the input so the user can type a message
            if (input) input.focus();
        }}

        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;

        async function toggleVoiceRecording() {{
            const btn = document.getElementById('voiceRecordBtn');
            if (!isRecording) {{
                // Check if browser supports getUserMedia
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                    addMessage('❌ Il browser non supporta la registrazione audio. Usa HTTPS o un browser compatibile.', 'system');
                    return;
                }}

                // Check permission status first (if Permissions API available)
                if (navigator.permissions && navigator.permissions.query) {{
                    try {{
                        const permStatus = await navigator.permissions.query({{ name: 'microphone' }});
                        if (permStatus.state === 'denied') {{
                            addMessage('🎤 Accesso al microfono negato. Vai nelle impostazioni del browser per abilitarlo.', 'system');
                            return;
                        }}
                    }} catch (e) {{
                        // Permissions API may not support 'microphone' query in some browsers
                    }}
                }}

                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = (e) => {{
                        audioChunks.push(e.data);
                    }};
                    
                    mediaRecorder.onstop = () => {{
                        const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                        addMessage(`🎤 Voice recorded (${{(audioBlob.size/1024).toFixed(1)}}KB)`, 'user');
                        btn.style.backgroundColor = '#333';
                        isRecording = false;
                    }};
                    
                    mediaRecorder.start();
                    isRecording = true;
                    btn.style.backgroundColor = '#f44336';
                    btn.title = 'Stop Recording';
                }} catch (error) {{
                    if (error.name === 'NotAllowedError') {{
                        addMessage('🎤 Permesso microfono negato. Clicca sull\'icona 🔒 nella barra del browser per abilitarlo.', 'system');
                    }} else if (error.name === 'NotFoundError') {{
                        addMessage('🎤 Nessun microfono trovato. Collega un microfono e riprova.', 'system');
                    }} else if (error.name === 'NotReadableError') {{
                        addMessage('🎤 Microfono in uso da un\'altra app. Chiudi le altre app e riprova.', 'system');
                    }} else {{
                        addMessage(`🎤 Errore microfono: ${{error.message || error.name}}`, 'system');
                    }}
                }}
            }} else {{
                if (mediaRecorder && isRecording) {{
                    mediaRecorder.stop();
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());
                }}
            }}
        }}

        function toggleReadOnly(checked) {{
            readOnlyMode = checked;
            safeLocalStorageSet('readOnlyMode', checked ? 'true' : 'false');
            const label = document.getElementById('readOnlyLabel');
            if (label) label.textContent = checked ? T.readonly_on : T.readonly_off;
            const wrapper = document.querySelector('.readonly-toggle');
            if (wrapper) wrapper.classList.toggle('active', checked);
        }}

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
                /vuoi\\s+(eliminare|procedere|continuare).*?\\?/i,
                /s[i\u00ec]\\s*\\/\\s*no/i,
                /confirm.*?\\?\\s*(yes.*no)?/i,
                /type\\s+['"]?yes['"]?\\s+or\\s+['"]?no['"]?/i,
                /do\\s+you\\s+want\\s+to\\s+(delete|proceed|continue).*?\\?/i,
                /confirma.*?\\?/i,
                /escribe\\s+s[i\u00ed]\\s+o\\s+no/i,
                /confirme[sz]?.*?\\?/i,
                /tape[sz]?\\s+['"]?oui['"]?\\s+ou\\s+['"]?non['"]?/i,
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

        function extractNumberedEntityOptions(text) {{
            if (!text || typeof text !== 'string') return [];
            // Handles formats like: 1) light.kitchen — Kitchen, 1. `light.kitchen`, option 1) device name
            const lines = String(text).split(/\\r?\\n/);
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
                div.innerHTML = content;

                // If this assistant message contains a snapshot id, add an undo button
                const snap = extractSnapshotId(text);
                if (snap) {{
                    appendUndoButton(div, snap);
                }}

                // If the assistant is asking to choose an entity_id, provide tap-to-select UI
                injectEntityPicker(div, text);
            }} else {{
                div.textContent = text;
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
                    addThinkingStep('📤 Caricamento documento...');
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
                            addMessage(`❌ Upload fallito: ${{err.error || 'Errore sconosciuto'}}`, 'system');
                            sending = false;
                            setStopMode(false);
                            removeThinking();
                            return;
                        }}
                    }} catch (upErr) {{
                        addMessage(`❌ Errore upload: ${{upErr.message}}`, 'system');
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

                const payload = {{
                    message: text || `[Documento caricato: ${{docToSend ? docToSend.name : ''}}]`,
                    session_id: currentSessionId,
                    read_only: readOnlyMode
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
                            }} else if (evt.type === 'error') {{
                                removeThinking();
                                addMessage('\u274c ' + evt.message, 'system');
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

        async function loadChatList() {{
            try {{
                const resp = await fetch(apiUrl('api/conversations'));
                if (!resp.ok) throw new Error('conversations failed: ' + resp.status);
                const data = await resp.json();
                console.log('[loadChatList] received ', data.conversations ? data.conversations.length : 0, ' conversations');
                chatList.innerHTML = '';
                if (data.conversations && data.conversations.length > 0) {{
                    function parseConvTs(conv) {{
                        try {{
                            const raw = (conv && (conv.last_updated || conv.id)) ? (conv.last_updated || conv.id) : '';
                            if (typeof raw === 'number') return raw;
                            const s = String(raw || '').trim();
                            if (!s) return 0;
                            // Typical session ids are Date.now() strings
                            const n = parseInt(s, 10);
                            if (!Number.isNaN(n) && n > 0) return n;
                            const p = Date.parse(s);
                            return Number.isNaN(p) ? 0 : p;
                        }} catch (e) {{
                            console.warn('[parseConvTs] parse error for', conv, e);
                            return 0;
                        }}
                    }}

                    function formatGroupLabel(ts) {{
                        try {{
                            if (!ts || ts === 0) return '';
                            const d = new Date(ts);
                            if (Number.isNaN(d.getTime())) return '';

                            const now = new Date();
                            const startToday = new Date(now);
                            startToday.setHours(0, 0, 0, 0);
                            const startYesterday = new Date(startToday);
                            startYesterday.setDate(startYesterday.getDate() - 1);

                            const startD = new Date(d);
                            startD.setHours(0, 0, 0, 0);
                            const diffDays = Math.floor((startToday.getTime() - startD.getTime()) / 86400000);

                            if (diffDays === 0) return (T.today || 'Today');
                            if (diffDays === 1) return (T.yesterday || 'Yesterday');
                            if (diffDays >= 2 && diffDays <= 6) {{
                                const tpl = (T.days_ago || '{{n}} days ago');
                                return tpl.replace('{{n}}', String(diffDays));
                            }}

                            const sameYear = d.getFullYear() === now.getFullYear();
                            const opts = sameYear
                                ? {{ day: '2-digit', month: 'short' }}
                                : {{ day: '2-digit', month: 'short', year: 'numeric' }};
                            try {{
                                return d.toLocaleDateString(undefined, opts);
                            }} catch (e) {{
                                return d.toDateString();
                            }}
                        }} catch (e) {{
                            console.warn('[formatGroupLabel] format error for ts=', ts, e);
                            return '';
                        }}
                    }}

                    const convs = data.conversations.slice();
                    convs.sort((a, b) => {{
                        try {{
                            return parseConvTs(b) - parseConvTs(a);
                        }} catch (e) {{
                            console.warn('[loadChatList sort] sort error', e);
                            return 0;
                        }}
                    }});

                    let lastLabel = null;
                    convs.forEach((conv, idx) => {{
                        try {{
                            const ts = parseConvTs(conv);
                            const label = formatGroupLabel(ts);
                            if (label && label !== lastLabel) {{
                                const header = document.createElement('div');
                                header.className = 'chat-group-title';
                                header.textContent = label;
                                chatList.appendChild(header);
                                lastLabel = label;
                            }}
                            const item = document.createElement('div');
                            item.className = 'chat-item' + (conv.id === currentSessionId ? ' active' : '');
                            const left = document.createElement('div');
                            left.style.flex = '1';
                            left.addEventListener('click', () => loadConversation(conv.id));

                            const title = document.createElement('div');
                            title.className = 'chat-item-title';
                            title.textContent = conv.title || '';

                            const info = document.createElement('div');
                            info.className = 'chat-item-info';
                            info.textContent = String(conv.message_count || 0) + ' ' + (T.messages_count || 'messages');

                            left.appendChild(title);
                            left.appendChild(info);

                            const del = document.createElement('span');
                            del.className = 'chat-item-delete';
                            del.title = T.delete_chat || 'Delete chat';
                            del.textContent = '\U0001f5d1';
                            del.addEventListener('click', (evt) => deleteConversation(evt, conv.id));

                            item.appendChild(left);
                            item.appendChild(del);
                            chatList.appendChild(item);
                        }} catch (e) {{
                            console.error('[loadChatList forEach] error at index', idx, ':', e);
                        }}
                    }});
                }} else {{
                    chatList.innerHTML = '<div style="padding: 12px; text-align: center; color: #999; font-size: 12px;">' + T.no_conversations + '</div>';
                }}
            }} catch(e) {{
                console.error('Error loading chat list:', e);
                if (!window._chatListErrorNotified) {{
                    addMessage('\u26a0\ufe0f Error loading conversations: ' + (e && e.message ? e.message : String(e)), 'system');
                    window._chatListErrorNotified = true;
                }}
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
            safeLocalStorageSet('currentSessionId', sessionId);
            try {{
                const resp = await fetch(apiUrl(`api/conversations/${{sessionId}}`));
                if (resp.status === 404) {{
                    console.log('Session not found, creating new session');
                    newChat();
                    return;
                }}
                const data = await resp.json();
                chat.innerHTML = '';
                if (data.messages && data.messages.length > 0) {{
                    suggestionsEl.style.display = 'none';
                    data.messages.forEach(m => {{
                        if (m.role === 'user' || m.role === 'assistant') {{
                            const metadata = (m.role === 'assistant' && (m.model || m.provider)) ? {{ model: m.model, provider: m.provider }} : null;
                            addMessage(m.content, m.role, null, metadata);
                        }}
                    }});
                }} else {{
                    chat.innerHTML = `<div class="message system">
                        {msgs['welcome']}<br>
                        {msgs['provider_model']}<br>
                        {msgs['capabilities']}<br>
                        {msgs['vision_feature']}
                    </div>`;
                    suggestionsEl.style.display = 'flex';
                }}
                loadChatList();
                closeSidebarMobile();
            }} catch(e) {{ console.error('Error loading conversation:', e); }}
        }}

        async function loadHistory() {{
            await loadConversation(currentSessionId);
        }}

        async function newChat() {{
            currentSessionId = Date.now().toString();
            safeLocalStorageSet('currentSessionId', currentSessionId);
            chat.innerHTML = `<div class="message system">
                {msgs['welcome']}<br>
                {msgs['provider_model']}<br>
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
            'github': '🚀 GitHub Models'
        }};

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
        async function loadModels() {{
            try {{
                const response = await fetch(apiUrl('api/get_models'));
                if (!response.ok) {{
                    throw new Error('get_models failed: ' + response.status);
                }}
                const data = await response.json();
                console.log('[loadModels] API response:', data);

                const select = document.getElementById('modelSelect');
                const currentProvider = data.current_provider;
                const currentModel = data.current_model;

                // First-time onboarding: prompt user to pick an agent once
                if (data.needs_first_selection && !window._firstSelectionPrompted) {{
                    addMessage('\U0001f446 ' + T.select_agent, 'system');
                    window._firstSelectionPrompted = true;
                }}

                if (currentProvider) {{
                    currentProviderId = currentProvider;
                }}

                updateHeaderProviderStatus(currentProviderId, data.available_providers);

                const testBtn = document.getElementById('testNvidiaBtn');
                if (testBtn) {{
                    testBtn.style.display = (currentProviderId === 'nvidia') ? 'inline-flex' : 'none';
                }}

                console.log('[loadModels] Provider:', currentProvider, 'Current model:', currentModel);

                // Clear existing options
                select.innerHTML = '';

                // Add models for ALL available providers, grouped by optgroup
                const providerOrder = ['anthropic', 'openai', 'google', 'nvidia', 'github'];
                let availableProviders = data.available_providers && data.available_providers.length
                    ? data.available_providers.map(p => p.id)
                    : Object.keys(data.models || {{}});
                if (!availableProviders.length && currentProvider) {{
                    availableProviders = [currentProvider];
                }}

                for (const providerId of providerOrder) {{
                    if (!availableProviders.includes(providerId)) continue;
                    if (!data.models || !data.models[providerId] || data.models[providerId].length === 0) continue;

                    // Special grouping for NVIDIA: split into tested vs to-test
                    if (providerId === 'nvidia' && (Array.isArray(data.nvidia_models_tested) || Array.isArray(data.nvidia_models_to_test))) {{
                        const tested = Array.isArray(data.nvidia_models_tested) ? data.nvidia_models_tested : [];
                        const toTest = Array.isArray(data.nvidia_models_to_test) ? data.nvidia_models_to_test : [];

                        const groups = [
                            {{ label: (PROVIDER_LABELS[providerId] || providerId) + ' \u2705 ' + T.nvidia_tested, models: tested }},
                            {{ label: (PROVIDER_LABELS[providerId] || providerId) + ' ' + T.nvidia_to_test, models: toTest }},
                        ].filter(g => Array.isArray(g.models) && g.models.length > 0);

                        for (const g of groups) {{
                            const group = document.createElement('optgroup');
                            group.label = g.label;
                            g.models.forEach(model => {{
                                const option = document.createElement('option');
                                option.value = JSON.stringify({{model: model, provider: providerId}});
                                const displayName = model.replace(/^(Claude|OpenAI|Google|NVIDIA|GitHub):\\s*/, '');
                                option.textContent = displayName;
                                if (model === currentModel && providerId === currentProvider) {{
                                    option.selected = true;
                                }}
                                group.appendChild(option);
                            }});
                            select.appendChild(group);
                        }}
                        continue;
                    }}

                    const group = document.createElement('optgroup');
                    group.label = PROVIDER_LABELS[providerId] || providerId;

                    data.models[providerId].forEach(model => {{
                        const option = document.createElement('option');
                        option.value = JSON.stringify({{model: model, provider: providerId}});
                        // Show just the model name without provider prefix
                        const displayName = model.replace(/^(Claude|OpenAI|Google|NVIDIA|GitHub):\\s*/, '');
                        option.textContent = displayName;
                        if (model === currentModel && providerId === currentProvider) {{
                            option.selected = true;
                        }}
                        group.appendChild(option);
                    }});

                    select.appendChild(group);
                }}
                if (!select.options.length) {{
                    const option = document.createElement('option');
                    option.textContent = T.no_models;
                    option.disabled = true;
                    option.selected = true;
                    select.appendChild(option);
                    if (!window._modelsEmptyNotified) {{
                        addMessage('\u26a0\ufe0f ' + T.no_models_msg, 'system');
                        window._modelsEmptyNotified = true;
                    }}
                }}
                console.log('[loadModels] Loaded models for', availableProviders.length, 'providers');
            }} catch (error) {{
                console.error('[loadModels] Error loading models:', error);
                if (!window._modelsErrorNotified) {{
                    addMessage('\u26a0\ufe0f ' + T.models_load_error + (error.message || error), 'system');
                    window._modelsErrorNotified = true;
                }}
            }}
        }}

        async function testNvidiaModel() {{
            const btn = document.getElementById('testNvidiaBtn');
            if (!btn) return;

            const cursorKey = 'nvidiaTestCursor';
            const cursor = parseInt(safeLocalStorageGet(cursorKey) || '0', 10) || 0;

            const oldText = btn.textContent;
            btn.disabled = true;
            btn.textContent = '⏳ Test...';
            try {{
                const response = await fetch(apiUrl('api/nvidia/test_models'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{max_models: 20, cursor: cursor}})
                }});
                const data = await response.json().catch(() => ({{}}));

                if (response.ok && data && data.success) {{
                    if (typeof data.next_cursor === 'number') {{
                        safeLocalStorageSet(cursorKey, String(data.next_cursor));
                    }}
                    if (typeof data.remaining === 'number' && data.remaining <= 0) {{
                        safeLocalStorageSet(cursorKey, '0');
                    }}
                    const parts = [];
                    parts.push(T.nvidia_test_result.replace('{{ok}}', data.ok).replace('{{removed}}', data.removed).replace('{{tested}}', data.tested).replace('{{total}}', data.total));
                    if (data.stopped_reason) parts.push(`(${{data.stopped_reason}})`);
                    if (typeof data.timeouts === 'number' && data.timeouts > 0) parts.push('\u2014 ' + T.nvidia_timeout.replace('{{n}}', data.timeouts));
                    if (typeof data.remaining === 'number' && data.remaining > 0) parts.push('\u2014 ' + T.nvidia_remaining.replace('{{n}}', data.remaining));
                    addMessage('\U0001f50d ' + parts.join(' '), 'system');
                }} else {{
                    const msg = (data && (data.message || data.error)) || (T.nvidia_test_failed + ' (' + response.status + ')');
                    addMessage('\u26a0\ufe0f ' + msg, 'system');
                }}

                if (data && data.blocklisted) await loadModels();
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
                const parsed = JSON.parse(value);
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
                }}
            }} catch (error) {{
                console.error('Error changing model:', error);
            }}
        }}

        // Load history on page load
        function bindCspSafeHandlers() {{
            try {{
                // Bind controls without relying on inline handlers (CSP blocks onclick/onchange in HA Ingress)
                const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
                if (sidebarToggleBtn) sidebarToggleBtn.addEventListener('click', toggleSidebar);

                const modelSelect = document.getElementById('modelSelect');
                if (modelSelect) modelSelect.addEventListener('change', (e) => changeModel(e.target.value));

                const testBtn = document.getElementById('testNvidiaBtn');
                if (testBtn) testBtn.addEventListener('click', testNvidiaModel);

                const newChatBtn = document.getElementById('newChatBtn');
                if (newChatBtn) newChatBtn.addEventListener('click', newChat);

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
                if (removeDocBtn) removeDocBtn.addEventListener('click', (e) => {{ e.preventDefault(); removeDocument(); }});

                const voiceBtn = document.getElementById('voiceRecordBtn');
                if (voiceBtn) voiceBtn.addEventListener('click', toggleVoiceRecording);

                if (input) {{
                    input.addEventListener('keydown', handleKeyDown);
                    input.addEventListener('input', () => autoResize(input));
                }}

                // Suggestions: make clickable via JS (inline onclick may be blocked)
                document.querySelectorAll('.suggestion').forEach((el) => {{
                    el.addEventListener('click', () => sendSuggestion(el));
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

        (function bootUI() {{
            try {{
                // Reinforce click handler assignment (helps when inline onclick gets lost/cached)
                if (sendBtn) {{
                    sendBtn.onclick = () => handleButtonClick();
                }}

                bindCspSafeHandlers();

                initSidebarResize();
                loadModels();
                loadChatList();
                loadHistory();
                if (input) input.focus();
            }} catch (e) {{
                const msg = (e && e.message) ? e.message : String(e);
                _appendSystemRaw('❌ UI boot error: ' + msg);
            }}
        }})();
        
        // Export global functions for onclick handlers
        window.toggleVoiceRecording = toggleVoiceRecording;
        window.handleDocumentSelect = handleDocumentSelect;
        window.removeDocument = removeDocument;
        window.changeModel = changeModel;
        window.handleButtonClick = handleButtonClick;
        }}
        
    </script>
</body>
</html>"""
