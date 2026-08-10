-- audit_fenabrave_full_monthly_load.sql
--
-- Auditoria de fechamento para a carga mensal completa da Fenabrave.
-- Uso:
-- 1. Ajustar `target_period` no CTE `params`.
-- 2. Executar o arquivo inteiro no Supabase SQL Editor.
-- 3. Revisar cada bloco antes de considerar o mes como aprovado.

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_files AS (
  SELECT
    f.id AS source_file_id,
    f.reference_period,
    f.original_filename,
    f.source_url,
    f.storage_bucket,
    f.storage_path,
    f.file_size_bytes,
    f.sha256,
    f.extraction_status,
    f.extraction_notes
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
),
selected_file AS (
  SELECT *
  FROM selected_files
  ORDER BY source_file_id DESC
  LIMIT 1
)
SELECT
  'source_file_uniqueness' AS check_name,
  CASE
    WHEN COUNT(*) = 1 THEN 'passed'
    WHEN COUNT(*) = 0 THEN 'failed'
    ELSE 'failed'
  END AS check_status,
  COUNT(*) AS matching_source_files,
  STRING_AGG(source_file_id::text, ', ' ORDER BY source_file_id) AS source_file_ids
FROM selected_files;

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_file AS (
  SELECT
    f.id AS source_file_id,
    f.reference_period,
    f.original_filename,
    f.source_url,
    f.storage_bucket,
    f.storage_path,
    f.file_size_bytes,
    f.sha256,
    f.extraction_status,
    f.extraction_notes
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
  ORDER BY f.id DESC
  LIMIT 1
)
SELECT
  source_file_id,
  reference_period,
  original_filename,
  extraction_status,
  CASE
    WHEN source_url IS NULL
      OR storage_bucket IS NULL
      OR storage_path IS NULL
      OR file_size_bytes IS NULL
      OR sha256 IS NULL
    THEN 'failed'
    ELSE 'passed'
  END AS metadata_check,
  source_url,
  storage_bucket,
  storage_path,
  file_size_bytes,
  sha256,
  extraction_notes
FROM selected_file;

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_file AS (
  SELECT f.id AS source_file_id, f.reference_period
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
  ORDER BY f.id DESC
  LIMIT 1
),
expected_items AS (
  SELECT *
  FROM (
    VALUES
      ('fenabrave_item_01_ranking_emplacamentos_mes'),
      ('fenabrave_item_02_ranking_emplacamentos_acumulado'),
      ('fenabrave_item_03_ranking_por_marca_mes'),
      ('fenabrave_item_04_ranking_por_marca_acumulado'),
      ('fenabrave_item_05_emplacamentos_por_subsegmento'),
      ('fenabrave_item_06_mercado_eletrificados_mes'),
      ('fenabrave_item_07_total_marca_hibrido_mes'),
      ('fenabrave_item_08_total_marca_eletrico_mes'),
      ('fenabrave_item_11_participacao_venda_direta_varejo_mes'),
      ('fenabrave_item_12_participacao_venda_direta_varejo_acumulado'),
      ('fenabrave_item_13_ranking_marca_emplacamento_varejo_mes'),
      ('fenabrave_item_14_ranking_marca_emplacamento_varejo_acumulado'),
      ('fenabrave_item_15_ranking_marca_emplacamento_direta_mes'),
      ('fenabrave_item_16_ranking_marca_emplacamento_direta_acumulado'),
      ('fenabrave_item_17_participacao_mercado_marca_mes'),
      ('fenabrave_item_18_participacao_mercado_marca_acumulado'),
      ('fenabrave_item_19_modelos_emplacados_venda_direta_mes'),
      ('fenabrave_item_20_modelos_emplacados_varejo_mes'),
      ('fenabrave_item_21_modelos_emplacados_venda_direta_acumulado'),
      ('fenabrave_item_22_modelos_emplacados_varejo_acumulado')
  ) AS t(item_code)
),
actual_counts AS (
  SELECT source_file_id, item_code, COUNT(*) AS actual_row_count
  FROM public.market_vehicle_model_rankings
  GROUP BY source_file_id, item_code
  UNION ALL
  SELECT source_file_id, item_code, COUNT(*) AS actual_row_count
  FROM public.market_vehicle_brand_rankings
  GROUP BY source_file_id, item_code
  UNION ALL
  SELECT source_file_id, item_code, COUNT(*) AS actual_row_count
  FROM public.market_vehicle_subsegment_shares
  GROUP BY source_file_id, item_code
  UNION ALL
  SELECT source_file_id, item_code, COUNT(*) AS actual_row_count
  FROM public.market_vehicle_electrified_registrations
  GROUP BY source_file_id, item_code
  UNION ALL
  SELECT source_file_id, item_code, COUNT(*) AS actual_row_count
  FROM public.market_vehicle_sales_channel_mix
  GROUP BY source_file_id, item_code
),
control_rows AS (
  SELECT
    i.item_code,
    i.status,
    i.validation_status,
    i.row_count AS control_row_count,
    a.actual_row_count
  FROM selected_file f
  JOIN public.market_fenabrave_extraction_items i
    ON i.source_file_id = f.source_file_id
  LEFT JOIN actual_counts a
    ON a.source_file_id = i.source_file_id
   AND a.item_code = i.item_code
)
SELECT
  e.item_code,
  c.status AS control_status,
  c.validation_status,
  c.control_row_count,
  c.actual_row_count,
  CASE
    WHEN c.item_code IS NULL THEN 'failed'
    WHEN c.status NOT IN ('validated', 'warning_accepted') THEN 'failed'
    WHEN c.validation_status NOT IN ('passed', 'warning') THEN 'failed'
    WHEN c.control_row_count IS DISTINCT FROM c.actual_row_count THEN 'failed'
    ELSE 'passed'
  END AS control_check
