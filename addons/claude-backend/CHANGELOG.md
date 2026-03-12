# Changelog

> **⚠️ Dopo l'aggiornamento, ricostruire l'add-on** (Impostazioni → Add-on → Amira → Ricostruisci) per applicare le nuove dipendenze.
## 4.6.6 - Fix create dashboard
-- **Fix create dashboard**

## 4.6.5 — HTML dashboard reliability, auth hardening, quality guardrails
- **HTML dashboard generation reliability**
  - Fixed chunked `create_html_dashboard` loop handling and improved draft auto-finalization path
  - Improved truncated/escaped HTML normalization and malformed `<head>` repair
  - Added stricter detection to avoid unnecessary autocomplete on complete raw HTML
  - Enforced dashboard page `<title>` alignment with saved sidebar title (`Amira — ...`)

- **Auth + data loading fixes for generated dashboards**
  - Hardened auth patch to sanitize stale static headers (`Authorization: Bearer + tok`) even when helper is already present
  - Added `_authFetch(...)` wrapper injection for HA `/api/states` and `/api/history` calls to reduce token race issues
  - Result: generated dashboards are less likely to show persistent `n/d` due to early token resolution timing

- **Quality guardrails (non-template)**
  - Removed backend prebuilt chart auto-injection to keep layouts model-driven
  - Added mandatory chart requirements in both intent prompt and `create_html_dashboard` tool description:
    - at least 2 always-visible charts in main layout
    - one trend (line/area) + one comparative (bar/doughnut/pie)
  - Added raw HTML quality gate: reject KPI-only outputs when charts are expected

- **Dashboard generation telemetry**
  - Added minimal generation metrics persistence in `/config/amira/dashboard_generation_metrics.json`
  - Tracks success/rejection and recent quality details for troubleshooting provider/model behavior

- **Delete dashboard robustness**
  - `delete_dashboard` now resolves by id/url_path/title with slug normalization and `.html` tolerance
  - Also removes matching file under `/config/www/dashboards/*.html` when present

- **Runtime UX/i18n consistency**
  - Replaced newly introduced hardcoded Italian runtime status strings with neutral messages in tool-loop paths

## 4.6.4 — MCP LLM-first fix: tool dinamici nel prompt + esecuzione corretta
- **MCP in LLM-first (ToolRegistry attivo)**
  - I tool MCP dinamici runtime ora vengono sempre iniettati in `tool_schemas` (`+N`), anche quando il ToolRegistry è inizializzato da catalogo statico legacy
  - Risolto caso in cui il modello vedeva e chiamava `mcp_*` ma il backend rispondeva `Unknown tool` perché l'esecuzione passava dal registry statico
  - I tool `mcp_*` ora vengono eseguiti via dispatcher MCP diretto nel tool loop

- **Affidabilità richiesta MCP**
  - Regola prompt MCP generica su richieste DB/filesystem/repo (senza hardcode SQLite-only)
  - Retry interno one-shot se il modello chiude senza tool_call su richiesta chiaramente MCP-oriented

- **HTML dashboard draft fail-safe**
  - Fix caso `create_html_dashboard` in chunked mode: se il modello si ferma su `draft_started/draft_appended`
    e poi risponde “creata” senza chiamata finale, il backend ora finalizza automaticamente la bozza

## 4.6.3 — MCP UX/runtime: stato server, stop, autostart persistente manuale
- **MCP UI (chat_ui)**
  - Aggiunto badge stato per ogni server MCP con pallino:
    - verde = attivo
    - grigio = fermo
  - Aggiunto pulsante **Stop** accanto a **Start**
  - Pulsanti Start/Stop disabilitati dinamicamente in base allo stato corrente
  - Stato live letto da `/api/mcp/servers` per mostrare anche i server configurati ma non avviati

- **MCP API/runtime (api.py + mcp.py)**
  - Nuovo endpoint: `POST /api/mcp/server/<name>/stop`
  - `POST /api/mcp/server/<name>/start` ora salva il server in autostart runtime
  - `GET /api/mcp/servers` ora restituisce anche:
    - `running`
    - `state` (`running`/`stopped`)
    - `autostart`
    - server configurati ma non avviati
  - Aggiunta persistenza runtime su `/config/amira/mcp_runtime.json`:
    - se avvii manualmente un server e lo lasci attivo, al riavvio addon riparte
    - se lo stoppi, viene rimosso dall’autostart
  - Avvio MCP al boot limitato ai soli server marcati autostart (non tutti quelli nel config)
- **MCP manager**
  - Nuovo metodo `remove_server(name)` per disconnettere e deregistrare un singolo server

