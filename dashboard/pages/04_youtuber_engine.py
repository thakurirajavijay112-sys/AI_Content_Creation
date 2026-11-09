"""Dashboard Page 4 — AI YouTuber Engine"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">📺 AI YouTuber Engine</div>', unsafe_allow_html=True)
st.info("**Engine 3 — AI YouTuber Engine** will be fully implemented in Phase 7.")

st.markdown("""
> Generates original entertaining YouTube videos inspired by high-retention challenge and 
> storytelling formats. Does **not** copy any creator's scripts, branding, or content.
""")

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Content Categories")
    categories = ["Challenges & Competitions", "Survival & Endurance",
                  "Treasure Hunts", "Mystery Challenges", "Interesting Experiments",
                  "Unusual Comparisons", "Gaming Challenges", "Entertainment",
                  "Storytelling", "Creative Short-Form"]
    for cat in categories:
        st.markdown(f"- {cat}")

with col2:
    st.markdown("### Creative Principles")
    principles = ["Strong hooks", "Curiosity-driven", "Escalating stakes",
                  "Compelling storytelling", "Suspense & tension", "Competition elements",
                  "Surprising outcomes", "Satisfying conclusions"]
    for p in principles:
        st.markdown(f"- {p}")

st.markdown("---")
st.markdown("### Video Formats")
fmt_col1, fmt_col2 = st.columns(2)
with fmt_col1:
    st.markdown("**Short-Form**")
    st.markdown("- Format: 9:16 vertical\n- Resolution: 1080×1920\n- Target: 45 seconds")

with fmt_col2:
    st.markdown("**Long-Form**")
    st.markdown("- Format: 16:9 horizontal\n- Resolution: 1920×1080\n- Configurable duration")

st.warning("""
⚠️ **Important:** This engine cannot autonomously perform real-world challenges or experiments.
Human participation, safety checks, filming, and approval are required where applicable.
""")
