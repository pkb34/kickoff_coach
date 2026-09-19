import unittest

from engine import assign_demo_personality, process_with_agent, validate_answers, validate_baseline
from followups import select_demo_questions, select_questions_with_agent, validate_followup_answers


VALID = {"study_hours": 12, "activity": {"type": "sports", "hours": 5}, "class_hours": 16, "sleep_hours": 7.5}
BASELINE = {
    "sleep_hours": 7.5, "class_hours": 15, "gpa": 3.1,
    "activity_hours": 4, "weekday_study_hours": 1.5, "weekend_study_hours": 2,
}


class EngineTests(unittest.TestCase):
    def test_four_answers_and_demo_result(self):
        answers = validate_answers(VALID)
        result = process_with_agent(answers)
        self.assertEqual(result["weekly_scheduled_hours"], 33)
        self.assertEqual(result["status"], "demo_rule_result")

    def test_missing_question_rejected(self):
        data = dict(VALID)
        del data["sleep_hours"]
        with self.assertRaises(ValueError):
            validate_answers(data)

    def test_activity_type_and_hours_must_agree(self):
        data = dict(VALID)
        data["activity"] = {"type": "none", "hours": 2}
        with self.assertRaises(ValueError):
            validate_answers(data)

    def test_each_demo_personality_is_reachable(self):
        base = validate_baseline(BASELINE)
        self.assertEqual(assign_demo_personality(base), "midfielder")
        self.assertEqual(assign_demo_personality({**base, "activity_hours": 9}), "captain")
        self.assertEqual(assign_demo_personality({**base, "gpa": 3.6, "weekday_study_hours": 3, "weekend_study_hours": 3}), "penalty_striker")
        self.assertEqual(assign_demo_personality({**base, "weekday_study_hours": 0.5, "sleep_hours": 6}), "defender")

    def test_agent_slot_and_demo_followup_selection(self):
        baseline = validate_baseline({**BASELINE, "sleep_hours": 6, "gpa": 2.7})
        self.assertIsNone(select_questions_with_agent(baseline))
        selected = select_demo_questions(baseline)
        self.assertIn("sleep_quality", selected)
        self.assertIn("coursework_support", selected)
        responses = {
            "sleep_quality": "Somewhat rested",
            "coursework_support": "Sometimes challenging",
        }
        self.assertEqual(validate_followup_answers(selected, responses), responses)
        with self.assertRaises(ValueError):
            validate_followup_answers(selected, {"sleep_quality": "Somewhat rested"})


if __name__ == "__main__":
    unittest.main()
