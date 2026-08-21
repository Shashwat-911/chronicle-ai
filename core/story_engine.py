"""
story_engine.py — Story state management for ChronicleAI.

Manages all persistent game state using Python dataclasses and Pandas DataFrames.
Handles state creation, mutation via DM response tags, serialization,
turn telemetry logging, DataFrame transformation pipelines, and context
window management for the Gemini API.
"""

from __future__ import annotations

import io
import re
import uuid
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from typing import Any

import pandas as pd


@dataclass
class StoryState:
    """Complete game state for a single playthrough."""

    session_id: str
    world_name: str
    protagonist_name: str
    protagonist_class: str  # Warrior / Mage / Rogue / Scholar
    current_scene: str  # Paragraph describing current location
    story_beat: int  # Which turn we're on (starts at 1)
    health: int  # 0-100
    sanity: int  # 0-100
    inventory: list[str] = field(default_factory=list)
    active_quests: list[str] = field(default_factory=list)
    completed_quests: list[str] = field(default_factory=list)
    npc_relationships: dict[str, str] = field(default_factory=dict)
    world_flags: dict[str, bool] = field(default_factory=dict)
    full_history: list[dict[str, str]] = field(default_factory=list)
    last_dm_response: str = ""
    chapter: int = 1
    turn_telemetry: list[dict[str, Any]] = field(default_factory=list)
    inventory_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)


# ── Tag-parsing regex patterns ──────────────────────────────────────

_TAG_PATTERNS: dict[str, re.Pattern] = {
    "health_change": re.compile(r"\[HEALTH_CHANGE:\s*([+-]?\d+)\]"),
    "sanity_change": re.compile(r"\[SANITY_CHANGE:\s*([+-]?\d+)\]"),
    "item_gained": re.compile(r"\[ITEM_GAINED:\s*(.+?)\]"),
    "item_lost": re.compile(r"\[ITEM_LOST:\s*(.+?)\]"),
    "npc_met": re.compile(r"\[NPC_MET:\s*(.+?),\s*(.+?)\]"),
    "quest_started": re.compile(r"\[QUEST_STARTED:\s*(.+?)\]"),
    "quest_completed": re.compile(r"\[QUEST_COMPLETED:\s*(.+?)\]"),
    "world_flag": re.compile(r"\[WORLD_FLAG:\s*(.+?)=(.+?)\]"),
    "chapter_end": re.compile(r"\[CHAPTER_END\]"),
}

# ── Default inventories per class ────────────────────────────────────

_CLASS_INVENTORIES: dict[str, list[str]] = {
    "Warrior": ["Iron Sword", "Shield", "Healing Salve"],
    "Mage": ["Spellbook", "3× Mana Potion", "Crystal Focus"],
    "Rogue": ["Twin Daggers", "Lockpick Set", "Smoke Bomb"],
    "Scholar": ["Ancient Tome", "Quill & Ink", "Lantern", "Cipher Ring"],
}

# World geographic anchor coordinates for interactive cartography
_WORLD_MAP_NODES: dict[str, list[dict[str, Any]]] = {
    "The Shattered Realm": [
        {"location": "Ashveil Sky-Docks", "lat": 45.18, "lon": 5.72, "status": "Current", "danger": "Moderate"},
        {"location": "The Gilded Antler Inn", "lat": 45.19, "lon": 5.74, "status": "Visited", "danger": "Safe"},
        {"location": "Mayor Draven's Manor", "lat": 45.22, "lon": 5.76, "status": "Infiltrated", "danger": "High"},
        {"location": "The Ancient Sealed Vault", "lat": 45.21, "lon": 5.78, "status": "Objective", "danger": "Extreme"},
    ],
    "Tidecaller's Deep": [
        {"location": "Black Sand Wreckage", "lat": -28.12, "lon": 153.54, "status": "Current", "danger": "Moderate"},
        {"location": "The Drowned Beacon", "lat": -28.10, "lon": 153.56, "status": "Visible", "danger": "High"},
        {"location": "Whispering Grotto", "lat": -28.15, "lon": 153.52, "status": "Unexplored", "danger": "Extreme"},
    ],
    "The Ashen Wastes": [
        {"location": "Ruins of New Citadel", "lat": 36.31, "lon": -115.14, "status": "Current", "danger": "High"},
        {"location": "The Bone Ridge Crossing", "lat": 36.35, "lon": -115.10, "status": "Tracked", "danger": "Extreme"},
        {"location": "Vault of the Last Living God", "lat": 36.40, "lon": -115.05, "status": "Destination", "danger": "Unknown"},
    ],
}


