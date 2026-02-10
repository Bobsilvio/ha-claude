"""AI Assistant API with multi-provider support for Home Assistant."""

import os
import json
import logging
import queue
import time
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
import requests

import tools
import intent
import providers_openai
import providers_anthropic
import providers_google
import chat_ui

load_dotenv()

app = Flask(__name__)
CORS(app)

# Version
VERSION = "3.1.2"

# Configuration
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").lower()
AI_MODEL = os.getenv("AI_MODEL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_THINKING_MODE = os.getenv("NVIDIA_THINKING_MODE", "False").lower() == "true"
# Filter out bashio 'null' values
if AI_MODEL in ("null", "None", ""):
    AI_MODEL = ""
API_PORT = int(os.getenv("API_PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
ENABLE_FILE_ACCESS = os.getenv("ENABLE_FILE_ACCESS", "False").lower() == "true"
LANGUAGE = os.getenv("LANGUAGE", "en").lower()  # Supported: en, it, es, fr
SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN", "") or os.getenv("HASSIO_TOKEN", "")

# Custom system prompt override (can be set dynamically via API)
CUSTOM_SYSTEM_PROMPT = None

logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"ENABLE_FILE_ACCESS env var: {os.getenv('ENABLE_FILE_ACCESS', 'NOT SET')}")
logger.info(f"ENABLE_FILE_ACCESS parsed: {ENABLE_FILE_ACCESS}")
logger.info(f"HA_CONFIG_DIR: /config")
logger.info(f"LANGUAGE: {LANGUAGE}")

# Load multilingual keywords for intent detection
KEYWORDS = {}
try:
    keywords_file = os.path.join(os.path.dirname(__file__), "keywords.json")
    if os.path.isfile(keywords_file):
        with open(keywords_file, "r", encoding="utf-8") as f:
            keywords_data = json.load(f)
            KEYWORDS = keywords_data.get("keywords", {})
        logger.info(f"Loaded keywords for {len(KEYWORDS)} languages: {list(KEYWORDS.keys())}")
    else:
        logger.warning(f"keywords.json not found at {keywords_file}")
except Exception as e:
    logger.error(f"Error loading keywords.json: {e}")

# Language-specific text
LANGUAGE_TEXT = {
    "en": {
        "before": "Before",
        "after": "After",
        "respond_instruction": "Respond in English.",
        "show_yaml_rule": "CRITICAL: After CREATING or MODIFYING automations/scripts/dashboards, you MUST show the YAML code to the user in your response. Never skip this step.",
        "confirm_entity_rule": "CRITICAL: Before creating automations, ALWAYS use search_entities first to find the correct entity_id, then confirm with the user if multiple matches are found.",
        "confirm_delete_rule": "CRITICAL DESTRUCTIVE: Before DELETING or MODIFYING an automation/script/dashboard, you MUST:\n1. Use get_automations/get_scripts/get_dashboards to list all options\n2. Identify with CERTAINTY which one the user wants to delete/modify (by name/alias)\n3. Show the user WHICH ONE you will delete/modify\n4. ASK for EXPLICIT CONFIRMATION before proceeding\n5. NEVER delete/modify without confirmation - it's an IRREVERSIBLE operation",
        "example_vs_create_rule": "CRITICAL INTENT: Distinguish between 'show example' vs 'actually create':\n- If user asks for an \"example\", \"show me\", \"how to\", \"demo\" → respond with YAML code ONLY, do NOT call create_automation/create_script\n- If user explicitly asks to \"create\", \"save\", \"add\", \"make it real\" → call create_automation/create_script\n- When in doubt, show the YAML code first and ask if they want to create it"
    },
    "it": {
        "before": "Prima",
        "after": "Dopo",
        "respond_instruction": "Rispondi sempre in Italiano.",
        "show_yaml_rule": "CRITICO: Dopo aver CREATO o MODIFICATO automazioni/script/dashboard, DEVI sempre mostrare il codice YAML all'utente nella tua risposta. Non saltare mai questo passaggio.",
        "confirm_entity_rule": "CRITICO: Prima di creare automazioni, USA SEMPRE search_entities per trovare il corretto entity_id, poi conferma con l'utente se ci sono più risultati.",
        "confirm_delete_rule": "CRITICO DISTRUTTIVO: Prima di ELIMINARE o MODIFICARE un'automazione/script/dashboard, DEVI:\n1. Usare get_automations/get_scripts/get_dashboards per elencare tutte le opzioni\n2. Identificare con CERTEZZA quale l'utente vuole eliminare/modificare (per nome/alias)\n3. Mostrare all'utente QUALE eliminerai/modificherai\n4. CHIEDERE CONFERMA ESPLICITA prima di procedere\n5. NON eliminare/modificare MAI senza conferma - è un'operazione IRREVERSIBILE",
        "example_vs_create_rule": "CRITICO INTENTO: Distingui tra 'mostra esempio' e 'crea effettivamente':\n- Se l'utente chiede un \"esempio\", \"mostrami\", \"fammi vedere\", \"come si fa\" → rispondi con il codice YAML SOLAMENTE, NON chiamare create_automation/create_script\n- Se l'utente chiede esplicitamente di \"creare\", \"salvare\", \"aggiungere\", \"rendilo reale\" → chiama create_automation/create_script\n- In caso di dubbio, mostra prima il codice YAML e chiedi se vuole crearlo effettivamente"
    },
    "es": {
        "before": "Antes",
        "after": "Después",
        "respond_instruction": "Responde siempre en Español.",
        "show_yaml_rule": "CRÍTICO: Después de CREAR o MODIFICAR automatizaciones/scripts/dashboards, DEBES mostrar el código YAML al usuario en tu respuesta. Nunca omitas este paso.",
        "confirm_entity_rule": "CRÍTICO: Antes de crear automatizaciones, USA SIEMPRE search_entities para encontrar el entity_id correcto, luego confirma con el usuario si hay múltiples resultados.",
        "confirm_delete_rule": "CRÍTICO DESTRUCTIVO: Antes de ELIMINAR o MODIFICAR una automatización/script/dashboard, DEBES:\n1. Usar get_automations/get_scripts/get_dashboards para listar todas las opciones\n2. Identificar con CERTEZA cuál quiere eliminar/modificar el usuario (por nombre/alias)\n3. Mostrar al usuario CUÁL eliminarás/modificarás\n4. PEDIR CONFIRMACIÓN EXPLÍCITA antes de proceder\n5. NUNCA eliminar/modificar sin confirmación - es una operación IRREVERSIBLE",
        "example_vs_create_rule": "CRÍTICO INTENCIÓN: Distingue entre 'mostrar ejemplo' y 'crear realmente':\n- Si el usuario pide un \"ejemplo\", \"muéstrame\", \"cómo se hace\", \"demo\" → responde con código YAML SOLAMENTE, NO llames create_automation/create_script\n- Si el usuario pide explícitamente \"crear\", \"guardar\", \"añadir\", \"hazlo real\" → llama create_automation/create_script\n- En caso de duda, muestra primero el código YAML y pregunta si quiere crearlo realmente"
    },
    "fr": {
        "before": "Avant",
        "after": "Après",
        "respond_instruction": "Réponds toujours en Français.",
        "show_yaml_rule": "CRITIQUE: Après avoir CRÉÉ ou MODIFIÉ des automatisations/scripts/dashboards, tu DOIS toujours montrer le code YAML à l'utilisateur dans ta réponse. Ne saute jamais cette étape.",
        "confirm_entity_rule": "CRITIQUE: Avant de créer des automatisations, UTILISE TOUJOURS search_entities pour trouver le bon entity_id, puis confirme avec l'utilisateur s'il y a plusieurs résultats.",
        "confirm_delete_rule": "CRITIQUE DESTRUCTIF: Avant de SUPPRIMER ou MODIFIER une automatisation/script/dashboard, tu DOIS:\n1. Utiliser get_automations/get_scripts/get_dashboards pour lister toutes les options\n2. Identifier avec CERTITUDE laquelle l'utilisateur veut supprimer/modifier (par nom/alias)\n3. Montrer à l'utilisateur LAQUELLE tu vas supprimer/modifier\n4. DEMANDER une CONFIRMATION EXPLICITE avant de procéder\n5. NE JAMAIS supprimer/modifier sans confirmation - c'est une opération IRRÉVERSIBLE",
        "example_vs_create_rule": "CRITIQUE INTENTION: Distingue entre 'montrer exemple' et 'créer réellement':\n- Si l'utilisateur demande un \"exemple\", \"montre-moi\", \"comment faire\", \"démo\" → réponds avec le code YAML SEULEMENT, NE PAS appeler create_automation/create_script\n- Si l'utilisateur demande explicitement de \"créer\", \"sauvegarder\", \"ajouter\", \"rends-le réel\" → appelle create_automation/create_script\n- En cas de doute, montre d'abord le code YAML et demande s'il veut le créer réellement"
    }
}

def get_lang_text(key: str) -> str:
    """Get language-specific text."""
    return LANGUAGE_TEXT.get(LANGUAGE, LANGUAGE_TEXT["en"]).get(key, "")

# ---- Image handling helpers (v3.0.0) ----

def parse_image_data(data_uri: str) -> tuple:
    """
    Parse data URI to extract media type and base64 data.
    Example: 'data:image/jpeg;base64,/9j/4AAQ...' -> ('image/jpeg', '/9j/4AAQ...')
    """
    if not data_uri or not data_uri.startswith('data:'):
        return None, None

    try:
        # Format: data:image/jpeg;base64,<base64_data>
        header, data = data_uri.split(',', 1)
        media_type = header.split(';')[0].split(':')[1]
        return media_type, data
    except:
        return None, None


def format_message_with_image_anthropic(text: str, media_type: str, base64_data: str) -> list:
    """
    Format message with image for Anthropic Claude.
    Returns content array with text and image blocks.
    """
    return [
        {"type": "text", "text": text},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64_data
            }
        }
    ]


