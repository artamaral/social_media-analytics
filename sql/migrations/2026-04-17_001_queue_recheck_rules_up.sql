-- Migration: 2026-04-17_001_queue_recheck_rules_up
-- Objetivo:
-- Centralizar no banco as regras de prioridade e rechecagem periodica.
--
-- Altera:
-- - create/replace function public.calculate_post_priority
-- - create/replace function public.calculate_next_check
-- - create/replace function public.sync_post_latest
-- - create/replace function public.add_to_queue
-- - create/replace function public.refresh_post_queue_on_metrics
-- - trigger trg_sync_post
-- - trigger trg_refresh_post_queue
-- - trigger trigger_add_to_queue
--
-- Motivacao:
-- Evitar regra de negocio no worker Python e permitir ajuste de frequencia via SQL.
--
-- Impacto esperado:
-- Posts com maior prioridade serao rechecados com maior frequencia.
-- Novas coletas atualizam automaticamente a fila.
--
-- Pre-condicoes:
-- - Tabelas public.posts, public.post_metrics_history e public.post_update_queue existentes.
-- - Permissao para criar functions e triggers.
--
-- Pos-validacao sugerida:
-- Verificar pg_proc, pg_trigger e amostragem de post_update_queue.

-- Migration

begin;

-- =========================================================
-- MIGRATION: centraliza regras de priorizacao e rechecagem no SQL
-- Objetivo:
-- 1. Garantir que os triggers existam como funcoes executaveis
-- 2. Recalcular prioridade no banco
-- 3. Definir proximo next_check no banco
-- 4. Recolocar o post na fila automaticamente a cada nova coleta
-- =========================================================

-- ---------------------------------------------------------
-- 1) Funcao de prioridade
-- Regra de negocio atual:
-- views + likes * 10 + comments * 20
-- ---------------------------------------------------------
create or replace function public.calculate_post_priority(
  p_views integer,
  p_likes integer,
  p_comments integer
)
returns double precision
language sql
immutable
as $$
  select
    coalesce(p_views, 0) * 1 +
    coalesce(p_likes, 0) * 10 +
    coalesce(p_comments, 0) * 20
$$;

comment on function public.calculate_post_priority(integer, integer, integer)
is 'Calcula a prioridade do post para ordenacao da fila de rechecagem.';


-- ---------------------------------------------------------
-- 2) Funcao de agendamento
-- Regra sugerida:
-- score >= 50000 -> 1h
-- score >= 20000 -> 3h
-- score >= 5000  -> 6h
-- score < 5000   -> 12h
-- ---------------------------------------------------------
create or replace function public.calculate_next_check(
  p_priority_score double precision,
  p_checked_at timestamp without time zone default now()
)
returns timestamp without time zone
language sql
immutable
as $$
  select case
    when coalesce(p_priority_score, 0) >= 50000 then p_checked_at + interval '1 hour'
    when coalesce(p_priority_score, 0) >= 20000 then p_checked_at + interval '3 hours'
    when coalesce(p_priority_score, 0) >= 5000 then p_checked_at + interval '6 hours'
    else p_checked_at + interval '12 hours'
  end
$$;

comment on function public.calculate_next_check(double precision, timestamp without time zone)
is 'Define o proximo horario de rechecagem com base na prioridade do post.';


-- ---------------------------------------------------------
-- 3) Trigger function: sincroniza posts com o ultimo historico
-- ---------------------------------------------------------
create or replace function public.sync_post_latest()
returns trigger
language plpgsql
as $$
begin
  update public.posts
  set
    views = new.views,
    likes = new.likes,
    comments = new.comments,
    collected_at = new.collected_at
  where post_id = new.post_id;

  return new;
end;
$$;

comment on function public.sync_post_latest()
is 'Atualiza a tabela posts com os dados mais recentes inseridos em post_metrics_history.';


-- ---------------------------------------------------------
-- 4) Trigger function: coloca post novo na fila
-- Usada no insert inicial em posts
-- ---------------------------------------------------------
create or replace function public.add_to_queue()
returns trigger
language plpgsql
as $$
declare
  v_priority_score double precision;
begin
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
    null,
    now(),
    true
  )
  on conflict (post_id) do nothing;

  return new;
end;
$$;

comment on function public.add_to_queue()
is 'Insere posts novos na fila de atualizacao com prioridade inicial e elegibilidade imediata.';


-- ---------------------------------------------------------
-- 5) Trigger function: atualiza a fila apos cada nova coleta
-- Regra central da recorrencia:
-- - recalcula prioridade
-- - atualiza last_checked
-- - agenda next_check
-- - mantem needs_update = true
-- ---------------------------------------------------------
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


-- ---------------------------------------------------------
-- 6) Garante trigger de sincronizacao do historico -> posts
-- ---------------------------------------------------------
drop trigger if exists trg_sync_post on public.post_metrics_history;

create trigger trg_sync_post
after insert on public.post_metrics_history
for each row
execute function public.sync_post_latest();


-- ---------------------------------------------------------
-- 7) Garante trigger de rechecagem do historico -> queue
-- ---------------------------------------------------------
drop trigger if exists trg_refresh_post_queue on public.post_metrics_history;

create trigger trg_refresh_post_queue
after insert on public.post_metrics_history
for each row
execute function public.refresh_post_queue_on_metrics();


-- ---------------------------------------------------------
-- 8) Garante trigger de insercao inicial de posts -> queue
-- Mantem consistencia mesmo se o banco ja tiver sido alterado antes
-- ---------------------------------------------------------
drop trigger if exists trigger_add_to_queue on public.posts;

create trigger trigger_add_to_queue
after insert on public.posts
for each row
execute function public.add_to_queue();

commit;

-- =========================================================
-- VALIDACAO POS-MIGRATION
-- Rode separadamente depois do commit, se quiser validar
-- =========================================================
-- select proname
-- from pg_proc
-- where proname in (
--   'calculate_post_priority',
--   'calculate_next_check',
--   'sync_post_latest',
--   'add_to_queue',
--   'refresh_post_queue_on_metrics'
-- );

-- select tgname, tgrelid::regclass, tgfoid::regprocedure
-- from pg_trigger
-- where tgname in (
--   'trigger_add_to_queue',
--   'trg_sync_post',
--   'trg_refresh_post_queue'
-- );

-- select *
-- from public.post_update_queue
-- order by last_checked desc nulls last
-- limit 20;



