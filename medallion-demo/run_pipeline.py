#!/usr/bin/env python3
"""
Run the full Medallion Pipeline end-to-end.

Usage:
    python run_pipeline.py
    python run_pipeline.py --date 2025-01-15
    python run_pipeline.py --layer bronze
    python run_pipeline.py --layer gold --date 2025-06-01
"""
import sys
import time
import subprocess
from datetime import date
from pathlib import Path

import click

from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger("pipeline.runner")

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          MEDALLION ARCHITECTURE PIPELINE                     ║
║          Spec-Driven AI Development Demo                     ║
║                                                              ║
║    🥉 Bronze → 🥈 Silver → 🥇 Gold                         ║
╚══════════════════════════════════════════════════════════════╝
"""


def step(name: str):
    """Print a pipeline step banner."""
    print(f"\n{'─' * 60}")
    print(f"  ▶ {name}")
    print(f"{'─' * 60}")


@click.command()
@click.option("--date", "run_date", default=None,
              help="Pipeline run date (YYYY-MM-DD). Defaults to today.")
@click.option("--layer", default=None,
              type=click.Choice(["bronze", "silver", "gold", "all"]),
              help="Run a specific layer only. Default: all")
@click.option("--skip-data-gen", is_flag=True,
              help="Skip sample data generation")
@click.option("--quality/--no-quality", default=True,
              help="Run data quality checks between layers")
def main(run_date: str | None, layer: str | None, skip_data_gen: bool, quality: bool):
    """Run the Medallion Architecture Pipeline."""
    print(BANNER)

    run_date = run_date or date.today().isoformat()
    layer = layer or "all"
    run_layers = ["bronze", "silver", "gold"] if layer == "all" else [layer]

    config = load_config()
    start_time = time.time()

    print(f"  Run date:   {run_date}")
    print(f"  Layers:     {', '.join(run_layers)}")
    print(f"  Quality:    {'enabled' if quality else 'disabled'}")

    # ── Step 0: Generate sample data ──
    if not skip_data_gen and "bronze" in run_layers:
        step("0. Generating sample data")
        subprocess.run([sys.executable, "sample_data/generate_sample_data.py"], check=True)
        print("  ✓ Sample data generated")

    # ── Step 1: Bronze Ingestion ──
    if "bronze" in run_layers:
        step("1. 🥉 BRONZE — Raw Ingestion")
        from src.bronze.ingest import BronzeIngester
        ingester = BronzeIngester(config)
        bronze_results = ingester.ingest_all(run_date)
        for r in bronze_results:
            status = "✓" if r.get("status") != "FAILED" else "✗"
            count = r.get("records_ingested", 0)
            print(f"  {status} {r['table']}: {count} records")

        if quality:
            step("1b. 🔍 Bronze Quality Gate")
            _run_quality_gate("bronze", config)

    # ── Step 2: Silver Transformation ──
    if "silver" in run_layers:
        step("2. 🥈 SILVER — Cleanse & Conform")
        from src.silver.transform import SilverTransformer
        transformer = SilverTransformer(config)
        silver_results = transformer.transform_all(run_date)
        for r in silver_results:
            print(f"  ✓ {r['table']}: {r['valid_count']} valid, "
                  f"{r['quarantined']} quarantined")

    # ── Step 3: Gold Aggregation ──
    if "gold" in run_layers:
        step("3. 🥇 GOLD — Business Aggregates")

        from src.gold.customer_360 import Customer360Builder
        c360 = Customer360Builder(config)
        c360_result = c360.build(run_date)
        print(f"  ✓ Customer 360: {c360_result['total_customers']} customers")
        print(f"    LTV breakdown: {c360_result['ltv_breakdown']}")

        from src.gold.daily_revenue import DailyRevenueBuilder
        rev = DailyRevenueBuilder(config)
        rev_result = rev.build()
        print(f"  ✓ Daily Revenue: {rev_result['total_days']} days, "
              f"${rev_result['total_revenue']:,.2f} total")

        if quality:
            step("3b. 🔍 Gold Quality Gate")
            _run_quality_gate("gold", config)

    # ── Summary ──
    elapsed = time.time() - start_time
    print(f"\n{'═' * 60}")
    print(f"  ✅ Pipeline complete in {elapsed:.1f}s")
    print(f"{'═' * 60}\n")

    # Show output file tree
    data_path = Path("data")
    if data_path.exists():
        print("  Output files:")
        for layer_dir in sorted(data_path.iterdir()):
            if layer_dir.is_dir():
                files = list(layer_dir.rglob("*.parquet"))
                print(f"    {layer_dir.name}/ ({len(files)} parquet files)")


def _run_quality_gate(layer: str, config: dict):
    """Run quality checks for a layer."""
    import pandas as pd
    from src.quality.gates import bronze_to_silver_gate, silver_to_gold_gate
    from src.quality.checks import CheckStatus
    from src.utils.config import get_layer_path

    if layer == "bronze":
        bronze_path = get_layer_path(config, "bronze")
        for table in ["customers", "orders"]:
            parquet_glob = str(bronze_path / table / "**" / "*.parquet")
            try:
                df = pd.read_parquet(parquet_glob)
                results = bronze_to_silver_gate(table, df)
                for r in results:
                    icon = "✓" if r.status == CheckStatus.PASS else \
                           "⚠" if r.status == CheckStatus.WARN else "✗"
                    print(f"  {icon} {r.check_name}: {r.pass_rate:.1f}% [{r.status.value}]")
            except Exception as e:
                print(f"  ⚠ Could not check {table}: {e}")

    elif layer == "gold":
        gold_path = get_layer_path(config, "gold")
        c360_file = gold_path / "customer_360" / "customer_360.parquet"
        if c360_file.exists():
            df = pd.read_parquet(str(c360_file))
            results = silver_to_gold_gate("customer_360", df)
            for r in results:
                icon = "✓" if r.status == CheckStatus.PASS else \
                       "⚠" if r.status == CheckStatus.WARN else "✗"
                print(f"  {icon} {r.check_name}: {r.pass_rate:.1f}% [{r.status.value}]")


if __name__ == "__main__":
    main()
