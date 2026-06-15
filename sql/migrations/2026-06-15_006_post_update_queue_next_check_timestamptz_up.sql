-- Migration: 2026-06-15_006_post_update_queue_next_check_timestamptz_up
-- Objetivo:
-- - Converter post_update_queue.next_check para timestamp with time zone.
-- - Interpretar os valores existentes como UTC, sem antecipar ou atrasar a fila.
-- - Manter v_post_update_queue_batch como fonte operacional do worker.
-- - Recriar views dependentes com leitura explicita de timezone.

drop view if exists public.v_dashboard_post_update_queue_batch;
drop view if exists public.v_dashboard_queue_bottleneck_status;
drop view if exists public.v_dashboard_post_update_operational_signal_items;
drop view if exists public.v_dashboard_post_update_operational_signals;
drop view if exists public.v_post_update_queue_batch_v2;
drop view if exists public.v_post_update_queue_batch;

alter table public.post_update_queue
  alter column next_check type timestamp with time zone
  using next_check at time zone 'UTC';

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
    v_checked_at at time zone 'UTC',
    public.calculate_next_check(
      v_priority_score,
      v_checked_at,
      v_post_date,
      v_total_checagens
    ) at time zone 'UTC',
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

create or replace view public.v_post_update_queue_batch as
with history_counts as (
  select
    post_id,
    count(*) as total_checagens
  from public.post_metrics_history
  group by post_id
),
eligible as (
  select
    q.post_id,
    q.priority_score,
    q.last_checked,
    q.next_check,
    q.needs_update,
    p.created_at,
    coalesce(h.total_checagens, 0) as total_checagens,
    public.calculate_priority_band(q.priority_score) as priority_band
  from public.post_update_queue q
  join public.posts p
    on p.post_id = q.post_id
  left join history_counts h
    on h.post_id = q.post_id
  left join public.post_collection_failures f
    on f.post_id = q.post_id
  where q.needs_update = true
    and q.next_check <= now()
    and coalesce(f.status, 'active') <> 'unavailable'
),
guardrail_ranked as (
  select
    e.*,
    row_number() over (
      order by
        e.total_checagens asc,
        e.created_at asc,
        e.priority_score desc,
        e.post_id
    ) as guardrail_rank
  from eligible e
  where e.total_checagens < 3
),
guardrail_slice as (
  select
    g.post_id,
    g.priority_score,
    g.last_checked,
    g.next_check,
    g.needs_update,
    g.created_at,
    g.total_checagens,
    g.priority_band,
    0 as slice_order
  from guardrail_ranked g
  where g.guardrail_rank <= 4
),
normal_eligible as (
  select e.*
  from eligible e
  where e.total_checagens >= 3
),
quotas as (
  select *
  from (
    values
      (6, 7),
      (5, 7),
      (4, 7),
      (3, 6),
      (2, 5),
      (1, 4)
  ) as t(priority_band, quota)
),
ranked as (
  select
    e.*,
    row_number() over (
      partition by e.priority_band
      order by
        e.next_check asc,
        e.last_checked asc nulls first,
        e.post_id
    ) as band_rank
  from normal_eligible e
),
primary_slice as (
  select
    r.post_id,
    r.priority_score,
    r.last_checked,
    r.next_check,
    r.needs_update,
    r.created_at,
    r.total_checagens,
    r.priority_band,
    1 as slice_order
  from ranked r
  join quotas q
    on q.priority_band = r.priority_band
  where r.band_rank <= q.quota
),
remaining as (
  select
    r.post_id,
    r.priority_score,
    r.last_checked,
    r.next_check,
    r.needs_update,
    r.created_at,
    r.total_checagens,
    r.priority_band,
    row_number() over (
      order by
        r.next_check asc,
        r.last_checked asc nulls first,
        r.priority_band desc,
        r.post_id
    ) as refill_rank
  from ranked r
  where not exists (
    select 1
    from primary_slice p
    where p.post_id = r.post_id
  )
),
final_batch as (
  select * from guardrail_slice
  union all
  select * from primary_slice
  union all
  select
    post_id,
    priority_score,
    last_checked,
    next_check,
    needs_update,
    created_at,
    total_checagens,
    priority_band,
    2 as slice_order
  from remaining
  where refill_rank <= greatest(
    40
    - (select count(*) from guardrail_slice)
    - (select count(*) from primary_slice),
    0
  )
)
select
  post_id,
  priority_score,
  last_checked,
  next_check,
  needs_update,
  priority_band
from final_batch
order by
  slice_order asc,
  case
    when slice_order = 0 then total_checagens
    else null
  end asc nulls last,
  case
    when slice_order = 0 then created_at
    else null
  end asc nulls last,
  priority_band desc,
  next_check asc,
  last_checked asc nulls first,
  post_id
