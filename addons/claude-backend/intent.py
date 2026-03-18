"""Intent detection and smart context for Home Assistant AI assistant."""

import os
import json
import re
import logging
from typing import Dict, List, Optional

import api

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Compact tool descriptions for AI-based intent classification
# Each tool ➜ 1-line description (~500 tokens total for the full map)
# ---------------------------------------------------------------------------
TOOL_DESCRIPTIONS: Dict[str, str] = {
    "get_entities": "Get all entities or filter by domain (light, sensor, switch …)",
    "get_entity_state": "Get current state and attributes of one entity",
    "call_service": "Call a HA service: turn on/off lights, switches, climate, covers, media, notify …",
    "create_automation": "Create a new automation (triggers, conditions, actions)",
    "get_automations": "Search/list existing automations by keyword",
    "update_automation": "Modify an existing automation by ID",
    "trigger_automation": "Manually trigger an automation",
    "get_available_services": "List all available HA service domains and services",
    "search_entities": "Search entities by keyword in entity_id or friendly_name",
    "get_integration_entities": "Find entities belonging to an integration/platform",
    "get_events": "List all available HA event types",
    "get_history": "Get state history of an entity over a time period",
    "get_scenes": "Get all available scenes",
    "activate_scene": "Activate a scene",
    "get_scripts": "List all available scripts",
    "run_script": "Run a script with optional variables",
    "update_script": "Modify an existing script",
    "get_areas": "Get all areas/rooms and their entities",
    "send_notification": "Send a notification (persistent or mobile)",
    "get_dashboards": "List all Lovelace dashboards",
    "create_dashboard": "Create a new Lovelace YAML dashboard",
    "create_script": "Create a new script with a sequence of actions",
    "delete_dashboard": "Delete a dashboard",
    "delete_automation": "Delete an automation",
    "delete_script": "Delete a script",
    "manage_areas": "Create, rename, or delete areas/rooms",
    "manage_entity": "Rename, assign to area, enable/disable an entity",
    "get_devices": "Get all registered devices with manufacturer, model, area",
    "manage_statistics": "Validate and fix recorder statistics",
    "get_statistics": "Get advanced statistics (min/max/mean/sum) for a sensor",
    "shopping_list": "View, add, or complete items in the shopping list",
    "create_backup": "Create a full HA backup",
    "browse_media": "Browse media content from media players",
    "get_dashboard_config": "Get the full config of a Lovelace dashboard",
    "update_dashboard": "Modify an existing Lovelace dashboard",
    "get_frontend_resources": "List registered frontend resources (custom cards, HACS)",
    "read_config_file": "Read a HA YAML config file (configuration.yaml, etc.)",
    "write_config_file": "Write/update a HA config file (auto-backup)",
    "check_config": "Validate HA configuration",
    "list_config_files": "List files in the HA config directory",
    "list_snapshots": "List available config snapshots",
    "restore_snapshot": "Restore a file from a snapshot",
    "manage_helpers": "Create/update/delete helpers (input_boolean, input_number, etc.)",
    "read_html_dashboard": "Read the HTML source of a custom dashboard",
    "create_html_dashboard": "Create a custom HTML dashboard with real-time monitoring",
    "get_repairs": "Get active issues/repairs and system health",
    "dismiss_repair": "Dismiss a specific repair issue",
    "fire_event": "Fire a custom event on the HA event bus",
    "get_logged_users": "List all HA users: who is connected/logged in, roles, status",
    "get_error_log": "Interactive error log viewer (summary + detail modes)",
    "get_ha_logs": "Get HA system logs and error messages",
}


# ---- Intent tool sets and prompts ----

# Tool sets by intent category
# NOTE: With the LLM-first approach (OpenClaw style), most intents use tools=None
# which means ALL tools are sent to the LLM and it decides autonomously.
# Only special cases restrict the tool set.
INTENT_TOOL_SETS = {
    "chat": [],  # No tools needed for greetings/chitchat
    "card_editor": ["search_entities", "get_integration_entities"],
    "create_html_dashboard": ["read_html_dashboard", "create_html_dashboard", "search_entities", "get_integration_entities", "get_frontend_resources"],
    "manage_statistics": ["manage_statistics"],
    # LLM-first: all tools available, model decides
    "auto": None,
    # Follow-up intents (carried forward from previous_intent): all get full tool set
    "create_dashboard": None,
    "config_edit": None,
    "modify_automation": None,
    "modify_script": None,
    "modify_dashboard": None,
    "system_debug": None,
}

# ---------------------------------------------------------------------------
# Unified system guidance prompt (OpenClaw-style: LLM decides, no pre-routing)
# This replaces ALL per-intent focused prompts. The LLM receives ALL tools
# and this guidance helps it decide which ones to use.
# ---------------------------------------------------------------------------
HA_SYSTEM_GUIDANCE = """You are a Home Assistant AI assistant with full tool access.
You decide which tools to call based on the user's request. Be autonomous and efficient.

TOOL USAGE GUIDE:
— DEVICE CONTROL: call_service + search_entities (find the entity first, then act)
  • switch.* → switch.turn_on/off, light.* → light.turn_on/off, cover.* → cover.open/close, climate.* → climate.set_temperature
  • Action format: {"service": "domain.action", "target": {"entity_id": "..."}}

— QUERY CURRENT STATE: get_entity_state, search_entities, get_entities
  • search_entities to find the entity, get_entity_state to read it

— HISTORY / PAST DATA (e.g. "what was the temperature this morning", "yesterday", "3 hours ago"):
  • ALWAYS use get_history + search_entities. Include get_statistics for min/max/average.
  • Never answer history questions without calling get_history.

— AUTOMATIONS:
  • Find: get_automations (search by keyword)
  • Create: search_entities first (find correct entity_ids), then create_automation with COMPLETE config
  • Modify: MANDATORY 2-step:
      STEP 1 — call preview_automation_change(automation_id, changes) IMMEDIATELY. Do NOT ask "shall I prepare the preview?" — just call it.
      STEP 2 — ONLY after user confirms ("sì/yes/ok/procedi"), call update_automation(automation_id, changes)
      NEVER call update_automation directly on the first request. Always preview first.
      If the user asks additional tweaks before confirming, produce a NEW preview with updated changes.
      Do not ask repeated confirmation for each micro-tweak; ask once on the latest preview.
  • Delete: identify it, ASK EXPLICIT CONFIRMATION, then delete_automation

— SCRIPTS:
  • Same pattern as automations: search → preview_automation_change → confirm → update_script

— DASHBOARDS (Lovelace):
  • Create: search_entities first, then create_dashboard with complete views array
  • Modify: get_dashboard_config, then update_dashboard
  • Delete: ASK CONFIRMATION, then delete_dashboard

— CONFIG FILES (YAML editing):
  • Read: read_config_file (call IMMEDIATELY, no announcements)
  • Show the COMPLETE corrected file in ```yaml, then ASK CONFIRMATION
  • Write: write_config_file (ENTIRE file content) → check_config to validate
  • Snapshots: list_snapshots, restore_snapshot

— HELPERS: manage_helpers (create/update/delete input_boolean, input_number, input_select, etc.; "counter" is auto-mapped to input_number on this API channel)
  • If user asks to create/update/delete a counter helper, DO NOT refuse. Call manage_helpers with helper_type="counter" and let backend compatibility mapping handle it.
— AREAS/ROOMS: manage_areas, manage_entity, get_areas, get_devices
— NOTIFICATIONS: send_notification + search_entities
— SCENES: get_scenes, activate_scene
— SHOPPING LIST: shopping_list
— SYSTEM DIAGNOSTICS:
  • Error logs: get_error_log() for summary, get_error_log(entry_index=N) for details
  • System health: get_repairs, dismiss_repair
  • Users: get_logged_users
  • Events: fire_event
— STATISTICS MANAGEMENT: manage_statistics (validate/fix_units/clear_orphaned/clear)
  • Call EXACTLY ONE action per turn. validate is read-only, fix_units/clear_orphaned validate internally.

GENERAL RULES:
- For WRITE operations (create/modify/delete automations, scripts, dashboards, config files):
  ALWAYS show what will change and ASK FOR CONFIRMATION before executing. Never auto-confirm.
  Exception: preview_automation_change is read-only and safe — call it immediately without asking.
- Use search_entities when you need to find an entity_id. NEVER guess entity_ids.
- Be concise. Go straight to the answer — no preambles like "ecco i risultati".
- Respond in the user's language.
- If the request is just a greeting or chitchat, reply briefly without calling any tools."""

