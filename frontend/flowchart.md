# WCPT current flow

```mermaid
flowchart TD
    A[Welcome: Start WCPT] --> B[Three starting questions]
    B --> C[Validate activity, learning time, and sleep fields]
    C --> D[Start local Python question agent]
    D --> E[Ask a deeper question]
    E --> F[Student answers or skips]
    F --> G[Record answer and check conditional triggers]
    G -->|Core topics or selected extras remain| E
    G -->|8 to 10 deeper questions done| H[Review structured record]
    H -->|Change starting answers| B
    H -->|Confirm| I[Save locally to SQLite]
    I --> J[Local descriptive analysis and direct happiness rating]
    J --> K[Illustrative role, national team, and player analogy]
    K -->|Student requests briefing| L[Send minimal summary to Gemini]
    L --> M[Possible future moment and suggestions]
```

Question selection and arithmetic analysis are local Python. The optional Gemini request sends a compact numeric summary after the student clicks the briefing button; it does not send the transcript or raw replies. No agent asks questions about academic marks.
