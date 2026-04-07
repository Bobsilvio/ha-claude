# Changelog

> **⚠️ After updating, rebuild the add-on** (Settings → Add-ons → Amira → Rebuild) to apply new dependencies.

## 4.7.2 — In-flight context compaction for multi-round tool calls

### Fix
- **In-flight tool result compaction** (`api.py`): in multi-round conversations, tool results from all rounds except the most recent one are now condensed in-place before each subsequent API call. This prevents the accumulated context from growing too large and causing 2-minute read timeouts (the symptom seen with Qwen3.6-plus:free on complex automation tasks). The most recent round's results are always kept full so the model has complete data to work with.
- Previously, 4.7.0 compaction only applied when saving to history (between sessions). This extends it to the active `messages` array within the same multi-round request.

---

## 4.7.1 — Preserve intermediate text bubbles during multi-round tool calls

### Fix
- **Intermediate assistant text no longer disappears** (`chat_ui.py`): when the model generates text ("Ottimo, procedo...") before calling tools, that bubble now stays visible in the chat instead of being erased by the `clear` event. Subsequent content from the next round appears in a new bubble below it. Previously the intermediate text was lost both from the chat and from the log.
- **Server-side log for intermediate text** (`api.py`): added `💬 Intermediate text before tool round` log line so the text is traceable even if the chat is not visible.

---

## 4.7.0 — Conversation history compaction for large tool results

### Improvement
- **Tool result compaction** (`api.py`): large tool results (> 3000 chars) are now stored in conversation history as smart summaries instead of the raw full content. The full result is still used in the current round (the model works on the real data); only what goes into history is condensed. This prevents context window overflow on subsequent turns and avoids redundant re-fetches.
  - `get_dashboard_config`: stores view names, card counts, card types used
  - `get_entities` / `search_entities` / `get_integration_entities`: stores entity count + first 40 entity_ids
  - `get_automations`: stores automation count + first 40 aliases
  - All other tools: truncated to first 3000 chars with a note
- Handles both Anthropic format (`role=user, content=[{type:tool_result}]`) and OpenAI/OpenRouter format (`role=tool, content=str`).

---

## 4.6.99 — System prompt: avoid redundant tool calls

### Improvement
- **`HA_SYSTEM_GUIDANCE` updated** (`intent.py`): added explicit instruction to avoid calling the same tool twice if its result is already in conversation history. Models (especially non-Anthropic ones like Qwen) tend to re-fetch data already present in context, wasting tokens and slowing responses. The rule covers all tools generically (GENERAL RULES section) and is reinforced specifically for `get_dashboard_config` in the DASHBOARDS section.

---

## 4.6.98 — Fix: partial response never cleared on mid-stream error or dropped tool calls

### Bug fix
- **Response no longer disappears after tool-call drops** (`chat_ui.py`): when the LLM produced text in round N followed by tool calls that were all dropped, the server emitted a `clear` event before round N+1. If round N+1 produced no new text, the `done` event arrived with an empty `fullText`, leaving an empty assistant bubble. Fix: on `clear`, the current `fullText` and `div` are saved. On `done` (or stream error), if `fullText` is still empty and a saved text exists, the saved text is restored and re-rendered — so the user always sees the last meaningful response.

---

## 4.6.97 — New tool: get_attribute

### New feature
- **`get_attribute` tool** (`tools.py`): new read-only tool that returns all attributes of an entity, or a specific attribute by name. Accepts `entity_id` (required) and `attribute` (optional, e.g. `"last_triggered"`). Unlike `get_entity_state` which filters to a fixed set of useful keys, `get_attribute` returns the raw attribute value — useful for fields like `last_triggered`, `battery_level`, `rgb_color`, `supported_features`, etc. Added as an alias/extension to handle models (e.g. Qwen) that call this tool name instead of `get_entity_state`.

---

## 4.6.96 — Fix: HTML dashboard false-positive intent + update_dashboard safety

