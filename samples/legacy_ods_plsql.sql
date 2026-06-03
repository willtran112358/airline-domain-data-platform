-- AS-IS anti-pattern: nightly ODS load from PSS export (simplified)
-- Issues: NULL fare -> 0, no lineage, mixed segment grain, status drift

CREATE OR REPLACE PROCEDURE load_booking_ods AS
BEGIN
  MERGE INTO ods.booking_daily tgt
  USING (
    SELECT
      b.pnr_locator,
      b.passenger_id,
      NVL(s.base_fare, 0) AS base_fare,           -- masks NULL -> wrong yield
      NVL(s.segment_status, 'OK') AS segment_status,  -- hides cancelled
      SYSDATE AS load_dt
    FROM staging.pss_booking_export b
    LEFT JOIN staging.pss_segment_export s
      ON b.pnr_locator = s.pnr_locator
  ) src
  ON (tgt.pnr_locator = src.pnr_locator)
  WHEN MATCHED THEN UPDATE SET
    tgt.base_fare = src.base_fare,
    tgt.segment_status = src.segment_status,
    tgt.load_dt = src.load_dt
  WHEN NOT MATCHED THEN INSERT VALUES (
    src.pnr_locator, src.passenger_id, src.base_fare,
    src.segment_status, src.load_dt
  );
END;
/
