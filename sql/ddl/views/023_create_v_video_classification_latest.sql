-- 023_create_v_video_classification_latest.sql

DROP VIEW IF EXISTS public.v_video_classification_latest;

-- Ultima classificacao disponivel por video e estagio.
CREATE VIEW public.v_video_classification_latest AS
WITH ranked_results AS (
  SELECT
    r.*,
    run.round_id,
    run.status AS run_status,
    run.started_at,
    run.completed_at,
    tv.taxonomy_version,
    ROW_NUMBER() OVER (
      PARTITION BY r.post_id, r.evaluation_stage
      ORDER BY COALESCE(run.completed_at, r.created_at) DESC, r.id DESC
    ) AS recency_rank
  FROM public.video_classification_results r
  JOIN public.video_classification_runs run
    ON run.id = r.run_id
  JOIN public.video_taxonomy_versions tv
    ON tv.id = r.taxonomy_version_id
)
SELECT
  -- Preserve existing column order: PostgreSQL only allows new view columns at the end.
  id,
  run_id,
  round_id,
  run_status,
  taxonomy_version_id,
  taxonomy_version,
  post_id,
  evaluation_stage,
  input_evidence_level,
  automotive_domain,
  activity_type,
  topic_path,
  topic_path_secondary,
  content_type,
  audience_intent,
  confidence_score,
  evidence_summary,
  taxonomy_gaps,
  validation_issues,
  needs_human_review,
  model_used,
  prompt_contract_version,
  output_schema_version,
  created_at,
  started_at,
  completed_at,
  transcript_quality_score,
  transcript_quality_status,
  transcript_quality_issues,
  transcript_quality_impact,
  needs_retranscription
FROM ranked_results
WHERE recency_rank = 1;

COMMENT ON VIEW public.v_video_classification_latest IS
  'Ultima classificacao GPT por post_id e estagio usando a Taxonomia Video V2.';


CREATE OR REPLACE VIEW public.v_video_classification_quality AS
SELECT
  -- Preserve existing column order: append new aggregate columns after distinct_topic_paths.
  tv.taxonomy_version,
  run.round_id,
  r.evaluation_stage,
  run.model_used,
  COUNT(*) AS classified_videos,
  COUNT(*) FILTER (WHERE r.needs_human_review) AS needs_human_review_count,
  COUNT(*) FILTER (WHERE NULLIF(BTRIM(COALESCE(r.taxonomy_gaps, '')), '') IS NOT NULL) AS taxonomy_gap_count,
  COUNT(*) FILTER (WHERE NULLIF(BTRIM(COALESCE(r.validation_issues, '')), '') IS NOT NULL) AS validation_issue_count,
  ROUND(AVG(r.confidence_score)::numeric, 3) AS avg_confidence_score,
  MIN(r.confidence_score) AS min_confidence_score,
  MAX(r.confidence_score) AS max_confidence_score,
  COUNT(DISTINCT r.topic_path) AS distinct_topic_paths,
  COUNT(*) FILTER (
    WHERE r.transcript_quality_status IN ('usable', 'partially_usable')
  ) AS usable_transcript_count,
  COUNT(*) FILTER (WHERE r.needs_retranscription) AS needs_retranscription_count,
  COUNT(*) FILTER (
    WHERE r.transcript_quality_impact = 'high'
  ) AS high_transcript_impact_count,
  ROUND(AVG(r.transcript_quality_score)::numeric, 3) AS avg_transcript_quality_score
FROM public.video_classification_results r
JOIN public.video_classification_runs run
  ON run.id = r.run_id
JOIN public.video_taxonomy_versions tv
  ON tv.id = r.taxonomy_version_id
GROUP BY
  tv.taxonomy_version,
  run.round_id,
  r.evaluation_stage,
  run.model_used;

COMMENT ON VIEW public.v_video_classification_quality IS
  'Resumo de qualidade das classificacoes GPT por rodada, estagio e versao de taxonomia.';
