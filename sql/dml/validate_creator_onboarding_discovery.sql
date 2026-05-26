-- validate_creator_onboarding_discovery.sql

-- Validacao operacional do worker de discovery inicial de creators.
-- Troque o valor de creator_id na CTE `params` antes de executar no Supabase.

WITH params AS (
  SELECT 55::integer AS creator_id
),
creator_base AS (
  SELECT
    p.creator_id,
    e.name::text AS entity_name,
    c.platform,
    c.username,
    c.channel_id,
    c.created_at AS creator_created_at
  FROM params p
  LEFT JOIN public.creators c ON c.id = p.creator_id
  LEFT JOIN public.entities e ON e.id = c.entity_id
),
post_counts AS (
  SELECT
    p.creator_id,
    count(*) AS posts_total,
    min(p.created_at) AS first_post_inserted_at,
    max(p.created_at) AS latest_post_inserted_at,
    max(p.post_date) AS latest_post_date
  FROM public.posts p
  JOIN params prm ON prm.creator_id = p.creator_id
  GROUP BY p.creator_id
),
queue_counts AS (
  SELECT
    p.creator_id,
    count(*) AS queue_total,
    count(*) FILTER (WHERE q.needs_update IS TRUE) AS queue_needs_update,
    min(q.next_check) AS first_next_check,
    max(q.next_check) AS latest_next_check
  FROM public.posts p
  JOIN public.post_update_queue q ON q.post_id = p.post_id
  JOIN params prm ON prm.creator_id = p.creator_id
  GROUP BY p.creator_id
),
history_counts AS (
  SELECT
    p.creator_id,
    count(h.post_id) AS snapshots_total,
    count(DISTINCT h.post_id) AS posts_with_snapshot
  FROM public.posts p
  LEFT JOIN public.post_metrics_history h ON h.post_id = p.post_id
  JOIN params prm ON prm.creator_id = p.creator_id
  GROUP BY p.creator_id
),
dashboard_view AS (
  SELECT
    v.creator_id,
    v.entity_name AS dashboard_entity_name,
    v.post_count AS dashboard_post_count,
    v.latest_post_date AS dashboard_latest_post_date
  FROM public.v_dashboard_creator_summary v
  JOIN params prm ON prm.creator_id = v.creator_id
)
SELECT
  cb.creator_id,
  cb.entity_name,
  cb.platform,
  cb.username,
  cb.channel_id,
  coalesce(pc.posts_total, 0) AS posts_total,
  coalesce(qc.queue_total, 0) AS queue_total,
  coalesce(qc.queue_needs_update, 0) AS queue_needs_update,
  coalesce(hc.snapshots_total, 0) AS snapshots_total,
  coalesce(hc.posts_with_snapshot, 0) AS posts_with_snapshot,
  dv.dashboard_post_count,
  pc.first_post_inserted_at,
  pc.latest_post_inserted_at,
  pc.latest_post_date,
  qc.first_next_check,
  qc.latest_next_check,
  dv.dashboard_latest_post_date,
  CASE
    WHEN cb.platform IS NULL THEN 'nok_creator_not_found'
    WHEN coalesce(pc.posts_total, 0) = 0 THEN 'nok_no_posts'
    WHEN coalesce(qc.queue_total, 0) = 0 THEN 'nok_no_queue'
    WHEN coalesce(dv.dashboard_post_count, 0) <> coalesce(pc.posts_total, 0) THEN 'atencao_dashboard_mismatch'
    ELSE 'ok'
  END AS validation_status
FROM creator_base cb
LEFT JOIN post_counts pc ON pc.creator_id = cb.creator_id
LEFT JOIN queue_counts qc ON qc.creator_id = cb.creator_id
LEFT JOIN history_counts hc ON hc.creator_id = cb.creator_id
LEFT JOIN dashboard_view dv ON dv.creator_id = cb.creator_id;

-- Amostra dos posts descobertos e status na fila.
WITH params AS (
  SELECT 55::integer AS creator_id
)
SELECT
  p.creator_id,
  p.post_id,
  p.title,
  p.post_date,
  p.created_at AS post_inserted_at,
  q.needs_update,
  q.next_check,
  q.priority_score
FROM public.posts p
LEFT JOIN public.post_update_queue q ON q.post_id = p.post_id
JOIN params prm ON prm.creator_id = p.creator_id
ORDER BY p.created_at DESC, p.post_date DESC
LIMIT 50;

-- Validacao direta da view consumida pelo Streamlit.
WITH params AS (
  SELECT 55::integer AS creator_id
)
SELECT
  creator_id,
  entity_name,
  username,
  channel_id,
  post_count,
  total_views,
  latest_post_date,
  latest_collected_at,
  is_active
FROM public.v_dashboard_creator_summary v
JOIN params prm USING (creator_id);
