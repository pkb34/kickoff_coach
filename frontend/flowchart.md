# WCPT current and future flow

```mermaid
flowchart TD
    A[Welcome: Start WCPT] --> B[Collection page: opening question]
    B --> C[Student reply]
    C --> D[Collector updates fields and coverage]
    D -->|Invalid or unclear| E[Clarify current question]
    E --> C
    D -->|Required details remain| F[Choose next relevant question]
    F --> C
    D -->|All details addressed| G[Student reviews and corrects record]
    G -->|Correction creates a gap| F
    G -->|Confirmed| H[Save structured record and transcript]
    H --> I[Demo personality result]
    H -.Future.-> J[Separate analysis agent]
    J -.Future.-> K[Personality, advice, predictions, support]
```

The collector is currently a transparent rule-based demo. The future backend agent will replace it through `collection_gateway.py`. The separate analysis agent is planned but not implemented.
