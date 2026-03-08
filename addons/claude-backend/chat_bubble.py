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


def get_chat_bubble_js(ingress_url: str, language: str = "en", show_bubble: bool = True, show_card_button: bool = True) -> str:
    """Generate the floating chat bubble JavaScript module.

    Args:
        ingress_url: Addon ingress URL prefix (e.g. '/api/hassio_ingress/<token>')
        language: User language (en/it/es/fr)
        show_bubble: If False, the floating bubble button is hidden.
        show_card_button: If False, the Amira button in the card editor is hidden.

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
            "channel_agents": "Channel Agents",
            "channel_default": "Default (active)",
            "channel_telegram": "Telegram",
            "channel_whatsapp": "WhatsApp",
            "channel_saved": "Saved",
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
            "channel_agents": "Agent per canale",
            "channel_default": "Predefinito (attivo)",
            "channel_telegram": "Telegram",
            "channel_whatsapp": "WhatsApp",
            "channel_saved": "Salvato",
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
            "channel_agents": "Agentes por canal",
            "channel_default": "Predeterminado (activo)",
            "channel_telegram": "Telegram",
            "channel_whatsapp": "WhatsApp",
            "channel_saved": "Guardado",
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
            "channel_agents": "Agents par canal",
            "channel_default": "Par d\u00e9faut (actif)",
            "channel_telegram": "Telegram",
            "channel_whatsapp": "WhatsApp",
            "channel_saved": "Enregistr\u00e9",
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

  console.log('[Amira] Bubble JS executing — bubble={show_bubble}, card_btn={show_card_button}');

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
    window.addEventListener('error', function(ev) {{
      console.error('[Amira Bubble JS Error]', ev.message, 'at', ev.filename, ev.lineno + ':' + ev.colno);
      _amiraBubbleSendError({{ level: 'error', message: String(ev.message), source: ev.filename || '', line: ev.lineno, col: ev.colno, stack: ev.error && ev.error.stack || '', timestamp: new Date().toISOString(), ui: 'bubble' }});
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
  const T = {__import__('json').dumps(t, ensure_ascii=False)};
  const VOICE_LANG = '{voice_lang}';
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

    let m = path.match(/\\/config\\/automation\\/edit\\/([^/]+)/);
    if (m) {{ ctx.type = 'automation'; ctx.id = m[1]; ctx.label = T.context_automation + ': ' + m[1]; return ctx; }}

    m = path.match(/\\/config\\/automation\\/trace\\/([^/]+)/);
    if (m) {{ ctx.type = 'automation'; ctx.id = m[1]; ctx.label = T.context_automation + ' (trace): ' + m[1]; return ctx; }}

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
        <button id="haChannelAgentsBtn" title="${{T.channel_agents}}" style="background:none;border:none;cursor:pointer;font-size:14px;padding:2px 4px;line-height:1;flex-shrink:0;opacity:0.6;">&#9881;</button>
      </div>
      <div id="haChannelAgentsPanel" style="display:none;padding:8px 12px;border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--secondary-background-color,#f5f5f5);flex-shrink:0;">
        <div style="font-size:11px;font-weight:600;margin-bottom:6px;color:var(--primary-text-color,#333);">&#128225; ${{T.channel_agents}}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <label style="display:flex;align-items:center;gap:4px;font-size:11px;color:var(--secondary-text-color,#666);flex:1;min-width:140px;">
            ${{T.channel_telegram}}
            <select id="haChannelTelegramAgent" style="flex:1;font-size:11px;padding:2px 4px;border-radius:4px;border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);color:var(--primary-text-color,#333);cursor:pointer;min-width:80px;"></select>
          </label>
          <label style="display:flex;align-items:center;gap:4px;font-size:11px;color:var(--secondary-text-color,#666);flex:1;min-width:140px;">
            ${{T.channel_whatsapp}}
            <select id="haChannelWhatsappAgent" style="flex:1;font-size:11px;padding:2px 4px;border-radius:4px;border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);color:var(--primary-text-color,#333);cursor:pointer;min-width:80px;"></select>
          </label>
        </div>
        <div id="haChannelAgentsSaved" style="display:none;font-size:10px;color:#4caf50;margin-top:4px;">&#10003; ${{T.channel_saved}}</div>
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
  const channelAgentsBtn = document.getElementById('haChannelAgentsBtn');
  const channelAgentsPanel = document.getElementById('haChannelAgentsPanel');
  const channelTelegramSel = document.getElementById('haChannelTelegramAgent');
  const channelWhatsappSel = document.getElementById('haChannelWhatsappAgent');
  const channelSavedMsg = document.getElementById('haChannelAgentsSaved');

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

  // Global copy helper — clipboard API needs HTTPS; fallback with textarea for HTTP
  window.__amiraCopyCode = function(btn) {{
    var code = btn.parentElement.querySelector('code');
    if (!code) return;
    var txt = code.textContent;
    function ok() {{ btn.textContent = 'Copiato!'; setTimeout(function(){{ btn.textContent = 'Copia'; }}, 1500); }}
    function fallback() {{
      var ta = document.createElement('textarea');
      ta.value = txt; ta.style.cssText = 'position:fixed;left:-9999px;';
      document.body.appendChild(ta); ta.select();
      try {{ document.execCommand('copy'); ok(); }} catch(e) {{ btn.textContent = 'Errore'; }}
      document.body.removeChild(ta);
    }}
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(txt).then(ok).catch(fallback);
    }} else {{ fallback(); }}
  }};

  function _renderInlineMd(text) {{
    // Fenced code blocks: ```lang + newline + content + ``` -> styled pre with copy button
    const codeBlocks = [];
    text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, function(m, lang, code) {{
      const escaped = code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      const placeholder = '___CODEBLOCK_' + codeBlocks.length + '___';
      codeBlocks.push('<div style="position:relative;margin:6px 0;">'
        + '<button onclick="window.__amiraCopyCode(this)" style="position:absolute;top:6px;right:6px;background:#334155;border:1px solid #475569;color:#e2e8f0;border-radius:4px;padding:3px 10px;font-size:11px;cursor:pointer;font-weight:500;letter-spacing:0.3px;transition:background .15s;z-index:1;" onmouseover="this.style.background=\\'#475569\\'" onmouseout="this.style.background=\\'#334155\\'">Copia</button>'
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
    const hdrClose = document.createElement('button');
    hdrClose.textContent = '✕';
    hdrClose.style.cssText = 'background:none;border:none;color:#fff;cursor:pointer;font-size:16px;padding:0 4px;line-height:1;margin-left:auto;';
    hdrClose.onclick = closeCardPanel;
    hdr.appendChild(hdrTitle);
    if (_mainAgentSel && _mainAgentSel.style.display !== 'none' && _mainAgentSel.options.length) hdr.appendChild(cardAgentSel);
    if (_mainProvSel && _mainProvSel.options.length) hdr.appendChild(cardProvSel);
    if (_mainModSel  && _mainModSel.options.length)  hdr.appendChild(cardModSel);
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
                else if (evt.type === 'done') {{
                  if (evt.full_text) {{ assistantText = evt.full_text; }}
                  if (evt.usage) {{ _flushUsage = evt.usage; }}
                }}
              }} catch(e) {{}}
            }}
            if (assistantText) {{
              assistantEl.style.display = '';
              assistantEl.innerHTML = renderMarkdown(assistantText);
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
              assistantEl.innerHTML = prefix + renderMarkdown(assistantText);
              messagesEl.scrollTop = messagesEl.scrollHeight;
            }} else if (evt.type === 'clear') {{
              assistantText = '';
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
                assistantEl.innerHTML = renderMarkdown(assistantText);
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

  // ---- Channel Agents Panel ----
  let _channelAgentsVisible = false;

  function _populateChannelAgentSelect(sel, agents, currentAgentId) {{
    if (!sel) return;
    sel.innerHTML = '';
    const defOpt = document.createElement('option');
    defOpt.value = '';
    defOpt.textContent = T.channel_default;
    sel.appendChild(defOpt);
    if (Array.isArray(agents)) {{
      agents.forEach(a => {{
        const opt = document.createElement('option');
        opt.value = a.id;
        const ident = a.identity || {{}};
        opt.textContent = (ident.emoji || '\U0001f916') + ' ' + (ident.name || a.id);
        if (a.id === currentAgentId) opt.selected = true;
        sel.appendChild(opt);
      }});
    }}
  }}

  async function _loadChannelAgents() {{
    try {{
      const resp = await fetch(API_BASE + '/api/agents/channels', {{credentials:'same-origin'}});
      if (!resp.ok) return;
      const data = await resp.json();
      if (!data.success) return;
      const mapping = data.channel_agents || {{}};
      const agents = agentData ? (agentData.agents || []) : [];
      _populateChannelAgentSelect(channelTelegramSel, agents, (mapping.telegram || {{}}).agent_id || '');
      _populateChannelAgentSelect(channelWhatsappSel, agents, (mapping.whatsapp || {{}}).agent_id || '');
      // Show/hide gear button based on whether we have multiple agents
      if (channelAgentsBtn) {{
        channelAgentsBtn.style.display = agents.length >= 2 ? '' : 'none';
      }}
    }} catch(e) {{
      console.warn('[Amira] Channel agents load error:', e);
    }}
  }}

  async function _saveChannelAgent(channel, agentId) {{
    try {{
      const body = {{}};
      body[channel] = agentId || null;
      await fetch(API_BASE + '/api/agents/channels', {{
        method: 'PUT',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(body),
        credentials: 'same-origin',
      }});
      if (channelSavedMsg) {{
        channelSavedMsg.style.display = '';
        setTimeout(() => {{ if (channelSavedMsg) channelSavedMsg.style.display = 'none'; }}, 2000);
      }}
    }} catch(e) {{
      console.warn('[Amira] Channel agent save error:', e);
    }}
  }}

  if (channelAgentsBtn) {{
    channelAgentsBtn.addEventListener('click', () => {{
      _channelAgentsVisible = !_channelAgentsVisible;
      if (channelAgentsPanel) channelAgentsPanel.style.display = _channelAgentsVisible ? '' : 'none';
      channelAgentsBtn.style.opacity = _channelAgentsVisible ? '1' : '0.6';
      if (_channelAgentsVisible) _loadChannelAgents();
    }});
  }}
  if (channelTelegramSel) {{
    channelTelegramSel.addEventListener('change', () => _saveChannelAgent('telegram', channelTelegramSel.value));
  }}
  if (channelWhatsappSel) {{
    channelWhatsappSel.addEventListener('change', () => _saveChannelAgent('whatsapp', channelWhatsappSel.value));
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
      // Refresh channel agents dropdown (needs agentData.agents)
      _loadChannelAgents();
    }} catch(e) {{
      console.warn('[Amira] Could not load agents:', e);
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

  providerSelect.addEventListener('change', async () => {{
    const provider = providerSelect.value;
    populateModels(provider);
    try {{
      await fetch(API_BASE + '/api/set_model', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ provider }}),
        credentials: 'same-origin',
      }});
      // Refresh to get new current_model_technical
      await loadAgents();
    }} catch(e) {{}}
  }});

  modelSelect.addEventListener('change', async () => {{
    const model = modelSelect.value;
    const provider = providerSelect.value;
    try {{
      await fetch(API_BASE + '/api/set_model', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ provider, model }}),
        credentials: 'same-origin',
      }});
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

  // Initial setup
  registerDevice();
  updateContextBar();
  loadAgents();

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
