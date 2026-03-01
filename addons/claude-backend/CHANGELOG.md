# Changelog

## 4.1.1 — Dockerfile fixes + new modules
- **FIX**: Corrected Dockerfile `COPY` instructions — removed non-existent `memory_system.py` reference
- **NEW**: Added `scheduled_tasks.py` to the Docker image (task scheduler module)
- **NEW**: Added `voice_transcription.py` to the Docker image (voice/TTS module)
- **FIX**: Removed duplicate `COPY memory.py` instruction in Dockerfile
