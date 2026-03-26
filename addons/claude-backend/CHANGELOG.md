# Changelog

> **⚠️ After updating, rebuild the add-on** (Settings → Add-ons → Amira → Rebuild) to apply new dependencies.

## 4.6.35 — Skills store: nascondi skill già installate

### Bug fixes / UX
- **Store non mostra le skill già installate**: le skill installate senza aggiornamenti vengono rimosse dalla lista store per evitare duplicati; compaiono solo nello store se è disponibile un aggiornamento (con pulsante "⬆ Aggiorna")
- Se tutte le skill dello store sono già installate e aggiornate, lo store mostra "Nessuna skill disponibile"

---

## 4.6.34 — Skills update detection + banner notifica

### Nuove funzionalità
- **Rilevamento aggiornamenti skill**: all'avvio (dopo 3 s) la chat confronta le versioni installate con lo store GitHub e mostra un banner giallo in cima alla chat se ci sono aggiornamenti disponibili
- **Banner dismissibile**: mostra le skill da aggiornare con versione corrente → nuova; pulsante "Vai alle Skill" apre direttamente il pannello; "✕" per chiudere
- **Pulsante "Aggiorna" nello store**: le skill installate con versione inferiore a quella dello store mostrano un pulsante arancione "⬆ Aggiorna" invece del badge verde "Installed"; il bordo della card diventa giallo per evidenziarle
- **i18n completa**: banner e pulsante aggiornamento tradotti in IT/EN/ES/FR

---

## 4.6.33 — Raise skill size limit to 60 KB

### Bug fixes
- **Fixed "Skill content too large"**: raised `_MAX_BODY_CHARS` from 8000 to 60000 — the SAK skill is ~46 KB and HTML-JS Card ~9 KB, both exceeded the old limit

---

## 4.6.32 — Fix skills.py missing from Dockerfile

### Bug fixes
- **Fixed `skills.py` not copied into Docker image**: `COPY skills.py .` was missing from Dockerfile, causing `No module named 'skills'` and "Skills non disponibili" even after rebuild

---

## 4.6.31 — Fix Skills store button crash + sys.path import fix

### Bug fixes
- **Fixed `SyntaxError: missing } in template string`** in Skills store panel: the Install button used `onclick='...'` with string concatenation that broke JS single-quoted strings; replaced with `data-name`/`data-url` attributes + `querySelectorAll` event listeners
- **Fixed `No module named 'skills'`**: `skills_routes.py` now explicitly adds the app root to `sys.path` and imports `skills` at module load time with a try/except; if unavailable, endpoints return `skills_unavailable` instead of a generic error
- **Improved error messages**: Skills panel now shows "Skills non disponibili. Riavvia l'add-on." instead of a false "internet connection" error when the module is missing; actual error detail shown below network errors for easier debugging

---

## 4.6.30 — Skills system + SAK/HTML-JS/Mushroom skills + fix Skills UI crash

### Skills system
- **New Skills system**: install/uninstall AI skills from GitHub registry directly from the Settings panel (🧩 Skills tab); each skill injects expert documentation into the AI prompt when invoked with `/skill-name` in chat
- **Skills store**: fetches available skills from `https://raw.githubusercontent.com/Bobsilvio/ha-claude/main/skills/index.json` with 5-minute cache
- **Three skills published**: `swiss-army-knife-card` (SAK — coordinate system, 19+ tool types, colorstops, sparkline, templates, animations), `html-js-card` (HTML+CSS+JS Lovelace cards), `mushroom` (Mushroom UI Cards)
- **`/command` invocation**: typing `/swiss-army-knife-card create a temperature card` in chat automatically injects the skill documentation before the AI response
- **Autocomplete**: typing `/` in the chat input shows installed skills with name + description

### Bug fix
- **Fixed Skills panel crash** (`NameError: name 'language' is not defined`): the JS `lang` variable in the Skills panel was referencing the Python variable `language` which does not exist — corrected to `ui_lang`

---

## 4.6.29 — Remove deprecated armhf arch + fix macOS junk files in translations

### Supervisor / config fixes
- **Removed deprecated `armhf` arch value** from `config.yaml` — HA supervisor was warning on every reload; supported architectures are now `aarch64` and `amd64` only
- **Auto-cleanup of macOS AppleDouble files** (`._*.yaml`) at startup: the s6-overlay run script now runs `find /app/translations -name '._*' -delete` before launching the server — these binary files are created by macOS Finder when copying files to SMB/AFP shares and caused YAML parse errors in the supervisor
- **Added `translations/.gitignore`** with `._*` to prevent these files from being accidentally committed

---

## 4.6.28 — Fix supervisor ingress spam + bubble setup crash

