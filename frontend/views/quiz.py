"""Three starting questions followed by local adaptive follow-ups."""

from __future__ import annotations

import sqlite3
import json
from html import escape

import streamlit as st

from analysis_agent import analyze_record
from databricks_writer import sync_pending
from football_matches import match_football_identity
from local_question_agent import HOUR_BUCKETS, STARTING_QUESTIONS, answer_question, start_agent, structured_record, validate_baseline
from pixel_theme import question_scene_html
from sound_design import sound_controls
from storage import save_collection_submission
from voice_gateway import voice_answer
from gemini_gateway import is_configured
from wpti_types import BEHAVIOR_CHOICES, infer_profile_from_record


def hour_picker(label: str, key: str, prior: str) -> str:
    """Choose one short time band without horizontal scrolling."""
    options = [item[0] for item in HOUR_BUCKETS[key]] + ["Not sure", "Skip"]
    previous = prior
    if prior and prior.replace(".", "", 1).isdigit():
        number = float(prior)
        previous = next((name for name, low, high in HOUR_BUCKETS[key] if low <= number <= high), prior)
    previous = {"I don't know": "Not sure", "Prefer not to say": "Skip"}.get(previous, previous)
    choice = st.radio(label, options, index=options.index(previous) if previous in options else None,
                      horizontal=True)
    return {"Not sure": "I don't know", "Skip": "Prefer not to say"}.get(choice, choice) if choice else ""


def picture_question(question_id: str, title: str, comfort: str, render):
    question_col, picture_col = st.columns([4, 1.35], gap="small", vertical_alignment="center")
    with question_col:
        st.markdown(f"**{title}**")
        st.caption(comfort)
        value = render()
    with picture_col:
        st.html(question_scene_html(question_id))
    return value


st.caption("WPTI · YOUR LITTLE CHECK-IN")
st.title("Let's meet the you behind the jersey ✨")
st.write("Tap what feels closest. There are no perfect answers here, promise.")
st.caption("Completed check-ins are saved locally and queued for the team's Databricks workspace. Please leave out names and other identifying details.")

SIDE_NOTES = {
    "activity_balance": "Busy days can pull you in two directions. It is okay to protect your energy, and it is okay to be curious too.",
    "class_experience": "Some ideas take a few tries to click. That says nothing bad about you.",
    "study_routine": "Starting small still counts. You do not need a perfect study session to make progress.",
    "learning_barrier": "A tough class is a challenge you are facing, not a description of who you are.",
    "academic_progress": "Feeling behind can happen to anyone. You deserve a little help before things pile up.",
    "sleep_quality": "Different bodies need different rhythms. Your own sense of rest matters too.",
    "sleep_barrier": "Rest can be messy sometimes. You deserve gentleness while you work out what helps.",
    "wellbeing_rating": "Whatever number comes to mind, you are more than a number. A hard day does not have to be carried alone.",
    "support_preference": "Asking for help is allowed, even when you are not sure what kind would help yet.",
}

state = st.session_state.get("local_agent_state")

