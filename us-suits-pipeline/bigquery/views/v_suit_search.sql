-- Consumer view: Full-text-friendly suit search
-- Optimized for downstream search / API serving

CREATE OR REPLACE VIEW \`suits_gold.v_suit_search\` AS
SELECT
  s.suit_id,
  s.state_code,
  s.county,
  s.case_number,
  s.case_type,
  s.filing_date,
  s.year_filed,
  s.case_status,
  s.days_open,
  s.amount_demanded,
  s.primary_plaintiff,
  s.primary_defendant,
  s.judge_name,
  s.cause_of_action,
  s.disposition,
  s.disposition_date,
  -- Searchable text blob
  CONCAT(
    COALESCE(s.primary_plaintiff, ''), ' ',
    COALESCE(s.primary_defendant, ''), ' ',
    COALESCE(s.case_number, ''), ' ',
    COALESCE(s.cause_of_action, ''), ' ',
    COALESCE(s.judge_name, '')
  ) AS search_text,
  s._gold_refreshed_at
FROM \`suits_gold.suit_best_view\` s
WHERE s.case_status != 'SEALED';
