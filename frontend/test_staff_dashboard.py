import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import storage


class StaffDashboardTests(unittest.TestCase):
    def test_password_gate_and_aggregate_only(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"WPTI_STAFF_PASSWORD": "test-only-pass"}):
            previous = storage.DB_PATH
            storage.DB_PATH = Path(directory) / "sample.sqlite3"
            try:
                storage.save_collection_submission(
                    {"private_response": "do not show"}, [],
                    {"analysis": {"metrics": {
                        "weekly_class_hours": 15, "weekly_independent_study_hours": 8,
                        "weekly_extracurricular_hours": 3, "nightly_sleep_hours": 8,
                        "self_reported_happiness_index": 70,
                        "self_reported_academic_progress": "Feeling on track",
                    }}, "wpti": {"position": "Goalkeeper"}},
                )
                app = AppTest.from_file("staff_dashboard.py").run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.metric), 0)
                app.text_input[0].set_value("test-only-pass")
                app.button[0].click().run()
                self.assertFalse(app.exception)
                self.assertTrue(any(metric.label == "Saved check-ins with analysis" for metric in app.metric))
                self.assertFalse(any("do not show" in str(item.value) for item in app.markdown))
            finally:
                storage.DB_PATH = previous

    def test_authenticated_staff_can_render_gemini_group_report(self):
        report = {
            "status": "generated", "overview": "A group overview.",
            "wellbeing": "A wellbeing summary.",
            "performance": "A progress summary.",
            "suggested_actions": ["Offer office hours.", "Share support links.", "Ask for feedback."],
            "limitations": "Self-reported data only.",
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"WPTI_STAFF_PASSWORD": "test-only-pass"}), \
             patch("gemini_gateway.is_configured", return_value=True), \
             patch("staff_report.generate_staff_report", return_value=report) as generate:
            previous = storage.DB_PATH
            storage.DB_PATH = Path(directory) / "group.sqlite3"
            try:
                for _ in range(10):
                    storage.save_collection_submission({}, [], {"analysis": {"metrics": {
                        "weekly_class_hours": 15, "weekly_independent_study_hours": 8,
                        "weekly_extracurricular_hours": 3, "nightly_sleep_hours": 8,
                        "self_reported_happiness_index": 70,
                        "self_reported_academic_progress": "Feeling on track",
                    }}})
                app = AppTest.from_file("staff_dashboard.py").run()
                app.text_input[0].set_value("test-only-pass")
                next(button for button in app.button if button.label == "Open overview").click().run()
                next(button for button in app.button if button.label == "Generate group report with Gemini").click().run()
                self.assertFalse(app.exception)
                self.assertEqual(generate.call_count, 1)
                self.assertTrue(any("A group overview." in str(item.value) for item in app.markdown))
            finally:
                storage.DB_PATH = previous


if __name__ == "__main__":
    unittest.main()
