"""
AI-CONTENT-AUTOMATION — Script Generator
=========================================
Generates timed, high-retention video scripts for 45-second vertical Shorts.
Produces both:
1. Pure narration text (for Text-to-Speech synthesis with zero stage cues).
2. Scene-by-scene storyboards (narration, visual footage prompt, SFX cues).
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from ai.provider_manager import ai_provider_manager
from database.db_manager import db
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScriptScene:
    """Represents one scene in the video storyboard."""
    scene_number: int
    duration_s: float
    narration: str
    visual_prompt: str
    sfx_cue: Optional[str] = None


@dataclass
class VideoScript:
    """Represents a complete generated script."""
    id: Optional[int]
    idea_id: Optional[int]
    engine: str
    title: str
    narration_text: str  # Clean spoken text ONLY for TTS
    scenes: List[ScriptScene] = field(default_factory=list)
    word_count: int = 0
    estimated_duration_s: float = 45.0
    status: str = "draft"


class ScriptGenerator:
    """Generates production-ready video scripts tailored to 45-second short videos."""

    def __init__(self, provider_manager=None):
        self.ai = provider_manager or ai_provider_manager

    def generate_short_script(
        self,
        title: str,
        concept: str,
        hook: str,
        category: str = "amazing_facts",
        language: str = "en",
        idea_id: Optional[int] = None,
        engine: str = "ai_shorts",
    ) -> VideoScript:
        """
        Generates a 45-second script structured in 4-5 scenes.
        Supports 8 languages (en, hi, ne, pt, es, zh, ja, ar).
        Enforces a target word count of 115-135 words (optimal for 45s at 150 WPM).
        """
        system_prompt = (
            "You are an award-winning scriptwriter for fast-paced viral short videos. "
            "Your writing is punchy, cinematic, clear, and strictly fact-based. "
            "Never use fluff, filler, clichés like 'In a world...', or fake statistics."
        )

        lang_instruction = ""
        if language and language != "en":
            from core.languages import LanguageManager
            lp = LanguageManager.get_profile(language)
            lang_instruction = f"""
STRICT LANGUAGE REQUIREMENT:
- The video "title" and all scene "narration" MUST be written in {lp.name} ({lp.native_name}).
- Write naturally, colloquially, and fluently as spoken by native {lp.name} speakers.
- IMPORTANT: All "visual_prompt" strings MUST remain in clear English for stock footage & image generation.
"""

        prompt = f"""
Write a complete, high-retention 45-second video script.
Title: {title}
Core Concept: {concept}
Opening Hook: {hook}
Category: {category}
{lang_instruction}

STRICT TIMING & WORD COUNT RULES:
1. Target Word Count: EXACTLY 115 to 135 spoken words (this equals 45 seconds when spoken naturally).
2. Structure into 4 or 5 sequential scenes:
   - Scene 1 (0-5s): The Hook (Grabs attention immediately)
   - Scene 2 (5-15s): The Context / The Setup
   - Scene 3 (15-30s): The Core Revelation / Escalation / Key Twist
   - Scene 4 (30-40s): The Climax / Impact
   - Scene 5 (40-45s): The Loop / Takeaway (Ends on a thought that makes the video loop seamlessly)
3. For each scene, provide:
   - "narration": Spoken words ONLY. No brackets, no emojis, no asterisks, no speaker names.
   - "visual_prompt": Exact stock footage or visual description to display during this scene.
   - "sfx_cue": Audio sound effect (e.g., 'whoosh', 'dramatic boom', 'glitch', 'subtle heartbeat').

Return JSON matching this exact structure:
{{
  "title": "{title}",
  "scenes": [
    {{
      "scene_number": 1,
      "duration_s": 5.0,
      "narration": "First spoken line.",
      "visual_prompt": "Cinematic slow motion shot of an ancient clock ticking in darkness.",
      "sfx_cue": "ticking clock then low bass thud"
    }}
  ]
}}
"""
        logger.info(f"Generating short-form script for: '{title}'")
        data = self.ai.generate_json(prompt, system_prompt=system_prompt)

        scenes_data = data.get("scenes", [])
        scenes: List[ScriptScene] = []
        narration_parts: List[str] = []

        total_duration = 0.0
        for s in scenes_data:
            narr = str(s.get("narration", "")).strip()
            if not narr:
                continue

            scene = ScriptScene(
                scene_number=int(s.get("scene_number", len(scenes) + 1)),
                duration_s=float(s.get("duration_s", 9.0)),
                narration=narr,
                visual_prompt=str(s.get("visual_prompt", "")).strip(),
                sfx_cue=s.get("sfx_cue"),
            )
            scenes.append(scene)
            narration_parts.append(narr)
            total_duration += scene.duration_s

        full_narration = " ".join(narration_parts)
        word_count = len(full_narration.split())

        # Save to database
        script_id = db.execute("""
            INSERT INTO scripts (idea_id, engine, title, content, word_count, duration_s, status, created_at, updated_at)
            VALUES (:idea_id, :engine, :title, :content, :words, :dur, 'draft', datetime('now'), datetime('now'))
        """, {
            "idea_id": idea_id,
            "engine": engine,
            "title": title,
            "content": full_narration,
            "words": word_count,
            "dur": total_duration,
        })

        logger.info(f"Saved script #{script_id} ({word_count} words, {total_duration:.1f}s)")

        return VideoScript(
            id=script_id,
            idea_id=idea_id,
            engine=engine,
            title=title,
            narration_text=full_narration,
            scenes=scenes,
            word_count=word_count,
            estimated_duration_s=total_duration,
            status="draft",
        )

    def update_script_text(self, script_id: int, new_content: str) -> bool:
        """Allows manual editing of script narration in database."""
        words = len(new_content.split())
        est_duration = (words / 140.0) * 60.0  # Approx at 140 words per min
        db.execute("""
            UPDATE scripts
            SET content=:content, word_count=:words, duration_s=:dur, updated_at=datetime('now')
            WHERE id=:id
        """, {
            "id": script_id,
            "content": new_content,
            "words": words,
            "dur": round(est_duration, 1),
        })
        logger.info(f"Updated script #{script_id} ({words} words)")
        return True
