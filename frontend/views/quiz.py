"""Three starting questions followed by local adaptive follow-ups."""

from __future__ import annotations

import sqlite3

import streamlit as st

from analysis_agent import analyze_record
from engine import assign_local_demo_personality
from football_matches import match_football_identity
from local_question_agent import (
    BASELINE_SPECS, STARTING_QUESTIONS, answer_question,
    baseline_for_demo_personality, start_agent, structured_record, validate_baseline,
)
from storage import save_collection_submission


st.caption("WCPT · LOCAL QUESTION AGENT")
st.title("⚽ Tell Us About Your Week")
st.write("Start with three quick questions. Then we'll ask a few more based on what you share.")
st.info("Your answers stay here. If you ask The Gaffer for advice later, we'll only send a small summary — never your name or full responses.")

state = st.session_state.get("local_agent_state")

if state is None:
    prior = st.session_state.get("starting_answers", {})
    st.subheader("Three starting questions")
    st.caption("Use a number of hours. Not sure? You can type “I don't know” or “Prefer not to say.”")
    with st.form("three_starting_questions"):
        st.markdown(f"**1. {STARTING_QUESTIONS[0]}**")
        activity_type = st.text_input("Main activity type", value=prior.get("activity_type", ""), placeholder="e.g. soccer club, volunteering, or none")
        activity_hours = st.text_input("Activity hours per week", value=prior.get("activity_hours", ""), placeholder="e.g. 4")

        st.divider()
        st.markdown(f"**2. {STARTING_QUESTIONS[1]}**")
        class_hours = st.text_input("Scheduled class hours per week", value=prior.get("class_hours", ""), placeholder="e.g. 15")
        weekday_study = st.text_input("Study hours on a typical weekday, outside class", value=prior.get("weekday_study_hours", ""), placeholder="e.g. 2")
        weekend_study = st.text_input("Study hours on a typical weekend day, outside class", value=prior.get("weekend_study_hours", ""), placeholder="e.g. 3")

        st.divider()
        st.markdown(f"**3. {STARTING_QUESTIONS[2]}**")
        sleep_hours = st.text_input("Average sleep hours per night", value=prior.get("sleep_hours", ""), placeholder="e.g. 7.5")
        submitted = st.form_submit_button("Keep going", type="primary", use_container_width=True)

    if submitted:
        raw = {
            "activity_type": activity_type, "activity_hours": activity_hours,
            "class_hours": class_hours, "weekday_study_hours": weekday_study,
            "weekend_study_hours": weekend_study, "sleep_hours": sleep_hours,
        }
        try:
            baseline = validate_baseline(raw)
            st.session_state["starting_answers"] = raw
            st.session_state["local_agent_state"] = start_agent(baseline)
            st.rerun()
        except ValueError as error:
            st.error(str(error))

else:
    answered = len(state["answers"])
    if state["status"] == "asking":
        st.caption(f"Starting questions: 3 complete · Deeper follow-up: {answered + 1} of approximately 8–10")
    else:
        st.caption(f"All topics addressed · {3 + answered} questions total ({answered} deeper follow-ups)")

    with st.expander("Your three starting answers"):
        for key, detail in state["baseline"]["fields"].items():
            value = detail["value"] if detail["status"] == "answered" else detail["status"].replace("_", " ").title()
            suffix = f" {detail['unit']}" if detail["status"] == "answered" and detail["unit"] else ""
            st.write(f"**{BASELINE_SPECS[key]['label']}:** {value}{suffix}")

    for message in state["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if state["status"] == "asking":
        with st.form(f"deep_answer_{answered}", clear_on_submit=True):
            if state["current_question_id"] == "wellbeing_rating":
                reply = st.text_input("Your 0–10 rating", placeholder="e.g. 7")
            else:
                reply = st.text_area("Your answer", max_chars=800, placeholder="A few sentences are enough.")
            sent = st.form_submit_button("Send Answer", type="primary", use_container_width=True)
        if sent:
            try:
                st.session_state["local_agent_state"] = answer_question(state, reply)
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        if st.button("Prefer not to answer this question"):
            st.session_state["local_agent_state"] = answer_question(state, "Prefer not to say")
            st.rerun()

    else:
        record = structured_record(state)
        st.subheader("Review your information")
        st.write("You're all set. Take a quick look, then see your result.")
        with st.expander("Preview complete structured record"):
            st.json(record)
        if st.button("See my result", type="primary", use_container_width=True):
            try:
                baseline = baseline_for_demo_personality(record)
                result = (
                    {"status": "demo_personality", "personality": assign_local_demo_personality(baseline)}
                    if baseline else {"status": "insufficient_data", "personality": None}
                )
                result["analysis"] = analyze_record(record)
                result["football_match"] = (
                    match_football_identity(result["personality"]) if result["personality"] else None
                )
                result["gemini"] = {"status": "not_requested"}
                st.session_state["latest_submission"] = save_collection_submission(record, state["messages"], result)
                st.switch_page("views/result.py")
            except (OSError, sqlite3.Error):
                st.error("Unable to save your answers locally. Please try again.")

    if st.button("Change Starting Answers / Start Over"):
        st.session_state.pop("local_agent_state", None)
        st.session_state.pop("latest_submission", None)
        st.rerun()

st.caption("This is a fun, rule-based demo — not a real assessment.")
