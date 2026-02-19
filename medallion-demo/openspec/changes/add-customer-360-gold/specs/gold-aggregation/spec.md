# Gold Aggregation Specification (DELTA)
# Change: add-customer-360-gold

## Requirements

### REQ-GLD-002: Customer 360 Aggregate (NEW)

+ The system SHALL produce a `gold_customer_360` table with:
+ - `customer_id`, `email`, `first_name`, `last_name`, `signup_date`
+ - `total_orders`: Lifetime order count
+ - `total_revenue`: Lifetime revenue (sum of completed order totals)
+ - `avg_order_value`: Mean order value
+ - `first_order_date`, `last_order_date`
+ - `days_since_last_order`: Recency metric
+ - `order_frequency_days`: Average days between orders
+ - `completed_orders`, `cancelled_orders`: Status breakdown
+ - `ltv_tier`: Enum [platinum, gold, silver, bronze]
+ - `rfm_score`: Composite RFM score (111–555)
+ - `rfm_segment`: Named segment from RFM mapping

+ #### Scenario: Customer with orders
+ - GIVEN a customer with 10 completed orders totaling $2,500
+ - WHEN the Gold pipeline runs
+ - THEN `total_orders` = 10
+ - AND `total_revenue` = 2500.00
+ - AND `ltv_tier` = "gold"
+ - AND `rfm_segment` is assigned based on quintile scoring

+ #### Scenario: Customer with no orders
+ - GIVEN a customer who has never placed an order
+ - WHEN the Gold pipeline runs
+ - THEN `total_orders` = 0
+ - AND `total_revenue` = 0.00
+ - AND `ltv_tier` = "bronze"
+ - AND `rfm_segment` = "No Orders"

+ ### REQ-GLD-002a: RFM Scoring
+ The system SHALL compute RFM scores using quintile binning:
+ - Recency: days since last order (lower days = higher score)
+ - Frequency: order count in last 12 months
+ - Monetary: total spend in last 12 months
+ - Each scored 1–5, composite = R*100 + F*10 + M

+ ### REQ-GLD-002b: RFM Segment Mapping
+ The system SHALL map composite RFM scores to named segments:
+ - Champions: R≥4, F≥4, M≥4
+ - Loyal: R≥4, F≥3
+ - New Customers: R≥4, F≤2
+ - At Risk: R≤2, F≥3
+ - Lost: R≤2, F≤2, M≤2
+ - Other: all remaining combinations
