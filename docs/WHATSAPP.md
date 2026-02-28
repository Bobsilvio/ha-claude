# 📱 WhatsApp con Amira — Guida completa (Twilio)

> **Telegram non ha bisogno di questa configurazione** — funziona con semplice long-polling, nessun IP pubblico richiesto.
> **WhatsApp via Twilio richiede un URL pubblico raggiungibile da Internet sulla porta 5010.**

---

## Come funziona

```
Tu (WhatsApp) ──→ Twilio ──→ [URL webhook :5010] ──→ Amira ──→ AI ──→ risposta ──→ Twilio ──→ Te
```

Twilio riceve il tuo messaggio WhatsApp, lo gira all'addon tramite una richiesta HTTP POST al **webhook URL**. Amira elabora il messaggio con l'AI e risponde via Twilio.

---

## ⚠️ Perché NON funziona `https://ha.tuodominio.eu/api/whatsapp/webhook`

L'URL `https://ha.tuodominio.eu` punta all'interfaccia di **Home Assistant** (porta 443), non all'addon Amira. L'ingress di HA smista le richieste agli addon solo tramite un token speciale (`/api/hassio_ingress/<token>/...`) che Twilio non conosce.

**Amira ascolta direttamente sulla porta 5010.** L'URL corretto è:

```
http://ha.tuodominio.eu:5010/api/whatsapp/webhook
```

oppure con HTTPS (se il tuo reverse proxy gestisce la 5010 con SSL):

```
https://ha.tuodominio.eu:5010/api/whatsapp/webhook
```

---

## Prerequisiti

