# Student information collection standard (MVP, v2.0)

This is the active standard for the local information-collection agent. The interface is in English. The project owner will provide final wording for the starting questions later.

## Three starting question groups

| Group | Structured fields | Unit and range |
|---|---|---|
| Extracurricular activities | `activity_type`, `activity_hours` | Main activity text; 0–60 hours/week |
| Learning time | `class_hours`, `weekday_study_hours`, `weekend_study_hours` | 0–60 class hours/week; 0–24 study hours/day outside class for each day type |
| Sleep | `sleep_hours` | 0–24 hours/night |

The page presents **three** questions, with separate inputs where one question asks for multiple values. Every field may be answered, marked `unknown`, or marked `declined`. If activity hours are zero, activity type becomes `not_applicable`. The active schema has no academic-mark field; question text, prompts, and structured outputs must not request it.

## Deeper follow-ups

The local agent asks eight core questions covering activity balance, classroom experience, study routine, learning barriers, sleep quality, a direct 0–10 seven-day happiness rating, campus belonging, and support preferences. It can add up to two targeted questions about activity tradeoffs, study variation, sleep barriers, or a desired connection step. Selection depends on the reported hours and follow-up replies. This yields **8–10 deeper questions, 11–13 total**.

The current engine uses a fixed question bank and deterministic triggers. Student replies are stored as text; the engine does not claim to understand arbitrary language. A student can skip a follow-up. Missing information is recorded explicitly and is never filled with a guessed value. Generated question text and user replies pass a scope guard for academic-mark requests or disclosure.

## Record and review

`local_question_agent.structured_record()` returns schema `2.0` with `baseline`, `followups`, `coverage`, and `question_count`. Each baseline field has `status`, `value`, and `unit`; each follow-up has its question, answer/status, and topic. The UI shows the record before confirmation. Changing the starting answers restarts the deeper sequence; editing individual follow-up replies is future work. Confirmation saves the record and transcript in local SQLite.

The result is an illustrative football label based on available time fields, not a validated student assessment. When a required numeric value is unknown or declined, it leaves the personality unassigned. The happiness index displays only the student's direct rating multiplied by ten; a declined or unknown rating stays unavailable. No sleep or wellbeing prediction is calculated. The optional Gemini future-moments paragraph is a possible scenario, not a prediction.

## Later study-design decisions

- Final wording of the three starting questions and whether to split weekday/weekend sleep.
- Whether to add a local language model and how to validate its questions against the scope and length limits.
- Whether students should be able to revise one follow-up without restarting the conversation.
- Consent, retention, access, and deletion policy before collecting real student data.
