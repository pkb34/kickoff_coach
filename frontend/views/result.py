"""A warm, student-facing reflection with an optional AI game plan."""

from __future__ import annotations

import sqlite3

import streamlit as st

from campus_resources import recommendations, RESOURCE_CATALOG
from databricks_gateway import get_demo_telemetry
from databricks_writer import sync_pending
from engine import PERSONALITIES
from gemini_gateway import generate_briefing, is_configured
from pixel_theme import character_stage
from sound_design import cheer_replay_button, confetti_html, sound_controls
from storage import update_collection_result


def time_text(metrics: dict, key: str) -> str | None:
    interval = metrics.get("time_ranges", {}).get(key)
    if interval:
        low, high = interval
        return f"{low:g}" if low == high else f"{low:g}–{high:g}"
    value = metrics.get(key)
    return f"{value:g}" if value is not None else None


def personal_note(metrics: dict) -> str:
    """Describe reported time use without inferring traits or diagnoses."""
    parts = []
    study = time_text(metrics, "weekly_independent_study_hours")
    activities = time_text(metrics, "weekly_extracurricular_hours")
    sleep = time_text(metrics, "nightly_sleep_hours")
    if study is not None:
        parts.append(f"You shared that you typically study about {study} hours outside class per week")
    if activities is not None:
        parts.append(f"spend about {activities} hours on activities")
    if sleep is not None:
        parts.append(f"and sleep around {sleep} hours a night")
    if not parts:
        return "Thanks for sharing what you could. Your routines are more than any one answer, and this space is here to help you reflect."
    sentence = ", ".join(parts) + "."
    return sentence + " Those parts of your routine deserve room to work together. Small adjustments and moments of rest count, too."


submission = st.session_state.get("latest_submission")
status = submission.get("result", {}).get("status") if submission else None
if status not in ("demo_personality", "insufficient_data"):
    st.title("Your Football Role")
    st.info("Complete the quiz to meet your match.")
    if st.button("Start my check-in", type="primary"):
        st.switch_page("views/quiz.py")
    st.stop()

analysis = submission["result"].get("analysis")
metrics = analysis["metrics"] if analysis else {}
football_match = submission["result"].get("football_match")
if st.session_state.get("celebrated_submission_id") != submission["id"]:
    st.html(confetti_html())
    st.session_state["celebrated_submission_id"] = submission["id"]
st.caption("WPTI · YOUR STORY")
with st.expander("Hear your little stadium celebration"):
    cheer_replay_button()

if status == "demo_personality":
    role = submission["result"]["personality"]
    personality = PERSONALITIES[role]
    wpti = submission["result"].get("wpti")
    display_name = wpti["position"] if wpti else personality["name"]
    portrait, story = st.columns([1, 2], gap="large")
    with portrait:
        st.html(character_stage(display_name, display_name))
    with story:
        st.caption("MEET YOUR PITCH PARTNER")
        st.title(display_name)
        if wpti:
            st.subheader(f"Your WPTI type · {wpti['code']}")
            st.write(" · ".join(wpti["axis_labels"]))
            st.write(wpti["position_note"])
            st.caption("Your four-letter style comes from four answers about how you approach everyday moments. It can change as you do.")
        else:
            st.subheader(personality["tagline"])
        st.write(personal_note(metrics))
        st.success("Your role is a playful match based on this check-in. It is not a fixed label for who you are.")
        if football_match:
            st.markdown(f"**Your national team vibe: {football_match['national_team']}**")
            st.write(football_match["team_description"])
            st.caption(f"[Explore the team's football style]({football_match['team_source']})")
else:
    st.title("Your check-in is complete")
    st.write("Thank you for sharing what you could. We need a few more of the reflection answers to suggest a four-letter type without guessing.")

