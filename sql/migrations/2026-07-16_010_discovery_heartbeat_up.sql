-- Implementa heartbeat dedicado do youtube_main_scraper e reescreve
-- v_dashboard_new_post_discovery_status para priorizar heartbeat sobre
-- evidencias indiretas.

create table if not exists public.youtube_discovery_heartbeats (
  id bigserial primary key,
  started_at timestamp without time zone not null default now(),
  finished_at timestamp without time zone,
  status text not null,
  processed_creators integer not null default 0,
  attempted_creators integer not null default 0,
  inserted_or_updated_posts integer not null default 0,
  errors integer not null default 0,
  total_creators integer,
  batch_size integer,
  cursor_start integer,
  cursor_end integer,
  error_summary text,
  constraint youtube_discovery_heartbeats_status_check check (
    status in ('running', 'success', 'partial_error', 'failed', 'no_creators')
  )
);

create index if not exists youtube_discovery_heartbeats_started_at_idx
  on public.youtube_discovery_heartbeats (started_at desc);

create index if not exists youtube_discovery_heartbeats_status_started_at_idx
  on public.youtube_discovery_heartbeats (status, started_at desc);

comment on table public.youtube_discovery_heartbeats is
  'Heartbeat operacional do youtube_main_scraper, registrando cada execucao do worker de discovery.';

alter table public.youtube_discovery_heartbeats disable row level security;

grant select, insert, update on public.youtube_discovery_heartbeats
  to anon, authenticated, service_role;

grant usage, select on sequence public.youtube_discovery_heartbeats_id_seq
  to anon, authenticated, service_role;

drop view if exists public.v_dashboard_new_post_discovery_status;

