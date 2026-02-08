"""AI Assistant API with multi-provider support for Home Assistant."""

import os
import json
import logging
import queue
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# Version
VERSION = "2.6.5"

# Configuration
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "")
AI_MODEL = os.getenv("AI_MODEL", "")
# Filter out bashio 'null' values
if AI_MODEL in ("null", "None", ""):
    AI_MODEL = ""
API_PORT = int(os.getenv("API_PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO)
logger = logging.getLogger(__name__)

def get_ha_token() -> str:
    """Get Home Assistant Supervisor token with multiple fallbacks."""
    # 1. Environment variable (set by s6 run script)
    token = os.getenv("SUPERVISOR_TOKEN", "")
    if token:
        return token
    # 2. s6-overlay container environment file
    try:
        token_file = "/run/s6/container_environment/SUPERVISOR_TOKEN"
        if os.path.isfile(token_file):
            with open(token_file, "r") as f:
                token = f.read().strip()
                if token:
                    return token
    except Exception:
        pass
    # 3. bashio config approach (HA addon env)
    try:
        token_file2 = "/var/run/s6/container_environment/SUPERVISOR_TOKEN"
        if os.path.isfile(token_file2):
            with open(token_file2, "r") as f:
                token = f.read().strip()
                if token:
                    return token
    except Exception:
        pass
    return ""


def get_ha_headers() -> dict:
    """Build HA API headers with current token."""
    token = get_ha_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

# ---- Provider defaults ----

PROVIDER_DEFAULTS = {
    "anthropic": {"model": "claude-sonnet-4-20250514", "name": "Claude (Anthropic)"},
    "openai": {"model": "gpt-4o", "name": "ChatGPT (OpenAI)"},
    "google": {"model": "gemini-2.0-flash", "name": "Gemini (Google)"},
    "github": {"model": "gpt-4o", "name": "GitHub Models"},
}

PROVIDER_MODELS = {
    "anthropic": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-20250514"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o3-mini"],
    "google": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
    "github": [
        # OpenAI
        "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
        "o1", "o1-mini", "o1-preview", "o3", "o3-mini", "o4-mini",
        "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-chat",
        # Meta Llama
        "Meta-Llama-3.1-405B-Instruct", "Meta-Llama-3.1-8B-Instruct",
        "Llama-3.3-70B-Instruct", "Llama-4-Scout-17B-16E-Instruct",
        "Llama-4-Maverick-17B-128E-Instruct-FP8",
        # Mistral
        "mistral-small-2503", "mistral-medium-2505", "Ministral-3B", "Codestral-2501",
        # Cohere
        "Cohere-command-r-plus-08-2024", "Cohere-command-r-08-2024", "cohere-command-a",
        # DeepSeek
        "DeepSeek-R1", "DeepSeek-R1-0528", "DeepSeek-V3-0324",
        # Microsoft
        "MAI-DS-R1", "Phi-4", "Phi-4-mini-instruct", "Phi-4-reasoning", "Phi-4-mini-reasoning",
        # AI21
        "AI21-Jamba-1.5-Large",
        # xAI
        "grok-3", "grok-3-mini",
    ],
}


def get_active_model() -> str:
    """Get the active model name."""
    # ai_model (manual override) takes priority
    if AI_MODEL:
        return AI_MODEL
    # For github provider, use the dropdown selection
    if AI_PROVIDER == "github" and GITHUB_MODEL:
        return GITHUB_MODEL
    return PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("model", "unknown")


def get_api_key() -> str:
    """Get the API key for the active provider."""
    if AI_PROVIDER == "anthropic":
        return ANTHROPIC_API_KEY
    elif AI_PROVIDER == "openai":
        return OPENAI_API_KEY
    elif AI_PROVIDER == "google":
        return GOOGLE_API_KEY
    elif AI_PROVIDER == "github":
        return GITHUB_TOKEN
    return ""


# ---- Initialize AI client ----

ai_client = None
api_key = get_api_key()

if AI_PROVIDER == "anthropic" and api_key:
    import anthropic
    ai_client = anthropic.Anthropic(api_key=api_key)
    logger.info(f"Anthropic client initialized (model: {get_active_model()})")
elif AI_PROVIDER == "openai" and api_key:
    from openai import OpenAI
    ai_client = OpenAI(api_key=api_key)
    logger.info(f"OpenAI client initialized (model: {get_active_model()})")
elif AI_PROVIDER == "google" and api_key:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    ai_client = genai
    logger.info(f"Google Gemini client initialized (model: {get_active_model()})")
elif AI_PROVIDER == "github" and api_key:
    from openai import OpenAI
    ai_client = OpenAI(
        api_key=api_key,
        base_url="https://models.inference.ai.azure.com"
    )
    logger.info(f"GitHub Copilot client initialized (model: {get_active_model()})")
else:
    logger.warning(f"AI provider '{AI_PROVIDER}' not configured - set the API key in addon settings")

# Conversation history
conversations: Dict[str, List[Dict]] = {}

# Conversation persistence
CONVERSATIONS_FILE = "/data/conversations.json"


def load_conversations():
    """Load conversations from persistent storage."""
    global conversations
    try:
        if os.path.isfile(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, "r") as f:
                conversations = json.load(f)
            logger.info(f"Loaded {len(conversations)} conversation(s) from disk")
    except Exception as e:
        logger.warning(f"Could not load conversations: {e}")


def save_conversations():
    """Save conversations to persistent storage."""
    try:
        os.makedirs(os.path.dirname(CONVERSATIONS_FILE), exist_ok=True)
        # Keep only last 10 sessions, 50 messages each
        trimmed = {}
        for sid, msgs in list(conversations.items())[-10:]:
            trimmed[sid] = msgs[-50:]
        with open(CONVERSATIONS_FILE, "w") as f:
            json.dump(trimmed, f, ensure_ascii=False, default=str)
    except Exception as e:
        logger.warning(f"Could not save conversations: {e}")


# Load saved conversations on startup
load_conversations()

# ---- Home Assistant API helpers ----


def call_ha_api(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
    """Call Home Assistant API."""
    url = f"{HA_URL}/api/{endpoint}"
    headers = get_ha_headers()
    token = get_ha_token()
    logger.debug(f"HA API call: {method} {url} (token present: {bool(token)}, len={len(token)})")
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}

        if response.status_code in [200, 201]:
            return response.json() if response.text else {"status": "success"}
        elif response.status_code == 401:
            logger.error(f"HA API 401 Unauthorized - token might be missing or invalid. HA_URL={HA_URL}, token_len={len(token)}")
            return {"error": "401 Unauthorized - check SUPERVISOR_TOKEN"}
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


# ---- Tool definitions (shared across providers) ----

HA_TOOLS_DESCRIPTION = [
    {
        "name": "get_entities",
        "description": "Get the current state of all Home Assistant entities, or filter by domain (e.g. 'light', 'switch', 'sensor', 'automation', 'climate').",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter (e.g. 'light', 'switch', 'sensor')."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_entity_state",
        "description": "Get the current state and attributes of a specific entity.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID (e.g. 'light.living_room')."
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "call_service",
        "description": "Call a Home Assistant service to control devices: turn on/off lights, switches, set climate temperature, lock/unlock, open/close covers, send notifications, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain (e.g. 'light', 'switch', 'climate', 'cover')."
                },
                "service": {
                    "type": "string",
                    "description": "Service name (e.g. 'turn_on', 'turn_off', 'toggle')."
                },
                "data": {
                    "type": "object",
                    "description": "Service data including target entity_id and parameters."
                }
            },
            "required": ["domain", "service", "data"]
        }
    },
    {
        "name": "create_automation",
        "description": "Create a new Home Assistant automation with triggers, conditions, and actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "alias": {"type": "string", "description": "Name for the automation."},
                "description": {"type": "string", "description": "Description of the automation."},
                "trigger": {"type": "array", "description": "List of triggers.", "items": {"type": "object"}},
                "condition": {"type": "array", "description": "Optional conditions.", "items": {"type": "object"}},
                "action": {"type": "array", "description": "List of actions.", "items": {"type": "object"}},
                "mode": {"type": "string", "enum": ["single", "restart", "queued", "parallel"]}
            },
            "required": ["alias", "trigger", "action"]
        }
    },
    {
        "name": "get_automations",
        "description": "Get all existing automations.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "trigger_automation",
        "description": "Manually trigger an existing automation.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Automation entity_id."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_available_services",
        "description": "Get all available Home Assistant service domains and services.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "search_entities",
        "description": "Search entities by keyword in entity_id or friendly_name. Use this to find specific devices, sensors, or integrations.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword (e.g. 'calcio', 'temperature', 'motion', 'light')."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_events",
        "description": "Get all available Home Assistant event types. Use this to discover events fired by integrations and addons.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_history",
        "description": "Get the state history of an entity over a time period. Useful for checking past values, trends, and when things changed.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "The entity ID to get history for."},
                "hours": {"type": "number", "description": "Hours of history to retrieve (default 24, max 168)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_scenes",
        "description": "Get all available scenes in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "activate_scene",
        "description": "Activate a Home Assistant scene.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Scene entity_id (e.g. 'scene.movie_night')."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_scripts",
        "description": "Get all available scripts in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_script",
        "description": "Run a Home Assistant script with optional variables.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Script entity_id (e.g. 'script.goodnight')."},
                "variables": {"type": "object", "description": "Optional variables to pass to the script."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_areas",
        "description": "Get all areas/rooms configured in Home Assistant and their entities. Useful for room-based control like 'turn off everything in the bedroom'.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "send_notification",
        "description": "Send a notification to Home Assistant (persistent notification visible in HA UI, or to a mobile device).",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The notification message."},
                "title": {"type": "string", "description": "Optional notification title."},
                "target": {"type": "string", "description": "Notify service target (e.g. 'mobile_app_phone'). If empty, creates a persistent notification in HA."}
            },
            "required": ["message"]
        }
    },
    {
        "name": "get_dashboards",
        "description": "Get all Lovelace dashboards in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_dashboard",
        "description": "Create a NEW Lovelace dashboard (does NOT modify existing ones). The AI builds the views and cards config. Common card types: entities, gauge, history-graph, weather-forecast, light, thermostat, button, markdown, grid, horizontal-stack, vertical-stack.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Dashboard title (e.g. 'Luci e Temperature')."},
                "url_path": {"type": "string", "description": "URL slug (lowercase, no spaces, e.g. 'luci-temp'). Must be unique."},
                "icon": {"type": "string", "description": "MDI icon (e.g. 'mdi:thermometer', 'mdi:lightbulb'). Optional."},
                "views": {
                    "type": "array",
                    "description": "List of views (tabs) with cards. Each view has: title, path, icon, cards[].",
                    "items": {"type": "object"}
                }
            },
            "required": ["title", "url_path", "views"]
        }
    },
    {
        "name": "create_script",
        "description": "Create a new Home Assistant script with a sequence of actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "Unique script ID (lowercase, underscores, e.g. 'goodnight_routine')."},
                "alias": {"type": "string", "description": "Friendly name for the script."},
                "description": {"type": "string", "description": "Description of what the script does."},
                "sequence": {"type": "array", "description": "List of actions to execute in order.", "items": {"type": "object"}},
                "mode": {"type": "string", "enum": ["single", "restart", "queued", "parallel"], "description": "Execution mode (default: single)."}
            },
            "required": ["script_id", "alias", "sequence"]
        }
    }
]


