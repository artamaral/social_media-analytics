-- Auditoria Sprint 1: integridade entre creators e posts.
--
-- Objetivo:
-- Validar se todos os creators ativos possuem posts descobertos e se todos os
-- posts estao vinculados a um creator valido.
--
-- Como usar:
-- 1. Execute a query detalhada para listar inconsistencias.
-- 2. Execute a query de resumo para dimensionar o problema por tipo.
--
-- Leitura:
-- - active_creator_without_posts: creator ativo que ainda nao tem nenhum post.
-- - post_without_creator_id: post sem creator_id.
-- - post_with_missing_creator: creator_id aponta para creator inexistente.
-- - post_with_inactive_creator: post ligado a creator inativo.
-- - creator_without_recent_discovery: creator ativo com posts, mas sem posts
--   inseridos recentemente; e um sinal de discovery, nao necessariamente erro.

-- Query 1: lista detalhada de inconsistencias.
with creator_post_rollup as (
  select
    c.id as creator_id,
    count(p.id) as posts_total,
    count(p.id) filter (
      where p.created_at >= now() - interval '7 days'
    ) as posts_inserted_7d,
    count(p.id) filter (
      where p.created_at >= now() - interval '30 days'
    ) as posts_inserted_30d,
    min(p.created_at) as first_post_inserted_at,
    max(p.created_at) as latest_post_inserted_at,
    max(p.post_date) as latest_post_date,
    max(p.collected_at) as latest_post_collected_at
  from public.creators c
  left join public.posts p
    on p.creator_id = c.id
  group by c.id
),
creator_issues as (
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
    c.id as creator_id,
    c.username as creator_username,
    c.channel_id,
    c.platform,
    c.is_active,
    e.name::text as entity_name,
    null::integer as internal_post_id,
    null::text as post_id,
    null::text as title,
    null::timestamp without time zone as post_date,
    null::timestamp without time zone as post_created_at,
    r.posts_total::bigint,
    r.posts_inserted_7d::bigint,
    r.posts_inserted_30d::bigint,
    r.first_post_inserted_at,
    r.latest_post_inserted_at,
    r.latest_post_date,
    r.latest_post_collected_at
  from public.creators c
  left join public.entities e
    on e.id = c.entity_id
  left join creator_post_rollup r
    on r.creator_id = c.id
),
post_issues as (
  select
    'post'::text as record_scope,
    case
      when p.creator_id is null then 'post_without_creator_id'
      when c.id is null then 'post_with_missing_creator'
      when coalesce(c.is_active, true) = false then 'post_with_inactive_creator'
      else 'ok'
    end as audit_status,
    p.creator_id,
    c.username as creator_username,
    c.channel_id,
    c.platform,
    c.is_active,
    e.name::text as entity_name,
    p.id as internal_post_id,
    p.post_id,
    p.title,
    p.post_date,
    p.created_at as post_created_at,
    null::bigint as posts_total,
    null::bigint as posts_inserted_7d,
    null::bigint as posts_inserted_30d,
    null::timestamp without time zone as first_post_inserted_at,
    null::timestamp without time zone as latest_post_inserted_at,
    null::timestamp without time zone as latest_post_date,
    null::timestamp without time zone as latest_post_collected_at
  from public.posts p
  left join public.creators c
    on c.id = p.creator_id
  left join public.entities e
    on e.id = c.entity_id
),
issues as (
  select * from creator_issues
  union all
  select * from post_issues
)
select
  record_scope,
  audit_status,
  creator_id,
  creator_username,
  channel_id,
  platform,
  is_active,
  entity_name,
  internal_post_id,
  post_id,
  title,
  post_date,
  post_created_at,
  posts_total,
  posts_inserted_7d,
  posts_inserted_30d,
  first_post_inserted_at,
  latest_post_inserted_at,
  latest_post_date,
  latest_post_collected_at
from issues
where audit_status <> 'ok'
order by
  case audit_status
    when 'post_without_creator_id' then 1
    when 'post_with_missing_creator' then 2
    when 'active_creator_without_posts' then 3
    when 'post_with_inactive_creator' then 4
    when 'creator_without_recent_discovery' then 5
    else 6
  end,
  creator_username nulls last,
  post_created_at desc nulls last,
  post_id;

-- Query 2: resumo agregado.
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
summary as (
  select * from creator_summary
  union all
  select * from post_summary
)
select
  record_scope,
  audit_status,
  platform,
  is_active,
  count(*) as total_records
from summary
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
