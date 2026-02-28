#!/usr/bin/env python3
"""
Multimodal Image Support (Vision Models Integration)

Supports:
- Claude (Anthropic) Vision
- GPT-4V (OpenAI) Vision
- Google Vision AI

Features:
- Image format detection and validation
- Automatic provider fallback
- Image analysis caching
- Base64 encoding for API transmission
"""

import os
import json
import base64
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, List
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    JPG = "jpg"  # Alias for JPEG
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"


class VisionProvider(Enum):
    """Available vision providers."""
    CLAUDE = "claude"
    GPT4V = "gpt4v"
    GOOGLE = "google"


class ImageAnalyzer:
    """Analyze images using vision models."""
    
    # Max image sizes per provider (bytes)
    MAX_SIZES = {
        VisionProvider.CLAUDE: 5 * 1024 * 1024,    # 5 MB
        VisionProvider.GPT4V: 10 * 1024 * 1024,    # 10 MB
        VisionProvider.GOOGLE: 10 * 1024 * 1024,   # 10 MB
    }
    
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.provider_order = [
            VisionProvider.CLAUDE,
            VisionProvider.GPT4V,
            VisionProvider.GOOGLE,
        ]
    
    def _get_image_format(self, image_path: str) -> Optional[ImageFormat]:
        """Detect image format from file extension."""
        ext = Path(image_path).suffix.lower().lstrip(".")
        for fmt in ImageFormat:
            if fmt.value == ext:
                return fmt
        return None

    @staticmethod
    def _media_type(fmt: Optional["ImageFormat"]) -> str:
        """Return valid MIME type for image format (jpg→image/jpeg)."""
        if fmt is None:
            return "image/jpeg"
        return "image/jpeg" if fmt.value in ("jpg", "jpeg") else f"image/{fmt.value}"
    
    def _validate_image(self, image_path: str) -> Tuple[bool, str]:
        """Validate image file."""
        if not os.path.exists(image_path):
            return False, "Image file not found"
        
        size = os.path.getsize(image_path)
        if size > self.MAX_SIZES[VisionProvider.CLAUDE]:
            return False, f"Image too large ({size / 1024 / 1024:.1f} MB)"
        
        fmt = self._get_image_format(image_path)
        if not fmt:
            return False, f"Unsupported image format"
        
        return True, "OK"
    
    def _encode_image_base64(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _hash_image_content(self, image_path: str) -> str:
        """Get SHA256 hash of image content."""
        sha256_hash = hashlib.sha256()
        with open(image_path, "rb") as f:
            sha256_hash.update(f.read())
        return sha256_hash.hexdigest()
    
    def analyze_with_claude(self, image_path: str, prompt: str) -> Tuple[bool, str]:
        """Analyze image using Claude Vision."""
        if not self.anthropic_api_key:
            return False, "Claude API key not configured"
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            
            # Encode image
            base64_image = self._encode_image_base64(image_path)
            fmt = self._get_image_format(image_path)
            media_type = self._media_type(fmt)
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_image,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            response_text = message.content[0].text
            logger.info(f"Claude analysis: {len(response_text)} chars")
            return True, response_text
        except Exception as e:
            logger.error(f"Claude analysis error: {e}")
            return False, str(e)
    
    def analyze_with_gpt4v(self, image_path: str, prompt: str) -> Tuple[bool, str]:
        """Analyze image using GPT-4V."""
        if not self.openai_api_key:
            return False, "OpenAI API key not configured"
        
        try:
            base64_image = self._encode_image_base64(image_path)
            fmt = self._get_image_format(image_path)
            media_type = self._media_type(fmt)
            
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.openai_api_key}"}
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "max_tokens": 1024
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                text = result["choices"][0]["message"]["content"]
                logger.info(f"GPT-4V analysis: {len(text)} chars")
                return True, text
            else:
                error = response.json().get("error", {}).get("message", "Unknown error")
                return False, f"OpenAI error: {error}"
        except Exception as e:
            logger.error(f"GPT-4V analysis error: {e}")
            return False, str(e)
    
    def analyze_with_google(self, image_path: str, prompt: str) -> Tuple[bool, str]:
        """Analyze image using Google Vision AI."""
        if not self.google_api_key:
            return False, "Google API key not configured"
        
        try:
            base64_image = self._encode_image_base64(image_path)
            fmt = self._get_image_format(image_path)
            mime_type = self._media_type(fmt)
            
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_image
                                }
                            },
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                url,
                json=payload,
                params={"key": self.google_api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    logger.info(f"Google Vision analysis: {len(text)} chars")
                    return True, text
            
            error = response.json().get("error", {}).get("message", "Unknown error")
            return False, f"Google error: {error}"
        except Exception as e:
            logger.error(f"Google Vision error: {e}")
            return False, str(e)
    
    def analyze_with_fallback(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail."
    ) -> Tuple[bool, str, str]:
        """
        Analyze image with automatic fallback.
        Returns: (success, analysis, provider_used)
        """
        # Validate image
        valid, msg = self._validate_image(image_path)
        if not valid:
            return False, msg, "none"
        
        # Check cache
        image_hash = self._hash_image_content(image_path)
        cache_key = f"{image_hash}:{prompt[:50]}"
        
        if cache_key in self.analysis_cache:
            cached = self.analysis_cache[cache_key]
            if datetime.fromisoformat(cached["timestamp"]) > datetime.now() - timedelta(days=7):
                logger.info("Image analysis cache hit")
                return True, cached["analysis"], f"{cached['provider']} (cached)"
        
        # Try providers in order
        for provider in self.provider_order:
            if provider == VisionProvider.CLAUDE:
                success, text = self.analyze_with_claude(image_path, prompt)
            elif provider == VisionProvider.GPT4V:
                success, text = self.analyze_with_gpt4v(image_path, prompt)
            elif provider == VisionProvider.GOOGLE:
                success, text = self.analyze_with_google(image_path, prompt)
            else:
                continue
            
            if success:
                # Cache result
                self.analysis_cache[cache_key] = {
                    "analysis": text,
                    "provider": provider.value,
                    "timestamp": datetime.now().isoformat(),
                    "image_hash": image_hash,
                }
                logger.info(f"Image analysis successful with {provider.value}")
                return True, text, provider.value
        
        return False, "All vision providers failed", "none"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get image analyzer statistics."""
        return {
            "cache_size": len(self.analysis_cache),
            "providers_available": {
                "claude": bool(self.anthropic_api_key),
                "gpt4v": bool(self.openai_api_key),
                "google": bool(self.google_api_key),
            },
            "cached_analyses": [
                {
                    "provider": v["provider"],
                    "timestamp": v["timestamp"],
                    "analysis_length": len(v["analysis"])
                }
                for v in list(self.analysis_cache.values())[-5:]
            ]
        }


# Global instance
_image_analyzer: Optional[ImageAnalyzer] = None


def initialize_image_analyzer() -> ImageAnalyzer:
    """Initialize global image analyzer."""
    global _image_analyzer
    _image_analyzer = ImageAnalyzer()
    logger.info("Image analyzer initialized")
    return _image_analyzer


def get_image_analyzer() -> Optional[ImageAnalyzer]:
    """Get global image analyzer instance."""
    if _image_analyzer is None:
        initialize_image_analyzer()
    return _image_analyzer


if __name__ == "__main__":
    # Quick demo
    logging.basicConfig(level=logging.INFO)
    
    analyzer = ImageAnalyzer()
    print("Image Analyzer Stats:", json.dumps(analyzer.get_stats(), indent=2))
