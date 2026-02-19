-- BigQuery DDL for Gold Layer Tables
-- These create external tables pointing to GCS Parquet files
-- and materialized views for optimized querying.

-- ═══════════════════════════════════════════════════════════
-- External table: suit_best_view (backed by GCS Parquet)
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE EXTERNAL TABLE \`suits_gold.suit_best_view_ext\`
WITH PARTITION COLUMNS (
  state_code STRING
)
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://your-bucket/us-suits/gold/suit_best_view/*'],
  hive_partition_uri_prefix = 'gs://your-bucket/us-suits/gold/suit_best_view/'
);

-- Materialized table (refreshed by Airflow)
CREATE TABLE IF NOT EXISTS \`suits_gold.suit_best_view\` (
  suit_id STRING NOT NULL,
  state_code STRING NOT NULL,
  county STRING,
  case_number STRING NOT NULL,
  case_type STRING,
  case_type_raw STRING,
  filing_date DATE,
  year_filed INT64,
  case_status STRING,
  case_status_raw STRING,
  court_name STRING,
  judge_name STRING,
  cause_of_action STRING,
  amount_demanded NUMERIC(18,2),
  disposition STRING,
  disposition_date DATE,
  days_open INT64,
  primary_plaintiff STRING,
  primary_defendant STRING,
  plaintiff_count INT64,
  defendant_count INT64,
  _gold_refreshed_at TIMESTAMP
)
PARTITION BY DATE_TRUNC(filing_date, MONTH)
CLUSTER BY state_code, case_type
OPTIONS (
  description = 'Consumer-ready best view of US court suits across all states'
);

-- ═══════════════════════════════════════════════════════════
-- External table: suit_party_best_view
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS \`suits_gold.suit_party_best_view\` (
  party_id STRING NOT NULL,
  suit_id STRING NOT NULL,
  party_type STRING NOT NULL,
  party_name STRING NOT NULL,
  party_name_raw STRING,
  is_entity BOOLEAN,
  attorney_name STRING,
  attorney_firm STRING,
  total_suits_as_plaintiff INT64,
  total_suits_as_defendant INT64,
  first_appearance_date DATE,
  last_appearance_date DATE,
  total_appearances INT64,
  is_frequent_litigant BOOLEAN,
  _gold_refreshed_at TIMESTAMP
)
PARTITION BY DATE_TRUNC(first_appearance_date, YEAR)
CLUSTER BY party_type, is_frequent_litigant
OPTIONS (
  description = 'Party-level best view with cross-suit litigation metrics'
);

-- ═══════════════════════════════════════════════════════════
-- Analytics: suit_state_summary
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS \`suits_gold.suit_state_summary\` (
  state_code STRING NOT NULL,
  year_filed INT64,
  case_type STRING,
  suit_count INT64,
  avg_days_to_disposition FLOAT64,
  disposition_rate FLOAT64,
  _gold_refreshed_at TIMESTAMP
)
PARTITION BY RANGE_BUCKET(year_filed, GENERATE_ARRAY(2020, 2030, 1))
CLUSTER BY state_code, case_type;
