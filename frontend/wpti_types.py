"""Illustrative four-axis WPTI preferences and pitch-position mapping."""

from __future__ import annotations


AXES = (
    ("G", "F", "Guarding", "Forward-moving", "When a team needs you, do you first protect what is working or push toward the next chance?"),
    ("C", "S", "Connecting", "Solo", "Do you usually think best by working with others or by finding your own path first?"),
    ("P", "A", "Planning", "Adapting", "When a plan changes, do you prefer a clear new plan or room to improvise?"),
    ("T", "H", "Tactical", "Heart-led", "In a big moment, do you lean on a careful read or on what feels meaningful?"),
)

# These options answer ordinary questions about the student's week. The UI never
# asks the student to choose a WPTI letter or a football position directly.
BEHAVIOR_CHOICES = {
    "activity_balance": (
        ("Keep my rhythm", "G"),
        ("Try something new", "F"),
    ),
    "class_experience": (
        ("Talk it through", "C"),
        ("Think it through solo", "S"),
    ),
    "study_routine": (
        ("Make a little plan", "P"),
        ("Go with the flow", "A"),
    ),
    "learning_barrier": (
        ("Break it into steps", "T"),
        ("Start with what matters", "H"),
    ),
}

# Recognize answers from a check-in started before the shorter button labels.
LEGACY_BEHAVIOR_CHOICES = {
    "activity_balance": {"I protect time for what is already on my plate": "G",
                         "I make room to try a new opportunity": "F"},
    "class_experience": {"Talking it through with classmates helps me learn": "C",
                         "I learn best when I can think it through on my own first": "S"},
    "study_routine": {"A clear plan helps me get started": "P",
                      "I like adjusting my approach as the day unfolds": "A"},
    "learning_barrier": {"I break the problem into steps and look for a practical path": "T",
                         "I talk it through and start with what feels meaningful": "H"},
}

POSITIONS = {
    "GCPT": ("Goalkeeper", "defender"), "GCPH": ("Center Back", "defender"),
    "GCAT": ("Fullback", "defender"), "GCAH": ("Captain", "captain"),
    "GSPT": ("Goalkeeper", "defender"), "GSPH": ("Center Back", "defender"),
    "GSAT": ("Fullback", "defender"), "GSAH": ("Central Midfielder", "midfielder"),
    "FCPT": ("Central Midfielder", "midfielder"), "FCPH": ("Captain", "captain"),
    "FCAT": ("Attacking Midfielder", "midfielder"), "FCAH": ("Winger", "penalty_striker"),
    "FSPT": ("Striker", "penalty_striker"), "FSPH": ("Striker", "penalty_striker"),
    "FSAT": ("Winger", "penalty_striker"), "FSAH": ("Attacking Midfielder", "midfielder"),
}

POSITION_NOTES = {
    "Goalkeeper": "You may be drawn to steadying a moment before moving forward.",
    "Center Back": "You may like giving a group a reliable base to build on.",
    "Fullback": "You may enjoy supporting the team while staying ready to change direction.",
    "Central Midfielder": "You may like connecting the different parts of a busy team.",
    "Attacking Midfielder": "You may enjoy noticing possibilities and making room for new ideas.",
    "Winger": "You may feel energized by fresh routes and a little freedom to explore.",
    "Striker": "You may like taking a clear chance when it matters to you.",
    "Captain": "You may find meaning in bringing people together and helping a plan move.",
}


def profile_from_choices(choices: tuple[str, str, str, str]) -> dict:
    if len(choices) != 4 or any(value not in (axis[0], axis[1]) for value, axis in zip(choices, AXES)):
        raise ValueError("Choose one preference on each of the four cards.")
    code = "".join(choices)
    position, art_role = POSITIONS[code]
    return {"code": code, "position": position, "art_role": art_role,
            "axis_labels": [axis[2] if value == axis[0] else axis[3] for value, axis in zip(choices, AXES)],
            "position_note": POSITION_NOTES[position]}


def infer_profile_from_record(record: dict) -> dict | None:
    """Estimate a type from four contextual quiz answers; never guess a skipped axis."""
    answers = record.get("followups", {})
    letters = []
    for question_id, options in BEHAVIOR_CHOICES.items():
        answer = answers.get(question_id, {})
        if answer.get("status") != "answered":
            return None
        selected = next((letter for text, letter in options if answer.get("answer") == text), None)
        if selected is None:
            selected = LEGACY_BEHAVIOR_CHOICES[question_id].get(answer.get("answer"))
        if selected is None:
            return None
        letters.append(selected)
    profile = profile_from_choices(tuple(letters))
    profile["basis"] = "inferred_from_context_answers"
    return profile
