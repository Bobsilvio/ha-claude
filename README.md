<p align="center">
  <img src="image/amira-logo.png" width="48%">
</p>

<table align="center">
  <tr>
    <td align="center" width="260">
      <a href="https://ko-fi.com/silviosmart">
        <img src="https://storage.ko-fi.com/cdn/generated/zfskfgqnf/2025-03-07_rest-7d81acd901abf101cbdf54443c38f6f0-dlmmonph.jpg" width="220">
      </a>
    </td>
    <td align="left">
      <h2>☕ Support My Work</h2>
      <p>
        🇮🇹 Se ti piace il mio lavoro e vuoi che continui nello sviluppo delle card,
        puoi offrirmi un caffè.
      </p>
      <p>
        🇬🇧 If you like my work and want me to continue developing the cards,
        you can buy me a coffee.
      </p>
    </td>
  </tr>
</table>

<br>

<p align="center">
  <a href="https://www.paypal.com/donate/?hosted_button_id=Z6KY9V6BBZ4BN">
    <img src="https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white">
  </a>
</p>

### 🌍 Follow Me

<p align="center">
  <a href="https://www.tiktok.com/@silviosmartalexa">
    <img src="https://img.shields.io/badge/Follow-TikTok-000000?style=for-the-badge&logo=tiktok&logoColor=white">
  </a>
  &nbsp;
  <a href="https://www.instagram.com/silviosmartalexa">
    <img src="https://img.shields.io/badge/Follow-Instagram-E1306C?style=for-the-badge&logo=instagram&logoColor=white">
  </a>
  &nbsp;
  <a href="https://www.youtube.com/@silviosmartalexa">
    <img src="https://img.shields.io/badge/Subscribe-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white">
  </a>
</p>

---

### 🏠🤖 Amira Ai Assistant

**Smart home AI assistant addon** with multi-provider support — control your home, create automations, and manage configurations using natural language.

Supports **23+ AI providers** and **60+ models**: Anthropic Claude, OpenAI, Google Gemini, NVIDIA NIM, GitHub Models, GitHub Copilot (OAuth), OpenAI Codex (OAuth), Claude Web, Gemini Web, Groq, Mistral, DeepSeek, Ollama and more. Chat via **Telegram** or **WhatsApp** in addition to the built-in web UI.

