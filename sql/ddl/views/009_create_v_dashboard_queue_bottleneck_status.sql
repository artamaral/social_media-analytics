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
    q.needs_update,
    coalesce(c.total_checagens, 0) as total_checagens,
    c.last_snapshot_at,
    case
      when b.post_id is not null then true
      else false
    end as in_current_batch,
    case
      when q.next_check <= now()::timestamp then true
      else false
    end as is_due_now,
    extract(epoch from (now()::timestamp - q.next_check)) / 3600 as overdue_hours,
    case
      when p.post_date >= now()::timestamp - interval '3 days' then 'new_0_3d'
      when p.post_date >= now()::timestamp - interval '7 days' then 'recent_4_7d'
      when p.post_date >= now()::timestamp - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket,
    case
      when coalesce(c.total_checagens, 0) < 3 then 'needs_coverage'
      when coalesce(c.total_checagens, 0) between 3 and 49 then 'covered_3_49'
      when coalesce(c.total_checagens, 0) between 50 and 199 then 'overchecked_50_199'
      when coalesce(c.total_checagens, 0) between 200 and 499 then 'overchecked_200_499'
      else 'overchecked_500_plus'
    end as check_band
  from public.post_update_queue q
  join public.posts p
    on p.post_id = q.post_id
  left join checks c
    on c.post_id = q.post_id
  left join current_batch b
    on b.post_id = q.post_id
  left join public.post_collection_failures f
    on f.post_id = q.post_id
  where q.needs_update = true
    and coalesce(f.status, 'active') <> 'unavailable'
)
select
  priority_band,
  video_age_bucket,
  check_band,
  count(*) as total_posts,
  count(*) filter (where is_due_now) as posts_vencidos,
  count(*) filter (where in_current_batch) as posts_no_batch_atual,
  round(avg(total_checagens)::numeric, 2) as media_checagens,
  max(total_checagens) as max_checagens,
  round((avg(overdue_hours) filter (where is_due_now))::numeric, 2) as atraso_medio_horas,
  round((max(overdue_hours) filter (where is_due_now))::numeric, 2) as maior_atraso_horas,
  min(next_check) filter (where is_due_now) as next_check_mais_atrasado,
  max(last_snapshot_at) as ultimo_snapshot_do_grupo,
  round(
    (
      count(*) filter (
        where is_due_now
          and video_age_bucket in ('warm_8_30d', 'old_30d_plus')
          and total_checagens >= 3
      )::numeric
      / nullif(count(*) filter (where is_due_now), 0)
    ) * 100,
    2
  ) as pct_vencidos_warm_old_cobertos,
  round(
    (
      count(*) filter (
        where is_due_now
          and check_band in (
            'overchecked_50_199',
            'overchecked_200_499',
            'overchecked_500_plus'
          )
      )::numeric
      / nullif(count(*) filter (where is_due_now), 0)
    ) * 100,
    2
  ) as pct_vencidos_overchecked
from classified
group by
  priority_band,
  video_age_bucket,
  check_band;
