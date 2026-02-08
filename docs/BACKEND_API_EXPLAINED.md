# Backend API - Come Funziona?

## 🎯 Domanda Chiave
**"In che senso il backend API va avviato manualmente?"**

Ottima domanda! Ti spiego chiaramente.

---

## 📊 Overview

### Architettura

```
┌─────────────────────────────────────────────────┐
│ Home Assistant                                  │
│ ┌────────────────────────────────────────────┐ │
│ │ Claude Integration (Custom Component)      │ │
│ │ ↓ (chiama API)                             │ │
│ └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
         ↓ HTTP request
┌─────────────────────────────────────────────────┐
│ Backend API (Flask)                             │
│ - http://localhost:5000                         │
│ - Comunica con Home Assistant API              │
│ - Processa richieste da Claude                 │
└─────────────────────────────────────────────────┘
         ↓ REST calls
┌─────────────────────────────────────────────────┐
│ Home Assistant API (localhost:8123)             │
│ - Controllato dal Backend                      │
│ - Accende luci, esegue script, etc             │
└─────────────────────────────────────────────────┘
```

---

## ❓ Cosa Significano "Manualmente"?

### Docker Compose (Automatico)
```bash
$ docker-compose up -d

✅ Orchestrates tutto automaticamente:
  - Avvia Home Assistant container
  - Avvia Backend API container
  - Configurazione networking
  - Tutto connesso e pronto
```

### Custom Component (Manuale)

```bash
# 1. Installi il componente
$ cp -r custom_components/claude ~/.homeassistant/custom_components/

# 2. Riavvii HA
$ ha core restart

# 3. Configuri in HA UI
# Settings → Integrations → Claude

# 4. DI PERSONA AVVII L'API Backend ← "MANUALE"
$ python backend/api.py    # ← Tu avvii questo!
# oppure in Docker se vuoi
$ docker run -p 5000:5000 claude-api

# 5. Ora il componente può comunicare con l'API
#    Sono SEPARATI - non orchestrati
```

---

## 🔄 Il Flusso

### Scenario 1: Custom Component + API Locale

```
Step 1: Install
$ cp -r custom_components/claude ~/.homeassistant/custom_components/
$ ha core restart

Step 2: Start API (separate process)
$ python backend/api.py
→ API listening on http://localhost:5000

Step 3: Configure in HA
Claude Integration tries to connect to http://localhost:5000
↓
✅ "Cannot connect" → API not running ❌

Step 4: Use
Claude Integration ← sends message →  Backend API
                                       ↓
                                   HA API (8123)
                                       ↓
                                   Turns on lights
```

### Scenario 2: Docker Compose (All Automatic)

```
Step 1: Configure
$ cp .env.example .env
$ nano .env  # set HA_TOKEN

Step 2: Start (docker-compose handles it)
$ docker-compose up -d
→ Starts HA container
→ Starts Claude-API container
→ Networking configured
→ All automatic!

Step 3: Configure in HA UI (automatic)
Claude Integration automatically connects to http://claude-api:5000
(docker network DNS resolution)

Step 4: Use
(Same as above)
```

---

## 🚗 Analogia

Pensa a un **Taxi Service**:

### Custom Component = Taxi ordering system
```
Cliente (HA) ordina un taxi (Backend API)
Ma deve DIRE al taxi dove andare!
Il taxi non viene da solo - DEVE essere in servizio
```

È come:
- ✅ Install app taxi sul tuo telefono (HA + component)
- ⚠️ Ma il taxi (API) **non è automaticamente in servizio**
- 🚗 Tu CHIAMI il taxi e dici "avviati!" (manualmente start API)
- ✅ Poi puoi ordinarlo

### Docker Compose = Taxi company with dispatcher
```
La centrale (docker-compose) gestisce TUTTO
Quando chiedi un taxi (ordine) arriva subito
Ha tutto preconfigurato
```

---

## 📍 Dove Avvio l'API?

### Opzione 1: Locale (stesso host di HA)

```bash
# Terminal 1: Home Assistant
$ homeassistant --open-ui

# Terminal 2: Backend API
$ cd /path/to/ha-claude/backend
$ python api.py
→ Running on http://127.0.0.1:5000

# HA Component settings:
# API Endpoint: http://localhost:5000  ← funziona sulla stessa macchina
```

### Opzione 2: Server Remoto

```bash
# Remote server (es: VPS, Raspberry, altro host)
$ ssh user@192.168.1.100
$ python api.py
→ Running on http://0.0.0.0:5000

# HA Component settings:
# API Endpoint: http://192.168.1.100:5000  ← punta a remoto
```

### Opzione 3: Docker Container (raccomandato)

```bash
# Build image
$ docker build -t claude-api ./backend

# Run container
$ docker run -p 5000:5000 \
  -e HA_URL=http://192.168.1.50:8123 \
  -e HA_TOKEN=your_token \
  claude-api

# HA Component settings:
# API Endpoint: http://192.168.1.50:5000  ← container on same network
```

### Opzione 4: Docker Compose (più facile)

```bash
# Tutto orchestrato
$ docker-compose up -d

# Automaticamente:
# - HA container on :8123
# - API container on :5000
# - Network configured
# - Ready to use!
```

---

## ⚠️ Errori Comuni

### Errore 1: "Cannot connect to API"

```
❌ Problema: Api.py non è avviato

Soluzione:
1. Verifica che api.py sia in running
   $ curl http://localhost:5000/health
   
2. Se no, avvia:
   $ python backend/api.py
   
3. Aspetta 2 secondi e riprova HA config flow
```

### Errore 2: "API running ma HA non lo raggiunge"

```
❌ Problema: Firewall/networking

Soluzione:
1. Dalla macchina di HA, testa:
   $ curl http://api-ip:5000/health
   
2. Se timeout: firewall blocca
   - Apri porta 5000
   - O avvia API nello stesso host

3. Se "connection refused": API non in listening
   $ python backend/api.py
```

### Errore 3: "API connecting but HA operations fail"

```
❌ Problema: HA_TOKEN non valido nell'API

Soluzione:
1. In backend/.env configura:
   HA_URL=http://homeassistant.local:8123
   HA_TOKEN=your_long_lived_token  ← controlla
   
2. Restart API:
   $ pkill -f "python backend/api.py"
   $ python backend/api.py
```

---

## 🎯 Summary

### Custom Component Flow

**"Manualmente" significa che:**

```
Tu (User) devi gestire 2 step SEPARATI:

1. Install component (automatico)
   cp -r custom_components/...
   
2. Start API (tu fai!)
   python api.py  ← TU FAI QUESTO!
   
Non è orchestrato come Docker Compose
```

### Home Assistant Component
```
Does NOT include the Backend API
È solo il "connettore" a HA
Comunica con un'API esterna
```

### Backend API
```
È a HA Service REST
Riceve richieste dal componente
Comunica con HA interno tramite token
```

---

## 🚀 Consiglio

### Per User Normali
```
Usa Docker Compose! ✅
docker-compose up -d
↓
Tutto automatico, niente "manuale"
```

### Per Developers
```
Usa Custom Component + API locale ✅
python backend/api.py
↓
Sviluppi il backend separatamente
Testi componente indipendentemente
```

---

## 📋 Checklist Troubleshooting

- [ ] HA è in running su :8123
- [ ] API è in running su :5000
- [ ] Firewall non blocca porta 5000
- [ ] .env ha HA_TOKEN valido
- [ ] HA Component API Endpoint è corretto
- [ ] curl http://localhost:5000/health ritorna 200

---

**In sintesi: "Manualmente" = tu avvii il processo API, non è auto-orchestrato come Docker** 🎯
