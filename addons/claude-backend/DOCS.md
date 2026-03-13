# Amira Documentation

## Overview

**Amira** is an AI-powered smart home assistant add-on for Home Assistant. It provides a web-based chat interface with multi-provider AI support (40+ models), real-time cost tracking, multi-agent system, HTML custom dashboard generation, MCP tool integration, Telegram & WhatsApp messaging, file access, voice input, and more.

No long-lived tokens required — Amira integrates directly with Home Assistant's Supervisor API.

---

## Quick Start

1. **Add repository**: Settings → Add-ons → Add-on Store → ⋮ → Repositories → add `https://github.com/Bobsilvio/ha-claude`
2. **Install**: Search "Amira" → Install
3. **Add API key**: Add-on Configuration tab → add at least one provider key → Save
4. **Start** the add-on
5. **Open Amira** from the HA sidebar and start chatting

---

## Configuration: two layers

Amira uses **two layers** of configuration. Most features are now managed directly from the chat UI — you rarely need to touch the add-on config tab.

### Layer 1 — Add-on Configuration tab (API keys only)

| Setting | Description |
|---------|-------------|
| `anthropic_api_key` | Anthropic Claude API key |
| `openai_api_key` | OpenAI API key |
| `google_api_key` | Google Gemini API key |
| `github_token` | GitHub PAT (GitHub Models + GitHub Copilot OAuth) |
| `nvidia_api_key` | NVIDIA NIM API key |
| `groq_api_key` | Groq API key |
| `mistral_api_key` | Mistral API key |
| `openrouter_api_key` | OpenRouter API key |
| `deepseek_api_key` | DeepSeek API key |
| `perplexity_api_key` | Perplexity API key |
| `minimax_api_key` | MiniMax API key |
| `aihubmix_api_key` | AiHubMix API key |
| `siliconflow_api_key` | SiliconFlow API key |
| `volcengine_api_key` | VolcEngine API key |
| `dashscope_api_key` | DashScope (Alibaba Qwen) API key |
| `moonshot_api_key` | Moonshot (Kimi) API key |
| `zhipu_api_key` | Zhipu GLM API key |
| `custom_api_key` + `custom_api_base` + `custom_model_name` | Any OpenAI-compatible endpoint |
| `ollama_base_url` | Ollama server URL (default: `http://localhost:11434`) |
| `colored_logs` | Pretty-print add-on logs |
| `debug_mode` / `log_level` | `normal` / `verbose` / `debug` |

### Layer 2 — Settings UI (⚙️ icon in chat)

All runtime features are configured from the chat interface. No restart needed for most changes.

| Setting | Default | Description |
|---------|---------|-------------|
| **language** | `en` | UI language: English, Italian, Spanish, French |
| **enable_file_access** | OFF | Read/write `/config` files with automatic snapshots |
| **enable_file_upload** | ON | Upload documents (PDF, DOCX, TXT, MD, YAML) for AI analysis |
| **enable_memory** | OFF | Persistent AI memory across sessions (MEMORY.md) |
| **enable_rag** | OFF | RAG semantic search over uploaded documents |
| **enable_chat_bubble** | ON | Floating AI button on every HA page |
| **enable_amira_card_button** | ON | 🤖 Amira button in the Lovelace card editor |
| **enable_voice_input** | ON | Voice input in chat bubble |
| **enable_mcp** | OFF | MCP tool server integration |
| **fallback_enabled** | OFF | Auto fallback to next provider on error |
| **tts_voice** | `female` | TTS voice gender |
| **anthropic_extended_thinking** | OFF | Extended thinking for Claude models |
| **anthropic_prompt_caching** | OFF | Prompt caching for Claude (reduces cost on repeated context) |
| **openai_extended_thinking** | OFF | Extended thinking for OpenAI o-series |
| **nvidia_thinking_mode** | OFF | Extra reasoning tokens on NVIDIA models |
| **timeout** | `30` | API request timeout in seconds |
| **max_retries** | `3` | Retry failed requests |
| **max_conversations** | `10` | Chat history depth (1–100) |
| **max_snapshots_per_file** | `5` | Max backups per config file |
| **cost_currency** | `USD` | Cost display: USD or EUR |
| **mcp_config_file** | `/config/amira/mcp_config.json` | MCP servers config path |

