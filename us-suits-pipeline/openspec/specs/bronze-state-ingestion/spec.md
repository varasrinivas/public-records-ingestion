# Bronze Layer — State Court Suits Ingestion Specification

## Purpose
Ingest raw court suit/litigation records from multiple US state court systems.
Each state provides data in a different format, schema, and delivery mechanism.
The Bronze layer stores data exactly as received with lineage metadata.

## Requirements

### REQ-BRZ-001: Multi-Format Ingestion
The system SHALL ingest court data from the following formats:
- CSV (pipe-delimited, comma-delimited, tab-delimited)
- JSON (nested and flat structures)
- XML (state court XML schemas)
- Fixed-width text files

### REQ-BRZ-002: State-Specific Schema Preservation
The system SHALL preserve the original state-specific schema:
- TX: case_number, cause_nbr, file_date, case_status, plaintiff_name, defendant_name
- CA: docket_id, case_type_code, filing_date, parties_json, court_division
- NY: index_number, action_type, date_filed, plaintiff, defendant, county
- FL: case_id, case_type, filed_dt, pty_plaintiff, pty_defendant, division
- IL: case_number, case_category, filing_date, party_info_xml, court_room
- OH: case_num, type_cd, file_dt, plaintiff_nm, defendant_nm, judge_nm

### REQ-BRZ-003: Metadata Enrichment
Every Bronze record SHALL include:
- `_ingestion_timestamp`: UTC time of extraction
- `_source_state`: Two-letter state code (TX, CA, NY, FL, IL, OH)
- `_source_county`: County/jurisdiction name
- `_source_format`: File format (csv, json, xml, fixed_width)
- `_batch_id`: Deterministic batch identifier
- `_file_path`: Original source file path
- `_row_number`: Position in original file (for traceability)

### REQ-BRZ-004: Partitioning Strategy
Bronze data SHALL be partitioned by:
- `_source_state` (first level)
- `ingestion_date` (second level)
- Format: `bronze/suits/state=TX/ingestion_date=2025-01-15/`

### REQ-BRZ-005: Idempotent Ingestion
Re-running ingestion for the same state + date SHALL overwrite the
partition without creating duplicates.

### REQ-BRZ-006: Error Handling
- Malformed rows: write to `bronze_errors/` with error details
- File-level failures: retry 3x with exponential backoff
- Partial success: commit valid rows, quarantine failures
