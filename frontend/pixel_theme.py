"""Local, crisp pixel artwork shared by the app shell and result page."""

from base64 import b64encode
from functools import lru_cache
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "static"
ROLES = {"midfielder", "captain", "penalty_striker", "defender"}
POSITION_TILES = {
    "Goalkeeper": (0, 0), "Center Back": (1, 0), "Fullback": (2, 0),
    "Central Midfielder": (3, 0), "Attacking Midfielder": (0, 1),
    "Winger": (1, 1), "Striker": (2, 1), "Captain": (3, 1),
}
QUESTION_TILES = {
    "activity_type": (0, 0), "activity_hours": (1, 0), "class_hours": (2, 0),
    "weekday_study_hours": (3, 0), "weekend_study_hours": (0, 1),
    "sleep_hours": (1, 1), "activity_balance": (2, 1),
    "activity_tradeoff": (2, 1), "class_experience": (3, 1),
    "study_routine": (0, 2), "learning_barrier": (1, 2),
    "academic_progress": (2, 0),
    "sleep_quality": (2, 2), "wellbeing_rating": (3, 2),
    "campus_belonging": (0, 3), "connection_step": (0, 3),
    "support_preference": (1, 3), "study_variation": (2, 3),
    "sleep_barrier": (3, 3),
}
CHIBI_ART = {
    "midfielder": "chibi/box_to_box_midfielder.png",
    "captain": "chibi/playmaker_captain.png",
    "penalty_striker": "chibi/penalty_striker.png",
    # The earlier defensive sprite is a sweeper-keeper, our goalkeeper-style defender.
    "defender": "chibi/sweeper_keeper.png",
}


@lru_cache(maxsize=16)
def asset_uri(filename: str) -> str:
    path = ASSETS / filename
    mime_type = "image/png" if path.suffix.lower() == ".png" else "image/svg+xml"
    return f"data:{mime_type};base64," + b64encode(path.read_bytes()).decode("ascii")


def archetype_image_path(role: str) -> Path:
    """Return the saved chibi portrait for a known football personality."""
    if role not in ROLES:
        raise ValueError("Unknown archetype artwork")
    return ASSETS / CHIBI_ART[role]


def archetype_heading(role: str, name: str) -> str:
    if role not in ROLES:
        raise ValueError("Unknown archetype artwork")
    image_uri = asset_uri(CHIBI_ART[role])
    return (
        '<div class="archetype-heading">'
        f'<img src="{image_uri}" alt="{escape(name)} chibi soccer teammate" width="100" height="110">'
        f'<h1>{escape(name)}</h1></div>'
    )


def match_hero() -> str:
    """Show the entire original match illustration without cropping players."""
    image_uri = "/app/static/wpti_match_scene.png"
    return f"""
<style>
.wpti-match-film {{
  position:relative; width:100%; aspect-ratio:1672 / 941; overflow:hidden;
  border:5px solid #fff2bf; border-radius:27px; background:#74c9ed;
  box-shadow:0 20px 50px rgba(18,101,93,.22);
}}
.wpti-match-scene {{
  display:block; width:100%; height:100%; object-fit:contain;
}}
.wpti-match-film::after {{
  content:""; position:absolute; inset:0;
  background:linear-gradient(180deg,rgba(255,255,255,.03),transparent 60%,rgba(25,112,40,.04));
  pointer-events:none;
}}
</style>
<div class="wpti-match-film">
  <img class="wpti-match-scene" src="{image_uri}"
       alt="Four full-body cartoon football players on a sunny green pitch" width="1672" height="941">
</div>"""


def character_stage(role: str, name: str) -> str:
    """Animated card showing one of eight separate role characters."""
    legacy = {"defender": "Goalkeeper", "midfielder": "Central Midfielder",
              "captain": "Captain", "penalty_striker": "Striker"}
    position = legacy.get(role, role)
    if position not in POSITION_TILES:
        raise ValueError("Unknown archetype artwork")
    image_uri = asset_uri("chibi/eight_roles.png")
    col, row = POSITION_TILES[position]
    colors = {
        "Goalkeeper": ("#e7f0fb", "#76a9ca"), "Center Back": ("#e9f5e7", "#8ab88c"),
        "Fullback": ("#f7efe2", "#d9ae70"), "Central Midfielder": ("#e9eefc", "#8c9dd2"),
        "Attacking Midfielder": ("#f2ebf8", "#b19cca"), "Winger": ("#fbefe5", "#e5ab80"),
        "Striker": ("#f6ece5", "#d6a285"), "Captain": ("#e9f3e5", "#8daf89"),
    }
    background, accent = colors[position]
    x = col * 100 / 3
    y = row * 100
    return f"""
<style>
.wpti-character-stage {{
  position:relative; min-height:475px; overflow:hidden; border-radius:28px;
  background:linear-gradient(145deg,#fff 0%,var(--wpti-bg) 58%,#e7f4e5 100%);
  border:3px solid #fff4ce; box-shadow:8px 9px 0 rgba(34,99,70,.14);
}}
.wpti-character-stage::after {{
  content:"";position:absolute;left:10%;right:10%;bottom:12%;height:28px;
  background:rgba(41,91,70,.15);border-radius:50%;filter:blur(7px);
}}
.wpti-character-portrait {{
  position:absolute;z-index:2;width:100%;height:86%;left:0;top:1%;
  background-size:400% 200%;
  image-rendering:pixelated;animation:wpti-character-bob 3.2s ease-in-out infinite;
}}
@keyframes wpti-character-bob {{
  0%,100% {{transform:translateY(0)}}
  50% {{transform:translateY(-9px)}}
}}
@media (prefers-reduced-motion:reduce) {{
  .wpti-character-portrait {{animation:none}}
}}
</style>
<div class="wpti-character-stage" role="img" aria-label="Animated chibi {escape(name)} character"
     style="--wpti-bg:{background};--wpti-accent:{accent}">
  <div class="wpti-character-portrait" style="background-image:url('{image_uri}');background-position:{x:.4f}% {y:.4f}%"></div>
</div>"""


def question_scene_html(question_id: str) -> str:
    """A lightly animated matching mini-scene for each quiz prompt."""
    # A newly added or legacy follow-up must never crash the student check-in.
    col, row = QUESTION_TILES.get(question_id, QUESTION_TILES["activity_type"])
    image_uri = asset_uri("chibi/question_scenes.png")
    x, y = col * 100 / 3, row * 100 / 3
    return f'''<div class="wpti-question-art" role="img" aria-label="Little cartoon scene for {escape(question_id.replace('_',' '))}"
      style="background-image:url('{image_uri}');background-position:{x:.4f}% {y:.4f}%"></div>'''
