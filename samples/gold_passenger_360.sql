-- Proposed: passenger 360 mart for marketing, loyalty, and personalization

CREATE OR REPLACE VIEW gold.passenger_360 AS
SELECT
  p.golden_passenger_id,
  p.loyalty_tier,
  p.loyalty_points_balance,
  p.marketing_consent,
  agg.last_booking_ts_utc,
  agg.booking_count_12m,
  agg.ancillary_revenue_12m,
  agg.preferred_cabin_class,
  agg.home_airport_code
FROM gold.dim_passenger p
JOIN (
  SELECT
    b.golden_passenger_id,
    MAX(b.booking_ts_utc) AS last_booking_ts_utc,
    COUNT(DISTINCT b.booking_id) AS booking_count_12m,
    SUM(COALESCE(a.revenue_amount, 0)) AS ancillary_revenue_12m,
    MODE(s.cabin_class) AS preferred_cabin_class,
    MODE(f.origin_airport_code) AS home_airport_code
  FROM gold.fact_booking b
  JOIN gold.fact_flight_segment s ON b.booking_id = s.booking_id
  JOIN gold.dim_flight f ON s.flight_id = f.flight_id
  LEFT JOIN gold.fact_ancillary a ON s.segment_id = a.segment_id
  WHERE b.booking_ts_utc >= DATEADD(month, -12, CURRENT_DATE)
  GROUP BY b.golden_passenger_id
) agg ON p.golden_passenger_id = agg.golden_passenger_id
WHERE p.is_current = TRUE;
