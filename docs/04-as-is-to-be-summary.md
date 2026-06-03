# As-is → to-be summary

| Dimension | **As-is** | **To-be** |
|-----------|-----------|-----------|
| **Ingestion** | Nightly batch only | Batch + **Kafka** for Departure Control System and Payment Service Provider |
| **Storage** | Department Operational Data Store silos | **Medallion** bronze / silver / gold |
| **Passenger ID** | Passenger Service System vs loyalty vs CRM IDs | **`golden_passenger_id`** + cross-reference table |
| **Grain** | Mixed leg/segment in one table | Documented **segment** and origin–destination facts |
| **Ancillary** | Payment orphan rows | Join payment → Passenger Name Record → segment → flight |
| **On-Time Performance** | Manual CSV | **Streaming** check-in + schedule conformed |
| **DQ** | BI finds issues post-publish | **Block gold** on CRITICAL breach |
| **Lineage** | Tribal knowledge | `pipeline_run_id`, catalog, OpenLineage |
| **AI/ML** | Ad hoc production snapshots | Governed **feature** tables + consent |
| **Governance** | Passenger Name Record copied widely | Catalog PII tags + role-based access |
| **Cost** | Repeated full Passenger Service System extracts | Incremental + partition pruning |
| **Tooling** | Talend / Informatica | **Spark**, **Airflow**, **dbt**, cloud warehouse |

---

## Capability mapping (job description)

| JD responsibility | To-be capability |
|-------------------|------------------|
| ETL/ELT pipelines | Spark bronze→silver; dbt silver→gold |
| Real-time ingestion | Kafka landing → silver micro-batch |
| Data lake / warehouse | Object store + Snowflake/Redshift/BigQuery gold |
| Airline domain integration | Passenger Service System, Departure Control System, Payment Service Provider, loyalty, Revenue Management System, Operations Control Center |
| AI/ML enablement | `passenger_360`, `feature_*` marts |
| Governance & security | PII tags, lineage, RBAC |
