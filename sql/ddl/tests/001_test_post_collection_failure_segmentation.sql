begin;

-- Teste transacional da segregacao de videos ausentes.
--
-- Entrada geral:
-- - cria dois post_ids sinteticos na tabela `posts`
-- - simula chamadas a `register_post_collection_result(...)`
--
-- Saida esperada:
-- - somente o ID solicitado e nao retornado vira `unavailable_candidate`
-- - o ID retornado e saudavel nao cria linha em `post_collection_failures`
-- - a URL completa de revisao e gerada corretamente
-- - apos 3 falhas, o video vira `unavailable`
-- - se o video voltar na API, ele vira `recovered`
-- - tudo e revertido ao final pelo `rollback`
do $$
declare
  -- Dados de entrada sinteticos.
  -- O sufixo evita colisao com execucoes anteriores ou paralelas.
  suffix text := substr(md5(clock_timestamp()::text), 1, 12);
  returned_id text := 'codex_test_returned_' || suffix;
  missing_id text := 'codex_test_missing_' || suffix;

  -- Variaveis usadas para capturar as saidas intermediarias das validacoes.
  missing_count integer;
  returned_failure_rows integer;
  missing_failure_count integer;
  missing_status text;
  review_url text;
begin
  -- Entrada: cadastra dois posts temporarios.
  -- Saida esperada: ambos ficam disponiveis para a FK de
  -- `post_collection_failures.post_id`.
  insert into public.posts (post_id, title, video_type)
  values
    (returned_id, 'Codex test returned video', 'long'),
    (missing_id, 'Codex test missing video', 'long');

  -- Entrada: envia dois IDs como solicitados e apenas um como retornado.
  -- Saida esperada: `missing_id` deve ser segregado; `returned_id` nao.
  perform *
  from public.register_post_collection_result(
    array[returned_id, missing_id],
    array[returned_id]
  );

  -- Entrada: consulta o ID que nao voltou da API.
  -- Saida esperada: uma unica linha como `unavailable_candidate`
  -- com `failure_count = 1`.
  select count(*)
  into missing_count
  from public.post_collection_failures
  where post_id = missing_id
    and status = 'unavailable_candidate'
    and failure_count = 1;

  if missing_count <> 1 then
    raise exception 'Expected exactly one unavailable_candidate row for missing_id, found %', missing_count;
  end if;

  -- Entrada: consulta o ID saudavel que voltou da API.
  -- Saida esperada: nenhuma linha de falha criada para esse ID.
  select count(*)
  into returned_failure_rows
  from public.post_collection_failures
  where post_id = returned_id;

  if returned_failure_rows <> 0 then
    raise exception 'Returned healthy ID should not create a failure row, found %', returned_failure_rows;
  end if;

  -- Entrada: consulta a URL gerada para revisao humana.
  -- Saida esperada: URL completa do YouTube montada a partir de `post_id`.
  select youtube_url
  into review_url
  from public.post_collection_failures
  where post_id = missing_id;

  if review_url <> 'https://www.youtube.com/watch?v=' || missing_id then
    raise exception 'Unexpected youtube_url: %', review_url;
  end if;

  -- Entrada: simula mais duas chamadas validas onde o mesmo ID nao volta.
  -- Saida esperada: o contador de falhas chega a 3.
  perform *
  from public.register_post_collection_result(
    array[missing_id],
    array[]::text[]
  );

  perform *
  from public.register_post_collection_result(
    array[missing_id],
    array[]::text[]
  );

  -- Entrada: consulta o estado apos 3 falhas acumuladas.
  -- Saida esperada: `failure_count = 3` e `status = unavailable`.
  select failure_count, status
  into missing_failure_count, missing_status
  from public.post_collection_failures
  where post_id = missing_id;

  if missing_failure_count <> 3 or missing_status <> 'unavailable' then
    raise exception
      'Expected missing_id to become unavailable after 3 failures, got count %, status %',
      missing_failure_count,
      missing_status;
  end if;

  -- Entrada: simula uma chamada posterior onde o ID antes ausente voltou.
  -- Saida esperada: o registro deve ser recuperado, nao permanecer bloqueado.
  perform *
  from public.register_post_collection_result(
    array[missing_id],
    array[missing_id]
  );

  -- Entrada: consulta o estado final apos recovery.
  -- Saida esperada: `failure_count = 0` e `status = recovered`.
  select failure_count, status
  into missing_failure_count, missing_status
  from public.post_collection_failures
  where post_id = missing_id;

  if missing_failure_count <> 0 or missing_status <> 'recovered' then
    raise exception
      'Expected missing_id to recover after returning from YouTube, got count %, status %',
      missing_failure_count,
      missing_status;
  end if;

  raise notice 'post_collection_failure_segmentation test passed';
end;
$$;

-- Saida final do arquivo:
-- - nenhuma alteracao persistida no banco
-- - qualquer falha anterior aborta a transacao com `raise exception`
rollback;
