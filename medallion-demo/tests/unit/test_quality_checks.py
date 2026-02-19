"""Unit tests for the data quality framework."""
import pandas as pd
import pytest

from src.quality.checks import (
    NotNullCheck, UniqueCheck, AcceptedValuesCheck,
    RangeCheck, CheckStatus, run_quality_suite,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", None, "Dave", "Eve"],
        "status": ["active", "active", "inactive", "active", "unknown"],
        "score": [85, 92, 45, 101, 73],
    })


class TestNotNullCheck:
    def test_passes_with_no_nulls(self, sample_df):
        check = NotNullCheck("bronze", "test", "id")
        result = check.run(sample_df)
        assert result.status == CheckStatus.PASS
        assert result.records_passed == 5

    def test_detects_null_values(self, sample_df):
        check = NotNullCheck("bronze", "test", "name", threshold=100.0)
        result = check.run(sample_df)
        assert result.records_failed == 1
        assert result.status == CheckStatus.WARN  # 80% pass rate


class TestUniqueCheck:
    def test_passes_unique_column(self, sample_df):
        check = UniqueCheck("silver", "test", "id")
        result = check.run(sample_df)
        assert result.status == CheckStatus.PASS

    def test_detects_duplicates(self):
        df = pd.DataFrame({"id": [1, 2, 2, 3, 3]})
        check = UniqueCheck("silver", "test", "id")
        result = check.run(df)
        assert result.records_failed == 2


class TestAcceptedValuesCheck:
    def test_passes_valid_values(self, sample_df):
        check = AcceptedValuesCheck(
            "silver", "test", "status",
            ["active", "inactive", "unknown"]
        )
        result = check.run(sample_df)
        assert result.status == CheckStatus.PASS

    def test_detects_invalid_values(self, sample_df):
        check = AcceptedValuesCheck(
            "silver", "test", "status",
            ["active", "inactive"],
            threshold=100.0,
        )
        result = check.run(sample_df)
        assert result.records_failed == 1


class TestRangeCheck:
    def test_in_range(self, sample_df):
        check = RangeCheck("gold", "test", "score", min_val=0, max_val=200)
        result = check.run(sample_df)
        assert result.status == CheckStatus.PASS

    def test_out_of_range(self, sample_df):
        check = RangeCheck("gold", "test", "score", min_val=50, max_val=100)
        result = check.run(sample_df)
        assert result.records_failed == 2  # 45 and 101


class TestRunQualitySuite:
    def test_runs_multiple_checks(self, sample_df):
        checks = [
            NotNullCheck("bronze", "test", "id"),
            UniqueCheck("bronze", "test", "id"),
        ]
        results = run_quality_suite(sample_df, checks)
        assert len(results) == 2
        assert all(r.status == CheckStatus.PASS for r in results)
