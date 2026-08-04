create or replace view public.v_dashboard_queue_bottleneck_status as
with checks as (
  select
    post_id,
    count(*) as total_checagens,
    max(collected_at) as last_snapshot_at
  from public.post_metrics_history
  group by post_id
),
current_batch as (
  select post_id
  from public.v_post_update_queue_batch
),
classified as (
  select
    p.post_id,
    p.post_date,
    q.priority_score,
    public.calculate_priority_band(q.priority_score) as priority_band,
    q.last_checked,
    q.next_check,
    coalesce(c.total_checagens, 0) as total_checagens,
    coalesce(c.last_snapshot_at, q.last_checked::timestamp, p.created_at) as effective_last_check,
    extract(
      epoch from (
        now()::timestamp - coalesce(c.last_snapshot_at, q.last_checked::timestamp, p.created_at)
      )
    ) / 86400 as staleness_days,
    case
      when b.post_id is not null then true
      else false
    end as in_current_batch,
    case
      when q.next_check <= now() then true
      else false
    end as is_due_now,
    case
      when p.post_date >= now()::timestamp - interval '3 days' then 'new_0_3d'
      when p.post_date >= now()::timestamp - interval '7 days' then 'recent_4_7d'
      when p.post_date >= now()::timestamp - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket,
    case
      when coalesce(c.total_checagens, 0) < 3 then 'needs_coverage'
      when coalesce(c.total_checagens, 0) between 3 and 20 then 'covered_3_20'
      when coalesce(c.total_checagens, 0) between 21 and 100 then 'overchecked_21_100'
      else 'overchecked_101_plus'
    end as check_band
  from public.post_update_queue q
  join public.posts p
    on p.post_id = q.post_id
  left join checks c
    on c.post_id = q.post_id
  left join current_batch b
    on b.post_id = q.post_id
  where q.needs_update = true
    and not exists (
      select 1
      from public.post_collection_failures f
      where f.post_id = q.post_id
        and f.status = 'unavailable'
    )
)
select
  priority_band,
  video_age_bucket,
  check_band,
  count(*) as total_posts,
  round(avg(total_checagens)::numeric, 2) as media_checagens,
  max(total_checagens) as max_checagens,
  round(avg(staleness_days)::numeric, 2) as avg_staleness_days,
  round(
    (percentile_cont(0.5) within group (order by staleness_days))::numeric,
    2
  ) as p50_staleness_days,
  round(
    (percentile_cont(0.9) within group (order by staleness_days))::numeric,
    2
  ) as p90_staleness_days,
  round(
    (percentile_cont(0.95) within group (order by staleness_days))::numeric,
    2
  ) as p95_staleness_days,
  round(max(staleness_days)::numeric, 2) as max_staleness_days,
  count(*) filter (
    where staleness_days > 3.2
  ) as posts_acima_3_2d,
  count(*) filter (
    where staleness_days > 5
  ) as posts_acima_5d,
  count(*) filter (
    where staleness_days > 7
  ) as posts_acima_7d,
  count(*) filter (
    where is_due_now
  ) as posts_vencidos,
  count(*) filter (
    where in_current_batch
  ) as posts_no_batch_atual,
  min(effective_last_check) as oldest_effective_last_check,
  max(effective_last_check) as newest_effective_last_check,
  min(next_check) filter (
    where is_due_now
  ) as next_check_mais_atrasado
from classified
group by
  priority_band,
  video_age_bucket,
  check_band;
