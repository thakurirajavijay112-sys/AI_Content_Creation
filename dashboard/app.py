"""
AI-CONTENT-AUTOMATION — Streamlit Dashboard
============================================
Main dashboard entry point. Run with:
    streamlit run dashboard/app.py
Or via CLI:
    python main.py dashboard
"""

import sys
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Content Automation",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "AI-CONTENT-AUTOMATION — Automated Video Production System",
    },
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #e0e0e0; }

    /* Main content */
    .main { background-color: #0e1117; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 10px;
    }

    /* Status badges */
    .badge-green { background:#1a3a2a; color:#4ade80; border-radius:4px; padding:2px 8px; font-size:0.8em; }
    .badge-yellow { background:#3a2e1a; color:#fbbf24; border-radius:4px; padding:2px 8px; font-size:0.8em; }
    .badge-red { background:#3a1a1a; color:#f87171; border-radius:4px; padding:2px 8px; font-size:0.8em; }
    .badge-blue { background:#1a2a3a; color:#60a5fa; border-radius:4px; padding:2px 8px; font-size:0.8em; }
    .badge-gray { background:#2a2a2a; color:#9ca3af; border-radius:4px; padding:2px 8px; font-size:0.8em; }

    /* Section headers */
    .section-header {
        font-size: 1.5em;
        font-weight: bold;
        color: #60a5fa;
        margin-bottom: 1em;
        padding-bottom: 0.5em;
        border-bottom: 2px solid #2d3250;
    }

    /* Engine cards */
    .engine-card {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        transition: border-color 0.2s;
    }
    .engine-card:hover { border-color: #60a5fa; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎬 AI Content Automation")
    st.markdown("---")

    pages = {
        "📊 Overview": "overview",
        "✂️ AI Shorts Generator": "ai_shorts",
        "🎮 Streamer Clipper": "streamer_clipper",
        "📺 AI YouTuber Engine": "youtuber_engine",
        "📁 Video Library": "video_library",
        "📤 Publishing Queue": "publishing_queue",
        "⏰ Scheduler": "scheduler",
        "📈 Analytics": "analytics",
        "🔗 Platform Connections": "platforms",
        "⚙️ Settings": "settings",
        "📋 Logs": "logs",
    }

    if "current_page" not in st.session_state:
        st.session_state.current_page = "overview"

    for label, page_id in pages.items():
        if st.button(label, key=f"nav_{page_id}", use_container_width=True):
            st.session_state.current_page = page_id

    st.markdown("---")
    st.markdown("""
    <small style='color:#666'>
    ⚠️ Scheduler requires<br>this PC to stay awake.<br><br>
    Version: Phase 2<br>
    Timezone: Asia/Kathmandu
    </small>
    """, unsafe_allow_html=True)


# ── Route to pages ────────────────────────────────────────────────────────────
current = st.session_state.get("current_page", "overview")
pages_dir = Path(__file__).parent / "pages"

page_map = {
    "overview": pages_dir / "01_overview.py",
    "ai_shorts": pages_dir / "02_ai_shorts.py",
    "streamer_clipper": pages_dir / "03_streamer_clipper.py",
    "youtuber_engine": pages_dir / "04_youtuber_engine.py",
    "video_library": pages_dir / "05_video_library.py",
    "publishing_queue": pages_dir / "06_publishing_queue.py",
    "scheduler": pages_dir / "07_scheduler.py",
    "analytics": pages_dir / "08_analytics.py",
    "platforms": pages_dir / "09_platforms.py",
    "settings": pages_dir / "10_settings.py",
    "logs": pages_dir / "11_logs.py",
}

target_page = page_map.get(current)
if target_page and target_page.exists():
    exec(compile(target_page.read_text(encoding="utf-8"), str(target_page), "exec"))
else:
    st.error(f"Page '{current}' not found. This may not be implemented yet.")
