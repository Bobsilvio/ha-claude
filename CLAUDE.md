# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Amira** is a Home Assistant add-on providing multi-provider AI assistance with natural language device control, automation management, and chat UI. It runs as a Flask/Waitress service inside a Docker container managed by s6-overlay.

License: PolyForm Non-Commercial 1.0.0 (personal use only; commercial use requires written permission).

## Build & Run

### Docker (primary deployment path)
```bash
# Build the add-on image
docker build -t amira-backend ./addons/claude-backend

# The Dockerfile uses a multi-stage approach:
# Stage 1: core deps (always succeed)
# Stage 2: optional deps installed one-by-one with failure tolerance
```

### Local development
```bash
cd addons/claude-backend
pip install -r requirements_core.txt
pip install -r requirements_optional.txt  # partial installs OK
python server.py
```

### Tests
```bash
cd addons/claude-backend
python -m pytest tests/
# Run a single test file:
python -m pytest tests/test_registry.py
```

### Validate/build scripts
```bash
./addons/claude-backend/validate.sh
./addons/claude-backend/build.sh
```

## Architecture

### Entry Points
- `server.py` — WSGI entrypoint; starts the app or falls back to a diagnostic Flask server if imports fail
- `api.py` — main Flask application; registers all blueprints from `routes/`
- `rootfs/etc/s6-overlay/s6-rc.d/claude-backend/run` — Docker startup script (reads HA config via bashio, exports API keys, launches `python3 server.py`)

### Provider System (`providers/`)
- `base.py` defines `BaseProvider` with abstract methods: `validate_credentials()`, `stream_chat()`, `get_available_models()`
- All providers return a unified SSE event stream: `{"type": "status"|"content"|"tool_call"|"done"|"error", ...}`
- `manager_enhanced.py` orchestrates selection, fallback, and streaming
- Providers are lazy-loaded; optional providers degrade gracefully when their deps are missing
- Web session providers (`claude_web.py`, `chatgpt_web.py`, `gemini_web.py`) use browser session cookies rather than API keys

### Tool System
- `tool_registry.py` — registry of 50+ Home Assistant control tools with metadata
- `tools.py` — implementations (largest file; HA REST API calls)
- `intent.py` — LLM-first routing: all tools are sent to the LLM, which decides which to call; no keyword-based dispatch
- MCP external tools (`mcp.py`) extend the tool set via Model Context Protocol (HTTP or stdio servers)

### Route Structure (`routes/`)
22 Flask blueprints registered in `routes/__init__.py`. Key groupings:
- **Chat**: `chat_routes.py` — `/api/chat`, `/api/chat/stream`, `/api/chat/abort`
- **Agents**: `agents_routes.py` — CRUD + per-channel routing
- **Config**: `settings_routes.py`, `system_routes.py`
- **Messaging**: `messaging_routes.py`, Telegram/WhatsApp/Discord webhook routes
- **UI**: `ui_routes.py` (web chat), `bubble_routes.py` (floating HA bubble)
- **MCP**: `mcp_routes.py`

### Configuration Layers
1. `config.yaml` — HA add-on manifest; only API keys + logging level (set via HA UI)
2. `/config/amira/settings.json` — all runtime settings (set via ⚙️ Settings UI)
3. `/config/amira/agents.json` — multi-agent definitions (hot-reloaded, no restart needed)
4. `/config/amira/custom_system_prompt.txt` — optional prompt override

All persistent data lives under `/config/amira/` inside the container.

### Multi-Agent System
- `agent_config.py` loads/watches `agents.json`
- Each agent can override: model, provider fallback chain, tools, system prompt, temperature, thinking level
- Agents are assigned to messaging channels (Telegram/WhatsApp/Discord) independently

### Streaming
Flask `stream_with_context()` with Server-Sent Events. Responses are token-by-token from providers → forwarded to the client as `data: {...}\n\n` lines.

### Key Utilities
| Module | Purpose |
|--------|---------|
| `pricing.py` | Per-token cost calculation |
| `model_catalog.py` | Model metadata and capabilities |
| `model_fallback.py` | Fallback chain selection logic |
| `fallback.py` | Provider-level fallback execution |
| `core/error_utils.py` | Error message humanization |
| `core/translations.py` | EN/IT/ES/FR UI strings |
| `rag.py` | Semantic document search |
| `memory.py` | Persistent memory (`MEMORY.md` injected into prompts) |
| `prompt_caching.py` | Anthropic + OpenAI prompt caching |

### Optional Features
These are imported with `try/except` and silently disabled if deps are missing:
- RAG (`rag.py`) — requires sentence-transformers
- Voice (`voice_transcription.py`) — requires websocket-client
- Messaging bots — require python-telegram-bot / twilio / discord.py
- Web session providers — require curl_cffi / gemini_webapi

## Development Notes

- **Dependency split**: `requirements_core.txt` (always installed) vs `requirements_optional.txt` (best-effort). Never move optional-feature deps to core.
- **Adding a provider**: subclass `BaseProvider`, implement the three abstract methods, register in `providers/manager_enhanced.py`.
- **Adding a tool**: register in `tool_registry.py`, implement in `tools.py`, ensure the tool description fits in the compact format used in `intent.py`.
- **Adding a route**: create a blueprint in `routes/`, register it in `routes/__init__.py`.
- Version is tracked in `addons/claude-backend/config.yaml` (`version:` field) and should match `CHANGELOG.md`.

## Skills disponibili

Quando l'utente chiede di creare o modificare card Lovelace con le seguenti librerie, leggi il file SKILL.md corrispondente prima di rispondere:

| Libreria | SKILL.md |
|----------|----------|
| Swiss Army Knife Card (SAK) | `skills/swiss-army-knife-card/SKILL.md` |
| HTML-JS Card | `skills/html-js-card/SKILL.md` |
| Mushroom Cards | `skills/mushroom/SKILL.md` |

I file si trovano in `/Users/eleonor/italysat/ha-claude/skills/`.
