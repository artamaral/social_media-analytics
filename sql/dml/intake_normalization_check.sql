-- intake_normalization_check.sql

-- Verificar como os nomes em entity_intake serão normalizados
-- antes da publicação. Esta query é útil para auditoria manual.
SELECT
  id,
  raw_name,
  normalized_name AS current_normalized_name,
  LOWER(TRIM(unaccent(raw_name))) AS recalculated_normalized_name,
  sub_niche_name,
  status
FROM public.entity_intake
ORDER BY created_at DESC, id DESC;
