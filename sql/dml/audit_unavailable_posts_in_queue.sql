-- Auditoria Sprint 1: confirmar que a fila nao contem posts unavailable.
--
-- Objetivo:
-- Garantir que posts com public.post_collection_failures.status = 'unavailable'
-- nao aparecem na fila operacional nem na view de dashboard da fila.

with unavailable_posts as (
  select
    f.post_id,
    f.status,
    f.human_review_status,
    f.failure_count,
    f.last_failed_at,
    f.human_reviewed_at
  from public.post_collection_failures f
  where f.status = 'unavailable'
),
queue_leaks as (
  select
    'v_post_update_queue_batch' as checked_view,
    q.post_id,
    q.priority_score,
    q.last_checked,
    q.next_check,
    q.needs_update,
    q.priority_band,
    u.status,
    u.human_review_status,
    u.failure_count,
    u.last_failed_at,
    u.human_reviewed_at
  from public.v_post_update_queue_batch q
  join unavailable_posts u
    on u.post_id = q.post_id
),
dashboard_queue_leaks as (
  select
    'v_dashboard_post_update_queue_batch' as checked_view,
    q.post_id,
    q.priority_score,
    q.last_checked_utc as last_checked,
    q.next_check_utc as next_check,
    q.needs_update,
    q.priority_band,
    u.status,
    u.human_review_status,
    u.failure_count,
    u.last_failed_at,
    u.human_reviewed_at
  from public.v_dashboard_post_update_queue_batch q
  join unavailable_posts u
    on u.post_id = q.post_id
)
select *
from queue_leaks
union all
select *
from dashboard_queue_leaks
order by
  checked_view,
  post_id;

-- Resumo esperado:
-- total_unavailable_in_queue = 0 nas duas views.
with unavailable_posts as (
  select post_id
  from public.post_collection_failures
  where status = 'unavailable'
),
summary as (
  select
    'v_post_update_queue_batch' as checked_view,
    count(*) as total_unavailable_in_queue
  from public.v_post_update_queue_batch q
  join unavailable_posts u
    on u.post_id = q.post_id
  union all
  select
    'v_dashboard_post_update_queue_batch' as checked_view,
    count(*) as total_unavailable_in_queue
  from public.v_dashboard_post_update_queue_batch q
  join unavailable_posts u
    on u.post_id = q.post_id
)
select
  checked_view,
  total_unavailable_in_queue,
  case
    when total_unavailable_in_queue = 0 then 'ok'
    else 'leak_detected'
  end as audit_status
from summary
order by checked_view;
