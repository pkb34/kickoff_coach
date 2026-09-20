"""Football personality, local analysis, and optional Gemini briefing."""

from __future__ import annotations

import sqlite3

import streamlit as st

from engine import PERSONALITIES, assign_demo_personality
from databricks_gateway import get_demo_telemetry
from gemini_gateway import generate_briefing, is_configured
from storage import update_collection_result
from pixel_theme import archetype_heading


submission = st.session_state.get("latest_submission")
status = submission.get("result", {}).get("status") if submission else None
if status not in ("demo_personality", "insufficient_data"):
    st.title("Your Football Personality")
    st.info("Complete the quiz to see your result.")
    if st.button("Go to Quiz", type="primary"):
        st.switch_page("views/quiz.py")
    st.stop()

st.caption("WCPT · YOUR RESULT")
if status == "demo_personality":
    personality_key = submission["result"].get("personality")
    if not personality_key and "answers" in submission:
        personality_key = assign_demo_personality(submission["answers"])
    personality = PERSONALITIES[personality_key]
    st.html(archetype_heading(personality_key, personality["name"]))
    st.subheader(personality["tagline"])
    st.write(personality["description"])
    st.info("This is a fun personality match, not a prediction or a real assessment.")
    if submission.get("record", {}).get("schema_version") == "2.0":
        count = submission["record"]["question_count"]
        st.caption(f"You completed {count['starting']} starting questions and {count['deep']} adaptive follow-ups. This is an illustrative football role, not an assessment.")
    elif submission.get("record"):
        st.caption("The information check was saved as a structured record. This result uses a demo rule.")
    elif submission.get("followups"):
        st.caption(f"You answered {len(submission['followups'])} follow-up questions. They are saved for a future agent; the current personality display uses only page-one answers.")
else:
    personality = None
    st.title("Information Check Complete")
    st.warning("Your record was saved, but some numeric details were unavailable. This demo cannot assign a football personality without inventing answers.")

if submission.get("record"):
    with st.expander("View collected information"):
        st.json(submission["record"])

analysis = submission.get("result", {}).get("analysis")
football_match = submission.get("result", {}).get("football_match")

if analysis:
    st.subheader("Your Week in Numbers")
    metrics = analysis["metrics"]
    study, activities, sleep = st.columns(3)
    study.metric("Study outside class / week", f"{metrics['weekly_independent_study_hours']:g} h" if metrics["weekly_independent_study_hours"] is not None else "Unknown")
    activities.metric("Activities / week", f"{metrics['weekly_extracurricular_hours']:g} h" if metrics["weekly_extracurricular_hours"] is not None else "Unknown")
    sleep.metric("Sleep / night", f"{metrics['nightly_sleep_hours']:g} h" if metrics["nightly_sleep_hours"] is not None else "Unknown")
    with st.expander("How these figures were calculated"):
        for item in analysis["observations"]:
            st.write(item["text"])
        for item in analysis["limitations"]:
            st.caption(item)

if football_match:
    st.divider()
    st.subheader("Your Player Analogy")
    st.markdown(f"### {football_match['player']}")
    st.write(football_match["player_explanation"])
    st.caption(f"[Player source]({football_match['player_source']})")
    st.caption("These football matches are illustrative analogies, not measured personality traits.")

st.divider()
st.subheader("Ask The Gaffer")
st.write("Want a little encouragement for the week ahead? The Gaffer can make you a simple game plan.")
st.caption("Only a small summary is shared when you click. Your full answers stay here.")
if analysis and is_configured():
    if st.button("Get my game plan", type="primary", use_container_width=True):
        with st.spinner("The Gaffer is thinking..."):
            try:
                telemetry = get_demo_telemetry()
            except (OSError, TypeError, ValueError):
                telemetry = {
                    "status": "unavailable",
                    "message": "Databricks could not load the demo telemetry right now.",
                }
            try:
                briefing = generate_briefing(analysis, telemetry)
            except (OSError, TypeError, ValueError, KeyError, IndexError):
                briefing = {
                    "status": "unavailable",
                    "message": "The Gaffer could not make a game plan right now. Please try again in a moment.",
                }
        if telemetry.get("status") == "available":
            briefing["databricks_source"] = telemetry["source"]
        elif telemetry.get("status") == "unavailable":
            briefing["databricks_note"] = telemetry.get("message", "Databricks telemetry was unavailable, so this plan uses your quiz answers only.")
        submission["result"]["gemini"] = briefing
        try:
            update_collection_result(submission["id"], submission["result"])
        except (OSError, ValueError, sqlite3.Error):
            st.warning("The briefing was generated but could not be saved locally.")
        st.rerun()
elif analysis:
    st.info(
        "The Gaffer isn't connected yet. Add GEMINI_API_KEY to "
        "frontend/.streamlit/secrets.toml, then restart the app."
    )

briefing = submission.get("result", {}).get("gemini", {})
if briefing.get("status") == "generated":
    if briefing.get("databricks_source"):
        st.caption(f"Personalized with approved synthetic telemetry from {briefing['databricks_source']}.")
    elif briefing.get("databricks_note"):
        st.caption(briefing["databricks_note"])
    st.write(briefing["future_moments"])
    st.subheader("A little encouragement from The Gaffer")
    st.write(briefing["summary"])
    for idea in briefing["suggestions"]:
        st.write(f"• {idea}")
    st.caption(f"Drafted by {briefing['model']}. Review it as a suggestion, not an assessment.")
elif briefing.get("status") == "unavailable":
    st.warning(briefing["message"])

st.subheader("One quick note")
st.write("This app isn't trying to predict your future — it's here to help you reflect on your week.")

st.subheader("Need a hand?")
st.write("If things feel tough, talking with someone you trust or a campus resource can be a great next step.")

st.divider()
back, restart = st.columns(2)
with back:
    if st.button("Back to Information Check", use_container_width=True):
        st.switch_page("views/quiz.py")
with restart:
    if st.button("Start Again", type="primary", use_container_width=True):
        for key in (
            "latest_submission", "welcome_quote", "quiz_baseline", "quiz_step",
            "recommended_questions", "selected_questions", "followup_selection", "collection_state",
            "local_agent_state", "starting_answers",
        ):
            st.session_state.pop(key, None)
        st.switch_page("views/welcome.py")
