"""
AI-CONTENT-AUTOMATION — Hashtag Generator
===========================================
Generates tailored, high-reach hashtag sets for YouTube Shorts,
Instagram Reels, Facebook, and TikTok.
"""

from typing import List, Dict
from ai.provider_manager import ai_provider_manager
from core.logger import get_logger

logger = get_logger(__name__)


# Default high-traffic platform tags
PLATFORM_DEFAULT_TAGS = {
    "youtube": ["#Shorts", "#YouTubeShorts", "#ViralShorts"],
    "instagram": ["#reels", "#reelsinstagram", "#explorepage"],
    "tiktok": ["#fyp", "#foryou", "#viral"],
    "facebook": ["#reels", "#facebookreels", "#viral"],
}


class HashtagGenerator:
    """Generates relevant, platform-optimized hashtags."""

    def __init__(self, provider_manager=None):
        self.ai = provider_manager or ai_provider_manager

    def generate_hashtags(
        self,
        topic: str,
        category: str,
        target_platforms: List[str] = None,
        count: int = 10,
    ) -> Dict[str, str]:
        """
        Generates context-specific hashtags formatted as a single string for each platform.
        Example output:
            {'youtube': '#Shorts #SpaceMysteries #Astronomy', 'instagram': '#reels #space...'}
        """
        if not target_platforms:
            target_platforms = ["youtube", "instagram", "tiktok"]

        system_prompt = "You are a social media hashtag researcher. Return only valid hashtags without punctuation inside tags."

        prompt = f"""
Generate {count} top-performing hashtags for this content:
Topic: {topic}
Category: {category}

Return JSON with a single list of specific niche and trending hashtags:
{{
  "hashtags": ["#TopicTag1", "#TopicTag2", "#TopicTag3"]
}}
"""
        logger.info(f"Generating hashtags for: {topic}")
        try:
            data = self.ai.generate_json(prompt, system_prompt=system_prompt)
            niche_tags = [
                tag if tag.startswith("#") else f"#{tag}"
                for tag in data.get("hashtags", [])
            ]
        except Exception:
            # Fallback niche tags based on category
            clean_cat = category.replace(" ", "").replace("_", "")
            niche_tags = [f"#{clean_cat}", "#DailyFacts", "#DidYouKnow", "#TrendingNow"]

        results = {}
        for platform in target_platforms:
            p_key = platform.lower()
            base_tags = PLATFORM_DEFAULT_TAGS.get(p_key, ["#Shorts"])
            combined = base_tags + [t for t in niche_tags if t not in base_tags]
            # Form clean space-separated hashtag string (e.g., "#Shorts #Space #Mystery")
            results[p_key] = " ".join(combined[:count])

        return results
