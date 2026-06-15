-- Migration: 2026-06-15_006_post_update_queue_next_check_timestamptz_down
-- Rollback bloqueado por seguranca.
--
-- Esta migration altera o contrato de tipo de `post_update_queue.next_check`
-- e exige recriacao coordenada das views dependentes. Reverter automaticamente
-- sem revisar o estado atual do Supabase pode derrubar views usadas pelo worker
-- e pelo dashboard.
--
-- Se for necessario voltar ao contrato antigo:
-- 1. parar o worker de postMetrics
-- 2. exportar as definicoes atuais das views dependentes
-- 3. dropar as views dependentes
-- 4. executar:
--      alter table public.post_update_queue
--        alter column next_check type timestamp without time zone
--        using next_check at time zone 'UTC';
-- 5. recriar as views no contrato antigo
-- 6. validar `public.v_post_update_queue_batch`

do $$
begin
  raise exception
    'Rollback automatico bloqueado: reverta manualmente post_update_queue.next_check e views dependentes.';
end;
$$;
