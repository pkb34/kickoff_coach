import unittest

from local_question_agent import BASELINE_SPECS, CORE_QUESTION_IDS, EXTRA_QUESTION_IDS
from pixel_theme import QUESTION_TILES, question_scene_html


class QuestionArtTests(unittest.TestCase):
    def test_every_active_question_has_matching_art(self):
        ids = set(BASELINE_SPECS) | set(CORE_QUESTION_IDS) | set(EXTRA_QUESTION_IDS)
        self.assertFalse(ids - set(QUESTION_TILES))
        for question_id in ids:
            self.assertIn("wpti-question-art", question_scene_html(question_id))

    def test_unknown_legacy_question_uses_safe_art(self):
        self.assertIn("wpti-question-art", question_scene_html("future_team_question"))


if __name__ == "__main__":
    unittest.main()
