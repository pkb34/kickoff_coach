"""Compatibility entry point for the teammate's Gaffer feature.

The active result page uses gemini_gateway directly. This adapter retains the
original get_gaffer_advice interface without forwarding raw answers or the old
collection schema to Gemini.
"""

from __future__ import annotations

from analysis_agent import analyze_record
from gemini_gateway import generate_briefing


def _fallback_advice(personality: dict) -> str:
    name = personality.get("name", "player")
    return (
        f"As a {name}, consider one small, repeatable step this week. "
        "You can plan a manageable study block and leave room for rest."
    )


def get_gaffer_advice(record: dict, personality: dict) -> dict:
    """Return optional Gemini advice for a confirmed v2 record, or local text."""
    if record.get("schema_version") != "2.0":
        return {"provider": "local fallback", "text": _fallback_advice(personality)}
    briefing = generate_briefing(analyze_record(record))
    if briefing.get("status") == "generated":
        text = " ".join([briefing["summary"], *briefing["suggestions"]])
        return {"provider": "Gemini", "text": text,
                "future_moments": briefing["future_moments"]}
    return {"provider": "local fallback", "text": _fallback_advice(personality)}
