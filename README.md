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

---

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
# 🏠🤖 Amira Ai Assistant

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

### 👁️ Vision Support *(New in v3.0!)*
- **📸 Image Upload**: Send screenshots, photos, or dashboard images
- **Visual Analysis**: AI can see and understand images
- **Card Recreation**: "Create cards like this image" - AI analyzes and recreates layouts
- **Smart Suggestions**: Show a dashboard, get improvement suggestions
- **Multi-Provider**: Works with Claude, GPT-4o, Gemini vision models

### 📝 Configuration File Access *(New in v2.9)*
- **Read/Write YAML**: Access automations, scripts, scenes, and custom configs
- **File Explorer**: Browse your Home Assistant config directory
- **Safe Editing**: Automatic snapshots before modifications
- **Backup Management**: Restore or delete backups, per-file snapshot limits
- **Config Validation**: Check configuration before applying changes

### 💬 Interactive Chat Interface
- **Chat History**: Keep last 10 conversations, switch between them
- **Streaming Responses**: Real-time token-by-token output
- **Tool Indicators**: See what the AI is doing (badges for each tool call)
- **Copy Button**: One-click copy for all code blocks (YAML, JSON, Python)
- **Persistent Storage**: Conversations survive addon restarts

### 🫧 Floating Chat Bubble
- **Always Available**: AI chat bubble on every Home Assistant page
- **Context-Aware**: Detects automations, scripts, and HTML dashboards
- **HTML Dashboard Editing**: Modify dashboards in-place keeping same style
- **Voice Input**: Built-in voice recognition
- **Agent Switching**: Change AI provider/model on the fly
- **Hidden on Mobile**: Automatically hidden on companion app

### 🌍 Multilingual Support
- **4 Languages**: English, Italian, Spanish, French
- **AI Responses**: AI always responds in your chosen language (v2.9.27)
- **Config UI Translations**: Settings labels and descriptions in all 4 languages (v3.0.2)
- **Fully Localized**: Complete multilingual experience

### 📱 Messaging Integration
- **Telegram Bot**: Long polling — no public IP needed, works out of the box
- **WhatsApp**: Twilio integration with webhook support
- **Context Aware**: Full conversation history per user per channel
- **Multi-channel**: Use both simultaneously

### 🛠️ Dashboard Creation
- **Lovelace Dashboards**: Create custom dashboards with cards
- **HTML Dashboards**: AI-generated Vue 3 interactive dashboards with real-time data
- **11 Section Types**: Hero, pills, flow, gauge, gauges, kpi, chart, entities, controls, stats, value
- **Live Data**: WebSocket real-time updates with automatic proxy fallback (no browser auth needed)
- **Card Library**: Supports standard and custom cards
- **View Organization**: Multiple views with icons and titles

---

## 📋 Requirements

- **Home Assistant** 2024.1.0+ with Supervisor
- **API Key** for at least one AI provider (see setup guide below)

---

## 🚀 Quick Start
Simply click the button below to add it automatically:

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FBobsilvio%2Fha-claude)

### 1️⃣ Add Repository

In Home Assistant:
1. Go to **Settings** → **Add-ons & Backups** → **Add-on Store**
2. Click **⋮** (top right) → **Repositories**
3. Add: `https://github.com/Bobsilvio/ha-claude`

### 2️⃣ Install Add-on

1. Open **Add-on Store**
2. Search for **"Amira"**
3. Click **Install**

### 3️⃣ Configure

1. Open addon **Configuration** tab
2. Paste **at least one provider key** (Anthropic / OpenAI / Google / NVIDIA / GitHub)
3. (Optional) Select **Language**: en, it, es, or fr
4. (Optional) Enable **File Access** to allow config file operations
5. **Save** and **Start** the addon
6. Open **Amira** from the sidebar and pick an **agent/model** from the top dropdown (your choice is saved automatically)

### 4️⃣ Access

Click **"Amira"** in the Home Assistant sidebar!

---

## 🔑 Provider Setup

