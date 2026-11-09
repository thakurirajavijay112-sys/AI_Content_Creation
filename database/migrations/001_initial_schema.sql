-- ============================================================
-- AI-CONTENT-AUTOMATION — Initial Database Schema
-- Migration: 001
-- Applied by: database/db_manager.py
-- ============================================================
-- This file is used as a reference. The schema is also
-- defined inline in db_manager.py for resilience.
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS ideas (
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
);

CREATE TABLE IF NOT EXISTS scripts (
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
);

CREATE TABLE IF NOT EXISTS videos (
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
);

CREATE TABLE IF NOT EXISTS streamers (
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
);

CREATE TABLE IF NOT EXISTS stream_sessions (
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
);

CREATE TABLE IF NOT EXISTS clips (
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
);

CREATE TABLE IF NOT EXISTS permissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT NOT NULL,
    entity_id       INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    granted_by      TEXT,
    notes           TEXT,
    evidence_path   TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS publishing_jobs (
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
);

CREATE TABLE IF NOT EXISTS platform_connections (
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
);

CREATE TABLE IF NOT EXISTS scheduler_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name        TEXT NOT NULL,
    engine          TEXT,
    category        TEXT,
    triggered_at    TEXT DEFAULT (datetime('now')),
    completed_at    TEXT,
    status          TEXT DEFAULT 'running',
    error_message   TEXT,
    video_id        INTEGER REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      TEXT NOT NULL,
    engine          TEXT,
    platform        TEXT,
    video_id        INTEGER,
    value           REAL DEFAULT 0,
    metadata        TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS app_settings (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_engine ON videos(engine);
CREATE INDEX IF NOT EXISTS idx_videos_hash ON videos(content_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON publishing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_platform ON publishing_jobs(platform);
CREATE INDEX IF NOT EXISTS idx_clips_score ON clips(score);
CREATE INDEX IF NOT EXISTS idx_scheduler_status ON scheduler_history(status);
