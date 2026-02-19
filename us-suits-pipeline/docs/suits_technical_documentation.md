# US Suits Pipeline — Technical Documentation

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Layers](#2-architecture-layers)
3. [State Data Source Analysis](#3-state-data-source-analysis)
4. [Schema Mapping Reference](#4-schema-mapping-reference)
5. [Data Quality Framework](#5-data-quality-framework)
6. [Airflow Orchestration](#6-airflow-orchestration)
7. [BigQuery Gold Layer](#7-bigquery-gold-layer)
8. [Project Structure](#8-project-structure)
9. [Deployment & Operations](#9-deployment--operations)
10. [Adding a New State](#10-adding-a-new-state)

---

## 1. System Overview

This pipeline ingests raw court suit/litigation records from **6 US states**, transforms them through a **medallion architecture** (Bronze → Silver → Gold), and produces consumer-ready views in **BigQuery**.

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Processing | PySpark 3.5+ (Dataproc) | Distributed transforms at scale |
| Storage | Parquet on GCS | Columnar, partitioned, compressed |
| Warehouse | BigQuery | Gold layer serving, analytics queries |
| Orchestration | Apache Airflow (Cloud Composer) | DAG scheduling, quality gates |
| Specifications | OpenSpec | Living requirements, spec-driven AI dev |
| Quality | Custom PySpark checks | Between-layer validation + quarantine |
| Testing | pytest + chispa | Unit + integration PySpark tests |
| CI/CD | GitHub Actions | Lint → test → deploy pipeline |

### State Coverage

| State | County | Source Format | Date Format | Key Differences |
|-------|--------|-------------|-------------|-----------------|
| **TX** | Harris | Pipe-delimited CSV (`\|`) | `MM/dd/yyyy` | Uses `cause_nbr` as secondary ID |
| **CA** | Los Angeles | Nested JSON | `yyyy-MM-dd` | Parties in `parties.plaintiffs[]` array |
| **NY** | Kings | Comma CSV | `MM/dd/yyyy` | Case number is `index_number` (slash format) |
| **FL** | Miami-Dade | Comma CSV | `yyyyMMdd` | No date separators; uses `pty_` prefix |
| **IL** | Cook | Comma CSV | `dd-MMM-yyyy` | Month abbreviations (Jan, Feb...); `_info` suffix |
| **OH** | Cuyahoga | Tab-delimited CSV | `M/d/yyyy` | Single-digit month/day; `_nm` suffix for names |

---

## 2. Architecture Layers

### Bronze Layer — Raw Ingestion

**Purpose:** Store every record exactly as received from the source, with lineage metadata appended.

**Implementation:** `src/bronze/ingest.py` — `BronzeIngester` class

**Key Design Decisions:**
- **Schema-on-read:** All source fields stored as strings (no type coercion at Bronze)
- **Idempotent ingestion:** Deterministic `_batch_id` via UUID5 from state+date; overwrite-mode writes
- **Partitioning:** `state={STATE}/ingestion_date={YYYY-MM-DD}` for efficient downstream reads
- **Error isolation:** Malformed files logged and skipped; partial success allowed

**Metadata columns appended to every record:**

| Column | Type | Source |
|--------|------|--------|
| `_ingestion_timestamp` | STRING (ISO UTC) | Generated at ingest time |
| `_source_state` | STRING | State code (TX, CA, NY...) |
| `_source_county` | STRING | County from config |
| `_source_format` | STRING | csv / json |
| `_batch_id` | STRING | UUID5 deterministic hash |
| `_file_path` | STRING | Original source file path |
| `_row_number` | LONG | Position in original file |

**PySpark execution pattern:**
```python
# Each state ingested independently, writes to partitioned path
df = spark.read.csv(path, header=True, sep=delimiter, inferSchema=False)
df = add_metadata_columns(df, state_code, ingestion_date)
df.write.mode("overwrite").parquet(f"bronze/state={state}/ingestion_date={date}/")
```

---

### Silver Layer — Canonical Schema

**Purpose:** Transform state-specific schemas into a single unified model with standardized types, harmonized codes, and normalized names.

**Implementation:** `src/silver/canonicalize.py` — `SilverCanonicalizer` class

**Transformation Pipeline (per state):**

```
Raw DataFrame
    │
    ├── 1. Field Rename ─── state_mappings.py[field_map]
    │      cause_nbr → case_number (TX)
    │      docket_id → case_number (CA)
    │      index_number → case_number (NY)
    │
    ├── 2. Generate suit_id ─── "{state}_{county}_{case_number}"
    │
    ├── 3. Parse Dates ─── to_date(col, state_date_format)
    │      "01/15/2025" → 2025-01-15  (TX, MM/dd/yyyy)
    │      "20250115"   → 2025-01-15  (FL, yyyyMMdd)
    │      "15-Jan-2025"→ 2025-01-15  (IL, dd-MMM-yyyy)
    │
    ├── 4. Harmonize Case Types ─── create_map() lookup
    │      CV → CIVIL (TX)
    │      CIV → CIVIL (CA)
    │      Civil → CIVIL (NY)
    │
    ├── 5. Harmonize Statuses ─── create_map() lookup
    │      PEND → OPEN (TX)
    │      Active → OPEN (CA)
    │      TERMINATED → DISPOSED (OH)
    │
    ├── 6. Normalize Names ─── trim + entity detection
    │
    ├── 7. Parse Amount ─── strip non-numeric, cast to DECIMAL
    │
    ├── 8. Add Silver Metadata ─── _silver_processed_at, _silver_version
    │
    ├── 9. Validate ─── case_number not null, filing_date not null
    │      │
    │      ├── VALID → canonical DataFrame
    │      └── INVALID → quarantine DataFrame + _quarantine_reason
    │
    └── 10. Deduplicate ─── ROW_NUMBER OVER (PARTITION BY suit_id ORDER BY timestamp DESC)
```

**Canonical `silver_suit` schema:** 17 fields including suit_id (PK), state_code, county, case_number, case_type, filing_date, case_status, judge_name, amount_demanded, disposition, disposition_date, plus 3 lineage columns.

**Canonical `silver_suit_party` schema:** Extracted from plaintiff_name and defendant_name. One row per party per suit. Includes `is_entity` boolean from pattern matching (LLC, Inc., Corp., Bank, Insurance, N.A.).

---

### Gold Layer — Consumer Best Views

**Purpose:** Pre-computed, query-optimized tables materialized in BigQuery for analytics, search, and downstream services.

**Implementation:** `src/gold/build_best_view.py` — `BestViewBuilder` class

**Gold Tables:**

| Table | Grain | Key Enrichments |
|-------|-------|-----------------|
| `gold_suit_best_view` | 1 row per suit | `year_filed`, `days_open`, `primary_plaintiff`, `primary_defendant`, `plaintiff_count`, `defendant_count` |
| `gold_party_best_view` | 1 row per party × suit | `total_suits_as_plaintiff`, `total_suits_as_defendant`, `first/last_appearance_date`, `is_frequent_litigant` (10+ suits) |
| `gold_state_summary` | state × year × case_type | `suit_count`, `avg_days_to_disposition`, `disposition_rate` |
| `gold_monthly_trends` | year_month × state × case_type | `new_filings`, `filing_trend_3m_avg` (rolling window) |

---

## 3. State Data Source Analysis

### Field Name Comparison

| Canonical Field | TX | CA | NY | FL | IL | OH |
|----------------|----|----|----|----|----|----|
| case_number | `case_number` | `docket_id` | `index_number` | `case_id` | `case_number` | `case_num` |
| filing_date | `file_date` | `filing_date` | `date_filed` | `filed_dt` | `filing_date` | `file_dt` |
| case_type | `case_type` | `case_type_code` | `action_type` | `case_type` | `case_category` | `type_cd` |
| case_status | `case_status` | `status` | `status` | `case_status` | `case_status` | `status_cd` |
| plaintiff | `plaintiff_name` | `parties.plaintiffs[].name` | `plaintiff` | `pty_plaintiff` | `plaintiff_info` | `plaintiff_nm` |
| defendant | `defendant_name` | `parties.defendants[].name` | `defendant` | `pty_defendant` | `defendant_info` | `defendant_nm` |
| judge | `judge` | *(not in base)* | `judge_assigned` | `judge_name` | `presiding_judge` | `judge_nm` |
| amount | `amount` | `amount_controversy` | `relief_sought` | `amt_claimed` | `demand_amount` | `claim_amt` |

### Sample Record Comparison (Same Conceptual Case)

**TX (pipe-delimited):**
```
case_number|file_date|case_type|plaintiff_name|defendant_name
2024-CV-00042|01/15/2025|CV|Bank of America, N.A.|James Rodriguez
```

**CA (JSON):**
```json
{"docket_id":"LA-2025-123456","filing_date":"2025-01-15","case_type_code":"CIV",
 "parties":{"plaintiffs":[{"name":"Bank of America, N.A."}],"defendants":[{"name":"James Rodriguez"}]}}
```

**FL (no date separators):**
```
case_id,filed_dt,case_type,pty_plaintiff,pty_defendant
13-2025-CA-123456,20250115,CA,Bank of America NA,James Rodriguez
```

**After Silver canonicalization (unified):**
```
suit_id: TX_Harris_County_2024-CV-00042
state_code: TX
case_type: CIVIL
case_status: OPEN
filing_date: 2025-01-15
plaintiff_name: Bank of America, N.A.
```

---

## 4. Schema Mapping Reference

### Case Type Harmonization (10 canonical types)

| Canonical | TX | CA | NY | FL | IL | OH |
|-----------|----|----|----|----|----|----|
| `CIVIL` | CV | CIV | Civil | CA | L | CV |
| `FAMILY` | FM | FAM | Matrimonial | DR | D | DR |
| `CRIMINAL` | CR | CRIM | Criminal | CF/MM | CR | CR |
| `PROBATE` | PR | PROB | Surrogate | CP | P | PB |
| `SMALL_CLAIMS` | SC | SC | Small Claims | SC | SC | SC |
| `EVICTION` | EV | UD | L&T | CC | EV | FED |
| `PERSONAL_INJURY` | PI | PI | Tort | — | L-PI | — |
| `CONTRACT` | CT | CT | Contract | — | L-CT | — |
| `REAL_PROPERTY` | RP | RE | Real Prop | — | CH | — |
| `OTHER` | * | * | * | * | * | * |

### Status Harmonization (8 canonical statuses)

| Canonical | TX | CA | NY | FL | IL | OH |
|-----------|----|----|----|----|----|----|
| `OPEN` | PEND | Active/Pending | Active | OPEN/REOPEN | Open/Continued | ACTIVE |
| `DISPOSED` | DISP/CLOSED | Disposed | Disposed/Settled/Judgement Entered | CLOSED/DISPOSED/INACTIVE | Closed/Disposed | TERMINATED |
| `DISMISSED` | DISM | Dismissed | Dismissed | — | Dismissed | DISMISSED |
| `TRANSFERRED` | TRANSF | Transferred | — | — | — | TRANSFERRED |
| `APPEALED` | APPEAL | — | — | — | — | — |
| `UNKNOWN` | *(fallback)* | *(fallback)* | *(fallback)* | *(fallback)* | *(fallback)* | *(fallback)* |

### Date Format Parsing

| State | Input Format | Example Input | Parsed Output |
|-------|-------------|---------------|---------------|
| TX | `MM/dd/yyyy` | `01/15/2025` | `2025-01-15` |
| CA | `yyyy-MM-dd` | `2025-01-15` | `2025-01-15` (passthrough) |
| NY | `MM/dd/yyyy` | `01/15/2025` | `2025-01-15` |
| FL | `yyyyMMdd` | `20250115` | `2025-01-15` |
| IL | `dd-MMM-yyyy` | `15-Jan-2025` | `2025-01-15` |
| OH | `M/d/yyyy` | `1/15/2025` | `2025-01-15` |

---

## 5. Data Quality Framework

**Implementation:** `src/quality/spark_checks.py`

### Gate 1: Bronze → Silver (threshold: 95%)

| Check | Type | Severity | Description |
|-------|------|----------|-------------|
| `not_null(case_number)` | Not Null | BLOCK | Case number must be present |
| `not_null(filing_date)` | Not Null | BLOCK | Filing date must be present |
| `not_null(plaintiff_name)` | Not Null | WARN | At least one plaintiff |
| `valid_state_code` | Accepted Values | BLOCK | State in [TX,CA,NY,FL,IL,OH] |

### Gate 2: Silver → Gold (threshold: 98%)

| Check | Type | Severity | Description |
|-------|------|----------|-------------|
| `unique(suit_id)` | Uniqueness | BLOCK | suit_id globally unique |
| `accepted_values(case_type)` | Accepted Values | BLOCK | In canonical taxonomy |
| `accepted_values(case_status)` | Accepted Values | BLOCK | In canonical status list |
| `valid_date(filing_date)` | Validity | BLOCK | Valid DATE, not future |
| `party_exists_per_suit` | Referential | WARN | ≥1 party per suit |

### Gate 3: Gold Output (threshold: 99%)

| Check | Type | Severity | Description |
|-------|------|----------|-------------|
| `unique(suit_id)` | Uniqueness | BLOCK | Unique in best view |
| `not_null(primary_plaintiff)` | Not Null | WARN | Primary plaintiff populated |
| `non_negative(days_open)` | Range | BLOCK | days_open ≥ 0 |

### Quarantine Pipeline

Failed records are written to `gs://bucket/quarantine/{layer}/{table}/{date}/` with:
- All original record fields
- `_quarantine_reason`: which check failed
- `_quarantine_timestamp`: when it was quarantined
- Weekly volume reports by failure type per state
- Spike alert if quarantine volume exceeds 2× rolling 7-day average

---

## 6. Airflow Orchestration

**DAG file:** `airflow/dags/suits_medallion_pipeline.py`

### DAG Configuration

| Setting | Value |
|---------|-------|
| `dag_id` | `us_suits_medallion_pipeline` |
| `schedule` | `0 6 * * *` (daily at 6 AM UTC) |
| `retries` | 2 (exponential backoff, 5 min delay) |
| `max_active_runs` | 1 |
| `catchup` | False |

### Task Execution Order

```
start
  ├── ingest_tx_suits ─┐
  ├── ingest_ca_suits  │
  ├── ingest_ny_suits  ├── (parallel)
  ├── ingest_fl_suits  │
  ├── ingest_il_suits  │
  └── ingest_oh_suits ─┘
         │
  bronze_quality_gate
         │
  silver_canonicalize
         │
  silver_quality_gate
         │
  ├── gold_suit_best_view ──┐
  ├── gold_party_best_view  ├── (parallel)
  └── gold_analytics ───────┘
         │
  bq_load_all_gold_tables
         │
  notify_completion ✓
```

### SLA Monitoring

- Gold tables must be refreshed within **4 hours** of Bronze ingestion
- Staleness alert triggered if Gold is **>8 hours** behind
- Quality gate failure triggers **Slack + PagerDuty** notification

---

## 7. BigQuery Gold Layer

### DDL

**File:** `bigquery/ddl/create_gold_tables.sql`

**Partitioning & Clustering Strategy:**

| Table | Partition | Cluster | Rationale |
|-------|-----------|---------|-----------|
| `suit_best_view` | `filing_date` (MONTH) | `state_code, case_type` | Most queries filter by state + time |
| `suit_party_best_view` | `first_appearance_date` (YEAR) | `party_type, is_frequent_litigant` | Party lookups |
| `suit_state_summary` | `year_filed` (RANGE) | `state_code, case_type` | Analytics drill-down |

### Consumer Views

| View | Purpose | File |
|------|---------|------|
| `v_suit_search` | Full-text-friendly suit search with `search_text` blob | `bigquery/views/v_suit_search.sql` |
| `v_frequent_litigants` | Parties with 10+ suits, ranked by appearances | `bigquery/views/v_frequent_litigants.sql` |
| `v_state_dashboard` | Pre-aggregated state metrics with YoY comparison | `bigquery/views/v_state_dashboard.sql` |

---

## 8. Project Structure

```
us-suits-pipeline/
├── openspec/                              ← Spec-driven development
│   ├── specs/
│   │   ├── bronze-state-ingestion/spec.md    REQ-BRZ-001 → 006
│   │   ├── silver-canonical-suits/spec.md    REQ-SLV-001 → 008
│   │   ├── gold-best-view/spec.md            REQ-GLD-001 → 005
│   │   └── data-quality/spec.md              REQ-DQ-001 → 004
│   └── changes/
│       └── add-oh-state-source/              Example: adding Ohio
│
├── src/
│   ├── bronze/
│   │   └── ingest.py                         BronzeIngester (PySpark)
│   ├── silver/
│   │   └── canonicalize.py                   SilverCanonicalizer (PySpark)
│   ├── gold/
│   │   └── build_best_view.py                BestViewBuilder (PySpark)
│   ├── quality/
│   │   └── spark_checks.py                   Quality gates (PySpark)
│   ├── schemas/
│   │   └── state_mappings.py                 State→canonical field/type/status maps
│   └── utils/
│       ├── config.py                         YAML config loader
│       ├── logger.py                         Structured logging (structlog)
│       └── spark_session.py                  SparkSession factory
│
├── bigquery/
│   ├── ddl/create_gold_tables.sql            Table definitions
│   └── views/                                3 consumer views
│
├── airflow/dags/
│   └── suits_medallion_pipeline.py           Daily DAG with quality gates
│
├── sample_data/
│   └── generate_state_suits.py               Generates 500 records/state
│
├── tests/
│   ├── unit/
│   │   ├── test_state_mappings.py            Validates all state mappings
│   │   └── test_quality_checks.py            Quality check unit tests
│   └── integration/
│       └── test_pipeline_e2e.py              Full Bronze→Silver→Gold test
│
├── config/pipeline_config.yaml               All pipeline configuration
├── run_pipeline.py                           CLI pipeline runner
├── Makefile                                  Build targets
├── CLAUDE.md                                 AI agent context
├── AGENTS.md                                 Multi-agent coordination
└── docs/ADDING_NEW_STATE.md                  New state onboarding guide
```

---

## 9. Deployment & Operations

### Environments

| Environment | GCS Path | BQ Dataset | Cluster |
|-------------|----------|------------|---------|
| Dev | `gs://bucket-dev/us-suits/` | `suits_dev_*` | Local PySpark |
| Staging | `gs://bucket-staging/us-suits/` | `suits_staging_*` | Dataproc (2 workers) |
| Production | `gs://bucket-prod/us-suits/` | `suits_gold` | Dataproc (4 workers, autoscaling) |

### CI/CD Pipeline (GitHub Actions)

```
push to main → ruff lint → unit tests → integration tests → deploy to staging → approval → prod
```

### Data Retention

| Layer | Retention | Rationale |
|-------|-----------|-----------|
| Bronze | 7 years | Regulatory compliance |
| Silver | 3 years | Reprocessing window |
| Gold | Current + 2 years | Analytics history |
| Quarantine | 90 days | Investigation window |

---

## 10. Adding a New State

Full guide in `docs/ADDING_NEW_STATE.md`. Summary:

1. **Add state config** to `config/pipeline_config.yaml`
2. **Add schema mapping** to `src/schemas/state_mappings.py` (field_map, case_type_map, status_map, date_format)
3. **Add sample data generator** to `sample_data/generate_state_suits.py`
4. **Run tests:** `pytest tests/unit/test_state_mappings.py -v`
5. **Run pipeline:** `python run_pipeline.py --date 2025-01-15`
6. **Verify:** `pytest tests/integration/ -v`

The mapping file is the single source of truth. No PySpark code changes are needed for a new state — only configuration.