if state is None:
    prior = st.session_state.get("starting_answers", {})
    st.subheader("First, your everyday rhythm 🌱")
    st.caption("Choose the closest little circle. Not sure is an answer too.")
    with st.form("three_starting_questions"):
        st.markdown(f"### 1. {STARTING_QUESTIONS[0]}")
        activity_options = ["None", "Sports or movement", "Arts or music", "Volunteering", "Academic or career club", "Student organization", "Other activity", "I don't know", "Prefer not to say"]
        old_activity = prior.get("activity_type", "")
        activity_type = picture_question("activity_type", "What lights up your time outside class?", "Quiet days count too. You do not need a packed calendar to belong here.",
            lambda: st.radio("Your main activity", activity_options, index=activity_options.index(old_activity) if old_activity in activity_options else None, horizontal=True))
        activity_hours = picture_question("activity_hours", "How many hours does that usually take in a week?", "A little time for something you love still counts.",
            lambda: hour_picker("Activity hours each week", "activity_hours", prior.get("activity_hours", "")))

        st.divider()
        st.markdown(f"### 2. {STARTING_QUESTIONS[1]}")
        class_hours = picture_question("class_hours", "How many hours of class do you usually have in a week?", "Some schedules feel full; others leave more room. Both are real student lives.",
            lambda: hour_picker("Class hours each week", "class_hours", prior.get("class_hours", "")))
        weekday_study = picture_question("weekday_study_hours", "Outside class, how long do you study on a usual weekday?", "A gentle pace can be a good pace. Pick what really fits you.",
            lambda: hour_picker("Weekday study hours per day", "weekday_study_hours", prior.get("weekday_study_hours", "")))
        weekend_study = picture_question("weekend_study_hours", "And on a usual weekend day?", "Weekends can hold both rest and work. Yours gets to have its own rhythm.",
            lambda: hour_picker("Weekend study hours per day", "weekend_study_hours", prior.get("weekend_study_hours", "")))

        st.divider()
        st.markdown(f"### 3. {STARTING_QUESTIONS[2]}")
        sleep_hours = picture_question("sleep_hours", "How long do you usually sleep each night?", "Everybody's rest looks a little different. Pick what feels closest for your body.",
            lambda: hour_picker("Usual sleep per night", "sleep_hours", prior.get("sleep_hours", "")))
        submitted = st.form_submit_button("Let's keep going", type="primary", use_container_width=True)

    if submitted:
        raw = {
            "activity_type": activity_type or "", "activity_hours": activity_hours,
            "class_hours": class_hours, "weekday_study_hours": weekday_study,
            "weekend_study_hours": weekend_study,
            "sleep_hours": sleep_hours,
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
        st.caption(f"Your little chat · {answered + 1} of about 7–8")
    else:
        st.caption(f"All topics addressed · {3 + answered} questions total ({answered} deeper follow-ups)")

    if state["status"] == "asking":
        question_id = state["current_question_id"]
        previous_messages = state["messages"][:-1]
        if previous_messages:
            with st.expander("Earlier in our conversation"):
                for message in previous_messages:
                    who = "YOUR COACH" if message["role"] == "assistant" else "YOU"
                    kind = "coach" if message["role"] == "assistant" else "student"
                    st.html(f'<div class="wpti-conversation {kind}"><small>{who}</small><p>{escape(message["content"])}</p></div>')
        question_column, note_column = st.columns([3, 1], gap="small")
        with question_column:
            st.html(f'<div class="wpti-conversation coach"><small>YOUR COACH</small><p>{escape(state["messages"][-1]["content"])}</p></div>')
            st.html(f'<div class="wpti-side-note"><p>{escape(SIDE_NOTES.get(question_id, "Take your time. A little answer is enough."))}</p></div>')
            with st.form(f"deep_answer_{answered}", clear_on_submit=True):
                if question_id in BEHAVIOR_CHOICES:
                    options = [text for text, _ in BEHAVIOR_CHOICES[question_id]]
                    reply = st.radio("What feels closest?", options, index=None, horizontal=True) or ""
                elif question_id == "academic_progress":
                    options = ["Feeling on track", "Keeping up, but stretched", "Feeling behind", "Not sure yet"]
                    reply = st.radio("How classes feel", options, index=None, horizontal=True) or ""
                elif question_id == "wellbeing_rating":
                    options = [str(i) for i in range(11)]
                    reply = st.radio("Your 0–10 feeling", options, index=None, horizontal=True) or ""
                elif question_id == "sleep_quality":
                    options = ["Usually rested", "Some days rested, some days tired", "Usually tired", "I don't know"]
                    reply = st.radio("How rested do you feel?", options, index=None, horizontal=True) or ""
                else:
                    options = None
                    reply = st.text_area("Tell me in your own words", max_chars=800, placeholder="A sentence or two is plenty.", height=90)
                sent = st.form_submit_button("Send my answer", type="primary", use_container_width=True)
        with note_column:
            st.html(question_scene_html(question_id))
        if options is None:
            with st.expander("🎙️ Prefer speaking? Answer this open question by voice"):
                if is_configured():
                    st.caption("Your recording goes to Gemini for this answer and is not saved as audio. Writing is always okay too.")
                    spoken = json.dumps(state["messages"][-1]["content"])
                    st.iframe(
                        '<button id="hear" style="font:600 17px Fredoka,sans-serif;border:2px solid #98c7aa;'
                        'border-radius:999px;background:#f7ffed;color:#315a48;padding:9px 18px;cursor:pointer">'
                        '🔊 Hear this question</button>'
                        f'<script>document.getElementById("hear").onclick=()=>{{speechSynthesis.cancel();'
                        f'const u=new SpeechSynthesisUtterance({spoken});u.rate=.9;speechSynthesis.speak(u)}};</script>',
                        height=52,
                    )
                    audio = st.audio_input("Record a short answer", key=f"voice_{answered}_{question_id}")
                    if st.button("Send my voice answer", disabled=audio is None):
                        try:
                            with st.spinner("Listening..."):
                                heard = voice_answer(audio.getvalue(), state["messages"][-1]["content"])
                            st.session_state["local_agent_state"] = answer_question(state, heard)
                            st.session_state["sound_event"] = "tap"
                            st.rerun()
                        except ValueError as error:
                            st.warning(str(error))
                else:
                    st.caption("Voice needs the Gemini key on this device. Writing still works.")
        if sent:
            try:
                updated = answer_question(state, reply)
                st.session_state["local_agent_state"] = updated
                if updated["status"] == "asking":
                    st.session_state["sound_event"] = "tap"
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        if st.button("Prefer not to answer this question"):
            updated = answer_question(state, "Prefer not to say")
            st.session_state["local_agent_state"] = updated
            if updated["status"] == "asking":
                st.session_state["sound_event"] = "tap"
            st.rerun()

    else:
        record = structured_record(state)
        if st.session_state.get("latest_submission") is None:
            try:
                wpti = infer_profile_from_record(record)
                result = ({"status": "demo_personality", "personality": wpti["art_role"], "wpti": wpti}
                          if wpti else {"status": "insufficient_data", "personality": None, "wpti": None})
                result["analysis"] = analyze_record(record)
                result["football_match"] = (
                    match_football_identity(result["personality"]) if result["personality"] else None
                )
                result["gemini"] = {"status": "not_requested"}
                st.session_state["latest_submission"] = save_collection_submission(record, state["messages"], result)
                st.session_state["databricks_sync_status"] = sync_pending(limit=5)
            except (OSError, sqlite3.Error):
                st.error("Unable to save your answers locally. Please try again.")
                st.stop()
        st.session_state["sound_event"] = "cheer"
        st.switch_page("views/result.py")

    if st.button("Change Starting Answers / Start Over"):
        st.session_state.pop("local_agent_state", None)
        st.session_state.pop("latest_submission", None)
        st.rerun()

sound_controls("quiz")
