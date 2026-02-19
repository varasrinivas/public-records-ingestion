# Proposal: Add Customer 360 Gold Table

## Summary
Build a comprehensive Customer 360 view in the Gold layer that combines
customer profile data with order history, computing LTV, RFM segments,
and behavioral metrics for the analytics and marketing teams.

## Motivation
- Marketing needs a single customer view for campaign targeting
- Analytics team requires pre-computed cohort metrics
- ML team needs features for churn prediction model
- Currently, analysts write 200+ line queries joining 5+ Silver tables

## Scope
- New Gold table: `gold_customer_360`
- RFM segmentation logic
- LTV tier classification
- dbt model + tests
- Airflow DAG task for daily refresh
- Data quality checks

## Out of Scope
- Real-time customer profile (future: streaming)
- Customer graph / social connections
- PII masking (handled by governance layer)