def format_message_with_image_openai(text: str, data_uri: str) -> list:
    """
    Format message with image for OpenAI/GitHub.
    Returns content array with text and image_url blocks.
    """
    return [
        {"type": "text", "text": text},
        {
            "type": "image_url",
            "image_url": {"url": data_uri}
        }
    ]


def format_message_with_image_google(text: str, media_type: str, base64_data: str) -> list:
    """
    Format message with image for Google Gemini.
    Returns parts array for Gemini format.
    """
    # Gemini uses inline_data format
    return [
        {"text": text},
        {
            "inline_data": {
                "mime_type": media_type,
                "data": base64_data
            }
        }
    ]


# ---- Provider defaults ----

PROVIDER_DEFAULTS = {
    "anthropic": {"model": "claude-sonnet-4-20250514", "name": "Claude (Anthropic)"},
    "openai": {"model": "gpt-4o", "name": "ChatGPT (OpenAI)"},
    "google": {"model": "gemini-2.0-flash", "name": "Gemini (Google)"},
    "github": {"model": "openai/gpt-4o", "name": "GitHub Models"},
    "nvidia": {"model": "moonshotai/kimi-k2.5", "name": "NVIDIA NIM"},
}

# GitHub models that returned unknown_model at runtime (per current token)
GITHUB_MODEL_BLOCKLIST: set[str] = set()

PROVIDER_MODELS = {
    "anthropic": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-20250514"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o3-mini"],
    "google": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
    "nvidia": [
        "moonshotai/kimi-k2.5",
        "meta/llama-3.1-70b-instruct",
        "meta/llama-3.1-405b-instruct",
        "mistralai/mistral-large-2-instruct",
        "microsoft/phi-4",
        "nvidia/llama-3.1-nemotron-70b-instruct",
    ],
    "github": [
        # OpenAI (via Azure)
        "openai/gpt-4o", "openai/gpt-4o-mini",
        "openai/gpt-5", "openai/gpt-5-chat", "openai/gpt-5-mini", "openai/gpt-5-nano",
        "openai/gpt-4.1", "openai/gpt-4.1-mini", "openai/gpt-4.1-nano",
        "openai/o1", "openai/o1-mini", "openai/o1-preview",
        "openai/o3", "openai/o3-mini", "openai/o4-mini",
        # Meta Llama
        "meta/meta-llama-3.1-405b-instruct", "meta/meta-llama-3.1-8b-instruct",
        "meta/llama-3.3-70b-instruct",
        "meta/llama-4-scout-17b-16e-instruct", "meta/llama-4-maverick-17b-128e-instruct-fp8",
        "meta/llama-3.2-11b-vision-instruct", "meta/llama-3.2-90b-vision-instruct",
        # Mistral
        "mistral-ai/mistral-small-2503", "mistral-ai/mistral-medium-2505",
        "mistral-ai/ministral-3b", "mistral-ai/codestral-2501",
        # Cohere
        "cohere/cohere-command-r-plus-08-2024", "cohere/cohere-command-r-08-2024",
        "cohere/cohere-command-a",
        # DeepSeek
        "deepseek/deepseek-r1", "deepseek/deepseek-r1-0528", "deepseek/deepseek-v3-0324",
        # Microsoft
        "microsoft/mai-ds-r1", "microsoft/phi-4", "microsoft/phi-4-mini-instruct",
        "microsoft/phi-4-reasoning", "microsoft/phi-4-mini-reasoning",
        "microsoft/phi-4-multimodal-instruct",
        # AI21
        "ai21-labs/ai21-jamba-1.5-large",
        # xAI
        "xai/grok-3", "xai/grok-3-mini",
    ],
}



# Mapping user-friendly names (with prefixes) to technical model names
MODEL_NAME_MAPPING = {
    "Claude: Sonnet 4": "claude-sonnet-4-20250514",
    "Claude: Opus 4": "claude-opus-4-20250514",
    "Claude: Haiku 4": "claude-haiku-4-20250514",
    "OpenAI: GPT-4o": "gpt-4o",
    "OpenAI: GPT-4o-mini": "gpt-4o-mini",
    "OpenAI: GPT-4-turbo": "gpt-4-turbo",
    "OpenAI: o1": "o1",
    "OpenAI: o3-mini": "o3-mini",
    "Google: Gemini 2.0 Flash": "gemini-2.0-flash",
    "Google: Gemini 2.5 Pro": "gemini-2.5-pro",
    "Google: Gemini 2.5 Flash": "gemini-2.5-flash",
    "NVIDIA: Kimi K2.5 🧪": "moonshotai/kimi-k2.5",
    "NVIDIA: Kimi K2.5 🧪🆓": "moonshotai/kimi-k2.5",
    "NVIDIA: Llama 3.1 70B 🧪": "meta/llama-3.1-70b-instruct",
    "NVIDIA: Llama 3.1 70B 🧪🆓": "meta/llama-3.1-70b-instruct",
    "NVIDIA: Llama 3.1 405B 🧪": "meta/llama-3.1-405b-instruct",
    "NVIDIA: Llama 3.1 405B 🧪🆓": "meta/llama-3.1-405b-instruct",
    "NVIDIA: Mistral Large 2 🧪": "mistralai/mistral-large-2-instruct",
    "NVIDIA: Mistral Large 2 🧪🆓": "mistralai/mistral-large-2-instruct",
    "NVIDIA: Phi-4 🧪": "microsoft/phi-4",
    "NVIDIA: Phi-4 🧪🆓": "microsoft/phi-4",
    "NVIDIA: Nemotron 70B 🧪": "nvidia/llama-3.1-nemotron-70b-instruct",
    "NVIDIA: Nemotron 70B 🧪🆓": "nvidia/llama-3.1-nemotron-70b-instruct",
    # GitHub Models - IDs use publisher/model-name format
    "GitHub: GPT-4o": "openai/gpt-4o",
    "GitHub: GPT-4o-mini": "openai/gpt-4o-mini",
    "GitHub: GPT-5": "openai/gpt-5",
    "GitHub: GPT-5-chat": "openai/gpt-5-chat",
    "GitHub: GPT-5-mini": "openai/gpt-5-mini",
    "GitHub: GPT-5-nano": "openai/gpt-5-nano",
    "GitHub: GPT-4.1": "openai/gpt-4.1",
    "GitHub: GPT-4.1-mini": "openai/gpt-4.1-mini",
    "GitHub: GPT-4.1-nano": "openai/gpt-4.1-nano",
    "GitHub: o1": "openai/o1",
    "GitHub: o1-mini": "openai/o1-mini",
    "GitHub: o1-preview": "openai/o1-preview",
    "GitHub: o3": "openai/o3",
    "GitHub: o3-mini": "openai/o3-mini",
    "GitHub: o4-mini": "openai/o4-mini",
    "GitHub: Llama 3.1 405B": "meta/meta-llama-3.1-405b-instruct",
    "GitHub: Llama 3.1 8B": "meta/meta-llama-3.1-8b-instruct",
    "GitHub: Llama 3.3 70B": "meta/llama-3.3-70b-instruct",
    "GitHub: Llama 4 Scout": "meta/llama-4-scout-17b-16e-instruct",
    "GitHub: Llama 4 Maverick": "meta/llama-4-maverick-17b-128e-instruct-fp8",
    "GitHub: Llama 3.2 11B Vision": "meta/llama-3.2-11b-vision-instruct",
    "GitHub: Llama 3.2 90B Vision": "meta/llama-3.2-90b-vision-instruct",
    "GitHub: Mistral Small 2503": "mistral-ai/mistral-small-2503",
    "GitHub: Mistral Medium 2505": "mistral-ai/mistral-medium-2505",
    "GitHub: Ministral 3B": "mistral-ai/ministral-3b",
    "GitHub: Codestral 2501": "mistral-ai/codestral-2501",
    "GitHub: Cohere Command R+": "cohere/cohere-command-r-plus-08-2024",
    "GitHub: Cohere Command R": "cohere/cohere-command-r-08-2024",
    "GitHub: Cohere Command A": "cohere/cohere-command-a",
    "GitHub: DeepSeek R1": "deepseek/deepseek-r1",
    "GitHub: DeepSeek R1 0528": "deepseek/deepseek-r1-0528",
    "GitHub: DeepSeek V3": "deepseek/deepseek-v3-0324",
    "GitHub: MAI-DS-R1": "microsoft/mai-ds-r1",
    "GitHub: Phi-4": "microsoft/phi-4",
    "GitHub: Phi-4 Mini": "microsoft/phi-4-mini-instruct",
    "GitHub: Phi-4 Reasoning": "microsoft/phi-4-reasoning",
    "GitHub: Phi-4 Mini Reasoning": "microsoft/phi-4-mini-reasoning",
    "GitHub: Phi-4 Multimodal": "microsoft/phi-4-multimodal-instruct",
    "GitHub: Jamba 1.5 Large": "ai21-labs/ai21-jamba-1.5-large",
    "GitHub: Grok-3": "xai/grok-3",
    "GitHub: Grok-3 Mini": "xai/grok-3-mini",
}

