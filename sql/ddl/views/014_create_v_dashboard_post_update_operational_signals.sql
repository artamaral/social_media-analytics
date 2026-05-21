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
    60 as tolerancia_atraso_minutos,
    count(*) filter (
      where next_check <= now() - interval '60 minutes'
    ) as itens_atrasados,
    coalesce(
      max(atraso_minutos) filter (
        where next_check <= now() - interval '60 minutes'
      ),
      0
    ) as maior_atraso_minutos,
    count(*) filter (
      where coverage_status = 'at_risk_bootstrap'
    ) as at_risk_bootstrap,
    count(*) filter (
      where coverage_status = 'recovery_low'
    ) as recovery_low
  from eligible_posts
),
classified as (
  select
    checked_at,
    tolerancia_atraso_minutos,
    itens_atrasados,
    maior_atraso_minutos,
    at_risk_bootstrap,
    recovery_low,
    case
      when itens_atrasados = 0 then 'ok'
      when itens_atrasados <= 10 then 'atencao'
      else 'nok'
    end as itens_atrasados_status_code,
    case
      when itens_atrasados = 0 then 'Fila em dia'
      when itens_atrasados <= 10 then 'Fila com atraso'
      else 'Fila muito atrasada'
    end as itens_atrasados_status_label,
    case
      when itens_atrasados = 0 then 'Nenhum post passou da tolerancia de atraso configurada.'
      when itens_atrasados <= 10 then 'Existe atraso acima da tolerancia, mas ainda em volume controlado.'
      else 'A fila acumulou atraso acima do limite tolerado para a operacao horaria.'
    end as itens_atrasados_status_reason,
    case
      when at_risk_bootstrap <= 5 then 'ok'
      when at_risk_bootstrap <= 20 then 'atencao'
      else 'nok'
    end as at_risk_bootstrap_status_code,
    case
      when at_risk_bootstrap <= 5 then 'Bootstrap controlado'
      when at_risk_bootstrap <= 20 then 'Bootstrap em atencao'
      else 'Bootstrap acumulando risco'
    end as at_risk_bootstrap_status_label,
    case
      when at_risk_bootstrap <= 5 then 'Poucos posts novos estao perto de sair da janela de bootstrap sem cobertura minima.'
      when at_risk_bootstrap <= 20 then 'Ha acumulacao moderada de posts novos perto do limite da cobertura minima.'
      else 'Posts novos estao se acumulando perto do limite e podem virar recovery_low.'
    end as at_risk_bootstrap_status_reason,
    case
      when recovery_low = 0 then 'ok'
      when recovery_low <= 3 then 'atencao'
      else 'nok'
    end as recovery_low_status_code,
    case
      when recovery_low = 0 then 'Recuperacao em dia'
      when recovery_low <= 3 then 'Recuperacao em atencao'
      else 'Recuperacao comprometida'
    end as recovery_low_status_label,
    case
      when recovery_low = 0 then 'Nenhum post antigo esta abaixo da cobertura minima.'
      when recovery_low <= 3 then 'Existe residual pequeno de posts antigos abaixo da cobertura minima.'
      else 'Posts antigos abaixo da cobertura minima ja configuram falha de cobertura recorrente.'
    end as recovery_low_status_reason
  from aggregated
)
select
  checked_at,
  to_char(checked_at - interval '3 hours', 'DD/MM/YYYY HH24:MI') as checked_at_br,
  tolerancia_atraso_minutos,
  itens_atrasados,
  maior_atraso_minutos,
  at_risk_bootstrap,
  recovery_low,
  itens_atrasados_status_code,
  itens_atrasados_status_label,
  itens_atrasados_status_reason,
  at_risk_bootstrap_status_code,
  at_risk_bootstrap_status_label,
  at_risk_bootstrap_status_reason,
  recovery_low_status_code,
  recovery_low_status_label,
  recovery_low_status_reason,
  case
    when itens_atrasados_status_code = 'nok'
      or at_risk_bootstrap_status_code = 'nok'
      or recovery_low_status_code = 'nok' then 'nok'
    when itens_atrasados_status_code = 'atencao'
      or at_risk_bootstrap_status_code = 'atencao'
      or recovery_low_status_code = 'atencao' then 'atencao'
    else 'ok'
  end as status_code,
  case
    when itens_atrasados_status_code = 'nok'
      or at_risk_bootstrap_status_code = 'nok'
      or recovery_low_status_code = 'nok' then 'Sinais operacionais criticos'
    when itens_atrasados_status_code = 'atencao'
      or at_risk_bootstrap_status_code = 'atencao'
      or recovery_low_status_code = 'atencao' then 'Sinais operacionais em atencao'
    else 'Sinais operacionais estaveis'
  end as status_label,
  concat_ws(
    ' ',
    case
      when itens_atrasados_status_code <> 'ok' then itens_atrasados_status_reason
      else null
    end,
    case
      when at_risk_bootstrap_status_code <> 'ok' then at_risk_bootstrap_status_reason
      else null
    end,
    case
      when recovery_low_status_code <> 'ok' then recovery_low_status_reason
      else null
    end,
    case
      when itens_atrasados_status_code = 'ok'
       and at_risk_bootstrap_status_code = 'ok'
       and recovery_low_status_code = 'ok'
        then 'Fila, bootstrap e recuperacao estao dentro da faixa esperada.'
      else null
    end
  ) as status_reason
from classified;

grant select on public.v_dashboard_post_update_operational_signals to anon;
grant select on public.v_dashboard_post_update_operational_signals to authenticated;
