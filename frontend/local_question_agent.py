"""Offline, rule-based adaptive question agent for the student quiz.

No cloud API, remote model, or network call is used. A local language model can
replace question wording later without changing the UI or the no-GPA guard.
"""

from __future__ import annotations

import copy
import math
import re
from datetime import datetime, timezone


SCHEMA_VERSION = "2.0"
CORE_QUESTION_IDS = (
    "activity_balance", "class_experience", "study_routine", "learning_barrier",
    "academic_progress", "sleep_quality", "wellbeing_rating",
)
EXTRA_QUESTION_IDS = (
    "sleep_barrier", "support_preference",
)
MAX_EXTRA_QUESTIONS = 1
MAX_DEEP_QUESTIONS = 8
UNKNOWN = {"i don't know", "dont know", "don't know", "unknown", "not sure"}
DECLINED = {"prefer not to say", "skip", "decline", "no answer"}
PROHIBITED = re.compile(r"\b(?:gpa|grade[- ]point(?: average)?|grades?)\b|绩点|学分绩|记点", re.I)

STARTING_QUESTIONS = (
    "Your world beyond class ⚽",
    "Your learning days 📚",
    "Your rest 🌙",
)

BASELINE_SPECS = {
    "activity_type": {"label": "Extracurricular activity type", "unit": None, "kind": "text"},
    "activity_hours": {"label": "Extracurricular time", "unit": "hours/week", "kind": "number", "range": (0, 60)},
    "class_hours": {"label": "Class time", "unit": "hours/week", "kind": "number", "range": (0, 60)},
    "weekday_study_hours": {"label": "Weekday study time", "unit": "hours/day", "kind": "number", "range": (0, 24)},
    "weekend_study_hours": {"label": "Weekend study time", "unit": "hours/day", "kind": "number", "range": (0, 24)},
    "sleep_hours": {"label": "Average nightly sleep", "unit": "hours/night", "kind": "number", "range": (0, 24)},
}

# Fewer, honest time ranges for the student UI. Numeric values remain accepted
# for older records and teammate integrations.
HOUR_BUCKETS = {
    "activity_hours": (("0h", 0, 0), ("1–3h", 1, 3), ("4–6h", 4, 6),
                       ("7–10h", 7, 10), ("11–15h", 11, 15), ("16–20h", 16, 20),
                       ("21–30h", 21, 30)),
    "class_hours": (("0–5h", 0, 5), ("6–10h", 6, 10), ("11–13h", 11, 13),
                    ("14–16h", 14, 16), ("17–20h", 17, 20), ("21–25h", 21, 25),
                    ("26–40h", 26, 40)),
    "weekday_study_hours": (("0h", 0, 0), ("1h", 1, 1), ("2h", 2, 2),
                            ("3–4h", 3, 4), ("5–6h", 5, 6), ("7–8h", 7, 8),
                            ("9–12h", 9, 12)),
    "weekend_study_hours": (("0h", 0, 0), ("1h", 1, 1), ("2h", 2, 2),
                            ("3–4h", 3, 4), ("5–6h", 5, 6), ("7–8h", 7, 8),
                            ("9–12h", 9, 12)),
    "sleep_hours": (("1–4h", 1, 4), ("5h", 5, 5), ("6h", 6, 6),
                    ("7h", 7, 7), ("8h", 8, 8), ("9h", 9, 9), ("10–12h", 10, 12)),
}

TOPICS = {
    "activity_balance": "extracurricular balance",
    "activity_tradeoff": "extracurricular balance",
    "class_experience": "class participation",
    "study_routine": "study routine",
    "study_variation": "study routine",
    "learning_barrier": "learning barriers",
    "academic_progress": "self-reported academic progress",
    "sleep_quality": "rest and sleep",
    "sleep_barrier": "rest and sleep",
    "wellbeing_rating": "self-reported happiness",
    "campus_belonging": "campus connection",
    "connection_step": "campus connection",
    "support_preference": "support needs",
}


def _guard(text: str) -> str:
    if PROHIBITED.search(text):
        raise ValueError("This information is outside the quiz scope. Please answer without academic marks.")
    return text