### Bug fixes
- **Fixed continuous ingress errors in supervisor logs**: the anonymous 10 s sync-poll `setInterval` introduced in 4.6.26 was never cleared even after `removeBubbleFromDOM()` ran — with 2+ browser tabs/devices offset by ~5 s, this produced a steady stream of `Cannot connect` errors in the supervisor log indefinitely; the interval is now stored as `_syncPollInterval` and cancelled on first health-check failure
- **Fixed `setup_chat_bubble` crash on startup**: a JS comment containing `{type:'node'}` inside the Python f-string was parsed by Python as `format(type, "'node'")` → `unsupported format string passed to type.__format__`; escaped to `{{type:'node'}}`

---

## 4.6.27 — Bubble/buttons auto-hide when addon is stopped or deleted

### Bubble & injected buttons cleanup
- **Instant hide on addon stop**: reduced health-check `MAX_FAILS` from 2 to 1 — the floating bubble and all injected buttons disappear within 1–2 seconds of the addon becoming unreachable (connection refused is detected immediately)
- **Model/provider sync poll stopped**: the anonymous 10 s `setInterval` that polled `/api/status` to detect model changes was never cleared; it is now stored as `_syncPollInterval` and cancelled in `removeBubbleFromDOM()`
- **Route poll stopped**: the 1 s DOM-inspection interval that re-injects card/automation buttons on navigation is now stored as `_routePollInterval` and cancelled on first health-check failure, preventing buttons from being re-injected after the backend goes down
- **Card editor & automation buttons removed**: `removeBubbleFromDOM()` now also calls `removeCardEditorButton()` and `removeAutomationIntegration()`, so the "🤖 Amira" button in the card editor and the toolbar button in the automation editor are removed together with the bubble
- **Chat UI polling fixed**: the main chat UI (`chat_ui.py`) now stops its `/api/status` poll and web-session poll after the first failure (was 3 failures / 30 s), and both intervals are cancelled together
- **Auto-cleanup on addon delete (SIGTERM handler)**: `server.py` now registers a `SIGTERM` signal handler that calls `cleanup_chat_bubble()` before exiting — when HA stops or deletes the addon it sends SIGTERM first, so the Lovelace resource registration and all JS files under `/config/www/` are removed cleanly; on next page load no bubble scripts are loaded at all

---

## 4.6.26 — Flow widget: visual fork for choose/if/else branches

### Automation Flow widget (chat_bubble)
- **Visual bifurcation for `choose` and `if/else`**: instead of flattening branches into a linear sequence, the flow now renders a true fork — one SVG bezier arrow per branch diverging from the `choose`/`if` node, one row above and one below
- Each branch gets a **colored label badge** showing the humanized condition (`if tentativi < 3`, `Else`, etc.) followed by its action circles in a horizontal row connected by dashed arrows
- Branch colors use the `BRANCH_GRADS` palette (purple/orange/pink/blue) to visually distinguish alternative paths
- `repeat` nodes also render their sequence as a single-branch fork with a "Loop branch" label
- Internal architecture rewritten: flat `allNodes` array → `segments` array with `{type:'node'}` or `{type:'fork', branches:[...]}`, making the layout extensible for future branch types
- `_renderSegFork` dynamically computes the fork SVG height based on the number of branches

---

## 4.6.25 — Flow widget: smart action summary for complex automations

### Automation Flow widget (chat_bubble)
- **Actions section now shows top-level actions only** — complex automations with `choose` / `if` / `repeat` no longer explode into 10+ individual chips
- `choose` node → compact chip: "Scegli (N)" with branch conditions and action counts in the tooltip (e.g. `1. tentativi < 3 → 6 az.`)
- `if/else` node → chip with condition label; tooltip shows then/else action counts
- `repeat` node → chip reuses existing `flow_repeat_count` / `flow_repeat_while` / `flow_repeat_until` labels
- Added `flow_choose` translation key (EN: Choose / IT: Scegli / ES: Elige / FR: Choisir)

---

## 4.6.24 — Flow widget redesign, i18n unification, multilingual runtime, provider fixes

### Automation Flow widget (chat_bubble)
- Redesigned layout: compact **2-line pipeline** — status pill on top, centered `TRIGGER › CONDITION › ACTION` below
- Section labels (TRIGGER / CONDITION / ACTION) now appear **above** their chips for clearer visual hierarchy
- Entity chips now resolve **`friendly_name`** from `hass.states` instead of showing raw entity_id slugs
- Added **semantic state translation** based on `device_class`: `ON/OFF` now shown as Occupied/Clear, Open/Closed, Wet/Dry, Locked/Unlocked, etc. across all 4 languages
- Added **`_translateDeviceTriggerType`**: device triggers (e.g. `type: occupied`) are now translated correctly instead of showing raw type strings
- Added **`_entityDeviceClass`** and **`_entityTypeHint`** helpers; detail tooltip shows entity domain + device_class
- **`+N` overflow badge**: when a section has multiple items, shows first chip + clickable `+N` badge that expands the full list
- Added 17 new `flow_state_*` translation keys in EN / IT / ES / FR (`occupied`, `detected`, `open`, `closed`, `locked`, `wet`, `dry`, `home`, `away`, `ok`, `low`, `charging`, `connected`, `disconnected`, …)
- Fixed syntax error: unescaped newlines inside JS string literals

