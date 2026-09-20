# WCPT: World Cup Personality Test

This is a three-page, Python-only Streamlit prototype. Question selection and data processing run locally. The result page has an optional Gemini briefing requested by the student. The football artwork is stored in `static/soccer_background.png`.

## Current flow

1. **Welcome:** football artwork, a randomly selected player quote, and **Start WCPT**.
2. **Quiz:** three starting question groups cover extracurricular activity type and weekly time; weekly class hours and study time outside class on weekdays and weekends; and average nightly sleep. The local question agent then asks eight required deeper questions, including a direct 0–10 seven-day happiness rating, and up to two conditional questions. The full quiz has 11–13 questions.
3. **Result:** a local data-processing agent calculates descriptive time-use measures and displays the direct happiness rating scaled to 0–100. An illustrative rule selects one of four football roles; each role maps to a historical national-team style and player analogy. Students can request a Gemini briefing with a possible future-moments paragraph. Numerical future predictions are not implemented.

The active question agent is `local_question_agent.py`. It uses transparent Python rules to choose questions from a local bank based on the student's answers. It is **not** a locally hosted language model and does not generate arbitrary new prose. Exact wording for the three starting questions can be revised when the project owner supplies it. The quiz and result pages are `views/quiz.py` and `views/result.py`.

The local analysis is `analysis_agent.py`. Its happiness index is **only the student's own 0–10 answer multiplied by ten**; it is not a validated wellbeing scale. `football_matches.py` holds editable team/player analogies and links to football sources. `gemini_gateway.py` makes the only active external API request. It sends numeric time summaries, the self-rating, and answer-availability flags. It does **not** send names, activity descriptions, free-text replies, or the transcript. When Databricks is configured, a click on **Get my game plan** also adds the approved synthetic telemetry fields—study hours, extracurricular count, credit hours, and assignment-start style—to that Gemini request. Gemini text is shown as a possible scenario, not a forecast.

**Current scope rule:** the quiz must never ask about academic marks or grade point average. The active baseline schema does not contain that field. The older `collector.py`, `collection_gateway.py`, and `followups.py` are legacy code retained for old records/tests; they are not imported by the active quiz. Do not reconnect them to the quiz.

## Run locally

From this directory in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502 --browser.gatherUsageStats false
```

Open <http://127.0.0.1:8502/>. To run the tests:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Confirmed records and conversation transcripts are stored locally in `data/submissions.sqlite3`; set `STUDENT_DB_PATH` to choose another database. Students should avoid entering names or other identifying information. The app has no validated performance or wellbeing assessment.

## Optional Gemini connection

This workstation has a private `.streamlit/secrets.toml` with `GEMINI_API_KEY` and `GEMINI_MODEL`. The file is ignored by Git and must not be committed. On another machine, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in a key, or set the `GEMINI_API_KEY` environment variable. The default model is `gemini-2.5-flash-lite`; change `GEMINI_MODEL` only if your API key has access to another Gemini text model. The API is called only after the student clicks **Get my game plan** on the result page. If the request fails, the local analysis and football match remain available.

## Optional Databricks personalization

Put the four `DATABRICKS_...` values from `.streamlit/secrets.toml.example` in your ignored local `.streamlit/secrets.toml`. Set `DATABRICKS_DEMO_STUDENT_ID` to one synthetic `student_id` in `main.pitchside.student_checkins`, such as `VT-DEMO-001`. When both Databricks and Gemini are configured, the app fetches that synthetic record only when the student clicks **Get my game plan**. It sends Gemini only study hours, extracurricular count, credit hours, and assignment-start style—never the student ID, token, raw table text, or quiz transcript.

See `COLLECTION_STANDARD.md` for collection rules, `BACKEND_HANDOFF.md` for question-agent integration, `ANALYSIS_AGENT_HANDOFF.md` for the processing/Gemini contracts, and `flowchart.md` for the flow. `ANALYSIS_AGENT_DESIGN.md` is a historical design draft with superseded requirements.