FROM expected_items e
LEFT JOIN control_rows c
  ON c.item_code = e.item_code
ORDER BY e.item_code;

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_file AS (
  SELECT f.id AS source_file_id, f.reference_period
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
  ORDER BY f.id DESC
  LIMIT 1
),
segment_rows AS (
  SELECT
    segment_code,
    segmento,
    mes_atual
  FROM public.market_vehicle_registrations_segment s
  JOIN selected_file f
    ON f.source_file_id = s.source_file_id
),
totals AS (
  SELECT
    MAX(CASE WHEN segment_code = 'autos' THEN mes_atual END) AS autos,
    MAX(CASE WHEN segment_code = 'comerciais_leves' THEN mes_atual END) AS comerciais_leves,
    MAX(CASE WHEN segment_code = 'autos_comerciais_leves' THEN mes_atual END) AS autos_comerciais_leves,
    MAX(CASE WHEN segment_code = 'caminhoes' THEN mes_atual END) AS caminhoes,
    MAX(CASE WHEN segment_code = 'onibus' THEN mes_atual END) AS onibus,
    MAX(CASE WHEN segment_code = 'caminhoes_onibus' THEN mes_atual END) AS caminhoes_onibus,
    MAX(CASE WHEN segment_code = 'subtotal' THEN mes_atual END) AS subtotal,
    MAX(CASE WHEN segment_code = 'motos' THEN mes_atual END) AS motos,
    MAX(CASE WHEN segment_code = 'implementos_rodoviarios' THEN mes_atual END) AS implementos_rodoviarios,
    MAX(CASE WHEN segment_code = 'outros' THEN mes_atual END) AS outros,
    MAX(CASE WHEN segment_code = 'total' THEN mes_atual END) AS total_geral
  FROM segment_rows
)
SELECT
  'phase1_segment_presence' AS check_name,
  CASE
    WHEN COUNT(*) FILTER (
      WHERE segment_code IN (
        'autos',
        'comerciais_leves',
        'autos_comerciais_leves',
        'caminhoes',
        'onibus',
        'caminhoes_onibus'
      )
    ) = 6
     AND COUNT(DISTINCT segment_code) FILTER (
      WHERE segment_code IN (
        'autos',
        'comerciais_leves',
        'autos_comerciais_leves',
        'caminhoes',
        'onibus',
        'caminhoes_onibus'
      )
    ) = 6
    THEN 'passed'
    ELSE 'failed'
  END AS check_status,
  COUNT(*) AS segment_rows_loaded,
  STRING_AGG(segment_code, ', ' ORDER BY segment_code) AS segment_codes
