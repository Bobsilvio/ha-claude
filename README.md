# 🏠🤖 Claude AI for Home Assistant

**Integrazione All-in-One** - Controlla la tua casa intelligente con Claude (Haiku, Sonnet, Opus).

> ⏱️ **Installation**: 16 minuti | 🔧 **Setup**: Ultra-semplice | 🔄 **Auto-restart**: Sì ✅

Integrazione Home Assistant completa per controllare la tua casa intelligente con Claude Haiku 4.5, Sonnet o Opus.

## 🎯 Caratteristiche Principali

- **Multi-modello Claude**: Haiku ⚡⚡⚡ (veloce), Sonnet ⚡⚡ (bilanciato), Opus ⚡ (potente)
- **Controllo completo**: Luci, automazioni, script, sensori, climate
- **Config Flow UI**: Interfaccia di configurazione intuitiva in italiano
- **Sensori di monitoraggio**: Stato connessione, conteggio entità/automazioni/script
- **6 Servizi avanzati**:
  - `claude.send_message` - Invia messaggi a Claude
  - `claude.execute_automation` - Esegui automazioni
  - `claude.execute_script` - Esegui script con variabili
  - `claude.get_entity_state` - Leggi stato entità
  - `claude.call_service` - Chiama servizi Home Assistant
  - `claude.create_automation` - **Crea automazioni dinamicamente** ✨
- **Docker + Add-on**: Setup automatico con auto-restart su reboot
- **Documentazione completa**: In italiano e inglese

## 📋 Requisiti

- Home Assistant **2024.1.0+**
- Python 3.11+
- API Token Home Assistant (Settings → Developer Tools → Long-lived Access Tokens)
- Chiave API Anthropic Claude

## 🚀 Quick Start (16 minuti)

### 1️⃣ Aggiungi Repository (5 min)

Nel tuo Home Assistant:

```
Settings → Add-ons & backups → Add-on store (⋮) → Repositories
→ https://github.com/Bobsilvio/ha-claude → Create
```

Dovrebbe apparire "Claude AI Backend" nello store!

### 2️⃣ Installa Add-on (7 min)

```
Settings → Add-ons & backups → Add-on store
→ Cerca "Claude AI Backend" → Install
```

**Questo installa automaticamente:**
- ✅ Component Claude
- ✅ Backend API Flask
- ✅ Tutto quello che serve

### 3️⃣ Configura Add-on

Nel tab **Configuration** dell'add-on:
- Copia il tuo HA Token (Settings → Developer Tools → Long-lived Access Tokens)
- Incollalo nel campo `ha_token`
- **Save**

### 4️⃣ Avvia Add-on (2 min)

Nel tab **Info**:
- Click **Start**
- Guarda i log per il progresso
- Quando Status = "Running" ✅ → È pronto!

### 5️⃣ Configura Integrazione (2 min)

```
Settings → Devices & Services → Create Integration
→ Cerca "Claude" → Configura:
  - API Endpoint: http://localhost:5000
  - Modello: claude-3-haiku (o sonnet/opus)
  - Save
```

✅ **Done!** La tua integrazione Claude è attiva!

## 📦 Alternative di Installazione

### Con Docker Compose (per sviluppatori)

```bash
git clone https://github.com/Bobsilvio/ha-claude.git
cd ha-claude
cp .env.example .env

# Configura in .env:
# - HA_TOKEN=your_token
# - HA_URL=http://localhost:8123
# - CLAUDE_MODEL=claude-3-haiku

docker-compose up -d
```

### Manuale (no Add-on, no Docker)

```bash
# 1. Copia component
cp -r custom_components/claude ~/.homeassistant/custom_components/

# 2. Avvia backend
cd backend
pip install -r requirements.txt
python api.py &

# 3. Riavvia Home Assistant
# 4. Configura integrazione (vedi step 5 sopra)
```

Vedi [docs/INSTALLATION.md](docs/INSTALLATION.md) per istruzioni dettagliate.

## 🔧 Configurazione

### Config Flow

La configurazione è facile tramite l'interfaccia visuale:

1. **API Endpoint**: URL del backend Flask (default: `http://localhost:5000`)
2. **Modello**: Scegli tra:
   - `claude-3-haiku` - ⚡ veloce, economico (perfetto per task semplici)
   - `claude-3-sonnet` - ⚡⚡ equilibrato (perfetto per la maggior parte dei task)
   - `claude-3-opus` - ⚡⚡⚡ potente (per task complessi)
3. **Polling Interval**: Secondi tra gli aggiornamenti (default: 60)
4. **Timeout**: Timeout richieste API in secondi (default: 30)
5. **Max Retries**: Tentativi per richieste fallite (default: 3)

### Environment Variables (Docker/Manuale)

```bash
HA_URL=http://localhost:8123         # Home Assistant URL
HA_TOKEN=your_long_lived_token       # HA Token
API_PORT=5000                         # Backend port
CLAUDE_MODEL=claude-3-haiku          # Modello Claude
DEBUG_MODE=false                      # Abilita debug log
```

