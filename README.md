# 🏠🤖 AI Assistant for Home Assistant

Smart home AI assistant addon with **multi-provider support** — control your home, create automations, and chat with your devices using natural language.

Supports **4 providers** and **37+ AI models**: OpenAI, Anthropic Claude, Google Gemini, and GitHub Models (GPT-4o, Llama, Mistral, DeepSeek, Grok, Phi, Cohere and more).

---

## 🎯 Features

- **Multi-Provider AI**: Claude, ChatGPT, Gemini, GitHub Models (37+ models)
- **Smart Home Control**: Control lights, switches, sensors, automations via natural language
- **Tool-Calling**: AI can query devices, call services, and create automations automatically
- **Chat UI**: Interactive chat interface directly in the Home Assistant sidebar
- **One-Click Install**: Docker add-on with automatic setup
- **Ingress UI**: Secure integration through Home Assistant ingress

---

## 📋 Requirements

- Home Assistant **2024.1.0+** with Supervisor
- An API key for at least one AI provider (see below)

---

## 🚀 Installation

### 1. Add Repository

In Home Assistant:
```
Settings → Add-ons & backups → Add-on store (⋮) → Repositories
→ Add: https://github.com/Bobsilvio/ha-claude
```

### 2. Install Add-on

```
Settings → Add-ons & backups → Add-on store
→ Search "AI Assistant" → Install
```

### 3. Configure

1. Open the addon **Configuration** tab
2. Select your **AI Provider** from the dropdown
3. Enter the **API key** for your chosen provider (see guide below)
4. (Optional) Select a specific model from the dropdown
5. Save and **Start** the addon

### 4. Access

Once running, click **"AI Assistant"** in the Home Assistant sidebar!

---

## 🔑 Come ottenere le API Key

### 🟠 GitHub Models (Consigliato - Gratis!)

> **37+ modelli** con un solo token. Include GPT-4o, Llama, Mistral, DeepSeek, Grok, Phi-4, Cohere e altri. **Gratis** con limiti di richieste giornaliere.

| Cosa serve | Costo |
|---|---|
| Account GitHub (gratuito) | **$0** |
| GitHub Personal Access Token | **Gratuito** |

**Come ottenere il token:**

1. Vai su **https://github.com/settings/tokens**
2. Clicca **"Generate new token"** → **"Fine-grained token"**
3. Nome: `HA AI Assistant` (o quello che vuoi)
4. Scadenza: scegli la durata che preferisci
5. **Non servono permessi speciali** — il token base basta
6. Clicca **"Generate token"**
7. **Copia il token** (inizia con `github_pat_...`) — non potrai rivederlo

**Configurazione addon:**
- Provider: `github`
- GitHub Token: incolla il token
- GitHub Model: scegli dal dropdown (es. `gpt-4o`, `DeepSeek-R1`, `grok-3`...)

**Modelli disponibili e limiti (free tier):**

| Modello | Richieste/giorno | Tool-calling | Note |
|---|---|---|---|
| `gpt-4o` | 50 | ✅ | Consigliato, ottimi risultati |
| `gpt-4o-mini` | 150 | ✅ | Veloce, ideale per uso frequente |
| `gpt-4.1` / `gpt-4.1-mini` / `gpt-4.1-nano` | 50-150 | ✅ | Nuova generazione |
| `o1` / `o3` / `o3-mini` / `o4-mini` | 8-12 | ✅ | Ragionamento avanzato (Copilot Pro+) |
| `gpt-5` / `gpt-5-mini` / `gpt-5-nano` | 8 | ✅ | Ultimo modello (Copilot Pro+) |
| `Meta-Llama-3.1-405B-Instruct` | 150 | ⚠️ | Meta, open-source |
| `Llama-3.3-70B-Instruct` | 150 | ⚠️ | Meta, veloce |
| `Llama-4-Scout-17B-16E-Instruct` | 150 | ⚠️ | Meta, ultima gen |
| `mistral-small-2503` | 150 | ✅ | Mistral AI, multimodale |
| `mistral-medium-2505` | 150 | ✅ | Mistral AI, avanzato |
| `Cohere-command-r-plus-08-2024` | 150 | ✅ | Cohere, RAG ottimizzato |
| `cohere-command-a` | 150 | ✅ | Cohere, agente |
| `DeepSeek-R1` / `DeepSeek-R1-0528` | 8 | ❌ | Ragionamento (no tool-calling) |
| `DeepSeek-V3-0324` | 8 | ✅ | DeepSeek generativo |
| `Phi-4` / `Phi-4-reasoning` | 150 | ⚠️ | Microsoft, compatti |
| `grok-3` | 15 | ✅ | xAI |
| `grok-3-mini` | 30 | ✅ | xAI, veloce |
| `AI21-Jamba-1.5-Large` | 150 | ✅ | AI21, 256K contesto |

> ⚠️ = tool-calling parziale (il modello potrebbe non gestire correttamente il controllo HA)

---

### 🟣 Anthropic Claude

> Claude Sonnet 4, Opus 4, Haiku 4. Eccelle nell'analisi e nel ragionamento.

| Cosa serve | Costo |
|---|---|
| Account Anthropic | Registrazione gratuita |
| API Key | **A consumo** (pay-per-use) |

**Prezzi indicativi:**
- Claude Haiku 4: ~$0.25 / 1M token input, ~$1.25 / 1M token output
- Claude Sonnet 4: ~$3 / 1M input, ~$15 / 1M output
- Claude Opus 4: ~$15 / 1M input, ~$75 / 1M output

> Per uso domestico (qualche decina di messaggi al giorno), spendi indicativamente **$1-5/mese** con Sonnet.

**Come ottenere la key:**

