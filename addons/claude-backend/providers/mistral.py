"""Mistral provider - Mistral AI open-source and commercial models.

Mistral provides both open-source models (via Hugging Face) and commercial API access.
"""

import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class MistralProvider(EnhancedProvider):
    """Provider adapter for Mistral AI API.

    Inherits the standard OpenAI-compatible _do_stream() from EnhancedProvider.
    No custom _do_stream() needed — tool calling, message prep and streaming
    are all handled by the base class.
    """

    # --- Provider contract: set these, get everything for free ---
    BASE_URL      = "https://api.mistral.ai/v1"
    DEFAULT_MODEL = "mistral-large-latest"
    INCLUDE_USAGE = True   # Mistral supports stream_options
    # -------------------------------------------------------------

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize Mistral provider."""
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "mistral"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate Mistral API key is configured."""
        if not self.api_key:
            return False, "Mistral API key not configured"
        return True, ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat completion using Mistral API."""
        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.name)
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        self.rate_limiter.record_request()
        yield from self.stream_chat_with_caching(messages, intent_info, max_retries=2)

    def get_available_models(self) -> List[str]:
        return [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mistral-nemo",
            "open-mistral-7b",
            "open-mixtral-8x7b",
            "open-mixtral-8x22b",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        return {
            "auth_error": {
                "en": "Mistral: API key invalid or missing. Check your Mistral API key in the add-on settings.",
                "it": "Mistral: Chiave API non valida o mancante. Controlla la chiave API Mistral nelle impostazioni del componente aggiuntivo.",
                "es": "Mistral: Clave API inválida o faltante. Comprueba tu clave API de Mistral en la configuración del complemento.",
                "fr": "Mistral: Clé API invalide ou manquante. Vérifiez votre clé API Mistral dans les paramètres du module complémentaire.",
            },
            "rate_limit": {
                "en": "Mistral: Rate limit exceeded. Please retry in a moment.",
                "it": "Mistral: Limite di velocità superato. Riprova tra un momento.",
                "es": "Mistral: Límite de velocidad excedido. Vuelva a intentarlo en un momento.",
                "fr": "Mistral: Limite de débit dépassée. Veuillez réessayer dans un instant.",
            },
            "model_not_found": {
                "en": "Mistral: Model not found or not available.",
                "it": "Mistral: Modello non trovato o non disponibile.",
                "es": "Mistral: Modelo no encontrado o no disponible.",
                "fr": "Mistral: Modèle non trouvé ou non disponible.",
            },
        }

    def normalize_error_message(self, error: Exception) -> str:
        error_msg = str(error).lower()
        if self._is_auth_error(error_msg):
            return "Mistral: API key invalid or missing. Check your Mistral API key in the add-on settings."
        if self._is_rate_limit_error(error_msg):
            return "Mistral: Rate limit exceeded. Please retry in a moment."
        if "model" in error_msg:
            return "Mistral: Model not found or not available."
        return f"Mistral error: {error}"
