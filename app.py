"""
app.py — Main entry point for ChronicleAI: Interactive Visual Novel Engine.

A voice-driven, text-based RPG featuring dynamic Gemini-powered DM responses,
live audio transcription, state management, and visual novel aesthetics.
"""

from __future__ import annotations

import json
import logging
import os
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── 1. Page Configuration ───────────────────────────────────────────
st.set_page_config(
    page_title="Chronicle AI",
    page_icon="⚔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Session State Initialization (MUST be top-level) ─────────────
if "story_state" not in st.session_state:
    st.session_state.story_state = None
if "game_phase" not in st.session_state:
    st.session_state.game_phase = "setup"  # "setup" | "playing" | "game_over"
if "last_transcription" not in st.session_state:
    st.session_state.last_transcription = ""
if "processing" not in st.session_state:
    st.session_state.processing = False
if "audio_processed_id" not in st.session_state:
    st.session_state.audio_processed_id = None
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False
if "pending_action" not in st.session_state:
    st.session_state.pending_action = ""

# ── 3. Imports from Core & UI ───────────────────────────────────────
from core.story_engine import (
    StoryState,
    create_new_story,
    apply_dm_response,
    compute_story_stats,
    export_story_as_text,
)
from core.gemini_client import (
    check_api_connection,
    transcribe_audio,
    generate_dm_response,
    evaluate_story_ending,
)
from core.audio_handler import process_streamlit_audio, validate_audio
from ui.styles import STYLES
from ui.components import (
    render_header,
    render_stat_bars,
    render_story_panel,
    render_inventory,
    render_quest_log,
    render_history_sidebar,
    render_chapter_transition,
    render_game_over,
    render_character_panel,
    render_api_status,
)
from data.story_templates import STORY_TEMPLATES, get_template_choices

# ── 4. Inject Custom CSS ────────────────────────────────────────────
st.markdown(STYLES, unsafe_allow_html=True)


# ── Helper: Reset / Restart Story ───────────────────────────────────
def reset_to_setup() -> None:
    st.session_state.story_state = None
    st.session_state.game_phase = "setup"
    st.session_state.last_transcription = ""
    st.session_state.processing = False
    st.session_state.audio_processed_id = None
    st.session_state.demo_mode = False
    st.session_state.pending_action = ""


# ── Helper: Load Sample Demo Session ────────────────────────────────
def load_demo_session() -> None:
    demo_file = os.path.join(os.path.dirname(__file__), "data", "sample_stories", "demo_log.json")
    if os.path.exists(demo_file):
        try:
            with open(demo_file, "r", encoding="utf-8") as f:
                demo_data = json.load(f)
            
            # Construct a demo StoryState based on shattered_realm
            state = create_new_story(
                world_template=STORY_TEMPLATES["shattered_realm"],
                protagonist_name="Kaelen",
                protagonist_class="Scholar",
            )
            # Replay demo turns
            for i in range(0, len(demo_data), 2):
                player_turn = demo_data[i]
                dm_turn = demo_data[i + 1] if i + 1 < len(demo_data) else None
                if dm_turn:
                    apply_dm_response(state, dm_turn["content"], player_turn["content"])

            st.session_state.story_state = state
            st.session_state.game_phase = "playing"
            st.session_state.demo_mode = True
        except Exception as e:
            st.error(f"Failed to load demo: {e}")


# ═════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="chronicle-title-compact">⚔ CHRONICLE AI</div>', unsafe_allow_html=True)
    st.caption("Interactive Visual Novel Engine")
    
    api_connected = check_api_connection()
    render_api_status(api_connected)
    st.divider()

    state: StoryState | None = st.session_state.story_state

    if state is not None and st.session_state.game_phase in ("playing", "game_over"):
        st.markdown(f"**Session ID:** `{state.session_id[:8]}...`")
        st.markdown(f"**World:** {state.world_name}")
        st.markdown(f"**Hero:** {state.protagonist_name} ({state.protagonist_class})")
        st.divider()

        # Story Stats Expander
        with st.expander("📖 Story Statistics", expanded=True):
            stats = compute_story_stats(state)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Turns", stats["total_turns"])
                st.metric("Quests", stats["quests_ratio"])
            with c2:
                st.metric("NPCs Met", stats["unique_npcs_met"])
                st.metric("Danger", stats["danger_label"])
            st.caption(f"Chapter: {stats['chapter']} | Inventory: {stats['inventory_count']} items")

        # Export Story
        story_text = export_story_as_text(state)
        st.download_button(
            label="💾 Export Chronicle (.txt)",
            data=story_text,
            file_name=f"chronicle_{state.protagonist_name}_{state.session_id[:6]}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        st.divider()
        if st.button("🔄 Restart Chronicle", use_container_width=True):
            reset_to_setup()
            st.rerun()

    else:
        st.info("Choose a world and create your protagonist to begin your adventure.")
        if st.button("👁 Load Sample Demo Story", use_container_width=True):
            load_demo_session()
            st.rerun()

    st.markdown(
        """
        <div style="text-align: center; color: #8a7e6b; font-size: 0.75rem; margin-top: 2.5rem; font-family: 'Cinzel', serif; letter-spacing: 1px;">
            Powered by Gemini 2.5 Flash • Built with Streamlit
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════════
# PHASE 1: SETUP
# ═════════════════════════════════════════════════════════════════════
if st.session_state.game_phase == "setup":
    col_left, col_center, col_right = st.columns([1, 4, 1])

    with col_center:
        render_header()

        st.markdown("### 🗺️ Choose Your World")
        choices = get_template_choices()
        template_keys = [c[0] for c in choices]
        template_labels = [f"{c[2]} {c[1]}" for c in choices]

        selected_idx = st.radio(
            "Select World Template",
            range(len(template_labels)),
            format_func=lambda i: template_labels[i],
            label_visibility="collapsed",
        )
        selected_key = template_keys[selected_idx]
        selected_template = STORY_TEMPLATES[selected_key]

        # Display chosen setting box
        st.markdown(
            f"""
            <div class="world-option">
                <div style="font-family: 'Cinzel', serif; color: #c9a84c; font-size: 1.1rem; margin-bottom: 0.3rem;">
                    {selected_template.get('emoji', '⚔')} {selected_template['name']}
                </div>
                <div style="font-style: italic; color: #8a7e6b; font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Tone: {selected_template.get('tone', 'dark fantasy')}
                </div>
                <div style="font-size: 0.95rem; line-height: 1.6;">
                    {selected_template['setting']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        with st.form("start_form", clear_on_submit=False):
            col_name, col_class = st.columns(2)
            with col_name:
                protagonist_name = st.text_input(
                    "Protagonist Name",
                    value="Valerius",
                    placeholder="Enter your character's name",
                )
            with col_class:
                protagonist_class = st.selectbox(
                    "Class",
                    ["Warrior", "Mage", "Rogue", "Scholar"],
                    index=0,
                )

            submit_start = st.form_submit_button("⚔ BEGIN YOUR CHRONICLE", use_container_width=True, type="primary")

        st.markdown(
            "<div style='text-align: center; margin: 0.75rem 0 0.5rem; color: #8a7e6b; font-size: 0.85rem;'>— OR QUICK EVALUATION —</div>",
            unsafe_allow_html=True,
        )
        if st.button("📸 Demo Mode (Pre-Played 8-Turn Session)", use_container_width=True):
            load_demo_session()
            st.rerun()

        if submit_start:
            if not protagonist_name.strip():
                st.warning("Please give your protagonist a name.")
            else:
                with st.spinner("Forging the world and preparing your chronicle..."):
                    # 1. Create state
                    new_state = create_new_story(
                        world_template=selected_template,
                        protagonist_name=protagonist_name.strip(),
                        protagonist_class=protagonist_class,
                    )
                    # 2. Generate opening scene
                    if api_connected:
                        opening_dm = generate_dm_response(new_state, "[STORY_BEGIN]")
                    else:
                        opening_dm = (
                            f"{selected_template['opening_hook']}\n\n"
                            f"[QUEST_STARTED: {selected_template['main_quest']}]"
                        )
                    
                    # 3. Apply DM opening
                    apply_dm_response(new_state, opening_dm, "[STORY_BEGIN]")
                    st.session_state.story_state = new_state
                    st.session_state.game_phase = "playing"
                    st.rerun()


# ═════════════════════════════════════════════════════════════════════
# PHASE 2: PLAYING
# ═════════════════════════════════════════════════════════════════════
elif st.session_state.game_phase == "playing":
    state = st.session_state.story_state

    # Check for game over triggers
    if state.health <= 0 or state.sanity <= 0:
        st.session_state.game_phase = "game_over"
        st.rerun()

    # 3-Column Layout: [Left Sidebar Info, Center Story & Input, Right History]
    col_char, col_main, col_hist = st.columns([1.1, 2.8, 1.1])

    # ── Left Column: Character Sheet ──
    with col_char:
        render_character_panel(state.protagonist_name, state.protagonist_class)
        render_stat_bars(state.health, state.sanity)
        st.write("")
        render_inventory(state.inventory)
        st.write("")
        render_quest_log(state.active_quests, state.completed_quests)

    # ── Center Column: Main Story & Action Input ──
    with col_main:
        render_header(compact=True)

        # Chapter and Beat counter
        st.markdown(
            f'<div class="turn-counter">Chapter {state.chapter} • Turn {state.story_beat - 1}</div>',
            unsafe_allow_html=True,
        )

        # Latest story response
        render_story_panel(state.last_dm_response or state.current_scene, is_new=True)

        # ── INPUT SECTION ──
        st.markdown("##### ⚔ Your Action")

        # Audio transcription handler outside form to prevent rerun wipe
        audio_data = st.audio_input("🎤 Record Voice Action", key="voice_mic")
        if audio_data is not None:
            raw_bytes = process_streamlit_audio(audio_data)
            if raw_bytes and validate_audio(raw_bytes):
                audio_id = hash(raw_bytes)
                if audio_id != st.session_state.get("audio_processed_id"):
                    st.session_state.audio_processed_id = audio_id
                    with st.spinner("Transcribing your voice..."):
                        transcript = transcribe_audio(raw_bytes)
                        if transcript:
                            st.session_state.last_transcription = transcript
                            st.success(f"Transcribed: *\"{transcript}\"*")
                        else:
                            st.warning("Could not clearly transcribe audio. Please try again or type below.")

        with st.form("action_form", clear_on_submit=True):
            tab_text, tab_voice = st.tabs(["⌨️ Type Action", "🎤 Use Voice Transcription"])

            with tab_text:
                typed_action = st.text_area(
                    "What do you do?",
                    placeholder="I draw my sword and demand answers from the harbormaster...",
                    max_chars=200,
                    label_visibility="collapsed",
                    key="typed_action_input",
                )

            with tab_voice:
                if st.session_state.last_transcription:
                    st.info(f"🎙 **Ready to commit:** *\"{st.session_state.last_transcription}\"*")
                else:
                    st.caption("Record audio using the mic widget above, then submit here.")
                use_voice = st.checkbox("Submit recorded voice action", value=bool(st.session_state.last_transcription))

            commit_button = st.form_submit_button("⚔ Commit Action", use_container_width=True, type="primary")

        if commit_button:
            chosen_action = ""
            if use_voice and st.session_state.last_transcription:
                chosen_action = st.session_state.last_transcription
                st.session_state.last_transcription = ""  # Clear after use
            elif typed_action.strip():
                chosen_action = typed_action.strip()

            if not chosen_action:
                st.warning("Please type an action or record your voice before committing.")
            else:
                with st.spinner("The Dungeon Master deliberates..."):
                    dm_reply = generate_dm_response(state, chosen_action)
                    apply_dm_response(state, dm_reply, chosen_action)

                    # Check for game over or chapter transition
                    if state.health <= 0 or state.sanity <= 0 or state.story_beat >= 50:
                        st.session_state.game_phase = "game_over"
                    st.rerun()

    # ── Right Column: Story History ──
    with col_hist:
        st.markdown("##### 📜 Story So Far")
        render_history_sidebar(state.full_history)


# ═════════════════════════════════════════════════════════════════════
# PHASE 3: GAME OVER
# ═════════════════════════════════════════════════════════════════════
elif st.session_state.game_phase == "game_over":
    state = st.session_state.story_state

    col_l, col_center, col_r = st.columns([1, 4, 1])
    with col_center:
        with st.spinner("Inscribing your final chapter into the annals of legend..."):
            ending = evaluate_story_ending(state)
        
        render_game_over(ending)

        c_restart, c_export = st.columns(2)
        with c_restart:
            if st.button("🔄 Start New Chronicle", use_container_width=True, type="primary"):
                reset_to_setup()
                st.rerun()
        with c_export:
            story_text = export_story_as_text(state)
            st.download_button(
                label="💾 Download Final Chronicle",
                data=story_text,
                file_name=f"chronicle_final_{state.protagonist_name}_{state.session_id[:6]}.txt",
                mime="text/plain",
                use_container_width=True,
            )
