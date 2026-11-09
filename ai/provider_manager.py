"""
AI-CONTENT-AUTOMATION — AI Provider Manager
============================================
Central orchestrator that routes AI requests to the best available provider
based on priority and real-time availability.

Handles:
- Automatic failover (e.g., Gemini rate limit -> local Ollama).
- Rate limit and daily quota protection.
- Usage logging and error diagnostics.
"""

from typing import Dict, List, Optional, Any
from ai.providers.base_provider import BaseAIProvider, AIResponse
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.anthropic_provider import AnthropicProvider
from config import config
from core.logger import get_logger

logger = get_logger(__name__)


class AIProviderManager:
    """
    Manages and coordinates multiple AI model providers.
    Ensures zero downtime by falling back across providers.
    """

    def __init__(self):
        self.providers: Dict[str, BaseAIProvider] = {
            "gemini": GeminiProvider(),
            "ollama": OllamaProvider(),
            "anthropic": AnthropicProvider(),
        }
        self.priority: List[str] = [
            p.strip().lower() for p in config.ai.provider_priority if p.strip()
        ]

    def get_provider(self, name: str) -> Optional[BaseAIProvider]:
        """Returns a specific provider instance by name."""
        return self.providers.get(name.lower())

    def get_active_providers(self) -> List[str]:
        """Returns names of all currently configured and reachable providers."""
        active = []
        for name, provider in self.providers.items():
            try:
                if provider.is_available():
                    active.append(name)
            except Exception:
                pass
        return active

    def get_status(self) -> Dict[str, Any]:
        """Returns human-readable diagnostic status of all providers."""
        status = {}
        for name, provider in self.providers.items():
            available = False
            try:
                available = provider.is_available()
            except Exception:
                pass
            status[name] = {
                "available": available,
                "default_model": provider.default_model,
                "in_priority_list": name in self.priority,
            }
        return {
            "priority": self.priority,
            "providers": status,
            "active_count": len(self.get_active_providers()),
        }

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """
        Generates text using the preferred provider, or steps through priority order.
        Transparently falls back if a provider fails or hits quota limits.
        """
        chain = self._build_execution_chain(preferred_provider)
        errors = []

        for provider_name in chain:
            provider = self.providers.get(provider_name)
            if not provider or not provider.is_available():
                continue

            try:
                logger.info(f"Generating text with provider: {provider_name}")
                response = provider.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                self._record_analytics_event("ai_text_generation", provider_name, success=True)
                return response
            except Exception as e:
                logger.warning(f"Provider '{provider_name}' failed: {e}. Attempting fallback...")
                errors.append(f"{provider_name}: {str(e)}")
                self._record_analytics_event("ai_text_generation", provider_name, success=False)

        raise RuntimeError(
            f"All configured AI providers failed to generate text.\n"
            f"Attempted: {', '.join(chain)}\n"
            f"Errors: {'; '.join(errors)}\n\n"
            f"Remediation:\n"
            f"1. Check your GEMINI_API_KEY in .env, OR\n"
            f"2. Start Ollama locally with 'ollama serve' for offline generation."
        )

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Generates and parses JSON data, falling back across providers on failure.
        """
        chain = self._build_execution_chain(preferred_provider)
        errors = []

        for provider_name in chain:
            provider = self.providers.get(provider_name)
            if not provider or not provider.is_available():
                continue

            try:
                logger.info(f"Generating JSON with provider: {provider_name}")
                data = provider.generate_json(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                )
                self._record_analytics_event("ai_json_generation", provider_name, success=True)
                return data
            except Exception as e:
                logger.warning(f"Provider '{provider_name}' failed JSON generation: {e}. Falling back...")
                errors.append(f"{provider_name}: {str(e)}")
                self._record_analytics_event("ai_json_generation", provider_name, success=False)

        raise RuntimeError(
            f"All configured AI providers failed to generate structured JSON.\n"
            f"Attempted: {', '.join(chain)}\n"
            f"Errors: {'; '.join(errors)}"
        )

    def _build_execution_chain(self, preferred: Optional[str] = None) -> List[str]:
        """Builds the list of provider names to try in sequence."""
        if preferred and preferred.lower() in self.providers:
            # Preferred first, then rest of priority
            chain = [preferred.lower()]
            for p in self.priority:
                if p not in chain:
                    chain.append(p)
            return chain
        return self.priority.copy()

    def _record_analytics_event(self, event_type: str, provider: str, success: bool):
        """Records an event in the SQLite analytics table for monitoring."""
        try:
            from database.db_manager import db
            db.execute("""
                INSERT INTO analytics_events (event_type, engine, platform, value, metadata, created_at)
                VALUES (:type, 'shared_ai', :provider, :val, :meta, datetime('now'))
            """, {
                "type": event_type,
                "provider": provider,
                "val": 1.0 if success else 0.0,
                "meta": f"{{\"success\": {str(success).lower()}}}"
            })
        except Exception:
            pass  # Analytics shouldn't crash AI generation


# Singleton instance
ai_provider_manager = AIProviderManager()
