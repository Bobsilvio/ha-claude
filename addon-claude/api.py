"""Claude AI Assistant for Home Assistant - Flask Backend."""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests as http_requests
import anthropic

# ══════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
HA_BASE_URL = "http://supervisor/core"
OPTIONS_PATH = "/data/options.json"

# Load add-on options
def load_options():
    try:
        with open(OPTIONS_PATH) as f:
            return json.load(f)
    except Exception:
        return {}

options = load_options()
ANTHROPIC_API_KEY = options.get("anthropic_api_key", "")
CLAUDE_MODEL = options.get("claude_model", "claude-sonnet-4-20250514")
LANGUAGE = options.get("language", "it")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("claude-ai")

# HA API headers (using Supervisor token)
HA_HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
    "Content-Type": "application/json",
}

# Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")

# Conversation history (in-memory per session)
conversations = {}

# ══════════════════════════════════════════
# Home Assistant API Functions
# ══════════════════════════════════════════

def ha_api(method, endpoint, data=None):
    """Call Home Assistant API via Supervisor."""
    url = f"{HA_BASE_URL}/api/{endpoint}"
    try:
        if method == "GET":
            r = http_requests.get(url, headers=HA_HEADERS, timeout=30)
        elif method == "POST":
            r = http_requests.post(url, headers=HA_HEADERS, json=data, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        if r.status_code in (200, 201):
            return r.json() if r.text else {"status": "ok"}
        else:
            return {"error": f"HA API error {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        logger.error(f"HA API error: {e}")
        return {"error": str(e)}


def get_all_entities():
    """Get all entity states from HA."""
    result = ha_api("GET", "states")
    if isinstance(result, list):
        return result
    return []


def get_entity_state(entity_id):
    """Get state of a specific entity."""
    result = ha_api("GET", f"states/{entity_id}")
    return result


def call_ha_service(domain, service, data=None):
    """Call a Home Assistant service."""
    result = ha_api("POST", f"services/{domain}/{service}", data or {})
    return result


def create_automation(automation_config):
    """Create or update an automation in HA."""
    auto_id = automation_config.get("id", f"claude_auto_{int(datetime.now().timestamp())}")
    automation_config["id"] = auto_id
    
    url = f"{HA_BASE_URL}/api/config/automation/config/{auto_id}"
    try:
        r = http_requests.post(url, headers=HA_HEADERS, json=automation_config, timeout=30)
        if r.status_code in (200, 201):
            return {"status": "ok", "id": auto_id, "message": f"Automazione '{automation_config.get('alias', auto_id)}' creata con successo!"}
        else:
            return {"error": f"Errore creazione automazione: {r.status_code} - {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def get_entity_history(entity_id, hours=24):
    """Get entity history."""
    from datetime import timedelta
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    result = ha_api("GET", f"history/period/{start.isoformat()}?filter_entity_id={entity_id}&end_time={end.isoformat()}")
    if isinstance(result, list) and len(result) > 0:
        return result[0][:20]  # Limit to 20 entries
    return []


# ══════════════════════════════════════════
# Claude AI Tools (Function Calling)
# ══════════════════════════════════════════

TOOLS = [
    {
        "name": "get_entities",
        "description": "Ottieni la lista di tutte le entità di Home Assistant con i loro stati attuali. Usa questa funzione per scoprire quali dispositivi, sensori, luci, switch, etc. sono disponibili.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain_filter": {
                    "type": "string",
                    "description": "Filtra per dominio (es: 'light', 'switch', 'sensor', 'binary_sensor', 'climate', 'automation'). Lascia vuoto per tutti."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_entity_state",
        "description": "Ottieni lo stato dettagliato di una specifica entità di Home Assistant, inclusi attributi come luminosità, temperatura, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "L'ID dell'entità (es: 'light.salotto', 'sensor.temperatura_cucina', 'switch.presa_1')"
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "call_service",
        "description": "Chiama un servizio di Home Assistant per controllare un dispositivo. Esempi: accendere/spegnere luci, impostare temperatura, attivare scene, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Il dominio del servizio (es: 'light', 'switch', 'climate', 'scene', 'script', 'automation', 'media_player')"
                },
                "service": {
                    "type": "string",
                    "description": "Il nome del servizio (es: 'turn_on', 'turn_off', 'toggle', 'set_temperature', 'activate')"
                },
                "service_data": {
                    "type": "object",
                    "description": "Dati aggiuntivi per il servizio. Deve includere 'entity_id' se necessario. Esempio: {\"entity_id\": \"light.salotto\", \"brightness\": 128}"
                }
            },
            "required": ["domain", "service"]
        }
    },
    {
        "name": "create_automation",
        "description": "Crea una nuova automazione in Home Assistant. L'automazione viene salvata permanentemente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "alias": {
                    "type": "string",
                    "description": "Nome descrittivo dell'automazione"
                },
                "description": {
                    "type": "string",
                    "description": "Descrizione di cosa fa l'automazione"
                },
                "trigger": {
                    "type": "array",
                    "description": "Lista di trigger (es: [{\"platform\": \"state\", \"entity_id\": \"binary_sensor.motion\", \"to\": \"on\"}])",
                    "items": {"type": "object"}
                },
                "condition": {
                    "type": "array",
                    "description": "Lista di condizioni opzionali (es: [{\"condition\": \"time\", \"after\": \"18:00:00\"}])",
                    "items": {"type": "object"}
                },
                "action": {
                    "type": "array",
                    "description": "Lista di azioni (es: [{\"service\": \"light.turn_on\", \"target\": {\"entity_id\": \"light.salotto\"}}])",
                    "items": {"type": "object"}
                },
                "mode": {
                    "type": "string",
                    "description": "Modalità: 'single', 'restart', 'queued', 'parallel'. Default: 'single'"
                }
            },
            "required": ["alias", "trigger", "action"]
        }
    },
    {
        "name": "get_history",
        "description": "Ottieni la cronologia di un'entità nelle ultime ore. Utile per analizzare trend di temperatura, consumi, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "L'ID dell'entità"
                },
                "hours": {
                    "type": "integer",
                    "description": "Numero di ore di cronologia (default: 24, max: 168)"
                }
            },
            "required": ["entity_id"]
        }
    }
]