[![GitHub Release](https://img.shields.io/github/v/release/Bobsilvio/ha-claude)](https://github.com/Bobsilvio/ha-claude/releases)
[![License: PolyForm NC](https://img.shields.io/badge/License-PolyForm%20NC%201.0-blue)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io/)

---

## ✨ Key Features

### 🎯 Smart Home Control
- **Natural Language**: Control devices using conversational commands
- **Device Query**: Ask about states, history, and statistics
- **Service Calls**: Execute any Home Assistant service
- **Areas & Rooms**: Manage spaces and assign entities

### 🤖 Automation Management
- **Create Automations**: Build complex automations with triggers, conditions, and actions
- **Modify Existing**: Update automations with natural language instructions
- **YAML Diff View**: See exactly what changed with before/after comparison
- **Smart Suggestions**: AI understands your devices and suggests improvements

### 🔧 System Diagnostics & Repairs
- **Read Repairs**: View active HA repair issues and warnings
- **Health Check**: System health diagnostics (unsupported/unhealthy components)
- **AI Suggestions**: AI analyzes issues and suggests concrete fixes
- **Dismiss Issues**: Acknowledge and dismiss resolved repairs

### � File Upload
- **Multi-Format**: Upload PDF, DOCX, TXT, MD, YAML for AI analysis
- **Drag & Drop**: Drop files directly into chat (ON by default)
- **Context Injection**: Uploaded content is included in the AI conversation

### 👁️ Vision Support
- **Image Upload**: Send screenshots, photos, or dashboard images
- **Visual Analysis**: AI can see and understand images
- **Card Recreation**: "Create cards like this image" — AI analyzes and recreates layouts
- **Multi-Provider**: Works with Claude, GPT-4o, Gemini vision models

### 🔍 RAG (Retrieval-Augmented Generation)
- **Semantic Search**: Search over uploaded documents with vector embeddings
- **Automatic Indexing**: Documents are indexed on upload
- **Enable in Settings**: Settings → Features → RAG (OFF by default)

### 📝 Configuration File Access
- **Read/Write YAML**: Access automations, scripts, scenes, and custom configs
- **File Explorer**: Browse your Home Assistant config directory
- **Safe Editing**: Automatic snapshots before modifications
- **Config Validation**: Check configuration before applying changes

### 🧠 Memory
- **Persistent Knowledge**: `MEMORY.md` injected in every conversation — the AI always remembers
- **Session Log**: `HISTORY.md` append-only log of past sessions
- **Enable in Settings**: Settings → Features → Memory (OFF by default)
- **Storage**: `/config/amira/memory/`

### 💬 Interactive Chat Interface
- **Chat History**: Keep last N conversations, switch between them
- **Streaming Responses**: Real-time token-by-token output
- **Tool Indicators**: See what the AI is doing (badges for each tool call)
- **Copy Button**: One-click copy for all code blocks (YAML, JSON, Python)

### 🫧 Floating Chat Bubble
- **Always Available**: AI chat bubble on every Home Assistant page (ON by default)
- **Amira Card Editor Button**: 🤖 Amira button in the Lovelace card editor for inline AI help
- **Independent Toggles**: Bubble and card button can be enabled/disabled separately
- **Context-Aware**: Detects automations, scripts, and HTML dashboards
- **HTML Dashboard Editing**: Modify dashboards in-place keeping same style
- **Voice Input**: Built-in voice recognition with multi-provider TTS
- **Agent Switching**: Change AI provider/model on the fly
- **Tool Feedback**: Thinking indicator + step badges during multi-tool execution

### 🔄 Provider Fallback
- **Automatic Chain**: If primary provider fails, Amira tries the next one
- **Configurable Order**: Set your preferred fallback sequence
- **Enable in Settings**: Settings → Features → Auto Fallback (OFF by default)

### 🤖 Multi-Agent System
- **Custom Agents**: Create agents with their own model, provider, tools, and custom instructions
- **Agent Switching**: Select agents from the chat UI dropdown
- **Channel Routing**: Assign different agents to Telegram/WhatsApp channels
- **Instructions field**: Add personality/context prepended to the HA default prompt — the agent keeps full HA awareness

### 💰 Cost Tracking
- **Per-Message Cost**: Tracks token usage and cost for every message
- **Cache Breakdown**: Shows prompt caching savings
- **Daily Aggregates**: Usage statistics over time
- **Multi-Currency**: USD or EUR

### 🌍 Multilingual Support
- **4 Languages**: English, Italian, Spanish, French
- **AI Responses**: AI always responds in your chosen language
- **Config UI Translations**: Settings labels and descriptions in all 4 languages

### 🔌 MCP (Model Context Protocol)
- **Custom Tools**: Connect external services via MCP servers
- **Filesystem, Web Search, Git, Databases**: and any custom MCP-compatible server
- **Multi-server**: Run multiple MCP servers simultaneously
- **Start/Stop from UI**: Each server shows a live status badge — start and stop directly from Settings → MCP
- **Auto-restart**: Servers you start manually are remembered and restarted on add-on reboot

### 📱 Messaging Integration
- **Telegram Bot**: Long polling — no public IP needed, works out of the box
- **WhatsApp**: Twilio integration with webhook support
- **Context Aware**: Full conversation history per user per channel
- **Enable/Disable**: Toggle Telegram and WhatsApp independently from **Settings → Messaging** in the chat UI

### ⏰ Scheduled Tasks
- **Cron-based**: Schedule automations using cron expressions
- **Background Execution**: Tasks run independently without user interaction
- **History Tracking**: Log of past executions with error reporting

### 🛠️ Dashboard Creation
- **Lovelace Dashboards**: Create custom dashboards with cards
- **HTML Dashboards**: AI-generated interactive dashboards saved to `/config/www/dashboards/` and auto-added to the HA sidebar
- **Domain-aware design**: color palettes and chart types chosen per domain (solar, batteries, lights, climate, security, water…)
- **8 chart types**: bar, line/area, doughnut/pie, gauge, scatter, radar, mixed, stacked bar
- **Live Data**: WebSocket + REST real-time updates with automatic HA authentication

---

## 📋 Requirements

- **Home Assistant** 2024.1.0+ with Supervisor
- **API Key** for at least one AI provider

---

## 🚀 Quick Start

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FBobsilvio%2Fha-claude)

1. **Add repository** — Settings → Add-ons → Add-on Store → ⋮ → Repositories → add `https://github.com/Bobsilvio/ha-claude`
2. **Install** — search "Amira" → click Install
3. **Configure** — open **Configuration** tab, paste at least one API key, Save. Runtime features are managed from the Amira **Settings** UI (⚙️ icon in chat)
4. **Start** — click Start, open **Amira** from the sidebar, pick a model

---

## 🔑 Provider Setup

| Provider | Get Key | Free? |
|----------|---------|-------|
| 🟠 GitHub Models | [github.com/settings/tokens](https://github.com/settings/tokens) | ✅ Rate limited |
| 🟣 Anthropic Claude | [console.anthropic.com](https://console.anthropic.com) | ❌ ~$1-5/mo |
| 🟢 OpenAI | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | ❌ ~$1-3/mo |
| 🔵 Google Gemini | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | ✅ 1500 req/day |
| 🟩 NVIDIA NIM | [build.nvidia.com](https://build.nvidia.com) | ✅ Unlimited |
| ⚡ Groq | [console.groq.com](https://console.groq.com) | ✅ Unlimited |
| 🌐 OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) | ❌ Pay per use |
| 🌀 Claude Web | Browser session cookies | ✅ Requires subscription |
| 🌀 Gemini Web ⚠️ | Browser session cookies | ✅ Requires subscription |
| + 10 more | See [DOCS.md](addons/claude-backend/DOCS.md) | — |

**GitHub Copilot & OpenAI Codex** use OAuth — no API key needed, just a one-time login.

**Claude Web & Gemini Web** use browser session cookies — no API key needed, requires an active subscription. Connect via the 🔑 button in the chat UI. → [Full guide](addons/claude-backend/DOCS.md)

---

## 📱 Telegram & WhatsApp

Amira supports **Telegram** (long polling, no public IP) and **WhatsApp** (via Twilio webhook).

→ Setup guide: [docs/MESSAGING.md](docs/MESSAGING.md) · WhatsApp details: [docs/WHATSAPP.md](docs/WHATSAPP.md)

---

## 🔌 MCP (Model Context Protocol)

Extend Amira with external tools. Enable MCP in **Settings → Features**, then configure servers directly from the **Settings → MCP Config** editor in the chat UI.

Example server configuration (HTTP transport):

```json
{
  "my_server": {
    "transport": "http",
    "url": "http://192.168.1.x:7660"
  }
}
```

The config is saved to `/config/amira/mcp_config.json`. Start/stop servers directly from **Settings → MCP** in the chat UI.

→ Full guide: [docs/MCP.md](docs/MCP.md)

---

## 💡 Usage Examples

- *"Turn on the living room lights"* / *"Accendi le luci del soggiorno"*
- *"Create an automation that turns lights off at midnight"*
- *"Show me the temperature history from yesterday"*
- *"Create an HTML dashboard for my solar panels"*
- *"Make a battery monitoring dashboard with charts"*
- *"Build a lights control panel for my home"*
- 📸 *Upload an image* → *"Recreate these cards for my sensors"*

---

## 🆘 Troubleshooting

| Problem | Fix |
|---------|-----|
| Amira not in sidebar | Restart HA, clear browser cache |
| Bubble not showing | Check Settings → Features → Chat Bubble is ON; hard-refresh browser |
| Dashboard shows blank page | Browser console may show a JS error — try regenerating with Claude or GPT-4o |
| Dashboard shows 0 values | Auth issue — ask Amira to rebuild the dashboard |
| Error 401 on HA API | Visit `/api/status`, restart addon |
| API Key errors | Check format, verify account has credit |
| Rate limits | Switch model or wait a few minutes |

Logs: **Settings → Add-ons → Amira → Logs** · Full troubleshooting: [DOCS.md](addons/claude-backend/DOCS.md)

---

## 🤝 Contributing

Issues and pull requests welcome: [github.com/Bobsilvio/ha-claude/issues](https://github.com/Bobsilvio/ha-claude/issues)

---

## 📝 License

**PolyForm Noncommercial License 1.0.0** — see [LICENSE](LICENSE) for full terms.

- ✅ Personal use, hobby projects, home automation enthusiasts: **free**
- ✅ Non-profit and educational institutions: **free**
- ❌ Commercial use: **not permitted without explicit written permission**

---

## 🤖 Custom Agents

Create specialized AI assistants, each with its own model, personality, tools, and fallback chain. Manage agents from the **Config** tab in the sidebar or by editing `/config/amira/agents.json`.

**Why use multiple agents?**
- **Different tasks, different models** — a home agent on Claude Sonnet, a quick-chat agent on Groq Llama (free & fast)
- **Tool isolation** — only the "home" agent can control automations; the "coder" can only read/write files
- **Cost optimization** — route expensive reasoning to premium models, simple Q&A to free tiers
- **Custom personality** — each agent has its own name, emoji, and instructions

### Quick Start

```json
{
  "agents": [
    {
      "id": "home",
      "identity": { "name": "Amira", "emoji": "🏠", "description": "Home automation expert" },
      "model": { "primary": "anthropic/claude-sonnet-4-6", "fallbacks": ["google/gemini-2.0-flash"] },
      "default": true
    },
    {
      "id": "jarvis",
      "identity": { "name": "Jarvis", "emoji": "🤖", "description": "Personal assistant" },
      "model": { "primary": "groq/llama-3.3-70b-versatile" },
      "instructions": "Your name is Jarvis. The user is called Silvio Rossi. Always respond formally."
    },
    {
      "id": "quick",
      "identity": { "name": "Flash", "emoji": "⚡", "description": "Fast answers, no tools" },
      "model": { "primary": "groq/llama-3.3-70b-versatile" },
      "tools": [],
      "temperature": 0.7
    }
  ]
}
```

### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (lowercase, no spaces) |
| `identity.name` | string | Display name in UI and messages |
| `identity.emoji` | string | Icon shown in selector and chat |
| `identity.description` | string | Tooltip text |
| `model.primary` | string | `provider/model` (e.g. `anthropic/claude-sonnet-4-6`) |
| `model.fallbacks` | string[] | Ordered fallback models if primary fails |
| `instructions` | string | Custom instructions **prepended** to the HA default prompt — the agent retains full HA context |
| `tools` | string[] \| null | Allowed tools (`null` = all, `[]` = none) |
| `tools_blocked` | string[] | Explicitly blocked tools |
| `temperature` | number | 0.0–2.0 |
| `thinking_level` | string | `off`, `low`, `medium`, `high`, `adaptive` |
| `default` | bool | Pre-selected on load |
| `enabled` | bool | Set `false` to hide without deleting |

> **Note:** The old `system_prompt` and `system_prompt_override` keys are still accepted for backward compatibility and are treated as `instructions`.

### Channel Routing

Assign a specific agent per messaging channel. Each channel can have one agent:

```json
"channel_agents": {
  "telegram": "home",
  "whatsapp": "coder"
}
```

When a message arrives on Telegram, Amira automatically switches to the `home` agent (with its model and personality). WhatsApp messages use `coder`. If no channel agent is configured, the currently active agent is used.

### Agent API

| Endpoint | Description |
|----------|-------------|
| `GET /api/agents` | List all agents |
| `POST /api/agents` | Create a new agent |
| `PUT /api/agents/<id>` | Update an agent |
| `DELETE /api/agents/<id>` | Delete an agent |
| `POST /api/agents/set` | Switch the active agent |
| `GET /api/agents/channels` | Get channel assignments |
| `PUT /api/agents/channels` | Update channel assignments |

> No restart needed — config is hot-reloaded when `agents.json` changes.

---

## 🙏 Credits

Created with ❤️ for the Home Assistant community — Anthropic, OpenAI, Google, GitHub.

---

**Happy Automating! 🏠🤖**
