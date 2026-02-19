"""Unit tests for state field mappings and canonicalization logic."""
import pytest
from src.schemas.state_mappings import (
    STATE_FIELD_MAPPINGS, VALID_CASE_TYPES, VALID_STATUSES
)


class TestStateMappings:
    """Verify all state mappings are complete and valid."""

    EXPECTED_STATES = ["TX", "CA", "NY", "FL", "IL", "OH"]

    def test_all_states_have_mappings(self):
        for state in self.EXPECTED_STATES:
            assert state in STATE_FIELD_MAPPINGS, f"Missing mapping for {state}"

    def test_all_states_have_required_keys(self):
        required = ["field_map", "date_format", "case_type_map", "status_map"]
        for state, mapping in STATE_FIELD_MAPPINGS.items():
            for key in required:
                assert key in mapping, f"{state} missing '{key}'"

    def test_case_type_maps_to_valid_types(self):
        for state, mapping in STATE_FIELD_MAPPINGS.items():
            for raw, canonical in mapping["case_type_map"].items():
                assert canonical in VALID_CASE_TYPES, \
                    f"{state}: '{raw}' maps to invalid type '{canonical}'"

    def test_status_maps_to_valid_statuses(self):
        for state, mapping in STATE_FIELD_MAPPINGS.items():
            for raw, canonical in mapping["status_map"].items():
                assert canonical in VALID_STATUSES, \
                    f"{state}: '{raw}' maps to invalid status '{canonical}'"

    def test_field_maps_include_case_number(self):
        for state, mapping in STATE_FIELD_MAPPINGS.items():
            canonical_fields = list(mapping["field_map"].values())
            assert "case_number" in canonical_fields, \
                f"{state}: field_map missing 'case_number' target"

    def test_field_maps_include_filing_date(self):
        for state, mapping in STATE_FIELD_MAPPINGS.items():
            canonical_fields = list(mapping["field_map"].values())
            assert "filing_date" in canonical_fields, \
                f"{state}: field_map missing 'filing_date' target"

    def test_no_duplicate_canonical_targets(self):
        for state, mapping in STATE_FIELD_MAPPINGS.items():
            targets = list(mapping["field_map"].values())
            assert len(targets) == len(set(targets)), \
                f"{state}: duplicate canonical field targets in field_map"
