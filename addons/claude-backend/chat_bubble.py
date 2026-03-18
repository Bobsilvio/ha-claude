"""Floating chat bubble module for Home Assistant integration.

Generates a JavaScript ES module that injects a floating Amira
chat bubble into every Home Assistant page. The module is registered
as a Lovelace resource and loaded via extra_module_url or /local/.

Features:
- Context-aware (automation/script/device/dashboard detection)
- Draggable button (long-press) + draggable/resizable panel
- Markdown rendering (bold, italic, code, lists, links)
- Message history persistence (localStorage)
- Voice input (Web Speech API)
- Quick action chips (context-based suggestions)
- Abort streaming button
- Auto-reload after AI modifies current page
- Multi-tab sync (BroadcastChannel API)
- Separate session from main UI
"""

import logging

logger = logging.getLogger(__name__)


def get_chat_bubble_js(
    ingress_url: str,
    language: str = "en",
    show_bubble: bool = True,
    show_card_button: bool = True,
    show_automation_button: bool = True,
) -> str:
    """Generate the floating chat bubble JavaScript module.

    Args:
        ingress_url: Addon ingress URL prefix (e.g. '/api/hassio_ingress/<token>')
        language: User language (en/it/es/fr)
        show_bubble: If False, the floating bubble button is hidden.
        show_card_button: If False, the Amira button in the card editor is hidden.
        show_automation_button: If False, disables automation-page Amira UI/button.

    Returns:
        Complete JavaScript ES module as string
    """
    T = {
        "en": {
            "placeholder": "Ask about this page...",
            "send": "Send",
            "close": "Close",
            "context_automation": "Automation",
            "context_script": "Script",
            "context_entity": "Entity",
            "context_dashboard": "Dashboard",
            "context_settings": "Settings",
            "context_logs": "System Logs",
            "thinking": "Thinking",
            "new_chat": "New chat",
            "error_connection": "Connection error. Retrying...",
            "page_reload": "Updated! Reloading page...",
            "drag_hint": "Hold to drag",
            "voice_start": "Speak now...",
            "voice_unsupported": "Voice not supported in this browser",
            "voice_processing": "Processing audio...",
            "voice_mode": "Voice mode",
            "voice_speaking": "Speaking...",
            "voice_stop_speaking": "Stop speaking",
            "wake_word_active": "Listening for 'Ok Amira'...",
            "wake_word_detected": "Amira activated! Speak now...",
            "stop": "Stop",
            "qa_analyze": "Analyze this",
            "qa_optimize": "Optimize",
            "qa_add_condition": "Add condition",
            "qa_explain": "Explain",
            "qa_fix": "Fix errors",
            "qa_add_entities": "Add entities",
            "qa_describe": "Describe dashboard",
            "qa_explain_log": "Explain this error",
            "qa_fix_log": "How to fix this?",
            "qa_show_errors": "Show all errors",
            "qa_explain_log_text": "Explain this log error and tell me what causes it",
            "qa_fix_log_text": "How can I fix this log error? Give me step-by-step instructions",
            "qa_show_errors_text": "Show me all current errors and warnings from the HA logs",
            "qa_fix_logs_text": "What are the most critical issues in the logs and how to fix them?",
            "context_card_editor": "Card editor",
            "qa_card_explain": "Explain this card",
            "qa_card_optimize": "Improve this card",
            "qa_card_explain_text": "Explain what this Lovelace card does and how it works",
            "qa_card_optimize_text": "Suggest improvements for this Lovelace card YAML",
            "qa_card_add_feature": "Add feature",
            "qa_card_add_feature_text": "What features could I add to this Lovelace card? Suggest one and show the YAML",
            "qa_card_fix": "Fix this card",
            "qa_card_fix_text": "Check this Lovelace card YAML for errors or issues and fix them",
            "card_no_yaml_warn": "\u26a0\ufe0f Card editor \u2014 switch to code mode to read YAML",
            "card_new_chat": "New chat",
            "card_history": "Chat history",
            "confirm_yes": "Yes, confirm",
            "confirm_no": "No, cancel",
            "confirm_yes_value": "yes",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Delete",
            "context_statistics": "Statistics",
            "qa_stats_validate": "Find issues",
            "qa_stats_validate_text": "Check my statistics for issues: orphaned entities that no longer exist and unit mismatches",
            "qa_stats_clean": "Remove orphaned",
            "qa_stats_clean_text": "Find and remove all orphaned statistics for entities that no longer exist",
            "qa_stats_fix_units": "Fix units",
            "qa_stats_fix_units_text": "Find and fix all unit of measurement mismatches in my statistics",
            "history": "History",
            "no_conversations": "No conversations yet",
            "chat_source": "Chat UI",
            "bubble_source": "Bubble",
            "messages_count": "messages",
            "load_error": "Error loading conversations",
            "back_to_chat": "Back to chat",
            "copy_btn": "Copy",
            "copied": "Copied!",
            "auto_sidebar_title": "Amira",
            "flow_trigger": "Trigger",
            "flow_condition": "Condition",
            "flow_action": "Action",
            "flow_no_data": "No automation data",
            "flow_on": "Flow",
            "flow_off": "Flow off",
            "flow_unavailable": "Flow unavailable for this automation.",
            "flow_unavailable_migrate": "Flow unavailable: automation has no ID or config API is not accessible. Try Migrate.",
            "flow_last_triggered": "Last triggered",
            "flow_never": "Never",
            "flow_problem_subject": "Problem: {value}",
            "flow_trigger_device_problem": "When {value} reports a problem",
            "flow_trigger_device_generic": "Device trigger",
            "flow_actions_title": "Actions",
            "flow_branch": "Branch",
            "flow_actions_count": "actions",
            "flow_notify": "Notify",
            "flow_action_word": "Action",
            "flow_wait": "Wait",
            "flow_set": "Set",
            "flow_set_value_of": "Set value of",
            "flow_with_message": "Action with message",
            "flow_automation_action": "Automation action",
            "flow_state_word": "state",
            "flow_dynamic_value": "dynamic value",
            "flow_problem": "Problem",
            "flow_no_problem": "No problem",
            "flow_when_equals": "When {entity} = {value}",
            "flow_change": "Change: {entity}",
            "flow_time_window": "Time window",
            "flow_after": "After {value}",
            "flow_before": "Before {value}",
            "flow_cyclic_execution": "Cyclic execution: {value}",
            "flow_trigger_prefix": "Trigger: {value}",
            "flow_event": "event",
            "flow_condition_prefix": "Condition: {value}",
            "flow_verify": "check",
            "flow_check_state_of": "Checks state of {entity}",
            "flow_check_threshold_of": "Checks threshold of {entity}",
            "flow_starts_when": "Starts when {entity} changes state",
            "flow_becomes": "Starts when {entity} becomes {value}",
            "flow_change_from_to": "State change: {entity} from {from} to {to}",
            "flow_starts_fixed_time": "Starts at a fixed time",
            "flow_starts_above_threshold": "Starts when a numeric threshold is crossed",
            "flow_valid_between": "Valid only between {from} and {to}",
            "flow_valid_after": "Valid only after {value}",
            "flow_valid_before": "Valid only before {value}",
            "flow_if": "If {value}",
            "flow_else": "Else",
            "flow_branch_choose": "Choose branch #{index}",
            "flow_branch_default": "Choose default branch",
            "flow_event_generic": "Event",
            "flow_event_named": "Event: {value}",
            "flow_trigger_event_generic": "Triggered by event",
            "flow_trigger_event_type": "Triggered by event: {value}",
            "flow_trigger_event_when": "When event {value} fires",
            "flow_repeat_while": "Repeat while {value}",
            "flow_repeat_count": "Repeat {value} times",
            "flow_repeat_foreach": "Repeat for each item",
            "flow_repeat_until": "Repeat until {value}",
            "flow_repeat_branch": "Loop branch",
            "flow_data": "data",
            "flow_random_color": "random color",
            "flow_brightness": "brightness",
            "flow_service": "service",
            "flow_entities": "entities",
            "flow_template_condition": "Template condition",
            "flow_template_condition_short": "Template: {value}",
            "flow_template_eval": "Evaluates template: {value}",
            "flow_template_logic": "template logic",
            "flow_dynamic_message": "dynamic message",
            "flow_wait_for": "Wait for {value}",
            "flow_template_if_equals": "Only if {field} is {value}",
            "flow_template_if_not_equals": "Only if {field} is not {value}",
            "flow_template_event_check": "Custom check on event data",
            "flow_notify_match_summary": "final score with teams, score, scorers and venue",
        },
        "it": {
            "placeholder": "Chiedi qualcosa su questa pagina...",
            "send": "Invia",
            "close": "Chiudi",
            "context_automation": "Automazione",
            "context_script": "Script",
            "context_entity": "Entità",
            "context_dashboard": "Dashboard",
            "context_settings": "Impostazioni",
            "context_logs": "Log di sistema",
            "thinking": "Sto pensando",
            "new_chat": "Nuova chat",
            "error_connection": "Errore di connessione. Riprovo...",
            "page_reload": "Aggiornato! Ricarico la pagina...",
            "drag_hint": "Tieni premuto per spostare",
            "voice_start": "Parla ora...",
            "voice_unsupported": "Voce non supportata in questo browser",
            "voice_processing": "Elaborazione audio...",
            "voice_mode": "Modalità voce",
            "voice_speaking": "Sto parlando...",
            "voice_stop_speaking": "Ferma riproduzione",
            "wake_word_active": "In ascolto per 'Ok Amira'...",
            "wake_word_detected": "Amira attivata! Parla ora...",
            "stop": "Stop",
            "qa_analyze": "Analizza",
            "qa_optimize": "Ottimizza",
            "qa_add_condition": "Aggiungi condizione",
            "qa_explain": "Spiega",
            "qa_fix": "Correggi errori",
            "qa_add_entities": "Aggiungi entità",
            "qa_describe": "Descrivi dashboard",
            "qa_explain_log": "Spiega questo errore",
            "qa_fix_log": "Come si risolve?",
            "qa_show_errors": "Mostra tutti gli errori",
            "qa_explain_log_text": "Spiega questo errore di log e dimmi cosa lo causa",
            "qa_fix_log_text": "Come posso risolvere questo errore di log? Dammi le istruzioni passo per passo",
            "qa_show_errors_text": "Mostrami tutti gli errori e avvisi attuali nei log di Home Assistant",
            "qa_fix_logs_text": "Quali sono i problemi più critici nei log e come risolverli?",
            "context_card_editor": "Editor card",
            "qa_card_explain": "Spiega questa card",
            "qa_card_optimize": "Migliora questa card",
            "qa_card_explain_text": "Spiega cosa fa questa card Lovelace e come funziona",
            "qa_card_optimize_text": "Suggerisci miglioramenti per questo YAML della card Lovelace",
            "qa_card_add_feature": "Aggiungi funzione",
            "qa_card_add_feature_text": "Che funzionalità potrei aggiungere a questa card Lovelace? Suggerisci qualcosa e mostrami lo YAML",
            "qa_card_fix": "Correggi card",
            "qa_card_fix_text": "Controlla questo YAML della card Lovelace per errori o problemi e correggili",
            "card_no_yaml_warn": "\u26a0\ufe0f Editor card \u2014 passa alla modalit\u00e0 codice per leggere lo YAML",
            "card_new_chat": "Nuova chat",
            "card_history": "Storico chat",
            "confirm_yes": "Sì, conferma",
            "confirm_no": "No, annulla",
            "confirm_yes_value": "si",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Elimina",
            "context_statistics": "Statistiche",
            "qa_stats_validate": "Trova problemi",
            "qa_stats_validate_text": "Controlla le mie statistiche: trova entit\u00e0 orfane che non esistono pi\u00f9 e problemi di unit\u00e0 di misura",
            "qa_stats_clean": "Elimina orfane",
            "qa_stats_clean_text": "Trova e rimuovi tutte le statistiche di entit\u00e0 che non esistono pi\u00f9",
            "qa_stats_fix_units": "Correggi unit\u00e0",
            "qa_stats_fix_units_text": "Trova e correggi tutti i problemi di unit\u00e0 di misura nelle statistiche",
            "history": "Cronologia",
            "no_conversations": "Nessuna conversazione",
            "chat_source": "Chat UI",
            "bubble_source": "Bubble",
            "messages_count": "messaggi",
            "load_error": "Errore nel caricamento conversazioni",
            "back_to_chat": "Torna alla chat",
            "copy_btn": "Copia",
            "copied": "Copiato!",
            "auto_sidebar_title": "Amira",
            "flow_trigger": "Trigger",
            "flow_condition": "Condizione",
            "flow_action": "Azione",
            "flow_no_data": "Nessun dato automazione",
            "flow_on": "Flow",
            "flow_off": "Flow off",
            "flow_unavailable": "Flow non disponibile per questa automazione.",
            "flow_unavailable_migrate": "Flow non disponibile: automazione senza ID/config API non accessibile. Prova \"Migra\".",
            "flow_last_triggered": "Ultima attivazione",
            "flow_never": "Mai",
            "flow_problem_subject": "Problema: {value}",
            "flow_trigger_device_problem": "Quando {value} segnala un problema",
            "flow_trigger_device_generic": "Trigger dispositivo",
            "flow_actions_title": "Azioni",
            "flow_branch": "Ramo",
            "flow_actions_count": "azioni",
            "flow_notify": "Notifica",
            "flow_action_word": "Azione",
            "flow_wait": "Attendi",
            "flow_set": "Imposta",
            "flow_set_value_of": "Imposta valore di",
            "flow_with_message": "Azione con messaggio",
            "flow_automation_action": "Azione automazione",
            "flow_state_word": "stato",
            "flow_dynamic_value": "valore dinamico",
            "flow_problem": "Problema",
            "flow_no_problem": "Nessun problema",
            "flow_when_equals": "Quando {entity} = {value}",
            "flow_change": "Cambio: {entity}",
            "flow_time_window": "Fascia oraria",
            "flow_after": "Dopo {value}",
            "flow_before": "Prima di {value}",
            "flow_cyclic_execution": "Esecuzione ciclica: {value}",
            "flow_trigger_prefix": "Trigger: {value}",
            "flow_event": "evento",
            "flow_condition_prefix": "Condizione: {value}",
            "flow_verify": "verifica",
            "flow_check_state_of": "Controlla stato di {entity}",
            "flow_check_threshold_of": "Controlla soglia numerica di {entity}",
            "flow_starts_when": "Parte quando {entity} cambia stato",
            "flow_becomes": "Parte quando {entity} diventa {value}",
            "flow_change_from_to": "Cambio stato: {entity} da {from} a {to}",
            "flow_starts_fixed_time": "Parte a un orario fisso",
            "flow_starts_above_threshold": "Parte quando supera una soglia numerica",
            "flow_valid_between": "Valida solo tra {from} e {to}",
            "flow_valid_after": "Valida solo dopo {value}",
            "flow_valid_before": "Valida solo prima di {value}",
            "flow_if": "Se {value}",
            "flow_else": "Altrimenti",
            "flow_branch_choose": "Ramo choose #{index}",
            "flow_branch_default": "Ramo default choose",
            "flow_event_generic": "Evento",
            "flow_event_named": "Evento: {value}",
            "flow_trigger_event_generic": "Attivato da evento",
            "flow_trigger_event_type": "Attivato da evento: {value}",
            "flow_trigger_event_when": "Quando l'evento {value} viene attivato",
            "flow_repeat_while": "Ripeti finché {value}",
            "flow_repeat_count": "Ripeti {value} volte",
            "flow_repeat_foreach": "Ripeti per ogni elemento",
            "flow_repeat_until": "Ripeti fino a {value}",
            "flow_repeat_branch": "Ramo ciclo",
            "flow_data": "dati",
            "flow_random_color": "colore casuale",
            "flow_brightness": "luminosità",
            "flow_service": "servizio",
            "flow_entities": "entità",
            "flow_template_condition": "Condizione template",
            "flow_template_condition_short": "Template: {value}",
            "flow_template_eval": "Valuta template: {value}",
            "flow_template_logic": "logica template",
            "flow_dynamic_message": "messaggio dinamico",
            "flow_wait_for": "Attendi {value}",
            "flow_template_if_equals": "Solo se {field} è {value}",
            "flow_template_if_not_equals": "Solo se {field} non è {value}",
            "flow_template_event_check": "Controllo personalizzato sui dati evento",
            "flow_notify_match_summary": "risultato finale con squadre, punteggio, marcatori e stadio",
        },
        "es": {
            "placeholder": "Pregunta sobre esta página...",
            "send": "Enviar",
            "close": "Cerrar",
            "context_automation": "Automatización",
            "context_script": "Script",
            "context_entity": "Entidad",
            "context_dashboard": "Panel",
            "context_settings": "Configuración",
            "context_logs": "Registros del sistema",
            "thinking": "Pensando",
            "new_chat": "Nuevo chat",
            "error_connection": "Error de conexión. Reintentando...",
            "page_reload": "Actualizado! Recargando página...",
            "drag_hint": "Mantén presionado para mover",
            "voice_start": "Habla ahora...",
            "voice_unsupported": "Voz no soportada en este navegador",
            "voice_processing": "Procesando audio...",
            "voice_mode": "Modo voz",
            "voice_speaking": "Hablando...",
            "voice_stop_speaking": "Detener reproducción",
            "wake_word_active": "Escuchando 'Ok Amira'...",
            "wake_word_detected": "¡Amira activada! Habla ahora...",
            "stop": "Parar",
            "qa_analyze": "Analizar",
            "qa_optimize": "Optimizar",
            "qa_add_condition": "Añadir condición",
            "qa_explain": "Explicar",
            "qa_fix": "Corregir errores",
            "qa_add_entities": "Añadir entidades",
            "qa_describe": "Describir panel",
            "qa_explain_log": "Explica este error",
            "qa_fix_log": "¿Cómo solucionarlo?",
            "qa_show_errors": "Ver todos los errores",
            "qa_explain_log_text": "Explica este error de registro y dime qué lo causa",
            "qa_fix_log_text": "¿Cómo puedo corregir este error de registro? Dame instrucciones paso a paso",
            "qa_show_errors_text": "Muéstrame todos los errores y avisos actuales en los registros de Home Assistant",
            "qa_fix_logs_text": "¿Cuáles son los problemas más críticos en los registros y cómo solucionarlos?",
            "context_card_editor": "Editor de tarjeta",
            "qa_card_explain": "Explicar tarjeta",
            "qa_card_optimize": "Mejorar tarjeta",
            "qa_card_explain_text": "Explica qué hace esta tarjeta Lovelace y cómo funciona",
            "qa_card_optimize_text": "Sugiere mejoras para el YAML de esta tarjeta Lovelace",
            "qa_card_add_feature": "Añadir función",
            "qa_card_add_feature_text": "¿Qué funciones podría añadir a esta tarjeta Lovelace? Sugiere una y muéstrame el YAML",
            "qa_card_fix": "Corregir tarjeta",
            "qa_card_fix_text": "Revisa el YAML de esta tarjeta Lovelace en busca de errores y corrígelos",
            "card_no_yaml_warn": "\u26a0\ufe0f Editor de tarjeta \u2014 cambia al modo c\u00f3digo para leer el YAML",
            "card_new_chat": "Nuevo chat",
            "card_history": "Historial de chats",
            "confirm_yes": "Sí, confirma",
            "confirm_no": "No, cancela",
            "confirm_yes_value": "si",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Eliminar",
            "context_statistics": "Estad\u00edsticas",
            "qa_stats_validate": "Buscar problemas",
            "qa_stats_validate_text": "Revisa mis estad\u00edsticas: encuentra entidades hu\u00e9rfanas y problemas de unidades",
            "qa_stats_clean": "Eliminar hu\u00e9rfanas",
            "qa_stats_clean_text": "Encuentra y elimina todas las estad\u00edsticas de entidades que ya no existen",
            "qa_stats_fix_units": "Corregir unidades",
            "qa_stats_fix_units_text": "Encuentra y corrige todos los problemas de unidades de medida en las estad\u00edsticas",
            "history": "Historial",
            "no_conversations": "Sin conversaciones",
            "chat_source": "Chat UI",
            "bubble_source": "Bubble",
            "messages_count": "mensajes",
            "load_error": "Error al cargar conversaciones",
            "back_to_chat": "Volver al chat",
            "copy_btn": "Copiar",
            "copied": "\u00a1Copiado!",
            "auto_sidebar_title": "Amira",
            "flow_trigger": "Disparador",
            "flow_condition": "Condici\u00f3n",
            "flow_action": "Acci\u00f3n",
            "flow_no_data": "Sin datos de automatizaci\u00f3n",
            "flow_on": "Flow",
            "flow_off": "Flow off",
            "flow_unavailable": "Flow no disponible para esta automatización.",
            "flow_unavailable_migrate": "Flow no disponible: la automatización no tiene ID o la API no es accesible. Prueba \"Migrar\".",
            "flow_last_triggered": "Última activación",
            "flow_never": "Nunca",
            "flow_problem_subject": "Problema: {value}",
            "flow_trigger_device_problem": "Cuando {value} reporta un problema",
            "flow_trigger_device_generic": "Disparador de dispositivo",
            "flow_actions_title": "Acciones",
            "flow_branch": "Rama",
            "flow_actions_count": "acciones",
            "flow_notify": "Notificar",
            "flow_action_word": "Acción",
            "flow_wait": "Esperar",
            "flow_set": "Establecer",
            "flow_set_value_of": "Establecer valor de",
            "flow_with_message": "Acción con mensaje",
            "flow_automation_action": "Acción de automatización",
            "flow_state_word": "estado",
            "flow_dynamic_value": "valor dinámico",
            "flow_problem": "Problema",
            "flow_no_problem": "Sin problema",
            "flow_when_equals": "Cuando {entity} = {value}",
            "flow_change": "Cambio: {entity}",
            "flow_time_window": "Franja horaria",
            "flow_after": "Después de {value}",
            "flow_before": "Antes de {value}",
            "flow_cyclic_execution": "Ejecución cíclica: {value}",
            "flow_trigger_prefix": "Disparador: {value}",
            "flow_event": "evento",
            "flow_condition_prefix": "Condición: {value}",
            "flow_verify": "verificación",
            "flow_check_state_of": "Comprueba el estado de {entity}",
            "flow_check_threshold_of": "Comprueba el umbral numérico de {entity}",
            "flow_starts_when": "Se inicia cuando {entity} cambia de estado",
            "flow_becomes": "Se inicia cuando {entity} pasa a {value}",
            "flow_change_from_to": "Cambio de estado: {entity} de {from} a {to}",
            "flow_starts_fixed_time": "Se inicia a una hora fija",
            "flow_starts_above_threshold": "Se inicia al superar un umbral numérico",
            "flow_valid_between": "Válido solo entre {from} y {to}",
            "flow_valid_after": "Válido solo después de {value}",
            "flow_valid_before": "Válido solo antes de {value}",
            "flow_if": "Si {value}",
            "flow_else": "Si no",
            "flow_branch_choose": "Rama choose #{index}",
            "flow_branch_default": "Rama predeterminada choose",
            "flow_event_generic": "Evento",
            "flow_event_named": "Evento: {value}",
            "flow_trigger_event_generic": "Activado por evento",
            "flow_trigger_event_type": "Activado por evento: {value}",
            "flow_trigger_event_when": "Cuando se activa el evento {value}",
            "flow_repeat_while": "Repetir mientras {value}",
            "flow_repeat_count": "Repetir {value} veces",
            "flow_repeat_foreach": "Repetir por cada elemento",
            "flow_repeat_until": "Repetir hasta {value}",
            "flow_repeat_branch": "Rama de bucle",
            "flow_data": "datos",
            "flow_random_color": "color aleatorio",
            "flow_brightness": "brillo",
            "flow_service": "servicio",
            "flow_entities": "entidades",
            "flow_template_condition": "Condición de plantilla",
            "flow_template_condition_short": "Plantilla: {value}",
            "flow_template_eval": "Evalúa plantilla: {value}",
            "flow_template_logic": "lógica de plantilla",
            "flow_dynamic_message": "mensaje dinámico",
            "flow_wait_for": "Esperar {value}",
            "flow_template_if_equals": "Solo si {field} es {value}",
            "flow_template_if_not_equals": "Solo si {field} no es {value}",
            "flow_template_event_check": "Comprobación personalizada en datos del evento",
            "flow_notify_match_summary": "resultado final con equipos, marcador, goleadores y estadio",
        },
        "fr": {
            "placeholder": "Posez une question sur cette page...",
            "send": "Envoyer",
            "close": "Fermer",
            "context_automation": "Automatisation",
            "context_script": "Script",
            "context_entity": "Entité",
            "context_dashboard": "Tableau de bord",
            "context_settings": "Paramètres",
            "context_logs": "Journaux système",
            "thinking": "Réflexion",
            "new_chat": "Nouveau chat",
            "error_connection": "Erreur de connexion. Réessai...",
            "page_reload": "Mis à jour! Rechargement...",
            "drag_hint": "Maintenez pour déplacer",
            "voice_start": "Parlez maintenant...",
            "voice_unsupported": "Voix non supportée dans ce navigateur",
            "voice_processing": "Traitement audio...",
            "voice_mode": "Mode vocal",
            "voice_speaking": "En train de parler...",
            "voice_stop_speaking": "Arrêter la lecture",
            "wake_word_active": "Écoute de 'Ok Amira'...",
            "wake_word_detected": "Amira activée ! Parlez maintenant...",
            "stop": "Arrêter",
            "qa_analyze": "Analyser",
            "qa_optimize": "Optimiser",
            "qa_add_condition": "Ajouter condition",
            "qa_explain": "Expliquer",
            "qa_fix": "Corriger erreurs",
            "qa_add_entities": "Ajouter entités",
            "qa_describe": "Décrire tableau",
            "qa_explain_log": "Expliquer cette erreur",
            "qa_fix_log": "Comment corriger?",
            "qa_show_errors": "Voir toutes les erreurs",
            "qa_explain_log_text": "Explique cette erreur de journal et dis-moi ce qui la cause",
            "qa_fix_log_text": "Comment puis-je corriger cette erreur de journal ? Donne-moi des instructions étape par étape",
            "qa_show_errors_text": "Montre-moi toutes les erreurs et avertissements actuels dans les journaux Home Assistant",
            "qa_fix_logs_text": "Quels sont les problèmes les plus critiques dans les journaux et comment les corriger ?",
            "context_card_editor": "Éditeur de carte",
            "qa_card_explain": "Expliquer la carte",
            "qa_card_optimize": "Améliorer la carte",
            "qa_card_explain_text": "Explique ce que fait cette carte Lovelace et comment elle fonctionne",
            "qa_card_optimize_text": "Suggère des améliorations pour le YAML de cette carte Lovelace",
            "qa_card_add_feature": "Ajouter fonction",
            "qa_card_add_feature_text": "Quelles fonctionnalités pourrais-je ajouter à cette carte Lovelace ? Suggère-en une et montre-moi le YAML",
            "qa_card_fix": "Corriger la carte",
            "qa_card_fix_text": "Vérifie le YAML de cette carte Lovelace pour des erreurs et corrige-les",
            "card_no_yaml_warn": "\u26a0\ufe0f \u00c9diteur de carte \u2014 passe en mode code pour lire le YAML",
            "card_new_chat": "Nouveau chat",
            "card_history": "Historique des chats",
            "confirm_yes": "Oui, confirme",
            "confirm_no": "Non, annule",
            "confirm_yes_value": "oui",
            "confirm_no_value": "non",
            "confirm_delete_yes": "Supprimer",
            "context_statistics": "Statistiques",
            "qa_stats_validate": "Trouver probl\u00e8mes",
            "qa_stats_validate_text": "V\u00e9rifie mes statistiques : trouve les entit\u00e9s orphelines et les probl\u00e8mes d'unit\u00e9s",
            "qa_stats_clean": "Supprimer orphelines",
            "qa_stats_clean_text": "Trouve et supprime toutes les statistiques des entit\u00e9s qui n'existent plus",
            "qa_stats_fix_units": "Corriger unit\u00e9s",
            "qa_stats_fix_units_text": "Trouve et corrige tous les probl\u00e8mes d'unit\u00e9s de mesure dans les statistiques",
            "history": "Historique",
            "no_conversations": "Aucune conversation",
            "chat_source": "Chat UI",
            "bubble_source": "Bubble",
            "messages_count": "messages",
            "load_error": "Erreur de chargement des conversations",
            "back_to_chat": "Retour au chat",
            "copy_btn": "Copier",
            "copied": "Copi\u00e9 !",
            "auto_sidebar_title": "Amira",
            "flow_trigger": "D\u00e9clencheur",
            "flow_condition": "Condition",
            "flow_action": "Action",
            "flow_no_data": "Aucune donn\u00e9e d'automatisation",
            "flow_on": "Flow",
            "flow_off": "Flow off",
            "flow_unavailable": "Flow indisponible pour cette automatisation.",
            "flow_unavailable_migrate": "Flow indisponible : automatisation sans ID ou API de configuration inaccessible. Essayez \"Migrer\".",
            "flow_last_triggered": "Dernière activation",
            "flow_never": "Jamais",
            "flow_problem_subject": "Problème : {value}",
            "flow_trigger_device_problem": "Quand {value} signale un problème",
            "flow_trigger_device_generic": "Déclencheur appareil",
            "flow_actions_title": "Actions",
            "flow_branch": "Branche",
            "flow_actions_count": "actions",
            "flow_notify": "Notifier",
            "flow_action_word": "Action",
            "flow_wait": "Attendre",
            "flow_set": "Définir",
            "flow_set_value_of": "Définir la valeur de",
            "flow_with_message": "Action avec message",
            "flow_automation_action": "Action d'automatisation",
            "flow_state_word": "état",
            "flow_dynamic_value": "valeur dynamique",
            "flow_problem": "Problème",
            "flow_no_problem": "Aucun problème",
            "flow_when_equals": "Quand {entity} = {value}",
            "flow_change": "Changement : {entity}",
            "flow_time_window": "Plage horaire",
            "flow_after": "Après {value}",
            "flow_before": "Avant {value}",
            "flow_cyclic_execution": "Exécution cyclique : {value}",
            "flow_trigger_prefix": "Déclencheur : {value}",
            "flow_event": "événement",
            "flow_condition_prefix": "Condition : {value}",
            "flow_verify": "vérification",
            "flow_check_state_of": "Vérifie l'état de {entity}",
            "flow_check_threshold_of": "Vérifie le seuil numérique de {entity}",
            "flow_starts_when": "Démarre quand {entity} change d'état",
            "flow_becomes": "Démarre quand {entity} devient {value}",
            "flow_change_from_to": "Changement d'état : {entity} de {from} à {to}",
            "flow_starts_fixed_time": "Démarre à une heure fixe",
            "flow_starts_above_threshold": "Démarre quand un seuil numérique est dépassé",
            "flow_valid_between": "Valide uniquement entre {from} et {to}",
            "flow_valid_after": "Valide uniquement après {value}",
            "flow_valid_before": "Valide uniquement avant {value}",
            "flow_if": "Si {value}",
            "flow_else": "Sinon",
            "flow_branch_choose": "Branche choose #{index}",
            "flow_branch_default": "Branche par défaut choose",
            "flow_event_generic": "Événement",
            "flow_event_named": "Événement : {value}",
            "flow_trigger_event_generic": "Déclenché par événement",
            "flow_trigger_event_type": "Déclenché par événement : {value}",
            "flow_trigger_event_when": "Quand l'événement {value} se déclenche",
            "flow_repeat_while": "Répéter tant que {value}",
            "flow_repeat_count": "Répéter {value} fois",
            "flow_repeat_foreach": "Répéter pour chaque élément",
            "flow_repeat_until": "Répéter jusqu'à {value}",
            "flow_repeat_branch": "Branche de boucle",
            "flow_data": "données",
            "flow_random_color": "couleur aléatoire",
            "flow_brightness": "luminosité",
            "flow_service": "service",
            "flow_entities": "entités",
            "flow_template_condition": "Condition de template",
            "flow_template_condition_short": "Template : {value}",
            "flow_template_eval": "Évalue le template : {value}",
            "flow_template_logic": "logique de template",
            "flow_dynamic_message": "message dynamique",
            "flow_wait_for": "Attendre {value}",
            "flow_template_if_equals": "Seulement si {field} est {value}",
            "flow_template_if_not_equals": "Seulement si {field} n'est pas {value}",
            "flow_template_event_check": "Vérification personnalisée sur les données d'événement",
            "flow_notify_match_summary": "résultat final avec équipes, score, buteurs et stade",
        },
    }

    t = T.get(language, T["en"])
    # Voice language code for Web Speech API
    voice_lang = {"en": "en-US", "it": "it-IT", "es": "es-ES", "fr": "fr-FR"}.get(language, "en-US")

    return f"""/**
 * Amira - Floating Chat Bubble for Home Assistant
 * Context-aware, draggable, resizable, with voice input and markdown rendering.
 */
(function() {{
  'use strict';

  console.log('[Amira] Bubble JS executing — bubble={show_bubble}, card_btn={show_card_button}, auto_btn={show_automation_button}');

  // Global error handler — shows JS errors as visible banner + sends to backend
  if (!window.__AMIRA_BUBBLE_ERROR_HANDLER) {{
    window.__AMIRA_BUBBLE_ERROR_HANDLER = true;
    window.__AMIRA_BROWSER_ERRORS = window.__AMIRA_BROWSER_ERRORS || [];
    function _amiraBubbleSendError(entry) {{
      window.__AMIRA_BROWSER_ERRORS.push(entry);
      if (window.__AMIRA_BROWSER_ERRORS.length > 100) window.__AMIRA_BROWSER_ERRORS.shift();
      try {{
        var bp = (window.location.pathname || '/').endsWith('/') ? window.location.pathname : (window.location.pathname + '/');
        var url = window.location.origin.replace(/\\/$/, '') + bp + 'api/browser-errors';
        navigator.sendBeacon(url, JSON.stringify({{ errors: [entry] }}));
      }} catch(e) {{}}
    }}
    var _ourScriptSrc = (document.currentScript && document.currentScript.src) || '';
    window.addEventListener('error', function(ev) {{
      var src = ev.filename || '';
      var isOurs = _ourScriptSrc && src && src.indexOf(_ourScriptSrc.split('?')[0].split('/').pop().replace('.js','')) !== -1;
      // Always log + beacon, but only show red banner for errors from our own script
      _amiraBubbleSendError({{ level: 'error', message: String(ev.message), source: src, line: ev.lineno, col: ev.colno, stack: ev.error && ev.error.stack || '', timestamp: new Date().toISOString(), ui: 'bubble' }});
      if (!isOurs) {{
        // Third-party component error — log quietly, don't show banner
        console.warn('[Amira] third-party JS error (not ours):', ev.message, 'at', src, ev.lineno + ':' + ev.colno);
        return;
      }}
      console.error('[Amira Bubble JS Error]', ev.message, 'at', src, ev.lineno + ':' + ev.colno);
      var d = document.createElement('div');
      d.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:#b00020;color:#fff;padding:12px 16px;font:13px/1.4 monospace;max-height:30vh;overflow:auto;cursor:pointer;';
      d.textContent = '[Bubble JS Error] ' + ev.message + ' (line ' + ev.lineno + ':' + ev.colno + ')';
      d.title = 'Click per chiudere';
      d.onclick = function() {{ d.remove(); }};
      if (document.body) document.body.prepend(d);
    }});
  }}

  // Ensure DOM is ready before injecting
  if (!document.body) {{
    console.warn('[Amira] document.body not ready — deferring to DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', function() {{
      // Re-run by re-creating script element
      var s = document.createElement('script');
      s.src = document.currentScript ? document.currentScript.src : '';
      if (s.src) document.head.appendChild(s);
    }});
    return;
  }}

  const INGRESS_URL = '{ingress_url}';
  const API_BASE = INGRESS_URL;
  const UI_LANG = '{language}';
  const AMIRA_ENABLE_AUTOMATION_BUTTON = {'true' if show_automation_button else 'false'};
  const T = {__import__('json').dumps(t, ensure_ascii=False)};
  const VOICE_LANG = '{voice_lang}';
  function tt(key, fallback) {{
    try {{
      return (T && Object.prototype.hasOwnProperty.call(T, key) && T[key] !== undefined && T[key] !== null && T[key] !== '')
        ? String(T[key]) : String(fallback || '');
    }} catch(e) {{ return String(fallback || ''); }}
  }}
  function tf(key, fallback, vars) {{
    var s = tt(key, fallback);
    if (!vars) return s;
    Object.keys(vars).forEach(function(k) {{
      s = s.split(String.fromCharCode(123) + k + String.fromCharCode(125)).join(String(vars[k]));
    }});
    return s;
  }}

  // ---- Ingress session (needed for companion app / tablet WebView) ----
  // The companion app does not automatically get a hassio_session cookie.
  // We create one by calling /api/hassio/ingress/session with the HA Bearer token.
  let _ingressSessionOk = false;
  function _getHassToken() {{
    try {{
      const ha = document.querySelector('home-assistant');
      return (ha && ha.hass && ha.hass.auth && ha.hass.auth.data && ha.hass.auth.data.access_token) || '';
    }} catch(e) {{ return ''; }}
  }}
  async function _ensureIngressSession() {{
    if (_ingressSessionOk) return true;
    const token = _getHassToken();
    if (!token) return false;
    try {{
      const resp = await fetch('/api/hassio/ingress/session', {{
        method: 'POST',
        credentials: 'same-origin',
        headers: {{ 'Authorization': 'Bearer ' + token }},
      }});
      if (resp.ok) {{
        _ingressSessionOk = true;
        console.log('[Amira] Ingress session created (companion app / tablet)');
        return true;
      }}
    }} catch(e) {{}}
    return false;
  }}

  // ---- Device detection ----
  // Phone: small screen with touch (hide bubble — too small, accidental taps)
  // Tablet: larger touch screen (show bubble — usable screen size)
  // Desktop: mouse-based (always show bubble)
  const ua = navigator.userAgent;
  const isPhone = /iPhone|iPod/i.test(ua) || (/Android/i.test(ua) && /Mobile/i.test(ua));
  const isTablet = !isPhone && (/iPad/i.test(ua) || (/Android/i.test(ua) && !/Mobile/i.test(ua)) || (navigator.maxTouchPoints > 1 && window.innerWidth >= 600));

  // Hide only on phones — tablets and desktops get the bubble
  if (isPhone) return;

  // Prevent double injection
  if (document.getElementById('ha-claude-bubble')) return;

  // ---- HTML Dashboard names cache (for URL-based detection) ----
  let _htmlDashboardNames = null;
  fetch(API_BASE + '/custom_dashboards', {{credentials:'same-origin'}})
    .then(r => r.ok ? r.json() : null)
    .then(data => {{
      if (data && data.dashboards) {{
        _htmlDashboardNames = data.dashboards.map(d => d.name);
      }}
    }}).catch(() => {{}});

  // ---- Persistence helpers ----
  const STORE_PREFIX = 'ha-claude-bubble-';
  function loadSetting(key, fallback) {{
    try {{ const v = localStorage.getItem(STORE_PREFIX + key); return v ? JSON.parse(v) : fallback; }}
    catch(e) {{ return fallback; }}
  }}
  function saveSetting(key, val) {{
    try {{ localStorage.setItem(STORE_PREFIX + key, JSON.stringify(val)); }} catch(e) {{}}
  }}

  // ---- Multi-tab sync via BroadcastChannel ----
  let bc = null;
  try {{ bc = new BroadcastChannel('ha-claude-bubble-sync'); }} catch(e) {{}}

  function broadcastEvent(type, data) {{
    if (bc) try {{ bc.postMessage({{ type, ...data }}); }} catch(e) {{}}
  }}

  // ---- Simple Markdown renderer ----
  function renderMarkdown(text) {{
    if (!text) return '';
    
    // 1. Extract raw HTML diff blocks BEFORE any escaping/processing
    var diffBlocks = [];
    text = text.replace(/<!--DIFF-->([\\s\\S]*?)<!--\\/DIFF-->/g, function(m, html) {{
      diffBlocks.push(html);
      return '%%DIFF_' + (diffBlocks.length - 1) + '%%';
    }});
    
    // 1b. Extract <details>...</details> blocks before escaping
    // The AI uses these for collapsible entity lists.  We render them as-is
    // but still sanitise the inner text (strip script tags, on* attrs).
    var detailsBlocks = [];
    text = text.replace(/<details[^>]*>[\\s\\S]*?<\\/details>/gi, function(m) {{
      // Minimal sanitise: remove script tags and event handlers
      var safe = m.replace(/<script[\\s\\S]*?<\\/script>/gi, '')
                  .replace(/\\bon\\w+\\s*=\\s*["'][^"']*["']/gi, '');
      detailsBlocks.push(safe);
      return '%%DETAILS_' + (detailsBlocks.length - 1) + '%%';
    }});
    
    let html = text
      // Escape HTML
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      // Code blocks (``` ... ```)
      .replace(/```(\\w*)\\n([\\s\\S]*?)```/g, (_, lang, code) =>
        '<pre class="md-code-block"><code>' + code.trim() + '</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
      // Bold **text** or __text__
      .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
      .replace(/__(.+?)__/g, '<strong>$1</strong>')
      // Italic *text* or _text_
      .replace(/(?<![\\w*])\\*([^*]+)\\*(?![\\w*])/g, '<em>$1</em>')
      .replace(/(?<![\\w_])_([^_]+)_(?![\\w_])/g, '<em>$1</em>')
      // Links [text](url)
      .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      // Headers ### text
      .replace(/^### (.+)$/gm, '<strong style="font-size:1.05em">$1</strong>')
      .replace(/^## (.+)$/gm, '<strong style="font-size:1.1em">$1</strong>')
      .replace(/^# (.+)$/gm, '<strong style="font-size:1.15em">$1</strong>');

    // Unordered lists (- item or * item)
    html = html.replace(/^([ ]*)[\\-\\*] (.+)$/gm, (_, indent, content) => {{
      const level = Math.floor(indent.length / 2);
      return '<div class="md-li" style="padding-left:' + (level * 12 + 8) + 'px">&bull; ' + content + '</div>';
    }});
    // Ordered lists (1. item)
    html = html.replace(/^([ ]*)\\d+\\. (.+)$/gm, (_, indent, content) => {{
      const level = Math.floor(indent.length / 2);
      return '<div class="md-li" style="padding-left:' + (level * 12 + 8) + 'px">' + content + '</div>';
    }});
    // Line breaks (preserve single newlines as <br>)
    html = html.replace(/\\n/g, '<br>');
    // Clean up <br> before/after block elements
    html = html.replace(/<br>(<pre|<div|<strong style)/g, '$1');
    html = html.replace(/(<\\/pre>|<\\/div>)<br>/g, '$1');
    
    // 2. Restore diff HTML blocks (untouched by markdown transforms)
    for (var i = 0; i < diffBlocks.length; i++) {{
      html = html.replace('%%DIFF_' + i + '%%', diffBlocks[i]);
    }}
    // 2b. Restore <details> blocks
    for (var i = 0; i < detailsBlocks.length; i++) {{
      html = html.replace('%%DETAILS_' + i + '%%', detailsBlocks[i]);
    }}
    return html;
  }}

  // ---- Context Detection ----
  function findIframesDeep(root) {{
    const iframes = [];
    const queue = [root];
    while (queue.length > 0) {{
      const el = queue.shift();
      if (el.tagName === 'IFRAME') iframes.push(el);
      if (el.shadowRoot) queue.push(el.shadowRoot);
      if (el.children) for (const child of el.children) queue.push(child);
    }}
    return iframes;
  }}

  // Extract YAML from the HA card editor modal (walks Shadow DOM)
  // Returns the raw YAML string or '' if no editor is open
  function extractCardYaml() {{
    try {{
      // Try to read from a ha-code-editor or ha-yaml-editor element
      function readEditorValue(el) {{
        if (!el) return '';
        // 1. Direct .value property (ha-code-editor exposes this reliably)
        if (typeof el.value === 'string' && el.value.trim()) return el.value.trim();
        // 2. ._value internal property (older HA versions)
        if (typeof el._value === 'string' && el._value.trim()) return el._value.trim();
        // 3. ha-yaml-editor wraps ha-code-editor in its shadowRoot — read from there
        if (el.shadowRoot) {{
          const codeEl = el.shadowRoot.querySelector('ha-code-editor');
          if (codeEl) {{
            if (typeof codeEl.value === 'string' && codeEl.value.trim()) return codeEl.value.trim();
            // CodeMirror 6: .cm-content inside ha-code-editor's shadowRoot
            const cmContent = codeEl.shadowRoot ? codeEl.shadowRoot.querySelector('.cm-content') : null;
            if (cmContent && cmContent.innerText && cmContent.innerText.trim()) {{
              return cmContent.innerText.trim();
            }}
          }}
        }}
        // 4. CodeMirror 6: editor state via .editor?.state?.doc?.toString()
        try {{
          const cm = el.editor || el._editor || el.codemirror;
          if (cm && cm.state && cm.state.doc) {{
            const v = cm.state.doc.toString();
            if (v.trim()) return v.trim();
          }}
        }} catch(e) {{}}
        // 5. CodeMirror 6: .cm-content div innerText (visible text in the editor)
        const cmContent = el.querySelector ? el.querySelector('.cm-content') : null;
        if (cmContent && cmContent.innerText && cmContent.innerText.trim()) {{
          return cmContent.innerText.trim();
        }}
        // 6. Fallback: textarea inside
        const ta = el.querySelector ? el.querySelector('textarea') : null;
        if (ta && ta.value && ta.value.trim()) return ta.value.trim();
        return '';
      }}

      function walkForYaml(root, depth) {{
        if (!root || depth > 15) return '';
        const editorSelectors = [
          'ha-yaml-editor', 'ha-code-editor',
          'hui-card-editor', 'hui-entity-editor', 'hui-dialog-edit-card',
        ];
        for (const sel of editorSelectors) {{
          const els = root.querySelectorAll ? root.querySelectorAll(sel) : [];
          for (const el of els) {{
            const v = readEditorValue(el);
            if (v) return v;
            if (el.shadowRoot) {{
              const inner = walkForYaml(el.shadowRoot, depth + 1);
              if (inner) return inner;
            }}
          }}
        }}
        // Recurse into all shadow roots
        const allEls = root.querySelectorAll ? root.querySelectorAll('*') : [];
        for (const el of allEls) {{
          if (el.shadowRoot) {{
            const found = walkForYaml(el.shadowRoot, depth + 1);
            if (found) return found;
          }}
        }}
        return '';
      }}
      return walkForYaml(document, 0);
    }} catch(e) {{ return ''; }}
  }}

  // Navigate the shadow DOM of the HA card editor and return useful elements.
  // Path: hui-dialog-edit-card → shadowRoot → ha-dialog[open] → shadowRoot → ...
  // All return null when the editor is closed or path cannot be resolved.

  function _findEditCardEl() {{
    try {{
      function walk(root, depth) {{
        if (!root || depth > 8) return null;
        const direct = root.querySelector ? root.querySelector('hui-dialog-edit-card') : null;
        if (direct) return direct;
        const allEls = root.querySelectorAll ? root.querySelectorAll('*') : [];
        for (const el of allEls) {{
          if (el.shadowRoot) {{ const f = walk(el.shadowRoot, depth + 1); if (f) return f; }}
        }}
        return null;
      }}
      return walk(document, 0);
    }} catch(e) {{ return null; }}
  }}

  // ---- Shadow DOM walkers for automation editor ----
  // Walk down the HA shadow DOM tree to find automation editor elements.
  // Path: home-assistant → ha-panel-config → ha-config-automation → ha-automation-editor → hass-subpage
  function _walkAutoShadow(selectors) {{
    try {{
      let node = document;
      for (const sel of selectors) {{
        if (!node) return null;
        const target = node.querySelector ? node.querySelector(sel) : null;
        if (!target) return null;
        node = target.shadowRoot || target;
      }}
      return node;
    }} catch(e) {{ return null; }}
  }}

  function _findAutomationSubpage() {{
    // Direct path — works on HA 2024+
    const direct = _walkAutoShadow([
      'home-assistant', 'home-assistant-main', 'ha-panel-config',
      'ha-config-automation', 'ha-automation-editor', 'hass-subpage'
    ]);
    if (direct) return direct;
    // Alt path — some HA versions nest differently
    const alt = _walkAutoShadow([
      'home-assistant', 'home-assistant-main', 'ha-panel-config',
      'ha-config-automation', 'ha-automation-editor'
    ]);
    if (alt) {{
      // hass-subpage might be in light DOM
      const sub = (alt.querySelector ? alt.querySelector('hass-subpage') : null)
               || (alt.shadowRoot ? alt.shadowRoot.querySelector('hass-subpage') : null);
      if (sub) return sub;
    }}
    // BFS fallback
    try {{
      function walk(root, depth) {{
        if (!root || depth > 10) return null;
        const el = root.querySelector ? root.querySelector('ha-automation-editor') : null;
        if (el) {{
          const sr = el.shadowRoot || el;
          return sr.querySelector ? (sr.querySelector('hass-subpage') || sr) : null;
        }}
        const allEls = root.querySelectorAll ? root.querySelectorAll('*') : [];
        for (const c of allEls) {{
          if (c.shadowRoot) {{ const f = walk(c.shadowRoot, depth + 1); if (f) return f; }}
        }}
        return null;
      }}
      return walk(document, 0);
    }} catch(e) {{ return null; }}
  }}

  function _findAutomationToolbar() {{
    const subpage = _findAutomationSubpage();
    if (!subpage) return null;
    // hass-subpage has a shadowRoot with the toolbar inside
    const sr = subpage.shadowRoot || subpage;
    return sr.querySelector('app-toolbar')
        || sr.querySelector('.toolbar')
        || sr.querySelector('ha-top-app-bar-fixed')
        || sr.querySelector('[slot="toolbar"]')
        || null;
  }}

  function _findAutomationContentWrapper() {{
    const subpage = _findAutomationSubpage();
    if (!subpage) return null;
    const sr = subpage.shadowRoot || subpage;
    // The content div wraps the automation editor form
    return sr.querySelector('.content')
        || sr.querySelector('div[class*="content"]')
        || sr.querySelector('#content')
        || null;
  }}

  // Returns the footer element (for button injection).
  // Supports both legacy (footer#actions in shadowRoot) and new HA (ha-dialog-footer in light DOM).
  function getCardEditorFooter() {{
    try {{
      const editCardEl = _findEditCardEl();
      if (!editCardEl || !editCardEl.shadowRoot) return null;
      const haDialog = editCardEl.shadowRoot.querySelector('ha-dialog[open]');
      if (!haDialog) return null;
      // New HA: <ha-dialog-footer slot="footer"> as light DOM child
      const newFooter = haDialog.querySelector('ha-dialog-footer[slot="footer"]');
      if (newFooter) return newFooter;
      // Legacy: footer#actions in shadowRoot
      if (haDialog.shadowRoot) return haDialog.shadowRoot.querySelector('footer#actions') || null;
      return null;
    }} catch(e) {{ return null; }}
  }}

  function isCardEditorOpen() {{
    return getCardEditorFooter() !== null;
  }}

  function detectContext() {{
    const path = window.location.pathname;
    const ctx = {{ type: null, id: null, label: null, entities: null }};

    // Card editor detection: a modal can be open on top of any page
    // Check DOM before URL-based detection so it takes priority
    if (isCardEditorOpen()) {{
      const yaml = extractCardYaml();
      ctx.type = 'card_editor';
      ctx.label = T.context_card_editor;
      if (yaml) ctx.cardYaml = yaml;
      return ctx;
    }}

    let m = path.match(/\\/config\\/automation\\/(?:edit|show|trace)\\/([^/]+)/);
    if (m) {{
      ctx.type = 'automation';
      ctx.id = m[1];
      ctx.label = (path.includes('/trace/') ? (T.context_automation + ' (trace): ') : (T.context_automation + ': ')) + m[1];
      return ctx;
    }}
    if (path.includes('/config/automation')) {{
      ctx.type = 'automation';
      ctx.label = T.context_automation;
      return ctx;
    }}

    m = path.match(/\\/config\\/script\\/edit\\/([^/]+)/);
    if (m) {{ ctx.type = 'script'; ctx.id = m[1]; ctx.label = T.context_script + ': ' + m[1]; return ctx; }}

    if (path.includes('/config/entities')) {{ ctx.type = 'entities'; ctx.label = T.context_entity + ' registry'; return ctx; }}

    m = path.match(/\\/config\\/devices\\/device\\/([^/]+)/);
    if (m) {{ ctx.type = 'device'; ctx.id = m[1]; ctx.label = 'Device: ' + m[1]; return ctx; }}

    // Detect HTML dashboard: find iframe pointing to /local/dashboards/ (walks Shadow DOM)
    const allIframes = findIframesDeep(document.body);
    const dashIframe = allIframes.find(f => (f.getAttribute('src') || '').includes('/local/dashboards/'));
    if (dashIframe) {{
      const src = dashIframe.getAttribute('src') || '';
      const nameMatch = src.match(/\\/local\\/dashboards\\/([^.?]+)/);
      if (nameMatch) {{
        ctx.type = 'html_dashboard'; ctx.id = nameMatch[1];
        ctx.label = T.context_dashboard + ' (HTML): ' + nameMatch[1];
        ctx.entities = extractDashboardEntities();
        return ctx;
      }}
    }}

    // Fallback: match URL path against cached HTML dashboard names
    if (_htmlDashboardNames && _htmlDashboardNames.length > 0) {{
      const pathSlug = path.split('/').filter(Boolean)[0] || '';
      const match = _htmlDashboardNames.find(n => n === pathSlug);
      if (match) {{
        ctx.type = 'html_dashboard'; ctx.id = match;
        ctx.label = T.context_dashboard + ' (HTML): ' + match;
        ctx.entities = extractDashboardEntities();
        return ctx;
      }}
    }}

    m = path.match(/\\/(lovelace[^/]*)\\/?(.*)/);
    if (m) {{
      ctx.type = 'dashboard'; ctx.id = m[1]; ctx.label = T.context_dashboard + ': ' + (m[1] || 'default');
      ctx.entities = extractDashboardEntities();
      return ctx;
    }}

    // Detect statistics page (developer-tools/statistics)
    if (path.includes('/developer-tools/statistics') || path.includes('/config/developer-tools/statistics')) {{
      ctx.type = 'statistics';
      ctx.label = T.context_statistics;
      return ctx;
    }}

    // Detect logs/system log page
    if (path.includes('/config/logs') || path.includes('/config/log')) {{
      ctx.type = 'logs';
      ctx.label = T.context_logs;
      // Try to extract the currently visible log entry from the HA dialog/details panel
      ctx.logEntry = extractVisibleLogEntry();
      return ctx;
    }}

    if (path.startsWith('/config')) {{ ctx.type = 'settings'; ctx.label = T.context_settings; return ctx; }}
    return ctx;
  }}

  // Walk shadow DOM to extract visible log entry text from HA log dialog
  function extractVisibleLogEntry() {{
    try {{
      // HA renders log details in a dialog or ha-logbook-renderer inside shadow roots
      // Walk all shadow roots looking for text that looks like a log entry
      function walkShadow(root, depth) {{
        if (depth > 10) return null;
        // Look for ha-dialog, dialog, or elements containing log text
        const selectors = [
          'ha-dialog', 'ha-alert', 'ha-logbook-renderer',
          '[slot="content"]', '.mdc-dialog__content',
          'ha-markdown', 'ha-expansion-panel'
        ];
        for (const sel of selectors) {{
          const els = root.querySelectorAll ? root.querySelectorAll(sel) : [];
          for (const el of els) {{
            const text = el.innerText || el.textContent || '';
            if (text.length > 20 && (
              text.includes('WARNING') || text.includes('ERROR') ||
              text.includes('deprecated') || text.includes('CRITICAL') ||
              text.includes('occurrences') || text.includes('Registratore') ||
              text.includes('Logger') || text.includes('Source') || text.includes('Fonte')
            )) {{
              return text.trim().substring(0, 2000);
            }}
            if (el.shadowRoot) {{
              const found = walkShadow(el.shadowRoot, depth + 1);
              if (found) return found;
            }}
          }}
        }}
        // Recurse into all shadow roots
        const allEls = root.querySelectorAll ? root.querySelectorAll('*') : [];
        for (const el of allEls) {{
          if (el.shadowRoot) {{
            const found = walkShadow(el.shadowRoot, depth + 1);
            if (found) return found;
          }}
        }}
        return null;
      }}
      return walkShadow(document, 0);
    }} catch(e) {{ return null; }}
  }}

  function extractDashboardEntities() {{
    try {{
      const entities = new Set();
      const re = /(?:sensor|switch|light|climate|binary_sensor|input_boolean|automation|number|select|button|cover|fan|lock|media_player|vacuum|weather|water_heater|scene|script|input_number|input_select|input_text|person|device_tracker|calendar|camera|update|group|sun)\\.[a-z0-9_]+/g;
      // Check iframes (HTML dashboards)
      for (const iframe of document.querySelectorAll('iframe[src*="/local/"], iframe[src*="hacsfiles"]')) {{
        try {{
          const doc = iframe.contentDocument || iframe.contentWindow.document;
          if (!doc) continue;
          let match;
          while ((match = re.exec(doc.documentElement.innerHTML || '')) !== null) entities.add(match[0]);
        }} catch(e) {{}}
      }}
      // Also check main page
      let m2;
      const mainHtml = document.body.innerHTML || '';
      while ((m2 = re.exec(mainHtml)) !== null) entities.add(m2[0]);
      return entities.size > 0 ? Array.from(entities) : null;
    }} catch(e) {{ return null; }}
  }}

  function buildContextPrefix() {{
    const ctx = detectContext();
    if (!ctx.type) return '';
    if (ctx.type === 'card_editor') {{
      let p = '[CONTEXT: User is editing a Lovelace card in the HA card editor.';
      if (ctx.cardYaml) {{
        // Pre-validate entities against hass.states
        // hass.states is the AUTHORITATIVE source for the frontend — if an entity
        // is NOT in hass.states, HA cards CANNOT use it (disabled/unavailable/wrong id).
        let entityReport = '';
        let hasNotFound = false;
        try {{
          const haEl = document.querySelector('home-assistant');
          const hass = haEl && haEl.hass;
          if (hass && hass.states) {{
            const entityRe = /entity:\\s+([\\w]+\\.[\\w]+)/g;
            let em;
            const checks = [];
            while ((em = entityRe.exec(ctx.cardYaml)) !== null) {{
              const eid = em[1];
              const st = hass.states[eid];
              if (st) {{
                checks.push(eid + ': VALID (state=' + st.state + ')');
              }} else {{
                checks.push(eid + ': NOT FOUND in hass.states — card will show error. Could be wrong id, disabled, or hidden. Verify ONCE via get_integration_entities.');
                hasNotFound = true;
              }}
            }}
            if (checks.length > 0) {{
              entityReport = '\\nENTITY VALIDATION (hass.states — authoritative for cards):\\n' + checks.join('\\n') + '\\n';
            }}
          }}
        }} catch(e) {{}}

        p += ' The current card YAML is:\\n```yaml\\n' + ctx.cardYaml + '\\n```\\n'
           + entityReport
           + 'IMPORTANT RULES for card editing:\\n'
           + '1. Entities marked VALID exist and work in cards — no need to re-verify.\\n'
           + '2. For NOT FOUND entities: call get_integration_entities ONCE to check the integration. Call it only ONCE — do NOT repeat.\\n'
           + '3. If get_integration_entities confirms the entity EXISTS with a valid state but hass.states does not have it: report that the entity exists in HA but is not available to cards (may be disabled or hidden). Suggest the user try enabling it in Settings > Entities or restart HA. Do NOT keep searching.\\n'
           + '4. If get_integration_entities does NOT find the entity: look for a similar entity_id with matching device_class/unit and suggest the replacement.\\n'
           + '5. When suggesting a modification, ALWAYS show the complete corrected YAML in a ```yaml code block with a brief explanation.\\n'
           + '6. Do NOT suggest changes based on guesses about entity names. Only replace an entity if you found a valid alternative.\\n'
           + '7. If all entities are VALID and the YAML has no structural issues, say so clearly and suggest only optional improvements.\\n'
           + '8. The user will paste the YAML manually in the editor — do NOT use write_config_file or update_dashboard.\\n'
           + '9. NEVER show [TOOL RESULT] blocks or raw JSON data to the user — only show the final human-readable answer.\\n'
           + '10. After receiving tool results, produce your FINAL answer immediately. Do NOT call the same tool again.';
      }}
      p += ']';
      return p + ' ';
    }}
    if (ctx.type === 'automation' && ctx.id)
      return '[CONTEXT: User is viewing automation id="' + ctx.id + '". '
           + 'The automation_id for modify operations is: ' + ctx.id + '. '
           + 'Use get_automations or the DATA section to read it. Refer to it directly.] ';
    if (ctx.type === 'automation')
      return '[CONTEXT: User is viewing an automation page in Home Assistant. '
           + 'Automation id may be unavailable in this view (read-only or no-id automation). '
           + 'Analyze and explain based on visible automation logic.] ';
    if (ctx.type === 'script' && ctx.id)
      return '[CONTEXT: User is viewing script id="' + ctx.id + '". '
           + 'The script_id for modify operations is: ' + ctx.id + '. '
           + 'Use get_scripts or the DATA section to read it. Refer to it directly.] ';
    if (ctx.type === 'device' && ctx.id)
      return '[CONTEXT: User is viewing device "' + ctx.id + '". Use search_entities to find its entities.] ';
    if (ctx.type === 'html_dashboard' && ctx.id) {{
      let p = '[CONTEXT: User is viewing HTML dashboard "' + ctx.id + '".';
      if (ctx.entities && ctx.entities.length > 0) {{
        p += ' Entities: ' + ctx.entities.join(', ') + '.';
      }}
      p += ' The current HTML will be provided. Call create_html_dashboard(name="' + ctx.id + '", html="<complete modified html>") immediately. NEVER output HTML as text in the chat.]';
      return p + ' ';
    }}
    if (ctx.type === 'dashboard' && ctx.id) {{
      let p = '[CONTEXT: User is viewing dashboard "' + ctx.id + '".';
      if (ctx.entities && ctx.entities.length > 0) {{
        p += ' This dashboard currently shows: ' + ctx.entities.join(', ') + '.';
        p += ' If adding, use the same style/layout. Use get_dashboard_config to read current config.';
      }}
      return p + '] ';
    }}
    if (ctx.type === 'statistics') {{
      return '[CONTEXT: User is on the Home Assistant Statistics page (Developer Tools > Statistics). '
           + 'This page shows recorder statistics and their issues (orphaned entities, unit mismatches). '
           + 'Use manage_statistics with action=validate to find all issues. '
           + 'Then offer to fix them: clear_orphaned to remove statistics for deleted entities, '
           + 'fix_units to correct unit mismatches. Always validate FIRST, then act on user request.] ';
    }}
    if (ctx.type === 'logs') {{
      let p = '[CONTEXT: User is on the Home Assistant system logs page. '
            + 'Use get_ha_logs to fetch recent errors and warnings. ';
      // Use live entry if available; fall back to cached entry captured before
      // the dialog was dismissed by the bubble button click.
      const logEntry = ctx.logEntry || _cachedLogEntry;
      if (logEntry) {{
        p += 'The user has the following log entry open/visible:\\n---\\n' + logEntry + '\\n---\\n'
           + 'Analyze this specific entry and help fix it if possible.';
      }}
      p += ']';
      return p + ' ';
    }}
    return '';
  }}

  // ---- Quick Actions based on context ----
  function getQuickActions() {{
    const ctx = detectContext();
    if (!ctx.type) return [];
    if (ctx.type === 'card_editor') {{
      // In GUI mode the YAML is not readable — hide quick actions (they need the YAML)
      if (!ctx.cardYaml) return [];
      return [
        {{ label: T.qa_card_explain, text: T.qa_card_explain_text }},
        {{ label: T.qa_card_optimize, text: T.qa_card_optimize_text }},
        {{ label: T.qa_card_add_feature, text: T.qa_card_add_feature_text }},
        {{ label: T.qa_card_fix, text: T.qa_card_fix_text }},
      ];
    }}
    if (ctx.type === 'automation') return [
      {{ label: T.qa_analyze, text: 'Analyze this automation and tell me what it does' }},
      {{ label: T.qa_optimize, text: 'Optimize this automation - suggest improvements' }},
      {{ label: T.qa_add_condition, text: 'Add a time condition to this automation' }},
      {{ label: T.qa_fix, text: 'Check this automation for errors or issues' }},
    ];
    if (ctx.type === 'script') return [
      {{ label: T.qa_analyze, text: 'Analyze this script and tell me what it does' }},
      {{ label: T.qa_optimize, text: 'Optimize this script - suggest improvements' }},
      {{ label: T.qa_explain, text: 'Explain this script step by step' }},
    ];
    if (ctx.type === 'dashboard') return [
      {{ label: T.qa_describe, text: 'Describe what this dashboard shows' }},
      {{ label: T.qa_add_entities, text: 'Add more entities to this dashboard with the same style' }},
      {{ label: T.qa_optimize, text: 'Suggest improvements for this dashboard' }},
    ];
    if (ctx.type === 'device') return [
      {{ label: T.qa_analyze, text: 'Show me all entities for this device and their current states' }},
    ];
    if (ctx.type === 'statistics') return [
      {{ label: T.qa_stats_validate, text: T.qa_stats_validate_text }},
      {{ label: T.qa_stats_clean, text: T.qa_stats_clean_text }},
      {{ label: T.qa_stats_fix_units, text: T.qa_stats_fix_units_text }},
    ];
    if (ctx.type === 'logs') {{
      // Use live logEntry from ctx, or fall back to cached entry (persists after
      // dialog is dismissed when user clicked the bubble button)
      const hasEntry = !!(ctx.logEntry || _cachedLogEntry);
      const actions = [];
      if (hasEntry) {{
        actions.push({{ label: T.qa_explain_log, text: T.qa_explain_log_text }});
        actions.push({{ label: T.qa_fix_log, text: T.qa_fix_log_text }});
      }}
      actions.push({{ label: T.qa_show_errors, text: T.qa_show_errors_text }});
      actions.push({{ label: T.qa_fix, text: T.qa_fix_logs_text }});
      return actions;
    }}
    return [];
  }}

  // ---- Session Management (bubble-specific, separate from main UI) ----
  // Use localStorage (not sessionStorage) so the session survives tab close/reopen
  const SESSION_KEY = 'ha-claude-bubble-session';
  function getSessionId() {{
    let sid = null;
    try {{ sid = localStorage.getItem(SESSION_KEY); }} catch(e) {{}}
    if (!sid) {{
      // Migrate from sessionStorage if present (old behavior)
      try {{ sid = sessionStorage.getItem(SESSION_KEY); }} catch(e) {{}}
    }}
    if (!sid) {{ sid = 'bubble_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7); }}
    try {{ localStorage.setItem(SESSION_KEY, sid); }} catch(e) {{}}
    try {{ sessionStorage.setItem(SESSION_KEY, sid); }} catch(e) {{}}
    return sid;
  }}
  function setSessionId(sid) {{
    try {{ localStorage.setItem(SESSION_KEY, sid); }} catch(e) {{}}
    try {{ sessionStorage.setItem(SESSION_KEY, sid); }} catch(e) {{}}
  }}
  function resetSession() {{
    // Remove current session so getSessionId() generates a fresh one on next call
    try {{ localStorage.removeItem(SESSION_KEY); }} catch(e) {{}}
    try {{ sessionStorage.removeItem(SESSION_KEY); }} catch(e) {{}}
  }}

  // Card editor uses a separate session so conversations don't mix with bubble
  const CARD_SESSION_KEY = 'ha-claude-card-session';
  function getCardSessionId() {{
    let sid = null;
    try {{ sid = localStorage.getItem(CARD_SESSION_KEY); }} catch(e) {{}}
    if (!sid) {{ sid = 'card_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7); }}
    try {{ localStorage.setItem(CARD_SESSION_KEY, sid); }} catch(e) {{}}
    return sid;
  }}
  function resetCardSession() {{
    try {{ localStorage.removeItem(CARD_SESSION_KEY); }} catch(e) {{}}
  }}
  
  // ---- Fallback in-memory storage (for private browsing or disabled localStorage) ----
  let memoryHistoryFallback = [];
  let localStorageAvailable = true;
  try {{ localStorage.setItem('__test', '1'); localStorage.removeItem('__test'); }}
  catch(e) {{ 
    console.warn('[Bubble] localStorage not available (private mode?), using in-memory fallback');
    localStorageAvailable = false;
  }}

  // ---- Message History Persistence ----
  const HISTORY_KEY = STORE_PREFIX + 'history';
  const MAX_HISTORY = 50;
  function loadHistory() {{
    try {{ 
      if (!localStorageAvailable) {{
        console.log('[Bubble] Using in-memory fallback, stored:', memoryHistoryFallback.length, 'messages');
        return memoryHistoryFallback;
      }}
      const raw = localStorage.getItem(HISTORY_KEY);
      console.log('[Bubble] localStorage.getItem returned:', raw ? raw.substring(0, 50) + '...' : 'null');
      return JSON.parse(raw || '[]'); 
    }}
    catch(e) {{ 
      console.warn('[Bubble] loadHistory error:', e);
      return memoryHistoryFallback || []; 
    }}
  }}
  function saveHistory(messages) {{
    try {{ 
      if (!localStorageAvailable) {{
        memoryHistoryFallback = messages.slice(-MAX_HISTORY);
        console.log('[Bubble] saved to in-memory:', memoryHistoryFallback.length, 'messages');
        return;
      }}
      const json = JSON.stringify(messages.slice(-MAX_HISTORY));
      localStorage.setItem(HISTORY_KEY, json);
      console.log('[Bubble] saved to localStorage:', messages.length, 'messages');
    }}
    catch(e) {{
      // Fallback to in-memory if localStorage quota exceeded
      memoryHistoryFallback = messages.slice(-MAX_HISTORY);
      console.warn('[Bubble] localStorage error, using in-memory fallback:', e);
    }}
  }}
  function addToHistory(role, text) {{
    const h = loadHistory();
    h.push({{ role, text, ts: Date.now() }});
    saveHistory(h);
    broadcastEvent('new-message', {{ role, text }});
  }}
  function clearHistory() {{
    try {{ localStorage.removeItem(HISTORY_KEY); }} catch(e) {{}}
  }}

  // ---- Saved position/size ----
  const savedPos = loadSetting('btn-pos', null);
  const savedSize = loadSetting('panel-size', null);

  // ---- Styles ----
  const style = document.createElement('style');
  style.textContent = `
    #ha-claude-bubble {{
      position: fixed;
      z-index: 99999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    #ha-claude-bubble .bubble-btn {{
      position: fixed;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: var(--primary-color, #03a9f4);
      color: white;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      transition: box-shadow 0.2s;
      touch-action: none;
      user-select: none;
      -webkit-user-select: none;
    }}
    #ha-claude-bubble .bubble-btn:hover {{ box-shadow: 0 6px 24px rgba(0,0,0,0.4); }}
    #ha-claude-bubble .bubble-btn.dragging {{ opacity: 0.8; transform: scale(1.15); transition: none; }}
    #ha-claude-bubble .bubble-btn.has-context {{ animation: bubble-pulse 2s infinite; }}
    #ha-claude-bubble .bubble-btn.dragging.has-context {{ animation: none; }}
    @keyframes bubble-pulse {{
      0%, 100% {{ box-shadow: 0 4px 16px rgba(0,0,0,0.3); }}
      50% {{ box-shadow: 0 4px 16px rgba(3,169,244,0.6); }}
    }}
    #ha-claude-bubble .chat-panel {{
      display: none; position: fixed; bottom: 90px; right: 24px;
      width: 380px; min-width: 300px; min-height: 300px;
      max-width: calc(100vw - 48px); height: 520px; max-height: calc(100vh - 120px);
      background: var(--card-background-color, #fff); border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.3); flex-direction: column;
      overflow: hidden; border: 1px solid var(--divider-color, #e0e0e0); resize: both;
    }}
    #ha-claude-bubble .chat-panel.open {{ display: flex; }}
    #ha-claude-bubble .chat-header {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 16px; background: var(--primary-color, #03a9f4);
      color: white; font-weight: 600; font-size: 14px; cursor: move;
      flex-shrink: 0;
    }}
    #ha-claude-bubble .chat-header-actions {{ display: flex; gap: 8px; }}
    #ha-claude-bubble .chat-header button {{
      background: none; border: none; color: white; cursor: pointer;
      font-size: 16px; padding: 4px; opacity: 0.8; border-radius: 4px;
    }}
    #ha-claude-bubble .chat-header button:hover {{ opacity: 1; background: rgba(255,255,255,0.15); }}
    #ha-claude-bubble .context-bar {{
      padding: 6px 16px; background: var(--secondary-background-color, #f5f5f5);
      font-size: 11px; color: var(--secondary-text-color, #666);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0;
    }}
    #ha-claude-bubble .context-bar--warn {{
      background: #fff3cd; color: #856404;
      border-bottom-color: #ffc107;
    }}
    #ha-claude-bubble .quick-actions {{
      display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 16px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0); flex-shrink: 0;
    }}
    #ha-claude-bubble .quick-action-btn {{
      background: var(--secondary-background-color, #f0f0f0);
      color: var(--primary-text-color, #333); border: 1px solid var(--divider-color, #ddd);
      border-radius: 16px; padding: 4px 12px; font-size: 11px; cursor: pointer;
      white-space: nowrap; transition: background 0.15s;
    }}
    #ha-claude-bubble .quick-action-btn:hover {{
      background: var(--primary-color, #03a9f4); color: white; border-color: transparent;
    }}
    #ha-claude-bubble .chat-messages {{
      flex: 1; overflow-y: auto; padding: 12px 16px;
      display: flex; flex-direction: column; gap: 8px;
    }}
    #ha-claude-bubble .msg {{
      max-width: 85%; padding: 8px 12px; border-radius: 12px;
      font-size: 13px; line-height: 1.45; word-wrap: break-word;
    }}
    #ha-claude-bubble .msg.user {{
      align-self: flex-end; background: var(--primary-color, #03a9f4);
      color: white; border-bottom-right-radius: 4px; white-space: pre-wrap;
    }}
    #ha-claude-bubble .msg.assistant {{
      align-self: flex-start; background: var(--secondary-background-color, #f0f0f0);
      color: var(--primary-text-color, #333); border-bottom-left-radius: 4px;
    }}
    #ha-claude-bubble .msg.assistant pre.md-code-block {{
      background: var(--primary-text-color, #333); color: var(--card-background-color, #fff);
      padding: 8px; border-radius: 6px; overflow-x: auto; font-size: 12px;
      margin: 4px 0; white-space: pre-wrap; word-break: break-all;
    }}
    #ha-claude-bubble .msg.assistant code.md-inline-code {{
      background: rgba(0,0,0,0.08); padding: 1px 4px; border-radius: 3px; font-size: 12px;
    }}
    #ha-claude-bubble .msg.assistant .md-li {{ padding: 1px 0; }}
    #ha-claude-bubble .msg.assistant a {{ color: var(--primary-color, #03a9f4); text-decoration: underline; }}
    /* Collapsible details blocks for entity lists */
    #ha-claude-bubble .msg.assistant details {{ margin: 6px 0; border: 1px solid var(--divider-color, #e0e0e0); border-radius: 6px; overflow: hidden; }}
    #ha-claude-bubble .msg.assistant details summary {{ cursor: pointer; padding: 6px 10px; font-weight: 600; font-size: 13px; background: var(--secondary-background-color, #f5f5f5); user-select: none; }}
    #ha-claude-bubble .msg.assistant details summary:hover {{ background: var(--primary-color, #03a9f4); color: #fff; }}
    #ha-claude-bubble .msg.assistant details > div {{ max-height: 180px; overflow-y: auto; padding: 6px 10px; font-size: 12px; line-height: 1.5; }}
    #ha-claude-bubble .msg.assistant details code {{ background: rgba(0,0,0,0.06); padding: 1px 3px; border-radius: 3px; font-size: 11px; }}
    /* Diff styles for colored code changes */
    #ha-claude-bubble .diff-side {{ overflow-x: auto; margin: 8px 0; border-radius: 6px; border: 1px solid var(--divider-color, #e1e4e8); }}
    #ha-claude-bubble .diff-table {{ width: 100%; border-collapse: collapse; font-family: monospace; font-size: 11px; table-layout: fixed; }}
    #ha-claude-bubble .diff-table th {{ padding: 4px 8px; background: var(--secondary-background-color, #f6f8fa); border-bottom: 1px solid var(--divider-color, #e1e4e8); text-align: left; font-size: 10px; font-weight: 600; width: 50%; }}
    #ha-claude-bubble .diff-th-old {{ color: #cb2431; }}
    #ha-claude-bubble .diff-th-new {{ color: #22863a; border-left: 1px solid var(--divider-color, #e1e4e8); }}
    #ha-claude-bubble .diff-table td {{ padding: 1px 6px; white-space: pre-wrap; word-break: break-all; vertical-align: top; font-size: 10px; line-height: 1.4; }}
    #ha-claude-bubble .diff-eq {{ color: var(--secondary-text-color, #586069); }}
    #ha-claude-bubble .diff-del {{ background: #ffeef0; color: #cb2431; }}
    #ha-claude-bubble .diff-add {{ background: #e6ffec; color: #22863a; }}
    #ha-claude-bubble .diff-empty {{ background: var(--secondary-background-color, #fafbfc); }}
    #ha-claude-bubble .diff-table td + td {{ border-left: 1px solid var(--divider-color, #e1e4e8); }}
    /* Confirmation buttons */
    #ha-claude-bubble .confirm-buttons {{ display: flex; gap: 10px; margin-top: 12px; justify-content: center; }}
    #ha-claude-bubble .confirm-btn {{ padding: 8px 20px; border-radius: 20px; border: 2px solid; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
    #ha-claude-bubble .confirm-yes {{ background: #e8f5e9; border-color: #4caf50; color: #2e7d32; }}
    #ha-claude-bubble .confirm-yes:hover {{ background: #4caf50; color: white; }}
    #ha-claude-bubble .confirm-no {{ background: #ffebee; border-color: #f44336; color: #c62828; }}
    #ha-claude-bubble .confirm-no:hover {{ background: #f44336; color: white; }}
    #ha-claude-bubble .confirm-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    #ha-claude-bubble .confirm-btn.selected {{ opacity: 1; transform: scale(1.05); }}
    #ha-claude-bubble .confirm-buttons.answered .confirm-btn:not(.selected) {{ opacity: 0.3; }}
    #ha-claude-bubble .msg.thinking {{
      align-self: flex-start; background: var(--secondary-background-color, #f0f0f0);
      color: var(--secondary-text-color, #999); font-style: italic; white-space: pre-wrap;
    }}
    #ha-claude-bubble .thinking-elapsed {{
      font-size: 10px; opacity: 0.7; margin-left: 4px;
    }}
    #ha-claude-bubble .thinking-model {{
      font-size: 10px; opacity: 0.6; font-style: normal; margin-left: 2px;
    }}
    #ha-claude-bubble .thinking-dots span {{
      animation: bubble-blink 1.4s infinite both;
    }}
    #ha-claude-bubble .thinking-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
    #ha-claude-bubble .thinking-dots span:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes bubble-blink {{
      0%, 80%, 100% {{ opacity: 0; }}
      40% {{ opacity: 1; }}
    }}
    #ha-claude-bubble .thinking-steps {{
      margin-top: 4px; font-style: normal; font-size: 11px;
      color: var(--secondary-text-color, #888); line-height: 1.4;
    }}
    #ha-claude-bubble .progress-steps {{
      margin-bottom: 6px; font-size: 10px; color: var(--secondary-text-color, #999);
      line-height: 1.3; border-bottom: 1px solid var(--divider-color, #e0e0e0);
      padding-bottom: 4px;
    }}
    #ha-claude-bubble .progress-steps div {{
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    #ha-claude-bubble .msg-usage {{
      font-size: 10px; color: var(--secondary-text-color, #999); text-align: right;
      margin-top: 3px; padding-top: 3px; border-top: 1px solid var(--divider-color, rgba(150,150,150,0.15));
    }}
    #ha-claude-bubble .msg.error {{
      align-self: center; background: var(--error-color, #db4437);
      color: white; font-size: 12px;
    }}
    #ha-claude-bubble .msg.reload-notice {{
      align-self: center; background: var(--success-color, #4caf50);
      color: white; font-size: 12px; padding: 6px 12px;
    }}
    #ha-claude-bubble .msg.system {{
      align-self: center; background: var(--secondary-background-color, #f0f4ff);
      color: var(--secondary-text-color, #555); font-size: 11px;
      padding: 4px 10px; border-radius: 8px; max-width: 90%; text-align: center;
      opacity: 0.85;
    }}
    #ha-claude-bubble .chat-input-area {{
      display: flex; padding: 10px 12px;
      border-top: 1px solid var(--divider-color, #e0e0e0);
      gap: 6px; align-items: flex-end; flex-shrink: 0;
    }}
    #ha-claude-bubble .chat-input-area textarea {{
      flex: 1; border: 1px solid var(--divider-color, #ddd); border-radius: 8px;
      padding: 8px 12px; font-size: 13px; font-family: inherit; resize: none;
      max-height: 80px; outline: none;
      background: var(--card-background-color, #fff); color: var(--primary-text-color, #333);
    }}
    #ha-claude-bubble .chat-input-area textarea:focus {{ border-color: var(--primary-color, #03a9f4); }}
    #ha-claude-bubble .input-btn {{
      width: 36px; height: 36px; border-radius: 50%;
      border: none; cursor: pointer; font-size: 16px;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }}
    #ha-claude-bubble .send-btn {{
      background: var(--primary-color, #03a9f4); color: white;
    }}
    #ha-claude-bubble .send-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    #ha-claude-bubble .voice-btn {{
      background: var(--secondary-background-color, #f0f0f0);
      color: var(--primary-text-color, #666);
    }}
    #ha-claude-bubble .voice-btn.recording {{
      background: var(--error-color, #db4437); color: white;
      animation: voice-pulse 1s infinite;
    }}
    #ha-claude-bubble .voice-btn.processing {{
      background: var(--warning-color, #ff9800); color: white;
      animation: voice-pulse 0.6s infinite;
    }}
    @keyframes voice-pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.6; }}
    }}
    #ha-claude-bubble .voice-bar {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 4px 12px; border-top: 1px solid var(--divider-color, #e0e0e0);
      background: var(--secondary-background-color, #f5f5f5); font-size: 11px;
      color: var(--secondary-text-color, #888); flex-shrink: 0;
    }}
    #ha-claude-bubble .voice-toggle-label {{
      display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none;
    }}
    #ha-claude-bubble .voice-toggle-label input {{ display: none; }}
    #ha-claude-bubble .voice-toggle-track {{
      width: 30px; height: 16px; background: var(--disabled-text-color, #ccc);
      border-radius: 8px; position: relative; transition: background 0.2s;
    }}
    #ha-claude-bubble .voice-toggle-label input:checked + .voice-toggle-track {{
      background: #8b5cf6;
    }}
    #ha-claude-bubble .voice-toggle-thumb {{
      width: 12px; height: 12px; background: white; border-radius: 50%;
      position: absolute; top: 2px; left: 2px; transition: left 0.2s;
      box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }}
    #ha-claude-bubble .voice-toggle-label input:checked + .voice-toggle-track .voice-toggle-thumb {{
      left: 16px;
    }}
    #ha-claude-bubble .voice-speaking {{
      display: flex; align-items: center; gap: 4px; color: #8b5cf6; cursor: pointer;
    }}
    #ha-claude-bubble .wave-mini {{
      display: flex; gap: 1px; align-items: center;
    }}
    #ha-claude-bubble .wave-mini span {{
      display: inline-block; width: 2px; background: #8b5cf6; border-radius: 1px;
      animation: bubble-wave 0.6s ease-in-out infinite;
    }}
    #ha-claude-bubble .wave-mini span:nth-child(1) {{ height: 6px; animation-delay: 0s; }}
    #ha-claude-bubble .wave-mini span:nth-child(2) {{ height: 10px; animation-delay: 0.15s; }}
    #ha-claude-bubble .wave-mini span:nth-child(3) {{ height: 6px; animation-delay: 0.3s; }}
    @keyframes bubble-wave {{
      0%, 100% {{ transform: scaleY(1); }} 50% {{ transform: scaleY(0.4); }}
    }}
    #ha-claude-bubble .abort-btn {{
      background: var(--error-color, #db4437); color: white;
    }}
    /* ---- Conversation History Panel ---- */
    #ha-claude-bubble .history-panel {{
      display: none; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      background: var(--card-background-color, #fff); z-index: 10;
      flex-direction: column; overflow: hidden;
    }}
    #ha-claude-bubble .history-panel.open {{ display: flex; }}
    #ha-claude-bubble .history-header {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 16px; background: var(--primary-color, #03a9f4);
      color: white; font-weight: 600; font-size: 14px; flex-shrink: 0;
    }}
    #ha-claude-bubble .history-header button {{
      background: none; border: none; color: white; cursor: pointer;
      font-size: 16px; padding: 4px; opacity: 0.8; border-radius: 4px;
    }}
    #ha-claude-bubble .history-header button:hover {{ opacity: 1; background: rgba(255,255,255,0.15); }}
    #ha-claude-bubble .history-list {{
      flex: 1; overflow-y: auto; padding: 8px;
    }}
    #ha-claude-bubble .history-item {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 10px 12px; margin-bottom: 4px; border-radius: 8px; cursor: pointer;
      background: var(--secondary-background-color, #f5f5f5);
      border: 1px solid transparent; transition: all 0.15s;
    }}
    #ha-claude-bubble .history-item:hover {{
      border-color: var(--primary-color, #03a9f4);
      background: var(--primary-color, #03a9f4); color: white;
    }}
    #ha-claude-bubble .history-item:hover .history-meta {{ color: rgba(255,255,255,0.8); }}
    #ha-claude-bubble .history-item.active {{
      border-color: var(--primary-color, #03a9f4);
      background: color-mix(in srgb, var(--primary-color, #03a9f4) 15%, transparent);
    }}
    #ha-claude-bubble .history-item-info {{ flex: 1; min-width: 0; }}
    #ha-claude-bubble .history-title {{
      font-size: 12px; font-weight: 500; white-space: nowrap;
      overflow: hidden; text-overflow: ellipsis;
    }}
    #ha-claude-bubble .history-meta {{
      font-size: 10px; color: var(--secondary-text-color, #999); margin-top: 2px;
      display: flex; gap: 8px;
    }}
    #ha-claude-bubble .history-source {{
      font-size: 9px; padding: 1px 6px; border-radius: 8px;
      background: var(--primary-color, #03a9f4); color: white; opacity: 0.7;
      flex-shrink: 0;
    }}
    #ha-claude-bubble .history-empty {{
      text-align: center; padding: 24px 16px;
      color: var(--secondary-text-color, #999); font-size: 13px;
    }}
    #ha-claude-bubble .history-error {{
      text-align: center; padding: 16px;
      color: var(--error-color, #db4437); font-size: 12px;
    }}
    #ha-claude-bubble .agent-bar {{
      display: flex; align-items: center; gap: 6px;
      padding: 6px 12px; border-bottom: 1px solid var(--divider-color, #e0e0e0);
      background: var(--secondary-background-color, #f5f5f5); flex-shrink: 0;
      flex-wrap: nowrap; overflow: hidden;
    }}
    #ha-claude-bubble .agent-bar label {{
      font-size: 11px; color: var(--secondary-text-color, #666); white-space: nowrap;
      flex-shrink: 0;
    }}
    #ha-claude-bubble .agent-bar select {{
      flex: 1; min-width: 80px; font-size: 12px; padding: 3px 6px; border-radius: 6px;
      border: 1px solid var(--divider-color, #ddd);
      background: var(--card-background-color, #fff); color: var(--primary-text-color, #333);
      outline: none; cursor: pointer;
    }}
    #ha-claude-bubble .agent-bar select:focus {{ border-color: var(--primary-color, #03a9f4); }}
    #ha-claude-bubble .session-conn-bar {{
      display: none; align-items: center; gap: 8px; padding: 5px 12px;
      background: #d4edda; border-bottom: 1px solid #b8dac2;
      font-size: 11px; color: #155724; flex-shrink: 0;
    }}
    #ha-claude-bubble .session-conn-bar .sc-dot {{
      width: 7px; height: 7px; border-radius: 50%; background: #28a745; flex-shrink: 0;
    }}
    #ha-claude-bubble .session-conn-bar .sc-label {{
      font-weight: 600; white-space: nowrap;
    }}
    #ha-claude-bubble .session-conn-bar .sc-detail {{
      flex: 1; opacity: 0.75; font-size: 10px; white-space: nowrap;
      overflow: hidden; text-overflow: ellipsis;
    }}
    #ha-claude-bubble .session-conn-bar .sc-disc {{
      background: transparent; color: #155724; border: 1px solid #28a745;
      border-radius: 6px; padding: 2px 8px; cursor: pointer;
      font-size: 10px; font-weight: 600; white-space: nowrap; flex-shrink: 0;
    }}
    #ha-claude-bubble .session-conn-bar .sc-disc:hover {{ background: #c3e6cb; }}
    #ha-claude-bubble .tool-badges {{
      display: flex; flex-wrap: wrap; gap: 4px; padding: 4px 0;
    }}
    #ha-claude-bubble .tool-badge {{
      display: inline-block; background: var(--primary-color, #03a9f4);
      color: white; font-size: 10px; padding: 2px 8px; border-radius: 10px; opacity: 0.8;
    }}
    @media (max-width: 768px) {{
      #ha-claude-bubble .agent-bar {{
        gap: 4px; padding: 4px 8px;
      }}
      #ha-claude-bubble .agent-bar label {{
        display: none;
      }}
      #ha-claude-bubble .agent-bar select {{
        min-width: 70px; font-size: 11px; padding: 2px 4px;
      }}
    }}
    @media (max-width: 480px) {{
      #ha-claude-bubble .chat-panel {{
        width: calc(100vw - 16px) !important; height: calc(100vh - 100px) !important;
        right: 8px !important; bottom: 80px !important; border-radius: 12px;
      }}
      #ha-claude-bubble .bubble-btn {{ width: 48px; height: 48px; font-size: 20px; }}
      #ha-claude-bubble .agent-bar {{
        gap: 3px; padding: 3px 6px;
      }}
      #ha-claude-bubble .agent-bar select {{
        min-width: 60px; font-size: 10px; padding: 2px 3px;
      }}
    }}
  `;
  document.head.appendChild(style);

  // ---- Build DOM ----
  const root = document.createElement('div');
  root.id = 'ha-claude-bubble';
  root.innerHTML = `
    <div class="chat-panel" id="haChatPanel">
      <div class="chat-header" id="haChatHeader">
        <span>Amira</span>
        <div class="chat-header-actions">
          <button id="haChatHistory" title="${{T.history || 'History'}}">&#128240;</button>
          <button id="haChatNew" title="${{T.new_chat}}">&#10227;</button>
          <button id="haChatClose" title="${{T.close}}">&times;</button>
        </div>
      </div>
      <div class="history-panel" id="haHistoryPanel">
        <div class="history-header">
          <span>${{T.history || 'History'}}</span>
          <button id="haHistoryClose" title="${{T.back_to_chat || 'Back'}}">&times;</button>
        </div>
        <div class="history-list" id="haHistoryList"></div>
      </div>
      <div class="agent-bar" id="haAgentBar">
        <select id="haAgentSelect" style="display:none"></select>
        <select id="haProviderSelect"></select>
        <select id="haModelSelect"></select>
      </div>
      <div class="session-conn-bar" id="haSessionConnBar">
        <div class="sc-dot"></div>
        <span class="sc-label" id="haSessionConnLabel"></span>
        <span class="sc-detail" id="haSessionConnDetail"></span>
        <button class="sc-disc" id="haSessionConnDisc">Disconnect</button>
      </div>
      <div class="context-bar" id="haChatContext" style="display:none;"></div>
      <div class="quick-actions" id="haQuickActions" style="display:none;"></div>
      <div class="chat-messages" id="haChatMessages"></div>
      <div class="chat-input-area">
        <textarea id="haChatInput" rows="1" placeholder="${{T.placeholder}}"></textarea>
        <button class="input-btn voice-btn" id="haChatVoice" title="Voice">&#127908;</button>
        <button class="input-btn send-btn" id="haChatSend" title="${{T.send}}">&#9654;</button>
      </div>
      <div class="voice-bar" id="haChatVoiceBar">
        <label class="voice-toggle-label">
          <input type="checkbox" id="haChatVoiceToggle" />
          <span class="voice-toggle-track"><span class="voice-toggle-thumb"></span></span>
          <span>${{T.voice_mode}}</span>
        </label>
        <span class="voice-speaking" id="haChatSpeaking" style="display:none;" title="${{T.voice_stop_speaking}}">
          <span class="wave-mini"><span></span><span></span><span></span></span>
          ${{T.voice_speaking}}
        </span>
      </div>
    </div>
    <button class="bubble-btn" id="haChatBubbleBtn" title="Amira"{' style="display:none"' if not show_bubble else ''}>&#129302;</button>
  `;
  document.body.appendChild(root);

  // ---- Elements ----
  const panel = document.getElementById('haChatPanel');
  const btn = document.getElementById('haChatBubbleBtn');
  const header = document.getElementById('haChatHeader');
  const input = document.getElementById('haChatInput');
  const sendBtn = document.getElementById('haChatSend');
  const voiceBtn = document.getElementById('haChatVoice');
  const messagesEl = document.getElementById('haChatMessages');
  const contextBar = document.getElementById('haChatContext');
  const quickActionsEl = document.getElementById('haQuickActions');
  const closeBtn = document.getElementById('haChatClose');
  const newBtn = document.getElementById('haChatNew');
  const historyBtn = document.getElementById('haChatHistory');
  const historyPanel = document.getElementById('haHistoryPanel');
  const historyList = document.getElementById('haHistoryList');
  const historyCloseBtn = document.getElementById('haHistoryClose');
  const providerSelect = document.getElementById('haProviderSelect');
  const modelSelect = document.getElementById('haModelSelect');
  const agentSelect = document.getElementById('haAgentSelect');

  let isOpen = false;
  let isStreaming = false;
  let currentAbortController = null;

  // ---- Apply saved button position ----
  function clampBtnPosition() {{
    const sz = btn.offsetWidth || 56;
    const margin = 8;
    // If using left/top (dragged), clamp them
    if (btn.style.left && btn.style.left !== 'auto') {{
      let x = parseInt(btn.style.left) || 0;
      let y = parseInt(btn.style.top) || 0;
      x = Math.max(margin, Math.min(window.innerWidth - sz - margin, x));
      y = Math.max(margin, Math.min(window.innerHeight - sz - margin, y));
      btn.style.left = x + 'px';
      btn.style.top = y + 'px';
    }} else {{
      // Using right/bottom — ensure they don't push the button off-screen
      const r = parseInt(btn.style.right) || 24;
      const b = parseInt(btn.style.bottom) || 24;
      btn.style.right = Math.max(margin, r) + 'px';
      btn.style.bottom = Math.max(margin, b) + 'px';
    }}
  }}

  // ---- Apply saved button position (only if manually dragged) ----
  // If user never dragged the button, keep it at bottom-right using relative positioning
  // Only restore left/top if user explicitly dragged it
  const wasDragged = loadSetting('btn-dragged', false);

  function clampBtnPosition() {{
    const sz = btn.offsetWidth || 56;
    const margin = 8;
    // If using left/top (dragged), clamp them
    if (btn.style.left && btn.style.left !== 'auto') {{
      let x = parseInt(btn.style.left) || 0;
      let y = parseInt(btn.style.top) || 0;
      x = Math.max(margin, Math.min(window.innerWidth - sz - margin, x));
      y = Math.max(margin, Math.min(window.innerHeight - sz - margin, y));
      btn.style.left = x + 'px';
      btn.style.top = y + 'px';
    }}
    // Always ensure bottom/right are within bounds if they're being used
    if (btn.style.bottom && btn.style.bottom !== 'auto') {{
      const b = Math.max(margin, parseInt(btn.style.bottom) || 24);
      btn.style.bottom = b + 'px';
    }}
    if (btn.style.right && btn.style.right !== 'auto') {{
      const r = Math.max(margin, parseInt(btn.style.right) || 24);
      btn.style.right = r + 'px';
    }}
  }}

  if (wasDragged && savedPos) {{
    // User manually dragged it - restore exact position
    btn.style.left = savedPos.x + 'px';
    btn.style.top = savedPos.y + 'px';
    btn.style.right = 'auto';
    btn.style.bottom = 'auto';
  }} else if (isTablet) {{
    // Tablet default: top-right (avoids keyboard covering the chat)
    btn.style.top = '16px';
    btn.style.right = '16px';
    btn.style.left = 'auto';
    btn.style.bottom = 'auto';
  }} else {{
    // Desktop default: bottom-right
    btn.style.bottom = '24px';
    btn.style.right = '24px';
    btn.style.left = 'auto';
    btn.style.top = 'auto';
  }}
  // Clamp on startup in case viewport changed since last save
  setTimeout(clampBtnPosition, 0);

  window.addEventListener('resize', () => {{
    clampBtnPosition();
    if (isOpen) positionPanelNearButton();
  }});

  // ---- Apply saved panel size or tablet defaults ----
  if (savedSize) {{
    panel.style.width = savedSize.w + 'px';
    panel.style.height = savedSize.h + 'px';
  }} else if (isTablet) {{
    // Tablet: wider and shorter to leave room for keyboard
    panel.style.width = Math.min(520, window.innerWidth - 60) + 'px';
    panel.style.height = Math.min(400, window.innerHeight - 100) + 'px';
  }}

  // Save panel size on resize
  const panelResizeObserver = new ResizeObserver((entries) => {{
    for (const entry of entries) {{
      if (panel.classList.contains('open')) {{
        const rect = entry.contentRect;
        if (rect.width > 100 && rect.height > 100)
          saveSetting('panel-size', {{ w: Math.round(rect.width), h: Math.round(rect.height) }});
      }}
    }}
  }});
  panelResizeObserver.observe(panel);

  // ---- Draggable Button — uses Pointer Events + setPointerCapture ----
  // setPointerCapture ensures pointermove/pointerup are delivered to the button
  // even when the cursor moves outside the document (e.g. over an iframe or
  // another window region), which was causing the drag to "freeze".
  let isDragging = false, dragStarted = false, dragOffsetX = 0, dragOffsetY = 0;
  let dragStartX = 0, dragStartY = 0;
  const DRAG_THRESHOLD = 5;

  btn.addEventListener('pointerdown', (e) => {{
    if (e.button !== 0 && e.pointerType === 'mouse') return; // left button only for mouse
    e.preventDefault();
    btn.setPointerCapture(e.pointerId); // lock all pointer events to this element
    isDragging = false;
    dragStarted = false;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    dragOffsetX = e.clientX - btn.getBoundingClientRect().left;
    dragOffsetY = e.clientY - btn.getBoundingClientRect().top;
  }});

  btn.addEventListener('pointermove', (e) => {{
    if (!btn.hasPointerCapture(e.pointerId)) return;
    if (!isDragging) {{
      if (Math.abs(e.clientX - dragStartX) > DRAG_THRESHOLD || Math.abs(e.clientY - dragStartY) > DRAG_THRESHOLD) {{
        isDragging = true;
        dragStarted = true;
        btn.classList.add('dragging');
      }} else return;
    }}
    btn.style.left = Math.max(0, Math.min(window.innerWidth - 56, e.clientX - dragOffsetX)) + 'px';
    btn.style.top = Math.max(0, Math.min(window.innerHeight - 56, e.clientY - dragOffsetY)) + 'px';
    btn.style.right = 'auto'; btn.style.bottom = 'auto';
    if (isOpen) positionPanelNearButton();
  }});

  btn.addEventListener('pointerup', (e) => {{
    if (!btn.hasPointerCapture(e.pointerId)) return;
    btn.releasePointerCapture(e.pointerId);
    if (isDragging) {{
      isDragging = false;
      btn.classList.remove('dragging');
      saveSetting('btn-pos', {{ x: parseInt(btn.style.left) || 0, y: parseInt(btn.style.top) || 0 }});
      saveSetting('btn-dragged', true);
    }}
  }});

  btn.addEventListener('pointercancel', (e) => {{
    if (btn.hasPointerCapture(e.pointerId)) btn.releasePointerCapture(e.pointerId);
    isDragging = false;
    btn.classList.remove('dragging');
  }});

  // ---- Panel positioning ----
  function positionPanelNearButton() {{
    const rect = btn.getBoundingClientRect();
    const pw = panel.offsetWidth || 380, ph = panel.offsetHeight || 520;
    const vw = window.innerWidth, vh = window.innerHeight;
    let top, left;

    // Prefer opening below if button is in the top half, above if in the bottom half
    if (rect.top < vh / 2) {{
      // Button is in top half — open below
      top = rect.bottom + 10;
      if (top + ph > vh - 10) top = Math.max(10, vh - ph - 10);
    }} else {{
      // Button is in bottom half — open above
      top = rect.top - ph - 10;
      if (top < 10) top = 10;
    }}

    // Align right edge with button, but keep within viewport
    left = rect.right - pw;
    if (left < 10) left = 10;
    if (left + pw > vw - 10) left = vw - pw - 10;

    panel.style.top = top + 'px'; panel.style.left = left + 'px';
    panel.style.right = 'auto'; panel.style.bottom = 'auto';
  }}

  // ---- Toggle Panel ----
  function togglePanel() {{
    isOpen = !isOpen;
    panel.classList.toggle('open', isOpen);
    if (isOpen) {{ positionPanelNearButton(); updateContextBar(); updateQuickActions(); input.focus(); }}
  }}

  // Capture log entry on mousedown (fires BEFORE HA's click-outside handler
  // dismisses the dialog), so the cache is populated before the dialog closes.
  btn.addEventListener('mousedown', () => {{
    const curPath = window.location.pathname;
    if (curPath.includes('/config/log')) {{
      const live = extractVisibleLogEntry();
      if (live) _cachedLogEntry = live;
    }}
  }});
  btn.addEventListener('click', () => {{ if (!dragStarted) togglePanel(); }});
  closeBtn.addEventListener('click', () => {{ isOpen = false; panel.classList.remove('open'); historyPanel.classList.remove('open'); }});
  newBtn.addEventListener('click', () => {{
    resetSession(); clearHistory(); messagesEl.innerHTML = '';
    _cachedLogEntry = null; // clear stale log cache on new chat
    updateContextBar(); updateQuickActions();
    historyPanel.classList.remove('open');
    broadcastEvent('clear', {{}});
  }});

  // ---- Conversation History Panel ----
  historyBtn.addEventListener('click', () => {{
    const isHistoryOpen = historyPanel.classList.contains('open');
    if (isHistoryOpen) {{
      historyPanel.classList.remove('open');
    }} else {{
      historyPanel.classList.add('open');
      loadConversationList();
    }}
  }});
  historyCloseBtn.addEventListener('click', () => {{ historyPanel.classList.remove('open'); }});

  async function loadConversationList() {{
    historyList.innerHTML = '<div style="text-align:center;padding:20px;color:var(--secondary-text-color,#999);">&#8987;</div>';
    try {{
      const resp = await fetch(API_BASE + '/api/conversations', {{credentials:'same-origin'}});
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      const convs = data.conversations || [];
      historyList.innerHTML = '';
      if (convs.length === 0) {{
        historyList.innerHTML = '<div class="history-empty">' + (T.no_conversations || 'No conversations') + '</div>';
        return;
      }}
      const currentSid = getSessionId();
      convs.forEach(conv => {{
        const item = document.createElement('div');
        item.className = 'history-item' + (conv.id === currentSid ? ' active' : '');
        const info = document.createElement('div');
        info.className = 'history-item-info';
        const title = document.createElement('div');
        title.className = 'history-title';
        title.textContent = conv.title || 'Chat';
        const meta = document.createElement('div');
        meta.className = 'history-meta';
        const count = document.createElement('span');
        count.textContent = (conv.message_count || 0) + ' ' + (T.messages_count || 'messages');
        const source = document.createElement('span');
        source.className = 'history-source';
        source.textContent = conv.source === 'bubble' ? (T.bubble_source || 'Bubble') : (T.chat_source || 'Chat UI');
        meta.appendChild(count);
        info.appendChild(title);
        info.appendChild(meta);
        item.appendChild(info);
        item.appendChild(source);
        item.addEventListener('click', () => switchToConversation(conv.id));
        historyList.appendChild(item);
      }});
    }} catch(e) {{
      console.error('[Bubble] Error loading conversations:', e);
      historyList.innerHTML = '<div class="history-error">' + (T.load_error || 'Error loading conversations') + '</div>';
    }}
  }}

  async function switchToConversation(sessionId) {{
    try {{
      const resp = await fetch(API_BASE + '/api/conversations/' + encodeURIComponent(sessionId), {{credentials:'same-origin'}});
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      // Update session ID
      setSessionId(sessionId);
      // Clear current display and localStorage history
      messagesEl.innerHTML = '';
      const newHistory = [];
      if (data.messages && data.messages.length > 0) {{
        // Show last 20 messages
        const recent = data.messages.slice(-20);
        recent.forEach(m => {{
          if (m.role === 'user' || m.role === 'assistant') {{
            addMessage(m.role, m.content, m.role === 'assistant');
            newHistory.push({{ role: m.role, text: m.content, ts: Date.now() }});
          }}
        }});
      }}
      saveHistory(newHistory);
      historyPanel.classList.remove('open');
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }} catch(e) {{
      console.error('[Bubble] Error loading conversation:', e);
    }}
  }}

  // ---- Draggable Panel (header) ----
  let panelDragging = false, panelDragOffX = 0, panelDragOffY = 0;
  header.addEventListener('mousedown', (e) => {{
    if (e.target.tagName === 'BUTTON') return;
    panelDragging = true; panelDragOffX = e.clientX - panel.getBoundingClientRect().left;
    panelDragOffY = e.clientY - panel.getBoundingClientRect().top; e.preventDefault();
  }});
  document.addEventListener('mousemove', (e) => {{
    if (!panelDragging) return;
    panel.style.left = Math.max(0, Math.min(window.innerWidth - panel.offsetWidth, e.clientX - panelDragOffX)) + 'px';
    panel.style.top = Math.max(0, Math.min(window.innerHeight - panel.offsetHeight, e.clientY - panelDragOffY)) + 'px';
    panel.style.right = 'auto'; panel.style.bottom = 'auto';
  }});
  document.addEventListener('mouseup', () => {{ panelDragging = false; }});

  // ---- Context Bar ----
  function updateContextBar() {{
    const ctx = detectContext();
    if (ctx.label) {{
      let text = ctx.label;
      if (ctx.entities && ctx.entities.length > 0) text += ' (' + ctx.entities.length + ' entities)';
      if (ctx.type === 'logs' && (ctx.logEntry || _cachedLogEntry)) text += ' \u2022 log selezionato';
      // Card editor in GUI mode (no YAML readable) — show warning
      const noYaml = ctx.type === 'card_editor' && !ctx.cardYaml;
      if (noYaml) {{
        text = T.card_no_yaml_warn;
        contextBar.classList.add('context-bar--warn');
      }} else {{
        contextBar.classList.remove('context-bar--warn');
      }}
      contextBar.style.display = 'block'; contextBar.textContent = text;
      btn.classList.add('has-context');
    }} else {{
      contextBar.classList.remove('context-bar--warn');
      contextBar.style.display = 'none'; btn.classList.remove('has-context');
    }}
  }}

  // ---- Quick Actions ----
  function updateQuickActions() {{
    const actions = getQuickActions();
    quickActionsEl.innerHTML = '';
    if (actions.length === 0) {{ quickActionsEl.style.display = 'none'; return; }}
    quickActionsEl.style.display = 'flex';
    actions.forEach(a => {{
      const chip = document.createElement('button');
      chip.className = 'quick-action-btn';
      chip.textContent = a.label;
      chip.addEventListener('click', () => {{
        input.value = a.text;
        sendMessage();
        quickActionsEl.style.display = 'none'; // hide after use
      }});
      quickActionsEl.appendChild(chip);
    }});
  }}

  // SPA navigation detection
  let lastPath = window.location.pathname;
  let lastLogEntry = null;
  // Persistent log entry cache: survives dialog close so bubble can still use it
  // after user clicks bubble (which dismisses the HA dialog).
  // Cleared only when navigating away from the logs page or on new chat.
  let _cachedLogEntry = null;

  setInterval(() => {{
    const curPath = window.location.pathname;
    if (curPath !== lastPath) {{
      // Navigated to a different page — clear log cache
      lastPath = curPath;
      lastLogEntry = null;
      _cachedLogEntry = null;
      if (isOpen) {{ updateContextBar(); updateQuickActions(); }}
    }}
    // On logs page, poll for open log entry dialogs.
    // Update cache whenever a NEW entry is detected; never clear cache just
    // because the dialog was dismissed (it closes when bubble button is clicked).
    if (curPath.includes('/config/log')) {{
      const entry = extractVisibleLogEntry();
      const entryKey = entry ? entry.substring(0, 80) : null;
      if (entry) {{
        // A dialog is open — update (or refresh) the persistent cache
        _cachedLogEntry = entry;
      }}
      // Only trigger a UI refresh when the detected entry key actually changes
      if (entryKey !== lastLogEntry) {{
        lastLogEntry = entryKey;
        if (isOpen) {{ updateContextBar(); updateQuickActions(); }}
      }}
    }}
    // Card editor detection — open/close triggers context bar + quick actions update
    const cardOpen = isCardEditorOpen();
    if (cardOpen !== _lastCardEditorOpen) {{
      _lastCardEditorOpen = cardOpen;
      if (isOpen) {{ updateContextBar(); updateQuickActions(); }}
      if (cardOpen) {{
        _cardBtnInjected = false;
        injectCardEditorButton();
      }} else {{
        removeCardEditorButton();
        _cardBtnInjected = false;
      }}
    }}
    // Re-inject button if editor open but button disappeared (HA re-rendered)
    if (cardOpen && (!_cardBtnInjected || !_cardBtnExists())) {{
      _cardBtnInjected = false;
      injectCardEditorButton();
    }}
    // ---- Automation integrated view detection ----
    const autoMatch = AMIRA_ENABLE_AUTOMATION_BUTTON ? curPath.match(/\\/config\\/automation\\/(?:edit|show|trace)\\/([^/]+)/) : null;
    const onAutomationDetailView = !!(
      AMIRA_ENABLE_AUTOMATION_BUTTON
      && (autoMatch || _findAutomationFlowHost())
    );
    if (onAutomationDetailView) {{
      const autoId = autoMatch ? autoMatch[1] : null;
      // Inject toolbar button if not present
      if (!_autoBtnInjected || !_autoToolbarBtnExists()) {{
        _autoBtnInjected = false;
        injectAutomationToolbarButton();
      }}
      // Inject flow toggle near Amira button
      if (!_autoFlowToggleBtnExists()) {{
        injectAutomationFlowToggleButton();
      }} else {{
        _applyFlowVisibility();
      }}
      // Inject flow visualization if not done or automation changed
      if (autoId && (_lastAutoPageId !== autoId || _autoFlowStatus === 'idle')) {{
        if (_lastAutoPageId !== autoId) {{
          _autoFlowStatus = 'idle';
          _autoFlowUnavailableReason = '';
          _autoFlowInjected = false;
          _autoFlowConfigSig = '';
          _autoFlowLastCheckTs = 0;
        }}
        _lastAutoPageId = autoId;
        fetchAndRenderAutomationFlow(autoId, {{ showUnavailable: false }});
      }} else if (autoId && _autoFlowStatus === 'rendered' && _autoFlowVisible) {{
        const now = Date.now();
        if ((now - _autoFlowLastCheckTs) >= AUTO_FLOW_REFRESH_MS) {{
          _autoFlowLastCheckTs = now;
          fetchAndRenderAutomationFlow(autoId, {{ showUnavailable: false, refresh: true }});
        }}
      }}
      if (!autoId && _autoFlowInjected) {{
        const flow = _findAutomationFlowEl();
        if (flow) flow.remove();
        _autoFlowEl = null;
        _autoFlowInjected = false;
        _lastAutoPageId = null;
        _autoFlowStatus = 'idle';
        _autoFlowUnavailableReason = '';
        _autoFlowConfigSig = '';
        _autoFlowLastCheckTs = 0;
      }}
      // Auto-restore sidebar if it was open
      if (!_autoSidebarOpen && loadSetting('auto-sidebar-open', false)) {{
        openAutomationSidebar();
      }}
      // Hide floating bubble when sidebar is open
      if (_autoSidebarOpen) {{
        btn.style.display = 'none';
      }}
    }} else {{
      // Navigated away from automation page — clean up
      if (_autoBtnInjected || _autoSidebarOpen || _autoFlowInjected) {{
        removeAutomationIntegration();
        btn.style.display = '';
      }}
    }}
  }}, 1000);

  // ---- Card editor inline chat panel ----
  // Instead of fighting with pointer-events / shadow DOM / top-layer, we inject
  // a self-contained mini chat panel INSIDE the mdc-dialog__surface of the HA
  // card editor. It is a native child of the dialog, so clicks always work.
  // The Amira button in the footer toggles this panel open/closed.
  const CARD_PANEL_ID = 'amira-card-chat';
  const CARD_BTN_ID   = 'amira-card-editor-btn';
  let _lastCardEditorOpen = false;
  let _cardBtnInjected    = false;
  let _cardBtnParent      = null;
  let _cardPanelOpen      = false;
  // Direct element references — getElementById doesn't cross shadow DOM
  let _cardMsgsEl  = null;
  let _cardInputEl = null;
  let _cardPanelEl = null;
  let _cardProvSel   = null;  // card panel provider select mirror
  let _cardModSel    = null;  // card panel model select mirror
  let _cardAgentSel  = null;  // card panel agent select mirror

  function _cardBtnExists() {{
    return !!(_cardBtnParent && _cardBtnParent.querySelector('#' + CARD_BTN_ID));
  }}

  // Returns the dialog surface element (visible card panel container).
  // Supports legacy (.mdc-dialog__surface) and new HA (.content-wrapper / .body).
  function _getCardSurface() {{
    try {{
      const editCardEl = _findEditCardEl();
      if (!editCardEl?.shadowRoot) return null;
      const haDialog = editCardEl.shadowRoot.querySelector('ha-dialog[open]');
      if (!haDialog?.shadowRoot) return null;
      return haDialog.shadowRoot.querySelector('.mdc-dialog__surface')
          || haDialog.shadowRoot.querySelector('.content-wrapper')
          || haDialog.shadowRoot.querySelector('.body')
          || null;
    }} catch(e) {{ return null; }}
  }}

  // Global copy helper — robust across iframe/shadow contexts.
  window.__amiraCopyCode = function(btn) {{
    var wrap = btn && btn.parentElement ? btn.parentElement : null;
    var code = wrap ? wrap.querySelector('code') : null;
    if (!code) return;
    var txt = String(code.textContent || code.innerText || '');

    function ok() {{
      btn.textContent = T.copied || 'Copied!';
      setTimeout(function() {{ btn.textContent = T.copy_btn || 'Copy'; }}, 1500);
    }}
    function fail() {{
      btn.textContent = 'Error';
      setTimeout(function() {{ btn.textContent = T.copy_btn || 'Copy'; }}, 1500);
    }}
    function fallback() {{
      var ta = document.createElement('textarea');
      ta.value = txt;
      ta.style.cssText = 'position:fixed;left:-9999px;top:-9999px;opacity:0;';
      ta.setAttribute('readonly', '');
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      if (ta.setSelectionRange) ta.setSelectionRange(0, ta.value.length);
      try {{
        if (document.execCommand('copy')) ok();
        else fail();
      }} catch(e) {{
        fail();
      }}
      document.body.removeChild(ta);
    }}

    var clipboards = [];
    try {{
      if (navigator && navigator.clipboard && navigator.clipboard.writeText) clipboards.push(navigator.clipboard);
    }} catch(e) {{}}
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

    function tryClipboard(i) {{
      if (i >= clipboards.length) {{
        fallback();
        return;
      }}
      clipboards[i].writeText(txt).then(ok).catch(function() {{ tryClipboard(i + 1); }});
    }}
    tryClipboard(0);
  }};

  // Event delegation for copy buttons (inline onclick blocked by HA CSP).
  // Uses composedPath() to cross shadow DOM boundaries (card editor panel
  // lives inside HA dialog shadow root, so e.target is retargeted).
  function _findCopyBtn(e) {{
    var path = e.composedPath ? e.composedPath() : [e.target];
    for (var i = 0; i < path.length; i++) {{
      var el = path[i];
      if (el.classList && el.classList.contains('amira-copy-btn')) return el;
    }}
    return null;
  }}
  document.addEventListener('click', function(e) {{
    var btn = _findCopyBtn(e);
    if (btn) {{ e.preventDefault(); e.stopPropagation(); window.__amiraCopyCode(btn); }}
  }}, true);
  document.addEventListener('mouseover', function(e) {{
    var btn = _findCopyBtn(e);
    if (btn) btn.style.background = '#475569';
  }}, true);
  document.addEventListener('mouseout', function(e) {{
    var btn = _findCopyBtn(e);
    if (btn) btn.style.background = '#334155';
  }}, true);

  function _renderInlineMd(text) {{
    // Fenced code blocks: ```lang + newline + content + ``` -> styled pre with copy button
    const codeBlocks = [];
    text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, function(m, lang, code) {{
      const escaped = code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      const placeholder = '___CODEBLOCK_' + codeBlocks.length + '___';
      codeBlocks.push('<div style="position:relative;margin:6px 0;">'
        + '<button class="amira-copy-btn" style="position:absolute;top:6px;right:6px;background:#334155;border:1px solid #475569;color:#e2e8f0;border-radius:4px;padding:3px 10px;font-size:11px;cursor:pointer;font-weight:500;letter-spacing:0.3px;transition:background .15s;z-index:1;">' + T.copy_btn + '</button>'
        + '<pre style="background:#1e293b;color:#e2e8f0;padding:8px 10px;border-radius:6px;font-size:12px;overflow-x:auto;margin:0;white-space:pre-wrap;word-break:break-word;"><code>' + escaped + '</code></pre></div>');
      return placeholder;
    }});
    // Process remaining markdown (HTML-escape only outside code blocks)
    text = text
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/[*][*](.+?)[*][*]/g,'<b>$1</b>')
      .replace(/`([^`]+)`/g,'<code style="background:rgba(0,0,0,0.08);padding:1px 4px;border-radius:3px;font-size:12px">$1</code>')
      .replace(/\\n/g,'<br>');
    // Restore code blocks (already HTML-safe, not double-escaped)
    codeBlocks.forEach(function(block, i) {{
      text = text.replace('___CODEBLOCK_' + i + '___', block);
    }});
    return text;
  }}

  // ── Card conversation history ───────────────────────────────────────────
  let _cardHistoryOpen = false;

  async function _toggleCardHistory(msgsContainer) {{
    if (_cardHistoryOpen) {{
      // Close history → restore chat messages
      _cardHistoryOpen = false;
      if (msgsContainer) msgsContainer.innerHTML = '';
      await _loadCardConversation(getCardSessionId(), msgsContainer);
      return;
    }}
    _cardHistoryOpen = true;
    if (!msgsContainer) return;
    msgsContainer.innerHTML = '<div style="text-align:center;padding:16px;color:var(--secondary-text-color,#999);">⏳</div>';
    try {{
      const resp = await fetch(API_BASE + '/api/conversations?source=card', {{credentials:'same-origin'}});
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      const convs = data.conversations || [];
      msgsContainer.innerHTML = '';
      if (convs.length === 0) {{
        msgsContainer.innerHTML = '<div style="text-align:center;padding:16px;color:var(--secondary-text-color,#999);font-size:12px;">' + (T.no_conversations || 'No conversations') + '</div>';
        return;
      }}
      const currentSid = getCardSessionId();
      convs.forEach(conv => {{
        const item = document.createElement('div');
        const isActive = conv.id === currentSid;
        item.style.cssText = 'padding:8px 10px;border-bottom:1px solid var(--divider-color,#e0e0e0);cursor:pointer;font-size:12px;display:flex;justify-content:space-between;align-items:center;' + (isActive ? 'background:rgba(102,126,234,0.1);' : '');
        const info = document.createElement('div');
        info.style.cssText = 'flex:1;min-width:0;';
        const title = document.createElement('div');
        title.style.cssText = 'font-weight:500;color:var(--primary-text-color,#212121);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;';
        title.textContent = conv.title || 'Chat';
        const meta = document.createElement('div');
        meta.style.cssText = 'font-size:10px;color:var(--secondary-text-color,#999);margin-top:2px;';
        meta.textContent = (conv.message_count || 0) + ' ' + (T.messages_count || 'messages');
        info.appendChild(title);
        info.appendChild(meta);
        item.appendChild(info);
        if (isActive) {{
          const badge = document.createElement('span');
          badge.textContent = '●';
          badge.style.cssText = 'color:#667eea;font-size:10px;flex-shrink:0;margin-left:6px;';
          item.appendChild(badge);
        }}
        item.addEventListener('click', () => {{
          // Switch to this conversation
          try {{ localStorage.setItem(CARD_SESSION_KEY, conv.id); }} catch(e) {{}}
          _cardHistoryOpen = false;
          msgsContainer.innerHTML = '';
          _loadCardConversation(conv.id, msgsContainer);
        }});
        msgsContainer.appendChild(item);
      }});
    }} catch(e) {{
      console.error('[Amira card] history error:', e);
      msgsContainer.innerHTML = '<div style="text-align:center;padding:16px;color:#f44336;font-size:12px;">' + (T.error_connection || 'Error') + '</div>';
    }}
  }}

  async function _loadCardConversation(sessionId, msgsContainer) {{
    if (!msgsContainer) return;
    try {{
      const resp = await fetch(API_BASE + '/api/conversations/' + encodeURIComponent(sessionId), {{credentials:'same-origin'}});
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.messages && data.messages.length > 0) {{
        const recent = data.messages.slice(-30);
        recent.forEach(m => {{
          if (m.role === 'user' || m.role === 'assistant') {{
            _cardPanelAddMsg(m.role, m.content, true);
          }}
        }});
        msgsContainer.scrollTop = msgsContainer.scrollHeight;
      }}
    }} catch(e) {{
      console.error('[Amira card] load conversation error:', e);
    }}
  }}

  function openCardPanel() {{
    if (_cardPanelOpen) return;
    const surface = _getCardSurface();
    if (!surface) return;

    // Keep original surface width — only adjust overflow so the panel fits inside
    surface.style.cssText += ';display:flex !important;flex-direction:column !important;max-height:90vh !important;overflow:hidden !important;width:' + surface.offsetWidth + 'px !important;max-width:' + surface.offsetWidth + 'px !important;';

    const panel = document.createElement('div');
    panel.id = CARD_PANEL_ID;
    panel.style.cssText = 'display:flex;flex-direction:column;border-top:2px solid #667eea;background:var(--card-background-color,#fff);flex-shrink:0;height:300px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;width:100%;box-sizing:border-box;overflow:hidden;';

    // Header
    const hdr = document.createElement('div');
    hdr.style.cssText = 'display:flex;align-items:center;padding:6px 12px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;flex-shrink:0;gap:8px;';
    const hdrTitle = document.createElement('span');
    hdrTitle.textContent = '🤖 Amira';
    hdrTitle.style.cssText = 'font-weight:600;font-size:13px;white-space:nowrap;';
    // Agent select — mirrors haAgentSelect
    const _mainAgentSel = document.getElementById('haAgentSelect');
    const cardAgentSel = document.createElement('select');
    cardAgentSel.style.cssText = 'font-size:11px;padding:2px 4px;border-radius:4px;border:none;background:rgba(255,255,255,0.2);color:#fff;cursor:pointer;max-width:130px;min-width:0;flex-shrink:1;';
    if (_mainAgentSel && _mainAgentSel.style.display !== 'none' && _mainAgentSel.options.length) {{
      Array.from(_mainAgentSel.options).forEach(o => {{
        const opt = document.createElement('option');
        opt.value = o.value; opt.textContent = o.textContent;
        if (o.selected) opt.selected = true;
        cardAgentSel.appendChild(opt);
      }});
      cardAgentSel.addEventListener('change', () => {{ _mainAgentSel.value = cardAgentSel.value; _mainAgentSel.dispatchEvent(new Event('change')); }});
    }} else {{
      cardAgentSel.style.display = 'none';
    }}
    // Provider select — mirrors haProviderSelect
    const _mainProvSel = document.getElementById('haProviderSelect');
    const _mainModSel  = document.getElementById('haModelSelect');
    const cardProvSel = document.createElement('select');
    cardProvSel.style.cssText = 'font-size:11px;padding:2px 4px;border-radius:4px;border:none;background:rgba(255,255,255,0.2);color:#fff;cursor:pointer;max-width:150px;min-width:0;flex-shrink:1;';
    if (_mainProvSel) {{
      Array.from(_mainProvSel.options).forEach(o => {{
        const opt = document.createElement('option');
        opt.value = o.value; opt.textContent = o.textContent;
        if (o.selected) opt.selected = true;
        cardProvSel.appendChild(opt);
      }});
      cardProvSel.addEventListener('change', () => {{ _mainProvSel.value = cardProvSel.value; _mainProvSel.dispatchEvent(new Event('change')); }});
    }}
    const cardModSel = document.createElement('select');
    cardModSel.style.cssText = 'font-size:11px;padding:2px 4px;border-radius:4px;border:none;background:rgba(255,255,255,0.2);color:#fff;cursor:pointer;max-width:200px;min-width:0;flex-shrink:1;';
    if (_mainModSel) {{
      Array.from(_mainModSel.options).forEach(o => {{
        const opt = document.createElement('option');
        opt.value = o.value; opt.textContent = o.textContent;
        if (o.selected) opt.selected = true;
        cardModSel.appendChild(opt);
      }});
      cardModSel.addEventListener('change', () => {{ _mainModSel.value = cardModSel.value; _mainModSel.dispatchEvent(new Event('change')); }});
    }}
    // Spacer to push action buttons to the right
    const hdrSpacer = document.createElement('span');
    hdrSpacer.style.cssText = 'flex:1;';
    // New chat button
    const hdrNew = document.createElement('button');
    hdrNew.textContent = '＋';
    hdrNew.title = T.card_new_chat || 'New chat';
    hdrNew.style.cssText = 'background:rgba(255,255,255,0.2);border:none;color:#fff;cursor:pointer;font-size:14px;padding:2px 7px;border-radius:4px;line-height:1;';
    hdrNew.onclick = () => {{
      resetCardSession();
      if (_cardMsgsEl) _cardMsgsEl.innerHTML = '';
    }};
    // History button
    const hdrHistory = document.createElement('button');
    hdrHistory.textContent = '📋';
    hdrHistory.title = T.card_history || 'Chat history';
    hdrHistory.style.cssText = 'background:rgba(255,255,255,0.2);border:none;color:#fff;cursor:pointer;font-size:13px;padding:2px 7px;border-radius:4px;line-height:1;';
    hdrHistory.onclick = () => _toggleCardHistory(msgs);
    const hdrClose = document.createElement('button');
    hdrClose.textContent = '\u2715';
    hdrClose.style.cssText = 'background:none;border:none;color:#fff;cursor:pointer;font-size:16px;padding:0 4px;line-height:1;';
    hdrClose.onclick = closeCardPanel;
    hdr.appendChild(hdrTitle);
    if (_mainAgentSel && _mainAgentSel.style.display !== 'none' && _mainAgentSel.options.length) hdr.appendChild(cardAgentSel);
    if (_mainProvSel && _mainProvSel.options.length) hdr.appendChild(cardProvSel);
    if (_mainModSel  && _mainModSel.options.length)  hdr.appendChild(cardModSel);
    hdr.appendChild(hdrSpacer);
    hdr.appendChild(hdrNew);
    hdr.appendChild(hdrHistory);
    hdr.appendChild(hdrClose);

    // Quick actions
    const ctx = detectContext();
    const actions = getQuickActions(ctx);
    const qaRow = document.createElement('div');
    qaRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;padding:6px 8px;flex-shrink:0;border-bottom:1px solid var(--divider-color,#e0e0e0);';
    actions.forEach(a => {{
      const chip = document.createElement('button');
      chip.textContent = a.label;
      chip.style.cssText = 'background:var(--secondary-background-color,#f5f5f5);border:1px solid var(--divider-color,#ddd);border-radius:12px;padding:3px 10px;font-size:11px;cursor:pointer;white-space:nowrap;color:var(--primary-text-color,#212121);';
      chip.onclick = () => cardPanelSend(a.text);
      qaRow.appendChild(chip);
    }});

    // Messages
    const msgs = document.createElement('div');
    msgs.id = CARD_PANEL_ID + '-msgs';
    msgs.style.cssText = 'flex:1;overflow-y:auto;padding:8px 12px;display:flex;flex-direction:column;gap:6px;min-height:0;';

    // Input row
    const inputRow = document.createElement('div');
    inputRow.style.cssText = 'display:flex;gap:6px;padding:8px;flex-shrink:0;border-top:1px solid var(--divider-color,#e0e0e0);';
    const inp = document.createElement('textarea');
    inp.id = CARD_PANEL_ID + '-input';
    inp.placeholder = T.placeholder;
    inp.rows = 1;
    inp.style.cssText = 'flex:1;border:1px solid var(--divider-color,#ddd);border-radius:8px;padding:6px 10px;font-size:13px;resize:none;outline:none;background:var(--secondary-background-color,#f9f9f9);color:var(--primary-text-color,#212121);font-family:inherit;';
    inp.addEventListener('input', () => {{ inp.style.height='auto'; inp.style.height=Math.min(inp.scrollHeight,80)+'px'; }});
    inp.addEventListener('keydown', e => {{ if(e.key==='Enter'&&!e.shiftKey){{ e.preventDefault(); cardPanelSend(); }} }});
    const sendB = document.createElement('button');
    sendB.textContent = '▶';
    sendB.style.cssText = 'background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;border-radius:8px;padding:0 14px;cursor:pointer;font-size:16px;flex-shrink:0;';
    sendB.onclick = () => cardPanelSend();
    inputRow.appendChild(inp);
    inputRow.appendChild(sendB);

    panel.appendChild(hdr);
    // Info banner: YAML not detected (GUI mode)
    if (!ctx.cardYaml) {{
      const warn = document.createElement('div');
      warn.style.cssText = 'padding:6px 12px;background:#fff3cd;color:#856404;font-size:11px;border-bottom:1px solid #ffeeba;flex-shrink:0;display:flex;align-items:center;justify-content:space-between;';
      warn.innerHTML = '<span>' + (T.card_no_yaml_warn || '') + '</span>';
      const closeW = document.createElement('button');
      closeW.textContent = '\u2715';
      closeW.style.cssText = 'background:none;border:none;color:#856404;cursor:pointer;font-size:13px;padding:0 2px;';
      closeW.onclick = () => warn.remove();
      warn.appendChild(closeW);
      panel.appendChild(warn);
    }}
    if (actions.length) panel.appendChild(qaRow);
    panel.appendChild(msgs);
    panel.appendChild(inputRow);
    surface.appendChild(panel);
    // Save direct references — getElementById won't cross shadow DOM
    _cardPanelEl = panel;
    _cardMsgsEl  = msgs;
    _cardInputEl = inp;
    _cardProvSel   = cardProvSel;
    _cardModSel    = cardModSel;
    _cardAgentSel  = cardAgentSel;
    _cardPanelOpen = true;
    setTimeout(() => inp.focus(), 50);
  }}

  function closeCardPanel() {{
    const surface = _getCardSurface();
    if (surface) {{
      surface.style.display = '';
      surface.style.flexDirection = '';
      surface.style.maxHeight = '';
      surface.style.overflow = '';
      surface.style.width = '';
      surface.style.maxWidth = '';
    }}
    if (_cardPanelEl) _cardPanelEl.remove();
    _cardPanelEl = null;
    _cardMsgsEl  = null;
    _cardInputEl = null;
    _cardProvSel   = null;
    _cardModSel    = null;
    _cardAgentSel  = null;
    _cardPanelOpen = false;
  }}

  function _cardPanelAddMsg(role, text) {{
    if (!_cardMsgsEl) return null;
    const d = document.createElement('div');
    d.style.cssText = role === 'user'
      ? 'align-self:flex-end;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:6px 10px;border-radius:12px 12px 2px 12px;font-size:13px;max-width:85%;word-break:break-word;'
      : 'align-self:flex-start;background:var(--secondary-background-color,#f0f0f0);color:var(--primary-text-color,#212121);padding:6px 10px;border-radius:12px 12px 12px 2px;font-size:13px;max-width:85%;word-break:break-word;line-height:1.5;';
    if (role === 'user') d.textContent = text;
    else d.innerHTML = _renderInlineMd(text);
    _cardMsgsEl.appendChild(d);
    _cardMsgsEl.scrollTop = _cardMsgsEl.scrollHeight;
    return d;
  }}

  async function cardPanelSend(presetText) {{
    const text = presetText || (_cardInputEl ? _cardInputEl.value.trim() : '');
    if (!text) return;
    if (_cardInputEl && !presetText) {{ _cardInputEl.value = ''; _cardInputEl.style.height = 'auto'; }}
    _cardPanelAddMsg('user', text);
    const thinkEl = _cardPanelAddMsg('assistant', T.thinking + '…');
    try {{
      const ctx = detectContext();
      const prefix = buildContextPrefix(ctx);
      const fullMsg = prefix ? prefix + '\\n\\n' + text : text;
      const _session = getCardSessionId();
      const response = await fetch(API_BASE + '/api/chat/stream', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message: fullMsg, session_id: _session }})
      }});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '', assistantText = '';
      let firstToken = true;

      while (true) {{
        const {{ done, value }} = await reader.read();
        if (done) {{
          // Flush remaining buffer
          if (buffer.trim()) {{
            let _flushUsage = null;
            for (const line of buffer.split('\\n')) {{
              if (!line.startsWith('data: ')) continue;
              try {{
                const evt = JSON.parse(line.slice(6));
                if (evt.type === 'token') {{ assistantText += evt.content || ''; }}
                else if (evt.type === 'done') {{
                  if (evt.full_text) {{ assistantText = evt.full_text; }}
                  if (evt.usage) {{ _flushUsage = evt.usage; }}
                }}
              }} catch(e) {{}}
            }}
            if (thinkEl && assistantText) {{
              thinkEl.innerHTML = _renderInlineMd(assistantText);
            }}
            if (thinkEl && _flushUsage && (_flushUsage.input_tokens || _flushUsage.output_tokens)) {{
              const u = _flushUsage;
              const inp = (u.input_tokens || 0).toLocaleString();
              const out = (u.output_tokens || 0).toLocaleString();
              let usageTxt = inp + ' in / ' + out + ' out';
              if (u.cost !== undefined && u.cost > 0) {{
                const sym = u.currency === 'EUR' ? '\u20ac' : '$';
                usageTxt += ' \u2022 ' + sym + u.cost.toFixed(4);
              }} else if (u.cost === 0) {{
                usageTxt += ' \u2022 free';
              }}
              const uDiv = document.createElement('div');
              uDiv.style.cssText = 'font-size:10px;color:var(--secondary-text-color,#999);text-align:right;margin-top:3px;';
              uDiv.textContent = usageTxt;
              thinkEl.appendChild(uDiv);
            }}
          }}
          break;
        }}

        buffer += decoder.decode(value, {{ stream: true }});
        const lines = buffer.split('\\n');
        buffer = lines.pop() || '';

        for (const line of lines) {{
          if (!line.startsWith('data: ')) continue;
          try {{
            const evt = JSON.parse(line.slice(6));
            if (evt.type === 'token') {{
              if (firstToken) {{ firstToken = false; }}
              assistantText += evt.content || '';
              if (thinkEl) thinkEl.innerHTML = _renderInlineMd(assistantText);
              if (_cardMsgsEl) _cardMsgsEl.scrollTop = _cardMsgsEl.scrollHeight;
            }} else if (evt.type === 'clear') {{
              assistantText = '';
              if (thinkEl) thinkEl.innerHTML = T.thinking + '…';
            }} else if (evt.type === 'done') {{
              if (evt.full_text) {{
                assistantText = evt.full_text;
                if (thinkEl) thinkEl.innerHTML = _renderInlineMd(assistantText);
              }}
              if (thinkEl && evt.usage && (evt.usage.input_tokens || evt.usage.output_tokens)) {{
                const u = evt.usage;
                const inp = (u.input_tokens || 0).toLocaleString();
                const out = (u.output_tokens || 0).toLocaleString();
                let usageTxt = inp + ' in / ' + out + ' out';
                if (u.cost !== undefined && u.cost > 0) {{
                  const sym = u.currency === 'EUR' ? '\u20ac' : '$';
                  usageTxt += ' \u2022 ' + sym + u.cost.toFixed(4);
                }} else if (u.cost === 0) {{
                  usageTxt += ' \u2022 free';
                }}
                const uDiv = document.createElement('div');
                uDiv.style.cssText = 'font-size:10px;color:var(--secondary-text-color,#999);text-align:right;margin-top:3px;';
                uDiv.textContent = usageTxt;
                thinkEl.appendChild(uDiv);
              }}
            }} else if (evt.type === 'error') {{
              if (thinkEl) thinkEl.textContent = evt.message || T.error_connection;
            }} else if (evt.type === 'status') {{
              const msg = evt.message || evt.content || '';
              if (firstToken && thinkEl) thinkEl.textContent = msg + '…';
            }} else if (evt.type === 'tool') {{
              const desc = evt.description || evt.name || 'tool';
              if (firstToken && thinkEl) thinkEl.textContent = '\U0001f527 ' + desc + '…';
            }}
          }} catch (parseErr) {{}}
        }}
      }}
      // Fallback: if stream closed without any tokens, show something
      if (!assistantText && thinkEl) {{
        thinkEl.textContent = T.error_connection;
      }}
    }} catch(e) {{
      console.error('[Amira card panel] send error:', e);
      if (thinkEl) thinkEl.textContent = T.error_connection + ' (' + e.message + ')';
    }}
    if (_cardMsgsEl) _cardMsgsEl.scrollTop = _cardMsgsEl.scrollHeight;
  }}

  function injectCardEditorButton() {{
    if (!{'true' if show_card_button else 'false'}) return;
    if (_cardBtnInjected && _cardBtnExists()) return;
    const footer = getCardEditorFooter();
    if (!footer) return;
    const aiBtn = document.createElement('span');
    aiBtn.id = CARD_BTN_ID;
    aiBtn.setAttribute('role', 'button');
    aiBtn.setAttribute('tabindex', '0');
    // If footer is ha-dialog-footer (new HA), slot it as primaryAction
    if (footer.tagName && footer.tagName.toLowerCase() === 'ha-dialog-footer') {{
      aiBtn.setAttribute('slot', 'primaryAction');
    }}
    aiBtn.textContent = '🤖 Amira';
    aiBtn.style.cssText = 'display:inline-flex;align-items:center;justify-content:center;padding:0 16px;height:36px;min-width:64px;font-size:13px;font-weight:600;cursor:pointer;border:none;border-radius:4px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;box-shadow:0 2px 8px rgba(102,126,234,0.45);user-select:none;white-space:nowrap;margin-left:8px;transition:opacity 0.15s;';
    aiBtn.onmouseenter = () => {{ aiBtn.style.opacity='0.85'; }};
    aiBtn.onmouseleave = () => {{ aiBtn.style.opacity='1'; }};
    const toggle = (e) => {{ e.stopPropagation(); e.preventDefault(); _cardPanelOpen ? closeCardPanel() : openCardPanel(); }};
    aiBtn.addEventListener('click', toggle);
    aiBtn.addEventListener('keydown', e => {{ if(e.key==='Enter'||e.key===' ') toggle(e); }});
    footer.appendChild(aiBtn);
    _cardBtnParent = footer;
    _cardBtnInjected = true;
  }}

  function removeCardEditorButton() {{
    closeCardPanel();
    if (_cardBtnParent) {{
      const b = _cardBtnParent.querySelector('#' + CARD_BTN_ID);
      if (b) b.remove();
    }}
    _cardBtnInjected = false;
    _cardBtnParent = null;
  }}

  // ---- Automation page integrated sidebar + flow visualization ----
  const AMIRA_AUTO_BTN_ID   = 'amira-auto-toolbar-btn';
  const AMIRA_FLOW_TOGGLE_ID = 'amira-auto-flow-toggle-btn';
  const AMIRA_AUTO_BTN_GROUP_ID = 'amira-auto-toolbar-btn-group';
  const AMIRA_SIDEBAR_ID    = 'amira-auto-sidebar';
  const AMIRA_FLOW_ID       = 'amira-auto-flow';
  const AUTO_SESSION_KEY    = 'ha-claude-auto-session';
  let _autoSidebarOpen      = false;
  let _autoBtnInjected      = false;
  let _autoFlowInjected     = false;
  let _lastAutoPageId       = null;
  let _autoSidebarEl        = null;
  let _autoMsgsEl           = null;
  let _autoInputEl          = null;
  let _autoProvSel          = null;
  let _autoModSel           = null;
  let _autoAgentSel         = null;
  let _autoContentWrapper   = null;
  let _autoToolbarBtnEl     = null;
  let _autoFlowToggleBtnEl  = null;
  let _autoFlowEl           = null;
  let _autoFlowVisible      = loadSetting('auto-flow-visible', true);
  let _autoFlowStatus       = 'idle'; // idle | rendered | unavailable
  let _autoFlowUnavailableReason = '';
  let _autoFlowConfigSig    = '';
  let _autoFlowLastCheckTs  = 0;
  const AUTO_FLOW_REFRESH_MS = 4000;
  let _autoFlowRenderBusy   = false;

  function getAutoSessionId() {{
    let sid = null;
    try {{ sid = localStorage.getItem(AUTO_SESSION_KEY); }} catch(e) {{}}
    if (!sid) {{ sid = 'auto_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7); }}
    try {{ localStorage.setItem(AUTO_SESSION_KEY, sid); }} catch(e) {{}}
    return sid;
  }}
  function resetAutoSession() {{
    try {{ localStorage.removeItem(AUTO_SESSION_KEY); }} catch(e) {{}}
  }}

  // ---- Toolbar button injection (position:fixed on body — avoids Shadow DOM unreliability) ----
  function _autoToolbarBtnExists() {{
    if (_autoToolbarBtnEl && _autoToolbarBtnEl.isConnected) return true;
    if (document.getElementById(AMIRA_AUTO_BTN_ID)) return true;
    const toolbarContent = _findAutomationToolbarContent();
    return !!(toolbarContent && toolbarContent.querySelector('#' + AMIRA_AUTO_BTN_ID));
  }}

  function _findAutomationToolbarContent() {{
    try {{
      const toolbar = _findAutomationToolbar();
      if (!toolbar) return null;
      const root = toolbar.shadowRoot || toolbar;
      return root.querySelector('.toolbar-content')
          || root.querySelector('.toolbar')
          || root.querySelector('.main-title')
          || null;
    }} catch(e) {{ return null; }}
  }}

  function _getAutoToolbarButtonGroup(createIfMissing) {{
    const toolbarContent = _findAutomationToolbarContent();
    if (!toolbarContent) return null;
    let group = toolbarContent.querySelector ? toolbarContent.querySelector('#' + AMIRA_AUTO_BTN_GROUP_ID) : null;
    if (group || !createIfMissing) return group;
    group = document.createElement('div');
    group.id = AMIRA_AUTO_BTN_GROUP_ID;
    group.style.cssText = 'display:inline-flex;align-items:center;gap:8px;flex-shrink:0;margin-left:10px;';
    const toolbarIconSlot = toolbarContent.querySelector ? toolbarContent.querySelector('slot[name="toolbar-icon"]') : null;
    if (toolbarIconSlot && toolbarIconSlot.parentElement === toolbarContent) {{
      toolbarContent.insertBefore(group, toolbarIconSlot);
    }} else {{
      toolbarContent.appendChild(group);
    }}
    return group;
  }}

  function injectAutomationToolbarButton() {{
    if (_autoToolbarBtnExists()) {{ _autoBtnInjected = true; return; }}
    const toolbarContent = _findAutomationToolbarContent();
    if (!toolbarContent) return;
    const group = _getAutoToolbarButtonGroup(true);
    const wrapper = document.createElement('div');
    wrapper.id = AMIRA_AUTO_BTN_ID;
    // Native placement in the automation toolbar (same strategy as Flow button).
    const inlineStyle = 'display:inline-flex;align-items:center;cursor:pointer;padding:0 12px;height:32px;border-radius:16px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-size:13px;font-weight:600;gap:6px;user-select:none;white-space:nowrap;box-shadow:0 2px 8px rgba(102,126,234,0.35);transition:opacity 0.15s,transform 0.1s;line-height:1;flex-shrink:0;';
    wrapper.style.cssText = inlineStyle;
    wrapper.innerHTML = '<span style="font-size:15px;line-height:1;">&#129302;</span><span>Amira</span>';
    wrapper.onmouseenter = () => {{ wrapper.style.opacity='0.88'; wrapper.style.transform='translateY(-1px)'; }};
    wrapper.onmouseleave = () => {{ wrapper.style.opacity='1'; wrapper.style.transform=''; }};
    wrapper.addEventListener('click', (e) => {{
      e.stopPropagation(); e.preventDefault();
      _autoSidebarOpen ? closeAutomationSidebar() : openAutomationSidebar();
    }});
    // Place it inside a dedicated button group to avoid overlap.
    const title = toolbarContent.querySelector ? toolbarContent.querySelector('.main-title') : null;
    if (title && title.parentElement === toolbarContent) {{
      title.style.marginRight = 'auto';
    }}
    if (group) group.appendChild(wrapper);
    else toolbarContent.appendChild(wrapper);
    _autoToolbarBtnEl = wrapper;
    _autoBtnInjected = true;
  }}

  function _autoFlowToggleBtnExists() {{
    if (_autoFlowToggleBtnEl && _autoFlowToggleBtnEl.isConnected) return true;
    if (document.getElementById(AMIRA_FLOW_TOGGLE_ID)) return true;
    const toolbarContent = _findAutomationToolbarContent();
    return !!(toolbarContent && toolbarContent.querySelector('#' + AMIRA_FLOW_TOGGLE_ID));
  }}

  function _applyFlowVisibility() {{
    const flow = _findAutomationFlowEl();
    if (flow) flow.style.display = _autoFlowVisible ? '' : 'none';
    if (_autoFlowToggleBtnEl) {{
      _autoFlowToggleBtnEl.style.opacity = _autoFlowVisible ? '1' : '0.65';
      _autoFlowToggleBtnEl.textContent = _autoFlowVisible ? ('🧭 ' + tt('flow_on', 'Flow')) : ('🧭 ' + tt('flow_off', 'Flow off'));
    }}
  }}

  function injectAutomationFlowToggleButton() {{
    if (_autoFlowToggleBtnExists()) {{
      _applyFlowVisibility();
      return;
    }}
    const toolbarContent = _findAutomationToolbarContent();
    if (!toolbarContent) return;
    const group = _getAutoToolbarButtonGroup(true);
    const btn = document.createElement('div');
    btn.id = AMIRA_FLOW_TOGGLE_ID;
    btn.style.cssText = 'display:inline-flex;align-items:center;cursor:pointer;padding:0 10px;height:32px;border-radius:16px;background:linear-gradient(135deg,#e2e8f0,#cbd5e1);color:#1e293b;font-size:12px;font-weight:600;gap:6px;user-select:none;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.12);transition:opacity 0.15s,transform 0.1s;flex-shrink:0;';
    btn.onmouseenter = () => {{ btn.style.opacity='0.88'; btn.style.transform='translateY(-1px)'; }};
    btn.onmouseleave = () => {{ btn.style.opacity='1'; btn.style.transform=''; }};
    btn.addEventListener('click', (e) => {{
      e.stopPropagation(); e.preventDefault();
      _autoFlowVisible = !_autoFlowVisible;
      saveSetting('auto-flow-visible', _autoFlowVisible);
      if (_autoFlowVisible && !_findAutomationFlowEl()) {{
        if (_autoFlowStatus === 'unavailable') {{
          _renderFlowInfoMessage(_autoFlowUnavailableReason || tt('flow_unavailable', 'Flow unavailable for this automation.'));
        }} else if (_lastAutoPageId && _autoFlowStatus === 'idle') {{
          fetchAndRenderAutomationFlow(_lastAutoPageId, {{ showUnavailable: true }});
        }}
      }}
      _applyFlowVisibility();
    }});
    if (group) group.appendChild(btn);
    else toolbarContent.appendChild(btn);
    _autoFlowToggleBtnEl = btn;
    _applyFlowVisibility();
  }}

  function removeAutomationToolbarButton() {{
    if (_autoToolbarBtnEl && _autoToolbarBtnEl.remove) _autoToolbarBtnEl.remove();
    _autoToolbarBtnEl = null;
    const b = document.getElementById(AMIRA_AUTO_BTN_ID);
    if (b) b.remove();
    const toolbarContent = _findAutomationToolbarContent();
    if (toolbarContent) {{
      const sb = toolbarContent.querySelector('#' + AMIRA_AUTO_BTN_ID);
      if (sb) sb.remove();
      const fb = toolbarContent.querySelector('#' + AMIRA_FLOW_TOGGLE_ID);
      if (fb) fb.remove();
      const gb = toolbarContent.querySelector('#' + AMIRA_AUTO_BTN_GROUP_ID);
      if (gb) gb.remove();
    }}
    if (_autoFlowToggleBtnEl && _autoFlowToggleBtnEl.remove) _autoFlowToggleBtnEl.remove();
    _autoFlowToggleBtnEl = null;
    _autoBtnInjected = false;
  }}

  // ---- Flow visualization ----
  function _entityLabel(eid) {{
    if (!eid) return '';
    const raw = Array.isArray(eid) ? eid[0] : eid;
    if (!raw) return '';
    return String(raw).split('.').pop().replace(/_/g, ' ');
  }}

  function _normalizeEntityIds(v) {{
    const out = [];
    function pushOne(x) {{
      if (x === undefined || x === null) return;
      const s = String(x).trim();
      if (!s) return;
      if (s.includes(',')) {{
        s.split(',').forEach(part => pushOne(part));
        return;
      }}
      if (!out.includes(s)) out.push(s);
    }}
    if (Array.isArray(v)) v.forEach(pushOne);
    else pushOne(v);
    return out;
  }}

  function _nodeEntityIds(node, fallback) {{
    const fromNode = node && node.target && node.target.entity_id !== undefined
      ? node.target.entity_id
      : (node && node.entity_id !== undefined ? node.entity_id : fallback);
    return _normalizeEntityIds(fromNode);
  }}

  function _entityListText(ids, maxVisible) {{
    const arr = Array.isArray(ids) ? ids : [];
    if (!arr.length) return '';
    const m = Math.max(1, maxVisible || 2);
    const labels = arr.slice(0, m).map(_entityLabel).filter(Boolean);
    if (!labels.length) return '';
    if (arr.length <= m) return labels.join(', ');
    return labels.join(', ') + ' +' + (arr.length - m);
  }}

  function _formatDuration(delay) {{
    if (delay === null || delay === undefined) return '';
    if (typeof delay === 'number') return String(delay) + 's';
    if (typeof delay === 'string') {{
      const d = delay.trim();
      if (!d) return '';
      if (/^\\d+$/.test(d)) return d + 's';
      return d;
    }}
    if (typeof delay === 'object') {{
      const h = parseInt(delay.hours || 0, 10) || 0;
      const m = parseInt(delay.minutes || 0, 10) || 0;
      const s = parseInt(delay.seconds || 0, 10) || 0;
      const out = [];
      if (h) out.push(h + 'h');
      if (m) out.push(m + 'm');
      if (s) out.push(s + 's');
      return out.length ? out.join(' ') : '';
    }}
    return '';
  }}

  function _humanizeTimePattern(node) {{
    const parts = [];
    const mins = String(node.minutes || '').trim();
    const hours = String(node.hours || '').trim();
    const secs = String(node.seconds || '').trim();
    const minuteStep = mins.match(/^\\/(\\d+)$/);
    const hourStep = hours.match(/^\\/(\\d+)$/);
    const secStep = secs.match(/^\\/(\\d+)$/);

    if (minuteStep) parts.push('Ogni ' + minuteStep[1] + ' min');
    else if (hourStep) parts.push('Ogni ' + hourStep[1] + ' ore');
    else if (secStep) parts.push('Ogni ' + secStep[1] + ' sec');
    else if (mins && mins !== '*') parts.push('Al minuto ' + mins);
    else if (hours && hours !== '*') parts.push('All\\'ora ' + hours);
    else parts.push('Intervallo regolare');

    return parts.join(' ');
  }}

  function _humanizeService(service, entity, node) {{
    const svc = String(service || '');
    if (svc.startsWith('notify.')) {{
      const ch = svc.split('.').slice(1).join(' ').replace(/_/g, ' ').trim();
      return ch ? (tt('flow_notify', 'Notify') + ': ' + ch) : tt('flow_notify', 'Notify');
    }}
    const op = svc.split('.').pop();
    const ids = _nodeEntityIds(node || null, entity);
    const ent = _entityListText(ids, 2) || _entityLabel(entity);
    if (op === 'turn_on') return ent ? ('Accendi ' + ent) : 'Accendi';
    if (op === 'turn_off') return ent ? ('Spegni ' + ent) : 'Spegni';
    if (op === 'toggle') return ent ? ('Inverti ' + ent) : 'Inverti stato';
    if (op === 'open_cover') return ent ? ('Apri ' + ent) : 'Apri';
    if (op === 'close_cover') return ent ? ('Chiudi ' + ent) : 'Chiudi';
    const shortSvc = op ? op.replace(/_/g, ' ') : tt('flow_action_word', 'Action');
    return ent ? (shortSvc + ': ' + ent) : shortSvc;
  }}

  function _compactText(v, maxLen) {{
    if (v === undefined || v === null) return '';
    let s = String(v).replace(/\\s+/g, ' ').trim();
    // Humanize Jinja-like templates so users see readable intent, not raw syntax.
    s = s
      .replace(/\\u007b\\u007b\\s*trigger\\.event\\.data\\.([a-z0-9_]+)\\s*\\u007d\\u007d/gi, function(_, fld) {{
        return '[' + tt('flow_event', 'event') + ': ' + String(fld).replace(/_/g, ' ') + ']';
      }})
      .replace(/\\u007b\\u007b\\s*states\\('([^']+)'\\)\\s*\\u007d\\u007d/gi, function(_, eid) {{
        return '[' + tt('flow_state_word', 'state') + ' ' + _entityLabel(eid) + ']';
      }})
      .replace(/\\u007b\\u007b\\s*\\(\\s*states\\('([^']+)'\\)\\s*\\|\\s*int\\(0\\)\\s*\\)\\s*\\+\\s*1\\s*\\u007d\\u007d/gi, function(_, eid) {{
        return '[(' + _entityLabel(eid) + ') + 1]';
      }})
      .replace(/\\u007b%[\\s\\S]*?%\\u007d/g, '[' + tt('flow_template_logic', 'template logic') + ']')
      .replace(/\\u007b\\u007b[^\\u007d]+\\u007d\\u007d/g, '[' + tt('flow_dynamic_value', 'dynamic value') + ']');
    const dyn = '[' + tt('flow_dynamic_value', 'dynamic value') + ']';
    const tpl = '[' + tt('flow_template_logic', 'template logic') + ']';
    while (s.indexOf(dyn + dyn) !== -1) s = s.replaceAll(dyn + dyn, dyn);
    while (s.indexOf(dyn + ' ' + dyn) !== -1) s = s.replaceAll(dyn + ' ' + dyn, dyn);
    while (s.indexOf(tpl + tpl) !== -1) s = s.replaceAll(tpl + tpl, tpl);
    while (s.indexOf(tpl + ' ' + tpl) !== -1) s = s.replaceAll(tpl + ' ' + tpl, tpl);
    s = s.replace(/\\s+([,.;:!?])/g, '$1').trim();
    if (!s) return '';
    if (!maxLen || s.length <= maxLen) return s;
    return s.slice(0, Math.max(0, maxLen - 1)) + '…';
  }}

  function _humanizeStateValue(val, eid) {{
    const v = String(val || '').toLowerCase();
    const e = String(eid || '').toLowerCase();
    const isProblemLike = /error|fault|problem|alarm|allarme/.test(e);
    if (v === 'on') return isProblemLike ? tt('flow_problem', 'Problem') : 'ON';
    if (v === 'off') return isProblemLike ? tt('flow_no_problem', 'No problem') : 'OFF';
    return String(val || '');
  }}

  function _eventTriggerName(node, maxLen) {{
    if (!node || typeof node !== 'object') return '';
    const raw =
      node.event_type ||
      node.event ||
      node.event_name ||
      (node.event_data && (node.event_data.event_type || node.event_data.type || node.event_data.event)) ||
      (node.data && (node.data.event_type || node.data.event)) ||
      '';
    return _compactText(raw, maxLen || 72);
  }}

  function _humanizeFieldName(name) {{
    const f = String(name || '').trim();
    if (!f) return '';
    if (f === 'league_name') return 'campionato';
    if (f === 'home_team') return 'squadra casa';
    if (f === 'away_team') return 'squadra ospite';
    if (f === 'home_score') return 'gol casa';
    if (f === 'away_score') return 'gol ospite';
    if (f === 'goal_scorers_str') return 'marcatori';
    if (f === 'venue') return 'stadio';
    return f.replace(/_/g, ' ');
  }}

  function _templateBody(node) {{
    const raw = String((node && (node.value_template || node.template || node.value)) || '').trim();
    if (!raw) return '';
    return raw.replace(/^\\u007b\\u007b\\s*/, '').replace(/\\s*\\u007d\\u007d$/, '').trim();
  }}

  function _humanizeTemplateCondition(node, maxLen) {{
    const expr = _templateBody(node);
    if (!expr) return '';

    const eq = expr.match(/^trigger\\.event\\.data\\.([a-z0-9_]+)\\s*==\\s*['"]([^'"]+)['"]$/i);
    if (eq) {{
      const field = _humanizeFieldName(eq[1]);
      const val = _compactText(eq[2], 36);
      return tf('flow_template_if_equals', 'Only if {{field}} is {{value}}', {{ field: field, value: val }});
    }}
    const ne = expr.match(/^trigger\\.event\\.data\\.([a-z0-9_]+)\\s*!=\\s*['"]([^'"]+)['"]$/i);
    if (ne) {{
      const field = _humanizeFieldName(ne[1]);
      const val = _compactText(ne[2], 36);
      return tf('flow_template_if_not_equals', 'Only if {{field}} is not {{value}}', {{ field: field, value: val }});
    }}
    if (/trigger\\.event\\.data\\./i.test(expr)) {{
      return tt('flow_template_event_check', 'Custom check on event data');
    }}
    return _compactText(expr, maxLen || 120);
  }}

  function _describeFlowNode(node, type) {{
    if (!node || typeof node !== 'object') return '';
    if (type === 'trigger') {{
      const p = node.platform || node.trigger || '';
      const eid = node.entity_id || '';
      if (p === 'time_pattern') return _humanizeTimePattern(node);
      if (p === 'state' && eid) {{
        if (node.to !== undefined && node.to !== null && String(node.to) !== '') {{
          return tf('flow_when_equals', 'When state matches', {{ entity: _entityLabel(eid), value: _humanizeStateValue(node.to, eid) }});
        }}
        return tf('flow_change', 'State change', {{ entity: _entityLabel(eid) }});
      }}
      if (p === 'time') return node.at ? ('Alle ' + node.at) : 'A orario';
      if (p === 'mqtt') return node.topic ? ('MQTT ' + node.topic) : 'MQTT';
      if (p === 'sun') return (node.event || 'sun') + ' ' + (node.offset || '');
      if (p === 'homeassistant') return 'HA ' + (node.event || 'start');
      if (p === 'event') {{
        const ev = _eventTriggerName(node, 56);
        return ev ? tf('flow_event_named', 'Event: {{value}}', {{ value: ev }}) : tt('flow_event_generic', 'Event');
      }}
      if (p === 'numeric_state' && eid) return 'Valore: ' + _entityLabel(eid);
      if (p === 'zone' && eid) return 'Zona: ' + _entityLabel(eid);
      if (p === 'template') return tt('flow_template_condition', 'Template condition');
      if (p === 'webhook') return 'webhook';
      if (p === 'device' && node.device_id) {{
        const subj = _compactText(node.__subject || '', 40);
        const typ = String(node.type || '').toLowerCase();
        if (subj && /problem|fault|error|alarm|allarme/.test(typ)) {{
          return tf('flow_problem_subject', 'Problem: {{value}}', {{ value: subj }});
        }}
        return (node.type || tt('flow_trigger_device_generic', 'Device trigger')).replace(/_/g, ' ');
      }}
      if (eid) return _entityLabel(eid);
      return p ? p.replace(/_/g, ' ') : 'trigger';
    }}
    if (type === 'condition') {{
      const c = node.condition || '';
      const eid = node.entity_id || '';
      if (c === 'state' && eid) return _entityLabel(eid) + (node.state ? (' = ' + node.state) : '');
      if (c === 'sun') return 'Cond. sole';
      if (c === 'time') {{
        if (node.after && node.before) return node.after + ' - ' + node.before;
        if (node.after) return 'Dopo ' + node.after;
        if (node.before) return 'Prima di ' + node.before;
        return tt('flow_time_window', 'Time window');
      }}
      if (c === 'numeric_state' && eid) return 'Soglia: ' + _entityLabel(eid);
      if (c === 'template') {{
        const tpl = _humanizeTemplateCondition(node, 68);
        return tpl ? tf('flow_template_condition_short', 'Template: {{value}}', {{ value: tpl }}) : tt('flow_template_condition', 'Template condition');
      }}
      if (c === 'zone') return 'zone';
      if (c === 'and' || c === 'or' || c === 'not') return c.toUpperCase();
      if (eid) return _entityLabel(eid);
      return c ? c.replace(/_/g, ' ') : 'condition';
    }}
    if (type === 'action') {{
      const svc = node.service || node.action || '';
      const eid = (node.target && node.target.entity_id) || node.entity_id || '';
      if (svc) return _humanizeService(svc, eid, node);
      if (node.delay) {{
        const d = _formatDuration(node.delay);
        return d ? (tt('flow_wait', 'Wait') + ' ' + d) : tt('flow_wait', 'Wait');
      }}
      if (node.wait_template) return tt('flow_template_condition', 'Template condition');
      if (node.choose) return 'choose';
      if (node.repeat) return 'repeat';
      if (node.if) return 'if/then';
      if (node.scene) return 'scene: ' + (node.scene.split('.').pop() || '');
      if (node.event) return tf('flow_event_named', 'Event: {{value}}', {{ value: node.event }});
      return 'action';
    }}
    return '';
  }}

  function _flowIcon(type) {{
    if (type === 'trigger') return '\U0001f514';
    if (type === 'condition') return '\U0001f550';
    if (type === 'action') return '\U0001f4a1';
    return '\u2699\ufe0f';
  }}

  function _flowGradient(type) {{
    if (type === 'trigger') return 'linear-gradient(135deg,#e3f2fd,#bbdefb)';
    if (type === 'condition') return 'linear-gradient(135deg,#fff8e1,#ffecb3)';
    if (type === 'action') return 'linear-gradient(135deg,#e8f5e9,#c8e6c9)';
    return 'linear-gradient(135deg,#f5f5f5,#e0e0e0)';
  }}

  function _flowBorderColor(type) {{
    if (type === 'trigger') return '#90caf9';
    if (type === 'condition') return '#ffe082';
    if (type === 'action') return '#a5d6a7';
    return '#bdbdbd';
  }}

  function _describeFlowDetail(node, type) {{
    if (!node || typeof node !== 'object') return '';
    if (type === 'trigger') {{
      const p = node.platform || node.trigger || '';
      if (p === 'time_pattern') return tf('flow_cyclic_execution', 'Cyclic execution', {{ value: _humanizeTimePattern(node) }});
      if (p === 'state') {{
        const e = _entityLabel(node.entity_id) || 'entita';
        const from = (node.from !== undefined && String(node.from) !== '') ? _humanizeStateValue(node.from, node.entity_id) : '';
        const to = (node.to !== undefined && String(node.to) !== '') ? _humanizeStateValue(node.to, node.entity_id) : '';
        if (from && to) return tf('flow_change_from_to', 'State change', {{ entity: e, from: from, to: to }});
        if (to) return tf('flow_becomes', 'Starts on state', {{ entity: e, value: to }});
        return tf('flow_starts_when', 'Starts on state change', {{ entity: e }});
      }}
      if (p === 'time') return node.at ? tf('flow_after', 'After', {{ value: node.at }}) : tt('flow_starts_fixed_time', 'Starts at a fixed time');
      if (p === 'numeric_state') return tt('flow_starts_above_threshold', 'Starts when a numeric threshold is crossed');
      if (p === 'event') {{
        const ev = _eventTriggerName(node, 120);
        return ev ? tf('flow_trigger_event_when', 'When event {{value}} fires', {{ value: ev }}) : tt('flow_trigger_event_generic', 'Triggered by event');
      }}
      if (p === 'device') {{
        const subj = _compactText(node.__subject || '', 56);
        const typ = String(node.type || '').toLowerCase();
        if (subj && /problem|fault|error|alarm|allarme/.test(typ)) {{
          return tf('flow_trigger_device_problem', 'When {{value}} reports a problem', {{ value: subj }});
        }}
        return tt('flow_trigger_device_generic', 'Device trigger');
      }}
      return tf('flow_trigger_prefix', 'Trigger', {{ value: (p || tt('flow_event', 'event')) }});
    }}
    if (type === 'condition') {{
      const c = node.condition || '';
      if (c === 'time') {{
        const after = node.after || '';
        const before = node.before || '';
        if (after && before) return tf('flow_valid_between', 'Valid between', {{ from: after, to: before }});
        if (after) return tf('flow_valid_after', 'Valid after', {{ value: after }});
        if (before) return tf('flow_valid_before', 'Valid before', {{ value: before }});
      }}
      if (c === 'state') return tf('flow_check_state_of', 'Checks state', {{ entity: (_entityLabel(node.entity_id) || 'entity') }});
      if (c === 'numeric_state') return tf('flow_check_threshold_of', 'Checks threshold', {{ entity: (_entityLabel(node.entity_id) || 'entity') }});
      if (c === 'template') {{
        const tpl = _humanizeTemplateCondition(node, 180);
        return tpl ? tf('flow_template_eval', 'Evaluates template: {{value}}', {{ value: tpl }}) : tt('flow_template_condition', 'Template condition');
      }}
      return tf('flow_condition_prefix', 'Condition', {{ value: (c || tt('flow_verify', 'check')) }});
    }}
    if (type === 'action') {{
      const svc = node.service || node.action || '';
      const eid = (node.target && node.target.entity_id) || node.entity_id || '';
      if (svc) {{
        const svcMeta = ' · ' + tt('flow_service', 'service') + ': ' + String(svc);
        if (String(svc).startsWith('notify.')) {{
          const rawTitle = String((node.data && node.data.title) || '');
          const rawMsg = String((node.data && node.data.message) || '');
          const hasTemplate = /\\u007b\\u007b|\\u007b%/.test(rawTitle + ' ' + rawMsg);
          const isMatchSummary = /home_team|away_team|home_score|away_score|goal_scorers_str|venue/i.test(rawMsg);
          const title = _compactText(node.data && node.data.title, 64);
          const msg = _compactText(node.data && node.data.message, 180);
          let body = '';
          if (title) body = title;
          if (isMatchSummary) body += (body ? '\\n' : '') + tt('flow_notify_match_summary', 'final score with teams, score, scorers and venue');
          else if (msg) body += (body ? '\\n' : '') + msg;
          else if (hasTemplate) body += (body ? '\\n' : '') + tt('flow_dynamic_message', 'dynamic message');
          let out = tt('flow_notify', 'Notify') + ':';
          if (body) out += ' ' + body;
          out += '\\n' + tt('flow_service', 'service') + ': ' + String(svc);
          return out;
        }}
        if (svc === 'input_number.set_value' || svc === 'number.set_value') {{
          const targetName = _entityLabel(eid) || 'valore';
          const val = _compactText(node.data && node.data.value, 90);
          if (val) return tt('flow_set', 'Set') + ' ' + targetName + ' = ' + val + svcMeta;
          return tt('flow_set_value_of', 'Set value of') + ' ' + targetName + svcMeta;
        }}
        const base = tt('flow_action_word', 'Action') + ': ' + _humanizeService(svc, eid, node);
        const data = node.data && typeof node.data === 'object' ? node.data : null;
        const ids = _nodeEntityIds(node, eid);
        const entityBlock = ids.length > 1
          ? ('\\n' + tt('flow_entities', 'entities') + ':\\n' + ids.map(v => ('• ' + _entityLabel(v))).join('\\n'))
          : '';
        if (!data) return base + svcMeta;
        const bits = [];
        if (data.brightness !== undefined && data.brightness !== null && String(data.brightness) !== '') {{
          bits.push(tt('flow_brightness', 'brightness') + ' ' + String(data.brightness));
        }}
        if (data.xy_color !== undefined && data.xy_color !== null) {{
          const xyRaw = String(data.xy_color);
          const hasRandom = /\\|\\s*random|random/i.test(xyRaw);
          const hasTpl = (xyRaw.indexOf(String.fromCharCode(123) + String.fromCharCode(123)) !== -1)
            || (xyRaw.indexOf(String.fromCharCode(123) + '%') !== -1);
          if (hasRandom || hasTpl) bits.push(tt('flow_random_color', 'random color'));
          else bits.push('xy ' + _compactText(xyRaw, 44));
        }}
        if (data.rgb_color !== undefined && data.rgb_color !== null) {{
          bits.push('rgb ' + _compactText(data.rgb_color, 32));
        }}
        if (!bits.length) return base + svcMeta + entityBlock;
        return base + ' (' + tt('flow_data', 'data') + ': ' + bits.join(', ') + ')' + svcMeta + entityBlock;
      }}
      if (node.delay) {{
        const d = _formatDuration(node.delay);
        return d ? tf('flow_wait_for', 'Wait for {{value}}', {{ value: d }}) : tt('flow_wait', 'Wait');
      }}
      if (node.data && (node.data.message || node.data.title)) {{
        const title = _compactText(node.data.title, 64);
        const msg = _compactText(node.data.message, 180);
        return (title ? (title + ' — ') : '') + (msg || tt('flow_with_message', 'Action with message'));
      }}
      return tt('flow_automation_action', 'Automation action');
    }}
    return '';
  }}

  function _humanizeConditionOne(c) {{
    if (!c || typeof c !== 'object') return 'condizione';
    const t = c.condition || '';
    if (t === 'numeric_state') {{
      const n = _entityLabel(c.entity_id) || 'valore';
      const low = c.above !== undefined ? (' > ' + c.above) : '';
      const high = c.below !== undefined ? (' < ' + c.below) : '';
      return n + low + high;
    }}
    if (t === 'state') {{
      const n = _entityLabel(c.entity_id) || 'entita';
      return n + (c.state !== undefined ? (' = ' + c.state) : '');
    }}
    if (t === 'time') {{
      if (c.after && c.before) return c.after + ' - ' + c.before;
      if (c.after) return tf('flow_after', 'After', {{ value: c.after }});
      if (c.before) return tf('flow_before', 'Before', {{ value: c.before }});
      return 'fascia oraria';
    }}
    return t ? String(t).replace(/_/g, ' ') : 'condizione';
  }}

  function _expandActionNodes(actions) {{
    const out = [];
    let _branchCounter = 0;
    function _nextBranchId() {{
      _branchCounter += 1;
      return _branchCounter;
    }}

    function pushAction(node, branchLabel, detailLabel, branchId) {{
      if (!node || typeof node !== 'object') return;
      const clone = Object.assign({{}}, node);
      if (branchLabel) clone.__branch = branchLabel;
      if (detailLabel) clone.__detail = detailLabel;
      if (branchId) clone.__branchId = branchId;
      out.push(clone);
    }}

    function walk(list, branchLabel, branchId) {{
      if (!Array.isArray(list)) return;
      list.forEach((node) => {{
        if (!node || typeof node !== 'object') return;
        if (Array.isArray(node.choose) && node.choose.length) {{
          node.choose.forEach((ch, idx) => {{
            const conds = Array.isArray(ch.conditions) ? ch.conditions : (ch.conditions ? [ch.conditions] : []);
            const condTxt = conds.length ? conds.map(_humanizeConditionOne).join(' & ') : 'condizione';
            const label = tf('flow_if', 'If', {{ value: condTxt }});
            const bid = _nextBranchId();
            pushAction({{ action: '__branch__', __kind: 'branch_marker' }}, label, tf('flow_branch_choose', 'Choose branch', {{ index: (idx + 1) }}), bid);
            const seq = Array.isArray(ch.sequence) ? ch.sequence : (ch.sequence ? [ch.sequence] : []);
            walk(seq, label, bid);
          }});
          if (Array.isArray(node.default) && node.default.length) {{
            const defLabel = tt('flow_else', 'Else');
            const bid = _nextBranchId();
            pushAction({{ action: '__branch__', __kind: 'branch_marker' }}, defLabel, tt('flow_branch_default', 'Choose default branch'), bid);
            walk(node.default, defLabel, bid);
          }}
          return;
        }}
        if (node.if) {{
          const ifConds = Array.isArray(node.if) ? node.if : [node.if];
          const ifTxt = ifConds.map(_humanizeConditionOne).join(' & ') || 'condizione';
          const ifLabel = tf('flow_if', 'If', {{ value: ifTxt }});
          const thenBid = _nextBranchId();
          pushAction({{ action: '__branch__', __kind: 'branch_marker' }}, ifLabel, tf('flow_if', 'If', {{ value: ifTxt }}), thenBid);
          walk(Array.isArray(node.then) ? node.then : (node.then ? [node.then] : []), ifLabel, thenBid);
          if (Array.isArray(node.else) && node.else.length) {{
            const elseLabel = tt('flow_else', 'Else');
            const elseBid = _nextBranchId();
            pushAction({{ action: '__branch__', __kind: 'branch_marker' }}, elseLabel, tt('flow_else', 'Else'), elseBid);
            walk(node.else, elseLabel, elseBid);
          }}
          return;
        }}
        if (node.repeat && typeof node.repeat === 'object') {{
          const rep = node.repeat;
          let repLabel = 'repeat';
          if (Array.isArray(rep.while) && rep.while.length) {{
            const whileTxt = rep.while.map(_humanizeConditionOne).join(' & ');
            repLabel = tf('flow_repeat_while', 'Repeat while {{value}}', {{ value: whileTxt || tt('flow_verify', 'check') }});
          }} else if (rep.count !== undefined && rep.count !== null && String(rep.count) !== '') {{
            repLabel = tf('flow_repeat_count', 'Repeat {{value}} times', {{ value: String(rep.count) }});
          }} else if (Array.isArray(rep.for_each) || rep.for_each !== undefined) {{
            repLabel = tt('flow_repeat_foreach', 'Repeat for each item');
          }} else if (Array.isArray(rep.until) && rep.until.length) {{
            const untilTxt = rep.until.map(_humanizeConditionOne).join(' & ');
            repLabel = tf('flow_repeat_until', 'Repeat until {{value}}', {{ value: untilTxt || tt('flow_verify', 'check') }});
          }}
          const bid = _nextBranchId();
          pushAction({{ action: '__branch__', __kind: 'branch_marker' }}, repLabel, tt('flow_repeat_branch', 'Loop branch'), bid);
          const repSeq = Array.isArray(rep.sequence) ? rep.sequence : (rep.sequence ? [rep.sequence] : []);
          walk(repSeq, repLabel, bid);
          return;
        }}
        pushAction(node, branchLabel, '', branchId);
      }});
    }}

    walk(actions, '', 0);
    return out;
  }}

  function _formatLastTriggered(ts) {{
    if (!ts) return '';
    try {{
      const d = new Date(ts);
      if (isNaN(d.getTime())) return String(ts);
      return d.toLocaleString('it-IT', {{
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }});
    }} catch(e) {{
      return String(ts);
    }}
  }}

  function _relativeLastTriggered(ts) {{
    if (!ts) return '';
    try {{
      const d = new Date(ts);
      if (isNaN(d.getTime())) return '';
      const diffMs = Date.now() - d.getTime();
      if (!isFinite(diffMs) || diffMs < 0) return '';
      const sec = Math.round(diffMs / 1000);
      const localeMap = {{ it: 'it-IT', en: 'en-US', es: 'es-ES', fr: 'fr-FR' }};
      const loc = localeMap[UI_LANG] || 'en-US';
      const rtf = new Intl.RelativeTimeFormat(loc, {{ numeric: 'auto' }});
      if (sec < 90) return rtf.format(-sec, 'second');
      const min = Math.round(sec / 60);
      if (min < 90) return rtf.format(-min, 'minute');
      const hr = Math.round(min / 60);
      if (hr < 48) return rtf.format(-hr, 'hour');
      const day = Math.round(hr / 24);
      return rtf.format(-day, 'day');
    }} catch(e) {{
      return '';
    }}
  }}

  function _inferAutomationSubject(config) {{
    try {{
      const raw = String((config && (config.alias || config.name)) || '').trim();
      if (!raw) return '';
      let s = raw.split('|')[0].split('—')[0].split('-')[0].trim();
      if (!s) s = raw;
      s = s.replace(/\\bamira\\b/ig, '').replace(/\\s+/g, ' ').trim();
      return s;
    }} catch(e) {{
      return '';
    }}
  }}

  async function _fetchAutomationLastTriggered(automationId, token, config) {{
    if (!token || !automationId) return '';
    const candidates = [];
    if (String(automationId).startsWith('automation.')) candidates.push(String(automationId));
    else candidates.push('automation.' + String(automationId));
    candidates.push(String(automationId));
    if (config && config.id) {{
      const cid = String(config.id);
      if (cid.startsWith('automation.')) candidates.push(cid);
      else candidates.push('automation.' + cid);
      candidates.push(cid);
    }}
    if (config && config.alias) {{
      const slug = String(config.alias).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
      if (slug) candidates.push('automation.' + slug);
    }}
    for (const ent of candidates) {{
      try {{
        const r = await fetch('/api/states/' + encodeURIComponent(ent), {{
          headers: {{ 'Authorization': 'Bearer ' + token }}
        }});
        if (!r.ok) continue;
        const st = await r.json();
        const lt = st && st.attributes ? st.attributes.last_triggered : '';
        if (lt) return lt;
      }} catch(e) {{}}
    }}
    // Fallback: find automation state by attribute id/friendly_name.
    try {{
      const rs = await fetch('/api/states', {{
        headers: {{ 'Authorization': 'Bearer ' + token }}
      }});
      if (rs.ok) {{
        const all = await rs.json();
        if (Array.isArray(all)) {{
          const wantedId = String(automationId || '');
          const wantedAlias = String((config && config.alias) || '').trim();
          for (const st of all) {{
            if (!st || typeof st !== 'object') continue;
            const eid = String(st.entity_id || '');
            if (!eid.startsWith('automation.')) continue;
            const attrs = st.attributes || {{}};
            const attrId = attrs.id !== undefined && attrs.id !== null ? String(attrs.id) : '';
            const fname = String(attrs.friendly_name || '').trim();
            if ((attrId && attrId === wantedId) || (wantedAlias && fname && fname === wantedAlias)) {{
              const lt = attrs.last_triggered || '';
              if (lt) return lt;
            }}
          }}
        }}
      }}
    }} catch(e) {{}}
    return '';
  }}

  async function _fetchAutomationEnabledState(automationId, token, config) {{
    if (!token || !automationId) return '';
    const candidates = [];
    if (String(automationId).startsWith('automation.')) candidates.push(String(automationId));
    else candidates.push('automation.' + String(automationId));
    candidates.push(String(automationId));
    if (config && config.id) {{
      const cid = String(config.id);
      if (cid.startsWith('automation.')) candidates.push(cid);
      else candidates.push('automation.' + cid);
      candidates.push(cid);
    }}
    if (config && config.alias) {{
      const slug = String(config.alias).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
      if (slug) candidates.push('automation.' + slug);
    }}
    for (const ent of candidates) {{
      try {{
        const r = await fetch('/api/states/' + encodeURIComponent(ent), {{
          headers: {{ 'Authorization': 'Bearer ' + token }}
        }});
        if (!r.ok) continue;
        const st = await r.json();
        const s = String(st && st.state || '').toLowerCase();
        if (s === 'on' || s === 'off') return s;
      }} catch(e) {{}}
    }}
    return '';
  }}

  function _findAutomationFlowHost() {{
    // Prefer the container div around the automation editor.
    try {{
      const wrap = _findAutomationContentWrapper();
      if (wrap) return wrap;
    }} catch(e) {{}}
    try {{
      const subpage = _findAutomationSubpage();
      if (!subpage) return null;
      const root = subpage.shadowRoot || subpage;
      const editor = root.querySelector('manual-automation-editor');
      if (editor && editor.parentElement) return editor.parentElement;
    }} catch(e) {{}}
    return null;
  }}

  function _findAutomationFlowEl() {{
    if (_autoFlowEl && _autoFlowEl.isConnected) return _autoFlowEl;
    const byDoc = document.getElementById(AMIRA_FLOW_ID);
    if (byDoc) {{
      _autoFlowEl = byDoc;
      return byDoc;
    }}
    const host = _findAutomationFlowHost();
    if (host && host.querySelector) {{
      const inHost = host.querySelector('#' + AMIRA_FLOW_ID);
      if (inHost) {{
        _autoFlowEl = inHost;
        return inHost;
      }}
    }}
    return null;
  }}

  function _removeAllAutomationFlowEls() {{
    try {{
      const nodes = document.querySelectorAll('#' + AMIRA_FLOW_ID);
      nodes.forEach(n => {{ try {{ n.remove(); }} catch(e) {{}} }});
    }} catch(e) {{}}
    try {{
      const host = _findAutomationFlowHost();
      if (host && host.querySelectorAll) {{
        const inHost = host.querySelectorAll('#' + AMIRA_FLOW_ID);
        inHost.forEach(n => {{ try {{ n.remove(); }} catch(e) {{}} }});
      }}
    }} catch(e) {{}}
    _autoFlowEl = null;
  }}

  function _renderFlowInfoMessage(msg) {{
    const host = _findAutomationFlowHost();
    if (!host) return;
    _removeAllAutomationFlowEls();
    const flowEl = document.createElement('div');
    flowEl.id = AMIRA_FLOW_ID;
    flowEl.style.cssText = 'position:relative;z-index:2;display:flex;align-items:center;justify-content:center;padding:10px 12px;background:linear-gradient(to right,#f0f4ff,#fafafa);border:1px solid #7c8fff;border-radius:10px;min-height:56px;box-shadow:0 2px 8px rgba(0,0,0,0.08);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:8px 0 10px;color:var(--secondary-text-color,#64748b);font-size:12px;text-align:center;';
    flowEl.textContent = msg || T.flow_no_data;
    host.prepend(flowEl);
    _autoFlowEl = flowEl;
    _applyFlowVisibility();
  }}

  async function fetchAndRenderAutomationFlow(automationId, opts) {{
    if (_autoFlowRenderBusy) return;
    _autoFlowRenderBusy = true;
    try {{
    const showUnavailable = !!(opts && opts.showUnavailable);
    const refresh = !!(opts && opts.refresh);
    const existingFlow = _findAutomationFlowEl();
    // Global dedup — prevents double-render on rapid polling ticks
    if (existingFlow && !refresh) {{ _autoFlowInjected = true; return; }}
    _autoFlowInjected = true;  // set early to block re-entry during async fetch

    const flowEl = document.createElement('div');
    flowEl.id = AMIRA_FLOW_ID;
    // Render inside the automation editor container (not as a fixed top overlay).
    flowEl.style.cssText = 'position:relative;z-index:2;display:flex;flex-direction:column;align-items:stretch;gap:8px;padding:10px 12px;background:linear-gradient(to right,#f0f4ff,#fafafa);border:1px solid #7c8fff;border-radius:10px;min-height:56px;box-shadow:0 2px 8px rgba(0,0,0,0.08);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:8px 0 10px;';
    if (!document.getElementById('amira-flow-anim-style')) {{
      const st = document.createElement('style');
      st.id = 'amira-flow-anim-style';
      st.textContent = '@keyframes amiraFlowIn{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:1;transform:translateY(0)}}}}';
      document.head.appendChild(st);
    }}

    // Fetch automation config
    try {{
      const token = _getHassToken();
      if (!token) {{
        flowEl.innerHTML = '<span style="font-size:12px;color:#999;">' + T.flow_no_data + '</span>';
        const host = _findAutomationFlowHost();
        if (host) host.prepend(flowEl);
        else document.body.appendChild(flowEl);
        return;
      }}
      const resp = await fetch('/api/config/automation/config/' + encodeURIComponent(automationId), {{
        headers: {{ 'Authorization': 'Bearer ' + token }}
      }});
      if (!resp.ok) {{
        let msg = T.flow_no_data;
        if (resp.status === 404 || resp.status === 400) {{
          msg = tt('flow_unavailable_migrate', 'Flow unavailable: automation has no ID or config API is not accessible. Try Migrate.');
        }}
        _autoFlowStatus = 'unavailable';
        _autoFlowUnavailableReason = msg;
        _autoFlowInjected = true; // avoid retry loop
        if (showUnavailable) _renderFlowInfoMessage(msg);
        return;
      }}
      const rawConfig = await resp.json();
      const config = Array.isArray(rawConfig)
        ? (rawConfig[0] || {{}})
        : ((rawConfig && (rawConfig.config || rawConfig.automation)) || rawConfig || {{}});
      const configSig = JSON.stringify(config || {{}});
      if (refresh && existingFlow && _autoFlowConfigSig && _autoFlowConfigSig === configSig) {{
        _autoFlowStatus = 'rendered';
        _autoFlowUnavailableReason = '';
        _autoFlowInjected = true;
        return;
      }}
      const lastTriggered = await _fetchAutomationLastTriggered(automationId, token, config);
      const automationEnabledState = await _fetchAutomationEnabledState(automationId, token, config);

      const _trRaw = (config.trigger !== undefined) ? config.trigger : config.triggers;
      const _coRaw = (config.condition !== undefined) ? config.condition : config.conditions;
      const _acRaw = (config.action !== undefined) ? config.action : (config.actions !== undefined ? config.actions : config.sequence);
      const triggers = Array.isArray(_trRaw) ? _trRaw : (_trRaw ? [_trRaw] : []);
      const flowSubject = _inferAutomationSubject(config);
      const flowTriggers = triggers.map(t => {{
        if (!t || typeof t !== 'object') return t;
        const c = Object.assign({{}}, t);
        if (flowSubject) c.__subject = flowSubject;
        return c;
      }});
      const conditions = Array.isArray(_coRaw) ? _coRaw : (_coRaw ? [_coRaw] : []);
      const actions = Array.isArray(_acRaw) ? _acRaw : (_acRaw ? [_acRaw] : []);
      const expandedActions = _expandActionNodes(actions);

      const branchColors = ['#60a5fa', '#34d399', '#f59e0b', '#a78bfa', '#f472b6'];

      function makeBubble(node, type, label) {{
        const bubble = document.createElement('div');
        const isBranchMarker = (type === 'action' && node && node.__kind === 'branch_marker');
        const desc = isBranchMarker
          ? (node.__branch || _describeFlowNode(node, type))
          : _describeFlowNode(node, type);
        const detail = isBranchMarker
          ? (node.__detail || desc || label)
          : (_describeFlowDetail(node, type) || desc || label);
        const bColor = (type === 'action' && node && node.__branchId)
          ? branchColors[(node.__branchId - 1) % branchColors.length]
          : _flowBorderColor(type);
        const bg = (type === 'action' && node && node.__kind === 'branch_marker')
          ? 'linear-gradient(135deg,#eef2ff,#e0e7ff)'
          : _flowGradient(type);
        bubble.style.cssText = 'display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:12px;background:' + bg + ';border:1.5px solid ' + bColor + ';font-size:12px;white-space:nowrap;max-width:320px;overflow:hidden;text-overflow:ellipsis;flex-shrink:0;box-shadow:0 1px 4px rgba(0,0,0,0.08);cursor:pointer;transition:transform .14s ease,box-shadow .14s ease;';
        bubble.title = detail;
        const iconSpan = document.createElement('span');
        iconSpan.style.cssText = 'font-size:16px;flex-shrink:0;';
        iconSpan.textContent = isBranchMarker ? '⑂' : _flowIcon(type);
        const textSpan = document.createElement('span');
        textSpan.style.cssText = 'overflow:hidden;text-overflow:ellipsis;color:var(--primary-text-color,#333);font-weight:500;';
        textSpan.textContent = desc || label;
        textSpan.title = desc || label;
        bubble.appendChild(iconSpan);
        bubble.appendChild(textSpan);
        bubble.addEventListener('mouseenter', () => {{ bubble.style.transform = 'translateY(-1px)'; bubble.style.boxShadow = '0 3px 8px rgba(0,0,0,0.14)'; }});
        bubble.addEventListener('mouseleave', () => {{ bubble.style.transform = ''; bubble.style.boxShadow = '0 1px 4px rgba(0,0,0,0.08)'; }});
        bubble.addEventListener('click', () => {{
          if (detailInfo.style.display === 'block' && detailInfo.textContent === detail) {{
            detailInfo.style.display = 'none';
            return;
          }}
          detailInfo.textContent = detail;
          detailInfo.style.display = 'block';
        }});
        return bubble;
      }}

      function makeArrow(sym) {{
        const arrow = document.createElement('span');
        arrow.style.cssText = 'color:var(--secondary-text-color,#999);font-size:18px;flex-shrink:0;font-weight:bold;';
        arrow.textContent = sym || '\u2192';
        return arrow;
      }}

      function makeSectionLabel(text) {{
        const lbl = document.createElement('span');
        lbl.style.cssText = 'font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--secondary-text-color,#999);writing-mode:horizontal-tb;flex-shrink:0;margin-right:-2px;';
        lbl.textContent = text;
        return lbl;
      }}

      const detailInfo = document.createElement('div');
      detailInfo.style.cssText = 'display:none;align-self:center;text-align:center;margin:4px auto 0;padding:6px 10px;border-radius:8px;border:1px dashed #8da2ff;background:#f7f9ff;color:#334155;font-size:11px;white-space:pre-line;max-width:760px;line-height:1.35;';

      const ltInfo = document.createElement('div');
      const ltActiveStyle = (automationEnabledState === 'on')
        ? 'border:1px solid #86efac;background:#dcfce7;color:#14532d;'
        : 'border:1px solid #c7d2fe;background:#eef2ff;color:#334155;';
      ltInfo.style.cssText = 'display:inline-flex;align-items:center;padding:6px 10px;border-radius:8px;' + ltActiveStyle + 'font-size:11px;white-space:nowrap;flex-shrink:0;margin-right:4px;';
      const absTs = lastTriggered ? _formatLastTriggered(lastTriggered) : tt('flow_never', 'Never');
      const relTs = lastTriggered ? _relativeLastTriggered(lastTriggered) : '';
      ltInfo.textContent = tt('flow_last_triggered', 'Last triggered') + ': ' + absTs + (relTs ? (' (' + relTs + ')') : '');
      flowEl.appendChild(ltInfo);

      const topBlock = document.createElement('div');
      topBlock.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:6px;';

      // Trigger block (label above bubble)
      if (flowTriggers.length) {{
        const trLabel = document.createElement('div');
        trLabel.textContent = (T.flow_trigger || 'Trigger').toUpperCase();
        trLabel.style.cssText = 'font-size:10px;font-weight:700;letter-spacing:1px;color:var(--secondary-text-color,#64748b);text-align:center;';
        topBlock.appendChild(trLabel);

        const trRow = document.createElement('div');
        trRow.style.cssText = 'display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;';
        flowTriggers.forEach((t, i) => {{
          if (i > 0) {{ const plus = document.createElement('span'); plus.textContent = '+'; plus.style.cssText = 'color:var(--secondary-text-color,#999);font-size:14px;flex-shrink:0;'; trRow.appendChild(plus); }}
          trRow.appendChild(makeBubble(t, 'trigger', T.flow_trigger));
        }});
        topBlock.appendChild(trRow);
      }}

      // Conditions block (below trigger)
      if (conditions.length) {{
        const down = document.createElement('div');
        down.textContent = '↓';
        down.style.cssText = 'font-size:16px;color:var(--secondary-text-color,#94a3b8);line-height:1;';
        topBlock.appendChild(down);

        const coLabel = document.createElement('div');
        coLabel.textContent = (T.flow_condition || 'Condition').toUpperCase();
        coLabel.style.cssText = 'font-size:10px;font-weight:700;letter-spacing:1px;color:var(--secondary-text-color,#64748b);text-align:center;';
        topBlock.appendChild(coLabel);

        const coRow = document.createElement('div');
        coRow.style.cssText = 'display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;';
        conditions.forEach((c, i) => {{
          if (i > 0) {{ const plus = document.createElement('span'); plus.textContent = '+'; plus.style.cssText = 'color:var(--secondary-text-color,#999);font-size:14px;flex-shrink:0;'; coRow.appendChild(plus); }}
          coRow.appendChild(makeBubble(c, 'condition', T.flow_condition));
        }});
        topBlock.appendChild(coRow);
      }}

      if (flowTriggers.length || conditions.length) flowEl.appendChild(topBlock);

      if (expandedActions.length) {{
        const actionsBlock = document.createElement('div');
        actionsBlock.style.cssText = 'display:flex;flex-direction:column;gap:8px;';
        const actionsHead = document.createElement('div');
        actionsHead.style.cssText = 'display:flex;align-items:center;justify-content:center;gap:8px;';
        actionsHead.appendChild(makeSectionLabel(T.flow_action));
        actionsBlock.appendChild(actionsHead);

        const rows = [];
        let current = {{ title: tt('flow_actions_title', 'Actions'), branchId: 0, items: [] }};
        rows.push(current);
        expandedActions.forEach((a) => {{
          if (a && a.__kind === 'branch_marker') {{
            current = {{ title: a.__branch || tt('flow_branch', 'Branch'), branchId: a.__branchId || 0, items: [] }};
            rows.push(current);
            return;
          }}
          current.items.push(a);
        }});

        let renderedRows = 0;
        rows.forEach((row, idx) => {{
          if (!row.items.length) return;
          const rowWrap = document.createElement('div');
          const c = row.branchId ? branchColors[(row.branchId - 1) % branchColors.length] : '#94a3b8';
          rowWrap.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:6px;border-left:3px solid ' + c + ';padding:8px 10px;background:rgba(255,255,255,0.45);border-radius:8px;';

          const rowTitle = document.createElement('div');
          rowTitle.style.cssText = 'font-size:11px;font-weight:700;color:#475569;text-align:center;';
          rowTitle.textContent = row.title;
          rowWrap.appendChild(rowTitle);

          const steps = document.createElement('div');
          steps.style.cssText = 'display:flex;align-items:flex-start;justify-content:center;gap:8px;flex-wrap:wrap;';
          row.items.forEach((a, i) => {{
            if (i > 0) steps.appendChild(makeArrow('→'));
            const nodeWrap = document.createElement('div');
            nodeWrap.style.cssText = 'display:flex;flex-direction:column;gap:4px;max-width:320px;';
            const b = makeBubble(a, 'action', T.flow_action);
            nodeWrap.appendChild(b);
            steps.appendChild(nodeWrap);
          }});
          const count = document.createElement('div');
          count.style.cssText = 'font-size:11px;color:#64748b;margin-top:2px;text-align:center;';
          count.textContent = row.items.length + ' ' + tt('flow_actions_count', 'actions');
          rowWrap.appendChild(steps);
          rowWrap.appendChild(count);
          actionsBlock.appendChild(rowWrap);
          renderedRows += 1;
        }});

        if (renderedRows > 0) flowEl.appendChild(actionsBlock);
      }}

      if (!flowTriggers.length && !conditions.length && !expandedActions.length) {{
        if (refresh) _removeAllAutomationFlowEls();
        _autoFlowStatus = 'unavailable';
        _autoFlowUnavailableReason = T.flow_no_data;
        _autoFlowConfigSig = configSig;
        _autoFlowInjected = true;
        if (showUnavailable) _renderFlowInfoMessage(T.flow_no_data);
        return;
      }} else {{
        flowEl.appendChild(detailInfo);
      }}
      _autoFlowConfigSig = configSig;
    }} catch(e) {{
      console.warn('[Amira] Failed to fetch automation flow:', e);
      _autoFlowStatus = 'unavailable';
      _autoFlowUnavailableReason = T.flow_no_data;
      _autoFlowInjected = true;
      if (showUnavailable) _renderFlowInfoMessage(T.flow_no_data);
      return;
    }}

    // Append inside automation editor host when available.
    if (refresh) _removeAllAutomationFlowEls();
    const host = _findAutomationFlowHost();
    if (host) host.prepend(flowEl);
    else document.body.appendChild(flowEl);
    _autoFlowEl = flowEl;
    _autoFlowStatus = 'rendered';
    _autoFlowUnavailableReason = '';
    _applyFlowVisibility();
    }} finally {{
      _autoFlowRenderBusy = false;
    }}
  }}

  // ---- Automation sidebar chat panel ----
  function _autoAddMsg(role, text) {{
    if (!_autoMsgsEl) return null;
    const d = document.createElement('div');
    d.style.cssText = role === 'user'
      ? 'align-self:flex-end;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:8px 12px;border-radius:14px 14px 2px 14px;font-size:13px;max-width:85%;word-break:break-word;line-height:1.45;'
      : 'align-self:flex-start;background:var(--secondary-background-color,#f0f0f0);color:var(--primary-text-color,#212121);padding:8px 12px;border-radius:14px 14px 14px 2px;font-size:13px;max-width:85%;word-break:break-word;line-height:1.5;';
    if (role === 'user') d.textContent = text;
    else d.innerHTML = _renderInlineMd(text);
    _autoMsgsEl.appendChild(d);
    _autoMsgsEl.scrollTop = _autoMsgsEl.scrollHeight;
    return d;
  }}

  async function autoSidebarSend(presetText) {{
    const text = presetText || (_autoInputEl ? _autoInputEl.value.trim() : '');
    if (!text) return;
    if (_autoInputEl && !presetText) {{ _autoInputEl.value = ''; _autoInputEl.style.height = 'auto'; }}
    _autoAddMsg('user', text);
    const thinkEl = _autoAddMsg('assistant', T.thinking + '\u2026');
    try {{
      const ctx = detectContext();
      const prefix = buildContextPrefix(ctx);
      const fullMsg = prefix ? prefix + '\\n\\n' + text : text;
      const _session = getAutoSessionId();
      const response = await fetch(API_BASE + '/api/chat/stream', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message: fullMsg, session_id: _session }})
      }});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '', assistantText = '';
      let firstToken = true;

      while (true) {{
        const {{ done, value }} = await reader.read();
        if (done) {{
          if (buffer.trim()) {{
            let _flushUsage = null;
            for (const line of buffer.split('\\n')) {{
              if (!line.startsWith('data: ')) continue;
              try {{
                const evt = JSON.parse(line.slice(6));
                if (evt.type === 'token') {{ assistantText += evt.content || ''; }}
                else if (evt.type === 'done') {{
                  if (evt.full_text) {{ assistantText = evt.full_text; }}
                  if (evt.usage) {{ _flushUsage = evt.usage; }}
                }}
              }} catch(e) {{}}
            }}
            if (thinkEl && assistantText) {{
              thinkEl.innerHTML = _renderInlineMd(assistantText);
            }}
            if (thinkEl && _flushUsage && (_flushUsage.input_tokens || _flushUsage.output_tokens)) {{
              const u = _flushUsage;
              const iTokens = (u.input_tokens || 0).toLocaleString();
              const oTokens = (u.output_tokens || 0).toLocaleString();
              let usageTxt = iTokens + ' in / ' + oTokens + ' out';
              if (u.cost !== undefined && u.cost > 0) {{
                const sym = u.currency === 'EUR' ? '\u20ac' : '$';
                usageTxt += ' \u2022 ' + sym + u.cost.toFixed(4);
              }} else if (u.cost === 0) {{
                usageTxt += ' \u2022 free';
              }}
              const uDiv = document.createElement('div');
              uDiv.style.cssText = 'font-size:10px;color:var(--secondary-text-color,#999);text-align:right;margin-top:3px;';
              uDiv.textContent = usageTxt;
              thinkEl.appendChild(uDiv);
            }}
          }}
          break;
        }}

        buffer += decoder.decode(value, {{ stream: true }});
        const lines = buffer.split('\\n');
        buffer = lines.pop() || '';

        for (const line of lines) {{
          if (!line.startsWith('data: ')) continue;
          try {{
            const evt = JSON.parse(line.slice(6));
            if (evt.type === 'token') {{
              if (firstToken) {{ firstToken = false; }}
              assistantText += evt.content || '';
              if (thinkEl) thinkEl.innerHTML = _renderInlineMd(assistantText);
              if (_autoMsgsEl) _autoMsgsEl.scrollTop = _autoMsgsEl.scrollHeight;
            }} else if (evt.type === 'clear') {{
              assistantText = '';
              if (thinkEl) thinkEl.innerHTML = T.thinking + '\u2026';
            }} else if (evt.type === 'done') {{
              if (evt.full_text) {{
                assistantText = evt.full_text;
                if (thinkEl) thinkEl.innerHTML = _renderInlineMd(assistantText);
              }}
              if (thinkEl && evt.usage && (evt.usage.input_tokens || evt.usage.output_tokens)) {{
                const u = evt.usage;
                const iTokens = (u.input_tokens || 0).toLocaleString();
                const oTokens = (u.output_tokens || 0).toLocaleString();
                let usageTxt = iTokens + ' in / ' + oTokens + ' out';
                if (u.cost !== undefined && u.cost > 0) {{
                  const sym = u.currency === 'EUR' ? '\u20ac' : '$';
                  usageTxt += ' \u2022 ' + sym + u.cost.toFixed(4);
                }} else if (u.cost === 0) {{
                  usageTxt += ' \u2022 free';
                }}
                const uDiv = document.createElement('div');
                uDiv.style.cssText = 'font-size:10px;color:var(--secondary-text-color,#999);text-align:right;margin-top:3px;';
                uDiv.textContent = usageTxt;
                thinkEl.appendChild(uDiv);
              }}
            }} else if (evt.type === 'error') {{
              if (thinkEl) thinkEl.textContent = evt.message || T.error_connection;
            }} else if (evt.type === 'status') {{
              const msg = evt.message || evt.content || '';
              if (firstToken && thinkEl) thinkEl.textContent = msg + '\u2026';
            }} else if (evt.type === 'tool') {{
              const desc = evt.description || evt.name || 'tool';
              if (firstToken && thinkEl) thinkEl.textContent = '\U0001f527 ' + desc + '\u2026';
            }}
          }} catch (parseErr) {{}}
        }}
      }}
      if (!assistantText && thinkEl) {{
        thinkEl.textContent = T.error_connection;
      }}
    }} catch(e) {{
      console.error('[Amira auto sidebar] send error:', e);
      if (thinkEl) thinkEl.textContent = T.error_connection + ' (' + e.message + ')';
    }}
    if (_autoMsgsEl) _autoMsgsEl.scrollTop = _autoMsgsEl.scrollHeight;
  }}

  function openAutomationSidebar() {{
    if (_autoSidebarOpen) return;
    // Remove any stale chat panel
    if (_autoSidebarEl && _autoSidebarEl.remove) _autoSidebarEl.remove();
    const stale = document.getElementById(AMIRA_SIDEBAR_ID);
    if (stale) stale.remove();

    // Build horizontal chat panel (placed under the flow, inside automation editor host)
    const sidebar = document.createElement('div');
    sidebar.id = AMIRA_SIDEBAR_ID;
    sidebar.style.cssText = 'position:relative;z-index:2;display:flex;flex-direction:column;width:100%;min-height:260px;max-height:42vh;border:1px solid #667eea;border-radius:12px;background:var(--card-background-color,#fff);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;overflow:hidden;box-shadow:0 3px 10px rgba(0,0,0,0.10);margin:0 0 10px;';

    // Header
    const hdr = document.createElement('div');
    hdr.style.cssText = 'display:flex;align-items:center;padding:10px 14px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;flex-shrink:0;gap:8px;';
    const hdrTitle = document.createElement('span');
    hdrTitle.textContent = '\U0001f916 ' + T.auto_sidebar_title;
    hdrTitle.style.cssText = 'font-weight:600;font-size:14px;white-space:nowrap;';
    // Agent select mirror
    const _mainAgentSel = document.getElementById('haAgentSelect');
    const autoAgentSel = document.createElement('select');
    autoAgentSel.style.cssText = 'font-size:11px;padding:2px 4px;border-radius:4px;border:none;background:rgba(255,255,255,0.2);color:#fff;cursor:pointer;max-width:130px;min-width:0;flex-shrink:1;';
    if (_mainAgentSel && _mainAgentSel.style.display !== 'none' && _mainAgentSel.options.length) {{
      Array.from(_mainAgentSel.options).forEach(o => {{
        const opt = document.createElement('option');
        opt.value = o.value; opt.textContent = o.textContent;
        if (o.selected) opt.selected = true;
        autoAgentSel.appendChild(opt);
      }});
      autoAgentSel.addEventListener('change', () => {{ _mainAgentSel.value = autoAgentSel.value; _mainAgentSel.dispatchEvent(new Event('change')); }});
    }} else {{
      autoAgentSel.style.display = 'none';
    }}
    // Provider select mirror
    const _mainProvSel = document.getElementById('haProviderSelect');
    const _mainModSel  = document.getElementById('haModelSelect');
    const autoProvSel = document.createElement('select');
    autoProvSel.style.cssText = 'font-size:11px;padding:2px 4px;border-radius:4px;border:none;background:rgba(255,255,255,0.2);color:#fff;cursor:pointer;max-width:150px;min-width:0;flex-shrink:1;';
    if (_mainProvSel) {{
      Array.from(_mainProvSel.options).forEach(o => {{
        const opt = document.createElement('option');
        opt.value = o.value; opt.textContent = o.textContent;
        if (o.selected) opt.selected = true;
        autoProvSel.appendChild(opt);
      }});
      autoProvSel.addEventListener('change', () => {{ _mainProvSel.value = autoProvSel.value; _mainProvSel.dispatchEvent(new Event('change')); }});
    }}
    const autoModSel = document.createElement('select');
    autoModSel.style.cssText = 'font-size:11px;padding:2px 4px;border-radius:4px;border:none;background:rgba(255,255,255,0.2);color:#fff;cursor:pointer;max-width:200px;min-width:0;flex-shrink:1;';
    if (_mainModSel) {{
      Array.from(_mainModSel.options).forEach(o => {{
        const opt = document.createElement('option');
        opt.value = o.value; opt.textContent = o.textContent;
        if (o.selected) opt.selected = true;
        autoModSel.appendChild(opt);
      }});
      autoModSel.addEventListener('change', () => {{ _mainModSel.value = autoModSel.value; _mainModSel.dispatchEvent(new Event('change')); }});
    }}
    // New chat + close buttons
    const hdrActions = document.createElement('div');
    hdrActions.style.cssText = 'display:flex;gap:6px;margin-left:auto;';
    const newChatBtn = document.createElement('button');
    newChatBtn.innerHTML = '&#10227;';
    newChatBtn.title = T.new_chat;
    newChatBtn.style.cssText = 'background:none;border:none;color:#fff;cursor:pointer;font-size:16px;padding:4px;opacity:0.8;border-radius:4px;';
    newChatBtn.onmouseenter = () => {{ newChatBtn.style.opacity='1'; }};
    newChatBtn.onmouseleave = () => {{ newChatBtn.style.opacity='0.8'; }};
    newChatBtn.addEventListener('click', () => {{ resetAutoSession(); if (_autoMsgsEl) _autoMsgsEl.innerHTML = ''; }});
    const closeBtn2 = document.createElement('button');
    closeBtn2.innerHTML = '&times;';
    closeBtn2.title = T.close;
    closeBtn2.style.cssText = 'background:none;border:none;color:#fff;cursor:pointer;font-size:18px;padding:4px;opacity:0.8;border-radius:4px;';
    closeBtn2.onmouseenter = () => {{ closeBtn2.style.opacity='1'; }};
    closeBtn2.onmouseleave = () => {{ closeBtn2.style.opacity='0.8'; }};
    closeBtn2.addEventListener('click', () => {{ closeAutomationSidebar(); }});
    hdrActions.appendChild(newChatBtn);
    hdrActions.appendChild(closeBtn2);
    hdr.appendChild(hdrTitle);
    hdr.appendChild(autoAgentSel);
    hdr.appendChild(autoProvSel);
    hdr.appendChild(autoModSel);
    hdr.appendChild(hdrActions);
    sidebar.appendChild(hdr);

    // Quick actions row
    const qaRow = document.createElement('div');
    qaRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;padding:8px 14px;border-bottom:1px solid var(--divider-color,#e0e0e0);flex-shrink:0;';
    const qaItems = [
      {{ label: T.qa_analyze, text: T.qa_analyze }},
      {{ label: T.qa_optimize, text: T.qa_optimize }},
      {{ label: T.qa_add_condition, text: T.qa_add_condition }},
      {{ label: T.qa_explain, text: T.qa_explain }},
      {{ label: T.qa_fix, text: T.qa_fix }},
    ];
    qaItems.forEach(qa => {{
      const chip = document.createElement('button');
      chip.textContent = qa.label;
      chip.style.cssText = 'background:var(--secondary-background-color,#f0f0f0);color:var(--primary-text-color,#333);border:1px solid var(--divider-color,#ddd);border-radius:16px;padding:4px 12px;font-size:11px;cursor:pointer;white-space:nowrap;transition:background 0.15s;';
      chip.onmouseenter = () => {{ chip.style.background='var(--primary-color,#03a9f4)'; chip.style.color='#fff'; chip.style.borderColor='transparent'; }};
      chip.onmouseleave = () => {{ chip.style.background='var(--secondary-background-color,#f0f0f0)'; chip.style.color='var(--primary-text-color,#333)'; chip.style.borderColor='var(--divider-color,#ddd)'; }};
      chip.addEventListener('click', () => {{ autoSidebarSend(qa.text); }});
      qaRow.appendChild(chip);
    }});
    sidebar.appendChild(qaRow);

    // Messages container
    const msgs = document.createElement('div');
    msgs.style.cssText = 'flex:1;overflow-y:auto;padding:12px 14px;display:flex;flex-direction:column;gap:8px;';
    sidebar.appendChild(msgs);

    // Input area
    const inputRow = document.createElement('div');
    inputRow.style.cssText = 'display:flex;align-items:flex-end;gap:6px;padding:10px 14px;border-top:1px solid var(--divider-color,#e0e0e0);flex-shrink:0;background:var(--card-background-color,#fff);';
    const inp = document.createElement('textarea');
    inp.placeholder = T.placeholder;
    inp.rows = 1;
    inp.style.cssText = 'flex:1;resize:none;border:1px solid var(--divider-color,#ddd);border-radius:10px;padding:8px 12px;font-size:13px;font-family:inherit;outline:none;min-height:36px;max-height:80px;background:var(--card-background-color,#fff);color:var(--primary-text-color,#333);';
    inp.addEventListener('input', () => {{ inp.style.height = 'auto'; inp.style.height = Math.min(inp.scrollHeight, 80) + 'px'; }});
    inp.addEventListener('keydown', (e) => {{
      if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); autoSidebarSend(); }}
    }});
    const sendBtn2 = document.createElement('button');
    sendBtn2.innerHTML = '&#9654;';
    sendBtn2.title = T.send;
    sendBtn2.style.cssText = 'width:36px;height:36px;border-radius:50%;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:opacity 0.15s;';
    sendBtn2.onmouseenter = () => {{ sendBtn2.style.opacity='0.85'; }};
    sendBtn2.onmouseleave = () => {{ sendBtn2.style.opacity='1'; }};
    sendBtn2.addEventListener('click', () => {{ autoSidebarSend(); }});
    inputRow.appendChild(inp);
    inputRow.appendChild(sendBtn2);
    sidebar.appendChild(inputRow);

    // Append under flow when possible, otherwise at top of automation host.
    const host = _findAutomationFlowHost();
    const flow = host ? host.querySelector('#' + AMIRA_FLOW_ID) : null;
    if (host && flow && flow.nextSibling) {{
      host.insertBefore(sidebar, flow.nextSibling);
    }} else if (host && flow) {{
      host.appendChild(sidebar);
    }} else if (host) {{
      host.prepend(sidebar);
    }} else {{
      document.body.appendChild(sidebar);
    }}

    // Save refs
    _autoSidebarEl = sidebar;
    _autoMsgsEl    = msgs;
    _autoInputEl   = inp;
    _autoProvSel   = autoProvSel;
    _autoModSel    = autoModSel;
    _autoAgentSel  = autoAgentSel;
    _autoSidebarOpen = true;
    saveSetting('auto-sidebar-open', true);

    // Close floating bubble panel if open (sidebar takes over)
    if (isOpen) {{ isOpen = false; panel.classList.remove('open'); }}

    setTimeout(() => inp.focus(), 50);
  }}

  function closeAutomationSidebar() {{
    const el = document.getElementById(AMIRA_SIDEBAR_ID);
    if (el) el.remove();
    if (_autoSidebarEl) _autoSidebarEl.remove();
    _autoSidebarEl = null;
    _autoMsgsEl = null;
    _autoInputEl = null;
    _autoProvSel = null;
    _autoModSel = null;
    _autoAgentSel = null;
    _autoContentWrapper = null;
    _autoSidebarOpen = false;
    saveSetting('auto-sidebar-open', false);
  }}

  function removeAutomationIntegration() {{
    closeAutomationSidebar();
    removeAutomationToolbarButton();
    const flow = _findAutomationFlowEl();
    if (flow) flow.remove();
    _autoFlowEl = null;
    _autoFlowInjected = false;
    _lastAutoPageId = null;
    _autoFlowStatus = 'idle';
    _autoFlowUnavailableReason = '';
    _autoFlowConfigSig = '';
    _autoFlowLastCheckTs = 0;
  }}

  // ---- Auto-resize textarea ----
  input.addEventListener('input', () => {{ input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 80) + 'px'; }});

  // ---- Voice Input (MediaRecorder + server-side transcription) ----
  let isRecording = false;
  let bubbleMediaRecorder = null;
  let bubbleAudioChunks = [];
  let _bubbleSilenceId = null;
  let _bubbleVoiceCtx = null;
  let _bubbleWakeTriggered = false;

  // Polyfill: navigator.mediaDevices for older browsers / insecure iframe contexts
  (function() {{
    if (navigator.mediaDevices === undefined) navigator.mediaDevices = {{}};
    if (navigator.mediaDevices.getUserMedia === undefined) {{
      navigator.mediaDevices.getUserMedia = function(constraints) {{
        const legacy = navigator.getUserMedia || navigator.webkitGetUserMedia ||
                       navigator.mozGetUserMedia || navigator.msGetUserMedia;
        if (!legacy) return Promise.reject(new Error('getUserMedia not supported'));
        return new Promise(function(resolve, reject) {{ legacy.call(navigator, constraints, resolve, reject); }});
      }};
    }}
  }})();

  async function startBubbleVoiceRecording() {{
    if (isRecording) {{ stopBubbleVoiceRecording(); return; }}
    try {{
      const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
      bubbleAudioChunks = [];
      const mimeType = typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '');
      const options = mimeType ? {{ mimeType }} : {{}};
      bubbleMediaRecorder = new MediaRecorder(stream, options);
      bubbleMediaRecorder.ondataavailable = function(e) {{
        if (e.data.size > 0) bubbleAudioChunks.push(e.data);
      }};
      bubbleMediaRecorder.onstop = async function() {{
        stream.getTracks().forEach(t => t.stop());
        if (bubbleAudioChunks.length === 0) return;
        const audioBlob = new Blob(bubbleAudioChunks, {{ type: bubbleMediaRecorder.mimeType || 'audio/webm' }});
        await bubbleTranscribeAndSend(audioBlob);
      }};
      bubbleMediaRecorder.start();
      isRecording = true;
      voiceBtn.classList.add('recording');
      input.value = '';
      input.placeholder = T.voice_start;
      if (_bubbleWakeTriggered) {{ _startBubbleSilenceDetector(stream); }}
    }} catch(err) {{
      console.error('[Bubble Voice] Mic error:', err);
      isRecording = false;
      voiceBtn.classList.remove('recording');
      if (err.name === 'NotAllowedError') {{
        alert(T.voice_unsupported);
      }} else {{
        alert(T.voice_unsupported);
      }}
    }}
  }}

  function _startBubbleSilenceDetector(stream) {{
    const CALIBRATION_MS = 400;
    const SPEECH_MARGIN  = 8;
    const SILENCE_DURATION = 1200;
    const MAX_RECORD_MS = 10000;
    const CHECK_MS = 80;
    try {{
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      _bubbleVoiceCtx = new AudioCtx();
      const source = _bubbleVoiceCtx.createMediaStreamSource(stream);
      const analyser = _bubbleVoiceCtx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      const buf = new Uint8Array(analyser.fftSize);
      let calSamples = [];
      let noiseFloor = 0;
      let speechDetected = false;
      let silenceStart = 0;
      const t0 = Date.now();
      _bubbleSilenceId = setInterval(() => {{
        if (!isRecording) {{ _stopBubbleSilenceDetector(); return; }}
        const elapsed = Date.now() - t0;
        if (elapsed > MAX_RECORD_MS) {{
          console.log('[Bubble Silence] max recording time reached');
          stopBubbleVoiceRecording(); return;
        }}
        analyser.getByteTimeDomainData(buf);
        let sum = 0;
        for (let i = 0; i < buf.length; i++) {{ const v = buf[i] - 128; sum += v * v; }}
        const rms = Math.sqrt(sum / buf.length);
        if (elapsed < CALIBRATION_MS) {{ calSamples.push(rms); return; }}
        if (!noiseFloor && calSamples.length) {{
          noiseFloor = calSamples.reduce((a,b) => a+b, 0) / calSamples.length;
          console.log('[Bubble Silence] noise floor:', noiseFloor.toFixed(1));
        }}
        const threshold = noiseFloor + SPEECH_MARGIN;
        if (rms > threshold) {{
          speechDetected = true;
          silenceStart = 0;
        }} else if (speechDetected) {{
          if (!silenceStart) silenceStart = Date.now();
          else if (Date.now() - silenceStart >= SILENCE_DURATION) {{
            console.log('[Bubble Silence] silence detected, auto-stopping');
            stopBubbleVoiceRecording();
          }}
        }}
      }}, CHECK_MS);
    }} catch(e) {{ console.warn('[Bubble Silence] detector error:', e); }}
  }}

  function _stopBubbleSilenceDetector() {{
    if (_bubbleSilenceId) {{ clearInterval(_bubbleSilenceId); _bubbleSilenceId = null; }}
    if (_bubbleVoiceCtx) {{ try {{ _bubbleVoiceCtx.close(); }} catch(e) {{}} _bubbleVoiceCtx = null; }}
  }}

  function stopBubbleVoiceRecording() {{
    _stopBubbleSilenceDetector();
    _bubbleWakeTriggered = false;
    if (bubbleMediaRecorder && bubbleMediaRecorder.state !== 'inactive') {{
      bubbleMediaRecorder.stop();
    }}
    isRecording = false;
    voiceBtn.classList.remove('recording');
    voiceBtn.classList.add('processing');
  }}

  async function bubbleTranscribeAndSend(audioBlob) {{
    try {{
      input.placeholder = T.voice_processing || 'Processing...';
      const formData = new FormData();
      const ext = (audioBlob.type || '').includes('webm') ? 'webm' : 'wav';
      formData.append('file', audioBlob, `voice.${{ext}}`);
      const resp = await fetch(API_BASE + '/api/voice/transcribe', {{
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      }});
      const data = await resp.json();
      if (data.status === 'success' && data.text) {{
        input.value = data.text;
        sendMessage();
      }} else {{
        console.warn('[Bubble Voice] Transcription failed:', data.message || data);
      }}
    }} catch(err) {{
      console.error('[Bubble Voice] Transcription error:', err);
    }} finally {{
      voiceBtn.classList.remove('recording', 'processing');
      input.placeholder = T.placeholder;
    }}
  }}

  voiceBtn.addEventListener('click', () => {{
    unlockBubbleAudioContext();  // Unlock audio on user gesture (mobile)
    startBubbleVoiceRecording();
  }});

  // ---- Send / Abort ----
  input.addEventListener('keydown', (e) => {{
    if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); sendMessage(); }}
  }});

  // ---- Voice TTS (Text-to-Speech) ----
  const voiceToggle = root.querySelector('#haChatVoiceToggle');
  const speakingEl = root.querySelector('#haChatSpeaking');
  let voiceModeActive = false;
  let currentAudio = null;
  let audioContextUnlocked = false;
  let sharedAudioContext = null;

  // Unlock AudioContext on user gesture (required for mobile browsers)
  function unlockBubbleAudioContext() {{
    if (audioContextUnlocked) return;
    try {{
      if (!sharedAudioContext) {{
        sharedAudioContext = new (window.AudioContext || window.webkitAudioContext)();
      }}
      if (sharedAudioContext.state === 'suspended') {{
        sharedAudioContext.resume();
      }}
      // Play a silent buffer to unlock
      const silentBuffer = sharedAudioContext.createBuffer(1, 1, 22050);
      const src = sharedAudioContext.createBufferSource();
      src.buffer = silentBuffer;
      src.connect(sharedAudioContext.destination);
      src.start(0);
      audioContextUnlocked = true;
      console.log('[Voice] AudioContext unlocked for bubble');
    }} catch(e) {{
      console.warn('[Voice] AudioContext unlock failed:', e);
    }}
  }}

  try {{ voiceModeActive = localStorage.getItem('amira_bubble_voice') === 'true'; }} catch(e) {{}}
  if (voiceToggle) {{
    voiceToggle.checked = voiceModeActive;
    voiceToggle.addEventListener('change', async () => {{
      voiceModeActive = voiceToggle.checked;
      try {{ localStorage.setItem('amira_bubble_voice', voiceModeActive ? 'true' : 'false'); }} catch(e) {{}}
      unlockBubbleAudioContext();  // Unlock on user gesture
      // Check TTS providers when enabling voice mode
      if (voiceModeActive) {{
        try {{
          const provResp = await fetch(API_BASE + '/api/voice/tts/providers');
          if (provResp.ok) {{
            const provData = await provResp.json();
            if (!provData.providers || provData.providers.length === 0) {{
              console.warn('[TTS] No providers available for voice output');
            }} else {{
              console.log('[TTS] Available providers:', provData.providers);
            }}
          }}
        }} catch(e) {{ console.warn('[TTS] Could not check providers:', e); }}
      }}
    }});
  }}
  if (speakingEl) {{
    speakingEl.addEventListener('click', () => {{ stopBubbleTTS(); }});
  }}

  function stopBubbleTTS() {{
    if (currentAudio) {{
      if (currentAudio.stop) {{
        try {{ currentAudio.stop(); }} catch(e) {{}}
      }} else if (currentAudio.pause) {{
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }}
      currentAudio = null;
    }}
    if (speakingEl) speakingEl.style.display = 'none';
  }}

  async function playBubbleTTS(text) {{
    if (!text || !voiceModeActive) return;
    let clean = text
      .replace(/```[\\s\\S]*?```/g, '')
      .replace(/`[^`]+`/g, '')
      .replace(/\\[([^\\]]+)\\]\\([^)]+\\)/g, '$1')
      .replace(/^[\\s]*[-\\u2022*]\\s*(?:switch|light|sensor|binary_sensor|automation|script|input_boolean|climate|cover|fan|media_player|vacuum|lock|alarm)\\.[^\\n]*/gim, '')  // full lines: - sensor.xxx = value
      .replace(/\\([^)]*(?:switch|light|sensor|binary_sensor|automation|script|input_boolean|climate|cover|fan|media_player|vacuum|lock|alarm)[^)]*\\)/gi, '')
      .replace(/\\b(?:switch|light|sensor|binary_sensor|automation|script|input_boolean|climate|cover|fan|media_player|vacuum|lock|alarm)\\.[a-z0-9_]+(?:\\s*[:=]\\s*[^\\n,)]*)?/gi, '')  // entity_id + optional = value
      .replace(/\\p{{Emoji_Presentation}}|\\p{{Extended_Pictographic}}/gu, '')  // remove emoji
      .replace(/[#*_~>|]/g, '')
      .replace(/\\/{2,}/g, ' ')
      .replace(/(?<=\\s)\\/(?=\\s)/g, ' ')
      .replace(/\\n+/g, '. ')
      .replace(/\\s*\\.\\s*\\.\\s*/g, '. ')
      .replace(/\\s+/g, ' ')
      .trim();
    if (!clean || clean.length < 2) return;
    if (clean.length > 1000) clean = clean.substring(0, 1000) + '...';
    try {{
      if (speakingEl) speakingEl.style.display = 'flex';
      const resp = await fetch(API_BASE + '/api/voice/tts', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ text: clean }})
      }});
      if (!resp.ok) throw new Error('TTS ' + resp.status);
      const blob = await resp.blob();
      const arrayBuffer = await blob.arrayBuffer();

      // Try Web Audio API first (mobile-compatible with unlocked AudioContext)
      let played = false;
      if (sharedAudioContext && audioContextUnlocked) {{
        try {{
          if (sharedAudioContext.state === 'suspended') {{
            await sharedAudioContext.resume();
          }}
          const audioBuffer = await sharedAudioContext.decodeAudioData(arrayBuffer.slice(0));
          const source = sharedAudioContext.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(sharedAudioContext.destination);
          stopBubbleTTS();
          currentAudio = source;
          source.onended = () => {{
            currentAudio = null;
            if (speakingEl) speakingEl.style.display = 'none';
          }};
          source.start(0);
          played = true;
          console.log('[Voice] Bubble TTS playing via Web Audio API');
        }} catch(webAudioErr) {{
          console.warn('[Voice] Web Audio API failed, falling back:', webAudioErr);
        }}
      }}

      // Fallback to HTML5 Audio
      if (!played) {{
        const url = URL.createObjectURL(new Blob([arrayBuffer], {{ type: 'audio/mpeg' }}));
        stopBubbleTTS();
        const audio = new Audio(url);
        currentAudio = audio;
        audio.onended = () => {{
          URL.revokeObjectURL(url);
          currentAudio = null;
          if (speakingEl) speakingEl.style.display = 'none';
        }};
        audio.onerror = () => {{
          URL.revokeObjectURL(url);
          currentAudio = null;
          if (speakingEl) speakingEl.style.display = 'none';
        }};
        await audio.play();
        console.log('[Voice] Bubble TTS playing via HTML5 Audio fallback');
      }}
    }} catch(e) {{
      console.error('Bubble TTS error:', e);
      if (speakingEl) speakingEl.style.display = 'none';
    }}
  }}

  // ---- Wake Word Detection ("Ok Amira") ----
  let wakeWordRec = null;
  let wakeWordActive = false;
  const WAKE_PHRASES = ['ok amira', 'okay amira', 'ehi amira', 'hey amira', 'amira'];

  function startBubbleWakeWord() {{
    if (wakeWordActive || !voiceModeActive) return;
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;

    wakeWordRec = new SpeechRec();
    wakeWordRec.lang = VOICE_LANG;
    wakeWordRec.continuous = true;
    wakeWordRec.interimResults = true;

    wakeWordRec.onresult = function(event) {{
      for (let i = event.resultIndex; i < event.results.length; i++) {{
        const transcript = event.results[i][0].transcript.toLowerCase().trim();
        if (WAKE_PHRASES.some(p => transcript.includes(p))) {{
          stopBubbleWakeWord();
          // Trigger voice recording via MediaRecorder
          if (!isRecording) {{
            input.placeholder = T.wake_word_detected || 'Amira activated! Speak now...';
            _bubbleWakeTriggered = true;
            startBubbleVoiceRecording();
          }}
          return;
        }}
      }}
    }};

    wakeWordRec.onend = function() {{
      wakeWordActive = false;
      if (voiceModeActive && !isRecording && !isStreaming) {{
        setTimeout(function() {{ startBubbleWakeWord(); }}, 500);
      }}
    }};

    wakeWordRec.onerror = function(e) {{
      if (e.error !== 'no-speech' && e.error !== 'aborted') {{
        console.warn('Bubble wake word error:', e.error);
      }}
      wakeWordActive = false;
    }};

    try {{
      wakeWordRec.start();
      wakeWordActive = true;
    }} catch(e) {{
      wakeWordActive = false;
    }}
  }}

  function stopBubbleWakeWord() {{
    if (wakeWordRec) {{
      try {{ wakeWordRec.abort(); }} catch(e) {{}}
      wakeWordRec = null;
    }}
    wakeWordActive = false;
  }}

  // Toggle wake word with voice mode
  if (voiceToggle) {{
    voiceToggle.addEventListener('change', () => {{
      if (voiceModeActive) {{ startBubbleWakeWord(); }}
      else {{ stopBubbleWakeWord(); }}
    }});
    if (voiceModeActive) {{
      setTimeout(function() {{ startBubbleWakeWord(); }}, 1000);
    }}
  }}

  // Restart wake word after TTS finishes
  const _origPlayBubbleTTS = playBubbleTTS;
  playBubbleTTS = async function(text) {{
    stopBubbleWakeWord();
    await _origPlayBubbleTTS(text);
    setTimeout(function() {{
      if (voiceModeActive && !isRecording && !currentAudio) {{
        startBubbleWakeWord();
      }}
    }}, 2000);
  }};

  sendBtn.addEventListener('click', () => {{
    if (isStreaming) {{ abortStream(); }} else {{ sendMessage(); }}
  }});

  function addMessage(role, text, useMarkdown) {{
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    if (useMarkdown && role === 'assistant') {{
      div.innerHTML = renderMarkdown(text);
    }} else {{
      div.textContent = text;
    }}
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }}

  function abortStream() {{
    // Signal backend to abort
    fetch(API_BASE + '/api/chat/abort', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ session_id: getSessionId() }}),
      credentials: 'same-origin',
    }}).catch(() => {{}});
    // Also abort the fetch
    if (currentAbortController) currentAbortController.abort();
    isStreaming = false;
    sendBtn.innerHTML = '&#9654;';
    sendBtn.className = 'input-btn send-btn';
    sendBtn.disabled = false;
  }}

  const RELOAD_TOOLS = new Set([
    'update_automation', 'update_script', 'update_dashboard_card',
    'update_dashboard', 'create_automation', 'create_script',
  ]);

  const CONFIRM_PATTERNS = [
    /confermi.*\\?/i,
    /scrivi\\s+s[i\u00ec]\\s+o\\s+no/i,
    /digita\\s+['"\u2018\u2019]?elimina['"\u2018\u2019]?\\s+per\\s+confermare/i,
    /vuoi\\s+(eliminare|procedere|continuare|applic).*\\?/i,
    /vuoi\\s+che\\s+(applic|esegu|salv|scriva|modifich).*\\?/i,
    /s[i\u00ec]\\s*\\/\\s*no/i,
    /confirm.*\\?\\s*(yes.*no)?/i,
    /type\\s+['"]?yes['"]?\\s+or\\s+['"]?no['"]?/i,
    /do\\s+you\\s+want\\s+(me\\s+to\\s+)?(apply|proceed|continue|delete|save|write).*\\?/i,
    /should\\s+i\\s+(apply|proceed|write|save).*\\?/i,
    /confirma.*\\?/i,
    /escribe\\s+s[i\u00ed]\\s+o\\s+no/i,
    /\\u00bfquieres\\s+que\\s+(apliqu|proceda|guard).*\\?/i,
    /confirme[sz]?.*\\?/i,
    /tape[sz]?\\s+['"]?oui['"]?\\s+ou\\s+['"]?non['"]?/i,
    /veux-tu\\s+que\\s+(j['\u2019]appliqu|je\\s+proc[eè]d|je\\s+sauvegard).*\\?/i,
  ];

  function showConfirmationButtons(msgEl, text) {{
    if (!text || typeof text !== 'string') return;
    const isConfirmation = CONFIRM_PATTERNS.some(p => p.test(text));
    if (!isConfirmation) return;

    const isDeleteConfirm = /digita\\s+['"\u2018\u2019]?elimina['"\u2018\u2019]?/i.test(text) ||
                            /type\\s+['"]?delete['"]?/i.test(text);

    const btnContainer = document.createElement('div');
    btnContainer.className = 'confirm-buttons';

    const yesBtn = document.createElement('button');
    yesBtn.className = 'confirm-btn confirm-yes';
    yesBtn.textContent = isDeleteConfirm ? ('\\uD83D\\uDDD1 ' + T.confirm_delete_yes) : ('\\u2705 ' + T.confirm_yes);

    const noBtn = document.createElement('button');
    noBtn.className = 'confirm-btn confirm-no';
    noBtn.textContent = '\\u274C ' + T.confirm_no;

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
    msgEl.appendChild(btnContainer);
  }}

  async function sendMessage() {{
    const text = input.value.trim();
    if (!text || isStreaming) return;

    const ctx = detectContext();
    let contextPrefix = buildContextPrefix();

    // For HTML dashboards, fetch the actual HTML to pass as context
    if (ctx.type === 'html_dashboard' && ctx.id) {{
      try {{
        const resp = await fetch(API_BASE + '/api/dashboard_html/' + encodeURIComponent(ctx.id), {{credentials:'same-origin'}});
        if (resp.ok) {{
          const data = await resp.json();
          if (data.html) {{
            contextPrefix = '[CONTEXT: User is viewing HTML dashboard "' + ctx.id + '". '
              + 'The COMPLETE current HTML is below. Modify it as requested, then call create_html_dashboard(name="' + ctx.id + '", html="<complete modified html>") immediately — do NOT call read_html_dashboard first. '
              + 'CRITICAL: Keep ALL existing sections, style, and CSS unchanged — only ADD or MODIFY what the user requests. NEVER output HTML as text in the chat.]\\n'
              + '[CURRENT_DASHBOARD_HTML]\\n' + data.html + '\\n[/CURRENT_DASHBOARD_HTML]\\n';
          }}
        }}
      }} catch(e) {{ console.warn('[HA-Claude] Could not fetch dashboard HTML:', e); }}
    }}

    const fullMessage = contextPrefix + text;

    addMessage('user', text, false);
    addToHistory('user', text);
    input.value = ''; input.style.height = 'auto';
    input.placeholder = T.placeholder;
    isStreaming = true;

    // Switch send button to abort
    sendBtn.innerHTML = '&#9632;';
    sendBtn.className = 'input-btn abort-btn';
    sendBtn.disabled = false;

    let thinkingEl = addMessage('thinking', '', false);
    // Show current model name in the thinking label (like the main chat UI)
    const _thinkModel = agentData ? (agentData.current_model_technical || '') : '';
    const _thinkLabel = _thinkModel ? T.thinking + ' <span class="thinking-model">· ' + _thinkModel + '</span>' : T.thinking;
    thinkingEl.innerHTML = _thinkLabel + '... <span class="thinking-elapsed"></span><span class="thinking-dots"><span>.</span><span>.</span><span>.</span></span><div class="thinking-steps"></div>';
    const _thinkingStart = Date.now();
    let _thinkingSteps = [];
    let _thinkingTimer = setInterval(() => {{
      const el = thinkingEl.querySelector('.thinking-elapsed');
      if (!el) return;
      const s = Math.floor((Date.now() - _thinkingStart) / 1000);
      const m = Math.floor(s / 60);
      const r = s % 60;
      el.textContent = '(' + (m > 0 ? m + ':' + String(r).padStart(2, '0') : r + 's') + ')';
    }}, 1000);

    function _addThinkingStep(text) {{
      const t = String(text || '').trim();
      if (!t) return;
      if (_thinkingSteps.length && _thinkingSteps[_thinkingSteps.length - 1] === t) return;
      _thinkingSteps.push(t);
      if (_thinkingSteps.length > 6) _thinkingSteps = _thinkingSteps.slice(-6);
      const stepsEl = thinkingEl.querySelector('.thinking-steps');
      if (stepsEl) stepsEl.innerHTML = _thinkingSteps.map(s => '<div>\\u2022 ' + s.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>').join('');
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }}

    function _updateThinkingBase(text) {{
      // Keep elapsed timer and steps while updating the status line
      const elapsedEl = thinkingEl.querySelector('.thinking-elapsed');
      const elapsed = elapsedEl ? elapsedEl.outerHTML : '';
      const stepsEl = thinkingEl.querySelector('.thinking-steps');
      // Preserve steps HTML — re-read from current steps array for reliability
      const stepsHtml = _thinkingSteps.length
        ? '<div class="thinking-steps">' + _thinkingSteps.map(s => '<div>\\u2022 ' + s.replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</div>').join('') + '</div>'
        : '<div class="thinking-steps"></div>';
      thinkingEl.innerHTML = text + ' ' + elapsed + '<span class="thinking-dots"><span>.</span><span>.</span><span>.</span></span>' + stepsHtml;
    }}

    function _removeThinking() {{
      clearInterval(_thinkingTimer);
      if (thinkingEl.parentNode) thinkingEl.remove();
    }}

    function _restoreThinking() {{
      // Re-create thinking indicator between tool rounds
      clearInterval(_thinkingTimer);
      if (thinkingEl.parentNode) thinkingEl.remove();
      thinkingEl = addMessage('thinking', '', false);
      thinkingEl.innerHTML = _thinkLabel + '... <span class="thinking-elapsed"></span><span class="thinking-dots"><span>.</span><span>.</span><span>.</span></span><div class="thinking-steps"></div>';
      _thinkingTimer = setInterval(() => {{
        const el = thinkingEl.querySelector('.thinking-elapsed');
        if (!el) return;
        const s = Math.floor((Date.now() - _thinkingStart) / 1000);
        const m = Math.floor(s / 60);
        const r = s % 60;
        el.textContent = '(' + (m > 0 ? m + ':' + String(r).padStart(2, '0') : r + 's') + ')';
      }}, 1000);
      firstToken = true;
    }}

    let toolBadgesEl = null;
    let writeToolCalled = false;

    currentAbortController = new AbortController();

    try {{
      const response = await fetch(API_BASE + '/api/chat/stream', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message: fullMessage, session_id: getSessionId(), voice_mode: !!voiceModeActive }}),
        signal: currentAbortController.signal,
      }});

      if (!response.ok) throw new Error('HTTP ' + response.status);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '', assistantText = '';
      let pendingDiffHtml = '';  // accumulated diff_html content (separate so done/full_text can't overwrite it)
      let firstToken = true;

      const assistantEl = addMessage('assistant', '', false);
      assistantEl.style.display = 'none';

      while (true) {{
        const {{ done, value }} = await reader.read();
        // Flush any remaining buffer data on stream close
        if (done) {{
          if (buffer.trim()) {{
            let _flushUsage = null;
            for (const line of buffer.split('\\n')) {{
              if (!line.startsWith('data: ')) continue;
              try {{
                const evt = JSON.parse(line.slice(6));
                if (evt.type === 'token') {{ assistantText += evt.content || ''; }}
                else if (evt.type === 'diff_html') {{ pendingDiffHtml += (evt.content || '') + '\\n\\n'; }}
                else if (evt.type === 'done') {{
                  if (evt.full_text) {{ assistantText = evt.full_text; }}
                  if (evt.usage) {{ _flushUsage = evt.usage; }}
                }}
              }} catch(e) {{}}
            }}
            if (pendingDiffHtml || assistantText) {{
              assistantEl.style.display = '';
              assistantEl.innerHTML = renderMarkdown(pendingDiffHtml + assistantText);
            }}
            // Show cost from buffered done event
            if (_flushUsage && (_flushUsage.input_tokens || _flushUsage.output_tokens)) {{
              const u = _flushUsage;
              const inp = (u.input_tokens || 0).toLocaleString();
              const out = (u.output_tokens || 0).toLocaleString();
              let usageTxt = inp + ' in / ' + out + ' out';
              if (u.cost !== undefined && u.cost > 0) {{
                const sym = u.currency === 'EUR' ? '\u20ac' : '$';
                usageTxt += ' \u2022 ' + sym + u.cost.toFixed(4);
              }} else if (u.cost === 0) {{
                usageTxt += ' \u2022 free';
              }}
              const uDiv = document.createElement('div');
              uDiv.className = 'msg-usage';
              uDiv.textContent = usageTxt;
              assistantEl.appendChild(uDiv);
            }}
          }}
          break;
        }}

        buffer += decoder.decode(value, {{ stream: true }});
        const lines = buffer.split('\\n');
        buffer = lines.pop() || '';

        for (const line of lines) {{
          if (!line.startsWith('data: ')) continue;
          try {{
            const evt = JSON.parse(line.slice(6));
            if (evt.type === 'token') {{
              if (firstToken) {{
                const savedSteps = _thinkingSteps.slice(0);
                _removeThinking();
                assistantEl.style.display = '';
                if (savedSteps.length) {{
                  const pDiv = document.createElement('div');
                  pDiv.className = 'progress-steps';
                  pDiv.innerHTML = savedSteps.map(s => '<div>\\u2022 ' + s.replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</div>').join('');
                  assistantEl.appendChild(pDiv);
                }}
                firstToken = false;
              }}
              assistantText += evt.content || '';
              const stepsHtml = assistantEl.querySelector('.progress-steps');
              const prefix = stepsHtml ? stepsHtml.outerHTML : '';
              assistantEl.innerHTML = prefix + renderMarkdown(pendingDiffHtml + assistantText);
              messagesEl.scrollTop = messagesEl.scrollHeight;
            }} else if (evt.type === 'clear') {{
              assistantText = '';
              pendingDiffHtml = '';
              assistantEl.style.display = 'none';
              assistantEl.innerHTML = '';
              if (toolBadgesEl) {{ toolBadgesEl.remove(); toolBadgesEl = null; }}
              _restoreThinking();
            }} else if (evt.type === 'done') {{
              if (firstToken) {{
                _removeThinking();
                assistantEl.style.display = '';
                firstToken = false;
              }}
              if (evt.full_text) {{
                assistantText = evt.full_text;
                assistantEl.innerHTML = renderMarkdown(pendingDiffHtml + assistantText);
              }}
              // Append token usage
              if (evt.usage && (evt.usage.input_tokens || evt.usage.output_tokens)) {{
                const u = evt.usage;
                const inp = (u.input_tokens || 0).toLocaleString();
                const out = (u.output_tokens || 0).toLocaleString();
                let usageTxt = inp + ' in / ' + out + ' out';
                if (u.cost !== undefined && u.cost > 0) {{
                  const sym = u.currency === 'EUR' ? '\u20ac' : '$';
                  usageTxt += ' \u2022 ' + sym + u.cost.toFixed(4);
                }} else if (u.cost === 0) {{
                  usageTxt += ' \u2022 free';
                }}
                const uDiv = document.createElement('div');
                uDiv.className = 'msg-usage';
                uDiv.textContent = usageTxt;
                assistantEl.appendChild(uDiv);
              }}
              // TTS: read response aloud if voice mode is active
              if (voiceModeActive && assistantText) {{
                playBubbleTTS(assistantText);
              }}
            }} else if (evt.type === 'error') {{
              _removeThinking();
              assistantEl.style.display = '';
              assistantEl.className = 'msg error';
              assistantEl.textContent = evt.message || 'Error';
            }} else if (evt.type === 'tool') {{
              const desc = evt.description || evt.name || 'tool';
              _updateThinkingBase('\\U0001f527 ' + desc);
              _addThinkingStep(desc);
              if (!toolBadgesEl) {{
                toolBadgesEl = document.createElement('div');
                toolBadgesEl.className = 'tool-badges';
                messagesEl.insertBefore(toolBadgesEl, assistantEl);
              }}
              const badge = document.createElement('span');
              badge.className = 'tool-badge';
              badge.textContent = evt.name || 'tool';
              toolBadgesEl.appendChild(badge);
              messagesEl.scrollTop = messagesEl.scrollHeight;
              if (RELOAD_TOOLS.has(evt.name)) writeToolCalled = true;
            }} else if (evt.type === 'diff_html') {{
              // Rich side-by-side HTML diff from write tools (preview_automation_change, update_automation, etc.)
              if (firstToken) {{
                firstToken = false;
                _removeThinking();
                assistantEl.style.display = '';
              }}
              pendingDiffHtml += (evt.content || '') + '\\n\\n';
              const _stepsHtmlDiff = assistantEl.querySelector('.progress-steps');
              const _prefixDiff = _stepsHtmlDiff ? _stepsHtmlDiff.outerHTML : '';
              assistantEl.innerHTML = _prefixDiff + renderMarkdown(pendingDiffHtml + assistantText);
              messagesEl.scrollTop = messagesEl.scrollHeight;
            }} else if (evt.type === 'diff') {{
              if (assistantEl && evt.content) {{
                const wrapper = document.createElement('details');
                wrapper.style.cssText = 'margin:6px 0;font-size:11px;border:1px solid #334155;border-radius:5px;overflow:hidden;';
                const summary = document.createElement('summary');
                summary.style.cssText = 'padding:5px 8px;cursor:pointer;background:#1e293b;color:#94a3b8;user-select:none;';
                summary.textContent = '\\U0001f4dd Diff modifiche';
                wrapper.appendChild(summary);
                const pre = document.createElement('pre');
                pre.style.cssText = 'margin:0;padding:6px;overflow-x:auto;background:#0f172a;font-size:10px;line-height:1.5;';
                evt.content.split('\\n').forEach(function(line) {{
                  const span = document.createElement('span');
                  span.style.cssText = 'display:block;white-space:pre;';
                  if (line.startsWith('+') && !line.startsWith('+++')) {{
                    span.style.background = 'rgba(34,197,94,0.15)'; span.style.color = '#86efac';
                  }} else if (line.startsWith('-') && !line.startsWith('---')) {{
                    span.style.background = 'rgba(239,68,68,0.15)'; span.style.color = '#fca5a5';
                  }} else if (line.startsWith('@@')) {{
                    span.style.color = '#7dd3fc';
                  }} else {{
                    span.style.color = '#64748b';
                  }}
                  span.textContent = line;
                  pre.appendChild(span);
                }});
                wrapper.appendChild(pre);
                assistantEl.appendChild(wrapper);
              }}
            }} else if (evt.type === 'system_message') {{
              // Warning injected by backend (e.g. hallucinated success with no tool call)
              const sysMsg = evt.content || evt.message || '';
              if (sysMsg) addMessage('system', sysMsg, false);
            }} else if (evt.type === 'status') {{
              const msg = evt.message || evt.content || '';
              // Use wrench for tool-related steps, hourglass for generic status
              const icon = msg.startsWith('\\U0001f527') ? '' : '\\u23f3 ';
              _updateThinkingBase(icon + msg);
              _addThinkingStep(msg);
              // Also show tool badge for 🔧 status messages (these are tool executions)
              if (msg.startsWith('\\U0001f527') && !firstToken) {{
                // Tool ran and we're already showing the response — add a badge
              }} else if (msg.startsWith('\\U0001f527')) {{
                const toolName = msg.replace(/^\\U0001f527\\s*/, '').replace(/\\.\\.\\..*$/, '').trim();
                if (toolName) {{
                  if (!toolBadgesEl) {{
                    toolBadgesEl = document.createElement('div');
                    toolBadgesEl.className = 'tool-badges';
                    messagesEl.insertBefore(toolBadgesEl, assistantEl);
                  }}
                  const badge = document.createElement('span');
                  badge.className = 'tool-badge';
                  badge.textContent = toolName;
                  toolBadgesEl.appendChild(badge);
                  messagesEl.scrollTop = messagesEl.scrollHeight;
                }}
              }}
            }}
          }} catch (parseErr) {{}}
        }}
      }}

      // Guaranteed cleanup: remove thinking indicator and show the response bubble
      // even if the stream closed without sending a 'done' event or any tokens.
      _removeThinking();
      assistantEl.style.display = '';
      if (!assistantText && assistantEl.className.indexOf('error') === -1) {{
        assistantEl.textContent = '...';
      }}

      // Save to history
      if (assistantText) {{
        addToHistory('assistant', assistantText);
        // Show confirmation buttons if needed
        showConfirmationButtons(assistantEl, assistantText);
      }}

      // Auto-reload if write tool modified current page
      if (writeToolCalled && ctx.type) {{
        const shouldReload = (ctx.type === 'automation' && ctx.id) || (ctx.type === 'script' && ctx.id) || ctx.type === 'dashboard';
        if (shouldReload) {{
          addMessage('reload-notice', T.page_reload, false);
          setTimeout(() => window.location.reload(), 2500);
        }}
      }}

    }} catch (err) {{
      _removeThinking();
      if (err.name === 'AbortError') {{
        // User aborted
      }} else {{
        addMessage('error', T.error_connection, false);
        console.error('Chat bubble error:', err);
      }}
    }} finally {{
      isStreaming = false;
      currentAbortController = null;
      sendBtn.innerHTML = '&#9654;';
      sendBtn.className = 'input-btn send-btn';
      sendBtn.disabled = false;
    }}
  }}

  // ---- Restore message history on load ----
  async function restoreHistory() {{
    const history = loadHistory();
    console.log('[Bubble] Restored history:', history.length, 'messages');
    if (history.length > 0) {{
      // Restore from localStorage
      const recent = history.slice(-20);
      recent.forEach(m => {{
        addMessage(m.role, m.text, m.role === 'assistant');
      }});
      console.log('[Bubble] Loaded', recent.length, 'recent messages from localStorage');
      return;
    }}
    // localStorage empty — try loading from server for current session
    try {{
      const sid = getSessionId();
      const resp = await fetch(API_BASE + '/api/conversations/' + encodeURIComponent(sid), {{credentials:'same-origin'}});
      if (resp.ok) {{
        const data = await resp.json();
        if (data.messages && data.messages.length > 0) {{
          const newHistory = [];
          const recent = data.messages.slice(-20);
          recent.forEach(m => {{
            if (m.role === 'user' || m.role === 'assistant') {{
              addMessage(m.role, m.content, m.role === 'assistant');
              newHistory.push({{ role: m.role, text: m.content, ts: Date.now() }});
            }}
          }});
          saveHistory(newHistory);
          console.log('[Bubble] Loaded', recent.length, 'messages from server');
        }}
      }}
    }} catch(e) {{
      console.warn('[Bubble] Could not restore from server:', e);
    }}
  }}
  restoreHistory();

  // ---- Addon Health Check: Remove bubble if addon is down ----
  let addonHealthCheckFails = 0;
  const MAX_FAILS = 2;
  async function checkAddonHealth() {{
    try {{
      const resp = await fetch(API_BASE + '/api/status', {{
        method: 'GET',
        credentials: 'same-origin',
        timeout: 3000
      }});
      if (resp.ok) {{
        addonHealthCheckFails = 0;  // Reset counter on success
        console.log('[Bubble] Addon health: OK');
      }} else {{
        addonHealthCheckFails++;
        console.warn('[Bubble] Addon health check failed:', resp.status);
        if (addonHealthCheckFails >= MAX_FAILS) {{
          removeBubbleFromDOM();
        }}
      }}
    }} catch (error) {{
      addonHealthCheckFails++;
      console.warn('[Bubble] Addon health check error:', error);
      if (addonHealthCheckFails >= MAX_FAILS) {{
        removeBubbleFromDOM();
      }}
    }}
  }}

  function removeBubbleFromDOM() {{
    console.log('[Bubble] Addon unreachable, removing bubble from DOM');
    const root = document.getElementById('ha-claude-bubble');
    if (root) {{
      root.remove();
      clearInterval(healthCheckInterval);
    }}
  }}

  // Start health check every 30 seconds
  const healthCheckInterval = setInterval(checkAddonHealth, 30000);
  checkAddonHealth(); // Do first check immediately

  // ---- Multi-tab sync: listen for messages from other tabs ----
  if (bc) {{
    bc.onmessage = (event) => {{
      const {{ type, role, text }} = event.data || {{}};
      if (type === 'new-message' && role && text) {{
        // Add message from other tab
        addMessage(role, text, role === 'assistant');
      }} else if (type === 'clear') {{
        messagesEl.innerHTML = '';
      }}
    }};
  }}

  // ---- Agent/Provider Selector ----
  let agentData = null; // cached response from /api/get_models
  let _syncProvider = '';  // last known provider (for cross-UI polling)
  let _syncModel = '';     // last known model   (for cross-UI polling)

  async function loadAgents() {{
    try {{
      const resp = await fetch(API_BASE + '/api/get_models', {{credentials:'same-origin'}});
      if (!resp.ok) return;
      agentData = await resp.json();
      if (!agentData.success) return;

      // Populate agent select if agents available
      if (agentSelect && Array.isArray(agentData.agents) && agentData.agents.length >= 1) {{
        agentSelect.innerHTML = '';
        agentData.agents.forEach(a => {{
          const opt = document.createElement('option');
          opt.value = a.id;
          const ident = a.identity || {{}};
          opt.textContent = (ident.emoji || '\U0001f916') + ' ' + (ident.name || a.id);
          if (agentData.active_agent && a.id === agentData.active_agent) opt.selected = true;
          agentSelect.appendChild(opt);
        }});
        agentSelect.style.display = '';
      }} else if (agentSelect) {{
        agentSelect.style.display = 'none';
      }}

      // Populate provider select — web providers always last with warning label
      providerSelect.innerHTML = '';
      const allProv = agentData.available_providers || [];
      const normalProv = allProv.filter(p => !p.web);
      const webProv = allProv.filter(p => p.web);
      normalProv.concat(webProv).forEach(p => {{
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.web ? '\u26a0\ufe0f ' + p.name + ' (Web)' : p.name;
        if (p.id === agentData.current_provider) opt.selected = true;
        providerSelect.appendChild(opt);
      }});

      // Populate models for current provider
      populateModels(agentData.current_provider);
      // Sync card-panel provider mirror (if open)
      if (_cardProvSel) {{
        _cardProvSel.innerHTML = '';
        Array.from(providerSelect.options).forEach(o => {{
          const c = document.createElement('option');
          c.value = o.value; c.textContent = o.textContent;
          if (o.selected) c.selected = true;
          _cardProvSel.appendChild(c);
        }});
      }}
      // Sync card-panel agent mirror (if open)
      if (_cardAgentSel) {{
        if (agentSelect && agentSelect.style.display !== 'none' && agentSelect.options.length) {{
          _cardAgentSel.innerHTML = '';
          Array.from(agentSelect.options).forEach(o => {{
            const c = document.createElement('option');
            c.value = o.value; c.textContent = o.textContent;
            if (o.selected) c.selected = true;
            _cardAgentSel.appendChild(c);
          }});
          _cardAgentSel.style.display = '';
        }} else {{
          _cardAgentSel.style.display = 'none';
        }}
      }}
      // Track for cross-UI sync polling
      _syncProvider = agentData.current_provider || '';
      _syncModel    = agentData.current_model_technical || '';
    }} catch(e) {{
      console.warn('[Amira] Could not load agents:', e);
      // Retry once after 2s (companion app may need time to establish ingress session)
      if (!_ingressSessionOk) {{
        setTimeout(async () => {{
          await _ensureIngressSession();
          loadAgents();
        }}, 2000);
      }}
    }}
  }}

  function populateModels(provider) {{
    if (!agentData) return;
    modelSelect.innerHTML = '';
    const techModels = (agentData.models_technical || {{}})[provider] || [];
    const dispModels = (agentData.models || {{}})[provider] || [];
    techModels.forEach((tech, i) => {{
      const opt = document.createElement('option');
      opt.value = tech;
      opt.textContent = dispModels[i] || tech;
      if (tech === agentData.current_model_technical) opt.selected = true;
      modelSelect.appendChild(opt);
    }});
    // Sync card-panel model mirror (if open)
    if (_cardModSel) {{
      _cardModSel.innerHTML = '';
      Array.from(modelSelect.options).forEach(o => {{
        const c = document.createElement('option');
        c.value = o.value; c.textContent = o.textContent;
        if (o.selected) c.selected = true;
        _cardModSel.appendChild(c);
      }});
    }}
  }}

  function _showTierWarning(resp) {{
    if (!resp || !resp.tier_limited || !resp.tier_warning_msg) return;
    addMessage('system', resp.tier_warning_msg, false);
  }}

  // ---- Session connected bar (claude_web, github_copilot, openai_codex) ----
  const _scBar    = document.getElementById('haSessionConnBar');
  const _scLabel  = document.getElementById('haSessionConnLabel');
  const _scDetail = document.getElementById('haSessionConnDetail');
  const _scDisc   = document.getElementById('haSessionConnDisc');
  let   _scDiscHandler = null;

  function _showSessionBar(label, detail, onDisconnect) {{
    if (!_scBar) return;
    if (_scLabel)  _scLabel.textContent  = label;
    if (_scDetail) _scDetail.textContent = detail || '';
    // Replace disconnect handler
    if (_scDiscHandler) _scDisc.removeEventListener('click', _scDiscHandler);
    _scDiscHandler = onDisconnect;
    if (_scDisc) _scDisc.addEventListener('click', _scDiscHandler);
    _scBar.style.display = 'flex';
  }}

  function _hideSessionBar() {{
    if (_scBar) _scBar.style.display = 'none';
  }}

  async function checkAndShowSessionStatus(provider) {{
    try {{
      if (provider === 'claude_web' || provider === 'claude_web_native') {{
        const r = await fetch(API_BASE + '/api/session/claude_web/status', {{credentials:'same-origin'}});
        const d = await r.json();
        if (d.configured) {{
          const detail = d.age_days != null ? 'connesso da ' + d.age_days + 'g' : 'connesso';
          _showSessionBar('\U0001F517 Claude Web', detail, async () => {{
            if (!confirm('Disconnettere Claude Web? Dovrai reinserire la session key.')) return;
            await fetch(API_BASE + '/api/session/claude_web/clear', {{method:'POST', credentials:'same-origin'}}).catch(()=>{{}});
            _hideSessionBar();
            addMessage('system', '\u274C Claude Web disconnesso.', false);
          }});
        }} else {{
          _hideSessionBar();
        }}
      }} else if (provider === 'github_copilot') {{
        const r = await fetch(API_BASE + '/api/oauth/copilot/status', {{credentials:'same-origin'}});
        const d = await r.json();
        if (d.configured) {{
          const detail = d.age_days != null ? 'connesso da ' + d.age_days + 'g' : 'connesso';
          _showSessionBar('\U0001F517 GitHub Copilot', detail, async () => {{
            if (!confirm('Disconnettere GitHub Copilot?')) return;
            await fetch(API_BASE + '/api/oauth/copilot/revoke', {{method:'POST', credentials:'same-origin'}}).catch(()=>{{}});
            _hideSessionBar();
            addMessage('system', '\u274C GitHub Copilot disconnesso.', false);
          }});
        }} else {{
          _hideSessionBar();
        }}
      }} else if (provider === 'openai_codex') {{
        const r = await fetch(API_BASE + '/api/oauth/codex/status', {{credentials:'same-origin'}});
        const d = await r.json();
        if (d.configured) {{
          let detail = 'connesso';
          if (d.account_id) detail = d.account_id;
          if (d.expires_in_seconds != null) {{
            const h = Math.floor(d.expires_in_seconds / 3600);
            const m = Math.floor((d.expires_in_seconds % 3600) / 60);
            const exp = h > 0 ? 'scade in ' + h + 'h ' + m + 'm' : 'scade in ' + m + 'm';
            detail += (d.account_id ? ' \u00b7 ' : '') + exp;
          }}
          _showSessionBar('\U0001F511 OpenAI Codex', detail, async () => {{
            if (!confirm('Disconnettere OpenAI Codex?')) return;
            await fetch(API_BASE + '/api/oauth/codex/revoke', {{method:'POST', credentials:'same-origin'}}).catch(()=>{{}});
            _hideSessionBar();
            addMessage('system', '\u274C OpenAI Codex disconnesso.', false);
          }});
        }} else {{
          _hideSessionBar();
        }}
      }} else {{
        _hideSessionBar();
      }}
    }} catch(e) {{ _hideSessionBar(); }}
  }}

  providerSelect.addEventListener('change', async () => {{
    const provider = providerSelect.value;
    populateModels(provider);
    try {{
      const resp = await fetch(API_BASE + '/api/set_model', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ provider }}),
        credentials: 'same-origin',
      }}).then(r => r.json()).catch(() => ({{}}));
      // Refresh to get new current_model_technical
      await loadAgents();
      // Show system message in chat
      const provLabel = providerSelect.options[providerSelect.selectedIndex]?.textContent || provider;
      const modLabel  = modelSelect.options[modelSelect.selectedIndex]?.textContent || modelSelect.value || '';
      addMessage('system', '\U0001F504 ' + provLabel + (modLabel ? ' \u2192 ' + modLabel : ''), false);
      _showTierWarning(resp);
      await checkAndShowSessionStatus(provider);
    }} catch(e) {{}}
  }});

  modelSelect.addEventListener('change', async () => {{
    const model = modelSelect.value;
    const provider = providerSelect.value;
    try {{
      const resp = await fetch(API_BASE + '/api/set_model', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ provider, model }}),
        credentials: 'same-origin',
      }}).then(r => r.json()).catch(() => ({{}}));
      // Show system message in chat
      const provLabel = providerSelect.options[providerSelect.selectedIndex]?.textContent || provider;
      const modLabel  = modelSelect.options[modelSelect.selectedIndex]?.textContent || model;
      addMessage('system', '\U0001F504 ' + provLabel + ' \u2192 ' + modLabel, false);
      _showTierWarning(resp);
    }} catch(e) {{}}
  }});

  if (agentSelect) {{
    agentSelect.addEventListener('change', async () => {{
      const agentId = agentSelect.value;
      try {{
        await fetch(API_BASE + '/api/agents/set', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ agent_id: agentId }}),
          credentials: 'same-origin',
        }});
        await loadAgents();
        // Show system message in chat
        const agentLabel = agentSelect.options[agentSelect.selectedIndex]?.textContent || agentId;
        addMessage('system', '\U0001F916 ' + agentLabel.trim(), false);
      }} catch(e) {{}}
    }});
  }}

  // ---- Register device to bubble tracking system ----
  async function registerDevice() {{
    try {{
      // Check if device already has an ID stored
      let deviceId = localStorage.getItem('ha-claude-device-id');
      if (!deviceId) {{
        // Generate stable device ID from various sources
        const now = Date.now().toString(36);
        const rand = Math.random().toString(36).substring(2, 10);
        deviceId = 'device-' + now + '-' + rand;
        localStorage.setItem('ha-claude-device-id', deviceId);
      }}

      // Determine device type
      const devType = isPhone ? 'phone' : isTablet ? 'tablet' : 'desktop';

      // Send registration to backend
      const resp = await fetch(API_BASE + '/api/bubble/devices', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          device_id: deviceId,
          device_name: '',  // Will be set by user later
          device_type: devType,
        }}),
        credentials: 'same-origin',
      }});
    }} catch(e) {{
      console.error('[Amira] Device registration error:', e);
    }}
  }}

  // Initial setup — ensure ingress session first (needed for companion app / tablet)
  (async () => {{
    await _ensureIngressSession();
    registerDevice();
    updateContextBar();
    await loadAgents();
    // Show session status for web/OAuth providers on first load
    const initialProvider = providerSelect.value;
    if (initialProvider) checkAndShowSessionStatus(initialProvider);
  }})();

  // Poll every 10s for model/provider changes made from chat_ui or other tabs
  setInterval(async () => {{
    try {{
      const r = await fetch(API_BASE + '/api/status', {{credentials:'same-origin'}});
      if (!r.ok) return;
      const d = await r.json();
      const sp = d.provider || '';
      const sm = d.model || '';
      if (sp && sm && (sp !== _syncProvider || sm !== _syncModel)) {{
        await loadAgents();
      }}
    }} catch(e) {{}}
  }}, 10000);

  console.log('[Amira] Chat bubble loaded (v3)');
}})();
"""