### Bug fixes
- **False-positive HTML dashboard routing** (`intent.py`): messages that quoted or mentioned "JS templates", "javascript", etc. while asking about a Lovelace YAML dashboard were incorrectly routed to the `create_html_dashboard` intent, restricting Claude to only 5 tools and hiding `get_dashboard_config`/`update_dashboard`. The detection now requires EITHER an explicit HTML file reference (`/local/dashboards`, `.html`) OR both an HTML keyword AND a dashboard keyword — a single HTML keyword alone no longer triggers routing.
- **`update_dashboard` empty-views guard** (`tools.py`): when Claude hit the output token limit mid-generation, the tool call was emitted with `views=[]`, silently wiping the dashboard. The tool now refuses immediately with an explicit error message when `views` is empty, leaving the dashboard unchanged and asking the user to split the update into smaller turns.
- **Raised `max_tokens` ceiling** (`providers/anthropic.py`, `providers/openai.py`): base limit increased from 8192 → 32768 (32k), HTML dashboard intent from 16384 → 65536 (64k). The old 8192 limit was a claude-3 legacy value; claude-opus-4-6 supports 32k and claude-sonnet-4-6 supports 64k output tokens. This prevents truncation when generating large Lovelace YAML rewrites with `update_dashboard`.

---

## 4.6.95 — Fix: incoming message log now from api module with CHAT level

### Bug fix
- **`📨` log moved from `routes/chat_routes.py` to `api.py`** — both `chat_with_ai` and `stream_chat_with_ai` now log the incoming message at `CHAT` level (`💬`), consistent with the outgoing `📤` log. Previously the log appeared as `🟢 INFO: routes.chat_routes ->`, making it hard to visually trace request/response pairs. Now both lines read `💬 CHAT: api -> 📨 [provider]: ...` / `💬 CHAT: api -> 📤 [provider/model]: ...`.

---

## 4.6.94 — Remove duplicate Ollama URL from Settings UI

### Improvement
- **Ollama URL removed from Settings panel** — `ollama_base_url` is configured only in `config.yaml` (HA add-on UI), not duplicated in the Amira ⚙️ Settings panel. Removed: subsection rendering in `chat_ui.py`, LABELS entry, all IT/EN/ES/FR translations for Ollama settings, `SETTINGS_DEFAULTS`/`_SETTINGS_GLOBAL_MAP` entries in `settings_service.py`.
- `GET /api/ollama/test` endpoint kept (usable for future tooling or manual probing).

---

## 4.6.93 — Ollama: empty URL by default, provider hidden until configured

### Improvement
- **`ollama_base_url` defaults to `""`** in `config.yaml`, `api.py`, and `settings_service.py`. An empty URL means: Ollama is not configured, the provider does not appear in the UI selector, no connection is attempted at startup. Set a URL (e.g. `http://192.168.1.x:11434`) to enable it.
- **Skip startup model discovery** if `OLLAMA_BASE_URL` is empty — avoids a useless 2s connection timeout on every add-on start.
- `catalog_routes.py` already conditioned on `OLLAMA_BASE_URL` being non-empty — no change needed there.

---

## 4.6.92 — Ollama: URL configurable from Settings UI + Test connection button

### Improvement
- **Ollama URL in Settings** — `ollama_base_url` is now a runtime setting: editable in the ⚙️ Settings panel under AI → Ollama, saved to `settings.json`, applied immediately without add-on restart. Previously only configurable via `config.yaml` (required restart).
- **Test connection button** — next to the URL field a Test button pings `GET /api/tags` on the configured Ollama server and shows: ✅ + model list if reachable, ❌ + error message if not. New endpoint: `GET /api/ollama/test?url=<url>`.
- Translations: IT/EN/ES/FR for all new strings.

---

## 4.6.91 — Fix: embedded SSE error (HTTP 200 + error body) now retries properly

### Bug fix
- **Double-call on HTTP 200 with upstream error** — OpenRouter (and other providers) sometimes return HTTP 200 with an embedded SSE error event (e.g. `{"error": {...}}`) when the upstream model is rate-limited. Previously this bypassed `enhanced.py`'s retry logic (which only triggers on exceptions), causing the full fallback chain to run again as a "direct call" — effectively doubling all retry delays (~15s total for a simple "ciao"). Fix: when an embedded SSE error is received with no content yet emitted, `_openai_compat_stream` now raises `RuntimeError` instead of yielding an error event. This lets `stream_chat_with_caching` retry it automatically, and since the error message contains "rate limit", `_should_retry_error` correctly classifies it as retryable.

