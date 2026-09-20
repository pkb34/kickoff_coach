import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

import storage
from local_question_agent import (
    answer_question, start_agent,
    structured_record, validate_baseline,
)
from wpti_types import BEHAVIOR_CHOICES, infer_profile_from_record


BASELINE_RAW = {
    "activity_type": "soccer club", "activity_hours": "4",
    "class_hours": "15", "weekday_study_hours": "1.5",
    "weekend_study_hours": "2", "sleep_hours": "7.5",
}


class AppTests(unittest.TestCase):
    def test_academic_question_has_art_and_voice_only_on_open_question(self):
        app = AppTest.from_file("app.py").run()
        state = start_agent(validate_baseline({**BASELINE_RAW, "sleep_hours": "6"}))
        app.session_state["local_agent_state"] = state
        app.switch_page("views/quiz.py").run()
        self.assertFalse(app.exception)
        self.assertFalse(any("Prefer speaking?" in item.label for item in app.expander))

        while state["current_question_id"] != "academic_progress":
            question_id = state["current_question_id"]
            state = answer_question(state, BEHAVIOR_CHOICES[question_id][0][0])
        app.session_state["local_agent_state"] = state
        app.switch_page("views/quiz.py").run()
        self.assertFalse(app.exception)
        self.assertFalse(any("Prefer speaking?" in item.label for item in app.expander))

        state = answer_question(state, "Feeling on track")
        state = answer_question(state, "Usually tired")
        self.assertEqual(state["current_question_id"], "sleep_barrier")
        app.session_state["local_agent_state"] = state
        app.switch_page("views/quiz.py").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Prefer speaking?" in item.label for item in app.expander))

    def test_welcome_local_agent_and_result_render(self):
        with tempfile.TemporaryDirectory() as directory:
            old_path = storage.DB_PATH
            storage.DB_PATH = Path(directory) / "test.sqlite3"
            try:
                app = AppTest.from_file("app.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(app.button[0].label, "Discover My WPTI")
                app.toggle[0].set_value(True).run()
                self.assertFalse(app.exception)
                self.assertTrue(app.session_state["audio_enabled"])

                app.switch_page("views/quiz.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.text_input), 0)
                self.assertTrue(any(item.label == "Usual sleep per night" for item in app.radio))
                self.assertFalse(any("GPA" in item.label for item in app.radio))

                state = start_agent(validate_baseline(BASELINE_RAW))
                app.session_state["local_agent_state"] = state
                app.switch_page("views/quiz.py").run()
                self.assertFalse(app.exception)
                self.assertTrue(len(app.text_area) == 1 or len(app.radio) >= 1)
                app.radio[0].set_value(BEHAVIOR_CHOICES["activity_balance"][0][0])
                next_button = next(button for button in app.button if button.label == "Send my answer")
                next_button.click().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["local_agent_state"]["current_question_id"], "class_experience")
                self.assertEqual(len([m for m in app.session_state["local_agent_state"]["messages"]
                                      if m["role"] == "assistant"]), 2)

                while state["status"] == "asking":
                    question_id = state["current_question_id"]
                    reply = ("7" if question_id == "wellbeing_rating" else
                             BEHAVIOR_CHOICES[question_id][0][0] if question_id in BEHAVIOR_CHOICES else
                             "It feels manageable for me.")
                    state = answer_question(state, reply)
                record = structured_record(state)
                app.session_state["local_agent_state"] = state
                app.switch_page("views/quiz.py").run()
                self.assertFalse(app.exception)
                wpti = infer_profile_from_record(record)
                self.assertEqual(wpti["code"], "GCPT")
                self.assertEqual(app.session_state["latest_submission"]["result"]["wpti"]["code"], "GCPT")
                app.switch_page("views/result.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.metric), 4)
                self.assertTrue(any(metric.label == "How you feel lately" for metric in app.metric))
                self.assertTrue(any("national team vibe" in str(item.value).lower() for item in app.markdown))
                self.assertFalse(any("GPA" in metric.label for metric in app.metric))
                self.assertFalse(any(item.value == "Your Player Analogy" for item in app.subheader))
            finally:
                storage.DB_PATH = old_path


if __name__ == "__main__":
    unittest.main()
