#!/usr/bin/env python3
"""
Voice Transcription Module (Groq Whisper + Fallback Providers)

Supports:
- Groq Whisper (primary)
- OpenAI Whisper (fallback)
- Google Speech-to-Text (fallback)

Also provides:
- Text-to-Speech (Groq, OpenAI, Google)
- Audio format detection and conversion
"""

import os
import io
import json
import base64
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Any, List
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"
    M4A = "m4a"
    WEBM = "webm"
    AAC = "aac"


class TranscriptionProvider(Enum):
    """Available transcription providers."""
    GROQ = "groq"
    OPENAI = "openai"
    GOOGLE = "google"


class VoiceTranscriber:
    """Transcribe audio to text."""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.transcription_cache: Dict[str, Dict[str, Any]] = {}
        self.provider_order = [
            TranscriptionProvider.GROQ,
            TranscriptionProvider.OPENAI,
            TranscriptionProvider.GOOGLE,
        ]
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds (approximate)."""
        try:
            size = os.path.getsize(audio_path)
            # Rough estimate: bitrate ~128kbps = 16000 bytes per second
            return size / 16000
        except:
            return 0.0
    
    def _get_audio_format(self, audio_path: str) -> Optional[AudioFormat]:
        """Detect audio format from file extension."""
        ext = Path(audio_path).suffix.lower().lstrip(".")
        for fmt in AudioFormat:
            if fmt.value == ext:
                return fmt
        return None
    
    def transcribe_with_groq(self, audio_path: str) -> Tuple[bool, str]:
        """Transcribe using Groq Whisper API."""
        if not self.groq_api_key:
            return False, "Groq API key not configured"
        
        try:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            
            audio_fmt = self._get_audio_format(audio_path)
            mime = f"audio/{audio_fmt.value}" if audio_fmt else "audio/wav"
            filename = Path(audio_path).name
            
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (filename, audio_file, mime),
                }
                data = {
                    "model": "whisper-large-v3-turbo",
                    "language": "it",  # Italian by default
                }
                headers = {"Authorization": f"Bearer {self.groq_api_key}"}
                
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("text", "")
                    logger.info(f"Groq transcription: {len(text)} chars")
                    return True, text
                else:
                    error = response.json().get("error", {}).get("message", "Unknown error")
                    return False, f"Groq error: {error}"
        except Exception as e:
            logger.error(f"Groq transcription error: {e}")
            return False, str(e)
    
    def transcribe_with_openai(self, audio_path: str) -> Tuple[bool, str]:
        """Transcribe using OpenAI Whisper API."""
        if not self.openai_api_key:
            return False, "OpenAI API key not configured"
        
        try:
            url = "https://api.openai.com/v1/audio/transcriptions"
            
            audio_fmt = self._get_audio_format(audio_path)
            mime = f"audio/{audio_fmt.value}" if audio_fmt else "audio/wav"
            filename = Path(audio_path).name
            
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (filename, audio_file, mime),
                }
                data = {
                    "model": "whisper-1",
                    "language": "it",
                }
                headers = {"Authorization": f"Bearer {self.openai_api_key}"}
                
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("text", "")
                    logger.info(f"OpenAI transcription: {len(text)} chars")
                    return True, text
                else:
                    error = response.json().get("error", {}).get("message", "Unknown error")
                    return False, f"OpenAI error: {error}"
        except Exception as e:
            logger.error(f"OpenAI transcription error: {e}")
            return False, str(e)
    
    def transcribe_with_google(self, audio_path: str) -> Tuple[bool, str]:
        """Transcribe using Google Speech-to-Text API."""
        if not self.google_api_key:
            return False, "Google API key not configured"
        
        try:
            url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.google_api_key}"
            
            # Read audio file
            with open(audio_path, "rb") as f:
                audio_content = base64.b64encode(f.read()).decode("utf-8")
            
            payload = {
                "config": {
                    "encoding": "LINEAR16",
                    "languageCode": "it-IT",
                    "model": "latest_long",
                },
                "audio": {
                    "content": audio_content,
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                results = result.get("results", [])
                # Concatenate all transcriptions
                text = " ".join(
                    alt.get("transcript", "")
                    for result in results
                    for alt in result.get("alternatives", [])
                )
                logger.info(f"Google transcription: {len(text)} chars")
                return True, text
            else:
                error = response.json().get("error", {}).get("message", "Unknown error")
                return False, f"Google error: {error}"
        except Exception as e:
            logger.error(f"Google transcription error: {e}")
            return False, str(e)
    
    def transcribe_with_fallback(self, audio_path: str) -> Tuple[bool, str, str]:
        """
        Transcribe with automatic fallback between providers.
        Returns: (success, text, provider_used)
        """
        if not os.path.exists(audio_path):
            return False, "", "none"
        
        # Check cache first
        audio_hash = self._hash_file(audio_path)
        if audio_hash in self.transcription_cache:
            cached = self.transcription_cache[audio_hash]
            if datetime.fromisoformat(cached["timestamp"]) > datetime.now() - timedelta(hours=24):
                logger.info(f"Transcription cache hit")
                return True, cached["text"], f"{cached['provider']} (cached)"
        
        # Try providers in order
        for provider in self.provider_order:
            if provider == TranscriptionProvider.GROQ:
                success, text = self.transcribe_with_groq(audio_path)
            elif provider == TranscriptionProvider.OPENAI:
                success, text = self.transcribe_with_openai(audio_path)
            elif provider == TranscriptionProvider.GOOGLE:
                success, text = self.transcribe_with_google(audio_path)
            else:
                continue
            
            if success:
                # Cache result
                self.transcription_cache[audio_hash] = {
                    "text": text,
                    "provider": provider.value,
                    "timestamp": datetime.now().isoformat(),
                    "duration_seconds": self._get_audio_duration(audio_path),
                }
                logger.info(f"Transcription successful with {provider.value}")
                return True, text, provider.value
        
        return False, "All transcription providers failed", "none"
    
    @staticmethod
    def _hash_file(filepath: str) -> str:
        """Get SHA256 hash of file."""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            sha256_hash.update(f.read())
        return sha256_hash.hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transcription statistics."""
        return {
            "cache_size": len(self.transcription_cache),
            "providers_available": {
                "groq": bool(self.groq_api_key),
                "openai": bool(self.openai_api_key),
                "google": bool(self.google_api_key),
            },
            "cached_transcriptions": [
                {
                    "provider": v["provider"],
                    "duration": v["duration_seconds"],
                    "timestamp": v["timestamp"]
                }
                for v in list(self.transcription_cache.values())[-5:]
            ]
        }


