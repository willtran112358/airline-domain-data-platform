"""
Proposed: Airflow DAG — hybrid batch (PSS) + streaming checkpoint (DCS/payment).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airline-data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}


def run_dq_gate(**context):
    run_id = context["dag_run"].run_id
    # Integrate Great Expectations or SQL checks; raise on CRITICAL
    critical_failures = []
    if critical_failures:
        raise ValueError(f"DQ CRITICAL: {critical_failures}")
    print(f"DQ passed for run_id={run_id}")


with DAG(
    dag_id="airline_hybrid_commercial_etl",
    default_args=default_args,
    schedule_interval="0 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["airline", "pss", "medallion"],
) as dag:
    start = EmptyOperator(task_id="start")

    extract_pss = EmptyOperator(task_id="extract_pss_booking_incremental")
    bronze_to_silver = EmptyOperator(task_id="spark_booking_bronze_to_silver")
    silver_to_gold = EmptyOperator(task_id="dbt_silver_to_gold_marts")
    stream_checkpoint = EmptyOperator(task_id="dcs_payment_stream_checkpoint")
    dq_gate = PythonOperator(task_id="dq_gate_before_gold", python_callable=run_dq_gate)
    publish = EmptyOperator(task_id="publish_gold_to_bi")

    start >> extract_pss >> bronze_to_silver >> dq_gate
    start >> stream_checkpoint >> dq_gate
    dq_gate >> silver_to_gold >> publish
