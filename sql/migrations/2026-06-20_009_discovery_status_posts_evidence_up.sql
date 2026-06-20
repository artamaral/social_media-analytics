-- Migration: 2026-06-20_009_discovery_status_posts_evidence_up
-- Objetivo:
-- - Ajustar o status do discovery para usar os dados existentes no banco.
-- - Usar `posts.created_at` como evidencia de resultado do discovery.
-- - Manter `creator_metrics_history` como evidencia legada/auxiliar, nao como
--   unica fonte para marcar o worker como `nok`.
-- - Nao altera o worker `youtube_main_scraper`.

drop view if exists public.v_dashboard_new_post_discovery_status;

create view public.v_dashboard_new_post_discovery_status as
with latest_execution as (
  select
    max(collected_at)::timestamp as ultima_execucao_discovery,
    count(distinct creator_id) filter (
      where collected_at >= now() - interval '24 hours'
    ) as creators_avaliados_24h
  from public.creator_metrics_history
  where source = 'youtube_channels_api'
),
latest_discovery as (
  select
    max(created_at) as ultima_descoberta_de_post,
    count(*) filter (where created_at >= now()::timestamp - interval '24 hours') as novos_posts_24h,
    count(*) filter (where created_at >= now()::timestamp - interval '6 hours') as novos_posts_6h,
    count(*) filter (where created_at >= now()::timestamp - interval '3 hours') as novos_posts_3h
  from public.posts
),
classified as (
  select
    now()::timestamp as checked_at,
    latest_execution.ultima_execucao_discovery,
    latest_execution.creators_avaliados_24h,
    ultima_descoberta_de_post,
    novos_posts_24h,
    novos_posts_6h,
    novos_posts_3h,
    nullif(
      greatest(
        coalesce(latest_execution.ultima_execucao_discovery, timestamp '1970-01-01'),
        coalesce(ultima_descoberta_de_post, timestamp '1970-01-01')
      ),
      timestamp '1970-01-01'
    ) as ultima_evidencia_discovery,
    case
      when latest_execution.ultima_execucao_discovery is null then null
      else floor(extract(epoch from (now()::timestamp - latest_execution.ultima_execucao_discovery)) / 60)::int
    end as idade_da_ultima_execucao_minutos,
    case
      when ultima_descoberta_de_post is null then null
      else floor(extract(epoch from (now()::timestamp - ultima_descoberta_de_post)) / 60)::int
    end as idade_da_ultima_descoberta_minutos
  from latest_execution
  cross join latest_discovery
),
enriched as (
  select
    *,
    case
      when ultima_evidencia_discovery is null then null
      when ultima_evidencia_discovery = ultima_descoberta_de_post then 'post_insert'
      when ultima_evidencia_discovery = ultima_execucao_discovery then 'channel_snapshot_legacy'
      else 'unknown'
    end as fonte_ultima_evidencia,
    case
      when ultima_evidencia_discovery is null then null
      else floor(extract(epoch from (checked_at - ultima_evidencia_discovery)) / 60)::int
    end as idade_da_ultima_evidencia_minutos
  from classified
)
select
  checked_at,
  to_char(checked_at - interval '3 hours', 'DD/MM/YYYY HH24:MI') as checked_at_br,
  ultima_execucao_discovery,
  to_char(ultima_execucao_discovery - interval '3 hours', 'DD/MM/YYYY HH24:MI') as ultima_execucao_discovery_br,
  ultima_descoberta_de_post,
  to_char(ultima_descoberta_de_post - interval '3 hours', 'DD/MM/YYYY HH24:MI') as ultima_descoberta_de_post_br,
  ultima_evidencia_discovery,
  to_char(ultima_evidencia_discovery - interval '3 hours', 'DD/MM/YYYY HH24:MI') as ultima_evidencia_discovery_br,
  fonte_ultima_evidencia,
  idade_da_ultima_execucao_minutos,
  idade_da_ultima_descoberta_minutos,
  idade_da_ultima_evidencia_minutos,
  creators_avaliados_24h,
  novos_posts_24h,
  novos_posts_6h,
  novos_posts_3h,
  case
    when novos_posts_6h > 0 then 'ok'
    when novos_posts_24h > 0 then 'atencao'
    when idade_da_ultima_execucao_minutos <= 390 then 'ok'
    when idade_da_ultima_execucao_minutos <= 720 then 'atencao'
    else 'nok'
  end as status_code,
  case
    when novos_posts_6h > 0 then 'Discovery com posts recentes'
    when novos_posts_24h > 0 then 'Discovery com posts nas ultimas 24h'
    when idade_da_ultima_execucao_minutos <= 390 then 'Discovery em dia'
    when idade_da_ultima_execucao_minutos <= 720 then 'Discovery com atraso'
    else 'Discovery sem evidencia recente'
  end as status_label,
  case
    when novos_posts_6h > 0 then 'Ha posts inseridos nas ultimas 6 horas, confirmando resultado recente do discovery.'
    when novos_posts_24h > 0 then 'Ha posts inseridos nas ultimas 24 horas, mas nenhum nas ultimas 6 horas; sem heartbeat, isso comprova resultado recente, nao a ultima execucao sem novos posts.'
    when idade_da_ultima_execucao_minutos <= 390 then 'Snapshot legado de canal atualizado dentro da janela de 6 horas.'
    when idade_da_ultima_execucao_minutos <= 720 then 'Snapshot legado de canal acima da janela ideal, mas ainda dentro do limite de atencao.'
    else 'Sem posts novos nas ultimas 24 horas e sem snapshot legado recente; nao ha evidencia recente no banco.'
  end as status_reason
from enriched;

grant select on public.v_dashboard_new_post_discovery_status to anon;
grant select on public.v_dashboard_new_post_discovery_status to authenticated;

-- Validacao sugerida:
-- select
--   checked_at_br,
--   status_code,
--   status_label,
--   status_reason,
--   ultima_execucao_discovery_br,
--   ultima_descoberta_de_post_br,
--   ultima_evidencia_discovery_br,
--   fonte_ultima_evidencia,
--   novos_posts_24h,
--   novos_posts_6h,
--   novos_posts_3h
-- from public.v_dashboard_new_post_discovery_status;
