# Amira - Smart Home AI Assistant

Multi-provider AI assistant for Home Assistant. Control your smart home, create automations, and manage configurations with natural language.

Supports **23+ AI providers** and **60+ models**: Anthropic Claude, OpenAI, Google Gemini, NVIDIA NIM, GitHub Models, GitHub Copilot, OpenAI Codex, xAI Grok, Groq, Mistral, Ollama, DeepSeek, OpenRouter and more.

**Recent updates**: automation flow chart redesigned (human-readable trigger/condition/action, branch expansion for choose/if/repeat, refresh after Save, relative last-triggered time), plus model catalog cache panel in Settings, provider model test improvements, card-editor chat tab, and HTML dashboard snapshot debug files. See [CHANGELOG](CHANGELOG.md) for full details.

---

## 🚀 Quick Start

1. **Install** → Settings → Add-ons → Add-on Store → Search "Amira"
2. **Add at least one API key** (see providers table below)
3. **Start** → Open Web UI → Pick a model → Chat!

> 💡 **Free options**: GitHub Models (40+ models), NVIDIA NIM, Groq, Google Gemini (1500 req/day).
>
> 💳 **Already paying for ChatGPT Plus/Pro?** Use **OpenAI Codex** — included in your subscription, no API key needed. See below.

---

## ✨ Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🏠 **Smart Home Control** | Built-in | Natural language device control, service calls, area management |
| 🤖 **Automation Management** | Built-in | Create & modify automations with YAML diff view |
| 🔧 **System Diagnostics** | Built-in | View HA repairs, health checks, AI-suggested fixes |
| 💬 **Streaming Chat UI** | Built-in | Real-time responses, tool badges, code copy, conversation history |
| 🫧 **Floating Chat Bubble** | ⚙️ ON | AI accessible on every HA page, context-aware |
| 🧭 **Automation Flow Chart** | Built-in | Visual automation map in editor/detail pages with human-readable logic and branch rendering |
| 🤖 **Card Editor Button** | ⚙️ ON | Amira button in Lovelace card editor for inline AI help |
| 💬 **Card Chat Tab** | Built-in | Dedicated history tab for Lovelace card-editor conversations |
| 🎙️ **Voice Input & TTS** | ⚙️ ON | Multi-provider voice: Groq/OpenAI/Google STT + Edge/Groq/OpenAI TTS |
| 📎 **File Upload** | ⚙️ ON | Upload PDF, DOCX, TXT, MD, YAML for AI analysis |
| 👁️ **Vision** | Built-in | Image upload & analysis (Claude, GPT-4o, Gemini) |
| 🧠 **Memory** | ⚙️ OFF | Persistent MEMORY.md injected in every conversation |
| 📁 **File Access** | ⚙️ OFF | Read/write HA config files with automatic snapshots |
| 🔍 **RAG** | ⚙️ OFF | Semantic search over uploaded documents |
| 🔌 **MCP Tools** | ⚙️ OFF | Extend AI with external tools via Model Context Protocol |
| 🔄 **Provider Fallback** | ⚙️ OFF | Automatic fallback chain when primary provider fails |
| 🗂️ **Model Cache Panel** | Built-in | Inspect fixed/dynamic models, blocklists, tested models, refresh/clear cache |
| 🤖 **Multi-Agent System** | Built-in | Custom agents with own model, tools, prompt, fallback |
| 💰 **Cost Tracking** | Built-in | Per-message cost with cache breakdown, daily aggregates |
| 🛠️ **Dashboard Creation** | Built-in | Lovelace cards + AI-generated HTML dashboards (Vue 3) |
| 📱 **Telegram Bot** | ⚙️ OFF | Long polling — no public IP needed |
| 📱 **WhatsApp** | ⚙️ OFF | Twilio integration with webhook |
| ⏰ **Scheduled Tasks** | Built-in | Cron-based task scheduler |
| 🌍 **4 Languages** | Built-in | EN / IT / ES / FR — UI + AI responses |

