drop view if exists public.v_dashboard_post_update_operational_signal_items;

create view public.v_dashboard_post_update_operational_signal_items as
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from public.post_metrics_history
  group by post_id
),
classified as (
  select
    now() as checked_at,
    p.post_id,
    p.created_at,
    q.priority_score,
    q.last_checked,
    q.next_check,
    q.needs_update,
    coalesce(c.total_checagens, 0) as total_checagens,
    public.calculate_priority_band(q.priority_score) as priority_band,
    floor(extract(epoch from (now() - q.next_check)) / 60)::int as atraso_minutos,
    case
      when coalesce(c.total_checagens, 0) >= 3 then 'covered'
      when p.created_at < now() - interval '5 days' then 'at_risk_bootstrap'
      else 'bootstrap_low'
    end as coverage_status
  from public.posts p
  join public.post_update_queue q
    on q.post_id = p.post_id
  left join checks c
    on c.post_id = p.post_id
  where q.needs_update = true
    and not exists (
      select 1
      from public.post_collection_failures f
      where f.post_id = p.post_id
        and f.status = 'unavailable'
    )
)
select
  checked_at,
  to_char(checked_at - interval '3 hours', 'DD/MM/YYYY HH24:MI') as checked_at_br,
  post_id,
  created_at,
  to_char(created_at - interval '3 hours', 'DD/MM/YYYY HH24:MI') as created_at_br,
  last_checked,
  case
    when last_checked is null then null
    else to_char(last_checked - interval '3 hours', 'DD/MM/YYYY HH24:MI')
  end as last_checked_br,
  next_check,
  to_char(next_check - interval '3 hours', 'DD/MM/YYYY HH24:MI') as next_check_br,
  atraso_minutos,
  total_checagens,
  priority_band,
  priority_score,
  coverage_status,
  case
    when atraso_minutos >= 60 and coverage_status = 'at_risk_bootstrap' then 'atrasado_e_at_risk_bootstrap'
    when atraso_minutos >= 60 then 'item_atrasado'
    when coverage_status = 'at_risk_bootstrap' then 'at_risk_bootstrap'
    else 'outro'
  end as signal_scope
from classified
where atraso_minutos >= 60
   or coverage_status = 'at_risk_bootstrap'
order by
  case
    when atraso_minutos >= 60 and coverage_status = 'at_risk_bootstrap' then 1
    when atraso_minutos >= 60 then 2
    when coverage_status = 'at_risk_bootstrap' then 3
    else 4
  end,
  atraso_minutos desc,
  total_checagens asc,
  created_at asc,
  post_id;

grant select on public.v_dashboard_post_update_operational_signal_items to anon;
grant select on public.v_dashboard_post_update_operational_signal_items to authenticated;