# Per-provider reverse mapping: {provider: {technical_name: display_name}}
# This avoids conflicts when same technical model exists in multiple providers (e.g., gpt-4o in OpenAI and GitHub)
PROVIDER_DISPLAY = {}  # provider -> {tech_name -> display_name}
_PREFIX_TO_PROVIDER = {
    "Claude:": "anthropic",
    "OpenAI:": "openai",
    "Google:": "google",
    "NVIDIA:": "nvidia",
    "GitHub:": "github",
}
for _display_name, _tech_name in MODEL_NAME_MAPPING.items():
    for _prefix, _prov in _PREFIX_TO_PROVIDER.items():
        if _display_name.startswith(_prefix):
            if _prov not in PROVIDER_DISPLAY:
                PROVIDER_DISPLAY[_prov] = {}
            # Prefer emoji versions for NVIDIA (🧪🆓), but use clean names for others
            if _tech_name not in PROVIDER_DISPLAY[_prov]:
                PROVIDER_DISPLAY[_prov][_tech_name] = _display_name
            elif _prov == "nvidia" and "🆓" in _display_name:
                PROVIDER_DISPLAY[_prov][_tech_name] = _display_name
            break

# Legacy flat mapping (for backward compatibility)
MODEL_DISPLAY_MAPPING = {}
for _prov_models in PROVIDER_DISPLAY.values():
    for _tech, _disp in _prov_models.items():
        if _tech not in MODEL_DISPLAY_MAPPING:
            MODEL_DISPLAY_MAPPING[_tech] = _disp


def normalize_model_name(model_name: str) -> str:
    """Convert user-friendly model name to technical name.
    Handles legacy names with emoji badges (🆓, 🧪) for backward compatibility."""
    # Direct lookup
    if model_name in MODEL_NAME_MAPPING:
        return MODEL_NAME_MAPPING[model_name]
    
    # Try stripping emoji badges (🆓, 🧪) for backward compat with old configs
    import re
    cleaned = re.sub(r'[\s]*[🆓🧪]+[\s]*$', '', model_name).strip()
    if cleaned and cleaned in MODEL_NAME_MAPPING:
        return MODEL_NAME_MAPPING[cleaned]
    
    # Not found, return as-is (assume it's already a technical name)
    return model_name


def get_model_provider(model_name: str) -> str:
    """Get the provider prefix from a model name."""
    if model_name.startswith("Claude:"):
        return "anthropic"
    elif model_name.startswith("OpenAI:"):
        return "openai"
    elif model_name.startswith("Google:"):
        return "google"
    elif model_name.startswith("NVIDIA:"):
        return "nvidia"
    elif model_name.startswith("GitHub:"):
        return "github"
    # Try to infer from technical name
    tech_name = normalize_model_name(model_name)
    if tech_name.startswith("claude-"):
        return "anthropic"
    elif tech_name in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o3-mini"]:
        return "openai"
    elif tech_name.startswith("gemini-"):
        return "google"
    elif tech_name.startswith(("moonshotai/", "meta/", "mistralai/", "microsoft/", "nvidia/")):
        return "nvidia"
    return "unknown"


def validate_model_provider_compatibility() -> tuple[bool, str]:
    """Validate that the selected model is compatible with the selected provider."""
    if not AI_MODEL:
        return True, ""  # No model selected, use default

    model_provider = get_model_provider(AI_MODEL)
    if model_provider == "unknown":
        return True, ""  # Can't determine, allow it

    if model_provider != AI_PROVIDER:
        # Multilingual warning messages
        warnings = {
            "en": f"⚠️ WARNING: You selected model '{AI_MODEL}' which is not compatible with provider '{AI_PROVIDER}'. Change provider or model.",
            "it": f"⚠️ ATTENZIONE: Hai selezionato un modello '{AI_MODEL}' che non è compatibile con il provider '{AI_PROVIDER}'. Cambia provider o modello.",
            "es": f"⚠️ ADVERTENCIA: Has seleccionado el modelo '{AI_MODEL}' que no es compatible con el proveedor '{AI_PROVIDER}'. Cambia proveedor o modelo.",
            "fr": f"⚠️ ATTENTION: Vous avez sélectionné le modèle '{AI_MODEL}' qui n'est pas compatible avec le fournisseur '{AI_PROVIDER}'. Changez de fournisseur ou de modèle."
        }
        error_msg = warnings.get(LANGUAGE, warnings["en"])
        return False, error_msg

    return True, ""


def get_active_model() -> str:
    """Get the active model name (technical format)."""
    if AI_MODEL:
        return normalize_model_name(AI_MODEL)
    return PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("model", "unknown")


def get_api_key() -> str:
    """Get the API key for the active provider."""
    if AI_PROVIDER == "anthropic":
        return ANTHROPIC_API_KEY
    elif AI_PROVIDER == "openai":
        return OPENAI_API_KEY
    elif AI_PROVIDER == "google":
        return GOOGLE_API_KEY
    elif AI_PROVIDER == "nvidia":
        return NVIDIA_API_KEY
    elif AI_PROVIDER == "github":
        return GITHUB_TOKEN
    return ""


def get_max_tokens_param(max_tokens_value: int) -> dict:
    """Get the correct max tokens parameter based on the model.

    Newer models (o1, o3, o4, GPT-5, Grok-3) use 'max_completion_tokens' instead of 'max_tokens'.

    Args:
        max_tokens_value: The token limit value

    Returns:
        dict with either {"max_tokens": value} or {"max_completion_tokens": value}
    """
    # NVIDIA's OpenAI-compatible endpoint expects max_tokens.
    if AI_PROVIDER == "nvidia":
        return {"max_tokens": max_tokens_value}

    model = get_active_model().lower()

    # Models that require max_completion_tokens instead of max_tokens
    new_api_models = [
        "o1", "o3", "o4", "gpt-5", "grok-3"
    ]

    # Check if current model uses the new API parameter
    uses_new_api = any(pattern in model for pattern in new_api_models)

    if uses_new_api:
        return {"max_completion_tokens": max_tokens_value}
    else:
        return {"max_tokens": max_tokens_value}


def _retry_with_swapped_max_token_param(kwargs: dict, max_tokens_value: int, api_err: Exception):
    """Retry once by swapping max_tokens/max_completion_tokens when API says it's unsupported.

    Some providers/models (including GitHub Models) require different parameter names depending on model.
    Returns a response object on success, or None if no retry was attempted.
    """
    error_msg = str(api_err)

    wants_max_completion = ("use 'max_completion_tokens'" in error_msg.lower())
    wants_max_tokens = ("use 'max_tokens'" in error_msg.lower())

    if not (wants_max_completion or wants_max_tokens):
        return None

    # Swap parameters
    if wants_max_completion:
        kwargs.pop("max_tokens", None)
        kwargs["max_completion_tokens"] = max_tokens_value
        logger.warning("Retrying after unsupported_parameter: switching to max_completion_tokens")
    elif wants_max_tokens:
        kwargs.pop("max_completion_tokens", None)
        kwargs["max_tokens"] = max_tokens_value
        logger.warning("Retrying after unsupported_parameter: switching to max_tokens")

    return ai_client.chat.completions.create(**kwargs)


def _normalize_tool_args(args: object) -> str:
    """Return a stable string representation for tool-call arguments."""
    try:
        return json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        return str(args)


def _tool_signature(fn_name: str, args: object) -> str:
    return f"{fn_name}:{_normalize_tool_args(args)}"


def _github_model_variants(model: str) -> list[str]:
    """Return model identifier variants for GitHub Models runtime.

    GitHub's public catalog uses fully qualified IDs like 'openai/gpt-4o'.
    Some runtime configurations expect the short form (e.g., 'gpt-4o').
    We try both when we hit unknown_model.
    """
    if not model:
        return []
    variants = [model]
    if "/" in model:
        short = model.split("/", 1)[1]
        if short and short not in variants:
            variants.append(short)
    return variants


def get_ha_token() -> str:
    """Get the Home Assistant supervisor token."""
    return SUPERVISOR_TOKEN


def get_ha_headers() -> dict:
    """Get headers for Home Assistant API calls."""
    token = get_ha_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


# ---- Initialize AI client ----

