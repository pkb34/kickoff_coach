"""Separate password-protected local staff aggregate view."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from collections import Counter
from contextlib import closing

import altair as alt
import pandas as pd
import streamlit as st

from gemini_gateway import is_configured
from pixel_theme import asset_uri
from staff_report import MIN_REPORT_CHECKINS, build_staff_snapshot, generate_staff_report
from storage import DB_PATH


st.set_page_config(page_title="WPTI · Staff overview", layout="wide")
st.html('''<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&display=swap');
[data-testid="stAppViewContainer"]{background:#daf4dd url("PIXEL_BACKGROUND") center/560px;image-rendering:pixelated}
[data-testid="stMainBlockContainer"]{font-family:Fredoka,sans-serif;background:#fffdf0;border:4px solid #78c7a2;border-radius:22px;max-width:1160px;padding:35px;box-shadow:9px 9px 0 #94d7bf;margin:28px auto}
[data-testid="stMainBlockContainer"] *{font-family:Fredoka,sans-serif}
[data-testid="stBaseButton-primary"]{background:#f18b59;border-color:#d8744c;border-radius:16px;color:white}
[data-testid="stTextInput"] button{display:none}
</style>'''.replace("PIXEL_BACKGROUND", asset_uri("cute_soccer_background.png")))
st.title("Student wellbeing & learning · staff overview")
st.caption("Local prototype · group statistics from voluntary student check-ins")

expected = os.getenv("WPTI_STAFF_PASSWORD", "")
if not expected:
    st.info("Staff access is not configured. Set WPTI_STAFF_PASSWORD locally before starting this page.")
    st.stop()
if not st.session_state.get("staff_authenticated", False):
    typed = st.text_input("Staff password", type="password")
    if st.button("Open overview", type="primary"):
        if secrets.compare_digest(typed, expected):
            st.session_state["staff_authenticated"] = True
            st.rerun()
        else:
            st.error("That password did not match.")
    st.stop()

if st.button("Lock overview"):
    st.session_state["staff_authenticated"] = False
    st.session_state.pop("staff_report", None)
    st.session_state.pop("staff_report_snapshot", None)
    st.rerun()

if not DB_PATH.exists():
    st.info("No student check-ins have been saved yet.")
    st.stop()

with closing(sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)) as connection:
    rows = connection.execute("SELECT result_json FROM collection_submissions").fetchall()

analyses = []
roles = Counter()
for (raw,) in rows:
    try:
        result = json.loads(raw)
        analysis = result.get("analysis")
        if analysis and isinstance(analysis.get("metrics"), dict):
            analyses.append(analysis)
            position = (result.get("wpti") or {}).get("position")
            if position:
                roles[position] += 1
    except (ValueError, TypeError):
        continue

st.metric("Saved check-ins with analysis", len(analyses))
if not analyses:
    st.info("Once students finish, aggregate charts will appear here.")
    st.stop()

metrics = [item["metrics"] for item in analyses]
def average(key):
    values = [item.get(key) for item in metrics if isinstance(item.get(key), (int, float))]
    return f"{sum(values) / len(values):.1f} h" if values else "No answers"


def response_chart(items):
    frame = pd.DataFrame(items, columns=["Category", "Responses"])
    short_labels = {
        "Feeling on track": "On track",
        "Keeping up, but stretched": "Stretched",
        "Central Midfielder": "Midfielder",
    }
    frame["Label"] = frame["Category"].map(lambda value: short_labels.get(value, value))
    chart = alt.Chart(frame).mark_bar(color="#4b9f7a", cornerRadiusEnd=4).encode(
        y=alt.Y("Label:N", sort=None, axis=alt.Axis(title=None, labelAngle=0, labelLimit=130,
                                                     labelOverlap=False, labelFontSize=13)),
        x=alt.X("Responses:Q", axis=alt.Axis(title="Responses", tickMinStep=1)),
        tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Responses:Q")],
    ).properties(height=max(150, 50 * len(frame)), padding={"left": 48, "right": 8, "top": 6, "bottom": 6})
    st.altair_chart(chart, width="stretch")


class_col, study_col, activity_col, sleep_col = st.columns(4)
class_col.metric("Average class time / week", average("weekly_class_hours"))
study_col.metric("Study outside class / week", average("weekly_independent_study_hours"))
activity_col.metric("Activities / week", average("weekly_extracurricular_hours"))
sleep_col.metric("Sleep / night", average("nightly_sleep_hours"))
progress = Counter(item.get("self_reported_academic_progress") or "Not shared" for item in metrics)
st.subheader("How students say classes are going")
response_chart(sorted(progress.items()))

feeling = [item.get("self_reported_happiness_index") for item in metrics]
bins = Counter("0–40" if value <= 40 else "50–70" if value <= 70 else "80–100"
               for value in feeling if isinstance(value, (int, float)))
st.subheader("Self-reported feeling")
response_chart([(label, bins[label]) for label in ("0–40", "50–70", "80–100")])

if roles:
    st.subheader("Playful football positions")
    response_chart(sorted(roles.items()))

st.caption("Time averages use midpoints of selected ranges and are approximate. These charts summarize voluntary answers. They do not measure health or predict academic outcomes. "
           "A real prediction model would need validated outcomes and evaluation before use.")

st.divider()
st.subheader("Group report")
st.write("Gemini can turn these group statistics into a short staff briefing on reported wellbeing and academic progress. It receives only aggregate numbers, never a student's answers or transcript.")
snapshot = build_staff_snapshot(analyses)
snapshot_key = json.dumps(snapshot, sort_keys=True)
if st.session_state.get("staff_report_snapshot") != snapshot_key:
    st.session_state.pop("staff_report", None)
    st.session_state["staff_report_snapshot"] = snapshot_key

def displayed(value, suffix=""):
    return f"{value}{suffix}" if value is not None else "Too few answers"

report_rows = []
for key, label, unit in (
    ("weekly_class_hours", "Class time per week", " h"),
    ("weekly_independent_study_hours", "Study outside class per week", " h"),
    ("weekly_extracurricular_hours", "Activities per week", " h"),
    ("nightly_sleep_hours", "Sleep per night", " h"),
):
    item = snapshot["time"][key]
    report_rows.append({"Measure": label, "Answers": item["responses"],
                        "Group estimate": displayed(item["approximate_mean_hours"], unit)})
wellbeing = snapshot["wellbeing_self_report"]
progress_summary = snapshot["academic_progress_self_report"]
report_rows.append({"Measure": "Happiness self-rating", "Answers": wellbeing["responses"],
                    "Group estimate": displayed(wellbeing["mean_rating_out_of_10"], " / 10")})
report_rows.append({"Measure": "Feeling on track", "Answers": progress_summary["responses"],
                    "Group estimate": displayed(progress_summary["share_feeling_on_track_percent_rounded_to_10"], "%")})
st.table(pd.DataFrame(report_rows))
st.caption("Each answer count is shown separately. Time figures are approximate group averages; percentages are rounded. Figures from fewer than five answers are suppressed.")

if len(analyses) < MIN_REPORT_CHECKINS:
    st.info(f"The group report becomes available after {MIN_REPORT_CHECKINS} completed check-ins.")
elif not is_configured():
    st.info("Add GEMINI_API_KEY to the local secrets file or environment to generate the staff report.")
elif st.button("Generate group report with Gemini", type="primary"):
    with st.spinner("Reading the group patterns..."):
        st.session_state["staff_report"] = generate_staff_report(snapshot)

report = st.session_state.get("staff_report")
if report:
    if report.get("status") == "generated":
        st.markdown("#### Overview")
        st.write(report["overview"])
        st.markdown("#### Wellbeing")
        st.write(report["wellbeing"])
        st.markdown("#### Academic progress")
        st.write(report["performance"])
        st.markdown("#### Support ideas")
        for action in report["suggested_actions"]:
            st.markdown(f"- {action}")
        st.caption(report["limitations"])
    else:
        st.warning(report.get("message", "The report is unavailable right now."))
