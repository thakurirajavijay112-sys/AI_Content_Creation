"""Dashboard Page 3 — Streamer Clipper"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">🎮 Streamer Clipper</div>', unsafe_allow_html=True)
st.info("**Engine 2 — Streamer Clipper** will be fully implemented in Phase 6.")

tab1, tab2 = st.tabs(["Mode A: Live Monitor", "Mode B: Clip Discovery"])

with tab1:
    st.markdown("### Mode A — Live Stream Monitoring")
    st.markdown("""
    - Track a configurable list of streamers on Twitch
    - Detect when streamers go live (official API)
    - Analyse footage, audio, and chat activity
    - Detect exciting gameplay, funny moments, and emotional reactions
    - Generate clip timestamps from highlight candidates
    - **Requires:** Broadcaster/editor permission from each streamer
    """)
    st.warning("⚠️ Only processes footage from streamers who have granted permission.")

with tab2:
    st.markdown("### Mode B — Existing Clip Discovery")
    st.markdown("""
    - Discover public clips via official Twitch Clips API
    - Search by streamer, game, or popularity
    - Prioritises GTA 6 and other popular categories
    - Retrieves metadata and engagement statistics
    - Ranks clips by popularity and relevance
    - **Requires:** Creator permission before any editing or reposting
    """)

st.markdown("---")
st.markdown("### Moment Detection Scoring System")
scores = {
    "Excitement & Reactions": 25,
    "Interesting Dialogue": 20,
    "Funny / Unexpected Moments": 20,
    "Chat Activity Spikes": 15,
    "Gameplay Action": 10,
    "Replay Value": 10,
}
for criterion, points in scores.items():
    col1, col2 = st.columns([3, 1])
    col1.write(criterion)
    col2.write(f"**{points} pts**")
    st.progress(points / 100)

st.info("ℹ️ This scoring system helps identify interesting moments — it does not guarantee virality.")

st.markdown("---")
st.markdown("### Permission States")
permissions = [
    ("AUTHORISED", "green", "Creator has explicitly granted reuse rights"),
    ("CREATOR_PROVIDED", "green", "Creator directly provided the footage"),
    ("PENDING", "orange", "Awaiting creator approval"),
    ("NOT_AUTHORISED", "red", "No permission — cannot process or upload"),
]
for state, color, desc in permissions:
    st.markdown(f":{color}[**{state}**] — {desc}")