def initialize_ai_client():
    """Initialize or reinitialize the AI client based on current provider."""
    global ai_client

    api_key = get_api_key()

    if AI_PROVIDER == "anthropic" and api_key:
        import anthropic
        ai_client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"Anthropic client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "openai" and api_key:
        from openai import OpenAI
        ai_client = OpenAI(api_key=api_key)
        logger.info(f"OpenAI client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "google" and api_key:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        ai_client = genai
        logger.info(f"Google Gemini client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "nvidia" and api_key:
        from openai import OpenAI
        ai_client = OpenAI(
            api_key=api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        logger.info(f"NVIDIA NIM client initialized (model: {get_active_model()})")
    elif AI_PROVIDER == "github" and api_key:
        from openai import OpenAI
        ai_client = OpenAI(
            api_key=api_key,
            base_url="https://models.github.ai/inference",
            default_headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        logger.info(f"GitHub Models client initialized (model: {get_active_model()})")
    else:
        logger.warning(f"AI provider '{AI_PROVIDER}' not configured - set the API key in addon settings")
        ai_client = None

    return ai_client


ai_client = None
initialize_ai_client()

import pathlib

# Conversation history
conversations: Dict[str, List[Dict]] = {}

# Abort flag per session (for stop button)
abort_streams: Dict[str, bool] = {}

# --- Dynamic config structure scan ---
CONFIG_STRUCTURE_TEXT = ""

def scan_config_structure(root_dir="/config", max_depth=2):
    """Scan the config directory and return a formatted string of its structure."""
    lines = []
    def _scan(path, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(path))
        except Exception:
            return
        for entry in entries:
            if entry.startswith('.'):
                continue
            full = os.path.join(path, entry)
            rel = os.path.relpath(full, root_dir)
            prefix = "  " * depth + ("- " if depth else "")
            if os.path.isdir(full):
                lines.append(f"{prefix}{entry}/")
                _scan(full, depth+1)
            else:
                lines.append(f"{prefix}{entry}")
    _scan(root_dir, 0)
    return "\n".join(lines)

# Scan at startup
try:
    CONFIG_STRUCTURE_TEXT = scan_config_structure()
    logger.info("Config structure scanned for prompt.")
except Exception as e:
    CONFIG_STRUCTURE_TEXT = "(Could not scan config: " + str(e) + ")"
    logger.warning(f"Config structure scan failed: {e}")

def get_config_structure_section():
    return f"\nCurrent Home Assistant config structure (scanned at startup):\n\n{CONFIG_STRUCTURE_TEXT}\n"

# --- Configuration.yaml includes mapping ---
CONFIG_INCLUDES = {}

def parse_configuration_includes():
    """Parse configuration.yaml and extract all !include directives."""
    includes = {}
    config_file = "/config/configuration.yaml"

    if not os.path.isfile(config_file):
        logger.warning("configuration.yaml not found")
        return includes

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Look for patterns like "automation: !include automations.yaml"
            if '!include' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    include_part = parts[1].strip()

                    # Extract the file path after !include
                    if include_part.startswith('!include'):
                        filepath = include_part.replace('!include', '').strip()
                        # Remove quotes if present
                        filepath = filepath.strip('"\'')
                        includes[key] = filepath

        logger.info(f"Parsed configuration.yaml includes: {includes}")
        return includes
    except Exception as e:
        logger.error(f"Error parsing configuration.yaml: {e}")
        return includes

# Parse at startup
CONFIG_INCLUDES = parse_configuration_includes()
if CONFIG_INCLUDES:
    logger.info(f"Configuration includes loaded: {len(CONFIG_INCLUDES)} files mapped")
    for key, path in CONFIG_INCLUDES.items():
        logger.info(f"  - {key}: {path}")
else:
    logger.warning("No includes found in configuration.yaml - using defaults")

def get_config_file_path(key: str, default_filename: str) -> str:
    """Get the full path for a config file using the includes mapping."""
    if key in CONFIG_INCLUDES:
        filepath = CONFIG_INCLUDES[key]
        # Handle relative paths
        if not filepath.startswith('/'):
            filepath = os.path.join(HA_CONFIG_DIR, filepath)
        return filepath
    # Fallback to default
    return os.path.join(HA_CONFIG_DIR, default_filename)

def get_config_includes_text():
    """Generate a formatted text of configuration includes for the AI."""
    if not CONFIG_INCLUDES:
        return ""

    lines = ["## Configuration Files Mapping (from configuration.yaml):"]
    for key, filepath in CONFIG_INCLUDES.items():
        lines.append(f"- **{key}**: {filepath}")

    lines.append("\nIMPORTANT: When working with automations, scripts, scenes, etc., use the file paths above.")
    lines.append("Do NOT search for these files - they are pre-mapped for you.")
    return "\n".join(lines) + "\n"


# Conversation persistence - use /config for persistence across addon rebuilds
CONVERSATIONS_FILE = "/config/.storage/claude_conversations.json"


def load_conversations():
    """Load conversations from persistent storage."""
    global conversations
    try:
        if os.path.isfile(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, "r") as f:
                conversations = json.load(f)
            logger.info(f"Loaded {len(conversations)} conversation(s) from disk")
    except Exception as e:
        logger.warning(f"Could not load conversations: {e}")


def save_conversations():
    """Save conversations to persistent storage (without image data to save space)."""
    try:
        os.makedirs(os.path.dirname(CONVERSATIONS_FILE), exist_ok=True)
        # Keep only last 10 sessions, 50 messages each
        trimmed = {}
        for sid, msgs in list(conversations.items())[-10:]:
            # Strip image data from messages to reduce file size
            cleaned_msgs = []
            for msg in msgs[-50:]:
                cleaned_msg = {"role": msg.get("role", "")}
                content = msg.get("content", "")

                # If content is an array (with images), extract only text
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    cleaned_msg["content"] = "\n".join(text_parts) if text_parts else "[Image message]"
                else:
                    cleaned_msg["content"] = content

                # Preserve tool_calls and other metadata
                if "tool_calls" in msg:
                    cleaned_msg["tool_calls"] = msg["tool_calls"]
                
                # Preserve model/provider info for assistant messages
                if msg.get("role") == "assistant":
                    if "model" in msg:
                        cleaned_msg["model"] = msg["model"]
                    if "provider" in msg:
                        cleaned_msg["provider"] = msg["provider"]

                cleaned_msgs.append(cleaned_msg)

            trimmed[sid] = cleaned_msgs

        with open(CONVERSATIONS_FILE, "w") as f:
            json.dump(trimmed, f, ensure_ascii=False, default=str)
    except Exception as e:
        logger.warning(f"Could not save conversations: {e}")


# Load saved conversations on startup
load_conversations()

# ---- Snapshot system for safe config editing ----

SNAPSHOTS_DIR = "/config/.storage/claude_snapshots"
HA_CONFIG_DIR = "/config"  # Mapped via config.json "map": ["config:rw"]

def create_snapshot(filename: str) -> dict:
    """Create a snapshot of a file before modifying it. Returns snapshot info."""
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    src_path = os.path.join(HA_CONFIG_DIR, filename)
    if not os.path.isfile(src_path):
        return {"snapshot_id": None, "message": f"File '{filename}' does not exist (new file)"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace("/", "__").replace("\\", "__")
    snapshot_id = f"{timestamp}_{safe_name}"
    snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_id)

    import shutil
    shutil.copy2(src_path, snapshot_path)

    # Save metadata
    meta_path = snapshot_path + ".meta"
    meta = {"original_file": filename, "timestamp": timestamp, "snapshot_id": snapshot_id,
            "size": os.path.getsize(src_path)}
    with open(meta_path, "w") as f:
        json.dump(meta, f)

    # Keep max 50 snapshots, remove oldest
    all_snapshots = sorted([f for f in os.listdir(SNAPSHOTS_DIR) if not f.endswith(".meta")])
    while len(all_snapshots) > 50:
        oldest = all_snapshots.pop(0)
        try:
            os.remove(os.path.join(SNAPSHOTS_DIR, oldest))
            os.remove(os.path.join(SNAPSHOTS_DIR, oldest + ".meta"))
        except:
            pass

    logger.info(f"Snapshot created: {snapshot_id}")
    return {"snapshot_id": snapshot_id, "original_file": filename, "timestamp": timestamp}


# ---- Home Assistant API helpers ----


def call_ha_websocket(msg_type: str, **kwargs) -> dict:
    """Send a WebSocket command to Home Assistant and return the result."""
    import websocket as ws_lib
    token = get_ha_token()
    ws_url = HA_URL.replace("http://", "ws://").replace("https://", "wss://") + "/websocket"
    logger.debug(f"WS connect: {ws_url} for {msg_type}")
    try:
        ws = ws_lib.create_connection(ws_url, timeout=15)
        # Wait for auth_required
        auth_req = json.loads(ws.recv())
        logger.debug(f"WS auth_required: {auth_req.get('type')}")
        # Authenticate
        ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth_resp = json.loads(ws.recv())
        if auth_resp.get("type") != "auth_ok":
            ws.close()
            return {"error": f"WS auth failed: {auth_resp}"}
        # Send command
        msg = {"id": 1, "type": msg_type}
        msg.update(kwargs)
        ws.send(json.dumps(msg))
        result = json.loads(ws.recv())
        ws.close()
        logger.debug(f"WS result: {result}")
        return result
    except Exception as e:
        logger.error(f"WS error ({msg_type}): {e}")
        return {"error": str(e)}


def call_ha_api(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
    """Call Home Assistant API."""
    url = f"{HA_URL}/api/{endpoint}"
    headers = get_ha_headers()
    token = get_ha_token()
    logger.debug(f"HA API call: {method} {url} (token present: {bool(token)}, len={len(token)})")
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}

        if response.status_code in [200, 201]:
            return response.json() if response.text else {"status": "success"}
        elif response.status_code == 401:
            logger.error(f"HA API 401 Unauthorized - token might be missing or invalid. HA_URL={HA_URL}, token_len={len(token)}")
            return {"error": "401 Unauthorized - check SUPERVISOR_TOKEN"}
        else:
            logger.error(f"HA API error {response.status_code}: {response.text}")
            return {"error": f"API error {response.status_code}", "details": response.text}
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"error": str(e)}


def get_all_states() -> List[Dict]:
    """Get all entity states from HA."""
    result = call_ha_api("GET", "states")
    return result if isinstance(result, list) else []





# ---- Provider-specific chat implementations ----


def chat_anthropic(messages: List[Dict]) -> tuple:
    """Chat with Anthropic Claude. Returns (response_text, updated_messages)."""
    import anthropic

    response = ai_client.messages.create(
        model=get_active_model(),
        max_tokens=8192,
        system=tools.get_system_prompt(),
        tools=tools.get_anthropic_tools(),
        messages=messages
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        assistant_content = response.content
        for block in response.content:
            if block.type == "tool_use":
                logger.info(f"Tool: {block.name}")
                result = tools.execute_tool(block.name, block.input)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})

        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

        response = ai_client.messages.create(
            model=get_active_model(),
            max_tokens=8192,
            system=tools.get_system_prompt(),
            tools=tools.get_anthropic_tools(),
            messages=messages
        )

    final_text = "".join(block.text for block in response.content if hasattr(block, "text"))
    return final_text, messages


def chat_openai(messages: List[Dict]) -> tuple:
    """Chat with OpenAI/NVIDIA/GitHub. Returns (response_text, updated_messages)."""
    global AI_MODEL
    trimmed = intent.trim_messages(messages)
    system_prompt = tools.get_system_prompt()
    tools = tools.get_openai_tools_for_provider()
    max_tok = 4000 if AI_PROVIDER in ["github", "nvidia"] else 4096

    oai_messages = [{"role": "system", "content": system_prompt}] + trimmed

    # NVIDIA Kimi K2.5: use instant mode (thinking mode not yet supported in streaming)
    kwargs = {
        "model": get_active_model(),
        "messages": oai_messages,
        "tools": tools,
        **get_max_tokens_param(max_tok)
    }
    if AI_PROVIDER == "nvidia":
        kwargs["temperature"] = 0.6
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

    try:
        response = ai_client.chat.completions.create(**kwargs)
    except Exception as api_err:
        error_msg = str(api_err)
        if AI_PROVIDER == "github" and (
            "unsupported parameter" in error_msg.lower() or "unsupported_parameter" in error_msg.lower()
        ):
            retry = _retry_with_swapped_max_token_param(kwargs, max_tok, api_err)
            if retry is not None:
                response = retry
            else:
                raise
        elif AI_PROVIDER == "github" and "unknown_model" in error_msg.lower():
            bad_model = kwargs.get("model")

            # Try alternate model formats first (e.g., 'openai/gpt-4o' -> 'gpt-4o')
            tried = []
            for candidate in _github_model_variants(bad_model):
                if candidate in tried:
                    continue
                tried.append(candidate)
                if candidate == bad_model:
                    continue
                try:
                    logger.warning(f"GitHub unknown_model for {bad_model}. Retrying with model={candidate}.")
                    kwargs["model"] = candidate
                    response = ai_client.chat.completions.create(**kwargs)
                    break
                except Exception as retry_err:
                    if "unknown_model" in str(retry_err).lower():
                        continue
                    raise
            else:
                # Still unknown after variants: blocklist canonical ID (the one shown in UI)
                if bad_model:
                    GITHUB_MODEL_BLOCKLIST.add(bad_model)

                # Final fallback attempts (both qualified and short)
                fallback_candidates = ["openai/gpt-4o", "gpt-4o"]
                for fallback_model in fallback_candidates:
                    if bad_model == fallback_model:
                        continue
                    try:
                        logger.warning(f"GitHub unknown_model: {bad_model}. Falling back to {fallback_model}.")
                        kwargs["model"] = fallback_model
                        response = ai_client.chat.completions.create(**kwargs)
                        break
                    except Exception as fallback_err:
                        if "unknown_model" in str(fallback_err).lower():
                            continue
                        raise
                else:
                    raise
        else:
            raise

    msg = response.choices[0].message

    tool_cache: dict[str, str] = {}
    read_only_tools = {
        "get_automations", "get_scripts", "get_dashboards",
        "get_dashboard_config", "read_config_file",
        "list_config_files", "get_frontend_resources",
        "search_entities", "get_entity_state", "get_entities",
    }

    while msg.tool_calls:
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            logger.info(f"Tool: {tc.function.name}")
            args = json.loads(tc.function.arguments)
            fn_name = tc.function.name
            sig = _tool_signature(fn_name, args)
            if fn_name in read_only_tools and sig in tool_cache:
                logger.warning(f"Reusing cached tool result: {fn_name} {sig}")
                result = tool_cache[sig]
            else:
                result = tools.execute_tool(fn_name, args)
                if fn_name in read_only_tools:
                    tool_cache[sig] = result
            # Truncate tool results for GitHub/NVIDIA to stay within token limits
            if AI_PROVIDER in ["github", "nvidia"] and len(result) > 3000:
                result = result[:3000] + '... (truncated)'
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        trimmed = intent.trim_messages(messages)
        oai_messages = [{"role": "system", "content": system_prompt}] + trimmed

        # NVIDIA Kimi K2.5: use instant mode
        kwargs = {
            "model": get_active_model(),
            "messages": oai_messages,
            "tools": tools,
            **get_max_tokens_param(max_tok)
        }
        if AI_PROVIDER == "nvidia":
            kwargs["temperature"] = 0.6
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

        response = ai_client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

    return msg.content or "", messages


def chat_google(messages: List[Dict]) -> tuple:
    """Chat with Google Gemini. Returns (response_text, updated_messages)."""
    from google.generativeai.types import content_types

    model = ai_client.GenerativeModel(
        model_name=get_active_model(),
        system_instruction=SYSTEM_PROMPT,
        tools=[tools.get_gemini_tools()]
    )

    # Convert messages to Gemini format
    gemini_history = []
    for m in messages[:-1]:  # All except last
        role = "model" if m["role"] == "assistant" else "user"
        if isinstance(m["content"], str):
            gemini_history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=gemini_history)
    last_message = messages[-1]["content"] if messages else ""

    response = chat.send_message(last_message)

    # Handle function calls
    while response.candidates[0].content.parts:
        has_function_call = False
        function_responses = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                has_function_call = True
                fn = part.function_call
                logger.info(f"Tool: {fn.name}")
                args = dict(fn.args) if fn.args else {}
                result = tools.execute_tool(fn.name, args)
                function_responses.append(
                    ai_client.protos.Part(function_response=ai_client.protos.FunctionResponse(
                        name=fn.name,
                        response={"result": json.loads(result)}
                    ))
                )

        if not has_function_call:
            break

        response = chat.send_message(function_responses)

    final_text = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "text") and part.text:
            final_text += part.text

    return final_text, messages


