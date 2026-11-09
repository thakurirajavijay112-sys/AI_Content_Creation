"""
Dashboard Page 2 — AI Shorts Generator
Interactive Content Studio for idea generation, script writing, and metadata generation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from ai.provider_manager import ai_provider_manager
from ai.idea_generator import IdeaGenerator, CATEGORIES
from ai.script_generator import ScriptGenerator
from ai.title_generator import TitleGenerator
from ai.hashtag_generator import HashtagGenerator
from ai.fact_checker import FactChecker
from database.db_manager import db

st.markdown('<div class="section-header">✂️ AI Shorts Generator Studio</div>', unsafe_allow_html=True)

# Provider status badge
provider_status = ai_provider_manager.get_status()
active_providers = ai_provider_manager.get_active_providers()

col_status1, col_status2 = st.columns([3, 1])
with col_status1:
    if active_providers:
        st.success(f"🟢 Active AI Providers: **{', '.join([p.upper() for p in active_providers])}**")
    else:
        st.warning("⚠️ No AI provider configured yet. Add `GEMINI_API_KEY` to `.env` or start Ollama (`ollama serve`).")
with col_status2:
    st.caption(f"Priority: {', '.join(provider_status['priority'])}")

tab1, tab2, tab3 = st.tabs(["💡 1. Idea Generator", "📝 2. Script & Storyboard Studio", "🏷️ 3. Metadata & Fact Audit"])

# ── TAB 1: Idea Generator ──────────────────────────────────────────────────────
with tab1:
    st.markdown("### Generate & Score Original Video Ideas")
    cat_keys = list(CATEGORIES.keys())
    cat_labels = [k.replace("_", " ").title() for k in cat_keys]
    
    selected_idx = st.selectbox(
        "Choose Content Category",
        range(len(cat_keys)),
        format_func=lambda i: cat_labels[i]
    )
    selected_cat = cat_keys[selected_idx]
    st.caption(CATEGORIES[selected_cat])

    c_count, c_btn = st.columns([1, 2])
    with c_count:
        num_ideas = st.number_input("Ideas to generate", min_value=1, max_value=5, value=3)
    with c_btn:
        st.write("")
        st.write("")
        generate_btn = st.button("🚀 Generate New Ideas with AI", use_container_width=True)

    if generate_btn:
        with st.spinner("AI is researching and scoring original concepts..."):
            try:
                gen = IdeaGenerator()
                new_ideas = gen.generate_ideas(category=selected_cat, count=num_ideas)
                st.success(f"Generated {len(new_ideas)} fresh concepts!")
            except Exception as e:
                st.error(f"Generation error: {e}")

    # Display ideas stored in database
    st.markdown("---")
    st.markdown("#### Saved Ideas for this Category")
    saved_ideas = db.fetchall(
        "SELECT id, title, concept, hook, score, used, created_at FROM ideas WHERE category=:cat ORDER BY score DESC, created_at DESC LIMIT 15",
        {"cat": selected_cat}
    )

    if not saved_ideas:
        st.info("No ideas generated for this category yet. Click the button above to create some!")
    else:
        for idea in saved_ideas:
            status_tag = "🔴 (Used in Script)" if idea["used"] else "🟢 (Available)"
            with st.expander(f"⭐ {idea['score']:.1f}/100 — **{idea['title']}** {status_tag}"):
                st.markdown(f"**Concept:** {idea['concept']}")
                st.markdown(f"**Opening Hook:** *\"{idea['hook']}\"*")
                st.caption(f"ID #{idea['id']} | Created: {idea['created_at']}")
                
                if st.button("📝 Select & Write Script", key=f"use_idea_{idea['id']}"):
                    st.session_state["active_idea_id"] = idea["id"]
                    st.session_state["active_idea_title"] = idea["title"]
                    st.session_state["active_idea_concept"] = idea["concept"]
                    st.session_state["active_idea_hook"] = idea["hook"]
                    st.session_state["active_idea_category"] = selected_cat
                    st.info(f"Loaded '{idea['title']}'. Switch to the 'Script & Storyboard Studio' tab!")


# ── TAB 2: Script & Storyboard Studio ──────────────────────────────────────────
with tab2:
    st.markdown("### 45-Second Short Video Scriptwriter")
    
    loaded_title = st.session_state.get("active_idea_title", "")
    loaded_concept = st.session_state.get("active_idea_concept", "")
    loaded_hook = st.session_state.get("active_idea_hook", "")
    loaded_cat = st.session_state.get("active_idea_category", "amazing_facts")
    loaded_id = st.session_state.get("active_idea_id", None)

    title_input = st.text_input("Video Title", value=loaded_title, placeholder="e.g., The Mariana Trench Mystery")
    concept_input = st.text_area("Core Concept", value=loaded_concept, placeholder="What is this video about?")
    hook_input = st.text_input("Opening Hook (First spoken sentence)", value=loaded_hook, placeholder="First 3 seconds attention grabber")

    write_script_btn = st.button("✍️ Write Full 45s Script & Storyboard", use_container_width=True)

    if write_script_btn:
        if not title_input or not concept_input:
            st.warning("Please provide at least a title and concept.")
        else:
            with st.spinner("Writing scene-by-scene script with timing and visual cues..."):
                try:
                    s_gen = ScriptGenerator()
                    script_res = s_gen.generate_short_script(
                        title=title_input,
                        concept=concept_input,
                        hook=hook_input or title_input,
                        category=loaded_cat,
                        idea_id=loaded_id,
                    )
                    st.session_state["current_script_id"] = script_res.id
                    st.session_state["current_script_text"] = script_res.narration_text
                    st.session_state["current_script_scenes"] = script_res.scenes
                    st.session_state["current_script_title"] = script_res.title
                    st.success(f"Script created! Word count: {script_res.word_count} words ({script_res.estimated_duration_s:.1f}s)")
                except Exception as e:
                    st.error(f"Script generation failed: {e}")

    # Display current script if available
    curr_script_text = st.session_state.get("current_script_text", "")
    curr_script_id = st.session_state.get("current_script_id", None)
    curr_scenes = st.session_state.get("current_script_scenes", [])

    if curr_script_text:
        st.markdown("---")
        st.markdown("#### Spoken Voiceover (For Text-to-Speech)")
        st.caption("Clean text with no stage directions, emojis, or markdown. Ready for audio synthesis.")

        edited_text = st.text_area("Spoken Script", value=curr_script_text, height=140)
        
        words = len(edited_text.split())
        est_sec = round((words / 140.0) * 60, 1)
        st.caption(f"📊 Words: **{words}** | Estimated Duration: **~{est_sec}s** (Target: 40-50s)")

        if st.button("💾 Save Script Edits"):
            if curr_script_id:
                ScriptGenerator().update_script_text(curr_script_id, edited_text)
                st.session_state["current_script_text"] = edited_text
                st.success("Script updated in database!")

        # Storyboard scenes
        if curr_scenes:
            st.markdown("---")
            st.markdown("#### 🎬 Scene-by-Scene Storyboard")
            for scene in curr_scenes:
                with st.expander(f"Scene {scene.scene_number} ({scene.duration_s}s)"):
                    st.markdown(f"**Spoken Line:** *\"{scene.narration}\"*")
                    st.markdown(f"**Visual Prompt (Stock Footage):** `{scene.visual_prompt}`")
                    if scene.sfx_cue:
                        st.markdown(f"**Sound Effect Cue:** 🔊 *{scene.sfx_cue}*")


# ── TAB 3: Metadata & Fact Audit ──────────────────────────────────────────────
with tab3:
    st.markdown("### Metadata Generation & Fact Checking")
    
    meta_topic = st.session_state.get("current_script_title", loaded_title)
    meta_text = st.session_state.get("current_script_text", "")

    if not meta_topic or not meta_text:
        st.info("Write or select a script in Tab 2 first, then come here to generate metadata and audit facts.")
    else:
        st.markdown(f"**Active Video:** {meta_topic}")
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            gen_meta_btn = st.button("🏷️ Generate Title Options & Hashtags", use_container_width=True)
        with m_col2:
            audit_btn = st.button("🛡️ Audit Factual Accuracy", use_container_width=True)

        if gen_meta_btn:
            with st.spinner("Generating viral titles and platform tags..."):
                try:
                    t_gen = TitleGenerator()
                    titles = t_gen.generate_titles_and_description(
                        topic=meta_topic,
                        script_summary=meta_text[:200],
                        category=loaded_cat
                    )
                    h_gen = HashtagGenerator()
                    tags = h_gen.generate_hashtags(
                        topic=meta_topic,
                        category=loaded_cat,
                        target_platforms=["youtube", "instagram", "tiktok"]
                    )
                    
                    st.session_state["meta_titles"] = titles
                    st.session_state["meta_tags"] = tags
                except Exception as e:
                    st.error(f"Metadata generation failed: {e}")

        if audit_btn:
            with st.spinner("Checking claims and numbers for factual accuracy..."):
                try:
                    checker = FactChecker()
                    audit = checker.check_script(
                        title=meta_topic,
                        narration_text=meta_text,
                        category=loaded_cat
                    )
                    st.session_state["audit_result"] = audit
                except Exception as e:
                    st.error(f"Fact check audit failed: {e}")

        # Show Metadata
        if "meta_titles" in st.session_state:
            titles = st.session_state["meta_titles"]
            st.markdown("#### Title Recommendations")
            st.success(f"🏆 Primary: **{titles.primary_title}**")
            for i, var in enumerate(titles.variations, 1):
                st.write(f"• Option {i}: {var}")
            
            st.markdown("#### Video Description")
            st.info(titles.description)

        if "meta_tags" in st.session_state:
            tags = st.session_state["meta_tags"]
            st.markdown("#### Hashtags by Platform")
            st.write(f"**YouTube Shorts:** `{tags.get('youtube', '')}`")
            st.write(f"**Instagram Reels:** `{tags.get('instagram', '')}`")
            st.write(f"**TikTok:** `{tags.get('tiktok', '')}`")

        # Show Audit
        if "audit_result" in st.session_state:
            audit = st.session_state["audit_result"]
            st.markdown("---")
            st.markdown("#### 🛡️ Factual Audit Result")
            if audit.verdict == "PASS":
                st.success(f"✅ Verdict: **{audit.verdict}** (Accuracy Score: {audit.accuracy_score}/100)")
            elif audit.verdict == "REVIEW_REQUIRED":
                st.warning(f"⚠️ Verdict: **{audit.verdict}** (Accuracy Score: {audit.accuracy_score}/100)")
            else:
                st.error(f"❌ Verdict: **{audit.verdict}** (Accuracy Score: {audit.accuracy_score}/100)")
            
            if audit.flagged_claims:
                st.markdown("**Flagged Claims:**")
                for c in audit.flagged_claims:
                    st.warning(f"• {c}")
            if audit.suggested_corrections:
                st.markdown("**Suggested Corrections:**")
                for s in audit.suggested_corrections:
                    st.info(f"• {s}")
