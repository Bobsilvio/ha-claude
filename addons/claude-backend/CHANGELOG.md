# Changelog

## 4.1.1 — Dockerfile fixes + new modules
- **FIX**: Corrected Dockerfile `COPY` instructions — removed non-existent `memory_system.py` reference
- **NEW**: Added `scheduled_tasks.py` to the Docker image (task scheduler module)
- **NEW**: Added `voice_transcription.py` to the Docker image (voice/TTS module)
- **FIX**: Removed duplicate `COPY memory.py` instruction in Dockerfile

## 4.1.0 — Complete provider architecture rewrite + dashboard intelligence
> **Breaking change from v3.x** — provider system completely rewritten

### Provider system
- Replaced monolithic `providers_anthropic/google/openai.py` with the modular `providers/` package
- 22 provider classes: OpenAI, Anthropic, Google, Groq, Mistral, NVIDIA, DeepSeek, OpenRouter, Ollama, GitHub, GitHub Copilot, ChatGPT Web, OpenAI Codex, Zhipu, SiliconFlow, Moonshot, MiniMax, AiHubMix, VolcEngine, DashScope, Perplexity, Custom
- Provider manager with unified streaming interface and enhanced error handling
- Dynamic model list: `PROVIDER_MODELS` built from each provider's `get_available_models()` at startup — single source of truth
- `model_fetcher.py`: live model refresh from official APIs with on-disk cache
- `rate_limiter.py`, `error_handler.py`, `tool_simulator.py`: shared utilities across providers

### OpenAI Codex provider
- OAuth PKCE flow: token stored at `/data/oauth_codex.json` with auto-refresh
- Correct model list (gpt-5.x-codex only)
- Connected banner in UI showing account ID, expiry and disconnect button
- `/api/oauth/codex/revoke` endpoint

### HTML Dashboard
- **Smart context split**: `[CURRENT_DASHBOARD_HTML]` injected as a separate conversation turn to avoid token overflow while keeping the full entity context (10KB cap)
- **Intent detection**: filesystem lookup in `www/dashboards/` to correctly route requests to `create_html_dashboard`
- `openMoreInfo()` with native `hass-more-info` event + custom modal fallback
- Auth redirect: if token is missing, redirect to `/?redirect=...`
- Sidebar title always prefixed with `Amira — <title>` (enforced in `tools.py`)

### Chat UI & bubble
- `stripContextInjections()`: hides `[CONTEXT:...]` and `[CURRENT_DASHBOARD_HTML]` blocks from the displayed conversation history without affecting stored data
- Tool call artifacts hidden from conversation history (`api_conversation_get`)
- Bubble drag fixed with Pointer Events API + `setPointerCapture()`
- Removed outdated "Novita v3.0" vision feature strings across all 4 languages

### New features
- **MCP**: Model Context Protocol server support
- **Telegram & WhatsApp**: bot integration
- **Voice transcription**: Whisper STT and TTS support
- **Semantic cache**: reduces API calls via semantic response caching
- **RAG**: Retrieval-Augmented Generation on local files
- **File upload**: attach files to conversations
- **Memory**: two-layer memory system with `MEMORY.md` (long-term facts) and `HISTORY.md` (session log)
- **Scheduled tasks**: task scheduler with autonomous agent
- **Quality metrics**: response quality scoring
- **Prompt caching**: prompt caching to reduce Anthropic API costs
- **Image support**: multi-provider image analysis
- **GitHub Copilot**: dedicated OAuth provider
