-- Auditoria Sprint 1: gaps de coleta por post.
--
-- Objetivo:
-- Identificar posts ativos com possivel gap de coleta, usando duas leituras:
-- 1. frescor do ultimo snapshot em post_metrics_history;
-- 2. atraso em relacao ao next_check da fila operacional.
--
-- Leitura:
-- - active: entra na avaliacao principal de qualidade.
-- - unavailable_candidate/unavailable: aparece separado para auditoria, mas
--   nao deve contaminar a leitura principal de gaps da base ativa.
--
-- Observacao:
-- A regra de next_check desacelera posts warm/old ja cobertos. Por isso, a
-- auditoria separa "stale_24h" de "overdue_by_next_check".

with snapshot_rollup as (
  select
    h.post_id,
    count(*) as snapshot_count,
    min(h.collected_at) as first_snapshot_at,
    max(h.collected_at) as last_snapshot_at
  from public.post_metrics_history h
  group by h.post_id
),
classified_posts as (
  select
    p.id as internal_post_id,
    p.post_id,
    p.title,
    p.creator_id,
    c.username as creator_username,
    p.video_type,
    p.post_date,
    p.created_at,
    p.collected_at as post_collected_at,
    coalesce(s.snapshot_count, 0) as snapshot_count,
    s.first_snapshot_at,
    s.last_snapshot_at,
    coalesce(f.status, 'active') as failure_status,
    f.failure_count,
    f.last_failed_at,
    f.human_review_status,
    q.needs_update,
    q.last_checked,
    q.next_check,
    q.priority_score,
    public.calculate_priority_band(q.priority_score) as priority_band,
    case
      when p.post_date >= now() - interval '3 days' then 'new_0_3d'
      when p.post_date >= now() - interval '7 days' then 'recent_4_7d'
      when p.post_date >= now() - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket
  from public.posts p
  left join snapshot_rollup s
    on s.post_id = p.post_id
  left join public.creators c
    on c.id = p.creator_id
  left join public.post_collection_failures f
    on f.post_id = p.post_id
  left join public.post_update_queue q
    on q.post_id = p.post_id
),
audited as (
  select
    *,
    case
      when snapshot_count = 0 then null
      else round(
        (extract(epoch from (now()::timestamp - last_snapshot_at)) / 3600.0)::numeric,
        2
      )
    end as hours_since_last_snapshot,
    case
      when next_check is null then null
      else round(
        (extract(epoch from (now() - next_check)) / 3600.0)::numeric,
        2
      )
    end as hours_overdue_by_next_check,
    case
      when snapshot_count = 0 then 'no_snapshot'
      when failure_status <> 'active' then 'non_active_failure_status'
      when next_check is not null and next_check <= now()
        then 'overdue_by_next_check'
      when video_age_bucket in ('new_0_3d', 'recent_4_7d')
        and last_snapshot_at < now()::timestamp - interval '24 hours'
        then 'stale_new_recent_24h'
      when video_age_bucket in ('warm_8_30d', 'old_30d_plus')
        and last_snapshot_at < now()::timestamp - interval '72 hours'
        then 'stale_warm_old_72h'
      else 'ok'
    end as gap_status,
    case
      when snapshot_count < 3 then 'needs_coverage'
      when snapshot_count between 3 and 49 then 'covered_3_49'
      when snapshot_count between 50 and 199 then 'overchecked_50_199'
      when snapshot_count between 200 and 499 then 'overchecked_200_499'
      else 'overchecked_500_plus'
    end as check_band
  from classified_posts
)
select
  internal_post_id,
  post_id,
  title,
  creator_id,
  creator_username,
  video_type,
  post_date,
  created_at,
  post_collected_at,
  snapshot_count,
  first_snapshot_at,
  last_snapshot_at,
  hours_since_last_snapshot,
  video_age_bucket,
  check_band,
  failure_status,
  failure_count,
  last_failed_at,
  human_review_status,
  needs_update,
  priority_band,
  priority_score,
  last_checked,
  next_check,
  hours_overdue_by_next_check,
  gap_status
from audited
where gap_status <> 'ok'
order by
  case gap_status
    when 'overdue_by_next_check' then 1
    when 'stale_new_recent_24h' then 2
    when 'stale_warm_old_72h' then 3
    when 'no_snapshot' then 4
    when 'non_active_failure_status' then 5
    else 6
  end,
  case failure_status
    when 'active' then 1
    when 'unavailable_candidate' then 2
    when 'unavailable' then 3
    else 4
  end,
  coalesce(hours_overdue_by_next_check, 0) desc,
  coalesce(hours_since_last_snapshot, 0) desc,
  post_date desc nulls last,
  created_at desc,
  post_id;

-- Resumo agregado da mesma auditoria.
with snapshot_rollup as (
  select
    h.post_id,
    count(*) as snapshot_count,
    max(h.collected_at) as last_snapshot_at
  from public.post_metrics_history h
  group by h.post_id
),
audited as (
  select
    coalesce(f.status, 'active') as failure_status,
    case
      when p.post_date >= now() - interval '3 days' then 'new_0_3d'
      when p.post_date >= now() - interval '7 days' then 'recent_4_7d'
      when p.post_date >= now() - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket,
    case
      when coalesce(s.snapshot_count, 0) < 3 then 'needs_coverage'
      when coalesce(s.snapshot_count, 0) between 3 and 49 then 'covered_3_49'
      when coalesce(s.snapshot_count, 0) between 50 and 199 then 'overchecked_50_199'
      when coalesce(s.snapshot_count, 0) between 200 and 499 then 'overchecked_200_499'
      else 'overchecked_500_plus'
    end as check_band,
    case
      when coalesce(s.snapshot_count, 0) = 0 then 'no_snapshot'
      when coalesce(f.status, 'active') <> 'active' then 'non_active_failure_status'
      when q.next_check is not null and q.next_check <= now()
        then 'overdue_by_next_check'
      when p.post_date >= now() - interval '7 days'
        and s.last_snapshot_at < now()::timestamp - interval '24 hours'
        then 'stale_new_recent_24h'
      when p.post_date < now() - interval '7 days'
        and s.last_snapshot_at < now()::timestamp - interval '72 hours'
        then 'stale_warm_old_72h'
      else 'ok'
    end as gap_status
  from public.posts p
  left join snapshot_rollup s
    on s.post_id = p.post_id
  left join public.post_collection_failures f
    on f.post_id = p.post_id
  left join public.post_update_queue q
    on q.post_id = p.post_id
)
select
  gap_status,
  failure_status,
  video_age_bucket,
  check_band,
  count(*) as total_posts
from audited
group by
  gap_status,
  failure_status,
  video_age_bucket,
  check_band
order by
  case gap_status
    when 'ok' then 9
    when 'overdue_by_next_check' then 1
    when 'stale_new_recent_24h' then 2
    when 'stale_warm_old_72h' then 3
    when 'no_snapshot' then 4
    when 'non_active_failure_status' then 5
    else 6
  end,
  failure_status,
  video_age_bucket,
  check_band;
