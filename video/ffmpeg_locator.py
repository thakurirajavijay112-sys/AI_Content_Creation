"""
AI-CONTENT-AUTOMATION — FFmpeg & GPU Locator
==============================================
Automatically discovers the FFmpeg binary and probes GPU NVENC capabilities.
Works out of the box with custom download paths, C:\ffmpeg, or system PATH.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from config import config
from core.logger import get_logger

logger = get_logger(__name__)

# Common candidate locations on Windows
COMMON_FFMPEG_PATHS = [
    Path("C:/Users/thaku/Downloads/ffmpeg-9.0.2-full_build/ffmpeg-9.0.2-full_build/bin"),
    Path("C:/ffmpeg/bin"),
    Path("C:/Program Files/ffmpeg/bin"),
]


class FFmpegLocator:
    """Detects FFmpeg, FFprobe, and hardware acceleration status."""

    def __init__(self):
        self._ffmpeg_path: Optional[Path] = None
        self._ffprobe_path: Optional[Path] = None
        self._has_nvenc: Optional[bool] = None

    def get_ffmpeg_path(self) -> Path:
        """Returns the verified absolute path to ffmpeg executable."""
        if self._ffmpeg_path and self._ffmpeg_path.exists():
            return self._ffmpeg_path

        # 1. Configured path
        if config.video.ffmpeg_path:
            p = Path(config.video.ffmpeg_path)
            if p.is_file() and p.exists():
                self._ffmpeg_path = p
                return p
            elif p.is_dir() and (p / "ffmpeg.exe").exists():
                self._ffmpeg_path = p / "ffmpeg.exe"
                return self._ffmpeg_path

        # 2. Check system PATH
        which_path = shutil.which("ffmpeg")
        if which_path:
            self._ffmpeg_path = Path(which_path)
            return self._ffmpeg_path

        # 3. Check common Windows paths
        for candidate in COMMON_FFMPEG_PATHS:
            exe = candidate / "ffmpeg.exe"
            if exe.exists():
                self._ffmpeg_path = exe
                logger.info(f"Discovered FFmpeg at: {exe}")
                return exe

        raise FileNotFoundError(
            "FFmpeg executable not found. Please install FFmpeg to C:\\ffmpeg\\bin "
            "or set FFMPEG_PATH in your .env file."
        )

    def get_ffprobe_path(self) -> Path:
        """Returns the verified absolute path to ffprobe executable."""
        if self._ffprobe_path and self._ffprobe_path.exists():
            return self._ffprobe_path

        ffmpeg = self.get_ffmpeg_path()
        probe_candidate = ffmpeg.parent / "ffprobe.exe"
        if probe_candidate.exists():
            self._ffprobe_path = probe_candidate
            return probe_candidate

        which_probe = shutil.which("ffprobe")
        if which_probe:
            self._ffprobe_path = Path(which_probe)
            return self._ffprobe_path

        return probe_candidate

    def supports_nvenc(self) -> bool:
        """Checks if the installed FFmpeg build and GPU support NVIDIA NVENC encoding."""
        if self._has_nvenc is not None:
            return self._has_nvenc

        try:
            ffmpeg = self.get_ffmpeg_path()
            result = subprocess.run(
                [str(ffmpeg), "-encoders"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Look for h264_nvenc
            self._has_nvenc = "h264_nvenc" in result.stdout
            if self._has_nvenc:
                logger.info("NVIDIA NVENC hardware video encoding is supported and active.")
            else:
                logger.info("NVENC not detected in FFmpeg build; CPU libx264 will be used.")
            return self._has_nvenc
        except Exception as e:
            logger.warning(f"Failed to probe NVENC: {e}")
            self._has_nvenc = False
            return False

    def get_video_encoder(self) -> Tuple[str, list]:
        """
        Returns the encoder name and recommended options based on hardware.
        Returns: ("h264_nvenc", ["-preset", "p4", "-cq", "24"]) or ("libx264", ["-preset", "fast", "-crf", "23"])
        """
        user_choice = config.video.encoder.lower()

        if user_choice in ("nvenc", "gpu") or (user_choice == "auto" and self.supports_nvenc()):
            return "h264_nvenc", ["-preset", "p4", "-cq", "24", "-pix_fmt", "yuv420p"]
        else:
            return "libx264", ["-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p"]


# Singleton
ffmpeg_locator = FFmpegLocator()
