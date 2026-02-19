"""
State-to-canonical field mappings for Silver transformation.
Implements: REQ-SLV-001, REQ-SLV-003, REQ-SLV-004, REQ-SLV-006

Each state mapping defines:
- field_map: state column → canonical column
- case_type_map: state type code → canonical case type
- status_map: state status → canonical status
- date_format: state's date format string
"""

STATE_FIELD_MAPPINGS: dict[str, dict] = {
    "TX": {
        "field_map": {
            "case_number": "case_number",
            "file_date": "filing_date",
            "case_type": "case_type_raw",
            "case_status": "case_status_raw",
            "plaintiff_name": "plaintiff_name",
            "defendant_name": "defendant_name",
            "judge": "judge_name",
            "amount": "amount_demanded",
            "cause_of_action": "cause_of_action",
        },
        "county": "Harris County",
        "date_format": "MM/dd/yyyy",
        "case_type_map": {
            "CV": "CIVIL", "FM": "FAMILY", "CR": "CRIMINAL",
            "PR": "PROBATE", "SC": "SMALL_CLAIMS", "TX": "TAX", "EV": "EVICTION",
        },
        "status_map": {
            "PEND": "OPEN", "DISP": "DISPOSED", "DISM": "DISMISSED",
            "TRANSF": "TRANSFERRED", "APPEAL": "APPEALED", "CLOSED": "DISPOSED",
        },
    },
    "CA": {
        "field_map": {
            "docket_id": "case_number",
            "filing_date": "filing_date",
            "case_type_code": "case_type_raw",
            "status": "case_status_raw",
            "court_division": "court_name",
            "amount_controversy": "amount_demanded",
        },
        "county": "Los Angeles County",
        "date_format": "yyyy-MM-dd",
        "case_type_map": {
            "CIV": "CIVIL", "FAM": "FAMILY", "CRIM": "CRIMINAL",
            "PROB": "PROBATE", "SC": "SMALL_CLAIMS", "UD": "EVICTION",
        },
        "status_map": {
            "Active": "OPEN", "Disposed": "DISPOSED", "Dismissed": "DISMISSED",
            "Transferred": "TRANSFERRED", "Pending": "OPEN",
        },
    },
    "NY": {
        "field_map": {
            "index_number": "case_number",
            "date_filed": "filing_date",
            "action_type": "case_type_raw",
            "status": "case_status_raw",
            "plaintiff": "plaintiff_name",
            "defendant": "defendant_name",
            "judge_assigned": "judge_name",
            "relief_sought": "amount_demanded",
            "disposition_date": "disposition_date",
        },
        "county_field": "county",
        "date_format": "MM/dd/yyyy",
        "case_type_map": {
            "Civil": "CIVIL", "Matrimonial": "FAMILY", "Criminal": "CRIMINAL",
            "Surrogate": "PROBATE", "Small Claims": "SMALL_CLAIMS",
            "L&T": "EVICTION", "Tort": "PERSONAL_INJURY",
            "Contract": "CONTRACT", "Real Prop": "REAL_PROPERTY",
        },
        "status_map": {
            "Active": "OPEN", "Disposed": "DISPOSED", "Dismissed": "DISMISSED",
            "Settled": "DISPOSED", "Judgement Entered": "DISPOSED",
        },
    },
    "FL": {
        "field_map": {
            "case_id": "case_number",
            "filed_dt": "filing_date",
            "case_type": "case_type_raw",
            "case_status": "case_status_raw",
            "division": "court_name",
            "pty_plaintiff": "plaintiff_name",
            "pty_defendant": "defendant_name",
            "judge_name": "judge_name",
            "amt_claimed": "amount_demanded",
            "disp_dt": "disposition_date",
            "disp_type": "disposition",
        },
        "county": "Miami-Dade County",
        "date_format": "yyyyMMdd",
        "case_type_map": {
            "CA": "CIVIL", "DR": "FAMILY", "CF": "CRIMINAL", "MM": "CRIMINAL",
            "CP": "PROBATE", "SC": "SMALL_CLAIMS", "CC": "EVICTION",
        },
        "status_map": {
            "OPEN": "OPEN", "CLOSED": "DISPOSED", "REOPEN": "OPEN",
            "DISPOSED": "DISPOSED", "INACTIVE": "DISPOSED",
        },
    },
    "IL": {
        "field_map": {
            "case_number": "case_number",
            "filing_date": "filing_date",
            "case_category": "case_type_raw",
            "case_status": "case_status_raw",
            "court_room": "court_name",
            "plaintiff_info": "plaintiff_name",
            "defendant_info": "defendant_name",
            "presiding_judge": "judge_name",
            "demand_amount": "amount_demanded",
        },
        "county": "Cook County",
        "date_format": "dd-MMM-yyyy",
        "case_type_map": {
            "L": "CIVIL", "D": "FAMILY", "CR": "CRIMINAL",
            "P": "PROBATE", "SC": "SMALL_CLAIMS", "EV": "EVICTION", "CH": "REAL_PROPERTY",
        },
        "status_map": {
            "Open": "OPEN", "Closed": "DISPOSED", "Dismissed": "DISMISSED",
            "Disposed": "DISPOSED", "Continued": "OPEN",
        },
    },
    "OH": {
        "field_map": {
            "case_num": "case_number",
            "file_dt": "filing_date",
            "type_cd": "case_type_raw",
            "status_cd": "case_status_raw",
            "plaintiff_nm": "plaintiff_name",
            "defendant_nm": "defendant_name",
            "judge_nm": "judge_name",
            "claim_amt": "amount_demanded",
            "disp_dt": "disposition_date",
        },
        "county": "Cuyahoga County",
        "date_format": "M/d/yyyy",
        "case_type_map": {
            "CV": "CIVIL", "DR": "FAMILY", "CR": "CRIMINAL",
            "PB": "PROBATE", "SC": "SMALL_CLAIMS", "FED": "EVICTION",
        },
        "status_map": {
            "ACTIVE": "OPEN", "TERMINATED": "DISPOSED",
            "DISMISSED": "DISMISSED", "TRANSFERRED": "TRANSFERRED",
        },
    },
}

# Canonical case types (REQ-SLV-003)
VALID_CASE_TYPES = [
    "CIVIL", "FAMILY", "CRIMINAL", "PROBATE", "SMALL_CLAIMS",
    "TAX", "EVICTION", "PERSONAL_INJURY", "CONTRACT",
    "REAL_PROPERTY", "OTHER",
]

# Canonical statuses (REQ-SLV-004)
VALID_STATUSES = [
    "OPEN", "DISPOSED", "DISMISSED", "TRANSFERRED",
    "APPEALED", "STAYED", "SEALED", "UNKNOWN",
]
