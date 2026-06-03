# To-be architecture — airline lakehouse + passenger 360

Target state aligned with **Data Engineer (Airline Domain)** responsibilities: scalable ETL/ELT, real-time ingestion, governance, AI/ML enablement.

**Glossary:** [`00-source-system-glossary.md`](00-source-system-glossary.md)

---

## 1. Target landscape

```mermaid
flowchart TB
    classDef source fill:#e8eaf6,stroke:#3949ab,stroke-width:2px,color:#1a237e
    classDef ingest fill:#fff8e1,stroke:#ff8f00,stroke-width:2px,color:#e65100
    classDef bronze fill:#d7ccc8,stroke:#5d4037,stroke-width:2px,color:#3e2723
    classDef silver fill:#b0bec5,stroke:#546e7a,stroke-width:2px,color:#263238
    classDef gold fill:#fff9c4,stroke:#f9a825,stroke-width:2px,color:#f57f17
    classDef gov fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c
    classDef ops fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20

    subgraph sources["Airline source systems"]
        PSS["Passenger Service System<br/>Computer Reservation System"]:::source
        DCS["Departure Control System<br/>check-in events"]:::source
        PAY["Payment Service Provider<br/>auth and capture"]:::source
        CRM["Customer Relationship Management<br/>and Loyalty"]:::source
        RMS["Revenue Management System"]:::source
        OCC["Operations Control Center<br/>delay and recovery"]:::source
    end

    subgraph ingest["Ingestion layer"]
        CDC["Change Data Capture<br/>where PSS allows"]:::ingest
        JDBC["Spark JDBC incremental<br/>watermarked batch"]:::ingest
        MSK["Kafka event bus<br/>booking check-in payment"]:::ingest
        API["API Gateway micro-batch"]:::ingest
    end

    subgraph lake["Cloud lakehouse"]
        S3B["Bronze object store<br/>immutable raw"]:::bronze
        SPARK["Spark or Databricks ETL"]:::silver
        S3S["Silver conformed<br/>passenger and flight"]:::silver
        DQ["Data quality engine<br/>Great Expectations plus SQL"]:::gov
        GOV["Governance catalog<br/>PII tags and lineage"]:::gov
    end

    subgraph wh["Gold warehouse"]
        SF["Snowflake Redshift BigQuery"]:::gold
        P360["passenger_360 mart"]:::gold
    end

    subgraph dataops["DataOps"]
        AF["Airflow or Step Functions"]:::ops
        MON["Observability alerts"]:::ops
        CI["CI CD pipelines"]:::ops
    end

    PSS --> CDC
    PSS --> JDBC
    DCS --> MSK
    PAY --> MSK
    CRM --> JDBC
    RMS --> JDBC
    OCC --> MSK
    CDC --> S3B
    JDBC --> S3B
    MSK --> S3B
    S3B --> SPARK --> S3S
    S3S --> DQ
    DQ -->|"pass"| SF
    SF --> P360
    AF --> SPARK
    DQ --> MON
    GOV -.-> S3B
    GOV -.-> S3S
    CI --> SPARK
```

---

## 2. Medallion tiering

```mermaid
flowchart LR
    classDef bronze fill:#d7ccc8,stroke:#5d4037,stroke-width:2px,color:#3e2723
    classDef silver fill:#b0bec5,stroke:#546e7a,stroke-width:2px,color:#263238
    classDef gold fill:#fff9c4,stroke:#f9a825,stroke-width:2px,color:#f57f17

    B["Bronze raw<br/>Passenger Service System DCS PSP"]:::bronze
    S["Silver conformed<br/>passenger flight segment"]:::silver
    G["Gold warehouse<br/>KPIs passenger_360"]:::gold

    B -->|"Spark ETL"| S -->|"DQ pass"| G
```

