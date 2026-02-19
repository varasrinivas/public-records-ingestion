# US Public Records Data Engineering Architecture
## Suits, Liens & Judgments — Medallion Architecture

---

## 1. Domain Analysis

### 1.1 The Three Record Types

US public records for legal and financial due diligence fall into three distinct but interconnected categories. Understanding their fundamental differences is critical to designing the right data model.

**Suits (Civil Litigation)**
A suit is a legal proceeding initiated by a plaintiff against a defendant in court. Suit records originate from court case management systems and contain docket information, party names, case types, filing dates, and disposition outcomes. Suits are the *upstream event* — a judgment is the outcome of a suit, and a lien may follow from a judgment.

Key characteristics:
- Filed in state courts (county-level) or federal courts (district-level via PACER/CM-ECF)
- Every state has a unique case numbering scheme, field naming convention, and data format
- A single suit can involve multiple plaintiffs, defendants, and attorneys
- Cases evolve over time: filed → active → discovery → trial → judgment → appeal
- Case types span civil, family, criminal, probate, small claims, eviction, bankruptcy

**Judgments**
A judgment is a court's official decision resolving a suit. It may award monetary damages, issue injunctions, or order specific performance. Judgments are the *bridge* between suits and liens — a court issues a judgment, and the winning party may then record a judgment lien against the losing party's property.

Key characteristics:
- Recorded in court records at case disposition
- Include monetary amounts, prevailing party, judgment type (default, summary, consent, trial)
- May be satisfied (paid), vacated, or appealed
- The same judgment may be "domesticated" (filed) in multiple states
- Judgment duration varies by state (typically 5–20 years, renewable)

**Liens**
A lien is a legal claim against property to secure payment of a debt. Liens are filed with recording offices (county recorder, Secretary of State) rather than courts. They encumber real property, personal property, or both, depending on type.

Key lien types:

| Lien Type | Filed By | Filed Where | Attaches To |
|-----------|----------|-------------|-------------|
| Federal Tax Lien | IRS (Form 668) | County Recorder + SOS | All property (real + personal) |
| State Tax Lien | State tax authority | SOS and/or County Recorder (varies by state) | All property |
| Judgment Lien | Judgment creditor (Abstract of Judgment) | County Recorder | Real property in that county |
| Mechanic's Lien | Contractor / supplier | County Recorder | Specific improved property |
| UCC Lien (UCC-1) | Secured creditor | Secretary of State | Personal property / collateral |
| HOA Lien | Homeowners association | County Recorder | Specific property |
| Hospital / Medical Lien | Healthcare provider | County Recorder | Personal injury proceeds |

### 1.2 Filing Jurisdictions — The Core Complexity

The most significant data engineering challenge is that **no two states handle these records the same way**. The filing jurisdiction, office name, data format, and access mechanism all vary.

**Suits** are filed in:
- 50 state court systems (each with trial courts organized by county)
- 94 federal district courts (accessible via PACER)
- Specialized courts: bankruptcy courts, tax courts, Court of Federal Claims