| Provider | Get Key | Free? |
|----------|---------|-------|
| 🟠 GitHub Models | [github.com/settings/tokens](https://github.com/settings/tokens) | ✅ Rate limited |
| 🟣 Anthropic Claude | [console.anthropic.com](https://console.anthropic.com) | ❌ ~$1-5/mo typical |
| 🟢 OpenAI | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | ❌ ~$1-3/mo typical |
| 🔵 Google Gemini | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | ✅ 1500 req/day |
| 🟩 NVIDIA NIM | [build.nvidia.com](https://build.nvidia.com) | ✅ Unlimited |
| ⚡ Groq | [console.groq.com](https://console.groq.com) | ✅ Unlimited |
| 🌐 OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) | ❌ Pay per use |
| + 12 more | See [SETUP_HA.md](SETUP_HA.md) | — |

→ Step-by-step key creation guide: [SETUP_HA.md](SETUP_HA.md)

---

## 🔑 GitHub Copilot & OpenAI Codex (OAuth)

These providers use **OAuth authentication** — no API key to paste, just a one-time login.

### GitHub Copilot
Requires an active **GitHub Copilot subscription** (Individual, Business, or Enterprise).

1. Select **GitHub Copilot** from the model dropdown in Amira
2. A blue banner **"GitHub Copilot requires authentication"** appears → click **Connect GitHub Copilot**
3. A code like `ABCD-1234` is shown → open [github.com/login/device](https://github.com/login/device) and enter it
4. Authorize the app on GitHub → the addon polls automatically and confirms ✔ Connected
5. Token is saved persistently in `/data/oauth_copilot.json`

Available models: `gpt-4o`, `gpt-4o-mini`, `o3-mini`, `o1`, `claude-3.7-sonnet`, `gemini-2.0-flash`, and more.

### OpenAI Codex
Requires **ChatGPT Plus or Pro**.

1. Select **OpenAI Codex** from the model dropdown
2. Click **Connect OpenAI Codex** in the yellow banner
3. A browser tab opens to OpenAI login → after login, copy the full redirect URL and paste it in the Amira modal
4. Token saved in `/data/oauth_codex.json` and auto-refreshed

Available models: `o4-mini`, `o3`, `o3-mini`, `gpt-4.5`, `o1`.

---

## 📱 Telegram & WhatsApp

Amira supports **Telegram** (long polling, no public IP needed) and **WhatsApp** (via Twilio webhook).

### Telegram (quick setup)
1. Open Telegram → **@BotFather** → `/newbot` → get your token
2. In addon **Configuration**:
   ```
   telegram_bot_token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```
3. Save & Restart — message your bot and it replies with Amira AI responses

### WhatsApp via Twilio (requires public URL)
1. Sign up at [twilio.com](https://twilio.com) → get **Account SID**, **Auth Token**, and a WhatsApp Sandbox number
2. In addon **Configuration**:
   ```
   twilio_account_sid: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   twilio_auth_token:  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   twilio_whatsapp_from: +14155238886
   ```
3. In Twilio Console (Messaging → Try it out → Send a WhatsApp message → **Sandbox settings**) set:
   - **"When a message comes in"** → `http://YOUR-HA-IP:5010/api/whatsapp/webhook`
   - Method: **HTTP POST**
4. Open port **5010** on your router (Port Forwarding → TCP → your HA IP)
5. Save & Restart the addon
6. Send `join <your-sandbox-code>` from WhatsApp to the Twilio number to join the Sandbox

> ⚠️ Amira listens on port **5010** directly — the URL must include `:5010/api/whatsapp/webhook`.
> Using `https://ha.yourdomain.eu/api/whatsapp/webhook` (port 443) gives a **404** because that
> hits the HA frontend, not Amira. See the full guide for Nginx reverse proxy alternative.

→ **Full setup guide (italiano/english):** [docs/WHATSAPP.md](docs/WHATSAPP.md)

---

## ⚙️ Configuration Options

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| **Anthropic API Key** | Claude API key from console.anthropic.com | - | If using Claude |
| **OpenAI API Key** | OpenAI API key from platform.openai.com | - | If using OpenAI |
| **Google API Key** | Gemini API key from aistudio.google.com | - | If using Gemini |
| **NVIDIA API Key** | NVIDIA NIM API key | - | If using NVIDIA |
| **NVIDIA Thinking Mode** | Enable extra reasoning tokens (when supported) | `false` | ❌ |
| **GitHub Token** | Personal Access Token from GitHub | - | If using GitHub |
| **Language** | AI response language (en/it/es/fr) | `en` | ❌ |
| **Enable File Access** | Allow AI to read/write config files | `false` | ❌ |
| **Chat Bubble** | Floating AI bubble on every HA page (context-aware) | `false` | ❌ |
| **Max Backups per File** | Max backup snapshots per file (oldest auto-deleted) | `5` | ❌ |
| **Max Conversations** | Max chat conversations in history (1-100) | `10` | ❌ |
| **Debug Mode** | Enable detailed logging | `false` | ❌ |
| **Colored Logs** | Emoji indicators in addon logs | `true` | ❌ |
| **Log Level** | Log verbosity (normal/verbose/debug) | `normal` | ❌ |
| **API Port** | Internal API port | `5010` | ❌ |
| **Timeout** | API request timeout (seconds) | `30` | ❌ |
| **Max Retries** | Retry attempts for failed API calls | `3` | ❌ |

### 🔒 File Access Feature

When **Enable File Access** is enabled, the AI can:
- ✅ Read automation, script, and configuration files
- ✅ List files in your config directory (including custom folders like `lovelace/`)
- ✅ Modify YAML files with automatic snapshots (backups)
- ✅ Validate configuration before applying changes

**Safety features:**
- Automatic backup before any modification
- Read-only by default (disabled)
- Snapshots stored in `/config/amira/snapshots/`
- Restore or delete backups from the UI
- Per-file snapshot limits (configurable, default 5 per file)

**Use cases:**
- "Show me the YAML code for my morning routine automation"
- "List all files in the lovelace folder"
- "Add a condition to automation X checking if Y is on"

---

## � Data Storage

All persistent data is stored in **`/config/amira/`** — one folder, easy to backup or inspect.

```
/config/amira/
├── conversations.json        # Chat history
├── runtime_selection.json    # Last selected model/provider
├── snapshots/                # Config file backups (before edits)
├── mcp_config.json           # MCP servers (create manually)
└── memory/
    ├── MEMORY.md             # Long-term facts (always in context)
    └── HISTORY.md            # Session log (append-only)
```

> Files from older versions (`/config/.storage/claude_*`) are migrated automatically on first start.

---

## 🧠 Memory

When `enable_memory: true`, Amira uses a two-file system:

- **`MEMORY.md`** — Injected once in every session. Write here what the AI should always know.
- **`HISTORY.md`** — Automatic, append-only log of past sessions. Never auto-injected.

```bash
# SSH into HA, then:
nano /config/amira/memory/MEMORY.md
```

No per-message keyword search, no cross-session contamination. Token-efficient.

→ Full detail: [addons/claude-backend/README.md](addons/claude-backend/README.md)

---

## 💡 Usage Examples

Just talk naturally — Amira understands intent in English, Italian, Spanish and French:

- *"Turn on the living room lights"* / *"Accendi le luci del soggiorno"*
- *"Create an automation that turns lights off at midnight"*
- *"Show me the temperature history from yesterday"*
- *"Add a condition to the morning routine automation"*
- *"Create an HTML dashboard for my solar panels"*
- 📸 *Upload an image* → *"Recreate these cards for my sensors"*

→ Full multilingual example list: [DOCS.md](DOCS.md)

---

## 💬 Chat History

- **Persistent**: Conversations survive addon restarts
- **Configurable depth**: Keep last N chats (default 10)
- **Switchable**: Click any conversation to reload it
- **Storage**: `/config/amira/conversations.json`

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chat UI interface |
| `/api/chat/stream` | POST | Streaming chat (SSE) |
| `/api/conversations` | GET | List all conversations |
| `/api/conversations/<id>` | GET | Get specific conversation |
| `/api/snapshots` | GET | List backup snapshots |
| `/api/snapshots/<id>` | DELETE | Delete a backup snapshot |
| `/api/status` | GET | Diagnostics & health check |
| `/health` | GET | Simple health check |

---

## 🆘 Troubleshooting

### Amira not in sidebar
- Restart Home Assistant completely
- Check addon logs for errors
- Verify addon is in "Running" state
- Try clearing browser cache

### Error 401 on HA API
- `SUPERVISOR_TOKEN` is managed automatically
- Visit `/api/status` to check `ha_connection_ok`
- Restart the addon
- Check addon logs for token errors

### API Key errors
- Verify correct key for selected provider
- For Anthropic/OpenAI: ensure you've added credit to account
- For GitHub: token must be valid (not expired)
- Check key format (starts with correct prefix)

### Model not responding / rate limits
- GitHub Models free tier has daily limits (check the GitHub Models dashboard / provider docs)
- Try switching to a different model
- Wait a few minutes if rate limited
- Consider upgrading to paid tier

### File Access not working
- Verify **Enable File Access** is set to `true` in config
- Restart addon after enabling
- Check logs for "ENABLE_FILE_ACCESS: true"
- Ensure files exist in `/config/` directory

### Chat history not saving
- Conversations stored in `/config/amira/conversations.json`
- Check file permissions on `/config/amira/`
- Try sending a message to trigger save
- Restart addon if conversations don't persist

---

## 🤝 Contributing

Issues and pull requests welcome! Visit:
https://github.com/Bobsilvio/ha-claude/issues

---

## 📝 License

**PolyForm Noncommercial License 1.0.0** — see [LICENSE](LICENSE) for full terms.

- ✅ Personal use, hobby projects, home automation enthusiasts: **free**
- ✅ Non-profit organizations, educational and government institutions: **free**
- ❌ Commercial use (paid services, businesses, installers charging clients): **not permitted without explicit written permission from the author**

To request a commercial license: open an issue on [GitHub](https://github.com/Bobsilvio/ha-claude/issues).

---

## 🙏 Credits

Created with ❤️ for the Home Assistant community

**Special thanks to:**
- Anthropic for Claude API
- OpenAI for GPT models
- Google for Gemini
- GitHub for GitHub Models access

---

## ⭐ Show Your Support

If you find this project useful, consider:
- ⭐ **Starring** the repository
- 🐛 Reporting bugs or suggesting features
- 📢 Sharing with other Home Assistant users
- ☕ [Buy me a coffee](https://ko-fi.com/bobsilvio) *(optional)*

---

**Happy Automating! 🏠🤖**
