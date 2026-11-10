"""
AI-CONTENT-AUTOMATION — Engine 1: AI Shorts Generator
======================================================
Automated end-to-end production pipeline for original short videos.
Executes the full 13-step workflow:
1. Category selection
2. Idea generation (with duplicate check)
3. Scoring & best idea selection
4. Script generation (45s pacing)
5. Opening hook creation
6. Voiceover generation (Edge-TTS)
7. Visual sourcing / motion generation
8. Subtitle generation (ASS styled for 9:16)
9. FFmpeg rendering with GPU acceleration
10. Audio processing & background music
11. Metadata (title, description, hashtags)
12. Quality check & factual validation
13. Database storage & publishing queue insertion
"""

import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ai.idea_generator import IdeaGenerator, ContentIdea
from ai.script_generator import ScriptGenerator, VideoScript
from ai.title_generator import TitleGenerator, TitleOptions
from ai.hashtag_generator import HashtagGenerator
from ai.fact_checker import FactChecker, FactCheckResult
from audio.tts import tts_engine
from audio.transcription import transcription_engine
from audio.audio_processor import audio_processor
from video.subtitles import subtitle_generator
from video.renderer import video_renderer
from video.thumbnail import thumbnail_generator
from engines.ai_shorts.category_manager import CategoryManager, CategoryProfile
from engines.ai_shorts.visual_manager import visual_manager
from engines.ai_shorts.idea_scorer import IdeaScorer
from database.db_manager import db
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ShortsProductionResult:
    """Represents the output of the complete Shorts creation pipeline."""
    video_id: int
    title: str
    category: str
    video_path: str
    thumbnail_path: str
    subtitle_path: str
    audio_path: str
    duration_s: float
    quality_score: float
    titles_and_desc: TitleOptions
    hashtags: Dict[str, str]
    fact_check: FactCheckResult
    status: str  # 'pending', 'approved', 'queued'


