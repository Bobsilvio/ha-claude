"""OpenAI provider adapter with enhanced error handling and rate limiting.

Extends EnhancedProvider for automatic retry, caching, and intelligent fallback.
Supports OpenAI and OpenAI-compatible APIs (GitHub Models, Nvidia, etc.).
"""

import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class OpenAIProvider(EnhancedProvider):
    """Enhanced provider adapter for OpenAI and compatible APIs."""

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize OpenAI provider with enhanced features."""
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "openai"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate OpenAI API key is configured."""
        if not self.api_key:
            return False, "OpenAI API key not configured"
        return True, ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat with automatic retry, caching, and rate limiting.
        
        Features:
        - Automatic retry with exponential backoff
        - Integrated prompt caching from v3.17.11
        - Per-provider rate limit tracking
        - Supports OpenAI and compatible APIs
        """
        # Initialize rate limiter on first use
        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.name)
        
        # Check rate limit before streaming
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        
        # Record request for rate limiting
        self.rate_limiter.record_request()
        
        # Stream with automatic retry and caching integration
        try:
            yield from self.stream_chat_with_caching(messages, intent_info, max_retries=3)
        except Exception as e:
            logger.error(f"{self.name}: Error during streaming: {e}")
            raise

    def _do_stream(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """OpenAI API via the shared OpenAI-compatible streaming helper.

        This path supports native tool calling (`tool_calls`) and usage capture
        consistently with other API-key providers.
        """
        model = (self.model or "gpt-4o").replace("openai/", "")
        msgs = self._prepare_messages(messages, intent_info)
        tool_schemas = self._get_intent_tools(intent_info) or None
        _is_html_intent = bool(
            isinstance(intent_info, dict)
            and str(intent_info.get("intent", "")).lower() == "create_html_dashboard"
        )
        _max_tokens = 65536 if _is_html_intent else 32768
        yield from self._openai_compat_stream(
            "https://api.openai.com/v1",
            self.api_key,
            model,
            msgs,
            tools=tool_schemas,
            include_usage=True,
            max_tokens=_max_tokens,
        )

    def get_available_models(self) -> List[str]:
        """Return list of available OpenAI models."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1",
            "o1-mini",
            "o3-mini",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get OpenAI-specific error translations."""
        return {
            "rate_limit": {
                "en": "OpenAI: Rate limit exceeded. Please retry in a moment.",
                "it": "OpenAI: Limite di velocità superato. Riprova tra poco.",
                "es": "OpenAI: Límite de velocidad excedido. Intenta de nuevo en un momento.",
                "fr": "OpenAI: Limite de vitesse dépassée. Réessayez dans un moment.",
            },
            "auth_error": {
                "en": "OpenAI: API key invalid or missing. Check your OpenAI API key in settings.",
                "it": "OpenAI: Chiave API non valida o mancante. Controlla le impostazioni.",
                "es": "OpenAI: Clave API inválida o faltante. Verifica la configuración.",
                "fr": "OpenAI: Clé API invalide ou manquante. Vérifiez les paramètres.",
            },
            "quota_exceeded": {
                "en": "OpenAI: API quota or credits exceeded. Check your OpenAI account.",
                "it": "OpenAI: Quota API o crediti superati. Controlla il tuo account.",
                "es": "OpenAI: Cuota de API o créditos superados. Verifica tu cuenta.",
                "fr": "OpenAI: Quota ou crédits API dépassés. Vérifiez votre compte.",
            },
            "model_not_found": {
                "en": "OpenAI: Model not found or not available.",
                "it": "OpenAI: Modello non trovato o non disponibile.",
                "es": "OpenAI: Modelo no encontrado o no disponible.",
                "fr": "OpenAI: Modèle non trouvé ou indisponible.",
            },
            "context_length": {
                "en": "OpenAI: Message too long for the selected model. Try a shorter message.",
                "it": "OpenAI: Messaggio troppo lungo per il modello. Prova un messaggio più breve.",
                "es": "OpenAI: Mensaje demasiado largo para el modelo. Intenta un mensaje más corto.",
                "fr": "OpenAI: Message trop long pour le modèle. Essayez un message plus court.",
            },
        }
