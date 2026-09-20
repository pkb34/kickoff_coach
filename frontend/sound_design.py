"""Optional original audio cues; no third-party music or recordings."""

from base64 import b64encode
from functools import lru_cache
from pathlib import Path

import streamlit as st


AUDIO = Path(__file__).resolve().parent / "static" / "audio"


@lru_cache(maxsize=4)
def audio_uri(name: str) -> str:
    if name not in {"tap.wav", "soft_cheer.wav", "sunny_pitch.wav"}:
        raise ValueError("Unknown sound")
    return "data:audio/wav;base64," + b64encode((AUDIO / name).read_bytes()).decode("ascii")


def play_pending_event() -> None:
    event = st.session_state.pop("sound_event", None)
    if event and st.session_state.get("audio_enabled"):
        filename = "soft_cheer.wav" if event == "cheer" else "tap.wav"
        st.html(f'<audio src="{audio_uri(filename)}" autoplay preload="auto" aria-hidden="true"></audio>')


def sound_controls(page: str) -> None:
    """Optional original music without a browser media-control bar."""
    enabled = st.toggle("Cute music & sounds", value=st.session_state.get("audio_enabled", False),
                        key=f"sound_toggle_{page}")
    st.session_state["audio_enabled"] = enabled
    if enabled:
        # When autoplay is blocked, a small button gives the browser a direct click gesture.
        st.html(f'''<div class="wpti-music-shell">
          <audio id="wpti-music-{page}" src="{audio_uri("sunny_pitch.wav")}" loop preload="auto" style="display:none"></audio>
          <button id="wpti-music-start-{page}" type="button" style="display:none;border:2px solid #a3c99c;
            border-radius:999px;background:#fff4cf;color:#365c49;padding:8px 14px;font:600 16px Fredoka,sans-serif;
            cursor:pointer">♫ Tap to start the little tune</button></div>
          <script>
            (() => {{
              const audio = document.getElementById("wpti-music-{page}");
              const button = document.getElementById("wpti-music-start-{page}");
              audio.volume = .32;
              audio.play().catch(() => {{ button.style.display = "inline-block"; }});
              button.onclick = () => audio.play().then(() => {{ button.style.display = "none"; }});
            }})();
          </script>''', unsafe_allow_javascript=True)


def cheer_replay_button() -> None:
    """A simple replay action with no audio player chrome."""
    st.html(f'''<audio id="wpti-cheer-replay" src="{audio_uri("soft_cheer.wav")}" style="display:none"></audio>
      <button id="wpti-cheer-button" type="button" style="border:2px solid #a3c99c;
        border-radius:999px;background:#fff4cf;color:#365c49;padding:8px 14px;font:600 16px Fredoka,sans-serif;
        cursor:pointer">🎉 Replay the little cheer</button>
      <script>document.getElementById("wpti-cheer-button").onclick = () => {{
        const audio = document.getElementById("wpti-cheer-replay"); audio.currentTime = 0; audio.play();
      }};</script>''', unsafe_allow_javascript=True)


def confetti_html() -> str:
    colors = ["#f7a884", "#84bdab", "#f4d779", "#9bb1de", "#c7a9d9"]
    pieces = "".join(
        f'<span style="--left:{(index * 41) % 97}%;--delay:{(index % 9) * .13}s;'
        f'--color:{colors[index % len(colors)]};--twist:{(index % 3 - 1) * 180}deg"></span>'
        for index in range(32)
    )
    return f"""<style>
      .wpti-confetti {{position:fixed;inset:0;z-index:99;pointer-events:none;overflow:hidden}}
      .wpti-confetti span {{position:absolute;left:var(--left);top:-18px;width:9px;height:15px;
        border-radius:3px;background:var(--color);opacity:0;transform:rotate(var(--twist));
        animation:wpti-fall 2.8s ease-in var(--delay) 1 forwards}}
      @keyframes wpti-fall {{10%{{opacity:1}}80%{{opacity:1}}100%{{top:105vh;opacity:0;transform:translateX(85px) rotate(800deg)}}}}
      @media(prefers-reduced-motion:reduce){{.wpti-confetti{{display:none}}}}
    </style><div class="wpti-confetti" aria-hidden="true">{pieces}</div>"""
