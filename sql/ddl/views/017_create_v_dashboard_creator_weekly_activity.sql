CREATE OR REPLACE VIEW public.v_dashboard_creator_weekly_activity AS
WITH creator_posts AS (
  SELECT
    c.id AS creator_id,
    e.id AS entity_id,
    e.name::text AS entity_name,
    c.platform,
    p.post_id,
    COALESCE(NULLIF(p.video_type, ''), 'sem_tipo')::text AS video_type,
    p.post_date::date AS post_date,
    COALESCE(p.views, 0) AS views,
    COALESCE(p.likes, 0) AS likes,
    COALESCE(p.comments, 0) AS comments,
    p.collected_at
  FROM public.posts p
  JOIN public.creators c ON c.id = p.creator_id
  JOIN public.entities e ON e.id = c.entity_id
  WHERE p.creator_id IS NOT NULL
    AND p.post_date IS NOT NULL
    AND (DATE_TRUNC('week', p.post_date)::date + 6) < (TIMEZONE('America/Sao_Paulo', NOW()))::date
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
    COUNT(*)::numeric AS videos_publicados,
    SUM(views)::numeric AS views_novas,
    SUM(likes)::numeric AS likes_novos,
    SUM(comments)::numeric AS comentarios_novos,
    COUNT(*) FILTER (WHERE collected_at IS NOT NULL)::numeric AS posts_com_snapshot_na_semana,
    0::numeric AS posts_sem_baseline_para_delta
  FROM creator_posts
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    DATE_TRUNC('week', post_date)::date,
    (DATE_TRUNC('week', post_date)::date + 6)
),
published_all AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    'todos'::text AS video_type,
    week_start,
    week_end,
    SUM(videos_publicados)::numeric AS videos_publicados,
    SUM(views_novas)::numeric AS views_novas,
    SUM(likes_novos)::numeric AS likes_novos,
    SUM(comentarios_novos)::numeric AS comentarios_novos,
    SUM(posts_com_snapshot_na_semana)::numeric AS posts_com_snapshot_na_semana,
    0::numeric AS posts_sem_baseline_para_delta
  FROM published_by_type
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    week_start,
    week_end
),
weekly_activity AS (
  SELECT * FROM published_by_type
  UNION ALL
  SELECT * FROM published_all
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
    WHEN LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start) > 0
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
    WHEN views_novas > LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start) THEN 'alta'
    WHEN views_novas < LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start) THEN 'queda'
    WHEN LAG(views_novas) OVER (PARTITION BY creator_id, video_type ORDER BY week_start) IS NULL THEN 'sem_base'
    ELSE 'estavel'
  END AS week_status
FROM weekly_activity;

GRANT SELECT ON public.v_dashboard_creator_weekly_activity TO anon;
GRANT SELECT ON public.v_dashboard_creator_weekly_activity TO authenticated;