# ---- Main chat function ----


def sanitize_messages_for_provider(messages: List[Dict]) -> List[Dict]:
    """Remove messages incompatible with the current provider.
    Also truncates old messages to reduce token count (critical for rate limits)."""
    clean = []
    i = 0
    while i < len(messages):
        m = messages[i]
        role = m.get("role", "")
        skip = False

        # Skip tool-role messages for Anthropic (it uses tool_result inside user messages)
        if AI_PROVIDER == "anthropic" and role == "tool":
            skip = True

        # Skip assistant messages with tool_calls format (OpenAI format) for Anthropic
        elif AI_PROVIDER == "anthropic" and role == "assistant" and m.get("tool_calls"):
            skip = True

        # For Anthropic: Skip assistant messages with tool_use blocks if not followed by tool_result
        elif AI_PROVIDER == "anthropic" and role == "assistant":
            content = m.get("content", "")
            if isinstance(content, list):
                has_tool_use = any(isinstance(c, dict) and c.get("type") == "tool_use" for c in content)
                if has_tool_use:
                    # Check if next message has tool_result
                    next_has_result = False
                    if i + 1 < len(messages):
                        next_msg = messages[i + 1]
                        next_content = next_msg.get("content", "")
                        if next_msg.get("role") == "user" and isinstance(next_content, list):
                            next_has_result = any(isinstance(c, dict) and c.get("type") == "tool_result" for c in next_content)
                    if not next_has_result:
                        # Skip this orphaned tool_use message
                        skip = True

        # Skip Anthropic-format tool_result messages for OpenAI/GitHub
        elif AI_PROVIDER in ("openai", "github") and role == "user" and isinstance(m.get("content"), list):
            if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in m.get("content", [])):
                skip = True

        # For OpenAI/GitHub: Skip assistant messages with tool_calls if tool responses are missing
        elif AI_PROVIDER in ("openai", "github") and role == "assistant" and m.get("tool_calls"):
            tool_call_ids = {tc.get("id") or (tc.get("function", {}).get("name", "")) for tc in m.get("tool_calls", []) if isinstance(tc, dict)}
            # Look ahead for matching tool responses
            found_ids = set()
            for j in range(i + 1, len(messages)):
                if messages[j].get("role") == "tool":
                    found_ids.add(messages[j].get("tool_call_id", ""))
                elif messages[j].get("role") != "tool":
                    break
            if not tool_call_ids.issubset(found_ids):
                skip = True

        # Keep user/assistant/tool messages if not skipped
        if not skip:
            if role in ("user", "assistant"):
                content = m.get("content", "")
                # Accept strings or arrays (arrays can contain images)
                if isinstance(content, str) and content:
                    clean.append({"role": role, "content": content})
                elif isinstance(content, list) and content:
                    clean.append({"role": role, "content": content})
            elif AI_PROVIDER in ("openai", "github") and role == "tool":
                # Pass through tool responses for OpenAI/GitHub (required after tool_calls)
                clean.append(m)

        i += 1
    
    # Limit total messages: keep only last 10
    if len(clean) > 10:
        clean = clean[-10:]
    
    # Truncate OLD messages to save tokens (keep last 2 messages full)
    MAX_OLD_MSG = 1500
    for i in range(len(clean) - 2):
        content = clean[i].get("content", "")
        # Only truncate string content (skip arrays with images)
        if isinstance(content, str):
            # Strip previously injected smart context from old messages
            if "\n\n---\n\u26a0\ufe0f **CONTESTO PRE-CARICATO" in content:
                # Keep only the user's original message (before the smart context separator)
                content = content.split("\n\n---\n\u26a0\ufe0f **CONTESTO PRE-CARICATO")[0]
            if len(content) > MAX_OLD_MSG:
                content = content[:MAX_OLD_MSG] + "... [old message truncated]"
            clean[i] = {"role": clean[i]["role"], "content": content}
    
    return clean


