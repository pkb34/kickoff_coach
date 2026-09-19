"""Conversation contract and honest, deterministic demo collector.

The future backend agent can replace start_collection/advance_collection while
returning the same JSON-compatible state. No LLM is used here.
"""

from __future__ import annotations

import copy
import math
import re
from datetime import datetime, timezone


SCHEMA_VERSION = "1.0"
UNKNOWN = {"i don't know", "dont know", "don't know", "unknown", "not sure", "skip"}
DECLINED = {"prefer not to say", "decline", "no answer"}

FIELDS = {
    "sleep_hours": {
        "label": "Average nightly sleep", "unit": "hours/night", "kind": "number", "range": (0, 24),
        "question": "On an average night, about how many hours do you sleep? Enter a number such as 7.5.",
    },
    "sleep_quality": {
        "label": "Morning restfulness", "unit": None, "kind": "choice",
        "question": "You reported less than 7 hours of sleep. How do you usually feel on waking: rested, sometimes tired, or often tired?",
        "choices": {"rested": "rested", "sometimes tired": "sometimes_tired", "often tired": "often_tired"},
    },
    "class_hours": {
        "label": "Weekly class time", "unit": "hours/week", "kind": "number", "range": (0, 60),
        "question": "About how many hours do you spend in scheduled classes in a typical week?",
    },
    "gpa": {
        "label": "Current GPA", "unit": "0-4 scale", "kind": "number", "range": (0, 4),
        "question": "What is your current GPA on a 0–4.0 scale? If you do not have one yet, answer 'I don't know'.",
    },
    "activity_hours": {
        "label": "Weekly extracurricular time", "unit": "hours/week", "kind": "number", "range": (0, 60),
        "question": "How many hours per week do you spend on clubs or other extracurricular activities? Enter 0 if none.",
    },
    "activity_type": {
        "label": "Main extracurricular activity", "unit": None, "kind": "text",
        "question": "What kind of club or extracurricular activity takes most of that time? A short description is enough.",
    },
    "weekday_study_hours": {
        "label": "Weekday independent study", "unit": "hours/day", "kind": "number", "range": (0, 24),
        "question": "On a typical weekday, how many hours do you study outside scheduled classes? Give a daily average.",
    },
    "weekend_study_hours": {
        "label": "Weekend independent study", "unit": "hours/day", "kind": "number", "range": (0, 24),
        "question": "On a typical weekend day, how many hours do you study outside scheduled classes? Give a daily average.",
    },
}

BASE_REQUIRED = (
    "sleep_hours", "class_hours", "gpa", "activity_hours",
    "weekday_study_hours", "weekend_study_hours",
)


def required_fields(fields: dict) -> list[str]:
    """Return fields needed for coverage, including conditional clarifications."""
    required = list(BASE_REQUIRED)
    sleep = fields.get("sleep_hours", {})
    if sleep.get("status") == "answered" and sleep.get("value", 24) < 7:
        required.insert(1, "sleep_quality")
    activity = fields.get("activity_hours", {})
    if activity.get("status") == "answered" and activity.get("value", 0) > 0:
        required.insert(required.index("activity_hours") + 1, "activity_type")
    return required


def next_field(fields: dict) -> str | None:
    return next((key for key in required_fields(fields) if key not in fields), None)


def coverage(fields: dict) -> dict:
    required = required_fields(fields)
    answered = [key for key in required if fields.get(key, {}).get("status") == "answered"]
    unavailable = [key for key in required if fields.get(key, {}).get("status") in ("unknown", "declined")]
    missing = [key for key in required if key not in fields]
    return {
        "required": required, "answered": answered, "unavailable": unavailable,
        "missing": missing, "complete": not missing,
    }


def start_collection() -> dict:
    first = next_field({})
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "demo",
        "status": "collecting",
        "fields": {},
        "current_field": first,
        "messages": [{"role": "assistant", "content": FIELDS[first]["question"], "field": first}],
        "turn_count": 0,
    }


