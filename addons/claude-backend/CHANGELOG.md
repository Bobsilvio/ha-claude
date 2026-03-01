# Changelog

## 4.2.0 — Entity discovery: use real HA device_class instead of keyword matching
**Breaking change in entity matching logic — eliminates false positives entirely.**

### Problem
Previous approach used keyword/substring matching on entity_ids to find entities (e.g. searching for "battery" by matching "bat" inside entity names). This caused false positives: "bat" matched "sabato", pulling in unrelated consumption entities. Every new device_class would require a new keyword dictionary — fragile and unscalable.

### Solution
- `intent.py`: **Two-mode entity discovery:**
  - **Device-class mode** (battery, temperature, humidity, etc.): filters ONLY by the REAL `device_class` attribute from Home Assistant state — zero false positives, no substring matching needed
  - **Keyword mode** (fallback): for brands, room names, or custom terms that have no device_class mapping — still searches entity_id/friendly_name
- `intent.py`: removed `_keyword_synonyms` dictionary entirely — no longer needed since device_class filtering doesn't require synonym expansion
- `intent.py`: expanded `_device_class_aliases` to cover both IT and EN terms (batterie, battery, temperatura, temperature, etc.)
- `tools.py`: `_inject_entity_filter_fallback()` simplified — trusts the backend entity list as authoritative, removed all `_dc_keywords` dictionaries and keyword-based re-filtering

### Result
Works for any device_class (battery, temperature, motion, humidity, etc.) without maintaining keyword vocabularies. New device types work automatically.

## 4.1.14 — Fix iOS Companion App infinite loading + dashboard showing only 5 sensors
- `_fix_auth_redirect()`: entry-point regex now uses **prefix matching** (`load\w*` catches `loadBatteries()`, `loadSensors()`, etc.) — previously only matched exact names like `load()`, so `tok` stayed empty on iOS
- `_fix_auth_redirect()`: also wraps `setInterval`/`setTimeout` referencing entry-point functions in `_getTokenAsync().then(...)`
- New `_inject_entity_filter_fallback()` post-processor: when AI HTML filters `/api/states` by `device_class` (e.g. `=== 'battery'`), injects the backend's pre-filtered entity list as `window._HA_ENTITIES` and extends the filter to include all matching entities
- Dashboard creation pipeline now calls `_inject_entity_filter_fallback()` after auth redirect fix

