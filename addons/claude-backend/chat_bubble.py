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
        },
    }

    t = T.get(language, T["en"])

    return f"""/**
 * AI Assistant - Floating Chat Bubble for Home Assistant
 * Injected as a Lovelace resource, appears on every HA page.
 * Context-aware: detects current automation/script/entity from URL.
 */
(function() {{
  'use strict';

  const INGRESS_URL = '{ingress_url}';
  const API_BASE = INGRESS_URL;
  const T = {__import__('json').dumps(t, ensure_ascii=False)};

  // Prevent double injection
  if (document.getElementById('ha-claude-bubble')) return;

  // ---- Context Detection ----
  function detectContext() {{
    const path = window.location.pathname;
    const ctx = {{ type: null, id: null, label: null }};

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

    // /config/entities → entity registry
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

    // /lovelace/<path> or /lovelace-<name>/<path>
    m = path.match(/\\/(lovelace[^/]*)\\/?(.*)/);
    if (m) {{
      ctx.type = 'dashboard';
      ctx.id = m[1];
      ctx.label = T.context_dashboard + ': ' + (m[1] || 'default');
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
      return '[CONTEXT: User is viewing dashboard "' + ctx.id + '".] ';
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

  // ---- Styles ----
  const style = document.createElement('style');
  style.textContent = `
    #ha-claude-bubble {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 99999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    #ha-claude-bubble .bubble-btn {{
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
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    #ha-claude-bubble .bubble-btn:hover {{
      transform: scale(1.1);
      box-shadow: 0 6px 24px rgba(0,0,0,0.4);
    }}
    #ha-claude-bubble .bubble-btn.has-context {{
      animation: bubble-pulse 2s infinite;
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
      max-width: calc(100vw - 48px);
      height: 520px;
      max-height: calc(100vh - 120px);
      background: var(--card-background-color, #fff);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
      flex-direction: column;
      overflow: hidden;
      border: 1px solid var(--divider-color, #e0e0e0);
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
    #ha-claude-bubble .msg.error {{
      align-self: center;
      background: var(--error-color, #db4437);
      color: white;
      font-size: 12px;
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
    @media (max-width: 480px) {{
      #ha-claude-bubble .chat-panel {{
        width: calc(100vw - 16px);
        height: calc(100vh - 100px);
        right: 8px;
        bottom: 80px;
        border-radius: 12px;
      }}
      #ha-claude-bubble .bubble-btn {{
        width: 48px;
        height: 48px;
        font-size: 20px;
        bottom: 16px;
        right: 16px;
      }}
    }}
  `;
  document.head.appendChild(style);

  // ---- Build DOM ----
  const root = document.createElement('div');
  root.id = 'ha-claude-bubble';
  root.innerHTML = `
    <div class="chat-panel" id="haChatPanel">
      <div class="chat-header">
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
  const input = document.getElementById('haChatInput');
  const sendBtn = document.getElementById('haChatSend');
  const messagesEl = document.getElementById('haChatMessages');
  const contextBar = document.getElementById('haChatContext');
  const closeBtn = document.getElementById('haChatClose');
  const newBtn = document.getElementById('haChatNew');

  let isOpen = false;
  let isStreaming = false;

  // ---- Toggle Panel ----
  btn.addEventListener('click', () => {{
    isOpen = !isOpen;
    panel.classList.toggle('open', isOpen);
    if (isOpen) {{
      updateContextBar();
      input.focus();
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

  // ---- Context Bar ----
  function updateContextBar() {{
    const ctx = detectContext();
    if (ctx.label) {{
      contextBar.style.display = 'block';
      contextBar.textContent = '📍 ' + ctx.label;
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

  async function sendMessage() {{
    const text = input.value.trim();
    if (!text || isStreaming) return;

    // Add context prefix (invisible to user, sent to AI)
    const contextPrefix = buildContextPrefix();
    const fullMessage = contextPrefix + text;

    addMessage('user', text);
    input.value = '';
    input.style.height = 'auto';
    isStreaming = true;
    sendBtn.disabled = true;

    const thinkingEl = addMessage('thinking', T.thinking + '...');

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

      // Remove thinking indicator
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
            }} else if (evt.type === 'done') {{
              if (evt.full_text) {{
                assistantText = evt.full_text;
                assistantEl.textContent = assistantText;
              }}
            }} else if (evt.type === 'error') {{
              assistantEl.className = 'msg error';
              assistantEl.textContent = evt.message || 'Error';
            }}
          }} catch (parseErr) {{
            // Ignore malformed SSE lines
          }}
        }}
      }}

      if (!assistantText && assistantEl.className.indexOf('error') === -1) {{
        assistantEl.textContent = '...';
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
