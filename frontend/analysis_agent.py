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


def _interval(fields: dict, key: str, estimate: float | None) -> list[float] | None:
    """Retain the actual selected range; older exact answers become point intervals."""
    if estimate is None:
        return None
    interval = fields[key].get("range", [estimate, estimate])
    minimum, maximum = BASELINE_SPECS[key]["range"]
    if (not isinstance(interval, list) or len(interval) != 2 or
            any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in interval) or
            not minimum <= interval[0] <= estimate <= interval[1] <= maximum):
        raise ValueError(f"Invalid reported range for {key}.")
    return [float(interval[0]), float(interval[1])]


def _span(interval: list[float]) -> str:
    low, high = interval
    return f"{low:g}" if low == high else f"{low:g}–{high:g}"


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
    activity_range = _interval(fields, "activity_hours", activity)
    class_range = _interval(fields, "class_hours", class_time)
    weekday_range = _interval(fields, "weekday_study_hours", weekday)
    weekend_range = _interval(fields, "weekend_study_hours", weekend)
    sleep_range = _interval(fields, "sleep_hours", sleep)
    rating = followups["wellbeing_rating"].get("value")
    if followups["wellbeing_rating"].get("status") == "answered":
        if isinstance(rating, bool) or not isinstance(rating, (int, float)) or not math.isfinite(rating) or not 0 <= rating <= 10:
            raise ValueError("The self-reported happiness rating is invalid.")
        happiness_index = round(float(rating) * 10)
    else:
        happiness_index = None
    weekly_study = round(5 * weekday + 2 * weekend, 1) if weekday is not None and weekend is not None else None
    weekly_study_range = ([5 * weekday_range[0] + 2 * weekend_range[0],
                           5 * weekday_range[1] + 2 * weekend_range[1]]
                          if weekday_range and weekend_range else None)
    commitments = (
        round(class_time + activity + weekly_study, 1)
        if class_time is not None and activity is not None and weekly_study is not None else None
    )
    commitment_range = ([class_range[0] + activity_range[0] + weekly_study_range[0],
                         class_range[1] + activity_range[1] + weekly_study_range[1]]
                        if class_range and activity_range and weekly_study_range else None)

    metrics = {
        "weekly_class_hours": class_time,
        "weekly_extracurricular_hours": activity,
        "weekly_independent_study_hours": weekly_study,
        "weekly_reported_commitment_hours": commitments,
        "nightly_sleep_hours": sleep,
        "self_reported_happiness_index": happiness_index,
        "time_ranges": {
            "weekly_class_hours": class_range,
            "weekly_extracurricular_hours": activity_range,
            "weekly_independent_study_hours": weekly_study_range,
            "weekly_reported_commitment_hours": commitment_range,
            "nightly_sleep_hours": sleep_range,
        },
    }
    observations = []
    if weekly_study is not None:
        observations.append({
            "text": f"Reported study outside class spans about {_span(weekly_study_range)} hours per week using five weekdays and two weekend days.",
            "evidence": ["weekday_study_hours", "weekend_study_hours"],
        })
    if commitments is not None:
        observations.append({
            "text": f"Reported class, independent study, and extracurricular time spans about {_span(commitment_range)} hours per week.",
            "evidence": ["class_hours", "weekday_study_hours", "weekend_study_hours", "activity_hours"],
        })
    if sleep is not None:
        observations.append({
            "text": f"Reported usual sleep is {_span(sleep_range)} hours per night.",
            "evidence": ["sleep_hours"],
        })
    if happiness_index is not None:
        observations.append({
            "text": f"You rated how happy you feel lately as {rating:g}/10; the display scales this to {happiness_index}/100.",
            "evidence": ["wellbeing_rating"],
        })

    unavailable = [key for key, field in fields.items() if field.get("status") in {"unknown", "declined"}]
    topic_status = {key: followups[key].get("status", "missing") for key in CORE_QUESTION_IDS}
    progress = (followups["academic_progress"].get("answer")
                if topic_status["academic_progress"] == "answered" else None)
    if progress not in ("Feeling on track", "Keeping up, but stretched", "Feeling behind", "Not sure yet"):
        progress = None
    metrics["self_reported_academic_progress"] = progress
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
            "self_reported_progress": progress,
        },
        "wellbeing_context": {
            "sleep_hours_available": sleep is not None,
            "sleep_quality_response_available": topic_status["sleep_quality"] == "answered",
            "campus_connection_response_available": False,
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
        "time_ranges": {key: metrics.get("time_ranges", {}).get(key) for key in allowed},
        "self_reported_happiness_index": metrics["self_reported_happiness_index"],
        "unavailable_time_fields": [key for key in allowed if metrics[key] is None],
        "context_available": {
            "learning_barrier": analysis["performance_context"]["learning_barrier_response_available"],
            "sleep_quality": analysis["wellbeing_context"]["sleep_quality_response_available"],
            "campus_connection": analysis["wellbeing_context"]["campus_connection_response_available"],
        },
    }
