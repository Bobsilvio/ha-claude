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

load_dotenv()

app = Flask(__name__)
CORS(app)

# Version
VERSION = "3.0.54"

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
    "github": {"model": "gpt-4o", "name": "GitHub Models"},
    "nvidia": {"model": "moonshotai/kimi-k2.5", "name": "NVIDIA NIM"},
}

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
            base_url="https://models.inference.ai.azure.com"
        )
        logger.info(f"GitHub Copilot client initialized (model: {get_active_model()})")
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

# User-friendly tool descriptions (Italian)
TOOL_DESCRIPTIONS = {
    "get_entities": "Carico dispositivi",
    "get_entity_state": "Leggo stato dispositivo",
    "call_service": "Eseguo comando",
    "search_entities": "Cerco dispositivi",
    "get_automations": "Carico automazioni",
    "update_automation": "Modifico automazione",
    "create_automation": "Creo automazione",
    "trigger_automation": "Avvio automazione",
    "delete_automation": "Elimino automazione",
    "get_scripts": "Carico script",
    "run_script": "Eseguo script",
    "update_script": "Modifico script",
    "create_script": "Creo script",
    "delete_script": "Elimino script",
    "get_dashboards": "Carico dashboard",
    "get_dashboard_config": "Leggo config dashboard",
    "update_dashboard": "Modifico dashboard",
    "create_dashboard": "Creo dashboard",
    "delete_dashboard": "Elimino dashboard",
    "get_frontend_resources": "Verifico card installate",
    "get_scenes": "Carico scene",
    "activate_scene": "Attivo scena",
    "get_areas": "Carico stanze",
    "manage_areas": "Gestisco stanze",
    "get_history": "Carico storico",
    "get_statistics": "Carico statistiche",
    "send_notification": "Invio notifica",
    "read_config_file": "Leggo file config",
    "write_config_file": "Salvo file config",
    "list_config_files": "Elenco file config",
    "check_config": "Valido configurazione",
    "create_backup": "Creo backup",
    "get_available_services": "Carico servizi",
    "get_events": "Carico eventi",
    "manage_entity": "Gestisco entità",
    "get_devices": "Carico dispositivi",
    "shopping_list": "Lista spesa",
    "browse_media": "Sfoglio media",
    "list_snapshots": "Elenco snapshot",
    "restore_snapshot": "Ripristino snapshot",
}

def get_tool_description(tool_name: str) -> str:
    """Get user-friendly Italian description for a tool."""
    return TOOL_DESCRIPTIONS.get(tool_name, tool_name.replace('_', ' ').title())

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


# ---- Tool definitions (shared across providers) ----

HA_TOOLS_DESCRIPTION = [
    {
        "name": "get_entities",
        "description": "Get the current state of all Home Assistant entities, or filter by domain (e.g. 'light', 'switch', 'sensor', 'automation', 'climate').",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter (e.g. 'light', 'switch', 'sensor')."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_entity_state",
        "description": "Get the current state and attributes of a specific entity.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID (e.g. 'light.living_room')."
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "call_service",
        "description": "Call a Home Assistant service to control devices: turn on/off lights, switches, set climate temperature, lock/unlock, open/close covers, send notifications, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain (e.g. 'light', 'switch', 'climate', 'cover')."
                },
                "service": {
                    "type": "string",
                    "description": "Service name (e.g. 'turn_on', 'turn_off', 'toggle')."
                },
                "data": {
                    "type": "object",
                    "description": "Service data including target entity_id and parameters."
                }
            },
            "required": ["domain", "service", "data"]
        }
    },
    {
        "name": "create_automation",
        "description": "Create a new Home Assistant automation with triggers, conditions, and actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "alias": {"type": "string", "description": "Name for the automation."},
                "description": {"type": "string", "description": "Description of the automation."},
                "trigger": {"type": "array", "description": "List of triggers.", "items": {"type": "object"}},
                "condition": {"type": "array", "description": "Optional conditions.", "items": {"type": "object"}},
                "action": {"type": "array", "description": "List of actions.", "items": {"type": "object"}},
                "mode": {"type": "string", "enum": ["single", "restart", "queued", "parallel"]}
            },
            "required": ["alias", "trigger", "action"]
        }
    },
    {
        "name": "get_automations",
        "description": "Get all existing automations with their YAML source. Returns the list of automations AND the content of automations.yaml. To modify an automation, use update_automation instead of write_config_file.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "update_automation",
        "description": "Update or modify an existing automation by its ID. Pass the automation_id and the fields you want to change. The tool reads automations.yaml, finds the automation, applies the changes, creates a snapshot, and saves. Much simpler than rewriting the full file.",
        "parameters": {
            "type": "object",
            "properties": {
                "automation_id": {"type": "string", "description": "The automation's 'id' field from automations.yaml (e.g. '1728373064590')."},
                "changes": {"type": "object", "description": "Fields to update. Can include: alias, description, trigger, condition, action, mode. Only pass the fields you want to change."},
                "add_condition": {"type": "object", "description": "A single condition to ADD to the existing conditions (appended, does not replace). Use this for simple additions like excluding a team."}
            },
            "required": ["automation_id"]
        }
    },
    {
        "name": "trigger_automation",
        "description": "Manually trigger an existing automation.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Automation entity_id."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_available_services",
        "description": "Get all available Home Assistant service domains and services.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "search_entities",
        "description": "Search entities by keyword in entity_id or friendly_name. Use this to find specific devices, sensors, or integrations.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword (e.g. 'calcio', 'temperature', 'motion', 'light')."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_events",
        "description": "Get all available Home Assistant event types. Use this to discover events fired by integrations and addons.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_history",
        "description": "Get the state history of an entity over a time period. Useful for checking past values, trends, and when things changed.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "The entity ID to get history for."},
                "hours": {"type": "number", "description": "Hours of history to retrieve (default 24, max 168)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_scenes",
        "description": "Get all available scenes in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "activate_scene",
        "description": "Activate a Home Assistant scene.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Scene entity_id (e.g. 'scene.movie_night')."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_scripts",
        "description": "Get all available scripts in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_script",
        "description": "Run a Home Assistant script with optional variables.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Script entity_id (e.g. 'script.goodnight')."},
                "variables": {"type": "object", "description": "Optional variables to pass to the script."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "update_script",
        "description": "Update/modify an existing script directly in scripts.yaml. Reads the file, finds the script, applies changes, creates a snapshot, saves. Use this instead of write_config_file for scripts.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "The script ID (e.g. 'goodnight_routine' without 'script.' prefix)."},
                "changes": {"type": "object", "description": "Object with the fields to change (e.g. {\"alias\": \"New Name\", \"sequence\": [...]}). Only specified fields are modified."}
            },
            "required": ["script_id", "changes"]
        }
    },
    {
        "name": "get_areas",
        "description": "Get all areas/rooms configured in Home Assistant and their entities. Useful for room-based control like 'turn off everything in the bedroom'.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "send_notification",
        "description": "Send a notification to Home Assistant (persistent notification visible in HA UI, or to a mobile device).",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The notification message."},
                "title": {"type": "string", "description": "Optional notification title."},
                "target": {"type": "string", "description": "Notify service target (e.g. 'mobile_app_phone'). If empty, creates a persistent notification in HA."}
            },
            "required": ["message"]
        }
    },
    {
        "name": "get_dashboards",
        "description": "Get all Lovelace dashboards in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_dashboard",
        "description": "Create a NEW Lovelace dashboard (does NOT modify existing ones). The AI builds the views and cards config. Common card types: entities, gauge, history-graph, weather-forecast, light, thermostat, button, markdown, grid, horizontal-stack, vertical-stack.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Dashboard title (e.g. 'Luci e Temperature')."},
                "url_path": {"type": "string", "description": "URL slug (lowercase, no spaces, e.g. 'luci-temp'). Must be unique."},
                "icon": {"type": "string", "description": "MDI icon (e.g. 'mdi:thermometer', 'mdi:lightbulb'). Optional."},
                "views": {
                    "type": "array",
                    "description": "List of views (tabs) with cards. Each view has: title, path, icon, cards[].",
                    "items": {"type": "object"}
                }
            },
            "required": ["title", "url_path", "views"]
        }
    },
    {
        "name": "create_script",
        "description": "Create a new Home Assistant script with a sequence of actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "Unique script ID (lowercase, underscores, e.g. 'goodnight_routine')."},
                "alias": {"type": "string", "description": "Friendly name for the script."},
                "description": {"type": "string", "description": "Description of what the script does."},
                "sequence": {"type": "array", "description": "List of actions to execute in order.", "items": {"type": "object"}},
                "mode": {"type": "string", "enum": ["single", "restart", "queued", "parallel"], "description": "Execution mode (default: single)."}
            },
            "required": ["script_id", "alias", "sequence"]
        }
    },
    {
        "name": "delete_dashboard",
        "description": "Delete a Lovelace dashboard by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "string", "description": "The dashboard ID (get it from get_dashboards)."}
            },
            "required": ["dashboard_id"]
        }
    },
    {
        "name": "delete_automation",
        "description": "Delete an existing automation. Works for both UI-created automations (via API) and YAML-based automations (removes from file). If removing from YAML, creates a snapshot first and requires Home Assistant restart.",
        "parameters": {
            "type": "object",
            "properties": {
                "automation_id": {"type": "string", "description": "The automation entity_id (e.g. 'automation.my_automation')."}
            },
            "required": ["automation_id"]
        }
    },
    {
        "name": "delete_script",
        "description": "Delete an existing script. Works for both UI-created scripts (via API) and YAML-based scripts (removes from file). If removing from YAML, creates a snapshot first and requires Home Assistant restart.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "The script ID without prefix (e.g. 'goodnight_routine')."}
            },
            "required": ["script_id"]
        }
    },
    {
        "name": "manage_areas",
        "description": "Manage Home Assistant areas/rooms: list, create, rename, or delete areas.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "update", "delete"], "description": "Action to perform."},
                "name": {"type": "string", "description": "Area name (for create/update)."},
                "area_id": {"type": "string", "description": "Area ID (for update/delete)."},
                "icon": {"type": "string", "description": "MDI icon for the area (optional)."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "manage_entity",
        "description": "Update entity registry: rename, assign to area, enable/disable an entity.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "The entity ID to manage."},
                "name": {"type": "string", "description": "New friendly name (optional)."},
                "area_id": {"type": "string", "description": "Assign to area ID (optional). Use manage_areas list to get IDs."},
                "disabled_by": {"type": "string", "enum": ["user", ""], "description": "Set to 'user' to disable, '' to enable."},
                "icon": {"type": "string", "description": "Custom icon (optional)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_devices",
        "description": "Get all devices registered in Home Assistant with manufacturer, model, and area.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_statistics",
        "description": "Get advanced statistics (min, max, mean, sum) for a sensor over a time period. Useful for energy, temperature trends, averages.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Sensor entity_id (e.g. 'sensor.temperature')."},
                "period": {"type": "string", "enum": ["5minute", "hour", "day", "week", "month"], "description": "Statistics period (default: hour)."},
                "hours": {"type": "number", "description": "How many hours back to query (default 24, max 720)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "shopping_list",
        "description": "Manage the Home Assistant shopping list: view items, add new items, or mark items as complete.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "add", "complete"], "description": "Action to perform."},
                "name": {"type": "string", "description": "Item name (for add)."},
                "item_id": {"type": "string", "description": "Item ID (for complete, get from list)."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "create_backup",
        "description": "Create a full Home Assistant backup. This may take a few minutes.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "browse_media",
        "description": "Browse available media content (music, photos, etc.) from media players.",
        "parameters": {
            "type": "object",
            "properties": {
                "media_content_id": {"type": "string", "description": "Content path to browse (empty for root)."},
                "media_content_type": {"type": "string", "description": "Media type (e.g. 'music', 'image'). Default: 'music'."}
            },
            "required": []
        }
    },
    {
        "name": "get_dashboard_config",
        "description": "Get the full configuration of a Lovelace dashboard. Use this to read an existing dashboard before modifying it.",
        "parameters": {
            "type": "object",
            "properties": {
                "url_path": {"type": "string", "description": "Dashboard URL path (e.g. 'lovelace', 'energy-dashboard'). Use 'lovelace' or null for the default dashboard. Use get_dashboards to list all."}
            },
            "required": []
        }
    },
    {
        "name": "update_dashboard",
        "description": "Update/modify an existing Lovelace dashboard configuration. First use get_dashboard_config to read the current config, modify it, then save with this tool. Supports all card types including custom cards (card-mod, bubble-card, mushroom, etc.).",
        "parameters": {
            "type": "object",
            "properties": {
                "url_path": {"type": "string", "description": "Dashboard URL path. Use 'lovelace' or null for the default dashboard."},
                "views": {"type": "array", "description": "Complete array of views with their cards. This REPLACES all views.", "items": {"type": "object"}}
            },
            "required": ["views"]
        }
    },
    {
        "name": "get_frontend_resources",
        "description": "List all registered Lovelace frontend resources (custom cards, modules). Use this to check if custom cards like card-mod, bubble-card, mushroom-cards, etc. are installed via HACS.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "read_config_file",
        "description": "Read a Home Assistant configuration file (e.g. configuration.yaml, automations.yaml, scripts.yaml, secrets.yaml, ui-lovelace.yaml, or any YAML/JSON file in the config directory). Returns file content as text.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File path relative to HA config dir (e.g. 'configuration.yaml', 'ui-lovelace.yaml', 'dashboards/energy.yaml')."}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "write_config_file",
        "description": "Write/update a Home Assistant configuration file. ALWAYS creates a snapshot backup first (automatically). Use for editing configuration.yaml, YAML dashboards, includes, packages, etc. After writing, call check_config to validate.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File path relative to HA config dir (e.g. 'configuration.yaml', 'ui-lovelace.yaml')."},
                "content": {"type": "string", "description": "The full file content to write."}
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "check_config",
        "description": "Validate Home Assistant configuration. Call this after modifying configuration.yaml or any YAML file. Returns 'valid' or error details.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "list_config_files",
        "description": "List files in the Home Assistant config directory (or a subdirectory). Useful to discover YAML dashboards, packages, includes, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Subdirectory to list (empty for root config dir). E.g. 'dashboards', 'packages', 'custom_components'."}
            },
            "required": []
        }
    },
    {
        "name": "list_snapshots",
        "description": "List all available configuration snapshots. Snapshots are auto-created before any file modification.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "restore_snapshot",
        "description": "Restore a file from a previously created snapshot. Use list_snapshots to see available snapshots.",
        "parameters": {
            "type": "object",
            "properties": {
                "snapshot_id": {"type": "string", "description": "The snapshot ID (from list_snapshots)."}
            },
            "required": ["snapshot_id"]
        }
    }
]


def get_anthropic_tools():
    """Convert tools to Anthropic format."""
    tools = HA_TOOLS_DESCRIPTION
    if not ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_GROUPS.get("config_edit", []))
        filtered_count = len([t for t in tools if t["name"] in config_edit_tools])
        logger.info(f"ENABLE_FILE_ACCESS=False: filtering {filtered_count} config_edit tools: {config_edit_tools}")
        tools = [t for t in tools if t["name"] not in config_edit_tools]
    return [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in tools
    ]


def get_openai_tools():
    """Convert tools to OpenAI function-calling format."""
    tools = HA_TOOLS_DESCRIPTION
    if not ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_GROUPS.get("config_edit", []))
        filtered_count = len([t for t in tools if t["name"] in config_edit_tools])
        logger.debug(f"OpenAI: filtering {filtered_count} config_edit tools")
        tools = [t for t in tools if t["name"] not in config_edit_tools]
    return [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
        for t in tools
    ]


def get_gemini_tools():
    """Convert tools to Google Gemini format."""
    from google.generativeai.types import FunctionDeclaration, Tool
    tools = HA_TOOLS_DESCRIPTION
    if not ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_GROUPS.get("config_edit", []))
        tools = [t for t in tools if t["name"] not in config_edit_tools]
    declarations = []
    for t in tools:
        declarations.append(FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=t["parameters"]
        ))
    return Tool(function_declarations=declarations)


# ---- Tool execution ----