def chat_with_ai(user_message: str, session_id: str = "default") -> str:
    """Send a message to the configured AI provider with HA tools."""
    if not ai_client:
        provider_name = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("name", AI_PROVIDER)
        return f"\u26a0\ufe0f Chiave API per {provider_name} non configurata. Impostala nelle impostazioni dell'add-on."

    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({"role": "user", "content": user_message})
    messages = sanitize_messages_for_provider(conversations[session_id][-20:])

    try:
        if AI_PROVIDER == "anthropic":
            final_text, messages = chat_anthropic(messages)
        elif AI_PROVIDER == "openai":
            final_text, messages = chat_openai(messages)
        elif AI_PROVIDER == "google":
            final_text, messages = chat_google(messages)
        elif AI_PROVIDER == "nvidia":
            final_text, messages = chat_openai(messages)  # Same format, different base_url
        elif AI_PROVIDER == "github":
            final_text, messages = chat_openai(messages)  # Same format, different base_url
        else:
            return f"\u274c Provider '{AI_PROVIDER}' non supportato. Scegli: anthropic, openai, google, nvidia, github."

        conversations[session_id] = messages
        conversations[session_id].append({"role": "assistant", "content": final_text})
        save_conversations()
        return final_text

    except Exception as e:
        logger.error(f"AI error ({AI_PROVIDER}): {e}")
        return f"\u274c Errore {PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get('name', AI_PROVIDER)}: {str(e)}"


# ---- Streaming chat ----



def _format_write_tool_response(tool_name: str, result_data: dict) -> str:
    """Format a human-readable response from a successful write tool result.
    This avoids needing another API round just to format the response.
    For UPDATE operations, shows before/after side-by-side with color highlighting."""
    parts = []
    
    msg = result_data.get("message", "")
    if msg:
        parts.append(f"✅ {msg}")
    else:
        parts.append("✅ Operazione completata con successo!")
    
    # Show diff for update tools (only for updates, not creates)
    old_yaml = result_data.get("old_yaml", "")
    new_yaml = result_data.get("new_yaml", "")
    
    if old_yaml and new_yaml and tool_name in ("update_automation", "update_script", "update_dashboard"):
        # Build side-by-side comparison
        old_lines = old_yaml.strip().splitlines()
        new_lines = new_yaml.strip().splitlines()
        
        # Pad to same length
        max_len = max(len(old_lines), len(new_lines))
        old_lines += [""] * (max_len - len(old_lines))
        new_lines += [""] * (max_len - len(new_lines))
        
        # Build table header
        table_rows = []
        table_rows.append("| ❌ PRIMA (rimosso) | ✅ DOPO (aggiunto) |")
        table_rows.append("|---|---|")
        
        # Add each line pair to table
        for old, new in zip(old_lines, new_lines):
            # Escape pipes in content
            old_escaped = old.replace("|", "\\|") if old else ""
            new_escaped = new.replace("|", "\\|") if new else ""
            
            # Create code formatted cells
            old_cell = f"`{old_escaped}`" if old else ""
            new_cell = f"`{new_escaped}`" if new else ""
            
            table_rows.append(f"| {old_cell} | {new_cell} |")
        
        parts.append("\n**Confronto Prima/Dopo:**")
        parts.append("\n" + "\n".join(table_rows))
    
    elif old_yaml and new_yaml:
        # For CREATE operations, just show "Creato:"
        parts.append("\n**YAML creato:**")
        parts.append(f"```yaml\n{new_yaml[:2000]}\n```")
    
    tip = result_data.get("tip", "")
    if tip:
        parts.append(f"\nℹ️ {tip}")
    
    snapshot = result_data.get("snapshot", "")
    if snapshot and snapshot != "N/A (REST API)":
        parts.append(f"\n💾 Snapshot creato: `{snapshot}`")
    
    return "\n".join(parts)



def stream_chat_with_ai(user_message: str, session_id: str = "default", image_data: str = None):
    """Stream chat events for all providers with optional image support. Yields SSE event dicts.
    Uses LOCAL intent detection + smart context to minimize tokens sent to AI API."""
    if not ai_client:
        yield {"type": "error", "message": "API key non configurata"}
        return

    if session_id not in conversations:
        conversations[session_id] = []

    # Step 1: LOCAL intent detection FIRST (need this BEFORE building smart context)
    # We do a preliminary detect to know if user is creating or modifying
    intent_info = intent.detect_intent(user_message, "")  # Empty context for first pass
    intent_name = intent_info["intent"]
    
    # Step 2: Build smart context NOW that we know the intent
    # If user is creating new automation/script, skip fuzzy matching to avoid false automation injection
    smart_context = intent.build_smart_context(user_message, intent=intent_name)
    
    # Step 3: Re-detect intent WITH full smart context for accuracy
    intent_info = intent.detect_intent(user_message, smart_context)
    intent_name = intent_info["intent"]
    tool_count = len(intent_info.get("tools") or [])
    all_tools_count = len(tools.HA_TOOLS_DESCRIPTION)
    logger.info(f"Intent detected: {intent_name} (specific_target={intent_info['specific_target']}, tools={tool_count if tool_count else all_tools_count})")
    
    # Show intent to user
    INTENT_LABELS = {
        "modify_automation": "Modifica automazione",
        "modify_script": "Modifica script",
        "create_automation": "Crea automazione",
        "create_script": "Crea script",
        "create_dashboard": "Crea dashboard",
        "modify_dashboard": "Modifica dashboard",
        "control_device": "Controllo dispositivo",
        "query_state": "Stato dispositivo",
        "query_history": "Storico dati",
        "delete": "Eliminazione",
        "config_edit": "Modifica configurazione",
        "areas": "Gestione stanze",
        "notifications": "Notifica",
        "chat": "Chat",
        "generic": "Analisi richiesta",
    }
    intent_label = INTENT_LABELS.get(intent_name, "Elaboro")
    yield {"type": "status", "message": f"{intent_label}... ({tool_count if tool_count else all_tools_count} tools)"}
    
    # Step 3: Save original message and build enriched version for API
    if image_data:
        # Parse image data
        media_type, base64_data = parse_image_data(image_data)
        if not media_type or not base64_data:
            yield {"type": "error", "message": "Formato immagine non valido"}
            return

        # Save original message with image (without context text)
        if AI_PROVIDER == "anthropic":
            saved_content = format_message_with_image_anthropic(user_message, media_type, base64_data)
        elif AI_PROVIDER in ("openai", "github"):
            saved_content = format_message_with_image_openai(user_message, image_data)
        elif AI_PROVIDER == "google":
            saved_content = format_message_with_image_google(user_message, media_type, base64_data)
        else:
            saved_content = user_message

        conversations[session_id].append({"role": "user", "content": saved_content})

        # Build enriched version for API (with context)
        if smart_context:
            if intent_info["specific_target"]:
                text_content = f"{user_message}\n\n---\nDATI:\n{smart_context}"
            else:
                text_content = f"{user_message}\n\n---\nCONTESTO:\n{smart_context}\n---\nNON richiedere dati già presenti sopra. UNA sola chiamata tool, poi rispondi."
        else:
            text_content = user_message

        if AI_PROVIDER == "anthropic":
            api_content = format_message_with_image_anthropic(text_content, media_type, base64_data)
        elif AI_PROVIDER in ("openai", "github"):
            api_content = format_message_with_image_openai(text_content, image_data)
        elif AI_PROVIDER == "google":
            api_content = format_message_with_image_google(text_content, media_type, base64_data)
        else:
            api_content = text_content

        logger.info(f"Message with image: {text_content[:50]}... (media_type: {media_type})")
        yield {"type": "status", "message": "Elaborazione immagine..."}
    else:
        # No image - save original message
        conversations[session_id].append({"role": "user", "content": user_message})

        # Build enriched version for API (with context)
        if smart_context:
            if intent_info["specific_target"]:
                api_content = f"{user_message}\n\n---\nDATI:\n{smart_context}"
            else:
                api_content = f"{user_message}\n\n---\nCONTESTO:\n{smart_context}\n---\nNON richiedere dati già presenti sopra. UNA sola chiamata tool, poi rispondi."
            # Log estimated token count
            est_tokens = len(api_content) // 4  # ~4 chars per token
            logger.info(f"Smart context: {len(smart_context)} chars, est. ~{est_tokens} tokens for user message")
            yield {"type": "status", "message": "Contesto pre-caricato..."}
        else:
            api_content = user_message

    # Create a copy of messages for API with enriched last user message
    messages = conversations[session_id][:-1] + [{"role": "user", "content": api_content}]

    try:
        # Remember current conversation length to avoid duplicates
        conv_length_before = len(conversations[session_id])

        if AI_PROVIDER == "nvidia":
            yield from providers_openai.stream_chat_nvidia_direct(messages, intent_info=intent_info)
            # Sync ONLY new assistant messages (skip the enriched user message we created)
            for msg in messages[conv_length_before:]:
                if msg.get("role") == "assistant":
                    msg["model"] = get_active_model()
                    msg["provider"] = AI_PROVIDER
                    conversations[session_id].append(msg)
        elif AI_PROVIDER in ("openai", "github"):
            yield from providers_openai.stream_chat_openai(messages, intent_info=intent_info)
            # Sync ONLY new assistant messages (skip the enriched user message we created)
            for msg in messages[conv_length_before:]:
                if msg.get("role") == "assistant":
                    msg["model"] = get_active_model()
                    msg["provider"] = AI_PROVIDER
                    conversations[session_id].append(msg)
        elif AI_PROVIDER == "anthropic":
            clean_messages = sanitize_messages_for_provider(messages)
            yield from providers_anthropic.stream_chat_anthropic(clean_messages, intent_info=intent_info)
            # Sync ONLY new assistant messages (skip the enriched user message we created)
            for msg in clean_messages[conv_length_before:]:
                if msg.get("role") == "assistant":
                    msg["model"] = get_active_model()
                    msg["provider"] = AI_PROVIDER
                    conversations[session_id].append(msg)
        elif AI_PROVIDER == "google":
            clean_messages = sanitize_messages_for_provider(messages)
            yield from providers_google.stream_chat_google(clean_messages)
            # Sync ONLY new assistant messages (skip the enriched user message we created)
            for msg in clean_messages[conv_length_before:]:
                if msg.get("role") == "assistant":
                    msg["model"] = get_active_model()
                    msg["provider"] = AI_PROVIDER
                    conversations[session_id].append(msg)
        else:
            yield {"type": "error", "message": f"Provider '{AI_PROVIDER}' non supportato"}
            return

        # Trim and save
        if len(conversations[session_id]) > 50:
            conversations[session_id] = conversations[session_id][-40:]
        save_conversations()
    except Exception as e:
        logger.error(f"Stream error ({AI_PROVIDER}): {e}")
        yield {"type": "error", "message": str(e)}



