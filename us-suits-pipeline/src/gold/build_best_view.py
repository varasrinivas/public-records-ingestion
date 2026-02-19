"""
Gold Layer — Suits Best View Builder (PySpark)
Implements: REQ-GLD-001 through REQ-GLD-005

Produces consumer-ready best view tables from Silver canonical data.
Writes Parquet to GCS and loads into BigQuery.
"""
from datetime import date
from pathlib import Path

import click
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from src.utils.config import load_config, get_layer_path
from src.utils.spark_session import get_spark
from src.utils.logger import get_logger

logger = get_logger("gold.best_view")


class BestViewBuilder:
    """Build Gold best view tables from Silver canonical suits."""

    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self.silver_path = str(get_layer_path(config, "silver"))
        self.gold_path = str(get_layer_path(config, "gold"))

    def build_suit_best_view(self) -> dict:
        """
        Build suit_best_view: one row per suit with enrichments.
        Implements: REQ-GLD-001
        """
        suits_path = f"{self.silver_path}/suits"
        suits = self.spark.read.parquet(suits_path)

        parties_path = f"{self.silver_path}/parties"
        parties = self.spark.read.parquet(parties_path) if Path(parties_path).exists() else None

        # Count parties per suit
        if parties is not None:
            party_counts = parties.groupBy("suit_id").agg(
                F.count(F.when(F.col("party_type") == "PLAINTIFF", 1)).alias("plaintiff_count"),
                F.count(F.when(F.col("party_type") == "DEFENDANT", 1)).alias("defendant_count"),
            )
            suits = suits.join(party_counts, "suit_id", "left")
        else:
            suits = suits \
                .withColumn("plaintiff_count", F.lit(1)) \
                .withColumn("defendant_count", F.lit(1))

        # Enrichments (REQ-GLD-001)
        today = date.today().isoformat()
        best_view = suits \
            .withColumn("year_filed", F.year(F.col("filing_date"))) \
            .withColumn(
                "days_open",
                F.datediff(
                    F.coalesce(F.col("disposition_date"), F.lit(today).cast("date")),
                    F.col("filing_date")
                )
            ) \
            .withColumn("primary_plaintiff", F.col("plaintiff_name")) \
            .withColumn("primary_defendant", F.col("defendant_name")) \
            .withColumn("_gold_refreshed_at", F.current_timestamp())

        # Select final columns
        output_cols = [
            "suit_id", "state_code", "county", "case_number",
            "case_type", "case_type_raw", "filing_date", "year_filed",
            "case_status", "case_status_raw",
            "court_name", "judge_name", "cause_of_action",
            "amount_demanded", "disposition", "disposition_date",
            "days_open", "primary_plaintiff", "primary_defendant",
            "plaintiff_count", "defendant_count",
            "_gold_refreshed_at",
        ]
        best_view = best_view.select(
            [c for c in output_cols if c in best_view.columns]
        )

        # Write partitioned by state, clustered by case_type/year
        output = f"{self.gold_path}/suit_best_view"
        best_view.write.mode("overwrite") \
            .partitionBy("state_code") \
            .parquet(output)

        count = best_view.count()
        logger.info("gold_suit_best_view_complete", count=count)
        return {"table": "suit_best_view", "records": count}

    def build_party_best_view(self) -> dict:
        """
        Build suit_party_best_view with cross-suit metrics.
        Implements: REQ-GLD-002
        """
        parties_path = f"{self.silver_path}/parties"
        if not Path(parties_path).exists():
            return {"table": "suit_party_best_view", "records": 0}

        parties = self.spark.read.parquet(parties_path)
        suits_path = f"{self.silver_path}/suits"
        suits = self.spark.read.parquet(suits_path).select("suit_id", "filing_date")

        # Join parties with suit filing dates
        enriched = parties.join(suits, "suit_id", "left")

        # Cross-suit metrics per party_name
        party_stats = enriched.groupBy("party_name").agg(
            F.count(F.when(F.col("party_type") == "PLAINTIFF", 1))
                .alias("total_suits_as_plaintiff"),
            F.count(F.when(F.col("party_type") == "DEFENDANT", 1))
                .alias("total_suits_as_defendant"),
            F.min("filing_date").alias("first_appearance_date"),
            F.max("filing_date").alias("last_appearance_date"),
            F.count("suit_id").alias("total_appearances"),
        )
        party_stats = party_stats.withColumn(
            "is_frequent_litigant",
            F.col("total_appearances") >= 10
        )

        # Join stats back to individual party records
        best_view = enriched.join(party_stats, "party_name", "left") \
            .withColumn("_gold_refreshed_at", F.current_timestamp())

        output = f"{self.gold_path}/suit_party_best_view"
        best_view.write.mode("overwrite").partitionBy("party_type").parquet(output)

        count = best_view.count()
        logger.info("gold_party_best_view_complete", count=count)
        return {"table": "suit_party_best_view", "records": count}

    def build_analytics(self) -> dict:
        """
        Build pre-computed analytics aggregates.
        Implements: REQ-GLD-003
        """
        suits_path = f"{self.gold_path}/suit_best_view"
        suits = self.spark.read.parquet(suits_path)

        # ── State Summary ──
        state_summary = suits.groupBy("state_code", "year_filed", "case_type").agg(
            F.count("suit_id").alias("suit_count"),
            F.avg(F.when(F.col("disposition_date").isNotNull(), F.col("days_open")))
                .alias("avg_days_to_disposition"),
            F.count(F.when(F.col("disposition_date").isNotNull(), 1))
                .cast("double")
                .alias("disposed_count"),
        )
        state_summary = state_summary.withColumn(
            "disposition_rate",
            F.round(F.col("disposed_count") / F.col("suit_count") * 100, 2)
        ).drop("disposed_count")

        state_summary = state_summary.withColumn(
            "_gold_refreshed_at", F.current_timestamp()
        )

        state_output = f"{self.gold_path}/suit_state_summary"
        state_summary.write.mode("overwrite").partitionBy("state_code").parquet(state_output)

        # ── Monthly Trends ──
        monthly = suits.withColumn(
            "year_month", F.date_format(F.col("filing_date"), "yyyy-MM")
        ).groupBy("year_month", "state_code", "case_type").agg(
            F.count("suit_id").alias("new_filings"),
            F.count(F.when(F.col("disposition_date").isNotNull(), 1)).alias("dispositions"),
        )

        # Rolling 3-month average
        window_3m = Window.partitionBy("state_code", "case_type") \
            .orderBy("year_month").rowsBetween(-2, 0)
        monthly = monthly.withColumn(
            "filing_trend_3m_avg",
            F.round(F.avg("new_filings").over(window_3m), 1)
        )
        monthly = monthly.withColumn("_gold_refreshed_at", F.current_timestamp())

        monthly_output = f"{self.gold_path}/suit_monthly_trends"
        monthly.write.mode("overwrite").partitionBy("state_code").parquet(monthly_output)

        summary_count = state_summary.count()
        monthly_count = monthly.count()

        logger.info("gold_analytics_complete",
                     state_summary=summary_count, monthly=monthly_count)
        return {
            "suit_state_summary": summary_count,
            "suit_monthly_trends": monthly_count,
        }

    def build_all(self) -> dict:
        """Build all Gold tables."""
        results = {}
        results["suit_best_view"] = self.build_suit_best_view()
        results["party_best_view"] = self.build_party_best_view()
        results["analytics"] = self.build_analytics()
        return results


@click.command()
@click.option("--date", "run_date", default=None)
def main(run_date: str | None):
    config = load_config()
    spark = get_spark("gold-best-view")
    builder = BestViewBuilder(spark, config)
    results = builder.build_all()
    for table, info in results.items():
        click.echo(f"  {table}: {info}")
    spark.stop()

if __name__ == "__main__":
    main()
