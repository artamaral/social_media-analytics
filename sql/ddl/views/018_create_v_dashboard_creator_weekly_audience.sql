CREATE OR REPLACE VIEW public.v_dashboard_creator_weekly_audience AS
WITH base_history AS (
  SELECT
    c.id AS creator_id,
    e.id AS entity_id,
    e.name::text AS entity_name,
    c.platform,
    c.username,
    h.collected_at,
    h.followers,
    DATE_TRUNC('week', (h.collected_at - INTERVAL '3 hours'))::date AS week_start,
    (DATE_TRUNC('week', (h.collected_at - INTERVAL '3 hours'))::date + 6) AS week_end
  FROM public.creator_metrics_history h
  JOIN public.creators c ON c.id = h.creator_id
  JOIN public.entities e ON e.id = c.entity_id
  WHERE h.collected_at IS NOT NULL
),
completed_week_history AS (
  SELECT *
  FROM base_history
  WHERE week_end < (TIMEZONE('America/Sao_Paulo', NOW()))::date
),
weekly_snapshot_rollup AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    username,
    week_start,
    week_end,
    COUNT(*)::bigint AS snapshots_na_semana,
    COUNT(followers)::bigint AS snapshots_com_followers,
    MAX(collected_at) AS latest_collected_at
  FROM completed_week_history
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    username,
    week_start,
    week_end
),
weekly_followers_ranked AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    username,
    week_start,
    week_end,
    collected_at,
    followers,
    ROW_NUMBER() OVER (
      PARTITION BY creator_id, week_start
      ORDER BY collected_at ASC, followers ASC
    ) AS rn_first,
    ROW_NUMBER() OVER (
      PARTITION BY creator_id, week_start
      ORDER BY collected_at DESC, followers DESC
    ) AS rn_last
  FROM completed_week_history
  WHERE followers IS NOT NULL
),
weekly_followers_rollup AS (
  SELECT
    creator_id,
    entity_id,
    entity_name,
    platform,
    username,
    week_start,
    week_end,
    MAX(followers) FILTER (WHERE rn_first = 1) AS followers_first,
    MAX(followers) FILTER (WHERE rn_last = 1) AS followers_last
  FROM weekly_followers_ranked
  GROUP BY
    creator_id,
    entity_id,
    entity_name,
    platform,
    username,
    week_start,
    week_end
),
weekly_audience AS (
  SELECT
    s.creator_id,
    s.entity_id,
    s.entity_name,
    s.platform,
    s.username,
    s.week_start,
    s.week_end,
    TO_CHAR(s.week_start, 'DD/MM/YYYY') || '-' || TO_CHAR(s.week_end, 'DD/MM/YYYY') AS week_label,
    s.snapshots_na_semana,
    s.snapshots_com_followers,
    f.followers_first,
    f.followers_last,
    s.latest_collected_at
  FROM weekly_snapshot_rollup s
  LEFT JOIN weekly_followers_rollup f
    ON f.creator_id = s.creator_id
   AND f.entity_id = s.entity_id
   AND f.week_start = s.week_start
   AND f.week_end = s.week_end
),
weekly_audience_with_previous AS (
  SELECT
    wa.*,
    LAG(wa.followers_last) OVER (
      PARTITION BY wa.creator_id
      ORDER BY wa.week_start
    ) AS previous_followers_last
  FROM weekly_audience wa
)
SELECT
  creator_id,
  entity_id,
  entity_name,
  platform,
  username,
  week_start,
  week_end,
  week_label,
  snapshots_na_semana,
  snapshots_com_followers,
  followers_first,
  followers_last,
  followers_last - previous_followers_last AS followers_delta_vs_prev_week,
  CASE
    WHEN followers_last IS NULL OR previous_followers_last IS NULL THEN 'sem_base'
    WHEN followers_last > previous_followers_last THEN 'cresceu'
    WHEN followers_last < previous_followers_last THEN 'caiu'
    ELSE 'estavel'
  END AS followers_weekly_status,
  latest_collected_at
FROM weekly_audience_with_previous
ORDER BY creator_id, week_start;

GRANT SELECT ON public.v_dashboard_creator_weekly_audience TO anon;
GRANT SELECT ON public.v_dashboard_creator_weekly_audience TO authenticated;