### Translation system
- **Unified translation dict** in `core/translations.py`: merged `LANGUAGE_TEXT` + `_LANGUAGE_TEXT_EXTRA` into a single canonical dict (134 keys per language); removed the `.update()` patch loop
- Fixed **language mixing bugs** in `es` and `fr` sections (French strings were incorrectly placed in the Spanish block and vice versa)
- Added `_SUPPORTED_LANGS` guard to prevent unsupported language codes from being used at runtime
- Added new backend strings: `strict_language_lock`, `warn_no_tool_called_with_guidance`, `html_*`, `scheduler_*`, `err_github_copilot_model_incompatible`, and more

### Multilingual runtime
- `fallback.py` and `model_fallback.py`: log messages now use inline `_t(en, it, es, fr)` helper — all provider cooldown / auth-failure / rate-limit warnings are fully localized
- `manager_enhanced.py`: rate-limit skip logs use `get_lang_text` translation wrapper
- `intent.py`: strict language lock injected into all intent prompts; entity search headers localized per language; `set_current_language` synced at API config-change time
- `tools.py`: added `TOOL_DESCRIPTIONS_EN` map for localized tool progress labels

### Provider / API fixes
- Fixed `NameError: name 'SYSTEM_PROMPT' is not defined` on Google Gemini provider (`api.py:2575`) — replaced with `tools.get_system_prompt()`
- Response instructions and voice guidelines in system prompt refined for natural spoken language (no entity IDs, no technical parentheses, concise confirmations)
- Ollama provider renamed from `🦙 Ollama (Local)` → `🦙 Ollama` in the UI provider list

### Other
- `pricing.py`, `mcp.py`, `routes/conversation_routes.py`: minor localization and robustness improvements
- `providers/chatgpt_web.py`, `claude_web.py`, `gemini_web.py`, `github_copilot.py`: compatibility and reliability fixes

---

## 4.6.23 — Messaging UI split + Discord listener compatibility + docs alignment

### Settings UI (Messaging)
- Split **Settings → Messaging** into 3 clear subsections:
  - **Telegram**
  - **WhatsApp**
  - **Discord**
- Kept existing fields and save behavior unchanged, with better visual grouping.

### Discord runtime fix
- Fixed Discord listener registration compatibility across `discord.py` variants:
  - replaced non-portable listener registration with canonical `@client.event` handlers (`on_ready`, `on_message`)
- Added diagnostic startup/event logs in `discord_bot.py` to simplify troubleshooting:
  - listener registration/intents summary
  - inbound Discord event trace (`user/channel/guild/content_len`)

### Documentation updates
- Updated messaging docs to include Discord setup and troubleshooting:
  - `docs/MESSAGING.md`
  - `addons/claude-backend/DOCS.md`
  - `docs/SETUP_HA.md`
- Added Discord in messaging overview, security notes, API examples, and endpoint references.

---

## 4.6.22 — Discord messaging channel

### New: Discord bot integration
- Added Discord messaging channel (like Telegram/WhatsApp) with dedicated bot listener (`discord.py`)
- New settings:
  - `enable_discord`
  - `discord_bot_token`
  - `discord_allowed_channel_ids`
  - `discord_allowed_user_ids`
- Added Discord API endpoint: `POST /api/discord/message`
- Added Discord startup lifecycle in bot bootstrap (`start_messaging_bots`)
- Added Discord support in chat history panel (`Messaging` tab) and channel badges
- Added Discord as assignable channel in Agent Channel Assignment

### Runtime and dependencies
- Added optional dependency `discord.py>=2.4.0`
- Included `discord_bot.py` in Docker image build
- Messaging stats/chats now include Discord channel

---

## 4.6.21 — xAI API, fallback/agent reliability, Ollama Cloud key support

### New provider: xAI (Grok)
- Added native `xai` provider with official endpoint `https://api.x.ai/v1`
- New add-on config key: `xai_api_key` (runtime export `XAI_API_KEY`)
- xAI is now available in the provider selector UI, model catalog, and persisted runtime selection

### Fallback and orchestration
- xAI integrated into the automatic fallback chain (priority, key detection, provider model override)
- Full compatibility with legacy/enhanced ProviderManager and startup model cache refresh

### Updated Grok models + readable names
- Updated xAI model list with recent Grok models (e.g. `grok-4-1-fast-*`, `grok-4.20-*`, `grok-code-fast-1`, `grok-3*`)
- Improved UI display humanization for xAI models not yet statically mapped
- xAI default set to `grok-4-1-fast-non-reasoning`

