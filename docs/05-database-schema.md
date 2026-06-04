# Gold schema — Singapore Airlines analytics

Physical target: Snowflake / BigQuery / Databricks SQL.

---

## Relationships

```mermaid
erDiagram
    DIM_PASSENGER ||--o{ XREF_PASSENGER_ID : maps
    DIM_PASSENGER ||--o{ FACT_BOOKING : books
    DIM_FLIGHT ||--o{ FACT_FLIGHT_SEGMENT : operates
    FACT_BOOKING ||--|{ FACT_FLIGHT_SEGMENT : contains
    FACT_FLIGHT_SEGMENT ||--o{ FACT_ANCILLARY : upsell
    FACT_BOOKING ||--o{ FACT_PAYMENT : pays
```

---

## Core model (key columns)

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#0B1F3F','primaryTextColor':'#fff'}}}%%
flowchart TB
    classDef dim fill:#0B1F3F,stroke:#C9A227,color:#fff
    classDef fact fill:#FFF8E7,stroke:#C9A227,color:#0B1F3F
    classDef xref fill:#E8EDF5,stroke:#5B7DB1,color:#0B1F3F

    DP["DIM_PASSENGER<br/>krisflyer_tier · consent"]:::dim
    XR["XREF_PASSENGER_ID"]:::xref
    DF["DIM_FLIGHT<br/>SQ · SIN"]:::dim
    FB["FACT_BOOKING"]:::fact
    FS["FACT_FLIGHT_SEGMENT"]:::fact
    FA["FACT_ANCILLARY"]:::fact
    FP["FACT_PAYMENT"]:::fact

    DP --> XR & FB
    FB --> FS
    DF --> FS
    FS --> FA
    FB --> FP
```

---

## Tables (abbreviated)

| Table | Purpose |
|-------|---------|
| **DIM_PASSENGER** | SCD2 SSOT; KrisFlyer tier from source only |
| **XREF_PASSENGER_ID** | PSS / KrisFlyer / CRM crosswalk |
| **DIM_FLIGHT** | Schedule + OCC actuals for OTP |
| **FACT_BOOKING** | PNR header, channel |
| **FACT_FLIGHT_SEGMENT** | Yield / load factor grain |
| **FACT_ANCILLARY** | Seat, bag, lounge revenue |
| **FACT_PAYMENT** | PSP linkage |

---

## KPI grain

| KPI | Grain | Tables |
|-----|-------|--------|
| Load factor | Flight + cabin + date | `FACT_FLIGHT_SEGMENT`, `DIM_FLIGHT` |
| Yield | OD + cabin + month | `FACT_FLIGHT_SEGMENT` |
| Ancillary | Segment | `FACT_ANCILLARY` |
| OTP | Flight instance | `DIM_FLIGHT` + DCS |

---

## Partitioning

| Table | Partition | Cluster |
|-------|-----------|---------|
| `FACT_FLIGHT_SEGMENT` | `departure_date_key` | `flight_id` |
| `FACT_BOOKING` | `booking_ts_utc` (month) | `pnr_locator` |
| `DIM_PASSENGER` | — | `golden_passenger_id` |

---

## Source mapping

| Source | Bronze | Gold |
|--------|--------|------|
| PSS (Amadeus) | `booking_raw` | `FACT_BOOKING`, `FACT_FLIGHT_SEGMENT` |
| DCS | `checkin_event` | `segment_status` enrich |
| KrisFlyer | `member_profile` | `DIM_PASSENGER`, `XREF` |
| PSP | `payment_auth` | `FACT_PAYMENT` |
| OCC | `delay_event` | `DIM_FLIGHT` actual times |
