"""
AI-CONTENT-AUTOMATION — Microsoft Edge TTS Provider
=====================================================
Uses edge-tts for realistic, human-quality neural voices.
Provides exact word-level and sentence-level millisecond timestamps for animated subtitles.
100% Free, no API keys required.
"""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import edge_tts

from audio.tts_providers.base_tts import BaseTTSProvider, TTSResult, WordTimestamp
from config import config
from core.logger import get_logger

logger = get_logger(__name__)


# Curated list of popular, high-retention English voices
RECOMMENDED_VOICES = {
    "en-US-AriaNeural": "Aria (US Female — Expressive, energetic)",
    "en-US-GuyNeural": "Guy (US Male — Casual, conversational)",
    "en-US-ChristopherNeural": "Christopher (US Male — Deep, authoritative, storytelling)",
    "en-US-JennyNeural": "Jenny (US Female — Natural, friendly)",
    "en-GB-SoniaNeural": "Sonia (UK Female — Sophisticated)",
    "en-GB-RyanNeural": "Ryan (UK Male — Documentary style)",
    "en-IN-PrabhatNeural": "Prabhat (Indian English Male — Clear, articulate)",
}


class EdgeTTSProvider(BaseTTSProvider):
    """
    Microsoft Edge Neural TTS implementation.
    Captures audio bytes and derives accurate word-level and sentence-level timestamps.
    """

    def __init__(self):
        super().__init__(
            name="edge_tts",
            default_voice=config.tts.voice or "en-US-ChristopherNeural"
        )

    def is_available(self) -> bool:
        """Edge TTS is free and available whenever network is accessible."""
        return True

    def synthesize(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        rate: float = 1.0,
        volume: float = 1.0,
    ) -> TTSResult:
        """
        Synthesizes text to an MP3 file and collects timestamps synchronously.
        """
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        target_voice = voice or self.default_voice

        # Format rate string (e.g., +10% or -5%)
        rate_percent = int(round((rate - 1.0) * 100))
        rate_str = f"{rate_percent:+d}%" if rate_percent != 0 else "+0%"

        # Format volume string
        volume_percent = int(round((volume - 1.0) * 100))
        volume_str = f"{volume_percent:+d}%" if volume_percent != 0 else "+0%"

        logger.info(f"Synthesizing {len(text.split())} words with voice: {target_voice}")
        result = asyncio.run(self._async_synthesize(
            text=text,
            output_file=out_file,
            voice=target_voice,
            rate_str=rate_str,
            volume_str=volume_str,
        ))
        return result

    async def _async_synthesize(
        self,
        text: str,
        output_file: Path,
        voice: str,
        rate_str: str,
        volume_str: str,
    ) -> TTSResult:
        """Async implementation collecting audio chunks and boundary timing."""
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate_str,
            volume=volume_str,
        )

        word_timestamps: List[WordTimestamp] = []
        audio_chunks: List[bytes] = []

        async for chunk in communicate.stream():
            chunk_type = chunk.get("type", "")
            if chunk_type == "audio":
                audio_chunks.append(chunk["data"])
            elif chunk_type in ("WordBoundary", "word_boundary"):
                offset_ms = int(chunk["offset"] / 10000)
                dur_ms = int(chunk["duration"] / 10000)
                word = chunk["text"]
                word_timestamps.append(WordTimestamp(
                    word=word,
                    start_ms=offset_ms,
                    end_ms=offset_ms + dur_ms,
                ))
            elif chunk_type in ("SentenceBoundary", "sentence_boundary"):
                # Split sentence into words and distribute timing proportionally
                offset_ms = int(chunk["offset"] / 10000)
                dur_ms = int(chunk["duration"] / 10000)
                sentence_text = chunk.get("text", "")
                words = sentence_text.split()
                if words:
                    per_word_dur = max(150, int(dur_ms / len(words)))
                    current_start = offset_ms
                    for w in words:
                        word_timestamps.append(WordTimestamp(
                            word=w,
                            start_ms=current_start,
                            end_ms=current_start + per_word_dur,
                        ))
                        current_start += per_word_dur

        # Write audio data to disk
        with open(output_file, "wb") as f:
            for b in audio_chunks:
                f.write(b)

        # Calculate duration based on last timestamp or file estimate
        if word_timestamps:
            duration_s = word_timestamps[-1].end_ms / 1000.0
        else:
            duration_s = max(2.0, (len(text.split()) / 140.0) * 60.0)

        logger.info(f"Synthesized {duration_s:.2f}s of audio with {len(word_timestamps)} word timestamps.")

        return TTSResult(
            audio_path=str(output_file),
            duration_s=duration_s,
            provider=self.name,
            voice=voice,
            word_timestamps=word_timestamps,
            metadata={"file_size_bytes": output_file.stat().st_size}
        )

    def list_voices(self) -> List[Dict[str, str]]:
        """Returns recommended voices list."""
        return [
            {"voice": k, "label": v}
            for k, v in RECOMMENDED_VOICES.items()
        ]