Settings are stored in `/config/amira/settings.json` and persist across restarts.

---

## Features

### Chat & AI

- **Streaming chat UI** with real-time responses
- **40+ AI models** from 12+ providers — switch without restarting
- **Persistent model selection** — your chosen model is restored after restart
- **Multi-language UI** — English, Italian, Spanish, French
- **Voice input** — speak instead of type (in chat bubble)
- **File upload** — PDF, DOCX, TXT, MD, YAML injected into AI context
- **Image/vision** — send screenshots or photos to vision-capable models
- **Conversation history** — multiple named chats, persistent across sessions

### Home Assistant Integration

Ask Amira in natural language:
- *"Turn on the living room lights at 50% brightness"*
- *"Create an automation that turns off all lights at midnight"*
- *"What's the current temperature in the bedroom?"*
- *"Show me the energy usage for today"*
- *"Create a dashboard for my solar panels"*

Amira can read device states, call services, create/edit automations and scripts, manage helpers, and more — all without you ever touching YAML.

### HTML Custom Dashboards

Amira can generate fully custom HTML dashboards saved to `/config/www/dashboards/` and accessible directly from the HA sidebar.

Ask:
- *"Create a dashboard for my solar panels with charts"*
- *"Make a battery monitoring dashboard"*
- *"Build a lights control panel for my home"*

Each generated dashboard:
- Connects to HA in real-time via WebSocket + REST API with automatic authentication
- Auto-refreshes entity states
- Includes domain-appropriate chart types (bar, line/area, donut, gauge, scatter, radar, stacked)
- Uses a professional color palette matched to the domain (solar = amber/green, climate = cyan, security = red, etc.)
- Supports click-to-expand cards that open the HA native more-info panel
- Works on mobile and desktop

Dashboards are saved at `/config/www/dashboards/<name>.html` and added to the HA sidebar automatically. You can also ask Amira to modify or delete any existing dashboard.

### Multi-Agent System

Define multiple AI agents with different models, tools, and personalities. Switch between them from the chat UI.

**Configuration**: create `/config/amira/agents.json` (or use the Settings UI → Agents):

