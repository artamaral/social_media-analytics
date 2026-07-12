-- 008_test_fenabrave_items11_12_sales_channel_mix.sql

-- Validacao estrutural dos itens 11 e 12 da fase 2 Fenabrave.
SELECT
  source_file_id,
  reference_period,
  item_code,
  published_period_type,
  vehicle_category,
  COUNT(*) AS row_count,
  ROUND(SUM(share_pct)::numeric, 4) AS total_share_pct,
  MIN(share_pct) AS min_share_pct,
  MAX(share_pct) AS max_share_pct
FROM public.market_vehicle_sales_channel_mix
WHERE item_code IN (
  'fenabrave_item_11_participacao_venda_direta_varejo_mes',
  'fenabrave_item_12_participacao_venda_direta_varejo_acumulado'
)
GROUP BY
  source_file_id,
  reference_period,
  item_code,
  published_period_type,
  vehicle_category
ORDER BY
  reference_period,
  item_code,
  vehicle_category;

-- Cobertura mensal dos itens 11 e 12 por PDF Fenabrave.
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
   'fenabrave_item_11_participacao_venda_direta_varejo_mes',
   'fenabrave_item_12_participacao_venda_direta_varejo_acumulado'
 )
WHERE s.source_name = 'Fenabrave'
ORDER BY f.reference_period, i.item_code;
