#!/usr/bin/env python3
"""
Run the full US Suits Medallion Pipeline end-to-end.

Usage:
    python run_pipeline.py
    python run_pipeline.py --date 2025-01-15
    python run_pipeline.py --layer silver
"""
import sys
import time
import subprocess
from datetime import date

import click
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger("pipeline.runner")

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║       US PUBLIC RECORDS — SUITS PIPELINE                        ║
║       Spec-Driven Medallion Architecture                        ║
║                                                                  ║
║  🥉 Bronze (raw state data)                                     ║
║  🥈 Silver (canonical schema)                                   ║
║  🥇 Gold   (best view for consumers)                            ║
╚══════════════════════════════════════════════════════════════════╝
"""


def step(name: str):
    print(f"\n{'─' * 65}")
    print(f"  ▶ {name}")
    print(f"{'─' * 65}")


@click.command()
@click.option("--date", "run_date", default=None, help="Pipeline run date")
@click.option("--layer", default="all", type=click.Choice(["bronze", "silver", "gold", "all"]))
@click.option("--skip-datagen", is_flag=True, help="Skip sample data generation")
def main(run_date, layer, skip_datagen):
    print(BANNER)
    run_date = run_date or date.today().isoformat()
    layers = ["bronze", "silver", "gold"] if layer == "all" else [layer]
    config = load_config()
    t0 = time.time()

    print(f"  Date:    {run_date}")
    print(f"  Layers:  {', '.join(layers)}")
    print(f"  States:  {', '.join(config['states'].keys())}")

    if not skip_datagen and "bronze" in layers:
        step("0. Generate Sample State Court Data")
        subprocess.run([sys.executable, "sample_data/generate_state_suits.py"], check=True)

    from src.utils.spark_session import get_spark
    spark = get_spark("suits-pipeline-runner")

    try:
        if "bronze" in layers:
            step("1. 🥉 BRONZE — Ingest Raw State Data")
            from src.bronze.ingest import BronzeIngester
            ingester = BronzeIngester(spark, config)
            for r in ingester.ingest_all(run_date):
                s = "✓" if r.get("status") != "FAILED" else "✗"
                print(f"  {s} {r.get('state','?')}: {r.get('records_ingested', 0)} records")

        if "silver" in layers:
            step("2. 🥈 SILVER — Canonicalize to Unified Schema")
            from src.silver.canonicalize import SilverCanonicalizer
            canon = SilverCanonicalizer(spark, config)
            result = canon.run(run_date)
            print(f"  ✓ {result['total_canonical_suits']} canonical suit records")
            for st, stats in result['state_stats'].items():
                print(f"    {st}: {stats['valid']} valid, {stats['quarantined']} quarantined")

        if "gold" in layers:
            step("3. 🥇 GOLD — Build Consumer Best Views")
            from src.gold.build_best_view import BestViewBuilder
            builder = BestViewBuilder(spark, config)
            results = builder.build_all()
            for table, info in results.items():
                print(f"  ✓ {table}: {info}")

    finally:
        spark.stop()

    elapsed = time.time() - t0
    print(f"\n{'═' * 65}")
    print(f"  ✅ Pipeline complete in {elapsed:.1f}s")
    print(f"{'═' * 65}\n")


if __name__ == "__main__":
    main()
