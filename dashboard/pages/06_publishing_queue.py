"""Dashboard Page 6 — Publishing Queue"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">📤 Publishing Queue</div>', unsafe_allow_html=True)

@st.cache_data(ttl=15)
def _load_queue():
    try:
        from database.db_manager import db
        db.initialise_schema()
        return db.fetchall("""
            SELECT pj.id, pj.platform, pj.status, pj.scheduled_at, pj.published_at,
                   pj.retry_count, pj.error_message, v.title as video_title
            FROM publishing_jobs pj
            LEFT JOIN videos v ON pj.video_id = v.id
            ORDER BY pj.created_at DESC LIMIT 50
        """), None
    except Exception as e:
        return [], str(e)

jobs, error = _load_queue()

if error:
    st.error(f"Error: {error}")
else:
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    queued = [j for j in jobs if j["status"] == "queued"]
    published = [j for j in jobs if j["status"] == "published"]
    failed = [j for j in jobs if j["status"] == "failed"]
    running = [j for j in jobs if j["status"] == "running"]

    col1.metric("Queued", len(queued))
    col2.metric("Running", len(running))
    col3.metric("Published", len(published))
    col4.metric("Failed", len(failed))

    if not jobs:
        st.info("No publishing jobs yet. Jobs are created when videos are approved and scheduled.")
    else:
        status_colors = {
            "queued": "🔵", "running": "🟡", "published": "🟢",
            "failed": "🔴", "cancelled": "⚫"
        }
        for job in jobs:
            icon = status_colors.get(job["status"], "⚪")
            with st.expander(f"{icon} {job['platform'].upper()} — {job.get('video_title', 'Unknown')} — {job['status']}"):
                st.write(f"**Platform:** {job['platform']}")
                st.write(f"**Status:** {job['status']}")
                st.write(f"**Scheduled:** {job.get('scheduled_at', 'N/A')}")
                st.write(f"**Published:** {job.get('published_at', 'Not yet')}")
                st.write(f"**Retry count:** {job.get('retry_count', 0)}")
                if job.get("error_message"):
                    st.error(f"Error: {job['error_message']}")
                if job["status"] == "failed" and job.get("retry_count", 0) < 3:
                    if st.button("🔄 Retry", key=f"retry_{job['id']}"):
                        st.info("Retry functionality coming in Phase 9")
