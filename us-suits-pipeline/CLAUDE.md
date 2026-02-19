# Project: US Public Records — Suits Pipeline

## Architecture
Medallion architecture processing US court suit data from 6 states:
- **Bronze** (src/bronze/): PySpark raw ingestion, state-native schemas preserved
- **Silver** (src/silver/): PySpark canonical transformation, dedup, quarantine
- **Gold** (src/gold/): PySpark best views, loaded to BigQuery for consumers

## Specifications
All requirements in `openspec/specs/`. Check specs before implementing.
Key spec files:
- bronze-state-ingestion/spec.md — REQ-BRZ-001 through 006
- silver-canonical-suits/spec.md — REQ-SLV-001 through 008
- gold-best-view/spec.md — REQ-GLD-001 through 005
- data-quality/spec.md — REQ-DQ-001 through 004

## State Schemas
Mappings in `src/schemas/state_mappings.py`. Each state has unique:
- Field names (case_number vs docket_id vs index_number)
- Date formats (MM/dd/yyyy vs yyyyMMdd vs dd-MMM-yyyy)
- Case type codes (CV vs CIV vs Civil)
- Status codes (PEND vs Active vs OPEN)

## Tech Stack
- PySpark 3.5+ for all transforms
- BigQuery for Gold serving layer
- Parquet on GCS (local filesystem for dev)
- Airflow for orchestration

## Commands
```bash
python sample_data/generate_state_suits.py  # Generate test data
python run_pipeline.py --date 2025-01-15    # Full pipeline
pytest tests/ -v                             # Run tests
```