class AIShortsEngine:
    """Engine 1 orchestrator: creates original 9:16 vertical short videos."""

    def __init__(self):
        self.engine_name = "ai_shorts"
        self.output_dir = Path(__file__).parent.parent.parent / "generated" / "videos" / "shorts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def produce_short(
        self,
        category: str = "amazing_facts",
        custom_topic: Optional[str] = None,
        custom_script_text: Optional[str] = None,
        language: str = "en",
        voice_override: Optional[str] = None,
        auto_queue_publish: bool = True,
        captions: bool = True,
    ) -> ShortsProductionResult:
        """
        Executes the full automated production workflow.
        Returns complete metadata, rendered video path, and quality score.
        Supports 8 languages (en, hi, ne, pt, es, zh, ja, ar).
        captions=True burns styled subtitles; captions=False produces clean video.
        """
        start_time = time.time()
        category_clean = category.lower().replace(" ", "_").strip()
        profile = CategoryManager.get_profile(category_clean)

        from core.languages import LanguageManager
        lang_profile = LanguageManager.get_profile(language)

        logger.info(f"=== Starting Engine 1 Production: {profile.display_title} [{lang_profile.name}] ===")

        # ── Step 1 & 2 & 3: Idea Selection ──────────────────────────────────────
        idea_id = None
        idea_score = 85.0
        if custom_topic:
            idea_title = custom_topic
            idea_concept = custom_topic
            idea_hook = custom_topic
        else:
            idea_gen = IdeaGenerator()
            # Fetch highest-scoring unused idea or generate new candidates
            best_idea = idea_gen.get_best_unused_idea(category=category_clean)
            if not best_idea:
                logger.info("No unused ideas found. Generating fresh concepts...")
                candidates = idea_gen.generate_ideas(category=category_clean, count=3)
                ranked = IdeaScorer.rank_ideas(candidates)
                best_idea = ranked[0]

            idea_id = best_idea.id
            idea_title = best_idea.title
            idea_concept = best_idea.concept
            idea_hook = best_idea.hook
            idea_score = getattr(best_idea, 'score', 85.0)
            idea_gen.mark_used(idea_id)

        logger.info(f"Selected Idea: '{idea_title}' (Score: {idea_score:.1f})")

        # ── Step 4 & 5: Script Generation ───────────────────────────────────────
        script_gen = ScriptGenerator()
        if custom_script_text:
            script = ScriptGenerator().generate_short_script(
                title=idea_title, concept=idea_concept, hook=idea_hook,
                category=category_clean, language=language, idea_id=idea_id
            )
            script.narration_text = custom_script_text
            script_gen.update_script_text(script.id, custom_script_text)
        else:
            script = script_gen.generate_short_script(
                title=idea_title,
                concept=idea_concept,
                hook=idea_hook,
                category=category_clean,
                language=language,
                idea_id=idea_id,
            )

        logger.info(f"Script ready ({lang_profile.name}): {script.word_count} words ({script.estimated_duration_s:.1f}s)")

        # ── Step 6: Voiceover Generation ────────────────────────────────────────
        timestamp_prefix = int(time.time())
        slug = hashlib.md5(idea_title.encode()).hexdigest()[:8]
        audio_filename = f"voice_{category_clean}_{timestamp_prefix}_{slug}.mp3"

        selected_voice = voice_override or lang_profile.default_voice
        tts_result = tts_engine.generate_speech(
            text=script.narration_text,
            output_filename=audio_filename,
            voice=selected_voice,
        )
        audio_path = tts_result.audio_path
        actual_duration = tts_result.duration_s
        logger.info(f"Voiceover generated: {actual_duration:.1f}s via {tts_result.provider} ({selected_voice})")

        # ── Step 7: Subtitle Generation ─────────────────────────────────────────
        # Convert word boundaries to dynamic 4-word subtitle segments
        ass_path: Optional[Path] = None
        if captions:
            if tts_result.word_timestamps:
                segments = transcription_engine.segments_from_word_timestamps(
                    tts_result.word_timestamps, words_per_segment=4
                )
            else:
                segments = transcription_engine.segments_from_word_timestamps([], 4)

            ass_filename = f"subs_{timestamp_prefix}_{slug}.ass"
            ass_path = subtitle_generator.output_dir / ass_filename
            subtitle_generator.generate_styled_ass(
                segments=segments,
                output_path=str(ass_path),
                font_name=lang_profile.font_name,
                font_size=56,
                primary_color=profile.subtitle_primary_color,
                outline_color=profile.subtitle_outline_color,
                margin_v=340,
            )
        else:
            logger.info("Captions disabled — skipping subtitle generation.")

        # ── Step 8: Multi-Scene Cinematic Visual Sourcing ───────────────────────
        visual_path = visual_manager.get_or_create_multi_scene_visual(
            scenes=script.scenes,
            category=category_clean,
            total_duration=actual_duration,
            title_text=idea_title,
        )

        # ── Step 9 & 10: Video Rendering ────────────────────────────────────────
        video_filename = f"short_{category_clean}_{timestamp_prefix}_{slug}.mp4"
        final_video_path = self.output_dir / video_filename

        rendered_video = video_renderer.render_short_video(
            visual_source=str(visual_path),
            audio_path=str(audio_path),
            output_path=str(final_video_path),
            subtitle_path=str(ass_path) if ass_path else None,
            duration_s=actual_duration,
            width=1080,
            height=1920,
        )

        # ── Step 11: Branded Thumbnail ───────────────────────────────────────────
        thumb_filename = f"thumb_{timestamp_prefix}_{slug}.jpg"
        thumb_path = thumbnail_generator.output_dir / thumb_filename
        try:
            thumbnail_generator.create_branded_thumbnail(
                title=idea_title,
                output_path=str(thumb_path),
                category=category_clean,
            )
        except Exception:
            thumbnail_generator.create_color_card(
                text=idea_title,
                output_path=str(thumb_path),
            )

        # ── Step 12: Metadata & Fact Audit ──────────────────────────────────────
        title_gen = TitleGenerator()
        titles_desc = title_gen.generate_titles_and_description(
            topic=idea_title,
            script_summary=script.narration_text[:200],
            category=category_clean,
        )

        hashtag_gen = HashtagGenerator()
        hashtags = hashtag_gen.generate_hashtags(
            topic=idea_title,
            category=category_clean,
            target_platforms=["youtube", "instagram", "tiktok"],
        )

        fact_checker = FactChecker()
        fact_audit = fact_checker.check_script(
            title=idea_title,
            narration_text=script.narration_text,
            category=category_clean,
        )

        # Quality Score Calculation (0 to 100)
        quality_score = self._compute_quality_score(
            video_file=rendered_video,
            expected_duration=actual_duration,
            fact_score=fact_audit.accuracy_score,
            word_count=script.word_count,
        )

        # ── Step 13: Database & Publishing Queue ────────────────────────────────
        content_hash = hashlib.sha256(rendered_video.read_bytes()).hexdigest()[:16]
        file_size_mb = round(rendered_video.stat().st_size / (1024 * 1024), 2)

        video_id = db.execute("""
            INSERT INTO videos (
                engine, script_id, title, description, hashtags,
                file_path, thumbnail_path, subtitle_path, duration_s,
                format, resolution, file_size_mb, content_hash,
                status, quality_score, created_at, updated_at
            ) VALUES (
                :engine, :script_id, :title, :desc, :tags,
                :fpath, :tpath, :spath, :dur,
                'vertical', '1080x1920', :size_mb, :hash,
                'pending', :score, datetime('now'), datetime('now')
            )
        """, {
            "engine": self.engine_name,
            "script_id": script.id,
            "title": titles_desc.primary_title,
            "desc": titles_desc.description,
            "tags": hashtags.get("youtube", ""),
            "fpath": str(rendered_video),
            "tpath": str(thumb_path),
            "spath": str(ass_path),
            "dur": round(actual_duration, 1),
            "size_mb": file_size_mb,
            "hash": content_hash,
            "score": quality_score,
        })

        # Insert publishing job if auto-queue is enabled
        if auto_queue_publish:
            for platform in ["youtube", "instagram", "tiktok"]:
                db.execute("""
                    INSERT INTO publishing_jobs (video_id, platform, status, created_at, updated_at)
                    VALUES (:vid, :plat, 'queued', datetime('now'), datetime('now'))
                """, {"vid": video_id, "plat": platform})

        elapsed = time.time() - start_time
        logger.info(f"=== Short Production Complete in {elapsed:.1f}s! Video #{video_id} Quality: {quality_score}/100 ===")

        return ShortsProductionResult(
            video_id=video_id,
            title=titles_desc.primary_title,
            category=category_clean,
            video_path=str(rendered_video),
            thumbnail_path=str(thumb_path),
            subtitle_path=str(ass_path),
            audio_path=str(audio_path),
            duration_s=round(actual_duration, 1),
            quality_score=quality_score,
            titles_and_desc=titles_desc,
            hashtags=hashtags,
            fact_check=fact_audit,
            status="pending",
        )

    @staticmethod
    def _compute_quality_score(
        video_file: Path,
        expected_duration: float,
        fact_score: float,
        word_count: int,
    ) -> float:
        """Calculates a comprehensive video production quality score."""
        score = 100.0

        # File integrity check (minimum 200 KB)
        if not video_file.exists() or video_file.stat().st_size < 200_000:
            return 0.0

        # Duration check (optimal shorts are 30-55s)
        if expected_duration < 25.0:
            score -= 15.0
        elif expected_duration > 59.0:
            score -= 10.0

        # Word count pacing (optimal 100-145 words)
        if word_count < 90 or word_count > 160:
            score -= 8.0

        # Factual integrity penalty
        if fact_score < 80.0:
            score -= (80.0 - fact_score) * 0.5

        return max(50.0, round(score, 1))


# Singleton instance
shorts_engine = AIShortsEngine()
