"""
AI-CONTENT-AUTOMATION — Tests: Phase 3 Shared AI Services
===========================================================
Tests for:
- Base AI provider interface & data structures
- Gemini, Ollama, and optional Anthropic provider adapters
- AI Provider Manager priority routing & fallback mechanism
- Idea Generator with database duplicate protection
- Script Generator with scene structure & timing constraints
- Title & Hashtag Generators
- Fact Checker audit functionality
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.providers.base_provider import BaseAIProvider, AIResponse
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.anthropic_provider import AnthropicProvider
from ai.provider_manager import AIProviderManager
from ai.idea_generator import IdeaGenerator
from ai.script_generator import ScriptGenerator
from ai.title_generator import TitleGenerator
from ai.hashtag_generator import HashtagGenerator
from ai.fact_checker import FactChecker


# ── Mock Provider for deterministic testing ────────────────────────────────────

class MockAIProvider(BaseAIProvider):
    """Deterministic mock provider for unit testing without live API keys."""
    def __init__(self, name="mock_provider", available=True):
        super().__init__(name=name, default_model="mock-v1")
        self._available = available
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    def generate_text(self, prompt, system_prompt=None, model=None, temperature=0.7, max_tokens=1000):
        self.call_count += 1
        return AIResponse(
            text="This is a generated mock script response for testing.",
            provider=self.name,
            model=self.default_model,
        )

    def generate_json(self, prompt, system_prompt=None, model=None, temperature=0.2):
        self.call_count += 1
        # Tailor mock response based on prompt contents
        if "video ideas" in prompt:
            return {
                "ideas": [
                    {
                        "title": "The Mariana Trench Mystery",
                        "concept": "Scientists discovered an eerie repeating metallic sound in the deepest ocean trench.",
                        "hook": "At the deepest point on Earth, scientists heard something that should not exist.",
                        "score": 92.0
                    },
                    {
                        "title": "Quantum Lock Phenomenon",
                        "concept": "Superconductors can levitate and lock in 3D space permanently.",
                        "hook": "What if you could freeze an object in mid-air with liquid nitrogen?",
                        "score": 86.5
                    }
                ]
            }
        elif "video script" in prompt:
            return {
                "title": "The Mariana Trench Mystery",
                "scenes": [
                    {
                        "scene_number": 1,
                        "duration_s": 5.0,
                        "narration": "At the deepest point on Earth, scientists heard something that should not exist.",
                        "visual_prompt": "Dark ocean trench depth gauge reading 11000 meters.",
                        "sfx_cue": "low sonar ping"
                    },
                    {
                        "scene_number": 2,
                        "duration_s": 10.0,
                        "narration": "Nearly seven miles below the surface, autonomous hydrophones picked up a metallic pulse echoing through the black water.",
                        "visual_prompt": "Underneath deep sea submersible camera light beam.",
                        "sfx_cue": "eerie metallic hum"
                    },
                    {
                        "scene_number": 3,
                        "duration_s": 15.0,
                        "narration": "For months, researchers suspected seismic activity. But the frequency showed a rhythm that no known geologic process can create.",
                        "visual_prompt": "Waveform audio spectrogram vibrating on lab computer screen.",
                        "sfx_cue": "rising tension riser"
                    },
                    {
                        "scene_number": 4,
                        "duration_s": 10.0,
                        "narration": "The sound matched acoustic call signatures of a new unidentified species of minke whale swimming under immense pressure.",
                        "visual_prompt": "Silhouette of massive creature gliding through deep blue.",
                        "sfx_cue": "deep aquatic drone"
                    },
                    {
                        "scene_number": 5,
                        "duration_s": 5.0,
                        "narration": "The ocean still holds millions of undiscovered secrets. What do you think is down there?",
                        "visual_prompt": "Black water fading back to deep darkness.",
                        "sfx_cue": "soft whoosh"
                    }
                ]
            }
        elif "titles and a description" in prompt:
            return {
                "primary_title": "The Deepest Sound on Earth",
                "variations": [
                    "What Did Scientists Hear in the Mariana Trench?",
                    "The Metallic Sound at 36,000 Feet Below",
                    "Ocean Mystery at the Bottom of the World"
                ],
                "description": "Discover the eerie true story of the strange acoustic sound detected in the Mariana Trench."
            }
        elif "Audit this short video script" in prompt:
            return {
                "accuracy_score": 96.0,
                "verdict": "PASS",
                "flagged_claims": [],
                "suggested_corrections": []
            }
        elif "hashtags" in prompt:
            return {
                "hashtags": ["#OceanMystery", "#MarianaTrench", "#DeepSea", "#ScienceFacts"]
            }
        return {}


# ── Unit Tests ────────────────────────────────────────────────────────────────

class TestAIProviders:
    """Verifies individual provider adapter behavior."""

    def test_gemini_provider_unconfigured_without_key(self, monkeypatch):
        """Gemini is_available() should return False if key is default template."""
        monkeypatch.setenv("GEMINI_API_KEY", "your_gemini_api_key_here")
        provider = GeminiProvider()
        assert provider.is_available() is False

    def test_gemini_provider_available_with_key(self, monkeypatch):
        """Gemini is_available() should return True when a key is provided."""
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyFakeValidLookingKeyForTest123")
        provider = GeminiProvider()
        provider.api_key = "AIzaSyFakeValidLookingKeyForTest123"
        assert provider.is_available() is True

    def test_ollama_provider_handles_offline_gracefully(self):
        """Ollama should return is_available() == False when port 11434 is unreachable."""
        provider = OllamaProvider()
        provider.base_url = "http://127.0.0.1:9999"  # Non-existent port
        assert provider.is_available() is False

    def test_anthropic_provider_strictly_optional(self, monkeypatch):
        """Anthropic must report unavailable if no ANTHROPIC_API_KEY is supplied."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        provider = AnthropicProvider()
        assert provider.is_available() is False
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate_text("Hello")
        assert "A Claude web/IDE subscription does not provide API credits" in str(exc_info.value)


