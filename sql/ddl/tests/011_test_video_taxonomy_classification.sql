-- 011_test_video_taxonomy_classification.sql

-- Validacoes basicas apos aplicar a DDL e carregar a Taxonomia Video V2.
-- Esta bateria nao executa chamada GPT nem ingestao.

SELECT
  taxonomy_version,
  status,
  source_topic_paths_file,
  source_compatibility_file
FROM public.video_taxonomy_versions
ORDER BY created_at DESC;


SELECT
  tv.taxonomy_version,
  COUNT(*) AS topic_path_count
FROM public.video_taxonomy_topic_paths tp
JOIN public.video_taxonomy_versions tv
  ON tv.id = tp.taxonomy_version_id
GROUP BY tv.taxonomy_version
ORDER BY tv.taxonomy_version;


SELECT
  tv.taxonomy_version,
  COUNT(*) AS compatibility_count
FROM public.video_taxonomy_technical_compatibility c
JOIN public.video_taxonomy_versions tv
  ON tv.id = c.taxonomy_version_id
GROUP BY tv.taxonomy_version
ORDER BY tv.taxonomy_version;


SELECT
  tp.topic_path_code
FROM public.video_taxonomy_topic_paths tp
WHERE tp.topic_path_code IN (
  'motor',
  'cambio',
  'off_road__4x4',
  'diagnostico__ruido_barulho',
  'motorhome',
  'carros_descartaveis'
);


SELECT
  c.compatibility_id,
  c.problem
FROM public.video_taxonomy_technical_compatibility c
WHERE c.problem = 'barulho';


SELECT
  r.id,
  r.post_id,
  r.confidence_score
FROM public.video_classification_results r
WHERE r.confidence_score < 0
   OR r.confidence_score > 1;


SELECT
  c.id,
  r.post_id,
  c.automotive_system,
  c.component,
  c.problem
FROM public.video_classification_technical_contexts c
JOIN public.video_classification_results r
  ON r.id = c.classification_result_id
WHERE COALESCE(c.automotive_system, '') LIKE '%;%'
   OR COALESCE(c.component, '') LIKE '%;%'
   OR COALESCE(c.problem, '') LIKE '%;%';


SELECT
  c.id,
  r.post_id,
  r.topic_path,
  c.context_role
FROM public.video_classification_technical_contexts c
JOIN public.video_classification_results r
  ON r.id = c.classification_result_id
WHERE r.topic_path LIKE 'fora_escopo%'
  AND c.context_role = 'primary';


SELECT
  *
FROM public.v_video_classification_quality
ORDER BY
  taxonomy_version,
  round_id,
  evaluation_stage;
