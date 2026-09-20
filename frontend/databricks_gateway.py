"""Optional, server-side Databricks telemetry for The Gaffer.

The browser never receives a Databricks token. This module retrieves one
configured synthetic demo record and exposes only the four approved fields for
the Gemini briefing.
"""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path


SECRETS_PATH = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
DEFAULT_TABLE = "main.pitchside.student_checkins"
REQUIRED_SETTINGS = (
    "DATABRICKS_SERVER_HOSTNAME",
    "DATABRICKS_HTTP_PATH",
    "DATABRICKS_TOKEN",
    "DATABRICKS_DEMO_STUDENT_ID",
)


def _settings() -> dict[str, str | None]:
    """Read local-only connection settings without displaying credentials."""
    local = {}
    if SECRETS_PATH.is_file():
        with SECRETS_PATH.open("rb") as source:
            local = tomllib.load(source)
    settings = {name: os.getenv(name) or local.get(name) for name in REQUIRED_SETTINGS}
    table = os.getenv("DATABRICKS_TABLE") or local.get("DATABRICKS_TABLE") or DEFAULT_TABLE
    if not isinstance(table, str) or not re.fullmatch(r"[A-Za-z0-9_.]+", table):
        raise ValueError("Invalid Databricks table name.")
    settings["DATABRICKS_TABLE"] = table
    return settings


def is_configured() -> bool:
    """Return True only if the full Databricks demo connection is available."""
    return all(_settings().get(name) for name in REQUIRED_SETTINGS)


def get_demo_telemetry() -> dict:
    """Fetch one approved synthetic record, or return a safe status message.

    The configured demo student ID stays on the server. Neither it nor any raw
    table text field is returned to the page or sent to Gemini.
    """
    settings = _settings()
    if not all(settings.get(name) for name in REQUIRED_SETTINGS):
        return {"status": "not_configured"}
    try:
        from databricks import sql
    except ImportError:
        return {"status": "unavailable", "message": "The Databricks connector is not installed."}

    query = (
        "SELECT study_hours, extracurricular_count, credit_hours, assignment_start_style "
        f"FROM {settings['DATABRICKS_TABLE']} WHERE student_id = ? LIMIT 1"
    )
    try:
        with sql.connect(
            server_hostname=settings["DATABRICKS_SERVER_HOSTNAME"],
            http_path=settings["DATABRICKS_HTTP_PATH"],
            access_token=settings["DATABRICKS_TOKEN"],
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (settings["DATABRICKS_DEMO_STUDENT_ID"],))
                row = cursor.fetchone()
    except Exception:
        return {"status": "unavailable", "message": "Databricks could not load the demo telemetry right now."}

    if row is None:
        return {"status": "unavailable", "message": "No Databricks demo record matched the configured student ID."}
    study_hours, extracurricular_count, credit_hours, assignment_start_style = row
    numeric = (study_hours, extracurricular_count, credit_hours)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in numeric):
        return {"status": "unavailable", "message": "The Databricks demo record is incomplete."}
    if not isinstance(assignment_start_style, str) or len(assignment_start_style) > 80:
        return {"status": "unavailable", "message": "The Databricks demo record has an invalid schedule style."}
    return {
        "status": "available",
        "source": "Databricks Unity Catalog",
        "study_hours": round(float(study_hours), 1),
        "extracurricular_count": int(extracurricular_count),
        "credit_hours": round(float(credit_hours), 1),
        "assignment_start_style": assignment_start_style.strip(),
    }


def gemini_telemetry_summary(telemetry: dict | None) -> dict | None:
    """Return only the user-approved Databricks fields for Gemini."""
    if not telemetry or telemetry.get("status") != "available":
        return None
    return {
        "weekly_study_hours": telemetry["study_hours"],
        "extracurricular_count": telemetry["extracurricular_count"],
        "credit_hours": telemetry["credit_hours"],
        "assignment_start_style": telemetry["assignment_start_style"],
    }
