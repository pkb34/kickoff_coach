"""Welcome page for the World Cup Personality Test."""

from __future__ import annotations

import random

import streamlit as st


QUOTES = [
    (
        "The Champions League is something amazing. It's every footballer's dream.",
        "Sadio Mané",
        "https://www.uefa.com/uefachampionsleague/news/027a-163de8844515-8671f00400fc-1000--sadio-mane-on-winning-the-champions-league-with-liverpool/",
    ),
    (
        "It's a dream to be playing football for a living.",
        "Harry Kane",
        "https://www.uefa.com/uefachampionsleague/news/0296-1d064b4913f9-b763898d0b25-1000--harry-kane-interview-my-playing-style-dropping-deep-taking-p/",
    ),
    (
        "I think football chose me.",
        "Patrizia Panico",
        "https://www.uefa.com/news-media/news/022d-0e16384252aa-d89f018aa580-1000--panico-i-didn-t-choose-this-sport-football-chose-me/",
    ),
]

if "welcome_quote" not in st.session_state:
    st.session_state["welcome_quote"] = random.choice(QUOTES)

quote, player, source = st.session_state["welcome_quote"]

st.write("")
st.write("")
st.caption("HOKIE COMPASS PRESENTS")
st.title("⚽ World Cup Personality Test")
st.subheader("What kind of player are you?")
st.write("Answer a short, adaptive information check about your week. Your answers determine which details we ask about next before showing an illustrative football personality.")

st.divider()
st.markdown(f'> “{quote}”')
st.caption(f"— [{player}]({source})")
st.divider()

left, center, right = st.columns([1, 2, 1])
with center:
    if st.button("Start WCPT", type="primary", use_container_width=True):
        st.switch_page("views/quiz.py")

st.caption("WCPT = World Cup Personality Test · For demonstration only")
