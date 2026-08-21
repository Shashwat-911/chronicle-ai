"""
components.py — Reusable UI components for ChronicleAI.

Provides rendering functions for every visual element of the
visual novel interface: headers, stat bars, dynamic KPI metric cards with deltas,
interactive inventory editor with st.data_editor, telemetry analytics with st.line_chart,
world cartography with st.map, story panels, inventory, quest logs,
chapter transitions, and game over screens.
"""

from __future__ import annotations

import re
from typing import Any
import pandas as pd
import streamlit as st

from core.story_engine import (
    StoryState,
    strip_tags,
    get_turn_history_df,
    get_inventory_dataframe,
    update_inventory_from_dataframe,
    get_npc_dataframe,
    get_world_locations_df,
    export_telemetry_csv,
)


# ── Header ───────────────────────────────────────────────────────────


def render_header(compact: bool = False) -> None:
    """Render the Chronicle AI title and subtitle.

    Args:
        compact: If ``True``, render a smaller inline header suitable
            for the playing phase.
    """
    if compact:
        st.markdown(
            '<div class="chronicle-header">'
            '<div class="chronicle-title-compact">⚔ CHRONICLE AI ⚔</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="chronicle-header">'
            '<div class="chronicle-title">⚔ CHRONICLE AI ⚔</div>'
            '<div class="chronicle-subtitle">'
            'An AI-Powered Interactive Dark Fantasy'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ── Dynamic KPI Cards (st.metric with deltas) ─────────────────────────


def render_kpi_dashboard(stats: dict[str, Any], health: int, sanity: int) -> None:
    """Render dynamic KPI metric cards featuring deltas.

    Args:
        stats: Computed story stats dictionary.
        health: Current health (0-100).
        sanity: Current sanity (0-100).
    """
    c1, c2, c3, c4 = st.columns(4)

    health_delta = stats.get("last_health_delta", 0)
    sanity_delta = stats.get("last_sanity_delta", 0)
    turn_num = stats.get("total_turns", 0)
    quests_ratio = stats.get("quests_ratio", "0/0")

    with c1:
        st.metric(
            label="💀 Vitality",
            value=f"{health}/100",
            delta=f"{health_delta:+d} HP" if health_delta != 0 else "Stable",
            delta_color="normal",
        )
    with c2:
        st.metric(
            label="🌙 Sanity",
            value=f"{sanity}/100",
            delta=f"{sanity_delta:+d} Mind" if sanity_delta != 0 else "Grounded",
            delta_color="normal",
        )
    with c3:
        st.metric(
            label="⏳ Turn Progress",
            value=f"Turn {turn_num}",
            delta="+1 Turn" if turn_num > 0 else "Arrival",
        )
    with c4:
        st.metric(
            label="📜 Active Quests",
            value=quests_ratio,
            delta=f"Chapter {stats.get('chapter', 1)}",
        )


# ── Stat Bars ────────────────────────────────────────────────────────


def render_stat_bars(health: int, sanity: int) -> None:
    """Render custom HTML health and sanity progress bars.

    Bars flash with a critical animation when their value drops below 30.

    Args:
        health: Current health value (0-100).
        sanity: Current sanity value (0-100).
    """
    health_crit = " stat-bar-critical" if health < 30 else ""
    sanity_crit = " stat-bar-critical" if sanity < 30 else ""

    html = f"""
    <div class="stat-bar-container">
        <div class="stat-bar-label">
            <span>💀 VITALITY</span>
            <span>{health}/100</span>
        </div>
        <div class="stat-bar-track">
            <div class="stat-bar-fill-health{health_crit}"
                 style="width: {health}%;"></div>
        </div>
    </div>
    <div class="stat-bar-container" style="margin-top: 0.75rem;">
        <div class="stat-bar-label">
            <span>🌙 SANITY</span>
            <span>{sanity}/100</span>
        </div>
        <div class="stat-bar-track">
            <div class="stat-bar-fill-sanity{sanity_crit}"
                 style="width: {sanity}%;"></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Story Panel ──────────────────────────────────────────────────────


def render_story_panel(text: str, is_new: bool = False) -> None:
    """Render the DM's latest narrative response in a styled panel.

    System tags (``[HEALTH_CHANGE: ...]`` etc.) are stripped before
    display. The text is converted to HTML paragraphs.

    Args:
        text: Raw DM response text (may contain system tags).
        is_new: If ``True``, apply a fade-in animation.
    """
    if not text:
        return

    # Strip system tags for display
    clean = strip_tags(text)

    # Convert double-newlines to paragraph tags
    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in clean.split("\n") if p.strip()]

    html_content = "".join(f"<p>{p}</p>" for p in paragraphs)

    anim_class = " story-panel-new" if is_new else ""

    st.markdown(
        f'<div class="story-panel{anim_class}">{html_content}</div>',
        unsafe_allow_html=True,
    )


# ── Inventory Badges ─────────────────────────────────────────────────


def render_inventory(items: list[str]) -> None:
    """Render the player's inventory as styled gold badges.

    Args:
        items: List of inventory item names.
    """
    st.markdown(
        '<div class="inventory-title">🎒 Inventory Pack</div>',
        unsafe_allow_html=True,
    )

    if not items:
        st.markdown(
            '<div class="inventory-container">'
            '<span class="inventory-empty">Your pack is empty...</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    badges = "".join(
        f'<span class="inventory-item">{item}</span>' for item in items
    )
    st.markdown(
        f'<div class="inventory-container">{badges}</div>',
        unsafe_allow_html=True,
    )


# ── Interactive Inventory Codex (st.data_editor) ─────────────────────


def render_interactive_inventory_editor(state: StoryState) -> None:
    """Render an interactive data editor for player equipment and notes."""
    df = get_inventory_dataframe(state)

    st.caption("✍️ Edit equipment notes, toggle equipped status, or update item condition below:")
    edited_df = st.data_editor(
        df,
        column_config={
            "Equipped": st.column_config.CheckboxColumn(
                "Equipped?",
                help="Check if this item is currently active or worn",
                default=False,
            ),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=["Weapon", "Armor", "Consumable", "Artifact", "Quest Item", "Utility"],
                required=True,
            ),
            "Condition": st.column_config.SelectboxColumn(
                "Condition",
                options=["Pristine", "Good", "Worn", "Damaged", "Discovered"],
                required=True,
            ),
            "Player Notes": st.column_config.TextColumn(
                "Player Lore & Notes",
                width="medium",
                help="Your personal notes about this item",
            ),
        },
        disabled=["Item Name"],
        use_container_width=True,
        key="inventory_data_editor",
    )

    # Sync edits back to StoryState
    update_inventory_from_dataframe(state, edited_df)


# ── Telemetry & Analytics Dashboard (st.line_chart + Pandas) ─────────


def render_telemetry_analytics(state: StoryState) -> None:
    """Render comprehensive telemetry analytics and time-series line chart."""
    df = get_turn_history_df(state)

    if len(df) > 1:
        st.markdown("###### 📈 Vitality & Sanity Telemetry Trend")
        # Multi-line chart
        chart_data = df.set_index("Turn")[["Vitality", "Sanity"]]
        st.line_chart(chart_data, color=["#c93a3a", "#7c5ac9"])
    else:
        st.info("📊 Telemetry charts will plot your vital trends as you take more actions.")

    st.markdown("###### 📋 Turn-by-Turn Journey Telemetry (Pandas Data Pipeline)")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = export_telemetry_csv(state)
    st.download_button(
        label="📥 Download Telemetry CSV Dataset",
        data=csv_data,
        file_name=f"chronicle_telemetry_{state.protagonist_name}_{state.session_id[:6]}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ── Interactive World Cartography (st.map) ───────────────────────────


def render_world_map_cartography(state: StoryState) -> None:
    """Render interactive geographical map and landmark discovery registry."""
    map_df = get_world_locations_df(state)
    st.caption(f"🗺️ Discovered Landmark Coordinates in **{state.world_name}**:")
    
    st.map(
        map_df,
        latitude="lat",
        longitude="lon",
        size=25,
        color="#c9a84c",
        use_container_width=True,
    )

    # Landmark nodes registry
    cols = st.columns(len(map_df))
    for idx, row in map_df.iterrows():
        col_target = cols[idx % len(cols)]
        with col_target:
            status_emoji = "📍" if row['status'] == 'Current' else ("🏰" if row['status'] == 'Visited' else "⚔")
            st.metric(
                label=f"{status_emoji} {row['location']}",
                value=row['status'],
                delta=f"Danger: {row['danger']}",
                delta_color="off",
            )


# ── NPC Relations Ledger ─────────────────────────────────────────────


def render_npc_ledger(state: StoryState) -> None:
    """Render discovered NPC registry in a structured table."""
    npc_df = get_npc_dataframe(state)
    if npc_df.empty:
        st.caption("No notable NPCs recorded in your codex yet.")
    else:
        st.dataframe(npc_df, use_container_width=True, hide_index=True)


# ── Quest Log ────────────────────────────────────────────────────────


def render_quest_log(active: list[str], completed: list[str]) -> None:
    """Render the quest log as an expandable section.

    Active quests display with gold diamonds; completed quests are
    struck through in muted green.

    Args:
        active: List of active quest names.
        completed: List of completed quest names.
    """
    with st.expander("📜 Quest Log", expanded=False):
        if not active and not completed:
            st.markdown(
                '<span class="inventory-empty">'
                'No quests yet — your journey awaits...'
                '</span>',
                unsafe_allow_html=True,
            )
            return

        for quest in active:
            st.markdown(
                f'<div class="quest-active">◆ {quest}</div>',
                unsafe_allow_html=True,
            )
        for quest in completed:
            st.markdown(
                f'<div class="quest-completed">✓ {quest}</div>',
                unsafe_allow_html=True,
            )


# ── History Sidebar ──────────────────────────────────────────────────


def render_history_sidebar(history: list[dict]) -> None:
    """Render the last 10 story exchanges in a compact sidebar format.

    Player actions appear right-aligned in gold italic.
    DM responses are truncated to 80 characters.

    Args:
        history: The full_history list from StoryState.
    """
    if not history:
        st.markdown(
            '<span class="inventory-empty">'
            'Your chronicle begins here...'
            '</span>',
            unsafe_allow_html=True,
        )
        return

    # Show last 10 entries
    recent = history[-10:]
    beat = max(1, (len(history) - len(recent)) // 2 + 1)

    html_parts: list[str] = []
    for entry in recent:
        if entry["role"] == "player":
            content = entry["content"]
            if content == "[STORY_BEGIN]":
                content = "⚔ Journey begins..."
            html_parts.append(
                f'<div class="history-entry">'
                f'<div class="history-beat-label">Turn {beat}</div>'
                f'<div class="history-player">{_escape(content)}</div>'
                f'</div>'
            )
        else:
            clean = strip_tags(entry["content"])
            truncated = clean[:80] + "..." if len(clean) > 80 else clean
            html_parts.append(
                f'<div class="history-entry">'
                f'<div class="history-dm">{_escape(truncated)}</div>'
                f'</div>'
            )
            beat += 1

    st.markdown("".join(html_parts), unsafe_allow_html=True)


# ── Chapter Transition ───────────────────────────────────────────────


def render_chapter_transition(chapter: int, title: str = "") -> None:
    """Render a dramatic full-width chapter announcement.

    Args:
        chapter: The chapter number.
        title: Optional chapter title.
    """
    title_html = (
        f'<div class="chapter-title">{_escape(title)}</div>'
        if title
        else ""
    )

    st.markdown(
        f"""
        <div class="chapter-transition">
            <div class="chapter-divider"></div>
            <div class="chapter-number">Chapter {_roman(chapter)}</div>
            {title_html}
            <div class="chapter-divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Game Over Screen ─────────────────────────────────────────────────


def render_game_over(ending: dict) -> None:
    """Render the full game over screen with ending badge, epilogue, and score.

    Args:
        ending: Dictionary with ``ending_type``, ``epilogue``, and ``score``.
    """
    ending_type = ending.get("ending_type", "victory")
    epilogue = ending.get("epilogue", "Your story has ended.")
    score = ending.get("score", 0)

    # Human-readable ending labels
    ending_labels = {
        "heroic_death": "⚔ Heroic Death ⚔",
        "madness": "🌑 Consumed by Madness 🌑",
        "victory": "👑 Triumphant Victory 👑",
        "legend": "⭐ Legendary ⭐",
    }

    label = ending_labels.get(ending_type, "The End")

    # Format epilogue paragraphs
    epi_paragraphs = [p.strip() for p in epilogue.split("\n\n") if p.strip()]
    if not epi_paragraphs:
        epi_paragraphs = [epilogue]
    epi_html = "".join(f"<p>{_escape(p)}</p>" for p in epi_paragraphs)

    st.markdown(
        f"""
        <div class="game-over-container">
            <div class="game-over-title">Your Chronicle Ends</div>
            <div class="ending-badge ending-{ending_type}">{label}</div>
            <div class="epilogue-text">{epi_html}</div>
            <div class="score-display">
                <div class="score-label">Your Legacy</div>
                <div class="score-value">{score}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Character Panel ──────────────────────────────────────────────────


def render_character_panel(name: str, char_class: str) -> None:
    """Render the character name and class badge.

    Args:
        name: Protagonist's name.
        char_class: Protagonist's class (Warrior/Mage/Rogue/Scholar).
    """
    class_css = f"class-{char_class.lower()}"

    st.markdown(
        f"""
        <div class="char-panel">
            <div class="char-name">{_escape(name)}</div>
            <div class="char-class-badge {class_css}">{char_class}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── API Status ───────────────────────────────────────────────────────


def render_api_status(connected: bool) -> None:
    """Render a small API connection status indicator.

    Args:
        connected: Whether the Gemini API key is configured.
    """
    if connected:
        dot_class = "api-dot-connected"
        label = "GEMINI CONNECTED"
    else:
        dot_class = "api-dot-disconnected"
        label = "GEMINI DISCONNECTED"

    st.markdown(
        f'<div class="api-status">'
        f'<span class="api-dot {dot_class}"></span>'
        f'<span>{label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Helpers ──────────────────────────────────────────────────────────


def _escape(text: str) -> str:
    """Basic HTML escaping for user-provided text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _roman(n: int) -> str:
    """Convert an integer to a Roman numeral string."""
    if n <= 0 or n > 50:
        return str(n)
    vals = [
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = ""
    for val, numeral in vals:
        while n >= val:
            result += numeral
            n -= val
    return result
