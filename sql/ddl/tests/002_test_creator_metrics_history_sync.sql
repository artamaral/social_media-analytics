-- Teste controlado da sincronizacao entre creator_metrics_history e creators.
-- Executar em transacao. O rollback evita persistir dados de teste.

begin;

do $$
declare
  v_creator_id integer;
  v_new_collected_at timestamp with time zone := now();
  v_current_followers bigint;
  v_current_source text;
begin
  select
    id
  into
    v_creator_id
  from public.creators
  where platform = 'youtube'
  order by id
  limit 1;

  if v_creator_id is null then
    raise exception 'Nenhum creator do YouTube encontrado para teste';
  end if;

  insert into public.creator_metrics_history (
    creator_id,
    followers,
    channel_view_count,
    channel_video_count,
    hidden_subscriber_count,
    collected_at,
    source
  )
  values (
    v_creator_id,
    123456,
    999999,
    321,
    false,
    v_new_collected_at,
    'test_creator_metrics_history_sync'
  );

  select
    followers,
    followers_source
  into
    v_current_followers,
    v_current_source
  from public.creators
  where id = v_creator_id;

  if v_current_followers <> 123456 then
    raise exception 'Trigger nao sincronizou followers. Esperado 123456, obtido %', v_current_followers;
  end if;

  if v_current_source <> 'test_creator_metrics_history_sync' then
    raise exception 'Trigger nao sincronizou source. Obtido %', v_current_source;
  end if;

  insert into public.creator_metrics_history (
    creator_id,
    followers,
    channel_view_count,
    channel_video_count,
    hidden_subscriber_count,
    collected_at,
    source
  )
  values (
    v_creator_id,
    1,
    1,
    1,
    false,
    v_new_collected_at - interval '1 hour',
    'test_old_snapshot'
  );

  select followers into v_current_followers
  from public.creators
  where id = v_creator_id;

  if v_current_followers <> 123456 then
    raise exception 'Snapshot antigo sobrescreveu valor corrente. Obtido %', v_current_followers;
  end if;

  raise notice 'Teste OK para creator_id=%', v_creator_id;
end;
$$;

rollback;
