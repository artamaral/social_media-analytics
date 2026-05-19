create or replace function public.register_post_collection_result(
  p_requested_ids text[],
  p_returned_ids text[]
)
returns table (
  post_id text,
  youtube_url text,
  status text,
  failure_count integer,
  action_taken text
)
language plpgsql
as $$
declare
  returned_id text;
  missing_id text;
begin
  /*
    Registra o resultado de uma chamada valida ao YouTube videos.list.
    A chamada deve acontecer somente quando a API respondeu com sucesso.
    Se a API falhar globalmente, o worker nao deve chamar esta funcao para
    evitar marcar videos saudaveis como indisponiveis.
  */

  create temporary table if not exists tmp_post_collection_actions (
    post_id text,
    youtube_url text,
    status text,
    failure_count integer,
    action_taken text
  ) on commit drop;

  truncate table tmp_post_collection_actions;

  foreach returned_id in array coalesce(p_returned_ids, array[]::text[]) loop
    update public.post_collection_failures f
    set
      failure_count = 0,
      last_success_at = now(),
      status = 'recovered',
      last_failure_reason = null
    where f.post_id = returned_id;

    if found then
      insert into tmp_post_collection_actions (
        post_id,
        youtube_url,
        status,
        failure_count,
        action_taken
      )
      select
        f.post_id,
        f.youtube_url,
        f.status,
        f.failure_count,
        'returned'
      from public.post_collection_failures f
      where f.post_id = returned_id;
    end if;
  end loop;

  foreach missing_id in array (
    select coalesce(array_agg(distinct requested_id), array[]::text[])
    from unnest(coalesce(p_requested_ids, array[]::text[])) as requested(requested_id)
    where requested_id is not null
      and not exists (
        select 1
        from unnest(coalesce(p_returned_ids, array[]::text[])) as returned(returned_id)
        where returned.returned_id = requested.requested_id
      )
  ) loop
    insert into public.post_collection_failures (
      post_id,
      failure_count,
      first_failed_at,
      last_failed_at,
      status,
      last_failure_reason
    )
    values (
      missing_id,
      1,
      now(),
      now(),
      'unavailable_candidate',
      'not_returned_by_youtube_videos_list'
    )
    on conflict (post_id) do update
      set
        failure_count = public.post_collection_failures.failure_count + 1,
        last_failed_at = now(),
        status = case
          when public.post_collection_failures.failure_count + 1 >= 3
            then 'unavailable'
          else 'unavailable_candidate'
        end,
        last_failure_reason = 'not_returned_by_youtube_videos_list';

    insert into tmp_post_collection_actions (
      post_id,
      youtube_url,
      status,
      failure_count,
      action_taken
    )
    select
      f.post_id,
      f.youtube_url,
      f.status,
      f.failure_count,
      'missing'
    from public.post_collection_failures f
    where f.post_id = missing_id;
  end loop;

  return query
  select
    a.post_id,
    a.youtube_url,
    a.status,
    a.failure_count,
    a.action_taken
  from tmp_post_collection_actions a
  order by
    case a.action_taken
      when 'missing' then 0
      else 1
    end,
    a.post_id;
end;
$$;
