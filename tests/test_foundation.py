"""
AI-CONTENT-AUTOMATION — Tests: Foundation
==========================================
Tests for Phase 2 components: config, database, logging, permissions.
Run with: pytest tests/test_foundation.py -v
"""

import sys
import pytest
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Tests for the central configuration system."""

    def test_config_loads(self):
        """Config should load without raising exceptions."""
        from config import config
        assert config is not None

    def test_config_has_all_sections(self):
        """Config should have all required sections."""
        from config import config
        assert hasattr(config, "app")
        assert hasattr(config, "database")
        assert hasattr(config, "ai")
        assert hasattr(config, "tts")
        assert hasattr(config, "whisper")
        assert hasattr(config, "video")
        assert hasattr(config, "scheduler")
        assert hasattr(config, "publishing")
        assert hasattr(config, "dashboard")
        assert hasattr(config, "shorts")
        assert hasattr(config, "clipper")
        assert hasattr(config, "youtuber")

    def test_config_defaults(self):
        """Config defaults should be sensible."""
        from config import config
        assert config.app.timezone == "Asia/Kathmandu"
        assert config.scheduler.daily_limit == 3
        assert config.shorts.default_duration == 45
        assert config.dashboard.port == 8501

    def test_config_validate_returns_list(self):
        """validate() should always return a list."""
        from config import config
        result = config.validate()
        assert isinstance(result, list)

    def test_config_summary_has_no_secrets(self):
        """summary() must not expose API keys or secrets."""
        from config import config
        summary = config.summary()
        summary_str = str(summary).lower()
        # Should not contain obvious secret patterns
        assert "secret" not in summary_str
        assert "password" not in summary_str
        # Should not contain actual key values (they'd be long strings)
        for value in summary.values():
            if isinstance(value, str):
                assert len(value) < 100, f"Suspicious long value in summary: {value[:20]}..."

    def test_database_path_is_absolute(self):
        """Database path should resolve to an absolute path."""
        from config import config
        assert config.database.path.is_absolute()

    def test_shorts_categories_not_empty(self):
        """Shorts categories list should not be empty."""
        from config import config
        assert len(config.shorts.categories) > 0


class TestDatabase:
    """Tests for the database manager."""

    @pytest.fixture(autouse=True)
    def _use_test_db(self, tmp_path, monkeypatch):
        """Redirect database to a temporary file for each test."""
        import os
        test_db = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_PATH", str(test_db))
        # Reload config and db with new path
        import importlib
        import config as config_module
        importlib.reload(config_module)
        import database.db_manager as db_module
        importlib.reload(db_module)

    def test_db_initialises(self):
        """Database schema should initialise without errors."""
        from database.db_manager import DatabaseManager
        from config import config
        manager = DatabaseManager()
        manager.initialise_schema()
        health = manager.health_check()
        assert health["status"] == "healthy"

    def test_db_tables_exist(self):
        """All required tables should exist after initialisation."""
        from database.db_manager import DatabaseManager
        manager = DatabaseManager()
        manager.initialise_schema()

        tables = ["ideas", "scripts", "videos", "streamers", "stream_sessions",
                  "clips", "permissions", "publishing_jobs", "platform_connections",
                  "scheduler_history", "analytics_events", "app_settings"]

        for table in tables:
            result = manager.fetchone(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            assert result is not None, f"Table '{table}' not found in database"

    def test_db_insert_and_fetch(self):
        """Should be able to insert and retrieve a record."""
        from database.db_manager import DatabaseManager
        manager = DatabaseManager()
        manager.initialise_schema()

        # Insert an idea
        manager.execute("""
            INSERT INTO ideas (engine, category, title, concept, score)
            VALUES (:engine, :cat, :title, :concept, :score)
        """, {
            "engine": "ai_shorts",
            "cat": "amazing_facts",
            "title": "Test Idea",
            "concept": "A test concept",
            "score": 85.5,
        })

        # Fetch it back
        row = manager.fetchone(
            "SELECT * FROM ideas WHERE title=:title",
            {"title": "Test Idea"}
        )
        assert row is not None
        assert row["engine"] == "ai_shorts"
        assert row["score"] == 85.5

    def test_db_health_check_returns_dict(self):
        """Health check should return a dict with status key."""
        from database.db_manager import DatabaseManager
        manager = DatabaseManager()
        manager.initialise_schema()
        health = manager.health_check()
        assert isinstance(health, dict)
        assert "status" in health
        assert health["status"] in ("healthy", "error")


class TestPermissions:
    """Tests for the permission manager."""

    def test_default_permission_is_not_authorised(self):
        """Unknown entities should default to NOT_AUTHORISED."""
        from permissions.permission_manager import PermissionManager, PermissionStatus
        from database.db_manager import DatabaseManager
        from config import config

        manager = PermissionManager()
        status = manager.get_permission("clip", 99999)
        assert status == PermissionStatus.NOT_AUTHORISED

    def test_not_authorised_entity_is_blocked(self):
        """is_authorised() should return False for NOT_AUTHORISED entities."""
        from permissions.permission_manager import PermissionManager
        manager = PermissionManager()
        assert manager.is_authorised("clip", 99999) is False


class TestProjectStructure:
    """Verify all required directories and files exist."""

    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent

    def test_required_dirs_exist(self, project_root):
        required_dirs = [
            "engines/ai_shorts", "engines/streamer_clipper", "engines/youtuber_engine",
            "ai", "audio", "video", "integrations", "publishers", "permissions",
            "scheduler", "database", "analytics", "dashboard", "dashboard/pages",
            "generated", "assets", "logs", "tests", "core",
        ]
        for d in required_dirs:
            path = project_root / d
            assert path.exists(), f"Required directory missing: {d}"

    def test_required_files_exist(self, project_root):
        required_files = [
            "main.py", "config.py", "requirements.txt", ".env.example", ".gitignore",
            "database/db_manager.py",
            "permissions/permission_manager.py",
            "dashboard/app.py",
            "core/logger.py",
        ]
        for f in required_files:
            path = project_root / f
            assert path.exists(), f"Required file missing: {f}"

    def test_no_env_file_committed(self, project_root):
        """The actual .env file should not exist in the project (only .env.example)."""
        # Note: .env SHOULD be in .gitignore — this test just verifies we
        # haven't accidentally created a .env with real credentials.
        env_file = project_root / ".env"
        if env_file.exists():
            content = env_file.read_text()
            assert "your_gemini_api_key_here" in content or len(content) < 100, \
                ".env file appears to contain real credentials — do not commit!"
