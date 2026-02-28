# Amira - Smart Home AI Assistant

Multi-provider AI assistant for Home Assistant. Control your smart home, create automations, and manage configurations with natural language.

Supports **19 AI providers** and **40+ models**: Anthropic Claude, OpenAI, Google Gemini, NVIDIA NIM, GitHub Models, Groq, Mistral, Ollama, DeepSeek, OpenRouter and more.

---

## 🚀 Quick Start

1. **Install** → Settings → Add-ons → Add-on Store → Search "Amira"
2. **Add at least one API key** (see providers table below)
3. **Start** → Open Web UI → Pick a model → Chat!

> 💡 **Free options**: GitHub Models (40+ models), NVIDIA NIM, Groq, Google Gemini (1500 req/day).
>
> 💳 **Already paying for ChatGPT Plus/Pro?** Use **OpenAI Codex** — included in your subscription, no API key needed. See below.

---

## ⚙️ Configuration

### Providers

| Provider | Key Setting | Free? | Get Key |
|----------|-------------|-------|---------|
| Anthropic Claude | `anthropic_api_key` | ❌ | [console.anthropic.com](https://console.anthropic.com) |
| OpenAI | `openai_api_key` | ❌ | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| Google Gemini | `google_api_key` | ✅ 1500 req/day | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| NVIDIA NIM | `nvidia_api_key` | ✅ Unlimited | [build.nvidia.com](https://build.nvidia.com) |
| GitHub Models | `github_token` | ✅ Rate limited | [github.com/settings/tokens](https://github.com/settings/tokens) |
| Groq | `groq_api_key` | ✅ Unlimited | [console.groq.com](https://console.groq.com) |
| Mistral | `mistral_api_key` | ❌ | [console.mistral.ai](https://console.mistral.ai) |
| Ollama (local) | `ollama_base_url` | ✅ Local | [ollama.com](https://ollama.com) |
| DeepSeek | `deepseek_api_key` | ❌ | [platform.deepseek.com](https://platform.deepseek.com) |
| OpenRouter | `openrouter_api_key` | ❌ | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Perplexity | `perplexity_api_key` | ❌ | [perplexity.ai/api](https://www.perplexity.ai/api) |
| MiniMax | `minimax_api_key` | ❌ | [minimaxi.com](https://www.minimaxi.com) |
| AiHubMix | `aihubmix_api_key` | ❌ | [aihubmix.com](https://aihubmix.com) |
| SiliconFlow | `siliconflow_api_key` | ❌ | [siliconflow.cn](https://siliconflow.cn) |
| VolcEngine | `volcengine_api_key` | ❌ | [volcengine.com](https://www.volcengine.com) |
| DashScope | `dashscope_api_key` | ❌ | [dashscope.aliyun.com](https://dashscope.aliyun.com) |
| Moonshot | `moonshot_api_key` | ❌ | [platform.moonshot.cn](https://platform.moonshot.cn) |
| Zhipu AI | `zhipu_api_key` | ❌ | [open.bigmodel.cn](https://open.bigmodel.cn) |
| GitHub Copilot | OAuth (no key) | ✅ (sub req.) | [github.com/login/device](https://github.com/login/device) |
| OpenAI Codex | OAuth (no key) | ✅ (sub req.) | ChatGPT Plus/Pro — see below |
| Custom | `custom_api_key` + `custom_api_base` | varies | Any OpenAI-compatible API |

### 💳 OpenAI Codex — for ChatGPT Plus/Pro subscribers

If you already pay for **ChatGPT Plus** ($20/mo) or **Pro** ($200/mo), you can use OpenAI's Codex models inside Amira **at no extra cost** — no API key required.

**How it works:** Amira authenticates with your ChatGPT account via OAuth (same login you use on chatgpt.com). The token is stored locally and auto-refreshed.

**Available models:** `gpt-5.3-codex`, `gpt-5.2-codex`, `gpt-5.1-codex`, `gpt-5-codex`, `gpt-5-codex-mini` — specialized for agentic coding tasks, ideal for HA automations, scripts and dashboard generation.

**vs. standard OpenAI API:**
| | OpenAI API (`openai_api_key`) | OpenAI Codex (OAuth) |
|---|---|---|
| Cost | Pay per token | Included in ChatGPT Plus/Pro |
| Auth | API key | Login with ChatGPT account |
| Models | GPT-4o, o3, o4-mini, … | gpt-5.x-codex family |
| Best for | General use, all OpenAI models | ChatGPT subscribers, coding tasks |

**Setup:**
1. Select **OpenAI Codex** as provider in Amira
2. Click **🔑 Connect OpenAI Codex** in the banner that appears
3. Log in with your ChatGPT account in the new tab
4. Copy the redirect URL (`localhost:1455/...`) and paste it in the Amira modal
5. Done — a green banner confirms the connection with expiry info

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `language` | `en` | UI language: en / it / es / fr |
| `enable_file_access` | `false` | Read/write HA config files |
| `enable_chat_bubble` | `false` | Floating AI button on every HA page |
| `enable_memory` | `false` | Persistent MEMORY.md (see below) |
| `enable_file_upload` | `false` | Upload PDF / DOCX / TXT |
| `enable_rag` | `false` | Semantic search in uploaded documents |
| `max_conversations` | `10` | Chat history depth (1–100) |
| `cost_currency` | `USD` | Cost display currency |
| `timeout` | `30` | Request timeout (seconds) |
| `mcp_config_file` | `/config/amira/mcp_config.json` | Custom MCP tools |

---

## 📁 Data Storage

All persistent data lives in **`/config/amira/`** — one folder, easy to backup.

```
/config/amira/
├── conversations.json        # Chat history
├── runtime_selection.json    # Last selected model/provider
├── model_blocklist.json      # Blocked/failed models
├── bubble_devices.json       # Chat bubble per-device config
├── custom_system_prompt.txt  # Custom system prompt override
├── mcp_config.json           # MCP servers (create this manually)
├── snapshots/                # Config file backups (before edits)
├── rag/                      # RAG document index
├── documents/                # Uploaded files
└── memory/
    ├── MEMORY.md             # Long-term facts (always in context)
    ├── HISTORY.md            # Session log (append-only)
    └── conversations.json    # Full conversation archive
```

> Files from older versions (`/config/.storage/claude_*`) are migrated automatically on first start.

---

## 🧠 Memory

When `enable_memory: true`, Amira uses a two-file system:

- **`MEMORY.md`** — Injected once in every system prompt. Write here what the AI should always know.
- **`HISTORY.md`** — Append-only log of past sessions. Never auto-injected, available for manual reference.

**Add persistent context (SSH into HA):**

```bash
mkdir -p /config/amira/memory
nano /config/amira/memory/MEMORY.md
```

Example:
```markdown
## User
Name: Eleonora. Home Assistant OS, single user.
## Preferences
Reply in Italian. Keep answers concise.
## Home
3 zones: Living room, Bedroom, Garden. Solar panels on roof.
```

No per-message keyword search, no cross-session contamination. Simple and token-efficient.

---

## 🔌 MCP Tools (Custom AI Actions)

Extend the AI with external tools via [Model Context Protocol](https://modelcontextprotocol.io/):

1. Create `/config/amira/mcp_config.json`
2. Add your servers:

```json
{
  "filesystem": {
    "transport": "http",
    "url": "http://YOUR-SERVER-IP:PORT"
  }
}
```

For stdio servers (if node/python available on the host):
```json
{
  "my_tool": {
    "transport": "stdio",
    "command": "uvx",
    "args": ["mcp-server-name"]
  }
}
```

3. Restart addon → check logs for "MCP: Initialized N server(s)"

→ Full guide: [MCP.md](../../../MCP.md)

---

## 📱 Messaging (Optional)

| Setting | Description |
|---------|-------------|
| `telegram_bot_token` | Bot token from Telegram @BotFather |
| `twilio_account_sid` | Twilio SID for WhatsApp |
| `twilio_auth_token` | Twilio auth token |
| `twilio_whatsapp_from` | Your Twilio WhatsApp number |

→ Setup guide: [MESSAGING.md](../../../MESSAGING.md)

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Invalid API key" | Check key format matches selected provider |
| No models in dropdown | Add at least one API key, restart |
| File access not working | Enable `enable_file_access: true`, restart |
| Bubble not visible | Enable `enable_chat_bubble: true`, refresh |
| Chat history lost | Check write permissions on `/config/amira/` |
| Memory not working | Enable `enable_memory: true`; check `/config/amira/memory/MEMORY.md` |
| MCP not loading | Validate JSON at `/config/amira/mcp_config.json`; check logs |

Check logs: **Settings → Add-ons → Amira → Logs**

---

## 📖 Docs

| | |
|---|---|
| [DOCS.md](../../../DOCS.md) | Full technical reference |
| [SETUP_HA.md](../../../SETUP_HA.md) | Step-by-step installation |
| [MCP.md](../../../MCP.md) | MCP tools setup |
| [MESSAGING.md](../../../MESSAGING.md) | Telegram / WhatsApp |

---

## 📜 License

PolyForm Non-Commercial License 1.0.0 — free for personal use.
Commercial use requires explicit written permission from the author.

---

## 🆘 Support

- 🐛 [Report Issues](https://github.com/Bobsilvio/ha-claude/issues)
- 💬 [Discussions](https://github.com/Bobsilvio/ha-claude/discussions)
- ⭐ Star on GitHub if you find it useful!


