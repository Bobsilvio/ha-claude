"""Flask API with real Claude AI integration for Home Assistant."""

import os
import json
import logging
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import anthropic

load_dotenv()

app = Flask(__name__)
CORS(app)

# Version
VERSION = "2.2.0"

# Configuration
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
HA_TOKEN = os.getenv("SUPERVISOR_TOKEN", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
API_PORT = int(os.getenv("API_PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO)
logger = logging.getLogger(__name__)

# Home Assistant headers
HA_HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

# Claude client
claude_client = None
if CLAUDE_API_KEY:
    claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    logger.info("Claude API client initialized")
else:
    logger.warning("CLAUDE_API_KEY not set - Claude integration disabled")

# Conversation history (per-session, in memory)
conversations: Dict[str, List[Dict]] = {}

# ---- Home Assistant API helpers ----


def call_ha_api(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
    """Call Home Assistant API."""
    url = f"{HA_URL}/api/{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HA_HEADERS, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HA_HEADERS, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=HA_HEADERS, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}

        if response.status_code in [200, 201]:
            return response.json() if response.text else {"status": "success"}
        else:
            logger.error(f"HA API error {response.status_code}: {response.text}")
            return {"error": f"API error {response.status_code}", "details": response.text}
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"error": str(e)}


def get_all_states() -> List[Dict]:
    """Get all entity states from HA."""
    result = call_ha_api("GET", "states")
    return result if isinstance(result, list) else []


# ---- Claude Tool Definitions ----

CLAUDE_TOOLS = [
    {
        "name": "get_entities",
        "description": "Get the current state of all Home Assistant entities, or filter by domain (e.g. 'light', 'switch', 'sensor', 'automation', 'climate'). Returns entity_id, state, and attributes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Optional domain to filter (e.g. 'light', 'switch', 'sensor', 'climate', 'automation'). If empty, returns all."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_entity_state",
        "description": "Get the current state and attributes of a specific entity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID (e.g. 'light.living_room', 'sensor.temperature')."
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "call_service",
        "description": "Call a Home Assistant service. Use this to control devices: turn on/off lights, switches, set climate temperature, lock/unlock, open/close covers, send notifications, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain (e.g. 'light', 'switch', 'climate', 'cover', 'lock', 'media_player', 'notify')."
                },
                "service": {
                    "type": "string",
                    "description": "Service name (e.g. 'turn_on', 'turn_off', 'toggle', 'set_temperature')."
                },
                "data": {
                    "type": "object",
                    "description": "Service data including target entity_id and any parameters."
                }
            },
            "required": ["domain", "service", "data"]
        }
    },
    {
        "name": "create_automation",
        "description": "Create a new Home Assistant automation. Provide alias, triggers, conditions (optional), and actions using HA format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "alias": {
                    "type": "string",
                    "description": "Human-readable name for the automation."
                },
                "description": {
                    "type": "string",
                    "description": "Description of what the automation does."
                },
                "trigger": {
                    "type": "array",
                    "description": "List of triggers.",
                    "items": {"type": "object"}
                },
                "condition": {
                    "type": "array",
                    "description": "Optional list of conditions.",
                    "items": {"type": "object"}
                },
                "action": {
                    "type": "array",
                    "description": "List of actions to execute.",
                    "items": {"type": "object"}
                },
                "mode": {
                    "type": "string",
                    "description": "Automation mode: 'single', 'restart', 'queued', 'parallel'.",
                    "enum": ["single", "restart", "queued", "parallel"]
                }
            },
            "required": ["alias", "trigger", "action"]
        }
    },
    {
        "name": "get_automations",
        "description": "Get all existing automations with their state and last triggered time.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "trigger_automation",
        "description": "Manually trigger/run an existing automation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The automation entity_id (e.g. 'automation.my_automation')."
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_available_services",
        "description": "Get a list of all available Home Assistant service domains and their services.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# ---- Tool execution ----


def execute_tool(tool_name: str, tool_input: Dict) -> str:
    """Execute a Claude tool call and return the result as string."""
    try:
        if tool_name == "get_entities":
            domain = tool_input.get("domain", "")
            states = get_all_states()
            if domain:
                states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
            result = []
            for s in states[:100]:
                result.append({
                    "entity_id": s.get("entity_id"),
                    "state": s.get("state"),
                    "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                    "attributes": {k: v for k, v in s.get("attributes", {}).items()
                                   if k in ("friendly_name", "unit_of_measurement", "device_class",
                                            "brightness", "color_temp", "temperature",
                                            "current_temperature", "hvac_modes")}
                })
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "get_entity_state":
            entity_id = tool_input.get("entity_id", "")
            result = call_ha_api("GET", f"states/{entity_id}")
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "call_service":
            domain = tool_input.get("domain", "")
            service = tool_input.get("service", "")
            data = tool_input.get("data", {})
            result = call_ha_api("POST", f"services/{domain}/{service}", data)
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "create_automation":
            automation_config = {
                "alias": tool_input.get("alias", "New Automation"),
                "description": tool_input.get("description", ""),
                "trigger": tool_input.get("trigger", []),
                "condition": tool_input.get("condition", []),
                "action": tool_input.get("action", []),
                "mode": tool_input.get("mode", "single"),
            }
            result = call_ha_api("POST", "config/automation/config/new", automation_config)
            if isinstance(result, dict) and "error" not in result:
                return json.dumps({
                    "status": "success",
                    "message": f"Automation '{automation_config['alias']}' created!",
                    "result": result
                }, ensure_ascii=False)
            else:
                return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_automations":
            states = get_all_states()
            automations = [s for s in states if s.get("entity_id", "").startswith("automation.")]
            result = []
            for a in automations:
                result.append({
                    "entity_id": a.get("entity_id"),
                    "state": a.get("state"),
                    "friendly_name": a.get("attributes", {}).get("friendly_name", ""),
                    "last_triggered": a.get("attributes", {}).get("last_triggered", ""),
                })
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "trigger_automation":
            entity_id = tool_input.get("entity_id", "")
            result = call_ha_api("POST", "services/automation/trigger", {"entity_id": entity_id})
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_available_services":
            services_raw = call_ha_api("GET", "services")
            if isinstance(services_raw, list):
                compact = {}
                for svc in services_raw:
                    domain = svc.get("domain", "")
                    compact[domain] = list(svc.get("services", {}).keys())
                return json.dumps(compact, ensure_ascii=False)
            return json.dumps(services_raw, ensure_ascii=False, default=str)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}")
        return json.dumps({"error": str(e)})