FROM segment_rows;

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_file AS (
  SELECT f.id AS source_file_id
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
  ORDER BY f.id DESC
  LIMIT 1
),
segment_rows AS (
  SELECT
    segment_code,
    mes_atual
  FROM public.market_vehicle_registrations_segment s
  JOIN selected_file f
    ON f.source_file_id = s.source_file_id
),
totals AS (
  SELECT
    MAX(CASE WHEN segment_code = 'autos' THEN mes_atual END) AS autos,
    MAX(CASE WHEN segment_code = 'comerciais_leves' THEN mes_atual END) AS comerciais_leves,
    MAX(CASE WHEN segment_code = 'autos_comerciais_leves' THEN mes_atual END) AS autos_comerciais_leves,
    MAX(CASE WHEN segment_code = 'caminhoes' THEN mes_atual END) AS caminhoes,
    MAX(CASE WHEN segment_code = 'onibus' THEN mes_atual END) AS onibus,
    MAX(CASE WHEN segment_code = 'caminhoes_onibus' THEN mes_atual END) AS caminhoes_onibus,
    MAX(CASE WHEN segment_code = 'subtotal' THEN mes_atual END) AS subtotal,
    MAX(CASE WHEN segment_code = 'motos' THEN mes_atual END) AS motos,
    MAX(CASE WHEN segment_code = 'implementos_rodoviarios' THEN mes_atual END) AS implementos_rodoviarios,
    MAX(CASE WHEN segment_code = 'outros' THEN mes_atual END) AS outros,
    MAX(CASE WHEN segment_code = 'total' THEN mes_atual END) AS total_geral
  FROM segment_rows
)
SELECT
  check_name,
  check_status,
  calculated_value,
  expected_value,
  difference
