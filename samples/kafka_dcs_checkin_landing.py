"""
SQ analytics — DCS check-in events (Kafka -> bronze).
Topic: sq.dcs.checkin.v1 — near real-time OTP / gate ops.
"""
import json
import os
from datetime import datetime, timezone

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
TOPIC = os.environ.get("DCS_TOPIC", "sq.dcs.checkin.v1")


def enrich_event(raw: dict, run_id: str) -> dict:
    return {
        **raw,
        "carrier_code": "SQ",
        "hub_airport": "SIN",
        "ingest_ts": datetime.now(timezone.utc).isoformat(),
        "source_system": "DCS",
        "pipeline_run_id": run_id,
        "event_type": "CHECK_IN",
    }


def run():
    run_id = os.environ.get("PIPELINE_RUN_ID", "sq-stream-local")
    sample = {
        "pnr_locator": "5KQZ2A",
        "segment_id": "SEG-SQ232-01",
        "flight_id": "SQ232-2026-06-03",
        "origin_airport": "SIN",
        "checkin_ts_utc": "2026-06-03T06:42:00Z",
        "bag_count": 2,
    }

    if DRY_RUN:
        print({"dry_run": True, "bronze_record": enrich_event(sample, run_id)})
        return

    from kafka import KafkaConsumer  # type: ignore

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP"],
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    for msg in consumer:
        record = enrich_event(msg.value, run_id)
        # s3://sq-analytics-lake-prod/bronze/dcs/checkin/dt=YYYY-MM-DD/


if __name__ == "__main__":
    run()
