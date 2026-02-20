# AI Assistant for Home Assistant (Add-on)

**Multi-provider AI chat interface** for Home Assistant. Chat with Claude, GPT-4, Gemini, NVIDIA, GitHub Models, and more.

## Quick Start

### 1. Add Repository
Settings → Add-ons & Backups → Add-on Store → ⋮ → Repositories → `https://github.com/Bobsilvio/ha-claude`

### 2. Install & Configure
- Install **AI Assistant for Home Assistant**
- Configuration tab → Add **at least one AI provider API key** (Anthropic/OpenAI/Google/NVIDIA/GitHub)
- Save & Start

### 3. First Run
Open **AI Assistant** from sidebar → Select an agent from the dropdown → Start chatting

## What You Get

- ✅ Streaming chat with real-time responses
- ✅ 40+ AI models across multiple providers
- ✅ Home Assistant integration (read states, call services)
- ✅ Multi-language UI (EN/IT/ES/FR)
- ✅ Floating chat bubble on every HA page (context-aware)
- ✅ Backup management with restore & delete + per-file limits
- ✅ Optional: File upload, Persistent memory, Document search

## Configuration

Add one or more provider API keys in the add-on configuration:

- **Anthropic API Key**: Claude 3.5 Sonnet/Haiku (get from [console.anthropic.com](https://console.anthropic.com))
- **OpenAI API Key**: GPT-4, o3-mini (get from [platform.openai.com](https://platform.openai.com))
- **Google API Key**: Gemini (get from [ai.google.dev](https://ai.google.dev))
- **NVIDIA API Key**: Open-source models (get from [build.nvidia.com](https://build.nvidia.com))
- **GitHub Token**: Fine-grained token with no special permissions (get from GitHub Settings)

**Optional Features**:
- `enable_chat_bubble` → Floating AI chat bubble on every HA page (context-aware, voice input, hidden on mobile)
- `enable_file_upload` → Upload PDF/DOCX/TXT for AI analysis
- `enable_memory` → AI remembers past conversations
- `enable_rag` → Semantic search over documents
- `enable_file_access` → Read/write `/config` files (with snapshots)
- `max_snapshots_per_file` → Max backup snapshots per file (default 5, oldest auto-deleted)
- `max_conversations` → Max chat conversations in history (1-100)
- `language` → UI language (en/it/es/fr)
- `debug_mode` → Verbose logging
- `log_level` → Log verbosity (normal/verbose/debug)

For all options and details, see **DOCS.md** tab in the add-on.

## Troubleshooting

- **Sidebar not visible?** → Restart Home Assistant and ensure add-on is running
- **API errors?** → Verify API key is valid and has correct permissions
- **Chat doesn't load?** → Hard-refresh browser (Ctrl+F5) or check add-on logs
- **More help?** → See **DOCS.md** tab or [GitHub issues](https://github.com/Bobsilvio/ha-claude/issues)

## Links

- 📖 **Full Documentation**: See **DOCS.md** tab
- 🐛 **Issues**: https://github.com/Bobsilvio/ha-claude/issues
- 💬 **Discussions**: https://github.com/Bobsilvio/ha-claude/discussions

