"""NVIDIA NIM provider adapter - uses OpenAI protocol with NVIDIA endpoints."""

import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class NVIDIAProvider(EnhancedProvider):
    """Provider adapter for NVIDIA NIM API (OpenAI-compatible).

    Inherits the standard _do_stream() from EnhancedProvider.
    INCLUDE_USAGE=False because NIM rejects stream_options.
    """

    # --- Provider contract ---
    BASE_URL      = "https://integrate.api.nvidia.com/v1"
    DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"
    INCLUDE_USAGE = False   # NIM rejects stream_options
    # -------------------------

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize NVIDIA provider."""
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "nvidia"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate NVIDIA API key is configured."""
        if not self.api_key:
            return False, "NVIDIA API key not configured"
        return True, ""

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat completion using NVIDIA NIM API.
        
        NVIDIA provides two interfaces:
        1. Direct streaming via stream_chat_nvidia_direct() for thinking models
        2. OpenAI-compatible via stream_chat_openai() with nvidia endpoint
        
        This adapter uses the enhanced streaming with rate limiting.
        """
        # Rate limiting check
        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.name)
        
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        
        self.rate_limiter.record_request()
        
        # Use enhanced caching and retry
        yield from self.stream_chat_with_caching(messages, intent_info, max_retries=2)

    def get_available_models(self) -> List[str]:
        """
        Note: NVIDIA models are fetched dynamically from the API.
        This returns common/recent models as fallback.
        """
        return [
            "moonshotai/kimi-k2.5",
            "meta/llama-3.1-405b-instruct",
            "meta/llama-3.1-70b-instruct",
            "mistralai/mixtral-8x22b-instruct-v0.1",
            "mistralai/mistral-large",
            "nvidia/llama-3.1-nemotron-70b-instruct",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get NVIDIA-specific error translations."""
        return {
            "auth_error": {
                "en": "NVIDIA: API key invalid or missing. Check your NVIDIA API key in the add-on settings.",
                "it": "NVIDIA: Chiave API non valida o mancante. Controlla la chiave API NVIDIA nelle impostazioni del componente aggiuntivo.",
                "es": "NVIDIA: Clave API inválida o faltante. Comprueba tu clave API de NVIDIA en la configuración del complemento.",
                "fr": "NVIDIA: Clé API invalide ou manquante. Vérifiez votre clé API NVIDIA dans les paramètres du module complémentaire.",
            },
            "rate_limit": {
                "en": "NVIDIA: Rate limit exceeded. Please retry in a moment.",
                "it": "NVIDIA: Limite di velocità superato. Riprova tra un momento.",
                "es": "NVIDIA: Límite de velocidad excedido. Vuelva a intentarlo en un momento.",
                "fr": "NVIDIA: Limite de débit dépassée. Veuillez réessayer dans un instant.",
            },
            "model_not_found": {
                "en": "NVIDIA: Model not found or not available. Try testing models from the settings.",
                "it": "NVIDIA: Modello non trovato o non disponibile. Prova a testare i modelli dalle impostazioni.",
                "es": "NVIDIA: Modelo no encontrado o no disponible. Intenta probar modelos desde la configuración.",
                "fr": "NVIDIA: Modèle non trouvé ou non disponible. Essayez de tester les modèles à partir des paramètres.",
            },
            "quota_exceeded": {
                "en": "NVIDIA: Model quota exceeded or not available (404). Try another model.",
                "it": "NVIDIA: Quota modello superata o non disponibile (404). Prova un altro modello.",
                "es": "NVIDIA: Cuota de modelo superada o no disponible (404). Prueba otro modelo.",
                "fr": "NVIDIA: Quota de modèle dépassé ou non disponible (404). Essayez un autre modèle.",
            },
        }

    def normalize_error_message(self, error: Exception) -> str:
        """Convert NVIDIA API error to user-friendly message."""
        error_msg = str(error).lower()

        if self._is_auth_error(error_msg):
            return "NVIDIA: API key invalid or missing. Check your NVIDIA API key in the add-on settings."
        if self._is_rate_limit_error(error_msg):
            return "NVIDIA: Rate limit exceeded. Please retry in a moment."
        if "model" in error_msg and "not found" in error_msg:
            return "NVIDIA: Model not found or not available. Try testing models from the settings."
        if "404" in error_msg:
            return "NVIDIA: Model not available (404). Try another model."

        return f"NVIDIA error: {error}"
