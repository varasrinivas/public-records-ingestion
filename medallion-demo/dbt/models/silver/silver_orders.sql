-- Silver Orders — cleansed, deduplicated, validated
-- Spec: REQ-SLV-001, REQ-SLV-002, REQ-SLV-003

WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY _ingestion_timestamp DESC
        ) AS _row_num
    FROM {{ ref('bronze_orders') }}
    WHERE order_id IS NOT NULL
      AND customer_id IS NOT NULL
      AND order_date IS NOT NULL
)

SELECT
    order_id,
    customer_id,
    CAST(order_date AS DATE) AS order_date,
    LOWER(TRIM(status)) AS status,
    total_amount,
    LOWER(TRIM(payment_method)) AS payment_method,
    _batch_id AS _bronze_batch_id,
    CURRENT_TIMESTAMP AS _silver_processed_at,
    '1.0.0' AS _silver_version
FROM ranked
WHERE _row_num = 1
  AND status IN ('completed', 'shipped', 'processing', 'cancelled', 'refunded')
  AND total_amount >= 0
