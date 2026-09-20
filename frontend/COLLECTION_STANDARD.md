# Student information collection standard (MVP, v2.0)

This is the active standard for the local information-collection agent. The interface is in English. The project owner will provide final wording for the starting questions later.

## Three starting question groups

| Group | Structured fields | Unit and range |
|---|---|---|
| Extracurricular activities | `activity_type`, `activity_hours` | Main activity text; 0–60 hours/week |
| Learning time | `class_hours`, `weekday_study_hours`, `weekend_study_hours` | 0–60 class hours/week; 0–24 study hours/day outside class for each day type |
| Sleep | `sleep_hours` | 0–24 hours/night |

The page presents **three** questions, with separate inputs where one question asks for multiple values. Every field may be answered, marked `unknown`, or marked `declined`. If activity hours are zero, activity type becomes `not_applicable`. The active schema has no academic-mark field; question text, prompts, and structured outputs must not request it.

The student UI uses seven time bands for each numeric field, with smaller bands near common answers and wider bands at the extremes. The structured field stores the selected `display` label and `[minimum, maximum]` `range`; `value` is the midpoint estimate for older integrations and must not be shown as an exact student answer. Older exact numeric submissions remain valid and are represented as point intervals in the analysis. The validation ranges in the table above are backend compatibility limits, not the current UI choices.

## Deeper follow-ups

The local agent asks seven core questions covering activity balance, classroom experience, study routine, learning barriers, self-reported academic progress without marks, sleep quality, and a direct 0–10 rating of how the student feels lately. It can add one targeted open question about sleep barriers or desired support. Selection depends on reported hours and follow-up replies. This yields **7–8 deeper questions, 10–11 total**.

The current engine uses a fixed question bank and deterministic triggers. Student replies are stored as text; the engine does not claim to understand arbitrary language. A student can skip a follow-up. Missing information is recorded explicitly and is never filled with a guessed value. Generated question text and user replies pass a scope guard for academic-mark requests or disclosure.

## Record and handoff

`local_question_agent.structured_record()` returns schema `2.0` with `baseline`, `followups`, `coverage`, and `question_count`. Each baseline field has `status`, `value`, and `unit`; each follow-up has its question, answer/status, and topic. After the final answer, the UI saves the record and transcript in local SQLite and opens the result directly. Students can restart the test; editing individual replies is future work.

The result is an illustrative football label inferred from four contextual answers, not a validated student assessment. When an axis answer is missing, the type remains unassigned rather than guessed. The happiness index displays only the student's direct rating multiplied by ten; a declined or unknown rating stays unavailable. No sleep or wellbeing prediction is calculated. The optional Gemini future-moments paragraph is a possible scenario, not a prediction.

## Later study-design decisions

- Final wording of the three starting questions and whether to split weekday/weekend sleep.
- Whether to add a local language model and how to validate its questions against the scope and length limits.
- Whether students should be able to revise one follow-up without restarting the conversation.
- Consent, retention, access, and deletion policy before collecting real student data.
