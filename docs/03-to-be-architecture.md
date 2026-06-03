# To-be architecture — airline lakehouse + passenger 360

Target state aligned with **Data Engineer (Airline Domain)** responsibilities: scalable ETL/ELT, real-time ingestion, governance, AI/ML enablement.

---

## 1. Target landscape

```mermaid
flowchart TB
    subgraph sources["Airline source systems"]
        PSS["PSS / CRS"]
        DCS["DCS events"]
        PAY["Payment events"]
        CRM["CRM / Loyalty"]
        RMS["RMS feeds"]
        OPS["Flight ops stream"]
    end

    subgraph ingest["Ingestion layer"]
        CDC["CDC / change files<br/>where PSS allows"]
        JDBC["Spark JDBC / API<br/>incremental batch"]
        MSK["Kafka / Event Hubs<br/>booking · check-in · payment"]
        API["API Gateway micro-batch<br/>reference data"]
    end

    subgraph lake["Cloud lakehouse"]
        S3B["Object store Bronze<br/>immutable raw"]
        CAT["Glue / Unity Catalog"]
        SPARK["Spark / Databricks ETL"]
        S3S["Silver<br/>conformed passenger · flight"]
        GOV["Lake Formation / Purview<br/>PII · lineage"]
        DQ["DQ engine<br/>GX + SQL contracts"]
    end

    subgraph wh["Warehouse gold"]
        SF["Snowflake / Redshift / BigQuery"]
        DM["dim_passenger SCD2"]
        FF["fact_flight_segment"]
        FB["fact_booking"]
        FA["fact_ancillary"]
        P360["passenger_360 mart"]
    end

    subgraph ops["DataOps"]
        AF["Airflow / Step Functions"]
        MON["Observability<br/>Datadog · CloudWatch"]
        CI["CI/CD pipelines"]
    end

    PSS --> CDC
    PSS --> JDBC
    DCS --> MSK
    PAY --> MSK
    CRM --> JDBC
    RMS --> JDBC
    OPS --> MSK
    CDC --> S3B
    JDBC --> S3B
    MSK --> S3B
    S3B --> SPARK --> S3S
    S3S --> DQ
    DQ -->|pass| SF
    SF --> DM
    SF --> FF
    SF --> FB
    SF --> FA
    SF --> P360
    AF --> SPARK
    DQ --> MON
    GOV --- S3B
    GOV --- S3S
```

---

## 2. Medallion tiering

| Tier | Path pattern | Content | Retention |
|------|--------------|---------|-----------|
| **Bronze** | `.../bronze/{system}/{entity}/dt=YYYY-MM-DD/` | Raw PSS, DCS, payment, loyalty | 7+ years (policy) |
| **Silver** | `.../silver/{domain}/{entity}/` | Typed, deduped, `flight_id`, `passenger_id` conformed | 5 years |
| **Gold** | `gold.*` in warehouse | Star schema, KPI marts, ML features | Current + SCD history |

**Standard audit columns:** `ingest_ts`, `source_system`, `source_record_id`, `pipeline_run_id`, `record_hash`

---

## 3. Passenger 360 (SSOT) model

```mermaid
erDiagram
    DIM_PASSENGER ||--o{ XREF_PASSENGER_ID : maps
    DIM_PASSENGER ||--o{ FACT_PASSENGER_SNAPSHOT : monthly
    DIM_PASSENGER ||--o{ FACT_BOOKING : books
    FACT_BOOKING ||--|{ FACT_FLIGHT_SEGMENT : contains
    DIM_FLIGHT ||--o{ FACT_FLIGHT_SEGMENT : operates
    FACT_FLIGHT_SEGMENT ||--o{ FACT_ANCILLARY : upsell
    FACT_BOOKING ||--o{ FACT_PAYMENT : pays

    DIM_PASSENGER {
        bigint passenger_sk PK
        string golden_passenger_id NK
        date valid_from
        date valid_to
        boolean is_current
        string loyalty_tier
        int loyalty_points_balance
        string preferred_language
        boolean marketing_consent
    }

    XREF_PASSENGER_ID {
        string golden_passenger_id
        string source_system
        string source_passenger_id
    }

    DIM_FLIGHT {
        string flight_id PK
        string flight_number
        date flight_date
        string origin_airport
        string destination_airport
        timestamp scheduled_dep_utc
        timestamp actual_dep_utc
    }

    FACT_BOOKING {
        string booking_id PK
        string pnr_locator
        string golden_passenger_id FK
        timestamp booking_ts_utc
        string channel
        string booking_status
    }

    FACT_FLIGHT_SEGMENT {
        string segment_id PK
        string booking_id FK
        string flight_id FK
        string cabin_class
        string segment_status
        decimal base_fare_amount
        string currency_code
    }

    FACT_ANCILLARY {
        string ancillary_id PK
        string segment_id FK
        string product_code
        decimal revenue_amount
        string fulfillment_status
    }

    FACT_PAYMENT {
        string payment_id PK
        string booking_id FK
        string payment_method
        decimal amount
        string auth_status
    }
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
