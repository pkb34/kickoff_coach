# Data-processing agent and Gemini handoff (current prototype)

The information-collection agent remains local in `local_question_agent.py`. After the student confirms the completed schema `2.0` record, `analysis_agent.analyze_record(record)` runs locally. It returns a descriptive `1.0` analysis with `metrics`, `observations` and their field evidence, `data_gaps`, `topic_status`, `performance_context`, `wellbeing_context`, and `limitations`.

## Current calculations

- `weekly_independent_study_hours = 5 × weekday_study_hours + 2 × weekend_study_hours`, only if both daily averages are available.
- `weekly_reported_commitment_hours = class_hours + activity_hours + weekly_independent_study_hours`, only if all components are available.
- `self_reported_happiness_index = 10 × the student's 0–10 answer about how happy they feel lately`. This is a display conversion of a direct answer, **not** a validated wellbeing score. If the student skips the rating, display `Not reported`.
- Sleep and classroom/activity time are reported as given. No weighted health or performance score and no future numerical prediction are produced.
- Time-band answers retain their selected interval. Derived weekly study and commitment intervals use the lower and upper bounds of each component. Midpoint values exist for compatibility and staff aggregates; student-facing copy must display ranges, never those midpoints as exact reported hours.

The existing four-role demo rule remains in `engine.assign_local_demo_personality()`. `football_matches.match_football_identity(role)` attaches one national-team style to each role. The mappings are illustrative and cite FIFA/UEFA sources for the football descriptions. They are not a scientific personality assessment.

## Optional Gemini path

Only `gemini_gateway.py` makes a network request. The result page calls it **after the student clicks** `Make my gentle game plan`:

The teammate's `gaffer.py` entry point remains as a compatibility wrapper. It accepts the confirmed v2 record and routes Gemini requests through this same restricted gateway; older records get local fallback text.

```python
analysis = analyze_record(record)
briefing = generate_briefing(analysis)
```

`analysis_agent.gemini_summary(analysis)` is the whitelist for outbound data. It contains four time intervals and their approximate numeric midpoints, the direct happiness index, missing-field names, and booleans saying whether context answers exist. The prompt requires Gemini to use the intervals rather than treat midpoint estimates as exact reported hours. It excludes activity descriptions, names, raw follow-up text, the full record, and the transcript. The request asks Gemini for JSON with `summary`, `suggestions`, and `future_moments`. The future paragraph must be conditional and must not claim to predict a student's future. The gateway validates shape, length, and the no-academic-marks rule before displaying or saving the response. On API failure, local results remain usable.

The key and model are read from `GEMINI_API_KEY` / `GEMINI_MODEL` environment variables or an ignored local `.streamlit/secrets.toml`. Never commit that file or put credentials in the browser. The current tested model is `gemini-3.5-flash-lite`. The source file `.streamlit/secrets.toml.example` documents the format without a credential.

## Extension points

1. Replace deterministic observations with a validated analysis method while keeping missing values and field evidence explicit.
2. If a future design uses free-text answers for Gemini, update the outbound-data contract and the student-facing disclosure before sending them.
3. Update `football_matches.py` to add more teams. Keep football-source links separate from the student-match explanation.
4. Version the analysis output when changing metrics or the happiness rating. Update the result page, Gemini projection, tests, and documentation together.
5. Define consent, access, retention, and deletion before using real student records outside the local demonstration.