def get_anthropic_tools():
    """Convert tools to Anthropic format."""
    return [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in HA_TOOLS_DESCRIPTION
    ]


def get_openai_tools():
    """Convert tools to OpenAI function-calling format."""
    return [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
        for t in HA_TOOLS_DESCRIPTION
    ]


def get_gemini_tools():
    """Convert tools to Google Gemini format."""
    from google.generativeai.types import FunctionDeclaration, Tool
    declarations = []
    for t in HA_TOOLS_DESCRIPTION:
        declarations.append(FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=t["parameters"]
        ))
    return Tool(function_declarations=declarations)


# ---- Tool execution ----


def execute_tool(tool_name: str, tool_input: Dict) -> str:
    """Execute a tool call and return the result as string."""
    try:
        if tool_name == "get_entities":
            domain = tool_input.get("domain", "")
            states = get_all_states()
            if domain:
                states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
            # Limit results for providers with small context windows
            max_entities = 30 if AI_PROVIDER == "github" else 100
            result = []
            for s in states[:max_entities]:
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
            config = {
                "alias": tool_input.get("alias", "New Automation"),
                "description": tool_input.get("description", ""),
                "trigger": tool_input.get("trigger", []),
                "condition": tool_input.get("condition", []),
                "action": tool_input.get("action", []),
                "mode": tool_input.get("mode", "single"),
            }
            result = call_ha_api("POST", "config/automation/config/new", config)
            if isinstance(result, dict) and "error" not in result:
                return json.dumps({"status": "success", "message": f"Automation '{config['alias']}' created!", "result": result}, ensure_ascii=False)
            return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_automations":
            states = get_all_states()
            autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
            result = [{"entity_id": a.get("entity_id"), "state": a.get("state"),
                       "friendly_name": a.get("attributes", {}).get("friendly_name", ""),
                       "last_triggered": a.get("attributes", {}).get("last_triggered", "")} for a in autos]
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "trigger_automation":
            entity_id = tool_input.get("entity_id", "")
            result = call_ha_api("POST", "services/automation/trigger", {"entity_id": entity_id})
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_available_services":
            svc_raw = call_ha_api("GET", "services")
            if isinstance(svc_raw, list):
                compact = {s.get("domain", ""): list(s.get("services", {}).keys()) for s in svc_raw}
                return json.dumps(compact, ensure_ascii=False)
            return json.dumps(svc_raw, ensure_ascii=False, default=str)

        elif tool_name == "search_entities":
            query = tool_input.get("query", "").lower()
            states = get_all_states()
            matches = []
            for s in states:
                eid = s.get("entity_id", "").lower()
                fname = s.get("attributes", {}).get("friendly_name", "").lower()
                if query in eid or query in fname:
                    matches.append({
                        "entity_id": s.get("entity_id"),
                        "state": s.get("state"),
                        "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                        "attributes": s.get("attributes", {})
                    })
            max_results = 20 if AI_PROVIDER == "github" else 50
            return json.dumps(matches[:max_results], ensure_ascii=False, default=str)

        elif tool_name == "get_events":
            events = call_ha_api("GET", "events")
            if isinstance(events, list):
                result = [{"event": e.get("event", ""), "listener_count": e.get("listener_count", 0)} for e in events]
                return json.dumps(result, ensure_ascii=False, default=str)
            return json.dumps(events, ensure_ascii=False, default=str)

        elif tool_name == "get_history":
            entity_id = tool_input.get("entity_id", "")
            hours = min(int(tool_input.get("hours", 24)), 168)
            start = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
            endpoint = f"history/period/{start}?filter_entity_id={entity_id}&significant_changes_only=1"
            result = call_ha_api("GET", endpoint)
            if isinstance(result, list) and result:
                entries = result[0] if isinstance(result[0], list) else result
                max_e = 20 if AI_PROVIDER == "github" else 50
                summary = [{"state": e.get("state"), "last_changed": e.get("last_changed")} for e in entries[-max_e:]]
                return json.dumps({"entity_id": entity_id, "hours": hours, "total_changes": len(entries), "history": summary}, ensure_ascii=False, default=str)
            return json.dumps({"entity_id": entity_id, "hours": hours, "history": []}, ensure_ascii=False, default=str)

        elif tool_name == "get_scenes":
            states = get_all_states()
            scenes = [{"entity_id": s.get("entity_id"), "state": s.get("state"),
                       "friendly_name": s.get("attributes", {}).get("friendly_name", "")}
                      for s in states if s.get("entity_id", "").startswith("scene.")]
            return json.dumps(scenes, ensure_ascii=False, default=str)

        elif tool_name == "activate_scene":
            entity_id = tool_input.get("entity_id", "")
            result = call_ha_api("POST", "services/scene/turn_on", {"entity_id": entity_id})
            return json.dumps({"status": "success", "scene": entity_id, "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_scripts":
            states = get_all_states()
            scripts = [{"entity_id": s.get("entity_id"), "state": s.get("state"),
                        "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                        "last_triggered": s.get("attributes", {}).get("last_triggered", "")}
                       for s in states if s.get("entity_id", "").startswith("script.")]
            return json.dumps(scripts, ensure_ascii=False, default=str)

        elif tool_name == "run_script":
            entity_id = tool_input.get("entity_id", "")
            variables = tool_input.get("variables", {})
            script_id = entity_id.replace("script.", "") if entity_id.startswith("script.") else entity_id
            result = call_ha_api("POST", f"services/script/{script_id}", variables)
            return json.dumps({"status": "success", "script": entity_id, "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_areas":
            try:
                template = '[{% for area in areas() %}{"id":{{ area | tojson }}, "name":{{ area_name(area) | tojson }}, "entities":{{ area_entities(area) | list | tojson }}}{% if not loop.last %},{% endif %}{% endfor %}]'
                url = f"{HA_URL}/api/template"
                resp = requests.post(url, headers=get_ha_headers(), json={"template": template}, timeout=30)
                if resp.status_code == 200:
                    areas_data = json.loads(resp.text)
                    if AI_PROVIDER == "github":
                        for area in areas_data:
                            area["entities"] = area["entities"][:10]
                    return json.dumps(areas_data, ensure_ascii=False, default=str)
                return json.dumps({"error": f"Template API error: {resp.status_code}"}, default=str)
            except Exception as e:
                return json.dumps({"error": f"Could not get areas: {str(e)}"}, default=str)

        elif tool_name == "send_notification":
            message = tool_input.get("message", "")
            title = tool_input.get("title", "AI Assistant")
            target = tool_input.get("target", "")
            if target:
                result = call_ha_api("POST", f"services/notify/{target}", {"message": message, "title": title})
            else:
                result = call_ha_api("POST", "services/persistent_notification/create", {"message": message, "title": title})
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_dashboards":
            url = f"{HA_URL}/api/lovelace/dashboards"
            resp = requests.get(url, headers=get_ha_headers(), timeout=30)
            if resp.status_code == 200:
                dashboards = resp.json()
                result = [{"id": d.get("id"), "title": d.get("title"), "url_path": d.get("url_path"),
                           "icon": d.get("icon", ""), "mode": d.get("mode", "")} for d in dashboards]
                return json.dumps(result, ensure_ascii=False, default=str)
            return json.dumps({"error": f"Could not get dashboards: {resp.status_code}"}, default=str)

        elif tool_name == "create_dashboard":
            title = tool_input.get("title", "AI Dashboard")
            url_path = tool_input.get("url_path", "ai-dashboard")
            icon = tool_input.get("icon", "mdi:robot")
            views = tool_input.get("views", [])

            # Step 1: Create the dashboard entry
            create_url = f"{HA_URL}/api/lovelace/dashboards"
            create_data = {"title": title, "url_path": url_path, "icon": icon, "mode": "storage"}
            resp1 = requests.post(create_url, headers=get_ha_headers(), json=create_data, timeout=30)
            if resp1.status_code not in [200, 201]:
                return json.dumps({"error": f"Failed to create dashboard: {resp1.status_code} - {resp1.text}"}, default=str)

            # Step 2: Set the dashboard config with views and cards
            config = {"views": views}
            config_url = f"{HA_URL}/api/lovelace/config/{url_path}"
            resp2 = requests.post(config_url, headers=get_ha_headers(), json=config, timeout=30)
            if resp2.status_code not in [200, 201]:
                return json.dumps({"status": "partial", "message": f"Dashboard created but config failed: {resp2.status_code} - {resp2.text}"}, default=str)

            return json.dumps({"status": "success", "message": f"Dashboard '{title}' created at /{url_path}",
                               "url_path": url_path, "views_count": len(views)}, ensure_ascii=False, default=str)

        elif tool_name == "create_script":
            script_id = tool_input.get("script_id", "")
            config = {
                "alias": tool_input.get("alias", "New Script"),
                "description": tool_input.get("description", ""),
                "sequence": tool_input.get("sequence", []),
                "mode": tool_input.get("mode", "single"),
            }
            result = call_ha_api("POST", f"config/script/config/{script_id}", config)
            if isinstance(result, dict) and "error" not in result:
                return json.dumps({"status": "success", "message": f"Script '{config['alias']}' created (script.{script_id})",
                                   "entity_id": f"script.{script_id}", "result": result}, ensure_ascii=False, default=str)
            return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        logger.error(f"Tool error ({tool_name}): {e}")
        return json.dumps({"error": str(e)})


# ---- System prompt ----

SYSTEM_PROMPT = """You are an AI assistant integrated into Home Assistant. You help users manage their smart home.

You can:
1. **Query entities** - See device states (lights, sensors, switches, climate, covers, etc.)
2. **Control devices** - Turn on/off lights, switches, set temperatures, etc.
3. **Search entities** - Find specific devices or integrations by keyword
4. **Entity history** - Check past values and trends ("what was the temperature yesterday?")
5. **Scenes & scripts** - List and activate scenes, run scripts
6. **Areas/rooms** - See entities organized by room for room-based control
7. **Create automations** - Build new automations with triggers, conditions, and actions
8. **List & trigger automations** - See and run existing automations
9. **Notifications** - Send persistent notifications or push to mobile devices
10. **Discover services & events** - See all available HA services and event types
11. **Create dashboards** - Create NEW Lovelace dashboards with cards (never modifies existing ones)

When creating dashboards, use proper Lovelace card types:
- entities card: {"type": "entities", "title": "Lights", "entities": ["light.living_room", "light.bedroom"]}
- gauge card: {"type": "gauge", "entity": "sensor.temperature", "name": "Temperature"}
- history-graph: {"type": "history-graph", "entities": [{"entity": "sensor.temperature"}], "hours_to_show": 24}
- thermostat: {"type": "thermostat", "entity": "climate.living_room"}
- button: {"type": "button", "entity": "switch.outlet", "name": "Toggle"}
- markdown: {"type": "markdown", "content": "# Title"}
- grid/horizontal-stack/vertical-stack for layout

Always first use get_entities or search_entities to find real entity IDs before creating dashboards.

When creating automations, use proper Home Assistant formats:
- State trigger: {"platform": "state", "entity_id": "binary_sensor.motion", "to": "on"}
- Time trigger: {"platform": "time", "at": "07:00:00"}
- Sun trigger: {"platform": "sun", "event": "sunset", "offset": "-00:30:00"}
- Service action: {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 255}}

When a user asks about specific devices or addons, use search_entities to find them by keyword.
Use get_history to answer questions about past states and trends.
Use get_areas when the user refers to rooms.

Always respond in the same language the user uses.
Be concise but informative."""

# Compact prompt for providers with small context (GitHub Models free tier: 8k tokens)
SYSTEM_PROMPT_COMPACT = """You are a Home Assistant AI assistant. Control devices, query states, search entities, check history, create automations, create dashboards.
When users ask about specific devices, use search_entities. Use get_history for past data.
To create a dashboard, ALWAYS first search entities to find real entity IDs, then use create_dashboard with proper Lovelace cards.
Respond in the user's language. Be concise."""

# Compact tool definitions for low-token providers
HA_TOOLS_COMPACT = [
    {
        "name": "get_entities",
        "description": "Get HA entity states, optionally filtered by domain.",
        "parameters": {"type": "object", "properties": {"domain": {"type": "string"}}, "required": []}
    },
    {
        "name": "call_service",
        "description": "Call HA service (e.g. light.turn_on, switch.toggle, climate.set_temperature, scene.turn_on, script.turn_on).",
        "parameters": {"type": "object", "properties": {
            "domain": {"type": "string"}, "service": {"type": "string"},
            "data": {"type": "object"}
        }, "required": ["domain", "service", "data"]}
    },
    {
        "name": "search_entities",
        "description": "Search entities by keyword in entity_id or friendly_name.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    },
    {
        "name": "get_history",
        "description": "Get state history of an entity. Params: entity_id (required), hours (default 24).",
        "parameters": {"type": "object", "properties": {
            "entity_id": {"type": "string"}, "hours": {"type": "number"}
        }, "required": ["entity_id"]}
    },
    {
        "name": "create_automation",
        "description": "Create HA automation with alias, trigger, action.",
        "parameters": {"type": "object", "properties": {
            "alias": {"type": "string"}, "trigger": {"type": "array", "items": {"type": "object"}},
            "action": {"type": "array", "items": {"type": "object"}}
        }, "required": ["alias", "trigger", "action"]}
    },
    {
        "name": "create_dashboard",
        "description": "Create a NEW Lovelace dashboard. Params: title, url_path (slug), views (array of {title, cards[]}). Card types: entities, gauge, history-graph, thermostat, button.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "url_path": {"type": "string"},
            "icon": {"type": "string"},
            "views": {"type": "array", "items": {"type": "object"}}
        }, "required": ["title", "url_path", "views"]}
    }
]


def get_system_prompt() -> str:
    """Get system prompt appropriate for current provider."""
    if AI_PROVIDER == "github":
        return SYSTEM_PROMPT_COMPACT
    return SYSTEM_PROMPT


def get_openai_tools_for_provider():
    """Get OpenAI-format tools appropriate for current provider."""
    if AI_PROVIDER == "github":
        return [
            {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
            for t in HA_TOOLS_COMPACT
        ]
    return get_openai_tools()


def trim_messages(messages: List[Dict], max_messages: int = 20) -> List[Dict]:
    """Trim conversation history, preserving tool_call/tool response pairs."""
    limit = 6 if AI_PROVIDER == "github" else max_messages
    if len(messages) <= limit:
        return messages
    trimmed = messages[-limit:]
    # Remove orphaned tool messages at the start (their parent assistant+tool_calls was trimmed)
    while trimmed and trimmed[0].get("role") == "tool":
        trimmed = trimmed[1:]
    # Also remove an assistant message with tool_calls if its tool responses were trimmed
    if trimmed and trimmed[0].get("role") == "assistant" and trimmed[0].get("tool_calls"):
        # Check if next message is a matching tool response
        if len(trimmed) < 2 or trimmed[1].get("role") != "tool":
            trimmed = trimmed[1:]
    return trimmed


# ---- Provider-specific chat implementations ----


def chat_anthropic(messages: List[Dict]) -> tuple:
    """Chat with Anthropic Claude. Returns (response_text, updated_messages)."""
    import anthropic

    response = ai_client.messages.create(
        model=get_active_model(),
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=get_anthropic_tools(),
        messages=messages
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        assistant_content = response.content
        for block in response.content:
            if block.type == "tool_use":
                logger.info(f"Tool: {block.name}")
                result = execute_tool(block.name, block.input)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})

        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

        response = ai_client.messages.create(
            model=get_active_model(),
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=get_anthropic_tools(),
            messages=messages
        )

    final_text = "".join(block.text for block in response.content if hasattr(block, "text"))
    return final_text, messages


def chat_openai(messages: List[Dict]) -> tuple:
    """Chat with OpenAI. Returns (response_text, updated_messages)."""
    trimmed = trim_messages(messages)
    system_prompt = get_system_prompt()
    tools = get_openai_tools_for_provider()
    max_tok = 4000 if AI_PROVIDER == "github" else 4096

    oai_messages = [{"role": "system", "content": system_prompt}] + trimmed

    response = ai_client.chat.completions.create(
        model=get_active_model(),
        messages=oai_messages,
        tools=tools,
        max_tokens=max_tok
    )

    msg = response.choices[0].message

    while msg.tool_calls:
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            logger.info(f"Tool: {tc.function.name}")
            args = json.loads(tc.function.arguments)
            result = execute_tool(tc.function.name, args)
            # Truncate tool results for GitHub to stay within token limits
            if AI_PROVIDER == "github" and len(result) > 3000:
                result = result[:3000] + '... (truncated)'
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        trimmed = trim_messages(messages)
        oai_messages = [{"role": "system", "content": system_prompt}] + trimmed
        response = ai_client.chat.completions.create(
            model=get_active_model(),
            messages=oai_messages,
            tools=tools,
            max_tokens=max_tok
        )
        msg = response.choices[0].message

    return msg.content or "", messages


def chat_google(messages: List[Dict]) -> tuple:
    """Chat with Google Gemini. Returns (response_text, updated_messages)."""
    from google.generativeai.types import content_types

    model = ai_client.GenerativeModel(
        model_name=get_active_model(),
        system_instruction=SYSTEM_PROMPT,
        tools=[get_gemini_tools()]
    )

    # Convert messages to Gemini format
    gemini_history = []
    for m in messages[:-1]:  # All except last
        role = "model" if m["role"] == "assistant" else "user"
        if isinstance(m["content"], str):
            gemini_history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=gemini_history)
    last_message = messages[-1]["content"] if messages else ""

    response = chat.send_message(last_message)

    # Handle function calls
    while response.candidates[0].content.parts:
        has_function_call = False
        function_responses = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                has_function_call = True
                fn = part.function_call
                logger.info(f"Tool: {fn.name}")
                args = dict(fn.args) if fn.args else {}
                result = execute_tool(fn.name, args)
                function_responses.append(
                    ai_client.protos.Part(function_response=ai_client.protos.FunctionResponse(
                        name=fn.name,
                        response={"result": json.loads(result)}
                    ))
                )

        if not has_function_call:
            break

        response = chat.send_message(function_responses)

    final_text = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "text") and part.text:
            final_text += part.text

    return final_text, messages


# ---- Main chat function ----


def chat_with_ai(user_message: str, session_id: str = "default") -> str:
    """Send a message to the configured AI provider with HA tools."""
    if not ai_client:
        provider_name = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("name", AI_PROVIDER)
        return f"\u26a0\ufe0f Chiave API per {provider_name} non configurata. Impostala nelle impostazioni dell'add-on."

    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({"role": "user", "content": user_message})
    messages = conversations[session_id][-20:]

    try:
        if AI_PROVIDER == "anthropic":
            final_text, messages = chat_anthropic(messages)
        elif AI_PROVIDER == "openai":
            final_text, messages = chat_openai(messages)
        elif AI_PROVIDER == "google":
            final_text, messages = chat_google(messages)
        elif AI_PROVIDER == "github":
            final_text, messages = chat_openai(messages)  # Same format, different base_url
        else:
            return f"\u274c Provider '{AI_PROVIDER}' non supportato. Scegli: anthropic, openai, google, github."

        conversations[session_id] = messages
        conversations[session_id].append({"role": "assistant", "content": final_text})
        save_conversations()
        return final_text

    except Exception as e:
        logger.error(f"AI error ({AI_PROVIDER}): {e}")
        return f"\u274c Errore {PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get('name', AI_PROVIDER)}: {str(e)}"


# ---- Streaming chat ----


def stream_chat_openai(messages):
    """Stream chat for OpenAI/GitHub with real token streaming. Yields SSE event dicts."""
    trimmed = trim_messages(messages)
    system_prompt = get_system_prompt()
    tools = get_openai_tools_for_provider()
    max_tok = 4000 if AI_PROVIDER == "github" else 4096
    full_text = ""

    while True:
        oai_messages = [{"role": "system", "content": system_prompt}] + trim_messages(messages)

        response = ai_client.chat.completions.create(
            model=get_active_model(),
            messages=oai_messages,
            tools=tools,
            max_tokens=max_tok,
            stream=True
        )

        content_parts = []
        tool_calls_map = {}

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if delta.content:
                content_parts.append(delta.content)
                yield {"type": "token", "content": delta.content}

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.id:
                        tool_calls_map[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_map[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc_delta.function.arguments

        accumulated = "".join(content_parts)

        if not tool_calls_map:
            full_text = accumulated
            break

        # Build assistant message with tool calls
        tc_list = []
        for idx in sorted(tool_calls_map.keys()):
            tc = tool_calls_map[idx]
            tc_list.append({
                "id": tc["id"], "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]}
            })

        messages.append({"role": "assistant", "content": accumulated, "tool_calls": tc_list})

        for tc in tc_list:
            fn_name = tc["function"]["name"]
            yield {"type": "tool", "name": fn_name}
            args = json.loads(tc["function"]["arguments"])
            result = execute_tool(fn_name, args)
            if AI_PROVIDER == "github" and len(result) > 3000:
                result = result[:3000] + '... (truncated)'
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

    messages.append({"role": "assistant", "content": full_text})
    yield {"type": "done", "full_text": full_text}


def stream_chat_anthropic(messages):
    """Stream chat for Anthropic (processes tools, then streams final text word-by-word)."""
    final_text, _ = chat_anthropic(messages)
    messages.append({"role": "assistant", "content": final_text})
    words = final_text.split(' ')
    for i, word in enumerate(words):
        yield {"type": "token", "content": word + (' ' if i < len(words) - 1 else '')}
    yield {"type": "done", "full_text": final_text}


def stream_chat_google(messages):
    """Stream chat for Google Gemini (processes tools, then streams final text word-by-word)."""
    final_text, _ = chat_google(messages)
    messages.append({"role": "assistant", "content": final_text})
    words = final_text.split(' ')
    for i, word in enumerate(words):
        yield {"type": "token", "content": word + (' ' if i < len(words) - 1 else '')}
    yield {"type": "done", "full_text": final_text}


def stream_chat_with_ai(user_message: str, session_id: str = "default"):
    """Stream chat events for all providers. Yields SSE event dicts."""
    if not ai_client:
        yield {"type": "error", "message": "API key non configurata"}
        return

    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({"role": "user", "content": user_message})
    messages = conversations[session_id]

    try:
        if AI_PROVIDER in ("openai", "github"):
            yield from stream_chat_openai(messages)
        elif AI_PROVIDER == "anthropic":
            yield from stream_chat_anthropic(messages)
        elif AI_PROVIDER == "google":
            yield from stream_chat_google(messages)
        else:
            yield {"type": "error", "message": f"Provider '{AI_PROVIDER}' non supportato"}
            return

        # Trim and save
        if len(conversations[session_id]) > 50:
            conversations[session_id] = conversations[session_id][-40:]
        save_conversations()
    except Exception as e:
        logger.error(f"Stream error ({AI_PROVIDER}): {e}")
        yield {"type": "error", "message": str(e)}


# ---- Chat UI HTML ----


def get_chat_ui():
    """Generate the chat UI."""
    provider_name = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("name", AI_PROVIDER)
    model_name = get_active_model()
    configured = bool(get_api_key())
    status_color = "#4caf50" if configured else "#ff9800"
    status_text = provider_name if configured else f"{provider_name} (no key)"

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Assistant - Home Assistant</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
        .header h1 {{ font-size: 18px; font-weight: 600; }}
        .header .badge {{ font-size: 10px; opacity: 0.9; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px; }}
        .header .status {{ margin-left: auto; font-size: 12px; display: flex; align-items: center; gap: 6px; }}
        .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: {status_color}; animation: pulse 2s infinite; }}
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
        .tool-badge {{ display: inline-block; background: #e8f0fe; color: #1967d2; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px;">\U0001f916</span>
        <h1>AI Assistant</h1>
        <span class="badge">v{VERSION}</span>
        <span class="badge">{model_name}</span>
        <div class="status">
            <div class="status-dot"></div>
            {status_text}
        </div>
    </div>

    <div class="chat-container" id="chat">
        <div class="message system">
            \U0001f44b Ciao! Sono il tuo assistente AI per Home Assistant.<br>
            Provider: <strong>{provider_name}</strong> | Modello: <strong>{model_name}</strong><br>
            Posso controllare dispositivi, creare automazioni e gestire la tua casa smart.
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
            if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); sendMessage(); }}
        }}

        function addMessage(text, role) {{
            const div = document.createElement('div');
            div.className = 'message ' + role;
            if (role === 'assistant') {{ div.innerHTML = formatMarkdown(text); }}
            else {{ div.textContent = text; }}
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}

        function formatMarkdown(text) {{
            text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<pre><code>$2</code></pre>');
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            text = text.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
            text = text.replace(/\\n/g, '<br>');
            return text;
        }}

        function showThinking() {{
            const div = document.createElement('div');
            div.className = 'message thinking';
            div.id = 'thinking';
            div.innerHTML = 'Sto pensando<span class="dots"><span>.</span><span>.</span><span>.</span></span>';
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
                const resp = await fetch('api/chat/stream', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: text }})
                }});
                removeThinking();
                if (resp.headers.get('content-type')?.includes('text/event-stream')) {{
                    await handleStream(resp);
                }} else {{
                    const data = await resp.json();
                    if (data.response) {{ addMessage(data.response, 'assistant'); }}
                    else if (data.error) {{ addMessage('\u274c ' + data.error, 'system'); }}
                }}
            }} catch (err) {{
                removeThinking();
                addMessage('\u274c Errore: ' + err.message, 'system');
            }}
            sending = false;
            sendBtn.disabled = false;
            input.focus();
        }}

        async function handleStream(resp) {{
            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let div = null;
            let fullText = '';
            let buffer = '';
            let hasTools = false;
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
                            if (evt.type === 'tool') {{
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                hasTools = true;
                                div.innerHTML += '<div class="tool-badge">\U0001f527 ' + evt.name + '</div>';
                            }} else if (evt.type === 'token') {{
                                if (hasTools && div) {{ div.innerHTML = ''; hasTools = false; }}
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                fullText += evt.content;
                                div.innerHTML = formatMarkdown(fullText);
                            }} else if (evt.type === 'error') {{
                                addMessage('\u274c ' + evt.message, 'system');
                            }}
                            chat.scrollTop = chat.scrollHeight;
                        }} catch(e) {{}}
                    }}
                }}
            }}
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


