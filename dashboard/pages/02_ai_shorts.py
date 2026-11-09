"""
Dashboard Page 2 — AI Shorts Generator
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">✂️ AI Shorts Generator</div>', unsafe_allow_html=True)

st.info("**Engine 1 — AI Shorts Generator** will be fully implemented in Phase 5.")

st.markdown("### Supported Content Categories")
categories = {
    "🌍 Amazing Facts & Mysteries": "Fascinating world facts, unexplained phenomena, historical mysteries.",
    "💪 Motivation & Success": "Inspirational stories, success mindsets, life lessons.",
    "🤖 AI & Technology": "Latest AI breakthroughs, tech innovations, future predictions.",
    "👻 Horror & Scary Stories": "Suspenseful stories, creepy facts, unexplained events.",
    "⚽ Football Facts": "Remarkable football moments, records, player stories.",
    "🏏 Cricket Facts": "Cricket history, records, legendary moments.",
}

for cat, desc in categories.items():
    with st.expander(cat):
        st.write(desc)
        st.markdown("**Status:** 🟡 Planned — Phase 5")

st.markdown("---")
st.markdown("### Production Workflow")
steps = [
    "1. Select category",
    "2. Generate original ideas via AI",
    "3. Score and select best idea",
    "4. Write 45-second script with strong hook",
    "5. Generate voiceover (edge-tts / pyttsx3)",
    "6. Source licensed footage (Pexels / Pixabay)",
    "7. Generate subtitles (Whisper)",
    "8. Render vertical video (FFmpeg + NVENC)",
    "9. Add background music + SFX",
    "10. Generate title, description, hashtags",
    "11. Quality check",
    "12. Send to publishing queue",
]
for step in steps:
    st.markdown(f"- {step}")
