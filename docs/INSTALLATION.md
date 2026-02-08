# Installation Guide

Guida completa per installare Claude AI Assistant in Home Assistant.

## Requisiti Minimi

- **Home Assistant**: 2024.1.0 o superiore
- **Python**: 3.11+
- **RAM**: 512 MB minimo, 1 GB recommended
- **Storage**: 500 MB per il componente
- **Network**: Connessione Internet stabile

## Pre-requisiti

### 1. Home Assistant Long-Lived Access Token

1. In Home Assistant, vai a **Settings** → **Developer Tools**
2. Scrollare fino a **Long-Lived Access Tokens**
3. Cliccare **Create Token**
4. Dare un nome significativo ex: "Claude Integration"
5. **Copiare il token** (non è recuperabile dopo)
6. Salvare in luogo sicuro

### 2. Claude API Key (Opzionale)

Se usi i modelli Opus\Sonnet, serve la chiave:

1. Andare su https://console.anthropic.com
2. Creare account o fare login
3. Generare API Key
4. Salvare in .env

## Opzione A: Installazione Manuale

### Step 1: Download Componente

```bash
# Clone o scarica il repository
git clone https://github.com/your-username/ha-claude.git
cd ha-claude
```

### Step 2: Copia Componente

```bash
# macOS/Linux
cp -r custom_components/claude ~/.homeassistant/custom_components/

# Windows (PowerShell)
Copy-Item -Recurse custom_components/claude $env:USERPROFILE\.homeassistant\custom_components\
```

### Step 3: Riavvia Home Assistant

**Via UI:**
- Settings → System → Restart Home Assistant

**Via CLI:**
```bash
# Se usi SSH
ha core restart
```

### Step 4: Aggiungi Integrazione

1. Settings → Devices & Services
2. Cliccare "Create Integration"
3. Cercare "Claude"
4. Selezionare "Claude AI Assistant"
5. Configurare:
   - **API Endpoint**: `http://localhost:5000`
   - **Model**: Selezionare claude-3-haiku, sonnet, opus
   - **Polling Interval**: 60 secondi (di default)
   - **Timeout**: 30 secondi
   - **Max Retries**: 3

### Step 5: Avvia Backend API

```bash
# Opzione 1: Python venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# oppure 'venv\Scripts\activate' per Windows

pip install -r backend/requirements.txt
python backend/api.py
```

## Opzione B: Docker Compose (Recommended)

### Step 1: Preparazione

```bash
# Clone repository
git clone https://github.com/your-username/ha-claude.git
cd ha-claude

# Copia template environment
cp .env.example .env
```

### Step 2: Configura .env

```bash
nano .env  # o usa editor preferito
```

Valori da configurare:
```
HA_URL=http://home-assistant:8123       # URL Home Assistant
HA_TOKEN=your_long_lived_token_here     # Token da Settings
API_PORT=5000                           # Porta API (default)
DEBUG_MODE=False                        # True solo per debug
CLAUDE_MODEL=claude-3-haiku             # Modello iniziale
```

### Step 3: Avvia Stack

```bash
# Build e start
docker-compose up -d

# Verifica stato
docker-compose ps

# Vedi log
docker-compose logs -f claude-api
docker-compose logs -f home-assistant
```

## Opzione C: Hassio Add-on (Futuro)

al momento non disponibile, work in progress.

## Post-Installazione

### Verifica Installazione

1. **Check Integration**: Settings → Devices & Services → Claude
2. **Check Sensors**: Settings → Devices & Services → Entities
3. **Check Logs**: Settings → System → Logs
4. **Test Service**: Developer Tools → Services → claude.send_message

### Configurazione Avanzata

#### Environment Variables (per Backend)

```bash
# .env file
HA_URL=http://localhost:8123
HA_TOKEN=your_token
API_PORT=5000
DEBUG_MODE=False
CLAUDE_MODEL=claude-3-haiku
POLLING_INTERVAL=60
TIMEOUT=30
MAX_RETRIES=3
```

#### Configuration.yaml (Home Assistant)

```yaml
# Opzionale: forzare configurazione
claude:
  api_endpoint: http://localhost:5000
  model: claude-3-haiku
  polling_interval: 60
```

### Troubleshooting Installazione

| Problema | Soluzione |
|----------|-----------|
| "Integration not found" | Riavvia HA, clear cache browser |
| "Cannot connect API" | Verifica HA_TOKEN è corretto |
| "Module not found" | Reinstalla requirements |
| "Port 5000 already in use" | Cambia API_PORT in .env |
| "Timeout error" | Aumenta timeout, non firewall blocca |

### Monitoraggio Post-Setup

```yaml
# Aggiungi al configuration.yaml
group:
  claude_monitoring:
    name: "Claude Monitoring"
    entities:
      - switch.claude_connection
      - sensor.claude_status
      - sensor.claude_entities_count
```

### Performance Tuning

| Parametro | Valore Default | Raccomandazione |
|-----------|---|---|
| Polling Interval | 60s | 30-120s |
| Timeout | 30s | 15-60s |
| Max Retries | 3 | 1-5 |
| API Port | 5000 | 5000+ |

### Backup e Restore

```bash
# Backup
cp -r ~/.homeassistant/custom_components/claude ./backup/

# Restore
cp -r ./backup/claude ~/.homeassistant/custom_components/
```

## Upgrade

```bash
# Pull latest changes
git pull origin main

# Reinstall component
cp -r custom_components/claude ~/.homeassistant/custom_components/

# Riavvia HA
ha core restart
```

## Troubleshooting Generale

### Logs Location

```bash
# HA Logs
~/.homeassistant/home-assistant.log

# API Logs (if running in container)
docker-compose logs claude-api

# API Logs (if running locally)
./logs/api.log
```

### Debug Mode

```bash
# Abilita debug nel .env
DEBUG_MODE=True

# O in configuration.yaml
logger:
  default: info
  logs:
    custom_components.claude: debug
```

### Network Troubleshooting

```bash
# Test connessione
curl http://localhost:5000/health

# Verifica HA token
curl -H "Authorization: Bearer TOKEN" http://localhost:8123/api/

# Check ports
netstat -an | grep 5000
netstat -an | grep 8123
```

## Supporto

- 📖 [API Reference](api_reference.md)
- 🤖 [Automazioni Examples](automations_examples.md)
- 🔧 [Configuration Example](home_assistant_config_example.yaml)
- 🐛 [GitHub Issues](https://github.com/your-username/ha-claude/issues)

---

**Installation complete! Goditi la tua casa intelligente controllata da Claude 🎉**
