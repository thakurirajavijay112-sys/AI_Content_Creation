"""
AI-CONTENT-AUTOMATION — Thumbnail Generator
============================================
Extracts high-quality frame grabs from rendered videos
or overlays bold title typography onto images using Pillow and FFmpeg.
"""

import subprocess
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from video.ffmpeg_locator import ffmpeg_locator
from core.logger import get_logger

logger = get_logger(__name__)


class ThumbnailGenerator:
    """Creates thumbnails for Shorts (9:16) and YouTube videos (16:9)."""

    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "generated" / "thumbnails"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_frame_from_video(
        self,
        video_path: str,
        output_path: str,
        timestamp_s: float = 2.0,
    ) -> Path:
        """
        Extracts a clean frame from video at the specified timestamp using FFmpeg.
        """
        ffmpeg = ffmpeg_locator.get_ffmpeg_path()
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(ffmpeg),
            "-y",
            "-ss", str(timestamp_s),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(out_file),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            logger.error(f"Failed to extract thumbnail frame: {res.stderr}")
            raise RuntimeError(f"Thumbnail extraction failed: {res.stderr}")

        logger.info(f"Extracted thumbnail frame: {out_file.name}")
        return out_file

    def create_color_card(
        self,
        text: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920,
        bg_color: tuple = (18, 22, 35),
        text_color: tuple = (255, 235, 59),
    ) -> Path:
        """
        Generates a standalone branded poster card with centered typography.
        Useful for placeholder visuals and cover images.
        """
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Word wrap text for card
        words = text.split()
        lines = []
        current = []
        for w in words:
            current.append(w)
            if len(" ".join(current)) > 20:
                lines.append(" ".join(current))
                current = []
        if current:
            lines.append(" ".join(current))

        wrapped_text = "\n".join(lines)
        draw.text((width // 2, height // 2), wrapped_text, fill=text_color, anchor="mm")
        img.save(str(out_file), "JPEG", quality=95)

        logger.info(f"Created color card thumbnail: {out_file.name}")
        return out_file


# Singleton instance
thumbnail_generator = ThumbnailGenerator()
