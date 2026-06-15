create or replace function public.refresh_post_queue_on_metrics()
returns trigger
language plpgsql
as $$
declare
  v_priority_score double precision;
  v_checked_at timestamp without time zone;
  v_post_date timestamp without time zone;
  v_total_checagens integer;
begin
  v_checked_at := coalesce(new.collected_at, now());
  v_priority_score := public.calculate_post_priority(
    new.views,
    new.likes,
    new.comments
  );

  select p.post_date
  into v_post_date
  from public.posts p
  where p.post_id = new.post_id;

  select count(*)::integer
  into v_total_checagens
  from public.post_metrics_history h
  where h.post_id = new.post_id;

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
    public.calculate_next_check(
      v_priority_score,
      v_checked_at,
      v_post_date,
      v_total_checagens
    ),
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