if analysis:
    st.divider()
    st.subheader("A snapshot of your routine")
    happiness = metrics.get("self_reported_happiness_index")
    happy, study_col, activity_col, sleep_col = st.columns(4)
    happy.metric("How you feel lately", f"{happiness}/100" if happiness is not None else "Not shared")
    study = time_text(metrics, "weekly_independent_study_hours")
    study_col.metric("Study outside class", f"{study} h / week" if study is not None else "Not shared")
    activities = time_text(metrics, "weekly_extracurricular_hours")
    activity_col.metric("Activities", f"{activities} h / week" if activities is not None else "Not shared")
    sleep = time_text(metrics, "nightly_sleep_hours")
    sleep_col.metric("Sleep", f"{sleep} h / night" if sleep is not None else "Not shared")
    st.caption("Time values show the ranges you chose, not exact totals. The feeling score is your own 0–10 answer multiplied by ten; it is not a health measure.")
    progress = metrics.get("self_reported_academic_progress")
    if progress and progress != "Not sure yet":
        if progress == "Feeling behind":
            st.info("Classes feel a little heavy right now. You do not have to untangle everything at once; one conversation with a tutor or classmate can be a kind first step.")
        elif progress == "Keeping up, but stretched":
            st.info("You are keeping up while carrying a lot. A small pause or a clearer study plan may help make room to breathe.")
        else:
            st.info("You said classes feel on track. It is okay to notice what is working and keep some room for rest, too.")

st.divider()
st.subheader("A little more support, just for you")
st.write("Want two small, practical ideas for your next week? Ask for a short AI reflection based on the summary above.")
st.caption("The AI receives a short time-range summary, not your full written answers. You choose whether to ask.")
if analysis and is_configured():
    if st.button("Make my gentle game plan", type="primary", use_container_width=True):
        with st.spinner("Putting a little plan together..."):
            try:
                telemetry = get_demo_telemetry()
                briefing = generate_briefing(analysis, telemetry)
            except (OSError, TypeError, ValueError, KeyError, IndexError):
                briefing = {"status": "unavailable"}
        submission["result"]["gemini"] = briefing
        try:
            update_collection_result(submission["id"], submission["result"])
            st.session_state["databricks_sync_status"] = sync_pending(limit=5)
        except (OSError, ValueError, sqlite3.Error):
            st.warning("Your reflection is ready, but it could not be saved. You can still read it below.")
        st.rerun()
elif analysis:
    st.info("Personalized tips will be available here soon. For now, your check-in and football role are ready.")

briefing = submission["result"].get("gemini", {})
if briefing.get("status") == "generated":
    st.markdown("### A note for you")
    st.write(briefing["summary"])
    st.markdown("### Two little things to try")
    for idea in briefing["suggestions"]:
        st.write(idea)
    st.markdown("### A possible bright moment")
    st.write(briefing["future_moments"])
    st.caption("These are suggestions for reflection, not a prediction or professional assessment.")
elif briefing.get("status") == "unavailable":
    st.warning("Your extra reflection is taking a break right now. Please try again later.")

st.divider()
st.subheader("A few VT places that fit your interests")
st.write("Here are places to explore based on the activities and needs you chose. You decide what feels useful.")
if submission.get("record", {}).get("schema_version") == "2.0":
    for label, url, note in recommendations(submission["record"], analysis):
        st.write(note)
        st.link_button(label, url)
else:
    st.link_button("Browse student organizations", RESOURCE_CATALOG["organizations"][1])
with st.expander("More support, whenever you want it"):
    st.write("If you would like someone to talk to, campus support is available.")
    st.link_button("Cook Counseling Center", RESOURCE_CATALOG["counseling"][1])

back, restart = st.columns(2)
with back:
    if st.button("Back to the start", use_container_width=True):
        st.switch_page("views/welcome.py")
with restart:
    if st.button("Try a new round", use_container_width=True):
        for key in ("latest_submission", "quiz_baseline", "quiz_step", "recommended_questions",
                    "selected_questions", "followup_selection", "collection_state", "local_agent_state",
                    "starting_answers"):
            st.session_state.pop(key, None)
        st.switch_page("views/quiz.py")

sound_controls("result")
