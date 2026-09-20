import json
import unittest
from io import BytesIO
from unittest.mock import patch

from voice_gateway import voice_answer


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


class VoiceGatewayTests(unittest.TestCase):
    def test_spoken_choice_must_match_a_real_option(self):
        sent = {}

        def opener(call, timeout):
            sent["body"] = json.loads(call.data)
            payload = {"candidates": [{"content": {"parts": [{"text": '{"answer":"Talk it through"}'}]}}]}
            return Response(json.dumps(payload).encode())

        with patch("voice_gateway._settings", return_value=("test-key", "test-model")):
            answer = voice_answer(b"test-wav", "How do you learn?", ["Talk it through", "Think it through solo"], opener=opener)
        self.assertEqual(answer, "Talk it through")
        self.assertEqual(sent["body"]["contents"][0]["parts"][1]["inlineData"]["mimeType"], "audio/wav")

    def test_unlisted_response_is_not_guessed(self):
        def opener(call, timeout):
            payload = {"candidates": [{"content": {"parts": [{"text": '{"answer":"Other"}'}]}}]}
            return Response(json.dumps(payload).encode())

        with patch("voice_gateway._settings", return_value=("test-key", "test-model")):
            with self.assertRaises(ValueError):
                voice_answer(b"test-wav", "How do you learn?", ["Talk it through"], opener=opener)


if __name__ == "__main__":
    unittest.main()