| Requisito | Dove ottenerlo |
|-----------|---------------|
| Account Twilio (gratuito per il Sandbox) | [twilio.com](https://twilio.com) |
| **Account SID** | Console Twilio → home |
| **Auth Token** | Console Twilio → home |
| **Numero WhatsApp Sandbox** (`+1 415 523 8886`) | Console → Messaging → Try it out → Send a WhatsApp message |
| **Porta 5010 aperta** sul router/firewall verso HA | Vedi Step 2 |

---

## Step 1 — Credenziali nell'addon

Nella configurazione dell'addon Amira, imposta:

```yaml
twilio_account_sid: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   # inizia con "AC"
twilio_auth_token:  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
twilio_whatsapp_from: +14155238886                       # Sandbox Twilio
```

> Il numero `twilio_whatsapp_from` è il numero **mittente Twilio**, non il tuo numero personale.
> Per il Sandbox è sempre `+14155238886`.

Salva e riavvia l'addon.

---

## Step 2 — Aprire la porta 5010

Amira espone l'API sulla porta **5010** dell'host Home Assistant. Twilio deve poter raggiungere questa porta da Internet.

### Sul router (Port Forwarding)

1. Accedi al pannello del tuo router
2. Aggiungi una regola **Port Forwarding**:
   - Porta esterna: `5010`
   - Porta interna: `5010`
   - Protocollo: `TCP`
   - IP destinazione: l'IP locale di Home Assistant (es. `192.168.1.100`)
3. Salva

### Verifica che la porta sia raggiungibile

Dal telefono con WiFi spento (rete mobile), o da una rete esterna:

```bash
curl http://TUO_IP_PUBBLICO:5010/api/status
```

Dovresti ricevere un JSON con lo stato dell'addon. Se ottieni timeout o connessione rifiutata, la porta non è aperta.

### Alternativa: reverse proxy Nginx sulla porta 443

Se preferisci non esporre la porta 5010, puoi configurare Nginx per girare solo il path del webhook:

```nginx
server {
    listen 443 ssl;
    server_name ha.tuodominio.eu;
    # ... certificato SSL ...

    location /api/whatsapp/webhook {
        proxy_pass http://127.0.0.1:5010/api/whatsapp/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 60s;
    }
}
```

Con questa configurazione puoi usare `https://ha.tuodominio.eu/api/whatsapp/webhook` (porta 443, senza esporre la 5010).

---

## Step 3 — Configurare il webhook su Twilio

### Per il Sandbox (account gratuito)

1. Vai su [console.twilio.com](https://console.twilio.com)
2. Menu sinistro → **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Tab **"Sandbox settings"**
4. Campo **"When a message comes in"**: inserisci l'URL completo:

   | Scenario | URL da inserire |
   |----------|----------------|
   | Porta 5010 diretta | `http://ha.tuodominio.eu:5010/api/whatsapp/webhook` |
   | Nginx proxy su 443 | `https://ha.tuodominio.eu/api/whatsapp/webhook` |
   | ngrok (test) | `https://abc123.ngrok-free.app/api/whatsapp/webhook` |

5. Metodo: **HTTP POST**
6. Clicca **Save**

### Per un numero WhatsApp acquistato (account a pagamento)

1. Menu sinistro → **Messaging** → **Senders** → **WhatsApp senders**
2. Clicca sul tuo numero → sezione **"A message comes in"**
3. Inserisci l'URL del webhook e metodo **HTTP POST**
4. Salva

---

## Step 4 — Unirsi al Sandbox (solo prima volta)

Per ricevere messaggi dal Sandbox Twilio, ogni utente deve prima "unirsi":

1. Apri WhatsApp
2. Manda un messaggio al numero **+1 415 523 8886**
3. Testo: il codice che vedi nella tua console Twilio (es. `join subject-parts`)
4. Twilio risponde confermando — da quel momento ricevi le risposte di Amira

> Il codice di join è in: Console → Messaging → Try it out → Send a WhatsApp message → tab **"Sandbox"**

---

## Step 5 — Test

Manda un messaggio WhatsApp al numero Twilio. Controlla i log dell'addon:

```
Settings → Add-ons → Amira → Log
```

Messaggi da cercare:
- `✅ WhatsApp bot initialized` → credenziali trovate
- `WhatsApp message from +39...` → webhook funzionante, messaggio ricevuto
- `WhatsApp webhook signature invalid` → problema URL (vedi troubleshooting)
- `WhatsApp not configured` → credenziali mancanti

---

## Risoluzione problemi

### ❌ 404 Not Found

Stai navigando sull'ingress di Home Assistant (porta 443), non su Amira (porta 5010).
→ Usa `http://ha.tuodominio.eu:5010/api/whatsapp/webhook`

### ❌ Timeout / connessione rifiutata sulla porta 5010

La porta 5010 non è raggiungibile da Internet.
→ Verifica il Port Forwarding sul router e che il firewall del server la consenta.

### ❌ Signature invalid / 403

Amira tenta automaticamente più varianti dell'URL. Se persiste, l'URL nel campo webhook Twilio deve essere **identico** all'URL pubblico effettivamente raggiunto. Controlla nei log:
```
WhatsApp webhook signature invalid (url tried: 'http://...:5010/api/whatsapp/webhook')
```

### ❌ Twilio risponde da solo senza passare per Amira

Il webhook non è configurato su Twilio, o l'URL non include il path `/api/whatsapp/webhook`.

### ❌ "WhatsApp not configured" (501)

Credenziali mancanti. Verifica che `twilio_account_sid` inizi con `AC`, che `twilio_auth_token` sia corretto e che tu abbia riavviato l'addon dopo aver salvato.

### ❌ Sandbox non risponde dopo 24 ore

La sessione Sandbox Twilio scade dopo 24 ore di inattività. Manda di nuovo il codice di join.

---

## Differenze Sandbox vs numero reale

| | **Sandbox** (gratuito) | **Numero acquistato** |
|---|---|---|
| Costo | Gratuito | ~$15/mese + messaggi |
| Setup | Solo join code | Approvazione WhatsApp Business |
| Utenti | Max ~5 (devono fare join) | Illimitati |
| Numero | Condiviso (`+1 415 523 8886`) | Dedicato |
| Adatto per | Test e sviluppo | Produzione |

---

*Guida aggiornata per Amira v4.x — per problemi apri una [issue su GitHub](https://github.com/Bobsilvio/ha-claude/issues)*
