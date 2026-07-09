-- 007_test_fenabrave_items6_8_electrified_registrations.sql

-- Validacao estrutural dos itens 6, 7 e 8 da fase 2 Fenabrave.
SELECT
  source_file_id,
  reference_period,
  item_code,
  vehicle_category,
  aggregation_level,
  powertrain_type,
  COUNT(*) AS row_count,
  MIN(rank_position) AS min_rank,
  MAX(rank_position) AS max_rank,
  SUM(units) AS total_units,
  ROUND(SUM(COALESCE(market_share_pct, 0))::numeric, 4) AS total_share_pct
FROM public.market_vehicle_electrified_registrations
WHERE item_code IN (
  'fenabrave_item_06_mercado_eletrificados_mes',
  'fenabrave_item_07_total_marca_hibrido_mes',
  'fenabrave_item_08_total_marca_eletrico_mes'
)
GROUP BY
  source_file_id,
  reference_period,
  item_code,
  vehicle_category,
  aggregation_level,
  powertrain_type
ORDER BY
  reference_period,
  item_code,
  vehicle_category,
  powertrain_type;

-- Cobertura mensal dos itens 6, 7 e 8 por PDF Fenabrave.
SELECT
  f.reference_period,
  f.id AS source_file_id,
  f.storage_bucket,
  f.storage_path,
  i.item_code,
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
 AND i.item_code IN (
   'fenabrave_item_06_mercado_eletrificados_mes',
   'fenabrave_item_07_total_marca_hibrido_mes',
   'fenabrave_item_08_total_marca_eletrico_mes'
 )
WHERE s.source_name = 'Fenabrave'
ORDER BY f.reference_period, i.item_code;
