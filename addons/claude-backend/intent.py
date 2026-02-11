"""Intent detection and smart context for Home Assistant AI assistant."""

import os
import json
import re
import logging
from typing import Dict, List

import api

logger = logging.getLogger(__name__)


# ---- Intent tool sets and prompts ----

# Tool sets by intent category
INTENT_TOOL_SETS = {
    "chat": [],  # No tools needed for greetings/chitchat
    "find_automation": ["get_automations"],
    "modify_automation": ["update_automation"],
    "modify_script": ["update_script"],
    "create_automation": ["create_automation", "search_entities", "get_entity_state"],
    "create_script": ["create_script", "search_entities", "get_entity_state"],
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
    "chat": """Sei un assistente amichevole per Home Assistant. L'utente sta semplicemente salutando o chiacchierando.
Rispondi in modo breve e cordiale. Non chiamare nessun tool.""",

    "find_automation": """You are a Home Assistant automation finder.
The user is asking whether an automation already exists.
CRITICAL: Do NOT guess.
You MUST call get_automations ONCE with a short query extracted from the user message (room/device name, entity_id fragment, alias keywords).
Then answer:
- If you find matches: list the best 1-5 matches (id + alias) and ask which one they mean.
- If you find none: say you couldn't find it and propose next step (search by entity names or create a new automation).
Be concise and respond in the user's language.""",

    "modify_automation": """You are a Home Assistant automation editor. The user wants to modify an automation.
The automation config is provided in the DATI section of the user's message.
CRITICAL RULE - ALWAYS ASK FOR CONFIRMATION BEFORE MODIFYING:
1. FIRST, briefly confirm which automation you found: "Ho trovato l'automazione: [NAME] (id: [ID])"
2. Describe WHAT EXACTLY will change in simple language
3. ASK FOR EXPLICIT CONFIRMATION: "Confermi che devo fare questa modifica? Scrivi sì o no"
4. WAIT FOR USER TO CONFIRM - DO NOT call update_automation until user says "sì" or "sa" (Italian yes)
5. Only AFTER confirmation, call update_automation ONCE with the changes
6. Show a before/after diff of what changed.
- Respond in the user's language. Be concise.
- NEVER call get_automations or read_config_file — the data is already provided.
- If the automation in DATI doesn't match what the user asked for, tell them and ask for clarification. Do NOT modify the wrong automation.""",

    "modify_script": """You are a Home Assistant script editor. The user wants to modify a script.
The script config is provided in the DATI section.
CRITICAL RULE - ALWAYS ASK FOR CONFIRMATION BEFORE MODIFYING:
1. FIRST, briefly confirm which script you found: "Ho trovato lo script: [NAME] (id: [ID])"
2. Describe WHAT EXACTLY will change in simple language
3. ASK FOR EXPLICIT CONFIRMATION: "Confermi che devo fare questa modifica? Scrivi sì o no"
4. WAIT FOR USER TO CONFIRM - DO NOT call update_script until user says "sì" or "si"
5. Only AFTER confirmation, call update_script ONCE with the changes
6. Show a before/after diff of what changed.
- Respond in the user's language. Be concise.
- NEVER call get_scripts or read_config_file — the data is already provided.
- If the script doesn't match what the user asked for, tell them. Do NOT modify the wrong one.""",

    "create_automation": """You are a Home Assistant automation builder. The user wants to create a NEW automation.
CRITICAL WORKFLOW - follow these steps IN ORDER:
1. FIRST call search_entities to find the correct entity_id for the device the user mentioned.
   - A "luce" (light) could be a light.* OR a switch.* entity — you MUST search, never guess the domain.
   - Use keywords from the user's message (room name, device type).
2. If unsure about the entity type, call get_entity_state to verify the domain and attributes.
3. Build the automation with COMPLETE and CORRECT trigger/condition/action:
   - For time-based triggers use: {"platform": "time", "at": "HH:MM:SS"}
   - For state triggers use: {"platform": "state", "entity_id": "...", "to": "on"}
   - For actions use the CORRECT service for the entity domain:
     * switch.* entities → service: switch.turn_on / switch.turn_off
     * light.* entities → service: light.turn_on / light.turn_off
     * cover.* entities → service: cover.open_cover / cover.close_cover
     * climate.* entities → service: climate.set_temperature
   - Action format: {"service": "domain.action", "target": {"entity_id": "domain.entity_name"}}
4. Call create_automation ONCE with the complete config (alias, trigger, action, condition, mode).
NEVER create an automation with empty trigger or action arrays.
Respond in the user's language. Be concise.""",

    "create_script": """You are a Home Assistant script builder. The user wants to create a NEW script.
CRITICAL WORKFLOW:
1. FIRST call search_entities to find the correct entity_id(s) for the device(s) mentioned.
2. Build the script with a COMPLETE sequence of actions using correct services for each entity domain:
   - switch.* → switch.turn_on/off, light.* → light.turn_on/off, etc.
   - Action format: {"service": "domain.action", "target": {"entity_id": "domain.entity_name"}}
3. Call create_script ONCE with script_id, alias, sequence, and mode.
NEVER create a script with empty sequence.
Respond in the user's language. Be concise.""",

    "control_device": """You are a Home Assistant device controller. Help the user control their devices.
Use search_entities to find entities if needed, then call_service to control them.
Respond in the user's language. Be concise. Maximum 2 tool calls.""",

    "query_state": None,  # Will be generated dynamically with language instruction

    "delete": """You are a Home Assistant deletion assistant. User wants to delete an automation, script, or dashboard.
CRITICAL DESTRUCTION RULE - ALWAYS ASK FOR EXPLICIT CONFIRMATION:
1. FIRST, identify what will be deleted: "Vuoi eliminare: [NAME] (id: [ID]). Questa azione è IRREVERSIBILE."
2. ASK FOR EXPLICIT CONFIRMATION: "Digita 'elimina' per confermare l'eliminazione di [NAME], altrimenti digita 'no'"
3. WAIT FOR CONFIRMATION - DO NOT call delete_automation/delete_script/delete_dashboard until user types "elimina"
4. Only AFTER explicit confirmation, call the appropriate delete tool
- Respond in the user's language. Be concise.
- NEVER auto-confirm deletions. Deletions are IRREVERSIBLE.""",
}


