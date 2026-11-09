"""Dashboard Page 10 — Settings"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">⚙️ Settings</div>', unsafe_allow_html=True)

st.info("Settings are managed through the `.env` file. Edit it in your project root and restart the dashboard.")

try:
    from config import config

    st.markdown("### Current Configuration (read-only)")
    summary = config.summary()

    for key, value in summary.items():
        col1, col2 = st.columns([2, 3])
        col1.markdown(f"**{key.replace('_', ' ').title()}**")
        if isinstance(value, bool):
            col2.markdown("✅ Yes" if value else "❌ No")
        elif isinstance(value, list):
            col2.markdown(", ".join(str(v) for v in value))
        else:
            col2.markdown(str(value))

    st.markdown("---")
    st.markdown("### Edit Configuration")
    st.markdown("Open `.env` in your editor:")
    st.code("code .env", language="bash")
    st.markdown("Or copy the template:")
    st.code("copy .env.example .env", language="bash")

    st.markdown("---")
    st.markdown("### Configuration Warnings")
    warnings = config.validate()
    if warnings:
        for w in warnings:
            st.warning(w)
    else:
        st.success("No configuration issues detected.")

except Exception as e:
    st.error(f"Could not load configuration: {e}")
    st.markdown("Run `python main.py init` to initialise the system.")

st.markdown("---")
st.markdown("### System Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Clear Dashboard Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared!")

with col2:
    if st.button("🔍 Run Dependency Check", use_container_width=True):
        st.info("Run `python main.py check` in your terminal for a full dependency report.")

with col3:
    if st.button("🗄️ Reinitialise Database", use_container_width=True):
        try:
            from database.db_manager import db
            db.initialise_schema()
            st.success("Database schema reinitialised.")
        except Exception as e:
            st.error(f"Error: {e}")
