CREATE OR REPLACE VIEW public.v_dashboard_creator_weekly_activity AS
WITH creator_posts AS (
  SELECT
    c.id AS creator_id,
    e.id AS entity_id,
    e.name::text AS entity_name,
    c.platform,
    p.post_id,
    p.video_type,
    p.post_date::date AS post_date
  FROM public.posts p
  JOIN public.creators c ON c.id = p.creator_id
  JOIN public.entities e ON e.id = c.entity_id
  WHERE p.creator_id IS NOT NULL
),
closed_history_snapshots AS (
  SELECT
    cp.creator_id,
    cp.entity_id,
    cp.entity_name,
    cp.platform,
    cp.post_id,
    cp.video_type,
    cp.post_date,
    DATE_TRUNC('week', h.collected_at)::date AS week_start,
    (DATE_TRUNC('week', h.collected_at)::date + 6) AS week_end,
    h.id AS history_id,
    h.collected_at,
    COALESCE(h.views, 0) AS views,
    COALESCE(h.likes, 0) AS likes,
    COALESCE(h.comments, 0) AS comments
  FROM public.post_metrics_history h
  JOIN creator_posts cp ON cp.post_id = h.post_id
  WHERE h.collected_at IS NOT NULL
    AND (DATE_TRUNC('week', h.collected_at)::date + 6) < (TIMEZONE('America/Sao_Paulo', NOW()))::date
),
weekly_post_latest AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    post_id,
    video_type,
    post_date,
    week_start,
    week_end,
    collected_at,
    views,
    likes,
    comments
  FROM (
    SELECT
      chs.*,
      ROW_NUMBER() OVER (
        PARTITION BY chs.creator_id, chs.post_id, chs.week_start
        ORDER BY chs.collected_at DESC, chs.history_id DESC
      ) AS row_num
    FROM closed_history_snapshots chs
  ) ranked
  WHERE row_num = 1
),
post_week_delta AS (
  SELECT
    wpl.creator_id,
    wpl.entity_id,
    wpl.entity_name,
    wpl.platform,
    wpl.post_id,
    wpl.video_type,
    wpl.week_start,
    wpl.week_end,
    CASE
      WHEN baseline.post_id IS NOT NULL THEN wpl.views - baseline.views
      WHEN wpl.post_date BETWEEN wpl.week_start AND wpl.week_end THEN wpl.views
      ELSE NULL
    END AS views_novas,
    CASE
      WHEN baseline.post_id IS NOT NULL THEN wpl.likes - baseline.likes
      WHEN wpl.post_date BETWEEN wpl.week_start AND wpl.week_end THEN wpl.likes
      ELSE NULL
    END AS likes_novos,
    CASE
      WHEN baseline.post_id IS NOT NULL THEN wpl.comments - baseline.comments
      WHEN wpl.post_date BETWEEN wpl.week_start AND wpl.week_end THEN wpl.comments
      ELSE NULL
    END AS comentarios_novos,
    CASE
      WHEN baseline.post_id IS NULL
        AND NOT (wpl.post_date BETWEEN wpl.week_start AND wpl.week_end)
        THEN 1
      ELSE 0
    END AS sem_baseline_para_delta
  FROM weekly_post_latest wpl
  LEFT JOIN LATERAL (
    SELECT
      h.post_id,
      COALESCE(h.views, 0) AS views,
      COALESCE(h.likes, 0) AS likes,
      COALESCE(h.comments, 0) AS comments
    FROM public.post_metrics_history h
    WHERE h.post_id = wpl.post_id
      AND h.collected_at < wpl.week_start
    ORDER BY h.collected_at DESC, h.id DESC
    LIMIT 1
  ) baseline ON TRUE
),
movement_by_type AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    week_start,
    week_end,
    COUNT(DISTINCT post_id) AS posts_com_snapshot_na_semana,
    SUM(sem_baseline_para_delta) AS posts_sem_baseline_para_delta,
    COALESCE(SUM(views_novas), 0) AS views_novas,
    COALESCE(SUM(likes_novos), 0) AS likes_novos,
    COALESCE(SUM(comentarios_novos), 0) AS comentarios_novos
  FROM post_week_delta
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    video_type,
    week_start,
    week_end
),
movement_all AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    'todos'::text AS video_type,
    week_start,
    week_end,
    SUM(posts_com_snapshot_na_semana) AS posts_com_snapshot_na_semana,
    SUM(posts_sem_baseline_para_delta) AS posts_sem_baseline_para_delta,
    SUM(views_novas) AS views_novas,
    SUM(likes_novos) AS likes_novos,
    SUM(comentarios_novos) AS comentarios_novos
  FROM movement_by_type
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    week_start,
    week_end
),
movement_rollup AS (
  SELECT * FROM movement_by_type
  UNION ALL
  SELECT * FROM movement_all
),
published_by_type AS (
  SELECT
    cp.creator_id,
    cp.entity_id,
    cp.entity_name,
    cp.platform,
    cp.video_type,
    DATE_TRUNC('week', cp.post_date)::date AS week_start,
    (DATE_TRUNC('week', cp.post_date)::date + 6) AS week_end,
    COUNT(*) AS videos_publicados
  FROM creator_posts cp
  WHERE cp.post_date IS NOT NULL
    AND (DATE_TRUNC('week', cp.post_date)::date + 6) < (TIMEZONE('America/Sao_Paulo', NOW()))::date
  GROUP BY
    cp.creator_id,
    cp.entity_id,
    cp.entity_name,
    cp.platform,
    cp.video_type,
    DATE_TRUNC('week', cp.post_date)::date,
    (DATE_TRUNC('week', cp.post_date)::date + 6)
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
    SUM(videos_publicados) AS videos_publicados
  FROM published_by_type
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    week_start,
    week_end
),
published_rollup AS (
  SELECT * FROM published_by_type
  UNION ALL
  SELECT * FROM published_all
),
activity_base AS (
  SELECT
    COALESCE(m.creator_id, p.creator_id) AS creator_id,
    COALESCE(m.entity_id, p.entity_id) AS entity_id,
    COALESCE(m.entity_name, p.entity_name) AS entity_name,
    COALESCE(m.platform, p.platform) AS platform,
    COALESCE(m.video_type, p.video_type) AS video_type,
    COALESCE(m.week_start, p.week_start) AS week_start,
    COALESCE(m.week_end, p.week_end) AS week_end,
    COALESCE(p.videos_publicados, 0) AS videos_publicados,
    COALESCE(m.views_novas, 0) AS views_novas,
    COALESCE(m.likes_novos, 0) AS likes_novos,
    COALESCE(m.comentarios_novos, 0) AS comentarios_novos,
    COALESCE(m.posts_com_snapshot_na_semana, 0) AS posts_com_snapshot_na_semana,
    COALESCE(m.posts_sem_baseline_para_delta, 0) AS posts_sem_baseline_para_delta
  FROM movement_rollup m
  FULL OUTER JOIN published_rollup p
    ON p.creator_id = m.creator_id
   AND p.video_type = m.video_type
   AND p.week_start = m.week_start
   AND p.week_end = m.week_end
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
FROM activity_base;

GRANT SELECT ON public.v_dashboard_creator_weekly_activity TO anon;
GRANT SELECT ON public.v_dashboard_creator_weekly_activity TO authenticated;
