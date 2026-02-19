-- Silver Products — cleansed product catalog
-- Spec: REQ-SLV-001, REQ-SLV-003

WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY _ingestion_timestamp DESC
        ) AS _row_num
    FROM {{ source('raw', 'products') }}
    WHERE product_id IS NOT NULL
      AND product_id != ''
)

SELECT
    product_id,
    TRIM(name) AS name,
    TRIM(category) AS category,
    CAST(price AS DECIMAL(18,2)) AS price,
    CAST(cost AS DECIMAL(18,2)) AS cost,
    ROUND(
        (CAST(price AS DECIMAL(18,2)) - CAST(cost AS DECIMAL(18,2)))
        / NULLIF(CAST(price AS DECIMAL(18,2)), 0) * 100,
    2) AS margin_pct,
    _batch_id AS _bronze_batch_id,
    CURRENT_TIMESTAMP AS _silver_processed_at,
    '1.0.0' AS _silver_version
FROM ranked
WHERE _row_num = 1
  AND CAST(price AS DECIMAL(18,2)) > 0
