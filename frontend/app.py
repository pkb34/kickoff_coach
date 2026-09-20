"""WCPT three-page Streamlit application."""

from __future__ import annotations

import streamlit as st

from storage import migrate_legacy_results
from pixel_theme import asset_uri
from sound_design import play_pending_event


st.set_page_config(page_title="WPTI · Find Your Football Role", page_icon="🌿", layout="wide")

migrate_legacy_results()

st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&display=swap');
:root { --wpti-font: 'Fredoka', 'Comic Sans MS', 'Trebuchet MS', sans-serif; }
[data-testid="stAppViewContainer"] {
    background-color: #d8f3dc;
    background-image: linear-gradient(135deg,rgba(217,246,255,.38),rgba(250,255,214,.16) 55%,rgba(185,242,194,.35)),url("PIXEL_BACKGROUND");
    background-position: center center;
    background-size: 560px 560px;
    image-rendering: pixelated;
    background-attachment: fixed;
}
[data-testid="stMainBlockContainer"] {
    background: rgba(255, 253, 238, 0.97);
    border: 4px solid #78c7a2;
    border-radius: 22px;
    box-shadow: 9px 9px 0 #94d7bf;
    margin: 28px auto 48px;
    padding: 30px clamp(20px,4vw,60px) 48px;
    max-width: 1280px;
    animation: page-arrive .6s cubic-bezier(.22,.7,.25,1) both;
}
.stApp { color:#264b3b; }
.stApp p,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp label,
.stApp button,.stApp input,.stApp textarea,.stApp [data-testid="stMetricValue"],
.stApp [data-testid="stMetricLabel"],.stApp small { font-family:var(--wpti-font) !important; }
.stApp p,.stApp label { font-size:1.05rem; line-height:1.55; }
h1,h2,h3 { letter-spacing:-.02em; }
h1 { color:#205d42; font-weight:700; }
[data-testid="stForm"] { background:#fff9e1; border:3px solid #8ecb9e; border-radius:16px; padding:20px; box-shadow:6px 6px 0 #d0e9bf; }
[data-testid="stRadio"] [role="radiogroup"] { flex-wrap:wrap !important; overflow-x:visible; gap:3px 4px; padding:7px 2px 10px; }
[data-testid="stRadio"] [role="radiogroup"] label { flex:0 0 auto; border-radius:15px; padding:10px 15px; background:#fffdf1; margin:2px 5px 4px 0; border:3px solid #a9cc9e; box-shadow:3px 3px 0 #d2e5bf; white-space:nowrap; }
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) { background:#ffe5a0; border-color:#e89960; box-shadow:2px 3px 0 #d9ad69; }
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p { color:#6d4834; font-weight:700; }
[data-testid="stRadio"] [role="radiogroup"] label:has(input:focus-visible) { outline:3px solid #366a56; outline-offset:2px; }
[data-testid="stRadio"] [role="radiogroup"] label p { font-family:var(--wpti-font) !important; font-size:1.13rem; margin:0; }
[data-testid="stRadio"] [role="radiogroup"] label [data-testid="stMarkdownContainer"] { white-space:nowrap; }
[data-testid="stSelectbox"] > div > div { border-radius:17px; min-height:51px; background:#fffef5; border-color:#c9ddbd; }
[data-testid="stBaseButton-primary"] { border-radius:18px; background:#f18b59; border-color:#d8744c; color:#fff; font-weight:700; box-shadow:4px 5px 0 #a5d7a0; min-height:60px; }
[data-testid="stBaseButton-secondary"] { border-radius:18px; min-height:52px; }
.stApp button p { font-size:1.25rem !important; font-weight:700; }
.stApp button:hover { transform:translateY(-2px); transition:transform .15s ease,box-shadow .15s ease; }
[data-testid="stMetricValue"] { font-size:1.45rem !important; line-height:1.25; }
[data-testid="stMetricLabel"] { font-size:.98rem !important; }
[data-testid="stAlert"] [data-testid="stAlertIcon"] { display:none !important; }
[data-testid="stAlert"] svg { display:none !important; }
.wpti-conversation { border-radius:20px; padding:14px 18px; margin:3px 0 6px; max-width:100%; border:3px solid #b9d7a5; background:#f6faed; box-shadow:4px 4px 0 #e3edcd; }
.wpti-conversation.student { margin-left:auto; background:#fff4e6; border-color:#f2dfc5; }
.wpti-conversation small,.wpti-side-note small { color:#648977; font-size:.75rem; font-weight:700; letter-spacing:.09em; }
.wpti-conversation p { margin:.35em 0 0; }
.wpti-side-note { padding:10px 14px; border-radius:17px; background:#eaf4d9; border:2px solid #c4dcb0; margin:3px 0 8px; }
.wpti-side-note p { margin:0; font-size:.97rem; }
.wpti-question-art { width:100%; max-width:190px; aspect-ratio:1.18; margin:3px auto 9px;
  background-size:400% 400%; border-radius:12px; border:3px solid #98ba91;
  box-shadow:5px 5px 0 #d3e5be; image-rendering:pixelated;
  animation:wpti-card-bob 3.5s ease-in-out infinite; }
[data-testid="stMainBlockContainer"]:has(.wpti-character-stage) { background:linear-gradient(135deg,#fff5cf 24%,#e2f8db 67%,#d9f4ff 100%); }
[data-testid="stMainBlockContainer"]:has(.wpti-match-film) { max-width:1700px; }
@keyframes page-arrive { from { opacity:0; transform:translateX(16px) } to { opacity:1; transform:translateX(0) } }
@keyframes wpti-card-bob { 0%,100% { transform:translateY(0) rotate(-1deg) } 50% { transform:translateY(-6px) rotate(1deg) } }
.archetype-heading { display: flex; align-items: center; gap: 16px; }
.archetype-heading img { image-rendering: pixelated; flex-shrink: 0; }
.archetype-heading h1 { padding: 0; overflow-wrap: anywhere; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], footer { display:none !important; }
@media (max-width: 720px) {
    [data-testid="stMainBlockContainer"] {
        margin: 12px 10px 24px;
        padding: 18px 20px 28px;
    }
    .wpti-conversation { max-width:100%; }
}
@media (prefers-reduced-motion:reduce) { [data-testid="stMainBlockContainer"],.wpti-question-art { animation:none; } .stApp button:hover { transform:none; } }
</style>
""".replace("PIXEL_BACKGROUND", asset_uri("cute_soccer_background.png")))

play_pending_event()

welcome = st.Page("views/welcome.py", title="Welcome", url_path="welcome", default=True)
quiz = st.Page("views/quiz.py", title="Information Check", url_path="quiz")
result = st.Page("views/result.py", title="Result", url_path="result")

st.navigation([welcome, quiz, result], position="hidden").run()