class TextToSpeech:
    """Convert text to speech."""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
    
    def speak_with_openai(self, text: str, voice: str = "nova") -> Tuple[bool, bytes]:
        """Generate speech using OpenAI TTS."""
        if not self.openai_api_key:
            return False, b""
        
        try:
            url = "https://api.openai.com/v1/audio/speech"
            
            payload = {
                "model": "tts-1",
                "input": text,
                "voice": voice,
            }
            headers = {"Authorization": f"Bearer {self.openai_api_key}"}
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"OpenAI TTS: {len(text)} chars -> audio")
                return True, response.content
            else:
                return False, b""
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return False, b""
    
    def speak_with_google(self, text: str, language: str = "it-IT") -> Tuple[bool, bytes]:
        """Generate speech using Google TTS."""
        if not self.google_api_key:
            return False, b""
        
        try:
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.google_api_key}"
            
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": language,
                    "name": f"{language}-Neural2-A",
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                audio_content = base64.b64decode(result["audioContent"])
                logger.info(f"Google TTS: {len(text)} chars -> audio")
                return True, audio_content
            else:
                return False, b""
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return False, b""
    
    def speak_with_fallback(self, text: str, provider_order: Optional[List[str]] = None) -> Tuple[bool, bytes]:
        """
        Generate speech with automatic fallback.
        Returns: (success, audio_bytes)
        """
        if not provider_order:
            provider_order = ["openai", "google"]
        
        for provider in provider_order:
            if provider == "openai":
                success, audio = self.speak_with_openai(text)
            elif provider == "google":
                success, audio = self.speak_with_google(text)
            else:
                continue
            
            if success:
                logger.info(f"TTS successful with {provider}")
                return True, audio
        
        return False, b""


# Global instances
_voice_transcriber: Optional[VoiceTranscriber] = None
_text_to_speech: Optional[TextToSpeech] = None


def initialize_voice_system() -> Tuple[VoiceTranscriber, TextToSpeech]:
    """Initialize voice transcription and TTS."""
    global _voice_transcriber, _text_to_speech
    _voice_transcriber = VoiceTranscriber()
    _text_to_speech = TextToSpeech()
    logger.info("Voice transcription and TTS initialized")
    return _voice_transcriber, _text_to_speech


def get_voice_transcriber() -> Optional[VoiceTranscriber]:
    """Get global transcriber instance."""
    if _voice_transcriber is None:
        initialize_voice_system()
    return _voice_transcriber


def get_text_to_speech() -> Optional[TextToSpeech]:
    """Get global TTS instance."""
    if _text_to_speech is None:
        initialize_voice_system()
    return _text_to_speech


if __name__ == "__main__":
    # Quick demo
    logging.basicConfig(level=logging.INFO)
    
    transcriber = VoiceTranscriber()
    print("Voice Transcriber Stats:", json.dumps(transcriber.get_stats(), indent=2))
    
    tts = TextToSpeech()
    print("\nTTS available:", tts.speak_with_fallback("Ciao, questo è un test"))