## 4.6.2 — fix: manage_helpers API, preview guard, UI diff e costi panel
- ** tools.py

  - manage_helpers — 3 bug fix API:
    - WS endpoint corretto: input_number/create (era
  config/input_number/create — endpoint inesistente in HA)
    - REST create: POST /config/{type}/config con id nel body (era POST con ID
   nell'URL → 404)
    - REST update: PUT /config/{type}/config/{id} (era POST)
    - WS create: rimosso {type}_id dal payload (HA auto-genera l'ID dal nome)
    - WS delete: stesso fix endpoint
    - Rimosso import os dentro manage_helpers che rendeva os locale all'intera
   funzione → crashava preview_automation_change con UnboundLocalError
    - Counter list: mostra solo counter.*, non tutti gli input_number.*

  api.py

  - Preview confirmation guard (nuovo sistema):
    - preview_automation_change → mostra diff → utente conferma →
  update_automation
    - Guard blocca update_automation se non c'è un preview valido nella
  sessione
    - Se stessa automation ma firma diversa (LLM rigenera changes leggermente
  diverse): override con le changes esatte del preview mostrato → elimina il
  doppio loop di conferma
    - Normalizzazione trigger/triggers, action/actions, condition/conditions
  in _normalize_automation_change_args per evitare falsi-positivi nel
  sig-match
  - _format_write_tool_response:
    - Aggiunta gestione errori (era assente — AttributeError se
  result["result"] non era dict)
    - YAML completo rimosso quando il diff è già mostrato; mostrato solo per
  CREATE o quando non ci sono differenze
    - preview_automation_change aggiunto a _WRITE_TOOLS → genera il diff
  rosso/verde in UI

  intent.py

  - preview_automation_change va chiamata immediatamente senza chiedere
  "procedo?": eliminata la doppia conferma
  - Exception per preview_automation_change aggiunta alla regola generale "ask
   before executing"

  providers/tool_simulator.py

  - _repair_json: aggiunta _escape_control_chars_in_strings — converte
  newline/tab letterali dentro stringhe JSON in \n/\t (causa frequente di
  parse failure con YAML multilinea nei tool call)
  - Log errore esteso da 200 a 1000 char, con posizione esatta dell'errore
  JSON

  chat_ui.py

  - Costi panel: giorni raggruppati per mese con <details>/<summary>
  collassabili; mese corrente aperto di default, precedenti chiusi; 35 giorni
  invece di 7; giorno corrente evidenziato

## 4.6.1 — Fix bubble auth

### 🐛 Fix
- **Fix bubble 401 (Ingress session)**: fix bubble autenticazione

## 4.6.0 — Fix bubble auth (Ingress session) + agent persistence + fix write tools

### 🐛 Fix
- **Fix bubble 401 (Ingress session)**: la bubble JS, caricata da `/local/`, non aveva il cookie di sessione Ingress — tutte le chiamate API fallivano con 401 e la bubble si auto-rimuoveva dal DOM. Ora crea la sessione Ingress via `POST /api/hassio/ingress/session` con il token HA prima di qualsiasi chiamata API
- **Fix tool di scrittura bloccati (DuplicateCallHook)**: `_tool_call_history.add()` pre-registrava TUTTE le firme tool PRIMA dell'esecuzione — la prima chiamata di ogni write tool veniva bloccata come "duplicata". Spostato il recording a DOPO l'esecuzione
- **Fix agent non visibili nella bubble**: `get_agents_for_api()` non restituiva il campo `identity` che il JS della bubble leggeva — aggiunto `identity: {name, emoji, description}` alla risposta API
- **Health check meno aggressivo**: 401/403 (problemi auth Ingress) non contano più come failure — la bubble si rimuove solo per errori di rete o 5xx

### ✨ UX
- **Persistenza agente selezionato**: la selezione dell'agente viene salvata in localStorage e ripristinata al ricaricamento — sia in chat_ui che nella bubble
- **Conferma per operazioni MODIFY**: il system prompt ora richiede conferma prima di modificare automazioni/script/dashboard (non solo per DELETE)
- **Rimossa rotella agent per canale dalla bubble**: la gestione agent per canale è ora solo nelle impostazioni di chat_ui
- **bubbleFetch() autenticato**: tutte le 21 chiamate fetch della bubble usano il wrapper `bubbleFetch()` che aggiunge automaticamente `Authorization: Bearer` con il token HA

## 4.5.9 — Fix copia card editor (shadow DOM) + tools grid ridimensionabile

### 🐛 Fix
- **Fix tasto Copia nel card editor**: il bottone "Copia" nei code block del pannello card editor non funzionava perché il pannello è dentro lo shadow DOM del dialog HA — `e.target` veniva retargetted al shadow host. Ora usa `e.composedPath()` + capture phase per attraversare i confini shadow DOM
- **Hover bottone Copia**: anche hover/mouseout ora usano `composedPath()` per funzionare dentro shadow DOM

### 🎨 UI
- **Tools grid ridimensionabile**: la griglia dei tool consentiti nell'agent form ora si può trascinare col mouse per allungarla (`resize: vertical`), con bordo visibile e padding interno
- **Stili bottoni uniformati**: i bottoni Salva di LLM Priority e Settings ora usano `config-save-btn` (come agent form e config editor) — prima usavano `agent-add-btn` con stile diverso
- **Bottoni agent form allineati**: aggiunto padding e font-size consistenti ai bottoni Salva/Annulla dell'agent form, in linea con gli altri form
- **Dark mode bottoni**: aggiunto dark mode per `config-save-btn` e `agent-add-btn` — prima mancavano gli override per il tema scuro

## 4.5.7 — Fix tasto Copia nella bubble/card + tool descriptions agent form

### 🐛 Fix
- **Fix tasto Copia nei code block della bubble e card editor**: il bottone "Copia" nei blocchi di codice non funzionava perché usava `onclick` inline, bloccato dal CSP di Home Assistant. Ora usa event delegation tramite `document.addEventListener` con classe `.amira-copy-btn`
- **i18n bottone Copia nella bubble**: aggiunto `copy_btn` e `copied` nelle 4 lingue (EN/IT/ES/FR) — prima era hardcoded "Copia"/"Copiato!"

### ✨ UX
- **Descrizioni leggibili per i tool nell'agent form**: le chip dei tool consentiti ora mostrano una descrizione chiara (es. "Modifica automazione", "Carica storico") invece del nome tecnico (`update_automation`, `get_history`). Il nome tecnico resta visibile al hover come tooltip
- **i18n tool descriptions**: descrizioni tradotte in 4 lingue (EN/IT/ES/FR), coerenti con la lingua impostata nell'addon

## 4.5.5 — Fix modelli duplicati nel dropdown + pricing 120 modelli

### 🐛 Fix
- **Fix modelli Anthropic duplicati nel dropdown agente**: `get_available_models()` elencava sia la notazione con trattini (`claude-opus-4-6`) che con punti (`claude-opus-4.6`) — rimossi i duplicati, mantenuti solo gli ID API ufficiali
- **Aggiunti modelli v4 datati mancanti**: `claude-opus-4-20250514`, `claude-sonnet-4-20250514`, `claude-haiku-4-20250514`

## 4.5.4 — Pricing engine: 120 modelli, tutti i 22 provider coperti

### 💰 Cost Tracking
- **120 modelli con pricing esplicito**: da 59 a 120 entries nella tabella `MODEL_PRICING` — copertura completa per tutti i 22 provider supportati
- **Nuovi modelli Anthropic**: Claude Opus 4.6, Sonnet 4.6, Haiku 4.5, Opus 4.5, Opus 4.1 con relativi alias datati + alias generici (`claude-sonnet`, `claude-opus`, `claude-haiku`)
- **Nuovi modelli OpenAI**: GPT-4.1 family (4.1, 4.1-mini, 4.1-nano), GPT-5.1, GPT-5-mini, GPT-4 legacy, GPT-3.5 Turbo
- **OpenAI Codex (CLI)**: GPT-5.3/5.2/5.1/5 Codex family con varianti max, spark, mini
- **Nuovi modelli Google**: Gemini 3.x (3.1-pro, 3-pro, 3-flash) con pricing preview
- **Nuovi provider con pricing**: Perplexity (Sonar, Sonar Pro, Sonar Reasoning Pro), MiniMax (M2, M2.1), Zhipu (GLM-4 Flash/Plus), DashScope (Qwen Max/Plus/Turbo), Kimi K2
- **Modelli open-source cross-provider**: Llama 3.1 (8B/70B/405B), Qwen 2.5 (7B/32B), Mistral 7B/Nemo/Large — usati da SiliconFlow, VolcEngine, OpenRouter, GitHub Models
- **6 provider gratuiti**: `nvidia`, `ollama`, `github_copilot`, `github` (GitHub Models), `claude_web`, `chatgpt_web` — tutti in `FREE_PROVIDERS`
- **Alias Copilot-specifici**: `gpt-41-copilot` → GPT-4.1 pricing, `gpt-4-o-preview` → GPT-4o pricing

### 🐛 Fix
- **Fix fuzzy matching pricing errato**: il lookup cercava il primo match per prefisso — `gpt-4o-mini-2024-07-18` matchava `gpt-4o` ($2.50) invece di `gpt-4o-mini` ($0.15). Ora preferisce il match più lungo (longest-key-wins)

## 4.5.2 — Settings UI, bubble/card button indipendenti, feedback tool, fix default

### ⚙️ Settings migrati nella chat UI
- **Tutti i settings runtime ora nella UI**: lingua, feature toggle, provider avanzati, timeout, ecc. — gestiti dalla sezione ⚙️ Settings della chat con descrizioni in 4 lingue (EN/IT/ES/FR)
- **config.yaml semplificato**: contiene solo API key e impostazioni di log — tutti i toggle feature rimossi
- **settings.json persistente**: le impostazioni sono salvate in `/config/amira/settings.json` e applicate all'avvio
- **Restart addon dalla UI**: dopo il salvataggio dei settings, un dialog propone il riavvio automatico dell'addon
- **MCP config editor nella UI**: abilitazione MCP + percorso file config gestiti dalla sezione Settings → Features

### 🫧 Bubble e Card Button indipendenti
- **Toggle separati**: `enable_chat_bubble` (bubble floating) e `enable_amira_card_button` (🤖 Amira nel card editor) sono ora indipendenti
- **Default ON**: entrambi attivi al primo avvio — nessuna configurazione necessaria
- **Iniezione intelligente**: lo script JS viene sempre registrato se almeno uno dei due è attivo; cleanup completo quando entrambi disabilitati

### 🔄 Feedback tool nella bubble
- **Indicatore "thinking" durante le tool round**: tra una chiamata tool e la successiva, la bubble mostra nuovamente l'indicatore di pensiero con timer
- **Evento `clear` tra round**: il backend invia `clear` + `status` dopo ogni esecuzione tool, la bubble resetta il testo e i badge, e `_restoreThinking()` ricrea l'indicatore
- **Fix testo troncato**: rimossa la ri-emissione di `text_so_far` sul break dedup nativo — il testo non si accumula più tra round

### 🐛 Fix
- **Fix Anthropic 400 "unexpected tool_use_id"**: 3 bug interagenti nella gestione della conversation history — tool_result orfani, tool_use_id duplicati, e iniezione sintetica con ID non corrispondente
- **Fix default non applicati al primo avvio**: se `settings.json` non esisteva ancora, i valori env del run script sovrascrivevano i default corretti — ora `SETTINGS_DEFAULTS` viene sempre applicato come base, poi sovrascritto dai valori salvati
- **Fix run script disallineato**: env var `ENABLE_CHAT_BUBBLE`, `ENABLE_FILE_UPLOAD`, `ENABLE_MCP`, `FALLBACK_ENABLED` ora allineati ai `SETTINGS_DEFAULTS`
- **Fix 9 provider mancanti nel selettore**: Ollama, Custom, Perplexity, MiniMax, AiHubMix, SiliconFlow, VolcEngine, DashScope, Moonshot, Zhipu aggiunti al sistema di priorità LLM
- **Fix posizione eye button password**: spostato prima del campo input per allineamento corretto
- **Fix larghezza campi settings**: input da 120px→220px, password da 160px→260px
- **Fix stile bottone save MCP**: classe cambiata da `agent-form-actions` a `config-editor-footer`

### 📝 Documentazione
- **README aggiornato**: architettura config a 2 livelli (config.yaml + Settings UI), tabella settings con default corretti, nuovi endpoint API
- **DOCS.md aggiornato**: configurazione, MCP, troubleshooting, data storage aggiornati
- **Descrizioni settings in 4 lingue**: ogni setting ha una descrizione contestuale visibile nella UI

## 4.5.1 — Fix conversazioni card/bubble + icona cestino + salvataggio agenti + anti-allucinazione entity

### 🧠 Anti-hallucination
- **Validazione entity_id in `get_history`**: prima di interrogare lo storico, il tool verifica che l'entità esista in Home Assistant — se non esiste restituisce un errore chiaro con fino a 8 suggerimenti fuzzy (match per keyword su entity_id e friendly_name), permettendo anche ai modelli più piccoli di correggere e riprovare
- **Ricerca keyword in `get_entities`**: nuovo parametro opzionale `query` che filtra le entità per keyword nel nome/entity_id (es. `query="umidita"`) — evita che il modello debba scegliere tra i primi 30 sensori restituiti a caso e riduce drasticamente le allucinazioni di entity_id inesistenti

### 🐛 Fix
- **Fix conversazione card continua nella bubble**: aprendo la chat UI dalla card dopo aver usato la bubble, la conversazione proseguiva nella sessione bubble invece di crearne una nuova — ora se il `currentSessionId` salvato è di tipo `bubble_*`, viene generato un nuovo ID automaticamente
- **Fix sessione bubble non persistita**: cliccando su una conversazione bubble nella sidebar, il suo ID non viene più salvato in `localStorage` — riaprendo la pagina si riparte dalla chat UI, non dalla bubble
- **Fix icona cestino non visibile**: il carattere Unicode U+1F5D1 (🗑) non era supportato da tutti i browser/dispositivi e appariva come un quadrato con caratteri — sostituito con un'icona SVG trash universalmente compatibile
- **Fix salvataggio agente silenzioso**: creare un agente con ID contenente maiuscole (es. "Amira") falliva silenziosamente perché la validazione `[a-z0-9_-]` rifiutava l'input senza mostrare errori — ora l'ID viene auto-convertito in minuscolo e gli errori di validazione/salvataggio mostrano un `alert()` visibile
- **Fix `[object Object]` nella card agente**: con `include_disabled=true` l'API restituisce `model` come oggetto `{primary, fallbacks}` anziché stringa — la card e il form ora estraggono correttamente `model.primary`
- **Fix TypeError `model.split` nel form agente**: `agentData.model.split('/')` crashava quando `model` era un oggetto — ora viene normalizzato a stringa prima dello split
- **Fix icona cestino card agente**: anche il bottone delete sulle card agente usava il carattere Unicode U+1F5D1 non renderizzato — sostituito con SVG come nella lista conversazioni
- **Fix MEMORY.md ignorato con contenuti brevi**: il filtro `len > 150` in `get_long_term_memory()` scartava silenziosamente memorie brevi ma significative (es. "Mi chiamo Silvio") — abbassata la soglia a 10 caratteri
- **Fix memoria non iniettata in intent `chat`**: quando la domanda veniva classificata come `chat` (nessun tool), il blocco `else: smart_context = ""` saltava completamente l'iniezione di MEMORY.md — ora la memoria viene comunque caricata e iniettata nel contesto

## 4.5.0 — Architettura OpenClaw: catalogo modelli, cost tracking, multi-agent, safety guards

### 🧠 Dynamic Model Catalog (`model_catalog.py`)
- **Catalogo centralizzato**: ogni modello ha capabilities (VISION, REASONING, CODE, TOOL_USE, STREAMING, DOCUMENT), context window, max output tokens, pricing tier (FREE/CHEAP/STANDARD/PREMIUM)
- **Fonte unica di verità**: eliminati tutti gli elenchi statici sparsi — un solo registro consultato da agent system, fallback engine, UI e intent classifier
- **Arricchimento runtime**: tabella statica + discovery live da `/v1/models` (NVIDIA, Ollama, GitHub Copilot)
- **Query programmatiche**: `catalog.get_entry("anthropic", "claude-opus-4-6")` → capabilities, context window, pricing

### 💰 Real-time Cost Tracking (`pricing.py` + `usage_tracker.py`)
- **Pricing cache-aware per 120+ modelli**: Anthropic (cache read 10% input, write 125%), OpenAI (cache 50%), Google (25%), DeepSeek (10%), Groq, Mistral, Moonshot
- **Usage normalizer**: gestisce 20+ varianti di naming tra provider (prompt_tokens, input_tokens, promptTokens, cache_read_input_tokens, prompt_tokens_details.cached_tokens, ...)
- **Cost breakdown per messaggio**: input, output, cache_read, cache_write — mostrato con tooltip dettagliato nella UI
- **Visualizzazione UI**: `1.5k in / 300 out (500 cache↓, 200 cache↑) • $0.0084` con icone e formatting smart
- **Totali sessione**: contatore running di token e costi nella barra conversazione
- **Tracking persistente**: aggregazione giornaliera, per-modello, per-provider su `/data/usage_stats.json`
- **3 nuovi endpoint API**: `GET /api/usage_stats`, `GET /api/usage_stats/today`, `POST /api/usage_stats/reset`

### 🤖 Multi-Agent System (`agent_config.py` + `model_fallback.py`)
- **Profili agente**: identità (nome, emoji, descrizione), modello preferito, catena fallback, whitelist tool
- **Config JSON**: `/config/amira/agents.json` — editabile dall'utente, hot-reload
- **Selettore agente**: switch da UI chat e bubble — modello/provider applicati automaticamente
- **Fallback intelligente**: catena cascading (primario → fallback agente → default globali) con classificazione errori
- **Classificazione errori**: rate-limit (cooldown + probe periodico), auth (skip permanente), billing (abort), context-overflow (abort)
- **Health tracking**: monitoraggio salute provider con recovery automatico via probe

### 📊 Livello log CHAT personalizzato
- **Nuovo livello CHAT (25)**: tra INFO (20) e WARNING (30) — dedicato a domande utente e risposte AI
- **Colore blu** con icona 💬 nei log terminale
- **Tutti i canali**: Web UI (📩 domanda / 📤 risposta), Telegram, WhatsApp, Alexa
- **Facile da filtrare**: `grep CHAT` mostra solo conversazioni, niente rumore di sistema

### 🛡️ Safety Guards per automazioni
- **Rifiuto automazioni vuote**: `create_automation` restituisce errore se trigger E action sono vuoti
- **Rilevamento alias duplicati**: prima di creare, controlla `automations.yaml` — se esiste nome simile, suggerisce `update_automation`
- **Schema tool migliorati**: descrizioni parametri con esempi concreti (`{'platform': 'time', 'at': '20:00'}`)
- **Regole system prompt**: 3 nuove regole esplicite — mai usare `create_automation` per modificare automazioni esistenti

### 🐛 Fix
- **Fix SyntaxError chat UI**: `tip.join('\\n')` in formatUsage produceva newline letterale nel JS → `SyntaxError: string literal contains unescaped line break` → `switchSidebarTab is not defined` a cascata
- **Fix INCLUDE_USAGE**: `providers/github.py` ora invia `include_usage: true` per ricevere token count

### 📦 Nuovi file
- `model_catalog.py` — catalogo modelli centralizzato (~573 righe)
- `agent_config.py` — sistema multi-agente (~691 righe)
- `model_fallback.py` — fallback intelligente con health tracking (~596 righe)
- `tool_registry.py` — registro tool centralizzato ispirato a OpenClaw (~1049 righe)
- `usage_tracker.py` — tracking persistente costi/uso (~222 righe)

## 4.4.5 — AI intent classification + TTS vocale + 3 nuovi tool + error UX

### 🧠 Classificazione intent via AI
- **Rilevamento tool intelligente**: quando i keyword non matchano, una chiamata rapida (~300-500 ms) a un modello leggero (Groq, GitHub, ecc.) analizza la frase dell'utente e seleziona solo i tool necessari (1-6) invece del set statico di 12
- **3 strategie di classificazione**: REST diretto (provider standard), REST fallback (provider alternativo con API key), streaming (provider web come Codex/Copilot) — con fallback automatico a catena
- **~900 token di prompt**: lista dei 51 tool con descrizione a 1 riga, regole multilingua, zero hallucination
- **Fallback sicuro**: se tutte le strategie falliscono → set statico generico (come prima), zero regressione

### 🔊 Text-to-Speech (TTS) con Edge-TTS
- **Sintesi vocale**: le risposte di Amira possono essere ascoltate con un pulsante 🔊 accanto ai messaggi
- **Voci maschili/femminili**: nuova opzione `tts_voice` nella configurazione dell'add-on (`female` default, `male` disponibile)
- **4 lingue**: voci neurali per italiano, inglese, spagnolo e francese
- **UI integrata**: pulsante play/stop nei messaggi, sia nella chat principale che nella chat bubble

### 🔧 Nuovi tool
- **`fire_event`**: lancia eventi custom sul bus HA per triggerare automazioni (con blocklist eventi core per sicurezza)
- **`get_logged_users`**: lista utenti HA registrati con ruoli, stato attivo, owner, system-generated
- **`get_error_log`**: viewer interattivo del log errori in 2 modalità — sommario numerato + dettaglio con stack trace; supporta anche errori browser catturati

### 🛡️ Errori più chiari
- **Sanitizzazione errori provider**: i messaggi di errore con JSON grezzo, blob HTTP e noise tecnico vengono puliti in messaggi user-friendly (quota esaurita, rate limit con countdown, errori di rete)
- **429 quota vs rate limit**: distingue "crediti esauriti" da "troppe richieste al minuto" con messaggi diversi e tempo di reset quando disponibile
- **Claude Web 429**: parsing dettagliato con `resetsAt`, tipo di claim e tempo rimanente

### 🏠 Ollama lightweight mode
- **System prompt leggero per Ollama**: i modelli locali su CPU deboli (Celeron, RPi) ricevono un prompt conciso (~100 token) invece del prompt completo con 40+ tool (~7000 token) — riduce il prefill e rispetta la context window

### 🐛 Fix & miglioramenti
- **Fix conteggio tool per intent chat**: `tools=0` corretto (prima mostrava `tools=51` perché `None` veniva confuso con lista vuota)
- **Keyword "registri"** aggiunto alla categoria debug in tutte le 4 lingue
- **Provider model_fetcher**: fix minori per fetch modelli

## 4.4.4 — Fix risposte AI mancanti nello storico + cestino visibile
- **Fix risposte AI sparite nelle chat vecchie**: quando l'IA usava tool calls (es. automazioni, statistiche), la risposta finale veniva mostrata in streaming ma MAI salvata su disco — al ricaricamento della pagina spariva. Causa: `elif _streamed_text_parts` veniva saltato quando `new_msgs_from_provider` era non-vuoto (messaggi intermedi con tool_calls). Fix: cambiato `elif` → `if` così entrambi i blocchi vengono eseguiti
- **Cestino conversazioni più visibile**: il pulsante elimina era `opacity: 0` e visibile solo al hover (invisibile su mobile/touch). Ora sempre semi-visibile (`opacity: 0.45`), più grande (32px), con bordo colorato, sfondo rosso tenue, glow rosso al hover e migliore contrasto in dark mode

## 4.4.3 — Auto-blocklist modelli non supportati (GitHub Copilot)
- **Auto-blocklist su `model_not_supported`**: quando GitHub Copilot restituisce HTTP 400 con `model_not_supported` (es. `claude-opus-4.6-fast`), il modello viene automaticamente aggiunto alla blocklist e non appare più nella lista modelli
- **Blocklist persistente**: i modelli bloccati vengono salvati in `/config/amira/model_blocklist.json` con chiave `github_copilot` e sopravvivono ai riavvii
- **Messaggio utente chiaro**: quando un modello non è supportato, la chat mostra un avviso esplicito invitando a selezionarne un altro
- **Infrastruttura generica `blocklist_model()`**: helper centralizzato in `api.py` che supporta qualsiasi provider (nvidia, github, github_copilot) — estendibile in futuro

## 4.4.2 — Fix chat UI crash (SyntaxError + ReferenceError)
- **Fix `await` SyntaxError**: `bootUI()` was a sync function but used `await fetch(...)` for the SDK check added in v4.4.1 — browsers threw `Uncaught SyntaxError: await is only valid in async functions`. Now `async function bootUI()`
- **Fix `switchSidebarTab is not defined`**: sidebar tab buttons used `onclick="switchSidebarTab(...)"` but the function was defined in local script scope, not on `window` — caused `Uncaught ReferenceError` on every tab click
- **Export all onclick handlers to `window`**: added `window.` exports for `switchSidebarTab`, `newChat`, `toggleSidebar`, `sendSuggestion`, `testNvidiaModel`, `revokeCodexOAuth`, `toggleDarkMode`, `toggleReadOnly` — all inline `onclick` handlers now work correctly

## 4.4.1 — ARM / Raspberry Pi compatibility + crash-resilient startup
- **Fix ARM (aarch64/armv7) install failure**: split `pip install` into two stages in the Dockerfile — core dependencies (flask, waitress, etc.) MUST install, while heavy optional SDKs (anthropic, openai, google-genai, mcp, twilio, telegram) are installed individually with `--prefer-binary` and can fail without breaking the build
- **Crash-resilient server startup**: if `import api` fails at runtime (missing module, memory issue, etc.), a lightweight diagnostic Flask server starts on the same port, showing the exact error in the browser and in logs — eliminates the "Cannot connect to host" ingress loop
- **Startup diagnostics**: `server.py` now logs platform arch, Python version, and availability of all optional packages before loading the main app
- **SDK missing warning in chat UI**: if the selected AI provider requires an SDK that didn't install (e.g. `anthropic` on RPi), the user sees a clear warning banner in the chat with the exact package name and platform info — both on page load and on the 10s status poll
- **Clear error on chat**: `stream_chat_with_ai()` now checks SDK availability before trying to call the provider — returns a translated human-readable error instead of a cryptic traceback
- **API endpoints updated**: `/api/status` and `/api/system/features` now include `provider_sdk_available`, `provider_sdk_message`, `missing_packages`, and `platform` fields
- **httpx moved to core**: `httpx` is required by all providers (via `enhanced.py`), now in `requirements_core.txt` instead of optional
- **New files**: `requirements_core.txt` (8 mandatory packages) and `requirements_optional.txt` (8 provider SDKs / features) — original `requirements.txt` kept for local development

## 4.4.0 — Conversation list: modern card style + fix [CONTEXT] leak in titles/messages
- **Fix [CONTEXT:] in titles**: conversation titles no longer show raw `[CONTEXT: User is on the Home Assistant Statistics...]` — the server-side `api_conversations_list()` now strips context blocks before generating titles
- **Fix [CONTEXT:] with nested brackets**: `stripContextInjections()` regex was broken when context blocks contained nested brackets like `[TOOL RESULT]` — now uses bracket-depth counting to correctly strip the entire block
- **Fix saved messages**: `saved_user_message` now strips standalone `[CONTEXT: ...]` blocks (previously only stripped combined CONTEXT+DASHBOARD_HTML patterns)
- **Clean API responses**: both `/api/conversations/<id>` and `/api/mcp/conversations/<id>/messages` endpoints now strip `[CONTEXT: ...]` from user messages before returning
- **Modern conversation cards**: redesigned sidebar conversation items with gradient backgrounds, rounded corners, hover animations, accent bar on hover, gradient active state with white text, and smooth transitions
- **Dark mode cards**: matching dark theme with deep blue/purple gradients for cards and proper text contrast (white on active, light gray on normal)
- **Text contrast fix**: active card now uses white titles/info text, delete button adapts to active/normal state with proper contrast

## 4.3.9 — Log: fix [CONTEXT] stripping (robust regex)
- **Fix broken log stripping**: previous regex `[CONTEXT:.*?]` stopped at the first `]` in the text (e.g. inside the YAML or entity validation block), leaking partial instructions into the log
- **New `_strip_context_for_log()` helper**: scans for the YAML block with ```` ```yaml...``` ```` and the user text after the last `]\n` — reliably extracts both regardless of `]` characters inside the context body
- **Log format**: `[YAML]\n```yaml\n...\n```\n<user message>` — no instructions, no entity validation rules

## 4.3.8 — Log: hide [CONTEXT] instructions, show only YAML + user message
- **Cleaner logs**: `Stream [provider]: [CONTEXT: ...]` messages no longer dump the full instruction block — the regex strips the `[CONTEXT: ...]` prefix and keeps only the embedded YAML block (if present) and the user text that follows
- **Format**: log now shows `[YAML]\n```yaml\n...\n```\n<user message>` instead of hundreds of lines of rules
- **Applies to both** `/api/chat` and `/api/chat/stream` endpoints

## 4.3.7 — Card editor: warning when in GUI mode (no YAML readable)
- **GUI mode warning**: when the HA card editor is open in visual/GUI mode, the bubble context bar now shows a yellow warning `⚠️ Editor card — passa alla modalità codice per leggere lo YAML` (translated for all 4 languages) instead of the normal green label
- **Quick actions hidden in GUI mode**: the card quick-action chips (Explain, Improve, Add feature, Fix) are hidden when no YAML is readable — they are useless without the card code
- **CSS `context-bar--warn`**: new class with amber background (`#fff3cd`) applied to the context bar only when card is in GUI mode

## 4.3.6 — manage_statistics: tool implementation added
- **Fix `manage_statistics` Unknown tool error**: tool was referenced in the intent system and prompt but never implemented in `execute_tool` — every call returned `{"error": "Unknown tool: manage_statistics"}`; added full implementation with `recorder/validate_statistics`, `recorder/clear_statistics`, `recorder/update_statistics_metadata` WebSocket calls
- **Tool definition added to `HA_TOOLS_DESCRIPTION`**: `manage_statistics` now has a proper JSON schema with `action` enum (`validate`, `clear_orphaned`, `fix_units`) so all providers can see and call it correctly
- **Progress message added**: `"manage_statistics": "Gestisco statistiche"` added to the tool progress label map

## 4.3.5 — ToolSimulator: filter hallucinated tools + manage_statistics auto-fix
- **ToolSimulator intent filter**: no-tool providers (github_copilot, openai_codex) may hallucinate tool names not in the current intent (e.g. `get_repairs` inside a `manage_statistics` intent) — extracted tool calls are now filtered against the intent tool set; dropped calls are logged as warnings
- **manage_statistics auto-proceed**: if the user explicitly asks to fix/correct/remove (e.g. "correggi", "elimina", "fix everything"), the model now calls `fix_units` / `clear_orphaned` immediately after validate without asking confirmation again — previously it always asked, wasting a round
- **Prompt hardening**: added "The ONLY tool you should use is manage_statistics. Do NOT call any other tool." to prevent the model from hallucinating unrelated tool calls

## 4.3.4 — manage_statistics: timeout, compaction, 4 bug fixes, dedup loop breaker
- **manage_statistics timeout fix**: Copilot 2min timeout caused by large validate result — compact format now uses flat ID lists (max 30 orphaned, 15 unit issues), payload size logged
- **Higher read timeout**: github_copilot read timeout raised 120→180s for heavy tool results
- **Copilot token compaction**: `flatten_tool_messages` max_result_chars reduced 3000→2000 for Copilot to stay under context limits
- **4 bugs in statistics flow** fixed: (a) text buffer not flushed when `_skip_tool_extraction=True` → user saw `...`; (b) duplicate tool calls within single response (model emits same call twice); (c) model re-validates after user says "sì" because prompt said "ALWAYS validate FIRST"; (d) raw `<tool_call>` XML saved in conversation history — now cleaned via `clean_display_text`
- **manage_statistics broken**: `recorder/validate_statistics` returns a dict `{stat_id: [issues]}` not a list — code assumed list, silently dropping all issues; fixed with dual dict/list parser + `_ws_error_msg()` helper for robust error handling
- **ToolSimulator rule update**: `manage_statistics(validate)` classified as read-only to prevent confirmation prompt on validate
- **Dedup loop breaker for no-tool providers**: `_duplicate_count` + `_skip_tool_extraction` mechanism — 1st duplicate disables ToolSimulator next round, 2nd duplicate force-breaks with text emission
- **Custom card YAML rules**: card_editor prompt now includes YAML syntax rules for mini-graph-card, mushroom, custom:button-card, etc.
- **Statistics page context**: bubble detects Developer Tools > Statistics page, shows context bar and quick actions (Valida, Pulisci orfani, Correggi unità)
- **New `manage_statistics` tool**: validate, fix_units, clear_orphaned, clear actions — bulk statistics cleanup via recorder WebSocket API

## 4.3.3 — Card editor panel: width, selectors, smarter YAML analysis
- **Panel width fix**: opening the Amira chat in the card editor no longer expands the dialog — the panel now locks to the original `surface.offsetWidth` and resets it on close
- **Agent selector wider**: provider dropdown max-width raised from 90px→150px, model from 110px→200px — labels are now fully readable
- **Smarter YAML prompt**: Amira now uses `search_entities` to verify entity IDs autonomously instead of asking the user to check; only flags real problems; shows corrected YAML in a code block
- **Code block rendering in card panel**: `_renderInlineMd()` now renders fenced ````yaml` blocks as styled `<pre>` with a working 📋 copy button (placeholder-based approach avoids double HTML-escaping)

## 4.3.2 — Fix chat UI completely broken (send + sidebar)
- **Root cause**: bare `\n` (Python newline) inside a JS regex character class in `_stripCodeBlocks()` was inserted as a literal newline in the generated HTML, splitting the regex across two lines and causing a `SyntaxError: Invalid regular expression: missing /`
- **Impact**: the syntax error prevented the entire `<script>` block from executing — send button, conversation sidebar, and all JS features stopped working
- **Fix**: replaced `\n` with `\\n` in the regex `/`[^`\n]+`/g` so it produces the correct JS regex `/`[^`\n]+`/g`
- **validate.sh**: added check for bare `\n` inside JS regex character classes in `chat_ui.py` source

## 4.3.1 — Split-view file explorer
- **New sidebar tab "Files"** (📁): browse `/config` directory tree directly from the chat UI — shows dirs and files with icons, size, and breadcrumb navigation
- **File preview panel**: clicking a file opens a resizable middle panel (default 320px, drag splitter to resize, min 180px / max 600px) with tabbed view — up to 3 files open at once
- **YAML syntax highlight**: key–value pairs, strings, booleans, numbers, and comments are colour-coded without any external library
- **File context injection**: open files are automatically prepended to the AI payload as `[FILE: path]\ncontent\n[/FILE]` blocks — context bar above the input shows which files are active
- **Context bar stripping**: `[FILE:...]` blocks never appear in the chat history visible to the user (stripped by `stripContextInjections`)
- **New REST endpoints**: `GET /api/files/list?path=` and `GET /api/files/read?file=` — path-traversal protection, 15 000-char read limit with truncation notice
- **Responsive**: file panel and its splitter are hidden on mobile (`max-width: 599px`) — the tab still shows the tree for reference
- **Dark-mode** styles for all new elements

## 4.3.0 — Four bug fixes: Copilot tool round 2, bubble thinking label, log quick actions i18n, chatgpt_web warning
- **GitHub Copilot HTTP 400 on tool round 2**: after `flatten_tool_messages()` the conversation ended with an `assistant` turn (tool result merged in), which Copilot rejects — now injects a `user` continuation prompt when the last message is an assistant turn
- **`flatten_tool_messages` null content fix**: assistant messages with `content: None` now get a non-null placeholder so strict providers don't reject with 400
- **Tool result missing `name` field**: `role=tool` messages now include `"name": fn_name` so flatten produces `[TOOL RESULT: get_automations]` instead of `[TOOL RESULT: ]`
- **Bubble thinking label shows model name**: thinking indicator now shows active model — e.g. "Sto pensando · gpt-4o... (3s)" — using `agentData.current_model_technical`
- **Log quick actions in wrong language**: `getQuickActions()` was sending hardcoded English text to AI regardless of UI language — added `qa_*_text` i18n keys for all 4 languages (IT/EN/ES/FR)
- **chatgpt_web `curl_cffi` warning suppressed**: downgraded from `WARNING` to `DEBUG` since provider is hidden from UI

## 4.2.9 — GitHub Copilot: full model list + updated API headers
- **Static model list extended**: GitHub Copilot provider now shows 30+ known models immediately, even before authentication — includes Claude Opus/Sonnet/Haiku 4.x, GPT-5.x-codex, GPT-5.1/5.2, Gemini 3.x, Grok Code Fast, and all GPT-4o/4.1 variants
- **Updated API headers**: all Copilot HTTP calls (session token, /models, chat) now use `copilot-chat/0.26.7` and `vscode/1.100.0` (was `0.12.2` / `1.85.0`) — matches current Copilot extension version for full model access
- **Refresh button** (`Aggiorna modelli`) calls `GET /models` on `api.githubcopilot.com` and replaces the static list with the live models available on the user's subscription
- **Legacy display name mappings** updated in `api.py` to include all new Claude/Gemini/Grok/GPT-5 model names
- Reasoning/special models (`o1`, `o3`, `oswe-*`) excluded from `temperature`/`top_p` to avoid API errors

## 4.2.8 — Bubble: fix log dialog closed by bubble button click
- **Root cause**: HA dialogs close when clicking outside them; the bubble button is "outside" → clicking bubble always dismissed the open log popup before context could be captured
- **`mousedown` pre-capture**: bubble button now captures `extractVisibleLogEntry()` on `mousedown` (fires before HA's document-level click handler closes the dialog), storing it in `_cachedLogEntry`
- **Persistent log cache `_cachedLogEntry`**: survives dialog close — updated whenever a live entry is detected (1s poll or `mousedown`), never cleared just because the dialog was dismissed
- **Fallback in `buildContextPrefix()`**: uses `ctx.logEntry || _cachedLogEntry` so AI sees the log entry even after the dialog is gone
- **Fallback in `getQuickActions()`**: "Spiega questo errore" / "Come si risolve?" chips appear using cached entry
- **Fallback in `updateContextBar()`**: shows "• log selezionato" indicator using cached entry
- Cache cleared on: navigation away from logs page, or "Nuova chat" button

## 4.2.7 — Bubble: HA log page context-awareness + get_ha_logs tool
- **Bubble detects `/config/logs` page**: shows "Log di sistema" in context bar, pulse animation on bubble
- **Log entry extraction**: walks HA shadow DOM to find open log dialog text; if found, context bar shows "• log aperto" and quick actions are tailored to that specific entry
- **Quick actions on log page**: "Spiega questo errore", "Come si risolve?", "Mostra tutti gli errori", "Problemi critici"
- **Live re-detection**: poll every 1s checks if a log dialog was opened/closed (URL doesn't change in HA) and refreshes context bar + quick actions
- **New tool `get_ha_logs`**: fetches `/api/error_log` from HA, filters by level (error/warning/info/all) and optional keyword, returns up to 200 entries
- **New endpoint `/api/ha_logs`**: server-side proxy to HA error_log (used by bubble for direct log fetching)
- **System prompt** updated: AI can now call `get_ha_logs` to fetch and diagnose HA errors

## 4.2.6 — Fix dashboard HTML edit via bubble with no-tool providers (openai_codex)
- Fixed synthetic assistant turn injected between dashboard HTML context and user request:
  changed "Dimmi cosa vuoi modificare" → "Procedo con la modifica richiesta" to prevent
  the AI from repeating the waiting message instead of executing the edit
- Added explicit HTML-output instruction to `api_content` for no-tool providers even when
  there is no smart context, so the model always knows to return full HTML not conversational text

## 4.2.5 — Bubble: real-time step progress matching chat UI
- Bubble now shows tool step bullets and status updates in real time during elaboration (same as chat UI)
- Tool badges (colored chips) appear for `🔧` status events — shows which HA tools are being called
- Fixed `_updateThinkingBase`: now reliably preserves all step bullets when updating the status line
- Increased max visible steps from 4 → 6 in the thinking bubble
- Fixed SSE buffer drain on stream close: leftover data in buffer is processed before breaking
- Guaranteed cleanup after stream end: `_removeThinking()` and `assistantEl.style.display=''`  always called even if server closes without a `done` event

## 4.2.4 — Fix dropdown reset on hover while browsing options
- `loadModels()` no longer rebuilds the DOM while a `<select>` is open
- Added `_selectOpen` flag: set to `true` on `mousedown`/`focus`, cleared on `blur`/`change`/`Escape`/`Tab`
- Both `providerSelect` and `modelSelect` tracked: prevents poll (every 10s) and post-`changeModel` reload from closing the dropdown and jumping back to the previous selection while the user is scrolling through options

## 4.2.3 — Fix SyntaxError in two-level AI selector
- Fixed `SyntaxWarning: invalid escape sequence '\s'` in `chat_ui.py` that caused a `SyntaxError: unterminated string literal` at startup
- `\s` inside JS regex embedded in Python f-string was mis-interpreted as a Python escape sequence; changed to `\\s`
- Removed orphaned duplicate code block that appeared after `</html>"""` closing delimiter due to a botched previous edit

## 4.2.2 — Two-level AI selector: provider first, then model
- Header now shows two separate dropdowns instead of one grouped dropdown
- First select: choose provider (Anthropic, OpenAI, Google, GitHub Copilot…)
- Second select: choose model for that provider (auto-populated on provider change)
- Switching provider auto-selects and applies the first model of that provider
- Responsive: stacked full-width on mobile, compact side-by-side on tablet/desktop

## 4.2.1 — Fix Ollama HTTP 400 "can't find closing '}' symbol"
- `providers/ollama.py`: Ollama's template engine (Go `text/template`) interprets literal `{` / `}` in message content and tool descriptions as template actions, causing 400 errors when smart context includes JSON entity data
- Added `_escape_braces()`: inserts a zero-width space after `{` and before `}` to break template patterns without affecting visible text
- Added `_sanitize_messages()` / `_sanitize_tool_schemas()`: deep-sanitise all text content before sending to Ollama
- Added fallback: if Ollama still fails with tool schemas, automatically retry without tools
- Fixed missing `_prepare_messages()` call (system prompt was not injected for Ollama)
- Extracted HTTP streaming into `_ollama_stream()` for cleaner retry logic

## 4.2.0 — Entity discovery: use real HA device_class instead of keyword matching
**Breaking change in entity matching logic — eliminates false positives entirely.**

### Problem
Previous approach used keyword/substring matching on entity_ids to find entities (e.g. searching for "battery" by matching "bat" inside entity names). This caused false positives: "bat" matched "sabato", pulling in unrelated consumption entities. Every new device_class would require a new keyword dictionary — fragile and unscalable.

### Solution
- `intent.py`: **Two-mode entity discovery:**
  - **Device-class mode** (battery, temperature, humidity, etc.): filters ONLY by the REAL `device_class` attribute from Home Assistant state — zero false positives, no substring matching needed
  - **Keyword mode** (fallback): for brands, room names, or custom terms that have no device_class mapping — still searches entity_id/friendly_name
- `intent.py`: removed `_keyword_synonyms` dictionary entirely — no longer needed since device_class filtering doesn't require synonym expansion
- `intent.py`: expanded `_device_class_aliases` to cover both IT and EN terms (batterie, battery, temperatura, temperature, etc.)
- `tools.py`: `_inject_entity_filter_fallback()` simplified — trusts the backend entity list as authoritative, removed all `_dc_keywords` dictionaries and keyword-based re-filtering

### Result
Works for any device_class (battery, temperature, motion, humidity, etc.) without maintaining keyword vocabularies. New device types work automatically.

## 4.1.14 — Fix iOS Companion App infinite loading + dashboard showing only 5 sensors
- `_fix_auth_redirect()`: entry-point regex now uses **prefix matching** (`load\w*` catches `loadBatteries()`, `loadSensors()`, etc.) — previously only matched exact names like `load()`, so `tok` stayed empty on iOS
- `_fix_auth_redirect()`: also wraps `setInterval`/`setTimeout` referencing entry-point functions in `_getTokenAsync().then(...)`
- New `_inject_entity_filter_fallback()` post-processor: when AI HTML filters `/api/states` by `device_class` (e.g. `=== 'battery'`), injects the backend's pre-filtered entity list as `window._HA_ENTITIES` and extends the filter to include all matching entities
- Dashboard creation pipeline now calls `_inject_entity_filter_fallback()` after auth redirect fix

## 4.1.13 — Fix AI using device_class filter instead of pre-loaded entity list
- `intent.py`: add `device_class` field to entity objects injected in smart context (was missing — AI couldn't see it)
- `tools.py`: tool description now explicitly instructs AI to copy entity_ids from ## ENTITÀ TROVATE and use `__ENTITIES_JSON__`, never filter `/api/states` by `device_class`
- System prompts updated with same instruction

## 4.1.12 — Rewrite auth patch: fix stale headers + entry-point wrapping
- `_fix_auth_redirect()` completely rewritten to operate per `<script>` block
- Also removes stale `const headers = {Authorization: 'Bearer '+tok}` built before token resolved
- Wraps bare `load()` / `init()` / `render()` calls in `_getTokenAsync().then(...)` at statement level
- Injects `_authHeader()` helper for consistent auth headers in all fetch calls

## 4.1.11 — Fix AI-generated auth redirect breaking Companion App
- Added `_fix_auth_redirect()` post-processor applied to all generated HTML dashboards
- Removes `if(!tok){ location.href='/?redirect=...' }` pattern that caused infinite loading in Companion App
- Replaces sync `localStorage.getItem('hassTokens')` token read with async `_getTokenAsync()` — tries parent iframe postMessage first, then localStorage
- Injects initial states snapshot (`__INITIAL_STATES_JSON__`) so page renders immediately without client-side auth

## 4.1.10 — Fix HTML dashboard auth in Companion App
- `getTokenAsync()` now tries `postMessage` to parent window first (correct channel when page is inside a Lovelace iframe in Companion App)
- Token cached after first resolution to avoid repeated async lookups
- Fetch proceeds even without token (HA session-cookie fallback)

## 4.1.9 — Authoritative entity fallback from smart context
- `intent.py` saves pre-loaded entity_ids to `api._last_smart_context_entity_ids`
- `tools.py` uses those as last-resort fallback when AI passes only JS garbage in `entities[]` and HTML scan finds nothing

## 4.1.8 — Entity pre-filter via HA domain whitelist + HTML fallback extraction
- Replace regex pre-filter with HA domain whitelist (`sensor`, `binary_sensor`, `switch`, etc.) — JS vars like `stat.low`, `x.state`, `arr.map` are reliably rejected
- When entities list is all junk, scan raw HTML for quoted `domain.slug` literals to recover real entity_ids

## 4.1.7 — Smart context battery synonyms + entity pre-filter + Companion App auth
- `intent.py`: IT→EN keyword synonyms + `device_class` search (batterie→battery, temperatura→temperature, umidità→humidity, etc.) — finds all relevant entities, not just those with Italian names
- `tools.py`: pre-filter non-HA strings (JS expressions) from `entities[]` before HA validation
- `tools.py`: `getTokenAsync()` supporting HA Companion App (`externalApp`/`webkit`) with `localStorage` fallback
- `api.py`: improved OAuth provider logging at startup

## 4.1.6 — Fix messaging in chat UI + sort order
- WhatsApp/Telegram sessions no longer appear in the main chat UI conversation list
- Removed "Recent context: USER:..." prefix injected into WhatsApp messages (redundant, polluted saved conversations)
- Messaging list (WhatsApp + Telegram) now sorted with most recent chat first

## 4.1.5 — Smart context larger window + compact entity lists
- `MAX_SMART_CONTEXT` raised from 10 000 to 25 000 chars (5× more sensor data visible per query)
- Entity lists with >20 entries now use compact JSON, saving ~40% token space
- Entity injection capped at 80 entries per query (prevents single-keyword floods like "temperature" from eating the whole context)
- Fixes WhatsApp temperature queries returning only 4 out of 48 available sensors

## 4.1.4 — Add enable_mcp toggle
- Added `enable_mcp` option (default `false`) to disable MCP at startup
- When disabled, MCP servers are never contacted and no connection errors appear in logs
- New toggle visible in Home Assistant addon config UI (all 4 languages: IT, EN, FR, ES)

## 4.1.3 — Complete BoBot → Amira rename
- **CHANGE**: Renamed all remaining `BoBot`/`bobot` references to `Amira`/`amira` in `config.yaml` (panel title, port description, MCP config path)

## 4.1.2 — Rename addon to Amira
- **CHANGE**: Addon renamed from `BoBot` to `Amira` in Home Assistant addon store (`name` and `description` in `config.yaml`)

## 4.1.1 — Dockerfile fixes + new modules
- **FIX**: Corrected Dockerfile `COPY` instructions — removed non-existent `memory_system.py` reference
- **NEW**: Added `scheduled_tasks.py` to the Docker image (task scheduler module)
- **NEW**: Added `voice_transcription.py` to the Docker image (voice/TTS module)
- **FIX**: Removed duplicate `COPY memory.py` instruction in Dockerfile

## 4.1.0 — Complete provider architecture rewrite + dashboard intelligence
> **Breaking change from v3.x** — provider system completely rewritten

### Provider system
- Replaced monolithic `providers_anthropic/google/openai.py` with the modular `providers/` package
- 22 provider classes: OpenAI, Anthropic, Google, Groq, Mistral, NVIDIA, DeepSeek, OpenRouter, Ollama, GitHub, GitHub Copilot, ChatGPT Web, OpenAI Codex, Zhipu, SiliconFlow, Moonshot, MiniMax, AiHubMix, VolcEngine, DashScope, Perplexity, Custom
- Provider manager with unified streaming interface and enhanced error handling
- Dynamic model list: `PROVIDER_MODELS` built from each provider's `get_available_models()` at startup — single source of truth
- `model_fetcher.py`: live model refresh from official APIs with on-disk cache
- `rate_limiter.py`, `error_handler.py`, `tool_simulator.py`: shared utilities across providers

### OpenAI Codex provider
- OAuth PKCE flow: token stored at `/data/oauth_codex.json` with auto-refresh
- Correct model list (gpt-5.x-codex only)
- Connected banner in UI showing account ID, expiry and disconnect button
- `/api/oauth/codex/revoke` endpoint

### HTML Dashboard
- **Smart context split**: `[CURRENT_DASHBOARD_HTML]` injected as a separate conversation turn to avoid token overflow while keeping the full entity context (10KB cap)
- **Intent detection**: filesystem lookup in `www/dashboards/` to correctly route requests to `create_html_dashboard`
- `openMoreInfo()` with native `hass-more-info` event + custom modal fallback
- Auth redirect: if token is missing, redirect to `/?redirect=...`
- Sidebar title always prefixed with `Amira — <title>` (enforced in `tools.py`)

### Chat UI & bubble
- `stripContextInjections()`: hides `[CONTEXT:...]` and `[CURRENT_DASHBOARD_HTML]` blocks from the displayed conversation history without affecting stored data
- Tool call artifacts hidden from conversation history (`api_conversation_get`)
- Bubble drag fixed with Pointer Events API + `setPointerCapture()`
- Removed outdated "Novita v3.0" vision feature strings across all 4 languages

### New features
- **MCP**: Model Context Protocol server support
- **Telegram & WhatsApp**: bot integration
- **Voice transcription**: Whisper STT and TTS support
- **Semantic cache**: reduces API calls via semantic response caching
- **RAG**: Retrieval-Augmented Generation on local files
- **File upload**: attach files to conversations
- **Memory**: two-layer memory system with `MEMORY.md` (long-term facts) and `HISTORY.md` (session log)
- **Scheduled tasks**: task scheduler with autonomous agent
- **Quality metrics**: response quality scoring
- **Prompt caching**: prompt caching to reduce Anthropic API costs
- **Image support**: multi-provider image analysis
- **GitHub Copilot**: dedicated OAuth provider
