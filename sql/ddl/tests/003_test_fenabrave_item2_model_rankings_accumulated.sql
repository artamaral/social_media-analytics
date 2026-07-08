-- 003_test_fenabrave_item2_model_rankings_accumulated.sql

-- Validacao estrutural do item 2 da fase 2 Fenabrave.
-- Resultado esperado para cada PDF validado:
-- - 50 linhas de automoveis
-- - 50 linhas de comerciais_leves
-- - rankings de 1 a 50 sem duplicidade
-- - unidades positivas e modelo bruto preenchido
-- - total acumulado do top 50 maior ou igual ao total mensal do item 1

SELECT
  source_file_id,
  reference_period,
  vehicle_category,
  COUNT(*) AS row_count,
  MIN(rank_position) AS min_rank,
  MAX(rank_position) AS max_rank,
  COUNT(DISTINCT rank_position) AS distinct_ranks,
  SUM(CASE WHEN monthly_units IS NULL OR monthly_units <= 0 THEN 1 ELSE 0 END)
    AS invalid_units,
  SUM(CASE WHEN model_label_raw IS NULL OR trim(model_label_raw) = '' THEN 1 ELSE 0 END)
    AS missing_model_label
FROM public.market_vehicle_model_rankings
WHERE item_code = 'fenabrave_item_02_ranking_emplacamentos_acumulado'
GROUP BY source_file_id, reference_period, vehicle_category
ORDER BY reference_period, vehicle_category;

-- Comparacao mensal x acumulado do top 50 por categoria e periodo.
WITH monthly AS (
  SELECT
    source_file_id,
    reference_period,
    vehicle_category,
    SUM(monthly_units) AS monthly_top50_units
  FROM public.market_vehicle_model_rankings
  WHERE item_code = 'fenabrave_item_01_ranking_emplacamentos_mes'
  GROUP BY source_file_id, reference_period, vehicle_category
),
accumulated AS (
  SELECT
    source_file_id,
    reference_period,
    vehicle_category,
    SUM(monthly_units) AS accumulated_top50_units
  FROM public.market_vehicle_model_rankings
  WHERE item_code = 'fenabrave_item_02_ranking_emplacamentos_acumulado'
  GROUP BY source_file_id, reference_period, vehicle_category
)
SELECT
  a.reference_period,
  a.source_file_id,
  a.vehicle_category,
  m.monthly_top50_units,
  a.accumulated_top50_units,
  a.accumulated_top50_units - m.monthly_top50_units AS difference_from_monthly,
  (a.accumulated_top50_units >= m.monthly_top50_units) AS passed
FROM accumulated a
JOIN monthly m
  ON m.source_file_id = a.source_file_id
 AND m.reference_period = a.reference_period
 AND m.vehicle_category = a.vehicle_category
ORDER BY a.reference_period, a.vehicle_category;

-- Cobertura mensal do item 2 por PDF Fenabrave.
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
 AND i.item_code = 'fenabrave_item_02_ranking_emplacamentos_acumulado'
WHERE s.source_name = 'Fenabrave'
ORDER BY f.reference_period;
