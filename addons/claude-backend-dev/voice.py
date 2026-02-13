"""
Voice input/output system for speech-to-text and text-to-speech.
Supports both online (cloud) and offline (local) processing.
Optimized for Home Assistant on Raspberry Pi (lightweight).
"""

import os
import logging
from typing import Optional, Tuple, Dict
from enum import Enum
from io import BytesIO

logger = logging.getLogger(__name__)

# Voice backend configuration
class STTBackend(Enum):
    """Speech-to-Text backends."""
    GOOGLE_CLOUD = "google_cloud"      # Online, requires API key
    POCKETSPHINX = "pocketsphinx"      # Offline, lightweight
    GOOGLE_SPEECH = "google"           # Online via SpeechRecognition (free)
    DISABLED = "disabled"


class TTSBackend(Enum):
    """Text-to-Speech backends."""
    PYTTSX3 = "pyttsx3"                # Offline, lightweight
    GOOGLE_TTS = "google_tts"          # Online, free
    EDGE_TTS = "edge_tts"              # Online via Edge (lightweight)
    DISABLED = "disabled"


# Auto-detect available backends on startup
AVAILABLE_STT_BACKENDS = []
AVAILABLE_TTS_BACKENDS = []


def _detect_available_backends():
    """Detect which voice backends are available on this system."""
    global AVAILABLE_STT_BACKENDS, AVAILABLE_TTS_BACKENDS
    
    # Check SpeechRecognition (for Google STT)
    try:
        import speech_recognition
        AVAILABLE_STT_BACKENDS.append(STTBackend.GOOGLE_SPEECH)
        logger.info("✓ SpeechRecognition available (Google STT)")
    except ImportError:
        logger.debug("SpeechRecognition not available")
    
    # Check pocketsphinx (offline STT)
    try:
        import pocketsphinx
        AVAILABLE_STT_BACKENDS.append(STTBackend.POCKETSPHINX)
        logger.info("✓ pocketsphinx available (offline STT)")
    except ImportError:
        logger.debug("pocketsphinx not available")
    
    # Check pyttsx3 (offline TTS)
    try:
        import pyttsx3
        AVAILABLE_TTS_BACKENDS.append(TTSBackend.PYTTSX3)
        logger.info("✓ pyttsx3 available (offline TTS)")
    except ImportError:
        logger.debug("pyttsx3 not available")
    
    # Check edge-tts (lightweight online TTS)
    try:
        import edge_tts
        AVAILABLE_TTS_BACKENDS.append(TTSBackend.EDGE_TTS)
        logger.info("✓ edge-tts available (online TTS)")
    except ImportError:
        logger.debug("edge-tts not available")
    
    # Google TTS is always available via gtts
    try:
        import gtts
        AVAILABLE_TTS_BACKENDS.append(TTSBackend.GOOGLE_TTS)
        logger.info("✓ gTTS available (online TTS)")
    except ImportError:
        logger.debug("gTTS not available")
    
    if not AVAILABLE_STT_BACKENDS:
        logger.warning("⚠ No STT backends detected (install: SpeechRecognition, pocketsphinx)")
    if not AVAILABLE_TTS_BACKENDS:
        logger.warning("⚠ No TTS backends detected (install: pyttsx3, edge-tts, or gtts)")


def transcribe_audio(
    audio_data: bytes,
    language: str = "en-US",
    backend: Optional[STTBackend] = None
) -> Tuple[bool, str]:
    """
    Convert audio to text using speech recognition.
    
    Args:
        audio_data: Raw audio bytes (WAV format)
        language: Language code (e.g., "en-US", "it-IT")
        backend: Preferred backend (will auto-select if None)
    
    Returns:
        (success: bool, result: str or error message)
    """
    if not backend:
        backend = _select_best_stt_backend()
    
    if backend == STTBackend.DISABLED or not backend:
        return False, "STT not available"
    
    try:
        if backend == STTBackend.GOOGLE_SPEECH:
            return _transcribe_google_speech(audio_data, language)
        elif backend == STTBackend.POCKETSPHINX:
            return _transcribe_pocketsphinx(audio_data, language)
        else:
            return False, f"Backend {backend.value} not implemented"
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return False, str(e)


def synthesize_speech(
    text: str,
    language: str = "en-US",
    backend: Optional[TTSBackend] = None
) -> Tuple[bool, bytes]:
    """
    Convert text to speech audio.
    
    Args:
        text: Text to synthesize
        language: Language code (e.g., "en-US", "it-IT")
        backend: Preferred backend (will auto-select if None)
    
    Returns:
        (success: bool, audio_bytes: WAV data or empty if failed)
    """
    if not backend:
        backend = _select_best_tts_backend()
    
    if backend == TTSBackend.DISABLED or not backend:
        return False, b""
    
    try:
        if backend == TTSBackend.PYTTSX3:
            return _synthesize_pyttsx3(text, language)
        elif backend == TTSBackend.EDGE_TTS:
            return _synthesize_edge_tts(text, language)
        elif backend == TTSBackend.GOOGLE_TTS:
            return _synthesize_google_tts(text, language)
        else:
            return False, b""
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return False, b""


def get_voice_config() -> Dict:
    """Get voice system configuration and available backends."""
    return {
        "enabled_stts": [b.value for b in AVAILABLE_STT_BACKENDS],
        "enabled_ttss": [b.value for b in AVAILABLE_TTS_BACKENDS],
        "preferred_stt": _select_best_stt_backend().value if _select_best_stt_backend() else "disabled",
        "preferred_tts": _select_best_tts_backend().value if _select_best_tts_backend() else "disabled",
        "audio_format": "WAV",
        "sample_rate": 16000,
        "channels": 1,
    }