def _init_dynamic_prompts():
    """Initialize prompts that depend on api.get_lang_text (called after api module is loaded)."""
    if INTENT_PROMPTS["query_state"] is None:
        INTENT_PROMPTS["query_state"] = (
            """You are a Home Assistant status assistant. Help the user check device states.
Use search_entities or get_entity_state to find and report states.
Respond in the user's language. Be concise.
IMPORTANT: Do not ask the user to repeat what they want. Use the tools and answer."""
            + "\n" + api.get_lang_text("respond_instruction")
        )
    # Also add language instruction to chat prompt
    lang_instr = api.get_lang_text("respond_instruction")
    if lang_instr and lang_instr not in INTENT_PROMPTS["chat"]:
        INTENT_PROMPTS["chat"] += "\n\n" + lang_instr


# ---- Scoring helpers for query_state auto-stop ----

def _score_query_state_candidate(user_message: str, entity_id: str, friendly_name: str) -> int:
    msg = (user_message or "").lower()
    eid = (entity_id or "").lower()
    name = (friendly_name or "").lower()

    score = 0

    # Strong signals for "today production"
    if "produzione_giornal" in eid or "today_production" in eid or "day_production" in eid:
        score += 80
    if "giornal" in eid or "oggi" in eid or "today" in eid:
        score += 10

    # PV / solar / production keywords
    keywords = ["fotovolta", "solare", "solar", "pv", "produzione", "production", "energia", "energy"]
    for k in keywords:
        if k in msg and (k in eid or k in name):
            score += 8
        elif k in eid or k in name:
            score += 2

    # Prefer energy/production sensors
    if eid.startswith("sensor."):
        score += 3
    if "power" in eid or "kw" in eid:
        score += 2
    if "energy" in eid or "kwh" in eid:
        score += 6

    # De-prioritize obvious false positives
    if "ipv4" in eid or "ipv6" in eid or "address" in eid:
        score -= 50
    if eid.startswith("binary_sensor."):
        score -= 10
    if eid.startswith("button.") or eid.startswith("switch."):
        score -= 8

    return score


