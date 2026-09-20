"""Create the PitchSide Delta table and load synthetic sample data once."""

import os

from databricks import sql

from Data import TABLE_NAME, create_synthetic_students


def main():
    """Create the schema/table, clear old demo data, then insert fresh records."""
    students = create_synthetic_students()
    create_schema = "CREATE SCHEMA IF NOT EXISTS main.pitchside"
    create_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            student_id STRING,
            study_hours INT,
            extracurricular_count INT,
            credit_hours INT,
            primary_struggle STRING,
            assignment_start_style STRING
        ) USING DELTA
    """
    clear_table = f"DELETE FROM {TABLE_NAME}"
    insert_statement = f"INSERT INTO {TABLE_NAME} VALUES (?, ?, ?, ?, ?, ?)"
    rows = [tuple(row) for row in students.itertuples(index=False, name=None)]

    with sql.connect(
        server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(create_schema)
            cursor.execute(create_table)
            cursor.execute(clear_table)
            cursor.executemany(insert_statement, rows)

    print(f"Created {TABLE_NAME} with {len(rows)} synthetic records.")


if __name__ == "__main__":
    main()
