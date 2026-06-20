create or replace view public.v_dashboard_hot_now as
with unavailable_posts as (
  select distinct
    f.post_id
  from public.post_collection_failures f
  where f.status = 'unavailable'
),
latest_snapshot as (
  select distinct on (h.post_id)
    h.post_id,
    h.collected_at as latest_collected_at,
    h.views as views_latest,
    h.likes as likes_latest,
    h.comments as comments_latest
  from public.post_metrics_history h
  order by h.post_id, h.collected_at desc
),
snapshot_counts as (
  select
    h.post_id,
    count(*)::bigint as snapshot_count
  from public.post_metrics_history h
  group by h.post_id
),
base_posts as (
  select
    e.id as entity_id,
    e.name::text as entity_name,
    e.name::text as creator_name,
    c.id as creator_id,
    c.platform,
    c.username,
    c.channel_id,
    c.avatar_url,
    p.post_id,
    p.title,
    p.video_type,
    p.post_date as published_at,
    ls.latest_collected_at,
    ls.views_latest,
    ls.likes_latest,
    ls.comments_latest,
    coalesce(sc.snapshot_count, 0) as snapshot_count
  from public.posts p
  join public.creators c
    on c.id = p.creator_id
  join public.entities e
    on e.id = c.entity_id
  left join latest_snapshot ls
    on ls.post_id = p.post_id
  left join snapshot_counts sc
    on sc.post_id = p.post_id
  where not exists (
    select 1
    from unavailable_posts up
    where up.post_id = p.post_id
  )
),
snapshots as (
  select
    bp.*,
    h6.collected_at as collected_at_6h,
    h6.views as views_6h,
    h6.likes as likes_6h,
    h6.comments as comments_6h,
    h24.collected_at as collected_at_24h,
    h24.views as views_24h,
    h24.likes as likes_24h,
    h24.comments as comments_24h
  from base_posts bp
  left join lateral (
    select
      h.collected_at,
      h.views,
      h.likes,
      h.comments
    from public.post_metrics_history h
    where h.post_id = bp.post_id
      and bp.latest_collected_at is not null
      and h.collected_at <= bp.latest_collected_at - interval '6 hours'
      and h.collected_at >= bp.latest_collected_at - interval '8 hours'
    order by
      abs(extract(epoch from (h.collected_at - (bp.latest_collected_at - interval '6 hours')))) asc,
      h.collected_at desc
    limit 1
  ) h6 on true
  left join lateral (
    select
      h.collected_at,
      h.views,
      h.likes,
      h.comments
    from public.post_metrics_history h
    where h.post_id = bp.post_id
      and bp.latest_collected_at is not null
      and h.collected_at <= bp.latest_collected_at - interval '18 hours'
      and h.collected_at >= bp.latest_collected_at - interval '30 hours'
    order by
      abs(extract(epoch from (h.collected_at - (bp.latest_collected_at - interval '24 hours')))) asc,
      h.collected_at desc
    limit 1
  ) h24 on true
),
calculated as (
  select
    s.*,
    extract(epoch from ((now()::timestamp without time zone) - s.latest_collected_at)) / 3600.0
      as latest_snapshot_age_hours,
    extract(epoch from (s.latest_collected_at - s.collected_at_6h)) / 3600.0
      as hours_between_latest_and_6h,
    extract(epoch from (s.collected_at_6h - s.collected_at_24h)) / 3600.0
      as hours_between_6h_and_24h,
    s.views_latest - s.views_6h as views_delta_recent,
    s.likes_latest - s.likes_6h as likes_delta_recent,
    s.comments_latest - s.comments_6h as comments_delta_recent,
    (s.views_latest - s.views_6h)::numeric
      / nullif(extract(epoch from (s.latest_collected_at - s.collected_at_6h)) / 3600.0, 0)
      as velocity_6h,
    (s.views_6h - s.views_24h)::numeric
      / nullif(extract(epoch from (s.collected_at_6h - s.collected_at_24h)) / 3600.0, 0)
      as previous_velocity
  from snapshots s
),
classified as (
  select
    c.*,
    (c.velocity_6h - c.previous_velocity) as acceleration,
    case
      when c.latest_collected_at is null then 'no_snapshot'
      when c.snapshot_count < 3 then 'insufficient_snapshots'
      when c.latest_snapshot_age_hours > 12 then 'latest_snapshot_stale'
      when c.collected_at_6h is null then 'baseline_6h_missing'
      when c.collected_at_24h is null then 'baseline_24h_missing'
      when coalesce(c.views_delta_recent, 0) <= 0 then 'no_recent_views_delta'
      else 'eligible'
    end as eligibility_status
  from calculated c
)
select
  entity_id,
  entity_name,
  creator_id,
  creator_name,
  platform,
  username,
  channel_id,
  avatar_url,
  post_id,
  title,
  video_type,
  published_at,
  latest_collected_at,
  round(latest_snapshot_age_hours::numeric, 4) as latest_snapshot_age_hours,
  snapshot_count,
  views_latest,
  likes_latest,
  comments_latest,
  collected_at_6h,
  views_6h,
  likes_6h,
  comments_6h,
  round(hours_between_latest_and_6h::numeric, 4) as hours_between_latest_and_6h,
  collected_at_24h,
  views_24h,
  likes_24h,
  comments_24h,
  round(hours_between_6h_and_24h::numeric, 4) as hours_between_6h_and_24h,
  views_delta_recent,
  likes_delta_recent,
  comments_delta_recent,
  round(velocity_6h::numeric, 4) as velocity_6h,
  round(previous_velocity::numeric, 4) as previous_velocity,
  round(acceleration::numeric, 4) as acceleration,
  case
    when eligibility_status = 'eligible'
      then round((velocity_6h + greatest(acceleration, 0))::numeric, 4)
    else null
  end as hot_now_rank_score,
  eligibility_status,
  eligibility_status = 'eligible' as is_hot_now_eligible
from classified
order by
  hot_now_rank_score desc nulls last,
  acceleration desc nulls last,
  velocity_6h desc nulls last,
  latest_collected_at desc nulls last;

grant select on public.v_dashboard_hot_now to anon;
grant select on public.v_dashboard_hot_now to authenticated;
