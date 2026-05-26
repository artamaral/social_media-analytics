DROP VIEW IF EXISTS public.v_dashboard_creator_weekly_activity;

CREATE VIEW public.v_dashboard_creator_weekly_activity AS
WITH creator_posts AS (
  SELECT
    c.id AS creator_id,
    e.id AS entity_id,
    e.name::text AS entity_name,
    c.platform,
    p.post_id,
    COALESCE(NULLIF(p.video_type, ''), 'sem_tipo')::text AS video_type,
    p.post_date::date AS post_date
  FROM public.posts p
  JOIN public.creators c ON c.id = p.creator_id
  JOIN public.entities e ON e.id = c.entity_id
  WHERE p.creator_id IS NOT NULL
),
published_by_type AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    DATE_TRUNC('week', post_date)::date AS week_start,
    (DATE_TRUNC('week', post_date)::date + 6) AS week_end,
    COUNT(*)::numeric AS videos_publicados
  FROM creator_posts
  WHERE post_date IS NOT NULL
    AND (DATE_TRUNC('week', post_date)::date + 6) < (TIMEZONE('America/Sao_Paulo', NOW()))::date
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    DATE_TRUNC('week', post_date)::date,
    (DATE_TRUNC('week', post_date)::date + 6)
),
metric_snapshots AS (
  SELECT
    cp.creator_id,
    cp.entity_id,
    cp.entity_name,
    cp.platform,
    cp.video_type,
    cp.post_id,
    DATE_TRUNC('week', (pmh.collected_at - INTERVAL '3 hours'))::date AS week_start,
    (DATE_TRUNC('week', (pmh.collected_at - INTERVAL '3 hours'))::date + 6) AS week_end,
    pmh.collected_at,
    COALESCE(pmh.views, 0) AS views,
    COALESCE(pmh.likes, 0) AS likes,
    COALESCE(pmh.comments, 0) AS comments,
    ROW_NUMBER() OVER (
      PARTITION BY cp.post_id, DATE_TRUNC('week', (pmh.collected_at - INTERVAL '3 hours'))::date
      ORDER BY pmh.collected_at ASC
    ) AS rn_first,
    ROW_NUMBER() OVER (
      PARTITION BY cp.post_id, DATE_TRUNC('week', (pmh.collected_at - INTERVAL '3 hours'))::date
      ORDER BY pmh.collected_at DESC
    ) AS rn_last
  FROM public.post_metrics_history pmh
  JOIN creator_posts cp ON cp.post_id = pmh.post_id
  WHERE pmh.collected_at IS NOT NULL
    AND (DATE_TRUNC('week', (pmh.collected_at - INTERVAL '3 hours'))::date + 6) < (TIMEZONE('America/Sao_Paulo', NOW()))::date
),
metric_per_post_week AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    post_id,
    week_start,
    week_end,
    COUNT(*)::numeric AS snapshots_na_semana,
    MAX(views) FILTER (WHERE rn_first = 1) AS first_views,
    MAX(views) FILTER (WHERE rn_last = 1) AS last_views,
    MAX(likes) FILTER (WHERE rn_first = 1) AS first_likes,
    MAX(likes) FILTER (WHERE rn_last = 1) AS last_likes,
    MAX(comments) FILTER (WHERE rn_first = 1) AS first_comments,
    MAX(comments) FILTER (WHERE rn_last = 1) AS last_comments
  FROM metric_snapshots
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    post_id,
    week_start,
    week_end
),
metric_by_type AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    week_start,
    week_end,
    SUM(
      CASE
        WHEN snapshots_na_semana >= 2 THEN GREATEST(last_views - first_views, 0)
      END
    )::numeric AS views_novas,
    SUM(
      CASE
        WHEN snapshots_na_semana >= 2 THEN GREATEST(last_likes - first_likes, 0)
      END
    )::numeric AS likes_novos,
    SUM(
      CASE
        WHEN snapshots_na_semana >= 2 THEN GREATEST(last_comments - first_comments, 0)
      END
    )::numeric AS comentarios_novos,
    COUNT(*)::numeric AS posts_com_snapshot_na_semana,
    COUNT(*) FILTER (WHERE snapshots_na_semana < 2)::numeric AS posts_sem_baseline_para_delta,
    COUNT(*) FILTER (WHERE snapshots_na_semana >= 2)::numeric AS posts_com_base_para_delta,
    SUM(snapshots_na_semana)::numeric AS snapshots_na_semana
  FROM metric_per_post_week
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    week_start,
    week_end
),
typed_week_keys AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    week_start,
    week_end
  FROM published_by_type
  UNION
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    week_start,
    week_end
  FROM metric_by_type
),
typed_week_activity AS (
  SELECT
    k.creator_id,
    k.entity_id,
    k.entity_name,
    k.platform,
    k.video_type,
    k.week_start,
    k.week_end,
    COALESCE(p.videos_publicados, 0)::numeric AS videos_publicados,
    m.views_novas,
    m.likes_novos,
    m.comentarios_novos,
    COALESCE(m.posts_com_snapshot_na_semana, 0)::numeric AS posts_com_snapshot_na_semana,
    COALESCE(m.posts_sem_baseline_para_delta, 0)::numeric AS posts_sem_baseline_para_delta,
    COALESCE(m.posts_com_base_para_delta, 0)::numeric AS posts_com_base_para_delta,
    COALESCE(m.snapshots_na_semana, 0)::numeric AS snapshots_na_semana
  FROM typed_week_keys k
  LEFT JOIN published_by_type p
    ON p.creator_id = k.creator_id
   AND p.video_type = k.video_type
   AND p.week_start = k.week_start
  LEFT JOIN metric_by_type m
    ON m.creator_id = k.creator_id
   AND m.video_type = k.video_type
   AND m.week_start = k.week_start
),
all_week_activity AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    'todos'::text AS video_type,
    week_start,
    week_end,
    SUM(videos_publicados)::numeric AS videos_publicados,
    CASE WHEN SUM(posts_com_base_para_delta) > 0 THEN SUM(COALESCE(views_novas, 0))::numeric END AS views_novas,
    CASE WHEN SUM(posts_com_base_para_delta) > 0 THEN SUM(COALESCE(likes_novos, 0))::numeric END AS likes_novos,
    CASE WHEN SUM(posts_com_base_para_delta) > 0 THEN SUM(COALESCE(comentarios_novos, 0))::numeric END AS comentarios_novos,
    SUM(posts_com_snapshot_na_semana)::numeric AS posts_com_snapshot_na_semana,
    SUM(posts_sem_baseline_para_delta)::numeric AS posts_sem_baseline_para_delta,
    SUM(posts_com_base_para_delta)::numeric AS posts_com_base_para_delta,
    SUM(snapshots_na_semana)::numeric AS snapshots_na_semana
  FROM typed_week_activity
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    week_start,
    week_end
),
weekly_activity AS (
  SELECT * FROM typed_week_activity
  UNION ALL
  SELECT * FROM all_week_activity
)
SELECT
  creator_id,
  entity_id,
  entity_name,
  platform,
  video_type,
  week_start,
  week_end,
  TO_CHAR(week_start, 'DD/MM/YYYY') || '-' || TO_CHAR(week_end, 'DD/MM/YYYY') AS week_label,
  videos_publicados,
  views_novas,
  CASE
    WHEN views_novas IS NOT NULL
      AND LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start) > 0
      THEN ROUND(
        ((views_novas - LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start))::numeric
        / LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start)::numeric) * 100,
        4
      )
    ELSE NULL
  END AS views_growth_pct_vs_prev_week,
  likes_novos,
  comentarios_novos,
  posts_com_snapshot_na_semana,
  posts_sem_baseline_para_delta,
  CASE
    WHEN posts_com_base_para_delta <= 0 THEN 'sem_base'
    WHEN views_novas > LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start) THEN 'alta'
    WHEN views_novas < LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start) THEN 'queda'
    WHEN LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start) IS NULL THEN 'sem_base'
    ELSE 'estavel'
  END AS week_status,
  posts_com_base_para_delta,
  snapshots_na_semana,
  (posts_com_base_para_delta > 0) AS semana_tem_base
FROM weekly_activity;

GRANT SELECT ON public.v_dashboard_creator_weekly_activity TO anon;
GRANT SELECT ON public.v_dashboard_creator_weekly_activity TO authenticated;
