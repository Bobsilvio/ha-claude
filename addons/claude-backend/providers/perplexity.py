"""Perplexity provider - Sonar models with real-time web search.

Perplexity AI offers a unique API that combines LLM responses with live web search.
Uses an OpenAI-compatible format.

Models:
- sonar / sonar-pro       → conversational models with web search (Pro = higher quality)
- sonar-reasoning / sonar-reasoning-pro → reasoning + web search
- r1-1776                 → offline reasoning model (no web search, DeepSeek R1-based)
"""

import logging
from typing import Dict, List

from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class PerplexityProvider(OpenAICompatibleProvider):
    """Provider adapter for Perplexity AI (Sonar models with web search)."""

    # --- Provider contract ---
    BASE_URL      = "https://api.perplexity.ai"
    DEFAULT_MODEL = "sonar-pro"
    INCLUDE_USAGE = True
    # -------------------------

    def __init__(self, api_key: str = "", model: str = ""):
        """Initialize Perplexity provider."""
        super().__init__(
            api_key=api_key,
            model=model,
            provider_name="perplexity",
            api_base="https://api.perplexity.ai",
        )

    @staticmethod
    def get_provider_name() -> str:
        """Return provider identifier."""
        return "perplexity"

    def get_available_models(self) -> List[str]:
        """Return list of available Perplexity Sonar models."""
        return [
            # Search models (real-time web)
            "sonar-pro",
            "sonar",
            # Reasoning models (web search + chain-of-thought)
            "sonar-reasoning-pro",
            "sonar-reasoning",
            # Offline reasoning (no web search, DeepSeek R1-based)
            "r1-1776",
        ]

    def get_error_translations(self) -> Dict[str, Dict[str, str]]:
        """Get Perplexity-specific error translations."""
        return {
            "auth_error": {
                "en": "Perplexity: API key invalid or missing. Check your Perplexity API key in the add-on settings.",
                "it": "Perplexity: Chiave API non valida o mancante. Controlla la chiave API Perplexity nelle impostazioni.",
                "es": "Perplexity: Clave API inválida o faltante. Comprueba tu clave API de Perplexity en la configuración.",
                "fr": "Perplexity: Clé API invalide ou manquante. Vérifiez votre clé API Perplexity dans les paramètres.",
            },
            "rate_limit": {
                "en": "Perplexity: Rate limit exceeded. Please retry in a moment.",
                "it": "Perplexity: Limite di velocità superato. Riprova tra un momento.",
                "es": "Perplexity: Límite de velocidad excedido. Vuelva a intentarlo en un momento.",
                "fr": "Perplexity: Limite de débit dépassée. Veuillez réessayer dans un instant.",
            },
            "model_not_found": {
                "en": "Perplexity: Model not found. Check the model name in settings.",
                "it": "Perplexity: Modello non trovato. Controlla il nome del modello nelle impostazioni.",
                "es": "Perplexity: Modelo no encontrado. Comprueba el nombre del modelo en la configuración.",
                "fr": "Perplexity: Modèle non trouvé. Vérifiez le nom du modèle dans les paramètres.",
            },
            "connection_error": {
                "en": "Perplexity: Connection error. Check your internet connection.",
                "it": "Perplexity: Errore di connessione. Controlla la tua connessione Internet.",
                "es": "Perplexity: Error de conexión. Comprueba tu conexión a Internet.",
                "fr": "Perplexity: Erreur de connexion. Vérifiez votre connexion Internet.",
            },
        }
