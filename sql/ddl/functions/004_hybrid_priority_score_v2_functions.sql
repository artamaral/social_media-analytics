create or replace function public.calculate_post_base_popularity_v2(
  p_views integer,
  p_likes integer,
  p_comments integer
)
returns double precision
language sql
immutable
as $$
  select
    ln(coalesce(p_views, 0) + 1)
    + 10 * ln(coalesce(p_likes, 0) + 1)
    + 20 * ln(coalesce(p_comments, 0) + 1)
$$;

create or replace function public.calculate_velocity_raw_v2(
  p_delta_views double precision,
  p_delta_likes double precision,
  p_delta_comments double precision,
  p_hours_elapsed double precision
)
returns double precision
language sql
immutable
as $$
  select case
    when coalesce(p_hours_elapsed, 0) <= 0 then 0
    else
      greatest(coalesce(p_delta_views, 0) / p_hours_elapsed, 0)
      + 10 * greatest(coalesce(p_delta_likes, 0) / p_hours_elapsed, 0)
      + 20 * greatest(coalesce(p_delta_comments, 0) / p_hours_elapsed, 0)
  end
$$;

create or replace function public.calculate_velocity_score_v2(
  p_velocity_raw double precision
)
returns double precision
language sql
immutable
as $$
  select ln(greatest(coalesce(p_velocity_raw, 0), 0) + 1)
$$;

create or replace function public.calculate_acceleration_score_v2(
  p_velocity_raw_short double precision,
  p_velocity_raw_long double precision
)
returns double precision
language sql
immutable
as $$
  select ln(
    greatest(
      coalesce(p_velocity_raw_short, 0) - coalesce(p_velocity_raw_long, 0),
      0
    ) + 1
  )
$$;

create or replace function public.calculate_post_priority_v2(
  p_base_popularity double precision,
  p_velocity_score double precision,
  p_acceleration_score double precision,
  p_history_level text
)
returns double precision
language sql
immutable
as $$
  select case
    when p_history_level = 'full' then
      0.40 * coalesce(p_base_popularity, 0)
      + 0.40 * coalesce(p_velocity_score, 0)
      + 0.20 * coalesce(p_acceleration_score, 0)
    when p_history_level = 'partial' then
      0.60 * coalesce(p_base_popularity, 0)
      + 0.40 * coalesce(p_velocity_score, 0)
    else
      coalesce(p_base_popularity, 0)
  end
$$;

create or replace function public.calculate_priority_band_v2(
  p_priority_score double precision
)
returns integer
language sql
immutable
as $$
  select case
    when coalesce(p_priority_score, 0) >= 120 then 6
    when coalesce(p_priority_score, 0) >= 90 then 5
    when coalesce(p_priority_score, 0) >= 70 then 4
    when coalesce(p_priority_score, 0) >= 50 then 3
    when coalesce(p_priority_score, 0) >= 35 then 2
    else 1
  end
$$;

create or replace function public.calculate_next_check_v2(
  p_priority_score double precision,
  p_checked_at timestamp without time zone default now()
)
returns timestamp without time zone
language sql
immutable
as $$
  select case
    when coalesce(p_priority_score, 0) >= 120 then p_checked_at + interval '30 minutes'
    when coalesce(p_priority_score, 0) >= 90 then p_checked_at + interval '1 hour'
    when coalesce(p_priority_score, 0) >= 70 then p_checked_at + interval '2 hours'
    when coalesce(p_priority_score, 0) >= 50 then p_checked_at + interval '4 hours'
    when coalesce(p_priority_score, 0) >= 35 then p_checked_at + interval '8 hours'
    else p_checked_at + interval '12 hours'
  end
$$;
