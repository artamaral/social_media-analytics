-- Migration: 2026-06-15_004_queue_next_check_age_coverage_up
-- Objetivo:
-- Desacelerar a rechecagem de posts warm/old ja cobertos para reduzir
-- concentracao da fila em posts antigos e saturados.
--
-- Regra:
-- - total_checagens < 3: preserva politica atual e guardrail
-- - new_0_3d e recent_4_7d: preserva politica atual
-- - warm_8_30d e old_30d_plus com total_checagens >= 3:
--   - priority_band 5/6: minimo 12h
--   - priority_band 1/2/3/4: minimo 24h
--
-- Observacao:
-- A funcao antiga calculate_next_check(priority_score, checked_at) permanece
-- para compatibilidade. Esta migracao cria uma sobrecarga com post_date e
-- total_checagens e ajusta o trigger de rechecagem para usa-la.

begin;

create or replace function public.calculate_next_check(
  p_priority_score double precision,
  p_checked_at timestamp without time zone,
  p_post_date timestamp without time zone,
  p_total_checagens integer
)
returns timestamp without time zone
language sql
immutable
as $$
  with base as (
    select
      coalesce(p_checked_at, timestamp '1970-01-01 00:00:00') as checked_at,
      public.calculate_priority_band(p_priority_score) as priority_band,
      coalesce(p_total_checagens, 0) as total_checagens,
      public.calculate_next_check(
        p_priority_score,
        coalesce(p_checked_at, timestamp '1970-01-01 00:00:00')
      ) as base_next_check,
      case
        when p_post_date is null then 'unknown'
        when p_post_date >= coalesce(p_checked_at, timestamp '1970-01-01 00:00:00') - interval '3 days'
          then 'new_0_3d'
        when p_post_date >= coalesce(p_checked_at, timestamp '1970-01-01 00:00:00') - interval '7 days'
          then 'recent_4_7d'
        when p_post_date >= coalesce(p_checked_at, timestamp '1970-01-01 00:00:00') - interval '30 days'
          then 'warm_8_30d'
        else 'old_30d_plus'
      end as video_age_bucket
  )
  select case
    when total_checagens < 3 then base_next_check
    when video_age_bucket in ('new_0_3d', 'recent_4_7d', 'unknown') then base_next_check
    when video_age_bucket in ('warm_8_30d', 'old_30d_plus')
      and priority_band in (5, 6)
      then greatest(base_next_check, checked_at + interval '12 hours')
    when video_age_bucket in ('warm_8_30d', 'old_30d_plus')
      then greatest(base_next_check, checked_at + interval '24 hours')
    else base_next_check
  end
  from base
$$;

comment on function public.calculate_next_check(
  double precision,
  timestamp without time zone,
  timestamp without time zone,
  integer
) is 'Define next_check considerando prioridade, idade do post e cobertura historica minima.';

create or replace function public.refresh_post_queue_on_metrics()
returns trigger
language plpgsql
as $$
declare
  v_priority_score double precision;
  v_checked_at timestamp without time zone;
  v_post_date timestamp without time zone;
  v_total_checagens integer;
begin
  v_checked_at := coalesce(new.collected_at, now());

  v_priority_score := public.calculate_post_priority(
    new.views,
    new.likes,
    new.comments
  );

  select p.post_date
  into v_post_date
  from public.posts p
  where p.post_id = new.post_id;

  select count(*)::integer
  into v_total_checagens
  from public.post_metrics_history h
  where h.post_id = new.post_id;

  insert into public.post_update_queue (
    post_id,
    priority_score,
    last_checked,
    next_check,
    needs_update
  )
  values (
    new.post_id,
    v_priority_score,
    v_checked_at,
    public.calculate_next_check(
      v_priority_score,
      v_checked_at,
      v_post_date,
      v_total_checagens
    ),
    true
  )
  on conflict (post_id) do update
  set
    priority_score = excluded.priority_score,
    last_checked = excluded.last_checked,
    next_check = excluded.next_check,
    needs_update = excluded.needs_update;

  return new;
end;
$$;

comment on function public.refresh_post_queue_on_metrics()
is 'Reagenda automaticamente a fila apos cada nova coleta, considerando idade do post e cobertura historica.';

-- Recalcula a fila existente para que a regra passe a valer sem esperar
-- todos os posts serem coletados novamente.
with checks as (
  select
    post_id,
    count(*)::integer as total_checagens
  from public.post_metrics_history
  group by post_id
)
update public.post_update_queue q
set
  next_check = public.calculate_next_check(
    q.priority_score,
    q.last_checked::timestamp without time zone,
    p.post_date,
    coalesce(c.total_checagens, 0)
  )
