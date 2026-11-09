"""
AI-CONTENT-AUTOMATION — Subtitle Generator
============================================
Produces styled, high-impact vertical subtitles in both:
1. Standard SRT format.
2. Animated/Styled ASS (Advanced SubStation Alpha) format for FFmpeg burning.

Features:
- Vertical 9:16 safe area positioning (avoids platform UI buttons).
- Bold font with heavy black outline for 100% legibility on any footage.
- Dynamic word-highlighting color styling.
"""

from pathlib import Path
from typing import List, Optional
from audio.transcription import SubtitleSegment
from audio.tts_providers.base_tts import WordTimestamp
from core.logger import get_logger

logger = get_logger(__name__)


def format_srt_time(seconds: float) -> str:
    """Formats float seconds into SRT timestamp HH:MM:SS,mmm"""
    millis = int(round((seconds - int(seconds)) * 1000))
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_ass_time(seconds: float) -> str:
    """Formats float seconds into ASS timestamp H:MM:SS.cc"""
    centis = int(round((seconds - int(seconds)) * 100))
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:01d}:{minutes:02d}:{secs:02d}.{min(centis, 99):02d}"


class SubtitleGenerator:
    """Generates SRT and ASS subtitle files."""

    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "generated" / "subtitles"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_srt(self, segments: List[SubtitleSegment], output_path: str) -> Path:
        """Writes standard SRT subtitle file."""
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        for i, seg in enumerate(segments, 1):
            start = format_srt_time(seg.start_s)
            end = format_srt_time(seg.end_s)
            lines.append(f"{i}\n{start} --> {end}\n{seg.text.upper()}\n")

        out_file.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Saved SRT subtitles: {out_file.name}")
        return out_file

    def generate_styled_ass(
        self,
        segments: List[SubtitleSegment],
        output_path: str,
        font_name: str = "Arial",
        font_size: int = 54,
        primary_color: str = "&H0000FFFF",  # Bright Yellow in BGR hex
        outline_color: str = "&H00000000",  # Solid Black
        outline_width: int = 4,
        margin_v: int = 320,  # Vertical margin from bottom (safe area for Shorts)
    ) -> Path:
        """
        Generates Advanced SubStation Alpha (.ass) file with modern vertical styling:
        - Centered at the bottom (Alignment=2)
        - Heavy outline to ensure contrast against any background
        - High-visibility yellow primary text
        """
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortsStyle,{font_name},{font_size},{primary_color},&H00000000,{outline_color},&H80000000,-1,0,0,0,100,100,1,0,1,{outline_width},2,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for seg in segments:
            start = format_ass_time(seg.start_s)
            end = format_ass_time(seg.end_s)
            # Render text in uppercase for viral short visual impact
            text = seg.text.upper().replace("\n", " ")
            events.append(f"Dialogue: 0,{start},{end},ShortsStyle,,0,0,0,,{text}")

        full_content = header + "\n".join(events) + "\n"
        out_file.write_text(full_content, encoding="utf-8")
        logger.info(f"Saved styled ASS subtitles: {out_file.name}")
        return out_file


# Singleton instance
subtitle_generator = SubtitleGenerator()
