# Changelog

## 3.3.10-dev
- Fix global scope for toggleVoiceRecording, handleDocumentSelect, changeModel functions
- Export functions to window object so onclick handlers can access them
- Voice recording button should now work
- Stable: debug_mode shows debug info in responses, log_level=debug shows all internal logs

## 3.3.9-dev
- Add error handling to stream endpoint to catch and log actual exceptions
- Stream errors now show in logs instead of silently failing in waitress
- Debug mode improvements for troubleshooting chat issues

## 3.3.8-dev
- Fix feature flags mapping: use run script to read from addon config (like other options)
- Add ENABLE_VOICE, ENABLE_MEMORY, ENABLE_FILE_UPLOAD, ENABLE_RAG to run script
- Add detailed descriptions for feature flag options in config.yaml
- Now works exactly like enable_file_access and other standard addon options

## 3.3.7-dev
- Fix feature flags reading from Home Assistant addon config
- Read enable_voice, enable_memory, enable_file_upload, enable_rag from /root/options.json
- These settings now take effect immediately (no env var templating needed)
- Buttons and features should now work when enabled in addon config

## 3.3.6-dev
- Fix environment variable template syntax for feature flags
- Use Jinja2 templates in config.yaml for proper boolean to string conversion
- Buttons should now appear when you enable the features
- IMPORTANT: Restart addon after enabling features for env vars to load

## 3.3.5-dev
- Fix UI initialization error: remove missing ui_bootstrap.js and ui_main.js references
- JavaScript functions now load directly from inline HTML
- Buttons should now appear and be fully functional

## 3.3.4-dev
- Fix feature flags not passed to addon environment
- Map enable_file_upload, enable_voice, enable_memory, enable_rag to env vars
- Buttons now properly appear when features are enabled
- Important: Restart addon after enabling features for env vars to take effect

## 3.3.3-dev
- Add UI controls for file upload and voice recording in chat interface
- File upload button (📄) - import PDF, DOCX, TXT, MD documents to RAG
- Voice recording button (🎤) - record audio input for voice features
- Both buttons conditionally display based on feature enable flags

## 3.2.29-dev (develop branch)
- [EXPERIMENTAL] Add feature flags for upcoming features: enable_voice, enable_memory, enable_file_upload, enable_rag (all default OFF)
- [EXPERIMENTAL] **MEMORY SYSTEM**: Add persistent conversation memory that stores past conversations and injects relevant context into future chats. Includes:
  - Automatic saving of conversations to persistent storage
  - Semantic search in past conversations to find relevant context
  - Memory injection into system prompts for context-aware responses
  - API endpoints: GET /api/memory, GET /api/memory/search, GET /api/memory/stats, DELETE /api/memory/:id, POST /api/memory/cleanup
  - Configurable via `enable_memory` flag (default OFF for testing)
- [EXPERIMENTAL] **VOICE SYSTEM**: Add voice input/output with automatic backend detection:
  - Speech-to-Text (STT): SpeechRecognition (Google API, free), pocketsphinx (offline lightweight)
  - Text-to-Speech (TTS): pyttsx3 (offline), edge-tts (lightweight online), gTTS (online)
  - Auto-selects best available backend per system (prefers offline)
  - API endpoints: GET /api/voice/config, POST /api/voice/transcribe, POST /api/voice/speak
  - Configurable via `enable_voice` flag (default OFF for testing)
  - Optimized for Raspberry Pi and lightweight Home Assistant installations
- Development branch for testing new features without affecting stable v3.2.28 release

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
