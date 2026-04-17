-- Migration: 2026-04-17_001_queue_recheck_rules_down
-- Objetivo:
-- Reverter a centralizacao da regra de rechecagem no banco.
--
-- Reverte:
-- - remove trg_refresh_post_queue
-- - remove refresh_post_queue_on_metrics
-- - remove calculate_next_check
-- - remove calculate_post_priority
--
-- Observacao:
-- sync_post_latest e add_to_queue podem ser mantidas, pois ja fazem parte
-- do desenho original do projeto. Se for necessario voltar completamente,
-- remover manualmente essas funcoes e seus triggers.
--
-- Risco:
-- A fila deixa de ser reagendada automaticamente apos novas coletas.

begin;

drop trigger if exists trg_refresh_post_queue on public.post_metrics_history;

drop function if exists public.refresh_post_queue_on_metrics();
drop function if exists public.calculate_next_check(double precision, timestamp without time zone);
drop function if exists public.calculate_post_priority(integer, integer, integer);

-- Mantem sync_post_latest() e add_to_queue() porque eles ja existiam conceitualmente.
-- Se quiser remover e voltar ao estado sem essas definicoes, descomente abaixo:

-- drop trigger if exists trg_sync_post on public.post_metrics_history;
-- drop trigger if exists trigger_add_to_queue on public.posts;
-- drop function if exists public.sync_post_latest();
-- drop function if exists public.add_to_queue();

commit;