def execute_tool(tool_name, tool_input):
    """Execute a Claude tool call."""
    logger.info(f"Executing tool: {tool_name} with input: {json.dumps(tool_input, ensure_ascii=False)[:200]}")
    
    if tool_name == "get_entities":
        entities = get_all_entities()
        domain_filter = tool_input.get("domain_filter", "")
        if domain_filter:
            entities = [e for e in entities if e["entity_id"].startswith(f"{domain_filter}.")]
        
        summary = []
        for e in entities:
            attrs = e.get("attributes", {})
            name = attrs.get("friendly_name", e["entity_id"])
            summary.append(f"- {e['entity_id']}: {e['state']} ({name})")
        
        return f"Trovate {len(summary)} entità:\n" + "\n".join(summary[:100])
    
    elif tool_name == "get_entity_state":
        result = get_entity_state(tool_input["entity_id"])
        if "error" in result:
            return f"Errore: {result['error']}"
        attrs = result.get("attributes", {})
        name = attrs.get("friendly_name", result.get("entity_id", ""))
        return json.dumps({
            "entity_id": result.get("entity_id"),
            "state": result.get("state"),
            "friendly_name": name,
            "attributes": attrs,
            "last_changed": result.get("last_changed"),
        }, indent=2, ensure_ascii=False)
    
    elif tool_name == "call_service":
        result = call_ha_service(
            tool_input["domain"],
            tool_input["service"],
            tool_input.get("service_data", {})
        )
        if isinstance(result, list):
            return f"✅ Servizio {tool_input['domain']}.{tool_input['service']} eseguito con successo!"
        elif isinstance(result, dict) and "error" in result:
            return f"❌ Errore: {result['error']}"
        return f"✅ Servizio eseguito!"
    
    elif tool_name == "create_automation":
        config = {
            "alias": tool_input["alias"],
            "description": tool_input.get("description", ""),
            "trigger": tool_input["trigger"],
            "condition": tool_input.get("condition", []),
            "action": tool_input["action"],
            "mode": tool_input.get("mode", "single"),
        }
        result = create_automation(config)
        if "error" in result:
            return f"❌ Errore: {result['error']}"
        return f"✅ {result['message']}"
    
    elif tool_name == "get_history":
        history = get_entity_history(
            tool_input["entity_id"],
            tool_input.get("hours", 24)
        )
        if not history:
            return "Nessun dato storico trovato."
        
        entries = []
        for h in history:
            entries.append(f"- {h.get('last_changed', 'N/A')}: {h.get('state', 'N/A')}")
        return f"Cronologia ({len(entries)} punti):\n" + "\n".join(entries)
    
    return f"Tool sconosciuto: {tool_name}"


# ══════════════════════════════════════════
# System Prompt
# ══════════════════════════════════════════

