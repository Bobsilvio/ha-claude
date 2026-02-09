"""AI Assistant API with multi-provider support for Home Assistant."""

import os
import json
import logging
import queue
import time
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
VERSION = "2.9.9"

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
ENABLE_FILE_ACCESS = os.getenv("ENABLE_FILE_ACCESS", "False").lower() == "true"

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

# Abort flag per session (for stop button)
abort_streams: Dict[str, bool] = {}

# User-friendly tool descriptions (Italian)
TOOL_DESCRIPTIONS = {
    "get_entities": "Carico dispositivi",
    "get_entity_state": "Leggo stato dispositivo",
    "call_service": "Eseguo comando",
    "search_entities": "Cerco dispositivi",
    "get_automations": "Carico automazioni",
    "update_automation": "Modifico automazione",
    "create_automation": "Creo automazione",
    "trigger_automation": "Avvio automazione",
    "delete_automation": "Elimino automazione",
    "get_scripts": "Carico script",
    "run_script": "Eseguo script",
    "update_script": "Modifico script",
    "create_script": "Creo script",
    "delete_script": "Elimino script",
    "get_dashboards": "Carico dashboard",
    "get_dashboard_config": "Leggo config dashboard",
    "update_dashboard": "Modifico dashboard",
    "create_dashboard": "Creo dashboard",
    "delete_dashboard": "Elimino dashboard",
    "get_frontend_resources": "Verifico card installate",
    "get_scenes": "Carico scene",
    "activate_scene": "Attivo scena",
    "get_areas": "Carico stanze",
    "manage_areas": "Gestisco stanze",
    "get_history": "Carico storico",
    "get_statistics": "Carico statistiche",
    "send_notification": "Invio notifica",
    "read_config_file": "Leggo file config",
    "write_config_file": "Salvo file config",
    "list_config_files": "Elenco file config",
    "check_config": "Valido configurazione",
    "create_backup": "Creo backup",
    "get_available_services": "Carico servizi",
    "get_events": "Carico eventi",
    "manage_entity": "Gestisco entità",
    "get_devices": "Carico dispositivi",
    "shopping_list": "Lista spesa",
    "browse_media": "Sfoglio media",
    "list_snapshots": "Elenco snapshot",
    "restore_snapshot": "Ripristino snapshot",
}

def get_tool_description(tool_name: str) -> str:
    """Get user-friendly Italian description for a tool."""
    return TOOL_DESCRIPTIONS.get(tool_name, tool_name.replace('_', ' ').title())

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

# ---- Snapshot system for safe config editing ----

SNAPSHOTS_DIR = "/data/snapshots"
HA_CONFIG_DIR = "/homeassistant"  # Mapped via config.json "map": ["config:rw"]

def create_snapshot(filename: str) -> dict:
    """Create a snapshot of a file before modifying it. Returns snapshot info."""
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    src_path = os.path.join(HA_CONFIG_DIR, filename)
    if not os.path.isfile(src_path):
        return {"snapshot_id": None, "message": f"File '{filename}' does not exist (new file)"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace("/", "__").replace("\\", "__")
    snapshot_id = f"{timestamp}_{safe_name}"
    snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_id)

    import shutil
    shutil.copy2(src_path, snapshot_path)

    # Save metadata
    meta_path = snapshot_path + ".meta"
    meta = {"original_file": filename, "timestamp": timestamp, "snapshot_id": snapshot_id,
            "size": os.path.getsize(src_path)}
    with open(meta_path, "w") as f:
        json.dump(meta, f)

    # Keep max 50 snapshots, remove oldest
    all_snapshots = sorted([f for f in os.listdir(SNAPSHOTS_DIR) if not f.endswith(".meta")])
    while len(all_snapshots) > 50:
        oldest = all_snapshots.pop(0)
        try:
            os.remove(os.path.join(SNAPSHOTS_DIR, oldest))
            os.remove(os.path.join(SNAPSHOTS_DIR, oldest + ".meta"))
        except:
            pass

    logger.info(f"Snapshot created: {snapshot_id}")
    return {"snapshot_id": snapshot_id, "original_file": filename, "timestamp": timestamp}


# ---- Home Assistant API helpers ----


def call_ha_websocket(msg_type: str, **kwargs) -> dict:
    """Send a WebSocket command to Home Assistant and return the result."""
    import websocket as ws_lib
    token = get_ha_token()
    ws_url = HA_URL.replace("http://", "ws://").replace("https://", "wss://") + "/websocket"
    logger.debug(f"WS connect: {ws_url} for {msg_type}")
    try:
        ws = ws_lib.create_connection(ws_url, timeout=15)
        # Wait for auth_required
        auth_req = json.loads(ws.recv())
        logger.debug(f"WS auth_required: {auth_req.get('type')}")
        # Authenticate
        ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth_resp = json.loads(ws.recv())
        if auth_resp.get("type") != "auth_ok":
            ws.close()
            return {"error": f"WS auth failed: {auth_resp}"}
        # Send command
        msg = {"id": 1, "type": msg_type}
        msg.update(kwargs)
        ws.send(json.dumps(msg))
        result = json.loads(ws.recv())
        ws.close()
        logger.debug(f"WS result: {result}")
        return result
    except Exception as e:
        logger.error(f"WS error ({msg_type}): {e}")
        return {"error": str(e)}


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
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
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
        "description": "Get all existing automations with their YAML source. Returns the list of automations AND the content of automations.yaml. To modify an automation, use update_automation instead of write_config_file.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "update_automation",
        "description": "Update or modify an existing automation by its ID. Pass the automation_id and the fields you want to change. The tool reads automations.yaml, finds the automation, applies the changes, creates a snapshot, and saves. Much simpler than rewriting the full file.",
        "parameters": {
            "type": "object",
            "properties": {
                "automation_id": {"type": "string", "description": "The automation's 'id' field from automations.yaml (e.g. '1728373064590')."},
                "changes": {"type": "object", "description": "Fields to update. Can include: alias, description, trigger, condition, action, mode. Only pass the fields you want to change."},
                "add_condition": {"type": "object", "description": "A single condition to ADD to the existing conditions (appended, does not replace). Use this for simple additions like excluding a team."}
            },
            "required": ["automation_id"]
        }
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
        "name": "update_script",
        "description": "Update/modify an existing script directly in scripts.yaml. Reads the file, finds the script, applies changes, creates a snapshot, saves. Use this instead of write_config_file for scripts.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "The script ID (e.g. 'goodnight_routine' without 'script.' prefix)."},
                "changes": {"type": "object", "description": "Object with the fields to change (e.g. {\"alias\": \"New Name\", \"sequence\": [...]}). Only specified fields are modified."}
            },
            "required": ["script_id", "changes"]
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
    },
    {
        "name": "delete_dashboard",
        "description": "Delete a Lovelace dashboard by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "string", "description": "The dashboard ID (get it from get_dashboards)."}
            },
            "required": ["dashboard_id"]
        }
    },
    {
        "name": "delete_automation",
        "description": "Delete an existing automation.",
        "parameters": {
            "type": "object",
            "properties": {
                "automation_id": {"type": "string", "description": "The automation entity_id (e.g. 'automation.my_automation')."}
            },
            "required": ["automation_id"]
        }
    },
    {
        "name": "delete_script",
        "description": "Delete an existing script.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "The script ID without prefix (e.g. 'goodnight_routine')."}
            },
            "required": ["script_id"]
        }
    },
    {
        "name": "manage_areas",
        "description": "Manage Home Assistant areas/rooms: list, create, rename, or delete areas.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "update", "delete"], "description": "Action to perform."},
                "name": {"type": "string", "description": "Area name (for create/update)."},
                "area_id": {"type": "string", "description": "Area ID (for update/delete)."},
                "icon": {"type": "string", "description": "MDI icon for the area (optional)."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "manage_entity",
        "description": "Update entity registry: rename, assign to area, enable/disable an entity.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "The entity ID to manage."},
                "name": {"type": "string", "description": "New friendly name (optional)."},
                "area_id": {"type": "string", "description": "Assign to area ID (optional). Use manage_areas list to get IDs."},
                "disabled_by": {"type": "string", "enum": ["user", ""], "description": "Set to 'user' to disable, '' to enable."},
                "icon": {"type": "string", "description": "Custom icon (optional)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_devices",
        "description": "Get all devices registered in Home Assistant with manufacturer, model, and area.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_statistics",
        "description": "Get advanced statistics (min, max, mean, sum) for a sensor over a time period. Useful for energy, temperature trends, averages.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Sensor entity_id (e.g. 'sensor.temperature')."},
                "period": {"type": "string", "enum": ["5minute", "hour", "day", "week", "month"], "description": "Statistics period (default: hour)."},
                "hours": {"type": "number", "description": "How many hours back to query (default 24, max 720)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "shopping_list",
        "description": "Manage the Home Assistant shopping list: view items, add new items, or mark items as complete.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "add", "complete"], "description": "Action to perform."},
                "name": {"type": "string", "description": "Item name (for add)."},
                "item_id": {"type": "string", "description": "Item ID (for complete, get from list)."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "create_backup",
        "description": "Create a full Home Assistant backup. This may take a few minutes.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "browse_media",
        "description": "Browse available media content (music, photos, etc.) from media players.",
        "parameters": {
            "type": "object",
            "properties": {
                "media_content_id": {"type": "string", "description": "Content path to browse (empty for root)."},
                "media_content_type": {"type": "string", "description": "Media type (e.g. 'music', 'image'). Default: 'music'."}
            },
            "required": []
        }
    },
    {
        "name": "get_dashboard_config",
        "description": "Get the full configuration of a Lovelace dashboard. Use this to read an existing dashboard before modifying it.",
        "parameters": {
            "type": "object",
            "properties": {
                "url_path": {"type": "string", "description": "Dashboard URL path (e.g. 'lovelace', 'energy-dashboard'). Use 'lovelace' or null for the default dashboard. Use get_dashboards to list all."}
            },
            "required": []
        }
    },
    {
        "name": "update_dashboard",
        "description": "Update/modify an existing Lovelace dashboard configuration. First use get_dashboard_config to read the current config, modify it, then save with this tool. Supports all card types including custom cards (card-mod, bubble-card, mushroom, etc.).",
        "parameters": {
            "type": "object",
            "properties": {
                "url_path": {"type": "string", "description": "Dashboard URL path. Use 'lovelace' or null for the default dashboard."},
                "views": {"type": "array", "description": "Complete array of views with their cards. This REPLACES all views.", "items": {"type": "object"}}
            },
            "required": ["views"]
        }
    },
    {
        "name": "get_frontend_resources",
        "description": "List all registered Lovelace frontend resources (custom cards, modules). Use this to check if custom cards like card-mod, bubble-card, mushroom-cards, etc. are installed via HACS.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "read_config_file",
        "description": "Read a Home Assistant configuration file (e.g. configuration.yaml, automations.yaml, scripts.yaml, secrets.yaml, ui-lovelace.yaml, or any YAML/JSON file in the config directory). Returns file content as text.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File path relative to HA config dir (e.g. 'configuration.yaml', 'ui-lovelace.yaml', 'dashboards/energy.yaml')."}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "write_config_file",
        "description": "Write/update a Home Assistant configuration file. ALWAYS creates a snapshot backup first (automatically). Use for editing configuration.yaml, YAML dashboards, includes, packages, etc. After writing, call check_config to validate.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File path relative to HA config dir (e.g. 'configuration.yaml', 'ui-lovelace.yaml')."},
                "content": {"type": "string", "description": "The full file content to write."}
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "check_config",
        "description": "Validate Home Assistant configuration. Call this after modifying configuration.yaml or any YAML file. Returns 'valid' or error details.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "list_config_files",
        "description": "List files in the Home Assistant config directory (or a subdirectory). Useful to discover YAML dashboards, packages, includes, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Subdirectory to list (empty for root config dir). E.g. 'dashboards', 'packages', 'custom_components'."}
            },
            "required": []
        }
    },
    {
        "name": "list_snapshots",
        "description": "List all available configuration snapshots. Snapshots are auto-created before any file modification.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "restore_snapshot",
        "description": "Restore a file from a previously created snapshot. Use list_snapshots to see available snapshots.",
        "parameters": {
            "type": "object",
            "properties": {
                "snapshot_id": {"type": "string", "description": "The snapshot ID (from list_snapshots)."}
            },
            "required": ["snapshot_id"]
        }
    }
]


