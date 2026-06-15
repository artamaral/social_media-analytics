-- Migration: 2026-06-15_004_queue_next_check_age_coverage_down
-- Objetivo:
-- Reverter a regra de next_check por idade/cobertura, mantendo apenas a regra
-- historica baseada em priority_score.

begin;

drop view if exists public.v_dashboard_queue_bottleneck_status;

drop function if exists public.calculate_next_check(
  double precision,
  timestamp without time zone,
  timestamp without time zone,
  integer
);

create or replace function public.refresh_post_queue_on_metrics()
returns trigger
language plpgsql
as $$
declare
  v_priority_score double precision;
  v_checked_at timestamp without time zone;
begin
  v_checked_at := coalesce(new.collected_at, now());
  v_priority_score := public.calculate_post_priority(
    new.views,
    new.likes,
    new.comments
  );

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
    public.calculate_next_check(v_priority_score, v_checked_at),
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
is 'Reagenda automaticamente a fila apos cada nova coleta em post_metrics_history.';

update public.post_update_queue q
set next_check = public.calculate_next_check(
  q.priority_score,
  q.last_checked::timestamp without time zone
)
where q.last_checked is not null;

commit;
