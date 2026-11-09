"""
AI-CONTENT-AUTOMATION — Base AI Provider
==========================================
Abstract interface for all AI text & reasoning providers.
Allows interchangeable use of Google Gemini, local Ollama,
or other optional model adapters.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class AIResponse:
    """Standardized response from any AI provider."""
    text: str
    provider: str
    model: str
    finish_reason: str = "stop"
    raw_response: Optional[Any] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAIProvider(ABC):
    """Abstract base class for all AI model providers."""

    def __init__(self, name: str, default_model: str):
        self.name = name
        self.default_model = default_model

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and reachable."""
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """Generates plain text response."""
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """Generates and parses a JSON response from the model."""
        pass