def execute_tool(tool_name: str, tool_input: Dict) -> str:
    """Execute a tool call and return the result as string."""
    try:
        if tool_name == "get_entities":
            domain = tool_input.get("domain", "")
            states = get_all_states()
            if domain:
                states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
            # Limit results for providers with small context windows
            max_entities = 30 if AI_PROVIDER == "github" else 100
            result = []
            for s in states[:max_entities]:
                result.append({
                    "entity_id": s.get("entity_id"),
                    "state": s.get("state"),
                    "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                    "attributes": {k: v for k, v in s.get("attributes", {}).items()
                                   if k in ("friendly_name", "unit_of_measurement", "device_class",
                                            "brightness", "color_temp", "temperature",
                                            "current_temperature", "hvac_modes")}
                })
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "get_entity_state":
            entity_id = tool_input.get("entity_id", "")
            result = call_ha_api("GET", f"states/{entity_id}")
            # Return only essential fields to save tokens
            if isinstance(result, dict):
                slim = {
                    "entity_id": result.get("entity_id"),
                    "state": result.get("state"),
                    "friendly_name": result.get("attributes", {}).get("friendly_name", ""),
                    "last_changed": result.get("last_changed", "")
                }
                # Include only useful attributes
                attrs = result.get("attributes", {})
                useful_keys = ("friendly_name", "unit_of_measurement", "device_class",
                              "brightness", "color_temp", "temperature", "current_temperature",
                              "hvac_modes", "hvac_action", "preset_mode", "source", "media_title",
                              "id")  # 'id' is critical for automations
                slim["attributes"] = {k: v for k, v in attrs.items() if k in useful_keys}
                return json.dumps(slim, ensure_ascii=False, default=str)
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "call_service":
            domain = tool_input.get("domain", "")
            service = tool_input.get("service", "")
            data = tool_input.get("data", {})
            result = call_ha_api("POST", f"services/{domain}/{service}", data)
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "create_automation":
            import yaml
            config = {
                "alias": tool_input.get("alias", "New Automation"),
                "description": tool_input.get("description", ""),
                "trigger": tool_input.get("trigger", []),
                "condition": tool_input.get("condition", []),
                "action": tool_input.get("action", []),
                "mode": tool_input.get("mode", "single"),
            }
            result = call_ha_api("POST", "config/automation/config/new", config)
            if isinstance(result, dict) and "error" not in result:
                # Return the YAML so AI can show it to the user
                created_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
                return json.dumps({
                    "status": "success",
                    "message": f"Automation '{config['alias']}' created!",
                    "yaml": created_yaml,
                    "result": result,
                    "IMPORTANT": "Show the user the YAML code you created."
                }, ensure_ascii=False, default=str)
            return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_automations":
            states = get_all_states()
            autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
            result = [{"entity_id": a.get("entity_id"), "state": a.get("state"),
                       "friendly_name": a.get("attributes", {}).get("friendly_name", ""),
                       "id": a.get("attributes", {}).get("id", ""),
                       "last_triggered": a.get("attributes", {}).get("last_triggered", "")} for a in autos]
            return json.dumps({"automations": result, "edit_hint": "To edit an automation, use update_automation with the automation's id and the changes you want to make."}, ensure_ascii=False, default=str)

        elif tool_name == "update_automation":
            import yaml
            automation_id = tool_input.get("automation_id", "")
            changes = tool_input.get("changes", {})
            add_condition = tool_input.get("add_condition", None)
            
            if not automation_id:
                return json.dumps({"error": "automation_id is required."})
            
            # Strategy: try YAML first, then REST API fallback (for UI-created automations)
            updated_via = None
            old_yaml = ""
            new_yaml = ""
            
            # --- ATTEMPT 1: YAML file ---
            yaml_path = get_config_file_path("automation", "automations.yaml")
            if os.path.isfile(yaml_path):
                try:
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        automations = yaml.safe_load(f)
                    
                    if isinstance(automations, list):
                        found = None
                        found_idx = None
                        for idx, auto in enumerate(automations):
                            if str(auto.get("id", "")) == str(automation_id):
                                found = auto
                                found_idx = idx
                                break
                        
                        if found is not None:
                            old_yaml = yaml.dump(found, default_flow_style=False, allow_unicode=True)
                            cond_key = "conditions" if "conditions" in found else "condition"
                            # Remap condition↔conditions in changes to match existing key
                            if "condition" in changes and cond_key == "conditions":
                                changes["conditions"] = changes.pop("condition")
                            elif "conditions" in changes and cond_key == "condition":
                                changes["condition"] = changes.pop("conditions")
                            for key, value in changes.items():
                                found[key] = value
                            if add_condition:
                                if cond_key not in found or not found[cond_key]:
                                    found[cond_key] = []
                                if not isinstance(found[cond_key], list):
                                    found[cond_key] = [found[cond_key]]
                                found[cond_key].append(add_condition)
                            new_yaml = yaml.dump(found, default_flow_style=False, allow_unicode=True)
                            snapshot = create_snapshot("automations.yaml")
                            automations[found_idx] = found
                            with open(yaml_path, "w", encoding="utf-8") as f:
                                yaml.dump(automations, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                            updated_via = "yaml"
                except Exception as e:
                    logger.warning(f"YAML update attempt failed: {e}")
            
            # --- ATTEMPT 2: REST API (for UI-created automations) ---
            if updated_via is None:
                try:
                    # Get current config via REST API
                    current = call_ha_api("GET", f"config/automation/config/{automation_id}")
                    if isinstance(current, dict) and "error" not in current:
                        old_yaml = yaml.dump(current, default_flow_style=False, allow_unicode=True)
                        
                        # Normalize: HA may use 'condition' or 'conditions' - unify to what HA returned
                        cond_key = "conditions" if "conditions" in current else "condition"
                        
                        # Remap condition↔conditions in changes to match existing key
                        if "condition" in changes and cond_key == "conditions":
                            changes["conditions"] = changes.pop("condition")
                        elif "conditions" in changes and cond_key == "condition":
                            changes["condition"] = changes.pop("conditions")
                        
                        # Apply changes
                        for key, value in changes.items():
                            current[key] = value
                        if add_condition:
                            if cond_key not in current or not current[cond_key]:
                                current[cond_key] = []
                            if not isinstance(current[cond_key], list):
                                current[cond_key] = [current[cond_key]]
                            current[cond_key].append(add_condition)
                        
                        # Ensure no duplicate condition/conditions keys
                        if "condition" in current and "conditions" in current:
                            # Keep whichever has data, prefer 'conditions' (new format)
                            if current.get("conditions"):
                                current.pop("condition", None)
                            else:
                                current.pop("conditions", None)
                        
                        new_yaml = yaml.dump(current, default_flow_style=False, allow_unicode=True)
                        # Save via REST API (HA uses POST for both create and update)
                        save_result = call_ha_api("POST", f"config/automation/config/{automation_id}", current)
                        if isinstance(save_result, dict) and "error" not in save_result:
                            updated_via = "rest_api"
                        else:
                            return json.dumps({"error": f"REST API update failed: {save_result}",
                                               "IMPORTANT": "STOP. Inform the user about the error. Do NOT try other tools."}, default=str)
                    else:
                        return json.dumps({"error": f"Automation '{automation_id}' not found in YAML or via REST API.",
                                           "IMPORTANT": "STOP. Tell the user the automation was not found. Do NOT call more tools."}, default=str)
                except Exception as e:
                    return json.dumps({"error": f"Failed to update automation: {str(e)}",
                                       "IMPORTANT": "STOP. Inform the user about the error. Do NOT try other tools."})
            
            msg_parts = [f"Automation updated via {'YAML file' if updated_via == 'yaml' else 'HA REST API (UI-created automation)'}.",]
            return json.dumps({
                "status": "success",
                "message": " ".join(msg_parts),
                "updated_via": updated_via,
                "old_yaml": old_yaml,
                "new_yaml": new_yaml,
                "snapshot": snapshot.get("snapshot_id", "") if updated_via == "yaml" else "N/A (REST API)",
                "tip": "Changes applied immediately via REST API. No reload needed." if updated_via == "rest_api" else "Call services/automation/reload to apply changes.",
                "IMPORTANT": "DONE. Show the user the before/after diff and stop. Do NOT call any more tools."
            }, ensure_ascii=False, default=str)

        elif tool_name == "trigger_automation":
            entity_id = tool_input.get("entity_id", "")
            result = call_ha_api("POST", "services/automation/trigger", {"entity_id": entity_id})
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_available_services":
            svc_raw = call_ha_api("GET", "services")
            if isinstance(svc_raw, list):
                compact = {s.get("domain", ""): list(s.get("services", {}).keys()) for s in svc_raw}
                return json.dumps(compact, ensure_ascii=False)
            return json.dumps(svc_raw, ensure_ascii=False, default=str)

        elif tool_name == "search_entities":
            query = tool_input.get("query", "").lower().strip()
            states = get_all_states()
            matches = []
            
            # Build search index with scoring
            search_results = []
            
            for s in states:
                eid = s.get("entity_id", "").lower()
                fname = s.get("attributes", {}).get("friendly_name", "").lower()
                
                score = 0
                
                # Check 1: Exact substring in entity_id (highest priority)
                if query in eid:
                    score += 100
                
                # Check 2: Exact substring in friendly_name
                if query in fname:
                    score += 95
                
                # Check 3: Tokenization (split by underscore/hyphen/space and match individual tokens)
                # This allows "produzione" to match "yesterday_production" or "production_daily"
                eid_tokens = [t.strip() for t in eid.replace(".", " ").replace("_", " ").replace("-", " ").split()]
                fname_tokens = [t.strip() for t in fname.replace("_", " ").replace("-", " ").split()]
                query_tokens = [t.strip() for t in query.replace("_", " ").replace("-", " ").split()]
                
                # Check if any query token matches any entity token (for better cross-language matching)
                for qt in query_tokens:
                    for et in eid_tokens:
                        if len(qt) > 2 and len(et) > 2:
                            # Fuzzy match: if first 3 chars match or Levenshtein distance < 2
                            if qt[:3] == et[:3]:  # Quick prefix match
                                score += 30
                            elif abs(len(qt) - len(et)) <= 2 and (qt in et or et in qt):
                                score += 25
                    for et in fname_tokens:
                        if len(qt) > 2 and len(et) > 2:
                            if qt[:3] == et[:3]:
                                score += 35  # Friendly name match is slightly higher
                            elif abs(len(qt) - len(et)) <= 2 and (qt in et or et in qt):
                                score += 30
                
                # Check 4: Partial match (substring anywhere)
                if score == 0:
                    if query in eid or query in fname:
                        score += 10
                
                if score > 0:
                    search_results.append({
                        "entity_id": s.get("entity_id"),
                        "state": s.get("state"),
                        "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                        "score": score
                    })
            
            # Sort by score (descending) and take top results
            search_results.sort(key=lambda x: (-x["score"], x["entity_id"]))
            max_results = 20 if AI_PROVIDER == "github" else 50
            matches = [{k: v for k, v in item.items() if k != "score"} for item in search_results[:max_results]]
            
            return json.dumps(matches, ensure_ascii=False, default=str)

        elif tool_name == "get_events":
            events = call_ha_api("GET", "events")
            if isinstance(events, list):
                result = [{"event": e.get("event", ""), "listener_count": e.get("listener_count", 0)} for e in events]
                return json.dumps(result, ensure_ascii=False, default=str)
            return json.dumps(events, ensure_ascii=False, default=str)

        elif tool_name == "get_history":
            entity_id = tool_input.get("entity_id", "")
            hours = min(int(tool_input.get("hours", 24)), 168)
            start = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
            endpoint = f"history/period/{start}?filter_entity_id={entity_id}&significant_changes_only=1"
            result = call_ha_api("GET", endpoint)
            if isinstance(result, list) and result:
                entries = result[0] if isinstance(result[0], list) else result
                max_e = 20 if AI_PROVIDER == "github" else 50
                summary = [{"state": e.get("state"), "last_changed": e.get("last_changed")} for e in entries[-max_e:]]
                return json.dumps({"entity_id": entity_id, "hours": hours, "total_changes": len(entries), "history": summary}, ensure_ascii=False, default=str)
            return json.dumps({"entity_id": entity_id, "hours": hours, "history": []}, ensure_ascii=False, default=str)

        elif tool_name == "get_scenes":
            states = get_all_states()
            scenes = [{"entity_id": s.get("entity_id"), "state": s.get("state"),
                       "friendly_name": s.get("attributes", {}).get("friendly_name", "")}
                      for s in states if s.get("entity_id", "").startswith("scene.")]
            return json.dumps(scenes, ensure_ascii=False, default=str)

        elif tool_name == "activate_scene":
            entity_id = tool_input.get("entity_id", "")
            result = call_ha_api("POST", "services/scene/turn_on", {"entity_id": entity_id})
            return json.dumps({"status": "success", "scene": entity_id, "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_scripts":
            states = get_all_states()
            scripts = [{"entity_id": s.get("entity_id"), "state": s.get("state"),
                        "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                        "last_triggered": s.get("attributes", {}).get("last_triggered", "")}
                       for s in states if s.get("entity_id", "").startswith("script.")]
            return json.dumps(scripts, ensure_ascii=False, default=str)

        elif tool_name == "run_script":
            entity_id = tool_input.get("entity_id", "")
            variables = tool_input.get("variables", {})
            script_id = entity_id.replace("script.", "") if entity_id.startswith("script.") else entity_id
            result = call_ha_api("POST", f"services/script/{script_id}", variables)
            return json.dumps({"status": "success", "script": entity_id, "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "update_script":
            import yaml
            script_id = tool_input.get("script_id", "")
            changes = tool_input.get("changes", {})

            if not script_id:
                return json.dumps({"error": "script_id is required."})

            # Remove 'script.' prefix if present
            script_id = script_id.replace("script.", "") if script_id.startswith("script.") else script_id

            yaml_path = get_config_file_path("script", "scripts.yaml")
            if not os.path.isfile(yaml_path):
                return json.dumps({"error": "scripts.yaml not found."})

            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    scripts = yaml.safe_load(f)

                if not isinstance(scripts, dict):
                    return json.dumps({"error": "scripts.yaml is not a valid dict."})

                if script_id not in scripts:
                    return json.dumps({"error": f"Script '{script_id}' not found.",
                                       "available_scripts": list(scripts.keys())[:20]})

                found = scripts[script_id]
                if not isinstance(found, dict):
                    found = {}

                # Capture old state for diff
                old_yaml = yaml.dump({script_id: found}, default_flow_style=False, allow_unicode=True)

                # Apply changes
                for key, value in changes.items():
                    found[key] = value

                # Capture new state for diff
                new_yaml = yaml.dump({script_id: found}, default_flow_style=False, allow_unicode=True)

                # Create snapshot before saving
                snapshot = create_snapshot("scripts.yaml")

                # Write back
                scripts[script_id] = found
                with open(yaml_path, "w", encoding="utf-8") as f:
                    yaml.dump(scripts, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                return json.dumps({
                    "status": "success",
                    "message": f"Script '{found.get('alias', script_id)}' updated.",
                    "old_yaml": old_yaml,
                    "new_yaml": new_yaml,
                    "snapshot": snapshot.get("snapshot_id", ""),
                    "tip": "Call services/script/reload to apply changes.",
                    "IMPORTANT": "DONE. Show the user the before/after diff and stop. Do NOT call any more tools."
                }, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to update script: {str(e)}"})

        elif tool_name == "get_areas":
            try:
                template = '[{% for area in areas() %}{"id":{{ area | tojson }}, "name":{{ area_name(area) | tojson }}, "entities":{{ area_entities(area) | list | tojson }}}{% if not loop.last %},{% endif %}{% endfor %}]'
                url = f"{HA_URL}/api/template"
                resp = requests.post(url, headers=get_ha_headers(), json={"template": template}, timeout=30)
                if resp.status_code == 200:
                    areas_data = json.loads(resp.text)
                    if AI_PROVIDER == "github":
                        for area in areas_data:
                            area["entities"] = area["entities"][:10]
                    return json.dumps(areas_data, ensure_ascii=False, default=str)
                return json.dumps({"error": f"Template API error: {resp.status_code}"}, default=str)
            except Exception as e:
                return json.dumps({"error": f"Could not get areas: {str(e)}"}, default=str)

        elif tool_name == "send_notification":
            message = tool_input.get("message", "")
            title = tool_input.get("title", "AI Assistant")
            target = tool_input.get("target", "")
            if target:
                result = call_ha_api("POST", f"services/notify/{target}", {"message": message, "title": title})
            else:
                result = call_ha_api("POST", "services/persistent_notification/create", {"message": message, "title": title})
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_dashboards":
            ws_result = call_ha_websocket("lovelace/dashboards/list")
            if ws_result.get("success") and ws_result.get("result"):
                dashboards = ws_result["result"]
                result = [{"id": d.get("id"), "title": d.get("title"), "url_path": d.get("url_path"),
                           "icon": d.get("icon", ""), "mode": d.get("mode", "")} for d in dashboards]
                return json.dumps(result, ensure_ascii=False, default=str)
            return json.dumps({"error": f"Could not get dashboards: {ws_result}"}, default=str)

        elif tool_name == "create_dashboard":
            title = tool_input.get("title", "AI Dashboard")
            url_path = tool_input.get("url_path", "ai-dashboard")
            icon = tool_input.get("icon", "mdi:robot")
            views = tool_input.get("views", [])

            # Step 1: Register dashboard via WebSocket (REST API doesn't support this)
            ws_result = call_ha_websocket(
                "lovelace/dashboards/create",
                url_path=url_path,
                title=title,
                icon=icon,
                show_in_sidebar=True,
                require_admin=False
            )
            if ws_result.get("success") is False:
                error_msg = ws_result.get("error", {}).get("message", str(ws_result))
                return json.dumps({"error": f"Failed to create dashboard: {error_msg}"}, default=str)

            # Step 2: Set the dashboard config with views and cards via WebSocket
            ws_config = call_ha_websocket(
                "lovelace/config/save",
                url_path=url_path,
                config={"views": views}
            )
            if ws_config.get("success") is False:
                error_msg = ws_config.get("error", {}).get("message", str(ws_config))
                return json.dumps({"status": "partial", "message": f"Dashboard registered but config failed: {error_msg}"}, default=str)

            # Return the YAML so AI can show it to the user
            import yaml
            dashboard_yaml = yaml.dump({"views": views}, default_flow_style=False, allow_unicode=True)
            return json.dumps({
                "status": "success",
                "message": f"Dashboard '{title}' created! It appears in the sidebar at /{url_path}",
                "url_path": url_path,
                "views_count": len(views),
                "yaml": dashboard_yaml,
                "IMPORTANT": "Show the user the dashboard YAML you created."
            }, ensure_ascii=False, default=str)

        elif tool_name == "create_script":
            import yaml
            script_id = tool_input.get("script_id", "")
            config = {
                "alias": tool_input.get("alias", "New Script"),
                "description": tool_input.get("description", ""),
                "sequence": tool_input.get("sequence", []),
                "mode": tool_input.get("mode", "single"),
            }
            result = call_ha_api("POST", f"config/script/config/{script_id}", config)
            if isinstance(result, dict) and "error" not in result:
                # Return the YAML so AI can show it to the user
                created_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
                return json.dumps({
                    "status": "success",
                    "message": f"Script '{config['alias']}' created (script.{script_id})",
                    "entity_id": f"script.{script_id}",
                    "yaml": created_yaml,
                    "result": result,
                    "IMPORTANT": "Show the user the YAML code you created."
                }, ensure_ascii=False, default=str)
            return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

        # ===== DELETE OPERATIONS (WebSocket) =====
        elif tool_name == "delete_dashboard":
            dashboard_id = tool_input.get("dashboard_id", "")
            result = call_ha_websocket("lovelace/dashboards/delete", dashboard_id=dashboard_id)
            if result.get("success"):
                return json.dumps({"status": "success", "message": f"Dashboard '{dashboard_id}' deleted."}, ensure_ascii=False)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to delete dashboard: {error_msg}"}, default=str)

        elif tool_name == "delete_automation":
            automation_id = tool_input.get("automation_id", "")
            logger.info(f"delete_automation called: automation_id='{automation_id}'")

            # Need the object_id (without automation. prefix)
            object_id = automation_id.replace("automation.", "") if automation_id.startswith("automation.") else automation_id

            # Try API first (for UI-created automations)
            result = call_ha_api("DELETE", f"config/automation/config/{object_id}")
            if result and not isinstance(result, dict):
                logger.info(f"Automation deleted via API: {automation_id}")
                return json.dumps({"status": "success", "message": f"Automation '{automation_id}' deleted via API."}, ensure_ascii=False, default=str)

            # If API failed, try removing from YAML file (for file-based automations)
            logger.info(f"API delete failed, trying YAML file removal for: {automation_id}")
            yaml_path = get_config_file_path("automation", "automations.yaml")

            if not os.path.isfile(yaml_path):
                return json.dumps({"error": f"Cannot delete automation: API failed and {yaml_path} not found."}, ensure_ascii=False)

            try:
                # Create snapshot before modifying
                snapshot = create_snapshot("automations.yaml")

                with open(yaml_path, "r", encoding="utf-8") as f:
                    automations = yaml.safe_load(f) or []

                if not isinstance(automations, list):
                    return json.dumps({"error": "automations.yaml is not a list format"}, ensure_ascii=False)

                # Find and remove the automation by ID or alias
                found = False
                original_count = len(automations)

                # Try matching by ID first
                automations = [a for a in automations if str(a.get("id", "")) != object_id]

                # If no match by ID, try by alias (the display name)
                if len(automations) == original_count:
                    # Extract the name from the full automation_id if it looks like a title
                    name_to_match = automation_id.replace("automation.", "").replace("_", " ")
                    automations = [a for a in automations if a.get("alias", "").lower() != name_to_match.lower()]

                if len(automations) < original_count:
                    found = True
                    # Write back to file
                    with open(yaml_path, "w", encoding="utf-8") as f:
                        yaml.dump(automations, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                    logger.info(f"Automation deleted from YAML: {automation_id}")
                    return json.dumps({
                        "status": "success",
                        "message": f"Automation '{automation_id}' removed from {yaml_path}. Restart Home Assistant to apply changes.",
                        "snapshot": snapshot,
                        "restart_required": True
                    }, ensure_ascii=False, default=str)
                else:
                    return json.dumps({"error": f"Automation '{automation_id}' not found in {yaml_path}"}, ensure_ascii=False)

            except Exception as e:
                logger.error(f"Error deleting automation from YAML: {e}")
                return json.dumps({"error": f"Failed to delete from YAML: {str(e)}"}, ensure_ascii=False)

        elif tool_name == "delete_script":
            script_id = tool_input.get("script_id", "")
            logger.info(f"delete_script called: script_id='{script_id}'")

            object_id = script_id.replace("script.", "") if script_id.startswith("script.") else script_id

            # Try API first (for UI-created scripts)
            result = call_ha_api("DELETE", f"config/script/config/{object_id}")
            if result and not isinstance(result, dict):
                logger.info(f"Script deleted via API: {script_id}")
                return json.dumps({"status": "success", "message": f"Script '{script_id}' deleted via API."}, ensure_ascii=False, default=str)

            # If API failed, try removing from YAML file
            logger.info(f"API delete failed, trying YAML file removal for: {script_id}")
            yaml_path = get_config_file_path("script", "scripts.yaml")

            if not os.path.isfile(yaml_path):
                return json.dumps({"error": f"Cannot delete script: API failed and {yaml_path} not found."}, ensure_ascii=False)

            try:
                # Create snapshot before modifying
                snapshot = create_snapshot("scripts.yaml")

                with open(yaml_path, "r", encoding="utf-8") as f:
                    scripts = yaml.safe_load(f) or {}

                if not isinstance(scripts, dict):
                    return json.dumps({"error": "scripts.yaml is not a dict format"}, ensure_ascii=False)

                # Remove the script by key
                if object_id in scripts:
                    del scripts[object_id]

                    # Write back to file
                    with open(yaml_path, "w", encoding="utf-8") as f:
                        yaml.dump(scripts, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                    logger.info(f"Script deleted from YAML: {script_id}")
                    return json.dumps({
                        "status": "success",
                        "message": f"Script '{script_id}' removed from {yaml_path}. Restart Home Assistant to apply changes.",
                        "snapshot": snapshot,
                        "restart_required": True
                    }, ensure_ascii=False, default=str)
                else:
                    return json.dumps({"error": f"Script '{script_id}' not found in {yaml_path}"}, ensure_ascii=False)

            except Exception as e:
                logger.error(f"Error deleting script from YAML: {e}")
                return json.dumps({"error": f"Failed to delete from YAML: {str(e)}"}, ensure_ascii=False)

        # ===== AREA MANAGEMENT (WebSocket) =====
        elif tool_name == "manage_areas":
            action = tool_input.get("action", "list")
            if action == "list":
                result = call_ha_websocket("config/area_registry/list")
                areas = result.get("result", [])
                summary = [{"area_id": a.get("area_id"), "name": a.get("name"), "icon": a.get("icon", "")} for a in areas]
                return json.dumps({"areas": summary, "count": len(summary)}, ensure_ascii=False, default=str)
            elif action == "create":
                name = tool_input.get("name", "")
                params = {"name": name}
                if tool_input.get("icon"):
                    params["icon"] = tool_input["icon"]
                result = call_ha_websocket("config/area_registry/create", **params)
                if result.get("success"):
                    area = result.get("result", {})
                    return json.dumps({"status": "success", "message": f"Area '{name}' created.", "area_id": area.get("area_id")}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to create area: {error_msg}"}, default=str)
            elif action == "update":
                area_id = tool_input.get("area_id", "")
                params = {"area_id": area_id}
                if tool_input.get("name"):
                    params["name"] = tool_input["name"]
                if tool_input.get("icon"):
                    params["icon"] = tool_input["icon"]
                result = call_ha_websocket("config/area_registry/update", **params)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Area '{area_id}' updated."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to update area: {error_msg}"}, default=str)
            elif action == "delete":
                area_id = tool_input.get("area_id", "")
                result = call_ha_websocket("config/area_registry/delete", area_id=area_id)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Area '{area_id}' deleted."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to delete area: {error_msg}"}, default=str)

        # ===== ENTITY REGISTRY (WebSocket) =====
        elif tool_name == "manage_entity":
            entity_id = tool_input.get("entity_id", "")
            params = {"entity_id": entity_id}
            if tool_input.get("name") is not None:
                params["name"] = tool_input["name"]
            if tool_input.get("area_id") is not None:
                params["area_id"] = tool_input["area_id"]
            if tool_input.get("disabled_by") is not None:
                params["disabled_by"] = tool_input["disabled_by"] if tool_input["disabled_by"] else None
            if tool_input.get("icon") is not None:
                params["icon"] = tool_input["icon"]
            result = call_ha_websocket("config/entity_registry/update", **params)
            if result.get("success"):
                entry = result.get("result", {})
                return json.dumps({"status": "success", "message": f"Entity '{entity_id}' updated.",
                                   "name": entry.get("name"), "area_id": entry.get("area_id"),
                                   "disabled_by": entry.get("disabled_by")}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to update entity: {error_msg}"}, default=str)

        # ===== DEVICE REGISTRY (WebSocket) =====
        elif tool_name == "get_devices":
            result = call_ha_websocket("config/device_registry/list")
            devices = result.get("result", [])
            summary = []
            for d in devices[:100]:  # Limit to 100 devices
                summary.append({
                    "id": d.get("id"),
                    "name": d.get("name_by_user") or d.get("name", ""),
                    "manufacturer": d.get("manufacturer", ""),
                    "model": d.get("model", ""),
                    "area_id": d.get("area_id", ""),
                    "via_device_id": d.get("via_device_id", "")
                })
            return json.dumps({"devices": summary, "count": len(devices), "showing": len(summary)}, ensure_ascii=False, default=str)

        # ===== ADVANCED STATISTICS (WebSocket) =====
        elif tool_name == "get_statistics":
            entity_id = tool_input.get("entity_id", "")
            period = tool_input.get("period", "hour")
            hours = min(tool_input.get("hours", 24), 720)
            start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
            result = call_ha_websocket(
                "recorder/statistics_during_period",
                start_time=start_time,
                statistic_ids=[entity_id],
                period=period
            )
            stats = result.get("result", {}).get(entity_id, [])
            # Summarize: take last 50 entries max
            summary_stats = []
            for s in stats[-50:]:
                summary_stats.append({
                    "start": s.get("start"),
                    "mean": s.get("mean"),
                    "min": s.get("min"),
                    "max": s.get("max"),
                    "sum": s.get("sum"),
                    "state": s.get("state")
                })
            return json.dumps({"entity_id": entity_id, "period": period,
                               "hours": hours, "statistics": summary_stats,
                               "total_entries": len(stats)}, ensure_ascii=False, default=str)

        # ===== SHOPPING LIST (WebSocket) =====
        elif tool_name == "shopping_list":
            action = tool_input.get("action", "list")
            if action == "list":
                result = call_ha_websocket("shopping_list/items")
                items = result.get("result", [])
                return json.dumps({"items": items, "count": len(items)}, ensure_ascii=False, default=str)
            elif action == "add":
                name = tool_input.get("name", "")
                result = call_ha_websocket("shopping_list/items/add", name=name)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"'{name}' added to shopping list.",
                                       "item": result.get("result", {})}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to add item: {error_msg}"}, default=str)
            elif action == "complete":
                item_id = tool_input.get("item_id", "")
                result = call_ha_websocket("shopping_list/items/update", item_id=item_id, complete=True)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Item marked as complete."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to complete item: {error_msg}"}, default=str)

        # ===== BACKUP (Supervisor REST API) =====
        elif tool_name == "create_backup":
            try:
                ha_token = get_ha_token()
                resp = requests.post(
                    "http://supervisor/backups/new/full",
                    headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
                    json={"name": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"},
                    timeout=300
                )
                result = resp.json()
                if result.get("result") == "ok":
                    slug = result.get("data", {}).get("slug", "")
                    return json.dumps({"status": "success", "message": f"Backup created successfully!", "slug": slug}, ensure_ascii=False, default=str)
                return json.dumps({"error": f"Backup failed: {result}"}, default=str)
            except Exception as e:
                return json.dumps({"error": f"Backup error: {str(e)}"}, default=str)

        # ===== BROWSE MEDIA (WebSocket) =====
        elif tool_name == "browse_media":
            content_id = tool_input.get("media_content_id", "")
            content_type = tool_input.get("media_content_type", "music")
            params = {"media_content_type": content_type}
            if content_id:
                params["media_content_id"] = content_id
            result = call_ha_websocket("media_player/browse_media", **params)
            if result.get("success"):
                media = result.get("result", {})
                children = media.get("children", [])
                summary = []
                for c in children[:50]:
                    summary.append({
                        "title": c.get("title", ""),
                        "media_content_id": c.get("media_content_id", ""),
                        "media_content_type": c.get("media_content_type", ""),
                        "media_class": c.get("media_class", ""),
                        "can_expand": c.get("can_expand", False),
                        "can_play": c.get("can_play", False)
                    })
                return json.dumps({"title": media.get("title", "Media"), "children": summary,
                                   "count": len(children)}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Browse media failed: {error_msg}"}, default=str)

        # ===== DASHBOARD READ/EDIT =====
        elif tool_name == "get_dashboard_config":
            url_path = tool_input.get("url_path", None)
            params = {}
            if url_path and url_path != "lovelace":
                params["url_path"] = url_path
            result = call_ha_websocket("lovelace/config", **params)
            if result.get("success"):
                config = result.get("result", {})
                views = config.get("views", [])
                # Summarize to avoid huge response
                summary_views = []
                for v in views:
                    cards = v.get("cards", [])
                    card_summary = []
                    for c in cards:
                        card_info = {"type": c.get("type", "unknown")}
                        if c.get("title"):
                            card_info["title"] = c["title"]
                        if c.get("entity"):
                            card_info["entity"] = c["entity"]
                        if c.get("entities"):
                            card_info["entities"] = c["entities"][:10]
                        # Include full card for custom types
                        if c.get("type", "").startswith("custom:"):
                            card_info = c
                        card_summary.append(card_info)
                    summary_views.append({
                        "title": v.get("title", ""),
                        "path": v.get("path", ""),
                        "icon": v.get("icon", ""),
                        "cards_count": len(cards),
                        "cards": card_summary
                    })
                return json.dumps({"url_path": url_path or "lovelace",
                                   "views": summary_views, "views_count": len(views),
                                   "full_config": config}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to get dashboard config: {error_msg}"}, default=str)

        elif tool_name == "update_dashboard":
            import yaml
            url_path = tool_input.get("url_path", None)
            views = tool_input.get("views", [])
            old_yaml = ""
            new_yaml = ""

            # Auto-snapshot: save current dashboard config before modifying
            try:
                snap_params = {}
                if url_path and url_path != "lovelace":
                    snap_params["url_path"] = url_path
                old_config = call_ha_websocket("lovelace/config", **snap_params)
                if old_config.get("success"):
                    old_result = old_config.get("result", {})
                    old_yaml = yaml.dump({"views": old_result.get("views", [])}, default_flow_style=False, allow_unicode=True)

                    snap_file = f"_dashboard_snapshot_{url_path or 'lovelace'}.json"
                    snap_path = os.path.join(SNAPSHOTS_DIR, datetime.now().strftime("%Y%m%d_%H%M%S") + snap_file)
                    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
                    with open(snap_path, "w") as sf:
                        json.dump({"url_path": url_path or "lovelace", "config": old_result}, sf)
                    logger.info(f"Dashboard snapshot saved: {snap_path}")
            except Exception as e:
                logger.warning(f"Could not snapshot dashboard before update: {e}")

            new_yaml = yaml.dump({"views": views}, default_flow_style=False, allow_unicode=True)

            params = {"config": {"views": views}}
            if url_path and url_path != "lovelace":
                params["url_path"] = url_path
            result = call_ha_websocket("lovelace/config/save", **params)
            if result.get("success"):
                return json.dumps({
                    "status": "success",
                    "message": f"Dashboard '{url_path or 'lovelace'}' updated with {len(views)} view(s). A backup snapshot was saved.",
                    "views_count": len(views),
                    "old_yaml": old_yaml,
                    "new_yaml": new_yaml,
                    "IMPORTANT": "Show the user the before/after diff of the dashboard YAML."
                }, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to update dashboard: {error_msg}"}, default=str)

        elif tool_name == "get_frontend_resources":
            result = call_ha_websocket("lovelace/resources")
            if result.get("success"):
                resources = result.get("result", [])
                summary = []
                for r in resources:
                    url = r.get("url", "")
                    # Extract card name from URL
                    name = url.split("/")[-1].split(".")[0].split("?")[0] if url else ""
                    summary.append({
                        "id": r.get("id"),
                        "url": url,
                        "type": r.get("type", "module"),
                        "name": name
                    })
                # Check for common custom cards
                all_urls = " ".join([r.get("url", "") for r in resources]).lower()
                detected = []
                for card_name in ["card-mod", "bubble-card", "mushroom", "mini-graph", "mini-media-player",
                                  "button-card", "layout-card", "stack-in-card", "slider-entity-row",
                                  "auto-entities", "decluttering-card", "apexcharts-card", "swipe-card",
                                  "tabbed-card", "vertical-stack-in-card", "atomic-calendar"]:
                    if card_name in all_urls:
                        detected.append(card_name)
                return json.dumps({"resources": summary, "count": len(summary),
                                   "detected_custom_cards": detected}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to get resources: {error_msg}"}, default=str)

        # ===== CONFIG FILE OPERATIONS =====
        elif tool_name == "read_config_file":
            filename = tool_input.get("filename", "")
            # Security: prevent path traversal
            if ".." in filename or filename.startswith("/"):
                return json.dumps({"error": "Invalid filename. Use relative paths only (e.g. 'configuration.yaml')."})
            filepath = os.path.join(HA_CONFIG_DIR, filename)
            if not os.path.isfile(filepath):
                return json.dumps({"error": f"File '{filename}' not found in HA config directory."})
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # Truncate very large files
                if len(content) > 15000:
                    content = content[:15000] + f"\n\n... [TRUNCATED - file is {len(content)} chars total]"
                return json.dumps({"filename": filename, "content": content,
                                   "size": os.path.getsize(filepath)}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to read '{filename}': {str(e)}"})

        elif tool_name == "write_config_file":
            filename = tool_input.get("filename", "")
            content = tool_input.get("content", "")
            if ".." in filename or filename.startswith("/"):
                return json.dumps({"error": "Invalid filename. Use relative paths only."})
            if not filename:
                return json.dumps({"error": "filename is required."})
            filepath = os.path.join(HA_CONFIG_DIR, filename)
            # Auto-create snapshot before writing
            snapshot = create_snapshot(filename)
            try:
                # Create parent directories if needed
                os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else filepath, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                msg = f"File '{filename}' saved successfully."
                if snapshot.get("snapshot_id"):
                    msg += f" Backup snapshot created: {snapshot['snapshot_id']}"
                return json.dumps({"status": "success", "message": msg, "snapshot": snapshot,
                                   "tip": "Call check_config to validate the configuration."}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to write '{filename}': {str(e)}", "snapshot": snapshot})

        elif tool_name == "check_config":
            try:
                ha_token = get_ha_token()
                resp = requests.post(
                    f"{HA_URL}/api/config/core/check_config",
                    headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
                    timeout=30
                )
                result = resp.json()
                errors = result.get("errors", None)
                valid = result.get("result", "") == "valid"
                if valid:
                    return json.dumps({"status": "valid", "message": "Configuration is valid! You can reload or restart HA."}, ensure_ascii=False)
                return json.dumps({"status": "invalid", "errors": errors,
                                   "message": "Configuration has errors! Fix them or restore from snapshot."}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Config check failed: {str(e)}"})

        elif tool_name == "list_config_files":
            subpath = tool_input.get("path", "")
            logger.info(f"list_config_files called: subpath='{subpath}', ENABLE_FILE_ACCESS={ENABLE_FILE_ACCESS}")
            if ".." in subpath:
                return json.dumps({"error": "Invalid path."})
            dirpath = os.path.join(HA_CONFIG_DIR, subpath) if subpath else HA_CONFIG_DIR
            logger.info(f"list_config_files: checking directory '{dirpath}'")
            if not os.path.isdir(dirpath):
                logger.error(f"list_config_files: directory not found: '{dirpath}'")
                return json.dumps({"error": f"Directory '{subpath}' not found."})
            entries = []
            try:
                for entry in sorted(os.listdir(dirpath)):
                    full = os.path.join(dirpath, entry)
                    rel = os.path.join(subpath, entry) if subpath else entry
                    if os.path.isdir(full):
                        entries.append({"name": entry, "type": "directory", "path": rel})
                    else:
                        entries.append({"name": entry, "type": "file", "path": rel,
                                       "size": os.path.getsize(full)})
                # Filter out hidden/system and very large dirs
                entries = [e for e in entries if not e["name"].startswith(".")][:100]
                return json.dumps({"path": subpath or "/", "entries": entries,
                                   "count": len(entries)}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to list '{subpath}': {str(e)}"})

        # ===== SNAPSHOT MANAGEMENT =====
        elif tool_name == "list_snapshots":
            if not os.path.isdir(SNAPSHOTS_DIR):
                return json.dumps({"snapshots": [], "count": 0})
            snapshots = []
            for f in sorted(os.listdir(SNAPSHOTS_DIR)):
                if f.endswith(".meta"):
                    continue
                meta_path = os.path.join(SNAPSHOTS_DIR, f + ".meta")
                if os.path.isfile(meta_path):
                    with open(meta_path, "r") as mf:
                        meta = json.load(mf)
                    snapshots.append(meta)
                else:
                    snapshots.append({"snapshot_id": f, "original_file": f.split("_", 2)[-1].replace("__", "/")})
            return json.dumps({"snapshots": snapshots, "count": len(snapshots)}, ensure_ascii=False, default=str)

        elif tool_name == "restore_snapshot":
            snapshot_id = tool_input.get("snapshot_id", "")
            snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_id)
            meta_path = snapshot_path + ".meta"
            if not os.path.isfile(snapshot_path):
                return json.dumps({"error": f"Snapshot '{snapshot_id}' not found. Use list_snapshots."})
            # Read metadata to find original file
            original_file = ""
            if os.path.isfile(meta_path):
                with open(meta_path, "r") as mf:
                    meta = json.load(mf)
                original_file = meta.get("original_file", "")
            else:
                # Try to reconstruct from snapshot name
                parts = snapshot_id.split("_", 2)
                if len(parts) >= 3:
                    original_file = parts[2].replace("__", "/")
            if not original_file:
                return json.dumps({"error": "Cannot determine original file from snapshot."})
            # Create a snapshot of current state before restoring
            create_snapshot(original_file)
            # Restore
            import shutil
            dest = os.path.join(HA_CONFIG_DIR, original_file)
            shutil.copy2(snapshot_path, dest)
            return json.dumps({"status": "success",
                               "message": f"Restored '{original_file}' from snapshot '{snapshot_id}'. A new snapshot of the overwritten file was created.",
                               "restored_file": original_file}, ensure_ascii=False, default=str)

        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        logger.error(f"Tool error ({tool_name}): {e}")
        return json.dumps({"error": str(e)})


# ---- System prompt ----

SYSTEM_PROMPT = """You are an AI assistant integrated into Home Assistant. You help users manage their smart home.

You can:
1. **Query entities** - See device states (lights, sensors, switches, climate, covers, etc.)
2. **Control devices** - Turn on/off lights, switches, set temperatures, etc.
3. **Search entities** - Find specific devices or integrations by keyword
4. **Entity history** - Check past values and trends ("what was the temperature yesterday?")
5. **Advanced statistics** - Get min/max/mean/sum statistics for sensors over time periods
6. **Scenes & scripts** - List, activate scenes, run scripts, create new scripts
7. **Areas/rooms** - List, create, rename, delete areas. Assign entities to areas
8. **Devices & entity registry** - List devices, rename entities, enable/disable entities, assign to areas
9. **Create automations** - Build new automations with triggers, conditions, and actions
10. **List & trigger automations** - See and run existing automations
11. **Delete automations/scripts/dashboards** - Remove unwanted configurations
12. **Notifications** - Send persistent notifications or push to mobile devices
13. **Discover services & events** - See all available HA services and event types
14. **Create & modify dashboards** - Create NEW dashboards or modify EXISTING ones with any card type
15. **Check custom cards** - Verify which HACS custom cards are installed (card-mod, bubble-card, mushroom, etc.)
16. **Shopping list** - View, add, and complete shopping list items
17. **Backup** - Create full Home Assistant backups
18. **Browse media** - Browse media content from players (music, photos, etc.)
19. **Read/write config files** - Read and edit configuration.yaml, automations.yaml, YAML dashboards, packages, etc.
20. **Validate config** - Check HA configuration for errors after editing
21. **Snapshots** - Automatic backups before every file change, with restore capability

## Configuration File Management
- Use **list_config_files** to explore the HA config directory
- Use **read_config_file** to read any YAML/config file (including YAML-mode dashboards like ui-lovelace.yaml)
- Use **write_config_file** to modify files (auto-creates a snapshot before writing)
- Use **check_config** to validate after editing configuration.yaml
- Use **list_snapshots** and **restore_snapshot** to manage/restore backups

IMPORTANT for config editing:
1. ALWAYS read the file first with read_config_file
2. Make targeted changes (don't rewrite everything unless necessary)
3. After writing configuration.yaml, ALWAYS call check_config to validate
4. If validation fails, use restore_snapshot to undo changes
5. Snapshots are created automatically before every write - inform the user about this safety net

## Dashboard Management
- Use **get_dashboards** to list all dashboards
- Use **get_dashboard_config** to read an existing dashboard's full configuration
- Use **update_dashboard** to modify an existing dashboard (replaces all views)
- Use **create_dashboard** to create a brand new dashboard
- Use **get_frontend_resources** to check which custom cards (HACS) are installed
- Use **delete_dashboard** to remove a dashboard

IMPORTANT: When modifying a dashboard, ALWAYS:
1. First call get_dashboard_config to read the current config
2. Modify the views/cards as needed
3. Save with update_dashboard passing the complete views array

### ENTITY RULE (CRITICAL)
- NEVER invent or guess entity IDs. ALWAYS use search_entities first to find REAL entity IDs.
- Only use entity IDs that appear in the search results.
- If a search returns no results for a category, DO NOT include cards for that category.
- Example: if search_entities("light") returns only light.soggiorno and light.camera, use ONLY those two.

### Dashboard Layout (CRITICAL - never put cards in a flat vertical list!)
Always create visually appealing layouts using grids and stacks:

**Use grid cards to arrange items in columns:**
{"type": "grid", "columns": 2, "square": false, "cards": [card1, card2, card3, card4]}

**Use horizontal-stack for side-by-side cards:**
{"type": "horizontal-stack", "cards": [card1, card2]}

**Use vertical-stack to group related cards:**
{"type": "vertical-stack", "cards": [headerCard, contentCard]}

**Best layout practices:**
- Use a grid with 2-3 columns for button/entity cards
- Group related sensors in horizontal-stack
- Use vertical-stack with a markdown header + grid of cards for sections
- Example section structure:
  {"type": "vertical-stack", "cards": [
    {"type": "markdown", "content": "## 💡 Luci"},
    {"type": "grid", "columns": 3, "square": false, "cards": [
      {"type": "button", "entity": "light.soggiorno", "name": "Soggiorno", "icon": "mdi:sofa", "show_state": true},
      {"type": "button", "entity": "light.camera", "name": "Camera", "icon": "mdi:bed", "show_state": true}
    ]}
  ]}

### Standard Lovelace card types:
- entities: {"type": "entities", "title": "Lights", "entities": ["light.living_room"]}
- gauge: {"type": "gauge", "entity": "sensor.temperature"}
- history-graph: {"type": "history-graph", "entities": [{"entity": "sensor.temp"}], "hours_to_show": 24}
- thermostat: {"type": "thermostat", "entity": "climate.living_room"}
- button: {"type": "button", "entity": "switch.outlet", "name": "Toggle"}
- markdown: {"type": "markdown", "content": "# Title"}

### Custom cards (check availability with get_frontend_resources first!):

**card-mod** - Style any card with CSS:
{"type": "entities", "entities": ["light.room"], "card_mod": {"style": "ha-card { background: rgba(0,0,0,0.3); border-radius: 16px; }"}}

**bubble-card** - Modern UI cards:
{"type": "custom:bubble-card", "card_type": "button", "entity": "light.room", "name": "Light", "icon": "mdi:lightbulb", "button_type": "switch"}
{"type": "custom:bubble-card", "card_type": "pop-up", "hash": "#room", "name": "Living Room", "icon": "mdi:sofa"}
{"type": "custom:bubble-card", "card_type": "separator", "name": "Section", "icon": "mdi:home"}

**mushroom cards**:
{"type": "custom:mushroom-entity-card", "entity": "light.room", "fill_container": true}
{"type": "custom:mushroom-climate-card", "entity": "climate.room"}

**button-card** - Highly customizable buttons:
{"type": "custom:button-card", "entity": "light.room", "name": "Light", "icon": "mdi:lightbulb", "show_state": true,
 "styles": {"card": [{"background-color": "rgba(0,0,0,0.3)"}]}}

**mini-graph-card** - Beautiful sensor graphs:
{"type": "custom:mini-graph-card", "entities": ["sensor.temperature"], "hours_to_show": 24, "line_color": "#e74c3c"}

Before using any custom: card type, ALWAYS call get_frontend_resources to verify it's installed.
If the user wants a custom card that is not installed, inform them and suggest installing it via HACS.

## Automations
When creating automations, use proper Home Assistant formats:
- State trigger: {"platform": "state", "entity_id": "binary_sensor.motion", "to": "on"}
- Time trigger: {"platform": "time", "at": "07:00:00"}
- Sun trigger: {"platform": "sun", "event": "sunset", "offset": "-00:30:00"}
- Service action: {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 255}}

**CRITICAL - Entity Selection:**
BEFORE creating an automation, script, or dashboard:
1. ALWAYS use search_entities to find the correct entity_id (search for "light", "switch", "sensor", etc.)
2. If the user says "luce" (light) or mentions a device, search BOTH "light" AND "switch" domains
3. Present found entities to the user and ASK which one to use if there are multiple matches
4. NEVER guess or invent entity IDs - only use entities that actually exist

**CRITICAL - Show YAML After Creation:**
After CREATING or MODIFYING an automation, script, or dashboard, you MUST immediately show the YAML code to the user in your response. This is MANDATORY - never skip this step.

When managing areas/rooms, use manage_areas. To assign an entity to a room, use manage_entity with the area_id.
For advanced sensor analytics (averages, peaks, trends), use get_statistics instead of get_history.
When a user asks about specific devices or addons, use search_entities to find them by keyword.
Use get_history for recent state changes, get_statistics for aggregated data over longer periods.
Use get_areas when the user refers to rooms.

**CRITICAL - Delete/Modify Confirmation (ALWAYS REQUIRED):**
BEFORE deleting or modifying ANY automation, script, or dashboard:
1. **List all options**: Use get_automations, get_scripts, or get_dashboards to see all available items
2. **Identify with certainty**: Match by exact alias/name - if the user says "rimuovi questa" (remove this one), look at the conversation context to identify which one was just created/discussed
3. **Show what you'll delete/modify**: Display the name/alias of the item you identified
4. **ASK for confirmation**: "Vuoi eliminare l'automazione 'Nome Automazione'? Confermi?" (Do you want to delete automation 'Name'? Confirm?)
5. **Wait for user response**: NEVER proceed without explicit "sì"/"yes"/"conferma"/"ok" from the user
6. **NEVER delete the wrong item**: If there's ANY doubt, ask the user to clarify which item they mean

This is a DESTRUCTIVE operation - mistakes can delete important automations. ALWAYS confirm first.
To delete resources (after confirmation), use delete_automation, delete_script, or delete_dashboard.

## CRITICAL BEHAVIOR RULES
- When the user asks you to CREATE or MODIFY something (dashboard, automation, script, config), DO IT IMMEDIATELY.
- NEVER just describe what you plan to do. Execute ALL necessary tool calls in sequence and complete the task fully.
- Only respond with the final result AFTER the task is complete.
- If a task requires multiple tool calls, keep calling tools until the task is done. Do not stop halfway to explain your plan.

## SHOW YOUR CHANGES (CRITICAL)
When you modify an automation, script, configuration, or any YAML file, ALWAYS show the user exactly what you changed.
In your final response, include:
1. A brief summary of what you did
2. The relevant YAML section BEFORE (old) and AFTER (new) using code blocks, for example:

**Prima (old):**
```yaml
condition: []
```

**Dopo (new):**
```yaml
condition:
  - condition: not
    conditions:
      - condition: template
        value_template: "{{ 'Inter' in trigger.to_state.state }}"
```

This helps the user understand and verify the changes. Keep the diff focused on what changed, not the entire file.

## EFFICIENCY RULES (ABSOLUTELY CRITICAL - MAXIMUM 1-2 tool calls per task)
- EVERY extra tool call wastes 5-20 seconds. Users WILL experience errors and timeouts with too many calls.
- When context is pre-loaded in the user message, ALL that data is already available. NEVER re-fetch it.
- PRE-LOADED DATA = do NOT call: get_automations, get_scripts, get_dashboards, read_config_file, list_config_files, search_entities, get_entity_state for data already present.
- For modifying automations: call update_automation ONCE with automation_id + changes. That's IT. ONE call total.
- For modifying scripts: call update_script ONCE with script_id + changes. That's IT. ONE call total.
- After update_automation or update_script succeeds: STOP. Show the diff to the user. Do NOT call any verification tools.
- NEVER verify changes by calling get_automations or read_config_file after an update - the tool already returns old/new YAML.
- The MAXIMUM number of tool calls for ANY modification task is 2. If you've made 2 calls, you MUST respond.
- For other config editing: read_config_file → write_config_file → check_config (3 calls max).

Always respond in the same language the user uses.
Be concise but informative."""

# Compact prompt for providers with small context (GitHub Models free tier: 8k tokens)
def get_compact_prompt():
    """Generate compact prompt with language-specific instructions."""
    lang_instruction = get_lang_text("respond_instruction")
    show_yaml_rule = get_lang_text("show_yaml_rule")
    confirm_entity_rule = get_lang_text("confirm_entity_rule")
    confirm_delete_rule = get_lang_text("confirm_delete_rule")
    example_vs_create_rule = get_lang_text("example_vs_create_rule")

    return f"""You are a Home Assistant AI assistant. Control devices, query states, search entities, check history, create automations, create dashboards.
{example_vs_create_rule}
{confirm_entity_rule}
{show_yaml_rule}
{confirm_delete_rule}
When users ask about specific devices, use search_entities. Use get_history for past data.
To create a dashboard, ALWAYS first search entities to find real entity IDs, then use create_dashboard with proper Lovelace cards.
{lang_instruction} Be concise."""

def get_compact_prompt_with_files():
    """Generate compact prompt with files support and language-specific instructions."""
    before_text = get_lang_text("before")
    after_text = get_lang_text("after")
    lang_instruction = get_lang_text("respond_instruction")
    show_yaml_rule = get_lang_text("show_yaml_rule")
    confirm_entity_rule = get_lang_text("confirm_entity_rule")
    confirm_delete_rule = get_lang_text("confirm_delete_rule")
    example_vs_create_rule = get_lang_text("example_vs_create_rule")

    return f"""You are a Home Assistant AI assistant. Control devices, query states, create automations/dashboards, and READ CONFIG FILES.
Use list_config_files to explore folders (e.g., 'lovelace', 'yaml'). Use read_config_file to read YAML/JSON files.
Use get_automations, get_scripts, get_dashboards to list existing configs.
When users ask about files/folders, use list_config_files first to show what's available.

{example_vs_create_rule}
{show_yaml_rule}
{confirm_entity_rule}
{confirm_delete_rule}

CRITICAL - Show changes clearly:
When you MODIFY configs, show ONLY the changed sections in diff format:
**{before_text}:**
```yaml
- condition: []
```
**{after_text}:**
```yaml
+ condition:
+   - condition: state
+     entity_id: light.room
+     state: "on"
```

For NEW creations, show the complete YAML.

{lang_instruction} Be concise."""

# Compact tool definitions for low-token providers
HA_TOOLS_COMPACT = [
    {
        "name": "get_entities",
        "description": "Get HA entity states, optionally filtered by domain.",
        "parameters": {"type": "object", "properties": {"domain": {"type": "string"}}, "required": []}
    },
    {
        "name": "call_service",
        "description": "Call HA service (e.g. light.turn_on, switch.toggle, climate.set_temperature, scene.turn_on, script.turn_on).",
        "parameters": {"type": "object", "properties": {
            "domain": {"type": "string"}, "service": {"type": "string"},
            "data": {"type": "object"}
        }, "required": ["domain", "service", "data"]}
    },
    {
        "name": "search_entities",
        "description": "Search entities by keyword in entity_id or friendly_name.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    },
    {
        "name": "get_history",
        "description": "Get state history of an entity. Params: entity_id (required), hours (default 24).",
        "parameters": {"type": "object", "properties": {
            "entity_id": {"type": "string"}, "hours": {"type": "number"}
        }, "required": ["entity_id"]}
    },
    {
        "name": "create_automation",
        "description": "Create HA automation with alias, trigger, action.",
        "parameters": {"type": "object", "properties": {
            "alias": {"type": "string"}, "trigger": {"type": "array", "items": {"type": "object"}},
            "action": {"type": "array", "items": {"type": "object"}}
        }, "required": ["alias", "trigger", "action"]}
    },
    {
        "name": "create_dashboard",
        "description": "Create a NEW Lovelace dashboard. Params: title, url_path (slug), views (array of {title, cards[]}). Card types: entities, gauge, history-graph, thermostat, button.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "url_path": {"type": "string"},
            "icon": {"type": "string"},
            "views": {"type": "array", "items": {"type": "object"}}
        }, "required": ["title", "url_path", "views"]}
    }
]

# Extended tool set for GitHub with file access enabled
# Balance between COMPACT (6 tools) and FULL (40 tools) to stay under 8k token limit
HA_TOOLS_EXTENDED = HA_TOOLS_COMPACT + [
    {
        "name": "list_config_files",
        "description": "List files and directories in Home Assistant config folder. Use empty path for root, or 'lovelace', 'yaml', etc.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}
    },
    {
        "name": "read_config_file",
        "description": "Read content of a config file (YAML, JSON, etc). Returns file content as text.",
        "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}
    },
    {
        "name": "get_automations",
        "description": "Get list of all automations with id, alias, state, and full config.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_scripts",
        "description": "Get list of all scripts with id, name, and full config.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_dashboards",
        "description": "Get list of all Lovelace dashboards.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_areas",
        "description": "Get list of areas/rooms in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
]


def get_system_prompt() -> str:
    """Get system prompt appropriate for current provider."""
    # If custom system prompt is set, use it directly
    if CUSTOM_SYSTEM_PROMPT is not None:
        return CUSTOM_SYSTEM_PROMPT
    
    base_prompt = """You are an AI assistant integrated into Home Assistant. You help users manage their smart home.

You can:
1. **Query entities** - See device states (lights, sensors, switches, climate, covers, etc.)
2. **Control devices** - Turn on/off lights, switches, set temperatures, etc.
3. **Search entities** - Find specific devices or integrations by keyword
4. **Entity history** - Check past values and trends ("what was the temperature yesterday?")
5. **Advanced statistics** - Get min/max/mean/sum statistics for sensors over time periods
6. **Scenes & scripts** - List, activate scenes, run scripts, create new scripts
7. **Areas/rooms** - List, create, rename, delete areas. Assign entities to areas
8. **Devices & entity registry** - List devices, rename entities, enable/disable entities, assign to areas
9. **Create automations** - Build new automations with triggers, conditions, and actions
10. **List & trigger automations** - See and run existing automations
11. **Delete automations/scripts/dashboards** - Remove unwanted configurations
12. **Notifications** - Send persistent notifications or push to mobile devices
13. **Discover services & events** - See all available HA services and event types
14. **Create & modify dashboards** - Create NEW dashboards or modify EXISTING ones with any card type
15. **Check custom cards** - Verify which HACS custom cards are installed (card-mod, bubble-card, mushroom, etc.)
16. **Shopping list** - View, add, and complete shopping list items
17. **Backup** - Create full Home Assistant backups
18. **Browse media** - Browse media content from players (music, photos, etc.)
19. **Read/write config files** - Read and edit configuration.yaml, automations.yaml, YAML dashboards, packages, etc.
20. **Validate config** - Check HA configuration for errors after editing
21. **Snapshots** - Automatic backups before every file change, with restore capability

## Configuration File Management
- Use **list_config_files** to explore the HA config directory
- Use **read_config_file** to read any YAML/config file (including YAML-mode dashboards like ui-lovelace.yaml)
- Use **write_config_file** to modify files (auto-creates a snapshot before writing)
- Use **check_config** to validate after editing configuration.yaml
- Use **list_snapshots** and **restore_snapshot** to manage/restore backups

IMPORTANT for config editing:
1. ALWAYS read the file first with read_config_file
2. Make targeted changes (don't rewrite everything unless necessary)
3. After writing configuration.yaml, ALWAYS call check_config to validate
4. If validation fails, use restore_snapshot to undo changes
5. Snapshots are created automatically before every write - inform the user about this safety net

## Dashboard Management
- Use **get_dashboards** to list all dashboards
- Use **get_dashboard_config** to read an existing dashboard's full configuration
- Use **update_dashboard** to modify an existing dashboard (replaces all views)
- Use **create_dashboard** to create a brand new dashboard
- Use **get_frontend_resources** to check which custom cards (HACS) are installed
- Use **delete_dashboard** to remove a dashboard

IMPORTANT: When modifying a dashboard, ALWAYS:
1. First call get_dashboard_config to read the current config
2. Modify the views/cards as needed
3. Save with update_dashboard passing the complete views array

### ENTITY RULE (CRITICAL)
- NEVER invent or guess entity IDs. ALWAYS use search_entities first to find REAL entity IDs.
- Only use entity IDs that appear in the search results.
- If a search returns no results for a category, DO NOT include cards for that category.
- Example: if search_entities("light") returns only light.soggiorno and light.camera, use ONLY those two.

### Dashboard Layout (CRITICAL - never put cards in a flat vertical list!)
Always create visually appealing layouts using grids and stacks:

**Use grid cards to arrange items in columns:**
{"type": "grid", "columns": 2, "square": false, "cards": [card1, card2, card3, card4]}

**Use horizontal-stack for side-by-side cards:**
{"type": "horizontal-stack", "cards": [card1, card2]}

**Use vertical-stack to group related cards:**
{"type": "vertical-stack", "cards": [headerCard, contentCard]}


    """

    if AI_PROVIDER == "github":
        # GitHub has 8k token limit - use minimal prompt with only includes mapping
        compact_prompt = get_compact_prompt_with_files() if ENABLE_FILE_ACCESS else get_compact_prompt()
        # Only include file mapping if file access is enabled, skip verbose config structure
        if ENABLE_FILE_ACCESS and CONFIG_INCLUDES:
            includes_compact = "Config files: " + ", ".join([f"{k}={v}" for k, v in list(CONFIG_INCLUDES.items())[:5]]) + "\n"
            return includes_compact + compact_prompt
        return compact_prompt
    # For other providers, add language instruction and critical rules to base prompt
    lang_instruction = get_lang_text("respond_instruction")
    show_yaml_rule = get_lang_text("show_yaml_rule")
    confirm_entity_rule = get_lang_text("confirm_entity_rule")
    confirm_delete_rule = get_lang_text("confirm_delete_rule")
    example_vs_create_rule = get_lang_text("example_vs_create_rule")
    return get_config_structure_section() + get_config_includes_text() + base_prompt + f"\n\n{example_vs_create_rule}\n{show_yaml_rule}\n{confirm_entity_rule}\n{confirm_delete_rule}\n\n{lang_instruction}"


def get_openai_tools_for_provider():
    """Get OpenAI-format tools appropriate for current provider."""
    if AI_PROVIDER == "github":
        # GitHub Models has 8k token limit - use extended set if file access enabled, otherwise compact
        tool_set = HA_TOOLS_EXTENDED if ENABLE_FILE_ACCESS else HA_TOOLS_COMPACT
        return [
            {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
            for t in tool_set
        ]
    return get_openai_tools()


# ---- LOCAL INTENT DETECTION ----
# Analyze user message LOCALLY to determine intent and select only relevant tools/prompt.
# This dramatically reduces tokens sent to the AI API.

# Tool sets by intent category
INTENT_TOOL_SETS = {
    "modify_automation": ["update_automation"],
    "modify_script": ["update_script"],
    "create_automation": ["create_automation", "search_entities"],
    "create_script": ["create_script", "search_entities"],
    "create_dashboard": ["create_dashboard", "search_entities", "get_frontend_resources"],
    "modify_dashboard": ["get_dashboard_config", "update_dashboard", "get_frontend_resources"],
    "control_device": ["call_service", "search_entities", "get_entity_state"],
    "query_state": ["get_entities", "get_entity_state", "search_entities"],
    "query_history": ["get_history", "get_statistics", "search_entities"],
    "delete": ["delete_automation", "delete_script", "delete_dashboard"],
    "config_edit": ["read_config_file", "write_config_file", "check_config", "list_config_files",
                     "list_snapshots", "restore_snapshot"],
    "areas": ["manage_areas", "manage_entity", "get_areas", "get_devices"],
    "notifications": ["send_notification", "search_entities"],
}

# Compact focused prompts by intent
INTENT_PROMPTS = {
    "modify_automation": """You are a Home Assistant automation editor. The user wants to modify an automation.
The automation config is provided in the DATI section of the user's message.
CRITICAL RULE - ALWAYS ASK FOR CONFIRMATION BEFORE MODIFYING:
1. FIRST, briefly confirm which automation you found: "Ho trovato l'automazione: [NAME] (id: [ID])"
2. Describe WHAT EXACTLY will change in simple language
3. ASK FOR EXPLICIT CONFIRMATION: "Confermi che devo fare questa modifica? Scrivi sì o no"
4. WAIT FOR USER TO CONFIRM - DO NOT call update_automation until user says "sì" or "sa" (Italian yes)
5. Only AFTER confirmation, call update_automation ONCE with the changes
6. Show a before/after diff of what changed.
- Respond in the user's language. Be concise.
- NEVER call get_automations or read_config_file — the data is already provided.
- If the automation in DATI doesn't match what the user asked for, tell them and ask for clarification. Do NOT modify the wrong automation.""",

    "modify_script": """You are a Home Assistant script editor. The user wants to modify a script.
The script config is provided in the DATI section.
CRITICAL RULE - ALWAYS ASK FOR CONFIRMATION BEFORE MODIFYING:
1. FIRST, briefly confirm which script you found: "Ho trovato lo script: [NAME] (id: [ID])"
2. Describe WHAT EXACTLY will change in simple language
3. ASK FOR EXPLICIT CONFIRMATION: "Confermi che devo fare questa modifica? Scrivi sì o no"
4. WAIT FOR USER TO CONFIRM - DO NOT call update_script until user says "sì" or "si"
5. Only AFTER confirmation, call update_script ONCE with the changes
6. Show a before/after diff of what changed.
- Respond in the user's language. Be concise.
- NEVER call get_scripts or read_config_file — the data is already provided.
- If the script doesn't match what the user asked for, tell them. Do NOT modify the wrong one.""",

    "control_device": """You are a Home Assistant device controller. Help the user control their devices.
Use search_entities to find entities if needed, then call_service to control them.
Respond in the user's language. Be concise. Maximum 2 tool calls.""",

    "query_state": """You are a Home Assistant status assistant. Help the user check device states.
Use search_entities or get_entity_state to find and report states.
Respond in the user's language. Be concise.""",

    "delete": """You are a Home Assistant deletion assistant. User wants to delete an automation, script, or dashboard.
CRITICAL DESTRUCTION RULE - ALWAYS ASK FOR EXPLICIT CONFIRMATION:
1. FIRST, identify what will be deleted: "Vuoi eliminare: [NAME] (id: [ID]). Questa azione è IRREVERSIBILE."
2. ASK FOR EXPLICIT CONFIRMATION: "Digita 'elimina' per confermare l'eliminazione di [NAME], altrimenti digita 'no'"
3. WAIT FOR CONFIRMATION - DO NOT call delete_automation/delete_script/delete_dashboard until user types "elimina"
4. Only AFTER explicit confirmation, call the appropriate delete tool
- Respond in the user's language. Be concise.
- NEVER auto-confirm deletions. Deletions are IRREVERSIBLE.""",
}


def detect_intent(user_message: str, smart_context: str) -> dict:
    """Detect user intent locally from the message and available context.
    Uses multilingual keywords from keywords.json based on LANGUAGE setting.
    Returns: {"intent": str, "tools": list[str], "prompt": str|None, "specific_target": bool}
    If intent is clear + specific target found, use focused mode (fewer tools, shorter prompt).
    Otherwise fall back to full mode."""
    msg = user_message.lower()
    
    # Get keywords for current language, fallback to English if not available
    lang_keywords = KEYWORDS.get(LANGUAGE, KEYWORDS.get("en", {}))
    
    # Extract keywords for different categories
    create_kw = lang_keywords.get("create", [])
    modify_kw = lang_keywords.get("modify", [])
    auto_kw = lang_keywords.get("automation", [])
    script_kw = lang_keywords.get("script", [])
    dash_kw = lang_keywords.get("dashboard", [])
    control_kw = lang_keywords.get("control", [])
    query_kw = lang_keywords.get("query", [])
    history_kw = lang_keywords.get("history", [])
    delete_kw = lang_keywords.get("delete", [])
    config_kw = lang_keywords.get("config", [])
    
    # --- MODIFY AUTOMATION (most common case) ---
    has_modify = any(k in msg for k in modify_kw)
    has_auto = any(k in msg for k in auto_kw)
    # Also detect if smart context found a specific automation
    has_specific_auto = "## AUTOMAZIONE" in smart_context if smart_context else False
    
    if has_modify and (has_auto or has_specific_auto):
        return {"intent": "modify_automation", "tools": INTENT_TOOL_SETS["modify_automation"],
                "prompt": INTENT_PROMPTS["modify_automation"] + "\n\nIMPORTANT: Before calling update_automation, show the user which automation you will modify and ask for explicit confirmation. Provide modification details and ask: 'Confermi che devo modificare questa automazione? (sì/no)'", "specific_target": has_specific_auto}
    
    # --- MODIFY SCRIPT ---
    has_script = any(k in msg for k in script_kw)
    has_specific_script = "## SCRIPT" in smart_context if smart_context else False
    
    if has_modify and (has_script or has_specific_script):
        return {"intent": "modify_script", "tools": INTENT_TOOL_SETS["modify_script"],
                "prompt": INTENT_PROMPTS["modify_script"], "specific_target": has_specific_script}
    
    # --- CREATE AUTOMATION ---
    has_create = any(k in msg for k in create_kw)
    if has_create and has_auto:
        return {"intent": "create_automation", "tools": INTENT_TOOL_SETS["create_automation"],
                "prompt": None, "specific_target": False}
    
    # --- CREATE SCRIPT ---
    if has_create and has_script:
        return {"intent": "create_script", "tools": INTENT_TOOL_SETS["create_script"],
                "prompt": None, "specific_target": False}
    
    # --- DASHBOARD ---
    has_dash = any(k in msg for k in dash_kw)
    if has_dash and has_create:
        return {"intent": "create_dashboard", "tools": INTENT_TOOL_SETS["create_dashboard"],
                "prompt": None, "specific_target": False}
    if has_dash and has_modify:
        return {"intent": "modify_dashboard", "tools": INTENT_TOOL_SETS["modify_dashboard"],
                "prompt": None, "specific_target": False}
    
    # --- DEVICE CONTROL ---
    if any(k in msg for k in control_kw):
        return {"intent": "control_device", "tools": INTENT_TOOL_SETS["control_device"],
                "prompt": INTENT_PROMPTS["control_device"], "specific_target": False}
    
    # --- QUERY STATE ---
    if any(k in msg for k in query_kw):
        return {"intent": "query_state", "tools": INTENT_TOOL_SETS["query_state"],
                "prompt": INTENT_PROMPTS["query_state"], "specific_target": False}
    
    # --- HISTORY ---
    if any(k in msg for k in history_kw):
        return {"intent": "query_history", "tools": INTENT_TOOL_SETS["query_history"],
                "prompt": None, "specific_target": False}
    
    # --- DELETE ---
    if any(k in msg for k in delete_kw) and (has_auto or has_script or has_dash):
        return {"intent": "delete", "tools": INTENT_TOOL_SETS["delete"],
                "prompt": None, "specific_target": False}
    
    # --- CONFIG EDIT ---
    if any(k in msg for k in config_kw):
        return {"intent": "config_edit", "tools": INTENT_TOOL_SETS["config_edit"],
                "prompt": None, "specific_target": False}
    
    # --- GENERIC (full mode) ---
    return {"intent": "generic", "tools": None, "prompt": None, "specific_target": False}


def get_tools_for_intent(intent_info: dict, provider: str = "anthropic") -> list:
    """Get tool definitions filtered by intent. Returns full tools if intent is generic."""
    tool_names = intent_info.get("tools")
    if tool_names is None:
        # Generic: return all tools
        if provider == "anthropic":
            return get_anthropic_tools()
        elif provider in ("openai", "github"):
            return get_openai_tools_for_provider()
        return get_anthropic_tools()
    
    # Filter to only relevant tools
    filtered = [t for t in HA_TOOLS_DESCRIPTION if t["name"] in tool_names]
    
    if provider == "anthropic":
        return [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in filtered]
    elif provider in ("openai", "github"):
        return [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in filtered]
    return [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in filtered]


def get_prompt_for_intent(intent_info: dict) -> str:
    """Get system prompt for intent. Returns focused prompt if available, else full."""
    prompt = intent_info.get("prompt")
    if prompt:
        return prompt
    return get_system_prompt()


def trim_messages(messages: List[Dict], max_messages: int = 20) -> List[Dict]:
    """Trim conversation history, preserving tool_call/tool response pairs."""
    limit = 6 if AI_PROVIDER == "github" else max_messages
    if len(messages) <= limit:
        return messages
    trimmed = messages[-limit:]
    # Remove orphaned tool messages at the start (their parent assistant+tool_calls was trimmed)
    while trimmed and trimmed[0].get("role") == "tool":
        trimmed = trimmed[1:]
    # Also remove an assistant message with tool_calls if its tool responses were trimmed
    if trimmed and trimmed[0].get("role") == "assistant" and trimmed[0].get("tool_calls"):
        # Check if next message is a matching tool response
        if len(trimmed) < 2 or trimmed[1].get("role") != "tool":
            trimmed = trimmed[1:]
    return trimmed


# ---- Provider-specific chat implementations ----


def chat_anthropic(messages: List[Dict]) -> tuple:
    """Chat with Anthropic Claude. Returns (response_text, updated_messages)."""
    import anthropic

    response = ai_client.messages.create(
        model=get_active_model(),
        max_tokens=8192,
        system=get_system_prompt(),
        tools=get_anthropic_tools(),
        messages=messages
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        assistant_content = response.content
        for block in response.content:
            if block.type == "tool_use":
                logger.info(f"Tool: {block.name}")
                result = execute_tool(block.name, block.input)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})

        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

        response = ai_client.messages.create(
            model=get_active_model(),
            max_tokens=8192,
            system=get_system_prompt(),
            tools=get_anthropic_tools(),
            messages=messages
        )

    final_text = "".join(block.text for block in response.content if hasattr(block, "text"))
    return final_text, messages


def chat_openai(messages: List[Dict]) -> tuple:
    """Chat with OpenAI/NVIDIA/GitHub. Returns (response_text, updated_messages)."""
    trimmed = trim_messages(messages)
    system_prompt = get_system_prompt()
    tools = get_openai_tools_for_provider()
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

    response = ai_client.chat.completions.create(**kwargs)

    msg = response.choices[0].message

    while msg.tool_calls:
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            logger.info(f"Tool: {tc.function.name}")
            args = json.loads(tc.function.arguments)
            result = execute_tool(tc.function.name, args)
            # Truncate tool results for GitHub/NVIDIA to stay within token limits
            if AI_PROVIDER in ["github", "nvidia"] and len(result) > 3000:
                result = result[:3000] + '... (truncated)'
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        trimmed = trim_messages(messages)
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
        tools=[get_gemini_tools()]
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
                result = execute_tool(fn.name, args)
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
    for m in messages:
        role = m.get("role", "")
        # Skip tool-role messages for Anthropic (it uses tool_result inside user messages)
        if AI_PROVIDER == "anthropic" and role == "tool":
            continue
        # Skip assistant messages with tool_calls format (OpenAI format) for Anthropic
        if AI_PROVIDER == "anthropic" and role == "assistant" and m.get("tool_calls"):
            continue
        # Skip Anthropic-format tool_result messages for OpenAI/GitHub
        if AI_PROVIDER in ("openai", "github") and role == "user" and isinstance(m.get("content"), list):
            if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in m.get("content", [])):
                continue
        # Keep user/assistant messages (text or with images)
        if role in ("user", "assistant"):
            content = m.get("content", "")
            # Accept strings or arrays (arrays can contain images)
            if isinstance(content, str) and content:
                clean.append({"role": role, "content": content})
            elif isinstance(content, list) and content:
                clean.append({"role": role, "content": content})
    
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


def stream_chat_nvidia_direct(messages, intent_info=None):
    """Stream chat for NVIDIA using direct requests (not OpenAI SDK).
    This allows using NVIDIA-specific parameters like chat_template_kwargs for thinking mode."""
    trimmed = trim_messages(messages)

    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools"):
        system_prompt = get_prompt_for_intent(intent_info)
        tools = get_tools_for_intent(intent_info, AI_PROVIDER)
        logger.info(f"NVIDIA focused mode: {intent_info['intent']} ({len(tools)} tools)")
    else:
        system_prompt = get_system_prompt()
        tools = get_openai_tools_for_provider()

    # Log available tools
    tool_names = [t.get("function", {}).get("name", "unknown") for t in tools]
    logger.info(f"NVIDIA tools available ({len(tools)}): {', '.join(tool_names)}")

    full_text = ""
    max_rounds = 5
    tools_called_this_session = set()

    for round_num in range(max_rounds):
        oai_messages = [{"role": "system", "content": system_prompt}] + trim_messages(messages)

        # Prepare NVIDIA API request
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        }

        payload = {
            "model": get_active_model(),
            "messages": oai_messages,
            "tools": tools,
            "max_tokens": 8192,
            "temperature": 0.7,
            "stream": True,
            "chat_template_kwargs": {"thinking": NVIDIA_THINKING_MODE}
        }

        logger.info(f"NVIDIA: Calling API with model={payload['model']}, thinking={NVIDIA_THINKING_MODE}, stream=True")

        try:
            # Increase timeout when thinking mode is enabled (reasoning takes longer)
            timeout_seconds = 300 if NVIDIA_THINKING_MODE else 120
            response = requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout_seconds)
            response.raise_for_status()
            logger.info("NVIDIA: Response stream started")

            # Parse SSE stream manually
            content_parts = []
            tool_calls_map = {}

            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.strip():
                    continue

                # SSE format: "data: {...}"
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix

                    if data.strip() == "[DONE]":
                        break

                    try:
                        chunk_data = json.loads(data)
                        if not chunk_data.get("choices"):
                            continue

                        delta = chunk_data["choices"][0].get("delta", {})

                        if delta.get("content"):
                            content_parts.append(delta["content"])

                        if delta.get("tool_calls"):
                            for tc_delta in delta["tool_calls"]:
                                idx = tc_delta.get("index", 0)
                                if idx not in tool_calls_map:
                                    tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                                if tc_delta.get("id"):
                                    tool_calls_map[idx]["id"] = tc_delta["id"]
                                if tc_delta.get("function"):
                                    if tc_delta["function"].get("name"):
                                        tool_calls_map[idx]["name"] = tc_delta["function"]["name"]
                                    if tc_delta["function"].get("arguments"):
                                        tool_calls_map[idx]["arguments"] += tc_delta["function"]["arguments"]

                    except json.JSONDecodeError:
                        continue

            accumulated = "".join(content_parts)

            if not tool_calls_map:
                # No tools - stream the final text
                full_text = accumulated
                logger.warning(f"NVIDIA: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'")
                messages.append({"role": "assistant", "content": full_text})
                yield {"type": "clear"}
                for i in range(0, len(full_text), 4):
                    chunk = full_text[i:i+4]
                    yield {"type": "token", "content": chunk}
                break

            # Build assistant message with tool calls
            logger.info(f"Round {round_num+1}: {len(tool_calls_map)} tool(s), skipping intermediate text")
            tc_list = []
            for idx in sorted(tool_calls_map.keys()):
                tc = tool_calls_map[idx]
                tc_list.append({
                    "id": tc["id"], "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]}
                })

            messages.append({"role": "assistant", "content": accumulated, "tool_calls": tc_list})

            # Execute tools (same logic as OpenAI)
            tool_call_results = {}
            for tc in tc_list:
                fn_name = tc["function"]["name"]
                if fn_name in tools_called_this_session:
                    logger.info(f"Skipping already-called tool: {fn_name}")
                    continue

                tools_called_this_session.add(fn_name)
                args_str = tc["function"]["arguments"]
                tc_id = tc["id"]

                yield {"type": "tool_call", "name": fn_name, "arguments": args_str}

                try:
                    args = json.loads(args_str) if args_str.strip() else {}
                except json.JSONDecodeError:
                    result = json.dumps({"error": f"Invalid JSON arguments: {args_str}"})
                    tool_call_results[tc_id] = (fn_name, result)
                    continue

                # Execute tool using the standard execute_tool function
                logger.info(f"NVIDIA: Executing tool '{fn_name}' with args: {args}")
                result = execute_tool(fn_name, args)
                logger.info(f"NVIDIA: Tool '{fn_name}' returned {len(result)} chars: {result[:300]}...")
                
                tool_call_results[tc_id] = (fn_name, result)
                yield {"type": "tool_result", "name": fn_name, "result": result}

            # Add tool results to messages
            for tc_id, (fn_name, result) in tool_call_results.items():
                messages.append({"role": "tool", "tool_call_id": tc_id, "name": fn_name, "content": result})

        except Exception as e:
            logger.error(f"NVIDIA API error: {e}")
            error_msg = f"NVIDIA API error: {str(e)}"
            messages.append({"role": "assistant", "content": error_msg})
            yield {"type": "clear"}
            yield {"type": "token", "content": error_msg}
            break


def stream_chat_openai(messages, intent_info=None):
    """Stream chat for OpenAI/GitHub with real token streaming. Yields SSE event dicts.
    Uses intent_info to select focused tools and prompt when available."""
    trimmed = trim_messages(messages)
    
    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools"):
        system_prompt = get_prompt_for_intent(intent_info)
        tools = get_tools_for_intent(intent_info, AI_PROVIDER)
        logger.info(f"OpenAI focused mode: {intent_info['intent']} ({len(tools)} tools)")
    else:
        system_prompt = get_system_prompt()
        tools = get_openai_tools_for_provider()

    # Log available tools for debugging
    tool_names = [t.get("function", {}).get("name", "unknown") for t in tools]
    logger.info(f"OpenAI tools available ({len(tools)}): {', '.join(tool_names)}")

    max_tok = 4000 if AI_PROVIDER == "github" else 4096
    full_text = ""
    max_rounds = 5
    tools_called_this_session = set()

    for round_num in range(max_rounds):
        oai_messages = [{"role": "system", "content": system_prompt}] + trim_messages(messages)

        # NVIDIA Kimi K2.5: configure thinking mode
        kwargs = {
            "model": get_active_model(),
            "messages": oai_messages,
            "tools": tools,
            **get_max_tokens_param(max_tok),
            "stream": True
        }
        if AI_PROVIDER == "nvidia":
            kwargs["temperature"] = 0.7
            # Override with NVIDIA-specific max_tokens (always uses max_tokens, not max_completion_tokens)
            kwargs.pop("max_completion_tokens", None)  # Remove if present
            kwargs["max_tokens"] = 8192
            # NVIDIA can be slower, use longer timeout
            kwargs["timeout"] = 120.0
            # Note: chat_template_kwargs not supported by OpenAI SDK
            # Thinking mode would require using requests library directly

        logger.info(f"OpenAI: Calling API with model={kwargs['model']}, stream=True")
        response = ai_client.chat.completions.create(**kwargs)
        logger.info("OpenAI: Response stream started")

        content_parts = []
        tool_calls_map = {}

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if delta.content:
                content_parts.append(delta.content)

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.id:
                        tool_calls_map[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_map[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc_delta.function.arguments

        accumulated = "".join(content_parts)

        if not tool_calls_map:
            # No tools - stream the final text now
            full_text = accumulated
            logger.warning(f"OpenAI: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'")
            logger.info(f"OpenAI: This means the AI decided not to use any of the {len(tools)} available tools")
            # Save assistant message to conversation
            messages.append({"role": "assistant", "content": full_text})
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                chunk = full_text[i:i+4]
                yield {"type": "token", "content": chunk}
            break

        # Build assistant message with tool calls
        logger.info(f"Round {round_num+1}: {len(tool_calls_map)} tool(s), skipping intermediate text")
        tc_list = []
        for idx in sorted(tool_calls_map.keys()):
            tc = tool_calls_map[idx]
            tc_list.append({
                "id": tc["id"], "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]}
            })

        messages.append({"role": "assistant", "content": accumulated, "tool_calls": tc_list})

        tool_call_results = {}  # Map tc_id -> (fn_name, result)
        for tc in tc_list:
            fn_name = tc["function"]["name"]
            # Block redundant read-only tool calls
            redundant_read_tools = {"get_automations", "get_scripts", "get_dashboards",
                                    "get_dashboard_config", "read_config_file",
                                    "list_config_files", "get_frontend_resources",
                                    "search_entities", "get_entity_state"}
            if fn_name in redundant_read_tools and fn_name in tools_called_this_session:
                logger.warning(f"Blocked redundant tool call: {fn_name}")
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                 "content": json.dumps({"note": f"Skipped: {fn_name} already called. Use existing data. Respond NOW."})})
                continue
            yield {"type": "tool", "name": fn_name, "description": get_tool_description(fn_name)}
            args = json.loads(tc["function"]["arguments"])
            logger.info(f"OpenAI: Executing tool '{fn_name}' with args: {args}")
            result = execute_tool(fn_name, args)
            logger.info(f"OpenAI: Tool '{fn_name}' returned {len(result)} chars: {result[:300]}...")
            tools_called_this_session.add(fn_name)
            # Truncate large results to prevent token overflow
            max_len = 3000 if AI_PROVIDER == "github" else 8000
            if len(result) > max_len:
                result = result[:max_len] + '\n... [TRUNCATED - ' + str(len(result)) + ' chars total]'
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            tool_call_results[tc["id"]] = (fn_name, result)

        # AUTO-STOP: If a write tool succeeded, format response directly
        WRITE_TOOLS = {"update_automation", "update_script", "update_dashboard_card",
                       "create_automation", "create_script", "create_dashboard", "update_dashboard"}
        auto_stop = False
        for tc_id, (fn_name, result) in tool_call_results.items():
            if fn_name in WRITE_TOOLS:
                try:
                    rdata = json.loads(result)
                    if rdata.get("status") == "success":
                        auto_stop = True
                        full_text = _format_write_tool_response(fn_name, rdata)
                        break
                except (json.JSONDecodeError, KeyError):
                    pass

        if auto_stop:
            logger.info(f"Auto-stop: write tool succeeded, skipping further API calls")
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                yield {"type": "token", "content": full_text[i:i+4]}
            break

    messages.append({"role": "assistant", "content": full_text})
    yield {"type": "done", "full_text": full_text}


def stream_chat_anthropic(messages, intent_info=None):
    """Stream chat for Anthropic with real token streaming and tool event emission.
    Uses intent_info to select focused tools and prompt when available."""
    import anthropic

    # Use focused tools/prompt if intent detected, else full
    if intent_info and intent_info.get("tools"):
        focused_prompt = get_prompt_for_intent(intent_info)
        focused_tools = get_tools_for_intent(intent_info, "anthropic")
        logger.info(f"Anthropic focused mode: {intent_info['intent']} ({len(focused_tools)} tools)")
    else:
        focused_prompt = get_system_prompt()
        focused_tools = get_anthropic_tools()

    # Log available tools for debugging
    tool_names = [t.get("name", "unknown") for t in focused_tools]
    logger.info(f"Anthropic tools available ({len(focused_tools)}): {', '.join(tool_names)}")

    full_text = ""
    max_rounds = 5  # Strict limit: most tasks need 1-2 rounds max
    tools_called_this_session = set()  # Track tools already called to detect redundancy

    for round_num in range(max_rounds):
        # Check abort flag
        if abort_streams.get("default"):
            logger.info("Stream aborted by user")
            yield {"type": "error", "message": "Interrotto dall'utente."}
            abort_streams["default"] = False
            break
        # Rate-limit prevention: delay between API calls (not on first round)
        if round_num > 0:
            delay = min(3 + round_num, 6)  # 4s, 5s, 6s, 6s...
            logger.info(f"Rate-limit prevention: waiting {delay}s before round {round_num+1}")
            yield {"type": "status", "message": f"Elaboro la risposta... (step {round_num+1})"}
            time.sleep(delay)
            if abort_streams.get("default"):
                logger.info("Stream aborted by user during delay")
                yield {"type": "error", "message": "Interrotto dall'utente."}
                abort_streams["default"] = False
                break

        content_parts = []
        tool_uses = []
        current_tool_id = None
        current_tool_name = None
        current_tool_input_json = ""

        try:
            with ai_client.messages.stream(
                model=get_active_model(),
                max_tokens=8192,
                system=focused_prompt,
                tools=focused_tools,
                messages=messages
            ) as stream:
                for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_id = event.content_block.id
                            current_tool_name = event.content_block.name
                            current_tool_input_json = ""
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            content_parts.append(event.delta.text)
                        elif event.delta.type == "input_json_delta":
                            current_tool_input_json += event.delta.partial_json
                    elif event.type == "content_block_stop":
                        if current_tool_name:
                            try:
                                tool_input = json.loads(current_tool_input_json) if current_tool_input_json else {}
                            except json.JSONDecodeError:
                                tool_input = {}
                            tool_uses.append({
                                "id": current_tool_id,
                                "name": current_tool_name,
                                "input": tool_input
                            })
                            current_tool_name = None
                            current_tool_id = None
                            current_tool_input_json = ""

                final_message = stream.get_final_message()
        except Exception as api_err:
            error_msg = str(api_err)
            if "429" in error_msg or "rate" in error_msg.lower():
                logger.warning(f"Rate limit hit at round {round_num+1}: {error_msg}")
                yield {"type": "status", "message": "Rate limit raggiunto, attendo..."}
                time.sleep(10)  # Wait and retry this round
                continue
            else:
                raise

        accumulated_text = "".join(content_parts)

        if not tool_uses:
            # No tools - this is the final response. Stream the text now.
            full_text = accumulated_text
            logger.warning(f"Anthropic: AI responded WITHOUT calling any tools. Response: '{full_text[:200]}...'")
            logger.info(f"Anthropic: This means the AI decided not to use any of the {len(focused_tools)} available tools")
            # Save assistant message to conversation
            messages.append({"role": "assistant", "content": full_text})
            # Yield a clear signal to reset any previous tool badges
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                chunk = full_text[i:i+4]
                yield {"type": "token", "content": chunk}
            break

        # Tools found - DON'T stream intermediate text, just show tool badges
        logger.info(f"Round {round_num+1}: {len(tool_uses)} tool(s), skipping intermediate text")
        assistant_content = final_message.content
        tool_calls = getattr(final_message, 'tool_calls', None)
        assistant_msg = {"role": "assistant", "content": assistant_content}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        tool_results = []
        redundant_blocked = 0
        for tool in tool_uses:
            tool_key = tool['name']
            # Block redundant calls: if a read-only tool was already called, skip it
            redundant_read_tools = {"get_automations", "get_scripts", "get_dashboards", 
                                    "get_dashboard_config", "read_config_file", 
                                    "list_config_files", "get_frontend_resources",
                                    "search_entities", "get_entity_state"}
            if tool_key in redundant_read_tools and tool_key in tools_called_this_session:
                logger.warning(f"Blocked redundant tool call: {tool_key} (already called this session)")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool["id"],
                    "content": json.dumps({"note": f"Skipped: {tool_key} already called. Use the data you already have. Respond to the user NOW."})
                })
                redundant_blocked += 1
                continue

            logger.info(f"Anthropic: Executing tool '{tool['name']}' with input: {tool['input']}")
            yield {"type": "tool", "name": tool["name"], "description": get_tool_description(tool["name"])}
            result = execute_tool(tool["name"], tool["input"])
            logger.info(f"Anthropic: Tool '{tool['name']}' returned {len(result)} chars: {result[:300]}...")
            tools_called_this_session.add(tool_key)
            # Truncate large tool results to prevent token overflow
            if len(result) > 8000:
                result = result[:8000] + '\n... [TRUNCATED to save tokens - ' + str(len(result)) + ' chars total]'
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool["id"],
                "content": result
            })

        # If ALL tools were blocked as redundant, force stop
        if redundant_blocked == len(tool_uses):
            logger.info("All tool calls were redundant - forcing final response")
            if AI_PROVIDER in ("openai", "github"):
                for tr in tool_results:
                    messages.append({"role": "tool", "tool_call_id": tr["tool_use_id"], "content": tr["content"]})
            else:
                messages.append({"role": "user", "content": tool_results})
            messages.append({"role": "user", "content": [{"type": "text", "text": "You already have all the data needed. Respond to the user now with the results. Do not call any more tools."}]})
            continue

        # AUTO-STOP: If a write tool succeeded, format response directly — no more API calls needed
        WRITE_TOOLS = {"update_automation", "update_script", "update_dashboard_card",
                       "create_automation", "create_script", "create_dashboard", "update_dashboard"}
        auto_stop = False
        for tool in tool_uses:
            if tool["name"] in WRITE_TOOLS:
                for tr in tool_results:
                    if tr.get("tool_use_id") == tool["id"]:
                        try:
                            rdata = json.loads(tr["content"])
                            if rdata.get("status") == "success":
                                auto_stop = True
                                full_text = _format_write_tool_response(tool["name"], rdata)
                        except (json.JSONDecodeError, KeyError):
                            pass
                        break
            if auto_stop:
                break

        if auto_stop:
            logger.info(f"Auto-stop: write tool succeeded, skipping further API calls")
            yield {"type": "clear"}
            for i in range(0, len(full_text), 4):
                yield {"type": "token", "content": full_text[i:i+4]}
            break

        if AI_PROVIDER in ("openai", "github"):
            for tr in tool_results:
                messages.append({"role": "tool", "tool_call_id": tr["tool_use_id"], "content": tr["content"]})
        else:
            messages.append({"role": "user", "content": tool_results})
        # Loop back for next round

    messages.append({"role": "assistant", "content": full_text})
    yield {"type": "done", "full_text": full_text}


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


def stream_chat_google(messages):
    """Stream chat for Google Gemini with tool events. Falls back to word-by-word for text."""
    from google.generativeai.types import content_types

    model = ai_client.GenerativeModel(
        model_name=get_active_model(),
        system_instruction=get_system_prompt(),
        tools=[get_gemini_tools()]
    )

    gemini_history = []
    for m in messages[:-1]:
        role = "model" if m["role"] == "assistant" else "user"
        if isinstance(m.get("content"), str):
            gemini_history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=gemini_history)
    last_message = messages[-1]["content"] if messages else ""
    response = chat.send_message(last_message)

    while response.candidates[0].content.parts:
        has_function_call = False
        function_responses = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                has_function_call = True
                fn = part.function_call
                logger.info(f"Tool: {fn.name}")
                yield {"type": "tool", "name": fn.name}
                args = dict(fn.args) if fn.args else {}
                result = execute_tool(fn.name, args)
                function_responses.append(
                    ai_client.protos.Part(function_response=ai_client.protos.FunctionResponse(
                        name=fn.name,
                        response={"result": json.loads(result)}
                    ))
                )

        if not has_function_call:
            break
        # Rate-limit prevention for Google
        time.sleep(1)
        response = chat.send_message(function_responses)

    final_text = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "text") and part.text:
            final_text += part.text

    # Stream text word by word
    messages.append({"role": "assistant", "content": final_text})
    words = final_text.split(' ')
    for i, word in enumerate(words):
        yield {"type": "token", "content": word + (' ' if i < len(words) - 1 else '')}
    yield {"type": "done", "full_text": final_text}


MAX_SMART_CONTEXT = 10000  # Max chars to inject — keeps tokens under control

def build_smart_context(user_message: str, intent: str = None) -> str:
    """Pre-load relevant context based on user's message intent.
    Works like VS Code: gathers all needed data BEFORE sending to AI,
    so Claude can respond with a single action instead of multiple tool rounds.
    IMPORTANT: Context must be compact to avoid rate limits.
    CRITICAL: If intent is 'create_automation' or 'create_script', skip fuzzy matching
    to avoid incorrectly injecting an existing automation/script to be modified."""
    msg_lower = user_message.lower()
    context_parts = []
    
    # Skip automation/script fuzzy matching if user is CREATING new (not modifying)
    skip_automation_matching = (intent in ("create_automation", "create_script"))

    try:
        # --- AUTOMATION CONTEXT ---
        auto_keywords = ["automazione", "automation", "automazion", "trigger", "condizione", "condition"]
        if any(k in msg_lower for k in auto_keywords) and not skip_automation_matching:
            import yaml
            # Get automation list
            states = get_all_states()
            autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
            auto_list = [{"entity_id": a.get("entity_id"),
                         "friendly_name": a.get("attributes", {}).get("friendly_name", ""),
                         "id": str(a.get("attributes", {}).get("id", "")),
                         "state": a.get("state")} for a in autos]

            # If user mentions a specific automation name, include its config
            # Try YAML first, then REST API for UI-created automations
            yaml_path = get_config_file_path("automation", "automations.yaml")
            found_in_yaml = False
            found_specific = False
            target_auto_id = None
            target_auto_alias = None
            
            # Find the BEST matching automation using scored matching
            # Score each automation by how many words match AND how specific the match is
            best_score = 0
            best_match = None
            
            # Words to IGNORE in matching (common Italian/English words that appear everywhere)
            STOP_WORDS = {"questa", "questo", "quella", "quello", "della", "delle", "dello",
                          "degli", "dalla", "dalle", "stessa", "stesso", "altra", "altro",
                          "prima", "dopo", "quando", "perché", "quindi", "anche", "ancora",
                          "molto", "troppo", "sempre", "dovremmo", "dovrebbe", "potrebbe",
                          "voglio", "vorrei", "puoi", "fammi", "invia", "manda", "notifica",
                          "about", "this", "that", "with", "from", "have", "which", "there",
                          "their", "would", "should", "could"}
            
            # Extract meaningful words from user message (>3 chars, not stop words)
            msg_words = [w for w in msg_lower.split() if len(w) > 3 and w not in STOP_WORDS]
            
            for a in auto_list:
                fname = str(a.get("friendly_name", "")).lower()
                if not fname:
                    continue
                
                score = 0
                
                # Check 1: Full name appears in message (highest priority)
                if fname in msg_lower:
                    score = 100
                
                # Check 2: Check if message contains quoted automation name
                # Look for text between quotes that matches
                import re
                quoted = re.findall(r'["\u201c\u201d]([^"\u201c\u201d]+)["\u201c\u201d]', user_message)
                for q in quoted:
                    if q.lower() in fname or fname in q.lower():
                        score = 90
                        break
                
                # Check 3: Score by matching meaningful words
                if score == 0:
                    fname_words = set(fname.lower().split())
                    matching_words = [w for w in msg_words if w in fname or any(w in fw for fw in fname_words)]
                    if matching_words:
                        # Weight by length of matched words (longer = more specific)
                        score = sum(len(w) for w in matching_words)
                        # Bonus if multiple words match
                        if len(matching_words) >= 2:
                            score += 10
                
                if score > best_score:
                    best_score = score
                    best_match = a
            
            if best_match and best_score >= 5:  # Minimum threshold
                target_auto_id = best_match.get("id", "")
                target_auto_alias = best_match.get("friendly_name", "")
                logger.info(f"Smart context: matched automation '{target_auto_alias}' (score: {best_score})")
            
            if target_auto_id:
                # Try YAML first
                if os.path.isfile(yaml_path):
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        all_automations = yaml.safe_load(f)
                    if isinstance(all_automations, list):
                        for auto in all_automations:
                            if str(auto.get("id", "")) == str(target_auto_id):
                                auto_yaml = yaml.dump(auto, default_flow_style=False, allow_unicode=True)
                                if len(auto_yaml) > 4000:
                                    auto_yaml = auto_yaml[:4000] + "\n... [TRUNCATED]"
                                context_parts.append(f"## AUTOMAZIONE: \"{auto.get('alias')}\" (id: {target_auto_id})\n```yaml\n{auto_yaml}```\nUsa update_automation con automation_id='{target_auto_id}'.")
                                found_in_yaml = True
                                found_specific = True
                                break
                
                # REST API fallback for UI-created automations
                if not found_in_yaml:
                    try:
                        rest_config = call_ha_api("GET", f"config/automation/config/{target_auto_id}")
                        if isinstance(rest_config, dict) and "error" not in rest_config:
                            auto_yaml = yaml.dump(rest_config, default_flow_style=False, allow_unicode=True)
                            if len(auto_yaml) > 4000:
                                auto_yaml = auto_yaml[:4000] + "\n... [TRUNCATED]"
                            context_parts.append(f"## AUTOMAZIONE (UI): \"{target_auto_alias}\" (id: {target_auto_id})\n```yaml\n{auto_yaml}```\nUsa update_automation con automation_id='{target_auto_id}'.")
                            found_specific = True
                    except Exception:
                        pass
            
            # Only include the full automations list if NO specific automation was found
            if not found_specific:
                # Compact list: only name + id, no entity_id/state (saves ~60% chars)
                compact_list = [{"name": a.get("friendly_name", ""), "id": a.get("id", "")} for a in auto_list if a.get("friendly_name")]
                list_json = json.dumps(compact_list, ensure_ascii=False, separators=(',', ':'))
                if len(list_json) > 3000:
                    list_json = list_json[:3000] + '...]'
                context_parts.append(f"## AUTOMAZIONI DISPONIBILI\n{list_json}")

        # --- SCRIPT CONTEXT ---
        script_keywords = ["script", "scena", "scenari", "routine", "sequenza"]
        if any(k in msg_lower for k in script_keywords):
            import yaml
            # Get script list from states
            states = get_all_states() if 'states' not in dir() else states
            script_entities = [{"entity_id": s.get("entity_id"),
                               "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                               "state": s.get("state")} for s in states if s.get("entity_id", "").startswith("script.")]
            if script_entities:
                context_parts.append(f"## SCRIPT DISPONIBILI\n{json.dumps(script_entities, ensure_ascii=False, indent=1)}")

            # If user mentions a specific script name, include its YAML
            yaml_path = get_config_file_path("script", "scripts.yaml")
            if os.path.isfile(yaml_path):
                try:
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        all_scripts = yaml.safe_load(f)
                    if isinstance(all_scripts, dict):
                        for sid, sconfig in all_scripts.items():
                            alias = str(sconfig.get("alias", "")).lower() if isinstance(sconfig, dict) else ""
                            if alias and (alias in msg_lower or sid in msg_lower or any(word in alias for word in msg_lower.split() if len(word) > 4)):
                                script_yaml = yaml.dump({sid: sconfig}, default_flow_style=False, allow_unicode=True)
                                if len(script_yaml) > 6000:
                                    script_yaml = script_yaml[:6000] + "\n... [TRUNCATED]"
                                context_parts.append(f"## YAML SCRIPT TROVATO: \"{sconfig.get('alias', sid)}\" (id: {sid})\n```yaml\n{script_yaml}```\nPer modificarlo usa update_script con script_id='{sid}' e i campi da cambiare.")
                                break
                except Exception:
                    pass

        # --- DASHBOARD CONTEXT ---
        dash_keywords = ["dashboard", "lovelace", "scheda", "card", "pannello"]
        if any(k in msg_lower for k in dash_keywords):
            # Get dashboard list
            try:
                dashboards = call_ha_websocket("lovelace/dashboards/list")
                dash_list = dashboards.get("result", [])
                if dash_list:
                    summary = [{"id": d.get("id"), "title": d.get("title", ""), "url_path": d.get("url_path", "")} for d in dash_list]
                    context_parts.append(f"## DASHBOARD DISPONIBILI\n{json.dumps(summary, ensure_ascii=False, indent=1)}")

                    # If user mentions a specific dashboard name, pre-load its config
                    for dash in dash_list:
                        dash_title = str(dash.get("title", "")).lower()
                        dash_url = str(dash.get("url_path", "")).lower()
                        if dash_title and (dash_title in msg_lower or dash_url in msg_lower or any(word in dash_title for word in msg_lower.split() if len(word) > 4)):
                            try:
                                dparams = {}
                                if dash_url and dash_url != "lovelace":
                                    dparams["url_path"] = dash.get("url_path")
                                dconfig = call_ha_websocket("lovelace/config", **dparams)
                                if dconfig.get("success"):
                                    cfg = dconfig.get("result", {})
                                    cfg_json = json.dumps(cfg, ensure_ascii=False, default=str)
                                    if len(cfg_json) > 8000:
                                        # Summarize views only
                                        views_summary = []
                                        for v in cfg.get("views", []):
                                            views_summary.append({"title": v.get("title", ""), "path": v.get("path", ""),
                                                                  "cards_count": len(v.get("cards", [])),
                                                                  "cards": [{"type": c.get("type", "")} for c in v.get("cards", [])[:15]]})
                                        context_parts.append(f"## CONFIG DASHBOARD '{dash.get('title')}' (url: {dash.get('url_path', 'lovelace')})\n{json.dumps({'views': views_summary}, ensure_ascii=False, indent=1)}\nConfig troppo grande, caricato sommario. Per i dettagli il tool get_dashboard_config è disponibile.")
                                    else:
                                        context_parts.append(f"## CONFIG COMPLETA DASHBOARD '{dash.get('title')}' (url: {dash.get('url_path', 'lovelace')})\n```json\n{cfg_json}\n```")
                            except Exception:
                                pass
                            break
            except Exception:
                pass

            # Get installed custom cards
            try:
                resources = call_ha_websocket("lovelace/resources")
                res_list = resources.get("result", [])
                if res_list:
                    cards = [r.get("url", "").split("/")[-1].split(".")[0] for r in res_list if r.get("url")]
                    context_parts.append(f"## CUSTOM CARDS INSTALLATE\n{', '.join(cards)}")
            except Exception:
                pass

        # --- ENTITY/DEVICE CONTEXT ---
        entity_keywords = ["luce", "luci", "light", "temperatura", "temperature", "sensore", "sensor",
                          "clima", "climate", "switch", "interruttore", "media_player", "cover", "tapparella"]
        matched_domains = []
        domain_map = {"luce": "light", "luci": "light", "light": "light", "lights": "light",
                     "temperatura": "sensor", "temperature": "sensor", "sensore": "sensor", "sensor": "sensor",
                     "clima": "climate", "climate": "climate", "switch": "switch", "interruttore": "switch",
                     "media_player": "media_player", "cover": "cover", "tapparella": "cover"}
        for kw, domain in domain_map.items():
            if kw in msg_lower and domain not in matched_domains:
                matched_domains.append(domain)

        if matched_domains:
            states = get_all_states()
            for domain in matched_domains[:3]:  # Max 3 domains
                domain_entities = [{"entity_id": s.get("entity_id"),
                                   "state": s.get("state"),
                                   "friendly_name": s.get("attributes", {}).get("friendly_name", "")}
                                  for s in states if s.get("entity_id", "").startswith(f"{domain}.")][:30]
                if domain_entities:
                    context_parts.append(f"## ENTITÀ {domain.upper()}\n{json.dumps(domain_entities, ensure_ascii=False, indent=1)}")

    except Exception as e:
        logger.warning(f"Smart context error: {e}")

    if context_parts:
        context = "\n\n".join(context_parts)
        # Cap total context size to avoid rate limits
        if len(context) > MAX_SMART_CONTEXT:
            context = context[:MAX_SMART_CONTEXT] + "\n... [CONTEXT TRUNCATED]"
        logger.info(f"Smart context: injected {len(context)} chars of pre-loaded data")
        return context
    return ""


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
    intent_info = detect_intent(user_message, "")  # Empty context for first pass
    intent_name = intent_info["intent"]
    
    # Step 2: Build smart context NOW that we know the intent
    # If user is creating new automation/script, skip fuzzy matching to avoid false automation injection
    smart_context = build_smart_context(user_message, intent=intent_name)
    
    # Step 3: Re-detect intent WITH full smart context for accuracy
    intent_info = detect_intent(user_message, smart_context)
    intent_name = intent_info["intent"]
    tool_count = len(intent_info.get("tools") or [])
    all_tools_count = len(HA_TOOLS_DESCRIPTION)
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
            yield from stream_chat_nvidia_direct(messages, intent_info=intent_info)
            # Sync ONLY new assistant messages (skip the enriched user message we created)
            for msg in messages[conv_length_before:]:
                if msg.get("role") == "assistant":
                    msg["model"] = get_active_model()
                    msg["provider"] = AI_PROVIDER
                    conversations[session_id].append(msg)
        elif AI_PROVIDER in ("openai", "github"):
            yield from stream_chat_openai(messages, intent_info=intent_info)
            # Sync ONLY new assistant messages (skip the enriched user message we created)
            for msg in messages[conv_length_before:]:
                if msg.get("role") == "assistant":
                    msg["model"] = get_active_model()
                    msg["provider"] = AI_PROVIDER
                    conversations[session_id].append(msg)
        elif AI_PROVIDER == "anthropic":
            clean_messages = sanitize_messages_for_provider(messages)
            yield from stream_chat_anthropic(clean_messages, intent_info=intent_info)
            # Sync ONLY new assistant messages (skip the enriched user message we created)
            for msg in clean_messages[conv_length_before:]:
                if msg.get("role") == "assistant":
                    msg["model"] = get_active_model()
                    msg["provider"] = AI_PROVIDER
                    conversations[session_id].append(msg)
        elif AI_PROVIDER == "google":
            clean_messages = sanitize_messages_for_provider(messages)
            yield from stream_chat_google(clean_messages)
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


# ---- Chat UI HTML ----


def get_chat_ui():
    """Generate the chat UI with image upload support."""
    provider_name = PROVIDER_DEFAULTS.get(AI_PROVIDER, {}).get("name", AI_PROVIDER)
    model_name = get_active_model()
    configured = bool(get_api_key())
    status_color = "#4caf50" if configured else "#ff9800"
    status_text = provider_name if configured else f"{provider_name} (no key)"

    # Multilingual UI messages with provider-specific analyzing messages
    provider_analyzing = {
        "anthropic": {
            "en": "🧠 Claude is thinking deeply...",
            "it": "🧠 Claude sta pensando...",
            "es": "🧠 Claude está pensando...",
            "fr": "🧠 Claude réfléchit..."
        },
        "openai": {
            "en": "⚡ GPT is processing your request...",
            "it": "⚡ GPT sta elaborando...",
            "es": "⚡ GPT está procesando...",
            "fr": "⚡ GPT traite votre demande..."
        },
        "google": {
            "en": "✨ Gemini is analyzing...",
            "it": "✨ Gemini sta analizzando...",
            "es": "✨ Gemini está analizando...",
            "fr": "✨ Gemini analyse..."
        },
        "github": {
            "en": "🚀 GitHub AI is working on it...",
            "it": "🚀 GitHub AI sta lavorando...",
            "es": "🚀 GitHub AI está trabajando...",
            "fr": "🚀 GitHub AI travaille..."
        },
        "nvidia": {
            "en": "🎯 NVIDIA AI is computing...",
            "it": "🎯 NVIDIA AI sta calcolando...",
            "es": "🎯 NVIDIA AI está computando...",
            "fr": "🎯 NVIDIA AI calcule..."
        }
    }
    
    # Get provider-specific analyzing message
    analyzing_msg = provider_analyzing.get(AI_PROVIDER, provider_analyzing["openai"]).get(LANGUAGE, provider_analyzing[AI_PROVIDER]["en"])
    
    ui_messages = {
        "en": {
            "welcome": "👋 Hi! I'm your AI assistant for Home Assistant.",
            "provider_model": f"Provider: <strong>{provider_name}</strong> | Model: <strong>{model_name}</strong>",
            "capabilities": "I can control devices, create automations, and manage your smart home.",
            "vision_feature": "<strong>🖼 New in v3.0:</strong> Now you can send me images!",
            "analyzing": analyzing_msg
        },
        "it": {
            "welcome": "👋 Ciao! Sono il tuo assistente AI per Home Assistant.",
            "provider_model": f"Provider: <strong>{provider_name}</strong> | Modello: <strong>{model_name}</strong>",
            "capabilities": "Posso controllare dispositivi, creare automazioni e gestire la tua casa smart.",
            "vision_feature": "<strong>🖼 Novità v3.0:</strong> Ora puoi inviarmi immagini!",
            "analyzing": analyzing_msg
        },
        "es": {
            "welcome": "👋 ¡Hola! Soy tu asistente AI para Home Assistant.",
            "provider_model": f"Proveedor: <strong>{provider_name}</strong> | Modelo: <strong>{model_name}</strong>",
            "capabilities": "Puedo controlar dispositivos, crear automatizaciones y gestionar tu hogar inteligente.",
            "vision_feature": "<strong>🖼 Nuevo en v3.0:</strong> ¡Ahora puedes enviarme imágenes!",
            "analyzing": analyzing_msg
        },
        "fr": {
            "welcome": "👋 Salut ! Je suis votre assistant IA pour Home Assistant.",
            "provider_model": f"Fournisseur: <strong>{provider_name}</strong> | Modèle: <strong>{model_name}</strong>",
            "capabilities": "Je peux contrôler des appareils, créer des automatisations et gérer votre maison intelligente.",
            "vision_feature": "<strong>🖼 Nouveau dans v3.0:</strong> Vous pouvez maintenant m'envoyer des images!",
            "analyzing": analyzing_msg
        }
    }

    # Get messages for current language
    msgs = ui_messages.get(LANGUAGE, ui_messages["en"])

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Assistant - Home Assistant</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }}
        .main-container {{ display: flex; flex: 1; overflow: hidden; }}
        .sidebar {{ width: 250px; min-width: 150px; max-width: 500px; background: white; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; overflow-y: auto; resize: horizontal; overflow-x: hidden; position: relative; }}
        .sidebar-header {{ padding: 12px; border-bottom: 1px solid #e0e0e0; font-weight: 600; font-size: 14px; color: #666; }}
        .chat-list {{ flex: 1; overflow-y: auto; }}
        .chat-item {{ padding: 12px; border-bottom: 1px solid #f0f0f0; cursor: pointer; transition: background 0.2s; display: flex; justify-content: space-between; align-items: center; }}
        .chat-item:hover {{ background: #f8f9fa; }}
        .chat-item.active {{ background: #e8f0fe; border-left: 3px solid #667eea; }}
        .chat-item-title {{ font-size: 13px; color: #333; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .chat-item-info {{ font-size: 11px; color: #999; }}
        .chat-item-delete {{ color: #ef4444; font-size: 16px; padding: 4px 8px; opacity: 0.6; transition: all 0.2s; cursor: pointer; flex-shrink: 0; background: none; border: none; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; }}
        .chat-item:hover .chat-item-delete {{ opacity: 1; }}
        .chat-item-delete:hover {{ color: #dc2626; background: rgba(239,68,68,0.1); }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
        .header h1 {{ font-size: 18px; font-weight: 600; }}
        .header .badge {{ font-size: 10px; opacity: 0.9; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px; }}
        .header .new-chat {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 12px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
        .header .new-chat:hover {{ background: rgba(255,255,255,0.35); }}
        .model-selector {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 10px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: background 0.2s; max-width: 240px; }}
        .model-selector:hover {{ background: rgba(255,255,255,0.35); }}
        .model-selector option {{ background: #2c3e50; color: white; }}
        .model-selector optgroup {{ background: #1a252f; color: #aaa; font-style: normal; font-weight: 600; padding: 4px 0; }}
        .header .status {{ margin-left: auto; font-size: 12px; display: flex; align-items: center; gap: 6px; }}
        .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: {status_color}; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        .chat-container {{ flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }}
        .message {{ max-width: 85%; padding: 12px 16px; border-radius: 16px; line-height: 1.5; font-size: 14px; word-wrap: break-word; animation: fadeIn 0.3s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .message.user {{ background: #667eea; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }}
        .message.user img {{ max-width: 200px; max-height: 200px; border-radius: 8px; margin-top: 8px; display: block; }}
        .message.assistant {{ background: white; color: #333; align-self: flex-start; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .code-block {{ position: relative; margin: 8px 0; }}
        .code-block .copy-button {{ position: absolute; top: 8px; right: 8px; background: #667eea; color: white; border: none; border-radius: 6px; padding: 4px 10px; font-size: 11px; cursor: pointer; opacity: 0.8; transition: all 0.2s; z-index: 1; }}
        .code-block .copy-button:hover {{ opacity: 1; background: #5a6fd6; }}
        .code-block .copy-button.copied {{ background: #10b981; }}
        .message.assistant pre {{ background: #f5f5f5; padding: 10px; border-radius: 8px; overflow-x: auto; margin: 0; font-size: 13px; }}
        .message.assistant code {{ background: #f0f0f0; padding: 1px 5px; border-radius: 4px; font-size: 13px; }}
        .message.assistant pre code {{ background: none; padding: 0; }}
        .message.assistant strong {{ color: #333; }}
        .message.assistant ul, .message.assistant ol {{ margin: 6px 0 6px 20px; }}
        .message.assistant p {{ margin: 4px 0; }}
        .message.system {{ background: #fff3cd; color: #856404; align-self: center; text-align: center; font-size: 13px; border-radius: 8px; max-width: 90%; }}
        .message.thinking {{ background: #f8f9fa; color: #999; align-self: flex-start; border-bottom-left-radius: 4px; font-style: italic; }}
        .message.thinking .dots span {{ animation: blink 1.4s infinite both; }}
        .message.thinking .dots span:nth-child(2) {{ animation-delay: 0.2s; }}
        .message.thinking .dots span:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
        .input-area {{ padding: 12px 16px; background: white; border-top: 1px solid #e0e0e0; display: flex; flex-direction: column; gap: 8px; }}
        .image-preview-container {{ display: none; padding: 8px; background: #f8f9fa; border-radius: 8px; position: relative; }}
        .image-preview-container.visible {{ display: block; }}
        .image-preview {{ max-width: 150px; max-height: 150px; border-radius: 8px; border: 2px solid #667eea; }}
        .remove-image-btn {{ position: absolute; top: 4px; right: 4px; background: #ef4444; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; }}
        .input-row {{ display: flex; gap: 8px; align-items: flex-end; }}
        .input-area textarea {{ flex: 1; border: 1px solid #ddd; border-radius: 20px; padding: 10px 16px; font-size: 14px; font-family: inherit; resize: none; max-height: 120px; outline: none; transition: border-color 0.2s; }}
        .input-area textarea:focus {{ border-color: #667eea; }}
        .input-area button {{ background: #667eea; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; }}
        .input-area button:hover {{ background: #5a6fd6; }}
        .input-area button:disabled {{ background: #ccc; cursor: not-allowed; }}
        .input-area button.stop-btn {{ background: #ef4444; animation: pulse-stop 1s infinite; }}
        .input-area button.stop-btn:hover {{ background: #dc2626; }}
        .input-area button.image-btn {{ background: #10b981; }}
        .input-area button.image-btn:hover {{ background: #059669; }}
        @keyframes pulse-stop {{ 0%, 100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }} 50% {{ box-shadow: 0 0 0 6px rgba(239,68,68,0); }} }}
        .suggestions {{ display: flex; gap: 8px; padding: 0 16px 8px; flex-wrap: wrap; }}
        .suggestion {{ background: white; border: 1px solid #ddd; border-radius: 16px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }}
        .suggestion:hover {{ background: #667eea; color: white; border-color: #667eea; }}
        .tool-badge {{ display: inline-block; background: #e8f0fe; color: #1967d2; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
        .status-badge {{ display: inline-block; background: #fef3c7; color: #92400e; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px; animation: fadeIn 0.3s ease; }}
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px;">\U0001f916</span>
        <h1>AI Assistant</h1>
        <span class="badge">v{VERSION}</span>
        <select id="modelSelect" onchange="changeModel(this.value)" title="Cambia modello"></select>
        <!-- Populated by JavaScript -->
        <span class="badge">\U0001f5bc Vision</span>
        <button class="new-chat" onclick="newChat()" title="Nuova conversazione">✨ Nuova chat</button>
        <div class="status">
            <div class="status-dot"></div>
            {status_text}
        </div>
    </div>

    <div class="main-container">
        <div class="sidebar">
            <div class="sidebar-header">📝 Conversazioni</div>
            <div class="chat-list" id="chatList"></div>
        </div>
        <div class="main-content">
            <div class="chat-container" id="chat">
        <div class="message system">
            {msgs['welcome']}<br>
            {msgs['provider_model']}<br>
            {msgs['capabilities']}<br>
            {msgs['vision_feature']}
        </div>
    </div>

    <div class="suggestions" id="suggestions">
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f4a1 Mostra tutte le luci</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f321 Stato sensori</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f3e0 Stanze e aree</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f4c8 Storico temperatura</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\U0001f3ac Scene disponibili</div>
        <div class="suggestion" onclick="sendSuggestion(this)">\u2699\ufe0f Lista automazioni</div>
    </div>

    <div class="input-area">
        <div id="imagePreviewContainer" class="image-preview-container">
            <img id="imagePreview" class="image-preview" />
            <button class="remove-image-btn" onclick="removeImage()" title="Rimuovi immagine">×</button>
        </div>
        <div class="input-row">
            <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageSelect(event)" />
            <button class="image-btn" onclick="document.getElementById('imageInput').click()" title="Carica immagine">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
            </button>
            <textarea id="input" rows="1" placeholder="Scrivi un messaggio..." onkeydown="handleKeyDown(event)" oninput="autoResize(this)"></textarea>
            <button id="sendBtn" onclick="handleButtonClick()">
                <svg id="sendIcon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                <svg id="stopIcon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="display:none"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
            </button>
        </div>
    </div>
        </div>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('sendBtn');
        const sendIcon = document.getElementById('sendIcon');
        const stopIcon = document.getElementById('stopIcon');
        const suggestionsEl = document.getElementById('suggestions');
        const chatList = document.getElementById('chatList');
        const imageInput = document.getElementById('imageInput');
        const imagePreview = document.getElementById('imagePreview');
        const imagePreviewContainer = document.getElementById('imagePreviewContainer');
        let sending = false;
        let currentReader = null;
        let currentSessionId = localStorage.getItem('currentSessionId') || Date.now().toString();
        let currentImage = null;  // Stores base64 image data

        function handleImageSelect(event) {{
            const file = event.target.files[0];
            if (!file) return;
            
            // Check file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {{
                alert('L\\'immagine è troppo grande. Massimo 5MB.');
                return;
            }}
            
            const reader = new FileReader();
            reader.onload = (e) => {{
                currentImage = e.target.result;
                imagePreview.src = currentImage;
                imagePreviewContainer.classList.add('visible');
            }};
            reader.readAsDataURL(file);
        }}

        function removeImage() {{
            currentImage = null;
            imageInput.value = '';
            imagePreviewContainer.classList.remove('visible');
        }}

        function apiUrl(path) {{
            // Keep paths relative so HA Ingress routes to this add-on
            if (path.startsWith('/')) {{
                return path.slice(1);
            }}
            return path;
        }}

        function setStopMode(active) {{
            if (active) {{
                sendBtn.classList.add('stop-btn');
                sendBtn.disabled = false;
                sendIcon.style.display = 'none';
                stopIcon.style.display = 'block';
            }} else {{
                sendBtn.classList.remove('stop-btn');
                sendIcon.style.display = 'block';
                stopIcon.style.display = 'none';
            }}
        }}

        async function handleButtonClick() {{
            if (sending) {{
                try {{
                    await fetch(apiUrl('api/chat/abort'), {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: '{{}}' }});
                    if (currentReader) {{ currentReader.cancel(); currentReader = null; }}
                }} catch(e) {{ console.error('Abort error:', e); }}
                removeThinking();
                sending = false;
                setStopMode(false);
                sendBtn.disabled = false;
            }} else {{
                sendMessage();
            }}
        }}

        function autoResize(el) {{
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        }}

        function handleKeyDown(e) {{
            if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); sendMessage(); }}
        }}

        function addMessage(text, role, imageData = null, metadata = null) {{
            const div = document.createElement('div');
            div.className = 'message ' + role;
            if (role === 'assistant') {{ 
                let content = formatMarkdown(text);
                // Add model badge if metadata is available
                if (metadata && (metadata.model || metadata.provider)) {{
                    const modelBadge = `<div style="font-size: 11px; color: #999; margin-bottom: 6px; opacity: 0.8;">🤖 ${{metadata.provider || 'AI'}} | ${{metadata.model || 'unknown'}}</div>`;
                    content = modelBadge + content;
                }}
                div.innerHTML = content;
            }} else {{ 
                div.textContent = text; 
                if (imageData) {{
                    const img = document.createElement('img');
                    img.src = imageData;
                    div.appendChild(img);
                }}
            }}
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}

        function formatMarkdown(text) {{
            text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<div class="code-block"><button class="copy-button" onclick="copyCode(this)">📋 Copia</button><pre><code>$2</code></pre></div>');
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            text = text.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
            text = text.replace(/\\n/g, '<br>');
            return text;
        }}

        function copyCode(button) {{
            const codeBlock = button.nextElementSibling;
            const codeElement = codeBlock.querySelector('code');
            const code = codeElement ? (codeElement.innerText || codeElement.textContent) : codeBlock.textContent;

            const showSuccess = () => {{
                const originalText = button.textContent;
                button.textContent = '✓ Copiato!';
                button.classList.add('copied');
                setTimeout(() => {{
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }}, 2000);
            }};

            // Try modern clipboard API first (requires HTTPS)
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(code).then(showSuccess).catch(() => {{
                    // Fallback to older method for HTTP
                    fallbackCopy(code, showSuccess);
                }});
            }} else {{
                // Fallback for older browsers or HTTP
                fallbackCopy(code, showSuccess);
            }}
        }}

        function fallbackCopy(text, callback) {{
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {{
                document.execCommand('copy');
                callback();
            }} catch (err) {{
                console.error('Copy failed:', err);
            }}
            document.body.removeChild(textarea);
        }}

        function showThinking() {{
            const div = document.createElement('div');
            div.className = 'message thinking';
            div.id = 'thinking';
            div.innerHTML = '{msgs['analyzing']}<span class="dots"><span>.</span><span>.</span><span>.</span></span>';
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}

        function removeThinking() {{
            const el = document.getElementById('thinking');
            if (el) el.remove();
        }}

        function sendSuggestion(el) {{
            input.value = el.textContent.replace(/^.{{2}}/, '').trim();
            sendMessage();
        }}

        async function sendMessage() {{
            const text = input.value.trim();
            if (!text || sending) return;
            sending = true;
            setStopMode(true);
            input.value = '';
            input.style.height = 'auto';
            suggestionsEl.style.display = 'none';
            
            // Show user message with image if present
            const imageToSend = currentImage;
            addMessage(text, 'user', imageToSend);
            showThinking();
            
            try {{
                const payload = {{ 
                    message: text, 
                    session_id: currentSessionId 
                }};
                if (imageToSend) {{
                    payload.image = imageToSend;
                }}
                
                const resp = await fetch(apiUrl('api/chat/stream'), {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});
                
                // Clear image after sending
                removeImage();
                
                removeThinking();
                if (resp.headers.get('content-type')?.includes('text/event-stream')) {{
                    await handleStream(resp);
                }} else {{
                    const data = await resp.json();
                    if (data.response) {{ addMessage(data.response, 'assistant'); }}
                    else if (data.error) {{ addMessage('\u274c ' + data.error, 'system'); }}
                }}
            }} catch (err) {{
                removeThinking();
                if (err.name !== 'AbortError') {{
                    addMessage('\u274c Errore: ' + err.message, 'system');
                }}
            }}
            sending = false;
            setStopMode(false);
            sendBtn.disabled = false;
            currentReader = null;
            loadChatList();
            input.focus();
        }}

        async function handleStream(resp) {{
            const reader = resp.body.getReader();
            currentReader = reader;
            const decoder = new TextDecoder();
            let div = null;
            let fullText = '';
            let buffer = '';
            let hasTools = false;
            let gotAnyEvent = false;
            try {{
            while (true) {{
                const {{ done, value }} = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, {{ stream: true }});
                while (buffer.includes('\\n\\n')) {{
                    const idx = buffer.indexOf('\\n\\n');
                    const chunk = buffer.substring(0, idx);
                    buffer = buffer.substring(idx + 2);
                    for (const line of chunk.split('\\n')) {{
                        if (!line.startsWith('data: ')) continue;
                        try {{
                            const evt = JSON.parse(line.slice(6));
                            gotAnyEvent = true;
                            if (evt.type === 'tool') {{
                                removeThinking();
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                hasTools = true;
                                const desc = evt.description || evt.name;
                                div.innerHTML += '<div class="tool-badge">\U0001f527 ' + desc + '</div>';
                            }} else if (evt.type === 'clear') {{
                                removeThinking();
                                if (div) {{ div.innerHTML = ''; }}
                                fullText = '';
                                hasTools = false;
                            }} else if (evt.type === 'status') {{
                                removeThinking();
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                const oldStatus = div.querySelector('.status-badge');
                                if (oldStatus) oldStatus.remove();
                                div.innerHTML += '<div class="status-badge">\u23f3 ' + evt.message + '</div>';
                            }} else if (evt.type === 'token') {{
                                removeThinking();
                                if (hasTools && div) {{ div.innerHTML = ''; fullText = ''; hasTools = false; }}
                                if (!div) {{ div = document.createElement('div'); div.className = 'message assistant'; chat.appendChild(div); }}
                                fullText += evt.content;
                                div.innerHTML = formatMarkdown(fullText);
                            }} else if (evt.type === 'error') {{
                                removeThinking();
                                addMessage('\u274c ' + evt.message, 'system');
                            }} else if (evt.type === 'done') {{
                                removeThinking();
                            }}
                            chat.scrollTop = chat.scrollHeight;
                        }} catch(e) {{}}
                    }}
                }}
            }}
            }} catch(streamErr) {{
                if (streamErr.name !== 'AbortError') {{
                    console.error('Stream error:', streamErr);
                }}
            }}
            removeThinking();
            if (!gotAnyEvent) {{
                addMessage('\u274c Connessione interrotta. Riprova.', 'system');
            }}
        }}

        async function loadChatList() {{
            try {{
                const resp = await fetch(apiUrl('api/conversations'));
                const data = await resp.json();
                chatList.innerHTML = '';
                if (data.conversations && data.conversations.length > 0) {{
                    data.conversations.forEach(conv => {{
                        const item = document.createElement('div');
                        item.className = 'chat-item' + (conv.id === currentSessionId ? ' active' : '');
                        item.innerHTML = `
                            <div style="flex: 1;" onclick="loadConversation('${{conv.id}}')">
                                <div class="chat-item-title">${{conv.title}}</div>
                                <div class="chat-item-info">${{conv.message_count}} messaggi</div>
                            </div>
                            <span class="chat-item-delete" onclick="deleteConversation(event, '${{conv.id}}')" title="Elimina chat">🗑</span>
                        `;
                        chatList.appendChild(item);
                    }});
                }} else {{
                    chatList.innerHTML = '<div style="padding: 12px; text-align: center; color: #999; font-size: 12px;">Nessuna conversazione</div>';
                }}
            }} catch(e) {{ console.error('Error loading chat list:', e); }}
        }}

        async function deleteConversation(event, sessionId) {{
            event.stopPropagation();
            if (!confirm('Eliminare questa conversazione?')) return;
            try {{
                const resp = await fetch(apiUrl(`api/conversations/${{sessionId}}`), {{ method: 'DELETE' }});
                if (resp.ok) {{
                    if (sessionId === currentSessionId) {{
                        newChat();
                    }} else {{
                        loadChatList();
                    }}
                }}
            }} catch(e) {{ console.error('Error deleting conversation:', e); }}
        }}

        async function loadConversation(sessionId) {{
            currentSessionId = sessionId;
            localStorage.setItem('currentSessionId', sessionId);
            try {{
                const resp = await fetch(apiUrl(`api/conversations/${{sessionId}}`));
                if (resp.status === 404) {{
                    console.log('Session not found, creating new session');
                    newChat();
                    return;
                }}
                const data = await resp.json();
                chat.innerHTML = '';
                if (data.messages && data.messages.length > 0) {{
                    suggestionsEl.style.display = 'none';
                    data.messages.forEach(m => {{
                        if (m.role === 'user' || m.role === 'assistant') {{
                            const metadata = (m.role === 'assistant' && (m.model || m.provider)) ? {{ model: m.model, provider: m.provider }} : null;
                            addMessage(m.content, m.role, null, metadata);
                        }}
                    }});
                }} else {{
                    chat.innerHTML = `<div class="message system">
                        {msgs['welcome']}<br>
                        {msgs['provider_model']}<br>
                        {msgs['capabilities']}<br>
                        {msgs['vision_feature']}
                    </div>`;
                    suggestionsEl.style.display = 'flex';
                }}
                loadChatList();
            }} catch(e) {{ console.error('Error loading conversation:', e); }}
        }}

        async function loadHistory() {{
            await loadConversation(currentSessionId);
        }}

        async function newChat() {{
            currentSessionId = Date.now().toString();
            localStorage.setItem('currentSessionId', currentSessionId);
            chat.innerHTML = `<div class="message system">
                {msgs['welcome']}<br>
                {msgs['provider_model']}<br>
                {msgs['capabilities']}<br>
                {msgs['vision_feature']}
            </div>`;
            suggestionsEl.style.display = 'flex';
            removeImage();
            loadChatList();
        }}

        // Provider name mapping for optgroups
        const PROVIDER_LABELS = {{
            'anthropic': '🧠 Anthropic Claude',
            'openai': '⚡ OpenAI',
            'google': '✨ Google Gemini',
            'nvidia': '🎯 NVIDIA NIM',
            'github': '🚀 GitHub Models'
        }};

        // Load models and populate dropdown with ALL providers
        async function loadModels() {{
            try {{
                const response = await fetch(apiUrl('api/get_models'));
                if (!response.ok) {{
                    throw new Error('get_models failed: ' + response.status);
                }}
                const data = await response.json();
                console.log('[loadModels] API response:', data);
                
                const select = document.getElementById('modelSelect');
                const currentProvider = data.current_provider;
                const currentModel = data.current_model;
                
                console.log('[loadModels] Provider:', currentProvider, 'Current model:', currentModel);

                // Clear existing options
                select.innerHTML = '';

                // Add models for ALL available providers, grouped by optgroup
                const providerOrder = ['anthropic', 'openai', 'google', 'nvidia', 'github'];
                let availableProviders = data.available_providers && data.available_providers.length
                    ? data.available_providers.map(p => p.id)
                    : Object.keys(data.models || {{}});
                if (!availableProviders.length && currentProvider) {{
                    availableProviders = [currentProvider];
                }}
                
                for (const providerId of providerOrder) {{
                    if (!availableProviders.includes(providerId)) continue;
                    if (!data.models || !data.models[providerId] || data.models[providerId].length === 0) continue;
                    
                    const group = document.createElement('optgroup');
                    group.label = PROVIDER_LABELS[providerId] || providerId;
                    
                    data.models[providerId].forEach(model => {{
                        const option = document.createElement('option');
                        option.value = JSON.stringify({{model: model, provider: providerId}});
                        // Show just the model name without provider prefix
                        const displayName = model.replace(/^(Claude|OpenAI|Google|NVIDIA|GitHub):\\s*/, '');
                        option.textContent = displayName;
                        if (model === currentModel && providerId === currentProvider) {{
                            option.selected = true;
                        }}
                        group.appendChild(option);
                    }});
                    
                    select.appendChild(group);
                }}
                if (!select.options.length) {{
                    const option = document.createElement('option');
                    option.textContent = 'Nessun modello disponibile';
                    option.disabled = true;
                    option.selected = true;
                    select.appendChild(option);
                    if (!window._modelsEmptyNotified) {{
                        addMessage('⚠️ Nessun modello disponibile. Verifica le API key dei provider.', 'system');
                        window._modelsEmptyNotified = true;
                    }}
                }}
                console.log('[loadModels] Loaded models for', availableProviders.length, 'providers');
            }} catch (error) {{
                console.error('[loadModels] Error loading models:', error);
            }}
        }}

        // Change model (with automatic provider switch)
        async function changeModel(value) {{
            try {{
                const parsed = JSON.parse(value);
                const response = await fetch(apiUrl('api/set_model'), {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{model: parsed.model, provider: parsed.provider}})
                }});
                if (response.ok) {{
                    const data = await response.json();
                    console.log('Model changed to:', parsed.model, 'Provider:', parsed.provider);
                    // Show notification
                    const providerName = PROVIDER_LABELS[parsed.provider] || parsed.provider;
                    addMessage(`🔄 Passato a ${{providerName}} → ${{parsed.model}}`, 'system');
                }}
            }} catch (error) {{
                console.error('Error changing model:', error);
            }}
        }}

        // Load history on page load
        loadModels();
        loadChatList();
        loadHistory();
        input.focus();
    </script>
</body>
</html>"""


# ---- Flask Routes ----


@app.route('/')
def index():
    """Serve the chat UI."""
    return get_chat_ui(), 200, {'Content-Type': 'text/html; charset=utf-8'}


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
    global AI_PROVIDER, AI_MODEL

    data = request.json or {}

    if "provider" in data:
        AI_PROVIDER = data["provider"]

    if "model" in data:
        AI_MODEL = normalize_model_name(data["model"])

    logger.info(f"Runtime model changed → {AI_PROVIDER} / {AI_MODEL}")

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
        prompt = get_system_prompt()
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
                "system_prompt": get_system_prompt()
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
        models_technical[provider] = list(models)
        # Use per-provider display mapping to avoid cross-provider conflicts
        prov_map = PROVIDER_DISPLAY.get(provider, {})
        models_display[provider] = [prov_map.get(m, m) for m in models]

    # --- Current model (sia tech che display) ---
    current_model_tech = get_active_model()
    current_model_display = MODEL_DISPLAY_MAPPING.get(current_model_tech, current_model_tech)

    # --- Modelli del provider corrente (per HA settings: lista con flag current) ---
    provider_models = PROVIDER_MODELS.get(AI_PROVIDER, [])
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
