# Local question-agent handoff (active schema v2.0)

The active Python Streamlit quiz is `views/quiz.py`. It calls `local_question_agent.py` directly. That module is an offline, deterministic prototype. It starts with three question groups, selects eight required deeper questions plus up to two conditional ones, and returns a structured record. Question selection makes no cloud-model request. The separate optional Gemini briefing is described in `ANALYSIS_AGENT_HANDOFF.md`.

## Active Python interface

```python
baseline = validate_baseline(raw_fields)
state = start_agent(baseline)
state = answer_question(state, student_reply)  # repeat until status == "review"
record = structured_record(state)
```

`raw_fields` has exactly `activity_type`, `activity_hours`, `class_hours`, `weekday_study_hours`, `weekend_study_hours`, and `sleep_hours`. The first three questions are displayed in the UI, with separate inputs for their subfields. The structured record uses `schema_version: "2.0"`, `baseline`, `followups`, `coverage`, and `question_count`. `state` also contains the ordered `messages` transcript. The UI passes the record and transcript to `storage.save_collection_submission()`.

The active quiz must not request or record academic marks. A future local model or teammate adapter must keep this scope rule and reject out-of-scope generated questions **before display** and **before saving**. It must also keep the length bounds: three starting groups, eight to ten deeper questions, eleven to thirteen total in the current design. If the team later changes the count, update the standard, UI, and tests together.

## Adapter expectations for a later local model

1. Keep a Python entry point that accepts validated baseline fields and prior turns, then returns one student-facing English question plus an updated state.
2. Run locally on the machine or another explicitly approved local environment. Do not send student answers to GPT or a cloud endpoint.
3. Validate every returned question for scope, length, duplicate intent, and relevance before showing it. If validation fails, use a safe question from the local bank.
4. Preserve unknown/declined statuses and the original student reply. Do not infer a precise number from vague language.
5. Keep the eight coverage areas, including the direct happiness rating, and stop after at most ten deeper questions. Save only after student review.
6. Add tests for varied replies, skipped answers, ambiguous replies, model failure, and recovery. Do not let a backend error erase an existing session.

The old `collection_gateway.py` and `collector.py` implement a prior schema. They remain in the repository for historical tests and data compatibility, but the current quiz does not use them. Do not point the active quiz at them. The separate analysis agent is still future work; see `ANALYSIS_AGENT_BACKLOG.md`.
