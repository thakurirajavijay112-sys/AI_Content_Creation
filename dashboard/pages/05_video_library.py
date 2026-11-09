"""Dashboard Page 5 — Video Library"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">📁 Video Library</div>', unsafe_allow_html=True)

@st.cache_data(ttl=15)
def _load_videos():
    try:
        from database.db_manager import db
        db.initialise_schema()
        return db.fetchall("""
            SELECT id, engine, title, status, format, duration_s, file_size_mb,
                   quality_score, created_at, file_path, thumbnail_path
            FROM videos ORDER BY created_at DESC LIMIT 100
        """), None
    except Exception as e:
        return [], str(e)

videos, error = _load_videos()

if error:
    st.error(f"Error loading videos: {error}")
elif not videos:
    st.info("No videos generated yet. Videos will appear here after the engines produce content.")
    st.markdown("**To generate your first video:**")
    st.markdown("1. Complete Phase 3 (AI Services) setup")
    st.markdown("2. Navigate to the AI Shorts Generator page")
    st.markdown("3. Select a category and click Generate")
else:
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        engine_filter = st.selectbox("Filter by Engine",
            ["All", "ai_shorts", "streamer_clipper", "youtuber_engine"])
    with col2:
        status_filter = st.selectbox("Filter by Status",
            ["All", "pending", "approved", "rejected", "published", "failed"])
    with col3:
        st.metric("Total Videos", len(videos))

    # Apply filters
    filtered = videos
    if engine_filter != "All":
        filtered = [v for v in filtered if v["engine"] == engine_filter]
    if status_filter != "All":
        filtered = [v for v in filtered if v["status"] == status_filter]

    for video in filtered:
        with st.expander(f"🎬 {video.get('title', 'Untitled')} — {video['engine']} — {video['status']}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"**Engine:** {video['engine']}")
                st.write(f"**Status:** {video['status']}")
                st.write(f"**Format:** {video['format']} | **Duration:** {video.get('duration_s', 0):.1f}s")
                st.write(f"**Quality Score:** {video.get('quality_score', 0):.1f}/100")
                st.write(f"**Created:** {video['created_at']}")
            with c2:
                if video.get("file_path") and Path(video["file_path"]).exists():
                    if st.button("▶ Preview", key=f"preview_{video['id']}"):
                        st.video(video["file_path"])
                if video["status"] == "pending":
                    if st.button("✓ Approve", key=f"approve_{video['id']}"):
                        st.success("Approval functionality coming in Phase 9")
                    if st.button("✗ Reject", key=f"reject_{video['id']}"):
                        st.error("Rejection functionality coming in Phase 9")