---

## 4.6.90 — Sticky copy button on code blocks

### Improvement
- **Sticky copy button in code blocks** — the Copy button now uses `position:sticky;top:0` inside a header bar instead of `position:absolute`. When scrolling through a long code block in the chat, the button stays anchored to the top of the visible area at all times — no need to scroll back to the top to copy. Works in both the bubble and the main chat UI. Dark mode supported.

---

## 4.6.89 — Fix: YAML context re-injection for claude_web + removed entity validation

### Bug fix
- **Bubble card panel: YAML re-injected on every message with claude_web** — for no-tool providers (claude_web, etc.) tokens arrive all at once in the `done` event as `full_text` instead of individual `token` events. `_cardContextConfirmed` was never set to `true`, causing the full YAML context to be re-injected on every follow-up message. Fix: the flag is now set on `done` events as well (both in the main loop and the flush section).
- **Removed entity validation from card editor context** — the `ENTITY VALIDATION (hass.states)` block with `VALID`/`NOT FOUND` checks was removed from `buildContextPrefix()`. It was redundant (the bubble already handles it) and added verbose rules to the context. Card editing rules simplified from 10 to 6.

---

## 4.6.88 — claude_web conversation reuse + YAML deduplication nel card panel

### Improvement
- **`claude_web`: conversazione riutilizzata tra i turni** — invece di creare una nuova conversazione su claude.ai ad ogni request, il provider ora mantiene un `_conv_cache` (session_id → conv_uuid). Stessa session + stesso intent + stesso model → riusa l'UUID esistente e invia solo il nuovo messaggio (senza `[CONVERSATION HISTORY]`). Invalidazione automatica su: cambio intent, cambio model, TTL 12h, o errore 404 (conv scaduta su claude.ai, con retry automatico e nuova conv).
- **`api.py`: session_id propagato ai provider** — `intent_info["session_id"] = session_id` iniettato prima del tool loop, così i provider possono identificare la sessione corrente per la cache.
- **Bubble card panel: deduplicazione YAML** — il `[CONTEXT: User is editing a Lovelace card...{yaml}...]` viene inviato solo al primo messaggio della sessione o quando lo YAML cambia (hash tracking). I messaggi successivi con lo stesso YAML inviano solo la domanda dell'utente. Reset su nuova sessione ("+" button) o quando lo YAML cambia (nuova card). Riduce drasticamente il payload per card con YAML grande (es. 82k char → solo poche decine di char per i follow-up).

### Provider check
- **`grok_web`**: già riutilizza conversazioni esistenti (cerca `conversations[0]`) ✓
- **`chatgpt_web`**: usa `conversation_id: null` ogni volta — reuse possibile ma richiede `history_and_training_disabled: false` (salverebbe in account ChatGPT), lasciato per ora
- **`gemini_web`**: API stateless per sua natura, nessun cambiamento necessario

---

## 4.6.87 — Fix: smart context noise per card_editor + stripping CONTEXT block

