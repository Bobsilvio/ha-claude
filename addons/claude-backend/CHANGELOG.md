# Changelog
## 3.15.6 — Backup Download Feature
- **NEW**: Download any backup directly from the Backups tab
  - Each backup now has a Download button (next to Restore/Delete)
  - Downloads as `.bak` file with timestamp (e.g., `automations.yaml.20260220_143022.bak`)
  - Works for all backup types (automations, scripts, dashboards, etc.)
  - Translations added for EN/IT/ES/FR

## 3.15.5 — Automation Description Sync Fix
- **FIX**: **Automation descriptions now update when triggers change**
  - When modifying automation triggers without providing a new description, the old description is cleared
  - AI is now instructed to always include a NEW description when modifying trigger times
  - Prevents stale descriptions (e.g., "Turn on light at 21:00" staying when time changed to 22:00)
  - Works for both YAML-based and UI-created automations

## 3.15.4 — Bug Fixes
- **FIX**: Bubble conversations in sidebar now show proper date grouping (Today, Yesterday, etc.)
  - Correctly extracts timestamp from bubble session IDs (base36 decoding)
  - Groups by date just like Chat UI conversations
- **FIX**: Remove duplicate `const savedPos` declaration that caused JS SyntaxError

## 3.15.3 — History Cleanup & Polish
- **FIX**: **History cleanup** — HTML dashboard context blocks no longer clutter conversation history
  - `[CONTEXT:...]` and `[CURRENT_DASHBOARD_HTML]...[/CURRENT_DASHBOARD_HTML]` blocks are stripped before saving messages
  - Chat conversation view now shows only user questions, not the large HTML content
- **FIX**: **Dashboard success messages now translated** in EN/IT/ES/FR (was always responding in English)
  - "Dashboard created successfully!" translated with proper language support
  - Sidebar path message also localized
