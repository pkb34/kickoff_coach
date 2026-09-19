# Student information collection standard (MVP, v1.0)

This is the agreed working standard for the **information-collection agent**. The GPA scale is **0–4.0**, as confirmed by the project owner. Other details below are implementation defaults that can be revised as the study design develops. The interface is English.

## Required coverage

| Topic | Field ID | Meaning and unit | Valid answer | Coverage rule |
|---|---|---|---|---|
| Sleep | `sleep_hours` | Typical average hours slept per night | 0–24 hours, one decimal | Always ask |
| Class and GPA | `class_hours` | Scheduled class hours in a typical week | 0–60 hours | Always ask |
| Class and GPA | `gpa` | Current GPA on a 0–4.0 scale | 0.00–4.00 | Always ask; a student without a GPA can say unknown |
| Extracurricular | `activity_hours` | Clubs and other extracurricular hours in a typical week | 0–60 hours | Always ask; 0 means none |
| Extracurricular | `activity_type` | Main club/activity, short description | 2–80 characters | Ask only if `activity_hours > 0` |
| Study time | `weekday_study_hours` | Daily average study time outside class on a typical weekday | 0–24 hours/day | Always ask |
| Study time | `weekend_study_hours` | Daily average study time outside class on a typical weekend day | 0–24 hours/day | Always ask |
| Sleep clarification | `sleep_quality` | How rested the student usually feels on waking | `rested`, `sometimes_tired`, `often_tired` | Ask only if `sleep_hours < 7` |

The four main topics are sleep, class/GPA, extracurriculars, and study time. Activity type and sleep quality are conditional clarifications. The thresholds are **conversation triggers**, not health or academic diagnoses.

## Conversation rules

1. Start with a question about one or several required fields. The current demo asks one at a time; a future agent may combine questions if it can reliably extract separate answers.
2. After each student reply, update the structured fields, decide what remains missing, and ask the next relevant question. If an answer is unclear, ask for clarification without silently guessing a number.
3. A student may say `I don't know` or `Prefer not to say`. These become `unknown` or `declined`, with a null value. The topic counts as *addressed* but remains unavailable for analysis.
4. Finish when every currently required field has status `answered`, `unknown`, or `declined`. A conditional field becomes required only when its triggering answer is known. If activity time is 0, `activity_type` is `not_applicable`.
5. Show the extracted record to the student before saving. Corrections must update the record and reopen any newly needed conditional question.
6. Do not infer or fill missing GPA, sleep, or wellbeing data. Downstream analysis must see the missingness explicitly.

## Field record and traceability

Each field has `status`, `value`, `unit`, and `source_turn`. The transcript stores the original question/answer sequence. The final record has `schema_version`, `created_at`, `mode`, `fields`, and `coverage` (`required`, `answered`, `unavailable`, `missing`, `complete`). The `source_turn` links a field to the student's reply, so the backend can explain where a value came from. The demo does not attach confidence scores because it does not estimate them.

## Data and result boundaries

The current prototype asks for no name, student ID, email, diagnosis, or other identifying details. Avoid including these in free-text replies. Confirmed records and transcripts are stored in local SQLite for the demo; a production deployment needs retention, access, consent, and deletion decisions. The demo football personality requires all six numeric baseline fields; if any are unavailable, it does not invent a personality. GPA, sleep, and wellbeing predictions are not implemented.

## Still to decide with the project team

- Whether sleep should eventually be split into weekday and weekend averages, and whether class/learning time needs a more precise definition for different course formats.
- Whether the final agent should accept any natural-language answer or support structured controls as a fallback.
- Which extra clarifications are useful without increasing question burden, and how many rounds of questioning are acceptable.
- Whether the study needs more context for wellbeing, and how to avoid presenting an academic prototype as health advice.
