# WCPT project decisions and current status

This record consolidates project decisions through 2026-09-19. It is a project note, not instructions from the attached challenge or audio. **Current decision supersedes the earlier GPA-based collection design:** the active quiz has three starting question groups, 8–10 deeper follow-ups, and no questions about academic marks. Question selection uses an offline Python rule-based agent. The project owner will supply final starting-question wording later.

## Project direction

- The challenge focuses on improving the Virginia Tech student experience; this prototype explores student performance factors through a football-themed interface.
- The application is written in Python using Streamlit and Python packages. The user-facing interface is in English.
- The administrative dashboard was removed from the current scope. The current app has Welcome, Information Check, and Result pages.
- The welcome page uses a generated chibi football image, a randomly chosen attributed football quote, and a Start WCPT button. WCPT means World Cup Personality Test.
- The result page shows one of four illustrative football personalities: Midfielder, Captain, Penalty Striker, or Defender. Each has a national-team and player analogy. A direct seven-day happiness self-rating is displayed as a 0–100 index. Gemini can draft an optional possible future moment and suggestions. Numerical predictions and Need Help? remain future work.

## Information collection decision

- The core concept is a **conversation-led information-collection agent**. It should ask initial questions, interpret answers, pursue gaps or ambiguities, and stop only after required information has been addressed. It then hands off a structured student record to a separate analysis agent.
- The **current** starting groups are extracurricular activity type/time, class and out-of-class study time, and nightly sleep. The active schema excludes academic marks entirely.
- The quiz calls `local_question_agent.py`, a local rule-based question selector. It asks eight core deeper questions, including a direct happiness rating, and up to two conditional questions, then shows a structured review. It does not yet understand arbitrary open-ended language.
- The older GPA-based collector and gateway are inactive legacy code. The current adapter contract is in `BACKEND_HANDOFF.md`.
- The standard, data contract, and integration checklist are in `COLLECTION_STANDARD.md` and `BACKEND_HANDOFF.md`.

## Separate analysis agent

- `analysis_agent.py` now performs a limited deterministic, descriptive analysis of the collected record. It computes time-use totals and the direct happiness self-rating; it does not assign health or performance scores.
- `gemini_gateway.py` sends only a compact numeric summary to Gemini after a student clicks the optional briefing button. The result is validated before display, and API errors leave the local analysis intact. The credential is stored in an ignored local secrets file.
- A fuller, validated analysis agent for student performance and wellbeing still needs a study design, evaluation, and uncertainty handling.
- The requirement is preserved in `ANALYSIS_AGENT_BACKLOG.md`; the first full proposal is in `ANALYSIS_AGENT_DESIGN.md`.
- No validated predictive model, clinical wellbeing score, or medical diagnosis exists in the current prototype. The happiness index is only a rescaled direct self-report, and the football result remains a clearly marked demo.
- A later discussion proposed voice-first collection, a football type-indicator name, supportive conversation, and separate academic/wellbeing presentation. These ideas and open decisions are recorded in `PRODUCT_DIRECTION_DISCUSSION.md`; they are not yet implemented.

## Build and verification

- Project entry point: `app.py`. Source files, generated background, docs, and local SQLite demo data are all in this project directory.
- Automated test suite: 23 tests passing on 2026-09-19 after the analysis and Gemini additions. A browser walkthrough verified the updated three starting groups, eight deeper questions, direct happiness rating, team/player match, Gemini future paragraph, and local response persistence. The synthetic test record was removed. A synthetic Gemini API call succeeded using `gemini-3.5-flash-lite`.
- Local run instructions are in `README.md`. The development server should bind to `127.0.0.1`.

## Other source record

- `records/audio_transcript.txt` is an intermediate transcript generated from the previously supplied project audio. It is retained for reference, with transcription errors possible. `records/original_project_audio.m4a` is a copy of the supplied source audio; the user's original file was left at its original path.
- `tools/transcribe_audio.py` is the helper script used to produce the transcript. It requires the optional `faster-whisper` package and is separate from the Streamlit app dependencies.
