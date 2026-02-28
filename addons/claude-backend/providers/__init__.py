"""Provider package for multi-provider AI assistant support.

This package contains:
- base.py: Abstract base classes for all provider types
- manager.py: Provider factory and orchestration
- Chat providers: openai.py, anthropic.py, nvidia.py, github.py, google.py, groq.py, ollama.py, mistral.py
- Specialized providers: vision, tts, transcription implementations

Example usage:
    from providers import manager
    
    for event in manager.stream_chat("anthropic", messages, fallback_chain=["openai"]):
        if event["type"] == "content":
            print(event["content"], end="", flush=True)
        elif event["type"] == "error":
            print(f"Error: {event['message']}")
"""

from .base import BaseProvider, TextToSpeechProvider, VisionProvider, TranscriptionProvider
from .manager import ProviderManager, get_manager, stream_chat, get_manager_stats

# Lazy imports for provider implementations (loaded when needed)
_PROVIDER_CLASSES = {
    "openai": "providers.openai:OpenAIProvider",
    "anthropic": "providers.anthropic:AnthropicProvider",
    "nvidia": "providers.nvidia:NVIDIAProvider",
    "github": "providers.github:GitHubProvider",
    "google": "providers.google:GoogleProvider",
    "groq": "providers.groq:GroqProvider",
    "ollama": "providers.ollama:OllamaProvider",
    "mistral": "providers.mistral:MistralProvider",
    "openrouter": "providers.openrouter:OpenRouterProvider",
    "deepseek": "providers.deepseek:DeepSeekProvider",
    "minimax": "providers.minimax:MinimaxProvider",
    "aihubmix": "providers.aihubmix:AiHubMixProvider",
    "siliconflow": "providers.siliconflow:SiliconFlowProvider",
    "volcengine": "providers.volcengine:VolcEngineProvider",
    "dashscope": "providers.dashscope:DashScopeProvider",
    "moonshot": "providers.moonshot:MoonshotProvider",
    "zhipu": "providers.zhipu:ZhipuProvider",
    "perplexity": "providers.perplexity:PerplexityProvider",
    "custom": "providers.custom:CustomProvider",
    "github_copilot": "providers.github_copilot:GitHubCopilotProvider",
    "openai_codex": "providers.openai_codex:OpenAICodexProvider",
    "claude_web": "providers.claude_web:ClaudeWebProvider",
    "chatgpt_web": "providers.chatgpt_web:ChatGPTWebProvider",
}


def get_provider_class(provider_name: str):
    """Dynamically import and return a provider class.
    
    Args:
        provider_name: Provider identifier (e.g., 'openai', 'anthropic')
        
    Returns:
        Provider class (subclass of BaseProvider)
    """
    if provider_name not in _PROVIDER_CLASSES:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    class_path = _PROVIDER_CLASSES[provider_name]
    module_path, class_name = class_path.split(":")
    
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)


__all__ = [
    "BaseProvider",
    "TextToSpeechProvider",
    "VisionProvider",
    "TranscriptionProvider",
    "ProviderManager",
    "get_manager",
    "stream_chat",
    "get_manager_stats",
    "get_provider_class",
]
