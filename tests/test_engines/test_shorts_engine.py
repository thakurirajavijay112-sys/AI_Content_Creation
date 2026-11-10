"""
AI-CONTENT-AUTOMATION — Tests: Engine 1 (AI Shorts Generator)
=============================================================
Tests for:
- Category profiles and styling parameters for all 6 categories
- Idea scoring heuristic and ranking algorithms
- Visual manager motion background generation
- Complete end-to-end shorts production pipeline and database persistence
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engines.ai_shorts.category_manager import CategoryManager, CATEGORY_PROFILES
from engines.ai_shorts.idea_scorer import IdeaScorer
from engines.ai_shorts.visual_manager import visual_manager
from engines.ai_shorts.shorts_engine import AIShortsEngine, ShortsProductionResult
from ai.idea_generator import ContentIdea
from ai.provider_manager import ai_provider_manager
from tests.test_ai_providers import MockAIProvider


class TestCategoryManager:
    """Verifies all 6 content categories are properly defined."""

    def test_all_six_categories_configured(self):
        expected_categories = [
            "amazing_facts",
            "motivation",
            "ai_technology",
            "horror_stories",
            "football_facts",
            "cricket_facts",
        ]
        for cat in expected_categories:
            assert cat in CATEGORY_PROFILES
            prof = CategoryManager.get_profile(cat)
            assert prof.display_title is not None
            assert prof.recommended_voice.startswith("en-")
            assert prof.subtitle_primary_color.startswith("&H")
            assert len(prof.visual_keywords) > 0


class TestIdeaScorer:
    """Tests idea scoring algorithms and ranking."""

    def test_score_idea_heuristic(self):
        res = IdeaScorer.score_idea_heuristic(
            title="The Deepest Ocean Mystery",
            hook="At the deepest point on Earth, scientists heard an unexplained metallic sound.",
            concept="Researchers discovered an acoustic anomaly in the Mariana Trench."
        )
        assert "total_score" in res
        assert 50.0 <= res["total_score"] <= 100.0
        assert res["breakdown"]["hook_strength"] > 10.0

    def test_rank_ideas(self):
        ideas = [
            ContentIdea(id=1, engine="ai_shorts", category="facts", title="Boring idea", concept="Nothing special", hook="Hello", score=60.0),
            ContentIdea(id=2, engine="ai_shorts", category="facts", title="The Mariana Trench Mystery", concept="Strange anomaly discovered", hook="At the deepest point on Earth, scientists heard something impossible.", score=85.0),
        ]
        ranked = IdeaScorer.rank_ideas(ideas)
        assert ranked[0].title == "The Mariana Trench Mystery"
        assert ranked[0].score >= ranked[1].score


class TestVisualManager:
    """Tests motion background generation."""

    def test_thematic_motion_background(self, tmp_path):
        bg_clip = visual_manager.create_thematic_motion_background(
            category="amazing_facts",
            duration_s=2.0,
            title_text="Test Motion",
            width=540,  # Lower resolution for fast unit test
            height=960,
        )
        assert bg_clip.exists()
        assert bg_clip.stat().st_size > 5000


class TestShortsEnginePipeline:
    """Tests the full end-to-end Shorts production pipeline."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path):
        from database.db_manager import db
        test_db = tmp_path / "test_shorts_engine.db"
        orig_path = db.db_path
        db.set_path(test_db)
        db.initialise_schema()
        yield
        db.set_path(orig_path)

    def test_produce_short_end_to_end(self, monkeypatch):
        # Configure Mock AI provider so the test runs completely locally
        mock_provider = MockAIProvider(name="mock")
        ai_provider_manager.providers["mock"] = mock_provider
        ai_provider_manager.priority = ["mock"]

        engine = AIShortsEngine()

        result = engine.produce_short(
            category="amazing_facts",
            custom_topic="The Mariana Trench Sound",
            custom_script_text="At the deepest point on Earth, scientists recorded a repeating metallic pulse. It was a new species of whale.",
            auto_queue_publish=True,
        )

        assert isinstance(result, ShortsProductionResult)
        assert result.video_id is not None
        assert Path(result.video_path).exists()
        assert Path(result.thumbnail_path).exists()
        assert Path(result.subtitle_path).exists()
        assert result.duration_s > 1.0
        assert result.quality_score >= 60.0
        assert "youtube" in result.hashtags

        # Verify database record
        from database.db_manager import db
        video_row = db.fetchone("SELECT * FROM videos WHERE id=:id", {"id": result.video_id})
        assert video_row is not None
        assert video_row["engine"] == "ai_shorts"
        assert video_row["status"] == "pending"

        # Verify publishing jobs queued
        jobs = db.fetchall("SELECT * FROM publishing_jobs WHERE video_id=:id", {"id": result.video_id})
        assert len(jobs) == 3  # YouTube, Instagram, TikTok
