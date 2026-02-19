# US Public Records — Suits Pipeline

A production-grade **spec-driven** data engineering pipeline that ingests raw
court suit/litigation records from multiple US states, transforms them into a
canonical format, and produces a consumer-ready "best view" using the
**medallion architecture**.

## Architecture

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                     RAW STATE COURT DATA                                │
 │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
 │  │  TX    │ │  CA    │ │  NY    │ │  FL    │ │  IL    │ │  OH    │   │
 │  │ Harris │ │  LA    │ │ Kings  │ │ Miami  │ │ Cook   │ │ Cuya-  │   │
 │  │ County │ │ County │ │ County │ │ -Dade  │ │ County │ │ hoga   │   │
 │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘   │
 │      │          │          │          │          │          │          │
 │ ═════╪══════════╪══════════╪══════════╪══════════╪══════════╪════════  │
 │      ▼          ▼          ▼          ▼          ▼          ▼          │
 │ ┌─────────────────────────────────────────────────────────────────┐    │
 │ │  🥉 BRONZE — Raw Ingestion (state-native schemas)             │    │
 │ │  • Each state's raw format preserved as-is                     │    │
 │ │  • PySpark reads CSV/JSON/XML → Parquet on GCS                 │    │
 │ │  • Partitioned by state_code / ingestion_date                  │    │
 │ └───────────────────────────┬─────────────────────────────────────┘    │
 │                             │  Data Quality Gate                       │
 │                             ▼                                          │
 │ ┌─────────────────────────────────────────────────────────────────┐    │
 │ │  🥈 SILVER — Canonical Suits Schema                           │    │
 │ │  • Unified schema across all states                            │    │
 │ │  • Field mapping: case_number→suit_id, cause→case_type, etc.  │    │
 │ │  • Party normalization (plaintiff/defendant extraction)        │    │
 │ │  • Date standardization, status harmonization                  │    │
 │ │  • Deduplication + quarantine for invalid records              │    │
 │ └───────────────────────────┬─────────────────────────────────────┘    │
 │                             │  Business Logic Gate                     │
 │                             ▼                                          │
 │ ┌─────────────────────────────────────────────────────────────────┐    │
 │ │  🥇 GOLD — Best View for Consumers                            │    │
 │ │  • suit_best_view: Single row per suit, latest state           │    │
 │ │  • suit_party_best_view: Resolved party records                │    │
 │ │  • suit_analytics: Pre-computed metrics by state/type/year     │    │
 │ │  • BigQuery external tables + materialized views               │    │
 │ └─────────────────────────────────────────────────────────────────┘    │
 └──────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Processing | **PySpark 3.5+** | Distributed transforms across all layers |
| Storage | **Parquet on GCS** | Columnar storage, partitioned |
| Warehouse | **BigQuery** | Gold layer serving, analytics queries |
| Orchestration | **Apache Airflow** | DAG scheduling, monitoring, alerting |
| Spec Framework | **OpenSpec** | Spec-driven development lifecycle |
| Data Quality | **Custom + Great Expectations** | Between-layer quality gates |

## Quick Start

```bash
# 1. Generate sample state court data
python sample_data/generate_state_suits.py

# 2. Run the full pipeline locally (PySpark local mode)
python run_pipeline.py --date 2025-01-15

# 3. Run individual layers
python -m src.bronze.ingest --state TX --date 2025-01-15
python -m src.silver.canonicalize --date 2025-01-15
python -m src.gold.build_best_view --date 2025-01-15

# 4. Run tests
pytest tests/ -v
```

## Project Structure

```
us-suits-pipeline/
├── openspec/                          ← Spec-driven development
│   ├── specs/
│   │   ├── bronze-state-ingestion/    ← Raw ingestion requirements
│   │   ├── silver-canonical-suits/    ← Canonical schema spec
│   │   ├── gold-best-view/            ← Consumer view requirements
│   │   └── data-quality/              ← Quality framework spec
│   └── changes/
│       └── add-oh-state-source/       ← Example: adding a new state
├── src/
│   ├── bronze/                        ← PySpark raw ingestion
│   ├── silver/                        ← PySpark canonical transforms
│   ├── gold/                          ← PySpark + BigQuery best views
│   ├── quality/                       ← Data quality framework
│   ├── schemas/                       ← State schema mappings
│   └── utils/                         ← Shared config, Spark, logging
├── bigquery/                          ← BigQuery DDL & SQL
│   ├── ddl/                           ← Table definitions
│   └── views/                         ← Analytical views
├── airflow/dags/                      ← Orchestration
├── sample_data/                       ← State data generators
├── tests/                             ← Unit + integration tests
├── config/                            ← Environment configs
├── CLAUDE.md                          ← AI agent context
└── AGENTS.md                          ← Multi-agent coordination
```

## State Coverage

| State | Source Format | County Example | Status |
|-------|-------------|----------------|--------|
| TX | CSV (pipe-delimited) | Harris County | ✅ Active |
| CA | JSON (nested) | LA County | ✅ Active |
| NY | CSV (comma-delimited) | Kings County | ✅ Active |
| FL | Fixed-width text | Miami-Dade | ✅ Active |
| IL | XML | Cook County | ✅ Active |
| OH | CSV (tab-delimited) | Cuyahoga County | ✅ Active |

## Adding a New State

See `docs/ADDING_NEW_STATE.md` for the step-by-step guide using OpenSpec.