# ---- System prompt ----

SYSTEM_PROMPT = """You are Claude, an AI assistant integrated into Home Assistant. You help users manage their smart home.

You can:
1. **Query entities** - See the state of all devices (lights, sensors, switches, climate, covers, etc.)
2. **Control devices** - Turn on/off lights, switches, set temperatures, open/close covers, etc.
3. **Create automations** - Build new automations with triggers, conditions, and actions
4. **List automations** - See existing automations
5. **Trigger automations** - Manually run automations
6. **Discover services** - See all available HA services

When creating automations, use proper Home Assistant trigger/action formats. Examples:

Triggers:
- State: {"platform": "state", "entity_id": "binary_sensor.motion", "to": "on"}
- Time: {"platform": "time", "at": "07:00:00"}
- Sun: {"platform": "sun", "event": "sunset", "offset": "-00:30:00"}
- Numeric state: {"platform": "numeric_state", "entity_id": "sensor.temperature", "above": 25}

Actions:
- Service call: {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 255}}
- Delay: {"delay": {"seconds": 30}}
- Notification: {"service": "notify.mobile_app", "data": {"message": "Hello!"}}
- Condition check: {"condition": "state", "entity_id": "input_boolean.away", "state": "on"}

Always respond in the same language the user uses.
When you create an automation, confirm what was created and explain how it works.
When listing entities, organize them clearly by type.
Be concise but informative."""


# ---- Chat with Claude ----


def chat_with_claude(user_message: str, session_id: str = "default") -> str:
    """Send a message to Claude with HA tool-calling capabilities."""
    if not claude_client:
        return "\u26a0\ufe0f Claude API key non configurata. Impostala nelle impostazioni dell'add-on."

    # Get or create conversation history
    if session_id not in conversations:
        conversations[session_id] = []

    # Add user message
    conversations[session_id].append({"role": "user", "content": user_message})

    # Keep last 20 messages to avoid token limits
    messages = conversations[session_id][-20:]

    try:
        # Call Claude with tools
        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=CLAUDE_TOOLS,
            messages=messages
        )

        # Process tool calls in a loop
        while response.stop_reason == "tool_use":
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"Tool call: {block.name}({json.dumps(block.input, ensure_ascii=False)[:200]})")
                    tool_result = execute_tool(block.name, block.input)
                    logger.info(f"Tool result: {tool_result[:300]}...")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    })

            # Add assistant message + tool results
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            # Continue the conversation
            response = claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=CLAUDE_TOOLS,
                messages=messages
            )

        # Extract final text response
        final_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                final_text += block.text

        # Save to conversation history
        conversations[session_id] = messages
        conversations[session_id].append({"role": "assistant", "content": final_text})

        return final_text

    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return f"\u274c Claude API error: {e.message}"
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return f"\u274c Error: {str(e)}"