### Bug fix
- **Smart context inutile per card_editor** — quando l'intent era `card_editor`, `build_smart_context` riceveva il messaggio con il blocco `[CONTEXT: User is editing a Lovelace card...{yaml}...]` e cercava entità basandosi su parole dentro lo YAML (es. `sensor`, `button`, `bolletta`, `from`, `card`, ecc.), aggiungendo ~15k char di context irrilevante e sprecando token. Fix: se `intent == "card_editor"`, `build_smart_context` ritorna stringa vuota immediatamente — il YAML è già nel messaggio.
- **Stripping del blocco `[CONTEXT: ...]`** — aggiunto strip del blocco `[CONTEXT: ...]` in `build_smart_context` (parallelo all'esistente strip di `[FILE:...]`), per evitare che contenuti YAML/HTML iniettati dalla bubble inquinino il matching dei keyword nelle ricerche entità.

---

## 4.6.86 — Fix: card editor dialog si espande a tutto schermo quando si apre il pannello Amira

### Bug fix
- **Dialog card editor espanso a tutto schermo** — quando si cliccava il pulsante 🤖 Amira nel footer dell'editor card, la surface del dialog riceveva `max-height:90vh !important` che sovrascriveva il sizing nativo di HA e forzava il dialog a occupare quasi l'intera viewport. Fix: la height viene ora calcolata come `min(altezza_attuale + 360px, 90vh)`, così il dialog cresce solo di quanto necessario per ospitare il pannello Amira. Aggiunto anche `height:''` in `closeCardPanel()` per pulire correttamente il valore al momento della chiusura.

---

## 4.6.85 — Conversational routing: bypass tools for casual chat

### Improvement
- **Natural conversational routing** — added `_is_conversational()` heuristic in `intent.py` that detects casual chat (greetings, "chi sei", "come stai", "dimmi una barzelletta", "cosa pensi", etc.) and routes directly to `chat` intent (no tools, no HA context). HA action/entity keywords act as blockers so real HA requests are never mis-routed.
- **Increased chat keyword window** — legacy keyword check raised from ≤ 5 words to ≤ 8 words.
- **MCP injection guard** — MCP tools are no longer injected when `intent == "chat"` (tools=[]). Prevents the model from unexpectedly calling Supermemory or other MCP tools during chitchat.
- **Improved chat prompt** — `INTENT_PROMPTS["chat"]` rewritten to be more natural: friendly, no entity_id mentions, explains capabilities if asked.

---

## 4.6.84 — Fix: automation 404 error and false context injection when file is open

### Bug fix
- **`HA API error 404` + spurious automation context when a file is open** — `build_smart_context` used `user_message.lower()` as `msg_lower` without stripping `[FILE:...]` blocks. A package YAML containing `automation:` triggered the automation keyword check; the fuzzy name-matching then found automation names whose words appeared in the file content (e.g. "raccolta differenziata"). The resulting REST call `GET config/automation/config/{id}` returned 404 because the automation was matched by coincidence, not intent. Fix: strip `[FILE:...]...[/FILE]` blocks from `msg_lower` at the top of `build_smart_context` (same pattern already used in `detect_intent`).

---

## 4.6.83 — Fix: AI defaulting to html-js-card without being asked

### Bug fix
- **AI generating `type: custom:html-js-card` without explicit request** — when asked to create a Lovelace card for a complex package, the AI would spontaneously choose html-js-card even without the skill being active. Root cause: no rule in the system prompt prevented it. Fix: added a "Lovelace Card Format (CRITICAL)" rule to the system prompt explicitly stating that `custom:html-js-card` must only be used when the user explicitly asks for it (e.g. "fammela con html-js-card", "/html-js-card"). Default card format is standard Lovelace YAML (`type: entities`, `type: grid`, `type: tile`, Mushroom, etc.).

---

## 4.6.82 — Skill banner: deactivate button

### New feature
- **"✕ Disattiva" button in skill banner** — when a skill is active (e.g. `/html-js-card`), a new outlined button appears next to "New chat" to deactivate the skill in the current session without opening a new chat. Calls `POST /api/chat/skill/deactivate` and hides the banner. Useful when the user wants to switch from a skill-specific mode (e.g. html-js-card) back to generic Lovelace YAML generation in the same session.
- **`POST /api/chat/skill/deactivate`** — new backend endpoint that removes the session from `session_active_skill`, stopping skill re-injection for subsequent messages.

---

## 4.6.81 — Fix: Lovelace YAML false positive with file context

### Bug fix
- **Wrong `card_editor` routing when asking for a card with a package file open** — `has_lovelace_yaml` used `re.search(r"(?mi)^\s*type\s*:\s*", user_message)` on the raw message including `[FILE:...]` content. Package/automation YAML files contain `type:` keys (e.g. automation actions), triggering "Lovelace YAML detected" and routing to `card_editor` instead of the correct intent. Fix: when `_has_file_context` is True, the raw-message regex check is skipped; only the stripped `msg` (without file content) is checked for YAML keywords.

---

## 4.6.80 — Fix: _has_file_context not defined in build_smart_context

### Bug fix
- **`NameError: name '_has_file_context' is not defined`** — `_has_file_context` was defined only inside `detect_intent` but used also in `build_smart_context` (a separate function). Fix: detect `[FILE:...]` blocks locally at the top of `build_smart_context` as well.

---

## 4.6.79 — File context: extract entities directly from file content

### New feature
- **File-based entity lookup** — when a file is open in the file panel, the smart context now extracts HA entity IDs directly from the file content (regex on all known domains: `input_boolean`, `input_select`, `sensor`, `automation`, etc.) and looks up their current states in HA. The result replaces the generic keyword search entirely, so the AI gets exactly the entities used in the file (e.g. `input_boolean.raccolta_differenziata_da_notificare`) instead of unrelated update/package entities. Logged as `## ENTITA DEL FILE`.

---

## 4.6.78 — File context: larger limit + cleaner entity search

### Improvements
- **File context limit raised from 3000 to 15000 chars** — HA package files are often 5-20 KB; the previous 3000-char limit caused the AI to see only a fraction of the file and ask clarifying questions about entities it should have already seen.
- **Suppress generic Lovelace/YAML stop-words from entity search when file context is present** — words like `card`, `package`, `lovelace`, `type`, `name` now join the stop-word list when a `[FILE:...]` block is in the message, preventing dozens of irrelevant update/package entities from polluting the smart context.

---

## 4.6.77 — Fix: file context incorrectly routed to create_html_dashboard

### Bug fix
- **Wrong intent when asking for a card with a file open** — when the file panel injected `[FILE:...]` blocks, the word "card" in the user message (or "card" matching an existing `.html` filename in `www/dashboards`) triggered `has_html_ref = True`, routing the request to `create_html_dashboard` with only 5 tools and an HTML-only prompt. Fix: strip `[FILE:...]` blocks from `clean_msg` before intent keyword matching; when file context is present, require explicit HTML/JS keywords (`has_html_kw`) to route to `create_html_dashboard` — `has_html_ref` alone is not enough.

---

## 4.6.76 — Fix: bubble JS syntax error (font-family escaped quotes)

### Bug fix
- **`SyntaxError: missing ] after element list` in bubble JS** — the new diff-table CSS style block used `\'SF Mono\'` inside a Python f-string (`f"""..."""`). Python consumed the backslashes and output bare `'`, which terminated the surrounding JS single-quoted string early and broke the entire script. Fix: use double-quoted font names (`"SF Mono"`) in the CSS value so they don't interfere with the JS string delimiter.

---

## 4.6.75 — Fix: no-tool safety check false positives with file context

### Bug fix
- **Safety check blocked card/code generation replies** — when a file was open in the file panel, the `[FILE:...]` block in the user message contained YAML keywords (`enable`, `disable`, `open`, `close`) that triggered `_ACTION_REQUEST_RE`, causing the no-tool provider safety check to wrongly replace valid code-generation responses with the "action not executed" warning. Fix: strip `[FILE:...]` blocks before evaluating `_user_asked_action`.
- **Code-block responses never blocked** — added `not _assembled_has_code` to the safety check condition: a response containing a ` ``` ` code block is always code generation, never a hallucinated action confirmation.

---

## 4.6.74 — Fix: skip entity keyword search on file context content

### Bug fix
- **Spurious entity searches when a file is open** — when the file panel injected `[FILE: ...]...[/FILE]` blocks into the user message, the smart context keyword extractor scanned every word in the YAML/JSON file as a potential entity keyword, triggering dozens of useless HA entity searches. Fix: strip `[FILE:...]` blocks from the message before keyword extraction, the same way `[CURRENT_DASHBOARD_HTML]` blocks are already stripped.

---

## 4.6.73 — File panel: anti-truncation guard on save

### Bug fix
- **Write truncation guard** — `POST /api/files/write` now rejects writes where the new content is less than 60% of the original file size (files > 200 B), returning a `truncation_warning` error with original/new sizes. Pass `force: true` to override.
- **Edit mode loads full file** — clicking Edit when a file is only partially loaded (chunked) now fetches the complete content before opening the textarea, preventing partial overwrites on save.
- **Truncation confirm dialog** — if the server returns a truncation warning, the UI shows a confirm dialog with the size difference before allowing a forced save.

---

## 4.6.72 — File panel: line numbers, inline editing and save

### New features
- **Line numbers in file viewer** — each line shows its number on the left, non-selectable, in code-editor style.
- **Edit button** — opens an inline textarea with the full file content; Tab key inserts 2 spaces.
- **Save button** — sends the updated content via `POST /api/files/write` and refreshes the view; Cancel restores the read-only view without saving.
- **New `POST /api/files/write` endpoint** — writes a file in the HA config dir (existing files only, relative paths).

---

## 4.6.71 — Fix sync lista modelli al cambio provider nel sidebar automazioni

### Bug fix
- **Sidebar automazioni: lista modelli non aggiornata al cambio provider** — quando si cambiava provider nel sidebar, il selettore modelli continuava a mostrare i modelli del provider precedente finché non si ricaricava la pagina. Fix: `MutationObserver` sul selettore modelli principale che sincronizza automaticamente le opzioni nel sidebar ogni volta che vengono aggiornate.

---

## 4.6.70 — Fix stili code block e diff nel sidebar automazioni

### Bug fix
- **Sidebar automazioni: code block e diff senza stili** — il sidebar Amira nell'editor automazioni è inserito dentro lo shadow DOM di `hass-subpage`, quindi i CSS globali (in `document.head`) non erano applicati. Code block apparivano senza background scuro/box, e il diff prima/dopo non mostrava i colori rosso/verde. Fix: iniettare un `<style>` direttamente nello shadow root al momento dell'apertura del sidebar.

---

## 4.6.69 — Skill slash-autocomplete in chat_ui, bubble e card panel

### Nuova funzionalità
- **Tendina autocomplete skill con `/`**: digitare `/` in qualsiasi campo di chat mostra una tendina con le skill installate. Filtra in tempo reale (es. `/mu` → mushroom). Click o Enter/Tab (con item selezionato) inserisce `/nome-skill `.
- Navigazione da tastiera: `↑`/`↓` per selezionare, `Enter`/`Tab` per confermare, `Escape` per chiudere.
- Disponibile in: chat_ui principale, bubble Amira (main), card panel della bubble.

---

## 4.6.68 — Card panel: status progressivo + fix safety warning su card_editor

### Bug fix
- **Card panel: messaggi di status progressivi** — durante l'elaborazione, il panel card ora mostra gli step accumulati (⏳ messaggio corrente + • step precedenti) invece di sovrascrivere con solo l'ultimo messaggio "Contesto precaricato…". Allineato al comportamento della chat_ui principale.
- **Fix falso safety warning su `card_editor`** — l'intent `card_editor` era erroneamente soggetto al safety check "no-tool provider", che sostituiva la risposta corretta (suggerimenti YAML) con il warning ⚠️ nella storia della conversazione. Aggiunto `card_editor` agli intent esclusi (come `chat` e `create_html_dashboard`), dato che per questo intent il testo è la risposta attesa.

---

## 4.6.48 — Skill YAML auto-repair for weak-format outputs (e.g. NVIDIA)

### Bug fix
- **One-shot skill YAML repair retry**: when a skill is active and the model returns missing/malformed card YAML (or wrong card type), Amira now performs one automatic repair round instead of returning broken output.
- Validation checks include:
  - presence of a fenced ` ```yaml ... ``` ` block,
  - YAML parse validity,
  - skill-specific card type constraints (`custom:mushroom-*` for mushroom, exact `custom:html-js-card` for html-js-card).
- This improves reliability with weaker formatting models (notably some NVIDIA models) that may merge lines or ignore fence/type constraints.

---

## 4.6.47 — No-tool auto-continue on truncated outputs (`max_tokens`/`length`)

### Bug fix
- **No-tool providers now auto-continue once when output is truncated**: if a response ends with `finish_reason=max_tokens` (or `length`) and no tool calls are pending, Amira runs one internal continuation round instead of stopping mid-answer.
- This is especially useful for long YAML/code responses in `gemini_web` fallback flows (e.g. switching to official Google API), where outputs could stop at `content: |` or mid-code-block.
- Continuation policy:
  - continue exactly from the last line,
  - do not repeat previous text,
  - close open YAML/code fences if needed.

---

## 4.6.46 — Language consistency hardening + Gemini Web stream dedup + html-js-card skill safety

### Bug fixes
- **Per-request language override now patches all language snippets in prompts** (not only `strict_language_lock`): `respond_instruction`, YAML/entity/delete guidance, and create-vs-example rules are now consistently switched to the request language (`api.py`).
- **Removed Italian hardcoded runtime fallbacks** in key paths:
  - `perplexity_web`: request locale now follows configured language (`en/it/es/fr`) and empty-input fallback greeting is localized.
  - `chat_bubble`: last-triggered timestamp formatting now uses UI language locale instead of fixed `it-IT`.
  - `voice_transcription`: STT/TTS language defaults now follow configured language (Groq/OpenAI/Google STT + Google TTS).
- **Gemini Web duplicate answer fix**: SDK streaming now handles cumulative chunks correctly (append only new suffix, ignore replayed chunks), preventing duplicated full responses in chat.
- **html-js-card skill safety rules tightened**:
  - Added mandatory selector-to-markup consistency rule (`id` used in JS must exist in generated HTML/SVG).
  - Added null-safe DOM operation guidance for `classList/style/getContext/textContent`.
  - Added explicit broken-case example (`#line-home` missing) and corrected pattern.
  - Fixed skill examples to use valid JavaScript (removed invalid assignment patterns).

---

## 4.6.45 — Skill mode: skip tool simulator in all web providers

### Improvement
- All web providers (`chatgpt_web`, `gemini_web`, `grok_web`, `perplexity_web`) now skip the tool simulator system prompt when a skill is active — same fix applied in 4.6.44 for `claude_web`. Only SKILL.md instructions are sent, reducing token waste and removing conflicting context.

---

## 4.6.44 — Skill mode: skip tool schemas to save tokens

### Improvement
- When a skill is active (e.g. `/html-js-card`), all HA tool schemas are cleared (`tool_schemas = []`) before sending to any provider — the model only needs to generate content (YAML, HTML), not control devices.
- `claude_web` provider: also skips the tool simulator system prompt entirely in skill mode — further reducing token usage and removing conflicting context.

---

## 4.6.43 — Fix: skill card type ignored when using claude_web provider

### Bug fix
- **`claude_web` + skill**: the SKILL.md rules were buried under the tool simulator in the system prompt, causing the model to use its training-data defaults (`button-card`, `mushroom-*`, `power-flow-card-plus`) instead of `custom:html-js-card`. Fix: when a skill is active, a short, direct reminder is appended to the **user message itself** (highest attention position) immediately before generation — `[⚠️ SKILL ACTIVE: html-js-card — ONLY output type: custom:html-js-card — NEVER use button-card...]`.
- `api.py`: sets `intent_info["active_skill"]` when injecting a skill so providers can read it.

---

## 4.6.42 — Fix: claude_web strips YAML code fences in skill mode

### Bug fix
- **`claude_web` provider**: anti-artifact rule #2 forbade ALL markdown code blocks, causing Lovelace card YAML to be output as plain text (no copy button, no syntax highlight). Added explicit exception: Lovelace card YAML (`type: custom:html-js-card`, etc.) MUST use ` ```yaml ``` ` fences. Automation/script YAML still routed through `preview_automation_change` tool.

---

## 4.6.41 — Skill active banner in chat

### New feature
- **Skill mode banner**: when a skill is active (e.g. `/html-js-card`), a purple banner appears at the top of the chat showing "🧩 Skill: html-js-card" with a hint to open a new chat to change topic, and a "New chat" button
- Banner is shown on skill activation and on every follow-up message where the skill is re-injected
- Banner disappears automatically on new chat

---

## 4.6.40 — Skill context persists for follow-up messages in a session

### New feature
- **Active skill re-injected on follow-up messages**: when a skill is activated via `/html-js-card` (or any skill command), the skill's SKILL.md instructions are automatically re-injected for every subsequent message in the same session — so the AI keeps following the skill rules (e.g. use `scripts:` not `<script src>`) even when the user replies with "si", "add a chart", etc. without repeating the slash command
- Skill session is cleared on new chat / global reset

---

## 4.6.39 — Remove entity picker UI from chat

### UX
- **Removed entity picker**: the sensor/entity buttons + free-text field + "Select" button that appeared below AI messages are no longer shown — they were triggering incorrectly after YAML card responses

---

## 4.6.38 — Bubble: fix YAML as bullet points + fix language forcing Italian on all users

### Bug fixes
- **YAML no longer rendered as bullet points in the bubble**: code blocks are now extracted into placeholders *before* the list regex runs, so `- sensor.temperature` lines inside `content: |` YAML blocks are no longer converted to bullet points
- **Bubble no longer forces Italian on non-Italian users**: the bubble now sends `language: UI_LANG` with every chat request; the server applies a per-request language lock (thread-safe, no global change) so each user gets responses in their own UI language regardless of the server's global language setting

---

## 4.6.37 — Fix backtick template literals stripped from code blocks in chat + html-js-card skill 1.3.0

### Bug fixes
- **Backtick template literals preserved in code blocks**: the inline-code regex (`` `text` `` → `<code>`) was running after code block extraction, hitting JS template literals like `` `${fmt(x, 0)}` `` inside YAML/JS code and stripping the backticks — causing `unexpected token: '{'` errors when the user pasted the copied code. Code blocks are now extracted into placeholders first, so inline processing never touches their content.

### Skill update: html-js-card 1.3.0
- **Fixed `document.getElementById` → `card.querySelector('#id')`**: the card uses shadow DOM, so `document.getElementById` always returns null; all examples and rules updated to use `card.querySelector`
- Added rule 11 and dedicated NEVER section for this mistake

### Bug fixes
- **Backtick template literals preserved in code blocks**: the inline-code regex (`` `text` `` → `<code>`) was running after code block extraction, hitting JS template literals like `` `${fmt(x, 0)}` `` inside YAML/JS code and stripping the backticks — causing `unexpected token: '{'` errors when the user pasted the copied code. Code blocks are now extracted into placeholders first, so inline processing never touches their content.

---

## 4.6.36 — Fix HTML tags stripped from YAML code blocks in chat

### Bug fixes
- **HTML tags no longer stripped from code blocks**: content inside ` ```yaml ``` ` or any fenced code block is now HTML-escaped before insertion into the DOM, so tags like `<style>`, `<div>`, `<script>` inside a `content: |` block are displayed as plain text instead of being interpreted and removed by the browser

---

## 4.6.35 — Skills store: hide already-installed skills

### Bug fixes / UX
- **Store no longer shows already-installed skills**: installed skills without available updates are removed from the store list to avoid duplication; they only reappear in the store if an update is available (with the "⬆ Update" button)
- If all store skills are already installed and up to date, the store shows "No new skills available"

---

## 4.6.34 — Skills update detection + notification banner

### New features
- **Skill update detection**: 3 seconds after page load, the chat compares installed skill versions against the GitHub store and shows a yellow banner at the top if updates are available
- **Dismissible banner**: lists skills to update with current → new version; "Go to Skills" button opens the panel directly; "✕" to dismiss
- **"Update" button in store**: installed skills with a lower version than the store show an orange "⬆ Update" button instead of the green "Installed" badge; the card border turns yellow to highlight them
- **Full i18n**: banner and update button translated in IT/EN/ES/FR

---

## 4.6.33 — Raise skill size limit to 60 KB

### Bug fixes
- **Fixed "Skill content too large"**: raised `_MAX_BODY_CHARS` from 8000 to 60000 — the SAK skill is ~46 KB and HTML-JS Card ~9 KB, both exceeded the old limit

---

## 4.6.32 — Fix skills.py missing from Dockerfile

### Bug fixes
- **Fixed `skills.py` not copied into Docker image**: `COPY skills.py .` was missing from Dockerfile, causing `No module named 'skills'` and "Skills not available" even after rebuild

---

## 4.6.31 — Fix Skills store button crash + sys.path import fix

### Bug fixes
- **Fixed `SyntaxError: missing } in template string`** in Skills store panel: the Install button used `onclick='...'` with string concatenation that broke JS single-quoted strings; replaced with `data-name`/`data-url` attributes + `querySelectorAll` event listeners
- **Fixed `No module named 'skills'`**: `skills_routes.py` now explicitly adds the app root to `sys.path` and imports `skills` at module load time with a try/except; if unavailable, endpoints return `skills_unavailable` instead of a generic error
- **Improved error messages**: Skills panel now shows "Skills not available. Please restart the add-on." instead of a false "internet connection" error when the module is missing; actual error detail shown below network errors for easier debugging

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