```json
{
  "home": {
    "identity": { "name": "Amira", "emoji": "🏠", "description": "Home automation expert" },
    "model": "anthropic/claude-sonnet-4-6",
    "fallback": ["google/gemini-2.0-flash", "groq/llama-3.3-70b-versatile"],
    "tools": null,
    "is_default": true
  },
  "coder": {
    "identity": { "name": "CodeBot", "emoji": "💻", "description": "Coding & config specialist" },
    "model": "anthropic/claude-opus-4-6",
    "fallback": ["openai/gpt-4o"],
    "tools": ["read_config_file", "write_config_file"],
    "system_prompt_override": "You are a coding expert. Always show code with comments.",
    "temperature": 0.2
  },
  "quick": {
    "identity": { "name": "Flash", "emoji": "⚡", "description": "Fast answers, no tools" },
    "model": "groq/llama-3.3-70b-versatile",
    "fallback": ["google/gemini-2.0-flash"],
    "tools": [],
    "temperature": 0.7
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | `provider/model` (e.g. `anthropic/claude-sonnet-4-6`) |
| `fallback` | string[] | Ordered fallback models if primary fails |
| `tools` | string[] \| null | Allowed tool names. `null` = all, `[]` = none |
| `tools_blocked` | string[] | Explicitly blocked tools |
| `system_prompt_override` | string | Replaces default system prompt |
| `temperature` | number | 0.0–2.0 |
| `thinking_level` | string | `off`, `low`, `medium`, `high`, `adaptive` |
| `is_default` | bool | Pre-selected on load |
| `enabled` | bool | Hide without deleting |

### MCP Tools

Connect external tool servers to extend Amira's capabilities (databases, APIs, file systems, etc.).

1. Enable MCP in **Settings → Features → MCP**
2. Open **Settings → MCP Config** in the chat UI
3. Add servers (saved to `/config/amira/mcp_config.json`):

```json
{
  "my_server": {
    "transport": "http",
    "url": "http://192.168.1.x:7660"
  }
}
```

4. Start servers from **Settings → MCP** — each server shows a live status badge (green = running, grey = stopped)
5. Servers you start manually are remembered and auto-restarted on add-on reboot

### Persistent Memory

When enabled (Settings → Features → Memory), Amira remembers facts across sessions:

- **`/config/amira/memory/MEMORY.md`** — injected in every session (write here what Amira should always know)
- **`/config/amira/memory/HISTORY.md`** — append-only session log

Edit directly via SSH:
```bash
nano /config/amira/memory/MEMORY.md
```

### Telegram & WhatsApp

- **Telegram**: long-polling bot — no public IP required. Configure bot token in Settings UI.
- **WhatsApp**: Twilio integration with webhook on port 5010. Configure in Settings UI.

### Cost Tracking

Every AI response shows:
- Token count (input / output / cache read / cache write)
- Dollar cost with breakdown tooltip
- Running session total

Usage is aggregated by day, model, and provider in `/data/usage_stats.json`. Access via API or reset from Settings UI.

---

## AI Providers

| Provider | Models | Cost | Notes |
|----------|--------|------|-------|
| **Anthropic** | Claude Opus/Sonnet/Haiku 4.x | $3–$15/1M tok | Best for complex reasoning, long context |
| **OpenAI** | GPT-4o, o3, o4-mini | $5–$20/1M tok | Balanced performance |
| **Google Gemini** | Gemini 2.0 Flash, 2.5 Pro | Free tier / $7.50/1M | Fast, free tier (1500 req/day) |
| **NVIDIA NIM** | Llama 3.1 405B/70B, Mistral, Mixtral, Kimi | Free (rate-limited) | Open-source models |
| **GitHub Models** | GPT-4o, o1, Llama, Phi | Free for GitHub users | Experimental models |
| **GitHub Copilot** | GPT-4o, Claude 3.7, Gemini 2.0 | Copilot subscription | OAuth flow — no extra API key |
| **OpenAI Codex** | gpt-5.x-codex series | ChatGPT Plus/Pro subscription | OAuth flow — no extra API key |
| **Groq** | Llama 3.1, Mixtral | Free tier | Fastest inference |
| **Mistral** | Mistral Large/Medium/Small | $2–$8/1M tok | European provider |
| **DeepSeek** | DeepSeek Chat, Reasoner | $0.14–$0.55/1M tok | Very cost-efficient |
| **OpenRouter** | 100+ models | Varies | One key for all providers |
| **Perplexity** | Sonar models | Pay per use | Real-time web search |
| **Ollama** | Any local model | Free | Privacy, offline, your hardware |
| **MiniMax** | MiniMax models | Pay per use | Long context |
| **AiHubMix** | Many models | Pay per use | Aggregator |
| **SiliconFlow** | Fast inference | Pay per use | Chinese provider |
| **VolcEngine** | ByteDance AI | Pay per use | Chinese provider |
| **DashScope** | Alibaba Qwen | Pay per use | Qwen series |
| **Moonshot** | Kimi models | Pay per use | Long context |
| **Zhipu** | GLM models | Pay per use | Chinese provider |
| **Custom** | Any OpenAI-compatible | — | Set `custom_api_base` + key |

> **Already paying for ChatGPT Plus/Pro?** Use the **OpenAI Codex** provider — it's included in your subscription at no extra cost, no separate API key needed.

> **GitHub Copilot subscriber?** Use the **GitHub Copilot** provider the same way.

---

## Data Storage

All persistent data lives in `/config/amira/`:

```
/config/amira/
├── settings.json              # All runtime settings (managed via Settings UI)
├── conversations.json         # Chat history
├── runtime_selection.json     # Last selected model/provider
├── agents.json                # Multi-agent config
├── mcp_config.json            # MCP servers config
├── mcp_runtime.json           # MCP autostart state (servers started manually)
├── custom_system_prompt.txt   # Custom system prompt override
├── scheduled_tasks.json       # Scheduled task definitions
├── snapshots/                 # Config file backups (before edits)
├── documents/                 # Uploaded files
├── rag/                       # RAG document index
└── memory/
    ├── MEMORY.md              # Long-term facts (always in context)
    └── HISTORY.md             # Session log (append-only)

