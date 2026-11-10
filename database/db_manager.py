"""
AI-CONTENT-AUTOMATION — Database Manager
==========================================
Uses Python's built-in sqlite3 module directly.
No external ORM dependency — maximises compatibility.
SQLAlchemy is available for engine-level operations in later phases,
but the core database manager uses only stdlib sqlite3.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, Any

from config import config
from core.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Central database manager using Python's built-in sqlite3.
    Thread-safe via check_same_thread=False with per-operation connections.
    """

    def __init__(self, db_path: Optional[Any] = None):
        self.db_path = Path(db_path) if db_path else config.database.path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database path: {self.db_path}")

    def set_path(self, new_path: Any):
        """Switches database path dynamically (used in testing)."""
        self.db_path = Path(new_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database path switched to: {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        """Create a new SQLite connection with optimal settings."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Rows accessible as dicts
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    @contextmanager
    def _get_conn(self):
        """Context manager for a database connection with auto-commit/rollback."""
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialise_schema(self):
        """
        Creates all tables if they don't exist. Safe to call multiple times.
        """
        logger.info("Initialising database schema...")
        with self._get_conn() as conn:
            # Try to load from SQL file first
            schema_file = Path(__file__).parent / "migrations" / "001_initial_schema.sql"
            if schema_file.exists():
                # Execute each statement separately (sqlite3 doesn't support executescript in WAL)
                sql_text = schema_file.read_text(encoding="utf-8")
                # Filter out PRAGMA lines (already set in connect) and execute rest
                statements = [s.strip() for s in sql_text.split(";") if s.strip()]
                for stmt in statements:
                    if stmt.upper().startswith("PRAGMA"):
                        continue
                    if stmt.upper().startswith("--"):
                        continue
                    if stmt:
                        conn.execute(stmt)
                logger.info("Schema applied from SQL file")
            else:
                self._create_tables(conn)
                logger.info("Schema created inline")

    def _create_tables(self, conn: sqlite3.Connection):
        """Create all tables (inline fallback)."""

        tables = [
            """CREATE TABLE IF NOT EXISTS ideas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                engine      TEXT NOT NULL,
                category    TEXT,
                title       TEXT NOT NULL,
                concept     TEXT,
                hook        TEXT,
                score       REAL DEFAULT 0,
                used        INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS scripts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id     INTEGER REFERENCES ideas(id),
                engine      TEXT NOT NULL,
                title       TEXT,
                content     TEXT NOT NULL,
                word_count  INTEGER DEFAULT 0,
                duration_s  REAL DEFAULT 0,
                status      TEXT DEFAULT 'draft',
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS videos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                engine          TEXT NOT NULL,
                script_id       INTEGER REFERENCES scripts(id),
                title           TEXT,
                description     TEXT,
                hashtags        TEXT,
                file_path       TEXT,
                thumbnail_path  TEXT,
                subtitle_path   TEXT,
                duration_s      REAL DEFAULT 0,
                format          TEXT DEFAULT 'vertical',
                resolution      TEXT DEFAULT '1080x1920',
                file_size_mb    REAL DEFAULT 0,
                content_hash    TEXT,
                status          TEXT DEFAULT 'pending',
                quality_score   REAL DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now')),
                updated_at      TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS streamers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                platform        TEXT NOT NULL DEFAULT 'twitch',
                username        TEXT NOT NULL,
                display_name    TEXT,
                channel_id      TEXT,
                permission      TEXT DEFAULT 'NOT_AUTHORISED',
                notes           TEXT,
                active          INTEGER DEFAULT 1,
                created_at      TEXT DEFAULT (datetime('now')),
                UNIQUE(platform, username)
            )""",

            """CREATE TABLE IF NOT EXISTS stream_sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                streamer_id     INTEGER REFERENCES streamers(id),
                stream_id       TEXT,
                title           TEXT,
                game            TEXT,
                started_at      TEXT,
                ended_at        TEXT,
                vod_url         TEXT,
                status          TEXT DEFAULT 'active',
                created_at      TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS clips (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                streamer_id     INTEGER REFERENCES streamers(id),
                session_id      INTEGER REFERENCES stream_sessions(id),
                clip_id         TEXT,
                source          TEXT,
                title           TEXT,
                start_time      REAL,
                end_time        REAL,
                duration_s      REAL,
                score           REAL DEFAULT 0,
                score_breakdown TEXT,
                permission      TEXT DEFAULT 'PENDING',
                file_path       TEXT,
                content_hash    TEXT,
                view_count      INTEGER DEFAULT 0,
                status          TEXT DEFAULT 'candidate',
                created_at      TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS permissions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type     TEXT NOT NULL,
                entity_id       INTEGER NOT NULL,
                status          TEXT NOT NULL DEFAULT 'PENDING',
                granted_by      TEXT,
                notes           TEXT,
                evidence_path   TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                updated_at      TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS publishing_jobs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id        INTEGER REFERENCES videos(id),
                platform        TEXT NOT NULL,
                scheduled_at    TEXT,
                published_at    TEXT,
                platform_id     TEXT,
                platform_url    TEXT,
                status          TEXT DEFAULT 'queued',
                error_message   TEXT,
                retry_count     INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now')),
                updated_at      TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS platform_connections (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                platform        TEXT NOT NULL UNIQUE,
                status          TEXT DEFAULT 'NOT_CONNECTED',
                account_name    TEXT,
                access_token    TEXT,
                refresh_token   TEXT,
                token_expiry    TEXT,
                scope           TEXT,
                notes           TEXT,
                updated_at      TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS scheduler_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name        TEXT NOT NULL,
                engine          TEXT,
                category        TEXT,
                triggered_at    TEXT DEFAULT (datetime('now')),
                completed_at    TEXT,
                status          TEXT DEFAULT 'running',
                error_message   TEXT,
                video_id        INTEGER REFERENCES videos(id)
            )""",

            """CREATE TABLE IF NOT EXISTS analytics_events (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type      TEXT NOT NULL,
                engine          TEXT,
                platform        TEXT,
                video_id        INTEGER,
                value           REAL DEFAULT 0,
                metadata        TEXT,
                created_at      TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS app_settings (
                key         TEXT PRIMARY KEY,
                value       TEXT,
                updated_at  TEXT DEFAULT (datetime('now'))
            )""",
        ]

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)",
            "CREATE INDEX IF NOT EXISTS idx_videos_engine ON videos(engine)",
            "CREATE INDEX IF NOT EXISTS idx_videos_hash ON videos(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON publishing_jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_platform ON publishing_jobs(platform)",
            "CREATE INDEX IF NOT EXISTS idx_clips_score ON clips(score)",
            "CREATE INDEX IF NOT EXISTS idx_scheduler_status ON scheduler_history(status)",
        ]

        for sql in tables + indexes:
            conn.execute(sql)

        logger.info("All database tables and indexes created.")

    def execute(self, sql: str, params: Optional[dict] = None) -> int:
        """
        Execute a write operation (INSERT/UPDATE/DELETE).
        Returns the last inserted row ID (for INSERTs).
        """
        with self._get_conn() as conn:
            cursor = conn.execute(sql, params or {})
            return cursor.lastrowid

    def fetchall(self, sql: str, params: Optional[dict] = None) -> list[dict]:
        """Execute a SELECT and return all matching rows as dicts."""
        with self._get_conn() as conn:
            cursor = conn.execute(sql, params or {})
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def fetchone(self, sql: str, params: Optional[dict] = None) -> Optional[dict]:
        """Execute a SELECT and return the first row as a dict (or None)."""
        with self._get_conn() as conn:
            cursor = conn.execute(sql, params or {})
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute_many(self, sql: str, params_list: list[dict]):
        """Execute the same SQL with multiple parameter sets (bulk operations)."""
        with self._get_conn() as conn:
            conn.executemany(sql, params_list)

    def get_setting(self, key: str, default: str = "") -> str:
        """Get an application setting from the key-value store."""
        row = self.fetchone("SELECT value FROM app_settings WHERE key=?", (key,))
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        """Store an application setting."""
        self.execute("""
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (key, value))

    def health_check(self) -> dict:
        """Returns database health status and table counts."""
        try:
            # Simple connectivity test
            self.fetchone("SELECT 1 as ok")

            stats = {}
            for table in ["ideas", "scripts", "videos", "publishing_jobs", "scheduler_history"]:
                row = self.fetchone(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = row["count"] if row else 0

            size = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            return {
                "status": "healthy",
                "path": str(self.db_path),
                "size_mb": round(size, 3),
                "tables": stats,
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "error": str(e)}


# ── Singleton instance ────────────────────────────────────────────────────────
db = DatabaseManager()