FROM (
  SELECT
    'autos_plus_comerciais_leves' AS check_name,
    CASE
      WHEN autos IS NULL OR comerciais_leves IS NULL OR autos_comerciais_leves IS NULL THEN 'failed'
      WHEN autos + comerciais_leves = autos_comerciais_leves THEN 'passed'
      ELSE 'failed'
    END AS check_status,
    autos + comerciais_leves AS calculated_value,
    autos_comerciais_leves AS expected_value,
    (autos + comerciais_leves) - autos_comerciais_leves AS difference
  FROM totals

  UNION ALL

  SELECT
    'caminhoes_plus_onibus',
    CASE
      WHEN caminhoes IS NULL OR onibus IS NULL OR caminhoes_onibus IS NULL THEN 'failed'
      WHEN caminhoes + onibus = caminhoes_onibus THEN 'passed'
      ELSE 'failed'
    END,
    caminhoes + onibus,
    caminhoes_onibus,
    (caminhoes + onibus) - caminhoes_onibus
  FROM totals

  UNION ALL

  SELECT
    'subtotal_plus_outros_vs_total',
    CASE
      WHEN subtotal IS NULL OR motos IS NULL OR implementos_rodoviarios IS NULL OR outros IS NULL OR total_geral IS NULL THEN 'warning'
      WHEN subtotal + motos + implementos_rodoviarios + outros = total_geral THEN 'passed'
      ELSE 'failed'
    END,
    subtotal + motos + implementos_rodoviarios + outros,
    total_geral,
    (subtotal + motos + implementos_rodoviarios + outros) - total_geral
  FROM totals
) checks
ORDER BY check_name;

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_file AS (
  SELECT f.id AS source_file_id
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
  ORDER BY f.id DESC
  LIMIT 1
),
pair_checks AS (
  SELECT
    'item1_vs_item2' AS check_name,
    a.reference_period,
    a.vehicle_category,
    SUM(a.monthly_units) AS current_total,
    SUM(b.monthly_units) AS compare_total,
    CASE WHEN SUM(b.monthly_units) >= SUM(a.monthly_units) THEN 'passed' ELSE 'failed' END AS check_status
  FROM public.market_vehicle_model_rankings a
  JOIN public.market_vehicle_model_rankings b
    ON b.source_file_id = a.source_file_id
   AND b.vehicle_category = a.vehicle_category
   AND b.item_code = 'fenabrave_item_02_ranking_emplacamentos_acumulado'
  JOIN selected_file f
    ON f.source_file_id = a.source_file_id
  WHERE a.item_code = 'fenabrave_item_01_ranking_emplacamentos_mes'
  GROUP BY a.reference_period, a.vehicle_category

  UNION ALL

  SELECT
    'item3_vs_item4',
    a.reference_period,
    a.vehicle_category,
    SUM(a.units) AS current_total,
    SUM(b.units) AS compare_total,
    CASE WHEN SUM(b.units) >= SUM(a.units) THEN 'passed' ELSE 'failed' END
  FROM public.market_vehicle_brand_rankings a
  JOIN public.market_vehicle_brand_rankings b
    ON b.source_file_id = a.source_file_id
   AND b.vehicle_category = a.vehicle_category
   AND b.item_code = 'fenabrave_item_04_ranking_por_marca_acumulado'
  JOIN selected_file f
    ON f.source_file_id = a.source_file_id
  WHERE a.item_code = 'fenabrave_item_03_ranking_por_marca_mes'
  GROUP BY a.reference_period, a.vehicle_category

  UNION ALL

  SELECT
    'item13_vs_item14',
    a.reference_period,
    a.vehicle_category,
    SUM(a.market_share_pct) AS current_total,
    SUM(b.market_share_pct) AS compare_total,
    CASE WHEN SUM(b.market_share_pct) >= SUM(a.market_share_pct) THEN 'passed' ELSE 'failed' END
  FROM public.market_vehicle_brand_rankings a
  JOIN public.market_vehicle_brand_rankings b
    ON b.source_file_id = a.source_file_id
   AND b.vehicle_category = a.vehicle_category
   AND b.item_code = 'fenabrave_item_14_ranking_marca_emplacamento_varejo_acumulado'
  JOIN selected_file f
    ON f.source_file_id = a.source_file_id
  WHERE a.item_code = 'fenabrave_item_13_ranking_marca_emplacamento_varejo_mes'
  GROUP BY a.reference_period, a.vehicle_category

  UNION ALL

  SELECT
    'item15_vs_item16',
    a.reference_period,
    a.vehicle_category,
    SUM(a.market_share_pct) AS current_total,
    SUM(b.market_share_pct) AS compare_total,
    CASE WHEN SUM(b.market_share_pct) >= SUM(a.market_share_pct) THEN 'passed' ELSE 'failed' END
  FROM public.market_vehicle_brand_rankings a
  JOIN public.market_vehicle_brand_rankings b
    ON b.source_file_id = a.source_file_id
   AND b.vehicle_category = a.vehicle_category
   AND b.item_code = 'fenabrave_item_16_ranking_marca_emplacamento_direta_acumulado'
  JOIN selected_file f
    ON f.source_file_id = a.source_file_id
  WHERE a.item_code = 'fenabrave_item_15_ranking_marca_emplacamento_direta_mes'
  GROUP BY a.reference_period, a.vehicle_category

  UNION ALL

  SELECT
    'item17_vs_item18',
    a.reference_period,
    a.vehicle_category,
    SUM(a.market_share_pct) AS current_total,
    SUM(b.market_share_pct) AS compare_total,
    CASE WHEN SUM(b.market_share_pct) >= SUM(a.market_share_pct) THEN 'passed' ELSE 'failed' END
  FROM public.market_vehicle_brand_rankings a
  JOIN public.market_vehicle_brand_rankings b
    ON b.source_file_id = a.source_file_id
   AND b.vehicle_category = a.vehicle_category
   AND b.item_code = 'fenabrave_item_18_participacao_mercado_marca_acumulado'
  JOIN selected_file f
    ON f.source_file_id = a.source_file_id
  WHERE a.item_code = 'fenabrave_item_17_participacao_mercado_marca_mes'
  GROUP BY a.reference_period, a.vehicle_category

  UNION ALL

  SELECT
    'item19_vs_item21',
    a.reference_period,
    a.vehicle_category,
    SUM(a.monthly_units) AS current_total,
    SUM(b.monthly_units) AS compare_total,
    CASE WHEN SUM(b.monthly_units) >= SUM(a.monthly_units) THEN 'passed' ELSE 'failed' END
  FROM public.market_vehicle_model_rankings a
  JOIN public.market_vehicle_model_rankings b
    ON b.source_file_id = a.source_file_id
   AND b.vehicle_category = a.vehicle_category
   AND b.item_code = 'fenabrave_item_21_modelos_emplacados_venda_direta_acumulado'
  JOIN selected_file f
    ON f.source_file_id = a.source_file_id
  WHERE a.item_code = 'fenabrave_item_19_modelos_emplacados_venda_direta_mes'
  GROUP BY a.reference_period, a.vehicle_category

  UNION ALL

  SELECT
    'item20_vs_item22',
    a.reference_period,
    a.vehicle_category,
    SUM(a.monthly_units) AS current_total,
    SUM(b.monthly_units) AS compare_total,
    CASE WHEN SUM(b.monthly_units) >= SUM(a.monthly_units) THEN 'passed' ELSE 'failed' END
  FROM public.market_vehicle_model_rankings a
  JOIN public.market_vehicle_model_rankings b
    ON b.source_file_id = a.source_file_id
   AND b.vehicle_category = a.vehicle_category
   AND b.item_code = 'fenabrave_item_22_modelos_emplacados_varejo_acumulado'
  JOIN selected_file f
    ON f.source_file_id = a.source_file_id
  WHERE a.item_code = 'fenabrave_item_20_modelos_emplacados_varejo_mes'
  GROUP BY a.reference_period, a.vehicle_category
)
SELECT
  check_name,
  vehicle_category,
  current_total,
  compare_total,
  compare_total - current_total AS delta,
  check_status
