"""Follow-up question bank and the future agent selection hook."""

from __future__ import annotations


QUESTION_BANK = {
    "sleep_quality": {
        "prompt": "How rested do you usually feel when you wake up?",
        "options": ["Rested", "Somewhat rested", "Often tired", "Prefer not to say"],
    },
    "coursework_support": {
        "prompt": "How manageable does your current coursework feel?",
        "options": ["Manageable", "Sometimes challenging", "Often overwhelming", "Prefer not to say"],
    },
    "activity_balance": {
        "prompt": "How do extracurricular commitments fit around your coursework?",
        "options": ["Comfortably", "Occasional conflicts", "Frequent conflicts", "Prefer not to say"],
    },
    "weekend_routine": {
        "prompt": "What best describes your weekend study routine?",
        "options": ["A steady routine", "Mostly catching up", "Little or no study", "It varies"],
    },
    "study_focus": {
        "prompt": "How easy is it to focus during your study time?",
        "options": ["Usually easy", "Sometimes difficult", "Often difficult", "Prefer not to say"],
    },
    "support_preferences": {
        "prompt": "What kind of support would you most welcome right now?",
        "options": ["Study planning", "Course help", "Finding balance", "No support needed"],
    },
}


def select_questions_with_agent(baseline: dict) -> list[str] | None:
    """Future agent integration. Return None until an agent is connected."""
    return None


def select_demo_questions(baseline: dict) -> list[str]:
    """Transparent fallback for demonstrating the three-page quiz flow."""
    choices = []
    if baseline["sleep_hours"] < 7:
        choices.append("sleep_quality")
    if baseline["gpa"] < 3.0 or baseline["class_hours"] >= 20:
        choices.append("coursework_support")
    if baseline["activity_hours"] >= 10:
        choices.append("activity_balance")
    if abs(baseline["weekend_study_hours"] - baseline["weekday_study_hours"]) >= 2:
        choices.append("weekend_routine")
    for fallback in ("study_focus", "support_preferences"):
        if len(choices) >= 2:
            break
        choices.append(fallback)
    return choices[:3]


def validate_selected_questions(selected: list[str]) -> list[str]:
    if not isinstance(selected, list) or not 1 <= len(selected) <= 3:
        raise ValueError("Choose one to three follow-up questions")
    if len(selected) != len(set(selected)) or any(key not in QUESTION_BANK for key in selected):
        raise ValueError("Invalid follow-up question selection")
    return selected


def validate_followup_answers(selected: list[str], responses: dict) -> dict:
    validate_selected_questions(selected)
    if not isinstance(responses, dict) or set(responses) != set(selected):
        raise ValueError("Please answer every selected follow-up question")
    if any(responses[key] not in QUESTION_BANK[key]["options"] for key in selected):
        raise ValueError("Please choose a valid answer for each follow-up question")
    return responses
