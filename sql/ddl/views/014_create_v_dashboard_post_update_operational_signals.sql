drop view if exists public.v_dashboard_post_update_operational_signals;

create view public.v_dashboard_post_update_operational_signals as
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from public.post_metrics_history
  group by post_id
),
eligible_posts as (
  select
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
      when p.created_at < now() - interval '7 days' then 'recovery_low'
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
),
aggregated as (
  select
    now() as checked_at,
    count(*) filter (
      where atraso_minutos > 0
        and atraso_minutos <= 60
    ) as itens_atrasados_ate_1h,
    count(*) filter (
      where atraso_minutos > 60
        and atraso_minutos <= 360
    ) as itens_atrasados_ate_6h,
    count(*) filter (
      where atraso_minutos > 360
        and atraso_minutos <= 1440
    ) as itens_atrasados_ate_24h,
    count(*) filter (
      where coverage_status = 'at_risk_bootstrap'
    ) as at_risk_bootstrap
  from eligible_posts
),
classified as (
  select
    checked_at,
    itens_atrasados_ate_1h,
    itens_atrasados_ate_6h,
    itens_atrasados_ate_24h,
    at_risk_bootstrap,
    case
      when itens_atrasados_ate_24h > 0 then 'nok'
      when itens_atrasados_ate_6h > 0 then 'atencao'
      when at_risk_bootstrap > 20 then 'nok'
      when at_risk_bootstrap > 5 then 'atencao'
      else 'ok'
    end as status_code,
    case
      when itens_atrasados_ate_24h > 0 then 'Sinais operacionais criticos'
      when itens_atrasados_ate_6h > 0 then 'Sinais operacionais em atencao'
      when itens_atrasados_ate_1h > 0 then 'Sinais operacionais em observacao'
      when at_risk_bootstrap > 20 then 'Bootstrap acumulando risco'
      when at_risk_bootstrap > 5 then 'Bootstrap em atencao'
      else 'Sinais operacionais estaveis'
    end as status_label,
    case
      when itens_atrasados_ate_24h > 0 then 'A fila acumulou atraso acima de 24 horas.'
      when itens_atrasados_ate_6h > 0 then 'A fila acumulou atraso acima de 6 horas.'
      when itens_atrasados_ate_1h > 0 then 'Ha atraso recente, mas ainda dentro da faixa de 1 hora.'
      when at_risk_bootstrap > 20 then 'Posts novos estao se acumulando perto do limite e podem perder cobertura minima.'
      when at_risk_bootstrap > 5 then 'Ha acumulacao moderada de posts novos perto do limite da cobertura minima.'
      else 'Fila e bootstrap estao dentro da faixa esperada.'
    end as status_reason
  from aggregated
)
select
  checked_at,
  to_char(checked_at - interval '3 hours', 'DD/MM/YYYY HH24:MI') as checked_at_br,
  itens_atrasados_ate_1h,
  itens_atrasados_ate_6h,
  itens_atrasados_ate_24h,
  at_risk_bootstrap,
  status_code,
  status_label,
  status_reason
from classified;

grant select on public.v_dashboard_post_update_operational_signals to anon;
grant select on public.v_dashboard_post_update_operational_signals to authenticated;