1. Vai su **https://console.anthropic.com/**
2. Crea un account o accedi
3. Vai su **"API Keys"** nel menu laterale
4. Clicca **"Create Key"**
5. Copia la chiave (inizia con `sk-ant-...`)
6. **Aggiungi credito**: vai su **Billing** → **Add funds** (minimo $5)

**Configurazione addon:**
- Provider: `anthropic`
- Anthropic API Key: incolla la key
- Modello di default: `claude-sonnet-4-20250514`

---

### 🟢 OpenAI (ChatGPT)

> GPT-4o, GPT-4o-mini, o1, o3-mini. Il provider più conosciuto.

| Cosa serve | Costo |
|---|---|
| Account OpenAI | Registrazione gratuita |
| API Key | **A consumo** (pay-per-use) |

**Prezzi indicativi:**
- GPT-4o-mini: ~$0.15 / 1M input, ~$0.60 / 1M output
- GPT-4o: ~$2.50 / 1M input, ~$10 / 1M output

> Per uso domestico, spendi indicativamente **$1-3/mese** con GPT-4o-mini.

**Come ottenere la key:**

1. Vai su **https://platform.openai.com/**
2. Crea un account o accedi
3. Vai su **"API Keys"** → **https://platform.openai.com/api-keys**
4. Clicca **"Create new secret key"**
5. Copia la chiave (inizia con `sk-...`)
6. **Aggiungi credito**: vai su **Billing** → **Add to credit balance** (minimo $5)

> ⚠️ L'API OpenAI è **separata** dall'abbonamento ChatGPT Plus ($20/mese). ChatGPT Plus non dà access all'API.

**Configurazione addon:**
- Provider: `openai`
- OpenAI API Key: incolla la key
- Modello di default: `gpt-4o`

---

### 🔵 Google Gemini

> Gemini 2.0 Flash, Gemini 2.5 Pro. Ha un **free tier generoso**.

| Cosa serve | Costo |
|---|---|
| Account Google | Gratuito |
| API Key | **Gratis** fino a 15 RPM / 1M TPM |

**Come ottenere la key:**

1. Vai su **https://aistudio.google.com/apikey**
2. Accedi con il tuo account Google
3. Clicca **"Create API Key"**
4. Seleziona un progetto Google Cloud (ne crea uno automaticamente se non ne hai)
5. Copia la chiave API

> 🎁 **Free tier**: 15 richieste al minuto, 1 milione di token al minuto, 1500 richieste al giorno — **completamente gratis!**

**Per uso a pagamento (opzionale):**
- Vai su **https://console.cloud.google.com/billing** per abilitare la fatturazione
- Gemini 2.0 Flash: ~$0.10 / 1M input, ~$0.40 / 1M output

**Configurazione addon:**
- Provider: `google`
- Google API Key: incolla la key
- Modello di default: `gemini-2.0-flash`

---

## 🏆 Quale provider scegliere?

| Criterio | Consigliato |
|---|---|
| **Gratis, senza credito** | 🟠 GitHub Models (`gpt-4o-mini`) o 🔵 Google Gemini |
| **Miglior qualità** | 🟣 Anthropic Claude Sonnet 4 |
| **Più modelli diversi** | 🟠 GitHub Models (37+ modelli con 1 token) |
| **Uso intensivo, basso costo** | 🟢 OpenAI GPT-4o-mini |
| **Sperimentare modelli open-source** | 🟠 GitHub Models (Llama, Mistral, DeepSeek) |

---

## ⚙️ Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `ai_provider` | AI provider (anthropic/openai/google/github) | `anthropic` |
| `anthropic_api_key` | Anthropic Claude API key | - |
| `openai_api_key` | OpenAI API key | - |
| `google_api_key` | Google Gemini API key | - |
| `github_token` | GitHub Personal Access Token | - |
| `github_model` | Model selection for GitHub Models | `gpt-4o` |
| `ai_model` | Manual model override (any provider) | auto |
| `api_port` | Backend API port | `5000` |
| `debug_mode` | Enable debug logging | `false` |

---

## 🛠️ Comandi Chat Utili

Una volta avviato, puoi chiedere all'AI:

- **"Stato della casa"** — mostra tutti i dispositivi e sensori
- **"Accendi la luce del salotto"** — controlla i dispositivi
- **"Crea un'automazione che accende le luci al tramonto"** — crea automazioni
- **"Quali automazioni ho attive?"** — elenca le automazioni
- **"Imposta il termostato a 22 gradi"** — regola i dispositivi

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Chat UI |
| `/api/chat` | POST | Send message |
| `/api/status` | GET | Connection diagnostics |
| `/api/health` | GET | Health check |

---

## 🆘 Troubleshooting

### "AI Assistant" non appare nella sidebar
- Riavvia Home Assistant completamente
- Controlla i log dell'addon per errori
- Verifica che l'addon sia in stato "Running"

### Errore 401 su HA API
- Il `SUPERVISOR_TOKEN` viene gestito automaticamente
- Verifica su `/api/status` che `ha_connection_ok` sia `true`
- Riavvia l'addon

### Errore "API key not configured"
- Verifica di aver inserito la chiave corretta nella configurazione addon
- Per Anthropic/OpenAI: assicurati di aver aggiunto credito all'account
- Per GitHub: il token deve essere valido (non scaduto)

### Il modello non risponde / errore provider
- Controlla i limiti di richieste (rate limits) del tuo provider
- GitHub Models free: verifica di non aver superato il limite giornaliero
- Prova un modello diverso

---

## 📝 License

MIT

## 🤝 Support

Issues? Visit: https://github.com/Bobsilvio/ha-claude/issues

---

**Created with ❤️ for Home Assistant**
