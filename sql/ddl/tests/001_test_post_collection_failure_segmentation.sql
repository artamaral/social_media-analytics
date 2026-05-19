begin;

do $$
declare
  suffix text := substr(md5(clock_timestamp()::text), 1, 12);
  returned_id text := 'codex_test_returned_' || suffix;
  missing_id text := 'codex_test_missing_' || suffix;
  missing_count integer;
  returned_failure_rows integer;
  missing_failure_count integer;
  missing_status text;
  review_url text;
begin
  insert into public.posts (post_id, title, video_type)
  values
    (returned_id, 'Codex test returned video', 'long'),
    (missing_id, 'Codex test missing video', 'long');

  perform *
  from public.register_post_collection_result(
    array[returned_id, missing_id],
    array[returned_id]
  );

  select count(*)
  into missing_count
  from public.post_collection_failures
  where post_id = missing_id
    and status = 'unavailable_candidate'
    and failure_count = 1;

  if missing_count <> 1 then
    raise exception 'Expected exactly one unavailable_candidate row for missing_id, found %', missing_count;
  end if;

  select count(*)
  into returned_failure_rows
  from public.post_collection_failures
  where post_id = returned_id;

  if returned_failure_rows <> 0 then
    raise exception 'Returned healthy ID should not create a failure row, found %', returned_failure_rows;
  end if;

  select youtube_url
  into review_url
  from public.post_collection_failures
  where post_id = missing_id;

  if review_url <> 'https://www.youtube.com/watch?v=' || missing_id then
    raise exception 'Unexpected youtube_url: %', review_url;
  end if;

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

  perform *
  from public.register_post_collection_result(
    array[missing_id],
    array[missing_id]
  );

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

rollback;
