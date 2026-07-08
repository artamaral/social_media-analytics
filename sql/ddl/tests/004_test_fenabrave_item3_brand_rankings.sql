-- 004_test_fenabrave_item3_brand_rankings.sql

-- Validacao estrutural do item 3 da fase 2 Fenabrave.
SELECT
  source_file_id,
  reference_period,
  vehicle_category,
  COUNT(*) AS row_count,
  MIN(rank_position) AS min_rank,
  MAX(rank_position) AS max_rank,
  COUNT(DISTINCT rank_position) AS distinct_ranks,
  SUM(CASE WHEN units IS NULL OR units <= 0 THEN 1 ELSE 0 END) AS invalid_units,
  SUM(CASE WHEN brand_name_raw IS NULL OR trim(brand_name_raw) = '' THEN 1 ELSE 0 END)
    AS missing_brand_name,
  SUM(CASE WHEN market_share_pct IS NULL OR market_share_pct < 0 OR market_share_pct > 100 THEN 1 ELSE 0 END)
    AS invalid_share
FROM public.market_vehicle_brand_rankings
WHERE item_code = 'fenabrave_item_03_ranking_por_marca_mes'
GROUP BY source_file_id, reference_period, vehicle_category
ORDER BY reference_period, vehicle_category;

-- Cobertura mensal do item 3 por PDF Fenabrave.
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
 AND i.item_code = 'fenabrave_item_03_ranking_por_marca_mes'
WHERE s.source_name = 'Fenabrave'
ORDER BY f.reference_period;
