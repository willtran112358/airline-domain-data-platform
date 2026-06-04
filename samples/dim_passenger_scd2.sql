-- SQ · passenger dimension SCD2 — KrisFlyer tier from source only

CREATE TABLE IF NOT EXISTS gold.dim_passenger (
  passenger_sk            BIGINT GENERATED ALWAYS AS IDENTITY,
  golden_passenger_id     VARCHAR(64) NOT NULL,
  valid_from              DATE NOT NULL,
  valid_to                DATE,
  is_current              BOOLEAN NOT NULL DEFAULT TRUE,
  krisflyer_id            VARCHAR(32),
  krisflyer_tier          VARCHAR(32),   -- PPS / Gold / Silver — source only
  krisflyer_miles_balance INTEGER,
  marketing_consent       BOOLEAN,
  home_country_code       CHAR(2),
  pipeline_run_id         VARCHAR(64),
  source_system           VARCHAR(32),
  PRIMARY KEY (passenger_sk)
);
