"""SQLite persistence for questionnaire submissions."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from engine import process_with_agent


DB_PATH = Path(os.environ.get("STUDENT_DB_PATH", Path(__file__).resolve().parent / "data" / "submissions.sqlite3"))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        study_hours REAL NOT NULL,
        activity_type TEXT NOT NULL,
        activity_hours REAL NOT NULL,
        class_hours REAL NOT NULL,
        sleep_hours REAL NOT NULL,
        result_json TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS quiz_submissions (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        baseline_json TEXT NOT NULL,
        selected_questions_json TEXT NOT NULL,
        followup_answers_json TEXT NOT NULL,
        result_json TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS collection_submissions (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        record_json TEXT NOT NULL,
        transcript_json TEXT NOT NULL,
        result_json TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS databricks_outbox (
        submission_id TEXT PRIMARY KEY,
        synced_at TEXT,
        FOREIGN KEY (submission_id) REFERENCES collection_submissions(id)
    )""")
    return connection


def save_submission(answers: dict, result: dict) -> dict:
    record_id = "STU-" + secrets.token_hex(4).upper()
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(_connect()) as connection:
        with connection:
            connection.execute(
                "INSERT INTO submissions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (record_id, created_at, answers["study_hours"], answers["activity_type"],
                 answers["activity_hours"], answers["class_hours"], answers["sleep_hours"],
                 json.dumps(result, ensure_ascii=False)),
            )
    return {"id": record_id, "created_at": created_at, "answers": answers, "result": result}


def save_quiz_submission(baseline: dict, selected: list[str], followups: dict, result: dict) -> dict:
    """Persist the full three-step quiz without changing earlier records."""
    record_id = "STU-" + secrets.token_hex(4).upper()
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(_connect()) as connection:
        with connection:
            connection.execute(
                "INSERT INTO quiz_submissions VALUES (?, ?, ?, ?, ?, ?)",
                (record_id, created_at, json.dumps(baseline), json.dumps(selected),
                 json.dumps(followups), json.dumps(result)),
            )
    return {
        "id": record_id, "created_at": created_at, "answers": baseline,
        "selected_questions": selected, "followups": followups, "result": result,
    }


def save_collection_submission(record: dict, transcript: list[dict], result: dict) -> dict:
    """Save a confirmed conversation and its structured handoff record."""
    record_id = "STU-" + secrets.token_hex(4).upper()
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(_connect()) as connection:
        with connection:
            connection.execute(
                "INSERT INTO collection_submissions VALUES (?, ?, ?, ?, ?)",
                (record_id, created_at, json.dumps(record, ensure_ascii=False),
                 json.dumps(transcript, ensure_ascii=False), json.dumps(result, ensure_ascii=False)),
            )
            connection.execute(
                "INSERT INTO databricks_outbox (submission_id) VALUES (?)", (record_id,)
            )
    return {
        "id": record_id, "created_at": created_at, "record": record,
        "transcript": transcript, "result": result,
    }


def update_collection_result(record_id: str, result: dict) -> None:
    """Persist a later optional Gemini briefing for one existing record."""
    with closing(_connect()) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE collection_submissions SET result_json = ? WHERE id = ?",
                (json.dumps(result, ensure_ascii=False), record_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("The saved collection record was not found.")
            connection.execute(
                "UPDATE databricks_outbox SET synced_at = NULL WHERE submission_id = ?", (record_id,)
            )


def pending_databricks_submissions(limit: int = 25) -> list[tuple[str, str, str, str]]:
    """Return unsynced structured records, without local conversation transcripts."""
    with closing(_connect()) as connection:
        return connection.execute("""
            SELECT c.id, c.created_at, c.record_json, c.result_json
            FROM databricks_outbox AS o
            JOIN collection_submissions AS c ON c.id = o.submission_id
            WHERE o.synced_at IS NULL
            ORDER BY c.created_at, c.id LIMIT ?
        """, (limit,)).fetchall()


def pending_databricks_count() -> int:
    with closing(_connect()) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM databricks_outbox WHERE synced_at IS NULL"
        ).fetchone()[0]


def enqueue_existing_databricks_submissions() -> int:
    """Explicit staff action to queue records saved before cloud sync existed."""
    with closing(_connect()) as connection:
        with connection:
            cursor = connection.execute("""
                INSERT OR IGNORE INTO databricks_outbox (submission_id)
                SELECT id FROM collection_submissions
            """)
            return cursor.rowcount


def mark_databricks_synced(record_id: str) -> None:
    with closing(_connect()) as connection:
        with connection:
            connection.execute(
                "UPDATE databricks_outbox SET synced_at = ? WHERE submission_id = ?",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), record_id),
            )


def migrate_legacy_results() -> int:
    """Replace Chinese demo feedback stored by earlier versions with English feedback."""
    updates = []
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT id, study_hours, activity_type, activity_hours, class_hours, sleep_hours, result_json FROM submissions"
        ).fetchall()
        for row in rows:
            old_result = json.loads(row[6])
            if old_result.get("status") != "demo_rule_result":
                continue
            if not any(0x4E00 <= ord(character) <= 0x9FFF for character in row[6]):
                continue
            answers = {
                "study_hours": row[1], "activity_type": row[2],
                "activity_hours": row[3], "class_hours": row[4],
                "sleep_hours": row[5],
            }
            updates.append((json.dumps(process_with_agent(answers), ensure_ascii=False), row[0]))
        if updates:
            with connection:
                connection.executemany("UPDATE submissions SET result_json = ? WHERE id = ?", updates)
    return len(updates)
