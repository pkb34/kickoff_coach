import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import storage
from engine import process_with_agent, validate_answers
from test_engine import VALID


class StorageTests(unittest.TestCase):
    def test_legacy_feedback_is_translated_without_changing_answers(self):
        with tempfile.TemporaryDirectory() as directory:
            previous_path = storage.DB_PATH
            storage.DB_PATH = Path(directory) / "test.sqlite3"
            try:
                answers = validate_answers(VALID)
                record = storage.save_submission(answers, process_with_agent(answers))
                old_result = {"status": "demo_rule_result", "title": chr(0x4E2D)}
                connection = sqlite3.connect(storage.DB_PATH)
                try:
                    connection.execute(
                        "UPDATE submissions SET result_json = ? WHERE id = ?",
                        (json.dumps(old_result, ensure_ascii=False), record["id"]),
                    )
                    connection.commit()
                finally:
                    connection.close()
                self.assertEqual(storage.migrate_legacy_results(), 1)
                self.assertEqual(storage.migrate_legacy_results(), 0)
                connection = sqlite3.connect(storage.DB_PATH)
                try:
                    row = connection.execute(
                        "SELECT study_hours, result_json FROM submissions WHERE id = ?", (record["id"],)
                    ).fetchone()
                finally:
                    connection.close()
                self.assertEqual(row[0], answers["study_hours"])
                self.assertEqual(json.loads(row[1])["title"], "Your Time-Use Summary")
            finally:
                storage.DB_PATH = previous_path


if __name__ == "__main__":
    unittest.main()