### Fallback model selector (UI)
- Fixed fallback priority dropdown data parsing in Settings so provider model lists are correctly shown (instead of always `Default provider model`)
- Added compatibility with both legacy and technical model payload shapes returned by `/api/get_models`

### Custom agents runtime fix
- Fixed active-agent runtime synchronization so selected provider/model is correctly applied after agent switch/reload
- Improved persistence/re-init path to avoid mismatch between agent configuration and active chat provider/model

### Gemini API-key schema fix
- Fixed Google Gemini request schema issue that caused `HTTP 400` with:
  `GenerateContentRequest...properties[disabled_by].enum[1]: cannot be empty`

### Grok Web cleanup (experimental)
- Removed `grok_web` from public catalog/update flow
- Added migration safeguard: if stale runtime selection still points to `grok_web`, it is automatically mapped to `xai`
- Improved runtime warning/error clarity for removed provider state

### Ollama Cloud API key support
- Added new add-on config key `ollama_api_key` (`OLLAMA_API_KEY` export in run script)
- Ollama provider/model fetcher now supports `Authorization: Bearer <key>` for cloud endpoints
- Startup model refresh now passes Ollama API key for dynamic catalog refresh
- Auto cloud host resolution: if `ollama_api_key` is set and `ollama_base_url` is left at local default, Amira automatically uses `https://ollama.com` (endpoints under `/api/...`)

### Documentation
- README and DOCS updated with `xai_api_key` and `ollama_api_key` usage notes

---

## 4.6.20 — Humanized automation flow chart, reliable refresh, improved toolbar UX

### Automation flow chart (chat bubble)
- Triggers/conditions/actions are now more readable in natural language (IT/EN/ES/FR), with better humanization of `event`, `template`, notifications, and delays
- Advanced branch support: visual expansion for `choose`, `if/else`, and `repeat` (including nested sequences)
- Improved rendering of multi-target actions:
  - robust parsing of single/list/CSV `entity_id`
  - multi-entity details (one per line) in click panel
  - action data summary (`brightness`, random/template `xy_color`, `rgb_color`)
- More readable multiline notification details:
  - `Notification: ...`
  - `Service: notify.xxx`
- More semantic `device/problem` trigger text where possible (e.g. subject inferred from automation alias, like "Washing machine")

### Last triggered
- Improved `Last triggered` badge:
  - now shows relative time too (e.g. `6 hours ago`) in addition to absolute timestamp
  - if automation is active (`state: on`) the badge uses green styling
  - explicit `Never` fallback when unavailable

### Refresh after automation save
- Flow now detects and applies changes after `Save` without changing page
- Added smart refresh with config signature (`JSON signature`) to avoid unnecessary recomputation
- Fixed duplicated flow cases with:
  - anti-race render lock
  - full stale-instance cleanup before re-render

### Toolbar / automation injection
- Aligned `Amira` button injection behavior with `Flow` button (same toolbar host, same group)
- Removed `position: fixed` fallback for `Amira` button in automations
- Injection now limited to automation detail/edit/trace views, excluding automation list view

### Chat UI tablet
- Improved sidebar resizing on tablets:
  - removed overly strict limits
  - smoother touch drag (`passive: false`, `preventDefault`, `touch-action: none`)
  - dynamic clamp on resize/orientation

---

## 4.6.19 — Unified tool-calling, more reliable HTML dashboards, stabilized Gemini Web

### Tool-calling (OpenClaw-style) on API-key providers
- Centralized `tool_calls` normalization in `providers/enhanced.py` (ID, tool name, JSON arguments)
- Robust malformed-arguments repair (trailing commas, control chars, dirty JSON)
- Automatic tool-call recovery from text output when model ends with `malformed_function_call`
- Same logic applied to providers with dedicated paths:
  - `providers/google.py`
  - `providers/anthropic.py`
  - `providers/ollama.py`

### HTML dashboard: no-tool provider robustness
- Auto-save HTML from text responses now uses `html_base64` for long payloads on no-tool providers (`gemini_web`, `openai_codex`, etc.), avoiding `RAW_HTML_REQUIRED` blocks for long inline HTML
- More resilient tool-arguments parsing in `api.py` before execution
- One-shot retry on `create_html_dashboard` intent when `malformed_function_call` arrives with no executable calls

### Gemini Web (UNSTABLE) — practical improvements
- Fixed SDK crash: undefined `_base_timeout`
- Added `gemini-3.1-pro` model support in Gemini Web catalog
- Hard timeouts for SDK stream/non-stream to avoid infinite stalls
- Alias retry after `3.1-pro` failures and clearer gateway error handling
- For HTML intents, automatic preference for more stable model (`gemini-3.0-flash`) on long requests
- On web instability (`timeout/stalled/502`), automatic fallback to Google API-key provider when configured

