"""
Proposed: Spark job — PSS booking bronze -> silver with lineage and DQ hooks.
Set DRY_RUN=1 to validate logic without a cluster.
"""
import os
from datetime import datetime, timezone

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"


def validate_segment(row: dict) -> dict | None:
    base_fare = row.get("base_fare_amount")
    if base_fare is not None and float(base_fare) < 0:
        return None  # quarantine
    status = (row.get("segment_status") or "").upper()
    if status in ("", "UNKNOWN"):
        return None
    return row


def transform_booking(bronze_row: dict, run_id: str) -> dict:
    silver = {
        "booking_id": bronze_row["booking_id"],
        "pnr_locator": bronze_row["pnr_locator"],
        "source_passenger_id": bronze_row.get("passenger_id"),
        "booking_ts_utc": bronze_row.get("booking_ts_utc"),
        "sales_channel": bronze_row.get("sales_channel"),
        "booking_status": bronze_row.get("booking_status"),
        "source_system": "PSS_NAVITAIRE",
        "ingest_ts": datetime.now(timezone.utc).isoformat(),
        "pipeline_run_id": run_id,
    }
    return silver


def run():
    run_id = os.environ.get("PIPELINE_RUN_ID", "local-dev")
    sample_bronze = {
        "booking_id": "BK-1001",
        "pnr_locator": "ABC123",
        "passenger_id": "PAX-9",
        "booking_ts_utc": "2026-06-01T10:00:00Z",
        "sales_channel": "WEB",
        "booking_status": "CONFIRMED",
        "base_fare_amount": "250.00",
        "segment_status": "HK",
    }

    if DRY_RUN:
        seg = validate_segment(sample_bronze)
        out = transform_booking(sample_bronze, run_id) if seg else None
        print({"dry_run": True, "silver_row": out})
        return

    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, current_timestamp, lit

    spark = SparkSession.builder.appName("airline-booking-bronze-silver").getOrCreate()
    bronze = spark.read.parquet("s3://airline-lake/bronze/pss/booking/")
    silver = (
        bronze.filter(col("booking_status").isin(["CONFIRMED", "TICKETED", "CANCELLED"]))
        .withColumn("source_system", lit("PSS_NAVITAIRE"))
        .withColumn("pipeline_run_id", lit(run_id))
        .withColumn("ingest_ts", current_timestamp())
    )
    (
        silver.write.mode("overwrite")
        .partitionBy("booking_date")
        .parquet("s3://airline-lake/silver/commercial/booking/")
    )


if __name__ == "__main__":
    run()
