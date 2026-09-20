# Local question-agent handoff (active schema v2.0)

The active Python Streamlit quiz is `views/quiz.py`. It calls `local_question_agent.py` directly. That module is an offline, deterministic prototype. It starts with three question groups, selects seven required deeper questions plus at most one conditional question, and returns a structured record. Question selection makes no cloud-model request. Optional one-turn speech recognition is in `voice_gateway.py`; it sends audio only after the student chooses to record and send. The separate optional Gemini briefing is described in `ANALYSIS_AGENT_HANDOFF.md`.

## Active Python interface

```python
baseline = validate_baseline(raw_fields)
state = start_agent(baseline)
state = answer_question(state, student_reply)  # repeat until status == "complete"
record = structured_record(state)
```

`raw_fields` has exactly `activity_type`, `activity_hours`, `class_hours`, `weekday_study_hours`, `weekend_study_hours`, and `sleep_hours`. The first three questions are displayed in the UI, with separate inputs for their subfields. The structured record uses `schema_version: "2.0"`, `baseline`, `followups`, `coverage`, and `question_count`. `state` also contains the ordered `messages` transcript. The UI passes the record and transcript to `storage.save_collection_submission()`. This enqueues the structured record and result for `databricks_writer.sync_pending()`; the transcript remains local. Sync uses the same ID on retry and never sends audio.

The active quiz must not request or record academic marks. A future local model or teammate adapter must keep this scope rule and reject out-of-scope generated questions **before display** and **before saving**. It must also keep the length bounds: three starting groups, seven to eight deeper questions, ten to eleven total in the current design. If the team later changes the count, update the standard, UI, and tests together.

## Adapter expectations for a later local model

1. Keep a Python entry point that accepts validated baseline fields and prior turns, then returns one student-facing English question plus an updated state.
2. Run question generation locally on the machine or another explicitly approved local environment. Do not send student answers to GPT for question generation. The separate Databricks storage path for structured answers is described above.
3. Validate every returned question for scope, length, duplicate intent, and relevance before showing it. If validation fails, use a safe question from the local bank.
4. Preserve unknown/declined statuses and the original student reply. Do not infer a precise number from vague language.
5. Keep the seven core coverage areas, including self-reported academic progress and the direct feeling rating, and stop after at most eight deeper questions. Save after all required topics are covered; the UI then opens the result without a separate review screen.
6. Add tests for varied replies, skipped answers, ambiguous replies, model failure, and recovery. Do not let a backend error erase an existing session.

The old `collection_gateway.py` and `collector.py` implement a prior schema. They remain in the repository for historical tests and data compatibility, but the current quiz does not use them. Do not point the active quiz at them. The separate analysis agent is still future work; see `ANALYSIS_AGENT_BACKLOG.md`.