FROM pair_checks
ORDER BY check_name, vehicle_category;

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_file AS (
  SELECT f.id AS source_file_id
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
  ORDER BY f.id DESC
  LIMIT 1
)
SELECT
  item_code,
  vehicle_category,
  ROUND(SUM(share_pct)::numeric, 4) AS total_share_pct,
  CASE
    WHEN ABS(SUM(share_pct) - 100) <= 0.5 THEN 'passed'
    ELSE 'failed'
  END AS check_status
FROM public.market_vehicle_sales_channel_mix m
JOIN selected_file f
  ON f.source_file_id = m.source_file_id
GROUP BY item_code, vehicle_category
ORDER BY item_code, vehicle_category;

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_file AS (
  SELECT f.id AS source_file_id
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
  ORDER BY f.id DESC
  LIMIT 1
)
SELECT
  'item5_current_month_total' AS check_name,
  ROUND(SUM(current_month_share_pct)::numeric, 4) AS total_share_pct,
  CASE WHEN SUM(current_month_share_pct) BETWEEN 99 AND 101 THEN 'passed' ELSE 'failed' END AS check_status
FROM public.market_vehicle_subsegment_shares s
JOIN selected_file f
  ON f.source_file_id = s.source_file_id
WHERE item_code = 'fenabrave_item_05_emplacamentos_por_subsegmento'

UNION ALL

SELECT
  'item5_current_year_total',
  ROUND(SUM(current_year_accum_share_pct)::numeric, 4),
  CASE WHEN SUM(current_year_accum_share_pct) BETWEEN 99 AND 101 THEN 'passed' ELSE 'failed' END
FROM public.market_vehicle_subsegment_shares s
JOIN selected_file f
  ON f.source_file_id = s.source_file_id
WHERE item_code = 'fenabrave_item_05_emplacamentos_por_subsegmento'

UNION ALL

SELECT
  'item5_prior_year_total',
  ROUND(SUM(prior_year_accum_share_pct)::numeric, 4),
  CASE WHEN SUM(prior_year_accum_share_pct) BETWEEN 99 AND 101 THEN 'passed' ELSE 'failed' END
FROM public.market_vehicle_subsegment_shares s
JOIN selected_file f
  ON f.source_file_id = s.source_file_id
WHERE item_code = 'fenabrave_item_05_emplacamentos_por_subsegmento';

WITH params AS (
  SELECT DATE '2026-07-01' AS target_period
),
fenabrave_source AS (
  SELECT id
  FROM public.market_data_sources
  WHERE source_name = 'Fenabrave'
),
selected_file AS (
  SELECT f.id AS source_file_id
  FROM public.market_source_files f
  JOIN fenabrave_source s
    ON s.id = f.source_id
  JOIN params p
    ON p.target_period = f.reference_period
  ORDER BY f.id DESC
  LIMIT 1
),
item6_market AS (
  SELECT
    vehicle_category,
    SUM(CASE WHEN powertrain_type = 'hybrid' THEN units ELSE 0 END) AS hybrid_units,
    SUM(CASE WHEN powertrain_type = 'electric' THEN units ELSE 0 END) AS electric_units,
    SUM(CASE WHEN powertrain_type = 'total_electrified' THEN units ELSE 0 END) AS total_units
  FROM public.market_vehicle_electrified_registrations e
  JOIN selected_file f
    ON f.source_file_id = e.source_file_id
  WHERE item_code = 'fenabrave_item_06_mercado_eletrificados_mes'
    AND aggregation_level = 'market'
  GROUP BY vehicle_category
)
SELECT
  vehicle_category,
  hybrid_units,
  electric_units,
  total_units,
  (hybrid_units + electric_units) AS recomputed_total,
  CASE
    WHEN hybrid_units + electric_units = total_units THEN 'passed'
    ELSE 'failed'
  END AS check_status
FROM item6_market
ORDER BY vehicle_category;
