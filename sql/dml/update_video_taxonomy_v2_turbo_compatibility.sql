-- update_video_taxonomy_v2_turbo_compatibility.sql

-- Ajuste pontual da Taxonomia Video V2:
-- turbo e componente/feature de powertrain, nao problem.

BEGIN;

WITH tv AS (
  SELECT id
  FROM public.video_taxonomy_versions
  WHERE taxonomy_version = 'taxonomia_video_v2'
)
UPDATE public.video_taxonomy_technical_compatibility c
SET
  automotive_system = 'motor',
  component = 'turbo',
  problem = NULL,
  compatibility_status = 'allowed_with_evidence',
  validation_rule = CASE c.compatibility_id
    WHEN 'cmp_092' THEN 'Turbo entra como componente/feature do review, sem problem e sem deslocar o topic_path principal.'
    WHEN 'cmp_103' THEN 'Turbo entra como componente/feature de powertrain, sem problem e sem virar rotulo solto.'
    ELSE c.validation_rule
  END,
  source_row = jsonb_set(
    jsonb_set(
      jsonb_set(
        COALESCE(c.source_row, '{}'::jsonb),
        '{component}',
        to_jsonb('turbo'::text),
        true
      ),
      '{problem}',
      to_jsonb(''::text),
      true
    ),
    '{validation_rule}',
    to_jsonb(CASE c.compatibility_id
      WHEN 'cmp_092' THEN 'Turbo entra como componente/feature do review, sem problem e sem deslocar o topic_path principal.'
      WHEN 'cmp_103' THEN 'Turbo entra como componente/feature de powertrain, sem problem e sem virar rotulo solto.'
      ELSE c.validation_rule
    END),
    true
  ),
  updated_at = now()
FROM tv
WHERE c.taxonomy_version_id = tv.id
  AND c.compatibility_id IN ('cmp_092', 'cmp_103');

UPDATE public.video_taxonomy_versions
SET
  source_compatibility_sha256 = '879A312E9A43A1C71776B04BCF8BD15ADDE37FC87A5B896C71F214664EB064FD'
WHERE taxonomy_version = 'taxonomia_video_v2';

COMMIT;
