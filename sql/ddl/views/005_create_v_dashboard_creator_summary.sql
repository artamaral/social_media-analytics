CREATE OR REPLACE VIEW public.v_dashboard_creator_summary AS
WITH post_rollup AS (
  SELECT
    p.creator_id,
    COUNT(*) AS post_count,
    COALESCE(SUM(p.views), 0) AS total_views,
    COALESCE(SUM(p.likes), 0) AS total_likes,
    COALESCE(SUM(p.comments), 0) AS total_comments,
    MAX(p.post_date) AS latest_post_date,
    MAX(p.collected_at) AS latest_collected_at
  FROM public.posts p
  GROUP BY p.creator_id
)
SELECT
  e.id AS entity_id,
  e.name::text AS entity_name,
  e.niche,
  e.creator_type,
  c.id AS creator_id,
  c.platform,
  c.username,
  c.channel_id,
  c.avatar_url,
  c.followers,
  COALESCE(pr.post_count, 0) AS post_count,
  COALESCE(pr.total_views, 0) AS total_views,
  COALESCE(pr.total_likes, 0) AS total_likes,
  COALESCE(pr.total_comments, 0) AS total_comments,
  CASE
    WHEN COALESCE(pr.total_views, 0) > 0
      THEN ROUND(((COALESCE(pr.total_likes, 0) + COALESCE(pr.total_comments, 0))::numeric / pr.total_views::numeric) * 100, 4)
    ELSE 0
  END AS engagement_rate_pct,
  pr.latest_post_date,
  pr.latest_collected_at,
  c.is_active
FROM public.creators c
JOIN public.entities e ON e.id = c.entity_id
LEFT JOIN post_rollup pr ON pr.creator_id = c.id;

GRANT SELECT ON public.v_dashboard_creator_summary TO anon;
GRANT SELECT ON public.v_dashboard_creator_summary TO authenticated;
