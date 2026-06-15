-- Migration: 2026-06-15_005_dashboard_queue_batch_timezone_up
-- Objetivo:
-- - Criar uma view de dashboard para leitura humana da fila atual.
-- - Preservar `public.v_post_update_queue_batch` como fonte operacional do worker.
-- - Expor `next_check` em UTC e America/Sao_Paulo para evitar confusao visual.

drop view if exists public.v_dashboard_post_update_queue_batch;

create view public.v_dashboard_post_update_queue_batch as
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
  (b.next_check at time zone 'UTC') at time zone 'America/Sao_Paulo' as next_check_br,
  (b.next_check at time zone 'UTC') <= now() as vencido_pela_regra_atual,
  floor(
    extract(epoch from (now() - (b.next_check at time zone 'UTC'))) / 60
  )::integer as atraso_minutos
from public.v_post_update_queue_batch b;

grant select on public.v_dashboard_post_update_queue_batch to anon;
grant select on public.v_dashboard_post_update_queue_batch to authenticated;

-- Validacao sugerida:
-- select
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
