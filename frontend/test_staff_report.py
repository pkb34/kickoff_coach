import io
import json
import unittest

from staff_report import MIN_REPORT_CHECKINS, _validate_report, build_staff_snapshot, generate_staff_report


class StaffReportTests(unittest.TestCase):
    def _analyses(self, count=MIN_REPORT_CHECKINS):
        return [{"private_note": "DO_NOT_SEND_THIS_RESPONSE", "metrics": {
            "weekly_class_hours": 15,
            "weekly_independent_study_hours": 12,
            "weekly_extracurricular_hours": 4,
            "nightly_sleep_hours": 7.5,
            "self_reported_happiness_index": 70,
            "self_reported_academic_progress": "Feeling on track",
            "extra_student_identifier": "DO_NOT_SEND_THIS_RESPONSE",
        }} for _ in range(count)]

    def test_snapshot_contains_only_group_statistics(self):
        snapshot = build_staff_snapshot(self._analyses())
        content = json.dumps(snapshot)
        self.assertEqual(snapshot["completed_checkins"], MIN_REPORT_CHECKINS)
        self.assertNotIn("DO_NOT_SEND_THIS_RESPONSE", content)
        self.assertNotIn("extra_student_identifier", content)
        self.assertEqual(snapshot["wellbeing_self_report"]["mean_rating_out_of_10"], 7)

    def test_gemini_receives_snapshot_and_returns_structured_report(self):
        captured = {}
        response = {"candidates": [{"content": {"parts": [{"text": json.dumps({
            "overview": "Ten students completed the check-in.",
            "wellbeing": "The average self-rating was seven out of ten.",
            "performance": "Students reported feeling on track.",
            "suggested_actions": ["Offer study support.", "Share rest resources.", "Invite feedback."],
            "limitations": "These voluntary answers do not predict outcomes.",
        })}]}}]}

        def fake_open(http_request, timeout):
            captured["body"] = http_request.data.decode("utf-8")
            captured["timeout"] = timeout
            return io.BytesIO(json.dumps(response).encode("utf-8"))

        result = generate_staff_report(
            build_staff_snapshot(self._analyses()),
            api_key="test-key", model="gemini-2.5-flash-lite", opener=fake_open,
        )
        self.assertEqual(result["status"], "generated")
        self.assertEqual(len(result["suggested_actions"]), 3)
        self.assertNotIn("DO_NOT_SEND_THIS_RESPONSE", captured["body"])
        self.assertIn("academic_progress_self_report", captured["body"])

    def test_small_cohort_does_not_call_gemini(self):
        snapshot = build_staff_snapshot(self._analyses(MIN_REPORT_CHECKINS - 1))
        self.assertEqual(generate_staff_report(snapshot, api_key="test-key")["status"], "insufficient_data")

    def test_sparse_measure_values_are_suppressed(self):
        analyses = self._analyses()
        for item in analyses[2:]:
            item["metrics"]["self_reported_academic_progress"] = None
        snapshot = build_staff_snapshot(analyses)
        self.assertEqual(snapshot["academic_progress_self_report"]["responses"], 2)
        self.assertIsNone(snapshot["academic_progress_self_report"]["share_feeling_on_track_percent_rounded_to_10"])

    def test_model_cannot_add_unchecked_numbers(self):
        with self.assertRaises(ValueError):
            _validate_report({
                "overview": "All 16 students answered the question.",
                "wellbeing": "Reported feelings vary.",
                "performance": "Progress answers are sparse.",
                "suggested_actions": ["Offer support.", "Invite feedback.", "Review access."],
                "limitations": "This is self-reported information.",
            }, "gemini-2.5-flash-lite")


if __name__ == "__main__":
    unittest.main()