class TestProviderManager:
    """Tests provider manager fallback and priority routing."""

    def test_manager_uses_active_provider(self):
        """Provider manager should route request to available provider."""
        manager = AIProviderManager()
        mock = MockAIProvider(name="mock_gemini", available=True)
        manager.providers["mock_gemini"] = mock
        manager.priority = ["mock_gemini"]

        response = manager.generate_text("Test prompt")
        assert response.text is not None
        assert response.provider == "mock_gemini"
        assert mock.call_count == 1

    def test_manager_falls_back_when_first_fails(self):
        """When the primary provider fails, manager must transparently fall back to secondary."""
        manager = AIProviderManager()
        
        # Failing primary
        failing_primary = MockAIProvider(name="failing_gemini", available=True)
        failing_primary.generate_text = MagicMock(side_effect=RuntimeError("Quota 429 exceeded"))
        
        # Working secondary
        backup_ollama = MockAIProvider(name="backup_ollama", available=True)

        manager.providers["failing_gemini"] = failing_primary
        manager.providers["backup_ollama"] = backup_ollama
        manager.priority = ["failing_gemini", "backup_ollama"]

        response = manager.generate_text("Test prompt")
        assert response.provider == "backup_ollama"
        assert backup_ollama.call_count == 1

    def test_manager_raises_clear_error_if_all_fail(self):
        """If all providers in priority fail, manager raises informative error."""
        manager = AIProviderManager()
        failing = MockAIProvider(name="broken", available=True)
        failing.generate_text = MagicMock(side_effect=ConnectionError("Offline"))
        manager.providers["broken"] = failing
        manager.priority = ["broken"]

        with pytest.raises(RuntimeError) as exc:
            manager.generate_text("Test prompt")
        assert "All configured AI providers failed" in str(exc.value)