def create_new_story(
    world_template: dict[str, Any],
    protagonist_name: str,
    protagonist_class: str,
) -> StoryState:
    """Initialize a fresh story state from a world template.

    Args:
        world_template: Dictionary from ``story_templates.STORY_TEMPLATES``.
        protagonist_name: Player-chosen character name.
        protagonist_class: One of Warrior / Mage / Rogue / Scholar.

    Returns:
        A fully initialized ``StoryState`` ready for play.
    """
    starting_inventory = list(
        _CLASS_INVENTORIES.get(protagonist_class, ["Worn Journal"])
    )

    starting_npcs: dict[str, str] = {}
    if "starting_npcs" in world_template:
        starting_npcs = dict(world_template["starting_npcs"])

    # Initial inventory metadata
    inv_meta: dict[str, dict[str, Any]] = {}
    for item in starting_inventory:
        inv_meta[item] = {
            "category": "Weapon" if "Sword" in item or "Dagger" in item or "Spellbook" in item else "Utility",
            "equipped": True if "Sword" in item or "Shield" in item or "Dagger" in item else False,
            "condition": "Pristine",
            "notes": "Starter equipment",
        }

    initial_telemetry = [
        {
            "turn": 0,
            "chapter": 1,
            "health": 100,
            "sanity": 100,
            "health_delta": 0,
            "sanity_delta": 0,
            "inventory_count": len(starting_inventory),
            "active_quests": 1,
            "completed_quests": 0,
            "npcs_known": len(starting_npcs),
            "danger_level": 0,
            "action_summary": "Chronicle Begun",
        }
    ]

    return StoryState(
        session_id=str(uuid.uuid4()),
        world_name=world_template["name"],
        protagonist_name=protagonist_name,
        protagonist_class=protagonist_class,
        current_scene=world_template.get("opening_hook", ""),
        story_beat=1,
        health=100,
        sanity=100,
        inventory=starting_inventory,
        active_quests=[world_template.get("main_quest", "Explore the world")],
        completed_quests=[],
        npc_relationships=starting_npcs,
        world_flags={},
        full_history=[],
        last_dm_response="",
        chapter=1,
        turn_telemetry=initial_telemetry,
        inventory_metadata=inv_meta,
    )


def _parse_tags(dm_response: str) -> dict[str, Any]:
    """Extract all system tags from a DM response string.

    Returns a dictionary of parsed tag values. Tags that can appear
    multiple times (items, NPCs, quests, flags) are returned as lists.
    """
    parsed: dict[str, Any] = {
        "health_change": 0,
        "sanity_change": 0,
        "items_gained": [],
        "items_lost": [],
        "npcs_met": [],
        "quests_started": [],
        "quests_completed": [],
        "world_flags": {},
        "chapter_end": False,
    }

    match = _TAG_PATTERNS["health_change"].search(dm_response)
    if match:
        parsed["health_change"] = int(match.group(1))

    match = _TAG_PATTERNS["sanity_change"].search(dm_response)
    if match:
        parsed["sanity_change"] = int(match.group(1))

    for match in _TAG_PATTERNS["item_gained"].finditer(dm_response):
        parsed["items_gained"].append(match.group(1).strip())

    for match in _TAG_PATTERNS["item_lost"].finditer(dm_response):
        parsed["items_lost"].append(match.group(1).strip())

    for match in _TAG_PATTERNS["npc_met"].finditer(dm_response):
        parsed["npcs_met"].append(
            (match.group(1).strip(), match.group(2).strip())
        )

    for match in _TAG_PATTERNS["quest_started"].finditer(dm_response):
        parsed["quests_started"].append(match.group(1).strip())

    for match in _TAG_PATTERNS["quest_completed"].finditer(dm_response):
        parsed["quests_completed"].append(match.group(1).strip())

    for match in _TAG_PATTERNS["world_flag"].finditer(dm_response):
        key = match.group(1).strip()
        val = match.group(2).strip().lower() == "true"
        parsed["world_flags"][key] = val

    if _TAG_PATTERNS["chapter_end"].search(dm_response):
        parsed["chapter_end"] = True

    return parsed