# Private helper functions

def _select_best_stt_backend() -> Optional[STTBackend]:
    """Select best available STT backend (prefer offline > online)."""
    if STTBackend.POCKETSPHINX in AVAILABLE_STT_BACKENDS:
        return STTBackend.POCKETSPHINX
    if STTBackend.GOOGLE_SPEECH in AVAILABLE_STT_BACKENDS:
        return STTBackend.GOOGLE_SPEECH
    return None


def _select_best_tts_backend() -> Optional[TTSBackend]:
    """Select best available TTS backend (prefer offline > online)."""
    if TTSBackend.PYTTSX3 in AVAILABLE_TTS_BACKENDS:
        return TTSBackend.PYTTSX3
    if TTSBackend.EDGE_TTS in AVAILABLE_TTS_BACKENDS:
        return TTSBackend.EDGE_TTS
    if TTSBackend.GOOGLE_TTS in AVAILABLE_TTS_BACKENDS:
        return TTSBackend.GOOGLE_TTS
    return None


def _transcribe_google_speech(audio_data: bytes, language: str) -> Tuple[bool, str]:
    """Use SpeechRecognition with Google API (free)."""
    import speech_recognition as sr
    
    try:
        recognizer = sr.Recognizer()
        audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
        
        # Use Google free API (no key needed)
        text = recognizer.recognize_google(audio, language=language)
        logger.info(f"Transcribed (Google): {text[:50]}...")
        return True, text
    except sr.UnknownValueError:
        return False, "Could not understand audio"
    except sr.RequestError as e:
        return False, f"Google API error: {e}"


def _transcribe_pocketsphinx(audio_data: bytes, language: str) -> Tuple[bool, str]:
    """Use pocketsphinx for offline speech recognition."""
    try:
        from pocketsphinx import Decoder
        import wave
        from io import BytesIO
        
        # Parse WAV data
        wav = wave.open(BytesIO(audio_data), 'rb')
        frames = wav.readframes(wav.getnframes())
        
        # Initialize decoder (English only by default)
        decoder = Decoder()
        decoder.start_utt()
        decoder.process_raw(frames, False, True)
        decoder.end_utt()
        
        text = decoder.hyp().hypstr if decoder.hyp() else ""
        
        if text:
            logger.info(f"Transcribed (pocketsphinx offline): {text[:50]}...")
            return True, text
        else:
            return False, "No speech detected"
    except Exception as e:
        return False, f"Pocketsphinx error: {e}"


def _synthesize_pyttsx3(text: str, language: str) -> Tuple[bool, bytes]:
    """Use pyttsx3 for offline text-to-speech."""
    import pyttsx3
    from io import BytesIO
    import wave
    
    try:
        engine = pyttsx3.init()
        
        # Set language/voice
        voices = engine.getProperty('voices')
        # Try to select voice for language
        for voice in voices:
            if language.lower() in voice.languages[0].lower():
                engine.setProperty('voice', voice.id)
                break
        
        # Configure output
        engine.setProperty('rate', 150)  # Speed
        engine.setProperty('volume', 0.9)
        
        # Synthesize to file
        output = BytesIO()
        engine.save_to_file(text, '/tmp/voice_output.wav')
        engine.runAndWait()
        
        # Read the generated file
        with open('/tmp/voice_output.wav', 'rb') as f:
            audio_data = f.read()
        
        logger.info(f"Synthesized (pyttsx3 offline): {text[:50]}...")
        return True, audio_data
    except Exception as e:
        return False, b""


def _synthesize_edge_tts(text: str, language: str) -> Tuple[bool, bytes]:
    """Use edge-tts (Microsoft Azure) for online TTS (lightweight, free)."""
    import asyncio
    import edge_tts
    
    try:
        # Map language to voice
        language_map = {
            "en": "en-US-AriaNeural",
            "it": "it-IT-IsabellaNeural",
            "es": "es-ES-AlvaroNeural",
            "fr": "fr-FR-DeniseNeural",
        }
        voice = language_map.get(language[:2], "en-US-AriaNeural")
        
        # Synthesize
        async def tts():
            output = BytesIO()
            async for chunk in edge_tts.Communicate(text=text, voice=voice).stream():
                if chunk["type"] == "audio":
                    output.write(chunk["data"])
            return output.getvalue()
        
        audio_data = asyncio.run(tts())
        logger.info(f"Synthesized (edge-tts): {text[:50]}...")
        return True, audio_data
    except Exception as e:
        logger.error(f"edge-tts error: {e}")
        return False, b""


def _synthesize_google_tts(text: str, language: str) -> Tuple[bool, bytes]:
    """Use Google Text-to-Speech (gTTS) for online TTS."""
    from gtts import gTTS
    from io import BytesIO
    
    try:
        # Map language
        lang_map = {
            "en": "en",
            "it": "it",
            "es": "es",
            "fr": "fr",
        }
        lang = lang_map.get(language[:2], "en")
        
        # Create TTS
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Get audio
        output = BytesIO()
        tts.write_to_fp(output)
        audio_data = output.getvalue()
        
        logger.info(f"Synthesized (gTTS): {text[:50]}...")
        return True, audio_data
    except Exception as e:
        logger.error(f"gTTS error: {e}")
        return False, b""


# Initialize on module load
_detect_available_backends()
