-- Auditoria Sprint 1: posts sem nenhum snapshot em post_metrics_history.
--
-- Objetivo:
-- Identificar somente posts cadastrados que ainda nao possuem nenhum registro
-- historico em public.post_metrics_history.
--
-- Leitura:
-- - failure_status = active: post ainda deve ser acompanhado pelo pipeline.
-- - failure_status = unavailable_candidate/unavailable: post deve ser lido
--   como caso de indisponibilidade, nao como falha comum de guardrail.

with snapshot_counts as (
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
    end as video_age_bucket,
    coalesce(s.snapshot_count, 0) as snapshot_count,
    s.first_snapshot_at,
    s.last_snapshot_at
  from public.posts p
  left join snapshot_counts s
    on s.post_id = p.post_id
  left join public.creators c
    on c.id = p.creator_id
  left join public.post_collection_failures f
    on f.post_id = p.post_id
  left join public.post_update_queue q
    on q.post_id = p.post_id
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
  video_age_bucket,
  failure_status,
  failure_count,
  last_failed_at,
  human_review_status,
  needs_update,
  last_checked,
  next_check,
  snapshot_count
from classified_posts
where snapshot_count = 0
order by
  case failure_status
    when 'active' then 1
    when 'unavailable_candidate' then 2
    when 'unavailable' then 3
    else 4
  end,
  post_date desc nulls last,
  created_at desc,
  post_id;