# ---- Flask Routes ----


@app.route('/')
def index():
    """Serve the chat UI."""
    return chat_ui.get_chat_ui(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/api/status')
def api_status():
    """Debug endpoint to check HA connection status."""
    token = get_ha_token()
    ha_ok = False
    ha_msg = ""
    try:
        resp = requests.get(f"{HA_URL}/api/", headers=get_ha_headers(), timeout=10)
        ha_ok = resp.status_code == 200
        ha_msg = f"{resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        ha_msg = str(e)

    return jsonify({
        "version": VERSION,
        "provider": AI_PROVIDER,
        "model": get_active_model(),
        "api_key_set": bool(get_api_key()),
        "ha_url": HA_URL,
        "supervisor_token_present": bool(token),
        "supervisor_token_length": len(token),
        "ha_connection_ok": ha_ok,
        "ha_response": ha_msg,
    })





@app.route('/api/set_model', methods=['POST'])
def api_set_model():
    global AI_PROVIDER, AI_MODEL, ai_client

    data = request.json or {}

    if "provider" in data:
        AI_PROVIDER = data["provider"]

    if "model" in data:
        AI_MODEL = normalize_model_name(data["model"])

    logger.info(f"Runtime model changed → {AI_PROVIDER} / {AI_MODEL}")

    # Reinitialize client so provider switches don't keep a stale client instance
    try:
        initialize_ai_client()
    except Exception as e:
        logger.exception(f"Failed to reinitialize AI client after model/provider change: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to initialize AI client for selected provider/model",
            "provider": AI_PROVIDER,
            "model": AI_MODEL,
        }), 500

    return jsonify({
        "success": True,
        "provider": AI_PROVIDER,
        "model": AI_MODEL
    })



@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get current runtime configuration."""
    return jsonify({
        "success": True,
        "config": {
            "ai_provider": AI_PROVIDER,
            "ai_model": get_active_model(),
            "language": LANGUAGE,
            "debug_mode": DEBUG_MODE,
            "enable_file_access": ENABLE_FILE_ACCESS,
            "version": VERSION
        }
    })


@app.route('/api/config', methods=['POST'])
def api_set_config():
    """Update runtime configuration dynamically."""
    global LANGUAGE, DEBUG_MODE, ENABLE_FILE_ACCESS
    
    try:
        data = request.get_json()
        updated = []
        
        # Update language
        if 'language' in data:
            new_lang = data['language'].lower()
            if new_lang in ['en', 'it', 'es', 'fr']:
                LANGUAGE = new_lang
                updated.append(f"language={LANGUAGE}")
                logger.info(f"Language changed to: {LANGUAGE}")
            else:
                return jsonify({"success": False, "error": f"Invalid language: {new_lang}. Supported: en, it, es, fr"}), 400
        
        # Update debug mode
        if 'debug_mode' in data:
            DEBUG_MODE = bool(data['debug_mode'])
            updated.append(f"debug_mode={DEBUG_MODE}")
            logger.info(f"Debug mode changed to: {DEBUG_MODE}")
            logging.getLogger().setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
        
        # Update file access
        if 'enable_file_access' in data:
            ENABLE_FILE_ACCESS = bool(data['enable_file_access'])
            updated.append(f"enable_file_access={ENABLE_FILE_ACCESS}")
            logger.info(f"File access changed to: {ENABLE_FILE_ACCESS}")
        
        return jsonify({
            "success": True,
            "message": f"Configuration updated: {', '.join(updated)}",
            "config": {
                "language": LANGUAGE,
                "debug_mode": DEBUG_MODE,
                "enable_file_access": ENABLE_FILE_ACCESS
            }
        })
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/system_prompt', methods=['GET'])
def api_get_system_prompt():
    """Get the current system prompt."""
    try:
        prompt = tools.get_system_prompt()
        return jsonify({
            "success": True,
            "system_prompt": prompt,
            "length": len(prompt)
        })
    except Exception as e:
        logger.error(f"Error getting system prompt: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/system_prompt', methods=['POST'])
def api_set_system_prompt():
    """Override the system prompt dynamically. Use 'reset' to restore default."""
    global CUSTOM_SYSTEM_PROMPT
    
    try:
        data = request.get_json()
        new_prompt = data.get('system_prompt')
        
        if not new_prompt:
            return jsonify({"success": False, "error": "system_prompt parameter required"}), 400
        
        if new_prompt.lower() == 'reset':
            CUSTOM_SYSTEM_PROMPT = None
            logger.info("System prompt reset to default")
            return jsonify({
                "success": True,
                "message": "System prompt reset to default",
                "system_prompt": tools.get_system_prompt()
            })
        
        CUSTOM_SYSTEM_PROMPT = new_prompt
        logger.info(f"System prompt overridden ({len(new_prompt)} chars)")
        
        return jsonify({
            "success": True,
            "message": "System prompt updated successfully",
            "system_prompt": CUSTOM_SYSTEM_PROMPT,
            "length": len(CUSTOM_SYSTEM_PROMPT)
        })
    except Exception as e:
        logger.error(f"Error setting system prompt: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint."""
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    if not message:
        return jsonify({"error": "Empty message"}), 400
    logger.info(f"Chat [{AI_PROVIDER}]: {message}")
    response_text = chat_with_ai(message, session_id)
    return jsonify({"response": response_text}), 200


@app.route('/api/chat/stream', methods=['POST'])
def api_chat_stream():
    """Streaming chat endpoint using Server-Sent Events with image support."""
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    image_data = data.get("image", None)  # Base64 image data
    if not message:
        return jsonify({"error": "Empty message"}), 400
    if image_data:
        logger.info(f"Stream [{AI_PROVIDER}] with image: {message[:50]}...")
    else:
        logger.info(f"Stream [{AI_PROVIDER}]: {message}")
    abort_streams[session_id] = False  # Reset abort flag

    def generate():
        for event in stream_chat_with_ai(message, session_id, image_data):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/api/chat/abort', methods=['POST'])