def _format_query_state_answer(entity_id: str, state_data: dict) -> str:
    state = state_data.get("state")
    attrs = state_data.get("attributes") or {}
    friendly_name = attrs.get("friendly_name") or entity_id
    unit = attrs.get("unit_of_measurement") or ""

    if state in (None, "unknown", "unavailable"):
        if api.LANGUAGE == "it":
            return f"Non riesco a leggere un valore disponibile per '{friendly_name}' ({entity_id})."
        return f"I can't read an available value for '{friendly_name}' ({entity_id})."

    value = f"{state}{(' ' + unit) if unit else ''}"
    if api.LANGUAGE == "it":
        return f"Oggi la produzione risulta: {value} (sensore: {friendly_name})."
    if api.LANGUAGE == "es":
        return f"La producción de hoy es: {value} (sensor: {friendly_name})."
    if api.LANGUAGE == "fr":
        return f"La production d'aujourd'hui est : {value} (capteur : {friendly_name})."
    return f"Today's production is: {value} (sensor: {friendly_name})."


# ---- Intent detection ----

def detect_intent(user_message: str, smart_context: str) -> dict:
    """Detect user intent locally from the message and available context.
    Uses multilingual keywords from keywords.json based on LANGUAGE setting.
    Returns: {"intent": str, "tools": list[str], "prompt": str|None, "specific_target": bool}
    If intent is clear + specific target found, use focused mode (fewer tools, shorter prompt).
    Otherwise fall back to full mode."""
    # Ensure dynamic prompts are initialized
    _init_dynamic_prompts()

    msg = user_message.lower()

    # Get keywords for current language, fallback to English if not available
    lang_keywords = api.KEYWORDS.get(api.LANGUAGE, api.KEYWORDS.get("en", {}))

    # --- CHAT (greetings, chitchat) --- NEW: detect before any other intent
    chat_kw = lang_keywords.get("chat", [])
    words = msg.strip().rstrip("!?.,").split()
    if len(words) <= 5 and any(k in msg for k in chat_kw):
        return {"intent": "chat", "tools": INTENT_TOOL_SETS["chat"],
                "prompt": INTENT_PROMPTS["chat"], "specific_target": False, "max_rounds": 1}

    # Extract keywords for different categories
    create_kw = lang_keywords.get("create", [])
    modify_kw = lang_keywords.get("modify", [])
    auto_kw = lang_keywords.get("automation", [])
    script_kw = lang_keywords.get("script", [])
    dash_kw = lang_keywords.get("dashboard", [])
    control_kw = lang_keywords.get("control", [])
    query_kw = lang_keywords.get("query", [])
    history_kw = lang_keywords.get("history", [])
    delete_kw = lang_keywords.get("delete", [])
    config_kw = lang_keywords.get("config", [])

    # --- MODIFY AUTOMATION (most common case) ---
    has_modify = any(k in msg for k in modify_kw)
    has_auto = any(k in msg for k in auto_kw)
    # Also detect if smart context found a specific automation
    has_specific_auto = "## AUTOMAZIONE" in smart_context if smart_context else False

    if has_modify and (has_auto or has_specific_auto):
        return {"intent": "modify_automation", "tools": INTENT_TOOL_SETS["modify_automation"],
                "prompt": INTENT_PROMPTS["modify_automation"] + "\n\nIMPORTANT: Before calling update_automation, show the user which automation you will modify and ask for explicit confirmation. Provide modification details and ask: 'Confermi che devo modificare questa automazione? (sì/no)'", "specific_target": has_specific_auto}

    # --- MODIFY SCRIPT ---
    has_script = any(k in msg for k in script_kw)
    has_specific_script = "## SCRIPT" in smart_context if smart_context else False

    if has_modify and (has_script or has_specific_script):
        return {"intent": "modify_script", "tools": INTENT_TOOL_SETS["modify_script"],
                "prompt": INTENT_PROMPTS["modify_script"], "specific_target": has_specific_script}

    # --- CREATE AUTOMATION ---
    has_create = any(k in msg for k in create_kw)

    # --- FIND AUTOMATION (existence check) ---
    # Common in Italian: "c'è un'automazione che..." is NOT a create request.
    # Keep this heuristic simple and conservative.
    if has_auto and not has_create:
        if ("c'e" in msg) or ("c’è" in msg) or ("c'è" in msg) or ("esiste" in msg) or ("ci sono" in msg):
            return {
                "intent": "find_automation",
                "tools": INTENT_TOOL_SETS["find_automation"],
                "prompt": INTENT_PROMPTS["find_automation"],
                "specific_target": False,
                "max_rounds": 2,
            }

    if has_create and has_auto:
        return {"intent": "create_automation", "tools": INTENT_TOOL_SETS["create_automation"],
                "prompt": INTENT_PROMPTS["create_automation"], "specific_target": False}

    # --- CREATE SCRIPT ---
    if has_create and has_script:
        return {"intent": "create_script", "tools": INTENT_TOOL_SETS["create_script"],
                "prompt": INTENT_PROMPTS["create_script"], "specific_target": False}

    # --- DASHBOARD ---
    has_dash = any(k in msg for k in dash_kw)
    if has_dash and has_create:
        return {"intent": "create_dashboard", "tools": INTENT_TOOL_SETS["create_dashboard"],
                "prompt": None, "specific_target": False}
    if has_dash and has_modify:
        return {"intent": "modify_dashboard", "tools": INTENT_TOOL_SETS["modify_dashboard"],
                "prompt": None, "specific_target": False}

    # --- DEVICE CONTROL ---
    if any(k in msg for k in control_kw):
        return {"intent": "control_device", "tools": INTENT_TOOL_SETS["control_device"],
                "prompt": INTENT_PROMPTS["control_device"], "specific_target": False}

    # --- QUERY STATE ---
    if any(k in msg for k in query_kw):
        return {"intent": "query_state", "tools": INTENT_TOOL_SETS["query_state"],
                "prompt": INTENT_PROMPTS["query_state"], "specific_target": False}

    # --- HISTORY ---
    if any(k in msg for k in history_kw):
        return {"intent": "query_history", "tools": INTENT_TOOL_SETS["query_history"],
                "prompt": None, "specific_target": False}

    # --- DELETE ---
    if any(k in msg for k in delete_kw) and (has_auto or has_script or has_dash):
        return {"intent": "delete", "tools": INTENT_TOOL_SETS["delete"],
                "prompt": None, "specific_target": False}

    # --- CONFIG EDIT ---
    if any(k in msg for k in config_kw):
        return {"intent": "config_edit", "tools": INTENT_TOOL_SETS["config_edit"],
                "prompt": None, "specific_target": False}

    # --- GENERIC (full mode) ---
    return {"intent": "generic", "tools": None, "prompt": None, "specific_target": False}


