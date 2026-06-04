<p align="center">
  <img src="docs/assets/sq-logo.svg" alt="Singapore Airlines — Enterprise Data Platform" width="420"/>
</p>

# Singapore Airlines — Enterprise Data Platform

<p align="center">
  <img src="docs/assets/sq-hero-banner.svg" alt="Singapore Airlines analytics platform" width="720"/>
</p>

| | |
|---|---|
| **Carrier** | Singapore Airlines (IATA **SQ**) · hub **SIN** (Changi) |
| **Loyalty** | KrisFlyer · PPS Club |
| **Sources** | PSS, DCS, PSP, KrisFlyer, RMS, OCC |
| **Stack** | S3 lake · Spark/Glue · Kafka · Airflow · dbt · Snowflake/BigQuery |
| **Environments** | `dev` · `uat` · `prod` — see [`config/platform.yaml`](config/platform.yaml) |

> **Notice:** Architecture and code samples are **illustrative** for data-team review. No production credentials, PNR data, or confidential airline content.

| Acronym | Full name |
|---------|-----------|
| **PSS** | Passenger Service System |
| **DCS** | Departure Control System |
| **OCC** | Operations Control Center |
| **RMS** | Revenue Management System |
| **KrisFlyer** | Frequent-flyer / loyalty program |
| **PNR** | Passenger Name Record |

Glossary: [`docs/00-source-system-glossary.md`](docs/00-source-system-glossary.md)

---

## Contents

