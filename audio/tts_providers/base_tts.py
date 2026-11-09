"""
AI-CONTENT-AUTOMATION — Base TTS Provider
==========================================
Abstract interface for voice synthesis engines.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WordTimestamp:
    """Exact word-level timing for animated subtitles."""
    word: str
    start_ms: int
    end_ms: int


@dataclass
class TTSResult:
    """Standardized result from voice synthesis."""
    audio_path: str
    duration_s: float
    provider: str
    voice: str
    word_timestamps: List[WordTimestamp] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTTSProvider(ABC):
    """Abstract base class for all Text-to-Speech providers."""

    def __init__(self, name: str, default_voice: str):
        self.name = name
        self.default_voice = default_voice

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider can synthesize speech."""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        rate: float = 1.0,
        volume: float = 1.0,
    ) -> TTSResult:
        """Synthesizes text into an audio file."""
        pass

    @abstractmethod
    def list_voices(self) -> List[Dict[str, str]]:
        """Returns available voice names and languages."""
        pass
