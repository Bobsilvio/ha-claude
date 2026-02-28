# Amira Documentation

## Overview

The **Amira add-on** brings enterprise-grade AI to your Home Assistant instance. It provides a web-based chat interface with multi-provider AI support (20+ providers, 60+ models), file access capabilities, persistent memory, document analysis, MCP tool integration, Telegram & WhatsApp messaging, and more.

The add-on integrates seamlessly with Home Assistant's Supervisor API — no long-lived tokens required, just your AI provider API keys.

## Features

### Core Features
- **Streaming chat UI** with real-time responses
- **Multi-provider support**: 20+ AI providers, 60+ models
- **Model switching**: Change AI providers and models on-the-fly without restarting
- **Persistent model selection**: Your chosen agent is saved and restored after restart
- **Multi-language UI**: English, Italian, Spanish, French
- **Home Assistant integration**: Read device states, call services directly from chat
- **Floating Chat Bubble**: AI accessible on every HA page
- **MCP Tools**: Extend AI with external tools and APIs

### Advanced Features
- **File Upload & Analysis**: Upload PDF, DOCX, TXT, MD, YAML files for AI analysis
- **Persistent Memory**: AI remembers past conversations across sessions via MEMORY.md
- **RAG (Retrieval-Augmented Generation)**: Semantic search over uploaded documents
- **File Access**: Optional read/write access to `/config` directory with automatic snapshots
- **Vision Support**: Image upload and analysis (screenshots, photos, dashboard images)
- **Telegram Bot**: Long polling — no public IP needed
- **WhatsApp**: Twilio integration with webhook support

## AI Providers

