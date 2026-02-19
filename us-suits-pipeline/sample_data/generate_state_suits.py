"""
Generate realistic sample court suits data for 6 US states.
Each state has a different format, schema, and field naming convention.

This simulates what real state court FOIA/public records data looks like.
"""
import csv
import json
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
OUTPUT_DIR = Path(__file__).parent
RECORDS_PER_STATE = 500

# --- Shared data pools ---
PLAINTIFF_INDIVIDUALS = [
    "John Smith", "Maria Garcia", "Robert Johnson", "Jennifer Williams",
    "Michael Brown", "Linda Davis", "David Miller", "Sarah Wilson",
    "James Anderson", "Patricia Thomas", "Charles Jackson", "Barbara White",
    "Joseph Harris", "Margaret Martin", "Christopher Lee", "Dorothy Clark",
]
PLAINTIFF_ENTITIES = [
    "Bank of America, N.A.", "Wells Fargo Bank", "JPMorgan Chase Bank",
    "Capital One Bank", "Discover Financial Services", "American Express",
    "Midland Credit Management", "Portfolio Recovery Associates",
    "LVNV Funding LLC", "Cavalry SPV I LLC", "Unifin Inc.",
    "State Farm Insurance", "Allstate Insurance Co.", "GEICO",
    "Progressive Insurance", "Citibank, N.A.", "US Bank, N.A.",
]
DEFENDANT_INDIVIDUALS = [
    "James Rodriguez", "Angela Martinez", "Kevin Thompson", "Michelle Lee",
    "Brian Taylor", "Stephanie Moore", "Jason White", "Nicole Harris",
    "Ryan Clark", "Samantha Lewis", "Justin Walker", "Ashley Robinson",
    "Brandon Hall", "Amber Young", "Zachary King", "Megan Wright",
]
JUDGES = [
    "Hon. Robert A. Wilson", "Hon. Maria S. Gonzalez", "Hon. David Chen",
    "Hon. Patricia Williams", "Hon. Michael O'Brien", "Hon. Susan Kim",
    "Hon. James Jackson", "Hon. Karen Martinez", "Hon. Andrew Patel",
]
LAW_FIRMS = [
    "Smith & Associates", "Johnson Law Group", "Davis Legal Partners",
    "Wilson Elser LLP", "Baker & McKenzie", "Hart & Associates",
    "Padilla Law Firm", "Reed Smith LLP", "Allen & Overy",
]

