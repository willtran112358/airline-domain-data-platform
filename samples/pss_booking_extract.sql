-- SQ · incremental PSS (Amadeus) booking extract — UTC watermark window

SELECT
  b.booking_id,
  b.pnr_locator,
  b.passenger_id,
  b.booking_ts_utc,
  b.sales_channel,
  b.booking_status,
  b.marketing_carrier_code,  -- SQ
  b.last_modified_ts
FROM pss_amadeus.booking b
WHERE b.marketing_carrier_code = 'SQ'
  AND b.last_modified_ts > :watermark_ts
  AND b.last_modified_ts < :upper_bound_ts
  AND b.booking_status NOT IN ('TEST', 'DUMMY')
ORDER BY b.last_modified_ts;
