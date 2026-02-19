# Silver Layer — Canonical Suits Schema Specification

## Purpose
Transform state-specific raw suit records into a unified canonical schema.
Every suit record, regardless of originating state, conforms to the same
structure after Silver transformation.

## Requirements

### REQ-SLV-001: Canonical Suit Record Schema
The Silver canonical suit record SHALL have the following fields:

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| suit_id | STRING | NO | Globally unique: `{state}_{county}_{case_number}` |
| state_code | STRING(2) | NO | Two-letter state code |
| county | STRING | NO | Normalized county name |
| case_number | STRING | NO | State-native case/docket number |
| case_type | STRING | NO | Harmonized case type (see REQ-SLV-003) |
| case_type_raw | STRING | YES | Original state-specific type code |
| filing_date | DATE | NO | Date suit was filed (ISO 8601) |
| case_status | STRING | NO | Harmonized status (see REQ-SLV-004) |
| case_status_raw | STRING | YES | Original state-specific status |
| court_name | STRING | YES | Court name |
| judge_name | STRING | YES | Assigned judge (Title Case) |
| cause_of_action | STRING | YES | Legal basis / cause description |
| amount_demanded | DECIMAL(18,2) | YES | Dollar amount if available |
| disposition | STRING | YES | Case outcome if resolved |
| disposition_date | DATE | YES | Date of disposition |
| last_activity_date | DATE | YES | Most recent docket activity |

### REQ-SLV-002: Canonical Party Record Schema
Each suit SHALL have associated party records:

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| party_id | STRING | NO | `{suit_id}_{party_type}_{sequence}` |
| suit_id | STRING | NO | Foreign key to canonical suit |
| party_type | STRING | NO | PLAINTIFF, DEFENDANT, ATTORNEY, OTHER |
| party_name | STRING | NO | Normalized party name |
| party_name_raw | STRING | YES | Original name from source |
| is_entity | BOOLEAN | NO | True if organization, false if individual |
| attorney_name | STRING | YES | Representing attorney |
| attorney_firm | STRING | YES | Law firm name |

### REQ-SLV-003: Case Type Harmonization
The system SHALL map state-specific case types to a canonical taxonomy:

| Canonical Type | TX | CA | NY | FL | IL | OH |
|----------------|----|----|----|----|----|----|
| CIVIL | CV | CIV | Civil | CA | L | CV |
| FAMILY | FM | FAM | Matrimonial | DR | D | DR |
| CRIMINAL | CR | CRIM | Criminal | CF/MM | CR | CR |
| PROBATE | PR | PROB | Surrogate | CP | P | PB |
| SMALL_CLAIMS | SC | SC | Small Claims | SC | SC | SC |
| TAX | TX | TAX | Tax | — | TX | TX |
| EVICTION | EV | UD | L&T | CC/EV | EV | FED |
| PERSONAL_INJURY | PI | PI | Tort | CA-PI | L-PI | CV-PI |
| CONTRACT | CT | CT | Contract | CA-CT | L-CT | CV-CT |
| REAL_PROPERTY | RP | RE | Real Prop | CA-RP | CH | CV-RP |
| OTHER | * | * | * | * | * | * |

### REQ-SLV-004: Status Harmonization
The system SHALL map state-specific statuses to canonical values:

| Canonical Status | Description |
|-----------------|-------------|
| OPEN | Active, pending |
| DISPOSED | Closed with judgment/settlement |
| DISMISSED | Dismissed (with or without prejudice) |
| TRANSFERRED | Transferred to another court/jurisdiction |
| APPEALED | Under appeal |
| STAYED | Proceedings stayed |
| SEALED | Record sealed |
| UNKNOWN | Status could not be determined |

### REQ-SLV-005: Name Normalization
Party names SHALL be normalized:
- Remove legal suffixes for matching: LLC, Inc., Corp., Ltd., et al.
- Title Case for individuals: "JOHN DOE" → "John Doe"
- Preserve entity casing: "Bank of America" stays as-is
- Detect entity vs. individual by pattern matching
- Strip extra whitespace and special characters

### REQ-SLV-006: Date Standardization
All dates SHALL be converted to ISO 8601 (YYYY-MM-DD):
- TX format: MM/DD/YYYY
- CA format: YYYY-MM-DD (already standard)
- NY format: MM/DD/YYYY
- FL format: YYYYMMDD (no separators)
- IL format: DD-Mon-YYYY (e.g., "15-Jan-2025")
- OH format: M/D/YYYY (single-digit months/days)

### REQ-SLV-007: Deduplication
- Deduplicate by `suit_id` (state + county + case_number)
- Latest `_ingestion_timestamp` wins
- Log dedup count per batch

### REQ-SLV-008: Quarantine
Invalid records SHALL be quarantined with:
- Original record data
- Failure reason(s)
- Originating state/county
- Quality check that failed
