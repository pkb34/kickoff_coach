"""Football personality result and future agent placeholders."""

from __future__ import annotations

import streamlit as st

from engine import PERSONALITIES, assign_demo_personality
from gaffer import get_gaffer_advice


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
st.write("Ask The Gaffer for an encouraging, non-clinical study-habit and wellbeing briefing based on your confirmed check-in.")

advice_key = f"gaffer_advice_{submission['id']}"
if st.button("Ask The Gaffer for advice", type="primary", disabled=personality is None):
    with st.spinner("The Gaffer is reviewing the match tape..."):
        st.session_state[advice_key] = get_gaffer_advice(submission["record"], personality)

if advice_key in st.session_state:
    advice = st.session_state[advice_key]
    st.success(advice["text"])
    st.caption(f"Advice provider: {advice['provider']}. This is supportive guidance, not medical, mental-health, or academic advice.")

st.subheader("Future Predictions")
gpa, sleep, wellbeing = st.columns(3)
gpa.metric("GPA", "Coming soon")
sleep.metric("Sleep Time", "Coming soon")
wellbeing.metric("Wellbeing", "Coming soon")
st.caption("No GPA, sleep, or wellbeing prediction is calculated in this version.")

st.subheader("Need Help?")
st.write("If you feel overwhelmed or your sleep and workload are consistently difficult to manage, consider reaching out to someone you trust or a campus support resource.")

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