create view public.v_dashboard_new_post_discovery_status as
with latest_heartbeat as (
  select
    h.id,
    h.started_at as heartbeat_started_at,
    h.finished_at as heartbeat_finished_at,
    h.status as heartbeat_status,
    h.processed_creators as heartbeat_processed_creators,
    h.attempted_creators as heartbeat_attempted_creators,
    h.inserted_or_updated_posts as heartbeat_inserted_or_updated_posts,
    h.errors as heartbeat_errors,
    h.error_summary as heartbeat_error_summary,
    case
      when h.finished_at is not null then h.finished_at
      else h.started_at
    end as heartbeat_reference_at
  from public.youtube_discovery_heartbeats h
  where h.status <> 'running'
  order by coalesce(h.finished_at, h.started_at) desc, h.id desc
  limit 1
),
latest_execution as (
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
    latest_discovery.ultima_descoberta_de_post,
    latest_discovery.novos_posts_24h,
    latest_discovery.novos_posts_6h,
    latest_discovery.novos_posts_3h,
    latest_heartbeat.heartbeat_started_at,
    latest_heartbeat.heartbeat_finished_at,
    latest_heartbeat.heartbeat_status,
    latest_heartbeat.heartbeat_processed_creators,
    latest_heartbeat.heartbeat_attempted_creators,
    latest_heartbeat.heartbeat_inserted_or_updated_posts,
    latest_heartbeat.heartbeat_errors,
    latest_heartbeat.heartbeat_error_summary,
    latest_heartbeat.heartbeat_reference_at,
    nullif(
      greatest(
        coalesce(latest_heartbeat.heartbeat_reference_at, timestamp '1970-01-01'),
        coalesce(latest_discovery.ultima_descoberta_de_post, timestamp '1970-01-01'),
        coalesce(latest_execution.ultima_execucao_discovery, timestamp '1970-01-01')
      ),
      timestamp '1970-01-01'
    ) as ultima_evidencia_discovery,
    case
      when latest_heartbeat.heartbeat_reference_at is null then null
      else floor(extract(epoch from (now()::timestamp - latest_heartbeat.heartbeat_reference_at)) / 60)::int
    end as idade_do_heartbeat_minutos,
    case
      when latest_execution.ultima_execucao_discovery is null then null
      else floor(extract(epoch from (now()::timestamp - latest_execution.ultima_execucao_discovery)) / 60)::int
    end as idade_da_ultima_execucao_minutos,
    case
      when latest_discovery.ultima_descoberta_de_post is null then null
      else floor(extract(epoch from (now()::timestamp - latest_discovery.ultima_descoberta_de_post)) / 60)::int
    end as idade_da_ultima_descoberta_minutos
  from latest_execution
  cross join latest_discovery
  left join latest_heartbeat on true
),
enriched as (
  select
    *,
    case
      when ultima_evidencia_discovery is null then null
      when heartbeat_reference_at is not null
        and ultima_evidencia_discovery = heartbeat_reference_at then 'heartbeat'
      when ultima_descoberta_de_post is not null
        and ultima_evidencia_discovery = ultima_descoberta_de_post then 'post_insert'
      when ultima_execucao_discovery is not null
        and ultima_evidencia_discovery = ultima_execucao_discovery then 'channel_snapshot_legacy'
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
  heartbeat_started_at,
  heartbeat_finished_at,
  heartbeat_status,
  heartbeat_processed_creators,
  heartbeat_attempted_creators,
  heartbeat_inserted_or_updated_posts,
  heartbeat_errors,
  heartbeat_error_summary,
  case
    when heartbeat_status = 'failed' and idade_do_heartbeat_minutos <= 720 then 'nok'
    when heartbeat_status in ('success', 'no_creators') and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) > 0 then 'ok'
    when heartbeat_status = 'partial_error' and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) > 0 then 'ok'
    when heartbeat_status in ('success', 'no_creators') and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) = 0 then 'ok'
    when heartbeat_status = 'partial_error' and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) = 0 then 'atencao'
    when heartbeat_status in ('success', 'partial_error', 'no_creators') and idade_do_heartbeat_minutos <= 720 then 'atencao'
    when novos_posts_24h > 0 then 'atencao'
    when idade_da_ultima_execucao_minutos <= 720 then 'atencao'
    else 'nok'
  end as status_code,
  case
    when heartbeat_status = 'failed' and idade_do_heartbeat_minutos <= 720 then 'Falhou antes de gerar resultado'
    when heartbeat_status in ('success', 'partial_error') and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) > 0 then 'Discovery com posts recentes'
    when heartbeat_status in ('success', 'no_creators') and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) = 0 then 'Rodou sem novidades'
    when heartbeat_status = 'partial_error' and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) = 0 then 'Rodou com erro parcial'
    when heartbeat_status in ('success', 'partial_error', 'no_creators') and idade_do_heartbeat_minutos <= 720 then 'Heartbeat com atraso'
    when novos_posts_24h > 0 then 'Discovery com posts nas ultimas 24h'
    when idade_da_ultima_execucao_minutos <= 720 then 'Discovery com evidencia legada'
    else 'Discovery sem evidencia recente'
  end as status_label,
  case
    when heartbeat_status = 'failed' and idade_do_heartbeat_minutos <= 720 then
      coalesce(
        'Ultimo heartbeat terminou em failed. ' || heartbeat_error_summary,
        'Ultimo heartbeat terminou em failed antes de produzir evidencia confiavel.'
      )
    when heartbeat_status in ('success', 'partial_error') and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) > 0 then
      'Heartbeat recente confirmou discovery com posts inseridos ou atualizados no banco.'
    when heartbeat_status in ('success', 'no_creators') and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) = 0 then
      'Heartbeat recente confirmou que o worker rodou sem encontrar posts novos.'
    when heartbeat_status = 'partial_error' and idade_do_heartbeat_minutos <= 360
      and coalesce(heartbeat_inserted_or_updated_posts, 0) = 0 then
      'Heartbeat recente confirmou execucao com erro parcial e sem novos posts persistidos.'
    when heartbeat_status in ('success', 'partial_error', 'no_creators') and idade_do_heartbeat_minutos <= 720 then
      'Heartbeat existe, mas ja esta acima da janela ideal de 6 horas e ainda dentro do limite de atencao.'
    when novos_posts_24h > 0 then
      'Ha posts inseridos nas ultimas 24 horas, mas sem heartbeat recente; isso comprova resultado recente, nao a ultima execucao sem novos posts.'
    when idade_da_ultima_execucao_minutos <= 720 then
      'Sem heartbeat recente e sem posts novos, mas o snapshot legado de canal ainda traz evidencia auxiliar dentro do limite de atencao.'
    else
      'Sem heartbeat recente, sem posts novos nas ultimas 24 horas e sem snapshot legado recente; nao ha evidencia recente no banco.'
  end as status_reason
from enriched;

grant select on public.v_dashboard_new_post_discovery_status to anon;
grant select on public.v_dashboard_new_post_discovery_status to authenticated;
