# Changelog

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
