"""
AI-CONTENT-AUTOMATION — Local Ollama Provider
==============================================
Runs completely offline on your local machine using Ollama.
Default model: llama3.2:3b (optimized for 4GB VRAM / 16GB RAM).
Zero cost, no API limits.
"""

import json
import re
from typing import Optional, Dict, Any
import httpx

from ai.providers.base_provider import BaseAIProvider, AIResponse
from config import config
from core.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseAIProvider):
    """
    Local Ollama API provider.
    Connects to http://localhost:11434 with zero external network dependency.
    """

    def __init__(self):
        super().__init__(
            name="ollama",
            default_model=config.ai.ollama.default_model or "llama3.2:3b"
        )
        self.base_url = config.ai.ollama.base_url.rstrip("/")
        self.enabled = config.ai.ollama.enabled

    def is_available(self) -> bool:
        """Pings the local Ollama daemon to check if it's currently running."""
        if not self.enabled:
            return False

        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """Generates plain text via local Ollama instance."""
        target_model = model or self.default_model

        payload: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

            return AIResponse(
                text=data.get("response", "").strip(),
                provider=self.name,
                model=target_model,
                raw_response=data,
            )
        except Exception as e:
            logger.error(f"Ollama local error: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generates structured JSON via Ollama with format='json' constraint."""
        target_model = model or self.default_model

        enhanced_system = (system_prompt or "") + "\nOutput MUST be valid JSON only."

        payload: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        if enhanced_system:
            payload["system"] = enhanced_system

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

            raw_text = data.get("response", "").strip()
            cleaned = self._clean_json_string(raw_text)
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Ollama JSON generation error: {e}")
            raise

    @staticmethod
    def _clean_json_string(text: str) -> str:
        """Strips markdown code fences if model enclosed JSON in them."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text
