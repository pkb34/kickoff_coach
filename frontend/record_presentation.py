"""Student-facing review of a collected record without exposing its JSON schema."""

from __future__ import annotations

import streamlit as st

from local_question_agent import BASELINE_SPECS


STATUS_TEXT = {
    "unknown": "I don't know",
    "declined": "Prefer not to say",
    "not_applicable": "None",
}


def _display_field(field: dict) -> str:
    if field.get("status") != "answered":
        return STATUS_TEXT.get(field.get("status"), "Not answered")
    value = field.get("value")
    unit = field.get("unit")
    return f"{value:g} {unit}" if isinstance(value, (int, float)) and unit else str(value)


def render_record_review(record: dict, *, expanded: bool = False) -> None:
    """Show questions and answers as ordinary text, not a developer data object."""
    if record.get("schema_version") != "2.0":
        return
    with st.expander("Review your answers", expanded=expanded):
        for key, field in record["baseline"]["fields"].items():
            st.write(f"**{BASELINE_SPECS[key]['label']}**")
            st.write(_display_field(field))
        for answer in record["followups"].values():
            st.write(f"**{answer['question']}**")
            st.write(answer.get("answer") or STATUS_TEXT.get(answer.get("status"), "Not answered"))
