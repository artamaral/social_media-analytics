-- 006_test_fenabrave_item5_subsegment_shares.sql

-- Validacao estrutural do item 5 da fase 2 Fenabrave.
SELECT
  source_file_id,
  reference_period,
  COUNT(*) AS row_count,
  COUNT(DISTINCT subsegment_name) AS distinct_subsegments,
  SUM(CASE WHEN subsegment_name IS NULL OR trim(subsegment_name) = '' THEN 1 ELSE 0 END)
    AS missing_subsegment_name,
  ROUND(SUM(current_month_share_pct)::numeric, 4) AS current_month_total,
  ROUND(SUM(current_year_accum_share_pct)::numeric, 4) AS current_year_total,
  ROUND(SUM(prior_year_accum_share_pct)::numeric, 4) AS prior_year_total
FROM public.market_vehicle_subsegment_shares
WHERE item_code = 'fenabrave_item_05_emplacamentos_por_subsegmento'
GROUP BY source_file_id, reference_period
ORDER BY reference_period;

-- Cobertura mensal do item 5 por PDF Fenabrave.
SELECT
  f.reference_period,
  f.id AS source_file_id,
  f.storage_bucket,
  f.storage_path,
  f.extraction_status AS source_file_status,
  i.status AS item_status,
  i.row_count,
  i.validation_status,
  CASE
    WHEN i.id IS NULL THEN 'missing_control'
    WHEN i.status IN ('validated', 'warning_accepted') THEN 'covered'
    WHEN i.status IN ('pending', 'extracted') THEN 'pending'
    WHEN i.status = 'failed' THEN 'failed'
    ELSE 'review'
  END AS coverage_status
FROM public.market_source_files f
JOIN public.market_data_sources s ON s.id = f.source_id
LEFT JOIN public.market_fenabrave_extraction_items i
  ON i.source_file_id = f.id
 AND i.item_code = 'fenabrave_item_05_emplacamentos_por_subsegmento'
WHERE s.source_name = 'Fenabrave'
ORDER BY f.reference_period;
