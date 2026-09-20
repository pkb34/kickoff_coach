import json
import unittest

from local_question_agent import (
    PROHIBITED, STARTING_QUESTIONS, answer_question,
    start_agent, structured_record, validate_baseline,
)


BASELINE = {
    "activity_type": "volunteering", "activity_hours": "3",
    "class_hours": "16", "weekday_study_hours": "2",
    "weekend_study_hours": "2", "sleep_hours": "8",
}


class LocalQuestionAgentTests(unittest.TestCase):
    def test_three_starting_seven_deep_ten_total(self):
        state = start_agent(validate_baseline(BASELINE))
        while state["status"] == "asking":
            self.assertIsNone(PROHIBITED.search(state["messages"][-1]["content"]))
            reply = "7" if state["current_question_id"] == "wellbeing_rating" else "It feels manageable for me."
            state = answer_question(state, reply)
        record = structured_record(state)
        self.assertEqual(len(STARTING_QUESTIONS), 3)
        self.assertEqual(record["question_count"], {"starting": 3, "deep": 7, "total": 10})
        self.assertTrue(record["coverage"]["complete"])
        self.assertEqual(record["followups"]["wellbeing_rating"]["value"], 7)
        self.assertNotIn("gpa", json.dumps(record).lower())
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(state["asked_ids"]), len(set(state["asked_ids"])))
        self.assertEqual(len([item for item in state["messages"] if item["role"] == "assistant"]), 7)

    def test_short_sleep_triggers_one_personal_followup(self):
        raw = {**BASELINE, "activity_hours": "10", "weekday_study_hours": "1",
               "weekend_study_hours": "4", "sleep_hours": "6"}
        state = start_agent(validate_baseline(raw))
        while state["status"] == "asking":
            reply = "7" if state["current_question_id"] == "wellbeing_rating" else "It feels manageable for me."
            state = answer_question(state, reply)
        record = structured_record(state)
        self.assertEqual(record["question_count"], {"starting": 3, "deep": 8, "total": 11})
        self.assertIn("sleep_barrier", record["followups"])
        self.assertIn("wellbeing_rating", record["followups"])

    def test_low_self_rating_can_trigger_support_question(self):
        state = start_agent(validate_baseline(BASELINE))
        while state["status"] == "asking":
            reply = ("3" if state["current_question_id"] == "wellbeing_rating" else
                     "It feels manageable for me.")
            state = answer_question(state, reply)
        self.assertIn("support_preference", state["answers"])
        self.assertEqual(len(state["answers"]), 8)

    def test_happiness_rating_requires_a_direct_number(self):
        state = start_agent(validate_baseline(BASELINE))
        while state["current_question_id"] != "wellbeing_rating":
            state = answer_question(state, "It feels manageable for me.")
        with self.assertRaises(ValueError):
            answer_question(state, "I feel fine")
        self.assertNotIn("wellbeing_rating", state["answers"])

    def test_reply_moves_to_next_relevant_question(self):
        state = start_agent(validate_baseline(BASELINE))
        state = answer_question(state, "Volunteering conflicts with my study time.")
        self.assertEqual(state["current_question_id"], "class_experience")
        self.assertIsNone(PROHIBITED.search(state["messages"][-1]["content"]))

    def test_mark_related_question_is_blocked_and_not_saved(self):
        state = start_agent(validate_baseline(BASELINE))
        with self.assertRaises(ValueError):
            answer_question(state, "My GPA is 3.5.")
        self.assertFalse(state["answers"])
        with self.assertRaises(ValueError):
            validate_baseline({**BASELINE, "gpa": "3.5"})

    def test_unknown_and_declined_baseline_answers(self):
        raw = {**BASELINE, "activity_type": "none", "activity_hours": "0",
               "sleep_hours": "Prefer not to say"}
        baseline = validate_baseline(raw)
        self.assertEqual(baseline["fields"]["activity_type"]["status"], "not_applicable")
        self.assertEqual(baseline["fields"]["sleep_hours"]["status"], "declined")


if __name__ == "__main__":
    unittest.main()
