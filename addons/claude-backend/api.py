"""AI Assistant API with multi-provider support for Home Assistant."""

import os
import json
import logging
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# Version
VERSION = "2.5.3"

# Configuration
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "")
AI_MODEL = os.getenv("AI_MODEL", "")
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

        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        logger.error(f"Tool error ({tool_name}): {e}")
        return json.dumps({"error": str(e)})


# ---- System prompt ----

SYSTEM_PROMPT = """You are an AI assistant integrated into Home Assistant. You help users manage their smart home.

You can:
1. **Query entities** - See device states (lights, sensors, switches, climate, covers, etc.)
2. **Control devices** - Turn on/off lights, switches, set temperatures, etc.
3. **Create automations** - Build new automations with triggers, conditions, and actions
4. **List & trigger automations** - See and run existing automations
5. **Discover services** - See all available HA services

When creating automations, use proper Home Assistant formats:
- State trigger: {"platform": "state", "entity_id": "binary_sensor.motion", "to": "on"}
- Time trigger: {"platform": "time", "at": "07:00:00"}
- Sun trigger: {"platform": "sun", "event": "sunset", "offset": "-00:30:00"}
- Service action: {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 255}}

Always respond in the same language the user uses.
Be concise but informative."""

# Compact prompt for providers with small context (GitHub Models free tier: 8k tokens)
SYSTEM_PROMPT_COMPACT = """You are a Home Assistant AI assistant. Control devices, query states, search entities, list events, create automations.
When a user asks about specific devices/addons, use search_entities to find them by keyword. Use get_events to discover event types.
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
        "description": "Call HA service (e.g. light.turn_on, switch.toggle, climate.set_temperature).",
        "parameters": {"type": "object", "properties": {
            "domain": {"type": "string"}, "service": {"type": "string"},
            "data": {"type": "object"}
        }, "required": ["domain", "service", "data"]}
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
        "name": "get_automations",
        "description": "List all automations.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "search_entities",
        "description": "Search entities by keyword in entity_id or friendly_name.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    },
    {
        "name": "get_events",
        "description": "List all available HA event types.",
        "parameters": {"type": "object", "properties": {}, "required": []}
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
    """Trim conversation history for providers with small context windows."""
    if AI_PROVIDER == "github":
        # Keep only last 6 messages for GitHub free tier (8k token limit)
        return messages[-6:] if len(messages) > 6 else messages
    return messages[-max_messages:] if len(messages) > max_messages else messages


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
        return final_text

    except Exception as e:
        logger.error(f"AI error ({AI_PROVIDER}): {e}")
        return f"\u274c Errore {PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get('name', AI_PROVIDER)}: {str(e)}"


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
                const resp = await fetch('api/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: text }})
                }});
                const data = await resp.json();
                removeThinking();
                if (data.response) {{ addMessage(data.response, 'assistant'); }}
                else if (data.error) {{ addMessage('\u274c ' + data.error, 'system'); }}
            }} catch (err) {{
                removeThinking();
                addMessage('\u274c Errore: ' + err.message, 'system');
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
