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

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Assistant - Home Assistant</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }}
        .main-container {{ display: flex; flex: 1; overflow: hidden; }}
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
        .main-content {{ flex: 1; display: flex; flex-direction: column; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
        .header h1 {{ font-size: 18px; font-weight: 600; }}
        .header .badge {{ font-size: 10px; opacity: 0.9; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px; }}
        .header .new-chat {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 12px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
        .header .new-chat:hover {{ background: rgba(255,255,255,0.35); }}
        .model-selector {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 10px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; max-width: 240px; }}
        .model-selector:hover {{ background: rgba(255,255,255,0.35); }}
        .model-selector option {{ background: #2c3e50; color: white; }}
        .model-selector optgroup {{ background: #1a252f; color: #aaa; font-style: normal; font-weight: 600; padding: 4px 0; }}
        .header .status {{ margin-left: auto; font-size: 12px; display: flex; align-items: center; gap: 6px; }}
        .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: {status_color}; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        .chat-container {{ flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }}
        .message {{ max-width: 85%; padding: 12px 16px; border-radius: 16px; line-height: 1.5; font-size: 14px; word-wrap: break-word; animation: fadeIn 0.3s ease; }}
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
        @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
        .input-area {{ padding: 12px 16px; background: white; border-top: 1px solid #e0e0e0; display: flex; flex-direction: column; gap: 8px; }}
        .image-preview-container {{ display: none; padding: 8px; background: #f8f9fa; border-radius: 8px; position: relative; }}
        .image-preview-container.visible {{ display: block; }}
        .image-preview {{ max-width: 150px; max-height: 150px; border-radius: 8px; border: 2px solid #667eea; }}
        .remove-image-btn {{ position: absolute; top: 4px; right: 4px; background: #ef4444; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; }}
        .input-row {{ display: flex; gap: 8px; align-items: flex-end; }}
        .input-area textarea {{ flex: 1; border: 1px solid #ddd; border-radius: 20px; padding: 10px 16px; font-size: 14px; font-family: inherit; resize: none; max-height: 120px; outline: none; transition: border-color 0.2s; }}
        .input-area textarea:focus {{ border-color: #667eea; }}
        .input-area button {{ background: #667eea; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; }}
        .input-area button:hover {{ background: #5a6fd6; }}
        .input-area button:disabled {{ background: #ccc; cursor: not-allowed; }}
        .input-area button.stop-btn {{ background: #ef4444; animation: pulse-stop 1s infinite; }}
        .input-area button.stop-btn:hover {{ background: #dc2626; }}
        .input-area button.image-btn {{ background: #10b981; }}
        .input-area button.image-btn:hover {{ background: #059669; }}
        @keyframes pulse-stop {{ 0%, 100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }} 50% {{ box-shadow: 0 0 0 6px rgba(239,68,68,0); }} }}
        .suggestions {{ display: flex; gap: 8px; padding: 0 16px 8px; flex-wrap: wrap; }}
        .suggestion {{ background: white; border: 1px solid #ddd; border-radius: 16px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }}
        .suggestion:hover {{ background: #667eea; color: white; border-color: #667eea; }}
        .tool-badge {{ display: inline-block; background: #e8f0fe; color: #1967d2; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
        .status-badge {{ display: inline-block; background: #fef3c7; color: #92400e; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
        .undo-button {{ display: inline-block; background: #fef3c7; color: #92400e; border: none; padding: 6px 12px; border-radius: 12px; font-size: 12px; margin-top: 8px; cursor: pointer; transition: opacity 0.2s; }}
        .undo-button:hover {{ opacity: 0.9; }}
        .undo-button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px;">\U0001f916</span>
        <h1>AI Assistant</h1>
        <span class="badge">v{api.VERSION}</span>
        <select id="modelSelect" class="model-selector" onchange="changeModel(this.value)" title="Cambia modello"></select>
        <button id="testNvidiaBtn" class="new-chat" onclick="testNvidiaModel()" title="Test veloce NVIDIA (può richiedere qualche secondo)" style="display:none">🔍 Test NVIDIA</button>
        <!-- Populated by JavaScript -->
        <button class="new-chat" onclick="newChat()" title="Nuova conversazione">✨ Nuova chat</button>
        <div class="status">
            <div class="status-dot"></div>
            {status_text}
        </div>
    </div>

    <div class="main-container">
        <div class="sidebar">
            <div class="sidebar-header">📝 Conversazioni</div>
            <div class="chat-list" id="chatList"></div>
        </div>
        <div class="splitter" id="sidebarSplitter" title="Trascina per ridimensionare"></div>
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
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f4a1 Mostra tutte le luci</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f321 Stato sensori</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f3e0 Stanze e aree</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f4c8 Storico temperatura</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f3ac Scene disponibili</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\u2699\ufe0f Lista automazioni</div>
    </div>

    <div class="input-area">
        <div id="imagePreviewContainer" class="image-preview-container">
            <img id="imagePreview" class="image-preview" />
            <button class="remove-image-btn" onclick="removeImage()" title="Rimuovi immagine">×</button>
        </div>
        <div class="input-row">
            <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageSelect(event)" />
            <button class="image-btn" onclick="document.getElementById('imageInput').click()" title="Carica immagine">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
            </button>
            <textarea id="input" rows="1" placeholder="Scrivi un messaggio..." onkeydown="handleKeyDown(event)" oninput="autoResize(this)"></textarea>
            <button id="sendBtn" onclick="handleButtonClick()">
                <svg id="sendIcon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                <svg id="stopIcon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="display:none"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
            </button>
        </div>
    </div>
        </div>
    </div>

    <script>
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
        let currentSessionId = localStorage.getItem('currentSessionId') || Date.now().toString();
        let currentImage = null;  // Stores base64 image data
        let currentProviderId = '{api.AI_PROVIDER}';

        const ANALYZING_BY_PROVIDER = {{
            'anthropic': {json.dumps(provider_analyzing['anthropic'].get(api.LANGUAGE, provider_analyzing['anthropic']['en']))},
            'openai': {json.dumps(provider_analyzing['openai'].get(api.LANGUAGE, provider_analyzing['openai']['en']))},
            'google': {json.dumps(provider_analyzing['google'].get(api.LANGUAGE, provider_analyzing['google']['en']))},
            'github': {json.dumps(provider_analyzing['github'].get(api.LANGUAGE, provider_analyzing['github']['en']))},
            'nvidia': {json.dumps(provider_analyzing['nvidia'].get(api.LANGUAGE, provider_analyzing['nvidia']['en']))}
        }};

        function getAnalyzingMsg() {{
            return ANALYZING_BY_PROVIDER[currentProviderId] || ANALYZING_BY_PROVIDER['openai'];
        }}

        function initSidebarResize() {{
            if (!sidebarEl || !splitterEl) return;

            const minWidth = 150;
            const maxWidth = 500;
            const storageKey = 'chatSidebarWidth';

            const saved = parseInt(localStorage.getItem(storageKey) || '', 10);
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
                localStorage.setItem(storageKey, String(finalW));
            }});
        }}

        function handleImageSelect(event) {{
            const file = event.target.files[0];
            if (!file) return;

            // Check file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {{
                alert('L\\'immagine è troppo grande. Massimo 5MB.');
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

        function apiUrl(path) {{
            // Build URLs robustly for Home Assistant Ingress.
            // If the current page URL doesn't end with '/', browsers treat the last segment as a file
            // and relative fetches may drop it (breaking requests).
            const cleanPath = (path || '').startsWith('/') ? (path || '').slice(1) : (path || '');
            const base = window.location.href.endsWith('/') ? window.location.href : (window.location.href + '/');
            return new URL(cleanPath, base).toString();
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
                sendMessage();
            }}
        }}

        function autoResize(el) {{
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        }}

        function handleKeyDown(e) {{
            if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); sendMessage(); }}
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
            btn.textContent = '↩︎ Ripristina backup';
            btn.title = 'Ripristina il backup (snapshot: ' + snapshotId + ')';
            btn.onclick = () => restoreSnapshot(snapshotId, btn);
            div.appendChild(btn);
        }}

        async function restoreSnapshot(snapshotId, btn) {{
            if (!snapshotId) return;
            if (!confirm('Vuoi ripristinare il backup? Questa operazione annulla la modifica appena fatta.')) return;

            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = '⏳ Ripristino...';
            try {{
                const resp = await fetch(apiUrl('api/snapshots/restore'), {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ snapshot_id: snapshotId }})
                }});
                const data = await resp.json().catch(() => ({{}}));
                if (resp.ok && data && data.status === 'success') {{
                    btn.textContent = '✓ Ripristinato';
                    addMessage('✅ Backup ripristinato. Se necessario, aggiorna la pagina Lovelace o verifica l’automazione/script.', 'system');
                }} else {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    const msg = (data && (data.error || data.message)) ? (data.error || data.message) : 'Ripristino fallito.';
                    addMessage('❌ ' + msg, 'system');
                }}
            }} catch (e) {{
                btn.disabled = false;
                btn.textContent = originalText;
                addMessage('❌ Errore ripristino: ' + e.message, 'system');
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
            text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<div class="code-block"><button class="copy-button" onclick="copyCode(this)">\U0001F4CB Copia</button><pre><code>$2</code></pre></div>');
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
                button.textContent = '✓ Copiato!';
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
            div.innerHTML = getAnalyzingMsg() + '<span class="dots"><span>.</span><span>.</span><span>.</span></span>';
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}

        function removeThinking() {{
            const el = document.getElementById('thinking');
            if (el) el.remove();
        }}

        function sendSuggestion(el) {{
            input.value = el.textContent.replace(/^.{{2}}/, '').trim();
            sendMessage();
        }}

        async function sendMessage() {{
            const text = (input && input.value ? input.value : '').trim();
            if (!text || sending) return;

            sending = true;
            setStopMode(true);

            try {{
                if (input) {{
                    input.value = '';
                    input.style.height = 'auto';
                }}
                if (suggestionsEl && suggestionsEl.style) {{
                    suggestionsEl.style.display = 'none';
                }}

                // Show user message with image if present
                const imageToSend = currentImage;
                addMessage(text, 'user', imageToSend);
                // Clear the preview immediately (keep imageToSend for the request payload)
                removeImage();
                showThinking();

                const payload = {{
                    message: text,
                    session_id: currentSessionId
                }};
                if (imageToSend) {{
                    payload.image = imageToSend;
                }}

                const resp = await fetch(apiUrl('api/chat/stream'), {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});

                removeThinking();

                if (!resp.ok) {{
                    const bodyText = await resp.text().catch(() => '');
                    throw new Error('Richiesta fallita (' + resp.status + '): ' + (bodyText ? bodyText.slice(0, 200) : '')); 
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
                        addMessage('\u274c Risposta inattesa dal server.', 'system');
                    }}
                }}
            }} catch (err) {{
                removeThinking();
                if (err && err.name !== 'AbortError') {{
                    addMessage('\u274c Errore: ' + (err.message || String(err)), 'system');
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
                                removeThinking();
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                hasTools = true;
                                const desc = evt.description || evt.name;
                                div.innerHTML += '<div class="tool-badge">\U0001f527 ' + desc + '</div>';
                            }} else if (evt.type === 'clear') {{
                                removeThinking();
                                if (div) {{ div.innerHTML = ''; }}
                                fullText = '';
                                hasTools = false;
                            }} else if (evt.type === 'status') {{
                                removeThinking();
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                const oldStatus = div.querySelector('.status-badge');
                                if (oldStatus) oldStatus.remove();
                                div.innerHTML += '<div class="status-badge">\u23f3 ' + evt.message + '</div>';
                            }} else if (evt.type === 'token') {{
                                removeThinking();
                                if (hasTools && div) {{ div.innerHTML = ''; fullText = ''; hasTools = false; }}
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                fullText += evt.content;
                                div.innerHTML = formatMarkdown(fullText);
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
                                }}
                            }}
                            chat.scrollTop = chat.scrollHeight;
                        }} catch(e) {{}}
                    }}
                }}
            }}
            }} catch(streamErr) {{
                if (streamErr.name !== 'AbortError') {{
                    console.error('Stream error:', streamErr);
                }}
            }}
            removeThinking();
            if (!gotAnyEvent) {{
                addMessage('\u274c Connessione interrotta. Riprova.', 'system');
            }}
        }}

        async function loadChatList() {{
            try {{
                const resp = await fetch(apiUrl('api/conversations'));
                const data = await resp.json();
                chatList.innerHTML = '';
                if (data.conversations && data.conversations.length > 0) {{
                    data.conversations.forEach(conv => {{
                        const item = document.createElement('div');
                        item.className = 'chat-item' + (conv.id === currentSessionId ? ' active' : '');
                        item.innerHTML = `
                            <div style="flex: 1;" onclick="loadConversation('${{conv.id}}')">
                                <div class="chat-item-title">${{conv.title}}</div>
                                <div class="chat-item-info">${{conv.message_count}} messaggi</div>
                            </div>
                            <span class="chat-item-delete" onclick="deleteConversation(event, '${{conv.id}}')" title="Elimina chat">\U0001f5d1</span>
                        `;
                        chatList.appendChild(item);
                    }});
                }} else {{
                    chatList.innerHTML = '<div style="padding: 12px; text-align: center; color: #999; font-size: 12px;">Nessuna conversazione</div>';
                }}
            }} catch(e) {{ console.error('Error loading chat list:', e); }}
        }}

        async function deleteConversation(event, sessionId) {{
            event.stopPropagation();
            if (!confirm('Eliminare questa conversazione?')) return;
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
            localStorage.setItem('currentSessionId', sessionId);
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
            }} catch(e) {{ console.error('Error loading conversation:', e); }}
        }}

        async function loadHistory() {{
            await loadConversation(currentSessionId);
        }}

        async function newChat() {{
            currentSessionId = Date.now().toString();
            localStorage.setItem('currentSessionId', currentSessionId);
            chat.innerHTML = `<div class="message system">
                {msgs['welcome']}<br>
                {msgs['provider_model']}<br>
                {msgs['capabilities']}<br>
                {msgs['vision_feature']}
            </div>`;
            suggestionsEl.style.display = 'flex';
            removeImage();
            loadChatList();
        }}

        // Provider name mapping for optgroups
        const PROVIDER_LABELS = {{
            'anthropic': '🧠 Anthropic Claude',
            'openai': '⚡ OpenAI',
            'google': '✨ Google Gemini',
            'nvidia': '🎯 NVIDIA NIM',
            'github': '🚀 GitHub Models'
        }};

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
                    addMessage('👆 Seleziona un agente dal menu in alto per iniziare. Potrai cambiarlo in qualsiasi momento.', 'system');
                    window._firstSelectionPrompted = true;
                }}

                if (currentProvider) {{
                    currentProviderId = currentProvider;
                }}

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
                            {{ label: (PROVIDER_LABELS[providerId] || providerId) + ' ✅ Testati', models: tested }},
                            {{ label: (PROVIDER_LABELS[providerId] || providerId) + ' Da testare', models: toTest }},
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
                    option.textContent = 'Nessun modello disponibile';
                    option.disabled = true;
                    option.selected = true;
                    select.appendChild(option);
                    if (!window._modelsEmptyNotified) {{
                        addMessage('⚠️ Nessun modello disponibile. Verifica le API key dei provider.', 'system');
                        window._modelsEmptyNotified = true;
                    }}
                }}
                console.log('[loadModels] Loaded models for', availableProviders.length, 'providers');
            }} catch (error) {{
                console.error('[loadModels] Error loading models:', error);
                if (!window._modelsErrorNotified) {{
                    addMessage('⚠️ Errore nel caricamento dei modelli: ' + (error.message || error), 'system');
                    window._modelsErrorNotified = true;
                }}
            }}
        }}

        async function testNvidiaModel() {{
            const btn = document.getElementById('testNvidiaBtn');
            if (!btn) return;

            const cursorKey = 'nvidiaTestCursor';
            const cursor = parseInt(localStorage.getItem(cursorKey) || '0', 10) || 0;

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
                        localStorage.setItem(cursorKey, String(data.next_cursor));
                    }}
                    if (typeof data.remaining === 'number' && data.remaining <= 0) {{
                        localStorage.setItem(cursorKey, '0');
                    }}
                    const parts = [];
                    parts.push(`Test NVIDIA: OK ${{data.ok}}, rimossi ${{data.removed}}, testati ${{data.tested}}/${{data.total}}`);
                    if (data.stopped_reason) parts.push(`(${{data.stopped_reason}})`);
                    if (typeof data.timeouts === 'number' && data.timeouts > 0) parts.push(`— timeout: ${{data.timeouts}}`);
                    if (typeof data.remaining === 'number' && data.remaining > 0) parts.push(`— restanti: ${{data.remaining}} (ripremi per continuare)`);
                    addMessage('🔍 ' + parts.join(' '), 'system');
                }} else {{
                    const msg = (data && (data.message || data.error)) || ('Test NVIDIA fallito (' + response.status + ')');
                    addMessage('⚠️ ' + msg, 'system');
                }}

                if (data && data.blocklisted) await loadModels();
            }} catch (e) {{
                addMessage('⚠️ Test NVIDIA fallito: ' + (e && e.message ? e.message : String(e)), 'system');
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
                    addMessage(`🔄 Passato a ${{providerName}} → ${{parsed.model}}`, 'system');
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
        initSidebarResize();
        loadModels();
        loadChatList();
        loadHistory();
        input.focus();
    </script>
</body>
</html>"""
