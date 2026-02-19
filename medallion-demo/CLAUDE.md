# Project: Medallion Architecture Data Engineering Demo

## Architecture
This is a spec-driven data lakehouse using the medallion pattern:
- **Bronze** (`src/bronze/`): Raw ingestion, append-only, schema-on-read
- **Silver** (`src/silver/`): Cleansed, deduplicated, validated, quarantined rejects
- **Gold** (`src/gold/`): Business aggregates, star schema, pre-computed KPIs

## Specifications
All requirements are in `openspec/specs/`. Always check the relevant spec before
implementing changes. Use the OpenSpec workflow:
`/opsx:new <feature>` → `/opsx:ff` → review → `/opsx:apply` → `/opsx:archive`

## Conventions
- Python 3.11+, type hints required
- DuckDB for local processing, BigQuery/Spark for production
- Parquet files for all layer storage
- Structured logging via structlog
- pytest for testing, minimum 80% coverage
- Data quality checks between every layer transition

## Testing
```bash
pytest tests/ -v --cov=src
```

## Key Commands
```bash
python sample_data/generate_sample_data.py     # Generate test data
python -m src.bronze.ingest --date 2025-01-15  # Run Bronze
python -m src.silver.transform                  # Run Silver
```
