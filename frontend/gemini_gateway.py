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
    if not isinstance(suggestions, list) or not 1 <= len(suggestions) <= 3:
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
        "You are The Gaffer, a warm, friendly football coach helping a college student reflect on their week. "
        "Speak directly to the student using you and natural contractions, with gentle encouragement "
        "and at most one playful football metaphor. Be caring and conversational, never clinical, "
        "judgmental, patronizing, or overly enthusiastic. "
        "Open by thanking them for taking a moment to check in. Acknowledge that busy or difficult "
        "weeks can happen without assuming how they feel. Do not minimize a low happiness rating "
        "or pressure them to be positive. Celebrate the act of reflecting, not invented achievements. "
        "Make each suggestion a small, achievable invitation using phrases like you could try or "
        "if it feels helpful. Remind them that one small step is enough and rest counts too. "
        "Use only the JSON summary below. If databricks_telemetry is present, treat it as synthetic demo telemetry and use it only to gently tailor the advice. "
        "Give a friendly summary grounded in the reported facts, two practical low-pressure suggestions, "
        "and one future_moments paragraph describing a possible positive moment in the coming week. "
        "Frame that paragraph as a possibility or choice, not as a prediction or guarantee. "
        "Do not invent student facts, assign a new score, diagnose health, predict future outcomes, or discuss academic marks. "
        "The context_available booleans indicate only that a response exists; they do not describe its meaning. "
        "The happiness index is a direct self-report scaled from 0–10, not a clinical assessment. "
        "Return only a JSON object with keys summary (string), suggestions (array of two strings), "
        "and future_moments (one short paragraph string).\n"
        + json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 300},
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
