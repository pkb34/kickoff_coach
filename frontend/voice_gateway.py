"""Optional one-turn voice answers through the already configured Gemini API."""

from __future__ import annotations

import base64
import json
from urllib import request

from gemini_gateway import ENDPOINT, _settings
from local_question_agent import PROHIBITED


def voice_answer(audio: bytes, question: str, options: list[str] | None = None, *, opener=None) -> str:
    """Return a transcript or an exact listed choice; never save or log audio."""
    key, model = _settings()
    if not key:
        raise ValueError("Voice replies need the Gemini key configured on this device.")
    if not audio or len(audio) > 8_000_000:
        raise ValueError("Please record a short answer (under about one minute).")
    instruction = (
        "Listen to this student's short spoken answer to the question. "
        "Return only JSON with one string property called answer. "
        "Do not add advice, commentary, private details, or an answer the student did not say. "
        "If the speech is unclear, return an empty answer. "
        f"Question: {question}\n"
    )
    if options:
        instruction += (
            "Map the meaning to exactly one of these choices. If no choice is clear, return an empty answer. "
            "Never guess a choice. Choices: " + json.dumps(options, ensure_ascii=False)
        )
    else:
        instruction += "Transcribe their answer as a short first-person sentence in English."
    body = {
        "contents": [{"role": "user", "parts": [
            {"text": instruction},
            {"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(audio).decode("ascii")}},
        ]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 180},
    }
    call = request.Request(
        ENDPOINT.format(model=model), data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with (opener or request.urlopen)(call, timeout=25) as response:
            payload = json.load(response)
        text = "".join(part.get("text", "") for part in payload["candidates"][0]["content"]["parts"])
        answer = json.loads(text).get("answer", "")
    except (OSError, KeyError, IndexError, TypeError, ValueError) as error:
        raise ValueError("I couldn't hear that clearly. Please try again or tap an answer.") from error
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 800:
        raise ValueError("I couldn't hear that clearly. Please try again or tap an answer.")
    answer = answer.strip()
    if PROHIBITED.search(answer):
        raise ValueError("Please answer without academic marks.")
    if options and answer not in options:
        raise ValueError("I couldn't match that to a choice. Please try again or tap an answer.")
    return answer
