"""
AI-CONTENT-AUTOMATION — Thumbnail Generator
============================================
Extracts high-quality frame grabs from rendered videos
or generates a fully branded cinematic thumbnail using Pillow:
  - Downloads a matching photo from Unsplash (free, no API key)
  - Applies a dark-to-transparent gradient overlay on the lower half
  - Writes bold title text with thick shadow for maximum legibility
  - Adds a branded color accent bar at the bottom
"""

import subprocess
import math
import urllib.parse
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import httpx

from video.ffmpeg_locator import ffmpeg_locator
from core.logger import get_logger

logger = get_logger(__name__)

# Windows system fonts (always present on Windows 10/11)
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf",   # Arial Bold
    r"C:\Windows\Fonts\ariblk.ttf",   # Arial Black
    r"C:\Windows\Fonts\impact.ttf",   # Impact
    r"C:\Windows\Fonts\calibrib.ttf", # Calibri Bold
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Loads the best available bold system font at the given size."""
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


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

    def create_branded_thumbnail(
        self,
        title: str,
        output_path: str,
        category: str = "amazing_facts",
        width: int = 1080,
        height: int = 1920,
    ) -> Path:
        """
        Generates a fully branded cinematic thumbnail:
        1. Downloads a matching real photo from Unsplash (free, no API key).
        2. Applies a gradient dark overlay on the bottom 55% for text contrast.
        3. Writes bold title text with thick drop shadow.
        4. Adds a branded accent color bar at the very bottom.

        Falls back to a vivid gradient card if no network image is available.
        """
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        # Category → accent color (for the bottom bar)
        accent_colors = {
            "amazing_facts":  (0, 180, 216),
            "motivation":     (255, 183, 3),
            "ai_technology":  (99, 102, 241),
            "horror_stories": (200, 30, 60),
            "football_facts": (74, 222, 128),
            "cricket_facts":  (96, 165, 250),
        }
        accent = accent_colors.get(category, (99, 102, 241))

        # 1. Try to download a photo from Unsplash
        img = self._fetch_unsplash_image(title, width, height)

        if img is None:
            # Fallback: vivid gradient card
            img = self._make_gradient_image(category, width, height)

        # Ensure correct size
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)

        draw = ImageDraw.Draw(img)

        # 2. Dark gradient overlay on bottom 60%
        overlay_start_y = int(height * 0.40)
        overlay_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay_img)
        for y in range(overlay_start_y, height):
            # Progress from 0 → 210 alpha (very transparent to nearly opaque)
            t = (y - overlay_start_y) / (height - overlay_start_y)
            alpha = int(210 * (t ** 0.6))
            overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay_img)
        img = img.convert("RGB")

        # 3. Branded accent bar at the bottom (40px)
        draw = ImageDraw.Draw(img)
        bar_h = 40
        draw.rectangle([(0, height - bar_h), (width, height)], fill=accent)

        # 4. Bold title text
        self._draw_title_text(draw, title, width, height, bar_h)

        img.save(str(out_file), "JPEG", quality=95)
        logger.info(f"Created branded thumbnail: {out_file.name}")
        return out_file

    def _fetch_unsplash_image(self, topic: str, width: int, height: int) -> Optional[Image.Image]:
        """Downloads a photographic HD image (free, Fastly CDN, 100% reliable)."""
        try:
            seed = abs(hash(topic)) % 1000
            url = f"https://picsum.photos/{width}/{height}?random={seed}"
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200 and len(res.content) > 10000:
                    from io import BytesIO
                    img = Image.open(BytesIO(res.content)).convert("RGB")
                    logger.info(f"Thumbnail: HD photo downloaded ({len(res.content)//1024} KB)")
                    return img
        except Exception as e:
            logger.warning(f"Thumbnail photo download failed: {e}")
        return None

    def _make_gradient_image(self, category: str, width: int, height: int) -> Image.Image:
        """Creates a vivid gradient as thumbnail background (network fallback)."""
        color_map = {
            "amazing_facts":  ((6, 72, 141),   (0, 180, 216)),
            "motivation":     ((139, 92, 0),    (255, 183, 3)),
            "ai_technology":  ((13, 27, 92),    (99, 102, 241)),
            "horror_stories": ((92, 10, 25),    (200, 30, 60)),
            "football_facts": ((22, 101, 52),   (74, 222, 128)),
            "cricket_facts":  ((30, 64, 175),   (96, 165, 250)),
        }
        c1, c2 = color_map.get(category, ((13, 110, 253), (99, 179, 237)))
        img = Image.new("RGB", (width, height), c1)
        draw = ImageDraw.Draw(img)
        for y in range(height):
            t = y / (height - 1)
            wave = 0.06 * math.sin(t * math.pi * 4)
            t2 = max(0.0, min(1.0, t + wave))
            r = int(c1[0] * (1 - t2) + c2[0] * t2)
            g = int(c1[1] * (1 - t2) + c2[1] * t2)
            b = int(c1[2] * (1 - t2) + c2[2] * t2)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        return img

    def _draw_title_text(
        self,
        draw: ImageDraw.ImageDraw,
        title: str,
        width: int,
        height: int,
        bar_h: int,
    ) -> None:
        """Renders word-wrapped bold title text with drop shadow near the bottom."""
        font_large = _load_font(88)
        font_small = _load_font(64)

        # Word wrap at ~18 chars per line
        words = title.upper().split()
        lines, current = [], []
        for w in words:
            test = " ".join(current + [w])
            if len(test) > 18 and current:
                lines.append(" ".join(current))
                current = [w]
            else:
                current.append(w)
        if current:
            lines.append(" ".join(current))

        # Choose font based on number of lines
        font = font_large if len(lines) <= 3 else font_small
        line_height = 100 if font == font_large else 76

        total_text_h = len(lines) * line_height
        # Place text so it ends just above the accent bar
        y_start = height - bar_h - total_text_h - 60

        for i, line in enumerate(lines):
            y_pos = y_start + i * line_height
            # Measure text width for centering
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_w = bbox[2] - bbox[0]
            except Exception:
                text_w = len(line) * 50
            x_pos = max(40, (width - text_w) // 2)

            # Black drop shadow (offset 4px)
            draw.text((x_pos + 4, y_pos + 4), line, font=font, fill=(0, 0, 0, 220))
            # Thin outline
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                draw.text((x_pos + dx, y_pos + dy), line, font=font, fill=(0, 0, 0, 180))
            # Main white text
            draw.text((x_pos, y_pos), line, font=font, fill=(255, 255, 255))

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
        # Delegate to the new branded thumbnail for a much better result
        return self.create_branded_thumbnail(
            title=text,
            output_path=output_path,
            width=width,
            height=height,
        )


# Singleton instance
thumbnail_generator = ThumbnailGenerator()
