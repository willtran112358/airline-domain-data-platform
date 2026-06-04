-- SQ · KrisFlyer passenger 360 mart

CREATE OR REPLACE VIEW gold.passenger_360 AS
SELECT
  p.golden_passenger_id,
  p.krisflyer_id,
  p.krisflyer_tier,
  p.krisflyer_miles_balance,
  p.marketing_consent,
  a.last_booking_ts_utc,
  a.booking_count_12m,
  a.ancillary_revenue_12m,
  a.preferred_cabin_class,
  a.home_airport_code
FROM gold.dim_passenger p
JOIN (
  SELECT
    b.golden_passenger_id,
    MAX(b.booking_ts_utc) AS last_booking_ts_utc,
    COUNT(DISTINCT b.booking_id) AS booking_count_12m,
    SUM(COALESCE(x.revenue_amount, 0)) AS ancillary_revenue_12m,
    MODE(s.cabin_class) AS preferred_cabin_class,
    MODE(f.origin_airport_code) AS home_airport_code
  FROM gold.fact_booking b
  JOIN gold.fact_flight_segment s ON b.booking_id = s.booking_id
  JOIN gold.dim_flight f ON s.flight_id = f.flight_id
  LEFT JOIN gold.fact_ancillary x ON s.segment_id = x.segment_id
  WHERE b.booking_ts_utc >= DATEADD(month, -12, CURRENT_DATE)
  GROUP BY b.golden_passenger_id
) a ON p.golden_passenger_id = a.golden_passenger_id
WHERE p.is_current = TRUE;
