-- Auditoria Sprint 1: consistencia de posts.collected_at.
--
-- Objetivo:
-- Validar se public.posts.collected_at esta preenchido e sincronizado com o
-- ultimo snapshot em public.post_metrics_history para cada post.
--
-- Como usar:
-- 1. Execute a query principal para listar inconsistencias.
-- 2. Execute o resumo final para dimensionar o problema por status e idade.
--
-- Leitura:
-- - active: deve ser tratado como possivel problema real de coleta/sync.
-- - unavailable_candidate/unavailable: deve ser lido primeiro como auditoria de
--   indisponibilidade, nao como falha comum de qualidade.

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
      when snapshot_count = 0 and post_collected_at is null
        then 'zero_snapshots_and_post_collected_at_null'
      when snapshot_count = 0 and post_collected_at is not null
        then 'post_collected_at_without_snapshot'
      when snapshot_count > 0 and post_collected_at is null
        then 'post_collected_at_null_with_snapshots'
      when snapshot_count > 0
        and post_collected_at <> last_snapshot_at
        then 'post_collected_at_differs_from_last_snapshot'
      else 'ok'
    end as audit_status,
    case
      when snapshot_count > 0 and post_collected_at is not null
        then extract(epoch from (last_snapshot_at - post_collected_at)) / 60.0
      else null
    end as minutes_between_last_snapshot_and_post_collected_at
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
  minutes_between_last_snapshot_and_post_collected_at,
  video_age_bucket,
  failure_status,
  failure_count,
  last_failed_at,
  human_review_status,
  needs_update,
  last_checked,
  next_check,
  audit_status
from audited
where audit_status <> 'ok'
order by
  case audit_status
    when 'post_collected_at_null_with_snapshots' then 1
    when 'post_collected_at_differs_from_last_snapshot' then 2
    when 'post_collected_at_without_snapshot' then 3
    when 'zero_snapshots_and_post_collected_at_null' then 4
    else 5
  end,
  case failure_status
    when 'active' then 1
    when 'unavailable_candidate' then 2
    when 'unavailable' then 3
    else 4
  end,
  abs(coalesce(minutes_between_last_snapshot_and_post_collected_at, 0)) desc,
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
      when coalesce(s.snapshot_count, 0) = 0 and p.collected_at is null
        then 'zero_snapshots_and_post_collected_at_null'
      when coalesce(s.snapshot_count, 0) = 0 and p.collected_at is not null
        then 'post_collected_at_without_snapshot'
      when coalesce(s.snapshot_count, 0) > 0 and p.collected_at is null
        then 'post_collected_at_null_with_snapshots'
      when coalesce(s.snapshot_count, 0) > 0
        and p.collected_at <> s.last_snapshot_at
        then 'post_collected_at_differs_from_last_snapshot'
      else 'ok'
    end as audit_status
  from public.posts p
  left join snapshot_rollup s
    on s.post_id = p.post_id
  left join public.post_collection_failures f
    on f.post_id = p.post_id
)
select
  audit_status,
  failure_status,
  video_age_bucket,
  count(*) as total_posts
from audited
group by
  audit_status,
  failure_status,
  video_age_bucket
order by
  case audit_status
    when 'ok' then 9
    else 1
  end,
  audit_status,
  failure_status,
  video_age_bucket;
