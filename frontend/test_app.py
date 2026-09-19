import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

import storage
from collector import advance_collection, start_collection, structured_record
from engine import assign_demo_personality


class AppTests(unittest.TestCase):
    def test_welcome_collection_and_result_render(self):
        with tempfile.TemporaryDirectory() as directory:
            old_path = storage.DB_PATH
            storage.DB_PATH = Path(directory) / "test.sqlite3"
            try:
                app = AppTest.from_file("app.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(app.button[0].label, "Start WCPT")

                app.switch_page("views/quiz.py").run()
                self.assertFalse(app.exception)
                self.assertTrue(any("Your answer" == item.label for item in app.text_input))
                self.assertTrue(any("Send Answer" == item.label for item in app.button))

                state = start_collection()
                for answer in ("7.5", "15", "3.1", "4", "sports club", "1.5", "2"):
                    state = advance_collection(state, answer)
                record = structured_record(state)
                baseline = {key: record["fields"][key]["value"] for key in (
                    "sleep_hours", "class_hours", "gpa", "activity_hours",
                    "weekday_study_hours", "weekend_study_hours",
                )}
                result = {"status": "demo_personality", "personality": assign_demo_personality(baseline)}
                app.session_state["latest_submission"] = storage.save_collection_submission(record, state["messages"], result)
                app.switch_page("views/result.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.metric), 5)
            finally:
                storage.DB_PATH = old_path


if __name__ == "__main__":
    unittest.main()
