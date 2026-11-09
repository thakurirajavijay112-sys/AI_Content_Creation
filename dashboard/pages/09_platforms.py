"""Dashboard Page 9 — Platform Connections"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.markdown('<div class="section-header">🔗 Platform Connections</div>', unsafe_allow_html=True)

PLATFORMS = {
    "YouTube": {
        "icon": "🔴",
        "api": "YouTube Data API v3",
        "status_note": "Mature API — upload Shorts + regular videos",
        "quota": "10,000 units/day free (~6 uploads)",
        "setup": "Create a project at console.cloud.google.com, enable YouTube Data API v3, generate OAuth credentials.",
        "phase": "Phase 8",
        "env_keys": ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"],
    },
    "Instagram": {
        "icon": "🟣",
        "api": "Meta Graph API",
        "status_note": "Requires Professional Account + Meta app review",
        "quota": "Meta rate limits apply",
        "setup": "Register at developers.facebook.com. App review required before public posting.",
        "phase": "Phase 8",
        "env_keys": ["META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN"],
    },
    "Facebook": {
        "icon": "🔵",
        "api": "Meta Graph API",
        "status_note": "Requires Facebook Page (not personal profile)",
        "quota": "Meta rate limits apply",
        "setup": "Same Meta app as Instagram. Requires a Page with admin access.",
        "phase": "Phase 8",
        "env_keys": ["META_APP_ID", "META_APP_SECRET"],
    },
    "TikTok": {
        "icon": "⚫",
        "api": "Content Posting API",
        "status_note": "New apps post privately until TikTok audits your app",
        "quota": "Per-request limits",
        "setup": "Register at developers.tiktok.com. Apply for Content Posting API. Expect weeks for audit.",
        "phase": "Phase 8",
        "env_keys": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
    },
    "Snapchat": {
        "icon": "🟡",
        "api": "Public Profile API",
        "status_note": "Partner access required — approval needed",
        "quota": "Partner-dependent",
        "setup": "Apply for Partner access at developers.snap.com. Standard accounts cannot publish programmatically.",
        "phase": "Phase 8 (investigative)",
        "env_keys": ["SNAPCHAT_CLIENT_ID", "SNAPCHAT_CLIENT_SECRET"],
    },
    "Twitch": {
        "icon": "🟣",
        "api": "Twitch API + Clip API",
        "status_note": "Clip integration + live stream. No general short-video upload endpoint.",
        "quota": "Standard API rate limits",
        "setup": "Register at dev.twitch.tv. OAuth with broadcaster or editor scope for clip creation.",
        "phase": "Phase 8",
        "env_keys": ["TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET"],
    },
    "Kick": {
        "icon": "🟢",
        "api": "RTMP Livestream only",
        "status_note": "No general publishing API as of 2026. Livestream via RTMP stream key.",
        "quota": "N/A",
        "setup": "Get stream key from Kick dashboard. RTMP endpoint only — no video upload API.",
        "phase": "Phase 8 (limited)",
        "env_keys": ["KICK_STREAM_KEY"],
    },
}

try:
    from config import config
    from database.db_manager import db
    db.initialise_schema()
    connections = db.fetchall("SELECT platform, status, account_name FROM platform_connections")
    conn_map = {c["platform"].lower(): c for c in connections}
except Exception:
    conn_map = {}
    config = None

for platform_name, info in PLATFORMS.items():
    p_key = platform_name.lower()
    db_conn = conn_map.get(p_key, {})
    db_status = db_conn.get("status", "NOT_CONNECTED")

    with st.expander(f"{info['icon']} {platform_name} — {db_status}", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**API:** {info['api']}")
            st.markdown(f"**Note:** {info['status_note']}")
            st.markdown(f"**Quota:** {info['quota']}")
            st.markdown(f"**Phase:** {info['phase']}")
            st.markdown("**Setup instructions:**")
            st.info(info["setup"])

        with c2:
            st.markdown("**Required .env keys:**")
            if config:
                for key in info["env_keys"]:
                    val = __import__("os").environ.get(key, "")
                    is_set = bool(val) and "your_" not in val
                    icon = "✅" if is_set else "❌"
                    st.markdown(f"{icon} `{key}`")
            else:
                for key in info["env_keys"]:
                    st.markdown(f"❓ `{key}`")

            if db_status == "NOT_CONNECTED":
                st.markdown("**Status:** Not connected")
                st.markdown(f"→ Configure in `.env` then connect in Phase 8")
            elif db_status == "CONNECTED":
                st.success("Connected")
                account = db_conn.get("account_name", "")
                if account:
                    st.markdown(f"Account: {account}")

st.markdown("---")
st.info("🔗 Platform OAuth connections will be implemented in Phase 8. Configure `.env` keys now to be ready.")
