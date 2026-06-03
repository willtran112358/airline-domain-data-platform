"""
Proposed: land DCS check-in events to bronze (Kafka -> object store).
Near real-time input for OTP and gate management dashboards.
"""
import json
import os
from datetime import datetime, timezone

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"


def enrich_event(raw: dict, run_id: str) -> dict:
    return {
        **raw,
        "ingest_ts": datetime.now(timezone.utc).isoformat(),
        "source_system": "DCS",
        "pipeline_run_id": run_id,
        "event_type": "CHECK_IN",
    }


def run():
    run_id = os.environ.get("PIPELINE_RUN_ID", "stream-local")
    sample = {
        "pnr_locator": "ABC123",
        "segment_id": "SEG-1",
        "flight_id": "VN210-2026-06-03",
        "checkin_ts_utc": "2026-06-03T08:15:00Z",
        "bag_count": 1,
    }

    if DRY_RUN:
        print({"dry_run": True, "bronze_record": enrich_event(sample, run_id)})
        return

    # Production: confluent-kafka consumer -> S3 bronze partition by event_date
    from kafka import KafkaConsumer  # type: ignore

    consumer = KafkaConsumer(
        "dcs.checkin.v1",
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP"],
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    for msg in consumer:
        record = enrich_event(msg.value, run_id)
        # write to s3://airline-lake/bronze/dcs/checkin/dt=.../
        _ = record


if __name__ == "__main__":
    run()
