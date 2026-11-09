"""Dashboard Page 7 — Scheduler"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">⏰ Scheduler</div>', unsafe_allow_html=True)

st.warning("""
⚠️ **Windows Limitation:** The scheduler is a Python process that must be running continuously.
It **cannot** produce videos while your computer is off, asleep, or hibernating.

To ensure scheduled videos are produced:
- Keep your computer on and awake during scheduled times, **or**
- Run `python main.py scheduler` in a terminal and keep it open
""")

try:
    from config import config
    sched = config.scheduler

    st.markdown("### Current Schedule (Nepal Standard Time — UTC+5:45)")
    st.markdown(f"| Time | Purpose |")
    st.markdown(f"|------|---------|")
    st.markdown(f"| {sched.time_1} NST | Video 1 |")
    st.markdown(f"| {sched.time_2} NST | Video 2 |")
    st.markdown(f"| {sched.time_3} NST | Video 3 |")

    st.markdown(f"**Daily limit:** {sched.daily_limit} videos")
    st.markdown(f"**Manual approval required:** {'Yes' if sched.manual_approval else 'No'}")
    st.markdown(f"**Scheduler enabled:** {'Yes' if sched.enabled else 'No'}")

except Exception as e:
    st.error(f"Could not load scheduler config: {e}")

st.markdown("---")
st.markdown("### Execution History")

try:
    from database.db_manager import db
    db.initialise_schema()
    history = db.fetchall("""
        SELECT job_name, engine, category, triggered_at, status, error_message
        FROM scheduler_history ORDER BY triggered_at DESC LIMIT 20
    """)
    if history:
        for h in history:
            icon = "🟢" if h["status"] == "completed" else ("🔴" if h["status"] == "failed" else "🟡")
            st.markdown(f"{icon} **{h['job_name']}** — {h['engine']} / {h['category']} — {h['triggered_at']} — {h['status']}")
    else:
        st.info("No scheduled jobs have run yet. Coming in Phase 9.")
except Exception as e:
    st.error(f"Error loading history: {e}")

st.markdown("---")
st.markdown("### Launch Scheduler")
st.code("python main.py scheduler", language="bash")
st.markdown("Run this in a terminal and keep it open to process scheduled jobs.")