- **IMPROVED**: **Bubble button positioning** — now stays at `bottom-right` even when resizing browser window
  - Uses relative positioning (`bottom` / `right`) instead of absolute coordinates
  - If manually dragged, saves exact position and restores it on reload
  - If never dragged, always defaults to bottom-right (doesn't get stuck off-screen)

## 3.15.2 — Bubble Confirmation Buttons & Resize Fix
- **NEW**: Chat bubble now shows Sì/No confirmation buttons when AI asks for confirmation
  - Pattern detection (IT/EN/ES/FR): "Confermi?", "vuoi eliminare?", "yes or no?", etc.
  - Yes/No buttons styled with emojis (✅/❌), hover effects, and disable state
  - Auto-sends user's choice as message — no typing needed
  - Same patterns as Chat UI for consistency
- **FIX**: Chat bubble fixed off-screen when resizing viewport
  - Dragged button position now clamped on window resize (min 8px margin)
  - If panel is open, repos as well
  - Startup validates saved position against current viewport

## 3.15.1 — Bubble Working Indicator
- **NEW**: Chat bubble now shows detailed working indicator during AI processing
  - Animated dots with elapsed time counter (e.g., "Thinking... (12s)")
  - Tool call steps shown as list (e.g., "search_entities", "create_automation")
  - Status messages visible (e.g., "Anthropic: rate limit, waiting 6s...")
  - Thinking indicator stays visible until first response token arrives
- **FIX**: Status events (rate-limit waits, retries) were invisible in bubble — `thinkingEl` was removed too early

## 3.15.0 — Backup Management & Config Descriptions
- **NEW**: Delete backups from the UI — each backup now has a delete button (with confirmation)
- **NEW**: `max_snapshots_per_file` config option — set max backup snapshots per file (default 5). Oldest auto-deleted when limit is reached. Applies per-file (e.g., 5 for automations.yaml, 5 for scripts.yaml)
- **NEW**: `max_conversations` config option — set max chat conversations in history (1-100, default 10)
- **NEW**: Full config descriptions in all 4 languages (EN/IT/ES/FR) via `translations/*.yaml` — all options now show name and description in the addon configuration page
- **NEW**: `DELETE /api/snapshots/<id>` API endpoint for programmatic backup deletion
- **IMPROVED**: README updated with chat bubble, backup management, and new config options

## 3.14.2
- **FIX**: Bubble conversations in sidebar don't show selection highlight when clicked
  - After loading a conversation, re-render the active tab (chat or bubble) to update highlight
  - Bubble list now always refreshes from API (was using stale cached data)

## 3.14.1
- **FIX**: Intent detection misrouted HTML dashboard edits as `modify_script`
  - Root cause: embedded `<script>` tags in `[CURRENT_DASHBOARD_HTML]` triggered "script" keyword match
  - Fix: strip `[CONTEXT:...]` prefix and `[CURRENT_DASHBOARD_HTML]...[/CURRENT_DASHBOARD_HTML]` block before keyword matching
  - Added early detection: messages with embedded HTML dashboard context auto-route to `create_html_dashboard`
- **FIX**: `read_html_dashboard` added to `create_html_dashboard` tool set (was missing from intent tools)
- **FIX**: Log truncation — messages >500 chars are truncated in logs (no more full HTML dumps)

## 3.14.0 — HTML Dashboard Edit from Bubble
- **FIX**: Bubble now correctly detects HTML dashboard pages
  - Shadow DOM iframe walk + URL path fallback (caches dashboard names from `/custom_dashboards`)
  - Works on custom URL paths like `/clima-fotovoltaico/` (not just `/lovelace/`)
- **FIX**: AI now knows about `read_html_dashboard` — added to system prompt under "HTML Dashboard Management"
  - Instructs AI to always read current HTML first, then modify keeping same style
- **IMPROVED**: Context prefix for HTML dashboards includes instruction to use `read_html_dashboard` + `create_html_dashboard` with same name

## 3.13.9
- **FIX**: Agent/provider selector not loading in bubble — missing `credentials:'same-origin'` on fetch calls to `/api/get_models`, `/api/set_model`, and `/api/chat/abort`

## 3.13.8
- **FIX**: Chat bubble hidden by health check — removed overly aggressive `/api/status` check that failed through ingress, cleanup on disable is handled by `cleanup_chat_bubble()` instead

## 3.13.7
- **NEW**: HTML dashboard context awareness in chat bubble
  - Bubble detects when user is on an HTML dashboard page (walks Shadow DOM to find iframe)
  - Fetches the full HTML source and passes it as context to the AI
  - AI can modify the dashboard keeping the same style/design/colors
  - Works with custom URL paths (e.g., `/clima-fotovoltaico/`) not just `/lovelace/`
- **NEW**: `read_html_dashboard` tool — AI can read an existing HTML dashboard's source code
- **NEW**: `/api/dashboard_html/<name>` endpoint — returns dashboard HTML as JSON

## 3.13.6
- **FIX**: Chat bubble setup crash — `surrogates not allowed` UTF-8 encoding error
  - Surrogate pair `\uD83D\uDDD1` in confirmation buttons caused write failure
  - Fixed invalid Python escape sequences (`\s`, `\?`) in JS regex patterns inside f-string

## 3.13.5
- **FIX**: Chat bubble hidden on mobile devices (companion app) — prevents accidental opens on touch

## 3.13.4
- **FIX**: Chat bubble now properly cleans up when disabled or addon is removed
  - When `enable_chat_bubble` is set to `false`: Lovelace resource is deregistered and JS file is deleted on next startup
  - When addon is removed/stopped: JS health check detects unreachable addon and auto-hides the bubble
  - No more ghost bubbles persisting after disabling the feature

## 3.13.3
- **FIX**: Entity validation in `create_automation` and `update_automation` — AI can no longer use non-existent entity_ids
  - Recursively extracts all entity_id references from triggers, conditions, and actions
  - Validates against Home Assistant's actual entity registry before creating/updating
  - Returns error with suggestions if invalid entities are found (e.g., `switch.luce_bagno` → `switch.switch_luce_bagno_piccolo`)
  - Fix: moved `_extract_entity_ids` to module level (was scoped inside `create_automation`, causing NameError in `update_automation`)

## 3.13.2
- **FIX**: Bubble button now draggable immediately (touch and drag, 5px threshold) — replaced broken long-press mechanism
- **NEW**: Live agent/provider selector in chat bubble — two dropdowns (Provider + Model) below the header
  - Fetches available providers and models from `/api/get_models` on open
  - Switching provider auto-loads its models and calls `/api/set_model`
  - Switching model applies immediately — no addon restart needed

## 3.13.1
- **FIX**: Chat bubble not loading — Lovelace resource registration was broken
  - Root cause: `call_ha_websocket` returns `{"type":"result","result":[...]}` but code checked `isinstance(result, list)` → always `False`, resource never found/updated
  - Fix: properly extract `result` from WS response dict
  - Changed `res_type` from `"module"` to `"js"` (IIFE script, not ES module)
  - Added content-hash cache-busting (`?v=VERSION&h=HASH`) to force browser reload on updates
  - Added duplicate resource cleanup (removes extra registrations from previous broken attempts)
  - After update: go to HA → Settings → Dashboards → Resources, delete any duplicate `ha-claude-chat-bubble` entries, then restart the addon

## 3.13.0 — Chat Bubble V2: Markdown, Voice, Quick Actions, Abort
- **Markdown rendering**: AI responses now render bold, italic, code blocks, inline code, lists, links, headers
- **Message history persistence**: chat messages survive page reload (stored in localStorage, last 50 messages)
- **Voice input**: microphone button using Web Speech API — tap to speak, auto-sends on recognition end; supports en/it/es/fr
- **Quick action chips**: context-based suggestion buttons appear when relevant:
  - Automation: "Analyze", "Optimize", "Add condition", "Fix errors"
  - Script: "Analyze", "Optimize", "Explain"
  - Dashboard: "Describe", "Add entities", "Optimize"
  - Device: "Show entities and states"
- **Abort streaming**: send button transforms into stop button during streaming; calls `/api/chat/abort` + AbortController
- **Multi-tab sync**: messages sync across browser tabs via BroadcastChannel API
- **Bubble-specific session**: separate `bubble_` prefixed session IDs — bubble chat doesn't interfere with main UI conversations

## 3.12.1 — Chat Bubble UX Improvements
- **Draggable button**: long-press (400ms) to enter drag mode (like iPhone app icons), position saved in localStorage
- **Resizable chat panel**: CSS `resize: both` with size persistence via ResizeObserver + localStorage
- **Draggable panel**: drag via header bar to reposition anywhere on screen
- **Panel auto-positioning**: panel intelligently positions near the button (above/below, clamped to viewport)
- **Auto-reload after update**: when AI modifies an automation/script/dashboard you're viewing, the page auto-reloads after 2.5s with a green notice
- **HTML dashboard context**: on lovelace pages, extracts entity_ids from dashboard iframes and includes them in context prefix — AI knows what entities are shown and can match the existing style when adding more
- **Tool badges in chat**: shows tool execution badges during streaming (same as main UI)

## 3.12.0 — Floating Chat Bubble
- **NEW**: Context-aware floating chat bubble on every Home Assistant page
  - Enable via `enable_chat_bubble: true` in add-on config
  - Detects current page context: automation edit, script edit, device, dashboard, settings
  - Sends context prefix to AI so it knows exactly what you're looking at
  - Full SSE streaming with tool execution badges
  - Session management (persists within tab), new chat button
  - Responsive design: works on desktop and mobile
  - Uses HA theme variables for dark/light mode compatibility
  - Auto-registers as Lovelace resource (JS module at `/local/ha-claude-chat-bubble.js`)
  - 4-language UI (en/it/es/fr)

## 3.11.7
- **FIX**: Anthropic 400 error on second request (orphaned tool_use in history)
  - Root cause: intermediate assistant messages with `tool_use` blocks were saved to conversation history, but without their corresponding `tool_result` blocks
  - On the next request, `sanitize_messages_for_provider` detected orphaned `tool_use` but the damage was done — API rejected with "tool_use ids without tool_result blocks"
  - Fix: sync logic now skips assistant messages with list content (tool_use blocks), saving only the final text response
  - Also applies to Google provider for consistency

## 3.11.6
- **FIX**: Anthropic tool_use

## 3.11.5
- **FIX**: Google Gemini chat hangs silently when model returns text without tool calls
- Root cause: Gemini SDK raises `ValueError` when accessing `response.text` on blocked/empty responses. `getattr(response, "text", None)` catches `AttributeError` but NOT `ValueError`, so the generator crashed silently — no error in logs, no SSE events, chat stuck on "risposta ricevuta"
- Now: safe extraction with try/except, fallback to candidate parts, safety filter detection with user message
- Added `err_response_blocked` translation key for all 4 languages

## 3.11.4 — Provider Alignment
- **Google Gemini provider fully aligned** with OpenAI/Anthropic:
  - Tool result truncation (20000 chars for read tools, 8000 for others)
  - Safe tool execution with try/except (no more crashes on tool errors)
  - Rate limit detection and retry (429/resource_exhausted → 10s wait + retry)
  - Progressive delay between rounds (3s→5s instead of fixed 1s)
  - Redundancy detection: read-only tools with same args cached, no re-execution
  - Draft dashboard auto-stop skip (both `draft_started` and `draft_appended`)
  - Empty dashboard auto-stop skip (`create_dashboard` with 0 views continues)
  - 4-char chunk streaming (smoother output, was word-by-word)
  - Humanized error messages for API key/quota/billing errors (4 languages)
  - Abort check during rate-limit delay
  - `write_config_file` added to WRITE_TOOLS auto-stop
- **Anthropic provider aligned**:
  - `create_html_dashboard` added to WRITE_TOOLS auto-stop
  - Draft dashboard auto-stop skip (draft_started/draft_appended)
  - Tool result truncation: 20000 chars for read tools (was 8000 for all)
  - Safe tool execution with try/except

## 3.11.3
- **FIX**: HTML dashboards with Chart.js broken by CSS `var()` used in JavaScript
- AI models sometimes generate `color: var('--text-color')` inside `<script>` blocks — `var` is a JS keyword, causing `SyntaxError: expected expression, got keyword 'var'`
- New `_fix_css_var_in_js()` sanitizer auto-replaces with `getComputedStyle(document.documentElement).getPropertyValue('--prop').trim()`
- Applied to all HTML dashboards (both raw and structured mode) before saving

## 3.11.2
- **FIX**: OOM crash (exit code 137) when uploading files with RAG enabled
- Replaced `sentence-transformers` / PyTorch embedding backend with lightweight TF-IDF approach (zero heavy dependencies)
- Old system loaded ~500MB+ PyTorch model per chunk — new system uses stdlib only (`re`, `math`, `collections.Counter`)
- RAG search now actually works: previously `sentence-transformers` was never installed, so all embeddings silently failed
- Added try/except safety net around `rag.index_document()` in upload endpoint — RAG failure no longer crashes file upload
- Migrates old `embeddings.json` automatically (removes it, starts fresh with `rag_index.json`)
- TF-IDF supports multilingual tokenization (accented characters: àáâãäåèéêëìíîïòóôõöùúûüñç)

## 3.11.1
- **FIX**: Google Gemini provider now supports focused mode (`intent_info`), WRITE_TOOLS auto-stop, max rounds (10), and abort check
- Previously: Google provider always used 44 tools, had no auto-stop, and could loop infinitely
- Now: same focused mode as OpenAI/NVIDIA — fewer tools for specific intents, auto-stop after write tool success
- **FIX**: Added missing HTML dashboard keywords: "chart", "grafic", "torta", "pie chart", "bar chart", "line chart", "donut", "gauge"
- "la puoi modificare inserendo qualche grafico?" now correctly triggers `create_html_dashboard` instead of `generic`
- **FIX**: Follow-up continuity — when previous intent was a dashboard/config edit and user sends a follow-up instruction ("modificala", "usa le stesse entità", "aggiungi un grafico"), the intent is carried forward
- This works across all 4 languages (IT/EN/ES/FR follow-up signals)
- Covers: modify, add, remove, use same entities/sensors patterns

## 3.11.0 — Full i18n (Internationalization)
- **i18n**: All 35+ hardcoded Italian user-facing strings replaced with `api.tr()` translation system
- Added ~30 new translation keys to `LANGUAGE_TEXT` for all 4 languages (en/it/es/fr):
  - Error messages: API key not configured, provider not supported, NVIDIA errors, image format errors
  - Status messages: image processing, context preloaded, tool repair, rate limit, prompt too large, user cancelled
  - Write tool responses: operation success, no changes, YAML updated/created, snapshot created
  - Intent labels: all 17 intent types translated (modify automation, create script, etc.)
  - Read-only mode note and instruction
  - Smart context: script found message
- **i18n**: Intent prompts (chat, modify_automation, modify_script, create_automation, create_script, config_edit, delete, helpers) — removed hardcoded Italian, now English base with "ALWAYS respond in the user's language"
- **i18n**: Confirmation keywords moved to `keywords.json` with proper translations for all 4 languages
- **i18n**: System labels DATI/CONTESTO → DATA/CONTEXT in API messages
- **FIX**: `config_edit` prompt now mentions backup snapshots are created automatically
- **FIX**: Confirmation continuity — user replies "si/yes/ok" → intent carried forward (not reset to generic)
- **FIX**: Increased tool result truncation limit for read operations (20000 chars for OpenAI/Google)

### Files modified
- `api.py` — LANGUAGE_TEXT keys + all hardcoded strings → `tr()`
- `providers_openai.py` — 7 status/error messages → `api.tr()`
- `providers_anthropic.py` — 2 abort messages → `api.tr()`
- `intent.py` — prompts in English, confirmation from keywords.json, DATI→DATA
- `tools.py` — read-only instruction + delete confirmation → `api.tr()` / English
- `keywords.json` — new `confirm` category × 4 languages

## 3.10.8
- **REMOVED**: `agent_name`, `agent_avatar`, `agent_instructions`, `html_dashboard_footer` from add-on configuration
- These are now hardcoded defaults ("AI Assistant", emoji, empty strings)
- Removed from config.yaml options/schema, run script, api.py env vars, and all translations
- Internal code that references these values via `getattr()` continues to work with the hardcoded defaults

## 3.10.7
- **FIX**: Snapshot restore now triggers `homeassistant/reload_all` for sensor/template/generic YAML files
- Previously, restoring a snapshot for `sensors.yaml` or `template.yaml` only copied the file back but did NOT reload HA
- The file was restored on disk but HA kept using the old (modified) version from memory
- Now: automations → `automation/reload`, scripts → `script/reload`, lovelace → `lovelace/reload`, everything else → `homeassistant/reload_all`

## 3.10.6
- **FIX**: `write_config_file` removed from auto-stop — model now explains changes and shows diff before/after writing
- **NEW**: Focused prompt for `config_edit` intent with mandatory confirmation workflow:
  1. Read file → 2. Explain changes → 3. Show diff → 4. Ask confirmation → 5. Write only after "sì"
- Previously, auto-stop silently wrote files without showing the user what changed

## 3.10.5
- **FIX**: Chat response disappearing after HTML dashboard creation — `create_html_dashboard` now triggers auto-stop
- After successful dashboard creation, the response is formatted and sent immediately instead of making another API call
- Draft calls (`draft=true`) correctly skip auto-stop so the model can continue sending chunks
- Applied to both OpenAI and NVIDIA provider streams

## 3.10.4
- **NEW**: Configurable `max_conversations` setting — number of chat conversations to keep in history (1-100, default 10)
- Previously hardcoded to 10 in both save and list endpoints
- Available in add-on configuration UI with translations (EN, IT, ES, FR)

## 3.10.3
- **FIX**: Detect truncated Vue.createApp scripts (has `createApp` but no `.mount()`) and force chunked/draft mode retry
- Previously, truncated scripts passed the `createApp` check and were saved as broken dashboards
- Now returns a clear error instructing the model to use draft mode (2-3 chunks under 6000 chars each)
- Covers the case where GPT-5.2 writes CSS + template + starts JS but hits token limit mid-computed/methods

## 3.10.2
- **FIX**: Intent detection now correctly routes HTML dashboard modification requests to focused `create_html_dashboard` intent
- Requests like "aggiungi sensori al pannello" with smart_context referencing `/local/dashboards/*.html` no longer fall through to generic intent (44 tools)
- Added `has_html_dash_ref` check: detects dashboard names, paths, and `.html` references in message and smart_context
- Auto-detect: if smart_context mentions an HTML dashboard file and user has modify intent, route to focused HTML dashboard intent (3 tools)

## 3.10.1
- **FIX**: Prompt now requires WebSocket auto-reconnect on close (`setTimeout(connectWs, 5000)`)
- **FIX**: Prompt forbids debug/technical UI (connection status pills, entity_id badges, accent hex, series counts)
- Dashboard is for end users: only show useful data, friendly names, a simple Live/Offline dot indicator

## 3.10.0
- **NEW**: Chunked/draft mode for HTML dashboards — model sends HTML in 2-3 parts under 6000 chars each
- `draft=true` buffers HTML chunks, omitting `draft` on last call finalizes and saves the dashboard
- Solves GPT-5.2 output token limit causing truncated HTML (CSS+template but no JS)
- Prompt updated to instruct model: chunk 1 = head+CSS, chunk 2 = template, chunk 3 = script+closing
- Auto-complete with Vue boilerplate kept as fallback if model doesn't use chunked mode

## 3.9.9
- **FIX**: Auto-complete truncated raw HTML dashboards instead of rejecting them
- GPT-5.2 hits output token limit before writing Vue.createApp JS section (~12K chars of CSS + template)
- New `_autocomplete_truncated_html()` closes unclosed tags and appends standard Vue + WebSocket boilerplate
- Boilerplate includes: reactive state, WebSocket live updates, `fmt()`, `powerText()`, `entityName()`, and common energy computed properties (solarW, gridW, battW, price, solarShare)
- Result: the model's beautiful CSS and partial template work with live data instead of being rejected

## 3.9.8
- **FIX**: Repair malformed JSON from GPT-5.2 `create_html_dashboard` tool calls
- Root cause found: model sends valid JSON structure (12K+ chars) with title, name, entities, html — but HTML value contains unescaped characters breaking `json.loads()`
- New `_repair_html_dashboard_json()` extracts fields via regex: simple string fields, entities array, and raw HTML value with JSON unescape
- Applied to both OpenAI and NVIDIA provider streams

## 3.9.7
- **FIX**: Safety net now also searches raw tool arguments string for HTML (not just accumulated text)
- GPT-5.2 may put HTML directly in arguments (invalid JSON), causing silent JSONDecodeError → empty args
- Added debug logging for JSONDecodeError and safety net search to diagnose the exact failure mode
- Safety net logs first 300 chars of each source when no HTML is found

## 3.9.6
- **FIX**: Focused prompt now explicitly tells model to pass HTML inside tool call arguments JSON, not as text
- **FIX**: Error message for missing html/sections now explains exactly how to structure the tool call
- **FIX**: Safety net regex more robust — catches `<html>` without DOCTYPE, `<head>...<body>` fragments

## 3.9.5
- **FIX**: Validate raw HTML has functional Vue app — reject incomplete HTML (CSS only, missing `createApp`, no WebSocket logic) with detailed error guiding the model to include full template + JS

## 3.9.4
- **FIX**: Safety net for GPT-5.2 calling `create_html_dashboard` with empty args — model writes HTML as streaming text instead of in tool parameters
- Automatically extracts HTML from assistant text, entity_ids from HTML code, and infers title/name from user message
- Applied to both OpenAI and NVIDIA provider streams

## 3.9.3
- **FIX**: HTML dashboard focused prompt was NEVER injected — intent detection returned `prompt: None` instead of the creative raw HTML prompt
- Model was falling back to structured mode because it never saw the raw HTML instructions

## 3.9.2
- **FIX**: `__THEME_CSS__` in raw HTML mode now outputs CSS properties only (no `:root{}` wrapper) — prevents invalid nested `:root{:root{...}}` CSS
- **FIX**: Prompt explicitly warns NOT to use `var(--primary-background-color)` or HA frontend CSS variables (not available in `/local/` iframes)
- **IMPROVEMENT**: Full placeholder reference in prompt — explains exact output of each placeholder with examples
- **IMPROVEMENT**: Better tool description documents `__THEME_CSS__` usage pattern: `:root{__THEME_CSS__}`

## 3.9.1
- **IMPROVEMENT**: HTML dashboards now default to RAW HTML mode — agent writes full HTML/CSS/JS for unique creative designs
- **IMPROVEMENT**: Focused prompt encourages varied styles: glass morphism, neon, neumorphism, gradients, animations, bento grids
- **IMPROVEMENT**: Complete WebSocket/REST guide in prompt — agent builds live-updating dashboards with full creative freedom
- **FIX**: Removed surrogate unicode character in schema description that caused UTF-8 encode error on chat messages

## 3.9.0
- **ARCHITECTURE**: HTML dashboards now served from `/config/www/dashboards/` via HA's static file server (`/local/`) — eliminates Ingress token dependency entirely
- **FIX**: HTML dashboard 401 Unauthorized permanently fixed — iframe URLs now use `/local/dashboards/name.html` (stable, never changes on addon restart/update)
- **IMPROVEMENT**: Dashboard JS uses direct HA REST API with Bearer token instead of addon proxy — simpler, no Ingress routing needed
- **NEW**: Automatic migration on startup — copies dashboards from old `.html_dashboards/` to `www/dashboards/` and updates all Lovelace iframe URLs
- **IMPROVEMENT**: Backward compatibility — serve route checks both new and old paths, list route scans both directories

## 3.8.5
- **NEW**: `trend` section type for HTML dashboards — KPI badges with live values + historical area chart with gradient fill
- **NEW**: `/dashboard_api/history` proxy endpoint — fetches entity history data server-side via SUPERVISOR_TOKEN (1h-168h range)
- **NEW**: Chart.js date-fns adapter for time-based X axis on trend charts
- **NEW**: `color` and `icon` properties on section items — custom colors for trend badges/lines, emoji icons for KPI badges
- **NEW**: `hours` property on sections — configure history range for trend charts (default 24h)

## 3.8.4
- **FIX**: `create_dashboard` now REJECTS calls with empty/missing views — returns error with step-by-step instructions forcing model to build complete views with cards before retrying
- **FIX**: Also rejects views arrays where ALL views have no cards
- **IMPROVEMENT**: Strengthened `create_dashboard` focused prompt — explicit mandatory steps, example views structure, card type recommendations per entity type
- **IMPROVEMENT**: Added `update_dashboard` to `create_dashboard` intent tool set — model can populate views as fallback after creation

## 3.8.3
- **FIX**: Dashboard creation with typos (e.g. "crarmi" instead of "crearmi") now correctly detected as create_dashboard intent
- **FIX**: "dashboard" keyword alone (without explicit "crea") now defaults to create intent instead of falling through to query_state
- **FIX**: Empty dashboards (0 views/cards) no longer auto-stop — model continues to populate views after creation
- **NEW**: Focused prompt for `create_dashboard` intent — guides model to search entities first, choose appropriate card types, and build complete views
- **NEW**: Typo-tolerant create keywords for Italian ("crar", "puoi crearmi", "puoi crarmi")
- **FIX**: Auto-stop skip applies to both OpenAI and Anthropic providers

## 3.8.2
- **NEW**: `get_repairs` tool — read active HA repair issues and system health diagnostics (unsupported/unhealthy components, resolution suggestions)
- **NEW**: `dismiss_repair` tool — dismiss/ignore specific repair issues after user review (write-guarded in read-only mode)
- **NEW**: Intent detection for repairs — multilingual keywords (IT/EN/ES/FR) route repair queries to focused tool set
- **NEW**: Focused prompt for repairs intent — guides AI to present issues clearly with severity, suggest fixes, and ask confirmation before dismissing

## 3.8.1
- **FIX**: Dashboard HTML iframe 401 Unauthorized — browser-side `localStorage.hassTokens` may be expired, missing, or blocked by storage partitioning
- **NEW**: Dashboard API proxy endpoints (`/dashboard_api/states`, `/dashboard_api/services/<domain>/<service>`) — server-side auth via SUPERVISOR_TOKEN, no browser token needed
- **NEW**: Dashboard JS now uses proxy for REST API calls and service calls (toggle, slider, etc.)
- **NEW**: Automatic fallback: WebSocket (if token available) → polling via proxy every 5s (always works)
- **NEW**: Input validation on proxy endpoints (alphanumeric + underscore only for domain/service)
- **FIX**: No more "No HA token" or "Auth failed" errors in dashboard iframes
- **IMPROVEMENT**: Dashboards work reliably regardless of browser token state, Ingress configuration, or HA session expiry

## 3.8.0
- **ARCHITECTURE**: Sections V2 — structured JSON spec with 11 section types and layout system replaces body_html
- **FIX**: GPT-5.2 sending `args: {}` — body_html was too large (~2000 tokens), sections spec is ~350 tokens
- **FIX**: Agent no longer shows HTML code walls in chat responses (DISPLAY_NOTE added)
- **NEW**: 11 section types: hero, pills, flow, gauge, gauges, kpi, chart, entities, controls, stats, value
- **NEW**: CSS Grid 3-column layout with span-1/span-2/span-3 for multi-column designs
- **NEW**: Per-entity label overrides via items[{entity, label}] in every section type
- **NEW**: Card style variants: gradient, outlined, flat
- **NEW**: Flow diagram section for energy flow visualization (PV → House → Grid)
- **NEW**: Gauge section with SVG donut + side stats for battery/SOC monitoring
- **NEW**: Pills section for top KPI row with live values
- **NEW**: Value section for single prominent number display
- **REMOVED**: body_html and custom_css parameters — agent now sends compact sections JSON
- **BENEFIT**: Agent has architectural creative control (sections, grouping, layout, colors) while addon renders beautiful HTML

## 3.7.6
- **NEW**: HTML dashboard entity validation — filters out entities that don't exist or are in unknown/unavailable state before building the dashboard
- **NEW**: Agent receives feedback on filtered entities (count + list) so it knows which sensors were removed
- **FIX**: Prevents broken `...` values in dashboard for non-existent entities
- **FIX**: Returns clear error if ALL entities are invalid

## 3.7.5
- **FIX**: Chart.js canvases inside CSS Grid cards caused infinite height expansion
- **FIX**: Shell now auto-wraps `<canvas data-chart>` in a fixed-height `.chart-auto-wrap` container before Chart.js init
- **FIX**: Canvas height is read from inline `style.height` or `height` attribute (default 250px) and applied to wrapper
- **NEW**: Shell CSS adds `canvas[data-chart]{display:block;width:100%!important}` and `.chart-auto-wrap{position:relative;width:100%;min-height:0}` to prevent grid sizing issues

## 3.7.4
- **FIX**: Dockerfile still had `EXPOSE 5000` and `ENV API_PORT=5000` — changed to 5010
- **FIX**: api.py fallback `os.getenv("API_PORT", 5000)` — changed to 5010
- **FIX**: DOCS.md referenced port 5000 — changed to 5010
- **FIX**: Supervisor warning `Option 'api_port' does not exist in the schema` — added `api_port: port?` to schema for backward compatibility (optional, value ignored, port comes from environment section)

## 3.7.3
- **ARCHITECTURE**: Shell + Skin approach — addon provides the "engine" (auth, WebSocket, Vue 3, Chart.js, theme CSS), agent provides the "skin" (body_html + custom_css)
- **FIX**: v3.7.2 was effectively a fixed template (agent only picked section types/colors) — now agent has FULL creative freedom over HTML/CSS
- **NEW**: `body_html` parameter — Vue 3 template with full access to reactive state, helpers (formatVal, entityName, toggle, callService, etc.)
- **NEW**: `custom_css` parameter — agent writes any CSS (gradients, glassmorphism, animations, grids, SVG)
- **NEW**: Auto Chart.js — agent adds `<canvas data-chart="bar" data-entities='[...]'>` and charts render automatically
- **NEW**: CSS variables exposed: --accent, --accent-rgb, --bg, --bg2, --text, --text2, --card, --border, --green/yellow/red/blue
- **REMOVED**: Structured sections spec (hero/gauges/chart/entities/controls/stats) — replaced by freeform body_html
- **BENEFIT**: Body HTML is ~500 tokens (vs ~3000 for full HTML) — fits in tool args. Agent keeps full creative control.

## 3.7.2
- **FIX**: HTML dashboard tool now uses structured design spec instead of raw HTML in tool args
- **REASON**: LLMs (GPT-5.2) truncate large tool call arguments - sending full HTML (~3000+ tokens) as a single parameter fails silently (args become `{}`)
- **NEW**: Agent now sends a compact JSON design spec: sections (hero/gauges/chart/entities/controls/stats), entity grouping, colors, chart types
- **NEW**: Addon builds the HTML from the spec with `_build_dashboard_html()` - handles auth, WebSocket, CSS theming, Chart.js
- **NEW**: 6 section types: hero (gradient banner), gauges (SVG donut), chart (bar/line/doughnut/radar/pie), entities (rows with toggles/sliders), controls (big toggle buttons), stats (KPI cards)
- **NEW**: `accent_color` parameter - agent chooses primary color for gradients and highlights
- **NEW**: Per-section `style` parameter: gradient, glassmorphism, flat, outlined
- **IMPROVEMENT**: Agent retains full creative control (layout architecture, entity grouping, colors, visualization choices) while output stays within token limits
- **IMPROVEMENT**: Auth boilerplate always correct - no risk of agent forgetting WebSocket auth flow

## 3.7.1
- **FIX**: Removed `api_port` from config options and schema - port is fixed at 5010 via environment variable and should not be visible to users in the addon settings UI

## 3.7.0
- **BREAKING**: HTML dashboard generation moved from addon template to AI agent
- **REMOVED**: `_generate_html_dashboard()` function (~600 lines) - no more hardcoded HTML template
- **NEW**: AI agent now generates the COMPLETE HTML code for dashboards (creative, unique designs per request)
- **NEW**: `create_html_dashboard` tool now accepts `html_content` as required parameter with full HTML document
- **NEW**: Tool description includes HA authentication snippets (WebSocket, REST API, service calls) so agent knows how to build functional dashboards
- **NEW**: Agent can create purpose-specific dashboards (energy flow, climate control, security, lighting scenes) with unique layouts
- **IMPROVEMENT**: `create_dashboard` tool description enhanced - agent now designs creative card layouts (gauge for %, history-graph for trends, thermostat for climate, etc.)
- **IMPROVEMENT**: `update_dashboard` tool description enhanced - encourages creative redesign while preserving user content
- **IMPROVEMENT**: Removed ~600 lines of template code from addon, replaced with ~10 lines of instructions in tool description
- **IMPROVEMENT**: Dashboard icon is now configurable via `icon` parameter (defaults to mdi:web)

## 3.6.0
- **ENHANCEMENT**: Complete rewrite of HTML dashboard generator with major visual and functional improvements
- **NEW**: Auto dark/light theme following HA preferences (CSS prefers-color-scheme)
- **NEW**: Glassmorphism card design with backdrop-filter blur and hover animations
- **NEW**: Domain-based entity grouping - entities auto-organized by domain (sensors, switches, lights, etc.)
- **NEW**: Domain-specific icons (🔋 battery, 🌡️ temperature, ⚡ power, 💧 humidity, etc.)
- **NEW**: Smart unit formatting - W→kW, Wh→kWh when values exceed 1000
- **NEW**: Toggle switches for switch/light/input_boolean entities (click to toggle)
- **NEW**: Range sliders for number/input_number entities (drag to set value)
- **NEW**: Value color coding - green/yellow/red for battery SOC, power flow coloring for solar/grid
- **NEW**: Search/filter bar to quickly find entities
- **NEW**: Hero card with live stats (entity count, numeric count, toggle count)
- **NEW**: Up to 4 gauge SVGs for percentage-based entities (battery SOC, etc.)
- **NEW**: Chart.js auto horizontal bars for >8 entities, vertical bars otherwise
- **NEW**: Dynamic chart palette with 12 colors and dark-mode aware grid lines
- **IMPROVEMENT**: Responsive mobile-first grid with proper breakpoints
- **IMPROVEMENT**: Entity rows show friendly_name, entity_id, and domain icon
- **IMPROVEMENT**: Removed Tailwind CSS CDN dependency (pure CSS for faster loading)
- **IMPROVEMENT**: WebSocket reconnection with debounced chart updates

## 3.5.6
- **FIX**: HTML dashboard iframe now renders full-page instead of small centered square
- **FIX**: Removed `aspect_ratio: "100%"` from iframe card (was constraining to 1:1 square)
- **FIX**: Lovelace wrapper view now uses `type: "panel"` for true full-page layout (no margins/max-width)

## 3.5.5
- **FIX**: Complete rewrite of HTML dashboard template - was rendering blank white page
- **FIX**: CSS custom properties had quoted values (`'#ffffff'` → `#ffffff`) - colors not applied
- **FIX**: Tailwind CSS loaded as `<link>` instead of `<script>` - styles not loading
- **FIX**: Vue.js template syntax broken - Python f-string `{{ }}` escaping produced single `{ }` instead of Vue `{{ }}`
- **FIX**: `template: '#app'` conflicted with `.mount('#app')` - Vue couldn't render
- **FIX**: WebSocket/REST API calls now authenticate with HA token from localStorage (same-origin Ingress)
- **IMPROVEMENT**: Switched from f-string to placeholder-based template (avoids all `{{ }}` escaping issues)
- **IMPROVEMENT**: Entity cards show friendly_name and unit_of_measurement
- **IMPROVEMENT**: Chart.js auto-selects bar/doughnut based on entity count
- **IMPROVEMENT**: Gauge SVG uses proper arc path calculation
- **IMPROVEMENT**: Entities split into chunks of 8 per card for better layout
- **IMPROVEMENT**: WebSocket subscribes to state_changed events with proper HA auth flow

## 3.5.4
- **FIX**: HTML dashboard iframe 404 error - iframe URL now uses Ingress proxy path instead of relative URL
- **FIX**: Added `get_addon_ingress_url()` helper that queries Supervisor API (`/addons/self/info`) to get correct Ingress path
- **FIX**: Dashboard iframe cards now load correctly through HA Ingress proxy (URL: `/api/hassio_ingress/<token>/custom_dashboards/...`)
- **IMPROVEMENT**: Ingress URL is cached at runtime for performance

## 3.5.3
- **FIX**: DELETE intent detection priority - now checked before QUERY_STATE to prevent misrouting
- **FIX**: Delete dashboard/automation/script requests now correctly route to 'delete' intent with proper tools
- Dashboard deletion now works when user says "cancella dashboard"

## 3.5.2
- **FIX**: Intent detection now recognizes HTML/Vue/Web keywords and routes to create_html_dashboard
- **FIX**: Keywords like "HTML", "Vue", "web app", "realtime", "interactive", "responsive", "custom CSS" trigger HTML dashboard tool
- **IMPROVEMENT**: Smarter intent routing - user can ask for "HTML dashboard" and model uses correct tool automatically
- Dashboard creation now correctly differentiates between YAML (Lovelace) and HTML (Vue.js) dashboards

## 3.5.1
- **IMPROVEMENT**: HTML dashboards now automatically create Lovelace wrapper with iframe
- **IMPROVEMENT**: Custom dashboards now appear directly in Home Assistant sidebar (no manual setup needed)
- **FEATURE**: Dashboard is fully accessible from sidebar - click to view, appears in the dashboard list
- Dashboard has automatic icon (mdi:web) and appears alongside native Lovelace dashboards
- Full title and description displayed in sidebar
- Frame height auto-scales to full viewport

## 3.5.0
- **IMPROVEMENT**: HTML dashboards now automatically create Lovelace wrapper with iframe
- **IMPROVEMENT**: Custom dashboards now appear directly in Home Assistant sidebar (no manual setup needed)
- **FEATURE**: Dashboard is fully accessible from sidebar - click to view, appears in the dashboard list
- Dashboard has automatic icon (mdi:web) and appears alongside native Lovelace dashboards
- Full title and description displayed in sidebar
- Frame height auto-scales to full viewport

## 3.5.0
- **NEW FEATURE**: Added `create_html_dashboard` tool for generating custom Vue 3 dashboards with real-time WebSocket
- **NEW**: Html dashboards support Vue 3, CSS, responsive design, and live entity monitoring
- **NEW**: Dashboards are self-contained, serve through Flask routes at `/custom_dashboards/<name>`
- **NEW**: List all dashboards via `/custom_dashboards` endpoint
- **IMPROVEMENT**: WebSocket real-time entity state updates in HTML dashboards
- **IMPROVEMENT**: Support for multiple themes (light, dark, auto-detect)
- **IMPROVEMENT**: Rich component library (info cards, gauges, charts, state displays)
- **REMOVED**: Deleted development addon (claude-backend-dev) - single plugin maintenance only
- Dashboards can monitor multiple entities with live updates
- Built-in error handling and connection status indicators
- Full responsive design (mobile, tablet, desktop)

## 3.4.9
- **FIX**: Fixed critical bug in get_dashboard_config tool that crashed with `slice(None, 10, None)` error
- **FIX**: Added robust try-catch error handling at card/view level in get_dashboard_config
- **FIX**: Improved type checking for entities array before slicing (prevents TypeError on non-list data)
- **IMPROVEMENT**: Enhanced logging in update_dashboard tool to track WS requests and responses
- Dashboard read/update operations now fail gracefully with clear error messages instead of crashing
- Added detailed logging to diagnose dashboard operation failures

## 3.4.8
- **IMPROVEMENT**: Enhanced dashboard creation tool with detailed logging (📊 emojis track progress)
- **IMPROVEMENT**: System prompt reinforces that create_dashboard MUST be used (never skip to manual YAML)
- **FIX**: Better error handling and exception catching in create_dashboard WebSocket calls
- Dashboard creation now fails gracefully with clear error messages when API issues occur
- Logging shows each step: WS request → response → success/failure

## 3.4.7
- **FIX**: Improved regex filtering for unnecessary comments (now handles code block markers and language specifiers)
- Comment-only code blocks like ```yaml\n# (nessun YAML...)\n``` are now properly removed
- Stronger pattern matching for all supported languages (IT, EN, ES, FR)
- Filter applied both in main response pipeline and provider logging

## 3.4.6
- **FIX**: Applied response cleaning filter to provider logging output
- Unnecessary comment-only code blocks no longer appear in server logs
- Cleaned logging output for both NVIDIA and OpenAI responses

## 3.4.5
- **FIX**: Added api_port back to schema with fixed value for backward compatibility
- Prevents "Option does not exist in schema" warning from Home Assistant Supervisor
- Port remains fixed at 5010 - configuration ignored if user changes it

## 3.4.4
- **FIX**: Backend post-processing added to remove unnecessary comment-only code blocks from AI responses
- Cleans up patterns like "# (nessun YAML necessario...)" that models add for simple text responses
- Responses now stay clean - code blocks only appear when showing actual code/config

## 3.4.3
- **FIX**: System prompt updated to prevent model from adding unnecessary comment-only code blocks (e.g., "# (no YAML needed)")
- Pure text responses now stay clean without filler comments
- Code blocks only appear when showing actual code/config the user needs

## 3.4.1
- **BREAKING**: Changed default port from 5000 to 5010 (avoid conflicts)
- **REMOVED**: api_port configuration option (port is now fixed)
- **REMOVED**: sync_ports.py script (port sync was not working reliably with HA Ingress)
- Chat UI and all features work normally with new port
- Port 5010 is internal to container, Ingress routes transparently
- Users needing direct access can use http://hostname:5010
## 3.4.0
- **NEW**: Dynamic API port synchronization with sync_ports.py script
- **NEW**: GPT-5.2, GPT-5.2-mini, o3, o3-mini models added to OpenAI options
- **FIX**: Python SyntaxWarning in chat_ui.py regex escape sequence
- **FIX**: Invalid JSON comments in build.json causing parse error
- **DOCS**: Added rebuild requirement warning to api_port config descriptions (EN/IT/ES/FR)
- OpenAI default model updated to GPT-5.2 (flagship)
- Users can now change api_port in config (requires rebuild to reload ingress proxy)
## 3.3.9
- **FIX**: Resolve Python SyntaxWarning in chat_ui.py regex escape sequence
- Fixes warning: invalid escape sequence '/\/' in apiUrl function

## 3.3.8
- **NEW**: Add GPT-5.2 and GPT-5.2-mini as default OpenAI models
- **NEW**: Add o3 and o3-mini reasoning models to OpenAI options
- OpenAI default model updated from GPT-4o to GPT-5.2 (flagship model)
- GitHub Models also support GPT-5.2 variants
- All available models now reflect current OpenAI lineup (Feb 2026)

## 3.3.7
- **FEAT**: Dynamic API port synchronization - users can now change `api_port` in addon config
- New `sync_ports.py` script auto-updates ingress_port and port mappings on runtime
- Fixes issue where changing api_port had no effect without manual config.yaml editing
- **FIX**: Add default value for ARG BUILD_FROM in Dockerfile (resolves InvalidDefaultArgInFrom warning)
- **FIX**: Improve sync_ports.py logging with debug output for port synchronization
- **DOCS**: Add ⚠️ rebuild warning to api_port description in all languages (EN/IT/ES/FR)

## 3.3.6
- **FIX**: Move logging/debug settings to bottom of config
- Settings now appear in 'Show advanced options' section in HA UI

## 3.3.5
- **FIX**: Correct config schema syntax (remove invalid bool(true))
- Fixes Home Assistant addon validation error

## 3.3.4
- **FEAT**: Move config option descriptions to translations (EN/IT/ES/FR)
- Add default values for optional settings in config schema
- Advanced settings (debug_mode, log_level, etc.) now appear in 'Show advanced options' section

## 3.3.3
- **FIX**: Correct apiUrl regex to prevent double-slash in API paths (`//api/chat/stream`)
- Fixes stream error: 'Cannot write to closing transport' in HA Ingress

## 3.3.1
- **FIX**: Removed voice feature references accidentally included from dev addon (caused AttributeError crash on UI load)
- Removed voice button, voice CSS, voice JS, voice API endpoints, voice env vars from public addon

## 3.3.0
- **NEW**: File Upload - upload documents (PDF, DOCX, TXT, MD, YAML) for AI analysis
- **NEW**: Persistent Memory - AI remembers past conversations across sessions
- **NEW**: RAG (Retrieval-Augmented Generation) - semantic document search and context injection
- All 3 features are EXPERIMENTAL and disabled by default (enable in addon config)
- File upload button (orange) appears in chat when enabled
- Documents auto-injected into AI context and cleaned up after use
- Memory searches past conversations by keywords and message content
- Added translation keys for all new features in EN/IT/ES/FR
- Added PyPDF2 and python-docx dependencies for document parsing
- Upload limit set to 10MB per file

## 3.2.30
- Maintenance release: internal code improvements and stability fixes.

## 3.2.29
- Maintenance release: internal code improvements and stability fixes.

## 3.2.28
- Add native GPT-5 support for OpenAI (gpt-5 and gpt-5-chat) with direct API key authentication - no longer need GitHub token to access GPT-5.

## 3.2.27
- Logging improvements: add descriptions to all config options, add new `log_level` config option (normal/verbose/debug), and filter noisy logs (health checks `/api/ui_ping` and streaming `/api/chat/stream`) from normal output to reduce log clutter. Enable verbose/debug level in config to see all logs.

## 3.2.26
- Improve error messages: show specific "Rate limit exceeded" message for HTTP 429 responses instead of generic error, so users know to wait and retry.

## 3.2.25
- Fix JavaScript extraction in `/ui_main.js`: correct f-string escaping for `\r` and `\n` in regex patterns to prevent syntax errors when JavaScript code is extracted from HTML template.

## 3.2.24
- Fix conversation list loading: add defensive error handling in date parsing and grouping logic to prevent exceptions from breaking chat history display + add detailed console logging for debugging.

## 3.2.23
- Fix: correct regex for extracting inline script from HTML template in `/ui_main.js` endpoint to avoid capturing `<script src="...">` tags instead of the actual JavaScript code (resolves "handleButtonClick is not defined" errors).

## 3.2.22
- Fix Home Assistant Ingress CSP: serve the main UI code as external `ui_main.js` (inline scripts can be blocked), and bind UI events via `addEventListener` instead of inline `onclick/onchange`.

## 3.2.21
- Diagnostics: load a tiny `ui_bootstrap.js` before the main UI script to log `/api/ui_ping` and show a clear in-chat error if the main handler isn't loaded (helps when logs show only `GET /` and Send does nothing).

## 3.2.20
- Fix UI boot in Home Assistant Ingress when `localStorage` is blocked: use safe get/set wrappers so the script doesn't crash before loading models/conversations or sending messages.

## 3.2.19
- Server debug logs: log incoming requests (method/path + ingress/forwarded context), response status+timing, and full tracebacks for unhandled exceptions.
- Hardening: return a clear 400 for invalid JSON bodies on `/api/chat` and `/api/chat/stream` (and log the content-type/length).

## 3.2.18
- Diagnostics: show JavaScript runtime errors directly in chat and reinforce the Send button handler (helps when UI appears unresponsive on mobile/Ingress).

## 3.2.17
- Fix UI init issues in Home Assistant Ingress: build API URLs from `origin + pathname` (avoids hash/query edge cases), show visible errors when loading models/conversations, and make send action awaitable.

## 3.2.16
- Fix: prevent 500 on `/` caused by unescaped `{n}` placeholder inside the chat UI template (conversation grouping labels).

## 3.2.15
- Fix: remove Python SyntaxWarning "invalid escape sequence" in `chat_ui.py` (escape backslashes in embedded JS regex literals).

## 3.2.14
- Progress UX: keep the last status/tool steps visible inside the assistant message while streaming (not only the "thinking" bubble).
- Entity disambiguation: improve detection of selection prompts (e.g. "scrivi/inserisci il numero") and tweak numbered option buttons for easier tapping.
- Conversation list: for chats older than Yesterday, show "N days ago" for recent chats (then fall back to the date).
- UI caching: add no-cache headers for the Ingress HTML to reduce stale UI after updates.

## 3.2.13
- Conversation list: group past chats by date with section headers like "Today" / "Yesterday".

## 3.2.12
- Entity disambiguation UI: show the clickable entity selection even when there is only 1 candidate (still only when the assistant is asking you to pick).

## 3.2.11
- Fix `search_entities` runtime error: "name 'List' is not defined".
- Fix double AI response in saved/loaded conversations (OpenAI/GitHub provider)
- Improve read-only toggle UX: eye icon, always-visible label, ON/OFF state indicator
- Fix version badge: read dynamically from config.yaml
- Migrate addon configuration from config.json to config.yaml

## 3.2.10
- When the assistant is unsure about which entity you mean, show a clickable/tappable list of found `entity_id`s in-chat plus a free input field to paste/type one manually.

## 3.2.9
- Reduce wrong device matches when searching entities: improve `search_entities` scoring using token coverage (e.g., "bagno piccolo"), and guide the assistant to ask for explicit selection when matches are low-confidence.
- Improve chat UI progress feedback: keep thinking bubble visible, show status/tool steps and elapsed timer

## 3.2.8
- Make it clearer what the assistant is doing while waiting: show a short in-chat list of progress steps (status + tools) in the thinking bubble.
- Fix header provider status not updating after switching provider/model in chat UI

## 3.2.5
- Fix intent detection for Italian "mi crei un'automazione" (routes to create_automation tools)

## 3.2.4
- Improve mobile header layout for agent/model selection

## 3.2.3
- Fix mobile chat UI overflow (no horizontal scroll)
- Hide conversations sidebar on mobile and add a header toggle ()

## 3.2.0

- Add read-only mode toggle in chat header (shows YAML without executing)
- Add clickable YES/NO confirmation buttons before create/modify/delete operations
- Add `manage_helpers` tool for Home Assistant helpers (input_boolean, input_number, input_select, input_text, input_datetime)
- Update intent prompts to always show YAML code before asking confirmation
- Add helper keywords and intent detection in all 4 languages

## 3.1.62

- Full multilingual UI support (English, Italian, Spanish, French)

## 3.1.61

- Beautify Google 429 error message
- Fix model dropdown styling

## 3.1.60

- Fix JS syntax error in formatMarkdown breaking entire chat UI

## 3.1.59

- Fix chat UI send button and Ingress URL handling

## 3.1.58

- Silence google.generativeai deprecation warning

## 3.1.57

- Fix conversation history loading and migration

## 3.1.56

- Fix Google Gemini tool schema (remove minimum/maximum)

## 3.1.55

- Multilingual progress status for all providers

## 3.1.54

- Stream progress status updates to chat

## 3.1.53

- Render plain YAML as code block in chat

## 3.1.52

- Always show YAML after write tools (NVIDIA auto-stop)

## 3.1.51

- Fix GitHub Actions tests workflow

## 3.1.50

- Force tool calls for create intents when model claims it searched

## 3.1.49

- Improve colored_logs readability in HA (emoji level badges)

## 3.1.48

- Fix NVIDIA stream retry vars, reduce noisy tool logs, add optional colored logs

## 3.1.47

- Ensure create_automation tool call

## 3.1.46

- Fix update_automation argument normalization

## 3.1.45

- Fix HA call_service payload
- Improve automation edit intent detection

## 3.1.44

- Add "AI Assistant" signature to automation/script descriptions

## 3.1.43

- Fix: create_automation writes directly to automations.yaml instead of REST API

## 3.1.42

- Fix: create_automation sends plural keys (triggers/conditions/actions) for HA 2024.x+

## 3.1.41

- Add focused prompts for create_automation/script
- Search entities first before creating

## 3.1.40

- Show created YAML in code block for create_automation/script/dashboard

## 3.1.39

- Fix UnicodeEncodeError surrogate emoji in chat_ui formatMarkdown

## 3.1.38

- Side-by-side diff view (GitHub-style split) for automation updates

## 3.1.37

- Diff view: unified diff with colored lines for automation edits

## 3.1.36

- Reduce o4-mini tool payloads (limit get_automations + auto query)

## 3.1.35

- Improve automation finding (intent + queryable get_automations)

## 3.1.34

- Validate call_service args and return proper errors

## 3.1.30

- Localize provider errors
- Add o4-mini token hint
- Fix o4-mini limit and 413 error
- Fix GitHub Models error message

## 3.1.26

- Undo snapshot and agent selection in chat
- Fix UI undo button crash
