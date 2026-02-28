# Home Assistant - Amira Setup Guide

Quick setup for users installing the Amira add-on on Home Assistant.

---

## 📋 Prerequisites

- Home Assistant installed
- SSH add-on (optional, for troubleshooting)
- 2GB+ RAM on HA machine

---

## 🚀 Installation

1. **Add custom repository** (if not already in official repo)
   - Settings → Add-ons & Backups → Add-on Store → ⋮ → Repositories
   - Add: `https://github.com/Bobsilvio/ha-claude`

2. **Install Amira add-on**
   - Search "Amira"
   - Click Install
   - Wait for "Add-on installed successfully"

3. **Configure it**
   - Click the add-on card
   - Go to **Configuration** tab
   - Fill in required fields:
     - **AI Provider**: Choose one (anthropic, openai, google, etc.)
     - **API Key**: Paste your API key for chosen provider
     - **Language**: en, it, es, or fr
   - Scroll down and click **Save**

4. **Start it**
   - Click **Start** button
   - Check logs to see "Amira Backend API started"
   - Go to **Info** tab, click blue "Open Web UI" button

---

## 🤖 First Chat

1. Open the web UI (blue button in add-on info)
2. You're in **Chat** tab (default)
3. Type a message: *"Hello, who are you?"*
4. Assistant responds with intro

---

## 📱 Messaging (Telegram / WhatsApp)

### Enable Telegram

1. Get a **Telegram bot token**:
   - Open Telegram → message **@BotFather**
   - Type `/newbot` → follow steps → copy token

2. Add to configuration:
   - Add-on Settings → **telegram_bot_token**: `paste_token_here`
   - Save and restart

3. Open Telegram → search bot → `/start`
   - Now chat with assistant via Telegram!

### Enable WhatsApp

1. Get **Twilio credentials** (trial account):
   - [Twilio.com](https://www.twilio.com) → sign up
   - Get: Account SID, Auth Token, WhatsApp number

2. Add to configuration:
   - **twilio_account_sid**: `paste_sid`
   - **twilio_auth_token**: `paste_token`
   - **twilio_whatsapp_from**: `+1234567890` (Twilio number)
   - Save and restart

3. Optional: Set webhook in Twilio dashboard to receive messages

---

## 🌐 MCP (Model Context Protocol)

### What is MCP?

Add custom tools like:
- 📁 **Filesystem**: Read/write files in `/config`
- 🔍 **Web Search**: Search the internet
- � **Git**: Version control history
- 📊 **Database**: Query databases
- 🔧 **Custom Tools**: Connect APIs

### Quick Setup (3 Steps)

**Step 1: Create Configuration File**

SSH into Home Assistant and create `/config/amira/mcp_config.json`:

```bash
cat > /config/amira/mcp_config.json << 'EOF'
{
  "filesystem": {
    "transport": "http",
    "url": "http://YOUR-SERVER-IP:PORT"
  }
}
EOF
```

**Step 2: Restart Add-on**

1. Settings → Add-ons → Amira
2. Click **Restart**
3. Check logs - should show `MCP Config: configured`

**Step 3: Test It**

Chat: *"List files in /config"*

### Add More Tools

See [MCP.md](MCP.md) for examples of:
- Web search (Brave Search)
- Git repository access
- Database queries
- Slack integration
- And more!

---

## ⚙️ Configuration Options

| Option | Meaning | Default |
|--------|---------|---------|
| **ai_provider** | Which AI to use | anthropic |
| **anthropic_api_key** | Claude API key | (required if using Anthropic) |
| **openai_api_key** | ChatGPT API key | (required if using OpenAI) |
| **enable_memory** | Remember past chats | false |
| **enable_chat_bubble** | Floating assistant | false |
| **enable_file_upload** | Accept file uploads | false |
| **language** | UI language | en |
| **telegram_bot_token** | Telegram bot token | (optional) |
| **twilio_account_sid** | WhatsApp SID | (optional) |
| **mcp_config_file** | Custom tools config | `/config/amira/mcp_config.json` |

---

## 🐛 Troubleshooting

### "Cannot connect to API"
- Restart add-on
- Check firewall/ports
- Look at add-on logs

### "Invalid API key"
- Copy key carefully (no extra spaces)
- Verify key is for correct provider
- Check key not expired

### "MCP server not connecting"
- Ensure `npx` is available
- JSON format must be valid
- Try simpler example first

### View Logs
1. Open add-on
2. Go to **Logs** tab
3. See real-time output

---

## 📚 More Info

- **Chat Features**: See [DOCS.md](DOCS.md)
- **Messaging Setup**: See [MESSAGING.md](MESSAGING.md)
- **MCP Tools**: See [MCP.md](MCP.md)
- **File Upload/RAG**: See [DOCS.md - File Processing](DOCS.md#-file-processing)

---

## 💡 Pro Tips

✅ **Memory**: Enable if you want assistant to remember context between chats
✅ **Chat Bubble**: Enable to add floating assistant on all HA pages
✅ **Multiple Providers**: Can configure multiple API keys, switch between them
✅ **MCP**: Start with filesystem tool, add more as needed

---

## 🆘 Help

- Check logs in add-on
- See [Troubleshooting](DOCS.md#-troubleshooting) section in DOCS.md
- Open GitHub issue with logs attached
