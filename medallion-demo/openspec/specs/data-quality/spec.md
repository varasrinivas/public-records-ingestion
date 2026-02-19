# Data Quality Framework Specification

## Purpose
Ensure data integrity across all medallion layers with automated validation,
quarantine handling, and quality metrics reporting.

## Requirements

### REQ-DQ-001: Quality Gates
The system SHALL enforce quality gates between layers:
- Bronze → Silver: Schema validation, null checks, type validation
- Silver → Gold: Referential integrity, business rule validation
- Each gate produces a pass/fail result with detailed metrics

### REQ-DQ-002: Quality Metrics
Each quality check SHALL produce:
- `check_name`: Descriptive name of the check
- `layer`: bronze | silver | gold
- `table_name`: Target table
- `records_checked`: Total records evaluated
- `records_passed`: Count passing the check
- `records_failed`: Count failing the check
- `pass_rate`: Percentage (0-100)
- `threshold`: Minimum acceptable pass rate
- `status`: PASS | FAIL | WARN
- `checked_at`: Timestamp of execution

### REQ-DQ-003: Quarantine Management
Failed records SHALL be quarantined:
- Stored in `quarantine/{layer}/{table}/{date}/`
- Include original record + failure reason + check name
- Quarantined records are excluded from downstream processing
- Weekly report of quarantine volumes by failure reason

### REQ-DQ-004: Alerting
The system SHALL alert on:
- Any quality gate FAIL (blocks pipeline progression)
- Pass rate below warning threshold (80% default)
- Quarantine volume spike (>2x 7-day average)
- Missing data (expected partition has 0 records)