### Anthropic Claude
- **Models**: claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5, and more
- **Cost**: ~$3–$15 per 1M tokens depending on model
- **Setup**: Get API key from [console.anthropic.com](https://console.anthropic.com)
- **Best for**: Complex reasoning, creative tasks, long context

### OpenAI
- **Models**: GPT-4o, GPT-4 Turbo, o1, o3-mini, and more
- **Cost**: $5–$20 per 1M tokens (varies by model)
- **Setup**: Create API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Best for**: Balanced performance, variety of models

### Google Gemini
- **Models**: Gemini 2.0 Flash, Gemini 1.5 Pro, and more
- **Cost**: Free tier (1500 req/day), ~$7.50 per 1M tokens (paid)
- **Setup**: Get API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Best for**: Fast responses, vision capabilities, free tier users

### NVIDIA NIM
- **Models**: Llama 3.1 405B/70B, Mistral Large, Mixtral, Kimi K2.5, and more
- **Cost**: Free tier (rate-limited)
- **Setup**: Get API key from [build.nvidia.com](https://build.nvidia.com)
- **Best for**: Open-source models, free inference, high throughput

### GitHub Models
- **Models**: GPT-4o, o1, o3-mini, Llama, Phi, and more
- **Cost**: Free for GitHub users (rate limits apply)
- **Setup**: GitHub PAT from [github.com/settings/tokens](https://github.com/settings/tokens) (no special permissions needed)
- **Best for**: GitHub users, experimental models, free access

### Groq
- **Models**: Llama 3.1 70B/8B, Mixtral, and more
- **Cost**: Free tier (generous limits)
- **Setup**: Get API key from [console.groq.com](https://console.groq.com)
- **Best for**: Very fast inference, free usage

### Mistral
- **Models**: Mistral Large, Medium, Small, and more
- **Cost**: Pay per use (~$2–$8 per 1M tokens)
- **Setup**: Get API key from [console.mistral.ai](https://console.mistral.ai)
- **Best for**: European users, efficient models

### Ollama (Local)
- **Models**: Any model you pull locally (Llama, Qwen, Mistral, etc.)
- **Cost**: Free (runs on your hardware)
- **Setup**: Install [ollama.com](https://ollama.com), set `ollama_base_url` (e.g. `http://192.168.1.x:11434`)
- **Best for**: Privacy, offline use, no API costs

### DeepSeek
- **Models**: DeepSeek Chat, DeepSeek Reasoner
- **Cost**: Very low (~$0.14–$0.55 per 1M tokens)
- **Setup**: Get API key from [platform.deepseek.com](https://platform.deepseek.com)
- **Best for**: Cost-efficient inference, reasoning tasks

### OpenRouter
- **Models**: Access to 100+ models from multiple providers
- **Cost**: Pay per use (varies by model)
- **Setup**: Get API key from [openrouter.ai/keys](https://openrouter.ai/keys)
- **Best for**: Switching between many providers with one key

### GitHub Copilot (OAuth)
- **Models**: GPT-4o, o3-mini, Claude 3.7 Sonnet, Gemini 2.0 Flash, and more
- **Cost**: Requires active GitHub Copilot subscription
- **Setup**: OAuth device flow — click "Connect GitHub Copilot" in the UI, enter the code at [github.com/login/device](https://github.com/login/device)
- **Best for**: GitHub Copilot subscribers getting extra value

### OpenAI Codex (OAuth)
- **Models**: gpt-5.3-codex, gpt-5.2-codex, gpt-5.1-codex, gpt-5-codex, gpt-5-codex-mini and more
- **Cost**: Included with **ChatGPT Plus** ($20/mo) or **Pro** ($200/mo) — no extra API charges
- **Setup**: OAuth flow — click "Connect OpenAI Codex" in the UI; once logged in a green banner confirms the connection with expiry info
- **Best for**: Users who already pay for ChatGPT Plus/Pro and want to use Codex models without a separate API key

> 💡 **Already paying for ChatGPT?** Use this provider instead of the standard OpenAI API — it's included in your subscription at no extra cost. The Codex models (`gpt-5.3-codex`, etc.) are optimized for agentic coding tasks and work well for Home Assistant automations, scripts and dashboard generation.

> ⚠️ Generic OpenAI reasoning models (o3, o4-mini) are **not** supported via this endpoint. Use the `openai` provider with an API key for those.

### Other Providers
- **Perplexity**: Real-time web search models — [perplexity.ai/api](https://www.perplexity.ai/api)
- **MiniMax**: Chinese LLM with long context — [minimaxi.com](https://www.minimaxi.com)
- **AiHubMix**: Aggregator with many models — [aihubmix.com](https://aihubmix.com)
- **SiliconFlow**: Fast Chinese inference — [siliconflow.cn](https://siliconflow.cn)
- **VolcEngine**: ByteDance AI — [volcengine.com](https://www.volcengine.com)
- **DashScope**: Alibaba Qwen models — [dashscope.aliyun.com](https://dashscope.aliyun.com)
- **Moonshot**: Kimi models — [platform.moonshot.cn](https://platform.moonshot.cn)
- **Zhipu AI**: GLM models — [open.bigmodel.cn](https://open.bigmodel.cn)
- **Custom**: Any OpenAI-compatible endpoint — set `custom_api_base` and `custom_api_key`

## Installation

1. **Add Repository**:
   - Settings → Add-ons & Backups → Add-on Store → ⋮ → Repositories
   - Add: `https://github.com/Bobsilvio/ha-claude`

2. **Install Add-on**:
   - Search for "Amira"
   - Click **Amira Ai Assistant** → **Install**

3. **Configure & Start**:
   - Open the **Configuration** tab
   - Add at least one provider API key
   - Click **Save** and **Start**

## Configuration

### Optional Features

| Setting | Default | Description |
|---------|---------|-------------|
| `language` | `en` | UI language (en/it/es/fr) |
| `enable_file_access` | `false` | Allow read/write `/config` files with snapshots |
| `enable_file_upload` | `false` | Allow uploading documents (PDF, DOCX, TXT, etc.) |
| `enable_memory` | `false` | Enable persistent conversation memory |
| `enable_rag` | `false` | Enable RAG for document search |
| `enable_chat_bubble` | `false` | Floating AI button on every HA page |
| `nvidia_thinking_mode` | `false` | Extra reasoning tokens on NVIDIA models |
| `colored_logs` | `true` | Pretty-print add-on logs |
| `debug_mode` | `false` | Verbose logging for troubleshooting |
| `timeout` | `30` | API request timeout (seconds) |
| `max_retries` | `3` | Retry failed requests |
| `log_level` | `normal` | Log verbosity: `normal`, `verbose`, `debug` |
| `max_conversations` | `10` | Chat history depth (1–100) |
| `max_snapshots_per_file` | `5` | Max backups per config file |

## Using the Chat

### First Launch
1. Open **Amira** from the Home Assistant sidebar
2. Click the **model dropdown** (top left of chat area)
3. Select an agent/model (e.g., "Groq → Llama 3.1 70B")
4. Start chatting

### Home Assistant Integration
Ask the AI about your smart home:
- Device states: *"What's the current garage door status?"*
- Services: *"Turn on the living room lights"*
- Automations: *"Show me my evening routine automation"*

### File Upload
If `enable_file_upload: true`:
1. Click the **file upload button** (in input area)
2. Select a document (PDF, DOCX, TXT, MD, YAML)
3. Documents are auto-injected into AI context (limit: 10MB)

### Persistent Memory
If `enable_memory: true`, Amira uses a two-file system:

- **`MEMORY.md`** — Injected in every session. Write here what the AI should always know.
- **`HISTORY.md`** — Append-only log of past sessions (for your reference).

```bash
# SSH into HA, then:
nano /config/amira/memory/MEMORY.md
```

## Advanced Configuration

### File Access
Requires `enable_file_access: true`. Snapshots stored in `/config/amira/snapshots/`.

### MCP Tools
Create `/config/amira/mcp_config.json` to add external tools:

```json
{
  "my_server": {
    "transport": "http",
    "url": "http://192.168.1.x:7660"
  }
}
```

→ Full guide: [MCP.md](../../../docs/MCP.md)

### Logging
Set `log_level`:
- **`normal`** (default): Core messages only
- **`verbose`**: Includes API request/response logs
- **`debug`**: Maximum detail

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Chat UI doesn't load | Restart add-on, hard-refresh browser (Ctrl+F5) |
| 401 API error | API key invalid — check format and account balance |
| 429 Rate limit | Wait or upgrade to higher tier with provider |
| File access not working | Enable `enable_file_access: true`, restart |
| Memory not saving | Check `/config/amira/memory/` folder exists and is writable |
| MCP not loading | Validate JSON at `/config/amira/mcp_config.json`; check logs |
| Module import errors | Restart the add-on (dependencies install on start) |

## API Reference

The add-on exposes a REST API accessible via HA Ingress or directly on port 5010.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/stream` | POST | Streaming chat (SSE) |
| `/api/models` | GET | List available providers and models |
| `/api/set_model` | POST | Change active provider/model |
| `/api/status` | GET | System status (HA connection, features, version) |
| `/api/conversations` | GET | List all conversations |
| `/api/snapshots` | GET | List config file backups |
| `/api/documents/upload` | POST | Upload document for analysis |
| `/api/messaging/stats` | GET | Telegram & WhatsApp statistics |
| `/health` | GET | Simple health check |

## Data Storage

All persistent data lives in **`/config/amira/`**:

```
/config/amira/
├── conversations.json        # Chat history
├── runtime_selection.json    # Last selected model/provider
├── mcp_config.json           # MCP servers (create manually)
├── snapshots/                # Config file backups (before edits)
├── documents/                # Uploaded files
├── rag/                      # RAG document index
└── memory/
    ├── MEMORY.md             # Long-term facts (always in context)
    └── HISTORY.md            # Session log (append-only)
```

## Security Notes

- **API Keys**: Stored in HA configuration, never exposed to UI
- **File Access**: Only reads/writes under `/config` directory
- **Ingress**: All traffic through HA Ingress by default
- **Memory**: Local only, no cloud sync
- **MCP Config**: Never commit `/config/amira/mcp_config.json` to git if it contains API keys

## Support

- **Issues**: https://github.com/Bobsilvio/ha-claude/issues
- **Discussions**: https://github.com/Bobsilvio/ha-claude/discussions
- **Repository**: https://github.com/Bobsilvio/ha-claude

## Changelog

See [CHANGELOG.md](https://github.com/Bobsilvio/ha-claude/blob/main/CHANGELOG.md) for version history.