# Compact focused prompts by intent (only for special contexts that need very specific instructions)
# Most intents use HA_SYSTEM_GUIDANCE (unified prompt). Only override here for
# contexts that need highly specific instructions the LLM can't infer from tool descriptions.
INTENT_PROMPTS = {
    "chat": """You are a friendly Home Assistant assistant. The user is simply greeting or chatting.
Reply briefly and warmly. Do NOT call any tools. ALWAYS respond in the user's language.""",

    "card_editor": """You are a Home Assistant Lovelace card expert.
The user is editing a card in the HA visual editor and wants you to check/fix the YAML.
The [CONTEXT] block contains the current card YAML and entity validation results.
- Entities marked VALID exist in hass.states and work in cards — do not re-verify.
- Entities marked NOT FOUND are not in hass.states (frontend). This can mean:
  a) The entity_id is wrong — call get_integration_entities ONCE to find the correct one.
  b) The entity exists in HA backend but is disabled/hidden — the tool will confirm this.
  c) The integration is not installed — the tool will return no results.
- CRITICAL: call get_integration_entities AT MOST ONCE per integration. After receiving the
  tool result, produce your final answer IMMEDIATELY. Do NOT call the same tool again.
- If the tool confirms the entity EXISTS with a valid state: tell the user the entity exists
  in HA but is not visible to cards (possibly disabled/hidden). Suggest enabling it or restarting HA.
- If the tool does NOT find the entity: look for a similar entity with matching device_class/unit
  and suggest it as a replacement.
- ALWAYS respond with the complete corrected YAML in a ```yaml code block.
- If all entities are VALID and YAML is correct, say so and suggest optional improvements only.

CUSTOM CARD YAML RULES — many users install custom cards via HACS. Follow the correct syntax:
- mini-graph-card: 'entities' MUST be a list. Example:
  type: custom:mini-graph-card
  entities:
    - entity: sensor.temperature
    - entity: sensor.humidity
  Do NOT use 'entity:' (singular) — it will fail with 'provide entities as a list'.
- mushroom cards: use the 'entity' field (singular) for the main entity.
- apexcharts-card: 'series' is a list of objects with 'entity' key.
- button-card: 'entity' (singular) for the main entity.
- stack-in-card / layout-card: 'cards' is a list of sub-cards.
When suggesting custom cards, always use the correct field names and list structures.

- Do NOT call create_dashboard, update_dashboard, or write_config_file — the user pastes YAML manually.
- NEVER output raw JSON, [TOOL RESULT] blocks, or tool call XML to the user.
- Respond in the user's language.""",

    "manage_statistics": """You are a Home Assistant statistics maintenance assistant.
The user wants to clean up, fix, or manage recorder statistics (the data shown in Settings > Developer Tools > Statistics).

CRITICAL RULES:
- Call EXACTLY ONE manage_statistics action per tool turn. NEVER call manage_statistics twice in one message.
- The validate action is READ-ONLY — call it without asking confirmation.
- fix_units and clear_orphaned already validate INTERNALLY — do NOT call validate first if you will call them.

STEPS:
1. Check the conversation history: if a previous [TOOL RESULT: manage_statistics] already exists,
   DO NOT call validate again. Skip directly to the appropriate action.
2. If the user explicitly asked to FIX / CORRECT units (e.g. 'correggi', 'fix', 'sistema', 'ripara')
   → call manage_statistics with action='fix_units' ONLY. It validates internally. ONE call.
3. If the user explicitly asked to REMOVE / CLEAN orphaned (e.g. 'rimuovi', 'elimina', 'pulisci', 'cancella')
   → call manage_statistics with action='clear_orphaned' ONLY. It validates internally. ONE call.
4. If the user asked both (e.g. 'trova e correggi tutto'): call clear_orphaned first, WAIT for the result,
   then call fix_units in the NEXT turn. One action per turn.
5. If the user just wants to see issues without fixing: call action='validate' ONLY.
6. If the user confirms with 'si', 'yes', 'ok', 'sì', 'procedi', 'fallo', 'vai': execute the
   action you proposed. Do NOT re-validate. Call the appropriate write action directly.
7. If the user wants to remove specific statistics: call action='clear' with the statistic_ids list.
8. After each action, ALWAYS list the specific entity_ids that were affected.
   Use a collapsible HTML block so the list doesn't take too much space:
   <details><summary>N entities affected (click to expand)</summary><div>
   <code>sensor.xxx</code><br><code>sensor.yyy</code><br>...</div></details>
9. Respond in the user's language.
- The ONLY tool you should use is manage_statistics. Do NOT call any other tool.
- NEVER call manage_statistics more than once per message/turn.""",

    # create_html_dashboard prompt is set separately due to its size (see INTENT_PROMPTS update below)
    "create_html_dashboard": None,  # Placeholder — set after dict definition

    # All other intents use the unified HA_SYSTEM_GUIDANCE prompt
    # (the LLM sees all tools and decides autonomously)
    "auto": HA_SYSTEM_GUIDANCE,
    # Follow-up intents (carried forward from previous_intent)
    "create_dashboard": HA_SYSTEM_GUIDANCE,
    "config_edit": HA_SYSTEM_GUIDANCE,
    "modify_automation": HA_SYSTEM_GUIDANCE,
    "modify_script": HA_SYSTEM_GUIDANCE,
    "modify_dashboard": HA_SYSTEM_GUIDANCE,
    "system_debug": HA_SYSTEM_GUIDANCE,
}

