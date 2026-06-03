-- Proposed: dbt model — silver booking + segment -> gold fact (grain: segment)

{{ config(
    materialized='incremental',
    unique_key='segment_id',
    on_schema_change='append_new_columns'
) }}

WITH silver_segment AS (
  SELECT *
  FROM {{ ref('silver_flight_segment') }}
  {% if is_incremental() %}
  WHERE last_modified_ts > (SELECT MAX(last_modified_ts) FROM {{ this }})
  {% endif %}
)

SELECT
  segment_id,
  booking_id,
  flight_id,
  departure_date_key,
  cabin_class,
  booking_class,
  segment_status,
  base_fare_amount,
  taxes_amount,
  currency_code,
  passenger_count,
  source_system,
  pipeline_run_id,
  last_modified_ts
FROM silver_segment
WHERE segment_status IN ('HK', 'TK', 'FLOWN', 'CANCELLED')
