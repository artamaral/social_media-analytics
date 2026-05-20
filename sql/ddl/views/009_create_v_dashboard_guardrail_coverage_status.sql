drop view if exists public.v_dashboard_guardrail_coverage_status;

create view public.v_dashboard_guardrail_coverage_status as
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from public.post_metrics_history
  group by post_id
),
coverage as (
  select
    p.post_id,
    p.created_at,
    coalesce(c.total_checagens, 0) as total_checagens,
    case
      when p.created_at >= now() - interval '3 days' then 'new_0_3d'
      when p.created_at >= now() - interval '7 days' then 'recent_4_7d'
      when p.created_at >= now() - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket,
    case
      when coalesce(c.total_checagens, 0) >= 3 then 'covered'
      when p.created_at < now() - interval '7 days' then 'recovery_low'
      when p.created_at < now() - interval '5 days' then 'at_risk_bootstrap'
      else 'bootstrap_low'
    end as coverage_status
  from public.posts p
  left join checks c
    on c.post_id = p.post_id
  left join public.post_collection_failures f
    on f.post_id = p.post_id
  where coalesce(f.status, 'active') <> 'unavailable'
),
labeled as (
  select
    post_id,
    created_at,
    total_checagens,
    video_age_bucket,
    case video_age_bucket
      when 'new_0_3d' then 1
      when 'recent_4_7d' then 2
      when 'warm_8_30d' then 3
      when 'old_30d_plus' then 4
    end as bucket_sort,
    case video_age_bucket
      when 'new_0_3d' then 'Novos: 0 a 3 dias'
      when 'recent_4_7d' then 'Recentes: 4 a 7 dias'
      when 'warm_8_30d' then 'Em aquecimento: 8 a 30 dias'
      when 'old_30d_plus' then 'Legado: mais de 30 dias'
    end as intervalo_video
  from coverage
)
select
  now() as checked_at,
  bucket_sort,
  video_age_bucket,
  intervalo_video,
  total_checagens,
  count(*) as total_posts,
  case
    when video_age_bucket in ('warm_8_30d', 'old_30d_plus')
     and total_checagens < 3 then true
    else false
  end as is_legacy_guardrail
from labeled
where total_checagens < 3
group by
  bucket_sort,
  video_age_bucket,
  intervalo_video,
  total_checagens,
  is_legacy_guardrail
order by
  bucket_sort,
  total_checagens;

grant select on public.v_dashboard_guardrail_coverage_status to anon;
grant select on public.v_dashboard_guardrail_coverage_status to authenticated;
