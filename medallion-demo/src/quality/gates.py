"""
Quality Gates — enforce quality between medallion layers.
Implements: REQ-DQ-001
"""
import pandas as pd
from src.quality.checks import (
    QualityCheck, NotNullCheck, UniqueCheck,
    AcceptedValuesCheck, RangeCheck, run_quality_suite, QualityResult
)


def bronze_to_silver_gate(table: str, df: pd.DataFrame) -> list[QualityResult]:
    """Quality gate between Bronze and Silver layers."""
    checks: list[QualityCheck] = []

    if table == "customers":
        checks = [
            NotNullCheck("bronze", "customers", "customer_id"),
            NotNullCheck("bronze", "customers", "email"),
            UniqueCheck("bronze", "customers", "customer_id", threshold=90.0),
        ]
    elif table == "orders":
        checks = [
            NotNullCheck("bronze", "orders", "order_id"),
            NotNullCheck("bronze", "orders", "customer_id"),
            NotNullCheck("bronze", "orders", "order_date"),
            UniqueCheck("bronze", "orders", "order_id"),
            AcceptedValuesCheck("bronze", "orders", "status",
                                ["completed", "shipped", "processing", "cancelled", "refunded"]),
            RangeCheck("bronze", "orders", "total_amount", min_val=0, max_val=100000),
        ]

    return run_quality_suite(df, checks)


def silver_to_gold_gate(table: str, df: pd.DataFrame) -> list[QualityResult]:
    """Quality gate between Silver and Gold layers."""
    checks: list[QualityCheck] = []

    if table == "customer_360":
        checks = [
            NotNullCheck("gold", "customer_360", "customer_id"),
            UniqueCheck("gold", "customer_360", "customer_id"),
            AcceptedValuesCheck("gold", "customer_360", "ltv_tier",
                                ["platinum", "gold", "silver", "bronze"]),
            RangeCheck("gold", "customer_360", "total_revenue", min_val=0),
            RangeCheck("gold", "customer_360", "total_orders", min_val=0),
        ]

    return run_quality_suite(df, checks)
