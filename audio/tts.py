"""
AI-CONTENT-AUTOMATION — Voice Synthesis Engine
================================================
Central Text-to-Speech manager.
Tries Edge TTS (free, human-realistic neural voices) first,
falling back to local pyttsx3 if network is unavailable.
"""

from pathlib import Path
from typing import Optional, List, Dict
import hashlib
import time

from audio.tts_providers.base_tts import BaseTTSProvider, TTSResult
from audio.tts_providers.edge_tts_provider import EdgeTTSProvider
from audio.tts_providers.pyttsx3_provider import Pyttsx3Provider
from config import config
from core.logger import get_logger

logger = get_logger(__name__)


class TTSEngine:
    """Manages voiceover generation with automatic offline fallback."""

    def __init__(self):
        self.edge_provider = EdgeTTSProvider()
        self.offline_provider = Pyttsx3Provider()
        self.output_dir = Path(__file__).parent.parent / "generated" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_speech(
        self,
        text: str,
        output_filename: Optional[str] = None,
        voice: Optional[str] = None,
        rate: float = 1.0,
        volume: float = 1.0,
        preferred_provider: str = "edge_tts",
    ) -> TTSResult:
        """
        Synthesizes text into speech.
        Automatically falls back to offline TTS if edge_tts fails.
        """
        if not output_filename:
            # Deterministic hash filename based on text and timestamp
            text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
            output_filename = f"tts_{int(time.time())}_{text_hash}.mp3"

        out_path = self.output_dir / output_filename

        # If user preferred offline or edge_tts
        if preferred_provider == "edge_tts":
            try:
                logger.info("Attempting synthesis with Edge-TTS...")
                return self.edge_provider.synthesize(
                    text=text,
                    output_path=str(out_path),
                    voice=voice,
                    rate=rate,
                    volume=volume,
                )
            except Exception as e:
                logger.warning(f"Edge-TTS failed ({e}). Falling back to offline pyttsx3...")
                # Fallback to wav output for pyttsx3 compatibility
                wav_path = out_path.with_suffix(".wav")
                return self.offline_provider.synthesize(
                    text=text,
                    output_path=str(wav_path),
                    voice=None,
                    rate=rate,
                    volume=volume,
                )
        else:
            wav_path = out_path.with_suffix(".wav")
            return self.offline_provider.synthesize(
                text=text,
                output_path=str(wav_path),
                voice=voice,
                rate=rate,
                volume=volume,
            )

    def list_available_voices(self) -> Dict[str, List[Dict[str, str]]]:
        """Returns voice catalogs from both providers."""
        return {
            "edge_tts": self.edge_provider.list_voices(),
            "pyttsx3": self.offline_provider.list_voices(),
        }


# Singleton instance
tts_engine = TTSEngine()