# ---- Chat UI HTML ----


def get_chat_ui():
    """Generate the chat UI."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Claude AI - Home Assistant</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
        .header h1 {{ font-size: 18px; font-weight: 600; }}
        .header .version {{ font-size: 11px; opacity: 0.8; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px; }}
        .header .status {{ margin-left: auto; font-size: 12px; display: flex; align-items: center; gap: 6px; }}
        .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #4caf50; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        .chat-container {{ flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }}
        .message {{ max-width: 85%; padding: 12px 16px; border-radius: 16px; line-height: 1.5; font-size: 14px; word-wrap: break-word; animation: fadeIn 0.3s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .message.user {{ background: #667eea; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }}
        .message.assistant {{ background: white; color: #333; align-self: flex-start; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .message.assistant pre {{ background: #f5f5f5; padding: 10px; border-radius: 8px; overflow-x: auto; margin: 8px 0; font-size: 13px; }}
        .message.assistant code {{ background: #f0f0f0; padding: 1px 5px; border-radius: 4px; font-size: 13px; }}
        .message.assistant pre code {{ background: none; padding: 0; }}
        .message.assistant strong {{ color: #333; }}
        .message.assistant ul, .message.assistant ol {{ margin: 6px 0 6px 20px; }}
        .message.assistant p {{ margin: 4px 0; }}
        .message.system {{ background: #fff3cd; color: #856404; align-self: center; text-align: center; font-size: 13px; border-radius: 8px; max-width: 90%; }}
        .message.thinking {{ background: #f8f9fa; color: #999; align-self: flex-start; border-bottom-left-radius: 4px; font-style: italic; }}
        .message.thinking .dots {{ display: inline-block; }}
        .message.thinking .dots span {{ animation: blink 1.4s infinite both; }}
        .message.thinking .dots span:nth-child(2) {{ animation-delay: 0.2s; }}
        .message.thinking .dots span:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
        .input-area {{ padding: 12px 16px; background: white; border-top: 1px solid #e0e0e0; display: flex; gap: 8px; align-items: flex-end; }}
        .input-area textarea {{ flex: 1; border: 1px solid #ddd; border-radius: 20px; padding: 10px 16px; font-size: 14px; font-family: inherit; resize: none; max-height: 120px; outline: none; transition: border-color 0.2s; }}
        .input-area textarea:focus {{ border-color: #667eea; }}
        .input-area button {{ background: #667eea; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; flex-shrink: 0; }}
        .input-area button:hover {{ background: #5a6fd6; }}
        .input-area button:disabled {{ background: #ccc; cursor: not-allowed; }}
        .suggestions {{ display: flex; gap: 8px; padding: 0 16px 8px; flex-wrap: wrap; }}
        .suggestion {{ background: white; border: 1px solid #ddd; border-radius: 16px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }}
        .suggestion:hover {{ background: #667eea; color: white; border-color: #667eea; }}
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px;">\U0001f916</span>
        <h1>Claude AI</h1>
        <span class="version">v{VERSION}</span>
        <div class="status">
            <div class="status-dot"></div>
            Home Assistant
        </div>
    </div>

    <div class="chat-container" id="chat">
        <div class="message system">
            \U0001f44b Ciao! Sono Claude, il tuo assistente AI per Home Assistant.<br>
            Posso controllare dispositivi, creare automazioni e gestire la tua casa smart.
        </div>
    </div>

    <div class="suggestions" id="suggestions">
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f4a1 Mostra tutte le luci</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f321 Stato sensori</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\u2699\ufe0f Lista automazioni</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f3e0 Stato della casa</div>
    </div>

    <div class="input-area">
        <textarea id="input" rows="1" placeholder="Scrivi un messaggio..." onkeydown="handleKeyDown(event)" oninput="autoResize(this)"></textarea>
        <button id="sendBtn" onclick="sendMessage()">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('sendBtn');
        const suggestionsEl = document.getElementById('suggestions');
        let sending = false;

        function autoResize(el) {{
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        }}

        function handleKeyDown(e) {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                sendMessage();
            }}
        }}

        function addMessage(text, role) {{
            const div = document.createElement('div');
            div.className = 'message ' + role;
            if (role === 'assistant') {{
                div.innerHTML = formatMarkdown(text);
            }} else {{
                div.textContent = text;
            }}
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
            return div;
        }}

        function formatMarkdown(text) {{
            // Code blocks
            text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<pre><code>$2</code></pre>');
            // Inline code
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            // Bold
            text = text.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
            // Italic
            text = text.replace(/(?<![*])\\*(?![*])(.+?)(?<![*])\\*(?![*])/g, '<em>$1</em>');
            // Line breaks
            text = text.replace(/\\n/g, '<br>');
            return text;
        }}

        function showThinking() {{
            const div = document.createElement('div');
            div.className = 'message thinking';
            div.id = 'thinking';
            div.innerHTML = 'Claude sta pensando<span class="dots"><span>.</span><span>.</span><span>.</span></span>';
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}

        function removeThinking() {{
            const el = document.getElementById('thinking');
            if (el) el.remove();
        }}

        function sendSuggestion(el) {{
            const text = el.textContent.replace(/^[\\s\\S]{{2}}/, '').trim();
            input.value = text;
            sendMessage();
        }}

        async function sendMessage() {{
            const text = input.value.trim();
            if (!text || sending) return;

            sending = true;
            sendBtn.disabled = true;
            input.value = '';
            input.style.height = 'auto';
            suggestionsEl.style.display = 'none';

            addMessage(text, 'user');
            showThinking();

            try {{
                const resp = await fetch('api/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: text }})
                }});
                const data = await resp.json();
                removeThinking();

                if (data.response) {{
                    addMessage(data.response, 'assistant');
                }} else if (data.error) {{
                    addMessage('\u274c ' + data.error, 'system');
                }}
            }} catch (err) {{
                removeThinking();
                addMessage('\u274c Errore di connessione: ' + err.message, 'system');
            }}

            sending = false;
            sendBtn.disabled = false;
            input.focus();
        }}

        input.focus();
    </script>
</body>
</html>"""


