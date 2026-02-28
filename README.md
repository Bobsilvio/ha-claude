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

Supports **20+ AI providers** and **60+ models**: Anthropic Claude, OpenAI, Google Gemini, NVIDIA NIM, GitHub Models, GitHub Copilot (OAuth), OpenAI Codex (OAuth), Groq, Mistral, DeepSeek, Ollama and more. Chat via **Telegram** or **WhatsApp** in addition to the built-in web UI.

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

### 👁️ Vision Support
- **Image Upload**: Send screenshots, photos, or dashboard images
- **Visual Analysis**: AI can see and understand images
- **Card Recreation**: "Create cards like this image" — AI analyzes and recreates layouts
- **Multi-Provider**: Works with Claude, GPT-4o, Gemini vision models

### 📝 Configuration File Access
- **Read/Write YAML**: Access automations, scripts, scenes, and custom configs
- **File Explorer**: Browse your Home Assistant config directory
- **Safe Editing**: Automatic snapshots before modifications
- **Config Validation**: Check configuration before applying changes

### 💬 Interactive Chat Interface
- **Chat History**: Keep last N conversations, switch between them
- **Streaming Responses**: Real-time token-by-token output
- **Tool Indicators**: See what the AI is doing (badges for each tool call)
- **Copy Button**: One-click copy for all code blocks (YAML, JSON, Python)

### 🫧 Floating Chat Bubble
- **Always Available**: AI chat bubble on every Home Assistant page
- **Context-Aware**: Detects automations, scripts, and HTML dashboards
- **HTML Dashboard Editing**: Modify dashboards in-place keeping same style
- **Voice Input**: Built-in voice recognition
- **Agent Switching**: Change AI provider/model on the fly

### 🌍 Multilingual Support
- **4 Languages**: English, Italian, Spanish, French
- **AI Responses**: AI always responds in your chosen language
- **Config UI Translations**: Settings labels and descriptions in all 4 languages

### 🔌 MCP (Model Context Protocol)
- **Custom Tools**: Connect external services via MCP servers
- **Filesystem, Web Search, Git, Databases**: and any custom MCP-compatible server
- **Multi-server**: Run multiple MCP servers simultaneously

### 📱 Messaging Integration
- **Telegram Bot**: Long polling — no public IP needed, works out of the box
- **WhatsApp**: Twilio integration with webhook support
- **Context Aware**: Full conversation history per user per channel

### ⏰ Scheduled Tasks
- **Cron-based**: Schedule automations using cron expressions
- **Background Execution**: Tasks run independently without user interaction
- **History Tracking**: Log of past executions with error reporting

### 🛠️ Dashboard Creation
- **Lovelace Dashboards**: Create custom dashboards with cards
- **HTML Dashboards**: AI-generated Vue 3 interactive dashboards with real-time data
- **11 Section Types**: Hero, pills, flow, gauge, gauges, kpi, chart, entities, controls, stats, value
- **Live Data**: WebSocket real-time updates with automatic proxy fallback

---

## 📋 Requirements

- **Home Assistant** 2024.1.0+ with Supervisor
- **API Key** for at least one AI provider

---

## 🚀 Quick Start

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FBobsilvio%2Fha-claude)

1. **Add repository** — Settings → Add-ons → Add-on Store → ⋮ → Repositories → add `https://github.com/Bobsilvio/ha-claude`
2. **Install** — search "Amira" → click Install
3. **Configure** — open **Configuration** tab, paste at least one API key, Save
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
| + 12 more | See [DOCS.md](addons/claude-backend/DOCS.md) | — |

**GitHub Copilot & OpenAI Codex** use OAuth — no API key needed, just a one-time login. → [Full guide](addons/claude-backend/DOCS.md)

---

## 📱 Telegram & WhatsApp

Amira supports **Telegram** (long polling, no public IP) and **WhatsApp** (via Twilio webhook).

→ Setup guide: [docs/MESSAGING.md](docs/MESSAGING.md) · WhatsApp details: [docs/WHATSAPP.md](docs/WHATSAPP.md)

---

## 🔌 MCP (Model Context Protocol)

Extend Amira with external tools. Create `/config/amira/mcp_config.json` and restart:

```json
{
  "web_search": {
    "command": "python",
    "args": ["-m", "mcp.server.brave_search"],
    "env": { "BRAVE_API_KEY": "YOUR_KEY" }
  }
}
```

→ Full guide: [docs/MCP.md](docs/MCP.md)

---

## 💡 Usage Examples

- *"Turn on the living room lights"* / *"Accendi le luci del soggiorno"*
- *"Create an automation that turns lights off at midnight"*
- *"Show me the temperature history from yesterday"*
- *"Create an HTML dashboard for my solar panels"*
- 📸 *Upload an image* → *"Recreate these cards for my sensors"*

---

## 🆘 Troubleshooting

| Problem | Fix |
|---------|-----|
| Amira not in sidebar | Restart HA, clear browser cache |
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

## 🙏 Credits

Created with ❤️ for the Home Assistant community — Anthropic, OpenAI, Google, GitHub.

---

**Happy Automating! 🏠🤖**
