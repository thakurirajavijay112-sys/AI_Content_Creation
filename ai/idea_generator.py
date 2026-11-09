"""
AI-CONTENT-AUTOMATION — Idea Generator
========================================
Generates and scores high-retention video ideas across all supported categories.
Enforces uniqueness by checking previous database entries to avoid duplicate topics.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ai.provider_manager import ai_provider_manager
from database.db_manager import db
from core.logger import get_logger

logger = get_logger(__name__)


# Supported content categories
CATEGORIES: Dict[str, str] = {
    "amazing_facts": "Amazing Facts and Mysteries — strange phenomena, bizarre scientific truths, and historical anomalies.",
    "motivation": "Motivation and Success — discipline, resilience, overcoming extreme odds, and peak performance habits.",
    "ai_technology": "AI and Technology — future breakthroughs, artificial intelligence reality, and computing milestones.",
    "horror_stories": "Horror and Scary Stories — unsettling true events, eerie mysteries, and suspenseful lore.",
    "football_facts": "Football (Soccer) Facts — unbelievable records, legendary players, and iconic match moments.",
    "cricket_facts": "Cricket Facts — historical feats, rare stats, rivalry records, and world cup milestones.",
}


@dataclass
class ContentIdea:
    """Represents a scored content idea."""
    id: Optional[int]
    engine: str
    category: str
    title: str
    concept: str
    hook: str
    score: float
    used: bool = False


class IdeaGenerator:
    """Generates unique, scored video ideas using configured AI providers."""

    def __init__(self, provider_manager=None):
        self.ai = provider_manager or ai_provider_manager

    def generate_ideas(
        self,
        category: str,
        count: int = 3,
        engine: str = "ai_shorts",
    ) -> List[ContentIdea]:
        """
        Generates original ideas for a given category.
        Ensures ideas do not duplicate existing topics in the database.
        """
        category_key = category.lower().replace(" ", "_")
        category_desc = CATEGORIES.get(category_key, category)

        # Retrieve recently generated titles in this category to prevent repetition
        recent_records = db.fetchall(
            "SELECT title FROM ideas WHERE category=:cat ORDER BY created_at DESC LIMIT 20",
            {"cat": category_key}
        )
        avoid_topics = [r["title"] for r in recent_records]
        avoid_clause = ""
        if avoid_topics:
            avoid_clause = (
                "DO NOT repeat or closely rephrase any of these recently covered topics:\n"
                + "\n".join(f"- {t}" for t in avoid_topics[:10])
            )

        system_prompt = (
            "You are an elite short-form content director and viral video strategist. "
            "You invent powerful, strictly factual, and curiosity-driven concepts for YouTube Shorts and TikTok."
        )

        prompt = f"""
Generate {count} unique, high-retention video ideas for the category:
Category: {category_desc}

Requirements:
1. Ideas must be original, engaging, and truthful (no fake statistics or clickbait lies).
2. Each idea must feature a compelling 3-second opening hook that stops user scrolling.
3. Assign an honest predicted retention score from 0 to 100 based on curiosity and replay value.
{avoid_clause}

Respond ONLY with a JSON object in this exact schema:
{{
  "ideas": [
    {{
      "title": "Short, punchy video title",
      "concept": "1-2 sentence core premise explaining the story or fact",
      "hook": "Exact first spoken sentence (0-3 seconds attention grabber)",
      "score": 88.5
    }}
  ]
}}
"""
        logger.info(f"Generating {count} ideas for category: {category_key}")
        data = self.ai.generate_json(prompt, system_prompt=system_prompt)
        raw_ideas = data.get("ideas", [])

        results: List[ContentIdea] = []
        for item in raw_ideas:
            title = str(item.get("title", "")).strip()
            concept = str(item.get("concept", "")).strip()
            hook = str(item.get("hook", "")).strip()
            score = float(item.get("score", 75.0))

            if not title:
                continue

            # Save to database
            idea_id = db.execute("""
                INSERT INTO ideas (engine, category, title, concept, hook, score, used, created_at, updated_at)
                VALUES (:engine, :cat, :title, :concept, :hook, :score, 0, datetime('now'), datetime('now'))
            """, {
                "engine": engine,
                "cat": category_key,
                "title": title,
                "concept": concept,
                "hook": hook,
                "score": score,
            })

            results.append(ContentIdea(
                id=idea_id,
                engine=engine,
                category=category_key,
                title=title,
                concept=concept,
                hook=hook,
                score=score,
                used=False
            ))

        # Sort by score descending so the strongest idea is first
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def get_best_unused_idea(self, category: Optional[str] = None) -> Optional[ContentIdea]:
        """Fetches the highest-scoring unused idea from the database."""
        query = "SELECT * FROM ideas WHERE used=0"
        params = {}
        if category:
            query += " AND category=:cat"
            params["cat"] = category.lower().replace(" ", "_")

        query += " ORDER BY score DESC, created_at DESC LIMIT 1"
        row = db.fetchone(query, params)
        if not row:
            return None

        return ContentIdea(
            id=row["id"],
            engine=row["engine"],
            category=row["category"],
            title=row["title"],
            concept=row["concept"],
            hook=row["hook"],
            score=row["score"],
            used=bool(row["used"])
        )

    def mark_used(self, idea_id: int):
        """Marks an idea as used once a script has been generated."""
        db.execute(
            "UPDATE ideas SET used=1, updated_at=datetime('now') WHERE id=:id",
            {"id": idea_id}
        )
        logger.info(f"Marked idea #{idea_id} as used")
