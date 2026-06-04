# As-is architecture — pre-lakehouse

---

## Landscape

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#0B1F3F','primaryTextColor':'#fff','primaryBorderColor':'#C9A227'}}}%%
flowchart TB
    classDef source fill:#0B1F3F,stroke:#C9A227,stroke-width:2px,color:#FFFFFF
    classDef ingest fill:#FFF8E7,stroke:#C9A227,stroke-width:2px,color:#0B1F3F
    classDef store fill:#E8EDF5,stroke:#5B7DB1,stroke-width:2px,color:#0B1F3F
    classDef bi fill:#C9A227,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F

    subgraph sources["Sources"]
        PSS["PSS · Amadeus"]:::source
        DCS["DCS"]:::source
        KF["KrisFlyer"]:::source
        RMS["RMS"]:::source
        OCC["OCC"]:::source
        PAY["PSP"]:::source
    end
    subgraph ingest["Ingestion"]
        ETL["Nightly ETL"]:::ingest
        SFTP["Settlement SFTP"]:::ingest
    end
    subgraph marts["Silos"]
        M1["Commercial"]:::store
        M2["Revenue"]:::store
        M3["Ops"]:::store
    end
    TAB["BI"]:::bi

    PSS --> ETL
    DCS -.->|"gap"| ETL
    KF --> ETL
    RMS --> ETL
    OCC --> SFTP
    PAY --> SFTP
    ETL --> M1 & M2
    SFTP --> M3
    M1 & M2 & M3 --> TAB
```

**Summary:** Batch PSS → department marts; DCS/OCC weakly integrated; no shared bronze or `golden_passenger_id`.

---

## Integration (as-is)

| Source | Pattern | Latency | Failure mode |
|--------|---------|---------|--------------|
| PSS | File dump | T+1 | Partial export after maintenance |
| DCS | Not in DW | — | Ops uses separate tooling |
| KrisFlyer | Weekly batch | T+1–T+7 | Stale tier for campaigns |
| PSP | Settlement CSV | T+2 | Refund / currency mismatch |
| OCC | Manual CSV | Ad hoc | OTP disagreements |

---

## Technical debt

| Area | Symptom |
|------|---------|
| Identity | No golden passenger key |
| Grain | Leg / segment / OD mixed |
| Streaming | No Kafka for DCS |
| DQ | Post-publish discovery |
| Cost | Repeated full PSS extracts |

See [`04-as-is-to-be-summary.md`](04-as-is-to-be-summary.md).
