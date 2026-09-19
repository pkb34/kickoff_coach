"""WCPT three-page Streamlit application."""

from __future__ import annotations

import streamlit as st

from storage import migrate_legacy_results


st.set_page_config(page_title="WCPT · World Cup Personality Test", page_icon="⚽", layout="centered")

migrate_legacy_results()

st.html("""
<style>
[data-testid="stAppViewContainer"] {
    background-image: linear-gradient(rgba(6, 29, 14, 0.12), rgba(6, 29, 14, 0.28)), url("/app/static/soccer_background.png");
    background-position: center center;
    background-size: cover;
    background-attachment: fixed;
}
[data-testid="stMainBlockContainer"] {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 22px;
    box-shadow: 0 18px 55px rgba(0, 24, 12, 0.25);
    margin: 28px auto 48px;
    padding: 28px 42px 42px;
}
[data-testid="stHeader"] { background: transparent; }
@media (max-width: 720px) {
    [data-testid="stMainBlockContainer"] {
        margin: 12px 10px 24px;
        padding: 18px 20px 28px;
    }
}
</style>
""")

welcome = st.Page("views/welcome.py", title="Welcome", url_path="welcome", default=True)
quiz = st.Page("views/quiz.py", title="Information Check", url_path="quiz")
result = st.Page("views/result.py", title="Result", url_path="result")

st.navigation([welcome, quiz, result], position="hidden").run()
