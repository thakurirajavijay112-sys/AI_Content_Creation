"""
AI-CONTENT-AUTOMATION — Speech Transcription Engine
=====================================================
Transcribes audio into text and timestamped subtitle segments.
Supports:
1. OpenAI Whisper (local inference for external streamer/creator audio).
2. Direct alignment from Edge-TTS word boundaries (fast, zero-GPU overhead).
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from core.logger import get_logger
from config import config

logger = get_logger(__name__)


@dataclass
class SubtitleSegment:
    """Represents a timed subtitle segment."""
    start_s: float
    end_s: float
    text: str


class TranscriptionEngine:
    """Manages audio transcription and subtitle segment generation."""

    def __init__(self):
        self._whisper_model = None
        self.model_name = config.whisper.model or "base"
        self.device = config.whisper.device or "cuda"

    def is_whisper_available(self) -> bool:
        """Checks if whisper module is installed and functional."""
        try:
            import whisper
            return True
        except (ImportError, Exception):
            return False

    def transcribe_audio(
        self,
        audio_path: str,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> List[SubtitleSegment]:
        """
        Transcribes an audio or video file using local Whisper.
        Returns timed subtitle segments.
        """
        if not self.is_whisper_available():
            raise RuntimeError(
                "Whisper is not currently installed or available. "
                "For AI Shorts, word timestamps from TTS are used automatically."
            )

        import whisper
        import torch

        # Check CUDA availability
        device = "cuda" if (torch.cuda.is_available() and self.device == "cuda") else "cpu"
        target_model = model_name or self.model_name

        logger.info(f"Loading Whisper model '{target_model}' on device '{device}'...")
        if self._whisper_model is None or getattr(self._whisper_model, "_name", "") != target_model:
            self._whisper_model = whisper.load_model(target_model, device=device)
            self._whisper_model._name = target_model

        logger.info(f"Transcribing audio: {audio_path}")
        result = self._whisper_model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            fp16=(device == "cuda"),
        )

        segments: List[SubtitleSegment] = []
        for s in result.get("segments", []):
            start = float(s["start"])
            end = float(s["end"])
            text = str(s["text"]).strip()
            if text:
                segments.append(SubtitleSegment(start_s=start, end_s=end, text=text))

        logger.info(f"Generated {len(segments)} subtitle segments from transcription.")
        return segments

    @staticmethod
    def segments_from_word_timestamps(
        word_timestamps,
        words_per_segment: int = 4,
    ) -> List[SubtitleSegment]:
        """
        Converts word timestamps (e.g. from Edge-TTS) into dynamic, fast-paced
        Shorts subtitle chunks (3-4 words per line for high retention).
        """
        if not word_timestamps:
            return []

        segments: List[SubtitleSegment] = []
        current_words = []
        seg_start = word_timestamps[0].start_ms / 1000.0

        for i, wt in enumerate(word_timestamps):
            current_words.append(wt.word)
            
            # Close segment if max words reached or punctuation pause
            is_last = (i == len(word_timestamps) - 1)
            ends_with_punct = any(wt.word.endswith(p) for p in [".", "!", "?", ","])
            
            if len(current_words) >= words_per_segment or ends_with_punct or is_last:
                seg_end = wt.end_ms / 1000.0
                seg_text = " ".join(current_words).strip()
                if seg_text:
                    segments.append(SubtitleSegment(
                        start_s=seg_start,
                        end_s=seg_end,
                        text=seg_text
                    ))
                current_words = []
                if not is_last:
                    seg_start = word_timestamps[i + 1].start_ms / 1000.0

        return segments


# Singleton instance
transcription_engine = TranscriptionEngine()
