# Silver Transformation Layer Specification

## Purpose
Transform raw Bronze data into cleansed, conformed, and deduplicated datasets.
Apply business rules, standardize schemas, and quarantine invalid records.

## Requirements

### REQ-SLV-001: Deduplication
The system SHALL deduplicate records using:
- Primary key fields defined per entity
- Latest `_ingestion_timestamp` wins for duplicate keys
- Dedup window: configurable (default 7 days lookback)

### REQ-SLV-002: Schema Validation
The system SHALL validate all records against defined schemas:
- Required fields must be non-null
- Data types must match specification
- Enum fields must contain valid values
- String patterns must match (email, phone, postal code)

#### Scenario: Invalid Record Quarantine
- GIVEN a Bronze record with null `customer_id`
- WHEN silver transformation runs
- THEN the record is moved to `quarantine/customers/`
- AND a quality event is logged with reason "REQUIRED_FIELD_NULL"
- AND the record is excluded from Silver output

### REQ-SLV-003: Type Casting & Standardization
The system SHALL standardize data types:
- Dates: ISO 8601 format (YYYY-MM-DD)
- Timestamps: UTC with timezone
- Currency: Decimal(18,2) in minor units (cents)
- Phone: E.164 format
- Email: lowercase, trimmed
- Names: trimmed, title case optional

### REQ-SLV-004: SCD Type 2 for Dimensions
The system SHALL implement Slowly Changing Dimensions Type 2:
- Track historical changes for dimension tables (customers, products)
- Columns: `valid_from`, `valid_to`, `is_current`
- Hash of tracked columns to detect changes
- Only insert new version when tracked columns change

### REQ-SLV-005: Data Lineage
Every Silver record SHALL include:
- `_bronze_batch_id`: Reference to source Bronze batch
- `_silver_processed_at`: Transformation timestamp
- `_silver_version`: Schema version applied