## 4.1.13 — Fix AI using device_class filter instead of pre-loaded entity list
- `intent.py`: add `device_class` field to entity objects injected in smart context (was missing — AI couldn't see it)
- `tools.py`: tool description now explicitly instructs AI to copy entity_ids from ## ENTITÀ TROVATE and use `__ENTITIES_JSON__`, never filter `/api/states` by `device_class`
- System prompts updated with same instruction

## 4.1.12 — Rewrite auth patch: fix stale headers + entry-point wrapping
- `_fix_auth_redirect()` completely rewritten to operate per `<script>` block
- Also removes stale `const headers = {Authorization: 'Bearer '+tok}` built before token resolved
- Wraps bare `load()` / `init()` / `render()` calls in `_getTokenAsync().then(...)` at statement level
- Injects `_authHeader()` helper for consistent auth headers in all fetch calls

## 4.1.11 — Fix AI-generated auth redirect breaking Companion App
- Added `_fix_auth_redirect()` post-processor applied to all generated HTML dashboards
- Removes `if(!tok){ location.href='/?redirect=...' }` pattern that caused infinite loading in Companion App
- Replaces sync `localStorage.getItem('hassTokens')` token read with async `_getTokenAsync()` — tries parent iframe postMessage first, then localStorage
- Injects initial states snapshot (`__INITIAL_STATES_JSON__`) so page renders immediately without client-side auth

## 4.1.10 — Fix HTML dashboard auth in Companion App
- `getTokenAsync()` now tries `postMessage` to parent window first (correct channel when page is inside a Lovelace iframe in Companion App)
- Token cached after first resolution to avoid repeated async lookups
- Fetch proceeds even without token (HA session-cookie fallback)

## 4.1.9 — Authoritative entity fallback from smart context
- `intent.py` saves pre-loaded entity_ids to `api._last_smart_context_entity_ids`
- `tools.py` uses those as last-resort fallback when AI passes only JS garbage in `entities[]` and HTML scan finds nothing

## 4.1.8 — Entity pre-filter via HA domain whitelist + HTML fallback extraction
- Replace regex pre-filter with HA domain whitelist (`sensor`, `binary_sensor`, `switch`, etc.) — JS vars like `stat.low`, `x.state`, `arr.map` are reliably rejected
- When entities list is all junk, scan raw HTML for quoted `domain.slug` literals to recover real entity_ids

## 4.1.7 — Smart context battery synonyms + entity pre-filter + Companion App auth
- `intent.py`: IT→EN keyword synonyms + `device_class` search (batterie→battery, temperatura→temperature, umidità→humidity, etc.) — finds all relevant entities, not just those with Italian names
- `tools.py`: pre-filter non-HA strings (JS expressions) from `entities[]` before HA validation
- `tools.py`: `getTokenAsync()` supporting HA Companion App (`externalApp`/`webkit`) with `localStorage` fallback
- `api.py`: improved OAuth provider logging at startup

## 4.1.6 — Fix messaging in chat UI + sort order
- WhatsApp/Telegram sessions no longer appear in the main chat UI conversation list
- Removed "Recent context: USER:..." prefix injected into WhatsApp messages (redundant, polluted saved conversations)
- Messaging list (WhatsApp + Telegram) now sorted with most recent chat first

## 4.1.5 — Smart context larger window + compact entity lists
- `MAX_SMART_CONTEXT` raised from 10 000 to 25 000 chars (5× more sensor data visible per query)
- Entity lists with >20 entries now use compact JSON, saving ~40% token space
- Entity injection capped at 80 entries per query (prevents single-keyword floods like "temperature" from eating the whole context)
- Fixes WhatsApp temperature queries returning only 4 out of 48 available sensors

## 4.1.4 — Add enable_mcp toggle
- Added `enable_mcp` option (default `false`) to disable MCP at startup
- When disabled, MCP servers are never contacted and no connection errors appear in logs
- New toggle visible in Home Assistant addon config UI (all 4 languages: IT, EN, FR, ES)

## 4.1.3 — Complete BoBot → Amira rename
- **CHANGE**: Renamed all remaining `BoBot`/`bobot` references to `Amira`/`amira` in `config.yaml` (panel title, port description, MCP config path)

## 4.1.2 — Rename addon to Amira
- **CHANGE**: Addon renamed from `BoBot` to `Amira` in Home Assistant addon store (`name` and `description` in `config.yaml`)

## 4.1.1 — Dockerfile fixes + new modules
- **FIX**: Corrected Dockerfile `COPY` instructions — removed non-existent `memory_system.py` reference
- **NEW**: Added `scheduled_tasks.py` to the Docker image (task scheduler module)
- **NEW**: Added `voice_transcription.py` to the Docker image (voice/TTS module)
- **FIX**: Removed duplicate `COPY memory.py` instruction in Dockerfile

## 4.1.0 — Complete provider architecture rewrite + dashboard intelligence
> **Breaking change from v3.x** — provider system completely rewritten

### Provider system
- Replaced monolithic `providers_anthropic/google/openai.py` with the modular `providers/` package
- 22 provider classes: OpenAI, Anthropic, Google, Groq, Mistral, NVIDIA, DeepSeek, OpenRouter, Ollama, GitHub, GitHub Copilot, ChatGPT Web, OpenAI Codex, Zhipu, SiliconFlow, Moonshot, MiniMax, AiHubMix, VolcEngine, DashScope, Perplexity, Custom
- Provider manager with unified streaming interface and enhanced error handling
- Dynamic model list: `PROVIDER_MODELS` built from each provider's `get_available_models()` at startup — single source of truth
- `model_fetcher.py`: live model refresh from official APIs with on-disk cache
- `rate_limiter.py`, `error_handler.py`, `tool_simulator.py`: shared utilities across providers

### OpenAI Codex provider
- OAuth PKCE flow: token stored at `/data/oauth_codex.json` with auto-refresh
- Correct model list (gpt-5.x-codex only)
- Connected banner in UI showing account ID, expiry and disconnect button
- `/api/oauth/codex/revoke` endpoint

### HTML Dashboard
- **Smart context split**: `[CURRENT_DASHBOARD_HTML]` injected as a separate conversation turn to avoid token overflow while keeping the full entity context (10KB cap)
- **Intent detection**: filesystem lookup in `www/dashboards/` to correctly route requests to `create_html_dashboard`
- `openMoreInfo()` with native `hass-more-info` event + custom modal fallback
- Auth redirect: if token is missing, redirect to `/?redirect=...`
- Sidebar title always prefixed with `Amira — <title>` (enforced in `tools.py`)

### Chat UI & bubble
- `stripContextInjections()`: hides `[CONTEXT:...]` and `[CURRENT_DASHBOARD_HTML]` blocks from the displayed conversation history without affecting stored data
- Tool call artifacts hidden from conversation history (`api_conversation_get`)
- Bubble drag fixed with Pointer Events API + `setPointerCapture()`
- Removed outdated "Novita v3.0" vision feature strings across all 4 languages

### New features
- **MCP**: Model Context Protocol server support
- **Telegram & WhatsApp**: bot integration
- **Voice transcription**: Whisper STT and TTS support
- **Semantic cache**: reduces API calls via semantic response caching
- **RAG**: Retrieval-Augmented Generation on local files
- **File upload**: attach files to conversations
- **Memory**: two-layer memory system with `MEMORY.md` (long-term facts) and `HISTORY.md` (session log)
- **Scheduled tasks**: task scheduler with autonomous agent
- **Quality metrics**: response quality scoring
- **Prompt caching**: prompt caching to reduce Anthropic API costs
- **Image support**: multi-provider image analysis
- **GitHub Copilot**: dedicated OAuth provider
