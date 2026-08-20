"""
audio_handler.py — Audio processing utilities for ChronicleAI.

Handles extraction, validation, and formatting of audio data
from Streamlit's st.audio_input widget for the Gemini API.
"""

from __future__ import annotations

import base64
import logging

logger = logging.getLogger(__name__)


def process_streamlit_audio(audio_input) -> bytes | None:
    """Extract raw bytes from a Streamlit audio_input widget value.

    Args:
        audio_input: The ``UploadedFile``-like object returned by
            ``st.audio_input()``. May be ``None`` if the user hasn't
            recorded anything.

    Returns:
        Raw audio bytes, or ``None`` if the input is empty/invalid.
    """
    if audio_input is None:
        return None

    try:
        audio_bytes = audio_input.read()
        # Reset the stream position so the widget can replay the audio
        audio_input.seek(0)

        if not audio_bytes:
            logger.warning("audio_input returned empty bytes")
            return None

        return audio_bytes
    except Exception as exc:
        logger.error("Failed to process audio input: %s", exc)
        return None


def validate_audio(audio_bytes: bytes) -> bool:
    """Check that audio data is non-trivial (not silence / empty).

    A minimum of 500 bytes filters out near-silent clips and corrupt
    recordings that would waste an API call.

    Args:
        audio_bytes: Raw audio data.

    Returns:
        ``True`` if the audio appears valid for transcription.
    """
    if not audio_bytes:
        return False
    if len(audio_bytes) < 500:
        logger.info(
            "Audio rejected: %d bytes (minimum 500)", len(audio_bytes)
        )
        return False
    return True


def format_audio_for_gemini(audio_bytes: bytes) -> dict:
    """Format raw audio bytes as an inline data part for the Gemini API.

    The ``google-genai`` SDK accepts inline audio as a dict with
    ``mime_type`` and ``data`` (base64-encoded) under the
    ``inline_data`` key.

    Args:
        audio_bytes: Raw audio data (WAV format from Streamlit recorder).

    Returns:
        A dict structured for the Gemini ``contents`` message format::

            {
                "inline_data": {
                    "mime_type": "audio/wav",
                    "data": "<base64-encoded bytes>"
                }
            }
    """
    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    return {
        "inline_data": {
            "mime_type": "audio/wav",
            "data": encoded,
        }
    }
