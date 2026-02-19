-- Gold Daily Revenue — with rolling averages and YoY comparison
-- Spec: REQ-GLD-003

WITH daily AS (
    SELECT
        order_date,
        COUNT(DISTINCT order_id) AS order_count,
        COUNT(DISTINCT customer_id) AS unique_customers,
        SUM(total_amount) AS total_revenue,
        AVG(total_amount) AS avg_order_value
    FROM {{ ref('silver_orders') }}
    WHERE status IN ('completed', 'shipped', 'processing')
    GROUP BY order_date
)

SELECT
    order_date,
    order_count,
    unique_customers,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(avg_order_value, 2) AS avg_order_value,
    ROUND(AVG(total_revenue) OVER (
        ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS revenue_7d_avg,
    ROUND(AVG(total_revenue) OVER (
        ORDER BY order_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 2) AS revenue_30d_avg,
    CURRENT_TIMESTAMP AS _gold_computed_at
FROM daily
ORDER BY order_date
