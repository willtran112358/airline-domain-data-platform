-- Proposed: incremental PSS booking extract with watermark (Oracle / SQL Server style)
-- Run in 02:00-05:00 window; avoid PSS maintenance blackout

SELECT
  b.booking_id,
  b.pnr_locator,
  b.passenger_id,
  b.booking_ts_utc,
  b.sales_channel,
  b.booking_status,
  b.last_modified_ts
FROM pss.booking b
WHERE b.last_modified_ts > :watermark_ts
  AND b.last_modified_ts < :upper_bound_ts
  AND b.booking_status NOT IN ('TEST', 'DUMMY')
ORDER BY b.last_modified_ts;