# ---- Set create_html_dashboard prompt separately (very long) ----
INTENT_PROMPTS["create_html_dashboard"] = """You are a creative Home Assistant HTML dashboard designer.
The user wants a UNIQUE, beautiful HTML dashboard page with real Home Assistant entities.

⚠️ CRITICAL OUTPUT RULE — READ FIRST:
- NEVER write HTML code as text in the chat. Not a single line. Not a snippet. Nothing.
- ALL HTML goes EXCLUSIVELY inside the 'html' parameter of the create_html_dashboard tool call.
- Your only text in the chat should be a single short sentence AFTER the tool completes,
  e.g. "Dashboard Tigo creata! Aprila qui: /local/dashboards/tigo.html"
- Violating this rule wastes tokens and confuses the user.

MODIFICATION MODE — If the message contains [CURRENT_DASHBOARD_HTML]:
- The full current HTML is already provided. Do NOT call read_html_dashboard.
- Modify the HTML as requested, preserving all existing sections, CSS, and JS.
- Call create_html_dashboard IMMEDIATELY with the complete modified HTML.
- Use the same name as shown in the CONTEXT tag (e.g. name="tigo").
- NEVER output any HTML as text — put it only in the tool call arguments.

MULTI-PAGE / MULTI-SECTION DETECTION — Ask the user BEFORE creating:
If the user request mentions multiple pages, sections, tabs, or areas (e.g. "luci, clima e sicurezza",
"3 pagine", "tab per ogni stanza", "sezioni diverse"), you MUST ask a clarifying question first:

  "Preferisci:
   A) **Una sola plancia** con tab interni HTML (navigazione via pulsanti nella pagina)
   B) **Plance separate** nel menu laterale di HA (una per ogni sezione)"

Wait for the user's answer before generating any HTML or calling any tool.
- If they choose A: create a single HTML file with a JS tab router (show/hide div sections).
- If they choose B: call create_html_dashboard once per section (each with a unique name/title).
Do NOT ask this question if the request is clearly for a single-page dashboard.

CREATION WORKFLOW (no [CURRENT_DASHBOARD_HTML] in message):
1. Call search_entities to find the correct entity_ids. NEVER guess entity_ids.
   If entities are already listed in the DATA section, skip search_entities.
2. Send the HTML in 2-3 CHUNKED tool calls (draft mode) to avoid output token limits:
   - Call 1: create_html_dashboard(title="...", name="slug", entities=[...], html="<!DOCTYPE html>...<style>CSS HERE</style></head><body>...", draft=true)
   - Call 2: create_html_dashboard(name="slug", html="...rest of template...", draft=true)
   - Call 3: create_html_dashboard(name="slug", html="...<script>Vue.createApp(...)...</script></body></html>")  ← NO draft = finalize
   Each chunk MUST be under 6000 characters. The tool concatenates all parts automatically.

CRITICAL: The HTML code MUST be passed as the value of the 'html' key in the tool call arguments.
Do NOT write HTML as text in your response — put it INSIDE the tool call arguments JSON.
Design a UNIQUE page every time — vary colors, layouts, typography, animations, card styles.

PLACEHOLDER REFERENCE (the tool replaces these in your HTML):
- __ENTITIES_JSON__ → JS array of entity_id strings, e.g. ["sensor.power","sensor.temp"] (MANDATORY)
- __TITLE__ → HTML-escaped title string
- __TITLE_JSON__ → JSON string of title (for JS: const title = __TITLE_JSON__)
- __ACCENT__ → hex color string, e.g. #22c55e
- __ACCENT_RGB__ → r,g,b string, e.g. 34,197,94 (for rgba())
- __THEME_CSS__ → CSS custom properties WITHOUT :root{} wrapper, e.g. --bg:#0f172a;--bg2:#1e293b;--text:#e2e8f0;--text2:#94a3b8;--card:rgba(30,41,59,.85);--border:#334155
  Usage: :root { __THEME_CSS__ } or define your own colors entirely.
- __LANG__ → language code (en/it/es/fr)
- __FOOTER__ → HTML-escaped footer text

IMPORTANT CSS RULES:
- Do NOT use var(--primary-background-color) or other HA frontend variables — they don't exist in /local/ iframes.
- Define ALL your colors directly in CSS or use __ACCENT__, __ACCENT_RGB__, __THEME_CSS__.
- The page is served at /local/dashboards/name.html (same-origin as HA, localStorage works).

JS DATA CONNECTION:
- Vue 3 CDN: <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
- Chart.js 4: <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
- Date adapter: <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
- Auth token + redirect if not logged in (ALWAYS use this pattern at the very start of your <script>):
    const tok = JSON.parse(localStorage.getItem('hassTokens')||'{}').access_token;
    if (!tok) { location.href = '/?redirect=' + encodeURIComponent(location.href); }
- WebSocket: connect to (location.protocol==='https:'?'wss:':'ws:')+'//'+location.host+'/api/websocket'
  → auth_required: send {type:'auth',access_token:token}
  → auth_ok: send {type:'subscribe_events',event_type:'state_changed'} + fetch /api/states with Bearer
  → IMPORTANT: on ws.onclose, ALWAYS reconnect with setTimeout(connectWs, 5000) — do NOT leave it disconnected
- REST fallback: GET /api/states with Authorization: Bearer <token>, poll every 5s while WS is not connected
- Service calls: POST /api/services/{domain}/{service} with Bearer token
- History: GET /api/history/period/{ISO_start}?filter_entity_id=...&end_time={ISO_end}&minimal_response&no_attributes

FETCHING ALL ENTITIES BY CATEGORY — use this pattern when the user asks for "all batteries", "all lights", etc.:
  const all = await fetch('/api/states', {headers:{Authorization:'Bearer '+tok}}).then(r=>r.json());
  // Battery sensors:  all.filter(s => s.attributes?.device_class === 'battery')
  // Temperature:      all.filter(s => s.attributes?.device_class === 'temperature')
  // Lights:           all.filter(s => s.entity_id.startsWith('light.'))
  NEVER hardcode a fixed list of entity_ids when the user asks for "all" of a category.

UI RULES:
- Do NOT show debug/technical info (connection status pills, token values, accent color hex, entity_id strings)
- The dashboard is for END USERS, not developers — show only useful data: entity values, labels, charts, status indicators
- A small colored dot (green=live, grey=offline) in the header is OK, but do NOT label it "WebSocket"/"REST"

DESIGN PHILOSOPHY — Make every dashboard look like it was designed by a professional UI designer:

🎨 COLORS & GRADIENTS (always — no flat/grey/white layouts ever):
Background: always a bold multi-stop gradient matching the mood of the dashboard theme.
Every card type gets its OWN accent gradient — NEVER a monotone grid of identical-looking cards.

PICK A COLOR IDENTITY based on what the dashboard is about, then build 4-5 complementary card accents:
  💡 Lights / ambiance   → warm: gold #f9ca24, amber #f0932b, peach #fd79a8, soft yellow
  🌡️ Climate / comfort   → cool: cyan #74b9ff, sky #0984e3, ice #dfe6e9, mint #55efc4
  🔋 Batteries / storage → electric: lime #badc58, green #6ab04c, teal #22a6b3, deep blue
  🪟 Blinds / shutters   → neutral-warm: sand #f8b739, brown #e17055, slate #636e72, warm grey
  🔌 Power / electrical  → tech: purple #6c5ce7, indigo #4834d4, violet #a29bfe, dark navy
  ☀️ Solar / energy      → solar: amber #f9ca24, orange #f0932b, grass-green #00b894, teal
  🔒 Security / alarm    → alert: crimson #d63031, orange-red #e17055, dark #2d3436, accent red
  🏠 Presence / rooms    → cozy: warm rose #fd79a8, mauve #e84393, soft purple #6c5ce7
  💧 Water / irrigation  → fresh: deep blue #0652DD, aqua #1289A7, cyan, soft teal
  🌬️ Air / ventilation   → airy: sky blue #74b9ff, light cyan, white-blue gradients
  🤖 Generic / mixed     → pick any 4 vivid contrasting hues — make it feel designed, not default

Rules:
- Background gradient: 2-3 stops, dark for dashboards with lots of data, lighter/warmer for control panels
- Card accent: 3px top border or left border with domain gradient (border-image or ::before strip)
- Chart colors: always multi-color datasets — never single-color bar charts
- Text hierarchy: white #fff for values, rgba(255,255,255,0.6) for labels, rgba(255,255,255,0.35) for units
- Use CSS variables: :root { --bg, --card, --accent, --text } and __ACCENT__ / __ACCENT_RGB__ placeholders

✨ WOW EFFECT (always):
- CSS animations on load: elements fade/slide in (opacity + transform), live values pulse, cards lift on hover
- Glassmorphism cards: backdrop-filter: blur(12px) + semi-transparent background + subtle border
- Smooth transitions on all interactive elements

📑 TABS (default for dashboards with 3+ distinct topics):
- Build a single-page tab router with a styled top navigation bar
- JS show/hide (display:none → grid/block) for instant switching — no page reload
- Active tab: accent-colored underline + highlighted background
- Each tab = one thematic group (e.g. Energia | Clima | Luci | Sicurezza)

🔍 POPUPS & DETAIL MODALS:
- ALWAYS add click-to-expand on entity cards — clicking a card shows a detail modal
- Use this pattern for HA native more-info:
    function openMoreInfo(entityId) {
      const haEl = document.querySelector('home-assistant') || parent?.document?.querySelector('home-assistant');
      if (haEl) {
        haEl.dispatchEvent(new CustomEvent('hass-more-info',
          { detail: { entityId }, bubbles: true, composed: true }));
        return;
      }
      showHistoryModal(entityId);  // fallback: custom modal with history chart
    }
- Add cursor:pointer to all entity cards and call openMoreInfo(entityId) on click
- Custom modals (for history charts, breakdowns, etc.): backdrop-blur overlay + centered card with × close button

📊 CHARTS — Be Creative, Use Variety:
Always include 2-4 charts per dashboard. Mix different chart types — never use only bars.
Choose the right chart for the data:

  BAR chart         → comparisons across items or time
                       e.g. power per panel, daily production, energy per room, water consumption per day
  LINE / AREA chart → trends over time with gradient fill, tension:0.4
                       e.g. temperature over 24h, battery charge curve, blinds usage frequency, light dimmer history
  DOUGHNUT / PIE    → distribution and shares
                       e.g. battery levels by device, light zones on/off share, circuit power split, room humidity split
  GAUGE (half-doughnut) → single KPI vs target: circumference:180, rotation:-90, cutout:'78%', CSS-overlaid number
                       e.g. battery %, HVAC efficiency, water tank level, overall security score, air quality index
  SCATTER chart     → correlation between two sensor values
                       e.g. temp vs humidity per room, signal vs battery level, brightness vs energy use
  RADAR chart       → multi-attribute per entity — great for comparing rooms or devices
                       e.g. rooms: temp/humidity/CO2/light/occupancy; devices: battery/signal/uptime/errors
  MIXED (bar+line)  → actual vs target on same axes
                       e.g. daily consumption bars + monthly goal line, production vs forecast
  STACKED BAR       → multi-source contribution per slot
                       e.g. solar+grid+battery per hour, room-by-room energy per day, device type breakdown

Rules:
- Always include at least one time-based LINE/AREA chart when history data is available (use /api/history/period/)
- Add a GAUGE for any single "how good is this?" KPI (efficiency, fill level, charge %)
- Add a DOUGHNUT for any "what's the share?" question
- Use gradient fills, animated on load (animation:{duration:800,easing:'easeOutQuart'})
- Dark backgrounds: use rgba colors with opacity for chart fills, bright solid for borders

🏗️ LAYOUT:
- CSS Grid with card hierarchy: hero KPI banner → visual charts/gauges → grouped detail cards
- Avoid flat lists of entity states — group by topic, use section titles with emoji icons
- Mix card sizes (wide hero, medium charts, small KPI pills)
- Place the most visually impactful chart (large line/area or mixed) as the hero element

INVENTIVENESS — Each dashboard should feel unique and purpose-built for its domain:
Always pick creative visual elements that match what the dashboard is about. Examples:

  💡 Lights:       color-swatch cards showing current RGB color, brightness slider visual, room map with lit/off overlay
  🔋 Batteries:    vertical fill-bar per battery (CSS animated), donut gauge per device, low-battery alert strip
  🪟 Blinds:       animated CSS shutter icon showing % open, grouped by room, one-click open-all/close-all buttons
  🌡️ Climate:      color-gradient temperature scale, room-by-room heat map, dew point indicator, comfort zone band on chart
  🔒 Security:     big status badge (ARMED/DISARMED) with color fill, door/window grid with open=red/closed=green dots
  ☀️ Solar:        Sankey-style energy flow (CSS arrows: panels→inverter→house/grid), production curve area chart
  🔌 Power/meters: live watt counter with pulse animation, stacked bar per circuit, cost estimate in real-time
  💧 Water:        fill-level gauge, consumption line chart, leak sensor status as colored alert cards
  🏠 Presence:     room occupancy grid (person icons, green=home/grey=away), last-seen timeline
  🌬️ Air/HVAC:     wind speed compass, AQI color scale, CO₂ trend with danger threshold line
  🤖 Mixed/general: hero summary strip + tabs per category + history charts per tab

Always add:
- Animated counters on KPI numbers (count up from 0 on load)
- Pulse ring or glow on any "live" value that updates in real-time
- Color-coded status dots (green=ok, amber=warning, red=alert) on every entity card
- Sortable table with inline mini-bar for any sensor array with 5+ similar items

DESIGN FREEDOM — vary these across dashboards:
- Color schemes: warm, cool, neon, pastel, monochrome, earth tones, gradients
- Card styles: glassmorphism, neumorphism, flat material, outlined, floating shadows
- Layouts: CSS Grid, masonry, bento grid, sidebar+main, full-width hero sections
- Typography: large stat numbers, condensed labels, accent fonts via Google Fonts
- Dark/light: use @media(prefers-color-scheme) or hardcode based on theme parameter

Respond in the user's language."""


