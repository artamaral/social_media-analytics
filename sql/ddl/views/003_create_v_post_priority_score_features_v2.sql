create or replace view public.v_post_priority_score_features_v2 as
with current_posts as (
  select
    p.post_id,
    p.views,
    p.likes,
    p.comments,
    coalesce(p.collected_at, now()::timestamp without time zone) as current_collected_at
  from public.posts p
),
snapshots as (
  select
    cp.post_id,
    cp.views,
    cp.likes,
    cp.comments,
    cp.current_collected_at,
    h6.collected_at as collected_at_6h,
    h6.views as views_6h,
    h6.likes as likes_6h,
    h6.comments as comments_6h,
    h24.collected_at as collected_at_24h,
    h24.views as views_24h,
    h24.likes as likes_24h,
    h24.comments as comments_24h
  from current_posts cp
  left join lateral (
    select
      h.collected_at,
      h.views,
      h.likes,
      h.comments
    from public.post_metrics_history h
    where h.post_id = cp.post_id
      and h.collected_at <= cp.current_collected_at - interval '6 hours'
    order by h.collected_at desc
    limit 1
  ) h6 on true
  left join lateral (
    select
      h.collected_at,
      h.views,
      h.likes,
      h.comments
    from public.post_metrics_history h
    where h.post_id = cp.post_id
      and h.collected_at <= cp.current_collected_at - interval '24 hours'
    order by h.collected_at desc
    limit 1
  ) h24 on true
),
features as (
  select
    s.*,
    extract(epoch from (s.current_collected_at - s.collected_at_6h)) / 3600.0 as hours_since_6h_snapshot,
    extract(epoch from (s.current_collected_at - s.collected_at_24h)) / 3600.0 as hours_since_24h_snapshot,
    public.calculate_post_base_popularity_v2(
      s.views,
      s.likes,
      s.comments
    ) as base_popularity,
    public.calculate_velocity_raw_v2(
      s.views - s.views_6h,
      s.likes - s.likes_6h,
      s.comments - s.comments_6h,
      extract(epoch from (s.current_collected_at - s.collected_at_6h)) / 3600.0
    ) as velocity_raw_6h,
    public.calculate_velocity_raw_v2(
      s.views - s.views_24h,
      s.likes - s.likes_24h,
      s.comments - s.comments_24h,
      extract(epoch from (s.current_collected_at - s.collected_at_24h)) / 3600.0
    ) as velocity_raw_24h
  from snapshots s
),
scored as (
  select
    f.*,
    case
      when f.collected_at_6h is not null and f.collected_at_24h is not null then 'full'
      when f.collected_at_6h is not null then 'partial'
      else 'low'
    end as history_level,
    public.calculate_velocity_score_v2(f.velocity_raw_6h) as velocity_score,
    public.calculate_acceleration_score_v2(
      f.velocity_raw_6h,
      f.velocity_raw_24h
    ) as acceleration_score
  from features f
)
select
  s.post_id,
  s.views,
  s.likes,
  s.comments,
  s.current_collected_at,
  s.collected_at_6h,
  s.collected_at_24h,
  s.hours_since_6h_snapshot,
  s.hours_since_24h_snapshot,
  s.base_popularity,
  s.velocity_raw_6h,
  s.velocity_raw_24h,
  s.velocity_score,
  s.acceleration_score,
  s.history_level,
  public.calculate_post_priority_v2(
    s.base_popularity,
    s.velocity_score,
    s.acceleration_score,
    s.history_level
  ) as priority_score_v2,
  public.calculate_priority_band_v2(
    public.calculate_post_priority_v2(
      s.base_popularity,
      s.velocity_score,
      s.acceleration_score,
      s.history_level
    )
  ) as priority_band_v2,
  public.calculate_next_check_v2(
    public.calculate_post_priority_v2(
      s.base_popularity,
      s.velocity_score,
      s.acceleration_score,
      s.history_level
    ),
    s.current_collected_at
  ) as proposed_next_check_v2
from scored s;
