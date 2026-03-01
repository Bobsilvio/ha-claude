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


def get_chat_bubble_js(ingress_url: str, language: str = "en") -> str:
    """Generate the floating chat bubble JavaScript module.

    Args:
        ingress_url: Addon ingress URL prefix (e.g. '/api/hassio_ingress/<token>')
        language: User language (en/it/es/fr)

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
            "confirm_yes": "Yes, confirm",
            "confirm_no": "No, cancel",
            "confirm_yes_value": "yes",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Delete",
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
            "confirm_yes": "Sì, conferma",
            "confirm_no": "No, annulla",
            "confirm_yes_value": "si",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Elimina",
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
            "confirm_yes": "Sí, confirma",
            "confirm_no": "No, cancela",
            "confirm_yes_value": "si",
            "confirm_no_value": "no",
            "confirm_delete_yes": "Eliminar",
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
            "confirm_yes": "Oui, confirme",
            "confirm_no": "Non, annule",
            "confirm_yes_value": "oui",
            "confirm_no_value": "non",
            "confirm_delete_yes": "Supprimer",
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

  function detectContext() {{
    const path = window.location.pathname;
    const ctx = {{ type: null, id: null, label: null, entities: null }};

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
    if (ctx.type === 'logs') {{
      let p = '[CONTEXT: User is on the Home Assistant system logs page. '
            + 'Use get_ha_logs to fetch recent errors and warnings. ';
      if (ctx.logEntry) {{
        p += 'The user has the following log entry open/visible:\\n---\\n' + ctx.logEntry + '\\n---\\n'
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
    if (ctx.type === 'logs') {{
      const ctx2 = detectContext();
      const hasEntry = !!(ctx2 && ctx2.logEntry);
      const actions = [];
      if (hasEntry) {{
        actions.push({{ label: T.qa_explain_log, text: 'Explain this log error and tell me what causes it' }});
        actions.push({{ label: T.qa_fix_log, text: 'How can I fix this log error? Give me step-by-step instructions' }});
      }}
      actions.push({{ label: T.qa_show_errors, text: 'Show me all current errors and warnings from the HA logs' }});
      actions.push({{ label: T.qa_fix, text: 'What are the most critical issues in the logs and how to fix them?' }});
      return actions;
    }}
    return [];
  }}

  // ---- Session Management (bubble-specific, separate from main UI) ----
  const SESSION_KEY = 'ha-claude-bubble-session';
  function getSessionId() {{
    let sid = sessionStorage.getItem(SESSION_KEY);
    if (!sid) {{ sid = 'bubble_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7); sessionStorage.setItem(SESSION_KEY, sid); }}
    return sid;
  }}
  function resetSession() {{
    // Remove current session so getSessionId() generates a fresh one on next call
    sessionStorage.removeItem(SESSION_KEY);
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
    @keyframes voice-pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.6; }}
    }}
    #ha-claude-bubble .abort-btn {{
      background: var(--error-color, #db4437); color: white;
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
          <button id="haChatNew" title="${{T.new_chat}}">&#10227;</button>
          <button id="haChatClose" title="${{T.close}}">&times;</button>
        </div>
      </div>
      <div class="agent-bar" id="haAgentBar">
        <label>Agent:</label>
        <select id="haProviderSelect"></select>
        <select id="haModelSelect"></select>
      </div>
      <div class="context-bar" id="haChatContext" style="display:none;"></div>
      <div class="quick-actions" id="haQuickActions" style="display:none;"></div>
      <div class="chat-messages" id="haChatMessages"></div>
      <div class="chat-input-area">
        <textarea id="haChatInput" rows="1" placeholder="${{T.placeholder}}"></textarea>
        <button class="input-btn voice-btn" id="haChatVoice" title="Voice">&#127908;</button>
        <button class="input-btn send-btn" id="haChatSend" title="${{T.send}}">&#9654;</button>
      </div>
    </div>
    <button class="bubble-btn" id="haChatBubbleBtn" title="Amira">&#129302;</button>
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
  const providerSelect = document.getElementById('haProviderSelect');
  const modelSelect = document.getElementById('haModelSelect');

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

  btn.addEventListener('click', () => {{ if (!dragStarted) togglePanel(); }});
  closeBtn.addEventListener('click', () => {{ isOpen = false; panel.classList.remove('open'); }});
  newBtn.addEventListener('click', () => {{
    resetSession(); clearHistory(); messagesEl.innerHTML = '';
    updateContextBar(); updateQuickActions();
    broadcastEvent('clear', {{}});
  }});

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
      if (ctx.type === 'logs' && ctx.logEntry) text += ' \u2022 log aperto';
      contextBar.style.display = 'block'; contextBar.textContent = text;
      btn.classList.add('has-context');
    }} else {{
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
  setInterval(() => {{
    const curPath = window.location.pathname;
    if (curPath !== lastPath) {{
      lastPath = curPath;
      lastLogEntry = null;
      if (isOpen) {{ updateContextBar(); updateQuickActions(); }}
    }}
    // On logs page, also re-check if a log entry dialog was opened/closed
    // (the URL doesn't change when a dialog opens in HA)
    if (isOpen && curPath.includes('/config/log')) {{
      const ctx = detectContext();
      const entry = ctx.logEntry || null;
      const entryKey = entry ? entry.substring(0, 80) : null;
      if (entryKey !== lastLogEntry) {{
        lastLogEntry = entryKey;
        updateContextBar();
        updateQuickActions();
      }}
    }}
  }}, 1000);

  // ---- Auto-resize textarea ----
  input.addEventListener('input', () => {{ input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 80) + 'px'; }});

  // ---- Voice Input (Web Speech API) ----
  let recognition = null;
  let isRecording = false;

  if (typeof webkitSpeechRecognition !== 'undefined' || typeof SpeechRecognition !== 'undefined') {{
    const SpeechRec = typeof SpeechRecognition !== 'undefined' ? SpeechRecognition : webkitSpeechRecognition;
    recognition = new SpeechRec();
    recognition.lang = VOICE_LANG;
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onresult = (event) => {{
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {{
        transcript += event.results[i][0].transcript;
      }}
      input.value = transcript;
    }};
    recognition.onend = () => {{
      isRecording = false;
      voiceBtn.classList.remove('recording');
      // Auto-send if we got text
      if (input.value.trim()) sendMessage();
    }};
    recognition.onerror = () => {{
      isRecording = false;
      voiceBtn.classList.remove('recording');
    }};
  }}

  voiceBtn.addEventListener('click', () => {{
    if (!recognition) {{ alert(T.voice_unsupported); return; }}
    if (isRecording) {{
      recognition.stop();
      return;
    }}
    isRecording = true;
    voiceBtn.classList.add('recording');
    input.value = '';
    input.placeholder = T.voice_start;
    recognition.start();
  }});

  // ---- Send / Abort ----
  input.addEventListener('keydown', (e) => {{
    if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); sendMessage(); }}
  }});
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

    const thinkingEl = addMessage('thinking', '', false);
    thinkingEl.innerHTML = T.thinking + '... <span class="thinking-elapsed"></span><span class="thinking-dots"><span>.</span><span>.</span><span>.</span></span><div class="thinking-steps"></div>';
    const _thinkingStart = Date.now();
    let _thinkingSteps = [];
    const _thinkingTimer = setInterval(() => {{
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

    let toolBadgesEl = null;
    let writeToolCalled = false;

    currentAbortController = new AbortController();

    try {{
      const response = await fetch(API_BASE + '/api/chat/stream', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message: fullMessage, session_id: getSessionId() }}),
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
            for (const line of buffer.split('\\n')) {{
              if (!line.startsWith('data: ')) continue;
              try {{
                const evt = JSON.parse(line.slice(6));
                if (evt.type === 'token') {{ assistantText += evt.content || ''; }}
                else if (evt.type === 'done' && evt.full_text) {{ assistantText = evt.full_text; }}
              }} catch(e) {{}}
            }}
            if (assistantText) {{
              assistantEl.innerHTML = renderMarkdown(assistantText);
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
              assistantEl.innerHTML = '';
              if (toolBadgesEl) {{ toolBadgesEl.remove(); toolBadgesEl = null; }}
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
  function restoreHistory() {{
    const history = loadHistory();
    console.log('[Bubble] Restored history:', history.length, 'messages');
    if (history.length === 0) return;
    // Only show last 20 messages
    const recent = history.slice(-20);
    recent.forEach(m => {{
      addMessage(m.role, m.text, m.role === 'assistant');
    }});
    console.log('[Bubble] Loaded', recent.length, 'recent messages to UI');
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

      // Populate provider select
      providerSelect.innerHTML = '';
      (agentData.available_providers || []).forEach(p => {{
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.name;
        if (p.id === agentData.current_provider) opt.selected = true;
        providerSelect.appendChild(opt);
      }});

      // Populate models for current provider
      populateModels(agentData.current_provider);
      // Track for cross-UI sync polling
      _syncProvider = agentData.current_provider || '';
      _syncModel    = agentData.current_model_technical || '';
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
