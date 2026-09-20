"""Optional Gemini briefing from a minimal local analysis projection.

This is the only active module that makes a network request. It never receives
the collection transcript or raw free-text responses.
"""

from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path
from urllib import error, request

from analysis_agent import gemini_summary
from databricks_gateway import gemini_telemetry_summary
from local_question_agent import PROHIBITED


# A current, fast, lower-cost text model available through the Gemini API.
DEFAULT_MODEL = "gemini-2.5-flash-lite"
SECRETS_PATH = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _settings() -> tuple[str | None, str]:
    local = {}
    if SECRETS_PATH.is_file():
        with SECRETS_PATH.open("rb") as source:
            local = tomllib.load(source)
    key = os.getenv("GEMINI_API_KEY") or local.get("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL") or local.get("GEMINI_MODEL") or DEFAULT_MODEL
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", model):
        raise ValueError("Invalid Gemini model name.")
    return key, model


def is_configured() -> bool:
    key, _ = _settings()
    return bool(key)


def _validate_briefing(candidate: object, model: str) -> dict:
    if not isinstance(candidate, dict):
        raise ValueError("Gemini did not return a JSON object.")
    summary = candidate.get("summary")
    suggestions = candidate.get("suggestions")
    future_moments = candidate.get("future_moments")
    if not isinstance(summary, str) or not 1 <= len(summary) <= 600:
        raise ValueError("Gemini returned an invalid summary.")
    if not isinstance(suggestions, list) or len(suggestions) != 2:
        raise ValueError("Gemini returned invalid suggestions.")
    if any(not isinstance(item, str) or not 1 <= len(item) <= 400 for item in suggestions):
        raise ValueError("Gemini returned an invalid suggestion.")
    if not isinstance(future_moments, str) or not 1 <= len(future_moments) <= 900:
        raise ValueError("Gemini returned an invalid future-moments paragraph.")
    if PROHIBITED.search(" ".join([summary, *suggestions, future_moments])):
        raise ValueError("Gemini returned information outside the quiz scope.")
    return {"status": "generated", "provider": "gemini", "model": model,
            "summary": summary.strip(), "suggestions": [item.strip() for item in suggestions],
            "future_moments": future_moments.strip()}


def generate_briefing(analysis: dict, telemetry: dict | None = None, *, api_key: str | None = None,
                      model: str | None = None, opener=None) -> dict:
    """Send the whitelisted summary only and return a validated short briefing."""
    configured_key, configured_model = _settings()
    key = api_key or configured_key
    selected_model = model or configured_model
    if not key:
        return {"status": "not_configured", "message": "Gemini is not configured on this server."}
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", selected_model):
        raise ValueError("Invalid Gemini model name.")

    summary = gemini_summary(analysis)
    telemetry_summary = gemini_telemetry_summary(telemetry)
    if telemetry_summary:
        summary["databricks_telemetry"] = telemetry_summary
    prompt = (
        "You are The Gaffer, a gentle and encouraging football-themed companion for a college student. "
        "Address the student as you. Thank them for checking in without assuming they feel good or bad. "
        "If their self-reported happiness is low, acknowledge that difficult weeks happen; never minimize it, "
        "pressure them to be positive, diagnose them, or pretend to know the reason. "
        "Use the quiz's time_summary, time_ranges, and self_reported_happiness_index as the only facts about this student. "
        "The time_summary values may be midpoints of selected ranges; describe the time_ranges as approximate ranges, never as exact reported hours. "
        "Write one short, empathetic summary grounded in those facts. Then give exactly two different, "
        "specific and achievable tips tied to reported study, activity, class, or sleep time. "
        "Each tip should say why it fits the information available and offer a small optional next step. "
        "Use invitations such as you could try or if it feels helpful, not commands. "
        "If a detail is missing, do not infer it; give a conditional suggestion instead. "
        "The context_available flags only say whether answers exist, not what those answers mean. "
        "If databricks_telemetry appears, it is synthetic demo data about someone else: "
        "do not describe it as this student's data or use it to personalize the tips. "
        "Add one short future_moments paragraph about a possible positive moment next week, framed as a choice, "
        "never a prediction or guarantee. Use at most one playful football metaphor. "
        "Do not invent achievements, assign a score, discuss academic marks, or make health claims. "
        "The happiness index is a direct self-report scaled from 0–10, not a clinical assessment. "
        "Return only JSON with summary (string), suggestions (exactly two strings), and future_moments (string).\n"
        + json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 500},
    }
    url = ENDPOINT.format(model=selected_model)
    http_request = request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with (opener or request.urlopen)(http_request, timeout=20) as response:
            payload = json.load(response)
        parts = payload["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts)
        return _validate_briefing(json.loads(text), selected_model)
    except error.HTTPError as exc:
        exc.close()
        if exc.code == 404:
            message = "The configured Gemini model is unavailable for this key. Choose a model this key can use."
        elif exc.code in {400, 401, 403}:
            message = "Gemini rejected this API request or key. Check the local key and model access."
        else:
            message = f"Gemini returned HTTP {exc.code}. Try again later."
        return {"status": "unavailable", "message": message}
    except (error.URLError, OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return {"status": "unavailable", "message": "Gemini could not produce a valid briefing. Try again later."}
