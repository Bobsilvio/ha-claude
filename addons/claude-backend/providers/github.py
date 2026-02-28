"""GitHub Models provider adapter - uses OpenAI protocol with GitHub endpoints."""

import logging
from typing import Any, Dict, List, Optional, Generator

from .enhanced import EnhancedProvider
from .error_handler import ErrorTranslator
from .rate_limiter import get_rate_limit_coordinator

logger = logging.getLogger(__name__)


class GitHubProvider(EnhancedProvider):
    """Provider adapter for GitHub Models (OpenAI-compatible API).

    Inherits the standard _do_stream() from EnhancedProvider.
    INCLUDE_USAGE=False because GitHub Models API does not support stream_options.
    _get_model() strips the optional 'provider/' prefix from model names.
    """

    # --- Provider contract ---
    BASE_URL      = "https://models.github.ai/inference"
    DEFAULT_MODEL = "gpt-4o"
    INCLUDE_USAGE = False   # GitHub Models API rejects stream_options
    EXTRA_HEADERS = {"User-Agent": "ha-amira (python)"}
    # -------------------------

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize GitHub provider."""
        super().__init__(api_key, model)
        self.translator = ErrorTranslator()
        self.rate_limiter = None

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "github"

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate GitHub token is configured."""
        if not self.api_key:
            return False, "GitHub token not configured"
        return True, ""

    def _get_model(self) -> str:
        """Normalize model name: strip provider/ prefix (new GitHub Models API).

        The new API at models.github.ai/inference expects plain model IDs,
        e.g. 'gpt-4o-mini' not 'openai/gpt-4o-mini'.
        """
        m = self.model or self.DEFAULT_MODEL
        return m.split("/", 1)[1] if "/" in m else m

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat completion using GitHub Models API (OpenAI-compatible SSE)."""
        if not self.api_key:
            yield {"type": "error", "message": "GitHub: token not configured"}
            return

        if not self.rate_limiter:
            self.rate_limiter = get_rate_limit_coordinator().get_limiter(self.name)
        can_request, wait_time = self.rate_limiter.can_request()
        if not can_request:
            raise RuntimeError(f"Rate limited. Wait {wait_time:.0f}s")
        self.rate_limiter.record_request()

        yield from self.stream_chat_with_caching(messages, intent_info, max_retries=2)

    def get_available_models(self) -> List[str]:
        """Return list of available GitHub Models (new API, no provider prefix)."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "o1",
            "o3-mini",
            "meta-llama-3.1-405b-instruct",
            "meta-llama-3.1-70b-instruct",
            "mistral-large",
            "mistral-nemo",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get GitHub-specific error translations."""
        return {
            "auth_error": {
                "en": "GitHub: Token invalid or expired. Check your GitHub personal access token.",
                "it": "GitHub: Token non valido o scaduto. Controlla il tuo token di accesso personale GitHub.",
                "es": "GitHub: Token inválido o expirado. Comprueba tu token de acceso personal de GitHub.",
                "fr": "GitHub: Token invalide ou expiré. Vérifiez votre token d'accès personnel GitHub.",
            },
            "rate_limit": {
                "en": "GitHub: Rate limit exceeded. Please retry in a moment.",
                "it": "GitHub: Limite di velocità superato. Riprova tra un momento.",
                "es": "GitHub: Límite de velocidad excedido. Vuelva a intentarlo en un momento.",
                "fr": "GitHub: Limite de débit dépassée. Veuillez réessayer dans un instant.",
            },
            "model_not_found": {
                "en": "GitHub: Model not found or not yet available.",
                "it": "GitHub: Modello non trovato o non ancora disponibile.",
                "es": "GitHub: Modelo no encontrado o aún no disponible.",
                "fr": "GitHub: Modèle non trouvé ou pas encore disponible.",
            },
            "unknown_model": {
                "en": "GitHub: Model identifier not recognized by GitHub Models API.",
                "it": "GitHub: Identificatore modello non riconosciuto dall'API GitHub Models.",
                "es": "GitHub: Identificador de modelo no reconocido por la API de GitHub Models.",
                "fr": "GitHub: Identifiant de modèle non reconnu par l'API GitHub Models.",
            },
        }

    def normalize_error_message(self, error: Exception) -> str:
        """Convert GitHub Models API error to user-friendly message."""
        error_msg = str(error).lower()

        if "budget limit" in error_msg or "reached its budget" in error_msg or "spending limit" in error_msg:
            return "GitHub: 403 budget limit"  # let humanize_provider_error handle it with the right key
        if self._is_auth_error(error_msg):
            return "GitHub: Token invalid or expired. Check your GitHub personal access token in the add-on settings."
        if self._is_rate_limit_error(error_msg):
            return "GitHub: Rate limit exceeded. Please retry in a moment."
        if "model" in error_msg and "not found" in error_msg:
            return "GitHub: Model not found or not yet available."
        if "unknown" in error_msg:
            return "GitHub: Model identifier not recognized by GitHub Models API."

        return f"GitHub error: {error}"