from public.posts p
left join checks c
  on c.post_id = p.post_id
where p.post_id = q.post_id
  and q.last_checked is not null;

create or replace view public.v_dashboard_queue_bottleneck_status as
with checks as (
  select
    post_id,
    count(*) as total_checagens,
    max(collected_at) as last_snapshot_at
  from public.post_metrics_history
  group by post_id
),
current_batch as (
  select post_id
  from public.v_post_update_queue_batch
),
classified as (
  select
    p.post_id,
    p.post_date,
    q.priority_score,
    public.calculate_priority_band(q.priority_score) as priority_band,
    q.last_checked,
    q.next_check,
    coalesce(c.total_checagens, 0) as total_checagens,
    coalesce(c.last_snapshot_at, q.last_checked::timestamp, p.created_at) as effective_last_check,
    extract(
      epoch from (
        now()::timestamp - coalesce(c.last_snapshot_at, q.last_checked::timestamp, p.created_at)
      )
    ) / 86400 as staleness_days,
    case
      when b.post_id is not null then true
      else false
    end as in_current_batch,
    case
      when q.next_check <= now()::timestamp then true
      else false
    end as is_due_now,
    case
      when p.post_date >= now()::timestamp - interval '3 days' then 'new_0_3d'
      when p.post_date >= now()::timestamp - interval '7 days' then 'recent_4_7d'
      when p.post_date >= now()::timestamp - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket,
    case
      when coalesce(c.total_checagens, 0) < 3 then 'needs_coverage'
      when coalesce(c.total_checagens, 0) between 3 and 49 then 'covered_3_49'
      when coalesce(c.total_checagens, 0) between 50 and 199 then 'overchecked_50_199'
      when coalesce(c.total_checagens, 0) between 200 and 499 then 'overchecked_200_499'
      else 'overchecked_500_plus'
    end as check_band
  from public.post_update_queue q
  join public.posts p
    on p.post_id = q.post_id
  left join checks c
    on c.post_id = q.post_id
  left join current_batch b
    on b.post_id = q.post_id
  left join public.post_collection_failures f
    on f.post_id = q.post_id
  where q.needs_update = true
    and coalesce(f.status, 'active') <> 'unavailable'
)
select
  priority_band,
  video_age_bucket,
  check_band,
  count(*) as total_posts,
  round(avg(total_checagens)::numeric, 2) as media_checagens,
  max(total_checagens) as max_checagens,
  round(avg(staleness_days)::numeric, 2) as avg_staleness_days,
  round(
    (percentile_cont(0.5) within group (order by staleness_days))::numeric,
    2
  ) as p50_staleness_days,
  round(
    (percentile_cont(0.9) within group (order by staleness_days))::numeric,
    2
  ) as p90_staleness_days,
  round(
    (percentile_cont(0.95) within group (order by staleness_days))::numeric,
    2
  ) as p95_staleness_days,
  round(max(staleness_days)::numeric, 2) as max_staleness_days,
  count(*) filter (
    where staleness_days > 3.2
  ) as posts_acima_3_2d,
  count(*) filter (
    where staleness_days > 5
  ) as posts_acima_5d,
  count(*) filter (
    where staleness_days > 7
  ) as posts_acima_7d,
  count(*) filter (
    where is_due_now
  ) as posts_vencidos,
  count(*) filter (
    where in_current_batch
  ) as posts_no_batch_atual,
  min(effective_last_check) as oldest_effective_last_check,
  max(effective_last_check) as newest_effective_last_check,
  min(next_check) filter (
    where is_due_now
  ) as next_check_mais_atrasado
from classified
group by
  priority_band,
  video_age_bucket,
  check_band;

commit;

-- Validacao sugerida pos-migration:
-- 1. Confirmar assinatura nova:
-- select public.calculate_next_check(
--   1000000,
--   timestamp '2026-06-15 12:00:00',
--   timestamp '2026-03-01 12:00:00',
--   900
-- );
-- Esperado: 2026-06-16 00:00:00 (minimo 12h para old band 6 coberto).
--
-- 2. Confirmar que needs_coverage preserva regra atual:
-- select public.calculate_next_check(
--   1000000,
--   timestamp '2026-06-15 12:00:00',
--   timestamp '2026-03-01 12:00:00',
--   2
-- );
-- Esperado: 2026-06-15 12:30:00.
