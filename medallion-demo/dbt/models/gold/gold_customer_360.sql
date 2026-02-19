-- Gold Customer 360 — comprehensive customer view
-- Spec: REQ-GLD-002

WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(total_amount) AS total_revenue,
        AVG(total_amount) AS avg_order_value,
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date,
        COUNT(DISTINCT CASE WHEN status = 'completed' THEN order_id END) AS completed_orders,
        COUNT(DISTINCT CASE WHEN status = 'cancelled' THEN order_id END) AS cancelled_orders
    FROM {{ ref('silver_orders') }}
    WHERE status != 'refunded'
    GROUP BY customer_id
),

customer_profile AS (
    SELECT * FROM {{ ref('silver_customers') }}
    WHERE is_current = true
)

SELECT
    p.customer_id,
    p.email,
    p.first_name,
    p.last_name,
    p.city,
    p.state,
    p.signup_date,
    COALESCE(o.total_orders, 0) AS total_orders,
    COALESCE(o.total_revenue, 0) AS total_revenue,
    COALESCE(ROUND(o.avg_order_value, 2), 0) AS avg_order_value,
    o.first_order_date,
    o.last_order_date,
    DATEDIFF('day', o.last_order_date, CURRENT_DATE) AS days_since_last_order,
    CASE
        WHEN COALESCE(o.total_revenue, 0) >= 5000 THEN 'platinum'
        WHEN COALESCE(o.total_revenue, 0) >= 1000 THEN 'gold'
        WHEN COALESCE(o.total_revenue, 0) >= 250 THEN 'silver'
        ELSE 'bronze'
    END AS ltv_tier,
    CURRENT_TIMESTAMP AS _gold_computed_at
FROM customer_profile p
LEFT JOIN customer_orders o ON p.customer_id = o.customer_id