# ---- Flask Routes ----


@app.route('/')
def index():
    """Serve the chat UI."""
    return get_chat_ui(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint - sends message to Claude with HA tools."""
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not message:
        return jsonify({"error": "Empty message"}), 400

    logger.info(f"Chat message: {message}")
    response_text = chat_with_claude(message, session_id)

    return jsonify({"response": response_text}), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "claude_configured": bool(CLAUDE_API_KEY),
        "ha_connected": bool(HA_TOKEN),
    }), 200


@app.route("/entities", methods=["GET"])
def get_entities_route():
    """Get all entities."""
    domain = request.args.get("domain", "")
    states = get_all_states()
    if domain:
        states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
    return jsonify({"entities": states, "count": len(states)}), 200


@app.route("/entity/<entity_id>/state", methods=["GET"])
def get_entity_state_route(entity_id: str):
    """Get entity state."""
    result = call_ha_api("GET", f"states/{entity_id}")
    return jsonify(result), 200


@app.route("/message", methods=["POST"])
def send_message_legacy():
    """Send a message to Claude (legacy endpoint)."""
    data = request.get_json()
    message = data.get("message", "")
    response_text = chat_with_claude(message)
    return jsonify({"status": "success", "response": response_text}), 200


@app.route("/service/call", methods=["POST"])
def call_service_route():
    """Call a Home Assistant service."""
    data = request.get_json()
    service = data.get("service", "")
    service_data = data.get("data", {})
    if not service or "." not in service:
        return jsonify({"error": "Invalid service format. Use 'domain.service'"}), 400
    domain, service_name = service.split(".", 1)
    result = call_ha_api("POST", f"services/{domain}/{service_name}", service_data)
    return jsonify(result), 200


@app.route("/execute/automation", methods=["POST"])
def execute_automation():
    """Execute an automation."""
    data = request.get_json()
    entity_id = data.get("entity_id", data.get("automation_id", ""))
    if not entity_id.startswith("automation."):
        entity_id = f"automation.{entity_id}"
    result = call_ha_api("POST", "services/automation/trigger", {"entity_id": entity_id})
    return jsonify(result), 200


@app.route("/execute/script", methods=["POST"])
def execute_script():
    """Execute a script."""
    data = request.get_json()
    script_id = data.get("script_id", "")
    variables = data.get("variables", {})
    result = call_ha_api("POST", f"services/script/{script_id}", variables)
    return jsonify(result), 200


@app.route("/conversation/clear", methods=["POST"])
def clear_conversation():
    """Clear conversation history."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")
    conversations.pop(session_id, None)
    return jsonify({"status": "cleared"}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(f"Starting Claude AI Backend v{VERSION} on port {API_PORT}")
    logger.info(f"Claude API: {'configured' if CLAUDE_API_KEY else 'NOT configured'}")
    logger.info(f"HA Token: {'available' if HA_TOKEN else 'NOT available'}")
    app.run(host="0.0.0.0", port=API_PORT, debug=DEBUG_MODE)
