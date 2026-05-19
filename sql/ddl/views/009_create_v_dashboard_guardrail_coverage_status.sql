create or replace view public.v_dashboard_guardrail_coverage_status as
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
)
select
  now() as checked_at,
  count(*) as total_posts_monitored,
  count(*) filter (where total_checagens < 3) as total_under_minimum,
  count(*) filter (where coverage_status = 'bootstrap_low') as bootstrap_low,
  count(*) filter (where coverage_status = 'at_risk_bootstrap') as at_risk_bootstrap,
  count(*) filter (where coverage_status = 'recovery_low') as recovery_low,
  count(*) filter (where coverage_status = 'covered') as covered,
  count(*) filter (where total_checagens = 0) as zero_checks,
  count(*) filter (where total_checagens = 1) as one_check,
  count(*) filter (where total_checagens = 2) as two_checks,
  case
    when count(*) filter (where coverage_status = 'recovery_low') = 0
      then true
    else false
  end as legacy_ready
from coverage;
