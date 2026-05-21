drop view if exists public.v_dashboard_worker_health_status;

create view public.v_dashboard_worker_health_status as
with latest_snapshot as (
  select
    max(created_at) as ultima_evidencia_de_execucao
  from public.post_metrics_history
),
classified as (
  select
    now() as checked_at,
    ultima_evidencia_de_execucao,
    case
      when ultima_evidencia_de_execucao is null then null
      else floor(extract(epoch from (now() - ultima_evidencia_de_execucao)) / 60)::int
    end as idade_da_ultima_evidencia_minutos
  from latest_snapshot
)
select
  checked_at,
  to_char(checked_at, 'DD/MM/YYYY HH24:MI') as checked_at_br,
  ultima_evidencia_de_execucao,
  to_char(ultima_evidencia_de_execucao, 'DD/MM/YYYY HH24:MI') as ultima_evidencia_de_execucao_br,
  idade_da_ultima_evidencia_minutos,
  case
    when ultima_evidencia_de_execucao is null then 'nok'
    when idade_da_ultima_evidencia_minutos <= 30 then 'ok'
    when idade_da_ultima_evidencia_minutos <= 120 then 'atencao'
    else 'nok'
  end as status_code,
  case
    when ultima_evidencia_de_execucao is null then 'Coleta sem evidencia'
    when idade_da_ultima_evidencia_minutos <= 30 then 'Coleta em dia'
    when idade_da_ultima_evidencia_minutos <= 120 then 'Coleta com atraso'
    else 'Coleta sem evidencia recente'
  end as status_label,
  case
    when ultima_evidencia_de_execucao is null then 'Nenhum snapshot encontrado em post_metrics_history.'
    when idade_da_ultima_evidencia_minutos <= 30 then 'Ultimo snapshot dentro da janela esperada.'
    when idade_da_ultima_evidencia_minutos <= 120 then 'Ultimo snapshot acima da janela ideal, mas ainda dentro do limite de atencao.'
    else 'Ultimo snapshot acima do limite tolerado para operacao normal.'
  end as status_reason
from classified;

grant select on public.v_dashboard_worker_health_status to anon;
grant select on public.v_dashboard_worker_health_status to authenticated;
