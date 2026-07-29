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
  r.id,
  r.post_id,
  r.transcript_quality_score,
  r.transcript_quality_status,
  r.transcript_quality_impact,
  r.needs_retranscription
FROM public.video_classification_results r
WHERE (r.transcript_quality_score < 0 OR r.transcript_quality_score > 1)
   OR (
     r.transcript_quality_status IN ('poor', 'empty')
     AND NOT r.needs_retranscription
   )
   OR (
     r.transcript_quality_impact = 'medium'
     AND (NOT r.needs_human_review OR r.confidence_score > 0.69)
   )
   OR (
     r.transcript_quality_impact = 'high'
     AND (NOT r.needs_human_review OR r.confidence_score > 0.49)
   );


SELECT
  r.id,
  r.post_id,
  r.input_payload #>> '{video,transcript_90s}' AS persisted_transcript
FROM public.video_classification_results r
WHERE NULLIF(r.input_payload #>> '{video,transcript_90s}', '') IS NOT NULL;


SELECT
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'video_classification_vehicle_entities'
  AND column_name IN ('catalog_row_id', 'catalog_model_id', 'catalog_match_level')
ORDER BY column_name;


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
