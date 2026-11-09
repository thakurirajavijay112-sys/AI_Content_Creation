"""
AI-CONTENT-AUTOMATION — Offline Fallback pyttsx3 Provider
=========================================================
100% offline TTS provider using local system speech engine (Windows SAPI5).
Used as a resilient fallback if internet connection drops.
"""

from pathlib import Path
from typing import Optional, List, Dict
import pyttsx3

from audio.tts_providers.base_tts import BaseTTSProvider, TTSResult
from core.logger import get_logger

logger = get_logger(__name__)


class Pyttsx3Provider(BaseTTSProvider):
    """Offline TTS using the system's native speech synthesizer."""

    def __init__(self):
        super().__init__(name="pyttsx3", default_voice="default")

    def is_available(self) -> bool:
        """Always available locally on Windows."""
        return True

    def synthesize(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        rate: float = 1.0,
        volume: float = 1.0,
    ) -> TTSResult:
        """Synthesizes text to a WAV/MP3 file via pyttsx3."""
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        engine = pyttsx3.init()
        try:
            # Set rate (default is ~200 WPM, scale by rate parameter)
            default_rate = engine.getProperty("rate")
            engine.setProperty("rate", int(default_rate * rate))

            # Set volume (0.0 to 1.0)
            engine.setProperty("volume", max(0.0, min(1.0, volume)))

            # Select voice if specified
            if voice and voice != "default":
                engine.setProperty("voice", voice)

            engine.save_to_file(text, str(out_file))
            engine.runAndWait()
        finally:
            engine.stop()

        words = len(text.split())
        duration_s = max(2.0, (words / 150.0) * 60.0)

        logger.info(f"Offline TTS synthesized {words} words to {out_file.name}")
        return TTSResult(
            audio_path=str(out_file),
            duration_s=duration_s,
            provider=self.name,
            voice=voice or "sapi5_default",
            word_timestamps=[],  # pyttsx3 doesn't produce word-level millisecond timestamps
        )

    def list_voices(self) -> List[Dict[str, str]]:
        """Lists local Windows voices."""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            return [{"voice": v.id, "label": v.name} for v in voices]
        except Exception:
            return []
