# Data Quality Framework — Suits Pipeline

## Requirements

### REQ-DQ-001: Bronze Quality Gate
Checks before Bronze → Silver:
- `case_number` / `case_id` is not null
- Filing date is parseable and not in the future
- At least one party name is present
- State code is valid (TX, CA, NY, FL, IL, OH)
- Pass threshold: 95%

### REQ-DQ-002: Silver Quality Gate
Checks before Silver → Gold:
- `suit_id` is unique
- `filing_date` is valid DATE
- `case_type` is in canonical taxonomy
- `case_status` is in canonical status list
- `state_code` matches a valid state
- At least one party record exists per suit
- Pass threshold: 98%

### REQ-DQ-003: Gold Quality Gate
Checks on Gold output:
- Referential integrity: every party references a valid suit
- No null `primary_plaintiff` on suit_best_view
- `days_open` is non-negative
- Analytics counts match underlying data
- Pass threshold: 99%

### REQ-DQ-004: Cross-Layer Reconciliation
After each run:
- Bronze record count per state matches source file row count
- Silver record count ≤ Bronze count (dedup reduces)
- Gold suit count = Silver unique suit count
- Variance alerts if counts differ by >5%
