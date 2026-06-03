# Database schema — airline analytics (gold layer)

Logical **star schema** for commercial + operational analytics. Physical implementation: Snowflake, Redshift, BigQuery, or Databricks SQL.

---

## 1. Entity-relationship diagram (full)

```mermaid
erDiagram
    DIM_AIRPORT ||--o{ DIM_ROUTE : connects
    DIM_AIRCRAFT ||--o{ DIM_FLIGHT : assigned
    DIM_CARRIER ||--o{ DIM_FLIGHT : operates
    DIM_FLIGHT ||--o{ FACT_FLIGHT_SEGMENT : instance
    DIM_PASSENGER ||--o{ FACT_BOOKING : books
    FACT_BOOKING ||--|{ FACT_FLIGHT_SEGMENT : contains
    FACT_FLIGHT_SEGMENT ||--o{ FACT_ANCILLARY : upsell
    FACT_BOOKING ||--o{ FACT_PAYMENT : pays
    FACT_FLIGHT_SEGMENT ||--o{ FACT_COUPON : documents
    DIM_PASSENGER ||--o{ XREF_PASSENGER_ID : maps
    DIM_DATE ||--o{ FACT_FLIGHT_SEGMENT : departs_on

    DIM_AIRPORT {
        string airport_code PK
        string airport_name
        string country_code
        string timezone_iana
    }

    DIM_ROUTE {
        string route_id PK
        string origin_airport_code FK
        string destination_airport_code FK
        int great_circle_distance_km
    }

    DIM_CARRIER {
        string carrier_code PK
        string carrier_name
        string alliance_code
    }

    DIM_AIRCRAFT {
        string aircraft_registration PK
        string aircraft_type
        int seat_capacity_economy
        int seat_capacity_business
    }

    DIM_FLIGHT {
        string flight_id PK
        string carrier_code FK
        string flight_number
        date flight_date
        string origin_airport_code FK
        string destination_airport_code FK
        string aircraft_registration FK
    }

    DIM_DATE {
        date date_key PK
        int year
        int month
        int week_of_year
        boolean is_holiday_flag
    }

    DIM_PASSENGER {
        bigint passenger_sk PK
        string golden_passenger_id NK
        date valid_from
        date valid_to
        boolean is_current
        string loyalty_program_code
        string loyalty_tier
        int loyalty_points_balance
        date loyalty_tier_expiry
        boolean marketing_consent
        string home_country_code
    }

    XREF_PASSENGER_ID {
        string golden_passenger_id PK
        string source_system PK
        string source_passenger_id PK
        timestamp first_seen_ts
        timestamp last_seen_ts
    }

    FACT_BOOKING {
        string booking_id PK
        string pnr_locator
        string golden_passenger_id FK
        timestamp booking_ts_utc
        string sales_channel
        string booking_status
        string office_id
        string ota_code
    }

    FACT_FLIGHT_SEGMENT {
        string segment_id PK
        string booking_id FK
        string flight_id FK
        date departure_date_key FK
        string cabin_class
        string booking_class
        string segment_status
        decimal base_fare_amount
        decimal taxes_amount
        string currency_code
        int passenger_count
    }

    FACT_COUPON {
        string coupon_id PK
        string segment_id FK
        string ticket_number
        int coupon_number
        string coupon_status
        timestamp coupon_issue_ts_utc
    }

    FACT_ANCILLARY {
        string ancillary_id PK
        string segment_id FK
        string product_category
        string product_code
        decimal revenue_amount
        string currency_code
        string fulfillment_status
        timestamp purchase_ts_utc
    }

    FACT_PAYMENT {
        string payment_id PK
        string booking_id FK
        string payment_method
        string payment_provider
        decimal amount
        string currency_code
        string auth_status
        timestamp auth_ts_utc
    }
```

---

## 2. KPI grain definitions

| KPI | Recommended grain | Key tables |
|-----|-------------------|------------|
| **Load Factor** | Flight + cabin + departure date | `FACT_FLIGHT_SEGMENT`, `DIM_FLIGHT` |
| **Yield** | OD + cabin + month | `FACT_FLIGHT_SEGMENT` + revenue fields |
| **Ancillary Revenue** | Segment or passenger-flight | `FACT_ANCILLARY` |
| **OTP** | Flight instance (actual vs scheduled) | `DIM_FLIGHT` + ops enrich |
| **Revenue Leakage** | Coupon vs flown segment | `FACT_COUPON` ⋈ `FACT_FLIGHT_SEGMENT` |

---

## 3. SCD2 — passenger dimension

| Column | Type | Notes |
|--------|------|-------|
| `passenger_sk` | BIGINT | Surrogate PK |
| `golden_passenger_id` | VARCHAR | NK — stable across sources |
| `valid_from` / `valid_to` | DATE | SCD2 window |
| `is_current` | BOOLEAN | Current row flag |
| `loyalty_tier` | VARCHAR | From loyalty system — not overwritten by ML |

---

## 4. Indexing & partitioning (physical hints)

| Table | Partition | Cluster / sort |
|-------|-----------|----------------|
| `FACT_FLIGHT_SEGMENT` | `departure_date_key` | `flight_id`, `booking_id` |
| `FACT_BOOKING` | `booking_ts_utc` (month) | `pnr_locator` |
| `FACT_ANCILLARY` | `purchase_ts_utc` (month) | `segment_id` |
| `DIM_PASSENGER` | N/A (slowly changing) | `golden_passenger_id` |

---

## 5. Source-to-target mapping (abbreviated)

| Source system | Bronze entity | Silver entity | Gold table |
|---------------|---------------|---------------|------------|
| PSS (Navitaire / Amadeus / Sabre) | `booking_raw`, `segment_raw` | `booking_conformed` | `FACT_BOOKING`, `FACT_FLIGHT_SEGMENT` |
| DCS | `checkin_event` | `segment_status_enriched` | `FACT_FLIGHT_SEGMENT.segment_status` |
| Payment PSP | `payment_auth` | `payment_conformed` | `FACT_PAYMENT` |
| Loyalty | `member_profile` | `passenger_conformed` | `DIM_PASSENGER`, `XREF_PASSENGER_ID` |
| RMS | `bid_price_snapshot` | `flight_inventory` | Features for yield (not in core star) |
| Flight ops | `delay_event` | `flight_actual_times` | `DIM_FLIGHT` enrich for OTP |
