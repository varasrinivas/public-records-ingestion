# AGENTS.md — Multi-Agent Context for Medallion Pipeline

## Project Overview
This is a spec-driven medallion architecture data engineering project.
All requirements live in `openspec/specs/`. Always check the relevant spec
before implementing changes.

## Architecture
```
Sources → Bronze (raw, append-only) → Silver (cleansed, deduped) → Gold (aggregates)
```

## Agent Responsibilities

### Data Pipeline Agent
- Scope: `src/bronze/`, `src/silver/`, `src/gold/`
- Always reference OpenSpec specs when implementing transforms
- Every function must be idempotent
- Add lineage metadata to every record
- Quarantine invalid records, never drop silently

### Data Quality Agent
- Scope: `src/quality/`, `tests/data_quality/`
- Enforce quality gates between layers
- Quality checks reference specs: REQ-DQ-001 through REQ-DQ-004
- Alert on pass rate below threshold (95% default)

### dbt Agent
- Scope: `dbt/models/`
- One CTE per transformation step
- Always include metadata columns
- Add schema tests in `schema.yml` for every model
- Reference source definitions in `sources.yml`

### Test Agent
- Scope: `tests/`
- Unit tests for business logic (RFM, LTV, quality checks)
- Integration tests run the full pipeline with sample data
- Name tests: `test_[function]_[scenario]`

## Key Files
| File | Purpose |
|------|---------|
| `config/pipeline_config.yaml` | All pipeline configuration |
| `openspec/specs/` | Living specifications (source of truth) |
| `run_pipeline.py` | Convenience runner for full pipeline |
| `sample_data/generate_sample_data.py` | Test data generator |

## Conventions
- Python 3.11+, type hints required
- Parquet for all data storage
- DuckDB for local processing
- structlog for logging
- pytest for testing (80% coverage minimum)
