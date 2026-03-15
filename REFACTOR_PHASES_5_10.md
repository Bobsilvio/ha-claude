# Ha-Claude Refactoring - Fasi 5-10 Completate

## Riepilogo

In questa sessione sono state completate le fasi 5-10 del refactoring di `api.py`.

**Metriche:**
- Righe rimosse da api.py: ~992 linee
- Riduzione percentuale: 9.6% (da 10.340 a 9.348)
- File creati: 6
- File modificati: 2 (api.py, settings_service.py)
- Commit: 6 + 1 status

## Fasi Completate

### Fase 5: services/model_service.py
**Commit:** 3e3edd3

Sposta costanti e funzioni per la gestione dei model blocklist:
- `NVIDIA_MODEL_BLOCKLIST`, `NVIDIA_MODEL_TESTED_OK`
- `MODEL_BLOCKLIST_FILE`
- `_NVIDIA_MODELS_CACHE`, `_NVIDIA_MODELS_CACHE_TTL_SECONDS`
- `load_model_blocklists()`
- `save_model_blocklists()`
- `mark_nvidia_model_tested_ok()`
- `blocklist_nvidia_model()`
- `blocklist_model()`
- `_fetch_nvidia_models_live(nvidia_api_key)`
- `get_nvidia_models_cached(nvidia_api_key)`

**Note:** Le funzioni `_fetch_nvidia_models_live()` e `get_nvidia_models_cached()` ora richiedono `nvidia_api_key` come parametro per evitare dipendenze da globali di api.py.

### Fase 6: services/settings_service.py
**Commit:** f83f47a

Sposta costanti e funzioni per la gestione delle impostazioni:
- `RUNTIME_SELECTION_FILE`, `SETTINGS_FILE`, `MCP_RUNTIME_FILE`
- `SETTINGS_DEFAULTS`, `_SETTINGS_GLOBAL_MAP`
- `_load_settings()`
- `_save_settings()`
- `_load_mcp_runtime_state()`
- `_save_mcp_runtime_state()`
- `_set_mcp_server_autostart()`
- `load_runtime_selection()` - ritorna tuple (provider, model)
- `save_runtime_selection()`

**Note:** `_apply_settings()` rimane in api.py perché modifica molti globali. In api.py è stato creato un wrapper di `load_runtime_selection()` che modifica i globali `AI_PROVIDER`, `AI_MODEL`, `SELECTED_MODEL`, `SELECTED_PROVIDER`.

### Fase 7: services/prompt_service.py
**Commit:** 173c9e0

Sposta costanti e funzioni per la gestione di prompt e agenti:
- `CUSTOM_SYSTEM_PROMPT_FILE`, `AGENTS_FILE`, `CONFIG_EDITABLE_FILES`
- `_load_custom_system_prompt_from_disk()`
- `_persist_custom_system_prompt_to_disk()`
- `load_agents_config()` (ritorna dict raw da disk)

**Note:** `load_agents_config()` in api.py modifica i globali `AGENT_NAME`, `AGENT_AVATAR`, `AGENT_INSTRUCTIONS` tramite AgentManager. La versione in prompt_service ritorna solo i dati raw.

### Fase 8: routes/__init__.py
**Commit:** 11e8d62

Crea infrastruttura per registrazione dei blueprint:
- File `routes/__init__.py` con funzione `register_blueprints(app)`
- Placeholder per future registrazioni di blueprint

### Fase 9: routes/chat_routes.py
**Commit:** b1c7d56

Crea blueprint per le route di chat:
- File `routes/chat_routes.py` con `chat_bp` blueprint
- Placeholder per route:
  - `POST /api/chat`
  - `POST /api/chat/stream`
  - `POST /api/chat/abort`
  - `POST /api/memory/clear`

**Note:** Le route rimangono in api.py per evitare circular import. Le registrazioni avverranno tramite `chat_bp.add_url_rule()` nelle prossime fasi.

### Fase 10: Blueprint Registration
**Commit:** f78e3a6

Registra i blueprint nel startup dell'app:
- `routes/__init__.py` importa e registra `chat_bp`
- `api.py` chiama `register_blueprints(app)` prima di `if __name__ == "__main__"`
- Chat blueprint ora registrato automaticamente al startup

## Struttura di Directory

```
addons/claude-backend/
├── core/                          # Core utilities (Fasi 1-4)
│   ├── translations.py
│   ├── image_helpers.py
│   ├── model_utils.py
│   └── error_utils.py
│
├── services/                       # Business logic (Fasi 5-7)
│   ├── __init__.py
│   ├── model_service.py           # Model blocklist e caching NVIDIA
│   ├── settings_service.py        # Settings e runtime config
│   └── prompt_service.py          # Custom prompts e agent config
│
├── routes/                         # Flask blueprint organization (Fasi 8-10)
│   ├── __init__.py
│   └── chat_routes.py             # Chat routes blueprint
│
├── api.py                          # Main Flask app (ridotto)
└── config.yaml
```

## Prossime Fasi

- **Fase 11:** Agents routes blueprint
- **Fase 12:** MCP routes blueprint
- **Fase 13+:** Memory, documents, conversations, settings, voice, OAuth, NVIDIA, catalog, analytics, UI, etc.

## Verifiche Completate

- Sintassi Python valida per tutti i file
- Import diretti testati
- No circular imports
- api.py ridotta da 10.340 a 9.348 linee
