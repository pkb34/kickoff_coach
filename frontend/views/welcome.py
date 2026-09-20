"""Welcome page for the World Cup Personality Test."""

from __future__ import annotations

import streamlit as st

from pixel_theme import match_hero
from sound_design import sound_controls

st.caption("HOKIE COMPASS PRESENTS")
st.title("Find your place on the pitch")
st.write("A few playful questions, a football role, and a fresh way to see your style. Ready to meet your match?")
st.html(match_hero())
st.markdown("### Every team has room for your kind of magic ✨")
st.write(
    "Are you the one who keeps everyone connected, spots an opening, or holds steady when things get busy? "
    "Share what studying, activities, and rest are usually like for you. Your answers shape a friendly reflection made for you."
)

left, center, right = st.columns([1, 2, 1])
with center:
    if st.button("Discover My WPTI", type="primary", use_container_width=True):
        st.session_state.pop("local_agent_state", None)
        st.session_state.pop("latest_submission", None)
        st.switch_page("views/quiz.py")

st.caption("WPTI · World Football Personality Type Indicator")
sound_controls("welcome")

# The staff app runs separately and still requires its own password.
st.html('''<div style="text-align:right;margin-top:12px">
<a href="http://127.0.0.1:8513/" target="_blank" rel="noopener noreferrer"
   style="display:inline-block;padding:5px 10px;border-radius:9px;border:1px solid #bfd3b7;
   color:#637b6d;background:#f7f9ed;font:500 12px Fredoka,sans-serif;
   text-decoration:none">Staff access</a></div>''')
