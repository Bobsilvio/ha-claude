# AI Assistant Documentation

## Overview

The **AI Assistant add-on** brings enterprise-grade AI to your Home Assistant instance. It provides a web-based chat interface with multi-provider AI support (Anthropic Claude, OpenAI GPT, Google Gemini, NVIDIA NIM, GitHub Models), file access capabilities, persistent memory, document analysis, and more.

The add-on integrates seamlessly with Home Assistant's Supervisor API, requiring no long-lived tokens—just your AI provider API keys.

## Features

### Core Features
- **Streaming chat UI** with real-time responses
- **Multi-provider support**: Anthropic, OpenAI, Google Gemini, NVIDIA NIM, GitHub Models (40+ models)
- **Model switching**: Change AI providers and models on-the-fly without restarting
- **Persistent model selection**: Your chosen agent is saved and restored after restart
- **Multi-language UI**: English, Italian, Spanish, French
- **Home Assistant integration**: Read device states, call services directly from chat

### Advanced Features (Experimental)
- **File Upload & Analysis** (v3.3.0+): Upload PDF, DOCX, TXT, MD, YAML files for AI analysis
- **Persistent Memory** (v3.3.0+): AI remembers past conversations across sessions
- **RAG (Retrieval-Augmented Generation)** (v3.3.0+): Semantic search over uploaded documents
- **File Access**: Optional read/write access to `/config` directory with automatic snapshots

## AI Providers

