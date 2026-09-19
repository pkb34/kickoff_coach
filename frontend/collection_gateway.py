"""Single integration point for a future information-collection agent.

Replace the active backend with an implementation of CollectorBackend. The UI
does not need to change if the backend keeps this contract.
"""

from __future__ import annotations

from typing import Protocol

from collector import FIELDS, advance_collection, coverage, revise_answer, start_collection


class CollectorBackend(Protocol):
    def start(self) -> dict: ...
    def advance(self, state: dict, student_message: str) -> dict: ...
    def revise(self, state: dict, field: str, answer: str) -> dict: ...


class DemoCollector:
    def start(self) -> dict:
        return start_collection()

    def advance(self, state: dict, student_message: str) -> dict:
        return advance_collection(state, student_message)

    def revise(self, state: dict, field: str, answer: str) -> dict:
        return revise_answer(state, field, answer)


ACTIVE_BACKEND: CollectorBackend = DemoCollector()


def start_session() -> dict:
    state = ACTIVE_BACKEND.start()
    validate_state(state)
    return state


def submit_turn(state: dict, student_message: str) -> dict:
    updated = ACTIVE_BACKEND.advance(state, student_message)
    validate_state(updated)
    return updated


def correct_answer(state: dict, field: str, answer: str) -> dict:
    updated = ACTIVE_BACKEND.revise(state, field, answer)
    validate_state(updated)
    return updated


def validate_state(state: dict) -> None:
    if not isinstance(state, dict) or state.get("schema_version") != "1.0":
        raise ValueError("Collector returned an unsupported schema version.")
    if state.get("status") not in ("collecting", "review"):
        raise ValueError("Collector returned an invalid status.")
    if not isinstance(state.get("fields"), dict) or not isinstance(state.get("messages"), list):
        raise ValueError("Collector returned an incomplete state.")
    if not isinstance(state.get("turn_count"), int) or state["turn_count"] < 0:
        raise ValueError("Collector returned an invalid turn count.")
    if state["status"] == "collecting" and state.get("current_field") not in FIELDS:
        raise ValueError("Collector must provide the next field while collecting.")
    if state["status"] == "review" and (state.get("current_field") is not None or not coverage(state["fields"])["complete"]):
        raise ValueError("Collector marked an incomplete record as ready for review.")
    for key, detail in state["fields"].items():
        if key not in FIELDS or not isinstance(detail, dict):
            raise ValueError("Collector returned an unknown field.")
        if detail.get("status") not in ("answered", "unknown", "declined", "not_applicable"):
            raise ValueError("Collector returned an invalid field status.")
        if detail.get("unit") != FIELDS[key]["unit"]:
            raise ValueError("Collector returned an invalid field unit.")
        if not isinstance(detail.get("source_turn"), int) or not 1 <= detail["source_turn"] <= state["turn_count"]:
            raise ValueError("Collector returned an invalid source turn.")
        if detail["status"] != "answered" and detail.get("value") is not None:
            raise ValueError("Unavailable fields must have a null value.")
    for message in state["messages"]:
        if not isinstance(message, dict) or message.get("role") not in ("assistant", "user") or not isinstance(message.get("content"), str):
            raise ValueError("Collector returned an invalid message.")
