"""
AI-CONTENT-AUTOMATION — Audio Processor
=========================================
Handles audio mixing, volume normalization, and background music ducking directly via FFmpeg.
Zero dependency on deprecated Python audioop/pydub libraries.
Fast, reliable, and native.
"""

import subprocess
from pathlib import Path
from typing import Optional
from video.ffmpeg_locator import ffmpeg_locator
from core.logger import get_logger

logger = get_logger(__name__)


class AudioProcessor:
    """Manages audio normalization, mixing, and background music ducking using FFmpeg."""

    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "generated" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def mix_narration_and_music(
        self,
        narration_path: str,
        music_path: Optional[str],
        output_path: str,
        music_volume: float = 0.12,  # 12% volume for background music (~ -18 dB)
        fade_out_s: float = 1.5,
    ) -> Path:
        """
        Mixes voiceover narration with background music using FFmpeg's amix filter.
        Ducks music to music_volume so narration is crisp and loud.
        Ends exactly when narration ends (duration=first).
        """
        ffmpeg = ffmpeg_locator.get_ffmpeg_path()
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        narr_p = Path(narration_path).resolve()
        if not music_path or not Path(music_path).exists():
            # If no music, copy/convert narration directly
            cmd = [
                str(ffmpeg), "-y",
                "-i", str(narr_p),
                "-c:a", "libmp3lame",
                "-q:a", "2",
                str(out_file),
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return out_file

        music_p = Path(music_path).resolve()

        # FFmpeg filter:
        # [0:a] is narration (volume=1.0)
        # [1:a] is looped music (volume lowered to ducking level)
        # amix mixes both, duration=first ensures output stops when narration stops
        filter_complex = (
            f"[0:a]volume=1.0[voice];"
            f"[1:a]volume={music_volume}[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2[out]"
        )

        cmd = [
            str(ffmpeg), "-y",
            "-i", str(narr_p),
            "-stream_loop", "-1",
            "-i", str(music_p),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "libmp3lame",
            "-q:a", "2",
            str(out_file),
        ]

        logger.info(f"Mixing narration and music via FFmpeg: {out_file.name}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            logger.error(f"FFmpeg audio mixing error: {res.stderr}")
            raise RuntimeError(f"Audio mixing failed: {res.stderr}")

        return out_file

    def get_audio_duration_seconds(self, audio_path: str) -> float:
        """Measures exact duration of an audio or video file via ffprobe."""
        ffprobe = ffmpeg_locator.get_ffprobe_path()
        cmd = [
            str(ffprobe),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            try:
                return float(res.stdout.strip())
            except ValueError:
                pass
        return 0.0


# Singleton instance
audio_processor = AudioProcessor()
