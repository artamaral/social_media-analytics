CREATE OR REPLACE VIEW public.v_dashboard_post_growth_7d AS
WITH windowed_history AS (
  SELECT
    h.post_id,
    h.collected_at,
    h.views,
    h.likes,
    h.comments
  FROM public.post_metrics_history h
  WHERE h.collected_at >= NOW() - INTERVAL '7 days'
),
first_snapshot AS (
  SELECT DISTINCT ON (wh.post_id)
    wh.post_id,
    wh.collected_at AS first_collected_at,
    wh.views AS first_views,
    wh.likes AS first_likes,
    wh.comments AS first_comments
  FROM windowed_history wh
  ORDER BY wh.post_id, wh.collected_at ASC
),
latest_snapshot AS (
  SELECT DISTINCT ON (wh.post_id)
    wh.post_id,
    wh.collected_at AS latest_collected_at,
    wh.views AS latest_views,
    wh.likes AS latest_likes,
    wh.comments AS latest_comments
  FROM windowed_history wh
  ORDER BY wh.post_id, wh.collected_at DESC
)
SELECT
  e.id AS entity_id,
  e.name::text AS entity_name,
  c.id AS creator_id,
  c.platform,
  c.username,
  c.channel_id,
  p.post_id,
  p.title,
  p.video_type,
  p.post_date,
  fs.first_collected_at,
  ls.latest_collected_at,
  fs.first_views,
  ls.latest_views,
  COALESCE(ls.latest_views, 0) - COALESCE(fs.first_views, 0) AS views_delta_7d,
  CASE
    WHEN COALESCE(fs.first_views, 0) > 0
      THEN ROUND(((COALESCE(ls.latest_views, 0) - fs.first_views)::numeric / fs.first_views::numeric) * 100, 4)
    ELSE NULL
  END AS views_growth_pct_7d,
  COALESCE(ls.latest_likes, 0) - COALESCE(fs.first_likes, 0) AS likes_delta_7d,
  COALESCE(ls.latest_comments, 0) - COALESCE(fs.first_comments, 0) AS comments_delta_7d
FROM latest_snapshot ls
JOIN first_snapshot fs ON fs.post_id = ls.post_id
JOIN public.posts p ON p.post_id = ls.post_id
JOIN public.creators c ON c.id = p.creator_id
JOIN public.entities e ON e.id = c.entity_id
WHERE ls.latest_collected_at > fs.first_collected_at;

GRANT SELECT ON public.v_dashboard_post_growth_7d TO anon;
GRANT SELECT ON public.v_dashboard_post_growth_7d TO authenticated;
