"""
AI-CONTENT-AUTOMATION — FFmpeg Video Rendering Engine
======================================================
Core video rendering pipeline supporting:
- Vertical 9:16 (1080x1920) for YouTube Shorts, Instagram Reels, and TikTok.
- Horizontal 16:9 (1920x1080) for regular YouTube videos.
- NVIDIA NVENC hardware GPU acceleration with automatic CPU fallback.
- Subtitle burning (ASS/SRT with safe path escaping on Windows).
- Audio mixing and background video looping/trimming.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, List, Tuple
from video.ffmpeg_locator import ffmpeg_locator
from core.logger import get_logger

logger = get_logger(__name__)


def escape_ffmpeg_filter_path(file_path: str) -> str:
    r"""
    Escapes a Windows file path for use in FFmpeg filter complex
    (subtitles/ass filter requires forward slashes and escaped colons).
    Example: 'C:\path\to\file.ass' -> 'C\\:/path/to/file.ass'
    """
    p = str(Path(file_path).resolve()).replace("\\", "/")
    # Escape the drive letter colon
    if len(p) >= 2 and p[1] == ":":
        p = p[0] + "\\:" + p[2:]
    return p


class VideoRenderer:
    """Coordinates FFmpeg encoding, cropping, and subtitle burning."""

    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "generated" / "videos" / "shorts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_short_video(
        self,
        visual_source: str,
        audio_path: str,
        output_path: str,
        subtitle_path: Optional[str] = None,
        duration_s: Optional[float] = None,
        width: int = 1080,
        height: int = 1920,
    ) -> Path:
        """
        Renders a finished 9:16 vertical short video:
        - Scales / crops visual source to 1080x1920
        - Loops or trims video to match audio duration
        - Burns styled ASS/SRT subtitles if provided
        - Uses GPU NVENC (or CPU fallback)
        """
        ffmpeg = ffmpeg_locator.get_ffmpeg_path()
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        encoder_name, encoder_flags = ffmpeg_locator.get_video_encoder()

        # Build video filter chain:
        # 1. Scale and crop to 9:16 (fill screen, center crop)
        filter_parts = [
            f"scale={width}:{height}:force_original_aspect_ratio=increase",
            f"crop={width}:{height}",
        ]

        # 2. Burn subtitles if supplied
        if subtitle_path and Path(subtitle_path).exists():
            escaped_sub = escape_ffmpeg_filter_path(subtitle_path)
            filter_parts.append(f"ass='{escaped_sub}'")

        vf_string = ",".join(filter_parts)

        cmd = [
            str(ffmpeg),
            "-y",
            # Loop video source if shorter than audio
            "-stream_loop", "-1",
            "-i", str(visual_source),
            "-i", str(audio_path),
            "-vf", vf_string,
            "-c:v", encoder_name,
            *encoder_flags,
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
        ]

        if duration_s:
            cmd.extend(["-t", str(duration_s)])

        cmd.append(str(out_file))

        logger.info(f"Rendering short video with encoder '{encoder_name}' to: {out_file.name}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode != 0:
                # If NVENC failed, retry with CPU libx264
                if encoder_name == "h264_nvenc":
                    logger.warning("NVENC failed, retrying with CPU libx264 fallback...")
                    return self._render_cpu_fallback(visual_source, audio_path, out_file, vf_string, duration_s)
                raise RuntimeError(f"FFmpeg render error: {res.stderr}")
        except Exception as e:
            logger.error(f"Render process exception: {e}")
            raise

        logger.info(f"Successfully rendered: {out_file.name} ({out_file.stat().st_size / (1024*1024):.2f} MB)")
        return out_file

    def _render_cpu_fallback(self, visual_source, audio_path, out_file, vf_string, duration_s) -> Path:
        """Safe CPU fallback using libx264."""
        ffmpeg = ffmpeg_locator.get_ffmpeg_path()
        cmd = [
            str(ffmpeg), "-y",
            "-stream_loop", "-1",
            "-i", str(visual_source),
            "-i", str(audio_path),
            "-vf", vf_string,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
        ]
        if duration_s:
            cmd.extend(["-t", str(duration_s)])
        cmd.append(str(out_file))

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if res.returncode != 0:
            raise RuntimeError(f"CPU Fallback FFmpeg render error: {res.stderr}")
        return out_file

    def generate_solid_background(
        self,
        duration_s: float,
        output_path: str,
        color: str = "black",
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> Path:
        """
        Generates a lightweight solid color MP4 video clip.
        Useful as a base track or test visual.
        """
        ffmpeg = ffmpeg_locator.get_ffmpeg_path()
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(ffmpeg), "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={width}x{height}:r={fps}",
            "-t", str(duration_s),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(out_file),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to generate solid background: {res.stderr}")

        return out_file


# Singleton instance
video_renderer = VideoRenderer()
