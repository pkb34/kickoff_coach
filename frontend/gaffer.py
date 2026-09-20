"""Gemini-powered, non-clinical study-habit guidance for WCPT results."""

from __future__ import annotations

import os


def _answered_value(record: dict, field: str) -> str:
    """Return a safe display value without forwarding unavailable answers."""
    detail = record.get("fields", {}).get(field, {})
    if detail.get("status") != "answered":
        return "not provided"
    return str(detail.get("value"))


def _fallback_advice(personality: dict) -> str:
    """Keep the prototype useful when an API key is not configured."""
    return (
        f"As a {personality['name']}, start with one small, repeatable change this week: "
        "choose two study blocks and protect a consistent wind-down time before bed. "
        "If your schedule or wellbeing feels hard to manage, consider talking with a trusted person "
        "or a campus support resource."
    )


def get_gaffer_advice(record: dict, personality: dict) -> dict:
    """Ask Gemini for concise encouragement based on confirmed, non-identifying answers."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "provider": "local fallback",
            "text": _fallback_advice(personality),
        }

    prompt = f"""
You are The Gaffer, an encouraging student-success coach in a soccer-themed app.

The student received the illustrative football personality: {personality['name']}.
Their confirmed, self-reported check-in is:
- Average nightly sleep: {_answered_value(record, 'sleep_hours')} hours
- Weekly class time: {_answered_value(record, 'class_hours')} hours
- GPA: {_answered_value(record, 'gpa')} on a 0–4 scale
- Weekly extracurricular time: {_answered_value(record, 'activity_hours')} hours
- Weekday independent study: {_answered_value(record, 'weekday_study_hours')} hours per day
- Weekend independent study: {_answered_value(record, 'weekend_study_hours')} hours per day

Write a supportive halftime briefing of 80–120 words. Give exactly two practical,
low-pressure actions for the coming week that support study habits and wellbeing.
Use encouraging, nonjudgmental language. Do not diagnose conditions, make academic
predictions, prescribe treatment, or treat the personality as a fact. If sleep is low
or the workload seems difficult, gently suggest a trusted person or campus resource.
Do not repeat personal identifiers or ask the student for sensitive details.
""".strip()

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt,
        )
        text = interaction.output_text.strip()
        if text:
            return {"provider": "Gemini", "text": text}
    except Exception:
        pass

    return {
        "provider": "local fallback",
        "text": _fallback_advice(personality),
    }
