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
            "mic_denied_settings": "Microphone access denied. Go to browser settings to enable it.",
            "mic_denied_icon": "Microphone denied. Click the 🔒 icon in the browser bar to enable it.",
            "mic_not_found": "No microphone found. Connect a microphone and try again.",
            "mic_in_use": "Microphone in use by another app. Close other apps and try again.",
            "mic_error": "Microphone error",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
            "tab_backups": "Backups",
            "tab_devices": "Bubble Devices",
            "tab_messaging": "📱 Messaging",
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
            "mic_denied_settings": "Accesso al microfono negato. Vai nelle impostazioni del browser per abilitarlo.",
            "mic_denied_icon": "Permesso microfono negato. Clicca l'icona 🔒 nella barra del browser per abilitarlo.",
            "mic_not_found": "Nessun microfono trovato. Collega un microfono e riprova.",
            "mic_in_use": "Microfono in uso da un'altra app. Chiudi le altre app e riprova.",
            "mic_error": "Errore microfono",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
            "tab_backups": "Backup",
            "tab_devices": "Bubble Devices",
            "tab_messaging": "📱 Messaggi",
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
            "mic_denied_settings": "Acceso al micrófono denegado. Ve a los ajustes del navegador para habilitarlo.",
            "mic_denied_icon": "Permiso de micrófono denegado. Haz clic en el icono 🔒 en la barra del navegador.",
            "mic_not_found": "No se encontró micrófono. Conecta un micrófono e inténtalo de nuevo.",
            "mic_in_use": "Micrófono en uso por otra app. Cierra las otras apps e inténtalo de nuevo.",
            "mic_error": "Error de micrófono",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bubble",
            "tab_backups": "Copias",
            "tab_devices": "Bubble Devices",
            "tab_messaging": "📱 Mensajes",
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
            "mic_denied_settings": "Acc\u00e8s au microphone refus\u00e9. Allez dans les param\u00e8tres du navigateur pour l'activer.",
            "mic_denied_icon": "Microphone refus\u00e9. Cliquez sur l'ic\u00f4ne \ud83d\udd12 dans la barre du navigateur.",
            "mic_not_found": "Aucun microphone trouv\u00e9. Connectez un microphone et r\u00e9essayez.",
            "mic_in_use": "Microphone utilis\u00e9 par une autre app. Fermez les autres apps et r\u00e9essayez.",
            "mic_error": "Erreur de microphone",
            # Sidebar tabs
            "tab_chat": "Chat",
            "tab_bubble": "Bulle",
            "tab_backups": "Sauvegardes",
            "tab_devices": "Bubble Devices",
            "tab_messaging": "📱 Messages",
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
        },
    }
    ui_js = ui_js_all.get(api.LANGUAGE, ui_js_all["en"])
    ui_js_json = json.dumps(ui_js, ensure_ascii=False)
    
    # Feature flags for UI elements
    file_upload_enabled = api.ENABLE_FILE_UPLOAD
    file_upload_display = "block" if file_upload_enabled else "none"

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
        .sidebar-tabs {{ display: flex; border-bottom: 1px solid #e0e0e0; background: #f8f9fa; }}
        .sidebar-tab {{ flex: 1; padding: 8px 4px; font-size: 12px; text-align: center; cursor: pointer; border: none; background: none; color: #666; transition: all 0.2s; border-bottom: 2px solid transparent; }}
        .sidebar-tab:hover {{ background: #f0f0f0; }}
        .sidebar-tab.active {{ color: #667eea; border-bottom-color: #667eea; font-weight: 600; }}
        .sidebar-content {{ flex: 1; overflow-y: auto; display: none; }}
        .sidebar-content.active {{ display: block; }}
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
        .model-selector {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 10px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; max-width: 240px; min-width: 0; }}
        .model-selector:hover {{ background: rgba(255,255,255,0.35); }}
        #refreshModelsBtn {{ background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 4px 7px; border-radius: 14px; font-size: 13px; cursor: pointer; transition: background 0.2s; line-height: 1; display: inline-block; }}
        #refreshModelsBtn:hover {{ background: rgba(255,255,255,0.3); }}
        #refreshModelsBtn:disabled {{ opacity: 0.5; cursor: default; }}
        @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
        #refreshModelsBtn.spinning {{ display: inline-block; animation: spin 0.8s linear infinite; }}
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

        /* Tablet: 600px - 1199px - sidebar visible but narrow */
        @media (min-width: 600px) and (max-width: 1199px) {{
            .mobile-only {{ display: none; }}
            .sidebar {{ width: 160px; min-width: 140px; max-width: 180px; }}
            .header {{ flex-wrap: wrap; padding: 10px 12px; gap: 8px; }}
            .header h1 {{ font-size: 16px; }}
            .model-selector {{ flex: 1 1 auto; max-width: 180px; font-size: 11px; }}
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
            border-bottom-color: #2a2a2a;
            color: #e0e0e0;
        }}

        body.dark-mode .chat-item:hover {{
            background: #2f2f2f;
        }}

        body.dark-mode .chat-item.active {{
            background: #1e3a8a;
            border-left-color: #8ab4f8;
        }}

        body.dark-mode .chat-item-title {{
            color: #e0e0e0;
        }}

        body.dark-mode .chat-item-info {{
            color: #808080;
        }}

        body.dark-mode .chat-group-title {{
            background: #1a1a1a;
            border-top-color: #2a2a2a;
            color: #707070;
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
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px;">\U0001f916</span>
        <h1>{agent_name}</h1>
        <span class="badge">v{api.get_version()}</span>
        <button id="sidebarToggleBtn" class="new-chat mobile-only" onclick="toggleSidebar()" title="{ui_js['conversations']}">\u2630</button>
        <select id="modelSelect" class="model-selector" title="{ui_js['change_model']}"></select>
        <button id="refreshModelsBtn" title="{ui_js.get('refresh_models', 'Refresh model list from provider APIs')}">&#x21bb;</button>
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
                <button class="sidebar-tab" data-tab="backups" onclick="switchSidebarTab('backups')">\U0001f4be {ui_js['tab_backups']}</button>
                <button class="sidebar-tab" data-tab="devices" onclick="switchSidebarTab('devices')">⚙️ {ui_js['tab_devices']}</button>
                <button class="sidebar-tab" data-tab="messaging" onclick="switchSidebarTab('messaging')">{ui_js['tab_messaging']}</button>
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

        function formatUsage(usage) {{
            if (!usage || (!usage.input_tokens && !usage.output_tokens)) return '';
            const inp = (usage.input_tokens || 0).toLocaleString();
            const out = (usage.output_tokens || 0).toLocaleString();
            let tokens = inp + ' in / ' + out + ' out';
            if (usage.cost !== undefined && usage.cost !== null) {{
                if (usage.cost > 0) {{
                    let sym = '$';  // Default
                    const curr = (usage.currency || 'USD').toUpperCase().trim();
                    if (curr === 'EUR') sym = '\u20ac';
                    else if (curr === 'GBP') sym = '\u00a3';
                    else if (curr === 'JPY') sym = '\u00a5';
                    else sym = '$';  // Fallback for any other currency
                    tokens += ' \u2022 ' + sym + usage.cost.toFixed(4);
                }} else {{
                    tokens += ' \u2022 free';
                }}
            }}
            return '<div class="message-usage">' + tokens + '</div>';
        }}

        let conversationUsage = {{ input_tokens: 0, output_tokens: 0, cost: 0, currency: 'USD' }};

        function updateConversationUsage(usage) {{
            if (!usage) return;
            conversationUsage.input_tokens += (usage.input_tokens || 0);
            conversationUsage.output_tokens += (usage.output_tokens || 0);
            conversationUsage.cost += (usage.cost || 0);
            conversationUsage.currency = usage.currency || 'USD';
            renderConversationTotal();
        }}

        function resetConversationUsage() {{
            conversationUsage = {{ input_tokens: 0, output_tokens: 0, cost: 0, currency: 'USD' }};
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
            const inp = conversationUsage.input_tokens.toLocaleString();
            const out = conversationUsage.output_tokens.toLocaleString();
            let text = '📊 ' + inp + ' in / ' + out + ' out';
            if (conversationUsage.cost > 0) {{
                const sym = conversationUsage.currency === 'EUR' ? '\u20ac' : '$';
                text += ' \u2022 ' + sym + conversationUsage.cost.toFixed(4) + ' total';
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
            // 1. Strip [CURRENT_DASHBOARD_HTML]...[/CURRENT_DASHBOARD_HTML] (may be very large)
            t = t.replace(/\\[CURRENT_DASHBOARD_HTML\\][\\s\\S]*?\\[\\/CURRENT_DASHBOARD_HTML\\]\\n?/g, '');
            // 2. Strip [CONTEXT: ... ] blocks — content ends at first ] not inside nested brackets
            //    These are always single-line context tags injected by the bubble
            t = t.replace(/\\[CONTEXT:[^\\]]*\\]\\s*/g, '');
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

                const payload = {{
                    message: text || `[${{T.document_uploaded || 'Document uploaded'}}: ${{docToSend ? docToSend.name : ''}}]`,
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
                            }} else if (evt.type === 'diff') {{
                                // Show colored diff block in the assistant message div
                                if (div && evt.content) {{
                                    const diffEl = renderDiff(evt.content);
                                    if (diffEl) div.appendChild(diffEl);
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
            }}
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
            'github_copilot': '🤖 GitHub Copilot',
            'openai_codex': '⌨️ OpenAI Codex',
            'claude_web': '🌐 Claude.ai Web ⚠️',
            'chatgpt_web': '🌐 ChatGPT Web ⚠️'
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

        // Refresh model lists by calling official provider /v1/models endpoints
        async function refreshModels() {{
            const btn = document.getElementById('refreshModelsBtn');
            if (!btn) return;
            btn.classList.add('spinning');
            btn.disabled = true;
            try {{
                const r = await fetch(apiUrl('api/refresh_models'), {{method: 'POST', credentials: 'same-origin'}});
                const data = await r.json();
                if (data.success) {{
                    const updated = Object.keys(data.updated || {{}});
                    const counts = updated.map(p => p + ':' + data.updated[p]).join(', ');
                    if (updated.length > 0) {{
                        addMessage('\u2705 Models refreshed \u2014 ' + updated.length + ' provider(s): ' + counts, 'system');
                    }} else {{
                        addMessage('\u2139\ufe0f No updates \u2014 all providers already up to date or no endpoint available.', 'system');
                    }}
                    await loadModels();
                }} else {{
                    addMessage('\u26a0\ufe0f Refresh failed: ' + (data.error || 'unknown error'), 'system');
                }}
            }} catch(e) {{
                addMessage('\u26a0\ufe0f Could not reach refresh endpoint: ' + e.message, 'system');
            }} finally {{
                btn.classList.remove('spinning');
                btn.disabled = false;
            }}
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
                if (currentModel) {{
                    currentModelDisplay = currentModel;
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
                let availableProviders = data.available_providers && data.available_providers.length
                    ? data.available_providers.map(p => p.id)
                    : Object.keys(data.models || {{}});
                if (!availableProviders.length && currentProvider) {{
                    availableProviders = [currentProvider];
                }}
                const providerOrder = [
                    'anthropic', 'openai', 'google', 'nvidia', 'github',
                    'github_copilot', 'groq', 'mistral', 'ollama', 'openrouter',
                    'deepseek', 'minimax', 'aihubmix', 'siliconflow', 'volcengine',
                    'dashscope', 'moonshot', 'zhipu'
                ];
                // Append any provider returned by the API not already in the order list
                for (const p of availableProviders) {{
                    if (!providerOrder.includes(p)) providerOrder.push(p);
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
                                const displayName = model.replace(/^(Claude|OpenAI|Google|NVIDIA|GitHub Models|GitHub Copilot|OpenAI Codex|GitHub|Groq|Mistral|Ollama|OpenRouter|DeepSeek|MiniMax|AiHubMix|SiliconFlow|VolcEngine|DashScope|Moonshot|Zhipu):\\s*/, '');
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
                        const displayName = model.replace(/^(Claude|OpenAI|Google|NVIDIA|GitHub Models|GitHub Copilot|OpenAI Codex|GitHub|Groq|Mistral|Ollama|OpenRouter|DeepSeek|MiniMax|AiHubMix|SiliconFlow|VolcEngine|DashScope|Moonshot|Zhipu):\\s*/, '');
                        option.textContent = displayName;
                        if (model === currentModel && providerId === currentProvider) {{
                            option.selected = true;
                        }}
                        group.appendChild(option);
                    }});

                    select.appendChild(group);
                }}
                
                // Hide dropdown only if there are truly no providers to choose from
                const providerCount = availableProviders.filter(p => data.models && data.models[p] && data.models[p].length > 0).length;
                if (providerCount === 0) {{
                    select.style.display = 'none';
                    console.log('[loadModels] No providers available, hiding dropdown');
                }} else {{
                    select.style.display = '';
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

                const modelSelect = document.getElementById('modelSelect');
                if (modelSelect) modelSelect.addEventListener('change', (e) => changeModel(e.target.value));

                const testBtn = document.getElementById('testNvidiaBtn');
                if (testBtn) testBtn.addEventListener('click', testNvidiaModel);

                const refreshModelsBtn = document.getElementById('refreshModelsBtn');
                if (refreshModelsBtn) refreshModelsBtn.addEventListener('click', refreshModels);

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

        (function bootUI() {{
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
                loadModels();
                loadChatList();
                loadHistory();
                if (currentProviderId === 'openai_codex') checkCodexOAuth();
                if (currentProviderId === 'github_copilot') checkCopilotOAuth();
                if (currentProviderId === 'claude_web') checkClaudeWebSession();
                if (currentProviderId === 'chatgpt_web') checkChatGPTWebSession();
                if (input) input.focus();

                // Poll every 10s for model/provider changes made from other UIs (e.g. bubble)
                let _statusFailures = 0;
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
        window.refreshModels = refreshModels;
        }}
        
    </script>
</body>
</html>"""
