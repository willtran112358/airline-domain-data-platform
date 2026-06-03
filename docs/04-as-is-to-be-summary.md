# As-is → to-be summary

| Dimension | **As-is** | **To-be** |
|-----------|-----------|-----------|
| **Ingestion** | Nightly batch only | Batch + **Kafka** for booking, DCS, payment |
| **Storage** | Dept ODS silos | **Medallion** bronze / silver / gold |
| **Passenger ID** | PSS vs loyalty vs CRM IDs | **`golden_passenger_id`** + xref table |
| **Grain** | Mixed leg/segment in one table | Documented **segment** and **OD** facts |
| **Ancillary** | Payment orphan rows | Join payment → PNR → segment → flight |
| **OTP / ops** | Manual CSV | **Streaming** check-in + schedule conformed |
| **DQ** | BI finds issues post-publish | **Block gold** on CRITICAL breach |
| **Lineage** | Tribal knowledge | `pipeline_run_id`, catalog, OpenLineage |
| **AI/ML** | Ad hoc prod snapshots | Governed **feature** tables + consent |
| **Governance** | PII copied widely | Lake Formation / Purview tags + RBAC |
| **Cost** | Repeated full PSS extracts | Incremental + partition pruning |
| **Tooling** | Talend / Informatica | **Spark**, **Airflow**, **dbt**, cloud DW |

---

## Capability mapping (JD)

| JD responsibility | To-be capability |
|-------------------|------------------|
| ETL/ELT pipelines | Spark on bronze→silver; dbt on silver→gold |
| Real-time ingestion | Kafka landing → silver micro-batch |
| Data lake / warehouse | S3 + Snowflake/Redshift gold |
| Data quality & observability | GX + SQL contracts + CloudWatch |
| Airline domain integration | PSS, DCS, payment, loyalty, RMS, ops |
| AI/ML enablement | `passenger_360`, `feature_*` marts |
| Governance & security | PII tags, lineage, RBAC |
