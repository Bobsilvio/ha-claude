# Test delle 4 Funzionalità Nuove

Testa tutto dalla chat dell'addon Home Assistant!

---

## 1️⃣ FILE UPLOAD & DOCUMENTI

**Prompt per la chat:**
```
Puoi fare un riassunto dei documenti che ho caricato? 
Se non ne hai ancora, dimmi di caricarne uno dal pannello file upload.
```

**Cosa aspettarsi:**
- Se è la prima volta: il sistema chiederà di caricare un PDF/DOCX
- Se hai già documento: farà un riassunto del contenuto estratto

---

## 2️⃣ RAG (RETRIEVAL AUGMENTED GENERATION)

**Prerequisito:** Carica prima un documento

**Prompt per la chat:**
```
Nel documento che ho caricato, quale è la parte più importante?
Dammi i punti chiave.
```

**Cosa aspettarsi:**
- Il sistema cercherà nel documento e trasmetterà il contesto
- Le risposte saranno basate sul tuo documento
- Vedrai riferimenti ai paragrafi trovati

---

## 3️⃣ MEMORY (PERSISTENT CONVERSATIONS)

**Primo messaggio:**
```
Ricordati che mi chiamo Marco e lavoro nel settore IT.
Mi piace Python e Home Assistant.
```

**Secondo messaggio (dopo 5 minuti):**
```
Chi sono io? Quali sono i miei interessi?
```

**Cosa aspettarsi:**
- Al secondo messaggio, il sistema ricorderà:
  - Nome: Marco
  - Settore: IT
  - Interessi: Python, Home Assistant
- Funziona su conversazioni lunghe

---

## 4️⃣ VOICE (TTS - Text To Speech)

**Prompt per la chat:**
```
Puoi dire "Ciao, sono Claude" ad alta voce?
```

**Cosa aspettarsi:**
- Se enable_voice è true:
  - Apparirà un **player audio** nella chat
  - Ascolterai la voce sintetizzata
  - Funziona se pyttsx3 o edge-tts sono installati

---

## 📊 VERIFICA STATUS FUNZIONI

**Prompt per la chat:**
```
Quali funzioni sperimentali sono attivate? Dammi lo stato di:
- File Upload
- RAG
- Voice
- Memory
```

**Cosa aspettarsi:**
- Una tabella con lo stato: ✅ Attivo o ❌ Inattivo
- Se inattive, chiedi come attivarle

---

## 🔧 FLOW DI TEST CONSIGLIATO

1. **Start:** Chiedi lo status delle funzioni
2. **File Upload:** Carica un documento
3. **RAG:** Fai domande sul documento
4. **Memory:** Presentati
5. **Memory (after):** Chiedi info su te stesso
6. **Voice:** Richiedi sintesi vocale

---

## 💡 TEST AVANZATI

### Test Combinato (RAG + Memory + Chat):
```
Dimmi cosa sai su di me e cosa dice il mio documento.
Poi sintetizza tutto in una risposta breve.
```

### Test Memory Persistenza:
```
Ricordami: Budget massimo per progetti: €5000
```

Poi dopo, in una nuova sessione:
```
Qual è il mio budget massimo?
```

---

## 🐛 TROUBLESHOOTING

| Problema | Soluzione |
|----------|-----------|
| File Upload non funziona | Verifica `enable_file_upload: true` in config |
| RAG vuoto | Carica prima un documento |
| Voice silenzioso | Controlla speaker + `enable_voice: true` |
| Memory non ricorda | Controlla `/config/.storage/claude_memory.json` |
| Ingress error porta 5001 (dev) | Controlla API_PORT environment variable |

---

## 📝 EXAMPLE CHAT SESSION

```
User: Sono Marco, lavoro in IT e mi piace Python
Assistant: ✅ Ricordato. Interessante profilo!

User: [Carica documento.pdf]
Assistant: ✅ Documento caricato e indicizzato

User: Riassumi il documento
Assistant: [RAG search] Il documento parla di...

User: Chi sono?
Assistant: [Memory] Sei Marco, lavori in IT, ami Python...

User: Sintetizza in audio
Assistant: [Voice TTS] 🔊 [Audio file with speech]
```

---

## ✅ CHECKLIST DI TEST

- [ ] Status funzioni visibile
- [ ] File Upload acepta documenti
- [ ] RAG trova contenuti nel documento
- [ ] Memory ricorda informazioni personali
- [ ] Voice sintetizza discorso
- [ ] Tutte le funzioni lavoran insieme

---

**Happy Testing! 🚀**

Se qualcosa non funziona, controlla i log dell'addon in Home Assistant.
