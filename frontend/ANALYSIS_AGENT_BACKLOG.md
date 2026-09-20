# Next phase: Student analysis agent

**Current scope update (2026-09-19):** The active collection schema v2.0 excludes academic marks. Historical references below to GPA are superseded. A limited local descriptive agent and optional Gemini briefing are now implemented; see `ANALYSIS_AGENT_HANDOFF.md`. The fuller analytical methods discussed below remain future work and must use only approved v2.0 fields unless the project owner explicitly changes this policy.

Recorded from the project discussion on 2026-09-19. This is a requirement note, **not** an implemented or approved analytical method. An initial analysis proposal now exists in [ANALYSIS_AGENT_DESIGN.md](ANALYSIS_AGENT_DESIGN.md); the analysis agent itself remains unimplemented.

## Intended role

The information-collection agent asks follow-up questions and produces a structured student record. A separate **analysis agent** consumes that record and analyzes student performance and wellbeing. Its outputs may later support the football-personality result, personalized advice, future GPA/sleep/wellbeing views, and a "Need Help?" section.

## Work to do after the collection frontend and interface are finished

1. Define the analysis questions and outputs precisely. Separate descriptive summaries, risk signals, recommendations, and any prediction. Decide which are appropriate for an MVP.
2. Inventory every collected field, its unit, source, status, uncertainty, and missingness. Determine what extra data would be needed to support each output.
3. Design an analysis flow: input validation; completeness check; feature derivation; evidence-backed interpretation; result generation; uncertainty and limitation labels; human-readable explanation; result review.
4. Investigate candidate methods and algorithms, including transparent rule-based baselines and any statistically trained models. Define how weights would be chosen and tested. Do not invent weights or imply a prediction is validated without data and evaluation.
5. Plan evaluation: accuracy or calibration where applicable, robustness to missing answers, subgroup fairness, explanation quality, student feedback, and how to detect harmful or overconfident advice.
6. Define the interface from collection record to analysis agent, and from analysis agent to the result page. Coordinate this with the teammate's backend code when it is available.
7. Consider the sensitive nature of GPA, sleep, and wellbeing data: minimize identifying information, control retention and access, and provide appropriate support language without presenting a health diagnosis.

## Decisions still open

- Is the primary output a football personality, an academic performance summary, wellbeing guidance, or several separate outputs?
- What does "wellbeing" mean operationally in this project, and which measures or labels are acceptable?
- Will real, consented outcome data be available to develop or validate predictions? If not, prediction panels should remain labeled as unimplemented rather than use arbitrary scores.
- Which support resources and escalation paths may be shown, and who will verify them?

Current project state: the result page is an illustrative prototype. Its personality display is based on demo rules, and GPA/sleep/wellbeing predictions are not implemented.
