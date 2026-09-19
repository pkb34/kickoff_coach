"""Conversational student-information collection UI."""

from __future__ import annotations

import sqlite3

import streamlit as st

from collection_gateway import correct_answer, start_session, submit_turn
from collector import FIELDS, baseline_for_demo_result, coverage, structured_record
from engine import assign_demo_personality
from storage import save_collection_submission


if "collection_state" not in st.session_state:
    st.session_state["collection_state"] = start_session()

state = st.session_state["collection_state"]
covered = coverage(state["fields"])
done = len(covered["answered"]) + len(covered["unavailable"])

st.caption("WCPT · INFORMATION CHECK")
st.title("⚽ Tell Us About Your Week")
st.write("Answer a few questions about sleep, classes and GPA, activities, and study time. Each answer helps choose the next question.")
st.info("Demo collector: this version understands short numbers and listed choices. A future agent will handle natural-language answers and deeper clarification. Please do not enter your name or other identifying details.")
st.progress(done / len(covered["required"]))
st.caption(f"{done} of {len(covered['required'])} needed details covered · {len(covered['unavailable'])} unavailable")

for message in state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if state["status"] == "collecting":
    field = state["current_field"]
    st.caption("You can also answer: I don't know · Prefer not to say")
    with st.form(f"answer_{field}_{state['turn_count']}", clear_on_submit=True):
        answer = st.text_input("Your answer", max_chars=500, key=f"answer_text_{state['turn_count']}")
        sent = st.form_submit_button("Send Answer", type="primary", use_container_width=True)
    if sent:
        try:
            st.session_state["collection_state"] = submit_turn(state, answer)
            st.rerun()
        except ValueError as error:
            st.error(str(error))

if state["fields"]:
    with st.expander("Review or correct collected details", expanded=state["status"] == "review"):
        for key, detail in state["fields"].items():
            spec = FIELDS[key]
            shown = detail["value"] if detail["status"] == "answered" else detail["status"].replace("_", " ").title()
            if key == "sleep_quality" and detail["status"] == "answered":
                shown = str(shown).replace("_", " ").title()
            unit = f" {spec['unit']}" if detail["status"] == "answered" and spec["unit"] and key != "gpa" else ""
            if key == "gpa" and detail["status"] == "answered":
                unit = " (0–4.0 scale)"
            st.write(f"**{spec['label']}:** {shown}{unit}")
        editable = [key for key in state["fields"] if state["fields"][key]["status"] != "not_applicable"]
        with st.form("correction_form", clear_on_submit=True):
            correction_field = st.selectbox("Correct a detail", editable, format_func=lambda key: FIELDS[key]["label"])
            correction_value = st.text_input("Correct value", max_chars=500)
            corrected = st.form_submit_button("Save Correction")
        if corrected:
            try:
                st.session_state["collection_state"] = correct_answer(state, correction_field, correction_value)
                st.rerun()
            except ValueError as error:
                st.error(str(error))

if state["status"] == "review":
    record = structured_record(state)
    if covered["unavailable"]:
        st.warning("Some details were marked unavailable. They will remain missing in the final record, and a demo personality may not be available.")
    st.caption("Review the record above, make any corrections, then confirm. The transcript and structured record will be saved locally.")
    with st.expander("Preview structured record"):
        st.json(record)
    if st.button("Confirm and See My Result", type="primary", use_container_width=True):
        try:
            baseline = baseline_for_demo_result(record)
            result = (
                {"status": "demo_personality", "personality": assign_demo_personality(baseline)}
                if baseline else {"status": "insufficient_data", "personality": None}
            )
            st.session_state["latest_submission"] = save_collection_submission(record, state["messages"], result)
            st.switch_page("views/result.py")
        except (OSError, sqlite3.Error):
            st.error("Unable to save the record. Check the data directory and try again.")

if st.button("Start This Information Check Again"):
    st.session_state["collection_state"] = start_session()
    st.session_state.pop("latest_submission", None)
    st.rerun()

st.caption("No AI assessment or GPA, sleep, or wellbeing prediction is performed in this prototype.")
