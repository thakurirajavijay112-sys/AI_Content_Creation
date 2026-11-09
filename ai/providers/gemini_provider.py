"""
AI-CONTENT-AUTOMATION — Google Gemini Provider
================================================
Adapter for Google's Gemini models via the google-generativeai SDK.
Supports gemini-1.5-flash (default, high speed, generous free quota)
and gemini-1.5-pro (deep reasoning).
"""

import json
import re
from datetime import datetime
from typing import Optional, Dict, Any

from ai.providers.base_provider import BaseAIProvider, AIResponse
from config import config
from core.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini API provider implementation.
    Includes daily quota monitoring to safeguard the 1,500 req/day free limit.
    """

    def __init__(self):
        super().__init__(
            name="gemini",
            default_model=config.ai.gemini.default_model or "gemini-1.5-flash"
        )
        self.api_key = config.ai.gemini.api_key
        self._client_configured = False
        self._daily_request_count = 0
        self._last_count_date = datetime.now().date()

    def _ensure_configured(self):
        """Initializes the google.generativeai client once key is verified."""
        if self._client_configured:
            return

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError(
                "Gemini API key is not configured. "
                "Please set GEMINI_API_KEY in your .env file."
            )

        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self._client_configured = True
        logger.info(f"Gemini client successfully configured with model: {self.default_model}")

    def _check_daily_quota(self):
        """Monitors and protects against exceeding daily free tier limits."""
        today = datetime.now().date()
        if today != self._last_count_date:
            self._daily_request_count = 0
            self._last_count_date = today

        daily_limit = config.ai.gemini.daily_limit
        if self._daily_request_count >= daily_limit:
            raise RuntimeError(
                f"Gemini daily safety threshold reached ({self._daily_request_count}/{daily_limit} calls). "
                "Switching to fallback provider to prevent unintended charges."
            )

    def is_available(self) -> bool:
        """Checks if an API key is provided and valid."""
        return bool(self.api_key) and self.api_key != "your_gemini_api_key_here"

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """Generates plain text response via Gemini."""
        self._ensure_configured()
        self._check_daily_quota()

        import google.generativeai as genai

        target_model = model or self.default_model
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        gemini_model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=system_prompt if system_prompt else None,
        )

        try:
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            self._daily_request_count += 1
            
            output_text = response.text if response.text else ""
            return AIResponse(
                text=output_text,
                provider=self.name,
                model=target_model,
                raw_response=response,
                metadata={"daily_calls_used": self._daily_request_count}
            )
        except Exception as e:
            logger.error(f"Gemini API error during text generation: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generates structured JSON data from Gemini."""
        self._ensure_configured()
        self._check_daily_quota()

        import google.generativeai as genai

        target_model = model or self.default_model
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
        )

        gemini_model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=system_prompt if system_prompt else None,
        )

        try:
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            self._daily_request_count += 1

            cleaned = self._clean_json_string(response.text)
            return json.loads(cleaned)
        except json.JSONDecodeError as jde:
            logger.warning(f"Failed to parse direct JSON from Gemini, attempting regex extraction: {jde}")
            cleaned = self._clean_json_string(response.text)
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Gemini API error during JSON generation: {e}")
            raise

    @staticmethod
    def _clean_json_string(text: str) -> str:
        """Strips markdown code fences (```json ... ```) if present."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text