def random_date(start_year=2022, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def random_amount():
    if random.random() < 0.3:
        return None  # 30% have no amount
    return round(random.uniform(500, 5000000), 2)

def random_plaintiff():
    return random.choice(PLAINTIFF_ENTITIES if random.random() < 0.6 else PLAINTIFF_INDIVIDUALS)

def random_defendant():
    return random.choice(DEFENDANT_INDIVIDUALS if random.random() < 0.7 else PLAINTIFF_ENTITIES)

# ═══════════════════════════════════════
#  TEXAS — Pipe-delimited CSV
# ═══════════════════════════════════════
def generate_tx():
    TX_TYPES = ["CV", "FM", "CR", "PR", "SC", "TX", "EV"]
    TX_STATUS = ["PEND", "DISP", "DISM", "TRANSF", "APPEAL", "CLOSED"]
    
    rows = []
    for i in range(1, RECORDS_PER_STATE + 1):
        d = random_date()
        rows.append({
            "cause_nbr": f"2024-{random.randint(10000, 99999)}",
            "case_number": f"{d.year}-CV-{i:05d}",
            "file_date": d.strftime("%m/%d/%Y"),
            "case_type": random.choice(TX_TYPES),
            "case_status": random.choice(TX_STATUS),
            "plaintiff_name": random_plaintiff(),
            "defendant_name": random_defendant(),
            "judge": random.choice(JUDGES),
            "court_number": f"{random.randint(1, 30)}",
            "amount": str(random_amount() or ""),
            "cause_of_action": random.choice(["Breach of Contract", "Personal Injury",
                "Debt Collection", "Property Damage", "Eviction", "Foreclosure",
                "Employment Dispute", "Insurance Claim"]),
        })
    
    # Add dirty records
    rows.append({"cause_nbr": "", "case_number": "", "file_date": "INVALID",
                  "case_type": "CV", "case_status": "", "plaintiff_name": "",
                  "defendant_name": "", "judge": "", "court_number": "",
                  "amount": "not_a_number", "cause_of_action": ""})
    
    with open(OUTPUT_DIR / "tx_harris_suits.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter="|")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  TX: {len(rows)} records (pipe-delimited CSV)")

# ═══════════════════════════════════════
#  CALIFORNIA — JSON (nested)
# ═══════════════════════════════════════
def generate_ca():
    CA_TYPES = ["CIV", "FAM", "CRIM", "PROB", "SC", "UD"]
    CA_STATUS = ["Active", "Disposed", "Dismissed", "Transferred", "Pending"]
    
    records = []
    for i in range(1, RECORDS_PER_STATE + 1):
        d = random_date()
        disp_date = (d + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d") \
                    if random.random() < 0.4 else None
        records.append({
            "docket_id": f"LA-{d.year}-{random.randint(100000, 999999)}",
            "case_type_code": random.choice(CA_TYPES),
            "filing_date": d.strftime("%Y-%m-%d"),
            "status": random.choice(CA_STATUS),
            "court_division": f"Division {random.randint(1, 50)}",
            "parties": {
                "plaintiffs": [
                    {"name": random_plaintiff(),
                     "attorney": random.choice(LAW_FIRMS) if random.random() < 0.7 else None}
                ],
                "defendants": [
                    {"name": random_defendant(),
                     "attorney": random.choice(LAW_FIRMS) if random.random() < 0.5 else None}
                    for _ in range(random.randint(1, 3))
                ]
            },
            "amount_controversy": random_amount(),
            "disposition": {
                "type": random.choice(["Judgment", "Settlement", "Default", None]),
                "date": disp_date,
            },
        })
    
    with open(OUTPUT_DIR / "ca_la_suits.json", "w") as f:
        json.dump(records, f, indent=2, default=str)
    print(f"  CA: {len(records)} records (nested JSON)")

# ═══════════════════════════════════════
#  NEW YORK — Comma CSV
# ═══════════════════════════════════════
def generate_ny():
    NY_TYPES = ["Civil", "Matrimonial", "Criminal", "Surrogate", "Small Claims",
                "L&T", "Tort", "Contract", "Real Prop"]
    NY_STATUS = ["Active", "Disposed", "Dismissed", "Settled", "Judgement Entered"]
    
    rows = []
    for i in range(1, RECORDS_PER_STATE + 1):
        d = random_date()
        rows.append({
            "index_number": f"{d.year}/{random.randint(10000, 99999)}",
            "action_type": random.choice(NY_TYPES),
            "date_filed": d.strftime("%m/%d/%Y"),
            "status": random.choice(NY_STATUS),
            "county": "Kings",
            "plaintiff": random_plaintiff(),
            "defendant": random_defendant(),
            "judge_assigned": random.choice(JUDGES),
            "relief_sought": str(random_amount() or ""),
            "disposition_date": (d + timedelta(days=random.randint(60, 500))).strftime("%m/%d/%Y")
                               if random.random() < 0.35 else "",
        })
    
    with open(OUTPUT_DIR / "ny_kings_suits.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  NY: {len(rows)} records (comma CSV)")

# ═══════════════════════════════════════
#  FLORIDA — CSV with YYYYMMDD dates
# ═══════════════════════════════════════
def generate_fl():
    FL_TYPES = ["CA", "DR", "CF", "MM", "CP", "SC", "CC"]
    FL_STATUS = ["OPEN", "CLOSED", "REOPEN", "DISPOSED", "INACTIVE"]
    
    rows = []
    for i in range(1, RECORDS_PER_STATE + 1):
        d = random_date()
        rows.append({
            "case_id": f"13-{d.year}-{random.choice(FL_TYPES)}-{random.randint(100000, 999999)}",
            "case_type": random.choice(FL_TYPES),
            "filed_dt": d.strftime("%Y%m%d"),
            "case_status": random.choice(FL_STATUS),
            "division": f"Division {random.choice(['A','B','C','D','E','F'])}",
            "pty_plaintiff": random_plaintiff(),
            "pty_defendant": random_defendant(),
            "judge_name": random.choice(JUDGES),
            "amt_claimed": str(random_amount() or "0.00"),
            "disp_dt": (d + timedelta(days=random.randint(30, 400))).strftime("%Y%m%d")
                       if random.random() < 0.4 else "",
            "disp_type": random.choice(["JUDGMENT", "SETTLEMENT", "DISMISSAL", ""])
                        if random.random() < 0.4 else "",
        })
    
    with open(OUTPUT_DIR / "fl_miamidade_suits.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  FL: {len(rows)} records (CSV, YYYYMMDD dates)")

# ═══════════════════════════════════════
#  ILLINOIS — CSV with DD-Mon-YYYY dates
# ═══════════════════════════════════════
def generate_il():
    IL_TYPES = ["L", "D", "CR", "P", "SC", "EV", "CH"]
    IL_STATUS = ["Open", "Closed", "Dismissed", "Disposed", "Continued"]
    
    rows = []
    for i in range(1, RECORDS_PER_STATE + 1):
        d = random_date()
        rows.append({
            "case_number": f"{d.year}L{random.randint(100000, 999999)}",
            "case_category": random.choice(IL_TYPES),
            "filing_date": d.strftime("%d-%b-%Y"),
            "case_status": random.choice(IL_STATUS),
            "court_room": f"Room {random.randint(100, 999)}",
            "plaintiff_info": random_plaintiff(),
            "defendant_info": random_defendant(),
            "presiding_judge": random.choice(JUDGES),
            "demand_amount": str(random_amount() or ""),
        })
    
    with open(OUTPUT_DIR / "il_cook_suits.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  IL: {len(rows)} records (CSV, DD-Mon-YYYY dates)")

# ═══════════════════════════════════════
#  OHIO — Tab-delimited CSV
# ═══════════════════════════════════════
def generate_oh():
    OH_TYPES = ["CV", "DR", "CR", "PB", "SC", "FED"]
    OH_STATUS = ["ACTIVE", "TERMINATED", "DISMISSED", "TRANSFERRED"]
    
    rows = []
    for i in range(1, RECORDS_PER_STATE + 1):
        d = random_date()
        rows.append({
            "case_num": f"CV-{d.year}-{random.randint(100000, 999999)}",
            "type_cd": random.choice(OH_TYPES),
            "file_dt": f"{d.month}/{d.day}/{d.year}",  # M/D/YYYY
            "status_cd": random.choice(OH_STATUS),
            "plaintiff_nm": random_plaintiff(),
            "defendant_nm": random_defendant(),
            "judge_nm": random.choice(JUDGES),
            "claim_amt": str(random_amount() or ""),
            "disp_dt": f"{(d + timedelta(days=random.randint(30, 300))).month}/"
                       f"{(d + timedelta(days=random.randint(30, 300))).day}/"
                       f"{(d + timedelta(days=random.randint(30, 300))).year}"
                       if random.random() < 0.35 else "",
        })
    
    with open(OUTPUT_DIR / "oh_cuyahoga_suits.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  OH: {len(rows)} records (tab-delimited CSV)")


if __name__ == "__main__":
    print("Generating state court suits data...")
    generate_tx()
    generate_ca()
    generate_ny()
    generate_fl()
    generate_il()
    generate_oh()
    print(f"\nDone! Files written to {OUTPUT_DIR}/")
