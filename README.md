# 🏠🤖 AI Assistant for Home Assistant

**Smart home AI assistant addon** with multi-provider support — control your home, create automations, and manage configurations using natural language.

Supports **4 AI providers** and **40+ models**: Anthropic Claude, OpenAI, Google Gemini, and GitHub Models (GPT, Llama, Mistral, DeepSeek, Grok, Phi, Cohere and more).

[![GitHub Release](https://img.shields.io/github/v/release/Bobsilvio/ha-claude)](https://github.com/Bobsilvio/ha-claude/releases)
[![License](https://img.shields.io/github/license/Bobsilvio/ha-claude)](LICENSE)
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

### 📝 Configuration File Access *(New in v2.9)*
- **Read/Write YAML**: Access automations, scripts, scenes, and custom configs
- **File Explorer**: Browse your Home Assistant config directory
- **Safe Editing**: Automatic snapshots before modifications
- **Config Validation**: Check configuration before applying changes

### 💬 Interactive Chat Interface
- **Chat History**: Keep last 10 conversations, switch between them
- **Streaming Responses**: Real-time token-by-token output
- **Tool Indicators**: See what the AI is doing (badges for each tool call)
- **Persistent Storage**: Conversations survive addon restarts

### 🌍 Multilingual Support *(New in v2.9.27)*
- **4 Languages**: English, Italian, Spanish, French
- **Configurable**: Set preferred language in addon settings
- **Consistent**: AI always responds in your chosen language

### 🛠️ Dashboard Creation
- **Lovelace Dashboards**: Create custom dashboards with cards
- **Card Library**: Supports standard and custom cards
- **View Organization**: Multiple views with icons and titles

---

## 📋 Requirements

- **Home Assistant** 2024.1.0+ with Supervisor
- **API Key** for at least one AI provider (see setup guide below)

---

## 🚀 Quick Start

### 1️⃣ Add Repository

In Home Assistant:
1. Go to **Settings** → **Add-ons & Backups** → **Add-on Store**
2. Click **⋮** (top right) → **Repositories**
3. Add: `https://github.com/Bobsilvio/ha-claude`

### 2️⃣ Install Add-on

1. Open **Add-on Store**
2. Search for **"AI Assistant"**
3. Click **Install**

### 3️⃣ Configure

1. Open addon **Configuration** tab
2. Select **AI Provider** (anthropic, openai, google, or github)
3. Enter your **API Key** (see [provider setup](#-provider-setup) below)
4. (Optional) Select **Language**: en, it, es, or fr
5. (Optional) Enable **File Access** to allow config file operations
6. **Save** and **Start** the addon

### 4️⃣ Access

Click **"AI Assistant"** in the Home Assistant sidebar!

---

## 🔑 Provider Setup

### 🟠 GitHub Models (Recommended - Free!)

> **40+ models** with one token. Includes GPT-4o, Llama, Mistral, DeepSeek, Grok, Phi, Cohere. **Free tier** available.

**Get Token:**
1. Go to https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Fine-grained token"**
3. Name: `HA AI Assistant`
4. Expiration: choose duration
5. **No special permissions needed**
6. Click **"Generate token"**
7. **Copy token** (starts with `github_pat_...`)

**Configure Addon:**
- AI Provider: `github`
- GitHub Token: paste token
- GitHub Model: choose from dropdown (e.g., `gpt-4o-mini`)

**Popular Models:**
| Model | Requests/day (free) | Best For |
|-------|-------------------|----------|
| `gpt-4o-mini` | 150 | Daily use, fast responses |
| `gpt-4o` | 50 | Quality, complex tasks |
| `DeepSeek-V3-0324` | 8 | Advanced reasoning |
| `grok-3-mini` | 30 | xAI, balanced |

---

### 🟣 Anthropic Claude

> Claude Sonnet 4, Opus 4, Haiku 4. Excellent reasoning and analysis.

**Get API Key:**
1. Go to https://console.anthropic.com/
2. Create account or sign in
3. Go to **"API Keys"**
4. Click **"Create Key"**
5. Copy key (starts with `sk-ant-...`)
6. **Add credit**: Billing → Add funds (minimum $5)

**Pricing (pay-per-use):**
- Claude Haiku 4: ~$0.25/1M input tokens
- Claude Sonnet 4: ~$3/1M input tokens
- Typical home use: **$1-5/month**

**Configure Addon:**
- AI Provider: `anthropic`
- Anthropic API Key: paste key

---

### 🟢 OpenAI (ChatGPT)

> GPT-4o, GPT-4o-mini. Industry standard.

**Get API Key:**
1. Go to https://platform.openai.com/
2. Create account or sign in
3. Go to **API Keys** → https://platform.openai.com/api-keys
4. Click **"Create new secret key"**
5. Copy key (starts with `sk-...`)
6. **Add credit**: Billing → Add to credit balance (minimum $5)

⚠️ **Note**: OpenAI API is **separate** from ChatGPT Plus subscription.

**Pricing:**
- GPT-4o-mini: ~$0.15/1M input tokens
- GPT-4o: ~$2.50/1M input tokens
- Typical home use: **$1-3/month** with GPT-4o-mini

**Configure Addon:**
- AI Provider: `openai`
- OpenAI API Key: paste key

---

### 🔵 Google Gemini

> Gemini 2.0 Flash, Gemini 2.5 Pro. Generous free tier.

**Get API Key:**
1. Go to https://aistudio.google.com/apikey
2. Sign in with Google account
3. Click **"Create API Key"**
4. Select or create Google Cloud project
5. Copy API key

**Free Tier:** 15 RPM, 1M TPM, 1500 requests/day — **completely free!**

**Configure Addon:**
- AI Provider: `google`
- Google API Key: paste key

---

## 🏆 Which Provider to Choose?

| Use Case | Recommended |
|----------|-------------|
| **Free, no credit card** | 🟠 GitHub Models or 🔵 Google Gemini |
| **Best quality** | 🟣 Anthropic Claude Sonnet 4 |
| **Most models (40+)** | 🟠 GitHub Models |
| **Low cost, high usage** | 🟢 OpenAI GPT-4o-mini |
| **Open-source models** | 🟠 GitHub Models (Llama, Mistral) |

---

## ⚙️ Configuration Options

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| **AI Provider** | Provider selection (anthropic/openai/google/github) | `anthropic` | ✅ |
| **Anthropic API Key** | Claude API key from console.anthropic.com | - | If using Claude |
| **OpenAI API Key** | OpenAI API key from platform.openai.com | - | If using OpenAI |
| **Google API Key** | Gemini API key from aistudio.google.com | - | If using Gemini |
| **GitHub Token** | Personal Access Token from GitHub | - | If using GitHub |
| **GitHub Model** | Model selection for GitHub provider | `gpt-4o` | If using GitHub |
| **Language** | AI response language (en/it/es/fr) | `en` | ❌ |
| **Enable File Access** | Allow AI to read/write config files | `false` | ❌ |
| **Debug Mode** | Enable detailed logging | `false` | ❌ |
| **API Port** | Internal API port | `5000` | ❌ |
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
- Snapshots stored in `/config/.storage/claude_snapshots/`
- Can restore previous versions from snapshots

**Use cases:**
- "Show me the YAML code for my morning routine automation"
- "List all files in the lovelace folder"
- "Add a condition to automation X checking if Y is on"

---

## 💡 Usage Examples

### Device Control
```
"Turn on the living room lights"
"Set thermostat to 22 degrees"
"What's the temperature in the bedroom?"
"Show me all lights that are currently on"
```

### Automation Management
```
"Create an automation that turns on lights at sunset"
"Add a condition to check if I'm home before turning on lights"
"Show me all automations for the kitchen"
"Delete the automation called 'old routine'"
```

### Configuration Files *(requires File Access enabled)*
```
"Show me the files in my lovelace folder"
"Read the content of automations.yaml"
"List all my custom YAML files"
"What's in the yaml/sensors.yaml file?"
```

### Dashboard Creation
```
"Create a dashboard for living room lights"
"Make a dashboard with all temperature sensors"
"Show me how to add a thermostat card"
```

### History & Statistics
```
"What was the temperature yesterday at noon?"
"Show me the average humidity over the last week"
"When was the last time the front door opened?"
```

---

## 🎨 YAML Diff Display

When modifying configs, the AI shows **before/after** with diff markers:

**Before:**
```yaml
- conditions: []
```

**After:**
```yaml
+ conditions:
+   - condition: state
+     entity_id: binary_sensor.presence
+     state: "on"
```

✅ Clear visualization of changes
✅ Only shows modified sections
✅ Easy to review before applying

---

## 💬 Chat History

- **Persistent**: Conversations survive addon restarts
- **Last 10**: Keep your 10 most recent conversations
- **Switchable**: Click any conversation to reload it
- **Storage**: Saved in `/config/.storage/claude_conversations.json`

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chat UI interface |
| `/api/chat/stream` | POST | Streaming chat (SSE) |
| `/api/conversations` | GET | List all conversations |
| `/api/conversations/<id>` | GET | Get specific conversation |
| `/api/status` | GET | Diagnostics & health check |
| `/health` | GET | Simple health check |

---

## 🆘 Troubleshooting

### AI Assistant not in sidebar
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
- GitHub Models free tier has daily limits (check table above)
- Try switching to a different model
- Wait a few minutes if rate limited
- Consider upgrading to paid tier

### File Access not working
- Verify **Enable File Access** is set to `true` in config
- Restart addon after enabling
- Check logs for "ENABLE_FILE_ACCESS: true"
- Ensure files exist in `/config/` directory

### Chat history not saving
- Conversations stored in `/config/.storage/claude_conversations.json`
- Check file permissions on `/config/.storage/`
- Try sending a message to trigger save
- Restart addon if conversations don't persist

---

## 📜 Changelog

### v2.9.27 (Latest)
- ✨ **Multilingual support** (EN, IT, ES, FR)
- ✨ **Improved YAML diff format** - show only changed sections
- 🐛 Fixed conversation persistence path
- 🐛 Fixed GitHub token limit with extended tool set

### v2.9.26
- ✨ **Show YAML before/after** for all modifications
- ✨ Enhanced tool responses with code display

### v2.9.25
- 🐛 **Fixed conversation persistence** - moved to `/config/.storage/`
- ✨ Chat history now survives addon rebuilds

### v2.9.24
- ✨ **File access support** with 12-tool extended set for GitHub
- ✨ Optimized token usage for GitHub Models

[Full Changelog →](https://github.com/Bobsilvio/ha-claude/releases)

---

## 🤝 Contributing

Issues and pull requests welcome! Visit:
https://github.com/Bobsilvio/ha-claude/issues

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

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
