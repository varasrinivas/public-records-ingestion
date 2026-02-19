"""
Data Quality Checks Framework
Implements: REQ-DQ-001 through REQ-DQ-004

Reusable quality checks that run between medallion layers.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable

import pandas as pd


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass
class QualityResult:
    """Result of a data quality check."""
    check_name: str
    layer: str
    table_name: str
    records_checked: int
    records_passed: int
    records_failed: int
    pass_rate: float
    threshold: float
    status: CheckStatus
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: str = ""

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "layer": self.layer,
            "table_name": self.table_name,
            "records_checked": self.records_checked,
            "records_passed": self.records_passed,
            "records_failed": self.records_failed,
            "pass_rate": round(self.pass_rate, 2),
            "threshold": self.threshold,
            "status": self.status.value,
            "checked_at": self.checked_at,
            "details": self.details,
        }


class QualityCheck:
    """Base class for data quality checks."""

    def __init__(self, name: str, layer: str, table: str, threshold: float = 95.0):
        self.name = name
        self.layer = layer
        self.table = table
        self.threshold = threshold

    def _make_result(self, total: int, passed: int, details: str = "") -> QualityResult:
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 100.0

        if pass_rate >= self.threshold:
            status = CheckStatus.PASS
        elif pass_rate >= 80.0:
            status = CheckStatus.WARN
        else:
            status = CheckStatus.FAIL

        return QualityResult(
            check_name=self.name,
            layer=self.layer,
            table_name=self.table,
            records_checked=total,
            records_passed=passed,
            records_failed=failed,
            pass_rate=pass_rate,
            threshold=self.threshold,
            status=status,
            details=details,
        )


class NotNullCheck(QualityCheck):
    """Check that a column has no null values."""

    def __init__(self, layer: str, table: str, column: str, threshold: float = 95.0):
        super().__init__(f"not_null_{column}", layer, table, threshold)
        self.column = column

    def run(self, df: pd.DataFrame) -> QualityResult:
        total = len(df)
        passed = int(df[self.column].notna().sum())
        return self._make_result(total, passed, f"Column: {self.column}")


class UniqueCheck(QualityCheck):
    """Check that a column has unique values."""

    def __init__(self, layer: str, table: str, column: str, threshold: float = 100.0):
        super().__init__(f"unique_{column}", layer, table, threshold)
        self.column = column

    def run(self, df: pd.DataFrame) -> QualityResult:
        total = len(df)
        unique_count = df[self.column].nunique()
        dupes = total - unique_count
        return self._make_result(total, total - dupes, f"Duplicates found: {dupes}")


class AcceptedValuesCheck(QualityCheck):
    """Check that column values are within an accepted set."""

    def __init__(self, layer: str, table: str, column: str,
                 accepted: list, threshold: float = 95.0):
        super().__init__(f"accepted_values_{column}", layer, table, threshold)
        self.column = column
        self.accepted = accepted

    def run(self, df: pd.DataFrame) -> QualityResult:
        total = len(df)
        passed = int(df[self.column].isin(self.accepted).sum())
        invalid = df[~df[self.column].isin(self.accepted)][self.column].unique()[:5]
        return self._make_result(total, passed, f"Invalid values (sample): {list(invalid)}")


class RangeCheck(QualityCheck):
    """Check that numeric values fall within a range."""

    def __init__(self, layer: str, table: str, column: str,
                 min_val: float = None, max_val: float = None, threshold: float = 95.0):
        super().__init__(f"range_{column}", layer, table, threshold)
        self.column = column
        self.min_val = min_val
        self.max_val = max_val

    def run(self, df: pd.DataFrame) -> QualityResult:
        total = len(df)
        series = pd.to_numeric(df[self.column], errors="coerce")
        mask = pd.Series(True, index=df.index)
        if self.min_val is not None:
            mask &= series >= self.min_val
        if self.max_val is not None:
            mask &= series <= self.max_val
        passed = int(mask.sum())
        return self._make_result(total, passed,
                                  f"Range: [{self.min_val}, {self.max_val}]")


def run_quality_suite(df: pd.DataFrame, checks: list[QualityCheck]) -> list[QualityResult]:
    """Run a suite of quality checks and return results."""
    results = []
    for check in checks:
        try:
            result = check.run(df)
            results.append(result)
        except Exception as e:
            results.append(QualityResult(
                check_name=check.name, layer=check.layer, table_name=check.table,
                records_checked=len(df), records_passed=0, records_failed=len(df),
                pass_rate=0.0, threshold=check.threshold, status=CheckStatus.FAIL,
                details=f"Check error: {str(e)}"
            ))
    return results
