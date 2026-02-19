"""Integration test — run full Bronze → Silver → Gold pipeline with sample data."""
import os
import pytest
import subprocess
from pathlib import Path

from src.utils.config import load_config
from src.bronze.ingest import BronzeIngester
from src.silver.transform import SilverTransformer
from src.gold.customer_360 import Customer360Builder
from src.gold.daily_revenue import DailyRevenueBuilder
from src.quality.gates import silver_to_gold_gate
import pandas as pd


@pytest.fixture(scope="module")
def config():
    """Load pipeline config."""
    return load_config()


@pytest.fixture(scope="module", autouse=True)
def generate_sample_data():
    """Generate sample data before tests."""
    subprocess.run(["python", "sample_data/generate_sample_data.py"], check=True)


@pytest.fixture(scope="module")
def run_pipeline(config):
    """Run the full pipeline and return results."""
    # Bronze
    ingester = BronzeIngester(config)
    bronze_results = ingester.ingest_all("2025-01-15")

    # Silver
    transformer = SilverTransformer(config)
    silver_results = transformer.transform_all("2025-01-15")

    # Gold
    c360_builder = Customer360Builder(config)
    c360_result = c360_builder.build("2025-01-15")

    revenue_builder = DailyRevenueBuilder(config)
    revenue_result = revenue_builder.build()

    return {
        "bronze": bronze_results,
        "silver": silver_results,
        "gold_c360": c360_result,
        "gold_revenue": revenue_result,
    }


class TestBronzeLayer:
    def test_all_sources_ingested(self, run_pipeline):
        bronze = run_pipeline["bronze"]
        tables = [r["table"] for r in bronze]
        assert "customers" in tables
        assert "orders" in tables

    def test_records_ingested(self, run_pipeline):
        for r in run_pipeline["bronze"]:
            assert r.get("records_ingested", 0) > 0


class TestSilverLayer:
    def test_all_tables_transformed(self, run_pipeline):
        silver = run_pipeline["silver"]
        tables = [r["table"] for r in silver]
        assert "customers" in tables
        assert "orders" in tables

    def test_quarantine_captures_invalid(self, run_pipeline):
        customer_result = next(r for r in run_pipeline["silver"] if r["table"] == "customers")
        assert customer_result["quarantined"] > 0  # We added dirty data

    def test_deduplication_works(self, run_pipeline):
        customer_result = next(r for r in run_pipeline["silver"] if r["table"] == "customers")
        assert customer_result["valid_count"] < customer_result["raw_count"]


class TestGoldLayer:
    def test_customer_360_built(self, run_pipeline):
        assert run_pipeline["gold_c360"]["total_customers"] > 0

    def test_ltv_tiers_assigned(self, run_pipeline):
        ltv = run_pipeline["gold_c360"]["ltv_breakdown"]
        assert "bronze" in ltv or "silver" in ltv or "gold" in ltv

    def test_rfm_segments_assigned(self, run_pipeline):
        rfm = run_pipeline["gold_c360"]["rfm_segments"]
        assert len(rfm) > 0

    def test_daily_revenue_computed(self, run_pipeline):
        assert run_pipeline["gold_revenue"]["total_days"] > 0
        assert run_pipeline["gold_revenue"]["total_revenue"] > 0

    def test_gold_quality_gate_passes(self, config, run_pipeline):
        df = pd.read_parquet("data/gold/customer_360/customer_360.parquet")
        results = silver_to_gold_gate("customer_360", df)
        for r in results:
            assert r.status.value in ("PASS", "WARN"), \
                f"Quality gate failed: {r.check_name} — {r.details}"
