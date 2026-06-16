-- Export operacional para o simulador offline da fila.
--
-- Local recomendado no projeto:
-- - `sql/dml/`
--
-- Motivo:
-- - esta query nao cria schema nem altera dado;
-- - ela prepara um snapshot operacional para consumo por script local;
-- - o repositorio ja usa `sql/dml/` para auditorias e leituras operacionais da fila.
--
-- Uso esperado:
-- 1. rodar a query no Supabase SQL Editor;
-- 2. exportar o resultado em CSV;
-- 3. usar o CSV como `--input` em:
--    `scripts/queue_simulation/simulate_queue_offline.py`
--
-- Colunas minimas entregues para o script:
-- - `post_id`
-- - `priority_score`
-- - `created_at`
-- - `post_date`
-- - `total_checagens`
-- - `last_checked`
-- - `next_check`
-- - `needs_update`
-- - `failure_status`
--
-- Colunas extras:
-- - `priority_band`
-- - `video_age_bucket`
-- - `check_band`
--
-- Observacao:
-- - o script ignora `failure_status = unavailable`;
-- - manter essa coluna no export ajuda a auditar o snapshot de entrada.

with history_counts as (
  select
    h.post_id,
    count(*)::integer as total_checagens
  from public.post_metrics_history h
  group by h.post_id
),
classified as (
  select
    q.post_id,
    q.priority_score,
    public.calculate_priority_band(q.priority_score) as priority_band,
    p.created_at,
    p.post_date,
    coalesce(h.total_checagens, 0) as total_checagens,
    q.last_checked,
    q.next_check,
    q.needs_update,
    coalesce(f.status, 'active') as failure_status,
    case
      when p.post_date >= now()::timestamp - interval '3 days' then 'new_0_3d'
      when p.post_date >= now()::timestamp - interval '7 days' then 'recent_4_7d'
      when p.post_date >= now()::timestamp - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket,
    case
      when coalesce(h.total_checagens, 0) < 3 then 'needs_coverage'
      when coalesce(h.total_checagens, 0) between 3 and 20 then 'covered_3_20'
      when coalesce(h.total_checagens, 0) between 21 and 100 then 'overchecked_21_100'
      else 'overchecked_101_plus'
    end as check_band
  from public.post_update_queue q
  join public.posts p
    on p.post_id = q.post_id
  left join history_counts h
    on h.post_id = q.post_id
  left join public.post_collection_failures f
    on f.post_id = q.post_id
  where q.needs_update = true
)
select
  post_id,
  priority_score,
  priority_band,
  created_at,
  post_date,
  total_checagens,
  last_checked,
  next_check,
  needs_update,
  failure_status,
  video_age_bucket,
  check_band
from classified
order by
  next_check asc nulls first,
  priority_band desc,
  total_checagens asc,
  post_id;