def _init_dynamic_prompts():
    """Initialize prompts that depend on api.get_lang_text (called after api module is loaded)."""
    # Add language instruction to chat prompt
    lang_instr = api.get_lang_text("respond_instruction")
    if lang_instr and lang_instr not in INTENT_PROMPTS["chat"]:
        INTENT_PROMPTS["chat"] += "\n\n" + lang_instr


def detect_intent(user_message: str, smart_context: str, previous_intent: str | None = None) -> dict:
    """Detect user intent locally from the message and available context.
    Uses multilingual keywords from keywords.json based on LANGUAGE setting.
    Returns: {"intent": str, "tools": list[str], "prompt": str|None, "specific_target": bool}
    If intent is clear + specific target found, use focused mode (fewer tools, shorter prompt).
    Otherwise fall back to full mode."""
    # Ensure dynamic prompts are initialized
    _init_dynamic_prompts()

    # --- CARD EDITOR CONTEXT (from bubble) ---
    # The bubble injects [CONTEXT: User is editing a Lovelace card...] prefix.
    # Route immediately to the dedicated card_editor intent.
    if "[CONTEXT: User is editing a Lovelace card" in user_message:
        logger.info("Card editor context detected — routing to card_editor intent")
        return {"intent": "card_editor", "tools": INTENT_TOOL_SETS["card_editor"],
                "prompt": INTENT_PROMPTS.get("card_editor"), "specific_target": True}

    # --- STATISTICS PAGE CONTEXT (from bubble) ---
    if "[CONTEXT: User is on the Home Assistant Statistics page" in user_message:
        logger.info("Statistics page context detected — routing to manage_statistics intent")
        return {"intent": "manage_statistics", "tools": INTENT_TOOL_SETS["manage_statistics"],
                "prompt": INTENT_PROMPTS.get("manage_statistics"), "specific_target": True}

    # Strip bubble context prefix and embedded HTML before keyword matching
    clean_msg = user_message
    # Remove [CURRENT_DASHBOARD_HTML]...[/CURRENT_DASHBOARD_HTML] block
    if "[CURRENT_DASHBOARD_HTML]" in clean_msg:
        clean_msg = re.sub(r'\[CURRENT_DASHBOARD_HTML\][\s\S]*?\[/CURRENT_DASHBOARD_HTML\]', '', clean_msg)
    # Remove [CONTEXT: ...] prefix — use rfind to handle nested brackets
    # (e.g. [TOOL RESULT] inside the context text)
    if clean_msg.startswith("[CONTEXT:"):
        bracket_end = clean_msg.rfind("] ")
        if bracket_end == -1:
            bracket_end = clean_msg.rfind("]")
        if bracket_end != -1:
            clean_msg = clean_msg[bracket_end + 1:]
    msg = clean_msg.strip().lower()
    has_yaml_fence = "```yaml" in msg or "```yml" in msg
    has_html_fence = "```html" in msg

    # --- LOVELACE YAML CARD (high-priority guard) ---
    # If the user pasted a Lovelace YAML card and is asking to improve/beautify that card,
    # we must route to card_editor (even if previous intent was create_html_dashboard).
    has_lovelace_yaml = (
        ("type:" in msg)
        and (
            "cards:" in msg
            or "custom:" in msg
            or "entity:" in msg
            or "- type:" in msg
        )
    ) or bool(re.search(r"(?mi)^\s*type\s*:\s*", user_message))
    explicit_html_request = any(
        k in msg for k in [
            "/local/dashboards",
            ".html",
            "dashboard html",
            "html dashboard",
            "pagina html",
            "crea una dashboard html",
            "create html dashboard",
        ]
    )
    card_edit_signals = any(
        k in msg for k in [
            "questa card",
            "questa scheda",
            "abbellisci",
            "migliora questa card",
            "migliora la card",
            "sistema questa card",
            "fix this card",
            "improve this card",
            "beautify this card",
        ]
    )
    if (has_yaml_fence or has_lovelace_yaml) and (card_edit_signals or not explicit_html_request):
        logger.info("Lovelace YAML detected (high-priority) — routing to card_editor intent")
        return {
            "intent": "card_editor",
            "tools": INTENT_TOOL_SETS["card_editor"],
            "prompt": INTENT_PROMPTS.get("card_editor"),
            "specific_target": False,
        }

    # --- EXPLICIT HTML BLOCK (high-priority guard) ---
    # If the user pasted an HTML fenced block, treat it as HTML dashboard context.
    if has_html_fence:
        logger.info("HTML fenced block detected — routing to create_html_dashboard intent")
        return {
            "intent": "create_html_dashboard",
            "tools": INTENT_TOOL_SETS["create_html_dashboard"],
            "prompt": INTENT_PROMPTS.get("create_html_dashboard"),
            "specific_target": True,
        }

    # --- CONFIRMATION CONTINUITY ---
    # Short confirmation replies ("si", "sì", "yes", "ok") should carry forward the previous intent
    # so the model stays in the same focused mode (e.g. config_edit with confirmation prompt)
    # Build confirmation words from all languages in keywords.json
    confirm_words = set()
    for lang_data in api.KEYWORDS.values():
        confirm_words.update(lang_data.get("confirm", []))
    stripped = msg.strip().rstrip("!?.,;:")
    if previous_intent and previous_intent not in ("generic", "chat") and stripped in confirm_words:
        intent_key = previous_intent
        if intent_key in INTENT_TOOL_SETS:
            logger.info(f"Confirmation detected ('{stripped}') — carrying forward intent: {intent_key}")
            return {"intent": intent_key, "tools": INTENT_TOOL_SETS[intent_key],
                    "prompt": INTENT_PROMPTS.get(intent_key), "specific_target": False}

    # --- FOLLOW-UP CONTINUITY ---
    # If previous intent was specific and current message is a follow-up instruction
    # (e.g. "modificala", "usa le stesse entità", "aggiungi un grafico"),
    # carry forward the intent. This handles multi-turn conversations.
    FOLLOW_UP_INTENTS = {"create_html_dashboard", "create_dashboard", "config_edit",
                         "modify_automation", "modify_script", "modify_dashboard",
                         "system_debug"}
    if previous_intent and previous_intent in FOLLOW_UP_INTENTS:
        # system_debug: carry forward for short selection messages ("il 3", "5", "analizza il primo")
        if previous_intent == "system_debug":
            import re as _re_intent
            # Match messages that are just a number, or contain selection patterns
            if _re_intent.match(r'^\\s*\\d+\\s*$', msg) or any(s in msg for s in [
                "analizza", "vedi", "mostra", "dettaglio", "investig", "il primo", "il secondo",
                "numero", "entry", "errore", "analyze", "show", "detail", "investigate",
                "analyse", "montre", "détail", "analiza", "muestra", "detalle"
            ]):
                logger.info(f"Debug selection detected — carrying forward system_debug intent")
                return {"intent": "system_debug", "tools": INTENT_TOOL_SETS["system_debug"],
                        "prompt": INTENT_PROMPTS.get("system_debug"), "specific_target": False}

        # Check if message looks like a follow-up (modify, use same, add, etc.)
        follow_up_signals = ["modifica", "modificala", "modificalo", "cambia", "aggiungi",
                             "inserisci", "togli", "rimuovi", "usa le stess", "stesse entit",
                             "stessi sensor", "gli stessi", "le stesse", "modify it", "change it",
                             "add", "remove", "use the same", "same entities", "same sensors",
                             "modifie", "change", "ajoute", "utilise les même",
                             "modifica", "cambia", "añade", "usa los mismos"]
        if any(s in msg for s in follow_up_signals):
            logger.info(f"Follow-up detected — carrying forward intent: {previous_intent}")
            return {"intent": previous_intent, "tools": INTENT_TOOL_SETS[previous_intent],
                    "prompt": INTENT_PROMPTS.get(previous_intent), "specific_target": False}

    # --- HTML DASHBOARD CONTEXT (from bubble or keywords) ---
    # The bubble injects [CURRENT_DASHBOARD_HTML] when editing an existing HTML dashboard.
    if "[CURRENT_DASHBOARD_HTML]" in user_message:
        logger.info("HTML dashboard context detected (embedded HTML) — routing to create_html_dashboard")
        return {"intent": "create_html_dashboard", "tools": INTENT_TOOL_SETS["create_html_dashboard"],
                "prompt": INTENT_PROMPTS.get("create_html_dashboard"), "specific_target": True}

    # Get keywords for current language, fallback to English if not available
    lang_keywords = api.KEYWORDS.get(api.LANGUAGE, api.KEYWORDS.get("en", {}))

    # --- CHAT (greetings, chitchat) --- short messages that don't need tools
    chat_kw = lang_keywords.get("chat", [])
    words = msg.strip().rstrip("!?.,").split()
    if len(words) <= 5 and any(k in msg for k in chat_kw):
        return {"intent": "chat", "tools": INTENT_TOOL_SETS["chat"],
                "prompt": INTENT_PROMPTS["chat"], "specific_target": False, "max_rounds": 1}

    # --- LOVELACE YAML CARD (manual paste) ---
    # Already handled above with high priority, before follow-up continuity.

    # --- HTML DASHBOARD CREATION/MODIFICATION (kept for specialized prompt) ---
    # The create_html_dashboard prompt is very specific (~100 lines of CSS/JS/Vue guidance)
    # so we keep keyword detection for it rather than relying on the LLM alone.
    html_keywords = ["html", "vue", "javascript", "js", "react", "svelte",
                     "interattiv", "realtime", "responsive", "custom css",
                     "custom design", "pannello web", "pagina web", "pagina live",
                     "pannello live", "plancia", "bento"]
    dash_kw = lang_keywords.get("dashboard", [])
    def _kw_in_msg(_msg: str, _kw: str) -> bool:
        # Avoid false positives for short tokens like "js" inside other words.
        if len(_kw) <= 3:
            return bool(re.search(rf"(?<![a-z0-9_]){re.escape(_kw)}(?![a-z0-9_])", _msg))
        return _kw in _msg

    has_html_kw = any(_kw_in_msg(msg, k) for k in html_keywords)
    has_dash = any(k in msg for k in dash_kw)
    has_html_ref = any(k in msg for k in ["/local/dashboards", ".html"])
    if not has_html_ref and smart_context:
        has_html_ref = "/local/dashboards" in smart_context or ".html" in smart_context
    if not has_html_ref:
        try:
            _dash_dir = os.path.join(api.HA_CONFIG_DIR, "www", "dashboards")
            if os.path.isdir(_dash_dir):
                _existing_html = {f[:-5].lower() for f in os.listdir(_dash_dir) if f.endswith(".html")}
                if _existing_html & set(re.findall(r"[\w-]+", msg)):
                    has_html_ref = True
                    has_dash = True
        except Exception:
            pass
    if has_html_kw or has_html_ref or (has_dash and has_html_kw):
        logger.info("HTML dashboard keywords detected — routing to create_html_dashboard")
        return {"intent": "create_html_dashboard", "tools": INTENT_TOOL_SETS["create_html_dashboard"],
                "prompt": INTENT_PROMPTS.get("create_html_dashboard"), "specific_target": False}

    # --- STATISTICS MANAGEMENT (kept for specialized one-call-per-turn prompt) ---
    statistics_manage_kw = lang_keywords.get("statistics_manage", [])
    has_stats_word = any(k in msg for k in ["statistich", "statistic", "estadístic", "statistique"])
    delete_kw = lang_keywords.get("delete", [])
    modify_kw = lang_keywords.get("modify", [])
    has_manage_signal = any(k in msg for k in delete_kw + modify_kw) or any(
        k in msg for k in ["non esist", "orfan", "orphan", "obsolet", "puliz", "clean", "purge",
                           "correggi", "fix", "converti", "convert", "valuta", "unità", "unit"])
    if any(k in msg for k in statistics_manage_kw) or (has_stats_word and has_manage_signal):
        return {"intent": "manage_statistics", "tools": INTENT_TOOL_SETS["manage_statistics"],
                "prompt": INTENT_PROMPTS["manage_statistics"], "specific_target": False}

    # --- LLM-FIRST: all other requests get ALL tools + unified guidance ---
    # The LLM sees every available tool and decides autonomously what to call.
    # No keyword-based intent routing — the model chooses the right tools natively.
    logger.info("LLM-first mode — all tools available, LLM decides autonomously")
    return {"intent": "auto", "tools": INTENT_TOOL_SETS.get("auto"),
            "prompt": HA_SYSTEM_GUIDANCE, "specific_target": False}

