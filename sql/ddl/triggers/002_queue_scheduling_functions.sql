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
