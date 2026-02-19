"""
Silver Layer — Canonical Suits Transformation (PySpark)
Implements: REQ-SLV-001 through REQ-SLV-008

Transforms state-specific raw court records into a unified canonical schema.
Handles field mapping, date parsing, type harmonization, name normalization,
deduplication, and quarantine.
"""
from datetime import date
from pathlib import Path

import click
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DateType, DecimalType

from src.schemas.state_mappings import (
    STATE_FIELD_MAPPINGS, VALID_CASE_TYPES, VALID_STATUSES
)
from src.utils.config import load_config, get_layer_path
from src.utils.spark_session import get_spark
from src.utils.logger import get_logger

logger = get_logger("silver.canonicalize")


class SilverCanonicalizer:
    """Transform Bronze data into canonical Silver schema using PySpark."""

    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self.bronze_path = str(get_layer_path(config, "bronze"))
        self.silver_path = str(get_layer_path(config, "silver"))
        self.quarantine_path = str(get_layer_path(config, "quarantine"))

    def canonicalize_state(self, state_code: str, df: DataFrame) -> tuple[DataFrame, DataFrame]:
        """
        Transform a single state's Bronze data to canonical schema.

        Returns: (canonical_df, quarantine_df)
        """
        mapping = STATE_FIELD_MAPPINGS[state_code]
        field_map = mapping["field_map"]
        type_map = mapping["case_type_map"]
        status_map = mapping["status_map"]
        county = mapping.get("county", "")
        date_fmt = mapping["date_format"]

        logger.info("silver_canonicalize_start", state=state_code)

        # ── Step 1: Rename fields to canonical names (REQ-SLV-001) ──
        canonical = df
        for src_col, dst_col in field_map.items():
            if src_col in df.columns:
                canonical = canonical.withColumn(dst_col, F.col(src_col))

        # ── Step 2: Generate suit_id (REQ-SLV-001) ──
        county_col = mapping.get("county_field")
        if county_col and county_col in canonical.columns:
            canonical = canonical.withColumn("county", F.col(county_col))
        else:
            canonical = canonical.withColumn("county", F.lit(county))

        canonical = canonical.withColumn(
            "suit_id",
            F.concat_ws("_",
                F.lit(state_code),
                F.regexp_replace(F.col("county"), " ", "_"),
                F.col("case_number")
            )
        )
        canonical = canonical.withColumn("state_code", F.lit(state_code))

        # ── Step 3: Parse dates (REQ-SLV-006) ──
        canonical = canonical.withColumn(
            "filing_date",
            F.to_date(F.col("filing_date"), date_fmt)
        )
        if "disposition_date" in canonical.columns:
            canonical = canonical.withColumn(
                "disposition_date",
                F.to_date(F.col("disposition_date"), date_fmt)
            )
        else:
            canonical = canonical.withColumn("disposition_date", F.lit(None).cast(DateType()))

        # ── Step 4: Harmonize case types (REQ-SLV-003) ──
        type_map_expr = F.create_map(
            *[item for k, v in type_map.items() for item in (F.lit(k), F.lit(v))]
        )
        canonical = canonical.withColumn(
            "case_type",
            F.coalesce(type_map_expr[F.col("case_type_raw")], F.lit("OTHER"))
        )

        # ── Step 5: Harmonize statuses (REQ-SLV-004) ──
        status_map_expr = F.create_map(
            *[item for k, v in status_map.items() for item in (F.lit(k), F.lit(v))]
        )
        canonical = canonical.withColumn(
            "case_status",
            F.coalesce(status_map_expr[F.col("case_status_raw")], F.lit("UNKNOWN"))
        )

        # ── Step 6: Normalize names (REQ-SLV-005) ──
        canonical = canonical.withColumn(
            "plaintiff_name",
            F.trim(F.col("plaintiff_name"))
        ).withColumn(
            "defendant_name",
            F.trim(F.col("defendant_name"))
        )

        # ── Step 7: Parse amount ──
        if "amount_demanded" in canonical.columns:
            canonical = canonical.withColumn(
                "amount_demanded",
                F.regexp_replace(F.col("amount_demanded"), "[^0-9.]", "")
                 .cast(DecimalType(18, 2))
            )
        else:
            canonical = canonical.withColumn(
                "amount_demanded", F.lit(None).cast(DecimalType(18, 2))
            )

        # ── Step 8: Ensure all canonical columns exist ──
        for col_name in ["court_name", "judge_name", "cause_of_action",
                         "disposition", "last_activity_date"]:
            if col_name not in canonical.columns:
                canonical = canonical.withColumn(col_name, F.lit(None).cast(StringType()))

        # ── Step 9: Add Silver metadata (REQ-SLV-005 lineage) ──
        canonical = canonical \
            .withColumn("_bronze_batch_id", F.col("_batch_id")) \
            .withColumn("_silver_processed_at", F.current_timestamp()) \
            .withColumn("_silver_version", F.lit("1.0.0"))

        # ── Step 10: Select canonical columns ──
        canonical_cols = [
            "suit_id", "state_code", "county", "case_number",
            "case_type", "case_type_raw", "filing_date",
            "case_status", "case_status_raw",
            "court_name", "judge_name", "cause_of_action",
            "amount_demanded", "disposition", "disposition_date",
            "last_activity_date",
            "plaintiff_name", "defendant_name",
            "_bronze_batch_id", "_silver_processed_at", "_silver_version",
        ]
        canonical = canonical.select(
            [c for c in canonical_cols if c in canonical.columns]
        )

        # ── Step 11: Validate & quarantine (REQ-SLV-008) ──
        valid = canonical.filter(
            F.col("case_number").isNotNull() &
            (F.col("case_number") != "") &
            F.col("filing_date").isNotNull() &
            F.col("state_code").isNotNull()
        )
        quarantine = canonical.filter(
            F.col("case_number").isNull() |
            (F.col("case_number") == "") |
            F.col("filing_date").isNull()
        ).withColumn("_quarantine_reason", F.lit("INVALID_REQUIRED_FIELDS"))

        return valid, quarantine

    def run(self, ingestion_date: str | None = None) -> dict:
        """Run Silver transformation for all states."""
        ing_date = ingestion_date or date.today().isoformat()

        all_valid = []
        all_quarantine = []
        state_stats = {}

        for state_code in self.config.get("states", {}).keys():
            # Read Bronze data for this state
            bronze_state_path = f"{self.bronze_path}/state={state_code}"
            if not Path(bronze_state_path).exists():
                logger.warn("bronze_missing", state=state_code)
                continue

            df = self.spark.read.parquet(bronze_state_path)
            valid, quarantine = self.canonicalize_state(state_code, df)

            valid_count = valid.count()
            quarantine_count = quarantine.count()

            all_valid.append(valid)
            if quarantine_count > 0:
                all_quarantine.append(quarantine)

            state_stats[state_code] = {
                "valid": valid_count,
                "quarantined": quarantine_count,
            }
            logger.info("silver_state_done", state=state_code,
                        valid=valid_count, quarantined=quarantine_count)

        # Union all states
        if all_valid:
            combined = all_valid[0]
            for df in all_valid[1:]:
                combined = combined.unionByName(df, allowMissingColumns=True)

            # Deduplicate (REQ-SLV-007)
            from pyspark.sql.window import Window
            window = Window.partitionBy("suit_id").orderBy(
                F.col("_silver_processed_at").desc()
            )
            combined = combined.withColumn("_rn", F.row_number().over(window))
            deduped = combined.filter(F.col("_rn") == 1).drop("_rn")

            # Write Silver
            suits_path = f"{self.silver_path}/suits"
            deduped.write.mode("overwrite") \
                .partitionBy("state_code") \
                .parquet(suits_path)

            # Write party records (extract from plaintiff/defendant)
            self._build_party_records(deduped, ing_date)

            total_deduped = deduped.count()
        else:
            total_deduped = 0

        # Write quarantine
        if all_quarantine:
            q_combined = all_quarantine[0]
            for df in all_quarantine[1:]:
                q_combined = q_combined.unionByName(df, allowMissingColumns=True)
            q_path = f"{self.quarantine_path}/silver/suits/date={ing_date}"
            q_combined.write.mode("overwrite").parquet(q_path)

        result = {
            "total_canonical_suits": total_deduped,
            "state_stats": state_stats,
            "ingestion_date": ing_date,
        }
        logger.info("silver_run_complete", **result)
        return result

    def _build_party_records(self, suits_df: DataFrame, ing_date: str):
        """
        Extract party records from suit data (REQ-SLV-002).
        Creates separate plaintiff and defendant rows.
        """
        # Plaintiffs
        plaintiffs = suits_df.select(
            F.col("suit_id"),
            F.concat_ws("_", F.col("suit_id"), F.lit("PLAINTIFF"), F.lit("1")).alias("party_id"),
            F.lit("PLAINTIFF").alias("party_type"),
            F.col("plaintiff_name").alias("party_name"),
            F.col("plaintiff_name").alias("party_name_raw"),
        ).filter(F.col("party_name").isNotNull() & (F.col("party_name") != ""))

        # Defendants
        defendants = suits_df.select(
            F.col("suit_id"),
            F.concat_ws("_", F.col("suit_id"), F.lit("DEFENDANT"), F.lit("1")).alias("party_id"),
            F.lit("DEFENDANT").alias("party_type"),
            F.col("defendant_name").alias("party_name"),
            F.col("defendant_name").alias("party_name_raw"),
        ).filter(F.col("party_name").isNotNull() & (F.col("party_name") != ""))

        parties = plaintiffs.unionByName(defendants)

        # Detect entity vs individual (REQ-SLV-005)
        entity_patterns = ["LLC", "Inc", "Corp", "Ltd", "Bank", "Insurance",
                           "N.A.", "Company", "Co.", "Services", "Funding",
                           "Associates", "Partners", "Group"]
        entity_regex = "|".join(entity_patterns)
        parties = parties.withColumn(
            "is_entity",
            F.col("party_name").rlike(f"(?i)({entity_regex})")
        )

        parties = parties \
            .withColumn("attorney_name", F.lit(None).cast(StringType())) \
            .withColumn("attorney_firm", F.lit(None).cast(StringType()))

        party_path = f"{self.silver_path}/parties"
        parties.write.mode("overwrite").partitionBy("party_type").parquet(party_path)


@click.command()
@click.option("--date", "ingestion_date", default=None)
def main(ingestion_date: str | None):
    config = load_config()
    spark = get_spark("silver-canonicalize")
    canon = SilverCanonicalizer(spark, config)
    result = canon.run(ingestion_date)
    click.echo(f"Canonicalized {result['total_canonical_suits']} suits")
    spark.stop()

if __name__ == "__main__":
    main()
