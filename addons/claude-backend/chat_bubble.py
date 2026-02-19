"""Floating chat bubble module for Home Assistant integration.

Generates a JavaScript ES module that injects a floating AI assistant
chat bubble into every Home Assistant page. The module is registered
as a Lovelace resource and loaded via extra_module_url or /local/.
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
    # Translations for the bubble UI
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
        },
    }

    t = T.get(language, T["en"])

    return f"""/**
 * AI Assistant - Floating Chat Bubble for Home Assistant
 * Injected as a Lovelace resource, appears on every HA page.
 * Context-aware: detects current automation/script/entity/dashboard from URL.
 * Features: draggable button, resizable panel, auto-reload after updates.
 */
(function() {{
  'use strict';

  const INGRESS_URL = '{ingress_url}';
  const API_BASE = INGRESS_URL;
  const T = {__import__('json').dumps(t, ensure_ascii=False)};

  // Prevent double injection
  if (document.getElementById('ha-claude-bubble')) return;

  // ---- Persistence helpers (localStorage) ----
  const STORE_PREFIX = 'ha-claude-bubble-';
  function loadSetting(key, fallback) {{
    try {{ const v = localStorage.getItem(STORE_PREFIX + key); return v ? JSON.parse(v) : fallback; }}
    catch(e) {{ return fallback; }}
  }}
  function saveSetting(key, val) {{
    try {{ localStorage.setItem(STORE_PREFIX + key, JSON.stringify(val)); }} catch(e) {{}}
  }}

  // ---- Context Detection ----
  function detectContext() {{
    const path = window.location.pathname;
    const ctx = {{ type: null, id: null, label: null, entities: null }};

    // /config/automation/edit/<id>
    let m = path.match(/\\/config\\/automation\\/edit\\/([^/]+)/);
    if (m) {{
      ctx.type = 'automation';
      ctx.id = m[1];
      ctx.label = T.context_automation + ': ' + m[1];
      return ctx;
    }}

    // /config/automation/trace/<id>
    m = path.match(/\\/config\\/automation\\/trace\\/([^/]+)/);
    if (m) {{
      ctx.type = 'automation';
      ctx.id = m[1];
      ctx.label = T.context_automation + ' (trace): ' + m[1];
      return ctx;
    }}

    // /config/script/edit/<id>
    m = path.match(/\\/config\\/script\\/edit\\/([^/]+)/);
    if (m) {{
      ctx.type = 'script';
      ctx.id = m[1];
      ctx.label = T.context_script + ': ' + m[1];
      return ctx;
    }}

    // /config/entities -> entity registry
    if (path.includes('/config/entities')) {{
      ctx.type = 'entities';
      ctx.label = T.context_entity + ' registry';
      return ctx;
    }}

    // /config/devices/device/<id>
    m = path.match(/\\/config\\/devices\\/device\\/([^/]+)/);
    if (m) {{
      ctx.type = 'device';
      ctx.id = m[1];
      ctx.label = 'Device: ' + m[1];
      return ctx;
    }}

    // /lovelace/<path> or /lovelace-<name>/<path> — detect HTML dashboard entities
    m = path.match(/\\/(lovelace[^/]*)\\/?(.*)/);
    if (m) {{
      ctx.type = 'dashboard';
      ctx.id = m[1];
      ctx.label = T.context_dashboard + ': ' + (m[1] || 'default');
      // Try to extract entities from HTML dashboard iframe
      ctx.entities = extractDashboardEntities();
      return ctx;
    }}

    // /config/* pages
    if (path.startsWith('/config')) {{
      ctx.type = 'settings';
      ctx.label = T.context_settings;
      return ctx;
    }}

    return ctx;
  }}

  // ---- Extract entities from HTML dashboard (iframe) ----
  function extractDashboardEntities() {{
    try {{
      const iframes = document.querySelectorAll('iframe[src*="/local/"], iframe[src*="hacsfiles"]');
      const entities = new Set();
      for (const iframe of iframes) {{
        try {{
          const doc = iframe.contentDocument || iframe.contentWindow.document;
          if (!doc) continue;
          const html = doc.documentElement.innerHTML || '';
          // Match entity_id patterns in the HTML
          const re = /(?:sensor|switch|light|climate|binary_sensor|input_boolean|automation|number|select|button|cover|fan|lock|media_player|vacuum|weather|water_heater|scene|script|input_number|input_select|input_text|person|device_tracker|calendar|camera|update|group|sun)\\.[a-z0-9_]+/g;
          let match;
          while ((match = re.exec(html)) !== null) {{
            entities.add(match[0]);
          }}
        }} catch(e) {{
          // Cross-origin iframe — can't access content
        }}
      }}
      // Also check the main page for web-component dashboards with entity references
      const mainHtml = document.body.innerHTML || '';
      const re2 = /(?:sensor|switch|light|climate|binary_sensor|input_boolean)\\.[a-z0-9_]+/g;
      let m2;
      while ((m2 = re2.exec(mainHtml)) !== null) {{
        entities.add(m2[0]);
      }}
      return entities.size > 0 ? Array.from(entities) : null;
    }} catch(e) {{
      return null;
    }}
  }}

  // ---- Build context message prefix ----
  function buildContextPrefix() {{
    const ctx = detectContext();
    if (!ctx.type) return '';

    if (ctx.type === 'automation' && ctx.id) {{
      return '[CONTEXT: User is viewing automation "' + ctx.id + '". '
        + 'Use get_automations to read it. Refer to it directly.] ';
    }}
    if (ctx.type === 'script' && ctx.id) {{
      return '[CONTEXT: User is viewing script "' + ctx.id + '". '
        + 'Use get_scripts to read it. Refer to it directly.] ';
    }}
    if (ctx.type === 'device' && ctx.id) {{
      return '[CONTEXT: User is viewing device "' + ctx.id + '". '
        + 'Use search_entities to find its entities.] ';
    }}
    if (ctx.type === 'dashboard' && ctx.id) {{
      let prefix = '[CONTEXT: User is viewing dashboard "' + ctx.id + '".';
      if (ctx.entities && ctx.entities.length > 0) {{
        prefix += ' This dashboard currently shows these entities: ' + ctx.entities.join(', ') + '.';
        prefix += ' If the user asks to add something, use the same style/layout already present in the dashboard HTML.';
        prefix += ' Use get_dashboard_config to read the current dashboard, then update it with the additions.';
      }}
      prefix += '] ';
      return prefix;
    }}
    return '';
  }}

  // ---- Session Management ----
  const SESSION_KEY = 'ha-claude-bubble-session';
  function getSessionId() {{
    let sid = sessionStorage.getItem(SESSION_KEY);
    if (!sid) {{
      sid = 'bubble_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7);
      sessionStorage.setItem(SESSION_KEY, sid);
    }}
    return sid;
  }}

  function resetSession() {{
    const sid = 'bubble_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7);
    sessionStorage.setItem(SESSION_KEY, sid);
    return sid;
  }}

  // ---- Saved position/size ----
  const savedPos = loadSetting('btn-pos', null);    // {{x, y}}
  const savedSize = loadSetting('panel-size', null); // {{w, h}}

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
    #ha-claude-bubble .bubble-btn:hover {{
      box-shadow: 0 6px 24px rgba(0,0,0,0.4);
    }}
    #ha-claude-bubble .bubble-btn.dragging {{
      opacity: 0.8;
      transform: scale(1.15);
      transition: none;
    }}
    #ha-claude-bubble .bubble-btn.has-context {{
      animation: bubble-pulse 2s infinite;
    }}
    #ha-claude-bubble .bubble-btn.dragging.has-context {{
      animation: none;
    }}
    @keyframes bubble-pulse {{
      0%, 100% {{ box-shadow: 0 4px 16px rgba(0,0,0,0.3); }}
      50% {{ box-shadow: 0 4px 16px rgba(3,169,244,0.6); }}
    }}
    #ha-claude-bubble .chat-panel {{
      display: none;
      position: fixed;
      bottom: 90px;
      right: 24px;
      width: 380px;
      min-width: 300px;
      min-height: 350px;
      max-width: calc(100vw - 48px);
      height: 520px;
      max-height: calc(100vh - 120px);
      background: var(--card-background-color, #fff);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
      flex-direction: column;
      overflow: hidden;
      border: 1px solid var(--divider-color, #e0e0e0);
      resize: both;
    }}
    #ha-claude-bubble .chat-panel.open {{
      display: flex;
    }}
    #ha-claude-bubble .chat-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: var(--primary-color, #03a9f4);
      color: white;
      font-weight: 600;
      font-size: 14px;
      cursor: move;
    }}
    #ha-claude-bubble .chat-header-actions {{
      display: flex;
      gap: 8px;
    }}
    #ha-claude-bubble .chat-header button {{
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      font-size: 16px;
      padding: 4px;
      opacity: 0.8;
      border-radius: 4px;
    }}
    #ha-claude-bubble .chat-header button:hover {{
      opacity: 1;
      background: rgba(255,255,255,0.15);
    }}
    #ha-claude-bubble .context-bar {{
      padding: 6px 16px;
      background: var(--secondary-background-color, #f5f5f5);
      font-size: 11px;
      color: var(--secondary-text-color, #666);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    #ha-claude-bubble .chat-messages {{
      flex: 1;
      overflow-y: auto;
      padding: 12px 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    #ha-claude-bubble .msg {{
      max-width: 85%;
      padding: 8px 12px;
      border-radius: 12px;
      font-size: 13px;
      line-height: 1.45;
      word-wrap: break-word;
      white-space: pre-wrap;
    }}
    #ha-claude-bubble .msg.user {{
      align-self: flex-end;
      background: var(--primary-color, #03a9f4);
      color: white;
      border-bottom-right-radius: 4px;
    }}
    #ha-claude-bubble .msg.assistant {{
      align-self: flex-start;
      background: var(--secondary-background-color, #f0f0f0);
      color: var(--primary-text-color, #333);
      border-bottom-left-radius: 4px;
    }}
    #ha-claude-bubble .msg.thinking {{
      align-self: flex-start;
      background: var(--secondary-background-color, #f0f0f0);
      color: var(--secondary-text-color, #999);
      font-style: italic;
    }}
    #ha-claude-bubble .msg.status {{
      align-self: center;
      background: transparent;
      color: var(--secondary-text-color, #999);
      font-size: 11px;
      padding: 2px 8px;
    }}
    #ha-claude-bubble .msg.error {{
      align-self: center;
      background: var(--error-color, #db4437);
      color: white;
      font-size: 12px;
    }}
    #ha-claude-bubble .msg.reload-notice {{
      align-self: center;
      background: var(--success-color, #4caf50);
      color: white;
      font-size: 12px;
      padding: 6px 12px;
    }}
    #ha-claude-bubble .chat-input-area {{
      display: flex;
      padding: 10px 12px;
      border-top: 1px solid var(--divider-color, #e0e0e0);
      gap: 8px;
      align-items: flex-end;
    }}
    #ha-claude-bubble .chat-input-area textarea {{
      flex: 1;
      border: 1px solid var(--divider-color, #ddd);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 13px;
      font-family: inherit;
      resize: none;
      max-height: 80px;
      outline: none;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #333);
    }}
    #ha-claude-bubble .chat-input-area textarea:focus {{
      border-color: var(--primary-color, #03a9f4);
    }}
    #ha-claude-bubble .send-btn {{
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--primary-color, #03a9f4);
      color: white;
      border: none;
      cursor: pointer;
      font-size: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    #ha-claude-bubble .send-btn:disabled {{
      opacity: 0.5;
      cursor: not-allowed;
    }}
    #ha-claude-bubble .tool-badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      padding: 4px 0;
    }}
    #ha-claude-bubble .tool-badge {{
      display: inline-block;
      background: var(--primary-color, #03a9f4);
      color: white;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 10px;
      opacity: 0.8;
    }}
    @media (max-width: 480px) {{
      #ha-claude-bubble .chat-panel {{
        width: calc(100vw - 16px) !important;
        height: calc(100vh - 100px) !important;
        right: 8px !important;
        bottom: 80px !important;
        border-radius: 12px;
      }}
      #ha-claude-bubble .bubble-btn {{
        width: 48px;
        height: 48px;
        font-size: 20px;
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
        <span>AI Assistant</span>
        <div class="chat-header-actions">
          <button id="haChatNew" title="${{T.new_chat}}">+</button>
          <button id="haChatClose" title="${{T.close}}">&times;</button>
        </div>
      </div>
      <div class="context-bar" id="haChatContext" style="display:none;"></div>
      <div class="chat-messages" id="haChatMessages"></div>
      <div class="chat-input-area">
        <textarea id="haChatInput" rows="1" placeholder="${{T.placeholder}}"></textarea>
        <button class="send-btn" id="haChatSend" title="${{T.send}}">&#9654;</button>
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
  const messagesEl = document.getElementById('haChatMessages');
  const contextBar = document.getElementById('haChatContext');
  const closeBtn = document.getElementById('haChatClose');
  const newBtn = document.getElementById('haChatNew');

  let isOpen = false;
  let isStreaming = false;

  // ---- Apply saved button position ----
  if (savedPos) {{
    btn.style.left = savedPos.x + 'px';
    btn.style.top = savedPos.y + 'px';
    btn.style.right = 'auto';
    btn.style.bottom = 'auto';
  }} else {{
    btn.style.bottom = '24px';
    btn.style.right = '24px';
  }}

  // ---- Apply saved panel size ----
  if (savedSize) {{
    panel.style.width = savedSize.w + 'px';
    panel.style.height = savedSize.h + 'px';
  }}

  // Save panel size on resize (via ResizeObserver)
  const panelResizeObserver = new ResizeObserver((entries) => {{
    for (const entry of entries) {{
      if (panel.classList.contains('open')) {{
        const rect = entry.contentRect;
        if (rect.width > 100 && rect.height > 100) {{
          saveSetting('panel-size', {{ w: Math.round(rect.width), h: Math.round(rect.height) }});
        }}
      }}
    }}
  }});
  panelResizeObserver.observe(panel);

  // ---- Draggable Button (long-press to drag, like iPhone) ----
  let isDragging = false;
  let dragStarted = false;
  let longPressTimer = null;
  let dragOffsetX = 0;
  let dragOffsetY = 0;

  function startDragCheck(clientX, clientY) {{
    dragOffsetX = clientX - btn.getBoundingClientRect().left;
    dragOffsetY = clientY - btn.getBoundingClientRect().top;
    longPressTimer = setTimeout(() => {{
      isDragging = true;
      dragStarted = true;
      btn.classList.add('dragging');
    }}, 400); // 400ms long-press threshold
  }}

  function handleDragMove(clientX, clientY) {{
    if (!isDragging) return;
    const x = Math.max(0, Math.min(window.innerWidth - 56, clientX - dragOffsetX));
    const y = Math.max(0, Math.min(window.innerHeight - 56, clientY - dragOffsetY));
    btn.style.left = x + 'px';
    btn.style.top = y + 'px';
    btn.style.right = 'auto';
    btn.style.bottom = 'auto';

    // Also move panel relative to button
    positionPanelNearButton();
  }}

  function endDrag() {{
    if (longPressTimer) {{
      clearTimeout(longPressTimer);
      longPressTimer = null;
    }}
    if (isDragging) {{
      isDragging = false;
      btn.classList.remove('dragging');
      // Save position
      saveSetting('btn-pos', {{
        x: parseInt(btn.style.left) || 0,
        y: parseInt(btn.style.top) || 0,
      }});
    }}
  }}

  // Mouse events for drag
  btn.addEventListener('mousedown', (e) => {{
    e.preventDefault();
    dragStarted = false;
    startDragCheck(e.clientX, e.clientY);
  }});
  document.addEventListener('mousemove', (e) => {{
    if (longPressTimer && !isDragging) {{
      // Cancel long-press if moved too much before threshold
      const dx = e.clientX - (btn.getBoundingClientRect().left + dragOffsetX);
      const dy = e.clientY - (btn.getBoundingClientRect().top + dragOffsetY);
      if (Math.abs(dx) > 10 || Math.abs(dy) > 10) {{
        clearTimeout(longPressTimer);
        longPressTimer = null;
      }}
    }}
    handleDragMove(e.clientX, e.clientY);
  }});
  document.addEventListener('mouseup', () => {{
    const wasDragging = dragStarted;
    endDrag();
    // Only toggle if was not dragging
    if (!wasDragging) {{
      // click handled by click event
    }}
  }});

  // Touch events for drag
  btn.addEventListener('touchstart', (e) => {{
    dragStarted = false;
    const touch = e.touches[0];
    startDragCheck(touch.clientX, touch.clientY);
  }}, {{ passive: true }});
  document.addEventListener('touchmove', (e) => {{
    if (isDragging) {{
      e.preventDefault();
      const touch = e.touches[0];
      handleDragMove(touch.clientX, touch.clientY);
    }}
  }}, {{ passive: false }});
  document.addEventListener('touchend', () => {{
    const wasDragging = dragStarted;
    endDrag();
    if (!wasDragging) {{
      // tap — toggle panel
      togglePanel();
    }}
  }});

  // ---- Position panel near button ----
  function positionPanelNearButton() {{
    const rect = btn.getBoundingClientRect();
    const pw = panel.offsetWidth || 380;
    const ph = panel.offsetHeight || 520;

    // Prefer above the button; if not enough space, below
    let top = rect.top - ph - 10;
    if (top < 10) top = rect.bottom + 10;

    // Prefer aligned to button right edge; clamp to viewport
    let left = rect.right - pw;
    if (left < 10) left = 10;
    if (left + pw > window.innerWidth - 10) left = window.innerWidth - pw - 10;

    panel.style.top = top + 'px';
    panel.style.left = left + 'px';
    panel.style.right = 'auto';
    panel.style.bottom = 'auto';
  }}

  // ---- Toggle Panel ----
  function togglePanel() {{
    isOpen = !isOpen;
    panel.classList.toggle('open', isOpen);
    if (isOpen) {{
      positionPanelNearButton();
      updateContextBar();
      input.focus();
    }}
  }}

  btn.addEventListener('click', (e) => {{
    // Only toggle on click if not dragging (mouse users)
    if (!dragStarted) {{
      togglePanel();
    }}
  }});

  closeBtn.addEventListener('click', () => {{
    isOpen = false;
    panel.classList.remove('open');
  }});

  newBtn.addEventListener('click', () => {{
    resetSession();
    messagesEl.innerHTML = '';
    updateContextBar();
  }});

  // ---- Draggable Panel (via header) ----
  let panelDragging = false;
  let panelDragOffX = 0;
  let panelDragOffY = 0;

  header.addEventListener('mousedown', (e) => {{
    if (e.target.tagName === 'BUTTON') return;
    panelDragging = true;
    panelDragOffX = e.clientX - panel.getBoundingClientRect().left;
    panelDragOffY = e.clientY - panel.getBoundingClientRect().top;
    e.preventDefault();
  }});
  document.addEventListener('mousemove', (e) => {{
    if (!panelDragging) return;
    const x = Math.max(0, Math.min(window.innerWidth - panel.offsetWidth, e.clientX - panelDragOffX));
    const y = Math.max(0, Math.min(window.innerHeight - panel.offsetHeight, e.clientY - panelDragOffY));
    panel.style.left = x + 'px';
    panel.style.top = y + 'px';
    panel.style.right = 'auto';
    panel.style.bottom = 'auto';
  }});
  document.addEventListener('mouseup', () => {{
    panelDragging = false;
  }});

  // ---- Context Bar ----
  function updateContextBar() {{
    const ctx = detectContext();
    if (ctx.label) {{
      let text = ctx.label;
      if (ctx.entities && ctx.entities.length > 0) {{
        text += ' (' + ctx.entities.length + ' entities)';
      }}
      contextBar.style.display = 'block';
      contextBar.textContent = text;
      btn.classList.add('has-context');
    }} else {{
      contextBar.style.display = 'none';
      btn.classList.remove('has-context');
    }}
  }}

  // Update context on URL change (SPA navigation)
  let lastPath = window.location.pathname;
  setInterval(() => {{
    if (window.location.pathname !== lastPath) {{
      lastPath = window.location.pathname;
      if (isOpen) updateContextBar();
    }}
  }}, 1000);

  // ---- Auto-resize textarea ----
  input.addEventListener('input', () => {{
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 80) + 'px';
  }});

  // ---- Send Message ----
  input.addEventListener('keydown', (e) => {{
    if (e.key === 'Enter' && !e.shiftKey) {{
      e.preventDefault();
      sendMessage();
    }}
  }});
  sendBtn.addEventListener('click', sendMessage);

  function addMessage(role, text) {{
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }}

  // ---- Auto-reload: tools that modify what the user is viewing ----
  const RELOAD_TOOLS = new Set([
    'update_automation', 'update_script', 'update_dashboard_card',
    'update_dashboard', 'create_automation', 'create_script',
  ]);

  async function sendMessage() {{
    const text = input.value.trim();
    if (!text || isStreaming) return;

    const ctx = detectContext();
    const contextPrefix = buildContextPrefix();
    const fullMessage = contextPrefix + text;

    addMessage('user', text);
    input.value = '';
    input.style.height = 'auto';
    isStreaming = true;
    sendBtn.disabled = true;

    const thinkingEl = addMessage('thinking', T.thinking + '...');
    let toolBadgesEl = null;  // Container for tool badges
    let writeToolCalled = false; // Track if a write tool was called for auto-reload

    try {{
      const response = await fetch(API_BASE + '/api/chat/stream', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          message: fullMessage,
          session_id: getSessionId(),
        }}),
      }});

      if (!response.ok) {{
        throw new Error('HTTP ' + response.status);
      }}

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let assistantText = '';

      thinkingEl.remove();
      const assistantEl = addMessage('assistant', '');

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
              assistantText += evt.content || '';
              assistantEl.textContent = assistantText;
              messagesEl.scrollTop = messagesEl.scrollHeight;
            }} else if (evt.type === 'clear') {{
              assistantText = '';
              assistantEl.textContent = '';
              // Remove tool badges on clear (final response coming)
              if (toolBadgesEl) {{ toolBadgesEl.remove(); toolBadgesEl = null; }}
            }} else if (evt.type === 'done') {{
              if (evt.full_text) {{
                assistantText = evt.full_text;
                assistantEl.textContent = assistantText;
              }}
            }} else if (evt.type === 'error') {{
              assistantEl.className = 'msg error';
              assistantEl.textContent = evt.message || 'Error';
            }} else if (evt.type === 'tool') {{
              // Show tool badge
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
              // Track write tools for auto-reload
              if (RELOAD_TOOLS.has(evt.name)) {{
                writeToolCalled = true;
              }}
            }} else if (evt.type === 'status') {{
              // Update thinking indicator
              thinkingEl.textContent = evt.message || '';
            }}
          }} catch (parseErr) {{
            // Ignore malformed SSE lines
          }}
        }}
      }}

      if (!assistantText && assistantEl.className.indexOf('error') === -1) {{
        assistantEl.textContent = '...';
      }}

      // ---- Auto-reload if a write tool modified the current page ----
      if (writeToolCalled && ctx.type) {{
        const shouldReload = (
          (ctx.type === 'automation' && ctx.id) ||
          (ctx.type === 'script' && ctx.id) ||
          (ctx.type === 'dashboard')
        );
        if (shouldReload) {{
          addMessage('reload-notice', T.page_reload);
          setTimeout(() => {{
            window.location.reload();
          }}, 2500);
        }}
      }}

    }} catch (err) {{
      thinkingEl.remove();
      addMessage('error', T.error_connection);
      console.error('Chat bubble error:', err);
    }} finally {{
      isStreaming = false;
      sendBtn.disabled = false;
    }}
  }}

  // Initial context check
  updateContextBar();
  console.log('[AI Assistant] Chat bubble loaded');
}})();
"""
