"""Base class for all AI provider implementations."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Abstract base class for all AI providers (Chat APIs, Vision, etc.)."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize provider with API key and model.
        
        Args:
            api_key: API key for the provider (provider-specific format)
            model: Model identifier (provider-specific format)
        """
        self.api_key = api_key
        self.model = model
        self.name = self.get_provider_name()

    @staticmethod
    @abstractmethod
    def get_provider_name() -> str:
        """Return the provider identifier (e.g., 'openai', 'anthropic', etc.)."""
        pass

    @abstractmethod
    def validate_credentials(self) -> tuple[bool, str]:
        """Validate that the provider credentials are valid.
        
        Returns:
            (is_valid, error_message) tuple
        """
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream a chat completion response.
        
        Args:
            messages: Conversation history in OpenAI format
            intent_info: Optional intent information for focused responses
            
        Yields:
            Event dictionaries with keys:
            - type: 'status', 'content', 'tool_call', 'done', 'error'
            - message: status/error message or content chunk
            - usage: token usage info in 'done' event
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Return list of available models for this provider."""
        pass

    def normalize_error_message(self, error: Exception) -> str:
        """Convert provider-specific error to user-friendly message.
        
        Override in subclasses for provider-specific error handling.
        """
        return str(error)

    def _format_event(
        self,
        event_type: str,
        message: Optional[str] = None,
        content: Optional[str] = None,
        tool_call: Optional[Dict] = None,
        usage: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Format a standard event for yielding.
        
        Args:
            event_type: One of 'status', 'content', 'tool_call', 'done', 'error'
            message: Status or error message
            content: Content chunk
            tool_call: Tool call information
            usage: Token usage information
            
        Returns:
            Formatted event dict
        """
        event: Dict[str, Any] = {"type": event_type}

        if message is not None:
            event["message"] = message
        if content is not None:
            event["content"] = content
        if tool_call is not None:
            event["tool_call"] = tool_call
        if usage is not None:
            event["usage"] = usage

        return event

    @staticmethod
    def _is_rate_limit_error(error_msg: str) -> bool:
        """Check if error indicates rate limiting.
        
        Common patterns across providers:
        - HTTP 429
        - 'too many requests'
        - 'rate limit' variations
        """
        msg = (error_msg or "").lower()
        # Permanent billing/quota errors — NOT retryable
        if (
            "insufficient_quota" in msg
            or "exceeded your current quota" in msg
            or "quota esaurita" in msg
            or "resource_exhausted" in msg
        ):
            return False
        return (
            "429" in msg
            or "too many requests" in msg
            or "rate limit" in msg
            or "ratelimit" in msg
            or "rate_limit_exceeded" in msg
        )

    @staticmethod
    def _is_auth_error(error_msg: str) -> bool:
        """Check if error indicates authentication failure."""
        msg = (error_msg or "").lower()
        return (
            "401" in msg
            or "403" in msg
            or "unauthorized" in msg
            or "authentication" in msg
            or "invalid api key" in msg
            or "api key" in msg
        )

    @staticmethod
    def _is_quota_error(error_msg: str) -> bool:
        """Check if error indicates quota/usage limit exceeded."""
        msg = (error_msg or "").lower()
        return (
            "quota" in msg
            or "limit" in msg
            or "exceeded" in msg
            or "overage" in msg
            or "usage" in msg
        )


class TextToSpeechProvider(ABC):
    """Abstract base class for Text-to-Speech providers."""

    def __init__(self, api_key: str = ""):
        """Initialize TTS provider with API key."""
        self.api_key = api_key
        self.name = self.get_provider_name()

    @staticmethod
    @abstractmethod
    def get_provider_name() -> str:
        """Return the provider identifier."""
        pass

    @abstractmethod
    def generate_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """Generate speech audio from text.
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'en', 'it')
            
        Returns:
            Audio bytes (MP3 or WAV), or None on error
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> tuple[bool, str]:
        """Validate TTS provider credentials."""
        pass


class VisionProvider(ABC):
    """Abstract base class for Vision/Image analysis providers."""

    def __init__(self, api_key: str = ""):
        """Initialize Vision provider with API key."""
        self.api_key = api_key
        self.name = self.get_provider_name()

    @staticmethod
    @abstractmethod
    def get_provider_name() -> str:
        """Return the provider identifier."""
        pass

    @abstractmethod
    def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        image_format: str = "jpeg",
    ) -> Optional[str]:
        """Analyze an image and return text description.
        
        Args:
            image_data: Raw image bytes
            prompt: Analysis prompt/question
            image_format: Image format ('jpeg', 'png', 'gif', 'webp')
            
        Returns:
            Analysis result text, or None on error
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> tuple[bool, str]:
        """Validate Vision provider credentials."""
        pass


class TranscriptionProvider(ABC):
    """Abstract base class for Speech-to-Text providers."""

    def __init__(self, api_key: str = ""):
        """Initialize transcription provider with API key."""
        self.api_key = api_key
        self.name = self.get_provider_name()

    @staticmethod
    @abstractmethod
    def get_provider_name() -> str:
        """Return the provider identifier."""
        pass

    @abstractmethod
    def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "mp3",
        language: str = "auto",
    ) -> Optional[str]:
        """Transcribe audio to text.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format ('mp3', 'wav', 'ogg', 'flac', etc.)
            language: Language code or 'auto' for auto-detection
            
        Returns:
            Transcribed text, or None on error
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> tuple[bool, str]:
        """Validate transcription provider credentials."""
        pass
