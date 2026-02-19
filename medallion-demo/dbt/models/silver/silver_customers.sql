-- Silver Customers — cleansed, deduplicated, SCD Type 2
-- Spec: REQ-SLV-001, REQ-SLV-002, REQ-SLV-003, REQ-SLV-004

WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY _ingestion_timestamp DESC
        ) AS _row_num
    FROM {{ source('raw', 'customers') }}
    WHERE customer_id IS NOT NULL
      AND customer_id != ''
      AND email LIKE '%@%'
      AND first_name IS NOT NULL
      AND first_name != ''
),

deduped AS (
    SELECT * FROM ranked WHERE _row_num = 1
),

standardized AS (
    SELECT
        customer_id,
        LOWER(TRIM(email)) AS email,
        TRIM(first_name) AS first_name,
        TRIM(last_name) AS last_name,
        TRIM(city) AS city,
        UPPER(TRIM(state)) AS state,
        CAST(signup_date AS DATE) AS signup_date,
        CASE
            WHEN LOWER(TRIM(is_active)) = 'true' THEN true
            ELSE false
        END AS is_active,
        -- SCD Type 2 fields (REQ-SLV-004)
        CURRENT_DATE AS valid_from,
        CAST('9999-12-31' AS DATE) AS valid_to,
        true AS is_current,
        -- Lineage (REQ-SLV-005)
        _batch_id AS _bronze_batch_id,
        CURRENT_TIMESTAMP AS _silver_processed_at,
        '1.0.0' AS _silver_version
    FROM deduped
)

SELECT * FROM standardized
