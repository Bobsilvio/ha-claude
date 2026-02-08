// ══════════════════════════════════════════
// Claude AI - Chat Application
// ══════════════════════════════════════════

let isWaiting = false;
let allEntities = [];

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    fetchHealth();
    document.getElementById("message-input").focus();
});

// ── API Calls ──

async function fetchHealth() {
    try {
        const res = await fetch(`${INGRESS_PATH}/api/health`);
        const data = await res.json();
        document.getElementById("model-info").textContent = `${data.model} • ${data.language.toUpperCase()}`;
    } catch (e) {
        console.error("Health check failed:", e);
    }
}

async function sendMessage() {
    const input = document.getElementById("message-input");
    const message = input.value.trim();
    if (!message || isWaiting) return;

    // Hide welcome
    const welcome = document.getElementById("welcome");
    if (welcome) welcome.style.display = "none";

    // Add user message
    addMessage("user", message);
    input.value = "";
    autoResize(input);
    
    // Show typing indicator
    isWaiting = true;
    document.getElementById("send-btn").disabled = true;
    showTyping();

    try {
        const res = await fetch(`${INGRESS_PATH}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, session_id: SESSION_ID }),
        });

        removeTyping();

        if (!res.ok) {
            const err = await res.json();
            addError(err.error || "Errore sconosciuto");
            return;
        }

        const data = await res.json();

        // Show tool calls if any
        if (data.tools_used && data.tools_used.length > 0) {
            for (const tool of data.tools_used) {
                addToolIndicator(tool.tool, tool.input);
            }
        }

        // Add AI response
        addMessage("assistant", data.response);

    } catch (e) {
        removeTyping();
        addError(`Errore di connessione: ${e.message}`);
    } finally {
        isWaiting = false;
        document.getElementById("send-btn").disabled = false;
        input.focus();
    }
}

async function clearChat() {
    try {
        await fetch(`${INGRESS_PATH}/api/clear`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: SESSION_ID }),
        });
    } catch (e) {
        console.error("Clear failed:", e);
    }

    const container = document.getElementById("chat-container");
    container.innerHTML = `
        <div class="welcome-message" id="welcome">
            <div class="welcome-icon">🏠</div>
            <h2>Benvenuto in Claude AI</h2>
            <p>Chiedimi qualsiasi cosa sulla tua casa smart!</p>
            <div class="suggestions">
                <button class="suggestion" onclick="sendSuggestion(this)">💡 Quali luci sono accese?</button>
                <button class="suggestion" onclick="sendSuggestion(this)">🌡️ Qual è la temperatura in casa?</button>
                <button class="suggestion" onclick="sendSuggestion(this)">⚡ Crea un'automazione per le luci</button>
                <button class="suggestion" onclick="sendSuggestion(this)">📊 Mostra tutti i sensori</button>
            </div>
        </div>
    `;
}

async function showEntities() {
    const modal = document.getElementById("entities-modal");
    modal.classList.add("active");
    
    const list = document.getElementById("entity-list");
    list.innerHTML = "<p>Caricamento...</p>";

    try {
        const res = await fetch(`${INGRESS_PATH}/api/entities`);
        const data = await res.json();
        allEntities = data.entities || [];
        renderEntities(allEntities);
    } catch (e) {
        list.innerHTML = `<p class="error-msg">Errore: ${e.message}</p>`;
    }
}

function renderEntities(entities) {
    const list = document.getElementById("entity-list");
    if (entities.length === 0) {
        list.innerHTML = "<p>Nessuna entità trovata</p>";
        return;
    }

    list.innerHTML = entities.slice(0, 200).map(e => {
        const name = e.attributes?.friendly_name || e.entity_id;
        const stateClass = e.state === "on" ? "on" : (e.state === "off" ? "off" : "");
        return `
            <div class="entity-item">
                <div>
                    <div>${name}</div>
                    <div class="entity-id">${e.entity_id}</div>
                </div>
                <span class="entity-state ${stateClass}">${e.state}</span>
            </div>
        `;
    }).join("");
}

function filterEntities() {
    const query = document.getElementById("entity-search").value.toLowerCase();
    const filtered = allEntities.filter(e => 
        e.entity_id.toLowerCase().includes(query) || 
        (e.attributes?.friendly_name || "").toLowerCase().includes(query)
    );
    renderEntities(filtered);
}

function closeModal(event) {
    if (event.target === event.currentTarget) {
        event.target.classList.remove("active");
    }
}

// ── UI Helpers ──

function addMessage(role, content) {
    const container = document.getElementById("chat-container");
    const avatar = role === "user" ? "👤" : "🤖";
    
    // Simple markdown-like formatting
    let formatted = escapeHtml(content)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,0.1);padding:2px 6px;border-radius:4px;font-size:13px;">$1</code>')
        .replace(/\n/g, '<br>');
    
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${formatted}</div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function addToolIndicator(toolName, toolInput) {
    const container = document.getElementById("chat-container");
    
    const toolIcons = {
        "get_entities": "🔍",
        "get_entity_state": "📡",
        "call_service": "⚡",
        "create_automation": "🔧",
        "get_history": "📊",
    };
    
    const toolLabels = {
        "get_entities": "Lettura entità",
        "get_entity_state": `Stato: ${toolInput.entity_id || ""}`,
        "call_service": `${toolInput.domain || ""}.${toolInput.service || ""}`,
        "create_automation": `Automazione: ${toolInput.alias || ""}`,
        "get_history": `Cronologia: ${toolInput.entity_id || ""}`,
    };

    const div = document.createElement("div");
    div.className = "tool-indicator";
    div.innerHTML = `
        <span class="icon">${toolIcons[toolName] || "🔧"}</span>
        <span>${toolLabels[toolName] || toolName}</span>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function addError(message) {
    const container = document.getElementById("chat-container");
    const div = document.createElement("div");
    div.className = "error-msg";
    div.textContent = `❌ ${message}`;
    container.appendChild(div);
    scrollToBottom();
}

function showTyping() {
    const container = document.getElementById("chat-container");
    const div = document.createElement("div");
    div.className = "typing-indicator";
    div.id = "typing";
    div.innerHTML = `
        <div class="message-avatar" style="background:var(--bg-secondary)">🤖</div>
        <div class="typing-dots">
            <span></span><span></span><span></span>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function removeTyping() {
    const el = document.getElementById("typing");
    if (el) el.remove();
}

function scrollToBottom() {
    const container = document.getElementById("chat-container");
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ── Input Handlers ──

function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResize(textarea) {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
}

function sendSuggestion(button) {
    const input = document.getElementById("message-input");
    input.value = button.textContent.replace(/^[\u{1F300}-\u{1FAD6}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]\s*/u, "");
    sendMessage();
}
