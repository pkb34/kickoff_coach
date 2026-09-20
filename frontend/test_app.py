import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

import storage
from analysis_agent import analyze_record
from engine import assign_local_demo_personality
from football_matches import match_football_identity
from local_question_agent import (
    answer_question, baseline_for_demo_personality, start_agent,
    structured_record, validate_baseline,
)


BASELINE_RAW = {
    "activity_type": "soccer club", "activity_hours": "4",
    "class_hours": "15", "weekday_study_hours": "1.5",
    "weekend_study_hours": "2", "sleep_hours": "7.5",
}


class AppTests(unittest.TestCase):
    def test_welcome_local_agent_and_result_render(self):
        with tempfile.TemporaryDirectory() as directory:
            old_path = storage.DB_PATH
            storage.DB_PATH = Path(directory) / "test.sqlite3"
            try:
                app = AppTest.from_file("app.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(app.button[0].label, "Start WCPT")

                app.switch_page("views/quiz.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.text_input), 6)
                self.assertFalse(any("GPA" in item.label for item in app.text_input))

                state = start_agent(validate_baseline(BASELINE_RAW))
                app.session_state["local_agent_state"] = state
                app.switch_page("views/quiz.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.text_area), 1)

                while state["status"] == "asking":
                    reply = "7" if state["current_question_id"] == "wellbeing_rating" else "It feels manageable for me."
                    state = answer_question(state, reply)
                record = structured_record(state)
                baseline = baseline_for_demo_personality(record)
                result = {"status": "demo_personality", "personality": assign_local_demo_personality(baseline)}
                result["analysis"] = analyze_record(record)
                result["football_match"] = match_football_identity(result["personality"])
                result["gemini"] = {"status": "not_requested"}
                app.session_state["latest_submission"] = storage.save_collection_submission(record, state["messages"], result)
                app.switch_page("views/result.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.metric), 6)
                self.assertFalse(any("GPA" in metric.label for metric in app.metric))
            finally:
                storage.DB_PATH = old_path


if __name__ == "__main__":
    unittest.main()
