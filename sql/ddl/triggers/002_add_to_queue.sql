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
