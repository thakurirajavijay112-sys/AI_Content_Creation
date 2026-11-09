"""
AI-CONTENT-AUTOMATION — Multi-Language & Voice Registry
========================================================
Supports 8 global languages for script generation, voiceover synthesis, and subtitles:
- English (en)
- Hindi (hi)
- Nepali (ne)
- Portuguese (pt)
- Spanish (es)
- Mandarin (zh)
- Japanese (ja)
- Arabic (ar)
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class VoiceOption:
    code: str
    label: str
    gender: str


@dataclass
class LanguageProfile:
    code: str
    name: str
    native_name: str
    default_voice: str
    voices: List[VoiceOption]
    font_name: str = "Segoe UI"


SUPPORTED_LANGUAGES: Dict[str, LanguageProfile] = {
    "en": LanguageProfile(
        code="en",
        name="English",
        native_name="English",
        default_voice="en-US-AndrewMultilingualNeural",
        voices=[
            VoiceOption("en-US-AndrewMultilingualNeural", "🎙 Andrew — Dynamic & Energetic Male", "Male"),
            VoiceOption("en-US-AvaMultilingualNeural", "🎙 Ava — Natural & Warm Female", "Female"),
            VoiceOption("en-US-BrianMultilingualNeural", "🎙 Brian — Deep & Rich Storyteller Male", "Male"),
            VoiceOption("en-GB-RyanNeural", "🎙 Ryan — Charismatic British Storyteller", "Male"),
        ],
        font_name="Segoe UI",
    ),
    "hi": LanguageProfile(
        code="hi",
        name="Hindi",
        native_name="हिन्दी",
        default_voice="hi-IN-MadhurNeural",
        voices=[
            VoiceOption("hi-IN-MadhurNeural", "🎙 Madhur — Natural Indian Male (मधुर)", "Male"),
            VoiceOption("hi-IN-SwaraNeural", "🎙 Swara — Expressive Indian Female (स्वरा)", "Female"),
        ],
        font_name="Nirmala UI",
    ),
    "ne": LanguageProfile(
        code="ne",
        name="Nepali",
        native_name="नेपाली",
        default_voice="ne-NP-SagarNeural",
        voices=[
            VoiceOption("ne-NP-SagarNeural", "🎙 Sagar — Clear Storyteller Male (सागर)", "Male"),
            VoiceOption("ne-NP-HemkalaNeural", "🎙 Hemkala — Warm Storyteller Female (हेमकला)", "Female"),
        ],
        font_name="Nirmala UI",
    ),
    "pt": LanguageProfile(
        code="pt",
        name="Portuguese",
        native_name="Português",
        default_voice="pt-BR-AntonioNeural",
        voices=[
            VoiceOption("pt-BR-AntonioNeural", "🎙 Antonio — Natural Storyteller Male (Brasil)", "Male"),
            VoiceOption("pt-BR-ThalitaMultilingualNeural", "🎙 Thalita — Dynamic Female (Brasil)", "Female"),
        ],
        font_name="Segoe UI",
    ),
    "es": LanguageProfile(
        code="es",
        name="Spanish",
        native_name="Español",
        default_voice="es-ES-AlvaroNeural",
        voices=[
            VoiceOption("es-ES-AlvaroNeural", "🎙 Alvaro — Cinematic Storyteller Male (España)", "Male"),
            VoiceOption("es-ES-XimenaNeural", "🎙 Ximena — Natural Female (España)", "Female"),
            VoiceOption("es-MX-JorgeNeural", "🎙 Jorge — Vibrant Latin American Male (México)", "Male"),
        ],
        font_name="Segoe UI",
    ),
    "zh": LanguageProfile(
        code="zh",
        name="Mandarin Chinese",
        native_name="中文 / 普通话",
        default_voice="zh-CN-YunxiNeural",
        voices=[
            VoiceOption("zh-CN-YunxiNeural", "🎙 Yunxi — Expressive Narrative Male (云希)", "Male"),
            VoiceOption("zh-CN-XiaoxiaoNeural", "🎙 Xiaoxiao — Warm Narrative Female (晓晓)", "Female"),
        ],
        font_name="Microsoft YaHei",
    ),
    "ja": LanguageProfile(
        code="ja",
        name="Japanese",
        native_name="日本語",
        default_voice="ja-JP-KeitaNeural",
        voices=[
            VoiceOption("ja-JP-KeitaNeural", "🎙 Keita — Storyteller Male (けいた)", "Male"),
            VoiceOption("ja-JP-NanamiNeural", "🎙 Nanami — Clear Female (ななみ)", "Female"),
        ],
        font_name="Meiryo",
    ),
    "ar": LanguageProfile(
        code="ar",
        name="Arabic",
        native_name="العربية",
        default_voice="ar-SA-HamedNeural",
        voices=[
            VoiceOption("ar-SA-HamedNeural", "🎙 Hamed — Resonant Storyteller Male (حامد)", "Male"),
            VoiceOption("ar-SA-ZariyahNeural", "🎙 Zariyah — Natural Female (زارية)", "Female"),
        ],
        font_name="Segoe UI",
    ),
}


class LanguageManager:
    """Provides language metadata, voice lookup, and script localization helpers."""

    @staticmethod
    def get_profile(code: str) -> LanguageProfile:
        return SUPPORTED_LANGUAGES.get(code, SUPPORTED_LANGUAGES["en"])

    @staticmethod
    def list_languages() -> List[Dict[str, str]]:
        return [
            {"code": code, "name": f"{p.name} ({p.native_name})"}
            for code, p in SUPPORTED_LANGUAGES.items()
        ]

    @staticmethod
    def get_voices_for_language(code: str) -> List[VoiceOption]:
        profile = LanguageManager.get_profile(code)
        return profile.voices