### Dashboard UX
- Cleaner sidebar titles: removed duplicates like `Amira — Amira - ...`
- Removed forced `Dashboard` suffix from final title
- Agent prefix is now applied only once

---

## 4.6.18 — Telegram security: authorized user whitelist

### New feature: Telegram whitelist
- **Risk resolved**: previously any Telegram user could send commands to the bot and control the home
- New **"Authorized User IDs"** field in Settings → Messaging: comma-separated Telegram user IDs (e.g. `123456789,987654321`)
- If the list is non-empty, users not in list receive a block message and their message is ignored
- Rejection message is **multilingual** (IT/EN/ES/FR) and follows the language set in Settings
- If left empty, the bot remains open (previous behavior) — not recommended
- How to find your ID: open Telegram → search `@userinfobot` → send `/start`

### Fix: `GET /api/settings` crash — non-serializable set
- `TELEGRAM_ALLOWED_IDS` was stored as a Python `set` in memory, but JSON cannot serialize it
- Fix: convert to sorted comma-separated string before API response

### README updated
- Added section "🔒 Telegram Security — User Whitelist" with step-by-step instructions

---

## 4.6.17 — Agent globals fix, Groq failed_generation, UI agent form

### Fix: `_sync_active_agent_globals` crash
- Removed stale `_override` reference left after `system_prompt_override` refactor — it caused `NameError` on every active-agent switch

### Fix: Groq `failed_generation` — automatic fallback to tool simulator
- When Groq returns `"Failed to call a function. Please adjust your prompt."` in SSE stream (before any content), it is now intercepted automatically and retried with the **XML tool simulator** without showing user-facing errors
- Distinguishes two cases: `"tool calling not supported"` → model permanently marked simulator-only; `"failed_generation"` → fallback only for that request (model remains native for next calls)

### Fix: Telegram/WhatsApp channels already assigned — agent UI
- Channel checkbox is now **disabled** (not clickable) if already assigned to another agent
- Added visible orange badge `🔒 Already assigned to: <agent_id>` under checkbox — no longer hidden in tooltip
- Fixed lock Unicode escape (`\uD83D\uDD12` surrogate → `\U0001F512`)
- Added `agent_channel_taken` translation string in EN/IT/ES/FR

### UI improvement: dropdown emoji picker in agent form
- Replaced flat 16-emoji grid (space-heavy) with a **compact dropdown**: button with current emoji + `▾`, click opens floating panel, selecting closes panel, outside click closes without changes

### Refactor: agent `instructions` — prepended to HA prompt (from 4.6.16)
- Removed `system_prompt_override` (which replaced full HA prompt); introduced `instructions` field that is **prepended** to HA default system prompt
- Backward compatibility: old JSON key `system_prompt` → read as `instructions`
- Updated UI: "AGENT INSTRUCTIONS" label with placeholder showing proper third-person usage
- `get_system_prompt()` in `tools.py` now composes `agent_instructions + custom_user_block + HA_default`

### Additional fixes (from 4.6.16)
- **Gemini Web**: added to `catalog_routes.py` and `model_catalog.py` — now visible in provider dropdown; modal no longer always visible (CSS fix); JS connect/disconnect completed
- **Bubble JS Error**: red banner now appears only for our script errors, not third-party component errors (Bubble Card, etc.)
- **Custom system prompt**: no longer replaces HA prompt; now prepended
- **`armv7` → `armhf`**: fixed deprecated arch value in `config.yaml`
- **s6 finish script**: auto-restart up to 5 times on unexpected crash; halt only on clean stop or SIGTERM

---

## 4.6.15 — Fix provider: errori tool call, TPM Groq, hallucination claude_web; UI stato sessione bubble

### Fix: provider Groq
- **Errore messaggio sbagliato su tool call malformato**: quando il modello generava un nome funzione tipo `update_automation,{...}` il sistema mostrava erroneamente "tier limitation". Ora viene rilevato con regex `(\w+)[,{]` e mostrato il messaggio corretto "malformed tool call"
- **`_TIER_MISSING` dict errato**: `update_automation` e `preview_automation_change` erano listati come mancanti dall'extended tier pur essendo già presenti — corretti
- **429 TPM dopo preview**: il tool result di `preview_automation_change` conteneva `old_yaml`/`new_yaml` nella history, causando overflow del limite 12k token/min su Groq. Aggiunto `_compress_tool_result` in `groq.py` che rimuove quei campi dalla history prima di ogni richiesta
- **Modello allam-2-7b**: rispondeva con output garbage — già gestito tramite `_SIMULATOR_MODELS` (fallback XML simulator)

