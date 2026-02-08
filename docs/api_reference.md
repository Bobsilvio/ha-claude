# API Reference

Documentazione completa di tutti gli endpoint dell'API Claude.

## Base URL

```
http://localhost:5000
```

## Autenticazione

L'API usa Home Assistant Bearer Token passato tramite header:
```
Authorization: Bearer YOUR_HA_TOKEN
```

## Endpoints

### 1. Health Check

**GET** `/health`

Verifica che il server sia in esecuzione.

**Risposta:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**cURL:**
```bash
curl http://localhost:5000/health
```

---

### 2. Get Entities

**GET** `/entities`

Recupera tutte le entità disponibili in Home Assistant.

**Risposta:**
```json
{
  "entities": {
    "light.living_room": {
      "entity_id": "light.living_room",
      "state": "on",
      "attributes": {
        "brightness": 255
      }
    }
  },
  "count": 42
}
```

**cURL:**
```bash
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/entities
```

---

### 3. Get Automations

**GET** `/automations`

Recupera tutte le automazioni disponibili.

**Risposta:**
```json
{
  "automations": {
    "automation.morning_routine": {
      "id": "automation.morning_routine",
      "name": "Morning Routine",
      "enabled": true
    }
  },
  "count": 5
}
```

**cURL:**
```bash
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/automations
```

---

### 4. Get Scripts

**GET** `/scripts`

Recupera tutti gli script disponibili.

**Risposta:**
```json
{
  "scripts": {
    "script.welcome": {
      "id": "script.welcome",
      "name": "Welcome Home",
      "sequence": []
    }
  },
  "count": 3
}
```

**cURL:**
```bash
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/scripts
```

---

### 5. Get Entity State

**GET** `/entity/{entity_id}/state`

Recupera lo stato di una specifica entità.

**Parametri:**
- `entity_id` (path): ID dell'entità (es: light.living_room)

**Risposta:**
```json
{
  "entity_id": "light.living_room",
  "state": "on",
  "attributes": {
    "brightness": 200,
    "color_temp": 366,
    "effect": "colorloop"
  },
  "last_changed": "2024-01-15T10:30:00+00:00"
}
```

**cURL:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:5000/entity/light.living_room/state
```

---

### 6. Send Message

**POST** `/message`

Invia un messaggio a Claude per l'elaborazione.

**Request Body:**
```json
{
  "message": "Accendi tutte le luci del soggiorno",
  "context": "Sera, temperatura 20°C"
}
```

**Risposta:**
```json
{
  "status": "success",
  "message": "Accendi tutte le luci del soggiorno",
  "response": "Processed: Accendi tutte le luci del soggiorno"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Accendi tutte le luci del soggiorno",
    "context": "Sera, temperatura 20°C"
  }'
```

---

### 7. Execute Automation

**POST** `/execute/automation`

Esegue un'automazione.

**Request Body:**
```json
{
  "automation_id": "automation.morning_routine"
}
```

**Risposta:**
```json
{
  "status": "success",
  "automation_id": "automation.morning_routine"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/execute/automation \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"automation_id": "automation.morning_routine"}'
```

---

### 8. Execute Script

**POST** `/execute/script`

Esegue uno script con variabili opzionali.

**Request Body:**
```json
{
  "script_id": "script.welcome",
  "variables": {
    "temperature": 22,
    "brightness": 100
  }
}
```

**Risposta:**
```json
{
  "status": "success",
  "script_id": "script.welcome",
  "result": "Script executed"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/execute/script \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "script_id": "script.welcome",
    "variables": {"temperature": 22}
  }'
```

---

### 9. Call Service

**POST** `/service/call`

Chiama un servizio Home Assistant.

**Request Body:**
```json
{
  "service": "light.turn_on",
  "data": {
    "entity_id": "light.living_room",
    "brightness": 255
  }
}
```

**Risposta:**
```json
{
  "status": "success",
  "service": "light.turn_on"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/service/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "service": "light.turn_on",
    "data": {
      "entity_id": "light.living_room",
      "brightness": 255
    }
  }'
```

---

### 10. Webhook

**POST** `/webhook/{webhook_id}`

Riceve webhook per bi-directional communication.

**Request Body:**
```json
{
  "action": "light_changed",
  "entity_id": "light.living_room",
  "new_state": "on"
}
```

**Risposta:**
```json
{
  "status": "received"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/webhook/my_webhook \
  -H "Content-Type: application/json" \
  -d '{"action": "light_changed"}'
```

---

## Status Codes

| Code | Significato |
|------|------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Server Error |

## Error Handling

Gli errori vengono ritornati in questo formato:

```json
{
  "error": "Descrizione dell'errore",
  "status": 400,
  "details": "Dettagli aggiuntivi"
}
```

## Rate Limiting

Attualmente non c'è rate limiting. Per produzione, si consiglia di implementare:
- Max 100 richieste per minuto per endpoint
- Queue per operazioni lunghe

## Timeout

- Default: 30 secondi
- Configurabile via `TIMEOUT` in .env

---

## Examples

### Scenario: Accendi luci e chiama script

```bash
# 1. Ottieni lo stato
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:5000/entity/light.living_room/state

# 2. Accendi luci
curl -X POST http://localhost:5000/service/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "service": "light.turn_on",
    "data": {
      "entity_id": "light.living_room",
      "brightness": 200
    }
  }'

# 3. Esegui script
curl -X POST http://localhost:5000/execute/script \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "script_id": "script.welcome",
    "variables": {"guests": 5}
  }'
```

---

## Best Practices

1. **Sempre usa HTTPS** in produzione
2. **Valida i dati** prima di inviarli
3. **Usa i timeout** appropriati
4. **Log gli errori** per debugging
5. **Rate limit** le richieste frequenti
6. **Monitora** la salute dell'API
