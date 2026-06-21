create or replace view public.v_dashboard_hot_now as
with unavailable_posts as (
  select distinct
    f.post_id
  from public.post_collection_failures f
  where f.status = 'unavailable'
),
ordered_snapshots as (
  select
    h.post_id,
    h.collected_at,
    h.views,
    h.likes,
    h.comments,
    lag(h.collected_at, 1) over (
      partition by h.post_id
      order by h.collected_at
    ) as prev_collected_at,
    lag(h.views, 1) over (
      partition by h.post_id
      order by h.collected_at
    ) as prev_views,
    lag(h.likes, 1) over (
      partition by h.post_id
      order by h.collected_at
    ) as prev_likes,
    lag(h.comments, 1) over (
      partition by h.post_id
      order by h.collected_at
    ) as prev_comments,
    lag(h.collected_at, 2) over (
      partition by h.post_id
      order by h.collected_at
    ) as prev2_collected_at,
    lag(h.views, 2) over (
      partition by h.post_id
      order by h.collected_at
    ) as prev2_views,
    lag(h.likes, 2) over (
      partition by h.post_id
      order by h.collected_at
    ) as prev2_likes,
    lag(h.comments, 2) over (
      partition by h.post_id
      order by h.collected_at
    ) as prev2_comments,
    row_number() over (
      partition by h.post_id
      order by h.collected_at desc
    ) as row_num_desc,
    count(*) over (
      partition by h.post_id
    )::bigint as snapshot_count
  from public.post_metrics_history h
),
latest_snapshot as (
  select
    os.post_id,
    os.collected_at as latest_collected_at,
    os.views as views_latest,
    os.likes as likes_latest,
    os.comments as comments_latest,
    os.prev_collected_at,
    os.prev_views,
    os.prev_likes,
    os.prev_comments,
    os.prev2_collected_at,
    os.prev2_views,
    os.prev2_likes,
    os.prev2_comments,
    os.snapshot_count
  from ordered_snapshots os
  where os.row_num_desc = 1
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
    ls.prev_collected_at,
    ls.prev_views,
    ls.prev_likes,
    ls.prev_comments,
    ls.prev2_collected_at,
    ls.prev2_views,
    ls.prev2_likes,
    ls.prev2_comments,
    coalesce(ls.snapshot_count, 0) as snapshot_count
  from public.posts p
  join public.creators c
    on c.id = p.creator_id
  join public.entities e
    on e.id = c.entity_id
  left join latest_snapshot ls
    on ls.post_id = p.post_id
  where not exists (
    select 1
    from unavailable_posts up
    where up.post_id = p.post_id
  )
),
calculated as (
  select
    bp.*,
    extract(epoch from ((now()::timestamp without time zone) - bp.latest_collected_at)) / 3600.0
      as latest_snapshot_age_hours,
    extract(epoch from (bp.latest_collected_at - bp.prev_collected_at)) / 3600.0
      as hours_between_latest_and_prev,
    extract(epoch from (bp.prev_collected_at - bp.prev2_collected_at)) / 3600.0
      as hours_between_prev_and_prev2,
    bp.views_latest - bp.prev_views as views_delta_recent,
    bp.likes_latest - bp.prev_likes as likes_delta_recent,
    bp.comments_latest - bp.prev_comments as comments_delta_recent,
    (bp.views_latest - bp.prev_views)::numeric
      / nullif(extract(epoch from (bp.latest_collected_at - bp.prev_collected_at)) / 3600.0, 0)
      as velocity_current,
    (bp.prev_views - bp.prev2_views)::numeric
      / nullif(extract(epoch from (bp.prev_collected_at - bp.prev2_collected_at)) / 3600.0, 0)
      as velocity_previous
  from base_posts bp
),
classified as (
  select
    c.*,
    (c.velocity_current - c.velocity_previous) as acceleration,
    case
      when c.latest_collected_at is null then 'no_snapshot'
      when c.snapshot_count < 3 then 'insufficient_snapshots'
      when c.latest_snapshot_age_hours > 24 then 'latest_snapshot_stale'
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
  prev_collected_at as collected_at_6h,
  prev_views as views_6h,
  prev_likes as likes_6h,
  prev_comments as comments_6h,
  round(hours_between_latest_and_prev::numeric, 4) as hours_between_latest_and_6h,
  prev2_collected_at as collected_at_24h,
  prev2_views as views_24h,
  prev2_likes as likes_24h,
  prev2_comments as comments_24h,
  round(hours_between_prev_and_prev2::numeric, 4) as hours_between_6h_and_24h,
  views_delta_recent,
  likes_delta_recent,
  comments_delta_recent,
  round(velocity_current::numeric, 4) as velocity_6h,
  round(velocity_previous::numeric, 4) as previous_velocity,
  round(acceleration::numeric, 4) as acceleration,
  case
    when eligibility_status = 'eligible'
      then round((velocity_current + greatest(acceleration, 0))::numeric, 4)
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
