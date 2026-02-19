# AGENTS.md — Multi-Agent Context

## Pipeline Agent
- Scope: src/bronze/, src/silver/, src/gold/
- Always use PySpark DataFrames, never pandas for production transforms
- Reference OpenSpec requirement IDs in docstrings
- All transforms must be idempotent

## Schema Agent
- Scope: src/schemas/
- When adding a new state: create mapping in state_mappings.py
- Every state needs: field_map, date_format, case_type_map, status_map
- Map all case types to VALID_CASE_TYPES enum

## Quality Agent
- Scope: src/quality/
- Quality gates use PySpark (not pandas)
- Bronze threshold: 95%, Silver: 98%, Gold: 99%

## BigQuery Agent
- Scope: bigquery/
- Use partitioning (filing_date) and clustering (state_code, case_type)
- External tables point to GCS Parquet paths
- Views use `suits_gold` dataset

## Adding a New State
1. Add config to config/pipeline_config.yaml
2. Add schema mapping to src/schemas/state_mappings.py
3. Add sample data generator to sample_data/
4. Run full pipeline test
5. Update README state coverage table
