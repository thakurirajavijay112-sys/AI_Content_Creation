"""
AI-CONTENT-AUTOMATION — Central Configuration
==============================================
Loads all settings from environment variables (.env file).
Never hardcodes credentials. All secrets come from .env.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

# ── Locate project root and load .env ────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # Allow running with environment variables set externally
    load_dotenv()


# ── Helper functions ──────────────────────────────────────────────────────────

def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()

def _get_bool(key: str, default: bool = False) -> bool:
    val = _get(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")

def _get_int(key: str, default: int = 0) -> int:
    try:
        return int(_get(key, str(default)))
    except ValueError:
        return default

def _get_float(key: str, default: float = 1.0) -> float:
    try:
        return float(_get(key, str(default)))
    except ValueError:
        return default

def _get_list(key: str, default: str = "", separator: str = ",") -> List[str]:
    val = _get(key, default)
    return [item.strip() for item in val.split(separator) if item.strip()]


# ── App Settings ──────────────────────────────────────────────────────────────

@dataclass
class AppConfig:
    name: str = field(default_factory=lambda: _get("APP_NAME", "AI-CONTENT-AUTOMATION"))
    env: str = field(default_factory=lambda: _get("APP_ENV", "development"))
    debug: bool = field(default_factory=lambda: _get_bool("DEBUG", True))
    log_level: str = field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))
    timezone: str = field(default_factory=lambda: _get("TIMEZONE", "Asia/Kathmandu"))
    project_root: Path = PROJECT_ROOT


# ── Database ──────────────────────────────────────────────────────────────────

@dataclass
class DatabaseConfig:
    path: Path = field(
        default_factory=lambda: PROJECT_ROOT / _get("DATABASE_PATH", "database/ai_content.db")
    )

    @property
    def url(self) -> str:
        return f"sqlite:///{self.path}"


# ── AI Providers ─────────────────────────────────────────────────────────────

@dataclass
class GeminiConfig:
    api_key: str = field(default_factory=lambda: _get("GEMINI_API_KEY"))
    default_model: str = field(default_factory=lambda: _get("GEMINI_DEFAULT_MODEL", "gemini-3.5-flash"))
    pro_model: str = field(default_factory=lambda: _get("GEMINI_PRO_MODEL", "gemini-3.5-flash-lite"))
    daily_limit: int = field(default_factory=lambda: _get_int("GEMINI_DAILY_REQUEST_LIMIT", 1400))

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and self.api_key != "your_gemini_api_key_here"


@dataclass
class OllamaConfig:
    base_url: str = field(default_factory=lambda: _get("OLLAMA_BASE_URL", "http://localhost:11434"))
    default_model: str = field(default_factory=lambda: _get("OLLAMA_DEFAULT_MODEL", "llama3.2:3b"))
    enabled: bool = field(default_factory=lambda: _get_bool("OLLAMA_ENABLED", True))


@dataclass
class AIConfig:
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    provider_priority: List[str] = field(
        default_factory=lambda: _get_list("AI_PROVIDER_PRIORITY", "gemini,ollama")
    )


# ── Voice / TTS ───────────────────────────────────────────────────────────────

@dataclass
class TTSConfig:
    provider: str = field(default_factory=lambda: _get("TTS_PROVIDER", "edge_tts"))
    voice: str = field(default_factory=lambda: _get("TTS_VOICE", "en-US-AriaNeural"))
    speed: float = field(default_factory=lambda: _get_float("TTS_SPEED", 1.0))
    volume: float = field(default_factory=lambda: _get_float("TTS_VOLUME", 1.0))


# ── Whisper ───────────────────────────────────────────────────────────────────

@dataclass
class WhisperConfig:
    model: str = field(default_factory=lambda: _get("WHISPER_MODEL", "medium"))
    device: str = field(default_factory=lambda: _get("WHISPER_DEVICE", "cuda"))
    language: str = field(default_factory=lambda: _get("WHISPER_LANGUAGE", "en"))


# ── Video / FFmpeg ────────────────────────────────────────────────────────────

@dataclass
class VideoConfig:
    ffmpeg_path: Optional[str] = field(
        default_factory=lambda: _get("FFMPEG_PATH") or None
    )
    ffprobe_path: Optional[str] = field(
        default_factory=lambda: _get("FFPROBE_PATH") or None
    )
    encoder: str = field(default_factory=lambda: _get("VIDEO_ENCODER", "auto"))
    crf: int = field(default_factory=lambda: _get_int("VIDEO_CRF", 23))
    preset: str = field(default_factory=lambda: _get("VIDEO_PRESET", "medium"))


# ── Scheduler ─────────────────────────────────────────────────────────────────

@dataclass
class SchedulerConfig:
    enabled: bool = field(default_factory=lambda: _get_bool("SCHEDULER_ENABLED", True))
    time_1: str = field(default_factory=lambda: _get("SCHEDULE_TIME_1", "08:00"))
    time_2: str = field(default_factory=lambda: _get("SCHEDULE_TIME_2", "14:00"))
    time_3: str = field(default_factory=lambda: _get("SCHEDULE_TIME_3", "20:00"))
    daily_limit: int = field(default_factory=lambda: _get_int("DAILY_VIDEO_LIMIT", 3))
    manual_approval: bool = field(
        default_factory=lambda: _get_bool("MANUAL_APPROVAL_REQUIRED", False)
    )


# ── Publishing Platforms ───────────────────────────────────────────────────────

@dataclass
class YouTubeConfig:
    client_id: str = field(default_factory=lambda: _get("YOUTUBE_CLIENT_ID"))
    client_secret: str = field(default_factory=lambda: _get("YOUTUBE_CLIENT_SECRET"))
    redirect_uri: str = field(default_factory=lambda: _get("YOUTUBE_REDIRECT_URI", "http://localhost:8080/oauth2callback"))
    enabled: bool = field(default_factory=lambda: _get_bool("YOUTUBE_ENABLED", False))

    @property
    def is_configured(self) -> bool:
        return (
            bool(self.client_id) and self.client_id != "your_youtube_client_id"
            and bool(self.client_secret)
        )


@dataclass
class MetaConfig:
    app_id: str = field(default_factory=lambda: _get("META_APP_ID"))
    app_secret: str = field(default_factory=lambda: _get("META_APP_SECRET"))
    access_token: str = field(default_factory=lambda: _get("META_ACCESS_TOKEN"))
    instagram_enabled: bool = field(default_factory=lambda: _get_bool("INSTAGRAM_ENABLED", False))
    facebook_enabled: bool = field(default_factory=lambda: _get_bool("FACEBOOK_ENABLED", False))

    @property
    def is_configured(self) -> bool:
        return bool(self.app_id) and self.app_id != "your_meta_app_id"


@dataclass
class TikTokConfig:
    client_key: str = field(default_factory=lambda: _get("TIKTOK_CLIENT_KEY"))
    client_secret: str = field(default_factory=lambda: _get("TIKTOK_CLIENT_SECRET"))
    enabled: bool = field(default_factory=lambda: _get_bool("TIKTOK_ENABLED", False))

    @property
    def is_configured(self) -> bool:
        return bool(self.client_key) and self.client_key != "your_tiktok_client_key"


@dataclass
class SnapchatConfig:
    client_id: str = field(default_factory=lambda: _get("SNAPCHAT_CLIENT_ID"))
    client_secret: str = field(default_factory=lambda: _get("SNAPCHAT_CLIENT_SECRET"))
    enabled: bool = field(default_factory=lambda: _get_bool("SNAPCHAT_ENABLED", False))


@dataclass
class TwitchConfig:
    client_id: str = field(default_factory=lambda: _get("TWITCH_CLIENT_ID"))
    client_secret: str = field(default_factory=lambda: _get("TWITCH_CLIENT_SECRET"))
    redirect_uri: str = field(default_factory=lambda: _get("TWITCH_REDIRECT_URI", "http://localhost:8080/twitch/callback"))
    enabled: bool = field(default_factory=lambda: _get_bool("TWITCH_ENABLED", False))

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id) and self.client_id != "your_twitch_client_id"


@dataclass
class KickConfig:
    stream_key: str = field(default_factory=lambda: _get("KICK_STREAM_KEY"))
    enabled: bool = field(default_factory=lambda: _get_bool("KICK_ENABLED", False))


@dataclass
class PublishingConfig:
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)
    meta: MetaConfig = field(default_factory=MetaConfig)
    tiktok: TikTokConfig = field(default_factory=TikTokConfig)
    snapchat: SnapchatConfig = field(default_factory=SnapchatConfig)
    twitch: TwitchConfig = field(default_factory=TwitchConfig)
    kick: KickConfig = field(default_factory=KickConfig)


# ── Stock Footage APIs ────────────────────────────────────────────────────────

@dataclass
class StockConfig:
    pexels_api_key: str = field(default_factory=lambda: _get("PEXELS_API_KEY"))
    pixabay_api_key: str = field(default_factory=lambda: _get("PIXABAY_API_KEY"))

    @property
    def pexels_configured(self) -> bool:
        return bool(self.pexels_api_key) and self.pexels_api_key != "your_pexels_api_key"

    @property
    def pixabay_configured(self) -> bool:
        return bool(self.pixabay_api_key) and self.pixabay_api_key != "your_pixabay_api_key"


# ── Dashboard ─────────────────────────────────────────────────────────────────

@dataclass
class DashboardConfig:
    host: str = field(default_factory=lambda: _get("DASHBOARD_HOST", "localhost"))
    port: int = field(default_factory=lambda: _get_int("DASHBOARD_PORT", 8501))
    secret_key: str = field(
        default_factory=lambda: _get("DASHBOARD_SECRET_KEY", "change_me_in_production")
    )


# ── Engine Configs ────────────────────────────────────────────────────────────

@dataclass
class ShortsConfig:
    default_duration: int = field(default_factory=lambda: _get_int("SHORTS_DEFAULT_DURATION", 45))
    max_duration: int = field(default_factory=lambda: _get_int("SHORTS_MAX_DURATION", 60))
    min_duration: int = field(default_factory=lambda: _get_int("SHORTS_MIN_DURATION", 30))
    categories: List[str] = field(
        default_factory=lambda: _get_list(
            "SHORTS_CATEGORIES",
            "amazing_facts,motivation,ai_technology,horror_stories,football_facts,cricket_facts"
        )
    )


@dataclass
class ClipperConfig:
    default_duration: int = field(default_factory=lambda: _get_int("CLIP_DEFAULT_DURATION", 35))
    min_duration: int = field(default_factory=lambda: _get_int("CLIP_MIN_DURATION", 20))
    max_duration: int = field(default_factory=lambda: _get_int("CLIP_MAX_DURATION", 60))
    min_score: int = field(default_factory=lambda: _get_int("CLIP_MIN_SCORE", 50))


@dataclass
class YouTuberEngineConfig:
    shorts_duration: int = field(default_factory=lambda: _get_int("YOUTUBER_SHORTS_DURATION", 45))
    longform_min: int = field(default_factory=lambda: _get_int("YOUTUBER_LONGFORM_MIN_DURATION", 300))
    longform_max: int = field(default_factory=lambda: _get_int("YOUTUBER_LONGFORM_MAX_DURATION", 600))


# ── Master Config ─────────────────────────────────────────────────────────────

@dataclass
class Config:
    """
    Single entry point for all application configuration.
    Usage:
        from config import config
        api_key = config.ai.gemini.api_key
    """
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    publishing: PublishingConfig = field(default_factory=PublishingConfig)
    stock: StockConfig = field(default_factory=StockConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    shorts: ShortsConfig = field(default_factory=ShortsConfig)
    clipper: ClipperConfig = field(default_factory=ClipperConfig)
    youtuber: YouTuberEngineConfig = field(default_factory=YouTuberEngineConfig)

    def validate(self) -> list[str]:
        """
        Returns a list of warnings for missing or unconfigured settings.
        Does NOT raise exceptions — just informs the user.
        """
        warnings = []
        if not self.ai.gemini.is_configured:
            warnings.append("Gemini API key not configured. AI features will use Ollama only.")
        if not self.publishing.youtube.is_configured:
            warnings.append("YouTube credentials not configured. YouTube publishing disabled.")
        if not self.stock.pexels_configured:
            warnings.append("Pexels API key not set. Stock footage search disabled.")
        if not self.stock.pixabay_configured:
            warnings.append("Pixabay API key not set. Stock image search disabled.")
        return warnings

    def summary(self) -> dict:
        """Returns a human-readable config summary (safe — no secrets)."""
        return {
            "app": self.app.name,
            "env": self.app.env,
            "ai_providers": self.ai.provider_priority,
            "gemini_configured": self.ai.gemini.is_configured,
            "ollama_enabled": self.ai.ollama.enabled,
            "tts_provider": self.tts.provider,
            "whisper_model": self.whisper.model,
            "scheduler_enabled": self.scheduler.enabled,
            "daily_limit": self.scheduler.daily_limit,
            "youtube_enabled": self.publishing.youtube.enabled,
            "instagram_enabled": self.publishing.meta.instagram_enabled,
            "tiktok_enabled": self.publishing.tiktok.enabled,
            "dashboard_port": self.dashboard.port,
        }


# ── Singleton instance ────────────────────────────────────────────────────────
config = Config()