def api_chat_abort():
    """Abort a running stream."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")
    abort_streams[session_id] = True
    logger.info(f"Abort requested for session {session_id}")
    return jsonify({"status": "abort_requested"}), 200


@app.route('/api/conversations/<session_id>/messages', methods=['GET'])
def api_conversation_messages(session_id):
    """Get all messages for a conversation session."""
    msgs = conversations.get(session_id, [])
    # Return only user/assistant text messages for UI display (filter empty content)
    display_msgs = []
    for m in msgs:
        content = m.get("content", "")
        # Skip messages with empty content or only whitespace
        if m.get("role") in ("user", "assistant") and isinstance(content, str) and content.strip():
            msg_data = {"role": m["role"], "content": content}
            # Include model/provider info for assistant messages
            if m.get("role") == "assistant":
                if "model" in m:
                    msg_data["model"] = m["model"]
                if "provider" in m:
                    msg_data["provider"] = m["provider"]
            display_msgs.append(msg_data)
    return jsonify({"session_id": session_id, "messages": display_msgs}), 200


@app.route('/api/conversations', methods=['GET'])
def api_conversations_list():
    """List all conversation sessions with metadata."""
    result = []
    for sid, msgs in conversations.items():
        if not msgs:
            continue
        # Extract first user message as title
        title = "Nuova conversazione"
        for msg in msgs:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    title = content[:50] + ("..." if len(content) > 50 else "")
                    break
        result.append({
            "id": sid,
            "title": title,
            "message_count": len(msgs),
            "last_updated": msgs[-1].get("timestamp", sid) if msgs else sid
        })
    # Sort by ID (timestamp) descending
    result.sort(key=lambda x: x["id"], reverse=True)
    return jsonify({"conversations": result[:10]}), 200  # Return last 10


@app.route('/api/conversations/<session_id>', methods=['GET'])
def api_conversation_get(session_id):
    """Get a specific conversation session."""
    if session_id in conversations:
        # Filter to only return displayable messages (user/assistant with non-empty string content)
        msgs = conversations.get(session_id, [])
        display_msgs = []
        for m in msgs:
            content = m.get("content", "")
            # For multimodal messages, extract text content
            if isinstance(content, list):
                # Extract text from content blocks (Anthropic format: [{type:text, text:...}])
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block.get("text"), str):
                            text_parts.append(block["text"])
                content = "\n".join(text_parts) if text_parts else ""
            
            if m.get("role") in ("user", "assistant") and isinstance(content, str) and content.strip():
                msg_data = {"role": m["role"], "content": content}
                # Include model/provider metadata for assistant messages
                if m.get("role") == "assistant":
                    if m.get("model"):
                        msg_data["model"] = m["model"]
                    if m.get("provider"):
                        msg_data["provider"] = m["provider"]
                display_msgs.append(msg_data)
        return jsonify({"session_id": session_id, "messages": display_msgs}), 200
    return jsonify({"error": "Conversation not found"}), 404


@app.route('/api/conversations/<session_id>', methods=['DELETE'])
def api_conversation_delete(session_id):
    """Clear a conversation session."""
    if session_id in conversations:
        del conversations[session_id]
        save_conversations()
    return jsonify({"status": "ok", "message": f"Session '{session_id}' cleared."}), 200

@app.route('/api/get_models', methods=['GET'])
def api_get_models():
    """Get available models (chat + HA settings) without duplicate routes."""
    # --- Providers disponibili (per HA settings) ---
    available_providers = []
    if ANTHROPIC_API_KEY:
        available_providers.append({"id": "anthropic", "name": "Anthropic Claude"})
    if OPENAI_API_KEY:
        available_providers.append({"id": "openai", "name": "OpenAI"})
    if GOOGLE_API_KEY:
        available_providers.append({"id": "google", "name": "Google Gemini"})
    if NVIDIA_API_KEY:
        available_providers.append({"id": "nvidia", "name": "NVIDIA NIM"})
    if GITHUB_TOKEN:
        available_providers.append({"id": "github", "name": "GitHub Models"})

    # --- Tutti i modelli per provider (come li vuole la chat: display/prefissi) ---
    models_display = {}
    models_technical = {}
    for provider, models in PROVIDER_MODELS.items():
        filtered_models = list(models)
        if provider == "github" and GITHUB_MODEL_BLOCKLIST:
            filtered_models = [m for m in filtered_models if m not in GITHUB_MODEL_BLOCKLIST]
        models_technical[provider] = list(filtered_models)
        # Use per-provider display mapping to avoid cross-provider conflicts
        prov_map = PROVIDER_DISPLAY.get(provider, {})
        models_display[provider] = [prov_map.get(m, m) for m in filtered_models]

    # --- Current model (sia tech che display) ---
    current_model_tech = get_active_model()
    current_model_display = MODEL_DISPLAY_MAPPING.get(current_model_tech, current_model_tech)

    # --- Modelli del provider corrente (per HA settings: lista con flag current) ---
    provider_models = models_technical.get(AI_PROVIDER, PROVIDER_MODELS.get(AI_PROVIDER, []))
    available_models = []
    for tech_name in provider_models:
        available_models.append({
            "technical_name": tech_name,
            "display_name": MODEL_DISPLAY_MAPPING.get(tech_name, tech_name),
            "is_current": tech_name == current_model_tech
        })

    return jsonify({
        "success": True,

        # compat chat (quello che già usa il tuo JS)
        "current_provider": AI_PROVIDER,
        "current_model": current_model_display,
        "models": models_display,

        # extra per HA (più completo)
        "current_model_technical": current_model_tech,
        "models_technical": models_technical,
        "available_providers": available_providers,
        "available_models": available_models
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "ai_provider": AI_PROVIDER,
        "ai_model": get_active_model(),
        "ai_configured": bool(get_api_key()),
        "ha_connected": bool(get_ha_token()),
    }), 200


@app.route("/entities", methods=["GET"])
def get_entities_route():
    """Get all entities."""
    domain = request.args.get("domain", "")
    states = get_all_states()
    if domain:
        states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
    return jsonify({"entities": states, "count": len(states)}), 200


@app.route("/entity/<entity_id>/state", methods=["GET"])
def get_entity_state_route(entity_id: str):
    """Get entity state."""
    return jsonify(call_ha_api("GET", f"states/{entity_id}")), 200


@app.route("/message", methods=["POST"])
def send_message_legacy():
    """Legacy message endpoint."""
    data = request.get_json()
    return jsonify({"status": "success", "response": chat_with_ai(data.get("message", ""))}), 200


@app.route("/service/call", methods=["POST"])
def call_service_route():
    """Call a Home Assistant service."""
    data = request.get_json()
    service = data.get("service", "")
    if not service or "." not in service:
        return jsonify({"error": "Use 'domain.service' format"}), 400
    domain, svc = service.split(".", 1)
    return jsonify(call_ha_api("POST", f"services/{domain}/{svc}", data.get("data", {}))), 200


@app.route("/execute/automation", methods=["POST"])
def execute_automation():
    """Execute an automation."""
    data = request.get_json()
    eid = data.get("entity_id", data.get("automation_id", ""))
    if not eid.startswith("automation."):
        eid = f"automation.{eid}"
    return jsonify(call_ha_api("POST", "services/automation/trigger", {"entity_id": eid})), 200


@app.route("/execute/script", methods=["POST"])
def execute_script():
    """Execute a script."""
    data = request.get_json()
    return jsonify(call_ha_api("POST", f"services/script/{data.get('script_id', '')}", data.get("variables", {}))), 200


@app.route("/conversation/clear", methods=["POST"])
def clear_conversation():
    """Clear conversation history."""
    sid = (request.get_json() or {}).get("session_id", "default")
    conversations.pop(sid, None)
    return jsonify({"status": "cleared"}), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(f"Provider: {AI_PROVIDER} | Model: {get_active_model()}")
    logger.info(f"API Key: {'configured' if get_api_key() else 'NOT configured'}")
    # get_ha_token() è già definita sopra, quindi qui è sicuro
    logger.info(f"HA Token: {'available' if get_ha_token() else 'NOT available'}")

    # Validate provider/model compatibility
    is_valid, error_msg = validate_model_provider_compatibility()
    if not is_valid:
        logger.warning(error_msg)
        # Auto-fix: reset to provider default model
        default_model = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("model", "")
        if default_model:
            AI_MODEL = default_model
            fix_msgs = {
                "en": f"✅ AUTO-FIX: Model automatically changed to '{MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (default for {AI_PROVIDER})",
                "it": f"✅ AUTO-FIX: Modello cambiato automaticamente a '{MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (default per {AI_PROVIDER})",
                "es": f"✅ AUTO-FIX: Modelo cambiado automáticamente a '{MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (predeterminado para {AI_PROVIDER})",
                "fr": f"✅ AUTO-FIX: Modèle changé automatiquement en '{MODEL_DISPLAY_MAPPING.get(default_model, default_model)}' (par défaut pour {AI_PROVIDER})"
            }
            logger.warning(fix_msgs.get(LANGUAGE, fix_msgs["en"]))

    # Use Waitress production WSGI server instead of Flask development server
    from waitress import serve
    logger.info(f"Starting production server on 0.0.0.0:{API_PORT}")
    serve(app, host="0.0.0.0", port=API_PORT, threads=6)
