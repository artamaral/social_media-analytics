create or replace function public.confirm_unavailable_posts(
  p_post_ids text[],
  p_reviewed_by text,
  p_notes text
)
returns table (
  updated_count integer
)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  normalized_post_ids text[];
  effective_notes text;
begin
  /*
    Confirma em lote os posts revisados manualmente como unavailable.
    A funcao nao remove registros nem altera snapshots; ela apenas
    consolida a revisao humana em post_collection_failures.
  */

  normalized_post_ids := coalesce(
    array(
      select distinct pid
      from unnest(coalesce(p_post_ids, array[]::text[])) as pid
      where pid is not null
        and btrim(pid) <> ''
    ),
    array[]::text[]
  );

  if coalesce(array_length(normalized_post_ids, 1), 0) = 0 then
    return query
    select 0::integer;
    return;
  end if;

  effective_notes := coalesce(
    nullif(btrim(p_notes), ''),
    'Confirmado manualmente no YouTube: video indisponivel.'
  );

  update public.post_collection_failures f
  set
    status = 'unavailable',
    human_review_status = 'confirmed_unavailable',
    human_reviewed_at = now(),
    human_reviewed_by = p_reviewed_by,
    human_review_notes = effective_notes
  where f.post_id = any(normalized_post_ids)
    and f.status in ('unavailable_candidate', 'unavailable');

  get diagnostics updated_count = row_count;

  return query
  select updated_count;
end;
$$;

grant execute on function public.confirm_unavailable_posts(text[], text, text)
  to anon, authenticated, service_role;
