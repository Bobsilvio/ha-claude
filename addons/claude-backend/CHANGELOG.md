# Changelog

## 4.1.1 — Dockerfile fixes + new modules
- **FIX**: Corrected Dockerfile `COPY` instructions — removed non-existent `memory_system.py` reference
- **NEW**: Added `scheduled_tasks.py` to the Docker image (task scheduler module)
- **NEW**: Added `voice_transcription.py` to the Docker image (voice/TTS module)
- **FIX**: Removed duplicate `COPY memory.py` instruction in Dockerfile

## 4.1.0 — Complete provider architecture rewrite + dashboard intelligence
> **Breaking change from v3.x** — provider system completamente riscritto

### Provider system
- Sostituito il sistema monolitico `providers_anthropic/google/openai.py` con il pacchetto modulare `providers/`
- 22 provider class: OpenAI, Anthropic, Google, Groq, Mistral, NVIDIA, DeepSeek, OpenRouter, Ollama, GitHub, GitHub Copilot, ChatGPT Web, OpenAI Codex, Zhipu, SiliconFlow, Moonshot, MiniMax, AiHubMix, VolcEngine, DashScope, Perplexity, Custom
- Provider manager con interfaccia di streaming unificata e gestione errori migliorata
- Lista modelli dinamica: `PROVIDER_MODELS` costruita da `get_available_models()` di ogni provider all'avvio — unica fonte di verità
- `model_fetcher.py`: aggiornamento live dei modelli dalle API ufficiali con cache su disco
- `rate_limiter.py`, `error_handler.py`, `tool_simulator.py`: utility condivise tra provider

### OpenAI Codex provider
- Flusso OAuth PKCE: token salvato in `/data/oauth_codex.json` con auto-refresh
- Lista modelli corretta (solo gpt-5.x-codex)
- Banner connessione in UI con ID account, scadenza e pulsante disconnetti
- Endpoint `/api/oauth/codex/revoke`

### Dashboard HTML
- **Smart context split**: `[CURRENT_DASHBOARD_HTML]` iniettato come turno separato nella conversazione per evitare token overflow mantenendo il contesto entità completo (cap 10KB)
- **Intent detection**: lookup filesystem in `www/dashboards/` per routing corretto verso `create_html_dashboard`
- `openMoreInfo()` con evento `hass-more-info` nativo + modal fallback
- Redirect autenticazione: se token assente, redirect a `/?redirect=...`
- Titolo sidebar sempre prefissato `Amira — <titolo>` (enforced in `tools.py`)

### Chat UI e bubble
- `stripContextInjections()`: nasconde blocchi `[CONTEXT:...]` e `[CURRENT_DASHBOARD_HTML]` dalla cronologia visualizzata
- Artifact delle tool call nascosti dalla cronologia (`api_conversation_get`)
- Drag della bubble corretto con Pointer Events API + `setPointerCapture()`
- Rimossi i testi obsoleti "Novità v3.0" in tutte e 4 le lingue

### Nuove funzionalità
- **MCP**: supporto server Model Context Protocol
- **Telegram & WhatsApp**: integrazione bot
- **Voice transcription**: supporto Whisper (STT) e TTS
- **Semantic cache**: riduzione chiamate API con cache semantica
- **RAG**: Retrieval-Augmented Generation su file locali
- **File upload**: caricamento file nelle conversazioni
- **Memory**: sistema memoria con `MEMORY.md` (long-term) e `HISTORY.md` (log sessioni)
- **Scheduled tasks**: task scheduler con agente autonomo
- **Quality metrics**: metriche qualità risposte
- **Prompt caching**: caching prompt per ridurre costi Anthropic
- **Image support**: analisi immagini multi-provider
- **GitHub Copilot**: provider OAuth dedicato
