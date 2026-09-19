"""PitchSide data layer: synthetic demo records or Databricks Unity Catalog."""

import os
import random

import pandas as pd


TABLE_NAME = "main.pitchside.student_checkins"
REQUIRED_DATABRICKS_VARIABLES = (
    "DATABRICKS_SERVER_HOSTNAME",
    "DATABRICKS_HTTP_PATH",
    "DATABRICKS_TOKEN",
)


def databricks_is_configured():
    """Return True only when all three Databricks connection values exist."""
    return all(os.getenv(name) for name in REQUIRED_DATABRICKS_VARIABLES)


def create_synthetic_students(rows=50):
    """Create privacy-safe, fictional student check-ins for the demo."""
    struggles = [
        "Time management",
        "Motivation",
        "Course difficulty",
        "Asking for help",
        "Staying focused",
    ]
    start_styles = ["Early", "A few days before", "Near the deadline"]
    records = []
    for number in range(rows):
        records.append(
            {
                "student_id": f"VT-DEMO-{number + 1:03}",
                "study_hours": random.randint(2, 25),
                "extracurricular_count": random.randint(0, 5),
                "credit_hours": random.randint(12, 21),
                "primary_struggle": random.choice(struggles),
                "assignment_start_style": random.choice(start_styles),
            }
        )
    return pd.DataFrame(records)


def load_students():
    """Read check-ins from Databricks, or return local synthetic data when offline."""
    if not databricks_is_configured():
        return create_synthetic_students()

    from databricks import sql

    with sql.connect(
        server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY student_id LIMIT 50")
            columns = [column[0] for column in cursor.description]
            return pd.DataFrame(cursor.fetchall(), columns=columns)


def source_name():
    """Return a readable data-source label for the Streamlit interface."""
    return "Databricks Unity Catalog" if databricks_is_configured() else "synthetic local demo data"
