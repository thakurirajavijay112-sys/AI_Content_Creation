"""
Dashboard Page 1 — Overview
Shows the high-level system status, engine activity, and daily targets.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from datetime import datetime, timedelta
import pytz

st.markdown('<div class="section-header">📊 System Overview</div>', unsafe_allow_html=True)

# ── Load data safely ───────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def _load_stats():
    try:
        from database.db_manager import db
        db.initialise_schema()
        return {
            "total_videos": db.fetchone("SELECT COUNT(*) as c FROM videos")["c"],
            "pending_approval": db.fetchone("SELECT COUNT(*) as c FROM videos WHERE status='pending'")["c"],
            "published": db.fetchone("SELECT COUNT(*) as c FROM publishing_jobs WHERE status='published'")["c"],
            "failed": db.fetchone("SELECT COUNT(*) as c FROM publishing_jobs WHERE status='failed'")["c"],
            "queued_jobs": db.fetchone("SELECT COUNT(*) as c FROM publishing_jobs WHERE status='queued'")["c"],
            "total_ideas": db.fetchone("SELECT COUNT(*) as c FROM ideas")["c"],
            "db_ok": True,
        }
    except Exception as e:
        return {"error": str(e), "db_ok": False}


@st.cache_data(ttl=60)
def _load_config_summary():
    try:
        from config import config
        return config.summary(), config.validate()
    except Exception as e:
        return {}, [str(e)]


stats = _load_stats()
config_summary, config_warnings = _load_config_summary()

# ── Current time (Nepal) ──────────────────────────────────────────────────────
nst = pytz.timezone("Asia/Kathmandu")
now_nst = datetime.now(nst)
st.markdown(f"**Current time (NST):** {now_nst.strftime('%A, %d %B %Y — %H:%M:%S')}")

if not stats.get("db_ok"):
    st.error(f"Database error: {stats.get('error')}. Run `python main.py init` first.")
    st.stop()

# ── Key Metrics Row ────────────────────────────────────────────────────────────
st.markdown("### 🎯 Daily Target Progress")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Videos Generated", stats["total_videos"], help="All videos ever created")
with col2:
    st.metric("Awaiting Approval", stats["pending_approval"],
              delta="manual review needed" if stats["pending_approval"] > 0 else None,
              delta_color="inverse")
with col3:
    st.metric("Published", stats["published"], help="Successfully uploaded to platforms")
with col4:
    st.metric("Failed Uploads", stats["failed"],
              delta="needs attention" if stats["failed"] > 0 else None,
              delta_color="inverse")
with col5:
    target = config_summary.get("daily_limit", 3)
    today_count = 0  # Will be live in Phase 9
    st.metric("Today's Progress", f"{today_count}/{target}", help=f"Daily target: {target} videos")

# ── Engine Status Cards ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ⚙️ Engine Status")

eng_col1, eng_col2, eng_col3 = st.columns(3)

with eng_col1:
    st.markdown("""
    <div class="engine-card">
        <h3>✂️ AI Shorts Generator</h3>
        <p><span class="badge-yellow">Phase 2 — Foundation</span></p>
        <p>6 categories ready for content generation.<br>
        Implementation in Phase 5.</p>
        <small>Categories: Facts • Motivation • AI/Tech • Horror • Football • Cricket</small>
    </div>
    """, unsafe_allow_html=True)

with eng_col2:
    st.markdown("""
    <div class="engine-card">
        <h3>🎮 Streamer Clipper</h3>
        <p><span class="badge-yellow">Phase 2 — Foundation</span></p>
        <p>Mode A (Live) + Mode B (Discovery).<br>
        Twitch integration in Phase 6.</p>
        <small>Permission manager: active</small>
    </div>
    """, unsafe_allow_html=True)

with eng_col3:
    st.markdown("""
    <div class="engine-card">
        <h3>📺 AI YouTuber Engine</h3>
        <p><span class="badge-yellow">Phase 2 — Foundation</span></p>
        <p>Challenge + storytelling formats.<br>
        Full implementation in Phase 7.</p>
        <small>Formats: Shorts (9:16) • Long-form (16:9)</small>
    </div>
    """, unsafe_allow_html=True)

# ── Platform Connection Status ────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔗 Platform Status")

try:
    from database.db_manager import db
    connections = db.fetchall("SELECT platform, status, account_name FROM platform_connections")
    conn_map = {c["platform"]: c for c in connections}
except Exception:
    conn_map = {}

platforms = ["YouTube", "Instagram", "Facebook", "TikTok", "Snapchat", "Twitch", "Kick"]
p_cols = st.columns(len(platforms))

platform_badge = {
    "CONNECTED": ("badge-green", "✓ Connected"),
    "NOT_CONNECTED": ("badge-gray", "○ Not Connected"),
    "PERMISSION_REQUIRED": ("badge-yellow", "⚠ Permission Req."),
    "APPROVAL_REQUIRED": ("badge-yellow", "⚠ Approval Req."),
    "UNSUPPORTED": ("badge-red", "✗ Unsupported"),
    "ERROR": ("badge-red", "✗ Error"),
}

for i, platform in enumerate(platforms):
    with p_cols[i]:
        p_data = conn_map.get(platform.lower(), {})
        status = p_data.get("status", "NOT_CONNECTED")
        badge_cls, badge_text = platform_badge.get(status, ("badge-gray", status))
        st.markdown(f"**{platform}**")
        st.markdown(f'<span class="{badge_cls}">{badge_text}</span>', unsafe_allow_html=True)

# ── Scheduler Status ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ⏰ Scheduler")

sched_col1, sched_col2 = st.columns(2)
with sched_col1:
    scheduler_enabled = config_summary.get("scheduler_enabled", False)
    if scheduler_enabled:
        st.success("Scheduler is configured. Run `python main.py scheduler` to start.")
    else:
        st.warning("Scheduler is disabled. Enable in Settings or .env file.")

    st.info(
        "⚠️ **Important:** The scheduler only runs while this computer is **on and awake**. "
        "If the computer sleeps or shuts down, scheduled jobs will be delayed until the next session."
    )

with sched_col2:
    daily_limit = config_summary.get("daily_limit", 3)
    st.markdown(f"**Daily target:** {daily_limit} videos")
    st.markdown("**Default schedule (Nepal time):**")
    st.markdown("- 🕗 08:00 NST — Video 1")
    st.markdown("- 🕑 14:00 NST — Video 2")
    st.markdown("- 🕗 20:00 NST — Video 3")

# ── Config warnings ────────────────────────────────────────────────────────────
if config_warnings:
    st.markdown("---")
    st.markdown("### ⚠️ Configuration Issues")
    for w in config_warnings:
        st.warning(w)

# ── Quick actions ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🚀 Quick Actions")
qcol1, qcol2, qcol3, qcol4 = st.columns(4)

with qcol1:
    if st.button("🔄 Refresh Stats", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with qcol2:
    if st.button("🔗 Connect Platforms", use_container_width=True):
        st.session_state.current_page = "platforms"
        st.rerun()

with qcol3:
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.current_page = "settings"
        st.rerun()

with qcol4:
    if st.button("📋 View Logs", use_container_width=True):
        st.session_state.current_page = "logs"
        st.rerun()
