"""Questionnaire validation and a temporary, transparent agent stand-in."""

from __future__ import annotations

import math

ACTIVITY_TYPES = {
    "none": "None", "sports": "Sports", "arts": "Arts and Culture",
    "volunteer": "Volunteering", "academic": "Academic or Professional Club",
    "student_org": "Student Organization", "other": "Other",
}

PERSONALITIES = {
    "midfielder": {
        "name": "Midfielder", "icon": "🧭",
        "tagline": "The connector who keeps the game moving",
        "description": "In this demo, your mix of study, activities, and rest maps to the player who links different parts of the field.",
    },
    "captain": {
        "name": "Captain", "icon": "🫡",
        "tagline": "The team-minded organizer",
        "description": "In this demo, your time in group-oriented activities maps to the player who helps organize the team.",
    },
    "penalty_striker": {
        "name": "Penalty Striker", "icon": "🎯",
        "tagline": "The focused finisher",
        "description": "In this demo, your independent study commitment maps to the player who concentrates on a key moment.",
    },
    "defender": {
        "name": "Defender", "icon": "🛡️",
        "tagline": "The steady last line",
        "description": "In this demo, your current schedule maps to the player who brings steadiness and protects the team shape.",
    },
}


def _number(value: object, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{name} is outside the allowed range")
    return round(number, 1)


def validate_baseline(data: object) -> dict:
    """Validate the four topic groups on the first quiz page."""
    expected = {
        "sleep_hours", "class_hours", "gpa", "activity_hours",
        "weekday_study_hours", "weekend_study_hours",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError("Please complete all four sections")
    normalized = {
        "sleep_hours": _number(data["sleep_hours"], "Nightly sleep hours", 0, 24),
        "class_hours": _number(data["class_hours"], "Weekly class hours", 0, 60),
        "gpa": _number(data["gpa"], "GPA", 0, 4),
        "activity_hours": _number(data["activity_hours"], "Weekly extracurricular hours", 0, 60),
        "weekday_study_hours": _number(data["weekday_study_hours"], "Weekday study hours", 0, 24),
        "weekend_study_hours": _number(data["weekend_study_hours"], "Weekend study hours", 0, 24),
    }
    normalized["gpa"] = round(float(data["gpa"]), 2)
    return normalized


def validate_answers(data: object) -> dict:
    """Validate exactly the four questionnaire topics and normalize values."""
    if not isinstance(data, dict) or set(data) != {"study_hours", "activity", "class_hours", "sleep_hours"}:
        raise ValueError("Please answer all four questions")
    activity = data["activity"]
    if not isinstance(activity, dict) or set(activity) != {"type", "hours"}:
        raise ValueError("Please provide an activity type and weekly hours")
    kind = activity["type"]
    if kind not in ACTIVITY_TYPES:
        raise ValueError("Invalid activity type")
    normalized = {
        "study_hours": _number(data["study_hours"], "Weekly independent study hours", 0, 80),
        "activity_type": kind,
        "activity_hours": _number(activity["hours"], "Weekly extracurricular hours", 0, 60),
        "class_hours": _number(data["class_hours"], "Weekly class hours", 0, 60),
        "sleep_hours": _number(data["sleep_hours"], "Nightly sleep hours", 0, 24),
    }
    if kind == "none" and normalized["activity_hours"] != 0:
        raise ValueError("If you select 'None,' enter 0 activity hours")
    if kind != "none" and normalized["activity_hours"] == 0:
        raise ValueError("Enter your activity hours or select 'None'")
    return normalized


def assign_demo_personality(answers: dict) -> str:
    """Map four answers to a showcase profile; this is not a validated assessment."""
    weekly_study = 5 * answers["weekday_study_hours"] + 2 * answers["weekend_study_hours"]
    if (answers["activity_hours"] >= 8
            and answers["class_hours"] >= 12
            and answers["gpa"] >= 2.5):
        return "captain"
    if (weekly_study >= 18
            and answers["gpa"] >= 3.3
            and answers["activity_hours"] < 8):
        return "penalty_striker"
    if (weekly_study >= 10
            and answers["activity_hours"] >= 3
            and answers["sleep_hours"] >= 7):
        return "midfielder"
    return "defender"


def process_with_agent(answers: dict) -> dict:
    """Temporary rule-based result. Replace this function when an agent is built."""
    busy_hours = answers["study_hours"] + answers["class_hours"] + answers["activity_hours"]
    observations, suggestions = [], []
    if answers["sleep_hours"] < 7:
        observations.append("Your reported sleep duration is below seven hours per night.")
        suggestions.append("Consider setting aside a more consistent sleep window. If sleep continues to affect you, contact campus support services.")
    if busy_hours > 55:
        observations.append("Your combined weekly study, class, and activity time is high.")
        suggestions.append("Review your schedule and prioritize essential coursework and rest.")
    if answers["study_hours"] < 5:
        observations.append("You reported fewer than five hours of independent study per week.")
        suggestions.append("Try scheduling two manageable study sessions for one course.")
    if answers["activity_hours"] > 20:
        observations.append("You spend more than 20 hours per week on extracurricular activities.")
        suggestions.append("Check whether club commitments conflict with assignment deadlines.")
    if not observations:
        observations.append("The demo rules did not identify an immediate time-management concern.")
        suggestions.append("Maintain a sustainable routine and review your study, activity, and rest schedule each week.")
    return {
        "status": "demo_rule_result",
        "title": "Your Time-Use Summary",
        "weekly_scheduled_hours": round(busy_hours, 1),
        "observations": observations,
        "suggestions": suggestions,
        "note": "This feedback comes from temporary rules while the AI agent is under development. It is not a grade prediction or health diagnosis.",
    }
