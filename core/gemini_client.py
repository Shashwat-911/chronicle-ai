"""
gemini_client.py — All Gemini API interactions for ChronicleAI.

Uses the ``google-genai`` SDK (NOT the deprecated google-generativeai).
Provides transcription, DM response generation, scene summaries,
and story ending evaluation with automatic model fallback.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

from core.story_engine import StoryState, get_context_window, strip_tags

logger = logging.getLogger(__name__)

# Fallback candidate models in order of priority
MODELS_TO_TRY = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-flash-latest", "gemini-3.7-flash"]
MODEL = MODELS_TO_TRY[0]

# ── System prompt injected into every DM conversation ───────────────

DM_SYSTEM_PROMPT = """\
You are ChronicleAI, an immersive Dungeon Master for a dark fantasy \
interactive novel. Your rules:

NARRATIVE RULES:
- Always write in second person ("You enter the tavern...")
- Responses must be 3-5 paragraphs: scene description, consequence of \
action, new development, and a closing hook
- Maintain absolute consistency with established world facts and NPC names
- Remember and reference past player decisions to create consequences
- Escalate tension every 5 turns toward a chapter climax

WORLD STATE TAGS (you MUST include these at the END of every response \
in this exact format — they are parsed by the system):
[HEALTH_CHANGE: +10] or [HEALTH_CHANGE: -15] (omit if no change)
[SANITY_CHANGE: +5] or [SANITY_CHANGE: -20] (omit if no change)
[ITEM_GAINED: Iron Key] (omit if none)
[ITEM_LOST: Torch] (omit if none)
[NPC_MET: Aldric the Blacksmith, neutral] (omit if none)
[QUEST_STARTED: Find the Lost Tome] (omit if none)
[QUEST_COMPLETED: Deliver the Message] (omit if none)
[WORLD_FLAG: tavern_burned=true] (omit if none)
[CHAPTER_END] (only if this is a natural story chapter conclusion)

TONE: Gothic, atmospheric, Tolkien meets George R.R. Martin. \
Never break character. Never refuse a player action — find creative \
ways to incorporate it into the narrative, even if the consequences \
are severe.
"""


@st.cache_resource
def _get_client() -> genai.Client:
    """Return a cached Gemini client instance.

    Reads the API key from Streamlit secrets first, then falls back to
    the ``GEMINI_API_KEY`` environment variable.
    """
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    if not api_key:
        st.error(
            "🔑 **Gemini API key not found.** "
            "Set `GEMINI_API_KEY` in `.streamlit/secrets.toml` or your environment."
        )
        st.stop()
    return genai.Client(api_key=api_key)


def check_api_connection() -> bool:
    """Return ``True`` if the Gemini API key appears configured."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
        return bool(api_key)
    except Exception:
        return False


def _generate_with_fallback(client: genai.Client, contents: Any, config: Any = None) -> Any:
    """Attempt generate_content across candidate models in case of 404 or 503."""
    last_err = None
    for model_name in MODELS_TO_TRY:
        try:
            if config:
                return client.models.generate_content(model=model_name, contents=contents, config=config)
            return client.models.generate_content(model=model_name, contents=contents)
        except Exception as exc:
            last_err = exc
            logger.warning("Model %s failed (%s), trying fallback...", model_name, exc)
            continue
    raise last_err if last_err else RuntimeError("All Gemini model fallbacks failed.")