def _parse_field(key: str, raw: str) -> dict:
    spec = BASELINE_SPECS[key]
    if not isinstance(raw, str):
        raise ValueError(f"{spec['label']}: please enter text.")
    value = raw.strip()
    lower = value.casefold().replace("’", "'")
    if lower in UNKNOWN:
        return {"status": "unknown", "value": None, "unit": spec["unit"]}
    if lower in DECLINED:
        return {"status": "declined", "value": None, "unit": spec["unit"]}
    if not value:
        raise ValueError(f"{spec['label']}: enter an answer or 'Prefer not to say'.")
    _guard(value)
    if spec["kind"] == "text":
        if not 2 <= len(value) <= 80:
            raise ValueError("Describe the main activity in 2–80 characters, or enter 'none'.")
        return {"status": "answered", "value": value, "unit": None}
    for label, minimum, maximum in HOUR_BUCKETS.get(key, ()):
        if value == label:
            return {"status": "answered", "value": round((minimum + maximum) / 2, 1),
                    "unit": spec["unit"], "display": label, "range": [minimum, maximum]}
    match = re.fullmatch(r"(\d+(?:\.\d{1,2})?)\s*(?:hours?|hrs?|h)?", value, re.I)
    if not match:
        raise ValueError(f"{spec['label']}: enter one number, 'I don't know', or 'Prefer not to say'.")
    number = float(match.group(1))
    minimum, maximum = spec["range"]
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{spec['label']}: enter {minimum}–{maximum} hours.")
    return {"status": "answered", "value": round(number, 1), "unit": spec["unit"]}


def validate_baseline(raw: dict) -> dict:
    """Normalize exactly three starting question groups and no academic mark."""
    if not isinstance(raw, dict) or set(raw) != set(BASELINE_SPECS):
        raise ValueError("Complete the three starting questions.")
    fields = {key: _parse_field(key, raw[key]) for key in BASELINE_SPECS}
    activity = fields["activity_hours"]
    kind = fields["activity_type"]
    if activity["status"] == "answered" and activity["value"] == 0:
        if kind["status"] == "answered" and kind["value"].casefold() not in ("none", "no activities", "no clubs"):
            raise ValueError("If extracurricular time is 0, enter 'none' as the activity type.")
        fields["activity_type"] = {"status": "not_applicable", "value": None, "unit": None}
    elif activity["status"] == "answered" and activity["value"] > 0:
        if kind["status"] == "answered" and kind["value"].casefold() in ("none", "no activities", "no clubs"):
            raise ValueError("Enter the activity type for a nonzero activity time.")
    return {"schema_version": SCHEMA_VERSION, "fields": fields, "starting_question_count": 3}


def _value(baseline: dict, key: str) -> object | None:
    field = baseline["fields"][key]
    return field["value"] if field["status"] == "answered" else None


def _hours(value: float) -> str:
    return f"{value:g} {'hour' if value == 1 else 'hours'}"


def _question_text(question_id: str, baseline: dict) -> str:
    activity_hours = _value(baseline, "activity_hours")
    activity_type = _value(baseline, "activity_type")
    weekday = _value(baseline, "weekday_study_hours")
    weekend = _value(baseline, "weekend_study_hours")
    sleep = _value(baseline, "sleep_hours")
    sleep_label = baseline["fields"]["sleep_hours"].get("display") or (_hours(sleep) if sleep is not None else "")
    questions = {
    "activity_balance": (
            f"You make room for {activity_type}. When life gets busy, what feels more like you?"
            if activity_hours and activity_type else
            "When studying and other plans compete, what feels more like you?"
        ),
        "activity_tradeoff": "When your plans all try to squeeze into the same afternoon, what feels hardest to balance?",
        "class_experience": "When class gets tricky, what helps an idea click?",
        "study_routine": (
            f"When you sit down to study, what helps you begin?"
            if weekday is not None and weekend is not None else
            "When you sit down to study, what helps you begin?"
        ),
        "study_variation": "Weekdays and weekends can have different rhythms. What shifts for you, and what would help?",
        "learning_barrier": "When coursework feels tough, what is your first move?",
        "academic_progress": "How are your classes feeling lately?",
        "sleep_quality": (
            f"With around {sleep_label} of sleep, how rested do mornings feel?"
            if sleep is not None else
            "When morning arrives, how rested do you usually feel?"
        ),
        "sleep_barrier": "What tends to get between you and the kind of rest you want, if anything?",
        "wellbeing_rating": "How have you been feeling lately, from 0 to 10?",
        "campus_belonging": "Does campus feel like a place where you can find your people lately?",
        "connection_step": "What tiny, low-pressure way of connecting with someone would feel okay to try?",
        "support_preference": "What kind of support would feel good right now?",
    }
    return _guard(questions[question_id])


