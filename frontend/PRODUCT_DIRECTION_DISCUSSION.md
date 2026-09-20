# Product direction discussion — voice, WPTI, and analysis output

**Current scope update (2026-09-19):** This discussion predates the three-question local-agent design. Historical academic-mark references below are superseded. The active quiz does not ask for or display those data.

Recorded 2026-09-19. These are **proposals for discussion**, not implemented or finalized requirements.

## Voice-first collection

The student may talk with an information-collection agent instead of filling out a long form. The agent listens, extracts needed fields, asks targeted follow-ups, speaks its next question, and ends by reading back or displaying the structured record for correction. The intended benefit is a less repetitive and more approachable experience. Whether voice increases candor is a hypothesis to test with students; privacy of the room, language/accent recognition, and microphone access can have the opposite effect.

An MVP can use turn-based recording and playback in the current Python Streamlit app (`st.chat_input(accept_audio=True)` or `st.audio_input`, speech-to-text, collector backend, text-to-speech, `st.audio`). Fully interruptible, low-latency voice dialogue is a later streaming/WebRTC phase. Keep a text/caption/correction option for accessibility and for exact GPA/hour confirmation even if voice is the primary path. Default to not retaining raw recordings; define consent and retention before using real student data. [Streamlit audio input](https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input), [W3C WebRTC](https://www.w3.org/TR/webrtc/).

## Conversation content and support

The collector needs direct academic and wellbeing information rather than using one social behavior as a proxy. A question such as "Did you call your parents this week?" can be optional context, but it cannot establish wellbeing for students with different family circumstances. Prefer neutral questions about campus belonging, perceived coursework strain, rest, and whether the student has someone they feel comfortable seeking support from. Allow skipping, do not press for sensitive details, and ask follow-ups only where they help the agreed information standard.

The agent may acknowledge a student's feelings and suggest student-approved campus support resources. It should not present itself as a counselor, diagnose a condition, or promise immediate human assistance. Any escalation behavior and resource wording need university review. [WHO on responsible AI for mental health](https://www.who.int/news/item/20-03-2026-towards-responsible-ai-for-mental-health-and-well-being--experts-chart-a-way-forward).

## Football personality name and role

The proposed full name "World Football Personality Type Indicator" abbreviates to **WFTI**. If the desired four-letter label is **WPTI**, a possible expansion is "World Player Type Indicator". This is a product naming decision. The four football archetypes can stay as an engagement layer and be explained with observed study/activity patterns; they should not be represented as a validated psychometric instrument or a measure of student health. Famous players may be used as optional inspiration only after checking image/quote permissions and avoiding an implication of endorsement.

## Analysis and presentation proposal

Keep **academic performance** and **wellbeing** as separate, evidence-linked sections. Performance can show reported GPA, class/study load, perceived course manageability, and action items. Wellbeing needs direct self-report, for example a reviewed measure such as WHO-5 if the project team accepts its scope and license; sleep/activity/GPA alone should not be combined into a made-up health score. [WHO-5 official description](https://www.who.int/publications/m/item/WHO-UCN-MSD-MHE-2024.01).

For a student-facing result, display: (1) confirmed facts; (2) academic pattern; (3) self-reported wellbeing and support needs; (4) a small number of practical suggestions; (5) the optional WFTI/WPTI archetype. Each observation should show which answers support it and when the system cannot conclude anything. If an authorized staff dashboard is later requested, default to aggregated trends and restricted access for identifiable records. Student-record disclosure needs an institution-specific privacy review. [US Department of Education guidance](https://studentprivacy.ed.gov/privacy-and-data-sharing).

Do not assign one 0–100 score across grades, sleep, belonging, and wellbeing without a defined construct and evidence. Use actual GPA on its own 0–4 scale; display completeness separately; use an established instrument's official scoring only if adopted. Future GPA, sleep, or wellbeing prediction requires longitudinal outcomes and separate evaluation. See `ANALYSIS_AGENT_DESIGN.md` for the detailed algorithm and evaluation proposal.

## Decisions to confirm

1. Is the next prototype voice-first with captions/text fallback, or strictly voice-only?
2. Is the result page for students only, or is a restricted staff dashboard returning to scope?
3. Which direct wellbeing questions or reviewed measure does the team want, and who approves campus support wording?
4. Should the product name be WFTI, WPTI with a different expansion, or another name?
