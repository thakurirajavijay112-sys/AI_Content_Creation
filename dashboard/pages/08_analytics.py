"""Dashboard Page 8 — Analytics"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
import pandas as pd

st.markdown('<div class="section-header">📈 Analytics</div>', unsafe_allow_html=True)

try:
    from database.db_manager import db
    db.initialise_schema()

    # Videos by engine
    engine_data = db.fetchall("""
        SELECT engine, COUNT(*) as count, AVG(quality_score) as avg_quality
        FROM videos GROUP BY engine
    """)

    # Jobs by platform
    platform_data = db.fetchall("""
        SELECT platform, COUNT(*) as total,
               SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) as published,
               SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
        FROM publishing_jobs GROUP BY platform
    """)

    if engine_data:
        st.markdown("### Videos by Engine")
        df_engine = pd.DataFrame(engine_data)
        st.dataframe(df_engine, use_container_width=True)
    else:
        st.info("No video data yet. Analytics will populate as videos are generated.")

    if platform_data:
        st.markdown("### Publishing by Platform")
        df_platform = pd.DataFrame(platform_data)
        st.dataframe(df_platform, use_container_width=True)
    else:
        st.info("No publishing data yet.")

    st.markdown("---")
    st.info("📊 Detailed charts, trends, and performance analytics will be added in Phase 9.")

except Exception as e:
    st.error(f"Analytics error: {e}")
