"""
Silver Layer — Cleansing, Conforming, and Deduplication
Implements: REQ-SLV-001 through REQ-SLV-005

Transforms raw Bronze data into validated, deduplicated, and type-cast
datasets. Invalid records are quarantined with failure reasons.
"""
import duckdb
from datetime import date
from pathlib import Path

from src.utils.config import load_config, get_layer_path
from src.utils.logger import get_logger

logger = get_logger("silver.transform")


class SilverTransformer:
    """Transform Bronze data into cleansed Silver datasets."""

    def __init__(self, config: dict):
        self.config = config
        self.bronze_path = get_layer_path(config, "bronze")
        self.silver_path = get_layer_path(config, "silver")
        self.quarantine_path = get_layer_path(config, "quarantine")
        self.conn = duckdb.connect()

    def transform_customers(self, ingestion_date: str | None = None) -> dict:
        """
        Transform customers: validate, deduplicate, standardize.

        REQ-SLV-001: Deduplication by customer_id
        REQ-SLV-002: Schema validation (email, required fields)
        REQ-SLV-003: Type casting & standardization
        """
        ing_date = ingestion_date or date.today().isoformat()
        bronze_glob = str(self.bronze_path / "customers" / "**" / "*.parquet")

        logger.info("silver_transform_start", table="customers", date=ing_date)

        # Load Bronze data
        raw = self.conn.execute(f"""
            SELECT * FROM read_parquet('{bronze_glob}', union_by_name=true)
        """).fetchdf()

        total_raw = len(raw)

        # ── Validate ──
        valid_mask = (
            raw["customer_id"].notna() &
            (raw["customer_id"] != "") &
            raw["email"].str.contains("@", na=False) &
            raw["first_name"].notna() &
            (raw["first_name"] != "")
        )

        valid_df = raw[valid_mask].copy()
        quarantine_df = raw[~valid_mask].copy()

        # ── Quarantine invalid records (REQ-SLV-002) ──
        if len(quarantine_df) > 0:
            quarantine_df["_quarantine_reason"] = "VALIDATION_FAILED"
            quarantine_df["_quarantine_date"] = ing_date
            q_path = self.quarantine_path / "silver" / "customers"
            q_path.mkdir(parents=True, exist_ok=True)
            quarantine_df.to_parquet(str(q_path / f"{ing_date}.parquet"), index=False)
            logger.warn("silver_quarantine", table="customers",
                        quarantined=len(quarantine_df))

        # ── Deduplicate (REQ-SLV-001): latest ingestion wins ──
        valid_df = valid_df.sort_values("_ingestion_timestamp", ascending=False)
        valid_df = valid_df.drop_duplicates(subset=["customer_id"], keep="first")

        # ── Standardize (REQ-SLV-003) ──
        valid_df["email"] = valid_df["email"].str.lower().str.strip()
        valid_df["first_name"] = valid_df["first_name"].str.strip()
        valid_df["last_name"] = valid_df["last_name"].str.strip()
        valid_df["is_active"] = valid_df["is_active"].map(
            {"true": True, "false": False}
        ).fillna(False)

        # ── Add Silver metadata (REQ-SLV-005) ──
        valid_df["_silver_processed_at"] = date.today().isoformat()
        valid_df["_silver_version"] = "1.0.0"

        # ── Write Silver output ──
        output = self.silver_path / "customers"
        output.mkdir(parents=True, exist_ok=True)
        valid_df.to_parquet(str(output / "customers.parquet"), index=False)

        result = {
            "table": "customers",
            "raw_count": total_raw,
            "valid_count": len(valid_df),
            "quarantined": len(quarantine_df),
            "deduped_removed": total_raw - len(quarantine_df) - len(valid_df),
        }
        logger.info("silver_transform_complete", **result)
        return result

    def transform_orders(self, ingestion_date: str | None = None) -> dict:
        """Transform orders: validate, deduplicate, type-cast."""
        ing_date = ingestion_date or date.today().isoformat()
        bronze_glob = str(self.bronze_path / "orders" / "**" / "*.parquet")

        raw = self.conn.execute(f"""
            SELECT * FROM read_parquet('{bronze_glob}', union_by_name=true)
        """).fetchdf()

        total_raw = len(raw)

        # Validate
        valid_mask = (
            raw["order_id"].notna() &
            (raw["order_id"] != "") &
            raw["customer_id"].notna() &
            (raw["customer_id"] != "") &
            raw["order_date"].notna()
        )

        valid_df = raw[valid_mask].copy()
        quarantine_df = raw[~valid_mask].copy()

        if len(quarantine_df) > 0:
            quarantine_df["_quarantine_reason"] = "VALIDATION_FAILED"
            q_path = self.quarantine_path / "silver" / "orders"
            q_path.mkdir(parents=True, exist_ok=True)
            quarantine_df.to_parquet(str(q_path / f"{ing_date}.parquet"), index=False)

        # Deduplicate
        valid_df = valid_df.sort_values("_ingestion_timestamp", ascending=False)
        valid_df = valid_df.drop_duplicates(subset=["order_id"], keep="first")

        # Type cast
        valid_df["total_amount"] = valid_df["total_amount"].astype(float)
        valid_df["_silver_processed_at"] = date.today().isoformat()
        valid_df["_silver_version"] = "1.0.0"

        output = self.silver_path / "orders"
        output.mkdir(parents=True, exist_ok=True)
        valid_df.to_parquet(str(output / "orders.parquet"), index=False)

        return {
            "table": "orders",
            "raw_count": total_raw,
            "valid_count": len(valid_df),
            "quarantined": len(quarantine_df),
        }

    def transform_all(self, ingestion_date: str | None = None) -> list[dict]:
        """Transform all Silver tables."""
        return [
            self.transform_customers(ingestion_date),
            self.transform_orders(ingestion_date),
        ]
