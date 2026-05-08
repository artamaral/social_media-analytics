CREATE OR REPLACE VIEW public.v_dashboard_data_quality_status AS
WITH posts_without_history AS (
  SELECT COUNT(*) AS total
  FROM public.posts p
  LEFT JOIN public.post_metrics_history h ON h.post_id = p.post_id
  WHERE h.post_id IS NULL
),
posts_with_null_collected_at AS (
  SELECT COUNT(*) AS total
  FROM public.posts p
  WHERE p.collected_at IS NULL
),
posts_stale_24h AS (
  SELECT COUNT(*) AS total
  FROM public.posts p
  LEFT JOIN (
    SELECT
      h.post_id,
      MAX(h.collected_at) AS latest_collected_at
    FROM public.post_metrics_history h
    GROUP BY h.post_id
  ) latest ON latest.post_id = p.post_id
  WHERE latest.latest_collected_at IS NULL
     OR latest.latest_collected_at < NOW() - INTERVAL '24 hours'
),
creators_without_posts AS (
  SELECT COUNT(*) AS total
  FROM public.creators c
  LEFT JOIN public.posts p ON p.creator_id = c.id
  WHERE p.id IS NULL
)
SELECT
  NOW() AS checked_at,
  (SELECT total FROM posts_without_history) AS posts_without_history,
  (SELECT total FROM posts_with_null_collected_at) AS posts_with_null_collected_at,
  (SELECT total FROM posts_stale_24h) AS posts_stale_24h,
  (SELECT total FROM creators_without_posts) AS creators_without_posts,
  CASE
    WHEN (SELECT total FROM posts_without_history) = 0
     AND (SELECT total FROM posts_with_null_collected_at) = 0
     AND (SELECT total FROM posts_stale_24h) = 0
     AND (SELECT total FROM creators_without_posts) = 0
      THEN true
    ELSE false
  END AS is_analytics_ready;