def apply_dm_response(
    state: StoryState,
    dm_response: str,
    player_action: str,
) -> StoryState:
    """Apply a DM response to the story state, mutating it in-place.

    Parses all system tags from the DM response, updates health, sanity,
    inventory, quests, NPCs, world flags, turn telemetry, and history.

    Args:
        state: Current game state (will be mutated).
        dm_response: Raw response text from Gemini (including tags).
        player_action: The player's action text that prompted this response.

    Returns:
        The updated ``StoryState`` (same object, mutated).
    """
    tags = _parse_tags(dm_response)

    prev_health = state.health
    prev_sanity = state.sanity

    # ── Health & Sanity (clamped 0-100) ──
    state.health = max(0, min(100, state.health + tags["health_change"]))
    state.sanity = max(0, min(100, state.sanity + tags["sanity_change"]))

    actual_health_delta = state.health - prev_health
    actual_sanity_delta = state.sanity - prev_sanity

    # ── Inventory ──
    for item in tags["items_gained"]:
        if item not in state.inventory:
            state.inventory.append(item)
            state.inventory_metadata[item] = {
                "category": "Artifact" if "Lantern" in item or "Ring" in item or "Map" in item else "Quest Item",
                "equipped": False,
                "condition": "Discovered",
                "notes": f"Acquired at Turn {state.story_beat}",
            }
    for item in tags["items_lost"]:
        if item in state.inventory:
            state.inventory.remove(item)
            if item in state.inventory_metadata:
                state.inventory_metadata[item]["notes"] = f"Lost/Consumed at Turn {state.story_beat}"

    # ── NPCs ──
    for npc_name, relationship in tags["npcs_met"]:
        state.npc_relationships[npc_name] = relationship

    # ── Quests ──
    for quest in tags["quests_started"]:
        if quest not in state.active_quests:
            state.active_quests.append(quest)
    for quest in tags["quests_completed"]:
        if quest in state.active_quests:
            state.active_quests.remove(quest)
        if quest not in state.completed_quests:
            state.completed_quests.append(quest)

    # ── World Flags ──
    state.world_flags.update(tags["world_flags"])

    # ── History ──
    state.full_history.append({"role": "player", "content": player_action})
    state.full_history.append({"role": "dm", "content": dm_response})

    # ── Scene & bookkeeping ──
    state.last_dm_response = dm_response
    current_turn = state.story_beat
    state.story_beat += 1

    # ── Chapter advancement ──
    if tags["chapter_end"] or (state.story_beat > 1 and state.story_beat % 10 == 1):
        state.chapter += 1

    # ── Compute and append Telemetry Record ──
    avg_vital = (state.health + state.sanity) / 2
    danger_lvl = 0 if avg_vital >= 80 else (1 if avg_vital >= 60 else (2 if avg_vital >= 40 else (3 if avg_vital >= 25 else (4 if avg_vital >= 10 else 5))))

    action_excerpt = (player_action[:30] + "...") if len(player_action) > 30 else player_action
    if player_action == "[STORY_BEGIN]":
        action_excerpt = "Prologue Arrival"

    state.turn_telemetry.append({
        "turn": current_turn,
        "chapter": state.chapter,
        "health": state.health,
        "sanity": state.sanity,
        "health_delta": actual_health_delta,
        "sanity_delta": actual_sanity_delta,
        "inventory_count": len(state.inventory),
        "active_quests": len(state.active_quests),
        "completed_quests": len(state.completed_quests),
        "npcs_known": len(state.npc_relationships),
        "danger_level": danger_lvl,
        "action_summary": action_excerpt,
    })

    return state


def serialize_state(state: StoryState) -> dict[str, Any]:
    """Convert a ``StoryState`` to a JSON-serializable dictionary."""
    return asdict(state)


def deserialize_state(data: dict[str, Any]) -> StoryState:
    """Reconstruct a ``StoryState`` from a serialized dictionary."""
    return StoryState(**data)


def get_context_window(
    state: StoryState,
    max_turns: int = 15,
) -> list[dict[str, str]]:
    """Return a bounded slice of conversation history for the Gemini context.

    Always includes the first 3 history entries (world establishment) and
    the most recent ``max_turns`` entries. This prevents context overflow
    while preserving critical early-game facts.

    Args:
        state: Current game state.
        max_turns: Maximum number of recent history entries to include.

    Returns:
        A list of ``{"role": ..., "content": ...}`` dictionaries.
    """
    history = state.full_history
    if len(history) <= max_turns:
        return list(history)

    # Always keep the first 3 entries (opening scene establishment)
    establishment = history[:3]
    recent = history[-max_turns:]

    # Avoid duplicates if recent overlaps with establishment
    if len(history) - max_turns <= 3:
        return list(history[: max_turns + 3])

    return establishment + recent


