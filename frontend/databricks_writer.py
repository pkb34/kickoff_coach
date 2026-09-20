"""Server-side, retryable upload of completed check-ins to Databricks Delta.

The local SQLite outbox is the durable source of pending writes. The cloud copy
contains the structured record and analysis, never the conversation transcript
or recorded voice. Submission IDs make retries idempotent with Delta MERGE.
"""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

from storage import mark_databricks_synced, pending_databricks_count, pending_databricks_submissions


SECRETS_PATH = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
DEFAULT_TABLE = "main.pitchside.wpti_submissions"
TABLE_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\Z")
CONNECTION_KEYS = ("DATABRICKS_SERVER_HOSTNAME", "DATABRICKS_HTTP_PATH", "DATABRICKS_TOKEN")


def _settings() -> dict[str, str]:
    local = {}
    if SECRETS_PATH.is_file():
        with SECRETS_PATH.open("rb") as source:
            local = tomllib.load(source)
    settings = {key: os.getenv(key) or local.get(key, "") for key in CONNECTION_KEYS}
    settings["DATABRICKS_AUTH_TYPE"] = os.getenv("DATABRICKS_AUTH_TYPE") or local.get("DATABRICKS_AUTH_TYPE", "pat")
    settings["DATABRICKS_SUBMISSIONS_TABLE"] = (
        os.getenv("DATABRICKS_SUBMISSIONS_TABLE") or local.get("DATABRICKS_SUBMISSIONS_TABLE") or DEFAULT_TABLE
    )
    if not TABLE_PATTERN.fullmatch(settings["DATABRICKS_SUBMISSIONS_TABLE"]):
        raise ValueError("DATABRICKS_SUBMISSIONS_TABLE must be a catalog.schema.table name.")
    if settings["DATABRICKS_AUTH_TYPE"] not in ("pat", "databricks-oauth"):
        raise ValueError("DATABRICKS_AUTH_TYPE must be pat or databricks-oauth.")
    return settings


def is_write_configured() -> bool:
    settings = _settings()
    return bool(settings["DATABRICKS_SERVER_HOSTNAME"] and settings["DATABRICKS_HTTP_PATH"] and
                (settings["DATABRICKS_AUTH_TYPE"] == "databricks-oauth" or settings["DATABRICKS_TOKEN"]))


def sync_pending(limit: int = 25) -> dict:
    """Upload pending submissions once; leave them queued on any failure."""
    pending = pending_databricks_count()
    if not pending:
        return {"status": "up_to_date", "synced": 0, "pending": 0}
    synced = 0
    try:
        settings = _settings()
        if not is_write_configured():
            return {"status": "not_configured", "synced": 0, "pending": pending}
        from databricks import sql

        table = settings["DATABRICKS_SUBMISSIONS_TABLE"]
        catalog, schema, _ = table.split(".")
        rows = pending_databricks_submissions(limit)
        create_table = f"""CREATE TABLE IF NOT EXISTS {table} (
            submission_id STRING, created_at STRING, record_json STRING,
            result_json STRING, synced_at TIMESTAMP
        ) USING DELTA"""
        merge = f"""MERGE INTO {table} AS target
            USING (SELECT ? AS submission_id, ? AS created_at,
                          ? AS record_json, ? AS result_json) AS incoming
            ON target.submission_id = incoming.submission_id
            WHEN MATCHED THEN UPDATE SET
                result_json = incoming.result_json, synced_at = current_timestamp()
            WHEN NOT MATCHED THEN INSERT
                (submission_id, created_at, record_json, result_json, synced_at)
                VALUES (incoming.submission_id, incoming.created_at,
                        incoming.record_json, incoming.result_json, current_timestamp())"""
        connection_args = {
            "server_hostname": settings["DATABRICKS_SERVER_HOSTNAME"],
            "http_path": settings["DATABRICKS_HTTP_PATH"],
        }
        if settings["DATABRICKS_AUTH_TYPE"] == "databricks-oauth":
            connection_args["auth_type"] = "databricks-oauth"
        else:
            connection_args["access_token"] = settings["DATABRICKS_TOKEN"]
        with sql.connect(**connection_args) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
                cursor.execute(create_table)
                for record_id, created_at, record_json, result_json in rows:
                    cursor.execute(merge, (record_id, created_at, record_json, result_json))
                    mark_databricks_synced(record_id)
                    synced += 1
        return {"status": "synced", "synced": synced, "pending": pending_databricks_count()}
    except Exception as error:
        # Never expose tokens or individual responses in user-facing errors.
        return {"status": "unavailable", "synced": synced, "pending": pending_databricks_count(),
                "error_type": type(error).__name__}
