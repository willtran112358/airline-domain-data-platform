-- Proposed: gold-layer DQ — load factor inputs must be internally consistent

-- CRITICAL: negative or zero available seats
SELECT flight_id, cabin_class, available_seats
FROM gold.fact_flight_inventory_daily
WHERE available_seats <= 0;

-- CRITICAL: flown passengers exceed capacity (data error)
SELECT f.flight_id, f.cabin_class, f.flown_passengers, i.available_seats
FROM gold.fact_flight_performance_daily f
JOIN gold.fact_flight_inventory_daily i
  ON f.flight_id = i.flight_id AND f.cabin_class = i.cabin_class
WHERE f.flown_passengers > i.available_seats;

-- WARNING: ancillary revenue without matching segment
SELECT a.ancillary_id, a.segment_id
FROM gold.fact_ancillary a
LEFT JOIN gold.fact_flight_segment s ON a.segment_id = s.segment_id
WHERE s.segment_id IS NULL;
