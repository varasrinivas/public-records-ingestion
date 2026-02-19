# Suits Pipeline — Code Review Style Guide

## PySpark Conventions
- Use PySpark DataFrames for all production transforms, never pandas
- Column references: use `F.col("name")` over `df.name`
- Always import functions as `from pyspark.sql import functions as F`
- Chain transformations: `df.withColumn().filter().select()`
- Use `F.coalesce()` for null handling, never assume non-null
- Partition output by `state_code` for Bronze/Silver/Gold

## Data Pipeline Rules
- Every stage must be idempotent (`.mode("overwrite")`)
- Never drop records silently — quarantine invalid data
- Reference OpenSpec requirement IDs in docstrings (REQ-BRZ-001, etc.)
- Quality gates between every layer transition
- All date fields in ISO 8601 format after Silver

## BigQuery Conventions
- Partition by `filing_date` (MONTH granularity)
- Cluster by `state_code`, `case_type`
- Views in `suits_gold` dataset
- External tables for Parquet-backed access

## Schema Rules
- Every new state needs entries in `state_mappings.py`
- Case types must map to `VALID_CASE_TYPES`
- Statuses must map to `VALID_STATUSES`
- Date formats must be documented in the state config

## Testing
- PySpark tests use `chispa` for DataFrame assertions
- Unit tests for all state mappings and business logic
- Integration test runs full Bronze → Silver → Gold pipeline
- Minimum 80% coverage on `src/`
