# WPTI current flow

```mermaid
flowchart TD
    A[Welcome artwork and optional original music] --> B[Three usual-routine question groups, seven time bands per field]
    B --> C[Validate activity, learning time, and sleep fields]
    C --> D[Start local Python question agent]
    D --> E[Ask a deeper question]
    E --> F[Student taps an answer, writes, or skips]
    E -->|Open question only| V[Optional browser voice reads the question]
    V -->|Student records and sends| W[Gemini transcribes one open answer; audio not saved]
    W --> G
    F --> G[Record answer and check conditional triggers]
    G -->|Core topics or selected extras remain| E
    G -->|7 core questions, at most 1 extra| P[Infer four axes from existing contextual answers]
    P --> Q[One of 16 letter types and a pitch position, if evidence is complete]
    Q --> I[Save locally to SQLite]
    I --> J[Local academic progress, honest time ranges, rest, and direct feeling rating]
    J --> K[Confetti, role-specific character, personal note, matching VT links]
    K -->|Student requests briefing| L[Send minimal summary to Gemini]
    L --> M[Empathetic note, two tips, possible future moment]
    I --> S[Separate password-gated staff page]
    S --> T[Aggregate progress and self-reported feeling charts]
```

Question selection and arithmetic analysis are local Python. Selected time intervals are retained and derived weekly intervals are calculated from their bounds; internal midpoints are estimates, not exact reports. Optional voice answers send only one short recording to Gemini after a separate student action. The optional result briefing sends a compact range summary after the student clicks its button; it does not send the transcript or raw replies. The staff page reads local saved results and displays aggregate self-reports. These are not validated predictions. No agent asks questions about academic marks.