@app.route('/api/status')
def api_status():
    """Debug endpoint to check HA connection status."""
    token = get_ha_token()
    ha_ok = False
    ha_msg = ""
    try:
        resp = requests.get(f"{HA_URL}/api/", headers=get_ha_headers(), timeout=10)
        ha_ok = resp.status_code == 200
        ha_msg = f"{resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        ha_msg = str(e)

    return jsonify({
        "version": VERSION,
        "provider": AI_PROVIDER,
        "model": get_active_model(),
        "api_key_set": bool(get_api_key()),
        "ha_url": HA_URL,
        "supervisor_token_present": bool(token),
        "supervisor_token_length": len(token),
        "ha_connection_ok": ha_ok,
        "ha_response": ha_msg,
    })


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint."""
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    if not message:
        return jsonify({"error": "Empty message"}), 400
    logger.info(f"Chat [{AI_PROVIDER}]: {message}")
    response_text = chat_with_ai(message, session_id)
    return jsonify({"response": response_text}), 200


@app.route('/api/chat/stream', methods=['POST'])
def api_chat_stream():
    """Streaming chat endpoint using Server-Sent Events."""
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    if not message:
        return jsonify({"error": "Empty message"}), 400
    logger.info(f"Stream [{AI_PROVIDER}]: {message}")

    def generate():
        for event in stream_chat_with_ai(message, session_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/api/conversations', methods=['GET'])
def api_conversations():
    """List conversation sessions."""
    sessions = {}
    for sid, msgs in conversations.items():
        sessions[sid] = {"message_count": len(msgs), "last_role": msgs[-1]["role"] if msgs else ""}
    return jsonify(sessions), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "ai_provider": AI_PROVIDER,
        "ai_model": get_active_model(),
        "ai_configured": bool(get_api_key()),
        "ha_connected": bool(get_ha_token()),
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
    return jsonify(call_ha_api("GET", f"states/{entity_id}")), 200


@app.route("/message", methods=["POST"])
def send_message_legacy():
    """Legacy message endpoint."""
    data = request.get_json()
    return jsonify({"status": "success", "response": chat_with_ai(data.get("message", ""))}), 200


@app.route("/service/call", methods=["POST"])
def call_service_route():
    """Call a Home Assistant service."""
    data = request.get_json()
    service = data.get("service", "")
    if not service or "." not in service:
        return jsonify({"error": "Use 'domain.service' format"}), 400
    domain, svc = service.split(".", 1)
    return jsonify(call_ha_api("POST", f"services/{domain}/{svc}", data.get("data", {}))), 200


@app.route("/execute/automation", methods=["POST"])
def execute_automation():
    """Execute an automation."""
    data = request.get_json()
    eid = data.get("entity_id", data.get("automation_id", ""))
    if not eid.startswith("automation."):
        eid = f"automation.{eid}"
    return jsonify(call_ha_api("POST", "services/automation/trigger", {"entity_id": eid})), 200


@app.route("/execute/script", methods=["POST"])
def execute_script():
    """Execute a script."""
    data = request.get_json()
    return jsonify(call_ha_api("POST", f"services/script/{data.get('script_id', '')}", data.get("variables", {}))), 200


@app.route("/conversation/clear", methods=["POST"])
def clear_conversation():
    """Clear conversation history."""
    sid = (request.get_json() or {}).get("session_id", "default")
    conversations.pop(sid, None)
    return jsonify({"status": "cleared"}), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(f"Starting AI Assistant v{VERSION} on port {API_PORT}")
    logger.info(f"Provider: {AI_PROVIDER} | Model: {get_active_model()}")
    logger.info(f"API Key: {'configured' if get_api_key() else 'NOT configured'}")
    logger.info(f"HA Token: {'available' if get_ha_token() else 'NOT available'}")
    app.run(host="0.0.0.0", port=API_PORT, debug=DEBUG_MODE)
