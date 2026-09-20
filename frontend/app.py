"""WCPT three-page Streamlit application."""

from __future__ import annotations

import streamlit as st

from storage import migrate_legacy_results
from pixel_theme import asset_uri


st.set_page_config(page_title="WCPT · World Cup Personality Test", page_icon="⚽", layout="centered")

migrate_legacy_results()

st.html("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #dcedcf;
    background-image: url("PIXEL_BACKGROUND");
    background-position: center center;
    background-size: 560px 560px;
    image-rendering: pixelated;
    background-attachment: fixed;
}
[data-testid="stMainBlockContainer"] {
    background: rgba(255, 253, 246, 0.97);
    border: 3px solid #aac49b;
    border-radius: 8px;
    box-shadow: 8px 8px 0 rgba(110, 145, 102, 0.24);
    margin: 28px auto 48px;
    padding: 28px 42px 42px;
}
.archetype-heading { display: flex; align-items: center; gap: 16px; }
.archetype-heading img { image-rendering: pixelated; flex-shrink: 0; }
.archetype-heading h1 { padding: 0; overflow-wrap: anywhere; }
[data-testid="stBaseButton-primary"] { box-shadow: 3px 3px 0 #b9caaa; }
[data-testid="stHeader"] { background: transparent; }
@media (max-width: 720px) {
    [data-testid="stMainBlockContainer"] {
        margin: 12px 10px 24px;
        padding: 18px 20px 28px;
    }
}
</style>
""".replace("PIXEL_BACKGROUND", asset_uri("cute_soccer_background.png")))

welcome = st.Page("views/welcome.py", title="Welcome", url_path="welcome", default=True)
quiz = st.Page("views/quiz.py", title="Information Check", url_path="quiz")
result = st.Page("views/result.py", title="Result", url_path="result")

st.navigation([welcome, quiz, result], position="hidden").run()
