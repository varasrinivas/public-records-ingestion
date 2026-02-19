# Bronze Ingestion Layer Specification

## Purpose
Ingest raw data from multiple sources into the Bronze layer of the medallion
architecture. Data is stored append-only in Parquet/Delta format with full
lineage metadata.

## Requirements

### REQ-BRZ-001: Source Ingestion
The system SHALL ingest data from the following source types:
- PostgreSQL databases (CDC or full extract)
- REST APIs (paginated JSON responses)
- Flat files (CSV, JSON, JSONL)
- Streaming sources (Kafka topics)

#### Scenario: PostgreSQL Full Extract
- GIVEN a configured PostgreSQL connection
- WHEN the ingestion job runs for table `orders`
- THEN all rows are extracted as-is
- AND stored in `bronze/orders/` partitioned by `ingestion_date`
- AND a `_metadata` struct is appended with source info

### REQ-BRZ-002: Metadata Tracking
The system SHALL attach the following metadata to every ingested record:
- `_ingestion_timestamp`: UTC timestamp of extraction
- `_source_system`: Identifier of the source (e.g., "postgres_prod")
- `_source_table`: Original table or endpoint name
- `_batch_id`: Unique identifier for the ingestion batch
- `_file_path`: Original file path (for file-based sources)

### REQ-BRZ-003: Schema-on-Read
The Bronze layer SHALL NOT enforce schemas on write.
- Raw data is stored exactly as received
- Schema inference happens at read time
- Schema evolution is handled by Delta Lake

### REQ-BRZ-004: Idempotent Ingestion
The system SHALL support idempotent re-ingestion:
- Re-running the same batch overwrites the same partition
- No duplicate records are created
- `_batch_id` is deterministic for the same source + date

### REQ-BRZ-005: Error Handling
The system SHALL handle ingestion errors gracefully:
- Network failures: retry with exponential backoff (3 retries)
- Schema detection failures: store raw bytes + error log
- Partial failures: commit successful records, log failures
