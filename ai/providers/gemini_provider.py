"""
AI-CONTENT-AUTOMATION — Google Gemini Provider
================================================
Adapter for Google's Gemini models via the google-generativeai SDK.
Supports auto-model discovery (gemini-flash-latest, gemini-pro-latest)
and daily quota protection.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from ai.providers.base_provider import BaseAIProvider, AIResponse
from config import config
from core.logger import get_logger

logger = get_logger(__name__)

# Models confirmed working on Gemini API with active generation capabilities
FALLBACK_MODELS = [
    "gemini-flash-lite-latest",    # Primary free-tier model (high quota, fast)
    "gemini-flash-latest",         # Standard high-speed fallback
    "gemma-4-26b-a4b-it",          # Open weights model hosted on Gemini API
]


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini API provider implementation.
    Includes model auto-selection, quota failover (429/503), and daily monitoring.
    """

    def __init__(self):
        super().__init__(
            name="gemini",
            default_model="gemini-flash-lite-latest"
        )
        self.api_key = config.ai.gemini.api_key
        self._client_configured = False
        self._daily_request_count = 0
        self._last_count_date = datetime.now().date()
        self._resolved_model: Optional[str] = "gemini-flash-lite-latest"

    def _ensure_configured(self):
        """Initializes the google.generativeai client once key is verified."""
        if self._client_configured:
            return

        # Re-check api key from environment if needed
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            import os
            self.api_key = os.environ.get("GEMINI_API_KEY", "")

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError(
                "Gemini API key is not configured. "
                "Please set GEMINI_API_KEY in your .env file."
            )

        import google.generativeai as genai
        genai.configure(api_key=self.api_key, transport="rest")
        self._client_configured = True
        logger.info("Gemini client successfully configured with REST transport.")

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
        import os
        env_key = os.environ.get("GEMINI_API_KEY")
        key = env_key if env_key is not None else self.api_key
        return bool(key) and key != "your_gemini_api_key_here"

    def _get_candidate_models(self, requested_model: Optional[str] = None) -> List[str]:
        """Builds an ordered list of model candidates to try."""
        candidates = []
        if self._resolved_model:
            candidates.append(self._resolved_model)
        if requested_model and requested_model not in candidates:
            candidates.append(requested_model)
        if self.default_model and self.default_model not in candidates:
            candidates.append(self.default_model)
        for m in FALLBACK_MODELS:
            if m not in candidates:
                candidates.append(m)
        return candidates

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_mime_type: Optional[str] = None,
    ) -> AIResponse:
        """Generates plain text response via Gemini with automatic model failover."""
        self._ensure_configured()
        self._check_daily_quota()

        import google.generativeai as genai

        gen_config_kwargs = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if response_mime_type:
            gen_config_kwargs["response_mime_type"] = response_mime_type

        generation_config = genai.types.GenerationConfig(**gen_config_kwargs)

        candidates = self._get_candidate_models(model)
        last_error = None

        for candidate in candidates:
            try:
                gemini_model = genai.GenerativeModel(
                    model_name=candidate,
                    system_instruction=system_prompt if system_prompt else None,
                )
                response = gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                self._daily_request_count += 1
                self._resolved_model = candidate

                output_text = response.text if response.text else ""
                return AIResponse(
                    text=output_text,
                    provider=self.name,
                    model=candidate,
                    raw_response=response,
                    metadata={"daily_calls_used": self._daily_request_count}
                )
            except Exception as e:
                err_str = str(e).lower()
                is_retryable = any(
                    k in err_str
                    for k in ("404", "not found", "429", "quota", "resourceexhausted", "503", "unavailable", "timed out")
                )
                if is_retryable:
                    logger.warning(
                        f"Gemini model '{candidate}' unavailable ({e}). "
                        "Failing over to next candidate model..."
                    )
                    last_error = e
                    continue
                else:
                    logger.error(f"Gemini API fatal error during text generation: {e}")
                    raise

        raise last_error or RuntimeError("All Gemini model candidates failed.")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generates structured JSON data from Gemini with clean parsing and control character repair."""
        enhanced_prompt = prompt + "\n\nCRITICAL: Respond ONLY with valid JSON. Do not write any conversational text outside the JSON block."
        res = self.generate_text(
            prompt=enhanced_prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=4096,
            response_mime_type="application/json",
        )
        cleaned = self._clean_json_string(res.text)

        # 1. Try standard lenient parse (strict=False permits literal newlines inside strings)
        try:
            return json.loads(cleaned, strict=False)
        except Exception as first_err:
            logger.warning(f"Initial JSON parse failed ({first_err}), attempting control character sanitization...")

        # 2. Sanitize unescaped control characters (ASCII 0-31 except \t, \r, \n)
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', cleaned)
        try:
            return json.loads(sanitized, strict=False)
        except Exception:
            pass

        # 3. Replace raw newlines inside string literals with \n
        def escape_string_newlines(match):
            inner = match.group(0)
            return inner.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

        escaped = re.sub(r'"(?:[^"\\]|\\.)*"', escape_string_newlines, sanitized, flags=re.DOTALL)
        return json.loads(escaped, strict=False)

    def generate_image(
        self,
        prompt: str,
        out_path: Path,
        model_name: str = "gemini-3.1-flash-image",
    ) -> Path:
        """
        Sends scene visual prompt to dedicated Gemini image-generation model.
        Decodes inline image data and saves to out_path.
        Logs model, response type, output status without leaking API keys.
        """
        self._ensure_configured()
        import google.generativeai as genai
        from PIL import Image
        import base64

        logger.info(f"[Gemini Image Gen] Requesting image with model '{model_name}'...")
        out_path = Path(out_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
        except Exception as e:
            err_msg = str(e)
            if "limit: 0" in err_msg:
                logger.warning(
                    f"[Gemini Image Gen] Model '{model_name}' has quota limit: 0 on current Free Tier key. "
                    "Image generation on Gemini API requires a billing-enabled account ($0.03/image)."
                )
            else:
                logger.warning(f"[Gemini Image Gen] API call failed with model '{model_name}': {err_msg[:200]}")
            raise RuntimeError(f"Gemini image generation failed ({model_name}): {err_msg[:200]}")

        # Extract image from candidates
        if not response.candidates:
            raise RuntimeError(f"Gemini image model '{model_name}' returned empty candidates.")

        for part in response.candidates[0].content.parts:
            # Check for inline image data
            inline_data = getattr(part, "inline_data", None)
            if inline_data and getattr(inline_data, "data", None):
                raw_bytes = inline_data.data
                if isinstance(raw_bytes, str):
                    raw_bytes = base64.b64decode(raw_bytes)
                out_path.write_bytes(raw_bytes)
                # Validate with Pillow
                with Image.open(out_path) as img:
                    img.verify()
                logger.info(f"[Gemini Image Gen] Successfully saved image to {out_path.name} (type: {inline_data.mime_type})")
                return out_path

        # If model returned text instead of image
        text_resp = getattr(response, "text", "")
        logger.warning(f"[Gemini Image Gen] Model '{model_name}' returned text instead of image data: '{text_resp[:100]}'")
        raise RuntimeError(f"Gemini image model '{model_name}' returned text instead of an image.")

    @staticmethod
    def _clean_json_string(text: str) -> str:
        """Strips markdown code fences (```json ... ```) if present."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        # Find first { and last } or first [ and last ]
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace:last_brace + 1].strip()
        return text
