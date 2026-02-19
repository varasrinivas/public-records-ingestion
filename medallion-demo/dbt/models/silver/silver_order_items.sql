-- Silver Order Items — validated, deduplicated line items
-- Spec: REQ-SLV-001, REQ-SLV-003

WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY order_item_id
            ORDER BY _ingestion_timestamp DESC
        ) AS _row_num
    FROM {{ source('raw', 'order_items') }}
    WHERE order_item_id IS NOT NULL
      AND order_id IS NOT NULL
      AND product_id IS NOT NULL
)

SELECT
    order_item_id,
    order_id,
    product_id,
    CAST(quantity AS INTEGER) AS quantity,
    CAST(unit_price AS DECIMAL(18,2)) AS unit_price,
    CAST(line_total AS DECIMAL(18,2)) AS line_total,
    _batch_id AS _bronze_batch_id,
    CURRENT_TIMESTAMP AS _silver_processed_at,
    '1.0.0' AS _silver_version
FROM ranked
WHERE _row_num = 1
  AND CAST(quantity AS INTEGER) > 0
  AND CAST(unit_price AS DECIMAL(18,2)) > 0