| Tier | Path pattern | Content | Retention |
|------|--------------|---------|-----------|
| **Bronze** | `.../bronze/{system}/{entity}/dt=YYYY-MM-DD/` | Raw PSS, DCS, payment, loyalty | 7+ years (policy) |
| **Silver** | `.../silver/{domain}/{entity}/` | Typed, deduped, `flight_id`, `passenger_id` conformed | 5 years |
| **Gold** | `gold.*` in warehouse | Star schema, KPI marts, ML features | Current + SCD history |

**Standard audit columns:** `ingest_ts`, `source_system`, `source_record_id`, `pipeline_run_id`, `record_hash`

---

## 3. Passenger 360 (Single Source of Truth) model

```mermaid
flowchart TB
    classDef dim fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef fact fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100
    classDef xref fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c

    DP["DIM_PASSENGER<br/>golden_passenger_id<br/>loyalty_tier SCD2"]:::dim
    XR["XREF_PASSENGER_ID<br/>PSS loyalty CRM IDs"]:::xref
    DF["DIM_FLIGHT<br/>schedule and actual times"]:::dim
    FB["FACT_BOOKING<br/>pnr_locator channel"]:::fact
    FS["FACT_FLIGHT_SEGMENT<br/>fare cabin status"]:::fact
    FA["FACT_ANCILLARY<br/>bags seats fees"]:::fact
    FP["FACT_PAYMENT<br/>Payment Service Provider"]:::fact

    DP -->|"maps"| XR
    DP -->|"books"| FB
    FB -->|"contains"| FS
    DF -->|"operates"| FS
    FS -->|"upsell"| FA
    FB -->|"pays"| FP
```

**Rule:** Preserve **declared** loyalty tier from source; use **estimated_*** only for ML features with `is_imputed` flag.

Full schema reference: [`05-database-schema.md`](05-database-schema.md)

---

## 4. Real-time vs batch patterns

| Pattern | When | Tool | Example |
|---------|------|------|---------|
| Full snapshot (small ref) | Daily airports, aircraft | Spark JDBC | `dim_airport` |
| Incremental watermark | PSS booking delta | `last_modified_ts` | `fact_booking` silver |
| Event stream | DCS check-in, payment auth | Kafka → bronze | Near real-time OTP inputs |
| CDC | If airline enables | Debezium / DMS | Low-latency seat changes |

**Timezone:** Store **UTC** in warehouse; expose **local station** in gold views for ops.

---

## 5. DQ shift-left

```text
Bronze ──► schema contract (PSS version)
Silver ──► uniqueness PNR+segment, referential flight_id
Gold   ──► business rules (flown segment must have ticket coupon)
         ──► BLOCK publish if severity=CRITICAL
```

Critical rules (examples):

- `pnr_locator` not null in silver booking
- Duplicate `segment_id` above threshold → quarantine
- Load factor inputs: **no negative ASK**; cabin grain documented

---

## 6. AI / ML enablement

| Use case | Gold / feature layer |
|----------|----------------------|
| Demand forecasting | `feature_flight_od_daily` from RMS + historical bookings |
| Churn / loyalty | `feature_passenger_rfm` from booking + ancillary |
| Personalization | `passenger_360` + consent flags |
| Ops optimization | `feature_flight_delay_risk` from ops + weather (optional) |

---

## 7. Security & governance

| Control | Implementation |
|---------|----------------|
| PNR / PII | Column tags `PII`, `FINANCIAL`; mask in bronze reads |
| Payment | PCI scope minimized — tokenized IDs only in lake |
| Lineage | OpenLineage / Databricks lineage on every pipeline |
| Access | RBAC by domain: `revenue_read`, `ops_read`, `ml_feature_read` |

---

## 8. Migration roadmap (phased)

| Phase | Focus |
|-------|-------|
| 0 | Landing zone, IAM, catalog, CI/CD |
| 1 | Booking bronze/silver + `dim_passenger` / xref |
| 2 | DCS + payment streaming → ops & ancillary gold |
| 3 | RMS + loyalty integration; decommission dept marts |
| 4 | ML feature store + real-time personalization API |

Summary: [`04-as-is-to-be-summary.md`](04-as-is-to-be-summary.md)
