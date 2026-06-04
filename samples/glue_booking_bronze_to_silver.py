"""
SQ analytics — PSS booking bronze -> silver (Glue/Spark).
Env: PIPELINE_RUN_ID, DRY_RUN=1 for local validation.
"""
import os
from datetime import datetime, timezone

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
LAKE = os.environ.get("SQ_LAKE_BUCKET", "sq-analytics-lake-prod")


def validate_segment(row: dict) -> dict | None:
    fare = row.get("base_fare_amount")
    if fare is not None and float(fare) < 0:
        return None
    if (row.get("segment_status") or "").upper() in ("", "UNKNOWN"):
        return None
    return row


def transform_booking(bronze: dict, run_id: str) -> dict:
    return {
        "booking_id": bronze["booking_id"],
        "pnr_locator": bronze["pnr_locator"],
        "source_passenger_id": bronze.get("passenger_id"),
        "booking_ts_utc": bronze.get("booking_ts_utc"),
        "sales_channel": bronze.get("sales_channel"),
        "booking_status": bronze.get("booking_status"),
        "carrier_code": "SQ",
        "source_system": "PSS_AMADEUS",
        "ingest_ts": datetime.now(timezone.utc).isoformat(),
        "pipeline_run_id": run_id,
    }


def run():
    run_id = os.environ.get("PIPELINE_RUN_ID", "sq-dev-local")
    sample = {
        "booking_id": "SQ-BK-8842101",
        "pnr_locator": "5KQZ2A",
        "passenger_id": "PSS-44102",
        "booking_ts_utc": "2026-06-01T02:15:00Z",
        "sales_channel": "SINGAPOREAIR_COM",
        "booking_status": "CONFIRMED",
        "base_fare_amount": "1280.00",
        "segment_status": "HK",
    }

    if DRY_RUN:
        seg = validate_segment(sample)
        print({"dry_run": True, "silver_row": transform_booking(sample, run_id) if seg else None})
        return

    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, current_timestamp, lit

    spark = SparkSession.builder.appName("sq-booking-bronze-silver").getOrCreate()
    bronze = spark.read.parquet(f"s3://{LAKE}/bronze/pss/booking/")
    (
        bronze.filter(col("booking_status").isin(["CONFIRMED", "TICKETED", "CANCELLED"]))
        .withColumn("carrier_code", lit("SQ"))
        .withColumn("source_system", lit("PSS_AMADEUS"))
        .withColumn("pipeline_run_id", lit(run_id))
        .withColumn("ingest_ts", current_timestamp())
        .write.mode("overwrite")
        .partitionBy("booking_date")
        .parquet(f"s3://{LAKE}/silver/commercial/booking/")
    )


if __name__ == "__main__":
    run()
