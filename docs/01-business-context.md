# Business context — airline data platform modernization

> **Disclaimer:** Composite narrative from typical airline / aviation data programs (PSS, loyalty, ops analytics). Educational portfolio — not official airline documentation.

---

## 1. Market & strategic drivers

| Driver | Why it matters now |
|--------|-------------------|
| **Recovery & yield pressure** | Post-disruption networks need agile pricing and capacity |
| **Ancillary revenue** | Bags, seats, meals — must be attributed to passenger and flight |
| **Personalization** | Loyalty + CRM need **passenger 360** across channels |
| **Operational resilience** | OTP, disruption management, crew/AC rotation — near real-time |
| **AI / ML** | Demand forecasting, churn, dynamic offers — needs governed features |
| **Regulatory & privacy** | PNR, payment PCI, GDPR/CCPA — lineage and access control |

---

## 2. Stakeholder map

```mermaid
flowchart LR
    classDef biz fill:#fff3e0,stroke:#ef6c00
    classDef tech fill:#e8f5e9,stroke:#2e7d32
    classDef ext fill:#e3f2fd,stroke:#1565c0

    CCO["CRO / CDO sponsor"]:::biz
    REV["Revenue Management"]:::biz
    OPS["Network / Flight Ops"]:::biz
    MKT["Marketing & Loyalty"]:::biz
    IT["Airline IT / Data owner"]:::tech
    PSS["PSS / DCS squad"]:::tech
    DE["Data engineering"]:::tech
    DS["Data Science / AI"]:::ext

    CCO --> IT
    REV --> DE
    OPS --> DE
    MKT --> DE
    IT --> DE
    PSS --> IT
    DE --> DS
```

---

## 3. As-is operating model

| Function | Typical behavior | Pain |
|----------|------------------|------|
| **Revenue Management** | RMS exports + Excel; stale booking snapshots | Cannot react intraday to cancellations |
| **Loyalty** | Separate warehouse from PSS | Tier status lags 24–48h |
| **Operations** | ACARS / ops DB siloed from commercial | OTP dashboards disagree with finance |
| **Marketing** | Campaign lists from CRM export | Duplicate passengers (PNR vs loyalty ID) |
| **Finance** | GL + settlement files T+1 | Ancillary leakage vs flown revenue |
| **Audit** | Sample PNR rows in Excel | No lineage from source to KPI |

---

## 4. Pain point deep dive

### 4.1 Passenger / customer fragmentation

- PSS **passenger_id** ≠ loyalty **member_id** ≠ CRM **contact_id**
- Same person books via OTA, airline.com, and call center — weak crosswalk
- **Email / phone** shared in family bookings → false duplicate merges

### 4.2 High-volume transactional lag

```
Booking (PSS) → nightly ETL → warehouse → RMS / marketing (T+1)
DCS check-in events → not in warehouse → ops dashboard manual
```

- Peak: **hundreds of thousands** of booking transactions/day on hub carriers
- Cancellations and schedule changes need **sub-hour** visibility for ops

### 4.3 Revenue leakage & ancillary blind spots

- Seat/bag fees in payment gateway not joined to **flown segment**
- **Yield** and **load factor** computed on different grains (leg vs segment vs OD)
- **Revenue leakage**: flown passengers without matching ticket document

### 4.4 Data quality discovered late

```
PSS export (optional fields) → ETL (status code mapping drift) → mart → Tableau
                                      ↑
                            No gate at silver; BI finds OTP drop weeks later
```

### 4.5 Governance & compliance

- PNR **PII** copied to multiple marts without classification
- No standard **audit columns** (`ingest_ts`, `pipeline_run_id`, `source_system`)
- AI teams train on **production snapshots** without anonymization workflow

---

## 5. Airline KPIs (business language)

| KPI | Definition (simplified) | Data pain if broken |
|-----|-------------------------|---------------------|
| **Load Factor** | RPK / ASK (or seats sold / seats available) | Double-count codeshare; wrong cabin grain |
| **Yield** | Revenue / RPK | FX timing; ancillary not in numerator |
| **Ancillary Revenue** | Non-ticket revenue per passenger / flight | Payment ↔ PNR join failures |
| **OTP (On-Time Performance)** | % arrivals within threshold | Ops clock vs published schedule mismatch |
| **Revenue Leakage** | Flown vs billed mismatch | Missing ticket–coupon linkage |

---

## 6. Executive one-liner

> *We cannot run revenue management, loyalty personalization, and operational control on disconnected batch silos — we need a governed lakehouse, passenger 360, and quality gates before gold KPIs reach the business.*

JD alignment: [`../README.md`](../README.md) §7
