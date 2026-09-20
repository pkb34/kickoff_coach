"""Local, deterministic processing of a confirmed quiz record.

The output is descriptive. It does not score health, predict outcomes, or infer
facts that the student did not provide. Gemini receives a smaller projection of
this output, never the raw follow-up answers or transcript.
"""

from __future__ import annotations

import math

from local_question_agent import BASELINE_SPECS, CORE_QUESTION_IDS, MAX_DEEP_QUESTIONS


ANALYSIS_SCHEMA_VERSION = "1.0"


def _number(fields: dict, key: str) -> float | None:
    field = fields[key]
    status = field.get("status")
    if status in {"unknown", "declined"}:
        return None
    if status != "answered":
        raise ValueError(f"Unexpected status for {key}.")
    value = field.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Invalid numeric value for {key}.")
    low, high = BASELINE_SPECS[key]["range"]
    if not low <= value <= high:
        raise ValueError(f"Value outside the expected range for {key}.")
    return round(float(value), 1)


def analyze_record(record: dict) -> dict:
    """Create an evidence-linked local analysis from a completed v2 record."""
    if not isinstance(record, dict) or record.get("schema_version") != "2.0":
        raise ValueError("A confirmed collection record with schema 2.0 is required.")
    fields = record.get("baseline", {}).get("fields", {})
    followups = record.get("followups", {})
    if set(fields) != set(BASELINE_SPECS):
        raise ValueError("The collection record has unexpected baseline fields.")
    if not isinstance(followups, dict) or not set(CORE_QUESTION_IDS).issubset(followups):
        raise ValueError("Required follow-up topics are missing.")
    if not 7 <= len(followups) <= MAX_DEEP_QUESTIONS or record.get("coverage", {}).get("complete") is not True:
        raise ValueError("The collection record is incomplete.")

    activity = _number(fields, "activity_hours")
    class_time = _number(fields, "class_hours")
    weekday = _number(fields, "weekday_study_hours")
    weekend = _number(fields, "weekend_study_hours")
    sleep = _number(fields, "sleep_hours")
    rating = followups["wellbeing_rating"].get("value")
    if followups["wellbeing_rating"].get("status") == "answered":
        if isinstance(rating, bool) or not isinstance(rating, (int, float)) or not math.isfinite(rating) or not 0 <= rating <= 10:
            raise ValueError("The self-reported happiness rating is invalid.")
        happiness_index = round(float(rating) * 10)
    else:
        happiness_index = None
    weekly_study = round(5 * weekday + 2 * weekend, 1) if weekday is not None and weekend is not None else None
    commitments = (
        round(class_time + activity + weekly_study, 1)
        if class_time is not None and activity is not None and weekly_study is not None else None
    )

    metrics = {
        "weekly_class_hours": class_time,
        "weekly_extracurricular_hours": activity,
        "weekly_independent_study_hours": weekly_study,
        "weekly_reported_commitment_hours": commitments,
        "nightly_sleep_hours": sleep,
        "self_reported_happiness_index": happiness_index,
    }
    observations = []
    if weekly_study is not None:
        observations.append({
            "text": f"Reported study outside class totals about {weekly_study:g} hours per week using five weekdays and two weekend days.",
            "evidence": ["weekday_study_hours", "weekend_study_hours"],
        })
    if commitments is not None:
        observations.append({
            "text": f"Reported class, independent study, and extracurricular time totals about {commitments:g} hours per week.",
            "evidence": ["class_hours", "weekday_study_hours", "weekend_study_hours", "activity_hours"],
        })
    if sleep is not None:
        observations.append({
            "text": f"Reported average sleep is about {sleep:g} hours per night.",
            "evidence": ["sleep_hours"],
        })
    if happiness_index is not None:
        observations.append({
            "text": f"You rated your happiness over the past seven days as {rating:g}/10; the display scales this to {happiness_index}/100.",
            "evidence": ["wellbeing_rating"],
        })

    unavailable = [key for key, field in fields.items() if field.get("status") in {"unknown", "declined"}]
    topic_status = {key: followups[key].get("status", "missing") for key in CORE_QUESTION_IDS}
    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "source_record_schema_version": "2.0",
        "status": "descriptive_only",
        "metrics": metrics,
        "observations": observations,
        "data_gaps": unavailable,
        "topic_status": topic_status,
        "performance_context": {
            "class_hours_available": class_time is not None,
            "study_hours_available": weekly_study is not None,
            "learning_barrier_response_available": topic_status["learning_barrier"] == "answered",
        },
        "wellbeing_context": {
            "sleep_hours_available": sleep is not None,
            "sleep_quality_response_available": topic_status["sleep_quality"] == "answered",
            "campus_connection_response_available": topic_status["campus_belonging"] == "answered",
            "happiness_rating_available": happiness_index is not None,
            "assessment_status": "not_assessed",
        },
        "limitations": [
            "These are descriptions of student-reported information, not an academic or health assessment.",
            "The happiness index is only the student's own 0–10 rating multiplied by ten; it is not a validated scale.",
            "No future outcome is predicted from this single check-in.",
        ],
    }


def gemini_summary(analysis: dict) -> dict:
    """Whitelisted, text-free projection permitted to leave the local app."""
    if analysis.get("schema_version") != ANALYSIS_SCHEMA_VERSION:
        raise ValueError("A valid local analysis is required.")
    metrics = analysis["metrics"]
    allowed = (
        "weekly_class_hours", "weekly_extracurricular_hours",
        "weekly_independent_study_hours", "nightly_sleep_hours",
    )
    return {
        "time_summary": {key: metrics[key] for key in allowed},
        "self_reported_happiness_index": metrics["self_reported_happiness_index"],
        "unavailable_time_fields": [key for key in allowed if metrics[key] is None],
        "context_available": {
            "learning_barrier": analysis["performance_context"]["learning_barrier_response_available"],
            "sleep_quality": analysis["wellbeing_context"]["sleep_quality_response_available"],
            "campus_connection": analysis["wellbeing_context"]["campus_connection_response_available"],
        },
    }
