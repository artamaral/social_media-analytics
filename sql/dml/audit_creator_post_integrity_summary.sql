-- Auditoria Sprint 1: resumo de integridade entre creators e posts.
--
-- Execute este arquivo inteiro no Supabase SQL Editor.

with creator_post_rollup as (
  select
    c.id as creator_id,
    count(p.id) as posts_total,
    count(p.id) filter (
      where p.created_at >= now() - interval '30 days'
    ) as posts_inserted_30d
  from public.creators c
  left join public.posts p
    on p.creator_id = c.id
  group by c.id
),
creator_summary as (
  select
    'creator'::text as record_scope,
    case
      when coalesce(c.is_active, true) = true
        and coalesce(r.posts_total, 0) = 0
        then 'active_creator_without_posts'
      when coalesce(c.is_active, true) = true
        and coalesce(r.posts_total, 0) > 0
        and coalesce(r.posts_inserted_30d, 0) = 0
        then 'creator_without_recent_discovery'
      else 'ok'
    end as audit_status,
    c.platform,
    coalesce(c.is_active, true) as is_active
  from public.creators c
  left join creator_post_rollup r
    on r.creator_id = c.id
),
post_summary as (
  select
    'post'::text as record_scope,
    case
      when p.creator_id is null then 'post_without_creator_id'
      when c.id is null then 'post_with_missing_creator'
      when coalesce(c.is_active, true) = false then 'post_with_inactive_creator'
      else 'ok'
    end as audit_status,
    coalesce(c.platform, 'unknown') as platform,
    coalesce(c.is_active, true) as is_active
  from public.posts p
  left join public.creators c
    on c.id = p.creator_id
),
audit_summary as (
  select
    record_scope,
    audit_status,
    platform,
    is_active
  from creator_summary
  union all
  select
    record_scope,
    audit_status,
    platform,
    is_active
  from post_summary
)
select
  record_scope,
  audit_status,
  platform,
  is_active,
  count(*) as total_records
from audit_summary
group by
  record_scope,
  audit_status,
  platform,
  is_active
order by
  case audit_status
    when 'ok' then 9
    when 'post_without_creator_id' then 1
    when 'post_with_missing_creator' then 2
    when 'active_creator_without_posts' then 3
    when 'post_with_inactive_creator' then 4
    when 'creator_without_recent_discovery' then 5
    else 6
  end,
  record_scope,
  platform,
  is_active;
