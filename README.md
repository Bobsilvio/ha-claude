[![Sample](https://storage.ko-fi.com/cdn/generated/zfskfgqnf/2025-03-07_rest-7d81acd901abf101cbdf54443c38f6f0-dlmmonph.jpg)](https://ko-fi.com/silviosmart)

## Supportami / Support Me

Se ti piace il mio lavoro e vuoi che continui nello sviluppo delle card, puoi offrirmi un caffè.\
If you like my work and want me to continue developing the cards, you can buy me a coffee.


[![PayPal](https://img.shields.io/badge/Donate-PayPal-%2300457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/donate/?hosted_button_id=Z6KY9V6BBZ4BN)

Non dimenticare di seguirmi sui social:\
Don't forget to follow me on social media:

[![TikTok](https://img.shields.io/badge/Follow_TikTok-%23000000?style=for-the-badge&logo=tiktok&logoColor=white)](https://www.tiktok.com/@silviosmartalexa)

[![Instagram](https://img.shields.io/badge/Follow_Instagram-%23E1306C?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/silviosmartalexa)

[![YouTube](https://img.shields.io/badge/Subscribe_YouTube-%23FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@silviosmartalexa)
# 🏠🤖 AI Assistant for Home Assistant

**Smart home AI assistant addon** with multi-provider support — control your home, create automations, and manage configurations using natural language.

Supports **5 AI providers** and **40+ models**: Anthropic Claude, OpenAI, Google Gemini, NVIDIA NIM (free Kimi K2.5), and GitHub Models (GPT, Llama, Mistral, DeepSeek, Grok, Phi, Cohere and more).

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

### 🔧 System Diagnostics & Repairs
- **Read Repairs**: View active HA repair issues and warnings
- **Health Check**: System health diagnostics (unsupported/unhealthy components)
- **AI Suggestions**: AI analyzes issues and suggests concrete fixes
- **Dismiss Issues**: Acknowledge and dismiss resolved repairs

### 👁️ Vision Support *(New in v3.0!)*
- **📸 Image Upload**: Send screenshots, photos, or dashboard images
- **Visual Analysis**: AI can see and understand images
- **Card Recreation**: "Create cards like this image" - AI analyzes and recreates layouts
- **Smart Suggestions**: Show a dashboard, get improvement suggestions
- **Multi-Provider**: Works with Claude, GPT-4o, Gemini vision models

### 📝 Configuration File Access *(New in v2.9)*
- **Read/Write YAML**: Access automations, scripts, scenes, and custom configs
- **File Explorer**: Browse your Home Assistant config directory
- **Safe Editing**: Automatic snapshots before modifications
- **Backup Management**: Restore or delete backups, per-file snapshot limits
- **Config Validation**: Check configuration before applying changes

### 💬 Interactive Chat Interface
- **Chat History**: Keep last 10 conversations, switch between them
- **Streaming Responses**: Real-time token-by-token output
- **Tool Indicators**: See what the AI is doing (badges for each tool call)
- **Copy Button**: One-click copy for all code blocks (YAML, JSON, Python)
- **Persistent Storage**: Conversations survive addon restarts

### 🫧 Floating Chat Bubble
- **Always Available**: AI chat bubble on every Home Assistant page
- **Context-Aware**: Detects automations, scripts, and HTML dashboards
- **HTML Dashboard Editing**: Modify dashboards in-place keeping same style
- **Voice Input**: Built-in voice recognition
- **Agent Switching**: Change AI provider/model on the fly
- **Hidden on Mobile**: Automatically hidden on companion app

### 🌍 Multilingual Support
- **4 Languages**: English, Italian, Spanish, French
- **AI Responses**: AI always responds in your chosen language (v2.9.27)
- **Config UI Translations**: Settings labels and descriptions in all 4 languages (v3.0.2)
- **Fully Localized**: Complete multilingual experience

### 🛠️ Dashboard Creation
- **Lovelace Dashboards**: Create custom dashboards with cards
- **HTML Dashboards**: AI-generated Vue 3 interactive dashboards with real-time data
- **11 Section Types**: Hero, pills, flow, gauge, gauges, kpi, chart, entities, controls, stats, value
- **Live Data**: WebSocket real-time updates with automatic proxy fallback (no browser auth needed)
- **Card Library**: Supports standard and custom cards
- **View Organization**: Multiple views with icons and titles

---

## 📋 Requirements

- **Home Assistant** 2024.1.0+ with Supervisor
- **API Key** for at least one AI provider (see setup guide below)

---

## 🚀 Quick Start
Simply click the button below to add it automatically:

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FBobsilvio%2Fha-claude)

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
2. Paste **at least one provider key** (Anthropic / OpenAI / Google / NVIDIA / GitHub)
3. (Optional) Select **Language**: en, it, es, or fr
4. (Optional) Enable **File Access** to allow config file operations
5. **Save** and **Start** the addon
6. Open **AI Assistant** from the sidebar and pick an **agent/model** from the top dropdown (your choice is saved automatically)

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
1. Paste the **GitHub Token** in the add-on configuration
2. In the chat UI, select **GitHub Models** and choose a model from the dropdown

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
1. Paste the **Anthropic API Key** in the add-on configuration
2. In the chat UI, select **Anthropic** and choose a model from the dropdown

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
1. Paste the **OpenAI API Key** in the add-on configuration
2. In the chat UI, select **OpenAI** and choose a model from the dropdown

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
1. Paste the **Google API Key** in the add-on configuration
2. In the chat UI, select **Google** and choose a model from the dropdown

---

### 🟩 NVIDIA NIM

> OpenAI-compatible API via NVIDIA NIM.

**Get API Key:**
- Create an API key in NVIDIA's developer portal for NIM.

**Configure Addon:**
1. Paste the **NVIDIA API Key** in the add-on configuration
2. In the chat UI, select **NVIDIA NIM** and choose a model from the dropdown

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
| **Anthropic API Key** | Claude API key from console.anthropic.com | - | If using Claude |
| **OpenAI API Key** | OpenAI API key from platform.openai.com | - | If using OpenAI |
| **Google API Key** | Gemini API key from aistudio.google.com | - | If using Gemini |
| **NVIDIA API Key** | NVIDIA NIM API key | - | If using NVIDIA |
| **NVIDIA Thinking Mode** | Enable extra reasoning tokens (when supported) | `false` | ❌ |
| **GitHub Token** | Personal Access Token from GitHub | - | If using GitHub |
| **Language** | AI response language (en/it/es/fr) | `en` | ❌ |
| **Enable File Access** | Allow AI to read/write config files | `false` | ❌ |
| **Chat Bubble** | Floating AI bubble on every HA page (context-aware) | `false` | ❌ |
| **Max Backups per File** | Max backup snapshots per file (oldest auto-deleted) | `5` | ❌ |
| **Max Conversations** | Max chat conversations in history (1-100) | `10` | ❌ |
| **Debug Mode** | Enable detailed logging | `false` | ❌ |
| **Colored Logs** | Emoji indicators in addon logs | `true` | ❌ |
| **Log Level** | Log verbosity (normal/verbose/debug) | `normal` | ❌ |
| **API Port** | Internal API port | `5010` | ❌ |
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
- Restore or delete backups from the UI
- Per-file snapshot limits (configurable, default 5 per file)

**Use cases:**
- "Show me the YAML code for my morning routine automation"
- "List all files in the lovelace folder"
- "Add a condition to automation X checking if Y is on"

---

## 💡 Usage Examples

The AI assistant uses keyword-based intent detection to route your request to the right tools. Below are example phrases that work well, in all supported languages.

### Device Control

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Accendi le luci del soggiorno"* / *"Spegni il climatizzatore"* |
| 🇬🇧 EN | *"Turn on the living room lights"* / *"Set thermostat to 22 degrees"* |
| 🇪🇸 ES | *"Enciende las luces del salón"* / *"Apaga el aire acondicionado"* |
| 🇫🇷 FR | *"Allume les lumières du salon"* / *"Éteins la climatisation"* |

### Query State

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Qual è lo stato della temperatura in camera?"* / *"Quanta energia produce il fotovoltaico?"* |
| 🇬🇧 EN | *"What is the temperature in the bedroom?"* / *"How much power is the solar producing?"* |
| 🇪🇸 ES | *"¿Cuál es la temperatura del dormitorio?"* / *"¿Cuánta energía produce el solar?"* |
| 🇫🇷 FR | *"Quel est l'état de la température dans la chambre?"* / *"Combien d'énergie produit le solaire?"* |

### Create Automation

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Crea un'automazione che accende le luci al tramonto"* / *"Fammi una nuova automazione per la sera"* |
| 🇬🇧 EN | *"Create an automation that turns on lights at sunset"* / *"Make a new automation for the morning routine"* |
| 🇪🇸 ES | *"Crea una automatización que encienda las luces al atardecer"* / *"Haz una nueva automatización para la mañana"* |
| 🇫🇷 FR | *"Crée une automatisation qui allume les lumières au coucher du soleil"* / *"Fais une nouvelle automatisation pour le matin"* |

### Modify Automation

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Modifica l'automazione delle luci del corridoio"* / *"Cambia l'orario dell'automazione serale"* |
| 🇬🇧 EN | *"Modify the hallway lights automation"* / *"Change the schedule of the evening automation"* |
| 🇪🇸 ES | *"Modifica la automatización de las luces del pasillo"* / *"Cambia el horario de la automatización nocturna"* |
| 🇫🇷 FR | *"Modifie l'automatisation des lumières du couloir"* / *"Change l'horaire de l'automatisation du soir"* |

### Create Dashboard (Lovelace)

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Crea una dashboard per l'energia solare"* / *"Fammi un pannello con i sensori di temperatura"* |
| 🇬🇧 EN | *"Create a dashboard for the living room lights"* / *"Build a panel with all temperature sensors"* |
| 🇪🇸 ES | *"Crea un dashboard para la energía solar"* / *"Haz un tablero con los sensores de temperatura"* |
| 🇫🇷 FR | *"Crée un dashboard pour l'énergie solaire"* / *"Fais un tableau de bord avec les capteurs de température"* |

### Create HTML Dashboard (Interactive)

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Crea una dashboard HTML interattiva per il fotovoltaico"* / *"Fammi un pannello web live con i dati energia"* |
| 🇬🇧 EN | *"Create an interactive HTML dashboard for solar monitoring"* / *"Build a responsive web app for energy data"* |
| 🇪🇸 ES | *"Crea un dashboard HTML interactivo para el solar"* / *"Haz una app web responsive con datos de energía"* |
| 🇫🇷 FR | *"Crée un dashboard HTML interactif pour le solaire"* / *"Fais une app web responsive avec les données d'énergie"* |

### History & Statistics

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Mostrami lo storico della temperatura di ieri"* / *"Qual è la media dei consumi dell'ultima settimana?"* |
| 🇬🇧 EN | *"Show me the temperature history from yesterday"* / *"What's the average consumption over the last week?"* |
| 🇪🇸 ES | *"Muéstrame el historial de temperatura de ayer"* / *"¿Cuál es la media de consumo de la última semana?"* |
| 🇫🇷 FR | *"Montre-moi l'historique de température d'hier"* / *"Quelle est la moyenne de consommation de la semaine dernière?"* |

### Scripts

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Crea uno script che accende tutte le luci"* / *"Esegui lo script della routine mattutina"* |
| 🇬🇧 EN | *"Create a script that turns on all lights"* / *"Run the morning routine script"* |
| 🇪🇸 ES | *"Crea un script que encienda todas las luces"* / *"Ejecuta la rutina de la mañana"* |
| 🇫🇷 FR | *"Crée un script qui allume toutes les lumières"* / *"Lance le script de la routine du matin"* |

### Helpers

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Crea un helper input_boolean per la modalità vacanza"* / *"Mostra tutti gli helper"* |
| 🇬🇧 EN | *"Create an input_boolean helper for vacation mode"* / *"List all helpers"* |
| 🇪🇸 ES | *"Crea un helper input_boolean para el modo vacaciones"* / *"Muestra todos los helpers"* |
| 🇫🇷 FR | *"Crée un helper input_boolean pour le mode vacances"* / *"Affiche tous les helpers"* |

### Repairs & Diagnostics

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Ci sono riparazioni o problemi?"* / *"Mostrami la salute del sistema"* |
| 🇬🇧 EN | *"Are there any repairs or issues?"* / *"Show me the system health"* |
| 🇪🇸 ES | *"¿Hay reparaciones o problemas?"* / *"Muéstrame la salud del sistema"* |
| 🇫🇷 FR | *"Y a-t-il des réparations ou problèmes?"* / *"Montre-moi la santé du système"* |

### Delete

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Elimina l'automazione 'vecchia routine'"* / *"Cancella la dashboard energia"* |
| 🇬🇧 EN | *"Delete the automation 'old routine'"* / *"Remove the energy dashboard"* |
| 🇪🇸 ES | *"Elimina la automatización 'rutina vieja'"* / *"Borra el dashboard de energía"* |
| 🇫🇷 FR | *"Supprime l'automatisation 'ancienne routine'"* / *"Efface le dashboard énergie"* |

### Configuration Files *(requires File Access enabled)*

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *"Mostrami il file configuration.yaml"* / *"Elenca i file nella cartella config"* |
| 🇬🇧 EN | *"Show me the configuration.yaml file"* / *"List files in the config folder"* |
| 🇪🇸 ES | *"Muéstrame el archivo configuration.yaml"* / *"Lista los archivos en la carpeta config"* |
| 🇫🇷 FR | *"Montre-moi le fichier configuration.yaml"* / *"Liste les fichiers dans le dossier config"* |

### Vision / Image Upload

| Language | Example |
|----------|---------|
| 🇮🇹 IT | *📸 Carica un'immagine, poi chiedi: "Ricrea queste card per i miei sensori"* |
| 🇬🇧 EN | *📸 Upload an image, then ask: "Recreate these cards for my sensors"* |
| 🇪🇸 ES | *📸 Sube una imagen, luego pregunta: "Recrea estas tarjetas para mis sensores"* |
| 🇫🇷 FR | *📸 Télécharge une image, puis demande: "Recrée ces cartes pour mes capteurs"* |

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
| `/api/snapshots` | GET | List backup snapshots |
| `/api/snapshots/<id>` | DELETE | Delete a backup snapshot |
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
- GitHub Models free tier has daily limits (check the GitHub Models dashboard / provider docs)
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
