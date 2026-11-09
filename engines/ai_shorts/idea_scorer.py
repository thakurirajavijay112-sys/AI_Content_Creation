"""
AI-CONTENT-AUTOMATION — Engine 1: Idea Scorer
==============================================
Scores and ranks candidate content ideas using a 4-pillar retention rubric:
1. Hook Strength (0-30 pts) — Does the first 3 seconds stop scrolling?
2. Curiosity Gap (0-30 pts) — Does it create an unresolved question?
3. Visual Appeal (0-20 pts) — Can this concept be visually illustrated?
4. Replay Value (0-20 pts) — Will viewers want to rewatch or loop?

Total Score: 0 to 100 points.
"""

from typing import Dict, Any, List
from ai.idea_generator import ContentIdea
from core.logger import get_logger

logger = get_logger(__name__)


class IdeaScorer:
    """Evaluates and ranks content ideas."""

    @staticmethod
    def score_idea_heuristic(title: str, hook: str, concept: str) -> Dict[str, Any]:
        """
        Calculates heuristic retention score based on proven short-form patterns.
        """
        hook_lower = hook.lower()
        title_lower = title.lower()

        # 1. Hook Strength (0-30 pts)
        hook_score = 15.0
        strong_hook_triggers = [
            "what if", "scientists discovered", "nobody knows", "the truth about",
            "at the deepest", "this is why", "secret", "never", "only 1%", "banned"
        ]
        for trigger in strong_hook_triggers:
            if trigger in hook_lower:
                hook_score += 4.0

        # Hook length penalty if too long (>18 words hurts immediate impact)
        hook_words = len(hook.split())
        if 5 <= hook_words <= 16:
            hook_score += 5.0
        elif hook_words > 22:
            hook_score -= 4.0
        hook_score = max(5.0, min(30.0, hook_score))

        # 2. Curiosity Gap (0-30 pts)
        curiosity_score = 18.0
        curiosity_words = ["mystery", "anomaly", "strange", "bizarre", "unexplained", "hidden", "record", "impossible"]
        for cw in curiosity_words:
            if cw in title_lower or cw in concept.lower():
                curiosity_score += 3.0
        curiosity_score = max(10.0, min(30.0, curiosity_score))

        # 3. Visual Appeal (0-20 pts)
        visual_score = 14.0
        visual_triggers = ["ocean", "space", "stadium", "robot", "dark", "gold", "mountain", "creature", "flight"]
        for vt in visual_triggers:
            if vt in concept.lower():
                visual_score += 2.0
        visual_score = max(5.0, min(20.0, visual_score))

        # 4. Replay Value (0-20 pts)
        replay_score = 14.0
        if any(term in concept.lower() for term in ["loop", "reveal", "twist", "ending", "secret"]):
            replay_score += 3.0
        replay_score = max(5.0, min(20.0, replay_score))

        total = round(hook_score + curiosity_score + visual_score + replay_score, 1)

        return {
            "total_score": total,
            "breakdown": {
                "hook_strength": hook_score,
                "curiosity_gap": curiosity_score,
                "visual_appeal": visual_score,
                "replay_value": replay_score,
            }
        }

    @classmethod
    def rank_ideas(cls, ideas: List[ContentIdea]) -> List[ContentIdea]:
        """Ranks a list of ideas by composite score descending."""
        for idea in ideas:
            analysis = cls.score_idea_heuristic(idea.title, idea.hook, idea.concept)
            # Blend AI score with heuristic score
            blended = round((idea.score * 0.6) + (analysis["total_score"] * 0.4), 1)
            idea.score = blended

        ideas.sort(key=lambda x: x.score, reverse=True)
        return ideas
