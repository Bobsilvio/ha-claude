# 🎯 QUICK TEST - Comandi Rapidi da Usare

## Step 1: Verifica Funzioni (SUBITO)

**Copia-incolla nella chat:**
```
Dimmi lo stato di queste funzionalità sperimentali:
- enable_file_upload
- enable_rag
- enable_voice
- enable_memory

Sono attivate? Quali versioni di librerie usi?
```

---

## Step 2: Test File Upload (Se attivo)

**1. Carica documento** via UI pannello file-upload
   - Usa `test_document.md` dal repo
   - Formato: PDF, DOCX, TXT, MD

**2. Poi chiedi in chat:**
```
Ho fatto l'upload di un documento.
Quanti paragrafi contiene? Quali sono i temi principali?
```

---

## Step 3: Test RAG (Se attivo)

**Prerequisito:** Documento uploadato

**Chiedi:**
```
Nel mio documento, cosa dici di Python?
Dammi i 3 punti più importanti.
```

**Poi:**
```
Quali sono i vantaggi di Home Assistant secondo il mio documento?
```

---

## Step 4: Test Memory (FUNZIONA SEMPRE)

**Primo prompt:**
```
Ricordati di me:
- Nome: Marco
- Professione: Sviluppatore Python
- Hobby: Home Automation
- Città: Milano
```

**Attendi risposta ✅**

**Secondo prompt (dopo alcuni messaggi):**
```
Cosa sai di me? Chi sono?
```

**Attendi risposta:** Dovrebbe ricordare TUTTO

---

## Step 5: Test Voice (Se attivo)

**Semplice:**
```
Sintetizza in audio questa frase: 
"Ciao, sono Claude, l'assistente di Home Assistant"
```

**Avanzato:**
```
Fai un riassunto di me in audio (basato su quello che ricordi)
```

---

## 🔥 TEST POWERHOUSE (Tutte le funzioni insieme)

```
Considerando che sono Marco, uno sviluppatore Python a Milano:

1. Riassumi il mio documento in 2 frasi
2. Che consiglio mi dai basato su quello che sai di me e del documento?
3. Sintetizza la risposta in audio
4. Ricordati questo consiglio per future conversazioni
```

---

## ❌ SE QUALCOSA NON FUNZIONA

**Chiedi in chat:**
```
Quali errori ci sono nel log del sistema?
Perché [funzione X] non è attivata?
Come la attivo?
```

---

## 📊 EXPECTED OUTPUT

| Feature | Expected | Result |
|---------|----------|--------|
| Memory | "Ricordo che sei Marco..." | ✅ / ❌ |
| File Upload | Accetta file | ✅ / ❌ |
| RAG | "Nel tuo documento..." | ✅ / ❌ |
| Voice | 🔊 Audio file | ✅ / ❌ |

---

**⏱️ Tempo totale test: ~5 minuti**

Copia i prompt sopra e usa direttamente nella chat dell'addon!
