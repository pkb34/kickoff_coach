import unittest

from collector import (
    advance_collection, baseline_for_demo_result, coverage,
    revise_answer, start_collection, structured_record,
)
from collection_gateway import validate_state


class CollectorTests(unittest.TestCase):
    def test_conditional_followups_and_complete_record(self):
        state = start_collection()
        validate_state(state)
        self.assertEqual(state["current_field"], "sleep_hours")
        state = advance_collection(state, "6.5")
        self.assertEqual(state["current_field"], "sleep_quality")
        for answer in ("often tired", "15", "3.25", "5", "soccer club", "2", "3"):
            state = advance_collection(state, answer)
        self.assertEqual(state["status"], "review")
        record = structured_record(state)
        self.assertTrue(record["coverage"]["complete"])
        self.assertEqual(record["fields"]["activity_type"]["value"], "soccer club")
        self.assertEqual(baseline_for_demo_result(record)["gpa"], 3.25)

    def test_invalid_answer_clarifies_without_guessing(self):
        state = advance_collection(start_collection(), "maybe six or seven")
        self.assertEqual(state["current_field"], "sleep_hours")
        self.assertNotIn("sleep_hours", state["fields"])
        self.assertIn("couldn't record", state["messages"][-1]["content"])

    def test_unavailable_is_preserved_and_result_not_invented(self):
        state = start_collection()
        for answer in ("I don't know", "15", "Prefer not to say", "0", "1", "2"):
            state = advance_collection(state, answer)
        self.assertEqual(state["status"], "review")
        self.assertEqual(state["fields"]["activity_type"]["status"], "not_applicable")
        record = structured_record(state)
        self.assertEqual(set(record["coverage"]["unavailable"]), {"sleep_hours", "gpa"})
        self.assertIsNone(baseline_for_demo_result(record))

    def test_correction_reopens_conditional_question(self):
        state = start_collection()
        for answer in ("8", "15", "3", "0", "1", "2"):
            state = advance_collection(state, answer)
        self.assertEqual(state["status"], "review")
        state = revise_answer(state, "sleep_hours", "6")
        self.assertEqual(state["current_field"], "sleep_quality")
        state = advance_collection(state, "sometimes tired")
        self.assertEqual(state["status"], "review")
        self.assertTrue(coverage(state["fields"])["complete"])


if __name__ == "__main__":
    unittest.main()