1. [Business context](#1-business-context)
2. [Architecture](#2-architecture)
3. [Engineering artifacts](#3-engineering-artifacts)
4. [Gold schema](#4-gold-schema)
5. [Repository layout](#5-repository-layout)

---

## 1. Business context

### 1.1 Current state (typical full-service carrier)

| Dimension | As-is |
|-----------|--------|
| **Commercial** | PSS (Amadeus) = booking system of record |
| **Loyalty** | KrisFlyer DB; tier lag vs PSS **24–48h** |
| **Operations** | DCS check-in; OCC delays — often outside warehouse |
| **Revenue** | RMS + settlement; ancillaries in PSP |
| **Identity** | PNR ID ≠ KrisFlyer ID ≠ CRM contact ID |

### 1.2 Pain points

| Pain | Impact | Symptom |
|------|--------|---------|
| No passenger 360 | Weak personalization | 3+ ID systems |
| Batch T+1 | RMS blind to intraday cancels | 18–36h pipelines |
| Ancillary leakage | Under-reported upsell KPIs | PSP ↔ PNR join breaks |
| OTP mismatch | Ops vs regulatory disagreement | DCS not in warehouse |
| DQ after publish | Wrong gold dashboards | BI finds nulls post-release |

Detail: [`docs/01-business-context.md`](docs/01-business-context.md)

### 1.3 Network KPIs

| KPI | Platform role |
|-----|----------------|
| **Load factor** | Consistent ASK / RPK grain |
| **Yield** | Revenue + RPK; FX + ancillary |
| **Ancillary revenue** | PSP + EMD + flown segment |
| **OTP** | Schedule vs actual (DCS + OCC) |

---

## 2. Architecture

### 2.1 As-is (batch silos)

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif','primaryColor':'#0B1F3F','primaryTextColor':'#FFFFFF','primaryBorderColor':'#C9A227','lineColor':'#5B7DB1','secondaryColor':'#E8EDF5','tertiaryColor':'#FFF8E7'}}}%%
flowchart TB
    classDef source fill:#0B1F3F,stroke:#C9A227,stroke-width:2px,color:#FFFFFF
    classDef ingest fill:#FFF8E7,stroke:#C9A227,stroke-width:2px,color:#0B1F3F
    classDef store fill:#E8EDF5,stroke:#5B7DB1,stroke-width:2px,color:#0B1F3F
    classDef bi fill:#C9A227,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F

    subgraph src["Source systems"]
        PSS["PSS · Amadeus<br/>bookings · tickets"]:::source
        DCS["DCS<br/>check-in · bags"]:::source
        KF["KrisFlyer · CRM"]:::source
        PAY["PSP · ancillaries"]:::source
    end
    subgraph etl["Nightly ETL"]
        T["Legacy ETL"]:::ingest
    end
    subgraph marts["Department marts"]
        M1["Commercial"]:::store
        M2["Revenue"]:::store
        M3["Network ops"]:::store
    end
    subgraph bi["Consumption"]
        TAB["Tableau · Power BI"]:::bi
    end
    PSS --> T
    DCS -.->|"often missing"| T
    KF --> T
    PAY --> T
    T --> M1 & M2 & M3
    M1 & M2 & M3 --> TAB
```

[`docs/02-as-is-architecture.md`](docs/02-as-is-architecture.md)

### 2.2 Target (lakehouse + streaming)

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif','primaryColor':'#0B1F3F','primaryTextColor':'#FFFFFF','primaryBorderColor':'#C9A227','lineColor':'#5B7DB1'}}}%%
flowchart TB
    classDef source fill:#0B1F3F,stroke:#C9A227,stroke-width:2px,color:#FFFFFF
    classDef stream fill:#FFF8E7,stroke:#C9A227,stroke-width:2px,color:#0B1F3F
    classDef bronze fill:#8D6E63,stroke:#4E342E,stroke-width:2px,color:#FFFFFF
    classDef silver fill:#78909C,stroke:#455A64,stroke-width:2px,color:#FFFFFF
    classDef gold fill:#C9A227,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F
    classDef dq fill:#E8EDF5,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F

    PSS["PSS batch<br/>Amadeus delta"]:::source
    DCS["DCS stream<br/>SIN hub events"]:::source
    K["MSK · Kafka"]:::stream
    B["Bronze · sq-analytics-lake"]:::bronze
    S["Silver · conformed"]:::silver
    DQ["DQ gate · CRITICAL block"]:::dq
    G["Gold · passenger_360 · KPIs"]:::gold

    PSS --> B
    DCS --> K --> B
    B --> S --> DQ --> G
```

| Principle | Implementation |
|-----------|----------------|
| **Medallion** | Bronze → Silver → Gold |
| **Passenger SSOT** | `dim_passenger` SCD2 + `xref_passenger_id` |
| **Hybrid ingest** | Batch PSS + Kafka DCS |
| **DQ shift-left** | Block gold on CRITICAL breach |
| **Lineage** | `pipeline_run_id` on every row |

[`docs/03-to-be-architecture.md`](docs/03-to-be-architecture.md)

### 2.3 Medallion flow

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif'}}}%%
flowchart LR
    classDef bronze fill:#8D6E63,stroke:#4E342E,stroke-width:2px,color:#FFFFFF
    classDef silver fill:#78909C,stroke:#455A64,stroke-width:2px,color:#FFFFFF
    classDef gold fill:#C9A227,stroke:#0B1F3F,stroke-width:3px,color:#0B1F3F

    B["Bronze<br/>immutable raw"]:::bronze
    S["Silver<br/>typed · deduped"]:::silver
    G["Gold<br/>KPIs · marts"]:::gold

    B -->|"Spark / Glue"| S
    S -->|"DQ contract"| G
```

---

## 3. Engineering artifacts

### 3.1 Pipeline map

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif'}}}%%
flowchart LR
    classDef legacy fill:#FFEBEE,stroke:#B71C1C,stroke-width:2px,color:#B71C1C
    classDef extract fill:#E3F2FD,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F
    classDef transform fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef stream fill:#FFF8E7,stroke:#C9A227,stroke-width:2px,color:#0B1F3F
    classDef dq fill:#E8EDF5,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F
    classDef gold fill:#C9A227,stroke:#0B1F3F,stroke-width:2px,color:#0B1F3F

    subgraph asis["Legacy"]
        LEG["legacy_ods_plsql.sql"]:::legacy
    end
    subgraph target["Target platform"]
        EXT["pss_booking_extract.sql"]:::extract
        BRZ["Bronze S3"]:::extract
        SPK["glue_booking_bronze_to_silver.py"]:::transform
        STR["kafka_dcs_checkin_landing.py"]:::stream
        AF["airflow_hybrid_etl_dag.py"]:::transform
        DBT["dbt_fact_flight_segment.sql"]:::transform
        DQC["dq_contract.py"]:::dq
        P360["gold_passenger_360.sql"]:::gold
    end
    LEG -.->|"replace"| EXT
    EXT --> BRZ --> SPK
    STR --> BRZ
    AF --> SPK --> DQC --> DBT --> P360
```

| Layer | Legacy | Target |
|-------|--------|--------|
| Transform | [`legacy_ods_plsql.sql`](samples/legacy_ods_plsql.sql) | [`glue_booking_bronze_to_silver.py`](samples/glue_booking_bronze_to_silver.py) |
| Extract | Full export | [`pss_booking_extract.sql`](samples/pss_booking_extract.sql) |
| Warehouse | Dept ODS | [`dim_passenger_scd2.sql`](samples/dim_passenger_scd2.sql), [`dbt_fact_flight_segment.sql`](samples/dbt_fact_flight_segment.sql) |
| Orchestration | Cron | [`airflow_hybrid_etl_dag.py`](samples/airflow_hybrid_etl_dag.py) |
| Streaming | — | [`kafka_dcs_checkin_landing.py`](samples/kafka_dcs_checkin_landing.py) |
| DQ | Post-BI | [`dq_contract.py`](samples/dq_contract.py), [`dq_load_factor_contract.sql`](samples/dq_load_factor_contract.sql) |
| Mart | Siloed CRM | [`gold_passenger_360.sql`](samples/gold_passenger_360.sql) |

### 3.2 Local validation

```powershell
cd samples
python dq_contract.py
$env:DRY_RUN=1
python glue_booking_bronze_to_silver.py
python kafka_dcs_checkin_landing.py
```

---

## 4. Gold schema

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontFamily':'Segoe UI, sans-serif'}}}%%
flowchart TB
    classDef dim fill:#0B1F3F,stroke:#C9A227,stroke-width:2px,color:#FFFFFF
    classDef fact fill:#FFF8E7,stroke:#C9A227,stroke-width:2px,color:#0B1F3F
    classDef xref fill:#E8EDF5,stroke:#5B7DB1,stroke-width:2px,color:#0B1F3F

    DP["DIM_PASSENGER<br/>golden_passenger_id<br/>krisflyer_tier · consent"]:::dim
    XR["XREF_PASSENGER_ID<br/>PSS · KrisFlyer · CRM"]:::xref
    DF["DIM_FLIGHT<br/>SQ flight · SIN hub<br/>sched · actual UTC"]:::dim
    FB["FACT_BOOKING<br/>pnr_locator · channel"]:::fact
    FS["FACT_FLIGHT_SEGMENT<br/>cabin · fare · status"]:::fact
    FA["FACT_ANCILLARY<br/>seat · bag · lounge"]:::fact
    FP["FACT_PAYMENT<br/>PSP auth · capture"]:::fact

    DP --> XR
    DP --> FB
    FB --> FS
    DF --> FS
    FS --> FA
    FB --> FP
```

| Table | Type | Sources |
|-------|------|---------|
| **DIM_PASSENGER** | Dimension | KrisFlyer, CRM |
| **XREF_PASSENGER_ID** | Bridge | PSS, KrisFlyer, CRM |
| **DIM_FLIGHT** | Dimension | PSS schedule, OCC actuals |
| **FACT_BOOKING** | Fact | PSS |
| **FACT_FLIGHT_SEGMENT** | Fact | PSS, DCS |
| **FACT_ANCILLARY** | Fact | Catalog, PSP |
| **FACT_PAYMENT** | Fact | PSP |

Full ERD: [`docs/05-database-schema.md`](docs/05-database-schema.md)

---

## 5. Repository layout

```text
├── README.md
├── config/platform.yaml          # env · lake paths · schedules
├── docs/                         # architecture & schema
├── samples/                      # runnable pipeline references
├── .github/workflows/ci.yml      # lint samples on push
└── requirements.txt
```

---

<details>
<summary><em>Internal — capability crosswalk (optional)</em></summary>

| Theme | Proof in repo |
|-------|----------------|
| ETL/ELT | Spark bronze→silver; dbt gold |
| Batch + stream | Airflow + Kafka DCS |
| Governance | SCD2, PII tags, `pipeline_run_id` |
| Airline domain | PSS, DCS, KrisFlyer, RMS, OCC |

</details>

---

*Singapore Airlines data platform reference · for client data-team review.*
