CREATE OR REPLACE VIEW public.v_dashboard_creator_weekly_timeseries AS
WITH base_history AS (
  SELECT
    c.id AS creator_id,
    e.id AS entity_id,
    e.name::text AS entity_name,
    c.platform,
    p.post_id,
    h.id AS history_id,
    h.collected_at,
    DATE_TRUNC('week', h.collected_at)::date AS week_start,
    (DATE_TRUNC('week', h.collected_at)::date + 6) AS week_end,
    h.views,
    h.likes,
    h.comments
  FROM public.post_metrics_history h
  JOIN public.posts p ON p.post_id = h.post_id
  JOIN public.creators c ON c.id = p.creator_id
  JOIN public.entities e ON e.id = c.entity_id
  WHERE h.collected_at IS NOT NULL
    AND p.creator_id IS NOT NULL
),
completed_week_history AS (
  SELECT *
  FROM base_history
  WHERE week_end < (TIMEZONE('America/Sao_Paulo', NOW()))::date
),
weekly_post_latest AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    post_id,
    week_start,
    week_end,
    collected_at,
    views,
    likes,
    comments
  FROM (
    SELECT
      ch.*,
      ROW_NUMBER() OVER (
        PARTITION BY ch.post_id, ch.week_start
        ORDER BY ch.collected_at DESC, ch.history_id DESC
      ) AS row_num
    FROM completed_week_history ch
  ) ranked
  WHERE row_num = 1
),
creator_week_rollup AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    week_start,
    week_end,
    TO_CHAR(week_start, 'DD/MM/YYYY') || '-' || TO_CHAR(week_end, 'DD/MM/YYYY') AS week_label,
    COALESCE(SUM(views), 0) AS views_week_end,
    COALESCE(SUM(likes), 0) AS likes_week_end,
    COALESCE(SUM(comments), 0) AS comments_week_end,
    COUNT(DISTINCT post_id) AS active_posts_in_week
  FROM weekly_post_latest
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    week_start,
    week_end
),
creator_week_with_previous AS (
  SELECT
    cwr.*,
    LAG(views_week_end) OVER (
      PARTITION BY creator_id
      ORDER BY week_start
    ) AS previous_views_week_end,
    LAG(likes_week_end) OVER (
      PARTITION BY creator_id
      ORDER BY week_start
    ) AS previous_likes_week_end,
    LAG(comments_week_end) OVER (
      PARTITION BY creator_id
      ORDER BY week_start
    ) AS previous_comments_week_end
  FROM creator_week_rollup cwr
)
SELECT
  creator_id,
  entity_id,
  entity_name,
  platform,
  week_start,
  week_end,
  week_label,
  views_week_end,
  views_week_end - previous_views_week_end AS views_delta_vs_prev_week,
  CASE
    WHEN previous_views_week_end IS NOT NULL AND previous_views_week_end > 0
      THEN ROUND(((views_week_end - previous_views_week_end)::numeric / previous_views_week_end::numeric) * 100, 4)
    ELSE NULL
  END AS views_growth_pct_vs_prev_week,
  likes_week_end,
  likes_week_end - previous_likes_week_end AS likes_delta_vs_prev_week,
  comments_week_end,
  comments_week_end - previous_comments_week_end AS comments_delta_vs_prev_week,
  active_posts_in_week
FROM creator_week_with_previous;

GRANT SELECT ON public.v_dashboard_creator_weekly_timeseries TO anon;
GRANT SELECT ON public.v_dashboard_creator_weekly_timeseries TO authenticated;