def compute_story_stats(state: StoryState) -> dict[str, Any]:
    """Compute aggregate stats for the current playthrough.

    Returns:
        A dictionary with total_turns, unique_npcs_met, quests_ratio,
        health_change_from_start, danger_level, and deltas.
    """
    total_turns = state.story_beat - 1  # beat starts at 1
    unique_npcs = len(state.npc_relationships)
    total_quests = len(state.active_quests) + len(state.completed_quests)
    completed = len(state.completed_quests)
    quests_ratio = f"{completed}/{total_quests}" if total_quests > 0 else "0/0"
    health_change = state.health - 100

    # Danger level: 0 (safe) to 5 (critical)
    avg_vital = (state.health + state.sanity) / 2
    if avg_vital >= 80:
        danger = 0
    elif avg_vital >= 60:
        danger = 1
    elif avg_vital >= 40:
        danger = 2
    elif avg_vital >= 25:
        danger = 3
    elif avg_vital >= 10:
        danger = 4
    else:
        danger = 5

    danger_labels = [
        "Safe", "Cautious", "Perilous", "Dire", "Critical", "Death's Door"
    ]

    # Calculate recent turn deltas from telemetry
    last_health_delta = 0
    last_sanity_delta = 0
    if len(state.turn_telemetry) >= 2:
        last_entry = state.turn_telemetry[-1]
        last_health_delta = last_entry.get("health_delta", 0)
        last_sanity_delta = last_entry.get("sanity_delta", 0)

    return {
        "total_turns": total_turns,
        "unique_npcs_met": unique_npcs,
        "quests_ratio": quests_ratio,
        "health_change_from_start": health_change,
        "danger_level": danger,
        "danger_label": danger_labels[danger],
        "chapter": state.chapter,
        "inventory_count": len(state.inventory),
        "last_health_delta": last_health_delta,
        "last_sanity_delta": last_sanity_delta,
    }


# ── Pandas Data Pipelines & Analytics ───────────────────────────────

def get_turn_history_df(state: StoryState) -> pd.DataFrame:
    """Build a structured Pandas DataFrame of turn-by-turn vital telemetry.

    Returns:
        DataFrame with columns ['Turn', 'Chapter', 'Vitality', 'Sanity',
        'Vitality Δ', 'Sanity Δ', 'Active Quests', 'Inventory Items', 'Danger Level', 'Action'].
    """
    if not state.turn_telemetry:
        # Fallback to single row
        return pd.DataFrame([
            {
                "Turn": 0,
                "Chapter": 1,
                "Vitality": state.health,
                "Sanity": state.sanity,
                "Vitality Δ": 0,
                "Sanity Δ": 0,
                "Active Quests": len(state.active_quests),
                "Inventory Items": len(state.inventory),
                "Danger Level": "Safe",
                "Action": "Genesis",
            }
        ])

    rows = []
    for item in state.turn_telemetry:
        danger_str = ["Safe", "Cautious", "Perilous", "Dire", "Critical", "Death's Door"][min(5, max(0, item.get("danger_level", 0)))]
        rows.append({
            "Turn": item["turn"],
            "Chapter": item["chapter"],
            "Vitality": item["health"],
            "Sanity": item["sanity"],
            "Vitality Δ": item["health_delta"],
            "Sanity Δ": item["sanity_delta"],
            "Active Quests": item["active_quests"],
            "Inventory Items": item["inventory_count"],
            "Danger Level": danger_str,
            "Action": item.get("action_summary", "Action"),
        })

    df = pd.DataFrame(rows)
    return df


def get_inventory_dataframe(state: StoryState) -> pd.DataFrame:
    """Generate an editable Pandas DataFrame for player inventory management.

    Returns:
        DataFrame with columns ['Item Name', 'Category', 'Equipped', 'Condition', 'Player Notes'].
    """
    rows = []
    for item in state.inventory:
        meta = state.inventory_metadata.get(item, {})
        rows.append({
            "Item Name": item,
            "Category": meta.get("category", "Equipment"),
            "Equipped": bool(meta.get("equipped", False)),
            "Condition": meta.get("condition", "Good"),
            "Player Notes": meta.get("notes", "No notes recorded"),
        })

    if not rows:
        return pd.DataFrame(columns=["Item Name", "Category", "Equipped", "Condition", "Player Notes"])

    return pd.DataFrame(rows)