def get_tools_for_intent(intent_info: dict, provider: str = "anthropic") -> list:
    """Get tool definitions filtered by intent. Returns full tools if intent is generic."""
    import tools as _tools

    tool_names = intent_info.get("tools")
    if tool_names is None:
        # Generic: return all tools
        if provider == "anthropic":
            return _tools.get_anthropic_tools()
        elif provider in ("openai", "github", "nvidia"):
            return _tools.get_openai_tools_for_provider()
        return _tools.get_anthropic_tools()

    # Filter to only relevant tools (empty list → empty result for chat intent)
    filtered = [t for t in _tools.HA_TOOLS_DESCRIPTION if t["name"] in tool_names]

    if provider == "anthropic":
        return [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in filtered]
    elif provider in ("openai", "github", "nvidia"):
        return [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in filtered]
    return [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in filtered]


def get_prompt_for_intent(intent_info: dict) -> str:
    """Get system prompt for intent. Returns focused prompt if available, else full."""
    import tools as _tools

    # Ensure dynamic prompts are initialized
    _init_dynamic_prompts()

    prompt = intent_info.get("prompt")
    if prompt:
        # Enforce configured LANGUAGE even in focused prompts
        lang_instruction = api.get_lang_text("respond_instruction")
        if lang_instruction and lang_instruction not in prompt:
            return prompt + "\n\n" + lang_instruction
        return prompt
    return _tools.get_system_prompt()


def trim_messages(messages: List[Dict], max_messages: int = 20) -> List[Dict]:
    """Trim conversation history, preserving tool_call/tool response pairs."""
    limit = 6 if api.AI_PROVIDER == "github" else max_messages
    # GitHub o4-mini has a very small request size limit (~4000 tokens).
    # Keep fewer turns to reduce the prompt size.
    try:
        if api.AI_PROVIDER == "github" and "o4-mini" in (api.get_active_model() or "").lower():
            limit = 4
    except Exception:
        pass
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


# ---- Smart context builder ----

MAX_SMART_CONTEXT = 10000  # Max chars to inject — keeps tokens under control