class TestIdeaGenerator:
    """Tests content idea generation and database storage."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path):
        from database.db_manager import db
        test_db = tmp_path / "test_ideas.db"
        orig_path = db.db_path
        db.set_path(test_db)
        db.initialise_schema()
        yield
        db.set_path(orig_path)

    def test_generates_and_stores_ideas(self):
        mock_provider = MockAIProvider(name="mock")
        manager = AIProviderManager()
        manager.providers["mock"] = mock_provider
        manager.priority = ["mock"]

        gen = IdeaGenerator(provider_manager=manager)
        ideas = gen.generate_ideas(category="amazing_facts", count=2)

        assert len(ideas) == 2
        assert ideas[0].title == "The Mariana Trench Mystery"
        assert ideas[0].score >= ideas[1].score  # Sorted descending
        assert ideas[0].id is not None

        # Verify best unused idea retrieval
        best = gen.get_best_unused_idea(category="amazing_facts")
        assert best is not None
        assert best.title == "The Mariana Trench Mystery"
        assert best.used is False

        # Mark as used
        gen.mark_used(best.id)
        next_best = gen.get_best_unused_idea(category="amazing_facts")
        assert next_best.title == "Quantum Lock Phenomenon"


class TestScriptGenerator:
    """Tests script generation, scene parsing, and word counting."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path):
        from database.db_manager import db
        test_db = tmp_path / "test_scripts.db"
        orig_path = db.db_path
        db.set_path(test_db)
        db.initialise_schema()
        yield
        db.set_path(orig_path)

    def test_generates_script_with_scenes(self):
        mock_provider = MockAIProvider(name="mock")
        manager = AIProviderManager()
        manager.providers["mock"] = mock_provider
        manager.priority = ["mock"]

        gen = ScriptGenerator(provider_manager=manager)
        script = gen.generate_short_script(
            title="The Mariana Trench Mystery",
            concept="Strange metallic sound in deep ocean.",
            hook="At the deepest point on Earth, scientists heard something.",
            category="amazing_facts"
        )

        assert script.id is not None
        assert len(script.scenes) == 5
        assert script.word_count > 50
        assert "metallic" in script.narration_text.lower()
        assert script.scenes[0].duration_s == 5.0
        assert script.scenes[0].sfx_cue is not None

    def test_update_script_text(self):
        mock_provider = MockAIProvider(name="mock")
        manager = AIProviderManager()
        manager.providers["mock"] = mock_provider
        manager.priority = ["mock"]

        gen = ScriptGenerator(provider_manager=manager)
        script = gen.generate_short_script(
            title="Test", concept="Test", hook="Hook"
        )
        new_text = "This is a manually edited script with updated facts and lines."
        gen.update_script_text(script.id, new_text)

        from database.db_manager import db
        row = db.fetchone("SELECT content, word_count FROM scripts WHERE id=:id", {"id": script.id})
        assert row["content"] == new_text
        assert row["word_count"] == len(new_text.split())


class TestMetadataAndFactChecking:
    """Tests title, hashtag, and factual accuracy validation."""

    def test_title_generator(self):
        mock_provider = MockAIProvider(name="mock")
        manager = AIProviderManager()
        manager.providers["mock"] = mock_provider
        manager.priority = ["mock"]

        gen = TitleGenerator(provider_manager=manager)
        options = gen.generate_titles_and_description(
            topic="Ocean Trench Sound",
            script_summary="Scientists recorded metallic pulse in trench",
            category="amazing_facts"
        )
        assert options.primary_title == "The Deepest Sound on Earth"
        assert len(options.variations) == 3
        assert len(options.description) > 10

    def test_hashtag_generator(self):
        mock_provider = MockAIProvider(name="mock")
        manager = AIProviderManager()
        manager.providers["mock"] = mock_provider
        manager.priority = ["mock"]

        gen = HashtagGenerator(provider_manager=manager)
        tags = gen.generate_hashtags(
            topic="Deep Sea",
            category="amazing_facts",
            target_platforms=["youtube", "instagram", "tiktok"]
        )
        assert "youtube" in tags
        assert "#Shorts" in tags["youtube"]
        assert "instagram" in tags
        assert "#reels" in tags["instagram"]

    def test_fact_checker_audit(self):
        mock_provider = MockAIProvider(name="mock")
        manager = AIProviderManager()
        manager.providers["mock"] = mock_provider
        manager.priority = ["mock"]

        checker = FactChecker(provider_manager=manager)
        result = checker.check_script(
            title="The Mariana Trench Mystery",
            narration_text="Scientists detected minke whale calls at extreme ocean depth.",
            category="amazing_facts"
        )
        assert result.verdict == "PASS"
        assert result.accuracy_score >= 80.0
        assert result.is_safe is True
