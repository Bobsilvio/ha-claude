# Contributing

Grazie per l'interesse a contribuire a Claude AI Assistant!

## Come Contribuire

### 1. Segnala Bug

Crea un issue con:
- Descrizione chiara del bug
- Passi per riprodurre
- Output atteso vs attuale
- Versione HA e Python

### 2. Suggerisci Miglioramenti

Crea un issue con:
- Caso d'uso
- Soluzione proposta
- Vantaggi
- Possibili svantaggi

### 3. Contribuisci Codice

1. **Fork** il repository
2. **Crea** feature branch: `git checkout -b feature/new-feature`
3. **Commit**: `git commit -m 'Add new feature'`
4. **Push**: `git push origin feature/new-feature`
5. **Pull Request**: Apri PR con descrizione

## Linee Guida

### Stile Codice

- Usa **Black** per formattazione
- Usa **pylint** per linting
- Aggiungi **type hints**
- Documenta con docstrings

```python
def example_function(param: str) -> bool:
    """Describe what this does.
    
    Args:
        param: Description of param
        
    Returns:
        Description of return value
    """
    return True
```

### Commit Messages

- Usa formato: `type: description`
- Tipi: feat, fix, docs, style, refactor, test
- Esempi:
  - `feat: add webhook support`
  - `fix: timeout handling in API client`
  - `docs: update API reference`

### Tests

- Scrivi tests per nuove features
- Mantieni coverage > 80%
- Esegui: `pytest tests/ -v`

## Code Review

- Rispondi ai commenti
- Aggiorna il PR se richiesto
- Grazie per la pazienza!

## Setup Sviluppo

```bash
# Clone
git clone https://github.com/your-username/ha-claude.git
cd ha-claude

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install -r tests/requirements.txt

# Run tests
pytest tests/ -v

# Format code
black custom_components/ backend/

# Lint
pylint custom_components/ backend/
```

## Aree Prioritarie

- [ ] Persistent conversation storage
- [ ] Improved error messages
- [ ] Performance optimization
- [ ] Mobile app integration
- [ ] Voice support

## Domande?

- Apri una Discussion
- Commenta su Issues
- Leggi la documentazione

---

Grazie per contribuire! 🎉