def get_anthropic_tools():
    """Convert tools to Anthropic format."""
    tools = HA_TOOLS_DESCRIPTION
    if not ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_GROUPS.get("config_edit", []))
        tools = [t for t in tools if t["name"] not in config_edit_tools]
    return [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in tools
    ]


def get_openai_tools():
    """Convert tools to OpenAI function-calling format."""
    tools = HA_TOOLS_DESCRIPTION
    if not ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_GROUPS.get("config_edit", []))
        tools = [t for t in tools if t["name"] not in config_edit_tools]
    return [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
        for t in tools
    ]


def get_gemini_tools():
    """Convert tools to Google Gemini format."""
    from google.generativeai.types import FunctionDeclaration, Tool
    tools = HA_TOOLS_DESCRIPTION
    if not ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_GROUPS.get("config_edit", []))
        tools = [t for t in tools if t["name"] not in config_edit_tools]
    declarations = []
    for t in tools:
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
            # Return only essential fields to save tokens
            if isinstance(result, dict):
                slim = {
                    "entity_id": result.get("entity_id"),
                    "state": result.get("state"),
                    "friendly_name": result.get("attributes", {}).get("friendly_name", ""),
                    "last_changed": result.get("last_changed", "")
                }
                # Include only useful attributes
                attrs = result.get("attributes", {})
                useful_keys = ("friendly_name", "unit_of_measurement", "device_class",
                              "brightness", "color_temp", "temperature", "current_temperature",
                              "hvac_modes", "hvac_action", "preset_mode", "source", "media_title",
                              "id")  # 'id' is critical for automations
                slim["attributes"] = {k: v for k, v in attrs.items() if k in useful_keys}
                return json.dumps(slim, ensure_ascii=False, default=str)
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
                       "id": a.get("attributes", {}).get("id", ""),
                       "last_triggered": a.get("attributes", {}).get("last_triggered", "")} for a in autos]
            return json.dumps({"automations": result, "edit_hint": "To edit an automation, use update_automation with the automation's id and the changes you want to make."}, ensure_ascii=False, default=str)

        elif tool_name == "update_automation":
            import yaml
            automation_id = tool_input.get("automation_id", "")
            changes = tool_input.get("changes", {})
            add_condition = tool_input.get("add_condition", None)
            
            if not automation_id:
                return json.dumps({"error": "automation_id is required."})
            
            # Strategy: try YAML first, then REST API fallback (for UI-created automations)
            updated_via = None
            old_yaml = ""
            new_yaml = ""
            
            # --- ATTEMPT 1: YAML file ---
            yaml_path = os.path.join(HA_CONFIG_DIR, "automations.yaml")
            if os.path.isfile(yaml_path):
                try:
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        automations = yaml.safe_load(f)
                    
                    if isinstance(automations, list):
                        found = None
                        found_idx = None
                        for idx, auto in enumerate(automations):
                            if str(auto.get("id", "")) == str(automation_id):
                                found = auto
                                found_idx = idx
                                break
                        
                        if found is not None:
                            old_yaml = yaml.dump(found, default_flow_style=False, allow_unicode=True)
                            cond_key = "conditions" if "conditions" in found else "condition"
                            # Remap condition↔conditions in changes to match existing key
                            if "condition" in changes and cond_key == "conditions":
                                changes["conditions"] = changes.pop("condition")
                            elif "conditions" in changes and cond_key == "condition":
                                changes["condition"] = changes.pop("conditions")
                            for key, value in changes.items():
                                found[key] = value
                            if add_condition:
                                if cond_key not in found or not found[cond_key]:
                                    found[cond_key] = []
                                if not isinstance(found[cond_key], list):
                                    found[cond_key] = [found[cond_key]]
                                found[cond_key].append(add_condition)
                            new_yaml = yaml.dump(found, default_flow_style=False, allow_unicode=True)
                            snapshot = create_snapshot("automations.yaml")
                            automations[found_idx] = found
                            with open(yaml_path, "w", encoding="utf-8") as f:
                                yaml.dump(automations, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                            updated_via = "yaml"
                except Exception as e:
                    logger.warning(f"YAML update attempt failed: {e}")
            
            # --- ATTEMPT 2: REST API (for UI-created automations) ---
            if updated_via is None:
                try:
                    # Get current config via REST API
                    current = call_ha_api("GET", f"config/automation/config/{automation_id}")
                    if isinstance(current, dict) and "error" not in current:
                        old_yaml = yaml.dump(current, default_flow_style=False, allow_unicode=True)
                        
                        # Normalize: HA may use 'condition' or 'conditions' - unify to what HA returned
                        cond_key = "conditions" if "conditions" in current else "condition"
                        
                        # Remap condition↔conditions in changes to match existing key
                        if "condition" in changes and cond_key == "conditions":
                            changes["conditions"] = changes.pop("condition")
                        elif "conditions" in changes and cond_key == "condition":
                            changes["condition"] = changes.pop("conditions")
                        
                        # Apply changes
                        for key, value in changes.items():
                            current[key] = value
                        if add_condition:
                            if cond_key not in current or not current[cond_key]:
                                current[cond_key] = []
                            if not isinstance(current[cond_key], list):
                                current[cond_key] = [current[cond_key]]
                            current[cond_key].append(add_condition)
                        
                        # Ensure no duplicate condition/conditions keys
                        if "condition" in current and "conditions" in current:
                            # Keep whichever has data, prefer 'conditions' (new format)
                            if current.get("conditions"):
                                current.pop("condition", None)
                            else:
                                current.pop("conditions", None)
                        
                        new_yaml = yaml.dump(current, default_flow_style=False, allow_unicode=True)
                        # Save via REST API (HA uses POST for both create and update)
                        save_result = call_ha_api("POST", f"config/automation/config/{automation_id}", current)
                        if isinstance(save_result, dict) and "error" not in save_result:
                            updated_via = "rest_api"
                        else:
                            return json.dumps({"error": f"REST API update failed: {save_result}",
                                               "IMPORTANT": "STOP. Inform the user about the error. Do NOT try other tools."}, default=str)
                    else:
                        return json.dumps({"error": f"Automation '{automation_id}' not found in YAML or via REST API.",
                                           "IMPORTANT": "STOP. Tell the user the automation was not found. Do NOT call more tools."}, default=str)
                except Exception as e:
                    return json.dumps({"error": f"Failed to update automation: {str(e)}",
                                       "IMPORTANT": "STOP. Inform the user about the error. Do NOT try other tools."})
            
            msg_parts = [f"Automation updated via {'YAML file' if updated_via == 'yaml' else 'HA REST API (UI-created automation)'}.",]
            return json.dumps({
                "status": "success",
                "message": " ".join(msg_parts),
                "updated_via": updated_via,
                "old_yaml": old_yaml,
                "new_yaml": new_yaml,
                "snapshot": snapshot.get("snapshot_id", "") if updated_via == "yaml" else "N/A (REST API)",
                "tip": "Changes applied immediately via REST API. No reload needed." if updated_via == "rest_api" else "Call services/automation/reload to apply changes.",
                "IMPORTANT": "DONE. Show the user the before/after diff and stop. Do NOT call any more tools."
            }, ensure_ascii=False, default=str)

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
                        "friendly_name": s.get("attributes", {}).get("friendly_name", "")
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

        elif tool_name == "update_script":
            import yaml
            script_id = tool_input.get("script_id", "")
            changes = tool_input.get("changes", {})

            if not script_id:
                return json.dumps({"error": "script_id is required."})

            # Remove 'script.' prefix if present
            script_id = script_id.replace("script.", "") if script_id.startswith("script.") else script_id

            yaml_path = os.path.join(HA_CONFIG_DIR, "scripts.yaml")
            if not os.path.isfile(yaml_path):
                return json.dumps({"error": "scripts.yaml not found."})

            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    scripts = yaml.safe_load(f)

                if not isinstance(scripts, dict):
                    return json.dumps({"error": "scripts.yaml is not a valid dict."})

                if script_id not in scripts:
                    return json.dumps({"error": f"Script '{script_id}' not found.",
                                       "available_scripts": list(scripts.keys())[:20]})

                found = scripts[script_id]
                if not isinstance(found, dict):
                    found = {}

                # Capture old state for diff
                old_yaml = yaml.dump({script_id: found}, default_flow_style=False, allow_unicode=True)

                # Apply changes
                for key, value in changes.items():
                    found[key] = value

                # Capture new state for diff
                new_yaml = yaml.dump({script_id: found}, default_flow_style=False, allow_unicode=True)

                # Create snapshot before saving
                snapshot = create_snapshot("scripts.yaml")

                # Write back
                scripts[script_id] = found
                with open(yaml_path, "w", encoding="utf-8") as f:
                    yaml.dump(scripts, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                return json.dumps({
                    "status": "success",
                    "message": f"Script '{found.get('alias', script_id)}' updated.",
                    "old_yaml": old_yaml,
                    "new_yaml": new_yaml,
                    "snapshot": snapshot.get("snapshot_id", ""),
                    "tip": "Call services/script/reload to apply changes.",
                    "IMPORTANT": "DONE. Show the user the before/after diff and stop. Do NOT call any more tools."
                }, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to update script: {str(e)}"})

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
            ws_result = call_ha_websocket("lovelace/dashboards/list")
            if ws_result.get("success") and ws_result.get("result"):
                dashboards = ws_result["result"]
                result = [{"id": d.get("id"), "title": d.get("title"), "url_path": d.get("url_path"),
                           "icon": d.get("icon", ""), "mode": d.get("mode", "")} for d in dashboards]
                return json.dumps(result, ensure_ascii=False, default=str)
            return json.dumps({"error": f"Could not get dashboards: {ws_result}"}, default=str)

        elif tool_name == "create_dashboard":
            title = tool_input.get("title", "AI Dashboard")
            url_path = tool_input.get("url_path", "ai-dashboard")
            icon = tool_input.get("icon", "mdi:robot")
            views = tool_input.get("views", [])

            # Step 1: Register dashboard via WebSocket (REST API doesn't support this)
            ws_result = call_ha_websocket(
                "lovelace/dashboards/create",
                url_path=url_path,
                title=title,
                icon=icon,
                show_in_sidebar=True,
                require_admin=False
            )
            if ws_result.get("success") is False:
                error_msg = ws_result.get("error", {}).get("message", str(ws_result))
                return json.dumps({"error": f"Failed to create dashboard: {error_msg}"}, default=str)

            # Step 2: Set the dashboard config with views and cards via WebSocket
            ws_config = call_ha_websocket(
                "lovelace/config/save",
                url_path=url_path,
                config={"views": views}
            )
            if ws_config.get("success") is False:
                error_msg = ws_config.get("error", {}).get("message", str(ws_config))
                return json.dumps({"status": "partial", "message": f"Dashboard registered but config failed: {error_msg}"}, default=str)

            return json.dumps({"status": "success", "message": f"Dashboard '{title}' created! It appears in the sidebar at /{url_path}",
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

        # ===== DELETE OPERATIONS (WebSocket) =====
        elif tool_name == "delete_dashboard":
            dashboard_id = tool_input.get("dashboard_id", "")
            result = call_ha_websocket("lovelace/dashboards/delete", dashboard_id=dashboard_id)
            if result.get("success"):
                return json.dumps({"status": "success", "message": f"Dashboard '{dashboard_id}' deleted."}, ensure_ascii=False)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to delete dashboard: {error_msg}"}, default=str)

        elif tool_name == "delete_automation":
            automation_id = tool_input.get("automation_id", "")
            # Need the object_id (without automation. prefix)
            object_id = automation_id.replace("automation.", "") if automation_id.startswith("automation.") else automation_id
            result = call_ha_api("DELETE", f"config/automation/config/{object_id}")
            return json.dumps({"status": "success", "message": f"Automation '{automation_id}' deleted."}, ensure_ascii=False, default=str)

        elif tool_name == "delete_script":
            script_id = tool_input.get("script_id", "").replace("script.", "")
            result = call_ha_api("DELETE", f"config/script/config/{script_id}")
            return json.dumps({"status": "success", "message": f"Script '{script_id}' deleted."}, ensure_ascii=False, default=str)

        # ===== AREA MANAGEMENT (WebSocket) =====
        elif tool_name == "manage_areas":
            action = tool_input.get("action", "list")
            if action == "list":
                result = call_ha_websocket("config/area_registry/list")
                areas = result.get("result", [])
                summary = [{"area_id": a.get("area_id"), "name": a.get("name"), "icon": a.get("icon", "")} for a in areas]
                return json.dumps({"areas": summary, "count": len(summary)}, ensure_ascii=False, default=str)
            elif action == "create":
                name = tool_input.get("name", "")
                params = {"name": name}
                if tool_input.get("icon"):
                    params["icon"] = tool_input["icon"]
                result = call_ha_websocket("config/area_registry/create", **params)
                if result.get("success"):
                    area = result.get("result", {})
                    return json.dumps({"status": "success", "message": f"Area '{name}' created.", "area_id": area.get("area_id")}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to create area: {error_msg}"}, default=str)
            elif action == "update":
                area_id = tool_input.get("area_id", "")
                params = {"area_id": area_id}
                if tool_input.get("name"):
                    params["name"] = tool_input["name"]
                if tool_input.get("icon"):
                    params["icon"] = tool_input["icon"]
                result = call_ha_websocket("config/area_registry/update", **params)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Area '{area_id}' updated."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to update area: {error_msg}"}, default=str)
            elif action == "delete":
                area_id = tool_input.get("area_id", "")
                result = call_ha_websocket("config/area_registry/delete", area_id=area_id)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Area '{area_id}' deleted."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to delete area: {error_msg}"}, default=str)

        # ===== ENTITY REGISTRY (WebSocket) =====
        elif tool_name == "manage_entity":
            entity_id = tool_input.get("entity_id", "")
            params = {"entity_id": entity_id}
            if tool_input.get("name") is not None:
                params["name"] = tool_input["name"]
            if tool_input.get("area_id") is not None:
                params["area_id"] = tool_input["area_id"]
            if tool_input.get("disabled_by") is not None:
                params["disabled_by"] = tool_input["disabled_by"] if tool_input["disabled_by"] else None
            if tool_input.get("icon") is not None:
                params["icon"] = tool_input["icon"]
            result = call_ha_websocket("config/entity_registry/update", **params)
            if result.get("success"):
                entry = result.get("result", {})
                return json.dumps({"status": "success", "message": f"Entity '{entity_id}' updated.",
                                   "name": entry.get("name"), "area_id": entry.get("area_id"),
                                   "disabled_by": entry.get("disabled_by")}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to update entity: {error_msg}"}, default=str)

        # ===== DEVICE REGISTRY (WebSocket) =====
        elif tool_name == "get_devices":
            result = call_ha_websocket("config/device_registry/list")
            devices = result.get("result", [])
            summary = []
            for d in devices[:100]:  # Limit to 100 devices
                summary.append({
                    "id": d.get("id"),
                    "name": d.get("name_by_user") or d.get("name", ""),
                    "manufacturer": d.get("manufacturer", ""),
                    "model": d.get("model", ""),
                    "area_id": d.get("area_id", ""),
                    "via_device_id": d.get("via_device_id", "")
                })
            return json.dumps({"devices": summary, "count": len(devices), "showing": len(summary)}, ensure_ascii=False, default=str)

        # ===== ADVANCED STATISTICS (WebSocket) =====
        elif tool_name == "get_statistics":
            entity_id = tool_input.get("entity_id", "")
            period = tool_input.get("period", "hour")
            hours = min(tool_input.get("hours", 24), 720)
            start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
            result = call_ha_websocket(
                "recorder/statistics_during_period",
                start_time=start_time,
                statistic_ids=[entity_id],
                period=period
            )
            stats = result.get("result", {}).get(entity_id, [])
            # Summarize: take last 50 entries max
            summary_stats = []
            for s in stats[-50:]:
                summary_stats.append({
                    "start": s.get("start"),
                    "mean": s.get("mean"),
                    "min": s.get("min"),
                    "max": s.get("max"),
                    "sum": s.get("sum"),
                    "state": s.get("state")
                })
            return json.dumps({"entity_id": entity_id, "period": period,
                               "hours": hours, "statistics": summary_stats,
                               "total_entries": len(stats)}, ensure_ascii=False, default=str)

        # ===== SHOPPING LIST (WebSocket) =====
        elif tool_name == "shopping_list":
            action = tool_input.get("action", "list")
            if action == "list":
                result = call_ha_websocket("shopping_list/items")
                items = result.get("result", [])
                return json.dumps({"items": items, "count": len(items)}, ensure_ascii=False, default=str)
            elif action == "add":
                name = tool_input.get("name", "")
                result = call_ha_websocket("shopping_list/items/add", name=name)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"'{name}' added to shopping list.",
                                       "item": result.get("result", {})}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to add item: {error_msg}"}, default=str)
            elif action == "complete":
                item_id = tool_input.get("item_id", "")
                result = call_ha_websocket("shopping_list/items/update", item_id=item_id, complete=True)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Item marked as complete."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to complete item: {error_msg}"}, default=str)

        # ===== BACKUP (Supervisor REST API) =====
        elif tool_name == "create_backup":
            try:
                ha_token = get_ha_token()
                resp = requests.post(
                    "http://supervisor/backups/new/full",
                    headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
                    json={"name": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"},
                    timeout=300
                )
                result = resp.json()
                if result.get("result") == "ok":
                    slug = result.get("data", {}).get("slug", "")
                    return json.dumps({"status": "success", "message": f"Backup created successfully!", "slug": slug}, ensure_ascii=False, default=str)
                return json.dumps({"error": f"Backup failed: {result}"}, default=str)
            except Exception as e:
                return json.dumps({"error": f"Backup error: {str(e)}"}, default=str)

        # ===== BROWSE MEDIA (WebSocket) =====
        elif tool_name == "browse_media":
            content_id = tool_input.get("media_content_id", "")
            content_type = tool_input.get("media_content_type", "music")
            params = {"media_content_type": content_type}
            if content_id:
                params["media_content_id"] = content_id
            result = call_ha_websocket("media_player/browse_media", **params)
            if result.get("success"):
                media = result.get("result", {})
                children = media.get("children", [])
                summary = []
                for c in children[:50]:
                    summary.append({
                        "title": c.get("title", ""),
                        "media_content_id": c.get("media_content_id", ""),
                        "media_content_type": c.get("media_content_type", ""),
                        "media_class": c.get("media_class", ""),
                        "can_expand": c.get("can_expand", False),
                        "can_play": c.get("can_play", False)
                    })
                return json.dumps({"title": media.get("title", "Media"), "children": summary,
                                   "count": len(children)}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Browse media failed: {error_msg}"}, default=str)

        # ===== DASHBOARD READ/EDIT =====
        elif tool_name == "get_dashboard_config":
            url_path = tool_input.get("url_path", None)
            params = {}
            if url_path and url_path != "lovelace":
                params["url_path"] = url_path
            result = call_ha_websocket("lovelace/config", **params)
            if result.get("success"):
                config = result.get("result", {})
                views = config.get("views", [])
                # Summarize to avoid huge response
                summary_views = []
                for v in views:
                    cards = v.get("cards", [])
                    card_summary = []
                    for c in cards:
                        card_info = {"type": c.get("type", "unknown")}
                        if c.get("title"):
                            card_info["title"] = c["title"]
                        if c.get("entity"):
                            card_info["entity"] = c["entity"]
                        if c.get("entities"):
                            card_info["entities"] = c["entities"][:10]
                        # Include full card for custom types
                        if c.get("type", "").startswith("custom:"):
                            card_info = c
                        card_summary.append(card_info)
                    summary_views.append({
                        "title": v.get("title", ""),
                        "path": v.get("path", ""),
                        "icon": v.get("icon", ""),
                        "cards_count": len(cards),
                        "cards": card_summary
                    })
                return json.dumps({"url_path": url_path or "lovelace",
                                   "views": summary_views, "views_count": len(views),
                                   "full_config": config}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to get dashboard config: {error_msg}"}, default=str)

        elif tool_name == "update_dashboard":
            url_path = tool_input.get("url_path", None)
            views = tool_input.get("views", [])
            # Auto-snapshot: save current dashboard config before modifying
            try:
                snap_params = {}
                if url_path and url_path != "lovelace":
                    snap_params["url_path"] = url_path
                old_config = call_ha_websocket("lovelace/config", **snap_params)
                if old_config.get("success"):
                    snap_file = f"_dashboard_snapshot_{url_path or 'lovelace'}.json"
                    snap_path = os.path.join(SNAPSHOTS_DIR, datetime.now().strftime("%Y%m%d_%H%M%S") + snap_file)
                    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
                    with open(snap_path, "w") as sf:
                        json.dump({"url_path": url_path or "lovelace", "config": old_config.get("result", {})}, sf)
                    logger.info(f"Dashboard snapshot saved: {snap_path}")
            except Exception as e:
                logger.warning(f"Could not snapshot dashboard before update: {e}")
            params = {"config": {"views": views}}
            if url_path and url_path != "lovelace":
                params["url_path"] = url_path
            result = call_ha_websocket("lovelace/config/save", **params)
            if result.get("success"):
                return json.dumps({"status": "success",
                                   "message": f"Dashboard '{url_path or 'lovelace'}' updated with {len(views)} view(s). A backup snapshot was saved.",
                                   "views_count": len(views)}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to update dashboard: {error_msg}"}, default=str)

        elif tool_name == "get_frontend_resources":
            result = call_ha_websocket("lovelace/resources")
            if result.get("success"):
                resources = result.get("result", [])
                summary = []
                for r in resources:
                    url = r.get("url", "")
                    # Extract card name from URL
                    name = url.split("/")[-1].split(".")[0].split("?")[0] if url else ""
                    summary.append({
                        "id": r.get("id"),
                        "url": url,
                        "type": r.get("type", "module"),
                        "name": name
                    })
                # Check for common custom cards
                all_urls = " ".join([r.get("url", "") for r in resources]).lower()
                detected = []
                for card_name in ["card-mod", "bubble-card", "mushroom", "mini-graph", "mini-media-player",
                                  "button-card", "layout-card", "stack-in-card", "slider-entity-row",
                                  "auto-entities", "decluttering-card", "apexcharts-card", "swipe-card",
                                  "tabbed-card", "vertical-stack-in-card", "atomic-calendar"]:
                    if card_name in all_urls:
                        detected.append(card_name)
                return json.dumps({"resources": summary, "count": len(summary),
                                   "detected_custom_cards": detected}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to get resources: {error_msg}"}, default=str)

        # ===== CONFIG FILE OPERATIONS =====
        elif tool_name == "read_config_file":
            filename = tool_input.get("filename", "")
            # Security: prevent path traversal
            if ".." in filename or filename.startswith("/"):
                return json.dumps({"error": "Invalid filename. Use relative paths only (e.g. 'configuration.yaml')."})
            filepath = os.path.join(HA_CONFIG_DIR, filename)
            if not os.path.isfile(filepath):
                return json.dumps({"error": f"File '{filename}' not found in HA config directory."})
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # Truncate very large files
                if len(content) > 15000:
                    content = content[:15000] + f"\n\n... [TRUNCATED - file is {len(content)} chars total]"
                return json.dumps({"filename": filename, "content": content,
                                   "size": os.path.getsize(filepath)}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to read '{filename}': {str(e)}"})

        elif tool_name == "write_config_file":
            filename = tool_input.get("filename", "")
            content = tool_input.get("content", "")
            if ".." in filename or filename.startswith("/"):
                return json.dumps({"error": "Invalid filename. Use relative paths only."})
            if not filename:
                return json.dumps({"error": "filename is required."})
            filepath = os.path.join(HA_CONFIG_DIR, filename)
            # Auto-create snapshot before writing
            snapshot = create_snapshot(filename)
            try:
                # Create parent directories if needed
                os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else filepath, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                msg = f"File '{filename}' saved successfully."
                if snapshot.get("snapshot_id"):
                    msg += f" Backup snapshot created: {snapshot['snapshot_id']}"
                return json.dumps({"status": "success", "message": msg, "snapshot": snapshot,
                                   "tip": "Call check_config to validate the configuration."}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to write '{filename}': {str(e)}", "snapshot": snapshot})

        elif tool_name == "check_config":
            try:
                ha_token = get_ha_token()
                resp = requests.post(
                    f"{HA_URL}/api/config/core/check_config",
                    headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
                    timeout=30
                )
                result = resp.json()
                errors = result.get("errors", None)
                valid = result.get("result", "") == "valid"
                if valid:
                    return json.dumps({"status": "valid", "message": "Configuration is valid! You can reload or restart HA."}, ensure_ascii=False)
                return json.dumps({"status": "invalid", "errors": errors,
                                   "message": "Configuration has errors! Fix them or restore from snapshot."}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Config check failed: {str(e)}"})

        elif tool_name == "list_config_files":
            subpath = tool_input.get("path", "")
            if ".." in subpath:
                return json.dumps({"error": "Invalid path."})
            dirpath = os.path.join(HA_CONFIG_DIR, subpath) if subpath else HA_CONFIG_DIR
            if not os.path.isdir(dirpath):
                return json.dumps({"error": f"Directory '{subpath}' not found."})
            entries = []
            try:
                for entry in sorted(os.listdir(dirpath)):
                    full = os.path.join(dirpath, entry)
                    rel = os.path.join(subpath, entry) if subpath else entry
                    if os.path.isdir(full):
                        entries.append({"name": entry, "type": "directory", "path": rel})
                    else:
                        entries.append({"name": entry, "type": "file", "path": rel,
                                       "size": os.path.getsize(full)})
                # Filter out hidden/system and very large dirs
                entries = [e for e in entries if not e["name"].startswith(".")][:100]
                return json.dumps({"path": subpath or "/", "entries": entries,
                                   "count": len(entries)}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to list '{subpath}': {str(e)}"})

        # ===== SNAPSHOT MANAGEMENT =====
        elif tool_name == "list_snapshots":
            if not os.path.isdir(SNAPSHOTS_DIR):
                return json.dumps({"snapshots": [], "count": 0})
            snapshots = []
            for f in sorted(os.listdir(SNAPSHOTS_DIR)):
                if f.endswith(".meta"):
                    continue
                meta_path = os.path.join(SNAPSHOTS_DIR, f + ".meta")
                if os.path.isfile(meta_path):
                    with open(meta_path, "r") as mf:
                        meta = json.load(mf)
                    snapshots.append(meta)
                else:
                    snapshots.append({"snapshot_id": f, "original_file": f.split("_", 2)[-1].replace("__", "/")})
            return json.dumps({"snapshots": snapshots, "count": len(snapshots)}, ensure_ascii=False, default=str)

        elif tool_name == "restore_snapshot":
            snapshot_id = tool_input.get("snapshot_id", "")
            snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_id)
            meta_path = snapshot_path + ".meta"
            if not os.path.isfile(snapshot_path):
                return json.dumps({"error": f"Snapshot '{snapshot_id}' not found. Use list_snapshots."})
            # Read metadata to find original file
            original_file = ""
            if os.path.isfile(meta_path):
                with open(meta_path, "r") as mf:
                    meta = json.load(mf)
                original_file = meta.get("original_file", "")
            else:
                # Try to reconstruct from snapshot name
                parts = snapshot_id.split("_", 2)
                if len(parts) >= 3:
                    original_file = parts[2].replace("__", "/")
            if not original_file:
                return json.dumps({"error": "Cannot determine original file from snapshot."})
            # Create a snapshot of current state before restoring
            create_snapshot(original_file)
            # Restore
            import shutil
            dest = os.path.join(HA_CONFIG_DIR, original_file)
            shutil.copy2(snapshot_path, dest)
            return json.dumps({"status": "success",
                               "message": f"Restored '{original_file}' from snapshot '{snapshot_id}'. A new snapshot of the overwritten file was created.",
                               "restored_file": original_file}, ensure_ascii=False, default=str)

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
5. **Advanced statistics** - Get min/max/mean/sum statistics for sensors over time periods
6. **Scenes & scripts** - List, activate scenes, run scripts, create new scripts
7. **Areas/rooms** - List, create, rename, delete areas. Assign entities to areas
8. **Devices & entity registry** - List devices, rename entities, enable/disable entities, assign to areas
9. **Create automations** - Build new automations with triggers, conditions, and actions
10. **List & trigger automations** - See and run existing automations
11. **Delete automations/scripts/dashboards** - Remove unwanted configurations
12. **Notifications** - Send persistent notifications or push to mobile devices
13. **Discover services & events** - See all available HA services and event types
14. **Create & modify dashboards** - Create NEW dashboards or modify EXISTING ones with any card type
15. **Check custom cards** - Verify which HACS custom cards are installed (card-mod, bubble-card, mushroom, etc.)
16. **Shopping list** - View, add, and complete shopping list items
17. **Backup** - Create full Home Assistant backups
18. **Browse media** - Browse media content from players (music, photos, etc.)
19. **Read/write config files** - Read and edit configuration.yaml, automations.yaml, YAML dashboards, packages, etc.
20. **Validate config** - Check HA configuration for errors after editing
21. **Snapshots** - Automatic backups before every file change, with restore capability

## Configuration File Management
- Use **list_config_files** to explore the HA config directory
- Use **read_config_file** to read any YAML/config file (including YAML-mode dashboards like ui-lovelace.yaml)
- Use **write_config_file** to modify files (auto-creates a snapshot before writing)
- Use **check_config** to validate after editing configuration.yaml
- Use **list_snapshots** and **restore_snapshot** to manage/restore backups

IMPORTANT for config editing:
1. ALWAYS read the file first with read_config_file
2. Make targeted changes (don't rewrite everything unless necessary)
3. After writing configuration.yaml, ALWAYS call check_config to validate
4. If validation fails, use restore_snapshot to undo changes
5. Snapshots are created automatically before every write - inform the user about this safety net

## Dashboard Management
- Use **get_dashboards** to list all dashboards
- Use **get_dashboard_config** to read an existing dashboard's full configuration
- Use **update_dashboard** to modify an existing dashboard (replaces all views)
- Use **create_dashboard** to create a brand new dashboard
- Use **get_frontend_resources** to check which custom cards (HACS) are installed
- Use **delete_dashboard** to remove a dashboard

IMPORTANT: When modifying a dashboard, ALWAYS:
1. First call get_dashboard_config to read the current config
2. Modify the views/cards as needed
3. Save with update_dashboard passing the complete views array

### ENTITY RULE (CRITICAL)
- NEVER invent or guess entity IDs. ALWAYS use search_entities first to find REAL entity IDs.
- Only use entity IDs that appear in the search results.
- If a search returns no results for a category, DO NOT include cards for that category.
- Example: if search_entities("light") returns only light.soggiorno and light.camera, use ONLY those two.

### Dashboard Layout (CRITICAL - never put cards in a flat vertical list!)
Always create visually appealing layouts using grids and stacks:

**Use grid cards to arrange items in columns:**
{"type": "grid", "columns": 2, "square": false, "cards": [card1, card2, card3, card4]}

**Use horizontal-stack for side-by-side cards:**
{"type": "horizontal-stack", "cards": [card1, card2]}

**Use vertical-stack to group related cards:**
{"type": "vertical-stack", "cards": [headerCard, contentCard]}

**Best layout practices:**
- Use a grid with 2-3 columns for button/entity cards
- Group related sensors in horizontal-stack
- Use vertical-stack with a markdown header + grid of cards for sections
- Example section structure:
  {"type": "vertical-stack", "cards": [
    {"type": "markdown", "content": "## 💡 Luci"},
    {"type": "grid", "columns": 3, "square": false, "cards": [
      {"type": "button", "entity": "light.soggiorno", "name": "Soggiorno", "icon": "mdi:sofa", "show_state": true},
      {"type": "button", "entity": "light.camera", "name": "Camera", "icon": "mdi:bed", "show_state": true}
    ]}
  ]}

### Standard Lovelace card types:
- entities: {"type": "entities", "title": "Lights", "entities": ["light.living_room"]}
- gauge: {"type": "gauge", "entity": "sensor.temperature"}
- history-graph: {"type": "history-graph", "entities": [{"entity": "sensor.temp"}], "hours_to_show": 24}
- thermostat: {"type": "thermostat", "entity": "climate.living_room"}
- button: {"type": "button", "entity": "switch.outlet", "name": "Toggle"}
- markdown: {"type": "markdown", "content": "# Title"}

### Custom cards (check availability with get_frontend_resources first!):

**card-mod** - Style any card with CSS:
{"type": "entities", "entities": ["light.room"], "card_mod": {"style": "ha-card { background: rgba(0,0,0,0.3); border-radius: 16px; }"}}

**bubble-card** - Modern UI cards:
{"type": "custom:bubble-card", "card_type": "button", "entity": "light.room", "name": "Light", "icon": "mdi:lightbulb", "button_type": "switch"}
{"type": "custom:bubble-card", "card_type": "pop-up", "hash": "#room", "name": "Living Room", "icon": "mdi:sofa"}
{"type": "custom:bubble-card", "card_type": "separator", "name": "Section", "icon": "mdi:home"}

**mushroom cards**:
{"type": "custom:mushroom-entity-card", "entity": "light.room", "fill_container": true}
{"type": "custom:mushroom-climate-card", "entity": "climate.room"}

**button-card** - Highly customizable buttons:
{"type": "custom:button-card", "entity": "light.room", "name": "Light", "icon": "mdi:lightbulb", "show_state": true,
 "styles": {"card": [{"background-color": "rgba(0,0,0,0.3)"}]}}

**mini-graph-card** - Beautiful sensor graphs:
{"type": "custom:mini-graph-card", "entities": ["sensor.temperature"], "hours_to_show": 24, "line_color": "#e74c3c"}

Before using any custom: card type, ALWAYS call get_frontend_resources to verify it's installed.
If the user wants a custom card that is not installed, inform them and suggest installing it via HACS.

## Automations
When creating automations, use proper Home Assistant formats:
- State trigger: {"platform": "state", "entity_id": "binary_sensor.motion", "to": "on"}
- Time trigger: {"platform": "time", "at": "07:00:00"}
- Sun trigger: {"platform": "sun", "event": "sunset", "offset": "-00:30:00"}
- Service action: {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 255}}

When managing areas/rooms, use manage_areas. To assign an entity to a room, use manage_entity with the area_id.
For advanced sensor analytics (averages, peaks, trends), use get_statistics instead of get_history.
When a user asks about specific devices or addons, use search_entities to find them by keyword.
Use get_history for recent state changes, get_statistics for aggregated data over longer periods.
Use get_areas when the user refers to rooms.
To delete resources, use delete_automation, delete_script, or delete_dashboard.

## CRITICAL BEHAVIOR RULES
- When the user asks you to CREATE or MODIFY something (dashboard, automation, script, config), DO IT IMMEDIATELY.
- NEVER just describe what you plan to do. Execute ALL necessary tool calls in sequence and complete the task fully.
- Only respond with the final result AFTER the task is complete.
- If a task requires multiple tool calls, keep calling tools until the task is done. Do not stop halfway to explain your plan.

## SHOW YOUR CHANGES (CRITICAL)
When you modify an automation, script, configuration, or any YAML file, ALWAYS show the user exactly what you changed.
In your final response, include:
1. A brief summary of what you did
2. The relevant YAML section BEFORE (old) and AFTER (new) using code blocks, for example:

**Prima (old):**
```yaml
condition: []
```

**Dopo (new):**
```yaml
condition:
  - condition: not
    conditions:
      - condition: template
        value_template: "{{ 'Inter' in trigger.to_state.state }}"
```

This helps the user understand and verify the changes. Keep the diff focused on what changed, not the entire file.

## EFFICIENCY RULES (ABSOLUTELY CRITICAL - MAXIMUM 1-2 tool calls per task)
- EVERY extra tool call wastes 5-20 seconds. Users WILL experience errors and timeouts with too many calls.
- When context is pre-loaded in the user message, ALL that data is already available. NEVER re-fetch it.
- PRE-LOADED DATA = do NOT call: get_automations, get_scripts, get_dashboards, read_config_file, list_config_files, search_entities, get_entity_state for data already present.
- For modifying automations: call update_automation ONCE with automation_id + changes. That's IT. ONE call total.
- For modifying scripts: call update_script ONCE with script_id + changes. That's IT. ONE call total.
- After update_automation or update_script succeeds: STOP. Show the diff to the user. Do NOT call any verification tools.
- NEVER verify changes by calling get_automations or read_config_file after an update - the tool already returns old/new YAML.
- The MAXIMUM number of tool calls for ANY modification task is 2. If you've made 2 calls, you MUST respond.
- For other config editing: read_config_file → write_config_file → check_config (3 calls max).

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


# ---- LOCAL INTENT DETECTION ----
# Analyze user message LOCALLY to determine intent and select only relevant tools/prompt.
# This dramatically reduces tokens sent to the AI API.

# Tool sets by intent category
INTENT_TOOL_SETS = {
    "modify_automation": ["update_automation"],
    "modify_script": ["update_script"],
    "create_automation": ["create_automation", "search_entities"],
    "create_script": ["create_script", "search_entities"],
    "create_dashboard": ["create_dashboard", "search_entities", "get_frontend_resources"],
    "modify_dashboard": ["get_dashboard_config", "update_dashboard", "get_frontend_resources"],
    "control_device": ["call_service", "search_entities", "get_entity_state"],
    "query_state": ["get_entities", "get_entity_state", "search_entities"],
    "query_history": ["get_history", "get_statistics", "search_entities"],
    "delete": ["delete_automation", "delete_script", "delete_dashboard"],
    "config_edit": ["read_config_file", "write_config_file", "check_config", "list_config_files",
                     "list_snapshots", "restore_snapshot"],
    "areas": ["manage_areas", "manage_entity", "get_areas", "get_devices"],
    "notifications": ["send_notification", "search_entities"],
}

# Compact focused prompts by intent
INTENT_PROMPTS = {
    "modify_automation": """You are a Home Assistant automation editor. The user wants to modify an automation.
The automation config is provided in the DATI section of the user's message.
RULES:
1. FIRST, briefly confirm which automation you found: "Ho trovato l'automazione: [NAME] (id: [ID])"
2. Then call update_automation ONCE with only the changed fields.
3. Show a before/after diff of the changes.
- Respond in the user's language. Be concise.
- NEVER call get_automations or read_config_file — the data is already provided.
- If the automation in DATI doesn't match what the user asked for, tell them and ask for clarification. Do NOT modify the wrong automation.""",

    "modify_script": """You are a Home Assistant script editor. The user wants to modify a script.
The script config is provided in the DATI section.
RULES:
1. FIRST, briefly confirm which script you found: "Ho trovato lo script: [NAME] (id: [ID])"
2. Then call update_script ONCE with only the changed fields.
3. Show a before/after diff.
- Respond in the user's language. Be concise.
- NEVER call get_scripts or read_config_file — the data is already provided.
- If the script doesn't match what the user asked for, tell them. Do NOT modify the wrong one.""",

    "control_device": """You are a Home Assistant device controller. Help the user control their devices.
Use search_entities to find entities if needed, then call_service to control them.
Respond in the user's language. Be concise. Maximum 2 tool calls.""",

    "query_state": """You are a Home Assistant status assistant. Help the user check device states.
Use search_entities or get_entity_state to find and report states.
Respond in the user's language. Be concise.""",
}


def detect_intent(user_message: str, smart_context: str) -> dict:
    """Detect user intent locally from the message and available context.
    Returns: {"intent": str, "tools": list[str], "prompt": str|None, "specific_target": bool}
    If intent is clear + specific target found, use focused mode (fewer tools, shorter prompt).
    Otherwise fall back to full mode."""
    msg = user_message.lower()
    
    # --- MODIFY AUTOMATION (most common case) ---
    modify_auto_kw = ["modifica", "cambia", "aggiorna", "escludi", "aggiungi", "rimuovi", "togli",
                       "modific", "cambiar", "aggiornar", "escluder", "aggiung", "rimuov",
                       "exclude", "change", "modify", "update", "remove", "add", "fix"]
    auto_kw = ["automazione", "automation", "automazion"]
    has_modify = any(k in msg for k in modify_auto_kw)
    has_auto = any(k in msg for k in auto_kw)
    # Also detect if smart context found a specific automation
    has_specific_auto = "## AUTOMAZIONE" in smart_context if smart_context else False
    
    if has_modify and (has_auto or has_specific_auto):
        return {"intent": "modify_automation", "tools": INTENT_TOOL_SETS["modify_automation"],
                "prompt": INTENT_PROMPTS["modify_automation"], "specific_target": has_specific_auto}
    
    # --- MODIFY SCRIPT ---
    script_kw = ["script", "routine", "sequenza"]
    has_script = any(k in msg for k in script_kw)
    has_specific_script = "## SCRIPT" in smart_context if smart_context else False
    
    if has_modify and (has_script or has_specific_script):
        return {"intent": "modify_script", "tools": INTENT_TOOL_SETS["modify_script"],
                "prompt": INTENT_PROMPTS["modify_script"], "specific_target": has_specific_script}
    
    # --- CREATE AUTOMATION ---
    create_kw = ["crea", "creare", "nuov", "create", "new", "aggiungi nuova"]
    has_create = any(k in msg for k in create_kw)
    if has_create and has_auto:
        return {"intent": "create_automation", "tools": INTENT_TOOL_SETS["create_automation"],
                "prompt": None, "specific_target": False}
    
    # --- CREATE SCRIPT ---
    if has_create and has_script:
        return {"intent": "create_script", "tools": INTENT_TOOL_SETS["create_script"],
                "prompt": None, "specific_target": False}
    
    # --- DASHBOARD ---
    dash_kw = ["dashboard", "lovelace", "scheda", "card", "pannello"]
    has_dash = any(k in msg for k in dash_kw)
    if has_dash and has_create:
        return {"intent": "create_dashboard", "tools": INTENT_TOOL_SETS["create_dashboard"],
                "prompt": None, "specific_target": False}
    if has_dash and has_modify:
        return {"intent": "modify_dashboard", "tools": INTENT_TOOL_SETS["modify_dashboard"],
                "prompt": None, "specific_target": False}
    
    # --- DEVICE CONTROL ---
    control_kw = ["accendi", "spegni", "accend", "spegn", "turn on", "turn off",
                  "imposta", "alza", "abbassa", "apri", "chiudi", "attiva", "disattiva"]
    if any(k in msg for k in control_kw):
        return {"intent": "control_device", "tools": INTENT_TOOL_SETS["control_device"],
                "prompt": INTENT_PROMPTS["control_device"], "specific_target": False}
    
    # --- QUERY STATE ---
    query_kw = ["stato", "status", "come sta", "è acceso", "è spento", "quanto", "temperatura",
                "valore", "che ore", "quanti gradi"]
    if any(k in msg for k in query_kw):
        return {"intent": "query_state", "tools": INTENT_TOOL_SETS["query_state"],
                "prompt": INTENT_PROMPTS["query_state"], "specific_target": False}
    
    # --- HISTORY ---
    history_kw = ["storico", "storia", "history", "ieri", "yesterday", "trend", "andamento",
                  "media", "massimo", "minimo", "statistich"]
    if any(k in msg for k in history_kw):
        return {"intent": "query_history", "tools": INTENT_TOOL_SETS["query_history"],
                "prompt": None, "specific_target": False}
    
    # --- DELETE ---
    delete_kw = ["elimina", "cancella", "rimuovi", "delete", "remove"]
    if any(k in msg for k in delete_kw) and (has_auto or has_script or has_dash):
        return {"intent": "delete", "tools": INTENT_TOOL_SETS["delete"],
                "prompt": None, "specific_target": False}
    
    # --- CONFIG EDIT ---
    config_kw = ["configuration.yaml", "config", "yaml", "configurazione", "snapshot"]
    if any(k in msg for k in config_kw):
        return {"intent": "config_edit", "tools": INTENT_TOOL_SETS["config_edit"],
                "prompt": None, "specific_target": False}
    
    # --- GENERIC (full mode) ---
    return {"intent": "generic", "tools": None, "prompt": None, "specific_target": False}


def get_tools_for_intent(intent_info: dict, provider: str = "anthropic") -> list:
    """Get tool definitions filtered by intent. Returns full tools if intent is generic."""
    tool_names = intent_info.get("tools")
    if tool_names is None:
        # Generic: return all tools
        if provider == "anthropic":
            return get_anthropic_tools()
        elif provider in ("openai", "github"):
            return get_openai_tools_for_provider()
        return get_anthropic_tools()
    
    # Filter to only relevant tools
    filtered = [t for t in HA_TOOLS_DESCRIPTION if t["name"] in tool_names]
    
    if provider == "anthropic":
        return [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in filtered]
    elif provider in ("openai", "github"):
        return [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in filtered]
    return [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in filtered]


def get_prompt_for_intent(intent_info: dict) -> str:
    """Get system prompt for intent. Returns focused prompt if available, else full."""
    prompt = intent_info.get("prompt")
    if prompt:
        return prompt
    return get_system_prompt()


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
        max_tokens=8192,
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
            max_tokens=8192,
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


def sanitize_messages_for_provider(messages: List[Dict]) -> List[Dict]:
    """Remove messages incompatible with the current provider.
    Also truncates old messages to reduce token count (critical for rate limits)."""
    clean = []
    for m in messages:
        role = m.get("role", "")
        # Skip tool-role messages for Anthropic (it uses tool_result inside user messages)
        if AI_PROVIDER == "anthropic" and role == "tool":
            continue
        # Skip assistant messages with tool_calls format (OpenAI format) for Anthropic
        if AI_PROVIDER == "anthropic" and role == "assistant" and m.get("tool_calls"):
            continue
        # Skip Anthropic-format tool_result messages for OpenAI/GitHub
        if AI_PROVIDER in ("openai", "github") and role == "user" and isinstance(m.get("content"), list):
            if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in m.get("content", [])):
                continue
        # Only keep simple user/assistant text messages
        if role in ("user", "assistant"):
            content = m.get("content", "")
            if isinstance(content, str) and content:
                clean.append({"role": role, "content": content})
    
    # Limit total messages: keep only last 10
    if len(clean) > 10:
        clean = clean[-10:]
    
    # Truncate OLD messages to save tokens (keep last 2 messages full)
    MAX_OLD_MSG = 1500
    for i in range(len(clean) - 2):
        content = clean[i].get("content", "")
        # Strip previously injected smart context from old messages
        if "\n\n---\n\u26a0\ufe0f **CONTESTO PRE-CARICATO" in content:
            # Keep only the user's original message (before the smart context separator)
            content = content.split("\n\n---\n\u26a0\ufe0f **CONTESTO PRE-CARICATO")[0]
        if len(content) > MAX_OLD_MSG:
            content = content[:MAX_OLD_MSG] + "... [old message truncated]"
        clean[i] = {"role": clean[i]["role"], "content": content}
    
    return clean


def chat_with_ai(user_message: str, session_id: str = "default") -> str:
    """Send a message to the configured AI provider with HA tools."""
    if not ai_client:
        provider_name = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("name", AI_PROVIDER)
        return f"\u26a0\ufe0f Chiave API per {provider_name} non configurata. Impostala nelle impostazioni dell'add-on."

    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({"role": "user", "content": user_message})
    messages = sanitize_messages_for_provider(conversations[session_id][-20:])

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


def stream_chat_openai(messages, intent_info=None):
    """Stream chat for OpenAI/GitHub with real token streaming. Yields SSE event dicts.
    Uses intent_info to select focused tools and prompt when available."""
    trimmed = trim_messages(messages)
    
    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools"):
        system_prompt = get_prompt_for_intent(intent_info)
        tools = get_tools_for_intent(intent_info, AI_PROVIDER)
        logger.info(f"OpenAI focused mode: {intent_info['intent']} ({len(tools)} tools)")
    else:
        system_prompt = get_system_prompt()
        tools = get_openai_tools_for_provider()
    
    max_tok = 4000 if AI_PROVIDER == "github" else 4096
    full_text = ""
    max_rounds = 5
    tools_called_this_session = set()

    for round_num in range(max_rounds):
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
            # No tools - stream the final text now
            full_text = accumulated
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                chunk = full_text[i:i+4]
                yield {"type": "token", "content": chunk}
            break

        # Build assistant message with tool calls
        logger.info(f"Round {round_num+1}: {len(tool_calls_map)} tool(s), skipping intermediate text")
        tc_list = []
        for idx in sorted(tool_calls_map.keys()):
            tc = tool_calls_map[idx]
            tc_list.append({
                "id": tc["id"], "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]}
            })

        messages.append({"role": "assistant", "content": accumulated, "tool_calls": tc_list})

        tool_call_results = {}  # Map tc_id -> (fn_name, result)
        for tc in tc_list:
            fn_name = tc["function"]["name"]
            # Block redundant read-only tool calls
            redundant_read_tools = {"get_automations", "get_scripts", "get_dashboards",
                                    "get_dashboard_config", "read_config_file",
                                    "list_config_files", "get_frontend_resources",
                                    "search_entities", "get_entity_state"}
            if fn_name in redundant_read_tools and fn_name in tools_called_this_session:
                logger.warning(f"Blocked redundant tool call: {fn_name}")
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                 "content": json.dumps({"note": f"Skipped: {fn_name} already called. Use existing data. Respond NOW."})})
                continue
            yield {"type": "tool", "name": fn_name, "description": get_tool_description(fn_name)}
            args = json.loads(tc["function"]["arguments"])
            result = execute_tool(fn_name, args)
            tools_called_this_session.add(fn_name)
            # Truncate large results to prevent token overflow
            max_len = 3000 if AI_PROVIDER == "github" else 8000
            if len(result) > max_len:
                result = result[:max_len] + '\n... [TRUNCATED - ' + str(len(result)) + ' chars total]'
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            tool_call_results[tc["id"]] = (fn_name, result)

        # AUTO-STOP: If a write tool succeeded, format response directly
        WRITE_TOOLS = {"update_automation", "update_script", "update_dashboard_card",
                       "create_automation", "create_script", "create_dashboard", "update_dashboard"}
        auto_stop = False
        for tc_id, (fn_name, result) in tool_call_results.items():
            if fn_name in WRITE_TOOLS:
                try:
                    rdata = json.loads(result)
                    if rdata.get("status") == "success":
                        auto_stop = True
                        full_text = _format_write_tool_response(fn_name, rdata)
                        break
                except (json.JSONDecodeError, KeyError):
                    pass

        if auto_stop:
            logger.info(f"Auto-stop: write tool succeeded, skipping further API calls")
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                yield {"type": "token", "content": full_text[i:i+4]}
            break

    messages.append({"role": "assistant", "content": full_text})
    yield {"type": "done", "full_text": full_text}


def stream_chat_anthropic(messages, intent_info=None):
    """Stream chat for Anthropic with real token streaming and tool event emission.
    Uses intent_info to select focused tools and prompt when available."""
    import anthropic

    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools"):
        focused_prompt = get_prompt_for_intent(intent_info)
        focused_tools = get_tools_for_intent(intent_info, "anthropic")
        logger.info(f"Anthropic focused mode: {intent_info['intent']} ({len(focused_tools)} tools)")
    else:
        focused_prompt = SYSTEM_PROMPT
        focused_tools = get_anthropic_tools()

    full_text = ""
    max_rounds = 5  # Strict limit: most tasks need 1-2 rounds max
    tools_called_this_session = set()  # Track tools already called to detect redundancy

    for round_num in range(max_rounds):
        # Check abort flag
        if abort_streams.get("default"):
            logger.info("Stream aborted by user")
            yield {"type": "error", "message": "Interrotto dall'utente."}
            abort_streams["default"] = False
            break
        # Rate-limit prevention: delay between API calls (not on first round)
        if round_num > 0:
            delay = min(3 + round_num, 6)  # 4s, 5s, 6s, 6s...
            logger.info(f"Rate-limit prevention: waiting {delay}s before round {round_num+1}")
            yield {"type": "status", "message": f"Elaboro la risposta... (step {round_num+1})"}
            time.sleep(delay)
            if abort_streams.get("default"):
                logger.info("Stream aborted by user during delay")
                yield {"type": "error", "message": "Interrotto dall'utente."}
                abort_streams["default"] = False
                break

        content_parts = []
        tool_uses = []
        current_tool_id = None
        current_tool_name = None
        current_tool_input_json = ""

        try:
            with ai_client.messages.stream(
                model=get_active_model(),
                max_tokens=8192,
                system=focused_prompt,
                tools=focused_tools,
                messages=messages
            ) as stream:
                for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_id = event.content_block.id
                            current_tool_name = event.content_block.name
                            current_tool_input_json = ""
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            content_parts.append(event.delta.text)
                        elif event.delta.type == "input_json_delta":
                            current_tool_input_json += event.delta.partial_json
                    elif event.type == "content_block_stop":
                        if current_tool_name:
                            try:
                                tool_input = json.loads(current_tool_input_json) if current_tool_input_json else {}
                            except json.JSONDecodeError:
                                tool_input = {}
                            tool_uses.append({
                                "id": current_tool_id,
                                "name": current_tool_name,
                                "input": tool_input
                            })
                            current_tool_name = None
                            current_tool_id = None
                            current_tool_input_json = ""

                final_message = stream.get_final_message()
        except Exception as api_err:
            error_msg = str(api_err)
            if "429" in error_msg or "rate" in error_msg.lower():
                logger.warning(f"Rate limit hit at round {round_num+1}: {error_msg}")
                yield {"type": "status", "message": "Rate limit raggiunto, attendo..."}
                time.sleep(10)  # Wait and retry this round
                continue
            else:
                raise

        accumulated_text = "".join(content_parts)

        if not tool_uses:
            # No tools - this is the final response. Stream the text now.
            full_text = accumulated_text
            # Yield a clear signal to reset any previous tool badges
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                chunk = full_text[i:i+4]
                yield {"type": "token", "content": chunk}
            break

        # Tools found - DON'T stream intermediate text, just show tool badges
        logger.info(f"Round {round_num+1}: {len(tool_uses)} tool(s), skipping intermediate text")
        assistant_content = final_message.content
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        redundant_blocked = 0
        for tool in tool_uses:
            tool_key = tool['name']
            # Block redundant calls: if a read-only tool was already called, skip it
            redundant_read_tools = {"get_automations", "get_scripts", "get_dashboards", 
                                    "get_dashboard_config", "read_config_file", 
                                    "list_config_files", "get_frontend_resources",
                                    "search_entities", "get_entity_state"}
            if tool_key in redundant_read_tools and tool_key in tools_called_this_session:
                logger.warning(f"Blocked redundant tool call: {tool_key} (already called this session)")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool["id"],
                    "content": json.dumps({"note": f"Skipped: {tool_key} already called. Use the data you already have. Respond to the user NOW."})
                })
                redundant_blocked += 1
                continue

            logger.info(f"Tool: {tool['name']}")
            yield {"type": "tool", "name": tool["name"], "description": get_tool_description(tool["name"])}
            result = execute_tool(tool["name"], tool["input"])
            tools_called_this_session.add(tool_key)
            # Truncate large tool results to prevent token overflow
            if len(result) > 8000:
                result = result[:8000] + '\n... [TRUNCATED to save tokens - ' + str(len(result)) + ' chars total]'
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool["id"],
                "content": result
            })

        # If ALL tools were blocked as redundant, force stop
        if redundant_blocked == len(tool_uses):
            logger.info("All tool calls were redundant - forcing final response")
            if AI_PROVIDER in ("openai", "github"):
                for tr in tool_results:
                    messages.append({"role": "tool", "tool_call_id": tr["tool_use_id"], "content": tr["content"]})
            else:
                messages.append({"role": "user", "content": tool_results})
            messages.append({"role": "user", "content": [{"type": "text", "text": "You already have all the data needed. Respond to the user now with the results. Do not call any more tools."}]})
            continue

        # AUTO-STOP: If a write tool succeeded, format response directly — no more API calls needed
        WRITE_TOOLS = {"update_automation", "update_script", "update_dashboard_card",
                       "create_automation", "create_script", "create_dashboard", "update_dashboard"}
        auto_stop = False
        for tool in tool_uses:
            if tool["name"] in WRITE_TOOLS:
                for tr in tool_results:
                    if tr.get("tool_use_id") == tool["id"]:
                        try:
                            rdata = json.loads(tr["content"])
                            if rdata.get("status") == "success":
                                auto_stop = True
                                full_text = _format_write_tool_response(tool["name"], rdata)
                        except (json.JSONDecodeError, KeyError):
                            pass
                        break
            if auto_stop:
                break

        if auto_stop:
            logger.info(f"Auto-stop: write tool succeeded, skipping further API calls")
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                yield {"type": "token", "content": full_text[i:i+4]}
            break

        if AI_PROVIDER in ("openai", "github"):
            for tr in tool_results:
                messages.append({"role": "tool", "tool_call_id": tr["tool_use_id"], "content": tr["content"]})
        else:
            messages.append({"role": "user", "content": tool_results})
        # Loop back for next round

    messages.append({"role": "assistant", "content": full_text})
    yield {"type": "done", "full_text": full_text}


def _format_write_tool_response(tool_name: str, result_data: dict) -> str:
    """Format a human-readable response from a successful write tool result.
    This avoids needing another API round just to format the response."""
    parts = []
    
    msg = result_data.get("message", "")
    if msg:
        parts.append(f"✅ {msg}")
    else:
        parts.append("✅ Operazione completata con successo!")
    
    # Show diff for update tools
    old_yaml = result_data.get("old_yaml", "")
    new_yaml = result_data.get("new_yaml", "")
    
    if old_yaml and new_yaml:
        # Show compact diff: only changed sections
        old_lines = set(old_yaml.strip().splitlines())
        new_lines = set(new_yaml.strip().splitlines())
        removed = old_lines - new_lines
        added = new_lines - old_lines
        
        if removed or added:
            parts.append("\n**Modifiche:**")
            if removed:
                parts.append("\n**Prima (rimosso):**")
                parts.append(f"```yaml\n{chr(10).join(sorted(removed))}\n```")
            if added:
                parts.append("\n**Dopo (aggiunto):**")
                parts.append(f"```yaml\n{chr(10).join(sorted(added))}\n```")
        else:
            # Show full before/after if sets don't differ well (order changes)
            parts.append(f"\n**Prima:**\n```yaml\n{old_yaml[:2000]}\n```")
            parts.append(f"\n**Dopo:**\n```yaml\n{new_yaml[:2000]}\n```")
    
    tip = result_data.get("tip", "")
    if tip:
        parts.append(f"\nℹ️ {tip}")
    
    snapshot = result_data.get("snapshot", "")
    if snapshot and snapshot != "N/A (REST API)":
        parts.append(f"\n💾 Snapshot creato: `{snapshot}`")
    
    return "\n".join(parts)


def stream_chat_google(messages):
    """Stream chat for Google Gemini with tool events. Falls back to word-by-word for text."""
    from google.generativeai.types import content_types

    model = ai_client.GenerativeModel(
        model_name=get_active_model(),
        system_instruction=SYSTEM_PROMPT,
        tools=[get_gemini_tools()]
    )

    gemini_history = []
    for m in messages[:-1]:
        role = "model" if m["role"] == "assistant" else "user"
        if isinstance(m.get("content"), str):
            gemini_history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=gemini_history)
    last_message = messages[-1]["content"] if messages else ""
    response = chat.send_message(last_message)

    while response.candidates[0].content.parts:
        has_function_call = False
        function_responses = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                has_function_call = True
                fn = part.function_call
                logger.info(f"Tool: {fn.name}")
                yield {"type": "tool", "name": fn.name}
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
        # Rate-limit prevention for Google
        time.sleep(1)
        response = chat.send_message(function_responses)

    final_text = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "text") and part.text:
            final_text += part.text

    # Stream text word by word
    messages.append({"role": "assistant", "content": final_text})
    words = final_text.split(' ')
    for i, word in enumerate(words):
        yield {"type": "token", "content": word + (' ' if i < len(words) - 1 else '')}
    yield {"type": "done", "full_text": final_text}