### Anthropic Claude
- **Models**: Claude 3.5 Sonnet, Haiku, Opus
- **Cost**: ~$3/$0.80/$15 per 1M tokens
- **Setup**: Get API key from [console.anthropic.com](https://console.anthropic.com)
- **Best for**: Complex reasoning, creative tasks, long context

### OpenAI
- **Models**: GPT-4o, GPT-4 Turbo, GPT-4, GPT-3.5 Turbo, o1-preview, o3-mini
- **Cost**: $5-$20 per 1M tokens (varies by model)
- **Setup**: Create API key at [platform.openai.com](https://platform.openai.com)
- **Best for**: Balanced performance, variety of models, tools integration

### Google Gemini
- **Models**: Gemini 2.0 Flash, Pro, Pro Vision
- **Cost**: Free tier available, ~$7.50 per 1M tokens (paid)
- **Setup**: Get API key from [ai.google.dev](https://ai.google.dev)
- **Best for**: Fast responses, vision capabilities, free tier users

### NVIDIA NIM
- **Models**: NVIDIA Llama 3.1 405B, Mistral, Mixtral, etc.
- **Cost**: Free tier (rate-limited)
- **Setup**: Get API key from [build.nvidia.com](https://build.nvidia.com)
- **Thinking Mode**: Available on supported models (opt-in)
- **Best for**: Open-source models, free inference, high throughput

### GitHub Models
- **Models**: OpenAI o1-preview, o3-mini, GPT-4o, Llama, Phi, etc.
- **Cost**: Free for GitHub users (token limits apply)
- **Setup**: Use GitHub PAT (fine-grained, no special permissions needed)
- **Best for**: GitHub users, experimental models, free access

## Installation

1. **Add Repository**:
   - Settings → Add-ons & Backups → Add-on Store → ⋮ → Repositories
   - Add: `https://github.com/Bobsilvio/ha-claude`

2. **Install Add-on**:
   - Search for "AI Assistant"
   - Click **AI Assistant for Home Assistant**
   - Click **Install**

3. **Configure & Start**:
   - Open the **Configuration** tab
   - Add at least one provider API key
   - Click **Save** and **Start**

## Configuration

### Required

At least one AI provider API key is required. Choose based on:
- **Anthropic API Key**: Best all-rounder, most reliable
- **OpenAI API Key**: Variety of models, popular choice
- **Google API Key**: Free options available
- **NVIDIA API Key**: Open-source models, free tier
- **GitHub Token**: Free for GitHub users

### Optional Features

| Setting | Default | Description |
|---------|---------|-------------|
| `language` | `en` | UI language (en/it/es/fr) |
| `enable_file_access` | `false` | Allow read/write `/config` files with snapshots |
| `enable_file_upload` | `false` | Allow uploading documents (PDF, DOCX, TXT, etc.) |
| `enable_memory` | `false` | Enable persistent conversation memory |
| `enable_rag` | `false` | Enable RAG for document search |
| `nvidia_thinking_mode` | `false` | Extra reasoning tokens on NVIDIA models |
| `colored_logs` | `true` | Pretty-print add-on logs |
| `debug_mode` | `false` | Verbose logging for troubleshooting |
| `timeout` | `30` | API request timeout (seconds) |
| `max_retries` | `3` | Retry failed requests |
| `log_level` | `normal` | Log verbosity: `normal`, `verbose`, `debug` |

## Using the Chat

### First Launch
1. Open **AI Assistant** from the Home Assistant sidebar
2. Click the **model dropdown** (top left of chat area)
3. Select an agent/model (e.g., "OpenAI → GPT-4o")
4. Start chatting

### Model Switching
- Click the **model dropdown** to switch providers/models instantly
- Selection is **saved automatically** and persists across restarts

### Home Assistant Integration
Ask the AI about your smart home:
- Device states: *"What's the current garage door status?"*
- Services: *"Turn on the living room lights"*
- Automations: *"Show me my evening routine automation"*

The AI reads states and can trigger actions directly from chat.

### File Upload (Experimental)
If `enable_file_upload: true`:
1. Click the **file upload button** (orange, in input area)
2. Select a document (PDF, DOCX, TXT, MD, YAML)
3. Documents are auto-injected into AI context

Files are cleaned up after use. Upload limit: **10MB per file**.

### Persistent Memory (Experimental)
If `enable_memory: true`:
- AI **remembers past conversations** across sessions
- Memory searches by keywords and message content
- Old conversations are kept (never deleted)
- Memory is local (no cloud sync)

### Document Search (RAG)
If `enable_rag: true` and `enable_file_upload: true`:
- Upload documents to build a knowledge base
- AI performs semantic search over documents
- Results automatically injected into prompts

## Advanced Configuration

### File Access
Requires `enable_file_access: true` in config.

**Snapshot & Restore Mechanism**:
- When you edit `/config` via chat, the add-on creates an automatic backup
- If edit fails or causes issues, you can restore the last snapshot
- Snapshots are kept in `/config/.claude_backups/`

**Example Uses**:
- Edit `configuration.yaml` to add automations
- Update secrets in `secrets.yaml`
- Write custom Python scripts to `python_scripts/`

### Logging & Debugging

Set `log_level` to control verbosity:

- **`normal`** (default): Core messages only (clean logs)
- **`verbose`**: Includes all API request/response logs
- **`debug`**: Maximum detail, including internal state

Use via YAML config or environment variable `LOG_LEVEL`.

## Troubleshooting

### Chat UI doesn't load
1. Verify add-on is **Running** (check green status in Add-ons)
2. Check add-on logs for errors
3. Hard-refresh browser (Ctrl+F5 / Cmd+Shift+R)
4. Restart Home Assistant if persists

### API errors (401, 403, 429)
- **401**: API key is invalid → Check provider account and key format
- **403**: Permissions issue → Verify API key has chat/inference permissions
- **429**: Rate limited → Wait or upgrade to higher tier with provider

### Home Assistant integration not working
- Check `/api/status` endpoint (add `/ha-claude/` to HA URL)
- Verify HA connection status shows `ok`
- Restart add-on if status shows `error`

### File Upload not working
- Ensure `enable_file_upload: true` and**Save** config
- Verify file is < 10MB
- Check supported formats: PDF, DOCX, DOC, TXT, MD, YAML, YML, ODT
- Restart add-on if issues persist

### Memory feature not saving
- Ensure `enable_memory: true` in config
- Check `/config/.claude_memory/` folder exists
- Restart add-on
- Check add-on logs for permission errors

### Module import errors
- Example: `ModuleNotFoundError: No module named 'PyPDF2'`
- Solution: Restart the add-on (dependencies are installed on start)

## API Reference

The add-on exposes a REST API at `/ha-claude/api/` (or direct port 5010 if not using Ingress).

### Chat Endpoints

**POST `/api/chat/stream`**
- Stream-based chat API
- Request body: `{"message": "...", "conversation_id": "..." (optional)}`
- Response: Server-Sent Events (SSE) with streamed tokens

**GET `/api/models`**
- List available providers and models
- Returns: `{"providers": {...}, "models": [...]}`

**POST `/api/set_model`**
- Change active provider/model
- Request body: `{"provider": "openai", "model": "gpt-4o"}`
- Returns: `{"success": true}`

**GET `/api/status`**
- System status (HA connection, feature flags, version)
- Returns: `{"ha_connection_ok": true, "version": "3.3.0", ...}`

### Document Endpoints (File Upload/RAG)

**POST `/api/documents/upload`**
- Upload document for analysis
- Multipart form-data with file
- Returns: `{"success": true, "filename": "...", "pages": N}`

**DELETE `/api/documents/{filename}`**
- Remove uploaded document
- Returns: `{"success": true}`

**GET `/api/documents`**
- List uploaded documents
- Returns: `{"documents": [...]}`

### Memory Endpoints

**GET `/api/memory/search`**
- Search conversation history
- Query params: `q=<query>`
- Returns: `{"results": [...]}`

**DELETE `/api/memory/clear`**
- Clear all memory (use with caution!)
- Returns: `{"success": true}`

For full API details, visit the `/api/` endpoint directly.

## Home Assistant Integration Examples

### Read Device State
*"What's the current temperature in the living room?"*
- AI reads the temperature sensor state from HA

### Call Service
*"Turn off the bedroom lights"*
- AI calls the `light.turn_off` service on bedroom lights

### Complex Automation
*"Create an automation that turns on kitchen lights when motion is detected after sunset"*
- AI reads existing automations and can write new ones to `configuration.yaml`

## Performance Tips

1. **Streaming**: Modern models stream responses (GPT-4o, Claude 3.5) → faster perceived performance
2. **Model Size**: Smaller models (o3-mini, Llama 3.1 70B) are faster but less capable
3. **Timeout Setting**: Increase if using complex reasoning or long documents
4. **Document Size**: Keep uploaded files < 5MB for best performance
5. **Memory Size**: Limit active memory by clearing old conversations occasionally

## Security Notes

- **API Keys**: Stored in HA configuration, never exposed to UI
- **File Access**: Only reads/writes under `/config` directory
- **Ingress**: All traffic through HA Ingress by default (no direct internet exposure)
- **Memory**: Local only, no cloud sync
- **Documents**: Deleted after use, not persisted

## Support

- **Issues**: https://github.com/Bobsilvio/ha-claude/issues
- **Discussions**: https://github.com/Bobsilvio/ha-claude/discussions
- **Repository**: https://github.com/Bobsilvio/ha-claude

## Changelog

See [CHANGELOG.md](https://github.com/Bobsilvio/ha-claude/blob/main/addons/claude-backend/CHANGELOG.md) for version history and updates.
