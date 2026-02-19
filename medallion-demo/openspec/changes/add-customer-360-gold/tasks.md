# Implementation Tasks

## Phase 1: Core Pipeline
- [x] 1.1 Create `src/gold/customer_360.py` with DuckDB transforms
- [x] 1.2 Implement RFM scoring logic
- [x] 1.3 Implement LTV tier classification
- [x] 1.4 Create dbt model `gold_customer_360.sql`
- [x] 1.5 Add dbt schema tests (unique, not_null, accepted_values)

## Phase 2: Orchestration
- [x] 2.1 Add `customer_360_refresh` task to Airflow DAG
- [x] 2.2 Configure Silver → Gold dependency
- [x] 2.3 Add data quality gate before Gold publish

## Phase 3: Quality & Testing
- [x] 3.1 Unit tests for RFM scoring
- [x] 3.2 Unit tests for LTV classification
- [x] 3.3 Integration test with sample data
- [x] 3.4 Data quality checks (null rates, value ranges, referential integrity)

## Phase 4: Documentation
- [x] 4.1 Update Gold layer spec with Customer 360 requirements
- [x] 4.2 Add column-level documentation to dbt schema
- [x] 4.3 Update data dictionary