## 📚 Documentazione

| Documento | Descrizione |
|-----------|------------|
| [QUICK_START.md](QUICK_START.md) | Setup veloce (5 min) |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Guida completa |
| [docs/api_reference.md](docs/api_reference.md) | Tutti gli API endpoint |
| [docs/BACKEND_API_EXPLAINED.md](docs/BACKEND_API_EXPLAINED.md) | Architettura sistema |
| [docs/CREATING_AUTOMATIONS.md](docs/CREATING_AUTOMATIONS.md) | Come creare automazioni dinamiche |
| [docs/automations_examples.md](docs/automations_examples.md) | Template pronti all'uso |

## 🎮 Servizi Disponibili

### claude.send_message
```yaml
service: claude.send_message
data:
  message: "Messaggio per Claude"
  context: "Contesto aggiuntivo (opzionale)"
```

### claude.execute_automation
```yaml
service: claude.execute_automation
data:
  automation_id: "automation.my_automation"
```

### claude.execute_script
```yaml
service: claude.execute_script
data:
  script_id: "script.my_script"
  variables: '{"temperature": 22, "brightness": 100}'
```

### claude.get_entity_state
```yaml
service: claude.get_entity_state
data:
  entity_id: "light.living_room"
```

### claude.call_service
Chiama qualsiasi servizio Home Assistant.

```yaml
service: claude.call_service
data:
  service: "light.turn_on"
  data: '{"entity_id": "light.living_room", "brightness": 255}'
```

### claude.create_automation ✨ NEW
Crea automazioni dinamicamente tramite Claude!

```yaml
service: claude.create_automation
data:
  automation_name: "Turn on lights at sunset"
  description: "Accendi le luci al tramonto"
  trigger: '{"platform": "sun", "event": "sunset"}'
  condition: '{"condition": "state", "entity_id": "input_boolean.people_home", "state": "on"}'
  action: '[{"service": "light.turn_on", "target": {"entity_id": "light.living_room"}}]'
```

## 🐳 Docker

```bash
# Setup
cp .env.example .env
# Configura il CLAUDE_MODEL desiderato in .env

# Run
docker-compose up -d

# Logs
docker-compose logs -f claude-backend
```

## 🧪 Testing

```bash
# Install dependencies
pip install -r tests/requirements.txt

# Run tests
pytest tests/

# Test API endpoints
python test_api.py
```

## 📊 Sensori

- **claude_status**: Stato connessione (connected/disconnected)
- **claude_entities_count**: Numero entità disponibili
- **claude_automations_count**: Numero automazioni
- **claude_scripts_count**: Numero script

## 🔌 Switch

- **claude_connection**: Attiva/Disattiva connessione all'API

## 🌐 Modelli Supportati

| Modello | Velocità | Costo | Caso d'uso |
|---------|----------|-------|----------|
| claude-3-haiku | ⚡⚡⚡ | Basso | Real-time, task semplici |
| claude-3-sonnet | ⚡⚡ | Medio | Balance ideale |
| claude-3-opus | ⚡ | Alto | Task complessi |

## 📝 Esempi di Utilizzo

### Scena automatica vocale
```yaml
automation:
  - id: "claude_voice_scene"
    trigger:
      platform: conversation
      command: "Claude, accendi la modalità serata"
    action:
      - service: claude.send_message
        data:
          message: "Attiva scena serata"
          context: "Home Assistant scene"
```

### Controllo temperatura intelligente
```yaml
automation:
  - id: "claude_smart_temp"
    trigger:
      platform: time
      at: "18:00:00"
    action:
      - service: claude.call_service
        data:
          service: "climate.set_temperature"
          data: '{"entity_id": "climate.living_room", "temperature": 21}'
```

## 🔒 Sicurezza

- Usa token Home Assistant sicuri
- Configura firewall per il backend API
- Non esporre il backend su internet senza SSL/TLS
- Usa password forti per Home Assistant

## 🐛 Troubleshooting

### "Cannot connect to API"
- Verifica che il backend sia in esecuzione
- Controlla l'URL dell'endpoint
- Verifica la connettività di rete

### "Model not found"
- Controlla che il modello sia disponibile nel tuo account Anthropic
- Verifica il nome del modello nelle impostazioni

### "Timeout error"
- Aumenta il valore di timeout nelle opzioni
- Controlla la latenza di rete

## 📄 Licenza

MIT License - vedi [LICENSE](LICENSE)

## 🤝 Contribuire

Contribuzioni benvenute! Vedi [CONTRIBUTION.md](CONTRIBUTION.md)

## 📞 Supporto

- [GitHub Issues](https://github.com/Bobsilvio/ha-claude/issues)
- [Home Assistant Community](https://community.home-assistant.io/)

## 🎉 Ringraziamenti

- Home Assistant team
- Anthropic per Claude
- Comunità Home Assistant

---

**Creato con ❤️ per controllare la casa intelligente con IA**