/config/www/
├── ha-claude-chat-bubble.js   # Floating chat bubble script (auto-generated)
└── dashboards/                # Custom HTML dashboards (auto-generated)
    └── <name>.html

/data/
└── usage_stats.json           # Cost/usage tracking (daily, per-model, per-provider)
```

---

## REST API

The add-on exposes a REST API on port 5010 (also via HA Ingress).

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/stream` | POST | Streaming chat (SSE) |
| `/api/models` | GET | List available providers and models |
| `/api/set_model` | POST | Change active provider/model |
| `/api/status` | GET | System status, features, version |
| `/api/settings` | GET/POST | Get or save runtime settings |
| `/api/conversations` | GET | List all conversations |
| `/api/agents` | GET/POST | List or create agents |
| `/api/agents/<id>` | PUT/DELETE | Update or delete an agent |
| `/api/agents/set` | POST | Switch active agent |
| `/api/snapshots` | GET | List config file backups |
| `/api/documents/upload` | POST | Upload document for analysis |
| `/api/mcp/servers` | GET | List MCP servers and status |
| `/api/mcp/server/<name>/start` | POST | Start a MCP server |
| `/api/mcp/server/<name>/stop` | POST | Stop a MCP server |
| `/api/messaging/stats` | GET | Telegram & WhatsApp statistics |
| `/api/usage_stats` | GET | Usage summary |
| `/api/usage_stats/today` | GET | Today's token and cost totals |
| `/api/usage_stats/reset` | POST | Reset all usage data |
| `/api/addon/restart` | POST | Restart the add-on |
| `/api/transcribe` | POST | Transcribe audio (Whisper) |
| `/api/tts` | POST | Text-to-speech |
| `/health` | GET | Health check |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Chat UI doesn't load | Restart add-on, hard-refresh browser (Ctrl+F5) |
| 401 API error | Check API key format and account balance |
| 429 Rate limit | Wait or upgrade plan with provider |
| Dashboard shows blank page | Check browser console; the model may have generated malformed HTML — try with Claude or GPT-4o |
| Dashboard shows 0 values | Auth issue — the add-on auto-patches generated dashboards; rebuild if needed |
| File access not working | Enable in Settings → Features → File Access, restart |
| Memory not saving | Enable in Settings → Features → Memory; check `/config/amira/memory/` is writable |
| MCP not loading | Enable in Settings → Features → MCP; validate JSON; check logs |
| Module import errors | Restart the add-on (dependencies install on first start) |
| Bubble not appearing | Enable in Settings → Features → Chat Bubble; hard-refresh HA |

---

## Security

- **API keys** stored in HA configuration, never exposed to the UI
- **File access** restricted to `/config` directory only
- **Dashboard auth** — generated HTML dashboards use an automatic auth patch to connect securely to the HA API without exposing tokens
- **Ingress** — all traffic via HA Ingress by default (no direct internet exposure)
- **MCP config** — never commit `/config/amira/mcp_config.json` to git if it contains API keys

---

## Support

- **Issues**: [github.com/Bobsilvio/ha-claude/issues](https://github.com/Bobsilvio/ha-claude/issues)
- **Discussions**: [github.com/Bobsilvio/ha-claude/discussions](https://github.com/Bobsilvio/ha-claude/discussions)
- **Repository**: [github.com/Bobsilvio/ha-claude](https://github.com/Bobsilvio/ha-claude)
