-- State-level dashboard metrics for BI tools

CREATE OR REPLACE VIEW \`suits_gold.v_state_dashboard\` AS
WITH current_year AS (
  SELECT EXTRACT(YEAR FROM CURRENT_DATE()) AS yr
)
SELECT
  s.state_code,
  s.case_type,
  s.year_filed,
  s.suit_count,
  ROUND(s.avg_days_to_disposition, 0) AS avg_days_to_resolve,
  ROUND(s.disposition_rate, 1) AS disposition_rate_pct,
  -- Year-over-year comparison
  LAG(s.suit_count) OVER (
    PARTITION BY s.state_code, s.case_type
    ORDER BY s.year_filed
  ) AS prev_year_count,
  SAFE_DIVIDE(
    s.suit_count - LAG(s.suit_count) OVER (
      PARTITION BY s.state_code, s.case_type ORDER BY s.year_filed
    ),
    LAG(s.suit_count) OVER (
      PARTITION BY s.state_code, s.case_type ORDER BY s.year_filed
    )
  ) * 100 AS yoy_change_pct
FROM \`suits_gold.suit_state_summary\` s
ORDER BY s.state_code, s.year_filed DESC;