def _parse_answer(field: str, raw: str) -> tuple[str, object]:
    value = raw.strip()
    lowered = value.casefold().replace("’", "'")
    if lowered in UNKNOWN:
        return "unknown", None
    if lowered in DECLINED:
        return "declined", None
    spec = FIELDS[field]
    if spec["kind"] == "number":
        match = re.fullmatch(r"\s*(\d+(?:\.\d{1,2})?)\s*(?:hours?|hrs?|h)?\s*", value, re.I)
        if not match:
            raise ValueError("Enter one number, 'I don't know', or 'Prefer not to say'.")
        number = float(match.group(1))
        minimum, maximum = spec["range"]
        if not math.isfinite(number) or not minimum <= number <= maximum:
            raise ValueError(f"Enter a number from {minimum} to {maximum}.")
        return "answered", round(number, 2 if field == "gpa" else 1)
    if spec["kind"] == "choice":
        if lowered not in spec["choices"]:
            raise ValueError("Please answer: rested, sometimes tired, or often tired.")
        return "answered", spec["choices"][lowered]
    if not 2 <= len(value) <= 80:
        raise ValueError("Please give a short description of 2–80 characters.")
    return "answered", value


def advance_collection(state: dict, student_message: str) -> dict:
    """Consume one reply and ask the next needed question; no data is persisted."""
    if state.get("status") != "collecting" or not state.get("current_field"):
        raise ValueError("This conversation is ready for review.")
    if not isinstance(student_message, str) or not student_message.strip() or len(student_message) > 500:
        raise ValueError("Please enter a short answer (up to 500 characters).")
    updated = copy.deepcopy(state)
    field = updated["current_field"]
    updated["turn_count"] += 1
    turn = updated["turn_count"]
    updated["messages"].append({"role": "user", "content": student_message.strip(), "field": field, "turn": turn})
    try:
        status, value = _parse_answer(field, student_message)
    except ValueError as error:
        updated["messages"].append({
            "role": "assistant", "content": f"I couldn't record that yet. {error} {FIELDS[field]['question']}",
            "field": field,
        })
        return updated

    updated["fields"][field] = {
        "status": status, "value": value, "unit": FIELDS[field]["unit"],
        "source_turn": turn,
    }
    if field == "activity_hours" and status == "answered" and value == 0:
        updated["fields"]["activity_type"] = {
            "status": "not_applicable", "value": None, "unit": None, "source_turn": turn,
        }
    following = next_field(updated["fields"])
    updated["current_field"] = following
    if following:
        updated["messages"].append({"role": "assistant", "content": FIELDS[following]["question"], "field": following})
    else:
        updated["status"] = "review"
        updated["messages"].append({
            "role": "assistant",
            "content": "We have reached the end of the information check. Please review the record below before confirming.",
            "field": None,
        })
    return updated


def revise_answer(state: dict, field: str, answer: str) -> dict:
    """Correct a previously answered field, then reopen any dependent questions."""
    if field not in state.get("fields", {}) or field not in FIELDS:
        raise ValueError("Choose an existing answer to correct.")
    status, value = _parse_answer(field, answer)
    updated = copy.deepcopy(state)
    updated["turn_count"] += 1
    turn = updated["turn_count"]
    updated["messages"].append({"role": "user", "content": f"Correction to {FIELDS[field]['label']}: {answer.strip()}", "field": field, "turn": turn})
    updated["fields"][field] = {"status": status, "value": value, "unit": FIELDS[field]["unit"], "source_turn": turn}
    if field == "sleep_hours":
        updated["fields"].pop("sleep_quality", None)
    if field == "activity_hours":
        updated["fields"].pop("activity_type", None)
        if status == "answered" and value == 0:
            updated["fields"]["activity_type"] = {
                "status": "not_applicable", "value": None, "unit": None, "source_turn": turn,
            }
    following = next_field(updated["fields"])
    updated["current_field"] = following
    updated["status"] = "collecting" if following else "review"
    updated["messages"].append({
        "role": "assistant",
        "content": FIELDS[following]["question"] if following else "Correction saved. Please review the record again.",
        "field": following,
    })
    return updated


def structured_record(state: dict) -> dict:
    if state.get("status") != "review" or not coverage(state["fields"])["complete"]:
        raise ValueError("Finish the information check before confirming.")
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": state["mode"],
        "fields": copy.deepcopy(state["fields"]),
        "coverage": coverage(state["fields"]),
    }


def baseline_for_demo_result(record: dict) -> dict | None:
    fields = record["fields"]
    if any(fields[key]["status"] != "answered" for key in BASE_REQUIRED):
        return None
    return {key: fields[key]["value"] for key in BASE_REQUIRED}
