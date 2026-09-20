import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from databricks import sql

import databricks_writer
import storage


class FakeConnection:
    def __init__(self, fail_merge=False):
        self.calls = []
        self.fail_merge = fail_merge

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self):
        return self

    def execute(self, query, values=None):
        self.calls.append((query, values))
        if self.fail_merge and query.startswith("MERGE INTO"):
            raise RuntimeError("Temporary connection failure")


class DatabricksWriterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        old_path = storage.DB_PATH
        storage.DB_PATH = Path(self.directory.name) / "checkins.sqlite3"
        self.addCleanup(setattr, storage, "DB_PATH", old_path)
        self.secrets = patch.object(databricks_writer, "SECRETS_PATH", Path(self.directory.name) / "missing.toml")
        self.secrets.start()
        self.addCleanup(self.secrets.stop)
        self.connection_settings = {
            "DATABRICKS_SERVER_HOSTNAME": "dbc-example.cloud.databricks.com",
            "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/demo",
            "DATABRICKS_TOKEN": "test-only-token",
        }

    def save(self):
        return storage.save_collection_submission(
            {"schema_version": "2.0", "baseline": {"activity_type": "Sports"}},
            [{"role": "user", "content": "private transcript words"}],
            {"analysis": {"metrics": {"nightly_sleep_hours": 7}}},
        )

    def test_unconfigured_upload_stays_queued(self):
        self.save()
        with patch.dict("os.environ", {key: "" for key in self.connection_settings}):
            self.assertEqual(databricks_writer.sync_pending()["status"], "not_configured")
        self.assertEqual(storage.pending_databricks_count(), 1)

    def test_upload_omits_transcript_and_updates_existing_result(self):
        saved = self.save()
        fake = FakeConnection()
        with patch.dict("os.environ", self.connection_settings), patch.object(sql, "connect", return_value=fake):
            result = databricks_writer.sync_pending()
            self.assertEqual(result, {"status": "synced", "synced": 1, "pending": 0})
            merge, params = fake.calls[-1]
            self.assertIn("MERGE INTO main.pitchside.wpti_submissions", merge)
            self.assertEqual(params[0], saved["id"])
            self.assertIn("Sports", params[2])
            self.assertNotIn("private transcript words", str(fake.calls))

            storage.update_collection_result(saved["id"], {"analysis": {"metrics": {"nightly_sleep_hours": 8}}})
            self.assertEqual(storage.pending_databricks_count(), 1)
            self.assertEqual(databricks_writer.sync_pending()["status"], "synced")
            self.assertIn('"nightly_sleep_hours": 8', fake.calls[-1][1][3])

    def test_failed_upload_can_be_retried(self):
        self.save()
        with patch.dict("os.environ", self.connection_settings), patch.object(
            sql, "connect", side_effect=[FakeConnection(fail_merge=True), FakeConnection()]
        ):
            self.assertEqual(databricks_writer.sync_pending()["status"], "unavailable")
            self.assertEqual(storage.pending_databricks_count(), 1)
            self.assertEqual(databricks_writer.sync_pending()["status"], "synced")
            self.assertEqual(storage.pending_databricks_count(), 0)

    def test_oauth_connects_without_a_token(self):
        self.save()
        fake = FakeConnection()
        settings = {**self.connection_settings, "DATABRICKS_TOKEN": "", "DATABRICKS_AUTH_TYPE": "databricks-oauth"}
        with patch.dict("os.environ", settings), patch.object(sql, "connect", return_value=fake) as connect:
            self.assertEqual(databricks_writer.sync_pending()["status"], "synced")
        self.assertEqual(connect.call_args.kwargs["auth_type"], "databricks-oauth")
        self.assertNotIn("access_token", connect.call_args.kwargs)

    def test_table_identifier_rejects_sql(self):
        with patch.dict("os.environ", {"DATABRICKS_SUBMISSIONS_TABLE": "main.pitchside.rows;DROP TABLE x"}):
            with self.assertRaises(ValueError):
                databricks_writer._settings()

    def test_staff_can_queue_older_local_records_explicitly(self):
        saved = self.save()
        with closing(sqlite3.connect(storage.DB_PATH)) as connection:
            with connection:
                connection.execute("DELETE FROM databricks_outbox WHERE submission_id = ?", (saved["id"],))
        self.assertEqual(storage.pending_databricks_count(), 0)
        self.assertEqual(storage.enqueue_existing_databricks_submissions(), 1)
        self.assertEqual(storage.enqueue_existing_databricks_submissions(), 0)
        self.assertEqual(storage.pending_databricks_count(), 1)


if __name__ == "__main__":
    unittest.main()
