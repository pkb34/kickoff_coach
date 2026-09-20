import json
import unittest
from io import BytesIO
from urllib.error import HTTPError

from analysis_agent import analyze_record, gemini_summary
from football_matches import MATCHES, match_football_identity
from gemini_gateway import generate_briefing
from local_question_agent import answer_question, start_agent, structured_record, validate_baseline


RAW = {
    "activity_type": "volunteering", "activity_hours": "3", "class_hours": "16",
    "weekday_study_hours": "2", "weekend_study_hours": "2", "sleep_hours": "8",
}


def sample_record(skip_rating=False):
    state = start_agent(validate_baseline(RAW))
    while state["status"] == "asking":
        reply = (("Prefer not to say" if skip_rating else "7")
                 if state["current_question_id"] == "wellbeing_rating" else
                 "Private test phrase from a student response.")
        state = answer_question(state, reply)
    return structured_record(state)


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


class AnalysisAgentTests(unittest.TestCase):
    def test_time_band_answers_keep_their_ranges(self):
        raw = {
            "activity_type": "Arts or music", "activity_hours": "4–6h",
            "class_hours": "14–16h", "weekday_study_hours": "1h",
            "weekend_study_hours": "3–4h", "sleep_hours": "7h",
        }
        state = start_agent(validate_baseline(raw))
        while state["status"] == "asking":
            reply = "7" if state["current_question_id"] == "wellbeing_rating" else "It feels manageable."
            state = answer_question(state, reply)
        analysis = analyze_record(structured_record(state))
        ranges = analysis["metrics"]["time_ranges"]
        self.assertEqual(ranges["weekly_extracurricular_hours"], [4.0, 6.0])
        self.assertEqual(ranges["weekly_independent_study_hours"], [11.0, 13.0])
        self.assertEqual(gemini_summary(analysis)["time_ranges"]["weekly_independent_study_hours"], [11.0, 13.0])

    def test_direct_rating_and_time_arithmetic(self):
        analysis = analyze_record(sample_record())
        self.assertEqual(analysis["metrics"]["self_reported_happiness_index"], 70)
        self.assertEqual(analysis["metrics"]["weekly_independent_study_hours"], 14)
        self.assertEqual(analysis["metrics"]["weekly_reported_commitment_hours"], 33)
        self.assertEqual(analysis["wellbeing_context"]["assessment_status"], "not_assessed")

    def test_skipped_rating_remains_unavailable(self):
        analysis = analyze_record(sample_record(skip_rating=True))
        self.assertIsNone(analysis["metrics"]["self_reported_happiness_index"])
        self.assertIsNone(gemini_summary(analysis)["self_reported_happiness_index"])

    def test_gemini_receives_only_whitelisted_summary(self):
        analysis = analyze_record(sample_record())
        sent = {}

        def opener(http_request, timeout):
            sent["body"] = http_request.data.decode("utf-8")
            sent["header"] = http_request.get_header("X-goog-api-key")
            payload = {"candidates": [{"content": {"parts": [{"text": json.dumps({
                "summary": "You have a reported routine.",
                "suggestions": ["Plan one study block.", "Keep a flexible rest window."],
                "future_moments": "Next week, you might find a comfortable rhythm by trying one small change.",
            })}]}}]}
            return Response(json.dumps(payload).encode("utf-8"))

        telemetry = {
            "status": "available",
            "study_hours": 12,
            "extracurricular_count": 2,
            "credit_hours": 15,
            "assignment_start_style": "Early",
            "student_id": "VT-DEMO-001",
            "primary_struggle": "Private source field",
        }
        briefing = generate_briefing(analysis, telemetry, api_key="test-key", opener=opener)
        self.assertEqual(briefing["status"], "generated")
        self.assertIn("future_moments", briefing)
        self.assertEqual(sent["header"], "test-key")
        self.assertNotIn("Private test phrase", sent["body"])
        self.assertNotIn("volunteering", sent["body"])
        self.assertIn("databricks_telemetry", sent["body"])
        self.assertIn("weekly_study_hours", sent["body"])
        self.assertIn("extracurricular_count", sent["body"])
        self.assertIn("credit_hours", sent["body"])
        self.assertIn("assignment_start_style", sent["body"])
        self.assertNotIn("VT-DEMO-001", sent["body"])
        self.assertNotIn("Private source field", sent["body"])
        self.assertIn("tied to reported study, activity, class, or sleep time", sent["body"])
        self.assertIn("do not describe it as this student's data", sent["body"])
        self.assertEqual(gemini_summary(analysis)["self_reported_happiness_index"], 70)

    def test_api_rejection_does_not_break_local_analysis(self):
        analysis = analyze_record(sample_record())

        def reject(_request, timeout):
            raise HTTPError("https://example.test", 403, "Forbidden", {}, None)

        briefing = generate_briefing(analysis, api_key="test-key", opener=reject)
        self.assertEqual(briefing["status"], "unavailable")
        self.assertEqual(analysis["metrics"]["self_reported_happiness_index"], 70)

    def test_every_demo_role_has_a_team_without_player_analogy(self):
        for role in MATCHES:
            match = match_football_identity(role)
            self.assertTrue(match["national_team"])
            self.assertNotIn("player", match)
            self.assertNotIn("player_explanation", match)
            self.assertTrue(match["team_source"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
