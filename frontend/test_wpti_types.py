"""Cover all four-axis combinations and their visible positions."""

import itertools
import unittest
from collections import Counter

from wpti_types import AXES, BEHAVIOR_CHOICES, POSITIONS, infer_profile_from_record, profile_from_choices


class WPTITests(unittest.TestCase):
    def test_all_sixteen_types_have_a_position(self):
        profiles = [profile_from_choices(choice) for choice in itertools.product(*[(axis[0], axis[1]) for axis in AXES])]
        self.assertEqual(len(profiles), 16)
        self.assertEqual(len({profile["code"] for profile in profiles}), 16)
        self.assertEqual({profile["code"] for profile in profiles}, set(POSITIONS))
        self.assertTrue(all(profile["position"] and profile["art_role"] for profile in profiles))
        self.assertEqual(set(Counter(profile["position"] for profile in profiles).values()), {2})

    def test_incomplete_preferences_are_rejected(self):
        with self.assertRaises(ValueError):
            profile_from_choices(("G", None, "P", "T"))

    def test_context_answers_produce_type_without_letter_questions(self):
        answers = {question_id: {"status": "answered", "answer": choices[0][0]}
                   for question_id, choices in BEHAVIOR_CHOICES.items()}
        self.assertEqual(infer_profile_from_record({"followups": answers})["code"], "GCPT")
        answers["activity_balance"]["status"] = "declined"
        self.assertIsNone(infer_profile_from_record({"followups": answers}))

    def test_opposite_answers_change_the_character(self):
        first = {key: {"status": "answered", "answer": options[0][0]}
                 for key, options in BEHAVIOR_CHOICES.items()}
        second = {key: {"status": "answered", "answer": options[1][0]}
                  for key, options in BEHAVIOR_CHOICES.items()}
        left = infer_profile_from_record({"followups": first})
        right = infer_profile_from_record({"followups": second})
        self.assertNotEqual(left["code"], right["code"])
        self.assertNotEqual(left["position"], right["position"])


if __name__ == "__main__":
    unittest.main()
