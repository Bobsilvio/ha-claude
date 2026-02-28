"""Unified error handling and normalization for all providers.

This module provides:
- Common error detection (rate limits, auth, quota, etc.)
- Multilingual error translations
- Provider-specific error mapping
- Error recovery strategies
"""

import logging
from typing import Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of provider errors."""
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class ErrorTranslator:
    """Translates provider-specific errors to user-friendly messages."""

    LANGUAGES = ["en", "it", "es", "fr"]
    DEFAULT_LANGUAGE = "en"

    # Common error patterns per provider
    ANTHROPIC_ERRORS = {
        "usage_limits": ErrorType.QUOTA_EXCEEDED,
        "overloaded": ErrorType.SERVER_ERROR,
        "authentication": ErrorType.AUTH_ERROR,
        "invalid api key": ErrorType.AUTH_ERROR,
        "429": ErrorType.RATE_LIMIT,
    }

    OPENAI_ERRORS = {
        "rate_limit": ErrorType.RATE_LIMIT,
        "quota_limit": ErrorType.QUOTA_EXCEEDED,
        "401": ErrorType.AUTH_ERROR,
        "invalid_auth_header": ErrorType.AUTH_ERROR,
        "502": ErrorType.SERVER_ERROR,
        "service_unavailable": ErrorType.SERVER_ERROR,
    }

    GOOGLE_ERRORS = {
        "PERMISSION_DENIED": ErrorType.AUTH_ERROR,
        "RESOURCE_EXHAUSTED": ErrorType.QUOTA_EXCEEDED,
        "DEADLINE_EXCEEDED": ErrorType.NETWORK_ERROR,
        "UNAVAILABLE": ErrorType.SERVER_ERROR,
    }

    TRANSLATIONS = {
        ErrorType.RATE_LIMIT: {
            "en": "Rate limit exceeded. Please try again in a moment.",
            "it": "Limite di velocità superato. Riprova tra poco.",
            "es": "Límite de velocidad excedido. Intenta de nuevo en un momento.",
            "fr": "Limite de vitesse dépassée. Réessayez dans un moment.",
        },
        ErrorType.AUTH_ERROR: {
            "en": "Authentication failed. Check your API key.",
            "it": "Autenticazione fallita. Controlla la tua chiave API.",
            "es": "Falló la autenticación. Verifica tu clave de API.",
            "fr": "L'authentification a échoué. Vérifiez votre clé API.",
        },
        ErrorType.QUOTA_EXCEEDED: {
            "en": "Usage limit exceeded. Upgrade your plan or try later.",
            "it": "Limite di utilizzo superato. Aggiorna il tuo piano o riprova più tardi.",
            "es": "Límite de uso excedido. Actualiza tu plan o intenta más tarde.",
            "fr": "Limite d'utilisation dépassée. Mettez à niveau votre plan ou réessayez plus tard.",
        },
        ErrorType.INVALID_REQUEST: {
            "en": "Invalid request. Please check your input.",
            "it": "Richiesta non valida. Controlla il tuo input.",
            "es": "Solicitud inválida. Por favor, verifica tu entrada.",
            "fr": "Demande invalide. Veuillez vérifier votre saisie.",
        },
        ErrorType.SERVER_ERROR: {
            "en": "Server error. Please try again.",
            "it": "Errore del server. Riprova.",
            "es": "Error del servidor. Por favor, intenta de nuevo.",
            "fr": "Erreur du serveur. Veuillez réessayer.",
        },
        ErrorType.NETWORK_ERROR: {
            "en": "Network error. Check your connection and try again.",
            "it": "Errore di rete. Controlla la tua connessione e riprova.",
            "es": "Error de red. Verifica tu conexión e intenta de nuevo.",
            "fr": "Erreur réseau. Vérifiez votre connexion et réessayez.",
        },
        ErrorType.UNKNOWN: {
            "en": "An error occurred. Please try again.",
            "it": "Si è verificato un errore. Riprova.",
            "es": "Ocurrió un error. Por favor intenta de nuevo.",
            "fr": "Une erreur s'est produite. Veuillez réessayer.",
        },
    }

    @classmethod
    def classify_error(
        cls,
        error_msg: str,
        provider: str = "generic"
    ) -> ErrorType:
        """Classify error by provider-specific patterns.
        
        Args:
            error_msg: Error message from provider
            provider: Provider name ('anthropic', 'openai', 'google', etc.)
            
        Returns:
            ErrorType classification
        """
        msg_lower = (error_msg or "").lower()

        # Select provider-specific patterns
        patterns = {}
        if provider == "anthropic":
            patterns = cls.ANTHROPIC_ERRORS
        elif provider == "openai":
            patterns = cls.OPENAI_ERRORS
        elif provider == "google":
            patterns = cls.GOOGLE_ERRORS

        # Check patterns
        for pattern, error_type in patterns.items():
            if pattern.lower() in msg_lower:
                return error_type

        # Fallback to generic patterns - order matters!
        # Check RATE_LIMIT first (more specific than LIMIT)
        if "429" in msg_lower or "too many requests" in msg_lower or "rate limit" in msg_lower or "ratelimit" in msg_lower:
            return ErrorType.RATE_LIMIT
        # Check AUTH before other codes/messages
        if "401" in msg_lower or "403" in msg_lower or "unauthorized" in msg_lower or "invalid api key" in msg_lower or "authentication failed" in msg_lower:
            return ErrorType.AUTH_ERROR
        # Check SERVER errors
        if "500" in msg_lower or "502" in msg_lower or "503" in msg_lower or "internal server error" in msg_lower or "bad gateway" in msg_lower or "service unavailable" in msg_lower:
            return ErrorType.SERVER_ERROR
        # Check NETWORK errors
        if "timeout" in msg_lower or "connection" in msg_lower:
            return ErrorType.NETWORK_ERROR
        # Check QUOTA (more specific patterns after generic ones)
        if "quota" in msg_lower or "usage limit" in msg_lower or "monthly limit" in msg_lower:
            return ErrorType.QUOTA_EXCEEDED
        # Generic INVALID_REQUEST
        if "400" in msg_lower or "invalid" in msg_lower:
            return ErrorType.INVALID_REQUEST

        return ErrorType.UNKNOWN

    @classmethod
    def translate_error(
        cls,
        error_msg: str,
        provider: str = "generic",
        language: str = DEFAULT_LANGUAGE,
    ) -> str:
        """Translate error to user-friendly message.
        
        Args:
            error_msg: Raw error message
            provider: Provider name for pattern matching
            language: Target language code
            
        Returns:
            User-friendly translated error message
        """
        if language not in cls.LANGUAGES:
            language = cls.DEFAULT_LANGUAGE

        # Classify error
        error_type = cls.classify_error(error_msg, provider)

        # Get translation
        translation = cls.TRANSLATIONS.get(error_type, {})
        user_msg = translation.get(language, translation.get(cls.DEFAULT_LANGUAGE, "An error occurred."))

        # Add context
        return f"{provider}: {user_msg}"

    @classmethod
    def is_retryable(cls, error_msg: str, provider: str = "generic") -> bool:
        """Check if error is retryable.
        
        Args:
            error_msg: Error message
            provider: Provider name
            
        Returns:
            True if error should trigger a retry
        """
        error_type = cls.classify_error(error_msg, provider)

        # Retryable error types
        retryable = {
            ErrorType.RATE_LIMIT,
            ErrorType.SERVER_ERROR,
            ErrorType.NETWORK_ERROR,
        }

        return error_type in retryable


class ErrorRecoveryStrategy:
    """Strategies for recovering from different error types."""

    @staticmethod
    def get_backoff_delay(retry_count: int, error_type: ErrorType) -> float:
        """Calculate backoff delay based on error type.
        
        Args:
            retry_count: Current retry attempt (0-indexed)
            error_type: Type of error
            
        Returns:
            Delay in seconds before retry
        """
        base_delay = {
            ErrorType.RATE_LIMIT: 2.0,      # Longer delay for rate limits
            ErrorType.SERVER_ERROR: 1.0,    # Standard delay for server errors
            ErrorType.NETWORK_ERROR: 0.5,   # Quick retry for network
            ErrorType.UNKNOWN: 1.0,         # Default
        }.get(error_type, 1.0)

        # Exponential backoff: delay * (2 ^ retry_count)
        return base_delay * (2 ** min(retry_count, 5))  # Cap at 2^5

    @staticmethod
    def get_max_retries(error_type: ErrorType) -> int:
        """Get maximum retry attempts for error type.
        
        Args:
            error_type: Type of error
            
        Returns:
            Maximum retry attempts
        """
        return {
            ErrorType.RATE_LIMIT: 3,
            ErrorType.SERVER_ERROR: 2,
            ErrorType.NETWORK_ERROR: 2,
            ErrorType.AUTH_ERROR: 0,        # Don't retry auth errors
            ErrorType.QUOTA_EXCEEDED: 0,    # Don't retry quota errors
            ErrorType.INVALID_REQUEST: 0,   # Don't retry invalid requests
            ErrorType.UNKNOWN: 1,
        }.get(error_type, 1)

    @staticmethod
    def get_mitigation_action(error_type: ErrorType) -> Optional[str]:
        """Get suggested mitigation action for error.
        
        Args:
            error_type: Type of error
            
        Returns:
            Suggested action message or None
        """
        actions = {
            ErrorType.RATE_LIMIT: "Consider switching to a different provider or waiting before retrying.",
            ErrorType.QUOTA_EXCEEDED: "Upgrade your API plan or increase available credits.",
            ErrorType.AUTH_ERROR: "Verify your API key is correct and has required permissions.",
            ErrorType.SERVER_ERROR: "The provider's service is experiencing issues. Try again in a moment.",
            ErrorType.NETWORK_ERROR: "Check your internet connection and try again.",
        }
        return actions.get(error_type)


class ProviderErrorHandler:
    """Unified error handler for all providers."""

    def __init__(self, provider_name: str, language: str = "en"):
        """Initialize error handler.
        
        Args:
            provider_name: Name of provider
            language: User language for translations
        """
        self.provider = provider_name
        self.language = language
        self.translator = ErrorTranslator()
        self.recovery = ErrorRecoveryStrategy()
        self.error_history = []

    def handle_error(
        self,
        error: Exception,
        retry_attempt: int = 0,
    ) -> Dict[str, any]:
        """Handle an error comprehensively.
        
        Args:
            error: The exception that occurred
            retry_attempt: Current retry attempt
            
        Returns:
            Dictionary with error details and recovery info
        """
        error_msg = str(error)
        error_type = self.translator.classify_error(error_msg, self.provider)

        # Translate message
        user_message = self.translator.translate_error(
            error_msg,
            self.provider,
            self.language
        )

        # Determine recovery strategy
        is_retryable = self.translator.is_retryable(error_msg, self.provider)
        max_retries = self.recovery.get_max_retries(error_type)
        should_retry = is_retryable and retry_attempt < max_retries

        if should_retry:
            backoff_delay = self.recovery.get_backoff_delay(retry_attempt, error_type)
        else:
            backoff_delay = 0

        result = {
            "provider": self.provider,
            "error_type": error_type.value,
            "original_error": error_msg,
            "user_message": user_message,
            "is_retryable": is_retryable,
            "should_retry": should_retry,
            "retry_attempt": retry_attempt,
            "max_retries": max_retries,
            "backoff_delay": backoff_delay,
            "mitigation_action": self.recovery.get_mitigation_action(error_type),
        }

        # Record in history
        self.error_history.append(result)

        logger.warning(
            f"ProviderErrorHandler({self.provider}): {error_type.value} - "
            f"retry={should_retry} (attempt {retry_attempt}/{max_retries})"
        )

        return result

    def get_error_summary(self) -> Dict[str, any]:
        """Get summary of error history."""
        if not self.error_history:
            return {"errors": 0, "error_types": {}}

        error_types = {}
        for error in self.error_history:
            et = error["error_type"]
            error_types[et] = error_types.get(et, 0) + 1

        return {
            "provider": self.provider,
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "last_error": self.error_history[-1] if self.error_history else None,
        }
