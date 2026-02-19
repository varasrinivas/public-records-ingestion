"""
PySpark Data Quality Checks for the Suits Pipeline.
Implements: REQ-DQ-001 through REQ-DQ-003
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.schemas.state_mappings import VALID_CASE_TYPES, VALID_STATUSES


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass
class QualityResult:
    check_name: str
    layer: str
    table_name: str
    records_checked: int
    records_passed: int
    records_failed: int
    pass_rate: float
    threshold: float
    status: CheckStatus
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def not_null_check(df: DataFrame, column: str, layer: str,
                   table: str, threshold: float = 95.0) -> QualityResult:
    total = df.count()
    passed = df.filter(F.col(column).isNotNull() & (F.col(column) != "")).count()
    rate = (passed / total * 100) if total > 0 else 100.0
    status = CheckStatus.PASS if rate >= threshold else (
        CheckStatus.WARN if rate >= 80 else CheckStatus.FAIL)
    return QualityResult(
        f"not_null_{column}", layer, table,
        total, passed, total - passed, rate, threshold, status)


def unique_check(df: DataFrame, column: str, layer: str,
                 table: str, threshold: float = 100.0) -> QualityResult:
    total = df.count()
    unique = df.select(column).distinct().count()
    dupes = total - unique
    rate = (unique / total * 100) if total > 0 else 100.0
    status = CheckStatus.PASS if rate >= threshold else (
        CheckStatus.WARN if rate >= 90 else CheckStatus.FAIL)
    return QualityResult(
        f"unique_{column}", layer, table,
        total, unique, dupes, rate, threshold, status)


def accepted_values_check(df: DataFrame, column: str, accepted: list,
                          layer: str, table: str, threshold: float = 95.0) -> QualityResult:
    total = df.count()
    passed = df.filter(F.col(column).isin(accepted)).count()
    rate = (passed / total * 100) if total > 0 else 100.0
    status = CheckStatus.PASS if rate >= threshold else (
        CheckStatus.WARN if rate >= 80 else CheckStatus.FAIL)
    return QualityResult(
        f"accepted_values_{column}", layer, table,
        total, passed, total - passed, rate, threshold, status)


def bronze_quality_gate(df: DataFrame) -> list[QualityResult]:
    """REQ-DQ-001: Bronze → Silver gate."""
    return [
        not_null_check(df, "case_number", "bronze", "suits"),
        not_null_check(df, "filing_date", "bronze", "suits"),
        not_null_check(df, "plaintiff_name", "bronze", "suits"),
    ]


def silver_quality_gate(df: DataFrame) -> list[QualityResult]:
    """REQ-DQ-002: Silver → Gold gate."""
    return [
        unique_check(df, "suit_id", "silver", "suits"),
        not_null_check(df, "suit_id", "silver", "suits", 99.0),
        not_null_check(df, "filing_date", "silver", "suits", 99.0),
        accepted_values_check(df, "case_type", VALID_CASE_TYPES, "silver", "suits", 98.0),
        accepted_values_check(df, "case_status", VALID_STATUSES, "silver", "suits", 98.0),
    ]


def gold_quality_gate(df: DataFrame) -> list[QualityResult]:
    """REQ-DQ-003: Gold output validation."""
    return [
        unique_check(df, "suit_id", "gold", "suit_best_view"),
        not_null_check(df, "primary_plaintiff", "gold", "suit_best_view", 95.0),
        not_null_check(df, "state_code", "gold", "suit_best_view", 100.0),
    ]
