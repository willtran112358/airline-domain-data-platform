-- Proposed: passenger dimension SCD2 — preserve loyalty tier from source; separate ML imputation

CREATE TABLE IF NOT EXISTS gold.dim_passenger (
  passenger_sk            BIGINT GENERATED ALWAYS AS IDENTITY,
  golden_passenger_id     VARCHAR(64) NOT NULL,
  valid_from              DATE NOT NULL,
  valid_to                DATE,
  is_current              BOOLEAN NOT NULL DEFAULT TRUE,
  loyalty_program_code    VARCHAR(16),
  loyalty_tier            VARCHAR(32),       -- from loyalty source only
  loyalty_points_balance  INTEGER,
  loyalty_tier_expiry     DATE,
  marketing_consent       BOOLEAN,
  home_country_code       CHAR(2),
  estimated_propensity_score DECIMAL(5,4),  -- ML feature; nullable
  is_imputed_score        BOOLEAN DEFAULT FALSE,
  source_system           VARCHAR(32),
  pipeline_run_id         VARCHAR(64),
  PRIMARY KEY (passenger_sk)
);

-- Close prior version on tier change
-- MERGE pattern: match on golden_passenger_id + is_current, close row, insert new
