import unittest

from campus_resources import recommendations


class CampusResourceTests(unittest.TestCase):
    def test_sport_and_rest_personalize_links(self):
        record = {
            "baseline": {"fields": {"activity_type": {"status": "answered", "value": "Sports or movement"}}},
            "followups": {"sleep_quality": {"answer": "Usually tired"},
                          "campus_belonging": {"answer": "I feel connected"}},
        }
        names = [label for label, _, _ in recommendations(record, {"metrics": {"self_reported_happiness_index": 70}})]
        self.assertIn("Explore VT sport clubs", names)
        self.assertIn("Explore Hokie Wellness sleep resources", names)
        self.assertNotIn("Connect with Cook Counseling Center", names)

    def test_support_option_is_available_for_lower_self_rating(self):
        record = {"baseline": {"fields": {"activity_type": {"status": "answered", "value": "Arts or music"}}},
                  "followups": {"campus_belonging": {"answer": "I feel disconnected"}}}
        names = [label for label, _, _ in recommendations(record, {"metrics": {"self_reported_happiness_index": 30}})]
        self.assertIn("Explore VT arts and design clubs", names)
        self.assertIn("Connect with Cook Counseling Center", names)


if __name__ == "__main__":
    unittest.main()