def get_tools_for_intent(intent_info: dict, provider: str = "anthropic") -> list:
    """Get tool definitions filtered by intent.
    tools=None → all tools (LLM-first mode / auto intent)
    tools=[]  → no tools (chat intent)
    tools=[...] → filtered subset (card_editor, manage_statistics, etc.)
    """
    import tools as _tools

    tool_names = intent_info.get("tools")

    # tools=None → LLM-first mode: return ALL tools
    if tool_names is None:
        if provider == "anthropic":
            return _tools.get_anthropic_tools()
        elif provider in ("openai", "github", "nvidia"):
            return _tools.get_openai_tools_for_provider()
        return _tools.get_anthropic_tools()

    # tools=[] → chat intent: no tools needed
    if len(tool_names) == 0:
        return []

    # tools=[...] → filter to specified subset
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
    # Tight-context providers/models need shorter history to stay within token limits
    _TIGHT_PROVIDERS = {"github", "groq"}
    model = (api.get_active_model() or "").lower()
    is_tight = api.AI_PROVIDER in _TIGHT_PROVIDERS or "nano" in model
    limit = 6 if is_tight else max_messages
    # Extra-small models: keep even fewer turns
    try:
        if is_tight and any(tag in model for tag in ("o4-mini", "nano", "mini")):
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
    # Final safety: remove any orphaned tool messages (tool without preceding
    # assistant+tool_calls or another tool) that survived trimming.
    validated = []
    for m in trimmed:
        if m.get("role") == "tool":
            if not validated:
                continue
            prev = validated[-1]
            if prev.get("role") == "tool" or (prev.get("role") == "assistant" and prev.get("tool_calls")):
                validated.append(m)
            # else: orphaned — skip
        else:
            validated.append(m)
    return validated


