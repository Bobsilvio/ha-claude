# Piano: Integrazione Amira nella pagina Automazioni

## Contesto
Il pulsante AMIRA nelle pagine automazione appare come bubble flottante, non integrato nell'header HA. La chat si apre come popup separato. L'utente vuole:
1. Pulsante AMIRA nel toolbar HA (accanto a "Tracce" e menu tre punti)
2. Chat come sidebar a destra (pagina divisa in due)
3. Flow visuale compatto con icone in alto (trigger → condition → action)

## File da modificare
- **`addons/claude-backend/chat_bubble.py`** — unico file, contiene tutto il JS generato

## Approccio

### Step 1: Shadow DOM Walker per Automation Editor
Aggiungere funzioni `_findAutomationToolbar()` e `_findAutomationContentArea()` (vicino a linea 655, dopo `getCardEditorFooter()`).

Percorso Shadow DOM:
```
document → home-assistant (shadowRoot) → ha-panel-config (shadowRoot)
  → ha-config-automation (shadowRoot) → ha-automation-editor (shadowRoot)
  → hass-subpage → [toolbar / .content]
```
Fallback BFS se il percorso diretto fallisce (come fa `_findEditCardEl()`).

### Step 2: Variabili di stato e costanti
Aggiungere vicino linea 1929 (dove ci sono le variabili del card editor):
- `AMIRA_AUTO_BTN_ID`, `AMIRA_SIDEBAR_ID`, `AMIRA_FLOW_ID`
- `_autoSidebarOpen`, `_autoBtnInjected`, `_autoFlowInjected`, `_lastAutoPageId`
- Refs diretti: `_autoSidebarEl`, `_autoMsgsEl`, `_autoInputEl`

### Step 3: Iniezione pulsante toolbar
Funzione `injectAutomationToolbarButton()`:
- Trova toolbar con `_findAutomationToolbar()`
- Crea button stile HA (flat, icona robot + "Amira")
- Click → toggle sidebar
- Pattern identico a `injectCardEditorButton()` (linea 2456)

### Step 4: Sidebar Chat integrata
Funzioni `openAutomationSidebar()` / `closeAutomationSidebar()` / `autoSidebarSend()`:
- Modello: `openCardPanel()` (linea 2149-2319) — stessa struttura con header gradient, selettori agent/model/provider, messaggi, input
- Layout: il container padre diventa `display:flex`, content automazione `flex:1`, sidebar `width:380px` a destra
- Sessione separata (localStorage `ha-claude-auto-session`)
- Condivide la logica di streaming con la bubble esistente (estrarre helper `_streamChat()` comune)
- Nasconde la floating bubble quando sidebar è aperta

### Step 5: Flow Visualization
Funzione `fetchAndRenderAutomationFlow(automationId)`:
- Fetch `/api/config/automation/config/{id}` con `_getHassToken()`
- Parse trigger/condition/action arrays dal JSON
- Genera HTML orizzontale con bolle + frecce:
  - Trigger: 🔔 sfondo blu (`#e3f2fd → #bbdefb`)
  - Condition: 🕐 sfondo ambra (`#fff8e1 → #ffecb3`)
  - Action: 💡 sfondo verde (`#e8f5e9 → #c8e6c9`)
- Etichette compatte estratte dal YAML (platform + entity_id, service name, ecc.)
- Iniettato sopra il content area nell'editor automazione
- Overflow-x scroll per automazioni complesse

### Step 6: Polling e integrazione
Estendere il `setInterval` alla linea 1879:
- Detect pagina automazione da URL (`/config/automation/edit/{id}`)
- Re-inject toolbar button se HA ri-renderizza
- Re-inject flow se automazione cambia
- Cleanup quando si naviga via
- Nasconde bubble flottante quando sidebar aperta

### Step 7: Traduzioni
Aggiungere stringhe T per en/it/es/fr (amira_toolbar, flow labels, sidebar title)

## Ordine implementazione
1. Traduzioni (piccolo)
2. Variabili di stato
3. Shadow DOM walkers
4. Toolbar button injection + polling
5. Flow visualization
6. Sidebar chat (il pezzo più grande, ~200 linee)
7. Integrazione hide/show bubble

## Verifica
- Aprire una pagina automazione in HA
- Verificare che il pulsante AMIRA appaia nel toolbar
- Verificare il flow visuale con trigger/condition/action
- Cliccare AMIRA → sidebar si apre a destra
- Inviare un messaggio nella sidebar → risposta streaming
- Navigare via → tutto viene rimosso, bubble ritorna
- Tornare → tutto viene ri-iniettato
