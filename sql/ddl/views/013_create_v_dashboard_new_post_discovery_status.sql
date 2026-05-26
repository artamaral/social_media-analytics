drop view if exists public.v_dashboard_new_post_discovery_status;

create view public.v_dashboard_new_post_discovery_status as
with latest_execution as (
  select
    max(collected_at) as ultima_execucao_discovery,
    count(distinct creator_id) filter (
      where collected_at >= now() - interval '24 hours'
    ) as creators_avaliados_24h
  from public.creator_metrics_history
  where source = 'youtube_channels_api'
),
latest_discovery as (
  select
    max(created_at) as ultima_descoberta_de_post,
    count(*) filter (where created_at >= now() - interval '24 hours') as novos_posts_24h
  from public.posts
),
classified as (
  select
    now() as checked_at,
    latest_execution.ultima_execucao_discovery,
    latest_execution.creators_avaliados_24h,
    ultima_descoberta_de_post,
    novos_posts_24h,
    case
      when latest_execution.ultima_execucao_discovery is null then null
      else floor(extract(epoch from (now() - latest_execution.ultima_execucao_discovery)) / 60)::int
    end as idade_da_ultima_execucao_minutos,
    case
      when ultima_descoberta_de_post is null then null
      else floor(extract(epoch from (now() - ultima_descoberta_de_post)) / 60)::int
    end as idade_da_ultima_descoberta_minutos
  from latest_execution
  cross join latest_discovery
)
select
  checked_at,
  to_char(checked_at - interval '3 hours', 'DD/MM/YYYY HH24:MI') as checked_at_br,
  ultima_execucao_discovery,
  to_char(ultima_execucao_discovery - interval '3 hours', 'DD/MM/YYYY HH24:MI') as ultima_execucao_discovery_br,
  ultima_descoberta_de_post,
  to_char(ultima_descoberta_de_post - interval '3 hours', 'DD/MM/YYYY HH24:MI') as ultima_descoberta_de_post_br,
  idade_da_ultima_execucao_minutos,
  idade_da_ultima_descoberta_minutos,
  creators_avaliados_24h,
  novos_posts_24h,
  case
    when ultima_execucao_discovery is null then 'nok'
    when idade_da_ultima_execucao_minutos <= 390 then 'ok'
    when idade_da_ultima_execucao_minutos <= 720 then 'atencao'
    else 'nok'
  end as status_code,
  case
    when ultima_execucao_discovery is null then 'Discovery sem evidencia'
    when idade_da_ultima_execucao_minutos <= 390 then 'Discovery em dia'
    when idade_da_ultima_execucao_minutos <= 720 then 'Discovery com atraso'
    else 'Discovery sem evidencia recente'
  end as status_label,
  case
    when ultima_execucao_discovery is null then 'Nenhum snapshot de canal encontrado em creator_metrics_history.'
    when idade_da_ultima_execucao_minutos <= 390 then 'Worker executou dentro da janela esperada de 6 horas.'
    when idade_da_ultima_execucao_minutos <= 720 then 'Worker executou acima da janela ideal, mas ainda dentro do limite de atencao.'
    else 'Worker sem evidencia recente acima do limite tolerado para o ciclo de 6 horas.'
  end as status_reason
from classified;

grant select on public.v_dashboard_new_post_discovery_status to anon;
grant select on public.v_dashboard_new_post_discovery_status to authenticated;
