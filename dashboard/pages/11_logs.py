"""Dashboard Page 11 — Logs"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">📋 System Logs</div>', unsafe_allow_html=True)

LOG_DIR = Path(__file__).parent.parent.parent / "logs"

LOG_FILES = {
    "Application Log": LOG_DIR / "app.log",
    "Error Log": LOG_DIR / "errors.log",
    "Scheduler Log": LOG_DIR / "scheduler.log",
    "Publishing Log": LOG_DIR / "publishing.log",
}

selected_log = st.selectbox("Select log file", list(LOG_FILES.keys()))
log_path = LOG_FILES[selected_log]

col1, col2, col3 = st.columns(3)
with col1:
    lines_to_show = st.number_input("Lines to show", min_value=10, max_value=500, value=100)
with col2:
    filter_text = st.text_input("Filter (contains)", "")
with col3:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()

if log_path.exists():
    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")

        if filter_text:
            lines = [l for l in lines if filter_text.lower() in l.lower()]

        # Show last N lines
        display_lines = lines[-lines_to_show:]
        display_text = "\n".join(display_lines)

        st.text_area(
            f"{selected_log} (last {lines_to_show} lines)",
            display_text,
            height=400,
        )

        # Stats
        st.caption(f"Total lines: {len(lines)} | File size: {log_path.stat().st_size / 1024:.1f} KB")

        # Download button
        st.download_button(
            label="⬇ Download full log",
            data=content.encode("utf-8"),
            file_name=log_path.name,
            mime="text/plain",
        )
    except Exception as e:
        st.error(f"Error reading log: {e}")
else:
    st.info(f"Log file not found: `{log_path}`")
    st.markdown("Log files are created when the application runs and produces output.")
    st.markdown("Run `python main.py init` to start generating logs.")
