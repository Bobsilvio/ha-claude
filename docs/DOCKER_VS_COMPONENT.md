# Docker vs Custom Component - Qual è la Differenza?

## 🎯 Risposta Breve

| | **Custom Component** | **Docker** |
|---|---|---|
| **Cosa installi** | Solo il componente HA | Stack completo (HA + Backend API) |
| **Richiede HA OS** | ❌ No (qualsiasi HA) | ⚠️ Dipende (vedi sotto) |
| **Dove gira** | **Su Home Assistant** | **Su Docker** (separato) |
| **Complessità** | ⭐ Facile | ⭐⭐ Media |
| **Risorse** | Minime (~50MB) | Moderate (~500MB) |
| **Consigliato** | ✅ User normali | ✅ Developers/Linux |

---

## 📊 Confronto Dettagliato

### Custom Component Installation

**Cos'è:**
Installi direttamente su Home Assistant il componente Claude.

**Come funziona:**
```
Your Home Assistant
    ↓
[Claude Integration] ← componente installato
    ↓
[Backend API running somewhere]
```

**Requisiti:**
- ✅ Home Assistant 2024.1.0+
- ✅ Accesso cartella `custom_components/`
- ✅ Backend API avviato (locale o remoto)
- ❌ **Non richiede HA OS**

**Installazione (3 step)**
```bash
# 1. Copia componente
cp -r custom_components/claude ~/.homeassistant/custom_components/

# 2. Riavvia HA
ha core restart

# 3. Configura in UI
Settings → Devices & Services → Claude
```

**Vantaggi:**
- ✅ Semplice da installare
- ✅ Funziona su qualsiasi HA (OS, Container, Bare Metal)
- ✅ Risorce minime
- ✅ Configurazione UI nativa

**Svantaggi:**
- ⚠️ Backend API va avviato manualmente
- ⚠️ Richiede Python e dipendenze separate

---

### Docker Compose Installation

**Cos'è:**
Stack Docker completo con Home Assistant + Backend API in container.

**Come funziona:**
```
Docker Host
├── [Home Assistant Container]
│   ├── [Claude Integration]
│   └── network: internal
│
└── [Claude API Container]
    ├── Flask backend
    └── network: internal
```

**Requisiti:**
- ✅ Docker e Docker Compose installati
- ✅ Linea di comando disponibile
- ❌ **Non richiede HA OS** (ma richiede Docker)

**Installazione (2 step)**
```bash
# 1. Configura
cp .env.example .env
nano .env  # inserisci HA_TOKEN

# 2. Avvia
docker-compose up -d
```

**Vantaggi:**
- ✅ Stack completo, tutto automatico
- ✅ Isolamento: niente conflitti con sistema host
- ✅ Facilissimo da deployare
- ✅ Upgrade semplice (`docker-compose pull && up -d`)
- ✅ Microservices setup

**Svantaggi:**
- ⚠️ Richiede Docker (non per principianti)
- ⚠️ ~500MB risorse
- ⚠️ Non è nativa l'integrazione HA

---

## 🏠 Case Specifici

### Caso 1: HA OS (Yellow, Green, Blue)

**Opzione a) Custom Component** ✅ CONSIGLIATO
```
HA OS Container
├── Home Assistant
└── custom_components/claude/ ← Copia qui

Backend API esterno (Docker/VPS)
```

**Opzione b) Docker**  ❌ Non ideale
```
HA OS non supporta Docker direttamente
Dovresti disabilitare HA OS e usare Docker
```

### Caso 2: HA Container (Docker)

**Opzione a) Custom Component** ✅ Possibile
```
Docker
├── HA Container
│   └── custom_components/claude/ ← Copia qui
└── Backend Container (separato)
```

**Opzione b) Docker Compose** ✅ CONSIGLIATO
```
docker-compose.yml orchestrates tutto
- HA che gira in container
- Backend che gira in container
- Network interno
```

### Caso 3: HA Bare Metal (Python venv)

**Opzione a) Custom Component** ✅ CONSIGLIATO
```
~/.homeassistant/
└── custom_components/claude/ ← Copia qui

Backend API:
  - Stesso venv
  - O VPS distinto
```

**Opzione b) Docker Compose** ✅ Alternativo
```
Docker Compose per Containerizzare tutto
(più pulito del bare metal)
```

### Caso 4: HA Supervised (Raspberry Pi)

**Opzione a) Custom Component** ✅ CONSIGLIATO
```
HA Supervised
├── Home Assistant
└── custom_components/claude/ ← Copia qui

Backend su Raspberry o VPS
```

**Opzione b) Docker Compose** ⚠️ Conflitto
```
Supervised usa Docker gestionato da HA
Usare Docker Compose aggiuntivo complica
```

---

## 🎓 Guida Scelta

**Scegli Custom Component se:**
- ✅ Hai HA OS (Yellow/Green/Blue)
- ✅ Vuoi installazione semplice
- ✅ Backend API su VPS/altro
- ✅ Non conosci Docker

**Scegli Docker Compose se:**
- ✅ Conosci Docker
- ✅ Vuoi stack isolato e completo
- ✅ Usi HA Container (non OS)
- ✅ Vuoi microservices

---

## 📋 Configurazione Richiesta

### Custom Component Setup

```yaml
# .homeassistant/configuration.yaml (opzionale)
claude:
  api_endpoint: http://192.168.1.100:5000    # Backend esterno
  model: claude-3-haiku
  polling_interval: 60
```

### Docker Compose Setup

```yaml
# docker-compose.yml (già configurato)
services:
  home-assistant:
    image: homeassistant/home-assistant:latest
    
  claude-api:
    build: ./backend
    environment:
      - HA_URL=http://home-assistant:8123
      - HA_TOKEN=your_token
```

---

## 🔄 Interoperabilità

**Puoi usare componente + Docker API?**

✅ **SÌ!** Setup misto:
```
HA OS (Custom Component)
    ↓ (API call)
Docker Container (Backend API) su stesso/diverso host
```

**Configurazione:**
```yaml
claude:
  api_endpoint: http://docker-host:5000
  # Il componente chiama l'API nel Docker container
```

---

## 🚀 Raccomandazioni

| Tua Setup | Installazione | Motivo |
|---|---|---|
| HA OS (Yellow/Green) | Custom Component | Non supporta Docker nativamente |
| HA Container | Docker Compose | Orchestrazione pulita |
| HA Supervised (RPi) | Custom Component | Supervised usa Docker gestito |
| HA Bare Metal | Custom Component | Più semplice |
| Multi-Host | Docker Compose | Microservices |

---

## 💡 Summary

### **La Differenza Principale:**

- **Custom Component**: Installi il componente IN Home Assistant
- **Docker**: Runni Home Assistant IN Docker (il componente dentro)

**Quando scegliere quale dipende dalla tua setup di HA, non dal componente!**

Vedi [INSTALLATION.md](INSTALLATION.md) per istruzioni step-by-step per la tua setup.
