"""Aggregate-only staff statistics and an optional Gemini narrative.

No student identifiers, individual answers, transcripts, or free text enter the
Gemini request. The report describes self-reports; it is not a prediction model.
"""

from __future__ import annotations

import json
import math
import re
from urllib import error, request

from gemini_gateway import ENDPOINT, _settings


MIN_REPORT_CHECKINS = 10
MIN_MEASURE_RESPONSES = 5
TIME_FIELDS = {
    "weekly_class_hours": (0, 60),
    "weekly_independent_study_hours": (0, 168),
    "weekly_extracurricular_hours": (0, 60),
    "nightly_sleep_hours": (0, 24),
}
PROGRESS_OPTIONS = {
    "Feeling on track",
    "Keeping up, but stretched",
    "Feeling behind",
    "Not sure yet",
}


def _valid_number(value: object, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and minimum <= number <= maximum else None


def _rounded_share(part: int, whole: int) -> int | None:
    return round(100 * part / whole / 10) * 10 if whole else None


def build_staff_snapshot(analyses: list[dict]) -> dict:
    """Create a small allowlisted aggregate, safe to include in a report prompt."""
    metrics = [item.get("metrics") for item in analyses if isinstance(item, dict)]
    metrics = [item for item in metrics if isinstance(item, dict)]
    cohort = len(metrics)

    times = {}
    for key, (minimum, maximum) in TIME_FIELDS.items():
        values = [_valid_number(item.get(key), minimum, maximum) for item in metrics]
        answers = [value for value in values if value is not None]
        times[key] = {
            "responses": len(answers),
            "approximate_mean_hours": (
                round(sum(answers) / len(answers), 1)
                if len(answers) >= MIN_MEASURE_RESPONSES else None
            ),
        }

    ratings = [_valid_number(item.get("self_reported_happiness_index"), 0, 100) for item in metrics]
    ratings = [value for value in ratings if value is not None]
    progress = [item.get("self_reported_academic_progress") for item in metrics]
    progress = [value for value in progress if isinstance(value, str) and value in PROGRESS_OPTIONS]

    return {
        "completed_checkins": cohort,
        "time": times,
        "wellbeing_self_report": {
            "responses": len(ratings),
            "mean_rating_out_of_10": (
                round(sum(ratings) / len(ratings) / 10, 1)
                if len(ratings) >= MIN_MEASURE_RESPONSES else None
            ),
            "share_rating_0_to_4_percent_rounded_to_10": _rounded_share(
                sum(value <= 40 for value in ratings), len(ratings)
            ) if len(ratings) >= MIN_MEASURE_RESPONSES else None,
        },
        "academic_progress_self_report": {
            "responses": len(progress),
            "share_feeling_on_track_percent_rounded_to_10": _rounded_share(
                progress.count("Feeling on track"), len(progress)
            ) if len(progress) >= MIN_MEASURE_RESPONSES else None,
            "share_stretched_or_behind_percent_rounded_to_10": _rounded_share(
                sum(value in {"Keeping up, but stretched", "Feeling behind"} for value in progress),
                len(progress),
            ) if len(progress) >= MIN_MEASURE_RESPONSES else None,
        },
    }


def _validate_report(candidate: object, model: str) -> dict:
    if not isinstance(candidate, dict):
        raise ValueError("Gemini did not return a JSON report.")
    fields = ("overview", "wellbeing", "performance", "limitations")
    if any(not isinstance(candidate.get(key), str) or not 1 <= len(candidate[key]) <= 1000 for key in fields):
        raise ValueError("Gemini returned an incomplete report.")
    actions = candidate.get("suggested_actions")
    if not isinstance(actions, list) or len(actions) != 3 or any(
        not isinstance(action, str) or not 1 <= len(action) <= 400 for action in actions
    ):
        raise ValueError("Gemini returned invalid suggested actions.")
    if any(re.search(r"\d|[%％]", text) for text in
           [*(candidate[key] for key in fields), *actions]):
        raise ValueError("Gemini repeated a numeric statistic outside the checked table.")
    return {"status": "generated", "model": model,
            **{key: candidate[key].strip() for key in fields},
            "suggested_actions": [action.strip() for action in actions]}


def generate_staff_report(snapshot: dict, *, api_key: str | None = None,
                          model: str | None = None, opener=None) -> dict:
    """Ask Gemini to explain aggregate patterns for authenticated staff only."""
    if snapshot.get("completed_checkins", 0) < MIN_REPORT_CHECKINS:
        return {"status": "insufficient_data",
                "message": f"At least {MIN_REPORT_CHECKINS} check-ins are needed for a group report."}
    configured_key, configured_model = _settings()
    key = api_key or configured_key
    selected_model = model or configured_model
    if not key:
        return {"status": "not_configured", "message": "Gemini is not configured on this server."}
    if not isinstance(selected_model, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", selected_model):
        raise ValueError("Invalid Gemini model name.")

    prompt = (
        "You are preparing a concise, empathetic internal student-support report for university staff. "
        "Use only the aggregate JSON below. It contains no individual records. "
        "Discuss (1) reported wellbeing, (2) reported academic progress and study context, "
        "and (3) exactly three practical, non-punitive support actions for staff. "
        "The app will separately display the exact figures and response counts. Do not repeat ANY numbers, "
        "percentages, statistics, or response counts in your prose. Write qualitative interpretation only. "
        "Approximate time averages come from the midpoints of answer ranges. "
        "The wellbeing figure is a direct happiness rating, not a health score. "
        "Academic progress is the student's own choice, not grades or measured performance. "
        "A metric set to null was suppressed because fewer than five students answered it; "
        "do not calculate or infer its value. "
        "Do not diagnose, rank students, identify anyone, infer causes, claim an intervention will work, "
        "predict future academic or health outcomes, or invent trends over time. "
        "If the sample is small or answers are missing, say so. Describe associations only if the "
        "aggregate data actually contains a cross-tabulation; it does not here. "
        "Return only JSON with overview, wellbeing, performance, suggested_actions (exactly three "
        "strings), and limitations. Use clear English and no football metaphors.\n"
        + json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
    )
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 850}}
    http_request = request.Request(
        ENDPOINT.format(model=selected_model), data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with (opener or request.urlopen)(http_request, timeout=25) as response:
            payload = json.load(response)
        parts = payload["candidates"][0]["content"]["parts"]
        content = "".join(part.get("text", "") for part in parts)
        return _validate_report(json.loads(content), selected_model)
    except error.HTTPError as exc:
        exc.close()
        if exc.code == 404:
            message = "The configured Gemini model is unavailable for this key."
        elif exc.code in {400, 401, 403}:
            message = "Gemini rejected the key or request. Check the local API setup."
        else:
            message = f"Gemini returned HTTP {exc.code}. Please try again later."
        return {"status": "unavailable", "message": message}
    except (error.URLError, OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError):
        return {"status": "unavailable", "message": "Gemini could not produce a valid report. Please try again."}
