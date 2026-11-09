"""
AI-CONTENT-AUTOMATION — Engine 1: Category Manager
====================================================
Defines style guides, visual themes, color palettes, and music preferences
for all 6 original Shorts categories:
1. Amazing Facts & Mysteries
2. Motivation & Success
3. AI & Technology
4. Horror & Scary Stories
5. Football (Soccer) Facts
6. Cricket Facts
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class CategoryProfile:
    """Style and audio-visual profile for a content category."""
    name: str
    display_title: str
    description: str
    recommended_voice: str
    subtitle_primary_color: str   # ASS format BGR hex
    subtitle_outline_color: str   # ASS format BGR hex
    theme_bg_color: str           # FFmpeg color name or hex
    visual_keywords: List[str]
    pacing_wpm: int = 145         # Words per minute target


CATEGORY_PROFILES: Dict[str, CategoryProfile] = {
    "amazing_facts": CategoryProfile(
        name="amazing_facts",
        display_title="Amazing Facts & Mysteries",
        description="Fascinating scientific curiosities, deep sea anomalies, and unexplained historical phenomena.",
        recommended_voice="en-US-ChristopherNeural",  # Authoritative, cinematic
        subtitle_primary_color="&H0000FFFF",          # Bright Yellow
        subtitle_outline_color="&H00000000",          # Solid Black
        theme_bg_color="navy",
        visual_keywords=["deep ocean", "space stars galaxy", "microscopic science", "ancient artifact", "satellite earth"],
        pacing_wpm=145,
    ),
    "motivation": CategoryProfile(
        name="motivation",
        display_title="Motivation & Success",
        description="High-energy discipline lessons, psychological resilience, and peak performance principles.",
        recommended_voice="en-US-GuyNeural",          # Gritty, direct
        subtitle_primary_color="&H0000D7FF",          # Bright Gold
        subtitle_outline_color="&H00000000",          # Solid Black
        theme_bg_color="black",
        visual_keywords=["running sunrise athlete", "gym training heavy", "mountain summit climb", "focused writing desk", "boxing ring"],
        pacing_wpm=150,
    ),
    "ai_technology": CategoryProfile(
        name="ai_technology",
        display_title="AI & Technology",
        description="Next-generation robotics, neural networks, quantum computing, and future tech realities.",
        recommended_voice="en-US-JennyNeural",        # Clean, modern, precise
        subtitle_primary_color="&H00FFFF00",          # Neon Cyan
        subtitle_outline_color="&H00000000",          # Solid Black
        theme_bg_color="#0a192f",
        visual_keywords=["robot humanoid hand", "server room blinking lights", "microchip circuit macro", "futuristic city drone", "cyber security code"],
        pacing_wpm=145,
    ),
    "horror_stories": CategoryProfile(
        name="horror_stories",
        display_title="Horror & Scary Stories",
        description="Eerie unexplained encounters, psychological suspense, and chilling historical lore.",
        recommended_voice="en-US-ChristopherNeural",  # Low, ominous storytelling tone
        subtitle_primary_color="&H000000FF",          # Blood Red
        subtitle_outline_color="&H00FFFFFF",          # White outline for contrast
        theme_bg_color="#0d0208",
        visual_keywords=["foggy dark forest night", "creepy abandoned house hallway", "flickering lantern shadow", "mysterious cabin woods", "thunderstorm lightning rain"],
        pacing_wpm=135,                               # Slower, more deliberate pacing
    ),
    "football_facts": CategoryProfile(
        name="football_facts",
        display_title="Football (Soccer) Facts",
        description="Incredible match records, iconic goals, legendary player moments, and tournament history.",
        recommended_voice="en-GB-RyanNeural",         # UK Sports commentary style
        subtitle_primary_color="&H0000FF00",          # Pitch Green
        subtitle_outline_color="&H00000000",          # Solid Black
        theme_bg_color="#032b12",
        visual_keywords=["stadium floodlights night", "soccer ball net goal", "crowd cheering stadium celebration", "football boots grass pitch", "referee whistle stadium"],
        pacing_wpm=155,                               # Energetic commentary pace
    ),
    "cricket_facts": CategoryProfile(
        name="cricket_facts",
        display_title="Cricket Facts",
        description="Historic World Cup feats, unbelievable bowling figures, cricket legends, and rare records.",
        recommended_voice="en-IN-PrabhatNeural",      # Clear cricket enthusiast voice
        subtitle_primary_color="&H0000A5FF",          # Bright Orange
        subtitle_outline_color="&H00000000",          # Solid Black
        theme_bg_color="#102a43",
        visual_keywords=["cricket pitch wicket stadium", "cricket leather ball seam spin", "cricket stadium crowd lights", "batsman shot slow motion", "cricket trophy stadium"],
        pacing_wpm=150,
    ),
}


class CategoryManager:
    """Manages content categories and returns specific styling profiles."""

    @staticmethod
    def get_profile(category_name: str) -> CategoryProfile:
        """Returns the profile for a given category key."""
        clean_key = category_name.lower().replace(" ", "_").strip()
        return CATEGORY_PROFILES.get(clean_key, CATEGORY_PROFILES["amazing_facts"])

    @staticmethod
    def list_categories() -> List[Dict[str, str]]:
        """Returns a list of all categories for dropdowns."""
        return [
            {"key": k, "title": p.display_title, "description": p.description}
            for k, p in CATEGORY_PROFILES.items()
        ]
