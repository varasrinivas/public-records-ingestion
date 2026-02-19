"""
Bronze Layer — Raw Data Ingestion
Implements: REQ-BRZ-001 through REQ-BRZ-005

Ingests raw data from configured sources into the Bronze layer.
Append-only, schema-on-read, with full lineage metadata.
"""
import click
import duckdb
from datetime import date
from pathlib import Path

from src.utils.config import load_config, get_layer_path
from src.utils.logger import get_logger
from src.utils.metadata import generate_batch_id

logger = get_logger("bronze.ingest")


class BronzeIngester:
    """Ingest raw data into the Bronze layer of the medallion architecture."""

    def __init__(self, config: dict):
        self.config = config
        self.bronze_path = get_layer_path(config, "bronze")
        self.conn = duckdb.connect()

    def ingest_csv(
        self,
        table_name: str,
        source_path: str,
        ingestion_date: str | None = None,
    ) -> dict:
        """
        Ingest a CSV file into Bronze layer.

        REQ-BRZ-001: Source ingestion from flat files
        REQ-BRZ-002: Metadata tracking
        REQ-BRZ-003: Schema-on-read (store raw)
        REQ-BRZ-004: Idempotent (overwrite partition)
        """
        ing_date = ingestion_date or date.today().isoformat()
        batch_id = generate_batch_id(f"csv/{table_name}", ing_date)

        logger.info("bronze_ingest_start",
                     table=table_name, source=source_path,
                     date=ing_date, batch_id=batch_id)

        # Read raw CSV without type coercion (schema-on-read)
        raw_df = self.conn.execute(f"""
            SELECT
                *,
                '{batch_id}' AS _batch_id,
                'csv_local' AS _source_system,
                '{table_name}' AS _source_table,
                CURRENT_TIMESTAMP AS _ingestion_timestamp,
                '{source_path}' AS _file_path
            FROM read_csv_auto('{source_path}', all_varchar=true)
        """).fetchdf()

        # Write to Bronze partition (idempotent overwrite)
        output_dir = self.bronze_path / table_name / f"ingestion_date={ing_date}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{batch_id}.parquet"
        raw_df.to_parquet(str(output_file), index=False)

        result = {
            "table": table_name,
            "batch_id": batch_id,
            "records_ingested": len(raw_df),
            "output_path": str(output_file),
            "ingestion_date": ing_date,
        }

        logger.info("bronze_ingest_complete", **result)
        return result

    def ingest_all(self, ingestion_date: str | None = None) -> list[dict]:
        """Ingest all configured sources."""
        results = []
        for table_name, source_cfg in self.config["bronze"]["sources"].items():
            try:
                result = self.ingest_csv(
                    table_name=table_name,
                    source_path=source_cfg["path"],
                    ingestion_date=ingestion_date,
                )
                results.append(result)
            except Exception as e:
                logger.error("bronze_ingest_error",
                             table=table_name, error=str(e))
                results.append({
                    "table": table_name,
                    "status": "FAILED",
                    "error": str(e),
                })
        return results


@click.command()
@click.option("--source", default=None, help="Specific source table to ingest")
@click.option("--date", "ingestion_date", default=None, help="Ingestion date (YYYY-MM-DD)")
def main(source: str | None, ingestion_date: str | None):
    """Ingest data into the Bronze layer."""
    config = load_config()
    ingester = BronzeIngester(config)

    if source:
        src_cfg = config["bronze"]["sources"][source]
        result = ingester.ingest_csv(source, src_cfg["path"], ingestion_date)
        click.echo(f"Ingested {result['records_ingested']} records for {source}")
    else:
        results = ingester.ingest_all(ingestion_date)
        for r in results:
            status = r.get("status", "OK")
            count = r.get("records_ingested", 0)
            click.echo(f"  {r['table']}: {count} records ({status})")


if __name__ == "__main__":
    main()
