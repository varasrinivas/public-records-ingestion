"""Unit tests for Gold Customer 360 — RFM scoring and LTV classification."""
import pandas as pd
import pytest

from src.gold.customer_360 import assign_ltv_tier, assign_rfm_segment, compute_rfm_scores


LTV_TIERS = {"platinum": 5000, "gold": 1000, "silver": 250, "bronze": 0}


class TestLtvTier:
    """Tests for LTV tier classification (REQ-GLD-002)."""

    def test_platinum_tier(self):
        assert assign_ltv_tier(5000, LTV_TIERS) == "platinum"
        assert assign_ltv_tier(10000, LTV_TIERS) == "platinum"

    def test_gold_tier(self):
        assert assign_ltv_tier(1000, LTV_TIERS) == "gold"
        assert assign_ltv_tier(4999.99, LTV_TIERS) == "gold"

    def test_silver_tier(self):
        assert assign_ltv_tier(250, LTV_TIERS) == "silver"
        assert assign_ltv_tier(999.99, LTV_TIERS) == "silver"

    def test_bronze_tier(self):
        assert assign_ltv_tier(0, LTV_TIERS) == "bronze"
        assert assign_ltv_tier(249.99, LTV_TIERS) == "bronze"

    def test_negative_revenue(self):
        assert assign_ltv_tier(-100, LTV_TIERS) == "bronze"


class TestRfmSegment:
    """Tests for RFM segment assignment (REQ-GLD-002)."""

    def test_champions(self):
        row = pd.Series({"r_score": 5, "f_score": 5, "m_score": 5})
        assert assign_rfm_segment(row) == "Champions"

    def test_loyal(self):
        row = pd.Series({"r_score": 4, "f_score": 3, "m_score": 3})
        assert assign_rfm_segment(row) == "Loyal"

    def test_new_customers(self):
        row = pd.Series({"r_score": 5, "f_score": 1, "m_score": 1})
        assert assign_rfm_segment(row) == "New Customers"

    def test_at_risk(self):
        row = pd.Series({"r_score": 2, "f_score": 4, "m_score": 3})
        assert assign_rfm_segment(row) == "At Risk"

    def test_lost(self):
        row = pd.Series({"r_score": 1, "f_score": 1, "m_score": 1})
        assert assign_rfm_segment(row) == "Lost"


class TestComputeRfmScores:
    """Tests for RFM score computation."""

    def test_scores_are_1_to_5(self):
        df = pd.DataFrame({
            "last_order_date": pd.date_range("2024-01-01", periods=20, freq="15D"),
            "total_orders": range(1, 21),
            "total_revenue": [x * 100 for x in range(1, 21)],
        })
        result = compute_rfm_scores(df, "2025-01-01")
        assert result["r_score"].between(1, 5).all()
        assert result["f_score"].between(1, 5).all()
        assert result["m_score"].between(1, 5).all()

    def test_rfm_score_composite(self):
        df = pd.DataFrame({
            "last_order_date": pd.date_range("2024-01-01", periods=10, freq="30D"),
            "total_orders": range(1, 11),
            "total_revenue": [x * 50 for x in range(1, 11)],
        })
        result = compute_rfm_scores(df, "2025-01-01")
        assert "rfm_score" in result.columns
        assert result["rfm_score"].between(111, 555).all()