limit 40;

create or replace view public.v_post_update_queue_batch_v2 as
with eligible as (
  select
    q.post_id,
    q.priority_score,
    q.last_checked,
    q.next_check,
    q.needs_update,
    f.priority_score_v2,
    f.priority_band_v2,
    f.proposed_next_check_v2,
    f.history_level,
    f.base_popularity,
    f.velocity_score,
    f.acceleration_score
  from public.post_update_queue q
  join public.v_post_priority_score_features_v2 f
    on f.post_id = q.post_id
  left join public.post_collection_failures cf
    on cf.post_id = q.post_id
  where q.needs_update = true
    and q.next_check <= now()
    and coalesce(cf.status, 'active') <> 'unavailable'
),
quotas as (
  select *
  from (
    values
      (6, 8),
      (5, 8),
      (4, 8),
      (3, 6),
      (2, 6),
      (1, 4)
  ) as t(priority_band_v2, quota)
),
ranked as (
  select
    e.*,
    row_number() over (
      partition by e.priority_band_v2
      order by
        e.next_check asc,
        e.last_checked asc nulls first,
        e.post_id
    ) as band_rank
  from eligible e
),
primary_slice as (
  select
    r.*
  from ranked r
  join quotas q
    on q.priority_band_v2 = r.priority_band_v2
  where r.band_rank <= q.quota
),
remaining as (
  select
    r.*,
    row_number() over (
      order by
        r.next_check asc,
        r.last_checked asc nulls first,
        r.priority_band_v2 desc,
        r.post_id
    ) as refill_rank
  from ranked r
  where not exists (
    select 1
    from primary_slice p
    where p.post_id = r.post_id
  )
),
final_batch as (
  select * from primary_slice
  union all
  select
    post_id,
    priority_score,
    last_checked,
    next_check,
    needs_update,
    priority_score_v2,
    priority_band_v2,
    proposed_next_check_v2,
    history_level,
    base_popularity,
    velocity_score,
    acceleration_score,
    band_rank
  from remaining
  where refill_rank <= greatest(
    40 - (select count(*) from primary_slice),
    0
  )
)
select
  post_id,
  priority_score,
  last_checked,
  next_check,
  needs_update,
  priority_score_v2,
  priority_band_v2,
  proposed_next_check_v2,
  history_level,
  base_popularity,
  velocity_score,
  acceleration_score
from final_batch
order by
  priority_band_v2 desc,
  next_check asc,
  last_checked asc nulls first,
  post_id
limit 40;

create or replace view public.v_dashboard_post_update_operational_signals as
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
      when itens_atrasados_ate_1h > 0 then 'Ha atraso recente, mas ainda dentro da faixa de 1 hora.'
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

create or replace view public.v_dashboard_post_update_operational_signal_items as
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
  to_char(next_check at time zone 'America/Sao_Paulo', 'DD/MM/YYYY HH24:MI') as next_check_br,
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
      when q.next_check <= now() then true
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

create or replace view public.v_dashboard_post_update_queue_batch as
select
  row_number() over (
    order by
      b.priority_band desc,
      b.next_check asc,
      b.last_checked asc nulls first,
      b.post_id
  ) as display_rank,
  now() as checked_at_utc,
  now() at time zone 'America/Sao_Paulo' as checked_at_br,
  b.post_id,
  b.priority_score,
  b.priority_band,
  b.needs_update,
  b.last_checked as last_checked_utc,
  b.last_checked at time zone 'America/Sao_Paulo' as last_checked_br,
  b.next_check as next_check_utc,
  b.next_check at time zone 'America/Sao_Paulo' as next_check_br,
  b.next_check <= now() as vencido_pela_regra_atual,
  floor(
    extract(epoch from (now() - b.next_check)) / 60
  )::integer as atraso_minutos
from public.v_post_update_queue_batch b;

grant select on public.v_dashboard_post_update_queue_batch to anon;
grant select on public.v_dashboard_post_update_queue_batch to authenticated;

-- Validacao sugerida:
-- select
--   column_name,
--   data_type
-- from information_schema.columns
-- where table_schema = 'public'
--   and table_name = 'post_update_queue'
--   and column_name = 'next_check';
--
-- select
--   display_rank,
--   checked_at_utc,
--   checked_at_br,
--   post_id,
--   priority_band,
--   last_checked_utc,
--   last_checked_br,
--   next_check_utc,
--   next_check_br,
--   vencido_pela_regra_atual,
--   atraso_minutos
-- from public.v_dashboard_post_update_queue_batch
-- order by display_rank;
