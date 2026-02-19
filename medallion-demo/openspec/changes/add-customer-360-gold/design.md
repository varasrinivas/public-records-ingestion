# Technical Design: Customer 360 Gold Table

## Data Flow
```
silver_customers ──┐
                   ├──► gold_customer_360
silver_orders ─────┘
```

## RFM Scoring Algorithm
- Recency: Days since last order → Score 1-5 (quintiles)
- Frequency: Order count in last 12 months → Score 1-5
- Monetary: Total spend in last 12 months → Score 1-5
- Segment: Concatenated "R{r}F{f}M{m}" → mapped to named segment

## RFM Segment Mapping
| Pattern | Segment | Description |
|---------|---------|-------------|
| 5,5,5 / 5,5,4 / 5,4,5 | Champions | Best customers |
| 5,4,4 / 4,5,5 / 4,5,4 | Loyal | Frequent, high-value |
| 5,1,1 / 4,1,1 | New Customers | Recent first purchase |
| 3,3,3 / 3,2,3 / 2,3,3 | At Risk | Declining engagement |
| 1,1,1 / 1,2,1 / 1,1,2 | Lost | Haven't purchased in long time |
| * | Other | Everything else |

## LTV Tier Thresholds
- Platinum: total_revenue >= $5,000
- Gold: total_revenue >= $1,000
- Silver: total_revenue >= $250
- Bronze: total_revenue < $250

## Incremental Strategy
- Full rebuild daily (customer count manageable <10M)
- Future: incremental with changed-customer detection
