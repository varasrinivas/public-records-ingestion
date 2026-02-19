# Data Engineering Style Guide

## Python Conventions
- Python 3.11+ with type hints on all function signatures
- Docstrings required on all public functions (Google style)
- Reference the OpenSpec requirement ID in docstrings (e.g., "Implements: REQ-BRZ-001")
- Use `pathlib.Path` for all file operations
- Use `structlog` for all logging (no print statements in library code)

## Data Pipeline Rules
- Every pipeline stage must be idempotent (safe to re-run)
- All data files use Parquet format
- Every record must carry lineage metadata (_batch_id, _source_system, timestamps)
- Invalid records are quarantined, never silently dropped
- Quality gates must pass before data flows to the next layer

## SQL / dbt Conventions
- CTEs over subqueries (one CTE per transformation step)
- Column names: snake_case, descriptive, prefixed with context
- Always include `_silver_version` or `_gold_computed_at` metadata columns
- Aggregate tables must include the computation timestamp

## Testing
- Unit tests for all business logic (RFM scoring, LTV tiers, quality checks)
- Integration test that runs the full Bronze → Silver → Gold pipeline
- Data quality checks between every layer transition
- Minimum 80% code coverage on `src/`

## Error Handling
- Catch specific exceptions; never use bare `except:`
- Log errors with structured context (table, batch_id, record_count)
- Partial failures: commit successful records, log and quarantine failures

## Spec-Driven Development
- Check `openspec/specs/` before implementing any feature
- Use `/opsx:new` for new features, `/opsx:ff` to generate planning docs
- Human reviews spec deltas before agent writes any code
- Archive changes with `/opsx:archive` after implementation
