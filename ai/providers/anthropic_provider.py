"""
AI-CONTENT-AUTOMATION — Optional Anthropic Claude Provider
===========================================================
OPTIONAL adapter for Anthropic Claude models.

IMPORTANT:
A Claude Antigravity or Claude Pro web subscription does NOT include API access.
Anthropic API requires a separate developer account and billed API key.
This provider is completely optional and only activates if ANTHROPIC_API_KEY
is explicitly supplied in the environment.
"""

import os
import json
import re
from typing import Optional, Dict, Any

from ai.providers.base_provider import BaseAIProvider, AIResponse
from core.logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseAIProvider):
    """
    Optional Anthropic API provider.
    Requires a separate, explicitly provided ANTHROPIC_API_KEY.
    """

    def __init__(self):
        super().__init__(
            name="anthropic",
            default_model=os.environ.get("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-haiku-20241022")
        )
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    def is_available(self) -> bool:
        """Returns True ONLY if an Anthropic API key has been explicitly configured."""
        return bool(self.api_key) and self.api_key != "your_anthropic_api_key_here"

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """Generates text via Anthropic API."""
        if not self.is_available():
            raise RuntimeError(
                "Anthropic API is not available. Please set ANTHROPIC_API_KEY in your .env file. "
                "Note: A Claude web/IDE subscription does not provide API credits."
            )

        import httpx

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model or self.default_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()

            output_text = data["content"][0]["text"]
            return AIResponse(
                text=output_text,
                provider=self.name,
                model=model or self.default_model,
                raw_response=data,
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generates structured JSON via Anthropic."""
        json_instruction = (system_prompt or "") + "\nRespond with valid JSON only. Do not include markdown codeblocks."
        response = self.generate_text(prompt, system_prompt=json_instruction, model=model, temperature=temperature)
        cleaned = self._clean_json_string(response.text)
        return json.loads(cleaned)

    @staticmethod
    def _clean_json_string(text: str) -> str:
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text