# ---- Smart context builder ----

MAX_SMART_CONTEXT = 25000  # Max chars to inject — keeps tokens under control


def build_smart_context(user_message: str, intent: str = None, max_chars: int = None) -> str:
    """Pre-load relevant context based on user's message intent.
    Works like VS Code: gathers all needed data BEFORE sending to AI,
    so the LLM can respond with fewer tool rounds.
    IMPORTANT: Context must be compact to avoid rate limits.

    Args:
        max_chars: Override the default MAX_SMART_CONTEXT cap. Useful when the message
                   already contains large blocks (e.g. [CURRENT_DASHBOARD_HTML]) so the
                   combined payload stays within model context limits.
    """
    msg_lower = user_message.lower()
    context_parts = []

    try:
        # --- AUTOMATION CONTEXT ---
        auto_keywords = ["automazione", "automation", "automazion", "trigger", "condizione", "condition"]
        force_automation_context = intent == "modify_automation"
        if force_automation_context or any(k in msg_lower for k in auto_keywords):
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

            # ── Priority 1: explicit automation_id from bubble context prefix ──────
            # The bubble injects [CONTEXT: User is viewing automation id="<id>". ...]
            # Parse this directly — no fuzzy matching needed.
            _ctx_id_m = re.search(
                r'\[CONTEXT:[^\]]*automation\s+id=["\x27]*(\d+)',
                user_message,
                re.IGNORECASE,
            )
            if _ctx_id_m:
                _ctx_id = _ctx_id_m.group(1)
                # Verify it exists in the state list
                _ctx_match = next((a for a in auto_list if str(a.get("id", "")) == _ctx_id), None)
                if _ctx_match:
                    target_auto_id = _ctx_id
                    target_auto_alias = _ctx_match.get("friendly_name", "")
                    logger.info(f"Smart context: using bubble context automation id='{target_auto_id}' ('{target_auto_alias}')")

            # ── Priority 2: fuzzy matching of automation name in message ──────────
            if not target_auto_id:
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
                if target_auto_id:
                    break  # already found via context prefix — skip fuzzy loop
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

            _bm = locals().get("best_match")
            _bs = locals().get("best_score", 0)
            if not target_auto_id and _bm and _bs >= 5:
                target_auto_id = _bm.get("id", "")
                target_auto_alias = _bm.get("friendly_name", "")
                logger.info(f"Smart context: matched automation '{target_auto_alias}' (score: {_bs})")

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
                        # Priority 1: explicit script_id from bubble context prefix
                        _ctx_sid_m = re.search(
                            r'\[CONTEXT:[^\]]*script\s+id=["\x27]*([^\s"\x27>\]]+)',
                            user_message,
                            re.IGNORECASE,
                        )
                        _ctx_sid = _ctx_sid_m.group(1) if _ctx_sid_m else None

                        _script_found = False
                        for sid, sconfig in all_scripts.items():
                            alias = str(sconfig.get("alias", "")).lower() if isinstance(sconfig, dict) else ""
                            # Match by context script_id, alias, or fuzzy word match
                            if (_ctx_sid and (sid == _ctx_sid or alias == _ctx_sid.lower())) or \
                               (not _ctx_sid and alias and (
                                   alias in msg_lower or sid in msg_lower
                                   or any(word in alias for word in msg_lower.split() if len(word) > 4)
                               )):
                                script_yaml = yaml.dump({sid: sconfig}, default_flow_style=False, allow_unicode=True)
                                if len(script_yaml) > 6000:
                                    script_yaml = script_yaml[:6000] + "\n... [TRUNCATED]"
                                context_parts.append(api.tr("smart_context_script_found", alias=sconfig.get('alias', sid), sid=sid, yaml=script_yaml))
                                _script_found = True
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

        # --- INTEGRATION-SPECIFIC ENTITY CONTEXT (for create_html_dashboard and generic searches) ---
        # Extract device/integration keywords from the message (e.g. "epcube", "shelly", "tasmota")
        # These are words that don't match stop-words and likely refer to an integration or device name.
        # IMPORTANT: strip [CONTEXT:...] and [CURRENT_DASHBOARD_HTML]...[/CURRENT_DASHBOARD_HTML] blocks
        # BEFORE keyword extraction — these contain HTML/CSS that would generate thousands of false matches.
        # The CONTEXT block may contain nested brackets (e.g. [TOOL RESULT]) so we find the last '] '
        _clean_user_msg = user_message
        if _clean_user_msg.startswith("[CONTEXT:"):
            _ctx_end = _clean_user_msg.rfind("] ")
            if _ctx_end == -1:
                _ctx_end = _clean_user_msg.rfind("]")
            if _ctx_end != -1:
                _clean_user_msg = _clean_user_msg[_ctx_end + 1:]
        _clean_user_msg = re.sub(
            r'\[CURRENT_DASHBOARD_HTML\][\s\S]*?\[/CURRENT_DASHBOARD_HTML\]', '',
            _clean_user_msg, flags=re.IGNORECASE
        )
        _clean_msg_lower = _clean_user_msg.lower()

        _ctx_stop = {"mi", "crei", "crea", "una", "un", "la", "il", "con", "i", "de", "dei", "degli",
                     "delle", "del", "le", "sensori", "sensore", "di", "e", "pagina", "html", "web",
                     "per", "make", "create", "page", "dashboard", "pannello", "plancia", "scheda",
                     "tutti", "tutte", "the", "and", "with", "for", "all", "my", "miei", "mie",
                     "fotovoltaico", "energia", "energy", "solar", "solare", "impianto", "sono",
                     "voglio", "vorrei", "puoi", "fammi", "bello", "bella", "mostra", "vedi",
                     "which", "that", "this", "show", "see", "have", "about",
                     "aggiungi", "aggiunge", "modify", "modifica", "anche", "pure"}
        _msg_words = [w for w in re.sub(r'[^\w\s]', ' ', _clean_msg_lower).split()
                      if len(w) >= 4 and w not in _ctx_stop]

        # Try to find integration-specific entities if user mentions a device/brand
        _integration_matches = []
        # device_class aliases: IT/EN keyword → HA device_class attribute values.
        # When a keyword maps to a device_class, we filter ONLY by real HA
        # attribute (not by substring in entity_id) — this is 100% accurate
        # and avoids false positives (e.g. "bat" matching "sabato").
        _device_class_aliases = {
            "batterie": ["battery"],
            "batteria": ["battery"],
            "battery": ["battery"],
            "temperatura": ["temperature"],
            "temperature": ["temperature"],
            "umidità": ["humidity"],
            "humidity": ["humidity"],
            "consumo": ["energy", "power"],
            "consumption": ["energy", "power"],
            "energia": ["energy"],
            "energy": ["energy"],
            "potenza": ["power"],
            "power": ["power"],
            "tensione": ["voltage"],
            "voltage": ["voltage"],
            "corrente": ["current"],
            "current": ["current"],
            "luminosità": ["illuminance"],
            "illuminance": ["illuminance"],
            "pressione": ["pressure"],
            "pressure": ["pressure"],
            "velocità": ["speed"],
            "speed": ["speed"],
            "movimento": ["motion", "occupancy"],
            "motion": ["motion", "occupancy"],
            "presenza": ["motion", "occupancy", "presence"],
            "occupancy": ["occupancy"],
        }
        if _msg_words and (intent == "create_html_dashboard" or any(k in msg_lower for k in entity_keywords)):
            try:
                all_states = api.get_all_states()
                for keyword in _msg_words:
                    _device_classes = _device_class_aliases.get(keyword, [])
                    if _device_classes:
                        # ---- DEVICE CLASS MODE ----
                        # Keyword maps to a known device_class → filter ONLY by
                        # the real HA attribute.  Zero false positives.
                        matched = [
                            {"entity_id": s.get("entity_id"),
                             "state": s.get("state"),
                             "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                             "unit": s.get("attributes", {}).get("unit_of_measurement", ""),
                             "device_class": s.get("attributes", {}).get("device_class", "")}
                            for s in all_states
                            if s.get("attributes", {}).get("device_class", "") in _device_classes
                        ]
                        if matched:
                            _integration_matches.extend(matched)
                            logger.info(f"Smart context: found {len(matched)} entities with device_class in {_device_classes} (keyword '{keyword}')")
                    else:
                        # ---- KEYWORD MODE (fallback) ----
                        # No device_class mapping → search entity_id / friendly_name.
                        # Used for brands, room names, custom terms, etc.
                        matched = [
                            {"entity_id": s.get("entity_id"),
                             "state": s.get("state"),
                             "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                             "unit": s.get("attributes", {}).get("unit_of_measurement", ""),
                             "device_class": s.get("attributes", {}).get("device_class", "")}
                            for s in all_states
                            if keyword in s.get("entity_id", "").lower()
                            or keyword in s.get("attributes", {}).get("friendly_name", "").lower()
                        ]
                        if matched:
                            _integration_matches.extend(matched)
                            logger.info(f"Smart context: found {len(matched)} entities matching keyword '{keyword}' in entity_id/name")

                # Deduplicate by entity_id
                _seen = set()
                _deduped = []
                for e in _integration_matches:
                    if e["entity_id"] not in _seen:
                        _seen.add(e["entity_id"])
                        _deduped.append(e)
                _integration_matches = _deduped
            except Exception as _e:
                logger.warning(f"Smart context: integration entity search failed: {_e}")

        # ALWAYS also search entity registry by platform name when keywords are present.
        # Keyword search may miss entities whose names don't contain the brand word
        # (e.g. Tigo solar panels: "tigo" is in platform="tigo_energy" but not in entity names,
        #  EPCube: "epcube" is in platform but entity_ids may differ).
        # This prevents the AI from hallucinating entity IDs when no matches are found.
        # Previously this only ran for create_html_dashboard — now it runs for ALL intents
        # that trigger entity search (any intent with entity_keywords or _msg_words).
        if _msg_words and (intent == "create_html_dashboard" or any(k in msg_lower for k in entity_keywords)):
            try:
                reg_result = api.call_ha_websocket("config/entity_registry/list")
                registry = reg_result.get("result", []) if isinstance(reg_result, dict) else []
                if registry:
                    all_states_reg = api.get_all_states()
                    state_map_reg = {s.get("entity_id"): s for s in all_states_reg}

                    # Also resolve config_entry titles for broader matching
                    # (e.g. user says "epcube" → config_entry title "EPCube" → match by entry_id)
                    _matched_entry_ids: set = set()
                    try:
                        cfg_result = api.call_ha_websocket("config_entries/get_entries")
                        cfg_entries = cfg_result.get("result", []) if isinstance(cfg_result, dict) else []
                        for ce in cfg_entries:
                            ce_domain = (ce.get("domain") or "").lower()
                            ce_title = (ce.get("title") or "").lower()
                            for keyword in _msg_words:
                                if keyword in ce_domain or keyword in ce_title:
                                    _matched_entry_ids.add(ce.get("entry_id", ""))
                    except Exception:
                        pass  # optional — platform match is enough

                    for keyword in _msg_words:
                        reg_matches = [
                            r for r in registry
                            if keyword in (r.get("platform") or "").lower()
                            or (_matched_entry_ids and r.get("config_entry_id") in _matched_entry_ids)
                        ]
                        for r in reg_matches:
                            eid = r.get("entity_id", "")
                            state = state_map_reg.get(eid, {})
                            _integration_matches.append({
                                "entity_id": eid,
                                "state": state.get("state", "unavailable"),
                                "friendly_name": (
                                    state.get("attributes", {}).get("friendly_name")
                                    or r.get("name") or r.get("original_name") or ""
                                ),
                                "unit": state.get("attributes", {}).get("unit_of_measurement", ""),
                                "device_class": state.get("attributes", {}).get("device_class", ""),
                            })
                        if reg_matches:
                            logger.info(f"Smart context: registry search found {len(reg_matches)} entities for platform '{keyword}'")
                    # Deduplicate
                    _seen2 = set()
                    _deduped2 = []
                    for e in _integration_matches:
                        if e["entity_id"] not in _seen2:
                            _seen2.add(e["entity_id"])
                            _deduped2.append(e)
                    _integration_matches = _deduped2
            except Exception as _e:
                logger.warning(f"Smart context: entity registry search failed: {_e}")

        if _integration_matches:
            # Cap to 80 entities to avoid bloating context; use compact JSON when list is large
            _capped = _integration_matches[:80]
            _ent_json = (json.dumps(_capped, ensure_ascii=False, separators=(',', ':'))
                         if len(_capped) > 20
                         else json.dumps(_capped, ensure_ascii=False, indent=1))
            _extra = f" [mostrando prime {len(_capped)}]" if len(_integration_matches) > 80 else ""
            context_parts.append(
                f"## ENTITÀ TROVATE (keyword: {', '.join(_msg_words[:5])}, totale: {len(_integration_matches)}){_extra}\n"
                + _ent_json
            )
            # Save entity_ids for tools.py to use as authoritative fallback
            # when the AI passes garbage in the entities[] tool argument
            api._last_smart_context_entity_ids = [e["entity_id"] for e in _capped if e.get("entity_id")]
        elif matched_domains:
            # Fallback: generic domain entities (for non-integration requests)
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
        if max_chars is not None:
            # Caller-supplied override (e.g. when [CURRENT_DASHBOARD_HTML] is already in the message)
            limit = max_chars
        else:
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