### Fix: `update_automation` eseguita dopo "no"
- Aggiunta regola di cancellazione esplicita nel prompt compact: se l'utente dice no/annulla/cancel il modello non deve chiamare write tool
- Aggiornata descrizione di `update_automation` in `HA_TOOLS_COMPACT` con istruzione "If user says no/cancel/annulla, do NOT call this tool"

### Fix: claude_web hallucinated success
- **Rilevamento runtime**: aggiunto tracciamento `_write_tools_executed` nell'agentic loop; se il provider è XML-simulator e la risposta contiene frasi di successo ("aggiornata", "applied", "✅", ecc.) senza aver chiamato nessun write tool → viene iniettato un evento `system_message` di avviso
- **Prompt XML simulator rafforzato**: aggiunta sezione `CONFIRMATION HANDLING — MANDATORY` con regole esplicite su cosa fare quando l'utente conferma con sì/yes/ok
- **Anti-artifact rules**: aggiunte regole 5 e 6 in `claude_web.py` per vietare YAML in code block e richiedere `<tool_call>` dopo conferma
- Aggiunte chiavi `warn_no_tool_called` e `err_malformed_tool_call` nei dizionari EN/IT/ES/FR
- Aggiunto handler `system_message` nel loop SSE di `chat_bubble.py`

### Nuovo: provider sperimentale `claude_web_native`
- Nuovo file `providers/claude_web_native.py`: prova i tre approcci possibili per usare la session key di claude.ai con l'API Messages nativa (x-api-key, Bearer, proxy claude.ai)
- Nuovo file `test_claude_web_native.py`: script standalone per testare la compatibilità — include header browser-like per passare Cloudflare
- Registrato in `providers/__init__.py` e `providers/manager.py`
- **Risultato**: la session key `sk-ant-sid02-` NON è compatibile con l'API Messages; il provider rimane sperimentale/documentativo

### UI bubble: barra verde stato sessione e disconnect
- **Barra verde `session-conn-bar`**: banner fisso tra l'agent-bar e la context-bar del pannello bubble — identico allo stile del banner Codex nella chat_ui. Mostra dot verde, label provider, dettaglio (giorni connesso / scadenza token) e bottone Disconnect
- **`checkAndShowSessionStatus(provider)`**: aggiorna la barra al cambio provider e all'apertura iniziale del pannello. Copre tre provider:
  - `claude_web` / `claude_web_native` → "🔗 Claude Web · connesso da Xg" + disconnect via `POST /api/session/claude_web/clear`
  - `github_copilot` → "🔗 GitHub Copilot · connesso da Xg" + disconnect via `POST /api/oauth/copilot/revoke`
  - `openai_codex` → "🔑 OpenAI Codex · account_id · scade in Xh Ym" + disconnect via `POST /api/oauth/codex/revoke`
- Per tutti gli altri provider la barra viene nascosta automaticamente
- **`clear_token()` in `providers/github_copilot.py`**: svuota il token in memoria e cancella `/data/oauth_copilot.json`
- **`POST /api/oauth/copilot/revoke`** aggiunto in `api.py`

---

