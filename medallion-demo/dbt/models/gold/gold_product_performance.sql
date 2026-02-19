-- Gold Product Performance — category-level revenue and margin analysis
-- Spec: REQ-GLD-001

WITH product_sales AS (
    SELECT
        p.product_id,
        p.name AS product_name,
        p.category,
        p.price,
        p.cost,
        p.margin_pct,
        SUM(oi.quantity) AS units_sold,
        SUM(oi.line_total) AS total_revenue,
        SUM(oi.quantity * p.cost) AS total_cost,
        COUNT(DISTINCT o.order_id) AS order_appearances,
        COUNT(DISTINCT o.customer_id) AS unique_buyers
    FROM {{ ref('silver_products') }} p
    INNER JOIN {{ ref('silver_order_items') }} oi ON p.product_id = oi.product_id
    INNER JOIN {{ ref('silver_orders') }} o ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'shipped', 'processing')
    GROUP BY 1, 2, 3, 4, 5, 6
)

SELECT
    product_id,
    product_name,
    category,
    price AS current_price,
    cost AS current_cost,
    margin_pct,
    units_sold,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(total_cost, 2) AS total_cost,
    ROUND(total_revenue - total_cost, 2) AS gross_profit,
    order_appearances,
    unique_buyers,
    ROUND(total_revenue / NULLIF(unique_buyers, 0), 2) AS revenue_per_buyer,
    PERCENT_RANK() OVER (ORDER BY total_revenue) AS revenue_percentile,
    CURRENT_TIMESTAMP AS _gold_computed_at
FROM product_sales
ORDER BY total_revenue DESC
