# As-is → target summary

| Dimension | As-is | Target |
|-----------|-------|--------|
| Ingestion | Nightly batch | Batch PSS + **Kafka** DCS |
| Storage | Dept ODS silos | **Medallion** lake |
| Passenger ID | PNR ≠ KrisFlyer ≠ CRM | **`golden_passenger_id`** + xref |
| Ancillary | Orphan PSP rows | PNR → segment → flight |
| OTP | Manual OCC CSV | DCS stream + schedule conform |
| DQ | Post-BI | **Block gold** on CRITICAL |
| Lineage | Tribal | `pipeline_run_id`, catalog |
| Tooling | Legacy ETL | Spark, Airflow, dbt |

---

## Capability outcomes

| Outcome | Target proof |
|---------|--------------|
| Unified commercial ops | Shared gold star schema |
| KrisFlyer 360 | `passenger_360` mart |
| Intraday ops | DCS Kafka landing |
| Governed KPIs | `dq_contract.py` + SQL checks |
