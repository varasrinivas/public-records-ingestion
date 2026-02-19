-- Bronze Orders — raw ingestion view (schema-on-read)
-- Spec: REQ-BRZ-003

SELECT
    order_id,
    customer_id,
    order_date,
    status,
    CAST(total_amount AS DECIMAL(18,2)) AS total_amount,
    payment_method,
    _batch_id,
    _source_system,
    _ingestion_timestamp
FROM {{ source('raw', 'orders') }}