def _extra_after(state: dict, answered_id: str, answer: str) -> str | None:
    if len([key for key in state["asked_ids"] if key in EXTRA_QUESTION_IDS]) >= MAX_EXTRA_QUESTIONS:
        return None
    if answer.casefold() in DECLINED or answer.casefold() in UNKNOWN:
        return None
    baseline = state["baseline"]
    lower = answer.casefold()
    candidate = None
    if answered_id == "sleep_quality":
        sleep = _value(baseline, "sleep_hours")
        if (sleep is not None and sleep < 7) or "usually tired" in lower:
            candidate = "sleep_barrier"
    elif answered_id == "wellbeing_rating" and lower.isdigit() and int(lower) <= 4:
        candidate = "support_preference"
    return candidate if candidate and candidate not in state["asked_ids"] else None


def _ask(state: dict, question_id: str) -> None:
    question = _question_text(question_id, state["baseline"])
    state["asked_ids"].append(question_id)
    state["current_question_id"] = question_id
    state["messages"].append({"role": "assistant", "content": question, "question_id": question_id})


def start_agent(baseline: dict) -> dict:
    if baseline.get("schema_version") != SCHEMA_VERSION or set(baseline.get("fields", {})) != set(BASELINE_SPECS):
        raise ValueError("The three starting questions are required before follow-ups.")
    state = {
        "schema_version": SCHEMA_VERSION,
        "mode": "offline_rules",
        "status": "asking",
        "baseline": copy.deepcopy(baseline),
        "asked_ids": [],
        "answers": {},
        "messages": [],
        "current_question_id": None,
    }
    _ask(state, CORE_QUESTION_IDS[0])
    return state


def answer_question(state: dict, raw_answer: str) -> dict:
    if state.get("status") != "asking" or not state.get("current_question_id"):
        raise ValueError("The follow-up conversation is already complete.")
    if not isinstance(raw_answer, str):
        raise ValueError("Please enter a short answer.")
    answer = raw_answer.strip()
    question_id = state["current_question_id"]
    if question_id == "wellbeing_rating" and answer.casefold() not in DECLINED | UNKNOWN:
        if not re.fullmatch(r"(?:10(?:\.0)?|[0-9](?:\.\d)?)", answer):
            raise ValueError("Enter a number from 0 to 10, or choose to skip this question.")
    elif not 2 <= len(answer) <= 800:
        raise ValueError("Enter 2–800 characters, or choose to skip this question.")
    _guard(answer)
    updated = copy.deepcopy(state)
    question = updated["messages"][-1]["content"]
    status = "declined" if answer.casefold() in DECLINED else "unknown" if answer.casefold() in UNKNOWN else "answered"
    updated["answers"][question_id] = {
        "question": question, "answer": None if status != "answered" else answer,
        "status": status, "topic": TOPICS[question_id],
    }
    if question_id == "wellbeing_rating":
        updated["answers"][question_id]["value"] = float(answer) if status == "answered" else None
    updated["messages"].append({"role": "user", "content": answer, "question_id": question_id})
    extra = _extra_after(updated, question_id, answer)
    next_core = next((key for key in CORE_QUESTION_IDS if key not in updated["asked_ids"]), None)
    next_id = extra or next_core
    if next_id and len(updated["asked_ids"]) < MAX_DEEP_QUESTIONS:
        _ask(updated, next_id)
    else:
        updated["status"] = "complete"
        updated["current_question_id"] = None
    return updated


def structured_record(state: dict) -> dict:
    if state.get("status") not in ("complete", "review") or not 7 <= len(state.get("answers", {})) <= MAX_DEEP_QUESTIONS:
        raise ValueError("Finish all required follow-up topics before saving.")
    if not set(CORE_QUESTION_IDS).issubset(state["answers"]):
        raise ValueError("A required follow-up topic is missing.")
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "offline_rules",
        "baseline": copy.deepcopy(state["baseline"]),
        "followups": copy.deepcopy(state["answers"]),
        "coverage": {"required_topics": list(CORE_QUESTION_IDS), "complete": True},
        "question_count": {"starting": 3, "deep": len(state["answers"]), "total": 3 + len(state["answers"])},
    }


def baseline_for_demo_personality(record: dict) -> dict | None:
    baseline = record["baseline"]
    numeric = ("activity_hours", "class_hours", "weekday_study_hours", "weekend_study_hours", "sleep_hours")
    if any(baseline["fields"][key]["status"] != "answered" for key in numeric):
        return None
    return {key: baseline["fields"][key]["value"] for key in numeric}
