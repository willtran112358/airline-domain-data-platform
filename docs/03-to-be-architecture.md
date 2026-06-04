# Target architecture — SQ lakehouse + passenger 360

**Config:** [`../config/platform.yaml`](../config/platform.yaml)

---

## Target landscape

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#0B1F3F','primaryTextColor':'#fff','primaryBorderColor':'#C9A227'}}}%%
flowchart TB
    classDef source fill:#0B1F3F,stroke:#C9A227,stroke-width:2px,color:#FFFFFF
    classDef bronze fill:#8D6E63,stroke:#4E342E,stroke-width:2px,color:#FFFFFF
    classDef silver fill:#78909C,stroke:#455A64,stroke-width:2px,color:#FFFFFF
    classDef gold fill:#C9A227,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F
    classDef gov fill:#E8EDF5,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F

    PSS["PSS · Amadeus"]:::source
    DCS["DCS · SIN hub"]:::source
    KF["KrisFlyer"]:::source
    MSK["Kafka MSK"]:::source
    B["Bronze S3"]:::bronze
    S["Silver Spark"]:::silver
    DQ["DQ · GE + SQL"]:::gov
    G["Gold · Snowflake"]:::gold
    P360["passenger_360"]:::gold
    AF["Airflow"]:::gov

    PSS --> B
    DCS & KF --> MSK --> B
    B --> S --> DQ --> G --> P360
    AF --> S
```

---

## Medallion

| Tier | Path | Content |
|------|------|---------|
| Bronze | `bronze/{system}/{entity}/dt=` | Raw PSS, DCS, PSP, KrisFlyer |
| Silver | `silver/{domain}/{entity}/` | Conformed passenger, flight, segment |
| Gold | `gold.*` | Star schema, KPIs, ML features |

**Audit columns:** `ingest_ts`, `source_system`, `pipeline_run_id`, `record_hash`

---

## Passenger 360

```mermaid
flowchart TB
    classDef dim fill:#0B1F3F,stroke:#C9A227,color:#fff
    classDef fact fill:#FFF8E7,stroke:#C9A227,color:#0B1F3F
    classDef xref fill:#E8EDF5,stroke:#5B7DB1,color:#0B1F3F

    DP["DIM_PASSENGER"]:::dim
    XR["XREF_PASSENGER_ID"]:::xref
    FB["FACT_BOOKING"]:::fact
    FS["FACT_FLIGHT_SEGMENT"]:::fact

    DP --> XR & FB --> FS
```

Schema: [`05-database-schema.md`](05-database-schema.md)

---

## Ingest patterns

| Pattern | Use | Example |
|---------|-----|---------|
| Incremental watermark | PSS booking delta | `fact_booking` |
| Event stream | DCS check-in | Kafka → bronze |
| Daily snapshot | Airports, aircraft | `dim_airport` |

Store **UTC** in warehouse; expose local station in gold views.

---

## DQ (shift-left)

```text
Bronze → PSS schema version contract
Silver → PNR uniqueness, flight_id referential
Gold   → BLOCK on CRITICAL (negative ASK, orphan ancillary)
```

---

## Migration phases

| Phase | Deliverable |
|-------|-------------|
| 0 | Landing zone, IAM, catalog, CI/CD |
| 1 | PSS bronze/silver + `dim_passenger` |
| 2 | DCS stream + ancillary gold |
| 3 | RMS + KrisFlyer; retire dept marts |
| 4 | ML features + personalization API |
