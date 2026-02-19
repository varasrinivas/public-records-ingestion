# Adding a New State to the Suits Pipeline

## Step-by-Step Guide (using OpenSpec)

### 1. Create a Change
```bash
/opsx:new add-{state}-state-source
/opsx:ff
```

### 2. Define the State Schema

Add to `src/schemas/state_mappings.py`:

```python
"{STATE_CODE}": {
    "field_map": {
        "source_case_field": "case_number",
        "source_date_field": "filing_date",
        "source_type_field": "case_type_raw",
        "source_status_field": "case_status_raw",
        "source_plaintiff_field": "plaintiff_name",
        "source_defendant_field": "defendant_name",
        # ... map all source fields to canonical names
    },
    "county": "County Name",
    "date_format": "MM/dd/yyyy",  # State's date format
    "case_type_map": {
        "STATE_CODE": "CANONICAL_TYPE",
        # ... map all type codes
    },
    "status_map": {
        "STATE_STATUS": "CANONICAL_STATUS",
        # ... map all status values
    },
}
```

### 3. Add to Config
```yaml
# config/pipeline_config.yaml
states:
  {STATE_CODE}:
    name: "State Name"
    county: "County Name"
    format: "csv"
    delimiter: ","
    date_format: "MM/dd/yyyy"
    source_path: "sample_data/{state}_county_suits.csv"
```

### 4. Generate Sample Data
Add a `generate_{state}()` function to `sample_data/generate_state_suits.py`.

### 5. Test
```bash
pytest tests/unit/test_state_mappings.py -v
python run_pipeline.py --date 2025-01-15
pytest tests/integration/ -v
```

### 6. Archive the Change
```bash
/opsx:archive
```
