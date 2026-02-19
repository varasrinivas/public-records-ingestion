"""
End-to-end integration test: Bronze → Silver → Gold.
Runs the full pipeline with sample data in PySpark local mode.
"""
import subprocess
import pytest
from pathlib import Path


@pytest.fixture(scope="module", autouse=True)
def generate_sample_data():
    """Generate sample data before running tests."""
    subprocess.run(
        ["python", "sample_data/generate_state_suits.py"],
        check=True
    )


@pytest.fixture(scope="module")
def spark():
    """Create a test SparkSession."""
    from pyspark.sql import SparkSession
    spark = SparkSession.builder \
        .master("local[2]") \
        .appName("test-suits-pipeline") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    yield spark
    spark.stop()


@pytest.fixture(scope="module")
def run_full_pipeline(spark):
    """Run the complete pipeline."""
    from src.utils.config import load_config
    from src.bronze.ingest import BronzeIngester
    from src.silver.canonicalize import SilverCanonicalizer
    from src.gold.build_best_view import BestViewBuilder

    config = load_config()

    # Bronze
    ingester = BronzeIngester(spark, config)
    bronze = ingester.ingest_all("2025-01-15")

    # Silver
    canon = SilverCanonicalizer(spark, config)
    silver = canon.run("2025-01-15")

    # Gold
    builder = BestViewBuilder(spark, config)
    gold = builder.build_all()

    return {"bronze": bronze, "silver": silver, "gold": gold}


class TestBronzeLayer:
    def test_all_states_ingested(self, run_full_pipeline):
        states = [r["state"] for r in run_full_pipeline["bronze"] if "state" in r]
        assert "TX" in states
        assert "CA" in states
        assert "NY" in states
        assert "FL" in states
        assert "IL" in states
        assert "OH" in states

    def test_records_ingested(self, run_full_pipeline):
        for r in run_full_pipeline["bronze"]:
            if r.get("status") != "FAILED":
                assert r.get("records_ingested", 0) > 0


class TestSilverLayer:
    def test_canonical_suits_created(self, run_full_pipeline):
        assert run_full_pipeline["silver"]["total_canonical_suits"] > 0

    def test_all_states_represented(self, run_full_pipeline):
        stats = run_full_pipeline["silver"]["state_stats"]
        assert len(stats) == 6

    def test_quarantine_captures_invalid(self, run_full_pipeline):
        # TX has dirty records
        tx_stats = run_full_pipeline["silver"]["state_stats"].get("TX", {})
        assert tx_stats.get("quarantined", 0) > 0

    def test_canonical_schema(self, spark, run_full_pipeline):
        df = spark.read.parquet("data/silver/suits/suits")
        expected_cols = ["suit_id", "state_code", "county", "case_number",
                         "case_type", "filing_date", "case_status"]
        for col in expected_cols:
            assert col in df.columns, f"Missing canonical column: {col}"


class TestGoldLayer:
    def test_suit_best_view_built(self, run_full_pipeline):
        assert run_full_pipeline["gold"]["suit_best_view"]["records"] > 0

    def test_party_best_view_built(self, run_full_pipeline):
        assert run_full_pipeline["gold"]["party_best_view"]["records"] > 0

    def test_analytics_built(self, run_full_pipeline):
        assert run_full_pipeline["gold"]["analytics"]["suit_state_summary"] > 0

    def test_best_view_enrichments(self, spark, run_full_pipeline):
        df = spark.read.parquet("data/gold/suits/suit_best_view")
        assert "days_open" in df.columns
        assert "year_filed" in df.columns
        assert "primary_plaintiff" in df.columns
        assert "primary_defendant" in df.columns

    def test_case_types_are_canonical(self, spark, run_full_pipeline):
        from src.schemas.state_mappings import VALID_CASE_TYPES
        df = spark.read.parquet("data/gold/suits/suit_best_view")
        types = [row.case_type for row in df.select("case_type").distinct().collect()]
        for t in types:
            assert t in VALID_CASE_TYPES, f"Non-canonical case type in Gold: {t}"