## 4.6.14 — Fix: dashboard rotte con LLM deboli (Llama, NVIDIA, ecc.)
- **Nuovo `_repair_malformed_html`**: ripara errori strutturali prodotti da modelli meno capaci prima del salvataggio
  - Tag HTML malformati (`<div class=<div class=`) → rimossi
  - `const tok = JSON.parse(localStorage...` troncato → rimosso (causa SyntaxError con auth patch)
  - `getTokenAsync` duplicato dentro Vue setup() → rimosso (la versione globale dell'auth patch è sufficiente)
- La funzione gira prima di tutti gli altri sanitizer nella pipeline

## 4.6.13 — Dashboard: istruzioni generiche per tutti i domini HA
- **Colori domain-aware**: palette adattiva per luci, batterie, tapparelle, clima, sicurezza, acqua, presenza, aria — non solo solare
- **Inventiva per dominio**: elementi visivi specifici per tipo (fill-bar batterie, shutter CSS animato, room heat map, Sankey flow, occupancy grid, AQI scale, ecc.)
- **Grafici contestualizzati**: ogni tipo di chart abbinato a esempi per tutti i domini (luci, batterie, tapparelle, clima, energia, sicurezza, acqua)

## 4.6.12 — Dashboard: più varietà di grafici, colori e creatività
- **Grafici**: l'IA ora riceve istruzioni esplicite su quando usare bar, line/area, donut/pie, gauge, scatter, mixed, stacked — sempre almeno 2 tipi diversi per dashboard
- **Colori**: palette dominio-specifiche (solar=amber/green, clima=cyan, sicurezza=red, batterie=lime), gradienti per ogni card, mai layout monotone
- **Inventiva**: suggerimenti su heatmap, sparkline, Sankey flow, contatori animati, pulse su valori live

## 4.6.11 — Fix: valori sensori tutti 0 nelle dashboard
- **Fix**: l'auth patch non sostituiva `fetch(\`${HA_URL}/api/...\`)` e `fetch(HA_URL + '/api/...')` con `_authFetch` — le chiamate HA restituivano 401 e i valori rimanevano 0. Aggiunto regex per template literal e concatenazione con variabile

## 4.6.10 — Fix: HTML dashboard non appare nella cronologia chat
- **Fix**: riaprendo una vecchia chat dopo aver creato una dashboard, non si vede più tutto il codice HTML — il messaggio in cronologia viene sostituito con una breve conferma testuale dopo il salvataggio del file

## 4.6.9 — Dashboard design guidelines: tabs, popup, colori, effetto wow
- **Rimosso quality gate bloccante**: nessuna rigenerazione forzata — l'LLM deve farlo bene al primo tentativo
- **Nuove istruzioni di design** in `intent.py` (prompt principale, vale per tutti i provider inclusi LLM web), tool description e system prompt: focus su colori vibranti, gradient, tab navigation, modal/popup per dettagli, glassmorphism, animazioni CSS on load
- **Tabs come default** per dashboard con 3+ argomenti — single-page tab router JS con nav bar stilizzata
- **Grafici non obbligatori**: includere quando il dato lo giustifica, non su ogni dashboard
- **Click-to-expand obbligatorio**: ogni card entità apre il pannello more-info HA o un modal con history chart

## 4.6.8 — Dashboard quality enforcement: grafici e design ricco obbligatori
- **Quality gate semi-bloccante**: se la dashboard non ha almeno 2 grafici Chart.js visibili nel layout principale (non in modali), l'LLM riceve un errore con istruzioni precise e deve rigenerare
- **Sections mode quality check**: se le sezioni non includono nessun tipo visivo ricco (`trend`, `gauge`, `gauges`, `chart`, `flow`), la dashboard viene rigettata
- **System prompt aggiornato**: aggiunta sezione "HTML Dashboard Visual Requirements" che elenca i requisiti obbligatori (grafici, gradienti, colori, CSS variables) — il server li fa rispettare
- **Tool description aggiornata**: rimosso "PREFERRED/FALLBACK", aggiunto banner ⚠️ MANDATORY con i requisiti visuali specifici che verranno enforced server-side

## 4.6.7 — Fix bubble companion app (tablet)
- **Fix bubble su tablet/companion app**: ripristinato `_ensureIngressSession()` per creare il cookie `hassio_session` tramite Bearer token — necessario per la companion app che non ottiene il cookie automaticamente come il browser desktop. Aggiunto retry automatico di `loadAgents()` se la sessione non è ancora pronta.

## 4.6.6 - Fix create dashboard
-- **Fix create dashboard**

## 4.6.5 — HTML dashboard reliability, auth hardening, quality guardrails
- **HTML dashboard generation reliability**
  - Fixed chunked `create_html_dashboard` loop handling and improved draft auto-finalization path
  - Improved truncated/escaped HTML normalization and malformed `<head>` repair
  - Added stricter detection to avoid unnecessary autocomplete on complete raw HTML
  - Enforced dashboard page `<title>` alignment with saved sidebar title (`Amira — ...`)

- **Auth + data loading fixes for generated dashboards**
  - Hardened auth patch to sanitize stale static headers (`Authorization: Bearer + tok`) even when helper is already present
  - Added `_authFetch(...)` wrapper injection for HA `/api/states` and `/api/history` calls to reduce token race issues
  - Result: generated dashboards are less likely to show persistent `n/d` due to early token resolution timing

- **Quality guardrails (non-template)**
  - Removed backend prebuilt chart auto-injection to keep layouts model-driven
  - Added mandatory chart requirements in both intent prompt and `create_html_dashboard` tool description:
    - at least 2 always-visible charts in main layout
    - one trend (line/area) + one comparative (bar/doughnut/pie)
  - Added raw HTML quality gate: reject KPI-only outputs when charts are expected

- **Dashboard generation telemetry**
  - Added minimal generation metrics persistence in `/config/amira/dashboard_generation_metrics.json`
  - Tracks success/rejection and recent quality details for troubleshooting provider/model behavior

- **Delete dashboard robustness**
  - `delete_dashboard` now resolves by id/url_path/title with slug normalization and `.html` tolerance
  - Also removes matching file under `/config/www/dashboards/*.html` when present

- **Runtime UX/i18n consistency**
  - Replaced newly introduced hardcoded Italian runtime status strings with neutral messages in tool-loop paths

## 4.6.4 — MCP LLM-first fix: tool dinamici nel prompt + esecuzione corretta
- **MCP in LLM-first (ToolRegistry attivo)**
  - I tool MCP dinamici runtime ora vengono sempre iniettati in `tool_schemas` (`+N`), anche quando il ToolRegistry è inizializzato da catalogo statico legacy
  - Risolto caso in cui il modello vedeva e chiamava `mcp_*` ma il backend rispondeva `Unknown tool` perché l'esecuzione passava dal registry statico
  - I tool `mcp_*` ora vengono eseguiti via dispatcher MCP diretto nel tool loop

- **Affidabilità richiesta MCP**
  - Regola prompt MCP generica su richieste DB/filesystem/repo (senza hardcode SQLite-only)
  - Retry interno one-shot se il modello chiude senza tool_call su richiesta chiaramente MCP-oriented

- **HTML dashboard draft fail-safe**
  - Fix caso `create_html_dashboard` in chunked mode: se il modello si ferma su `draft_started/draft_appended`
    e poi risponde “creata” senza chiamata finale, il backend ora finalizza automaticamente la bozza

## 4.6.3 — MCP UX/runtime: stato server, stop, autostart persistente manuale
- **MCP UI (chat_ui)**
  - Aggiunto badge stato per ogni server MCP con pallino:
    - verde = attivo
    - grigio = fermo
  - Aggiunto pulsante **Stop** accanto a **Start**
  - Pulsanti Start/Stop disabilitati dinamicamente in base allo stato corrente
  - Stato live letto da `/api/mcp/servers` per mostrare anche i server configurati ma non avviati

- **MCP API/runtime (api.py + mcp.py)**
  - Nuovo endpoint: `POST /api/mcp/server/<name>/stop`
  - `POST /api/mcp/server/<name>/start` ora salva il server in autostart runtime
  - `GET /api/mcp/servers` ora restituisce anche:
    - `running`
    - `state` (`running`/`stopped`)
    - `autostart`
    - server configurati ma non avviati
  - Aggiunta persistenza runtime su `/config/amira/mcp_runtime.json`:
    - se avvii manualmente un server e lo lasci attivo, al riavvio addon riparte
    - se lo stoppi, viene rimosso dall’autostart
  - Avvio MCP al boot limitato ai soli server marcati autostart (non tutti quelli nel config)
- **MCP manager**
  - Nuovo metodo `remove_server(name)` per disconnettere e deregistrare un singolo server

## 4.6.2 — fix: manage_helpers API, preview guard, UI diff e costi panel
- ** tools.py

  - manage_helpers — 3 bug fix API:
    - WS endpoint corretto: input_number/create (era
  config/input_number/create — endpoint inesistente in HA)
    - REST create: POST /config/{type}/config con id nel body (era POST con ID
   nell'URL → 404)
    - REST update: PUT /config/{type}/config/{id} (era POST)
    - WS create: rimosso {type}_id dal payload (HA auto-genera l'ID dal nome)
    - WS delete: stesso fix endpoint
    - Rimosso import os dentro manage_helpers che rendeva os locale all'intera
   funzione → crashava preview_automation_change con UnboundLocalError
    - Counter list: mostra solo counter.*, non tutti gli input_number.*

  api.py

  - Preview confirmation guard (nuovo sistema):
    - preview_automation_change → mostra diff → utente conferma →
  update_automation
    - Guard blocca update_automation se non c'è un preview valido nella
  sessione
    - Se stessa automation ma firma diversa (LLM rigenera changes leggermente
  diverse): override con le changes esatte del preview mostrato → elimina il
  doppio loop di conferma
    - Normalizzazione trigger/triggers, action/actions, condition/conditions
  in _normalize_automation_change_args per evitare falsi-positivi nel
  sig-match
  - _format_write_tool_response:
    - Aggiunta gestione errori (era assente — AttributeError se
  result["result"] non era dict)
    - YAML completo rimosso quando il diff è già mostrato; mostrato solo per
  CREATE o quando non ci sono differenze
    - preview_automation_change aggiunto a _WRITE_TOOLS → genera il diff
  rosso/verde in UI

  intent.py

  - preview_automation_change va chiamata immediatamente senza chiedere
  "procedo?": eliminata la doppia conferma
  - Exception per preview_automation_change aggiunta alla regola generale "ask
   before executing"

  providers/tool_simulator.py

  - _repair_json: aggiunta _escape_control_chars_in_strings — converte
  newline/tab letterali dentro stringhe JSON in \n/\t (causa frequente di
  parse failure con YAML multilinea nei tool call)
  - Log errore esteso da 200 a 1000 char, con posizione esatta dell'errore
  JSON

  chat_ui.py

  - Costi panel: giorni raggruppati per mese con <details>/<summary>
  collassabili; mese corrente aperto di default, precedenti chiusi; 35 giorni
  invece di 7; giorno corrente evidenziato

## 4.6.1 — Fix bubble auth

### 🐛 Fix
- **Fix bubble 401 (Ingress session)**: fix bubble autenticazione
