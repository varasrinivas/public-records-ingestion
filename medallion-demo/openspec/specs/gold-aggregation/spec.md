# Gold Aggregation Layer Specification

## Purpose
Produce business-ready datasets optimized for analytics, BI tools, and ML
feature stores. Implements star schema with pre-computed KPIs.

## Requirements

### REQ-GLD-001: Star Schema Design
The system SHALL produce a star schema with:
- `fact_orders`: Order transaction facts
- `fact_daily_revenue`: Daily revenue aggregates
- `dim_customers`: Customer dimension (SCD Type 2)
- `dim_products`: Product dimension
- `dim_date`: Date dimension (pre-populated calendar)

### REQ-GLD-002: Customer 360 Aggregate
The system SHALL produce a `gold_customer_360` table with:
- `customer_id`, `email`, `name`, `signup_date`
- `total_orders`: Lifetime order count
- `total_revenue`: Lifetime revenue (sum of order totals)
- `avg_order_value`: Mean order value
- `first_order_date`, `last_order_date`
- `days_since_last_order`: Recency metric
- `order_frequency_days`: Average days between orders
- `ltv_tier`: Enum [platinum, gold, silver, bronze]
- `rfm_segment`: RFM-based customer segment

### REQ-GLD-003: Daily Revenue Aggregate
The system SHALL produce a `gold_daily_revenue` table with:
- `date`, `total_revenue`, `order_count`, `unique_customers`
- `avg_order_value`
- `revenue_7d_avg`: 7-day rolling average
- `revenue_30d_avg`: 30-day rolling average
- `revenue_yoy_pct`: Year-over-year growth percentage
- `product_category_breakdown`: JSON map of category → revenue

### REQ-GLD-004: Partitioning & Clustering
- Fact tables: partitioned by `order_date` (daily)
- Dimension tables: not partitioned (small, full replace)
- Customer 360: clustered by `ltv_tier`
- Daily revenue: clustered by `date`

### REQ-GLD-005: Freshness SLA
- Gold tables SHALL be updated within 2 hours of Bronze ingestion
- Staleness monitoring SHALL alert if Gold is >4 hours behind
