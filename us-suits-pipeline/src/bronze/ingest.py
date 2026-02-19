"""
Bronze Layer — Raw State Court Data Ingestion (PySpark)
Implements: REQ-BRZ-001 through REQ-BRZ-006

Ingests raw court suits data from multiple US states.
Each state's format is preserved as-is with lineage metadata.
"""
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import click
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from src.utils.config import load_config, get_state_config, get_layer_path
from src.utils.spark_session import get_spark
from src.utils.logger import get_logger

logger = get_logger("bronze.ingest")


class BronzeIngester:
    """Ingest raw state court data into Bronze layer using PySpark."""

    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self.bronze_path = str(get_layer_path(config, "bronze"))

    def _generate_batch_id(self, state: str, ing_date: str) -> str:
        """Deterministic batch ID for idempotent ingestion (REQ-BRZ-005)."""
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"suits/{state}/{ing_date}"))

    def ingest_state(self, state_code: str, ingestion_date: str | None = None) -> dict:
        """
        Ingest raw data for a single state.

        REQ-BRZ-001: Multi-format ingestion
        REQ-BRZ-002: Preserve state-specific schema
        REQ-BRZ-003: Metadata enrichment
        REQ-BRZ-004: Partitioning by state/date
        REQ-BRZ-005: Idempotent overwrite
        """
        ing_date = ingestion_date or date.today().isoformat()
        state_cfg = get_state_config(self.config, state_code)
        batch_id = self._generate_batch_id(state_code, ing_date)
        source_path = state_cfg["source_path"]

        logger.info("bronze_ingest_start",
                     state=state_code, source=source_path,
                     date=ing_date, batch_id=batch_id)

        # Read based on format (REQ-BRZ-001)
        fmt = state_cfg["format"]
        if fmt == "csv":
            df = self.spark.read.csv(
                source_path,
                header=True,
                sep=state_cfg.get("delimiter", ","),
                encoding=state_cfg.get("encoding", "utf-8"),
                inferSchema=False,  # Schema-on-read: keep everything as string
            )
        elif fmt == "json":
            df = self.spark.read.json(source_path)
            # Flatten nested JSON — cast all to string for Bronze
            for col_name in df.columns:
                if df.schema[col_name].dataType != StringType():
                    df = df.withColumn(col_name, F.to_json(F.col(col_name)))
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        # Add row numbers for traceability (REQ-BRZ-003)
        df = df.withColumn("_row_number", F.monotonically_increasing_id())

        # Add metadata columns (REQ-BRZ-003)
        df = df \
            .withColumn("_ingestion_timestamp",
                        F.lit(datetime.now(timezone.utc).isoformat())) \
            .withColumn("_source_state", F.lit(state_code)) \
            .withColumn("_source_county", F.lit(state_cfg.get("county", ""))) \
            .withColumn("_source_format", F.lit(fmt)) \
            .withColumn("_batch_id", F.lit(batch_id)) \
            .withColumn("_file_path", F.lit(source_path))

        # Write partitioned Parquet (REQ-BRZ-004, REQ-BRZ-005: overwrite)
        output_path = f"{self.bronze_path}/state={state_code}/ingestion_date={ing_date}"
        df.write.mode("overwrite").parquet(output_path)

        count = df.count()
        result = {
            "state": state_code,
            "batch_id": batch_id,
            "records_ingested": count,
            "output_path": output_path,
            "ingestion_date": ing_date,
        }
        logger.info("bronze_ingest_complete", **result)
        return result

    def ingest_all(self, ingestion_date: str | None = None) -> list[dict]:
        """Ingest all configured states."""
        results = []
        for state_code in self.config.get("states", {}).keys():
            try:
                result = self.ingest_state(state_code, ingestion_date)
                results.append(result)
            except Exception as e:
                logger.error("bronze_ingest_error", state=state_code, error=str(e))
                results.append({"state": state_code, "status": "FAILED", "error": str(e)})
        return results


@click.command()
@click.option("--state", default=None, help="Specific state code (TX, CA, NY, FL, IL, OH)")
@click.option("--date", "ingestion_date", default=None, help="Ingestion date (YYYY-MM-DD)")
def main(state: str | None, ingestion_date: str | None):
    """Ingest state court data into Bronze layer."""
    config = load_config()
    spark = get_spark("bronze-ingest")
    ingester = BronzeIngester(spark, config)

    if state:
        result = ingester.ingest_state(state, ingestion_date)
        click.echo(f"Ingested {result['records_ingested']} records for {state}")
    else:
        results = ingester.ingest_all(ingestion_date)
        for r in results:
            s = r.get("status", "OK")
            c = r.get("records_ingested", 0)
            click.echo(f"  {r['state']}: {c} records ({s})")

    spark.stop()


if __name__ == "__main__":
    main()
