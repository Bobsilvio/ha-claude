# Quick Start - 5 minuti

## Passo 1: Preparazione (1 min)

### Requisiti
- Home Assistant running
- Home Assistant API Token (Settings → Developer Tools → Long-lived access tokens)
- Componente Claude scaricato

### File necessari
```
ha-claude/
├── custom_components/claude/
├── backend/
└── .env.example
```

## Passo 2: Setup Quick (2 min)

### Opzione A: Setup Manuale

1. **Copia il componente**:
   ```bash
   cp -r custom_components/claude ~/.homeassistant/custom_components/
   ```

2. **Riavvia Home Assistant**:
   - Settings → System → Restart

### Opzione B: Setup Docker

1. **Configura .env**:
   ```bash
   cp .env.example .env
   nano .env
   # Inserisci HA_TOKEN e scegli CLAUDE_MODEL
   ```

2. **Avvia stack**:
   ```bash
   docker-compose up -d
   ```

## Passo 3: Configurazione (1 min)

1. **Home Assistant UI**:
   - Settings → Devices & Services → Create Integration
   - Cerca "Claude"
   - Seleziona "Claude AI Assistant"

2. **Config Flow**:
   - **API Endpoint**: `http://localhost:5000` (se locale)
   - **Modello**: claude-3-haiku (veloce) / sonnet (bilanciato) / opus (potente)
   - **Polling Interval**: 60 secondi
   - **Clicca Submit**

## Passo 4: Primo Utilizzo (1 min)

### Verifica installazione

1. **Vai a Developer Tools → Services**

2. **Prova il servizio**:
   ```yaml
   Service: claude.send_message
   Data:
     message: "Quante luci ho in casa?"
     context: "Home automation query"
   ```

3. **Guarda l'output** in Settings → System → Logs

### Crea una semplice automazione

```yaml
automation:
  - id: "test_claude"
    alias: "Test Claude"
    trigger:
      platform: time
      at: "10:00:00"
    action:
      - service: claude.get_entity_state
        data:
          entity_id: "light.living_room"
```

## Passo 5: Primi Comandi (opzionale)

### Accendi luci
```yaml
service: claude.call_service
data:
  service: "light.turn_on"
  data: '{"entity_id": "light.living_room", "brightness": 255}'
```

### Esegui automazione
```yaml
service: claude.execute_automation
data:
  automation_id: "automation.your_automation"
```

### Esegui script
```yaml
service: claude.execute_script
data:
  script_id: "script.your_script"
  variables: '{"temperature": 22}'
```

## Troubleshooting rapido

| Problema | Soluzione |
|----------|-----------|
| "Cannot connect" | Verifica HA_TOKEN in .env |
| "Module not found" | Riavvia Home Assistant |
| "API timeout" | Aumenta timeout nelle opzioni |
| "Model not available" | Verifica nome modello |

## Prossimi passi

- Leggi [INSTALLATION.md](docs/INSTALLATION.md) per setup avanzato
- Vedi [api_reference.md](docs/api_reference.md) per tutti gli endpoint
- Consulta [automations_examples.md](docs/automations_examples.md) per template
- Configura trigger vocali con Home Assistant

## 📚 Documentazione

- [Installation Guide](docs/INSTALLATION.md) - Setup completo
- [API Reference](docs/api_reference.md) - Endpoint API
- [Automations Examples](docs/automations_examples.md) - Template ready-to-use
- [Configuration Example](docs/home_assistant_config_example.yaml) - Config HA

## 💡 Tips

- Inizia con claude-3-haiku per test veloci
- Usa il logging per debuggare problemi
- Monitora con i sensori integrati
- Testa con Developer Tools → Services prima di automatizzare

---

**Fatto! La tua integrazione Claude è pronta! 🎉**

Domande? Vedi [README.md](README.md) per informazioni complete.
