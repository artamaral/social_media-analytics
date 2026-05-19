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

create or replace function public.calculate_priority_band(
  p_priority_score double precision
)
returns integer
language sql
immutable
as $$
  select case
    when coalesce(p_priority_score, 0) >= 700000 then 6
    when coalesce(p_priority_score, 0) >= 300000 then 5
    when coalesce(p_priority_score, 0) >= 150000 then 4
    when coalesce(p_priority_score, 0) >= 50000 then 3
    when coalesce(p_priority_score, 0) >= 10000 then 2
    else 1
  end
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
    when coalesce(p_priority_score, 0) >= 700000 then p_checked_at + interval '30 minutes'
    when coalesce(p_priority_score, 0) >= 300000 then p_checked_at + interval '1 hour'
    when coalesce(p_priority_score, 0) >= 150000 then p_checked_at + interval '2 hours'
    when coalesce(p_priority_score, 0) >= 50000 then p_checked_at + interval '4 hours'
    when coalesce(p_priority_score, 0) >= 10000 then p_checked_at + interval '8 hours'
    else p_checked_at + interval '12 hours'
  end
$$;
