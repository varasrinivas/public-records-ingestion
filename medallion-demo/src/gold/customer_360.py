"""
Gold Layer — Customer 360 Aggregate
Implements: REQ-GLD-001, REQ-GLD-002

Produces a comprehensive customer view with LTV tiers, RFM segments,
and behavioral metrics. Driven by OpenSpec spec gold-aggregation.
"""
import duckdb
import pandas as pd
from datetime import date
from pathlib import Path

from src.utils.config import load_config, get_layer_path
from src.utils.logger import get_logger

logger = get_logger("gold.customer_360")


def compute_rfm_scores(df: pd.DataFrame, reference_date: str | None = None) -> pd.DataFrame:
    """
    Compute RFM (Recency, Frequency, Monetary) scores.

    Each metric is scored 1-5 using quintiles.
    """
    ref_date = pd.to_datetime(reference_date or date.today().isoformat())

    # Recency: days since last order (lower = better = higher score)
    df["recency_days"] = (ref_date - pd.to_datetime(df["last_order_date"])).dt.days
    df["recency_days"] = df["recency_days"].fillna(9999)

    # Score using quintiles (5 = best)
    df["r_score"] = pd.qcut(
        df["recency_days"].rank(method="first"),
        q=5, labels=[5, 4, 3, 2, 1]
    ).astype(int)

    df["f_score"] = pd.qcut(
        df["total_orders"].rank(method="first"),
        q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    df["m_score"] = pd.qcut(
        df["total_revenue"].rank(method="first"),
        q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    df["rfm_score"] = df["r_score"] * 100 + df["f_score"] * 10 + df["m_score"]

    return df


def assign_rfm_segment(row: pd.Series) -> str:
    """Map RFM scores to named customer segments."""
    r, f, m = row["r_score"], row["f_score"], row["m_score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 4 and f >= 3:
        return "Loyal"
    elif r >= 4 and f <= 2:
        return "New Customers"
    elif r >= 3 and f >= 2 and m >= 2:
        return "Potential Loyalists"
    elif r <= 2 and f >= 3:
        return "At Risk"
    elif r <= 2 and f <= 2 and m <= 2:
        return "Lost"
    elif r == 3 and f <= 2:
        return "About to Sleep"
    elif r <= 2 and f >= 2 and m >= 3:
        return "Cant Lose Them"
    else:
        return "Other"


def assign_ltv_tier(revenue: float, tiers: dict) -> str:
    """Classify customer by lifetime value tier."""
    if revenue >= tiers["platinum"]:
        return "platinum"
    elif revenue >= tiers["gold"]:
        return "gold"
    elif revenue >= tiers["silver"]:
        return "silver"
    else:
        return "bronze"


class Customer360Builder:
    """Build the Gold Customer 360 aggregate table."""

    def __init__(self, config: dict):
        self.config = config
        self.silver_path = get_layer_path(config, "silver")
        self.gold_path = get_layer_path(config, "gold")
        self.conn = duckdb.connect()

    def build(self, reference_date: str | None = None) -> dict:
        """Build the Customer 360 Gold table."""
        ref_date = reference_date or date.today().isoformat()
        logger.info("gold_customer360_start", reference_date=ref_date)

        # Load Silver data
        customers_path = str(self.silver_path / "customers" / "customers.parquet")
        orders_path = str(self.silver_path / "orders" / "orders.parquet")

        # Aggregate order metrics per customer
        order_metrics = self.conn.execute(f"""
            SELECT
                customer_id,
                COUNT(DISTINCT order_id) AS total_orders,
                SUM(CAST(total_amount AS DOUBLE)) AS total_revenue,
                AVG(CAST(total_amount AS DOUBLE)) AS avg_order_value,
                MIN(order_date) AS first_order_date,
                MAX(order_date) AS last_order_date,
                COUNT(DISTINCT CASE WHEN status = 'completed' THEN order_id END) AS completed_orders,
                COUNT(DISTINCT CASE WHEN status = 'cancelled' THEN order_id END) AS cancelled_orders
            FROM read_parquet('{orders_path}')
            WHERE status != 'refunded'
            GROUP BY customer_id
        """).fetchdf()

        # Load customer profiles
        customers = self.conn.execute(f"""
            SELECT
                customer_id, email, first_name, last_name,
                city, state, signup_date, is_active
            FROM read_parquet('{customers_path}')
        """).fetchdf()

        # Join customers with order metrics
        df = customers.merge(order_metrics, on="customer_id", how="left")

        # Fill nulls for customers with no orders
        df["total_orders"] = df["total_orders"].fillna(0).astype(int)
        df["total_revenue"] = df["total_revenue"].fillna(0.0)
        df["avg_order_value"] = df["avg_order_value"].fillna(0.0).round(2)
        df["completed_orders"] = df["completed_orders"].fillna(0).astype(int)
        df["cancelled_orders"] = df["cancelled_orders"].fillna(0).astype(int)

        # Compute days since last order
        ref = pd.to_datetime(ref_date)
        df["days_since_last_order"] = (
            ref - pd.to_datetime(df["last_order_date"])
        ).dt.days.fillna(-1).astype(int)

        # Order frequency (avg days between orders)
        df["days_as_customer"] = (
            ref - pd.to_datetime(df["signup_date"])
        ).dt.days.clip(lower=1)
        df["order_frequency_days"] = (
            df["days_as_customer"] / df["total_orders"].clip(lower=1)
        ).round(1)

        # LTV Tier
        ltv_config = self.config["gold"]["customer_360"]["ltv_tiers"]
        df["ltv_tier"] = df["total_revenue"].apply(
            lambda x: assign_ltv_tier(x, ltv_config)
        )

        # RFM Scoring (only for customers with orders)
        has_orders = df["total_orders"] > 0
        if has_orders.sum() >= 5:  # Need enough data for quintiles
            df.loc[has_orders] = compute_rfm_scores(
                df.loc[has_orders].copy(), ref_date
            )
            df.loc[has_orders, "rfm_segment"] = df.loc[has_orders].apply(
                assign_rfm_segment, axis=1
            )
        df["rfm_segment"] = df.get("rfm_segment", pd.Series(dtype=str)).fillna("No Orders")
        df["rfm_score"] = df.get("rfm_score", pd.Series(dtype=float)).fillna(0).astype(int)

        # Gold metadata
        df["_gold_computed_at"] = ref_date
        df["_gold_version"] = "1.0.0"

        # Select final columns
        output_cols = [
            "customer_id", "email", "first_name", "last_name",
            "city", "state", "signup_date", "is_active",
            "total_orders", "total_revenue", "avg_order_value",
            "first_order_date", "last_order_date",
            "days_since_last_order", "order_frequency_days",
            "completed_orders", "cancelled_orders",
            "ltv_tier", "rfm_score", "rfm_segment",
            "_gold_computed_at", "_gold_version",
        ]
        final_df = df[[c for c in output_cols if c in df.columns]]

        # Write Gold output
        output_dir = self.gold_path / "customer_360"
        output_dir.mkdir(parents=True, exist_ok=True)
        final_df.to_parquet(str(output_dir / "customer_360.parquet"), index=False)

        result = {
            "table": "gold_customer_360",
            "total_customers": len(final_df),
            "customers_with_orders": int(has_orders.sum()),
            "ltv_breakdown": final_df["ltv_tier"].value_counts().to_dict(),
            "rfm_segments": final_df["rfm_segment"].value_counts().to_dict(),
        }
        logger.info("gold_customer360_complete", **result)
        return result
