-- 010_test_carrosnaweb_catalog.sql

-- Validacoes basicas apos aplicar a DDL e rodar:
-- python scripts\carrosnaweb_ingestion\ingest_carrosnaweb_catalog.py --write

WITH counts AS (
  SELECT 'manufacturers' AS check_name, COUNT(*) AS row_count
  FROM public.market_carrosnaweb_manufacturers
  UNION ALL
  SELECT 'models' AS check_name, COUNT(*) AS row_count
  FROM public.market_carrosnaweb_models
  UNION ALL
  SELECT 'model_years' AS check_name, COUNT(*) AS row_count
  FROM public.market_carrosnaweb_model_years
)
SELECT *
FROM counts
ORDER BY check_name;


SELECT
  manufacturer_name,
  model_name,
  MIN(catalog_model_id) AS catalog_model_id,
  COUNT(*) AS years_count,
  MIN(model_year) AS first_year,
  MAX(model_year) AS last_year
FROM public.v_carrosnaweb_vehicle_catalog
WHERE
  (manufacturer_key = 'byd' AND model_key LIKE '%dolphin%')
  OR (manufacturer_key = 'renault' AND model_key LIKE '%kwid%')
  OR (manufacturer_key = 'changan' AND model_key LIKE '%uni t%')
  OR (manufacturer_key = 'hyundai' AND model_key LIKE '%hb20%')
GROUP BY
  manufacturer_name,
  model_name
ORDER BY
  manufacturer_name,
  model_name;


SELECT
  source_file_id,
  COUNT(*) AS rows_without_source_file
FROM (
  SELECT source_file_id FROM public.market_carrosnaweb_manufacturers
  UNION ALL
  SELECT source_file_id FROM public.market_carrosnaweb_models
  UNION ALL
  SELECT source_file_id FROM public.market_carrosnaweb_model_years
) catalog_rows
WHERE source_file_id IS NULL
GROUP BY source_file_id;


SELECT
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'v_carrosnaweb_vehicle_catalog'
  AND column_name IN ('catalog_row_id', 'catalog_model_id')
ORDER BY column_name;
