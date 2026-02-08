# 🏠🤖 Claude AI for Home Assistant

All-in-one Home Assistant integration - Control your smart home with Claude Haiku, Sonnet, or Opus.

**Installation**: 16 minutes | **Setup**: Ultra-simple | **Auto-update**: On reboot ✅

Integrazione Home Assistant completa per controllare la tua casa intelligente con Claude Haiku 4.5, Sonnet o Opus.

## 🎯 Caratteristiche Principali

- **Multi-modello Claude**: Haiku (veloce), Sonnet (bilanciato), Opus (potente)
- **Controllo completo**: Luci, automazioni, script, sensori, climate
- **Config Flow UI**: Interfaccia di configurazione intuitiva
- **Sensori di monitoraggio**: Stato della connessione, conteggio entità/automazioni/script
- **6 servizi avanzati**:
  - Invia messaggi a Claude
  - Esegui automazioni
  - Esegui script con variabili
  - Ottieni stato entità
  - Chiama servizi Home Assistant
  - **Crea automazioni dinamicamente** ✨ NEW
- **Backend Flask**: API REST completa verso Home Assistant
- **Docker Support**: Docker Compose per setup facile
- **Documentazione completa**: In italiano e inglese

## 📋 Requisiti

- Home Assistant 2024.1.0+
- Python 3.11+
- API Token Home Assistant
- Chiave API Anthropic Claude

## 🚀 Quick Start - Add-on (CONSIGLIATO - 2 minuti!)

**All-in-One: Component + Backend Automatico**

1. **Aggiungi Repository**:
   - Settings → Add-ons & backups → Add-on store (⋮) → Repositories
   - Aggiungi: `https://github.com/Bobsilvio/ha-claude`
   - Crea

2. **Installa Add-on**:
   - Cerca "Claude AI Backend"
   - Click Installa

3. **Configura Add-on**:
   - Vai su "Configurazione"
   - Aggiungi il tuo Home Assistant Token (Settings → Developer Tools → Long-lived Access Tokens)
   - Salva

4. **Avvia Add-on**:
   - Click "Avvia"
   - L'addon installa automaticamente il component e avvia l'API
   - ✅ Pronto!

5. **Configura Integrazione**:
   - Settings → Devices & Services → Crea Integrazione
   - Cerca "Claude"
   - API Endpoint: `http://localhost:5000`
   - Seleziona modello
   - Pronto!

## 🚀 Quick Start - Component Standalone (5 minuti)

**Per chi preferisce installazione manuale (no add-ons)**

1. **Scarica i file**:
   ```bash
   git clone https://github.com/Bobsilvio/ha-claude.git
   cd ha-claude
   ```

2. **Copia il componente**:
   ```bash
   cp -r custom_components/claude ~/.homeassistant/custom_components/
   ```

3. **Avvia il backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python api.py
   ```

4. **Riavvia Home Assistant**

5. **Configura**:
   - Settings → Devices & Services → Create Integration
   - Cerca "Claude"
   - API Endpoint: `http://localhost:5000`
   - Seleziona modello

## 📦 Installazione Completa

Vedi [INSTALLATION.md](docs/INSTALLATION.md) per istruzioni dettagliate e [ADDON_SETUP.md](ADDON_SETUP.md) per creare il tuo repository Add-ons.

## 🔧 Configurazione

### Config Flow UI

1. **API Endpoint**: URL del backend Flask (default: http://localhost:5000)
2. **Modello**: claude-3-haiku, claude-3-sonnet, claude-3-opus
3. **Polling Interval**: Secondi tra gli aggiornamenti (default: 60)
4. **Timeout**: Timeout richieste API in secondi (default: 30)
5. **Max Retries**: Tentativi per richieste fallite (default: 3)

### Environment Variables

```bash
HA_URL=http://localhost:8123
HA_TOKEN=your_home_assistant_token
API_PORT=5000
CLAUDE_MODEL=claude-3-haiku
```

## 📚 Documentazione

- [API Reference](docs/api_reference.md) - Tutti gli endpoint API
- [Automazioni Examples](docs/automations_examples.md) - Template di automazione
- [Creating Automations](docs/CREATING_AUTOMATIONS.md) - **Crea automazioni dinamicamente** ✨ NEW
- [Docker vs Component](docs/DOCKER_VS_COMPONENT.md) - Quali sono le differenze?
- [HA Config Example](docs/home_assistant_config_example.yaml) - Config HA di esempio
- [Quick Start](QUICK_START.md) - Setup veloce
- [Installation](docs/INSTALLATION.md) - Guida completa

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
```yaml
service: claude.call_service
data:
  s

### claude.create_automation ✨ NEW
```yaml
service: claude.create_automation
data:
  automation_name: "Turn on lights at sunset"
  description: "Automatically turn on living room lights"
  trigger: '{"platform": "sun", "event": "sunset"}'
  condition: '{"condition": "state", "entity_id": "binary_sensor.people_home", "state": "on"}'
  action: '[{"service": "light.turn_on", "target": {"entity_id": "light.living_room"}}]'
```ervice: "light.turn_on"
  data: '{"entity_id": "light.living_room", "brightness": 255}'
```

## 🐳 Docker

```bash
# Setup
cp .env.example .env
# Configura il CLAUDE_MODEL desiderato in .env

# Run
docker-compose up -d

# Logs
docker-compose logs -f claude-api
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
