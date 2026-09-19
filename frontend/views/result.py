"""Football personality result and future agent placeholders."""

from __future__ import annotations

import streamlit as st

from engine import PERSONALITIES, assign_demo_personality


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
    if submission.get("record"):
        st.caption("The information check was saved as a structured record. The demo personality uses only the six numeric baseline fields.")
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

st.divider()
st.subheader("Advice")
st.write("Reserved for future personalized advice from the agent.")

st.subheader("Future Predictions")
gpa, sleep, wellbeing = st.columns(3)
gpa.metric("GPA", "Coming soon")
sleep.metric("Sleep Time", "Coming soon")
wellbeing.metric("Wellbeing", "Coming soon")
st.caption("No GPA, sleep, or wellbeing prediction is calculated in this version.")

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
        ):
            st.session_state.pop(key, None)
        st.switch_page("views/welcome.py")
