"""Local, crisp pixel artwork shared by the app shell and result page."""

from base64 import b64encode
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "static"
ROLES = {"midfielder", "captain", "penalty_striker", "defender"}
CHIBI_ART = {
    "midfielder": "chibi/box_to_box_midfielder.png",
    "captain": "chibi/playmaker_captain.png",
    "penalty_striker": "chibi/penalty_striker.png",
    # The earlier defensive sprite is a sweeper-keeper, our goalkeeper-style defender.
    "defender": "chibi/sweeper_keeper.png",
}


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
