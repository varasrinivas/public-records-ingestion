# Gold Layer — Suits Best View Specification

## Purpose
Produce consumer-ready "best view" datasets for analytics, search, and
downstream applications. Materialized in BigQuery for SQL access.

## Requirements

### REQ-GLD-001: Suit Best View Table
The system SHALL produce `gold.suit_best_view` containing:
- One row per unique suit (latest data from Silver)
- All canonical suit fields from Silver
- Enrichment: `days_open` (filing_date to today or disposition_date)
- Enrichment: `year_filed` (extracted from filing_date)
- Enrichment: `plaintiff_count`, `defendant_count`
- Enrichment: `primary_plaintiff`, `primary_defendant` (first listed)
- Partitioned by `state_code`, clustered by `case_type`, `year_filed`

### REQ-GLD-002: Party Best View Table
The system SHALL produce `gold.suit_party_best_view` containing:
- One row per party per suit
- Resolved party name (deduplicated across appearances)
- Cross-suit metrics: `total_suits_as_plaintiff`, `total_suits_as_defendant`
- `first_appearance_date`, `last_appearance_date`
- `is_frequent_litigant`: true if party appears in 10+ suits

### REQ-GLD-003: Analytics Aggregate Tables
The system SHALL produce pre-computed analytics:

#### gold.suit_state_summary
- `state_code`, `year_filed`, `case_type`
- `suit_count`, `avg_days_to_disposition`, `disposition_rate`
- `top_plaintiff` (most frequent plaintiff in that state/year/type)
- `median_amount_demanded` (where available)

#### gold.suit_monthly_trends
- `year_month`, `state_code`, `case_type`
- `new_filings`, `dispositions`, `open_cases_snapshot`
- `filing_trend_3m_avg`, `filing_trend_yoy_pct`

### REQ-GLD-004: BigQuery Materialization
- Gold tables SHALL be materialized as BigQuery tables
- Parquet files on GCS as backing store
- BigQuery external tables pointing to GCS Parquet
- Scheduled refresh via Airflow (daily)
- Table expiration: never (persistent)

### REQ-GLD-005: Data Freshness
- Gold tables SHALL be updated within 4 hours of Bronze ingestion
- Freshness metadata: `_gold_refreshed_at` timestamp on every table
- Staleness alert if Gold is >8 hours behind
