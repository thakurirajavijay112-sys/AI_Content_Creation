"""
AI-CONTENT-AUTOMATION — Title & Description Generator
======================================================
Generates high-CTR, non-misleading titles and SEO-rich descriptions
for multiple video platforms.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ai.provider_manager import ai_provider_manager
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TitleOptions:
    """Represents a set of generated title options."""
    primary_title: str
    variations: List[str]
    description: str


class TitleGenerator:
    """Generates platform-ready video titles and descriptions."""

    def __init__(self, provider_manager=None):
        self.ai = provider_manager or ai_provider_manager

    def generate_titles_and_description(
        self,
        topic: str,
        script_summary: str,
        category: str,
    ) -> TitleOptions:
        """
        Generates 3-5 punchy, curiosity-driven titles and a keyword-rich description.
        Explicitly avoids deceptive or sensationalized clickbait.
        """
        system_prompt = (
            "You are a YouTube metadata and audience retention strategist. "
            "You craft titles that spark genuine curiosity while maintaining complete truthfulness. "
            "Never use deceptive clickbait or all-caps shouting."
        )

        prompt = f"""
Generate titles and a description for a short vertical video:
Topic: {topic}
Summary: {script_summary}
Category: {category}

Requirements:
1. Provide 4 title options:
   - Option 1 (Curiosity-based): Under 50 characters, sparks an unanswered question.
   - Option 2 (Fact/Revelation): Highlights the most surprising true element.
   - Option 3 (Direct/Searchable): High search-volume phrasing.
   - Option 4 (Story/Hook): Character- or narrative-driven.
2. Provide a 2-3 sentence video description that includes natural SEO keywords.

Return JSON in this format:
{{
  "primary_title": "Best overall title under 60 characters",
  "variations": [
    "Alternative Title 1",
    "Alternative Title 2",
    "Alternative Title 3"
  ],
  "description": "Engaging description text..."
}}
"""
        logger.info(f"Generating titles for topic: '{topic}'")
        data = self.ai.generate_json(prompt, system_prompt=system_prompt)

        primary = data.get("primary_title", topic)
        variations = data.get("variations", [])
        desc = data.get("description", "")

        return TitleOptions(
            primary_title=primary,
            variations=variations,
            description=desc,
        )
