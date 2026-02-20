"""Floating chat bubble module for Home Assistant integration.

Generates a JavaScript ES module that injects a floating AI assistant
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


def get_chat_bubble_js(ingress_url: str, language: str = "en", bubble_device_mode: str = "disable", bubble_device_ids: str = "") -> str:
    """Generate the floating chat bubble JavaScript module.

    Args:
        ingress_url: Addon ingress URL prefix (e.g. '/api/hassio_ingress/<token>')
        language: User language (en/it/es/fr)
        bubble_device_mode: Device visibility mode (disable|enable_all|tablet_only|custom)
        bubble_device_ids: Comma-separated list of device IDs for custom mode

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
 * AI Assistant - Floating Chat Bubble for Home Assistant
 * Context-aware, draggable, resizable, with voice input and markdown rendering.
 */
(function() {{
  'use strict';

  const INGRESS_URL = '{ingress_url}';
  const API_BASE = INGRESS_URL;
  const T = {__import__('json').dumps(t, ensure_ascii=False)};
  const VOICE_LANG = '{voice_lang}';
  const BUBBLE_DEVICE_MODE = '{bubble_device_mode}';  // disable|enable_all|tablet_only|custom
  const BUBBLE_DEVICE_IDS = '{bubble_device_ids}'.split(',').map(s => s.trim()).filter(s => s);

  // ---- Device detection ----
  const isMobile = /Mobi|iPhone|iPod/i.test(navigator.userAgent);
  const isTablet = /iPad|Android/i.test(navigator.userAgent) && !/iPhone|iPod/i.test(navigator.userAgent);
  const deviceType = isMobile ? 'phone' : isTablet ? 'tablet' : 'desktop';
  
  // Try to get device-specific ID from localStorage (stored by user or browser fingerprint)
  const deviceId = localStorage.getItem('ha-claude-device-id') || '';

  // Determine if bubble should be shown based on device mode
  function shouldShowBubble() {{
    if (BUBBLE_DEVICE_MODE === 'enable_all') return true;
    if (BUBBLE_DEVICE_MODE === 'disable') return !isMobile && !isTablet;  // Only desktop
    if (BUBBLE_DEVICE_MODE === 'tablet_only') return isTablet;
    if (BUBBLE_DEVICE_MODE === 'custom') {{
      // Show if device ID is in the allowed list OR if it's a desktop (always show desktop in custom mode)
      if (deviceType === 'desktop') return true;
      if (deviceId && BUBBLE_DEVICE_IDS.indexOf(deviceId) !== -1) return true;
      return false;
    }}
    return false;
  }}

  // Hide bubble based on device configuration
  if (!shouldShowBubble()) return;

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

    if (path.startsWith('/config')) {{ ctx.type = 'settings'; ctx.label = T.context_settings; return ctx; }}
    return ctx;
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
      return '[CONTEXT: User is viewing automation "' + ctx.id + '". Use get_automations to read it. Refer to it directly.] ';
    if (ctx.type === 'script' && ctx.id)
      return '[CONTEXT: User is viewing script "' + ctx.id + '". Use get_scripts to read it. Refer to it directly.] ';
    if (ctx.type === 'device' && ctx.id)
      return '[CONTEXT: User is viewing device "' + ctx.id + '". Use search_entities to find its entities.] ';
    if (ctx.type === 'html_dashboard' && ctx.id) {{
      let p = '[CONTEXT: User is viewing HTML dashboard "' + ctx.id + '".';
      if (ctx.entities && ctx.entities.length > 0) {{
        p += ' Entities: ' + ctx.entities.join(', ') + '.';
      }}
      p += ' Use read_html_dashboard to read current HTML, then create_html_dashboard with same name to modify keeping same style.]';
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
    const sid = 'bubble_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7);
    sessionStorage.setItem(SESSION_KEY, sid);
    return sid;
  }}

  // ---- Message History Persistence ----
  const HISTORY_KEY = STORE_PREFIX + 'history';
  const MAX_HISTORY = 50;
  function loadHistory() {{
    try {{ return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); }}
    catch(e) {{ return []; }}
  }}
  function saveHistory(messages) {{
    try {{ localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-MAX_HISTORY))); }}
    catch(e) {{}}
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
      width: 380px; min-width: 300px; min-height: 350px;
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
    }}
    #ha-claude-bubble .agent-bar label {{
      font-size: 11px; color: var(--secondary-text-color, #666); white-space: nowrap;
    }}
    #ha-claude-bubble .agent-bar select {{
      flex: 1; font-size: 12px; padding: 3px 6px; border-radius: 6px;
      border: 1px solid var(--divider-color, #ddd);
      background: var(--card-background-color, #fff); color: var(--primary-text-color, #333);
      outline: none; max-width: 160px; cursor: pointer;
    }}
    #ha-claude-bubble .agent-bar select:focus {{ border-color: var(--primary-color, #03a9f4); }}
    #ha-claude-bubble .tool-badges {{
      display: flex; flex-wrap: wrap; gap: 4px; padding: 4px 0;
    }}
    #ha-claude-bubble .tool-badge {{
      display: inline-block; background: var(--primary-color, #03a9f4);
      color: white; font-size: 10px; padding: 2px 8px; border-radius: 10px; opacity: 0.8;
    }}
    @media (max-width: 480px) {{
      #ha-claude-bubble .chat-panel {{
        width: calc(100vw - 16px) !important; height: calc(100vh - 100px) !important;
        right: 8px !important; bottom: 80px !important; border-radius: 12px;
      }}
      #ha-claude-bubble .bubble-btn {{ width: 48px; height: 48px; font-size: 20px; }}
    }}
  `;
  document.head.appendChild(style);

  // ---- Build DOM ----
  const root = document.createElement('div');
  root.id = 'ha-claude-bubble';
  root.innerHTML = `
    <div class="chat-panel" id="haChatPanel">
      <div class="chat-header" id="haChatHeader">
        <span>AI Assistant</span>
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
    <button class="bubble-btn" id="haChatBubbleBtn" title="AI Assistant">&#129302;</button>
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
  }} else {{
    // Default: always use bottom-right (relative positioning)
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

  // ---- Apply saved panel size ----
  if (savedSize) {{
    panel.style.width = savedSize.w + 'px';
    panel.style.height = savedSize.h + 'px';
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

  // ---- Draggable Button (immediate drag, 5px threshold) ----
  let isDragging = false, dragStarted = false, dragOffsetX = 0, dragOffsetY = 0;
  let dragStartX = 0, dragStartY = 0, mouseIsDown = false;
  const DRAG_THRESHOLD = 5;

  function onBtnDown(cx, cy) {{
    mouseIsDown = true;
    dragStarted = false;
    isDragging = false;
    dragStartX = cx;
    dragStartY = cy;
    dragOffsetX = cx - btn.getBoundingClientRect().left;
    dragOffsetY = cy - btn.getBoundingClientRect().top;
  }}
  function onMoveGlobal(cx, cy) {{
    if (!mouseIsDown) return;
    if (!isDragging) {{
      // Check threshold
      if (Math.abs(cx - dragStartX) > DRAG_THRESHOLD || Math.abs(cy - dragStartY) > DRAG_THRESHOLD) {{
        isDragging = true;
        dragStarted = true;
        btn.classList.add('dragging');
      }} else return;
    }}
    btn.style.left = Math.max(0, Math.min(window.innerWidth - 56, cx - dragOffsetX)) + 'px';
    btn.style.top = Math.max(0, Math.min(window.innerHeight - 56, cy - dragOffsetY)) + 'px';
    btn.style.right = 'auto'; btn.style.bottom = 'auto';
    if (isOpen) positionPanelNearButton();
  }}
  function onUpGlobal() {{
    if (!mouseIsDown) return;
    mouseIsDown = false;
    if (isDragging) {{
      isDragging = false;
      btn.classList.remove('dragging');
      saveSetting('btn-pos', {{ x: parseInt(btn.style.left) || 0, y: parseInt(btn.style.top) || 0 }});
      saveSetting('btn-dragged', true);  // Mark that button has been manually dragged
    }}
  }}

  btn.addEventListener('mousedown', (e) => {{ e.preventDefault(); onBtnDown(e.clientX, e.clientY); }});
  document.addEventListener('mousemove', (e) => {{ onMoveGlobal(e.clientX, e.clientY); }});
  document.addEventListener('mouseup', () => {{ onUpGlobal(); }});

  btn.addEventListener('touchstart', (e) => {{ onBtnDown(e.touches[0].clientX, e.touches[0].clientY); }}, {{ passive: true }});
  document.addEventListener('touchmove', (e) => {{ if (mouseIsDown) {{ e.preventDefault(); onMoveGlobal(e.touches[0].clientX, e.touches[0].clientY); }} }}, {{ passive: false }});
  document.addEventListener('touchend', () => {{ const wasDrag = dragStarted; onUpGlobal(); if (!wasDrag) togglePanel(); }});

  // ---- Panel positioning ----
  function positionPanelNearButton() {{
    const rect = btn.getBoundingClientRect();
    const pw = panel.offsetWidth || 380, ph = panel.offsetHeight || 520;
    let top = rect.top - ph - 10;
    if (top < 10) top = rect.bottom + 10;
    let left = rect.right - pw;
    if (left < 10) left = 10;
    if (left + pw > window.innerWidth - 10) left = window.innerWidth - pw - 10;
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
  setInterval(() => {{
    if (window.location.pathname !== lastPath) {{
      lastPath = window.location.pathname;
      if (isOpen) {{ updateContextBar(); updateQuickActions(); }}
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
    /vuoi\\s+(eliminare|procedere|continuare).*\\?/i,
    /s[i\u00ec]\\s*\\/\\s*no/i,
    /confirm.*\\?\\s*(yes.*no)?/i,
    /type\\s+['"]?yes['"]?\\s+or\\s+['"]?no['"]?/i,
    /do\\s+you\\s+want\\s+to\\s+(delete|proceed|continue).*\\?/i,
    /confirma.*\\?/i,
    /escribe\\s+s[i\u00ed]\\s+o\\s+no/i,
    /confirme[sz]?.*\\?/i,
    /tape[sz]?\\s+['"]?oui['"]?\\s+ou\\s+['"]?non['"]?/i,
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
              + 'Current HTML source below. To modify, use read_html_dashboard first then create_html_dashboard with same name="' + ctx.id + '" '
              + 'keeping the same style/design/colors/layout.]\\n'
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
      if (_thinkingSteps.length > 4) _thinkingSteps = _thinkingSteps.slice(-4);
      const stepsEl = thinkingEl.querySelector('.thinking-steps');
      if (stepsEl) stepsEl.innerHTML = _thinkingSteps.map(s => '<div>\\u2022 ' + s.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>').join('');
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }}

    function _updateThinkingBase(text) {{
      const elapsedEl = thinkingEl.querySelector('.thinking-elapsed');
      const elapsed = elapsedEl ? elapsedEl.outerHTML : '';
      const stepsEl = thinkingEl.querySelector('.thinking-steps');
      const steps = stepsEl ? stepsEl.outerHTML : '';
      thinkingEl.innerHTML = text + ' ' + elapsed + '<span class="thinking-dots"><span>.</span><span>.</span><span>.</span></span>' + steps;
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
        if (done) break;

        buffer += decoder.decode(value, {{ stream: true }});
        const lines = buffer.split('\\n');
        buffer = lines.pop() || '';

        for (const line of lines) {{
          if (!line.startsWith('data: ')) continue;
          try {{
            const evt = JSON.parse(line.slice(6));
            if (evt.type === 'token') {{
              if (firstToken) {{
                _removeThinking();
                assistantEl.style.display = '';
                firstToken = false;
              }}
              assistantText += evt.content || '';
              assistantEl.innerHTML = renderMarkdown(assistantText);
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
            }} else if (evt.type === 'status') {{
              const msg = evt.message || '';
              _updateThinkingBase('\\u23f3 ' + msg);
              _addThinkingStep(msg);
            }}
          }} catch (parseErr) {{}}
        }}
      }}

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
    if (history.length === 0) return;
    // Only show last 20 messages
    const recent = history.slice(-20);
    recent.forEach(m => {{
      addMessage(m.role, m.text, m.role === 'assistant');
    }});
  }}
  restoreHistory();

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
    }} catch(e) {{
      console.warn('[AI Assistant] Could not load agents:', e);
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

  // Initial setup
  updateContextBar();
  loadAgents();
  console.log('[AI Assistant] Chat bubble loaded (v3)');
}})();
"""