MAX_SMART_CONTEXT = 10000  # Max chars to inject — keeps tokens under control

def build_smart_context(user_message: str) -> str:
    """Pre-load relevant context based on user's message intent.
    Works like VS Code: gathers all needed data BEFORE sending to AI,
    so Claude can respond with a single action instead of multiple tool rounds.
    IMPORTANT: Context must be compact to avoid rate limits."""
    msg_lower = user_message.lower()
    context_parts = []

    try:
        # --- AUTOMATION CONTEXT ---
        auto_keywords = ["automazione", "automation", "automazion", "trigger", "condizione", "condition"]
        if any(k in msg_lower for k in auto_keywords):
            import yaml
            # Get automation list
            states = get_all_states()
            autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
            auto_list = [{"entity_id": a.get("entity_id"),
                         "friendly_name": a.get("attributes", {}).get("friendly_name", ""),
                         "id": str(a.get("attributes", {}).get("id", "")),
                         "state": a.get("state")} for a in autos]

            # If user mentions a specific automation name, include its config
            # Try YAML first, then REST API for UI-created automations
            yaml_path = os.path.join(HA_CONFIG_DIR, "automations.yaml")
            found_in_yaml = False
            found_specific = False
            target_auto_id = None
            target_auto_alias = None
            
            # Find the BEST matching automation using scored matching
            # Score each automation by how many words match AND how specific the match is
            best_score = 0
            best_match = None
            
            # Words to IGNORE in matching (common Italian/English words that appear everywhere)
            STOP_WORDS = {"questa", "questo", "quella", "quello", "della", "delle", "dello",
                          "degli", "dalla", "dalle", "stessa", "stesso", "altra", "altro",
                          "prima", "dopo", "quando", "perché", "quindi", "anche", "ancora",
                          "molto", "troppo", "sempre", "dovremmo", "dovrebbe", "potrebbe",
                          "voglio", "vorrei", "puoi", "fammi", "invia", "manda", "notifica",
                          "about", "this", "that", "with", "from", "have", "which", "there",
                          "their", "would", "should", "could"}
            
            # Extract meaningful words from user message (>3 chars, not stop words)
            msg_words = [w for w in msg_lower.split() if len(w) > 3 and w not in STOP_WORDS]
            
            for a in auto_list:
                fname = str(a.get("friendly_name", "")).lower()
                if not fname:
                    continue
                
                score = 0
                
                # Check 1: Full name appears in message (highest priority)
                if fname in msg_lower:
                    score = 100
                
                # Check 2: Check if message contains quoted automation name
                # Look for text between quotes that matches
                import re
                quoted = re.findall(r'["\u201c\u201d]([^"\u201c\u201d]+)["\u201c\u201d]', user_message)
                for q in quoted:
                    if q.lower() in fname or fname in q.lower():
                        score = 90
                        break
                
                # Check 3: Score by matching meaningful words
                if score == 0:
                    fname_words = set(fname.lower().split())
                    matching_words = [w for w in msg_words if w in fname or any(w in fw for fw in fname_words)]
                    if matching_words:
                        # Weight by length of matched words (longer = more specific)
                        score = sum(len(w) for w in matching_words)
                        # Bonus if multiple words match
                        if len(matching_words) >= 2:
                            score += 10
                
                if score > best_score:
                    best_score = score
                    best_match = a
            
            if best_match and best_score >= 5:  # Minimum threshold
                target_auto_id = best_match.get("id", "")
                target_auto_alias = best_match.get("friendly_name", "")
                logger.info(f"Smart context: matched automation '{target_auto_alias}' (score: {best_score})")
            
            if target_auto_id:
                # Try YAML first
                if os.path.isfile(yaml_path):
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        all_automations = yaml.safe_load(f)
                    if isinstance(all_automations, list):
                        for auto in all_automations:
                            if str(auto.get("id", "")) == str(target_auto_id):
                                auto_yaml = yaml.dump(auto, default_flow_style=False, allow_unicode=True)
                                if len(auto_yaml) > 4000:
                                    auto_yaml = auto_yaml[:4000] + "\n... [TRUNCATED]"
                                context_parts.append(f"## AUTOMAZIONE: \"{auto.get('alias')}\" (id: {target_auto_id})\n```yaml\n{auto_yaml}```\nUsa update_automation con automation_id='{target_auto_id}'.")
                                found_in_yaml = True
                                found_specific = True
                                break
                
                # REST API fallback for UI-created automations
                if not found_in_yaml:
                    try:
                        rest_config = call_ha_api("GET", f"config/automation/config/{target_auto_id}")
                        if isinstance(rest_config, dict) and "error" not in rest_config:
                            auto_yaml = yaml.dump(rest_config, default_flow_style=False, allow_unicode=True)
                            if len(auto_yaml) > 4000:
                                auto_yaml = auto_yaml[:4000] + "\n... [TRUNCATED]"
                            context_parts.append(f"## AUTOMAZIONE (UI): \"{target_auto_alias}\" (id: {target_auto_id})\n```yaml\n{auto_yaml}```\nUsa update_automation con automation_id='{target_auto_id}'.")
                            found_specific = True
                    except Exception:
                        pass
            
            # Only include the full automations list if NO specific automation was found
            if not found_specific:
                # Compact list: only name + id, no entity_id/state (saves ~60% chars)
                compact_list = [{"name": a.get("friendly_name", ""), "id": a.get("id", "")} for a in auto_list if a.get("friendly_name")]
                list_json = json.dumps(compact_list, ensure_ascii=False, separators=(',', ':'))
                if len(list_json) > 3000:
                    list_json = list_json[:3000] + '...]'
                context_parts.append(f"## AUTOMAZIONI DISPONIBILI\n{list_json}")

        # --- SCRIPT CONTEXT ---
        script_keywords = ["script", "scena", "scenari", "routine", "sequenza"]
        if any(k in msg_lower for k in script_keywords):
            import yaml
            # Get script list from states
            states = get_all_states() if 'states' not in dir() else states
            script_entities = [{"entity_id": s.get("entity_id"),
                               "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                               "state": s.get("state")} for s in states if s.get("entity_id", "").startswith("script.")]
            if script_entities:
                context_parts.append(f"## SCRIPT DISPONIBILI\n{json.dumps(script_entities, ensure_ascii=False, indent=1)}")

            # If user mentions a specific script name, include its YAML
            yaml_path = os.path.join(HA_CONFIG_DIR, "scripts.yaml")
            if os.path.isfile(yaml_path):
                try:
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        all_scripts = yaml.safe_load(f)
                    if isinstance(all_scripts, dict):
                        for sid, sconfig in all_scripts.items():
                            alias = str(sconfig.get("alias", "")).lower() if isinstance(sconfig, dict) else ""
                            if alias and (alias in msg_lower or sid in msg_lower or any(word in alias for word in msg_lower.split() if len(word) > 4)):
                                script_yaml = yaml.dump({sid: sconfig}, default_flow_style=False, allow_unicode=True)
                                if len(script_yaml) > 6000:
                                    script_yaml = script_yaml[:6000] + "\n... [TRUNCATED]"
                                context_parts.append(f"## YAML SCRIPT TROVATO: \"{sconfig.get('alias', sid)}\" (id: {sid})\n```yaml\n{script_yaml}```\nPer modificarlo usa update_script con script_id='{sid}' e i campi da cambiare.")
                                break
                except Exception:
                    pass

        # --- DASHBOARD CONTEXT ---
        dash_keywords = ["dashboard", "lovelace", "scheda", "card", "pannello"]
        if any(k in msg_lower for k in dash_keywords):
            # Get dashboard list
            try:
                dashboards = call_ha_websocket("lovelace/dashboards/list")
                dash_list = dashboards.get("result", [])
                if dash_list:
                    summary = [{"id": d.get("id"), "title": d.get("title", ""), "url_path": d.get("url_path", "")} for d in dash_list]
                    context_parts.append(f"## DASHBOARD DISPONIBILI\n{json.dumps(summary, ensure_ascii=False, indent=1)}")

                    # If user mentions a specific dashboard name, pre-load its config
                    for dash in dash_list:
                        dash_title = str(dash.get("title", "")).lower()
                        dash_url = str(dash.get("url_path", "")).lower()
                        if dash_title and (dash_title in msg_lower or dash_url in msg_lower or any(word in dash_title for word in msg_lower.split() if len(word) > 4)):
                            try:
                                dparams = {}
                                if dash_url and dash_url != "lovelace":
                                    dparams["url_path"] = dash.get("url_path")
                                dconfig = call_ha_websocket("lovelace/config", **dparams)
                                if dconfig.get("success"):
                                    cfg = dconfig.get("result", {})
                                    cfg_json = json.dumps(cfg, ensure_ascii=False, default=str)
                                    if len(cfg_json) > 8000:
                                        # Summarize views only
                                        views_summary = []
                                        for v in cfg.get("views", []):
                                            views_summary.append({"title": v.get("title", ""), "path": v.get("path", ""),
                                                                  "cards_count": len(v.get("cards", [])),
                                                                  "cards": [{"type": c.get("type", "")} for c in v.get("cards", [])[:15]]})
                                        context_parts.append(f"## CONFIG DASHBOARD '{dash.get('title')}' (url: {dash.get('url_path', 'lovelace')})\n{json.dumps({'views': views_summary}, ensure_ascii=False, indent=1)}\nConfig troppo grande, caricato sommario. Per i dettagli il tool get_dashboard_config è disponibile.")
                                    else:
                                        context_parts.append(f"## CONFIG COMPLETA DASHBOARD '{dash.get('title')}' (url: {dash.get('url_path', 'lovelace')})\n```json\n{cfg_json}\n```")
                            except Exception:
                                pass
                            break
            except Exception:
                pass

            # Get installed custom cards
            try:
                resources = call_ha_websocket("lovelace/resources")
                res_list = resources.get("result", [])
                if res_list:
                    cards = [r.get("url", "").split("/")[-1].split(".")[0] for r in res_list if r.get("url")]
                    context_parts.append(f"## CUSTOM CARDS INSTALLATE\n{', '.join(cards)}")
            except Exception:
                pass

        # --- ENTITY/DEVICE CONTEXT ---
        entity_keywords = ["luce", "luci", "light", "temperatura", "temperature", "sensore", "sensor",
                          "clima", "climate", "switch", "interruttore", "media_player", "cover", "tapparella"]
        matched_domains = []
        domain_map = {"luce": "light", "luci": "light", "light": "light", "lights": "light",
                     "temperatura": "sensor", "temperature": "sensor", "sensore": "sensor", "sensor": "sensor",
                     "clima": "climate", "climate": "climate", "switch": "switch", "interruttore": "switch",
                     "media_player": "media_player", "cover": "cover", "tapparella": "cover"}
        for kw, domain in domain_map.items():
            if kw in msg_lower and domain not in matched_domains:
                matched_domains.append(domain)

        if matched_domains:
            states = get_all_states()
            for domain in matched_domains[:3]:  # Max 3 domains
                domain_entities = [{"entity_id": s.get("entity_id"),
                                   "state": s.get("state"),
                                   "friendly_name": s.get("attributes", {}).get("friendly_name", "")}
                                  for s in states if s.get("entity_id", "").startswith(f"{domain}.")][:30]
                if domain_entities:
                    context_parts.append(f"## ENTITÀ {domain.upper()}\n{json.dumps(domain_entities, ensure_ascii=False, indent=1)}")

    except Exception as e:
        logger.warning(f"Smart context error: {e}")

    if context_parts:
        context = "\n\n".join(context_parts)
        # Cap total context size to avoid rate limits
        if len(context) > MAX_SMART_CONTEXT:
            context = context[:MAX_SMART_CONTEXT] + "\n... [CONTEXT TRUNCATED]"
        logger.info(f"Smart context: injected {len(context)} chars of pre-loaded data")
        return context
    return ""


def stream_chat_with_ai(user_message: str, session_id: str = "default"):
    """Stream chat events for all providers. Yields SSE event dicts.
    Uses LOCAL intent detection + smart context to minimize tokens sent to AI API."""
    if not ai_client:
        yield {"type": "error", "message": "API key non configurata"}
        return

    if session_id not in conversations:
        conversations[session_id] = []

    # Step 1: Build smart context (loads only the relevant data)
    smart_context = build_smart_context(user_message)
    
    # Step 2: LOCAL intent detection — decide which tools and prompt to use
    intent_info = detect_intent(user_message, smart_context)
    intent_name = intent_info["intent"]
    tool_count = len(intent_info.get("tools") or [])
    all_tools_count = len(HA_TOOLS_DESCRIPTION)
    logger.info(f"Intent detected: {intent_name} (specific_target={intent_info['specific_target']}, tools={tool_count if tool_count else all_tools_count})")
    
    # Show intent to user
    INTENT_LABELS = {
        "modify_automation": "Modifica automazione",
        "modify_script": "Modifica script",
        "create_automation": "Crea automazione",
        "create_script": "Crea script",
        "create_dashboard": "Crea dashboard",
        "modify_dashboard": "Modifica dashboard",
        "control_device": "Controllo dispositivo",
        "query_state": "Stato dispositivo",
        "query_history": "Storico dati",
        "delete": "Eliminazione",
        "config_edit": "Modifica configurazione",
        "areas": "Gestione stanze",
        "notifications": "Notifica",
        "generic": "Analisi richiesta",
    }
    intent_label = INTENT_LABELS.get(intent_name, "Elaboro")
    yield {"type": "status", "message": f"{intent_label}... ({tool_count if tool_count else all_tools_count} tools)"}
    
    # Step 3: Build the message to send
    if smart_context:
        # Shorter, more direct instructions when intent is clear
        if intent_info["specific_target"]:
            enriched_message = f"{user_message}\n\n---\nDATI:\n{smart_context}"
        else:
            enriched_message = f"{user_message}\n\n---\nCONTESTO:\n{smart_context}\n---\nNON richiedere dati già presenti sopra. UNA sola chiamata tool, poi rispondi."
        conversations[session_id].append({"role": "user", "content": enriched_message})
        # Log estimated token count
        est_tokens = len(enriched_message) // 4  # ~4 chars per token
        logger.info(f"Smart context: {len(smart_context)} chars, est. ~{est_tokens} tokens for user message")
        yield {"type": "status", "message": "Contesto pre-caricato..."}
    else:
        conversations[session_id].append({"role": "user", "content": user_message})

    # Pass the actual conversation list so tool calls are persisted in-place
    messages = conversations[session_id]

    try:
        if AI_PROVIDER in ("openai", "github"):
            yield from stream_chat_openai(messages, intent_info=intent_info)
        elif AI_PROVIDER == "anthropic":
            clean_messages = sanitize_messages_for_provider(messages)
            yield from stream_chat_anthropic(clean_messages, intent_info=intent_info)
            conversations[session_id] = clean_messages
        elif AI_PROVIDER == "google":
            clean_messages = sanitize_messages_for_provider(messages)
            yield from stream_chat_google(clean_messages)
            conversations[session_id] = clean_messages
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
        .header .new-chat {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 12px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
        .header .new-chat:hover {{ background: rgba(255,255,255,0.35); }}
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
        .input-area button {{ background: #667eea; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; }}
        .input-area button:hover {{ background: #5a6fd6; }}
        .input-area button:disabled {{ background: #ccc; cursor: not-allowed; }}
        .input-area button.stop-btn {{ background: #ef4444; animation: pulse-stop 1s infinite; }}
        .input-area button.stop-btn:hover {{ background: #dc2626; }}
        @keyframes pulse-stop {{ 0%, 100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }} 50% {{ box-shadow: 0 0 0 6px rgba(239,68,68,0); }} }}
        .suggestions {{ display: flex; gap: 8px; padding: 0 16px 8px; flex-wrap: wrap; }}
        .suggestion {{ background: white; border: 1px solid #ddd; border-radius: 16px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }}
        .suggestion:hover {{ background: #667eea; color: white; border-color: #667eea; }}
        .tool-badge {{ display: inline-block; background: #e8f0fe; color: #1967d2; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
        .status-badge {{ display: inline-block; background: #fef3c7; color: #92400e; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px;">\U0001f916</span>
        <h1>AI Assistant</h1>
        <span class="badge">v{VERSION}</span>
        <span class="badge">{model_name}</span>
        <button class="new-chat" onclick="newChat()" title="Nuova conversazione">✨ Nuova chat</button>
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
        <button id="sendBtn" onclick="handleButtonClick()">
            <svg id="sendIcon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            <svg id="stopIcon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="display:none"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
        </button>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('sendBtn');
        const sendIcon = document.getElementById('sendIcon');
        const stopIcon = document.getElementById('stopIcon');
        const suggestionsEl = document.getElementById('suggestions');
        let sending = false;
        let currentReader = null;

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
                    await fetch('api/chat/abort', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: '{{}}' }});
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
            div.innerHTML = 'Analizzo la richiesta<span class="dots"><span>.</span><span>.</span><span>.</span></span>';
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
            setStopMode(true);
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
                if (err.name !== 'AbortError') {{
                    addMessage('\u274c Errore: ' + err.message, 'system');
                }}
            }}
            sending = false;
            setStopMode(false);
            sendBtn.disabled = false;
            currentReader = null;
            input.focus();
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
                            if (evt.type === 'tool') {{
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
            // Safety: if stream ended without final response, show a message
            removeThinking();
            if (!gotAnyEvent) {{
                addMessage('\u274c Connessione interrotta. Riprova.', 'system');
            }}
        }}

        async function loadHistory() {{
            try {{
                const resp = await fetch('api/conversations/default/messages');
                const data = await resp.json();
                if (data.messages && data.messages.length > 0) {{
                    suggestionsEl.style.display = 'none';
                    data.messages.forEach(m => {{
                        addMessage(m.content, m.role);
                    }});
                }}
            }} catch(e) {{ console.log('No history:', e); }}
        }}

        async function newChat() {{
            if (!confirm('Iniziare una nuova conversazione? La cronologia verrà cancellata.')) return;
            try {{
                await fetch('api/conversations/default', {{ method: 'DELETE' }});
            }} catch(e) {{}}
            // Clear UI
            chat.innerHTML = `<div class="message system">
                \U0001f44b Ciao! Sono il tuo assistente AI per Home Assistant.<br>
                Provider: <strong>{provider_name}</strong> | Modello: <strong>{model_name}</strong><br>
                Posso controllare dispositivi, creare automazioni e gestire la tua casa smart.
            </div>`;
            suggestionsEl.style.display = 'flex';
        }}

        // Load history on page load
        loadHistory();
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
    abort_streams[session_id] = False  # Reset abort flag

    def generate():
        for event in stream_chat_with_ai(message, session_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/api/chat/abort', methods=['POST'])
def api_chat_abort():
    """Abort a running stream."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")
    abort_streams[session_id] = True
    logger.info(f"Abort requested for session {session_id}")
    return jsonify({"status": "abort_requested"}), 200


@app.route('/api/conversations', methods=['GET'])
def api_conversations():
    """List conversation sessions."""
    sessions = {}
    for sid, msgs in conversations.items():
        sessions[sid] = {"message_count": len(msgs), "last_role": msgs[-1]["role"] if msgs else ""}
    return jsonify(sessions), 200


@app.route('/api/conversations/<session_id>/messages', methods=['GET'])
def api_conversation_messages(session_id):
    """Get all messages for a conversation session."""
    msgs = conversations.get(session_id, [])
    # Return only user/assistant text messages for UI display
    display_msgs = []
    for m in msgs:
        if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
            display_msgs.append({"role": m["role"], "content": m["content"]})
    return jsonify({"session_id": session_id, "messages": display_msgs}), 200


@app.route('/api/conversations/<session_id>', methods=['DELETE'])
def api_conversation_delete(session_id):
    """Clear a conversation session."""
    if session_id in conversations:
        del conversations[session_id]
        save_conversations()
    return jsonify({"status": "ok", "message": f"Session '{session_id}' cleared."}), 200


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
