# Data Dictionary

## Medallion Architecture — Table Reference

### 🥉 Bronze Layer (Raw Ingestion)

| Table | Source | Primary Key | Description |
|-------|--------|-------------|-------------|
| `bronze.customers` | CSV / PostgreSQL | `customer_id` | Raw customer profiles as-is from source |
| `bronze.orders` | CSV / PostgreSQL | `order_id` | Raw order transactions |
| `bronze.order_items` | CSV / PostgreSQL | `order_item_id` | Raw order line items |
| `bronze.products` | CSV / PostgreSQL | `product_id` | Raw product catalog |

**Metadata columns** (all Bronze tables):
| Column | Type | Description |
|--------|------|-------------|
| `_batch_id` | string | Deterministic UUID for the ingestion batch |
| `_source_system` | string | Source system identifier (e.g., "csv_local") |
| `_source_table` | string | Original table/endpoint name |
| `_ingestion_timestamp` | timestamp | UTC time of extraction |
| `_file_path` | string | Original file path (file sources only) |

---

### 🥈 Silver Layer (Cleansed & Conformed)

| Table | Source | Primary Key | SCD | Description |
|-------|--------|-------------|-----|-------------|
| `silver.customers` | bronze.customers | `customer_id` | Type 2 | Validated, deduplicated customer profiles |
| `silver.orders` | bronze.orders | `order_id` | — | Validated, type-cast order records |
| `silver.order_items` | bronze.order_items | `order_item_id` | — | Validated line items |
| `silver.products` | bronze.products | `product_id` | Type 2 | Validated product catalog with margin |

**Silver metadata columns:**
| Column | Type | Description |
|--------|------|-------------|
| `_bronze_batch_id` | string | Reference to source Bronze batch |
| `_silver_processed_at` | timestamp | Transformation timestamp |
| `_silver_version` | string | Schema version applied |

**SCD Type 2 columns** (customers, products):
| Column | Type | Description |
|--------|------|-------------|
| `valid_from` | date | Start of validity period |
| `valid_to` | date | End of validity (9999-12-31 = current) |
| `is_current` | boolean | True if this is the active record |

---

### 🥇 Gold Layer (Business Aggregates)

#### `gold.customer_360`
Comprehensive customer view with lifetime metrics and behavioral segmentation.

| Column | Type | Description | Spec |
|--------|------|-------------|------|
| `customer_id` | string | Unique customer identifier | REQ-GLD-002 |
| `email` | string | Customer email (lowercase) | |
| `first_name` | string | Customer first name | |
| `last_name` | string | Customer last name | |
| `city` | string | City | |
| `state` | string | State code (2-letter) | |
| `signup_date` | date | Account creation date | |
| `is_active` | boolean | Active account flag | |
| `total_orders` | integer | Lifetime order count | REQ-GLD-002 |
| `total_revenue` | decimal | Lifetime revenue ($) | REQ-GLD-002 |
| `avg_order_value` | decimal | Mean order value ($) | REQ-GLD-002 |
| `first_order_date` | date | Date of first order | REQ-GLD-002 |
| `last_order_date` | date | Date of most recent order | REQ-GLD-002 |
| `days_since_last_order` | integer | Recency metric | REQ-GLD-002 |
| `order_frequency_days` | decimal | Avg days between orders | REQ-GLD-002 |
| `completed_orders` | integer | Count of completed orders | REQ-GLD-002 |
| `cancelled_orders` | integer | Count of cancelled orders | REQ-GLD-002 |
| `ltv_tier` | string | platinum / gold / silver / bronze | REQ-GLD-002 |
| `rfm_score` | integer | Composite RFM score (111–555) | REQ-GLD-002a |
| `rfm_segment` | string | Named customer segment | REQ-GLD-002b |

**LTV Tier Thresholds:**
| Tier | Revenue Threshold |
|------|-------------------|
| Platinum | ≥ $5,000 |
| Gold | ≥ $1,000 |
| Silver | ≥ $250 |
| Bronze | < $250 |

**RFM Segments:**
| Segment | R | F | Description |
|---------|---|---|-------------|
| Champions | ≥4 | ≥4 | Best customers, high value |
| Loyal | ≥4 | ≥3 | Frequent, engaged |
| New Customers | ≥4 | ≤2 | Recent first purchase |
| At Risk | ≤2 | ≥3 | Declining engagement |
| Lost | ≤2 | ≤2 | Haven't purchased recently |

#### `gold.daily_revenue`
Daily aggregated revenue with rolling averages and year-over-year comparison.

| Column | Type | Description | Spec |
|--------|------|-------------|------|
| `order_date` | date | Calendar date | REQ-GLD-003 |
| `order_count` | integer | Orders placed that day | REQ-GLD-003 |
| `unique_customers` | integer | Distinct buyers | REQ-GLD-003 |
| `total_revenue` | decimal | Day's total revenue ($) | REQ-GLD-003 |
| `avg_order_value` | decimal | Mean order value ($) | REQ-GLD-003 |
| `revenue_7d_avg` | decimal | 7-day rolling average | REQ-GLD-003 |
| `revenue_30d_avg` | decimal | 30-day rolling average | REQ-GLD-003 |
| `revenue_yoy_pct` | decimal | Year-over-year growth % | REQ-GLD-003 |

#### `gold.product_performance`
Product-level revenue and margin analysis.

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | string | Unique product identifier |
| `product_name` | string | Product display name |
| `category` | string | Product category |
| `current_price` | decimal | Current selling price |
| `margin_pct` | decimal | Gross margin percentage |
| `units_sold` | integer | Total units sold |
| `total_revenue` | decimal | Lifetime revenue |
| `gross_profit` | decimal | Revenue minus cost |
| `unique_buyers` | integer | Distinct customers |
| `revenue_per_buyer` | decimal | Avg revenue per buyer |
| `revenue_percentile` | decimal | Relative ranking (0–1) |

---

### 🚫 Quarantine Tables

| Path | Source | Description |
|------|--------|-------------|
| `quarantine/silver/customers/` | Bronze → Silver gate | Customers failing validation |
| `quarantine/silver/orders/` | Bronze → Silver gate | Orders failing validation |

| Column | Type | Description |
|--------|------|-------------|
| `_quarantine_reason` | string | Why the record was rejected |
| `_quarantine_date` | date | Date of rejection |
| *(all original columns)* | — | Full original record preserved |
