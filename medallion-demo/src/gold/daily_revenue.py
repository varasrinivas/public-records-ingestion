"""
Gold Layer — Daily Revenue Aggregate
Implements: REQ-GLD-003

Produces daily revenue metrics with rolling averages and YoY comparison.
"""
import duckdb
import pandas as pd
from pathlib import Path

from src.utils.config import get_layer_path
from src.utils.logger import get_logger

logger = get_logger("gold.daily_revenue")


class DailyRevenueBuilder:
    """Build the Gold Daily Revenue aggregate table."""

    def __init__(self, config: dict):
        self.config = config
        self.silver_path = get_layer_path(config, "silver")
        self.gold_path = get_layer_path(config, "gold")
        self.conn = duckdb.connect()

    def build(self) -> dict:
        """Build daily revenue aggregate with rolling averages."""
        orders_path = str(self.silver_path / "orders" / "orders.parquet")

        result_df = self.conn.execute(f"""
            WITH daily AS (
                SELECT
                    CAST(order_date AS DATE) AS order_date,
                    COUNT(DISTINCT order_id) AS order_count,
                    COUNT(DISTINCT customer_id) AS unique_customers,
                    SUM(CAST(total_amount AS DOUBLE)) AS total_revenue,
                    AVG(CAST(total_amount AS DOUBLE)) AS avg_order_value
                FROM read_parquet('{orders_path}')
                WHERE status IN ('completed', 'shipped', 'processing')
                GROUP BY CAST(order_date AS DATE)
            ),
            with_rolling AS (
                SELECT
                    *,
                    AVG(total_revenue) OVER (
                        ORDER BY order_date
                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                    ) AS revenue_7d_avg,
                    AVG(total_revenue) OVER (
                        ORDER BY order_date
                        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                    ) AS revenue_30d_avg
                FROM daily
            ),
            with_yoy AS (
                SELECT
                    w.*,
                    LAG(w.total_revenue, 365) OVER (ORDER BY w.order_date) AS prev_year_revenue,
                    CASE
                        WHEN LAG(w.total_revenue, 365) OVER (ORDER BY w.order_date) > 0
                        THEN ROUND(
                            (w.total_revenue - LAG(w.total_revenue, 365) OVER (ORDER BY w.order_date))
                            / LAG(w.total_revenue, 365) OVER (ORDER BY w.order_date) * 100,
                        2)
                        ELSE NULL
                    END AS revenue_yoy_pct
                FROM with_rolling w
            )
            SELECT
                order_date,
                order_count,
                unique_customers,
                ROUND(total_revenue, 2) AS total_revenue,
                ROUND(avg_order_value, 2) AS avg_order_value,
                ROUND(revenue_7d_avg, 2) AS revenue_7d_avg,
                ROUND(revenue_30d_avg, 2) AS revenue_30d_avg,
                revenue_yoy_pct,
                CURRENT_TIMESTAMP AS _gold_computed_at
            FROM with_yoy
            ORDER BY order_date
        """).fetchdf()

        output_dir = self.gold_path / "daily_revenue"
        output_dir.mkdir(parents=True, exist_ok=True)
        result_df.to_parquet(str(output_dir / "daily_revenue.parquet"), index=False)

        return {
            "table": "gold_daily_revenue",
            "total_days": len(result_df),
            "date_range": f"{result_df['order_date'].min()} to {result_df['order_date'].max()}" if len(result_df) > 0 else "N/A",
            "total_revenue": float(result_df["total_revenue"].sum()) if len(result_df) > 0 else 0,
        }
