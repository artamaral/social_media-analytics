-- Valida os itens 13 e 14 da fase 2 Fenabrave:
-- ranking por marca de emplacamento varejo, mensal e acumulado.
SELECT
  item_code,
  published_period_type,
  vehicle_category,
  COUNT(*) AS total_rows,
  MIN(rank_position) AS min_rank,
  MAX(rank_position) AS max_rank,
  COUNT(DISTINCT rank_position) AS distinct_ranks,
  SUM(CASE WHEN units IS NOT NULL THEN 1 ELSE 0 END) AS rows_with_units,
  SUM(CASE WHEN market_share_pct IS NULL OR market_share_pct < 0 OR market_share_pct > 100 THEN 1 ELSE 0 END)
    AS invalid_share_rows
FROM public.market_vehicle_brand_rankings
WHERE item_code IN (
  'fenabrave_item_13_ranking_marca_emplacamento_varejo_mes',
  'fenabrave_item_14_ranking_marca_emplacamento_varejo_acumulado'
)
GROUP BY
  item_code,
  published_period_type,
  vehicle_category
ORDER BY
  item_code,
  vehicle_category;