def build_smart_context(user_message: str, intent: str = None) -> str:
    """Pre-load relevant context based on user's message intent.
    Works like VS Code: gathers all needed data BEFORE sending to AI,
    so Claude can respond with a single action instead of multiple tool rounds.
    IMPORTANT: Context must be compact to avoid rate limits.
    CRITICAL: If intent is 'create_automation' or 'create_script', skip fuzzy matching
    to avoid incorrectly injecting an existing automation/script to be modified."""
    msg_lower = user_message.lower()
    context_parts = []

    # Skip automation/script fuzzy matching if user is CREATING new (not modifying)
    skip_automation_matching = (intent in ("create_automation", "create_script"))

    try:
        # --- AUTOMATION CONTEXT ---
        auto_keywords = ["automazione", "automation", "automazion", "trigger", "condizione", "condition"]
        if any(k in msg_lower for k in auto_keywords) and not skip_automation_matching:
            import yaml
            # Get automation list
            states = api.get_all_states()
            autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
            auto_list = [{"entity_id": a.get("entity_id"),
                         "friendly_name": a.get("attributes", {}).get("friendly_name", ""),
                         "id": str(a.get("attributes", {}).get("id", "")),
                         "state": a.get("state")} for a in autos]

            # If user mentions a specific automation name, include its config
            # Try YAML first, then REST API for UI-created automations
            yaml_path = api.get_config_file_path("automation", "automations.yaml")
            found_in_yaml = False
            found_specific = False
            target_auto_id = None
            target_auto_alias = None

            # Find the BEST matching automation using scored matching
            best_score = 0
            best_match = None

            # Words to IGNORE in matching
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
                        score = sum(len(w) for w in matching_words)
                        if len(matching_words) >= 2:
                            score += 10

                if score > best_score:
                    best_score = score
                    best_match = a

            if best_match and best_score >= 5:
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
                        rest_config = api.call_ha_api("GET", f"config/automation/config/{target_auto_id}")
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
                compact_list = [{"name": a.get("friendly_name", ""), "id": a.get("id", "")} for a in auto_list if a.get("friendly_name")]
                list_json = json.dumps(compact_list, ensure_ascii=False, separators=(',', ':'))
                if len(list_json) > 3000:
                    list_json = list_json[:3000] + '...]'
                context_parts.append(f"## AUTOMAZIONI DISPONIBILI\n{list_json}")

        # --- SCRIPT CONTEXT ---
        script_keywords = ["script", "scena", "scenari", "routine", "sequenza"]
        if any(k in msg_lower for k in script_keywords):
            import yaml
            states = api.get_all_states()
            script_entities = [{"entity_id": s.get("entity_id"),
                               "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                               "state": s.get("state")} for s in states if s.get("entity_id", "").startswith("script.")]
            if script_entities:
                context_parts.append(f"## SCRIPT DISPONIBILI\n{json.dumps(script_entities, ensure_ascii=False, indent=1)}")

            yaml_path = api.get_config_file_path("script", "scripts.yaml")
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
            try:
                dashboards = api.call_ha_websocket("lovelace/dashboards/list")
                dash_list = dashboards.get("result", [])
                if dash_list:
                    summary = [{"id": d.get("id"), "title": d.get("title", ""), "url_path": d.get("url_path", "")} for d in dash_list]
                    context_parts.append(f"## DASHBOARD DISPONIBILI\n{json.dumps(summary, ensure_ascii=False, indent=1)}")

                    for dash in dash_list:
                        dash_title = str(dash.get("title", "")).lower()
                        dash_url = str(dash.get("url_path", "")).lower()
                        if dash_title and (dash_title in msg_lower or dash_url in msg_lower or any(word in dash_title for word in msg_lower.split() if len(word) > 4)):
                            try:
                                dparams = {}
                                if dash_url and dash_url != "lovelace":
                                    dparams["url_path"] = dash.get("url_path")
                                dconfig = api.call_ha_websocket("lovelace/config", **dparams)
                                if dconfig.get("success"):
                                    cfg = dconfig.get("result", {})
                                    cfg_json = json.dumps(cfg, ensure_ascii=False, default=str)
                                    if len(cfg_json) > 8000:
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
                resources = api.call_ha_websocket("lovelace/resources")
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
            states = api.get_all_states()
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
        limit = MAX_SMART_CONTEXT
        try:
            if api.AI_PROVIDER == "github" and "o4-mini" in (api.get_active_model() or "").lower():
                # Smaller context for free/low-limit models
                limit = 2500
        except Exception:
            pass
        if len(context) > limit:
            context = context[:limit] + "\n... [CONTEXT TRUNCATED]"
        logger.info(f"Smart context: injected {len(context)} chars of pre-loaded data")
        return context
    return ""
