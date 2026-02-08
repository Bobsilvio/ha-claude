# 🚀 Guida Installazione Finale - Opzione B (Add-on)

## Quello che hai scelto

**Opzione B: Add-on All-in-One (Opzione A evoluta!)**

- ✅ **Add-on installa automaticamente** il componente Claude
- ✅ Backend API gestito automaticamente da Home Assistant come Add-on (Docker)
- ✅ **Un solo step di installazione**: installa l'addon = tutto fatto
- ✅ Auto-restart su reboot
- ✅ Niente script Python manuali
- ✅ Perfetto per il tuo setup PC

## Architettura

```
TUO PC
├── Home Assistant (port 8123)
│   └── Claude Add-on (Docker)
│       ├── Component Claude (copiato automaticamente)
│       └── API Flask Backend (automatic)
└── File system
    ├── ~/.homeassistant/custom_components/claude/ (auto-installed)
    └── automations.yaml (modificato da Claude)
```

**NO component manuale!** L'addon fa tutto da solo! 🚀

## Fase 1: Preparazione HA (una volta)

Non serve preparare niente! Tutto è già nel repo `ha-claude`.

Quando aggiungerai il repository GitHub in Home Assistant, HA troverà:
- ✅ Il componente (in `custom_components/`)
- ✅ L'addon (in `addons/`)
- ✅ Il repository.json (che dice a HA che è un repo di addon)

## Fase 2: Installazione Home Assistant

## Fase 2: Aggiungi Repository HA (5 min)

**L'addon installerà automaticamente il component!**

Nel tuo Home Assistant:

1. **Settings** → **Add-ons & backups** → **Add-on store** (icona in alto destra)
2. Click al menu **⋮** (tre punti) in alto a destra
3. **Repositories**
4. Aggiungi: `https://github.com/Bobsilvio/ha-claude`
5. **Create**
6. Chiudi la finestra

Dovrebbe apparire "Claude AI Backend" nel store!

## Fase 3: Aggiungi Repository Add-on

Nel tuo Home Assistant:

1. **Settings** → **Add-ons & backups** → **Add-on store**
2. Click al menu ⋮ (tre punti) in alto a destra
3. **Repositories**
4. Aggiungi: `https://github.com/Bobsilvio/ha-claude-addon-repo`
5. Click **Create**
6. Chiudi la finestra

Dovrebbe apparire "Claude AI Backend" nel store!

## Fase 4: Installa e Configura Add-on

Nel tuo Home Assistant:

1. **Settings** → **Add-ons & backups** → **Add-ons**
2. Cerca **"Claude AI Backend"**
3. Click sul risultato
4. Click **Install**
5. Aspetta (estrae il docker image - 1-2 minuti)

### 4.1 Configura Add-on

1. Tab **Configuration**
2. Devi aggiungere il tuo **Home Assistant Token**:
   - Settings → Developer Tools
   - Scorri al fondo: **Long-lived Access Tokens**
   - Click **Create Token**
   - Nome: "Claude Backend"
   - Click **Create**, copia il token
3. In Add-on Config, incolla il token nel campo `ha_token`
4. Click **Save**

### 4.2 Avvia Add-on

1. Tab **Info**
2. Click **Start**
3. **Guarda i log** per il progresso:
   ```
   Starting Claude Backend API Add-on...
   ✓ Component deployed to /homeassistant/custom_components/claude
   ✓ Home Assistant is ready
   ✓ Home Assistant reloaded successfully
   ✓ Claude AI Backend is ready!
   ```
4. Quando finisce: Status diventa **"Running"** (verde) ✅

**Cosa è successo automaticamente**:
- ✓ Component copied a `custom_components/claude/`
- ✓ Home Assistant reloaded
- ✓ API started on port 5000

## Fase 5: Configura Claude Integration

#### Nel tuo Home Assistant:

1. **Settings** → **Devices & Services** → **Integrations**
2. Click **Create Integration**
3. Cerca **"Claude"**
4. Click sul risultato
5. **API Endpoint**: `http://localhost:5000`
6. **Model**: Seleziona il tuo modello preferito (Haiku/Sonnet/Opus)
7. Click Submit

### Se vedi errore "Cannot connect":

**Check 1**: Add-on è running?
- Settings → Add-ons → Claude AI Backend → Status = Running (verde)?

**Check 2**: Test manuale:
- Apri browser: `http://localhost:5000/health`
- Dovrebbe mostrare: `{"status": "ok"}`

**Check 3**: Log Add-on:
- Settings → Add-ons → Claude AI Backend → Logs
- Cerca errori

## Fase 6: Usa i Servizi

Ora puoi usare tutti i servizi Claude!

### Esempio semplice:
```yaml
# Nel automations.yaml oppure in uno script
service: claude.send_message
data:
  message: "Accendi tutte le luci del soggiorno"
```

### Creare automazioni dinamicamente:
```yaml
service: claude.create_automation
data:
  automation_name: "Sunset lights"
  description: "Accendi luci al tramonto"
  trigger: '{"platform": "sun", "event": "sunset"}'
  condition: '{"condition": "state", "entity_id": "sun.sun", "state": "below_horizon"}'
  action: '[{"service": "light.turn_on", "target": {"entity_id": "light.living_room"}}]'
```

## ⏱️ Tempo Totale

```
Add Repository:     5 min
Install Add-on:     7 min (Docker image)
Configure Integ:    2 min
Test:               2 min
────────────────────────
TOTALE:            16 minuti
```

**Boom! Tutto pronto! 🚀**

## Risoluzione Problemi

### Add-on non appare nello Store

```
1. Verifica URL repository sia esatto
2. Vai: Settings → System → Updates → Check for updates
3. Se ancora non c'è, riavvia HA
```

### "Cannot connect to API" in Chrome

- Non visitare la UI da browser! È per HA solo
- Controlla che Add-on sia "Running"
- Controlla i log dell'Add-on

### Add-on si ferma subito

```
Check Log:
- Settings → Add-ons → Claude AI Backend → Logs
- Cerca qual è l'errore
- 99% è il token errato/mancante
```

### Backend non raggiunge Home Assistant

```
In Add-on Config, lascia: ha_url = http://homeassistant:8123
(Questo è il DNS interno di HA per Docker)
```

## Comportamento Atteso

✅ **Add-on riavvia automaticamente** se PC si riavvia  
✅ **Componente è disponibile** dopo riavvio HA  
✅ **Automazioni salvate** in `automations.yaml`  
✅ **Servizi disponibili** in Settings → Automazioni → Servizi  

## Prossimi Passi

1. Crea prime automazioni personalizzate
2. Sperimenta con diversi modelli (Haiku vs Sonnet)
3. Usa `claude.create_automation` per creare automazioni dinamicamente
4. Se vuoi condividere con altri: Pubblica il tuo repo con `README.md` aggiornato

## Supporto

- Documenti: [docs/](docs/)
- API Reference: [docs/API_REFERENCE.md](docs/api_reference.md)
- Creating Automations: [docs/CREATING_AUTOMATIONS.md](docs/CREATING_AUTOMATIONS.md)
- Backend API: [docs/BACKEND_API_EXPLAINED.md](docs/BACKEND_API_EXPLAINED.md)

---

**Buon divertimento! 🎉**

Se trovi bug o miglioramenti: GitHub Issues!
