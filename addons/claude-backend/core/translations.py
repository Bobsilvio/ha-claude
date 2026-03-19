"""Translation management for multi-language support."""

import os

# Global language setting
LANGUAGE = os.getenv("LANGUAGE", "en").lower()  # Supported: en, it, es, fr

LANGUAGE_TEXT = {
    "en": {
        "before": "Before",
        "after": "After",
        "respond_instruction": "Respond in English.",
        "show_yaml_rule": "CRITICAL: After CREATING or MODIFYING automations/scripts/dashboards, you MUST show the YAML code to the user in your response. Never skip this step.",
        "confirm_entity_rule": "CRITICAL: Before creating automations, ALWAYS use search_entities first to find the correct entity_id, then confirm with the user if multiple matches are found.",
        "confirm_delete_rule": "CRITICAL DESTRUCTIVE: Before DELETING or MODIFYING an automation/script/dashboard, you MUST:\n1. Use get_automations/get_scripts/get_dashboards to list all options\n2. Identify with CERTAINTY which one the user wants to delete/modify (by name/alias)\n3. Show the user WHICH ONE you will delete/modify\n4. ASK for EXPLICIT CONFIRMATION before proceeding\n5. NEVER delete/modify without confirmation - it's an IRREVERSIBLE operation",
        "example_vs_create_rule": "CRITICAL INTENT: Distinguish between 'show example' vs 'actually create':\n- If user asks for an \"example\", \"show me\", \"how to\", \"demo\" → respond with YAML code ONLY, do NOT call create_automation/create_script\n- If user explicitly asks to \"create\", \"save\", \"add\", \"make it real\" → call create_automation/create_script\n- When in doubt, show the YAML code first and ask if they want to create it",

        "err_github_budget_limit": "GitHub Models: budget limit reached for this account. Increase your GitHub budget/credit or pick another provider/model from the dropdown.",
        "err_github_request_too_large": "GitHub Models: the request is too long for the selected model{limit_part}. Try a shorter question or pick a larger model from the dropdown.",
        "err_api_usage_limits": "❌ API usage limits reached. Your access will be restored on {date}. Switch to another provider in the meantime.",
        "err_http_402": "❌ Insufficient balance. Top up your account credits at the provider's website, or switch to another provider.",
        "err_http_401": "Authentication failed (401). Check the provider API key/token.",
        "err_http_403": "Access denied (403). The request was blocked or the model is not available for this account/token.",
        "err_http_413": "Request too large (413). Reduce message/context length or switch model.",
        "err_http_429": "Rate limit (429). Wait a few seconds and retry, or switch model/provider.",
        "err_google_quota": "Google Gemini: quota exhausted (429). Wait a minute and retry, or switch to another model/provider.",
        "err_openai_quota": "❌ OpenAI quota exceeded. Your account has run out of credits. Check your plan and billing at platform.openai.com.",
        "err_loop_exhausted": "❌ The AI did not respond (request limit reached or repeated errors). Try again or switch model/provider.",

        "status_request_sent": "{provider}: sending request to the model...",
        "status_response_received": "{provider}: response received, processing...",
        "status_generating": "{provider}: generating the response...",
        "status_still_working": "{provider}: still working...",
        "status_actions_received": "Actions requested, executing...",
        "status_executing_tool": "{provider}: running tool {tool}...",
        "status_rate_limit_wait": "{provider}: rate limit reached, waiting...",
        "status_rate_limit_wait_seconds": "{provider}: rate limit, waiting {seconds}s...",

        "err_api_key_not_configured": "⚠️ API key for {provider_name} not configured. Set it in the add-on settings.",
        "err_provider_not_supported": "❌ Provider '{provider}' not supported. Choose: anthropic, openai, google, nvidia, github.",
        "err_provider_generic": "❌ Error {provider_name}: {error}",
        "err_api_key_not_configured_short": "API key not configured",
        "err_invalid_image_format": "Invalid image format",
        "err_nvidia_api_key": "NVIDIA API key not configured.",
        "err_nvidia_model_invalid": "Invalid NVIDIA model.",
        "err_nvidia_model_removed": "NVIDIA model {reason}: {model_id}. Removed from model list.",
        "err_response_blocked": "{provider}: response blocked by safety filters. Try rephrasing your request.",

        "status_analyzing": "Analyzing",
        "status_image_processing": "Processing image...",
        "status_context_preloaded": "Context preloaded...",
        "status_nvidia_model_removed": "⚠️ NVIDIA model not available (404). Removed from model list.",
        "status_tool_repair_retry": "Repaired tool state, retrying...",
        "status_token_params_retry": "Token parameters incompatible with model, retrying.",
        "status_github_format_retry": "GitHub model not recognized, retrying with alternative format.",
        "status_github_model_fallback": "Model not available on GitHub, switching to GPT-4o.",
        "status_rate_limit_waiting": "Rate limit reached, waiting...",
        "status_prompt_too_large": "Selected model has a low limit (prompt too large). Reducing context and retrying...",
        "status_user_cancelled": "Cancelled by user.",

        "write_op_success": "✅ Operation completed successfully!",
        "write_no_changes": "\nNo changes detected (content is identical).",
        "write_yaml_updated": "\n**Updated YAML:**",
        "write_yaml_created": "\n**Created YAML:**",
        "write_snapshot_created": "\n💾 Snapshot created: `{snapshot_id}`",

        "intent_modify_automation": "Modify automation",
        "intent_modify_script": "Modify script",
        "intent_create_dashboard": "Create dashboard",
        "intent_modify_dashboard": "Modify dashboard",
        "intent_config_edit": "Edit configuration",
        "intent_chat": "Chat",
        "intent_default": "Processing",

        "read_only_note": "**Read-only mode — no files were modified.**",

        "smart_context_script_found": "## YAML SCRIPT FOUND: \"{alias}\" (id: {sid})\n```yaml\n{yaml}```\nTo modify it use update_script with script_id='{sid}' and the fields to change.",
        "read_only_instruction": "READ-ONLY MODE: Show the user the complete YAML code in a yaml code block. At the end add the note: ",

        "dashboard_created_successfully": "Dashboard created successfully! Your ",
        "dashboard_sidebar_ready": "dashboard appears in the sidebar at /{path}",
        "dashboard_sidebar_failed": "HTML file is ready but sidebar integration failed",

        "err_tool_not_in_tier": "⚠️ The current model is in limited mode ({tier}) and does not support '{tool_name}'. Switch to a more powerful model (e.g. Claude, GPT-4o, Gemini) to use this feature.",
        "err_tool_not_in_tier_generic": "⚠️ The current model is in limited mode ({tier}) and does not support this feature. Switch to a more powerful model to access all features.",
        "err_malformed_tool_call": "⚠️ The model generated a malformed call for '{tool_name}'. Try rephrasing your request or switch to a more capable model.",
        "warn_tier_limited": "⚠️ Limited mode ({tier}): advanced features not available ({missing}). Switch to a more capable model.",
        "warn_no_tool_called": "⚠️ The model described a change but did not actually apply it. Nothing was modified in Home Assistant. Please try again.",
    },
    "it": {
        "before": "Prima",
        "after": "Dopo",
        "respond_instruction": "Rispondi sempre in Italiano.",
        "show_yaml_rule": "CRITICO: Dopo aver CREATO o MODIFICATO automazioni/script/dashboard, DEVI sempre mostrare il codice YAML al usuario in tua risposta. Nunca omitas este paso.",
        "confirm_entity_rule": "CRITICO: Antes de crear automazioni, USA SIEMPRE search_entities per trovare il corretto entity_id, poi confirma con l'utente se ci sono più risultati.",
        "confirm_delete_rule": "CRITICO DISTRUTTIVO: Antes de ELIMINARE o MODIFICARE un'automazione/script/dashboard, DEVI:\n1. Usar get_automations/get_scripts/get_dashboards per elencare tutte le opzioni\n2. Identificare con CERTEZZA quale l'utente vuole eliminare/modificare (per nome/alias)\n3. Mostrare al usuario CUÁL eliminarás/modificarás\n4. PEDIR CONFIRMACIÓN EXPLÍCITA antes de procedere\n5. NUNCA eliminar/modificare MAI senza conferma - è un'operazione IRREVERSIBILE",
        "example_vs_create_rule": "CRITICO INTENTO: Distingue tra 'mostra esempio' e 'crea effettivamente':\n- Se l'utente chiede un \"esempio\", \"mostrami\", \"come si fa\", \"demo\" → rispondi con il codice YAML SOLAMENTE, NON chiamare create_automation/create_script\n- Se l'utente chiede esplicitamente di \"creare\", \"salvare\", \"aggiungere\", \"rendilo reale\" → chiamare create_automation/create_script\n- En caso di dubbio, mostra prima il codice YAML e chiedi se vuole crearlo effettivamente",

        "err_github_budget_limit": "GitHub Models: limite budget raggiunto per questo account. Aumenta il budget/crédito su GitHub oppure seleziona un altro provider/modello dal menu in alto.",
        "err_github_request_too_large": "GitHub Models: richiesta troppo lunga per il modello selezionato{limit_part}. Prova a fare una domanda più corta, oppure scegli un modello più grande dal menu in alto.",
        "err_api_usage_limits": "❌ Limiti di utilizzo API raggiunti. Il tuo accesso verrà ripristinato il {date}. Nel frattempo passa a un altro provider.",
        "err_http_402": "❌ Credito insufficiente. Ricarica il saldo sul sito del provider, oppure passa a un altro provider.",
        "err_http_401": "Autenticazione fallita (401). Verifica la chiave/token del provider selezionato.",
        "err_http_403": "Accesso negato (403). La richiesta è stata bloccata oppure il modello non è disponibile per questo account/token.",
        "err_http_413": "Richiesta troppo grande (413). Riduci la lunghezza del messaggio/contesto o cambia modello.",
        "err_http_429": "Limite di velocità (429). Attendi qualche secondo e riprova, oppure cambia modello/provider.",
        "err_google_quota": "Google Gemini: quota esaurita (429). Attendi un minuto e riprova, oppure cambia modello/provider.",
        "err_openai_quota": "❌ Quota OpenAI esaurita. Il tuo account ha esaurito i crediti. Controlla il tuo piano e la fatturazione su platform.openai.com.",
        "err_loop_exhausted": "❌ L'IA non ha risposto (limite di round raggiunto o errori ripetuti). Riprova o cambia modello/provider.",

        "status_request_sent": "{provider}: invio richiesta al modello...",
        "status_response_received": "{provider}: risposta ricevuta, elaboro...",
        "status_generating": "{provider}: generando la risposta...",
        "status_still_working": "{provider}: ancora in elaborazione...",
        "status_actions_received": "Ho ricevuto una richiesta di azioni, eseguo...",
        "status_executing_tool": "{provider}: eseguo tool {tool}...",
        "status_rate_limit_wait": "{provider}: limite di velocità raggiunto, attendo...",
        "status_rate_limit_wait_seconds": "{provider}: limite di velocità, attendo {seconds}s...",

        "err_api_key_not_configured": "⚠️ Chiave API per {provider_name} non configurata. Impostala nelle impostazioni del componente aggiuntivo.",
        "err_provider_not_supported": "❌ Provider '{provider}' non supportato. Scegli tra: anthropic, openai, google, nvidia, github e altri.",
        "err_provider_generic": "❌ Errore {provider_name}: {error}",
        "err_api_key_not_configured_short": "Chiave API non configurata",
        "err_invalid_image_format": "Formato immagine non valido",
        "err_nvidia_api_key": "Chiave API NVIDIA non configurata.",
        "err_nvidia_model_invalid": "Modello NVIDIA non valido.",
        "err_nvidia_model_removed": "Modello NVIDIA {reason}: {model_id}. Rimosso dalla lista.",
        "err_response_blocked": "{provider}: risposta bloccata dai filtri di sicurezza. Prova a riformulare la richiesta.",

        "status_analyzing": "Analisi in corso",
        "status_image_processing": "Elaboro immagine...",
        "status_context_preloaded": "Contesto precaricato...",
        "status_nvidia_model_removed": "⚠️ Modello NVIDIA non disponibile (404). Rimosso dalla lista modelli.",
        "status_tool_repair_retry": "Stato strumenti ripristinato, nuovo tentativo...",
        "status_token_params_retry": "Parametri token incompatibili con il modello, nuovo tentativo.",
        "status_github_format_retry": "Modello GitHub non riconosciuto, nuovo tentativo con formato alternativo.",
        "status_github_model_fallback": "Modello non disponibile su GitHub, passaggio a GPT-4o.",
        "status_rate_limit_waiting": "Limite di velocità raggiunto, attendo...",
        "status_prompt_too_large": "Il modello selezionato ha un limite basso (prompt troppo grande). Riduco il contesto e riprovo...",
        "status_user_cancelled": "Annullato dall'utente.",

        "write_op_success": "✅ Operazione completata con successo!",
        "write_no_changes": "\nNessuna modifica rilevata (il contenuto è identico).",
        "write_yaml_updated": "\n**YAML aggiornato:**",
        "write_yaml_created": "\n**YAML creato:**",
        "write_snapshot_created": "\n💾 Snapshot creato: `{snapshot_id}`",

        "intent_modify_automation": "Modifica automazione",
        "intent_modify_script": "Modifica script",
        "intent_create_dashboard": "Crea dashboard",
        "intent_modify_dashboard": "Modifica dashboard",
        "intent_config_edit": "Modifica configurazione",
        "intent_chat": "Chat",
        "intent_default": "Elaborazione",

        "read_only_note": "**Modalità sola lettura — nessun file è stato modificato.**",

        "smart_context_script_found": "## YAML SCRIPT TROVATO: \"{alias}\" (id: {sid})\n```yaml\n{yaml}```\nPer modificarlo usa update_script con script_id='{sid}' e i campi da cambiare.",
        "read_only_instruction": "MODALITÀ SOLA LETTURA: Mostra all'utente il codice YAML completo in un code block yaml. Alla fine aggiungi la nota: ",

        "dashboard_created_successfully": "Dashboard creata con successo! ",
        "dashboard_sidebar_ready": "Il dashboard appare nella sidebar a /{path}",
        "dashboard_sidebar_failed": "File HTML pronto ma integrazione sidebar fallita",

        "err_tool_not_in_tier": "⚠️ Il modello attuale è in modalità ridotta ({tier}) e non supporta '{tool_name}'. Passa a un modello più potente (es. Claude, GPT-4o, Gemini) per usare questa funzione.",
        "err_tool_not_in_tier_generic": "⚠️ Il modello attuale è in modalità ridotta ({tier}) e non supporta questa funzione. Passa a un modello più potente per accedere a tutte le funzionalità.",
        "err_malformed_tool_call": "⚠️ Il modello ha generato una chiamata malformata per '{tool_name}'. Prova a riformulare la richiesta o passa a un modello più capace.",
        "warn_tier_limited": "⚠️ Modalità ridotta ({tier}): funzioni avanzate non disponibili ({missing}). Seleziona un modello più potente.",
        "warn_no_tool_called": "⚠️ Il modello ha descritto una modifica ma non l'ha eseguita. Nessuna modifica è stata applicata a Home Assistant. Riprova.",
    },
    "es": {
        "before": "Antes",
        "after": "Después",
        "respond_instruction": "Responde siempre en Español.",
        "show_yaml_rule": "CRÍTICO: Después de CREAR o MODIFICAR automatizaciones/scripts/dashboards, DEBES mostrar el código YAML al usuario en tu respuesta. Nunca omitas este paso.",
        "confirm_entity_rule": "CRÍTICO: Antes de crear automatizaciones, USA SIEMPRE search_entities para encontrar el entity_id correcto, luego confirma con el usuario si hay múltiples resultados.",
        "confirm_delete_rule": "CRÍTICO DESTRUCTIVO: Antes de ELIMINAR o MODIFICAR una automatización/script/dashboard, DEBES:\n1. Usar get_automations/get_scripts/get_dashboards para listar todas las opciones\n2. Identificar con CERTEZZA cuál quiere eliminar/modificar el usuario (por nombre/alias)\n3. Mostrar al usuario CUÁL eliminarás/modificarás\n4. PEDIR CONFIRMACIÓN EXPLÍCITA antes de proceder\n5. NUNCA eliminar/modificar sin confirmación - es una operación IRREVERSIBLE",
        "example_vs_create_rule": "CRÍTICO INTENCIÓN: Distingue entre 'mostrar ejemplo' y 'crear realmente':\n- Si el usuario pide un \"esempio\", \"mostrami\", \"cómo se hace\", \"demo\" → responde con el código YAML SOLAMENTE, NO llames create_automation/create_script\n- Si el usuario pide esplicitamente di \"crear\", \"guardar\", \"añadir\", \"hazlo real\" → llama create_automation/create_script\n- En caso de duda, muestra primero el código YAML y pregunta si quiere crearlo realmente",

        "err_github_budget_limit": "GitHub Models: se ha alcanzado el límite de presupuesto de esta cuenta. Aumenta el presupuesto/crédito en GitHub o elige otro proveedor/modelo en el desplegable.",
        "err_github_request_too_large": "GitHub Models: la solicitud es demasiado larga para el modelo seleccionado{limit_part}. Prueba con una pregunta más corta o elige un modelo más grande en el desplegable.",
        "err_http_401": "Autenticación fallida (401). Verifica la clave/token del proveedor.",
        "err_http_403": "Acceso denegado (403). La solicitud fue bloqueada o el modelo no está disponible para esta cuenta/token.",
        "err_api_usage_limits": "❌ Límites de uso de API alcanzados. Tu acceso se restablecerá el {date}. Cambia a otro proveedor mientras tanto.",
        "err_http_413": "Solicitud demasiado grande (413). Reduce el mensaje/contexto o cambia de modelo.",
        "err_http_429": "Límite de tasa (429). Espera unos segundos y reintenta, o cambia de modelo/proveedor.",
        "err_google_quota": "Google Gemini: cuota agotada (429). Espera un minuto y reintenta, o cambia de modelo/proveedor.",
        "err_openai_quota": "❌ Quota de OpenAI agotada. Tu cuenta se ha quedado sin créditos. Revisa tu plan y facturación en platform.openai.com.",
        "err_loop_exhausted": "❌ La IA no respondió (limite de rondas alcanzado o errores repetidos). Inténtalo de nuevo o cambia de modelo/proveedor.",

        "status_request_sent": "{provider} : envoi de la requête au modèle...",
        "status_response_received": "{provider} : réponse reçue, traitement...",
        "status_generating": "{provider} : génération de la réponse...",
        "status_still_working": "{provider} : toujours en cours...",
        "status_actions_received": "Acciones solicitadas, ejecutando...",
        "status_executing_tool": "{provider} : exécution de l'outil {tool}...",
        "status_rate_limit_wait": "{provider} : limite de débit alcanzado, attente...",
        "status_rate_limit_wait_seconds": "{provider} : limite de débit, attente {seconds}s...",

        "err_api_key_not_configured": "⚠️ Clé API pour {provider_name} non configurée. Configurez-la dans les paramètres de l'add-on.",
        "err_provider_not_supported": "❌ Proveedor '{provider}' non soportado. Elige: anthropic, openai, google, nvidia, github.",
        "err_provider_generic": "❌ Errore {provider_name}: {error}",
        "err_api_key_not_configured_short": "Clé API non configurée",
        "err_invalid_image_format": "Formato de imagen no válido",
        "err_nvidia_api_key": "Clé API NVIDIA non configurée.",
        "err_nvidia_model_invalid": "Modèle NVIDIA non valide.",
        "err_nvidia_model_removed": "Modèle NVIDIA {reason}: {model_id}. Eliminado de la lista.",
        "err_response_blocked": "{provider}: risposta bloccata dai filtri di sicurezza. Prova a riformulare la richiesta.",

        "status_analyzing": "Analizando",
        "status_image_processing": "Procesando imagen...",
        "status_context_preloaded": "Contesto precargado...",
        "status_nvidia_model_removed": "⚠️ Modèle NVIDIA non disponible (404). Eliminado de la liste des modèles.",
        "status_tool_repair_retry": "État des outils réparé, nouvelle tentative...",
        "status_token_params_retry": "Paramètres de token incompatibles avec le modèle, nouvelle tentative.",
        "status_github_format_retry": "Modèle GitHub non riconosciuto, nouvelle tentative avec format alternatif.",
        "status_github_model_fallback": "Modèle non disponible su GitHub, passage à GPT-4o.",
        "status_rate_limit_waiting": "Límite de débit alcanzado, en attente...",
        "status_prompt_too_large": "Il modello selezionato ha un limite basso (prompt troppo grande). Riduco il contesto e riprovo...",
        "status_user_cancelled": "Annulé par l'utilisateur.",

        "write_op_success": "✅ Operazione completata con successo!",
        "write_no_changes": "\nNessuna modifica rilevata (il contenuto è identico).",
        "write_yaml_updated": "\n**YAML aggiornato:**",
        "write_yaml_created": "\n**YAML creato:**",
        "write_snapshot_created": "\n💾 Snapshot creato: `{snapshot_id}`",

        "intent_modify_automation": "Modificar automación",
        "intent_modify_script": "Modificar script",
        "intent_create_dashboard": "Crear dashboard",
        "intent_modify_dashboard": "Modificar dashboard",
        "intent_config_edit": "Modificar configuración",
        "intent_chat": "Chat",
        "intent_default": "Procesando",

        "read_only_note": "**Modalità sola lettura — nessun file è stato modificato.**",

        "smart_context_script_found": "## YAML SCRIPT TROVATO: \"{alias}\" (id: {sid})\n```yaml\n{yaml}```\nPer modificarlo usa update_script con script_id='{sid}' e i campi a cambiar.",
        "read_only_instruction": "MODE LECTURE SEULE: Muestra al usuario el código YAML completo en un code block yaml. Al final añade la nota: ",

        "dashboard_created_successfully": "Dashboard creata con successo! ",
        "dashboard_sidebar_ready": "Il dashboard appare nella sidebar a /{path}",
        "dashboard_sidebar_failed": "File HTML pronto ma integrazione sidebar fallita",

        "err_tool_not_in_tier": "⚠️ El modelo actual está en modo reducido ({tier}) y no soporta '{tool_name}'. Cambia a un modelo más potente (ej. Claude, GPT-4o, Gemini) para usar esta función.",
        "err_tool_not_in_tier_generic": "⚠️ El modelo actual está en modo reducido ({tier}) y no soporta esta función. Cambia a un modelo más potente para acceder a todas las funciones.",
        "err_malformed_tool_call": "⚠️ El modelo generó una llamada malformada para '{tool_name}'. Intenta reformular tu solicitud o cambia a un modelo más capaz.",
        "warn_tier_limited": "⚠️ Modo reducido ({tier}): funciones avanzadas no disponibles ({missing}). Selecciona un modelo más potente.",
        "warn_no_tool_called": "⚠️ El modelo describió un cambio pero no lo aplicó. No se modificó nada en Home Assistant. Inténtalo de nuevo.",
    },
    "fr": {
        "before": "Avant",
        "after": "Après",
        "respond_instruction": "Réponds toujours en Français.",
        "show_yaml_rule": "CRITIQUE: Après avoir CRÉÉ ou MODIFIÉ des automatisations/scripts/dashboards, tu DOIS toujours montrer le code YAML à l'utilisateur dans ta réponse. Ne saute jamais cette étape.",
        "confirm_entity_rule": "CRITIQUE: Avant de créer des automatisations, UTILISE TOUJOURS search_entities pour trouver le bon entity_id, puis confirme avec l'utilisateur s'il y a plusieurs résultats.",
        "confirm_delete_rule": "CRITIQUE DESTRUCTIF: Avant de SUPPRIMER ou MODIFIER une automatisation/script/dashboard, tu DOIS:\n1. Utiliser get_automations/get_scripts/get_dashboards pour lister toutes les options\n2. Identifier avec CERTITUDE laquelle l'utilisateur veut supprimer/modifier (par nom/alias)\n3. Montrer à l'utilisateur LAQUELLE tu vas supprimer/modifier\n4. DEMANDER une CONFIRMACIÓN EXPLÍCITA avant de proceder\n5. NUNCA supprimer/modifier sans confirmation - c'est une opération IRRÉVERSIBLE",
        "example_vs_create_rule": "CRITIQUE INTENTION: Distingue entre 'mostrar ejemplo' et 'créer réellement':\n- Si l'utilisateur demande un \"exemple\", \"mostrami\", \"comment faire\", \"demo\" → réponds avec le code YAML SOLAMENTE, NON chiamare create_automation/create_script\n- Si l'utilisateur demande esplicitement de \"créer\", \"sauvegarder\", \"ajouter\", \"rends-le réel\" → chiamare create_automation/create_script\n- En cas de doute, montre d'abord le code YAML et demande s'il veut le créer réellement",

        "err_github_budget_limit": "GitHub Models : limite de budget atteinte pour ce compte. Augmente le budget/crédit GitHub ou choisis un autre fournisseur/modello dans la liste déroulante.",
        "err_github_request_too_large": "GitHub Models : la requête est trop longue pour le modèle sélectionné{limit_part}. Essaie une question plus courte ou choisis un modèle plus grand dans la liste déroulante.",
        "err_http_401": "Échec d'authentification (401). Vérifie la clé/le jeton du fournisseur.",
        "err_http_403": "Accès refusé (403). La requête a été bloquée ou le modèle n'est pas disponible pour ce compte/jeton.",
        "err_api_usage_limits": "❌ Limites d'utilisation API atteintes. Votre accès sera rétabli le {date}. Changez de fournisseur en attendant.",
        "err_http_413": "Requête trop volumineuse (413). Réduis le message/le contexte ou change de modèle.",
        "err_http_429": "Limite de débit (429). Attends quelques secondes et réessaie, ou change de modèle/fournisseur.",
        "err_google_quota": "Google Gemini : quota épuisé (429). Attends une minute et réessaie, ou change de modèle/fournisseur.",
        "err_openai_quota": "❌ Quota OpenAI épuisée. Ton compte n'a plus de crédits. Vérifie ton plan et ta facturation sur platform.openai.com.",
        "err_loop_exhausted": "❌ L'IA n'a pas répondu (limite de rounds atteinte ou erreurs répétées). Réessaie ou change de modèle/fournisseur.",

        "status_request_sent": "{provider} : envoi de la requête au modèle...",
        "status_response_received": "{provider} : réponse reçue, traitement...",
        "status_generating": "{provider} : génération de la réponse...",
        "status_still_working": "{provider} : toujours en cours...",
        "status_actions_received": "Acciones solicitadas, ejecutando...",
        "status_executing_tool": "{provider} : exécution de l'outil {tool}...",
        "status_rate_limit_wait": "{provider} : limite de débit alcanzado, attente...",
        "status_rate_limit_wait_seconds": "{provider} : limite de débit, attente {seconds}s...",

        "err_api_key_not_configured": "⚠️ Clé API pour {provider_name} non configurée. Configurez-la dans les paramètres de l'add-on.",
        "err_provider_not_supported": "❌ Fournisseur '{provider}' non pris en charge. Choisissez : anthropic, openai, google, nvidia, github.",
        "err_provider_generic": "❌ Erreur {provider_name} : {error}",
        "err_api_key_not_configured_short": "Clé API non configurée",
        "err_invalid_image_format": "Format d'image non valide",
        "err_nvidia_api_key": "Clé API NVIDIA non configurée.",
        "err_nvidia_model_invalid": "Modèle NVIDIA non valide.",
        "err_nvidia_model_removed": "Modèle NVIDIA {reason} : {model_id}. Retiré de la liste.",
        "err_response_blocked": "{provider}: risposta bloccata dai filtri di sicurezza. Prova a riformulare la richiesta.",

        "status_analyzing": "Analyse en cours",
        "status_image_processing": "Procesando imagen...",
        "status_context_preloaded": "Contesto precargado...",
        "status_nvidia_model_removed": "⚠️ Modèle NVIDIA non disponible (404). Retiré de la liste des modèles.",
        "status_tool_repair_retry": "État des outils réparé, nouvelle tentative...",
        "status_token_params_retry": "Paramètres de token incompatibles avec le modèle, nouvelle tentative.",
        "status_github_format_retry": "Modèle GitHub non riconosciuto, nouvelle tentative avec format alternatif.",
        "status_github_model_fallback": "Modèle non disponible su GitHub, passage à GPT-4o.",
        "status_rate_limit_waiting": "Límite de débit alcanzado, en attente...",
        "status_prompt_too_large": "Il modello selezionato ha un limite basso (prompt troppo grande). Riduco il contesto e riprovo...",
        "status_user_cancelled": "Annulé par l'utilisateur.",

        "write_op_success": "✅ Opération réalisée avec succès !",
        "write_no_changes": "\nAucun changement détecté (le contenu est identique).",
        "write_yaml_updated": "\n**YAML mis à jour :**",
        "write_yaml_created": "\n**YAML créé :**",
        "write_snapshot_created": "\n💾 Snapshot créé : `{snapshot_id}`",

        "intent_modify_automation": "Modifier une automatisation",
        "intent_modify_script": "Modifier un script",
        "intent_create_dashboard": "Créer un dashboard",
        "intent_modify_dashboard": "Modifier un dashboard",
        "intent_config_edit": "Modifier la configuration",
        "intent_chat": "Chat",
        "intent_default": "Traitement",

        "read_only_note": "**Mode lecture seule — aucun fichier n'a été modifié.**",

        "smart_context_script_found": "## YAML SCRIPT TROUVÉ : \"{alias}\" (id: {sid})\n```yaml\n{yaml}```\nPour le modifier, utilise update_script avec script_id='{sid}' et les champs à changer.",
        "read_only_instruction": "MODE LECTURE SEULE : Montre à l'utilisateur le code YAML complet dans un code block yaml. À la fin ajoute la note : ",

        "dashboard_created_successfully": "Dashboard créé avec succès ! Ton ",
        "dashboard_sidebar_ready": "dashboard apparaît dans la barre latérale à /{path}",
        "dashboard_sidebar_failed": "Le fichier HTML est prêt mais l'intégration dans la barre latérale a échoué",

        "err_tool_not_in_tier": "⚠️ Le modèle actuel est en mode réduit ({tier}) et ne supporte pas '{tool_name}'. Passe à un modèle plus puissant (ex. Claude, GPT-4o, Gemini) pour utiliser cette fonction.",
        "err_tool_not_in_tier_generic": "⚠️ Le modèle actuel est en mode réduit ({tier}) et ne supporte pas cette fonction. Passe à un modèle plus puissant pour accéder à toutes les fonctionnalités.",
        "err_malformed_tool_call": "⚠️ Le modèle a généré un appel malformé pour '{tool_name}'. Essaie de reformuler ta demande ou passe à un modèle plus capable.",
        "warn_tier_limited": "⚠️ Mode réduit ({tier}): fonctions avancées non disponibles ({missing}). Sélectionne un modèle plus puissant.",
        "warn_no_tool_called": "⚠️ Le modèle a décrit une modification mais ne l'a pas exécutée. Rien n'a été modifié dans Home Assistant. Réessaie.",
    }
}


def get_lang_text(key: str) -> str:
    """Get language-specific text."""
    return LANGUAGE_TEXT.get(LANGUAGE, LANGUAGE_TEXT["en"]).get(key, "")


def tr(key: str, default: str = "", **kwargs) -> str:
    """Translate a key and apply simple str.format() interpolation."""
    txt = get_lang_text(key) or default
    if not kwargs:
        return txt
    try:
        return txt.format(**kwargs)
    except Exception:
        return txt