def update_inventory_from_dataframe(state: StoryState, edited_df: pd.DataFrame) -> None:
    """Apply interactive user edits from ``st.data_editor`` back into the state."""
    if edited_df.empty:
        return

    new_items = []
    for _, row in edited_df.iterrows():
        item_name = str(row.get("Item Name", "")).strip()
        if not item_name:
            continue
        new_items.append(item_name)
        state.inventory_metadata[item_name] = {
            "category": str(row.get("Category", "Equipment")),
            "equipped": bool(row.get("Equipped", False)),
            "condition": str(row.get("Condition", "Good")),
            "notes": str(row.get("Player Notes", "")),
        }
    state.inventory = new_items


def get_npc_dataframe(state: StoryState) -> pd.DataFrame:
    """Generate a clean Pandas DataFrame of all discovered NPCs."""
    if not state.npc_relationships:
        return pd.DataFrame(columns=["NPC Name", "Disposition", "Status", "Attitude"])

    rows = []
    for name, disp in state.npc_relationships.items():
        status = "Ally" if "friendly" in disp.lower() else ("Adversary" if "hostile" in disp.lower() or "antagonist" in disp.lower() else "Neutral")
        rows.append({
            "NPC Name": name,
            "Disposition": disp,
            "Status": status,
            "Attitude": "🟢 Favorable" if status == "Ally" else ("🔴 Hostile" if status == "Adversary" else "🟡 Guarded"),
        })

    return pd.DataFrame(rows)


def get_world_locations_df(state: StoryState) -> pd.DataFrame:
    """Generate geographic coordinate data for interactive cartography / st.map."""
    nodes = _WORLD_MAP_NODES.get(state.world_name, [
        {"location": f"{state.world_name} Gateway", "lat": 37.7749, "lon": -122.4194, "status": "Current", "danger": "Moderate"}
    ])
    return pd.DataFrame(nodes)


def export_telemetry_csv(state: StoryState) -> str:
    """Export complete journey telemetry as formatted CSV string."""
    df = get_turn_history_df(state)
    return df.to_csv(index=False)


def strip_tags(text: str) -> str:
    """Remove all system tags from a DM response for display purposes."""
    cleaned = re.sub(
        r"\[(?:HEALTH_CHANGE|SANITY_CHANGE|ITEM_GAINED|ITEM_LOST|"
        r"NPC_MET|QUEST_STARTED|QUEST_COMPLETED|WORLD_FLAG|CHAPTER_END)"
        r"[^\]]*\]",
        "",
        text,
    )
    # Clean up extra whitespace left behind
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def export_story_as_text(state: StoryState) -> str:
    """Format the full story history as a readable .txt export.

    Returns:
        A formatted string suitable for saving as a text file.
    """
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append(f"  CHRONICLE AI — Story Export")
    lines.append(f"  World: {state.world_name}")
    lines.append(f"  Protagonist: {state.protagonist_name} the {state.protagonist_class}")
    lines.append(f"  Session: {state.session_id}")
    lines.append("=" * 60)
    lines.append("")

    turn = 0
    for i in range(0, len(state.full_history), 2):
        turn += 1
        player_entry = state.full_history[i] if i < len(state.full_history) else None
        dm_entry = state.full_history[i + 1] if i + 1 < len(state.full_history) else None

        if player_entry:
            lines.append(f"> [Turn {turn}] PLAYER: {player_entry['content']}")
            lines.append("")
        if dm_entry:
            lines.append(strip_tags(dm_entry["content"]))
            lines.append("")
            lines.append("-" * 40)
            lines.append("")

    # Final stats
    stats = compute_story_stats(state)
    lines.append("")
    lines.append("=" * 60)
    lines.append("  STORY STATISTICS")
    lines.append(f"  Turns Survived: {stats['total_turns']}")
    lines.append(f"  Chapter Reached: {stats['chapter']}")
    lines.append(f"  NPCs Met: {stats['unique_npcs_met']}")
    lines.append(f"  Quests: {stats['quests_ratio']}")
    lines.append(f"  Final Health: {state.health}/100")
    lines.append(f"  Final Sanity: {state.sanity}/100")
    lines.append(f"  Danger Level: {stats['danger_label']}")
    lines.append("=" * 60)

    return "\n".join(lines)