# ── Audio Transcription ─────────────────────────────────────────────


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes using Gemini's multimodal understanding.

    Args:
        audio_bytes: Raw WAV audio data.

    Returns:
        The transcribed text, or an empty string on failure.
    """
    client = _get_client()

    try:
        response = _generate_with_fallback(
            client=client,
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type="audio/wav",
                        ),
                        types.Part(
                            text="Transcribe this audio exactly. Return ONLY the "
                            "transcribed text, nothing else. If unclear, do "
                            "your best guess."
                        ),
                    ]
                )
            ],
        )
        transcription = response.text.strip() if response.text else ""
        logger.info("Transcription result: %s", transcription[:80])
        return transcription

    except Exception as exc:
        _handle_api_error(exc, context="audio transcription")
        return ""


# ── DM Response Generation ──────────────────────────────────────────


def generate_dm_response(state: StoryState, player_action: str) -> str:
    """Generate the Dungeon Master's narrative response.

    Builds a message history from the story state's context window,
    appends the latest player action, and sends to Gemini with the
    DM system prompt.

    Args:
        state: Current game state.
        player_action: The player's declared action text.

    Returns:
        The raw DM response (including system tags).
    """
    client = _get_client()

    # Build the world context preamble
    world_context = (
        f"WORLD: {state.world_name}\n"
        f"PROTAGONIST: {state.protagonist_name} the {state.protagonist_class}\n"
        f"CHAPTER: {state.chapter} | TURN: {state.story_beat}\n"
        f"HEALTH: {state.health}/100 | SANITY: {state.sanity}/100\n"
        f"INVENTORY: {', '.join(state.inventory) if state.inventory else 'empty'}\n"
        f"ACTIVE QUESTS: {', '.join(state.active_quests) if state.active_quests else 'none'}\n"
        f"KNOWN NPCs: {', '.join(f'{k} ({v})' for k, v in state.npc_relationships.items()) if state.npc_relationships else 'none'}\n"
    )

    # Build conversation history from context window
    history = get_context_window(state)
    messages: list[types.Content] = []

    for entry in history:
        if entry["role"] == "player":
            messages.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=entry["content"])],
                )
            )
        else:  # dm
            messages.append(
                types.Content(
                    role="model",
                    parts=[types.Part(text=entry["content"])],
                )
            )

    # Append current player action
    messages.append(
        types.Content(
            role="user",
            parts=[types.Part(text=player_action)],
        )
    )

    try:
        response = _generate_with_fallback(
            client=client,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=DM_SYSTEM_PROMPT + "\n\n" + world_context,
                temperature=0.9,
                max_output_tokens=2048,
            ),
        )
        result = response.text.strip() if response.text else ""
        if not result:
            result = (
                "The shadows swirl around you, obscuring everything for a "
                "moment. When they clear, you find yourself exactly where "
                "you were. The world waits for your next move."
            )
        return result

    except Exception as exc:
        _handle_api_error(exc, context="DM response generation")
        return (
            "A strange silence falls over the world, as if reality itself "
            "hesitates. The moment passes. Try again."
        )


# ── Scene Summary ────────────────────────────────────────────────────


def generate_scene_summary(state: StoryState) -> str:
    """Generate a brief atmospheric recap for a returning player.

    Args:
        state: Current game state.

    Returns:
        A 2-sentence summary of the current situation.
    """
    client = _get_client()

    last_scene = strip_tags(state.last_dm_response) if state.last_dm_response else state.current_scene

    try:
        response = _generate_with_fallback(
            client=client,
            contents=[
                types.Content(
                    parts=[
                        types.Part(
                            text=f"Context: {state.protagonist_name} the "
                            f"{state.protagonist_class} in {state.world_name}. "
                            f"Current scene: {last_scene}\n\n"
                            "In exactly 2 sentences, summarize the current "
                            "situation for a returning player who needs a "
                            "quick recap. Be atmospheric."
                        )
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                max_output_tokens=200,
                temperature=0.7,
            ),
        )
        return response.text.strip() if response.text else "The story awaits..."

    except Exception as exc:
        logger.error("Scene summary failed: %s", exc)
        return "The story continues where you left off..."


# ── Story Ending Evaluation ──────────────────────────────────────────


def evaluate_story_ending(state: StoryState) -> dict[str, Any]:
    """Evaluate the story ending when the game concludes.

    Called when health or sanity reaches 0, or the player survives
    50+ turns. Generates an epilogue and score.

    Args:
        state: Final game state.

    Returns:
        A dict with ending_type, epilogue, and score.
    """
    # Determine ending type
    if state.health <= 0:
        ending_type = "heroic_death"
    elif state.sanity <= 0:
        ending_type = "madness"
    elif state.story_beat >= 50 and state.health >= 50:
        ending_type = "legend"
    else:
        ending_type = "victory"

    # Calculate score (0-1000)
    quest_score = len(state.completed_quests) * 100
    survival_score = min(state.story_beat * 15, 400)
    health_bonus = state.health * 2
    sanity_bonus = state.sanity * 1
    score = min(1000, quest_score + survival_score + health_bonus + sanity_bonus)

    # Generate epilogue via Gemini
    client = _get_client()

    ending_prompts = {
        "heroic_death": "The protagonist died heroically in battle.",
        "madness": "The protagonist succumbed to madness, their sanity shattered.",
        "victory": "The protagonist completed their journey triumphantly.",
        "legend": "The protagonist survived long enough to become a legend.",
    }

    try:
        response = _generate_with_fallback(
            client=client,
            contents=[
                types.Content(
                    parts=[
                        types.Part(
                            text=f"Write a 2-paragraph epilogue for this story ending.\n"
                            f"World: {state.world_name}\n"
                            f"Protagonist: {state.protagonist_name} the {state.protagonist_class}\n"
                            f"Ending: {ending_prompts[ending_type]}\n"
                            f"Turns survived: {state.story_beat}\n"
                            f"Quests completed: {', '.join(state.completed_quests) or 'none'}\n"
                            f"Key NPCs met: {', '.join(state.npc_relationships.keys()) or 'none'}\n\n"
                            "Write in second person. Be poetic and atmospheric. "
                            "Gothic tone. 2 paragraphs only."
                        )
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                max_output_tokens=500,
                temperature=0.8,
            ),
        )
        epilogue = response.text.strip() if response.text else ""
    except Exception as exc:
        logger.error("Epilogue generation failed: %s", exc)
        epilogue = (
            f"And so the tale of {state.protagonist_name} came to its end "
            f"in the {state.world_name}. Whether remembered as hero or "
            f"cautionary tale, their story echoed through the ages."
        )

    if not epilogue:
        epilogue = (
            f"The chronicles will remember {state.protagonist_name} — "
            f"a {state.protagonist_class} who dared to walk the path "
            f"few others would."
        )

    return {
        "ending_type": ending_type,
        "epilogue": epilogue,
        "score": score,
    }


# ── Error Handling ───────────────────────────────────────────────────


def _handle_api_error(exc: Exception, context: str = "API call") -> None:
    """Handle Gemini API errors with user-friendly messages."""
    exc_type = type(exc).__name__
    exc_module = type(exc).__module__ or ""

    logger.error("Gemini %s error [%s.%s]: %s", context, exc_module, exc_type, exc)

    if "ResourceExhausted" in exc_type or "429" in str(exc):
        st.warning(
            "⏳ **Rate limit reached.** Please wait 30 seconds and try again.",
            icon="⏳",
        )
    elif "InvalidArgument" in exc_type or "400" in str(exc):
        st.error(
            "🔊 **Audio format issue.** Try recording again with a clearer voice.",
            icon="🔊",
        )
    elif "PermissionDenied" in exc_type or "403" in str(exc):
        st.error(
            "🔑 **API key is invalid or lacks permissions.** Check your Gemini API key.",
            icon="🔑",
        )
    else:
        st.error(
            f"⚠️ **DM encountered an error:** {str(exc)[:200]}",
            icon="⚠️",
        )