> ⚙️ = configurable from **Settings** UI (⚙️ icon in chat). ON/OFF shows the default.

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
| Ollama (local/cloud) | `ollama_base_url` + `ollama_api_key` (optional) | ✅ Local | [ollama.com](https://ollama.com) |
| DeepSeek | `deepseek_api_key` | ❌ | [platform.deepseek.com](https://platform.deepseek.com) |
| xAI Grok | `xai_api_key` | ❌ | [console.x.ai](https://console.x.ai) |
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

### Configuration Architecture

Amira uses **two layers** of configuration:

1. **`config.yaml`** (HA Add-on page → Configuration tab) — API keys and log settings only
2. **Settings UI** (Amira chat → ⚙️ Settings) — All runtime features, managed from the web interface with descriptions in 4 languages

> 💡 After saving settings in the UI, you'll be prompted to restart the addon to apply changes.

#### config.yaml settings (API keys + logging)

| Setting | Description |
|---------|-------------|
| `anthropic_api_key` | Anthropic Claude API key |
| `openai_api_key` | OpenAI API key |
| `google_api_key` | Google Gemini API key |
| `github_token` | GitHub Models / Copilot token |
| `nvidia_api_key` | NVIDIA NIM API key |
| `groq_api_key` | Groq API key |
| `ollama_base_url` | Ollama server URL (e.g. `http://192.168.1.x:11434`) |
| `ollama_api_key` | Ollama Cloud API key (optional; leave empty for local Ollama) |
| + 13 more providers | See providers table above |
| `colored_logs` | Pretty-print add-on logs |
| `debug_mode` | Verbose logging for troubleshooting |
| `log_level` | `normal` / `verbose` / `debug` |

Note: if `ollama_api_key` is set and `ollama_base_url` is still the default local URL, Amira auto-switches to `https://ollama.com` (official cloud host).

#### Runtime settings (managed via Settings UI)

| Setting | Default | Description |
|---------|---------|-------------|
| `language` | `en` | UI language: en / it / es / fr |
| `enable_file_access` | OFF | Read/write HA config files |
| `enable_file_upload` | **ON** | Upload PDF / DOCX / TXT |
| `enable_memory` | OFF | Persistent MEMORY.md (see below) |
| `enable_rag` | OFF | Semantic search in uploaded documents |
| `enable_chat_bubble` | **ON** | Floating AI button on every HA page |
| `enable_amira_card_button` | **ON** | 🤖 Amira button in the Lovelace card editor |
| `enable_voice_input` | **ON** | Voice input in chat bubble |
| `enable_mcp` | OFF | Enable MCP tool servers |
| `fallback_enabled` | OFF | Provider fallback chain |
| `tts_voice` | `female` | TTS voice gender (male / female) |
| `max_conversations` | `10` | Chat history depth (1–100) |
| `cost_currency` | `USD` | Cost display currency (USD, EUR) |
| `timeout` | `30` | Request timeout (seconds) |
| `max_retries` | `3` | Retry failed API requests |

### 🗂️ Model Cache (Settings → Config → Model Cache)

The Settings UI includes a dedicated **Model Cache** section showing:
- **Fixed models** (hardcoded curated models per provider)
- **Dynamic cached models** (discovered at runtime)
- **Blocklisted models** (provider-specific invalid/unsupported models)
- **Tested OK models** (for providers that support batch testing)

Controls:
- **Refresh Cache**: refreshes runtime-discovered models
- **Clear Cache**: clears dynamic cache while keeping persistent blocklist safety

Notes:
- Fixed and dynamic lists are de-duplicated. If a model appears in both, it is shown in **Fixed**.
- Blocklists are persisted and re-applied after startup, refresh, and clear operations.

### 💰 Cost & Usage Tracking

Every message shows real-time cost with cache token breakdown:
- **Per-message**: `1.5k in / 300 out (500 cache↓) • $0.0084` with tooltip showing input/output/cache breakdown
- **Session totals**: Running token and cost total for the current conversation
- **Persistent tracking**: Daily, per-model, and per-provider aggregates saved to `/data/usage_stats.json`
- **Cache-aware pricing**: Anthropic (90% read discount), OpenAI (50%), Google (75%), DeepSeek (90%)

**API endpoints:**
| Endpoint | Description |
|----------|-------------|
| `GET /api/usage_stats` | Full usage summary (last 30 days, by model, by provider) |
| `GET /api/usage_stats/today` | Today's totals |
| `POST /api/usage_stats/reset` | Reset all usage data |

### 🤖 Multi-Agent System

Agents let you create **specialised AI personalities**, each with its own model, tools, system prompt and fallback chain. Instead of one generic assistant, you can switch between tailored agents from the sidebar or the chat bubble.

**Why use multiple agents?**
- **Different tasks, different models** — a coding agent on Claude Opus, a quick-chat agent on Groq Llama (free & fast)
- **Tool isolation** — only the "home" agent can control automations; the "coder" can only read/write files
- **Cost optimisation** — route expensive reasoning to premium models, simple Q&A to free tiers
- **Custom personality** — each agent has its own name, emoji, and optional system prompt

#### Adding your first agent

Create (or edit) `/config/amira/agents.json`. You can use any of these formats:

**Recommended format (array):**

```json
{
  "agents": [
    {
      "id": "home",
      "identity": { "name": "Amira", "emoji": "🏠", "description": "Home automation expert" },
      "model": { "primary": "anthropic/claude-sonnet-4-6", "fallbacks": ["google/gemini-2.0-flash"] },
      "tools": ["create_automation", "update_automation", "call_service", "get_entity"],
      "is_default": true
    }
  ]
}
```

**Shorthand format (flat dict — agent ID as key):**

```json
{
  "home": {
    "identity": { "name": "Amira", "emoji": "🏠", "description": "Home automation expert" },
    "model": "anthropic/claude-sonnet-4-6",
    "is_default": true
  }
}
```

#### Adding a second agent

Add another entry to the `agents` array:

```json
{
  "agents": [
    {
      "id": "home",
      "identity": { "name": "Amira", "emoji": "🏠", "description": "Home automation expert" },
      "model": { "primary": "anthropic/claude-sonnet-4-6", "fallbacks": ["google/gemini-2.0-flash"] },
      "is_default": true
    },
    {
      "id": "coder",
      "identity": { "name": "CodeBot", "emoji": "💻", "description": "Coding & config specialist" },
      "model": { "primary": "anthropic/claude-opus-4-6", "fallbacks": ["openai/gpt-4o"] },
      "tools": ["read_config_file", "write_config_file", "list_config_files"],
      "system_prompt_override": "You are a coding expert. Always show code with comments.",
      "temperature": 0.2
    }
  ]
}
```

> **Tip:** You can also create and manage agents directly from the **Config** tab in the sidebar — no JSON editing required!

After saving, the agent selector appears in the sidebar. Click an agent to switch — model, tools and prompt apply instantly (no restart needed, config is hot-reloaded).

#### Field reference

| Field | Type | Description |
|-------|------|-------------|
| `identity.name` | string | Display name in UI |
| `identity.emoji` | string | Icon shown in selector and messages |
| `identity.description` | string | Tooltip text |
| `model` | string | `provider/model` — the preferred model |
| `fallback` | string[] | Ordered fallback models if primary fails |
| `tools` | string[] \| null | Allowed tools (`null` = all tools) |
| `tools_blocked` | string[] | Explicitly blocked tools |
| `system_prompt_override` | string \| null | Custom system prompt (replaces default) |
| `temperature` | number \| null | 0.0–2.0 (null = provider default) |
| `max_tokens` | number \| null | Max response length |
| `thinking_level` | string \| null | `off`, `low`, `medium`, `high`, `adaptive` |
| `is_default` | bool | Mark one agent as the default |
| `enabled` | bool | Set `false` to hide without deleting |
| `tags` | string[] | Arbitrary tags for organisation |

### 🧠 Dynamic Model Catalog

All model metadata lives in a centralized catalog (`model_catalog.py`) — capabilities (vision, reasoning, code, tool use), context windows, max output tokens, and pricing tiers. The catalog is:
1. Built from a rich static table (zero network calls)
2. Enriched at runtime by `/v1/models` discovery (NVIDIA, Ollama, GitHub Copilot)
3. Queried by the agent system, fallback engine, and UI

Model catalog/cache APIs:
- `GET /api/models/cache/status` — fixed/dynamic cache + blocklist + tested summary
- `POST /api/models/cache/refresh` — refresh dynamic cache
- `POST /api/models/cache/clear` — clear dynamic cache (blocklist persists)

Provider model test APIs:
- `POST /api/nvidia/test_models` — NVIDIA model batch validation
- `POST /api/provider/test_models` — batch validation for selected providers (currently OpenRouter, Mistral)

### 🛡️ Automation Safety

`create_automation` now includes safety guards:
- **Rejects empty automations** — trigger and action arrays must contain actual content
- **Detects duplicate aliases** — warns if a similar automation already exists, suggests `update_automation`
- **Improved tool schemas** — examples in parameter descriptions prevent AI from omitting required fields

---

## 📁 Data Storage

All persistent data lives in **`/config/amira/`** — one folder, easy to backup.

```
/config/amira/
├── settings.json             # Runtime settings (managed via Settings UI)
├── conversations.json        # Chat history
├── runtime_selection.json    # Last selected model/provider
├── model_blocklist.json      # Provider model blocklists/tested state (auto-managed)
├── llm_dashboards/           # Incoming/final HTML snapshots for dashboard debug
├── agents.json               # Multi-agent config (name, model, tools, fallback)
├── bubble_devices.json       # Chat bubble per-device config
├── custom_system_prompt.txt  # Custom system prompt override
├── mcp_config.json           # MCP servers config
├── snapshots/                # Config file backups (before edits)
├── rag/                      # RAG document index
├── documents/                # Uploaded files
└── memory/
    ├── MEMORY.md             # Long-term facts (always in context)
    ├── HISTORY.md            # Session log (append-only)
    └── conversations.json    # Full conversation archive

/config/www/
└── ha-claude-chat-bubble.js  # Floating chat bubble (auto-generated)

/data/
├── amira_models_cache.json   # Dynamic discovered model cache
└── usage_stats.json          # Persistent cost/usage tracking (daily, per-model, per-provider)
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

1. Enable MCP in **Settings → Features → MCP**
2. Open **Settings → MCP Config** in the chat UI
3. Add your servers in the JSON editor:

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

→ Full guide: [MCP.md](../../../docs/MCP.md)

---

## 📱 Messaging (Optional)

| Setting | Description |
|---------|-------------|
| `telegram_bot_token` | Bot token from Telegram @BotFather |
| `twilio_account_sid` | Twilio SID for WhatsApp |
| `twilio_auth_token` | Twilio auth token |
| `twilio_whatsapp_from` | Your Twilio WhatsApp number |

→ Setup guide: [MESSAGING.md](../../../docs/MESSAGING.md)

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Invalid API key" | Check key format matches selected provider |
| No models in dropdown | Add at least one API key, restart |
| File access not working | Enable in Settings → Features → File Access, restart |
| Bubble not visible | Check Settings → Features → Chat Bubble is ON; hard-refresh browser (Ctrl+F5) |
| Chat history lost | Check write permissions on `/config/amira/` |
| Memory not working | Enable in Settings → Features → Memory; check `/config/amira/memory/MEMORY.md` |
| MCP not loading | Validate JSON at `/config/amira/mcp_config.json`; check logs |

Check logs: **Settings → Add-ons → Amira → Logs**

---

## 📖 Docs

| | |
|---|---|
| [DOCS.md](DOCS.md) | Full technical reference |
| [SETUP_HA.md](../../../docs/SETUP_HA.md) | Step-by-step installation |
| [MCP.md](../../../docs/MCP.md) | MCP tools setup |
| [MESSAGING.md](../../../docs/MESSAGING.md) | Telegram / WhatsApp |

---

## 📜 License

PolyForm Non-Commercial License 1.0.0 — free for personal use.
Commercial use requires explicit written permission from the author.

---

## 🆘 Support

- 🐛 [Report Issues](https://github.com/Bobsilvio/ha-claude/issues)
- 💬 [Discussions](https://github.com/Bobsilvio/ha-claude/discussions)
- ⭐ Star on GitHub if you find it useful!
