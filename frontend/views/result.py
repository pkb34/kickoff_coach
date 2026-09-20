"""Football personality, local analysis, and optional Gemini briefing."""

from __future__ import annotations

import sqlite3

import streamlit as st

from engine import PERSONALITIES, assign_demo_personality
from gemini_gateway import generate_briefing, is_configured
from storage import update_collection_result


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
    st.title(f"{personality['icon']} {personality['name']}")
    st.subheader(personality["tagline"])
    st.write(personality["description"])
    st.info("This is an illustrative personality match for the prototype. It is not an AI assessment or a prediction.")
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

left, right = st.columns(2)
left.metric("Record ID", submission["id"])
right.metric("Personality", personality["name"] if personality else "Not assigned")

if submission.get("record"):
    with st.expander("View collected information"):
        st.json(submission["record"])

analysis = submission.get("result", {}).get("analysis")
football_match = submission.get("result", {}).get("football_match")

st.divider()
st.subheader("Your Happiness Index")
if analysis:
    happiness = analysis["metrics"]["self_reported_happiness_index"]
    st.metric("Self-reported happiness", f"{happiness}/100" if happiness is not None else "Not reported")
    st.caption("This is your own seven-day 0–10 rating multiplied by ten. It is not a clinical measure or a prediction.")
else:
    st.write("A self-reported happiness rating is not available for this earlier record.")

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
    st.subheader("Your National Team Match")
    st.markdown(f"### {football_match['national_team']}")
    st.write(football_match["team_style"])
    st.write(football_match["team_description"])
    st.caption(f"[Football style source]({football_match['team_source']})")

    st.subheader("Your Player Analogy")
    st.markdown(f"### {football_match['player']}")
    st.write(football_match["player_explanation"])
    st.caption(f"[Player source]({football_match['player_source']})")
    st.caption("These football matches are illustrative analogies, not measured personality traits.")

st.divider()
st.subheader("Future Moments")
st.write("Gemini can draft a possible next-week moment from a compact summary of your reported time and self-rating. This is a scenario, not a forecast.")
st.caption("The Gaffer is your optional football-themed briefing voice.")
st.caption("Only numeric summary fields and answer-availability flags are sent when you click. Free-text answers and the conversation transcript stay local.")
if analysis and is_configured():
    if st.button("Ask The Gaffer for Gemini Briefing", type="primary", use_container_width=True):
        with st.spinner("Drafting your briefing..."):
            briefing = generate_briefing(analysis)
        submission["result"]["gemini"] = briefing
        try:
            update_collection_result(submission["id"], submission["result"])
        except (OSError, ValueError, sqlite3.Error):
            st.warning("The briefing was generated but could not be saved locally.")
        st.rerun()
elif analysis:
    st.info("Gemini is not configured on this server. The local analysis and football match remain available.")

briefing = submission.get("result", {}).get("gemini", {})
if briefing.get("status") == "generated":
    st.write(briefing["future_moments"])
    st.subheader("Advice")
    st.write(briefing["summary"])
    for idea in briefing["suggestions"]:
        st.write(f"• {idea}")
    st.caption(f"Drafted by {briefing['model']}. Review it as a suggestion, not an assessment.")
elif briefing.get("status") == "unavailable":
    st.warning(briefing["message"])

st.subheader("Future Predictions")
st.write("No numerical future outcome is predicted from one check-in.")

st.subheader("Need Help?")
st.write("Reserved for future support guidance and referrals.")

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
