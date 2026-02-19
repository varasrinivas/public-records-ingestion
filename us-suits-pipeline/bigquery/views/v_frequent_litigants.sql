-- Frequent litigants: parties appearing in 10+ suits
-- Useful for compliance, risk analysis, and due diligence

CREATE OR REPLACE VIEW \`suits_gold.v_frequent_litigants\` AS
SELECT
  party_name,
  is_entity,
  total_suits_as_plaintiff,
  total_suits_as_defendant,
  total_appearances,
  first_appearance_date,
  last_appearance_date,
  DATE_DIFF(last_appearance_date, first_appearance_date, DAY) AS litigation_span_days,
  is_frequent_litigant
FROM \`suits_gold.suit_party_best_view\`
WHERE is_frequent_litigant = TRUE
ORDER BY total_appearances DESC;