SYSTEM_PROMPTS = {
    "it": """Sei Claude, un assistente AI integrato in Home Assistant. Il tuo compito è aiutare l'utente a gestire la sua casa smart.

CAPACITÀ:
- Leggere lo stato di tutti i sensori e dispositivi
- Accendere/spegnere luci, switch, prese
- Controllare climatizzazione e media player
- Creare automazioni permanenti che si salvano in Home Assistant
- Analizzare cronologia e trend dei sensori
- Suggerire ottimizzazioni energetiche

REGOLE:
- Rispondi SEMPRE in italiano
- Prima di eseguire azioni, conferma con l'utente cosa stai per fare
- Quando crei automazioni, spiega chiaramente cosa farà l'automazione
- Se non sei sicuro di un entity_id, usa get_entities per cercarlo
- Sii conciso ma chiaro nelle risposte
- Usa emoji per rendere le risposte più leggibili

Quando l'utente chiede di creare un'automazione:
1. Chiedi dettagli se mancano
2. Cerca le entità corrette con get_entities
3. Mostra un riepilogo all'utente
4. Crea l'automazione con create_automation""",

    "en": """You are Claude, an AI assistant integrated into Home Assistant. Your job is to help users manage their smart home.

CAPABILITIES:
- Read the state of all sensors and devices
- Turn on/off lights, switches, outlets
- Control HVAC and media players
- Create permanent automations saved in Home Assistant
- Analyze sensor history and trends
- Suggest energy optimizations

RULES:
- Always respond in English
- Before executing actions, confirm with the user what you're about to do
- When creating automations, clearly explain what the automation will do
- If unsure about an entity_id, use get_entities to search for it
- Be concise but clear in responses
- Use emoji to make responses more readable""",

    "es": """Eres Claude, un asistente de IA integrado en Home Assistant. Tu trabajo es ayudar al usuario a gestionar su hogar inteligente. Responde siempre en español.""",
    "fr": """Tu es Claude, un assistant IA intégré à Home Assistant. Ton rôle est d'aider l'utilisateur à gérer sa maison connectée. Réponds toujours en français.""",
    "de": """Du bist Claude, ein KI-Assistent, der in Home Assistant integriert ist. Deine Aufgabe ist es, dem Benutzer bei der Verwaltung seines Smart Homes zu helfen. Antworte immer auf Deutsch.""",
    "nl": """Je bent Claude, een AI-assistent geïntegreerd in Home Assistant. Je taak is de gebruiker te helpen bij het beheren van hun smart home. Antwoord altijd in het Nederlands.""",
}


# ══════════════════════════════════════════
# Flask Routes
# ══════════════════════════════════════════

@app.route("/")
def index():
    """Serve the chat UI."""
    ingress_path = os.environ.get("INGRESS_PATH", "")
    return render_template("index.html", ingress_path=ingress_path)


@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files."""
    return send_from_directory("static", filename)


@app.route("/api/health")
def health():
    """Health check."""
    return jsonify({"status": "ok", "model": CLAUDE_MODEL, "language": LANGUAGE})


@app.route("/api/entities")
def api_entities():
    """Get all entities for the UI."""
    entities = get_all_entities()
    return jsonify({"count": len(entities), "entities": entities})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages with Claude."""
    data = request.json
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")
    
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "API key di Anthropic non configurata. Vai nelle opzioni dell'add-on."}), 400
    
    if not user_message:
        return jsonify({"error": "Messaggio vuoto"}), 400
    
    # Get or create conversation history
    if session_id not in conversations:
        conversations[session_id] = []
    
    history = conversations[session_id]
    history.append({"role": "user", "content": user_message})
    
    # Keep last 20 messages
    if len(history) > 20:
        history = history[-20:]
        conversations[session_id] = history
    
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Call Claude with tools
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPTS.get(LANGUAGE, SYSTEM_PROMPTS["en"]),
            tools=TOOLS,
            messages=history,
        )
        
        # Process response - handle tool use loop
        final_text = ""
        tool_results = []
        
        while response.stop_reason == "tool_use":
            # Extract tool calls and text
            assistant_content = response.content
            history.append({"role": "assistant", "content": assistant_content})
            
            # Execute each tool call
            tool_use_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    logger.info(f"Tool call: {block.name}")
                    result = execute_tool(block.name, block.input)
                    tool_use_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
                    tool_results.append({
                        "tool": block.name,
                        "input": block.input,
                        "result": result[:500],
                    })
                elif block.type == "text":
                    final_text += block.text
            
            # Send tool results back to Claude
            history.append({"role": "user", "content": tool_use_results})
            
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPTS.get(LANGUAGE, SYSTEM_PROMPTS["en"]),
                tools=TOOLS,
                messages=history,
            )
        
        # Extract final text response
        for block in response.content:
            if hasattr(block, "text"):
                final_text += block.text
        
        # Save assistant response to history
        history.append({"role": "assistant", "content": final_text})
        conversations[session_id] = history
        
        return jsonify({
            "response": final_text,
            "tools_used": tool_results,
            "model": CLAUDE_MODEL,
        })
        
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return jsonify({"error": f"Errore API Claude: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    """Clear conversation history."""
    session_id = request.json.get("session_id", "default")
    conversations.pop(session_id, None)
    return jsonify({"status": "ok"})


# ══════════════════════════════════════════
# Main
# ══════════════════════════════════════════

if __name__ == "__main__":
    logger.info(f"Starting Claude AI Assistant")
    logger.info(f"Model: {CLAUDE_MODEL}")
    logger.info(f"Language: {LANGUAGE}")
    logger.info(f"Supervisor token: {'✓' if SUPERVISOR_TOKEN else '✗'}")
    
    port = int(os.environ.get("INGRESS_PORT", 8099))
    app.run(host="0.0.0.0", port=port, debug=False)
