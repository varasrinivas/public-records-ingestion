# Medallion Architecture — Spec-Driven AI Development Demo

A complete data engineering demo application that uses **OpenSpec** spec-driven
development to build a production-grade **medallion architecture** (Bronze → Silver → Gold)
data lakehouse pipeline.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Postgres │  │ REST API │  │ CSV/JSON │  │ Kafka    │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │              │              │              │                  │
│  ═════╪══════════════╪══════════════╪══════════════╪═════════════     │
│       ▼              ▼              ▼              ▼                  │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  🥉 BRONZE LAYER — Raw Ingestion                           │     │
│  │  • Append-only, schema-on-read                              │     │
│  │  • Source metadata + ingestion timestamp                     │     │
│  │  • Partitioned by ingestion_date                             │     │
│  │  • Formats: Parquet (Delta Lake)                             │     │
│  └────────────────────────┬────────────────────────────────────┘     │
│                           │ Data Quality Gate                        │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  🥈 SILVER LAYER — Cleansed & Conformed                    │     │
│  │  • Deduplicated, validated, type-cast                       │     │
│  │  • Standardized schemas & naming                            │     │
│  │  • SCD Type 2 for dimension tables                          │     │
│  │  • Quarantine table for rejected rows                       │     │
│  └────────────────────────┬────────────────────────────────────┘     │
│                           │ Business Logic Gate                      │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  🥇 GOLD LAYER — Business-Ready Aggregates                 │     │
│  │  • Pre-computed KPIs & metrics                              │     │
│  │  • Star schema (facts + dimensions)                         │     │
│  │  • Optimized for BI tools (Looker, Tableau, PowerBI)        │     │
│  │  • Partitioned & clustered for query performance            │     │
│  └─────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

## Spec-Driven Workflow

This project demonstrates how to use **OpenSpec** to drive the entire
development lifecycle with AI coding agents:

```bash
# 1. Initialize OpenSpec in your project
npm install -g @fission-ai/openspec@latest
openspec init

# 2. Create a change for a new pipeline feature
/opsx:new add-customer-360-gold

# 3. Fast-forward to generate specs, design, and tasks
/opsx:ff

# 4. Review the spec deltas (human reviews intent before code)
# Edit openspec/changes/add-customer-360-gold/specs/*.md

# 5. Agent implements against the approved spec
/opsx:apply

# 6. Archive and update living specs
/opsx:archive
```

## Project Structure

```
medallion-demo/
├── openspec/                          ← Spec-driven development
│   ├── specs/                         ← Living specifications
│   │   ├── bronze-ingestion/
│   │   ├── silver-transformation/
│   │   ├── gold-aggregation/
│   │   └── data-quality/
│   └── changes/                       ← Active changes
│       └── add-customer-360-gold/
├── src/                               ← Application code
│   ├── bronze/                        ← Raw ingestion layer
│   ├── silver/                        ← Cleansing & conforming
│   ├── gold/                          ← Business aggregates
│   ├── quality/                       ← Data quality framework
│   └── utils/                         ← Shared utilities
├── dbt/                               ← dbt models (SQL transforms)
│   └── models/
│       ├── bronze/
│       ├── silver/
│       └── gold/
├── airflow/                           ← Orchestration DAGs
│   └── dags/
├── tests/                             ← Comprehensive tests
│   ├── unit/
│   ├── integration/
│   └── data_quality/
├── config/                            ← Environment configs
├── docker/                            ← Docker setup
├── .gemini/                           ← AI assistant configs
└── CLAUDE.md                          ← Claude Code context
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with sample data
python -m src.bronze.ingest --source sample_data/
python -m src.silver.transform --date 2025-01-15
python -m src.gold.aggregate --date 2025-01-15

# Run tests
pytest tests/ -v

# Run data quality suite
python -m src.quality.runner --layer bronze --date 2025-01-15
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Storage | Delta Lake on Cloud Storage (GCS/S3) |
| Processing | Apache Spark / DuckDB (local) |
| Orchestration | Apache Airflow |
| SQL Transforms | dbt |
| Data Quality | Great Expectations + custom framework |
| Schema Registry | OpenSpec living specs |
| AI Agents | Gemini Code Assist / Claude Code / Copilot |

## Links
- [OpenSpec](https://openspec.dev) — Spec-driven AI development
- [Delta Lake](https://delta.io) — ACID transactions on data lakes
- [dbt](https://www.getdbt.com) — SQL-based transformations
- [Great Expectations](https://greatexpectations.io) — Data quality
