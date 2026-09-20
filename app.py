"""PitchSide: a fully Python Streamlit student check-in MVP."""

import os

import streamlit as st

from Data import load_students, source_name


ARCHETYPES = {
    "Sweeper-Keeper": "You do not have to defend every challenge alone. Make one support pass this week: office hours, tutoring, or a study group.",
    "Last-Minute Penalty Striker": "Use the pressure well, but start with one 25-minute task at least two days before each deadline.",
    "Pressing Winger": "Your energy is valuable. Pick one priority, silence distractions for 25 minutes, and make the next move simple.",
    "Box-to-Box Midfielder": "You are covering the whole pitch. Protect recovery time and choose your three most important commitments this week.",
    "Playmaker Captain": "Your routine looks balanced. Keep your structure and consider sharing a study strategy with a teammate.",
}


def choose_archetype(study_hours, extracurricular_count, credit_hours, primary_struggle, assignment_start_style):
    """Map the five check-in answers to one soccer-themed student archetype."""
    if primary_struggle == "Asking for help":
        return "Sweeper-Keeper"
    if assignment_start_style == "Near the deadline":
        return "Last-Minute Penalty Striker"
    if primary_struggle in {"Motivation", "Staying focused"}:
        return "Pressing Winger"
    if primary_struggle == "Time management" or credit_hours >= 18 or extracurricular_count >= 3 or study_hours >= 20:
        return "Box-to-Box Midfielder"
    return "Playmaker Captain"


def calculate_match_fitness(study_hours, extracurricular_count, credit_hours, primary_struggle, assignment_start_style):
    """Calculate a transparent 0–100 demo score from the check-in answers."""
    score = 90
    score -= max(credit_hours - 14, 0) * 3
    score -= max(extracurricular_count - 2, 0) * 5
    score -= max(study_hours - 18, 0) * 2
    score -= {"Time management": 8, "Motivation": 7, "Course difficulty": 5, "Asking for help": 6, "Staying focused": 7}[primary_struggle]
    score -= {"Early": 0, "A few days before": 4, "Near the deadline": 12}[assignment_start_style]
    return round(max(0, min(100, score)))


def get_gaffer_briefing(archetype, fitness):
    """Use Gemini when a key exists; otherwise provide a local, reliable briefing."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return f"Match fitness: {fitness}/100. {ARCHETYPES[archetype]}"
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = (
            "You are The Gaffer, an empathetic student-success coach. "
            f"Give a short, supportive halftime briefing for a {archetype} with match fitness {fitness}/100. "
            "Give two practical, non-medical next steps. Do not diagnose or shame the student."
        )
        return client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text
    except Exception:
        return f"Match fitness: {fitness}/100. {ARCHETYPES[archetype]}"


def main():
    """Render the all-Python Streamlit application."""
    st.set_page_config(page_title="PitchSide", page_icon="⚽", layout="wide")
    st.title("⚽ PitchSide | Expected Well-being")
    st.caption("A privacy-first hackathon demo using synthetic data. It is not a diagnosis or academic decision tool.")

    left, right = st.columns(2)
    with left:
        study_hours = st.slider("1. Weekly study hours", min_value=0, max_value=30, value=10)
        extracurricular_count = st.slider("2. Number of extracurricular activities", min_value=0, max_value=6, value=1)
        credit_hours = st.slider("3. Credit hours this semester", min_value=9, max_value=24, value=15)
    with right:
        primary_struggle = st.selectbox("4. What are you struggling with most?", ["Time management", "Motivation", "Course difficulty", "Asking for help", "Staying focused"])
        assignment_start_style = st.selectbox("5. When do you usually begin assignments?", ["Early", "A few days before", "Near the deadline"])

    if st.button("Get my halftime briefing", type="primary"):
        archetype = choose_archetype(study_hours, extracurricular_count, credit_hours, primary_struggle, assignment_start_style)
        fitness = calculate_match_fitness(study_hours, extracurricular_count, credit_hours, primary_struggle, assignment_start_style)
        score_column, archetype_column = st.columns(2)
        score_column.metric("Match Fitness", f"{fitness}/100")
        archetype_column.metric("Soccer Archetype", archetype)
        with st.spinner("The Gaffer is reviewing the match tape..."):
            st.success(get_gaffer_briefing(archetype, fitness))

        with st.expander(f"View sample telemetry from {source_name()}"):
            st.dataframe(load_students(), use_container_width=True)


if __name__ == "__main__":
    main()