**Liens** are filed in:
- Secretary of State offices (UCC liens, and in some states, tax liens)
- County Recorder / Clerk offices (judgment liens, mechanic's liens, tax liens)
- Rules vary dramatically — California SOS maintains UCCs, federal tax liens, state tax liens, *and* judgment liens; Ohio SOS maintains only UCC liens, with tax liens at the county level

**Judgments** exist in:
- Court case records (as the disposition of a suit)
- County recorder records (when abstracted/recorded as a lien)
- Both locations simultaneously

### 1.3 Data Source Formats

| Source Type | Format | Access Method | Volume Estimate |
|-------------|--------|---------------|-----------------|
| State courts (large counties) | CSV, JSON, XML, fixed-width | Bulk file download, SFTP, API | 500K–5M records/state/year |
| Federal courts (PACER) | XML, JSON (via PCL API) | REST API (paid, $0.10/page) | ~3M cases/year |
| Secretary of State (UCC) | CSV, XML, web scrape | Bulk download, API (varies) | ~20M active filings nationwide |
| County recorders (liens) | CSV, PDF images, web index | Varies: API, FTP, manual | Highly variable by county |
| Aggregators (LexisNexis, UniCourt) | JSON, CSV | REST API, S3 bulk delivery | Normalized, pre-processed |

### 1.4 Entity Relationships

```
┌────────────────────────────────────────────────────────────┐
│                    ENTITY RELATIONSHIP                      │
│                                                            │
│  ┌──────────┐   files    ┌──────────┐   results in         │
│  │ PARTY    │───────────▶│  SUIT    │──────────────┐       │
│  │(person/  │ plaintiff/ │(case in  │               │       │
│  │ entity)  │ defendant  │ court)   │               ▼       │
│  └──────────┘            └──────────┘         ┌──────────┐ │
│       │                                       │ JUDGMENT  │ │
│       │ debtor /                              │(court     │ │
│       │ creditor                              │ decision) │ │
│       │                                       └─────┬────┘ │
│       │                                             │       │
│       │              ┌──────────┐    recorded as    │       │
│       └─────────────▶│   LIEN   │◀──────────────────┘       │
│                      │(claim on │                           │
│                      │ property)│                           │
│                      └──────────┘                           │
│                           │                                 │
│                           ▼                                 │
│                      ┌──────────┐                           │
│                      │ PROPERTY │                           │
│                      │(real or  │                           │
│                      │ personal)│                           │
│                      └──────────┘                           │
└────────────────────────────────────────────────────────────┘

One PARTY can appear in many SUITS (as plaintiff or defendant)
One SUIT produces zero or one JUDGMENT
One JUDGMENT can produce zero or more LIENS (across multiple counties)
One LIEN attaches to one or more PROPERTIES
One PARTY can have many LIENS (tax, judgment, mechanic's, UCC)
```

---

## 2. Medallion Architecture Design

### 2.1 High-Level Data Flow

```
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                        RAW DATA SOURCES                                      │
 │                                                                              │
 │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐     │
 │  │State Courts│  │  PACER     │  │Secretary   │  │County Recorders   │     │
 │  │(50 states, │  │(94 federal │  │of State    │  │(3,000+ counties,  │     │
 │  │ CSV/JSON/  │  │ districts, │  │(UCC liens, │  │ judgment liens,   │     │
 │  │ XML)       │  │ REST API)  │  │ tax liens) │  │ mechanic's liens) │     │
 │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └────────┬───────────┘     │
 │        │               │               │                   │                 │
 │ ═══════╪═══════════════╪═══════════════╪═══════════════════╪═══════════════  │
 │        ▼               ▼               ▼                   ▼                 │
 │  ┌─────────────────────────────────────────────────────────────────────┐     │
 │  │  🥉 BRONZE LAYER — Raw Ingestion                                   │     │
 │  │                                                                     │     │
 │  │  bronze_suits_state      (per-state raw court data)                │     │
 │  │  bronze_suits_federal    (PACER district court data)               │     │
 │  │  bronze_liens_ucc        (SOS UCC filings per state)              │     │
 │  │  bronze_liens_tax        (federal + state tax liens)              │     │
 │  │  bronze_liens_judgment   (county recorder abstracts)              │     │
 │  │  bronze_liens_mechanic   (county mechanic's liens)               │     │
 │  │  bronze_judgments_state   (court disposition records)              │     │
 │  │  bronze_judgments_federal (PACER judgments)                        │     │
 │  │                                                                     │     │
 │  │  Storage: Parquet on GCS, partitioned by source_state/ingest_date  │     │
 │  │  Schema: raw source schema preserved, metadata columns appended    │     │
 │  └────────────────────────┬────────────────────────────────────────────┘     │
 │                           │                                                  │
 │                     Quality Gate 1                                           │
 │                   (schema validation,                                        │
 │                    null checks, date                                         │
 │                    parsing validation)                                       │
 │                           │                                                  │
 │                           ▼                                                  │
 │  ┌─────────────────────────────────────────────────────────────────────┐     │
 │  │  🥈 SILVER LAYER — Canonical Models                                │     │
 │  │                                                                     │     │
 │  │  silver_suit           (unified suit schema, all states + federal)  │     │
 │  │  silver_suit_party     (normalized parties per suit)               │     │
 │  │  silver_suit_docket    (docket entries / case events)              │     │
 │  │  silver_judgment       (unified judgment schema)                   │     │
 │  │  silver_lien           (unified lien schema, all types)           │     │
 │  │  silver_lien_party     (debtor/creditor per lien)                 │     │
 │  │  silver_party_master   (deduplicated party entity registry)        │     │
 │  │                                                                     │     │
 │  │  Transforms: field mapping, date standardization, case type         │     │
 │  │  harmonization, party name normalization, dedup, quarantine         │     │
 │  │  Storage: Parquet on GCS, partitioned by state_code                │     │
 │  └────────────────────────┬────────────────────────────────────────────┘     │
 │                           │                                                  │
 │                     Quality Gate 2                                           │
 │                  (referential integrity,                                     │
 │                   canonical value checks,                                    │
 │                   cross-entity consistency)                                  │
 │                           │                                                  │
 │                           ▼                                                  │
 │  ┌─────────────────────────────────────────────────────────────────────┐     │
 │  │  🥇 GOLD LAYER — Consumer Best Views (BigQuery)                    │     │
 │  │                                                                     │     │
 │  │  gold_suit_best_view          (one row per suit, latest state)     │     │
 │  │  gold_judgment_best_view      (one row per judgment)               │     │
 │  │  gold_lien_best_view          (one row per lien, current status)   │     │
 │  │  gold_party_profile           (360° view: suits + liens + judgments)│     │
 │  │  gold_party_risk_score        (aggregated risk metrics per party)   │     │
 │  │  gold_suit_judgment_lien_xref (cross-reference linking table)      │     │
 │  │  gold_analytics_state_summary (pre-computed state/type/year aggs)  │     │
 │  │  gold_analytics_monthly_trend (filing trends with rolling avgs)    │     │
 │  │                                                                     │     │
 │  │  Storage: BigQuery tables (Parquet on GCS as backing store)        │     │
 │  │  Partitioned by filing_date, clustered by state_code + record_type │     │
 │  └─────────────────────────────────────────────────────────────────────┘     │
 │                                                                              │
 │  ┌─────────────────────────────────────────────────────────────────────┐     │
 │  │  CONSUMERS                                                          │     │
 │  │  Looker / Tableau dashboards  │  Risk & Compliance APIs             │     │
 │  │  ML Feature Store (churn/risk)│  Due Diligence Search Portal        │     │
 │  │  Legal Analytics Platform     │  Downstream Microservices           │     │
 │  └─────────────────────────────────────────────────────────────────────┘     │
 └──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Bronze Layer — Raw Ingestion

The Bronze layer is the foundation. Every record from every source is stored exactly as received, with metadata appended for lineage tracking.

**Design Principles:**
- Schema-on-read: all source fields preserved as strings (no type coercion)
- Append-only within a partition; idempotent per source+date
- Every record gets `_batch_id`, `_source_system`, `_source_state`, `_ingestion_timestamp`
- Partitioned by `source_state` and `ingestion_date` for efficient downstream reads

**Bronze Tables:**

| Table | Source | Partition | Approx Record Shape |
|-------|--------|-----------|---------------------|
| `bronze_suits_state` | State court bulk files | `state / ingest_date` | case_number, filing_date, case_type, status, plaintiff, defendant, judge, county, amount |
| `bronze_suits_federal` | PACER PCL API | `district / ingest_date` | docket_number, case_name, cause_code, nature_of_suit, date_filed, date_terminated, judge |
| `bronze_liens_ucc` | SOS bulk files / API | `state / ingest_date` | file_number, file_date, debtor_name, secured_party, collateral_description, status |
| `bronze_liens_tax_federal` | IRS NFTL records | `state / ingest_date` | serial_number, taxpayer_name, tax_period, amount, filing_date, release_date |
| `bronze_liens_tax_state` | State tax authority files | `state / ingest_date` | lien_number, debtor_name, amount, tax_type, filing_date, county |
| `bronze_liens_judgment` | County recorder bulk | `state_county / ingest_date` | book_page, case_number, creditor, debtor, amount, filing_date, court |
| `bronze_liens_mechanic` | County recorder bulk | `state_county / ingest_date` | document_number, claimant, property_owner, property_address, amount, filing_date |
| `bronze_judgments_state` | State court dispositions | `state / ingest_date` | case_number, judgment_date, judgment_type, amount, prevailing_party, satisfied |
| `bronze_judgments_federal` | PACER case data | `district / ingest_date` | docket_number, judgment_date, nature_of_suit, amount, entered_by |

**PySpark Bronze Ingestion Pattern:**

```python
# Bronze ingester reads source files in native format,
# adds metadata, writes Parquet partitioned to GCS
class BronzeIngester:
    def ingest(self, source_type, state_code, date):
        df = self._read_source(source_type, state_code)  # CSV/JSON/XML
        df = df.select([F.col(c).cast("string") for c in df.columns])  # schema-on-read
        df = self._add_metadata(df, source_type, state_code, date)
        df.write.mode("overwrite") \
            .partitionBy("_source_state", "_ingestion_date") \
            .parquet(f"gs://bucket/bronze/{source_type}/")
```

### 2.3 Silver Layer — Canonical Models

The Silver layer is where the heavy transformation happens. Every state's unique schema is mapped to a common canonical model. This is the most complex and valuable part of the pipeline.

**Canonical Suit Schema (`silver_suit`):**

| Field | Type | Source Mapping Challenge |
|-------|------|-------------------------|
| `suit_id` | STRING | Generated: `{state}_{county}_{case_number}` or `FED_{district}_{docket}` |
| `record_source` | STRING | `STATE_COURT` or `FEDERAL_COURT` |
| `state_code` | STRING(2) | Direct mapping |
| `county_or_district` | STRING | TX: court_number → county; PACER: district name |
| `case_number` | STRING | TX: `cause_nbr`; CA: `docket_id`; NY: `index_number`; PACER: `docket_number` |
| `case_type` | STRING | Harmonized from 50+ state-specific codes → canonical taxonomy |
| `case_type_raw` | STRING | Original code preserved for audit |
| `filing_date` | DATE | TX: MM/dd/yyyy; FL: yyyyMMdd; IL: dd-MMM-yyyy; PACER: yyyy-MM-dd |
| `case_status` | STRING | Harmonized: OPEN / DISPOSED / DISMISSED / TRANSFERRED / APPEALED / SEALED |
| `case_status_raw` | STRING | Original status preserved |
| `court_name` | STRING | Varies by state |
| `judge_name` | STRING | Title case, normalized |
| `cause_of_action` | STRING | Free text, varies wildly |
| `amount_demanded` | DECIMAL(18,2) | Parsing: remove $, commas; handle "0.00" vs null |
| `disposition` | STRING | Settlement / Default Judgment / Trial Verdict / Dismissed / etc. |
| `disposition_date` | DATE | Multiple date formats |

**Canonical Lien Schema (`silver_lien`):**

| Field | Type | Notes |
|-------|------|-------|
| `lien_id` | STRING | Generated: `{lien_type}_{state}_{file_number}` |
| `lien_type` | STRING | `FEDERAL_TAX` / `STATE_TAX` / `JUDGMENT` / `MECHANIC` / `UCC` / `HOA` |
| `state_code` | STRING(2) | State where filed |
| `county` | STRING | County where filed (null for SOS-level filings) |
| `filing_office` | STRING | `SOS` / `COUNTY_RECORDER` / `COUNTY_CLERK` |
| `file_number` | STRING | Original filing/document number |
| `filing_date` | DATE | Standardized |
| `lien_amount` | DECIMAL(18,2) | Claimed amount |
| `lien_status` | STRING | `ACTIVE` / `RELEASED` / `EXPIRED` / `SATISFIED` / `PARTIAL_RELEASE` |
| `release_date` | DATE | If satisfied/released |
| `expiration_date` | DATE | Computed based on state-specific duration rules |
| `related_case_number` | STRING | For judgment liens: links back to the originating suit |
| `property_address` | STRING | For real property liens |
| `collateral_description` | STRING | For UCC liens |

**Canonical Judgment Schema (`silver_judgment`):**

| Field | Type | Notes |
|-------|------|-------|
| `judgment_id` | STRING | Generated: `{state}_{case_number}_{judgment_date}` |
| `suit_id` | STRING | FK to `silver_suit` (linking judgment to originating case) |
| `state_code` | STRING(2) | |
| `case_number` | STRING | |
| `judgment_date` | DATE | |
| `judgment_type` | STRING | `DEFAULT` / `CONSENT` / `SUMMARY` / `TRIAL_VERDICT` / `STIPULATED` |
| `judgment_amount` | DECIMAL(18,2) | |
| `prevailing_party` | STRING | PLAINTIFF / DEFENDANT |
| `satisfaction_status` | STRING | `UNSATISFIED` / `SATISFIED` / `PARTIALLY_SATISFIED` / `VACATED` |
| `satisfaction_date` | DATE | |

**Canonical Party Schema (`silver_party_master`):**

| Field | Type | Notes |
|-------|------|-------|
| `party_id` | STRING | Generated hash-based ID |
| `party_name_normalized` | STRING | Cleaned, title case for individuals, entity-preserved for businesses |
| `party_name_variants` | ARRAY&lt;STRING&gt; | All observed name variations |
| `is_entity` | BOOLEAN | Corp/LLC/Inc detection |
| `entity_type` | STRING | `INDIVIDUAL` / `CORPORATION` / `LLC` / `GOVERNMENT` / `TRUST` / `UNKNOWN` |
| `states_appeared` | ARRAY&lt;STRING&gt; | All states where this party has records |
| `total_as_plaintiff` | INT | Across all suits |
| `total_as_defendant` | INT | Across all suits |
| `total_liens_as_debtor` | INT | Across all lien types |
| `total_liens_as_creditor` | INT | |

**Key Silver Transformations (PySpark):**

1. **State Field Mapping** — A per-state configuration maps raw column names to canonical names (biggest engineering effort)
2. **Date Standardization** — Parse 10+ date formats into ISO 8601 DATE
3. **Case Type Harmonization** — Map ~200 state-specific codes to ~12 canonical types
4. **Status Harmonization** — Map ~50 state-specific statuses to 8 canonical values
5. **Party Name Normalization** — Strip suffixes (LLC, Inc.), standardize casing, detect entity vs. individual
6. **Suit-Judgment Linking** — Match judgments to their originating suits by case_number + state
7. **Judgment-Lien Linking** — Match judgment liens back to judgments by case_number + debtor name
8. **Deduplication** — By composite key per entity type; latest ingestion wins
9. **Quarantine** — Invalid/unparseable records quarantined with failure reasons

### 2.4 Gold Layer — Consumer Best Views

The Gold layer produces pre-computed, query-optimized views materialized in BigQuery.

**`gold_suit_best_view`** — One row per suit, enriched
- Joins suit + judgment + linked liens into a single denormalized row
- Adds: `days_open`, `year_filed`, `has_judgment`, `judgment_amount`, `lien_count`, `primary_plaintiff`, `primary_defendant`
- Partitioned by `filing_date` (MONTH), clustered by `state_code`, `case_type`

**`gold_lien_best_view`** — One row per lien, current status
- Joins lien + party (debtor/creditor) + related suit/judgment references
- Adds: `is_active` (computed from status + expiration), `days_since_filing`, `related_suit_id`, `related_judgment_id`
- Partitioned by `filing_date` (MONTH), clustered by `state_code`, `lien_type`

**`gold_judgment_best_view`** — One row per judgment
- Joins judgment + originating suit + downstream liens
- Adds: `has_lien_recorded`, `lien_states` (where judgment was domesticated), `days_to_satisfaction`

**`gold_party_profile`** — 360° party view (the most valuable consumer table)
- One row per unique party across all record types
- Aggregates: total suits as plaintiff/defendant, total liens as debtor/creditor, total judgment amounts, lien amounts outstanding
- Computes: `risk_score` based on lien/judgment activity, `litigation_velocity` (filings per year), `is_frequent_litigant`
- Enables due diligence queries: "Show me everything on entity X across all states"

**`gold_suit_judgment_lien_xref`** — Cross-reference linking table
- Maps the chain: Suit → Judgment → Lien(s)
- Enables traversal: "This lien came from this judgment, which came from this suit"

**Analytics aggregates:**

| Table | Grain | Key Metrics |
|-------|-------|-------------|
| `gold_analytics_state_summary` | state × year × record_type × case/lien type | filing_count, avg_amount, disposition_rate, median_days_to_resolution |
| `gold_analytics_monthly_trend` | year_month × state × record_type | new_filings, rolling_3m_avg, yoy_change_pct |
| `gold_analytics_top_litigants` | state × year | top_plaintiffs, top_defendants, repeat_filer_count |

---

## 3. Technology Architecture

### 3.1 Component Map

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                               │
│                     Apache Airflow (Cloud Composer)                       │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ ingest_suits │  │ ingest_liens │  │ ingest_judg  │  │  quality   │  │
│  │ _dag         │  │ _dag         │  │ ments_dag    │  │  _monitor  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬─────┘  │
│         │                 │                 │                  │         │
│ ════════╪═════════════════╪═════════════════╪══════════════════╪═══════  │
│         ▼                 ▼                 ▼                  ▼         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   PROCESSING ENGINE                             │    │
│  │                  PySpark on Dataproc                             │    │
│  │                                                                 │    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │    │
│  │  │ Bronze   │───▶│ Silver   │───▶│ Gold     │                  │    │
│  │  │ Ingest   │    │ Canonical│    │ Best View│                  │    │
│  │  │ Jobs     │    │ Jobs     │    │ Jobs     │                  │    │
│  │  └──────────┘    └──────────┘    └──────────┘                  │    │
│  └────────────────────────┬────────────────────────────────────────┘    │
│                           │                                             │
│ ══════════════════════════╪═══════════════════════════════════════════  │
│                           ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      STORAGE LAYER                               │   │
│  │                                                                  │   │
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐     │   │
│  │  │  Google Cloud Storage   │    │     BigQuery             │     │   │
│  │  │  (Parquet files)        │    │  (Gold tables + views)   │     │   │
│  │  │                         │    │                          │     │   │
│  │  │  gs://bucket/bronze/    │    │  suits_gold dataset      │     │   │
│  │  │  gs://bucket/silver/    │───▶│  ├─ suit_best_view       │     │   │
│  │  │  gs://bucket/gold/      │    │  ├─ lien_best_view       │     │   │
│  │  │  gs://bucket/quarantine/│    │  ├─ judgment_best_view   │     │   │
│  │  │                         │    │  ├─ party_profile        │     │   │
│  │  └─────────────────────────┘    │  └─ analytics_*          │     │   │
│  │                                 └─────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      SERVING / CONSUMERS                         │   │
│  │                                                                  │   │
│  │  Looker / Tableau   │  REST API (FastAPI)  │  ML Feature Store   │   │
│  │  Legal Analytics    │  Due Diligence Portal │  Risk Scoring Model │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Choices — Rationale

| Component | Technology | Why |
|-----------|-----------|-----|
| **Processing** | PySpark 3.5+ on Dataproc | Handles 100M+ records; native Parquet/GCS/BQ connectors; state-level parallelism |
| **Storage** | Parquet on GCS | Columnar, compressed, schema evolution; serves as durable backing for BigQuery external tables |
| **Warehouse** | BigQuery | Sub-second analytical queries on Gold tables; partitioning/clustering for cost efficiency; feeds BI tools directly |
| **Orchestration** | Airflow (Cloud Composer) | Manages complex DAG dependencies across 3 record types × 50 states; retries, SLAs, monitoring |
| **Language** | Python 3.11+ | PySpark native, BigQuery SDK, Airflow operators, rich data quality libraries |
| **Quality** | Custom framework + Great Expectations | Quality gates between every layer; quarantine-based error handling |
| **Schema Registry** | OpenSpec living specs | Formal requirements that AI agents and engineers implement against; survives team changes |

### 3.3 Airflow DAG Architecture

Three primary DAGs, one per record type, plus a cross-cutting quality/reconciliation DAG:

```
DAG: suits_medallion_pipeline (daily @ 06:00 UTC)
├── TaskGroup: bronze_ingest_suits
│   ├── ingest_tx_suits
│   ├── ingest_ca_suits
│   ├── ingest_ny_suits
│   ├── ... (one task per state + federal)
│   └── ingest_pacer_federal
├── bronze_quality_gate
├── silver_canonicalize_suits
├── silver_quality_gate
├── TaskGroup: gold_build
│   ├── build_suit_best_view
│   ├── build_suit_party_views
│   └── build_suit_analytics
├── bq_load_gold_tables
└── notify_completion

DAG: liens_medallion_pipeline (daily @ 06:00 UTC)
├── TaskGroup: bronze_ingest_liens
│   ├── ingest_ucc_liens (per state)
│   ├── ingest_federal_tax_liens
│   ├── ingest_state_tax_liens (per state)
│   ├── ingest_judgment_liens (per county batch)
│   └── ingest_mechanic_liens (per county batch)
├── bronze_quality_gate
├── silver_canonicalize_liens
├── silver_quality_gate
├── TaskGroup: gold_build
│   ├── build_lien_best_view
│   ├── build_lien_party_views
│   └── build_lien_analytics
├── bq_load_gold_tables
└── notify_completion

DAG: judgments_medallion_pipeline (daily @ 06:00 UTC)
├── TaskGroup: bronze_ingest_judgments
│   ├── ingest_state_judgments (per state)
│   └── ingest_pacer_judgments
├── bronze_quality_gate
├── silver_canonicalize_judgments
├── silver_quality_gate
├── gold_build_judgment_views
├── bq_load_gold_tables
└── notify_completion

DAG: cross_entity_reconciliation (daily @ 10:00 UTC, after all 3 complete)
├── build_suit_judgment_lien_xref     ← Links suits → judgments → liens
├── build_party_profile_360           ← Aggregates party across all 3 types
├── build_party_risk_score            ← Computes risk metrics
├── gold_quality_gate
├── bq_refresh_cross_entity_tables
└── data_freshness_sla_check
```

**Key Airflow Design Decisions:**
- Separate DAGs per record type (suits/liens/judgments) for independent failure isolation
- A fourth cross-cutting DAG runs after all three complete, building the linked views
- ExternalTaskSensor ensures the cross-entity DAG waits for all three pipelines
- State-level tasks are parallelized within TaskGroups
- Each DAG has SLA monitoring: Gold must be refreshed within 4 hours of Bronze ingest

### 3.4 BigQuery Schema Design

**Partitioning and Clustering Strategy:**

| Table | Partition Column | Partition Type | Cluster Columns | Rationale |
|-------|-----------------|----------------|-----------------|-----------|
| suit_best_view | filing_date | MONTH | state_code, case_type | Most queries filter by state + time range |
| lien_best_view | filing_date | MONTH | state_code, lien_type | Same pattern: "show me liens in TX last year" |
| judgment_best_view | judgment_date | MONTH | state_code, judgment_type | Time-bounded judgment searches |
| party_profile | — (small) | — | entity_type, state_code | Party lookups by name, filtered by state |
| suit_judgment_lien_xref | — (small) | — | state_code | Traversal queries |

**BigQuery Consumer Views:**

- `v_party_due_diligence` — Input: party name → Output: all suits, liens, judgments across all states
- `v_active_liens_by_state` — Active liens with computed expiration, filtered by state
- `v_litigation_risk_dashboard` — Pre-aggregated state × year metrics for BI tools
- `v_frequent_litigants` — Parties appearing in 10+ suits or with 5+ liens
- `v_suit_to_lien_chain` — The full chain: suit → judgment → lien(s) for a given case

---

## 4. Key Design Challenges and Solutions

### 4.1 Entity Resolution Across Sources

The hardest problem: the same entity appears differently across sources.

| Source | Name As Filed |
|--------|---------------|
| TX state court | "BANK OF AMERICA NA" |
| CA state court | "Bank of America, N.A." |
| PACER | "Bank of America, National Association" |
| County recorder | "BANK OF AMER NA" |
| UCC filing | "Bank of America, N.A. as successor" |

**Solution:** A multi-pass entity resolution pipeline in Silver:
1. **Normalize** — Strip punctuation, standardize suffixes, lowercase
2. **Token-based matching** — Jaccard similarity on name tokens
3. **Blocking** — Group by state + first 3 characters of name for efficiency
4. **Confidence scoring** — Above threshold → auto-merge; below → manual review queue
5. **party_master table** — Maintains canonical name + all observed variants

### 4.2 State-Specific Lien Expiration Rules

Lien duration varies dramatically by state. The Silver → Gold transform must compute `expiration_date` per state:

| State | Judgment Lien Duration | Federal Tax Lien | UCC Duration |
|-------|----------------------|------------------|--------------|
| CA | 10 years (renewable) | 10 years + 30 days | 5 years |
| TX | 10 years (abstract) | 10 years + 30 days | 5 years |
| NY | 10 years | 10 years + 30 days | 5 years |
| FL | 10 years (no real property lien by statute until 2023 change) | 10 years + 30 days | 5 years |

This is implemented as a state-specific configuration table consumed by PySpark during Gold computation.

### 4.3 Suit-Judgment-Lien Linkage

Not all judgments produce liens. Not all liens come from judgments. The linkage is probabilistic:

| Link | Matching Strategy | Confidence |
|------|-------------------|------------|
| Suit → Judgment | Same case_number + state + court | HIGH (deterministic) |
| Judgment → Judgment Lien | Same case_number OR debtor_name + amount + date proximity | MEDIUM (fuzzy) |
| Party across record types | Entity resolution pipeline | VARIABLE |

### 4.4 Volume and Performance

| Layer | Estimated Records (nationwide) | PySpark Cluster Sizing |
|-------|-------------------------------|------------------------|
| Bronze (all sources, annual) | ~200M records/year | Dataproc: 4 workers × n2-standard-8 |
| Silver (canonical) | ~150M records/year (after dedup) | Same cluster, 2–3 hour job |
| Gold (best views) | ~120M records | BigQuery-native for aggregates |

---

## 5. Data Quality Framework

Quality gates between every layer, with PySpark-native checks:

**Bronze → Silver Gate:**
- Case/file number not null (≥95% pass rate required)
- Filing date parseable and not in the future
- State code valid (2-letter code in known set)
- At least one party name present
- Amount non-negative (where present)

**Silver → Gold Gate:**
- Primary key unique (suit_id, lien_id, judgment_id) — 100% required
- Case type in canonical taxonomy — ≥98%
- Status in canonical values — ≥98%
- Filing date is valid DATE — ≥99%
- Referential integrity: every judgment links to a suit — ≥95%

**Gold Quality Checks:**
- Party profile completeness: every party has at least one associated record
- Cross-reference integrity: xref table links only to existing records
- Freshness SLA: Gold tables ≤4 hours behind Bronze

**Quarantine:**
- Failed records stored in `gs://bucket/quarantine/{layer}/{table}/{date}/`
- Include: original record + failure reason + check name + timestamp
- Weekly quarantine volume report by failure type
- Spike alerts: quarantine volume >2× rolling 7-day average

---

## 6. Spec-Driven Development Workflow

Every pipeline change is driven by OpenSpec specifications:

```
openspec/specs/
├── bronze-suit-ingestion/spec.md       ← REQ-BRZ-SUIT-001 through 006
├── bronze-lien-ingestion/spec.md       ← REQ-BRZ-LIEN-001 through 008
├── bronze-judgment-ingestion/spec.md   ← REQ-BRZ-JDG-001 through 004
├── silver-canonical-suit/spec.md       ← REQ-SLV-SUIT-001 through 010
├── silver-canonical-lien/spec.md       ← REQ-SLV-LIEN-001 through 008
├── silver-canonical-judgment/spec.md   ← REQ-SLV-JDG-001 through 006
├── silver-party-resolution/spec.md     ← REQ-SLV-PTY-001 through 005
├── gold-best-views/spec.md             ← REQ-GLD-001 through 008
├── gold-cross-entity/spec.md           ← REQ-GLD-XREF-001 through 004
└── data-quality/spec.md                ← REQ-DQ-001 through 006
```

**Workflow: Adding a new state or lien type**
```
1. /opsx:new add-{state}-{record_type}     ← Create change proposal
2. /opsx:ff                                 ← Generate design + tasks + spec deltas
3. Human reviews spec deltas                ← Critical gate before code
4. /opsx:apply                              ← Agent implements against spec
5. pytest tests/ -v                         ← Verify spec scenarios
6. /opsx:archive                            ← Merge into living specs
```

---

## 7. Production Deployment Summary

| Concern | Approach |
|---------|----------|
| **Infrastructure** | Terraform: GCS buckets, Dataproc cluster, BigQuery datasets, Cloud Composer, IAM |
| **Environments** | dev → staging → prod; each with isolated GCS paths and BQ datasets |
| **CI/CD** | GitHub Actions: lint → unit tests → integration test (PySpark local) → deploy to staging → approval → prod |
| **Monitoring** | Datadog/Cloud Monitoring: Airflow task durations, Spark job metrics, BQ query costs, data freshness SLAs |
| **Alerting** | Slack/PagerDuty: pipeline failures, quality gate failures, freshness SLA breaches, quarantine spikes |
| **Cost control** | BQ slot reservations for Gold refresh; Dataproc autoscaling; partition pruning; clustering for scan reduction |
| **Security** | Column-level security on PII (party names, addresses); VPC Service Controls; encryption at rest (CMEK) |
| **Retention** | Bronze: 7 years (regulatory); Silver: 3 years; Gold: current + 2 years; Quarantine: 90 days |
