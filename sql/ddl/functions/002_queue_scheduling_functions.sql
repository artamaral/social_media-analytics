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

create or replace function public.calculate_next_check(
  p_priority_score double precision,
  p_checked_at timestamp without time zone,
  p_post_date timestamp without time zone,
  p_total_checagens integer
)
returns timestamp without time zone
language sql
immutable
as $$
  with base as (
    select
      coalesce(p_checked_at, timestamp '1970-01-01 00:00:00') as checked_at,
      public.calculate_priority_band(p_priority_score) as priority_band,
      coalesce(p_total_checagens, 0) as total_checagens,
      public.calculate_next_check(
        p_priority_score,
        coalesce(p_checked_at, timestamp '1970-01-01 00:00:00')
      ) as base_next_check,
      case
        when p_post_date is null then 'unknown'
        when p_post_date >= coalesce(p_checked_at, timestamp '1970-01-01 00:00:00') - interval '3 days'
          then 'new_0_3d'
        when p_post_date >= coalesce(p_checked_at, timestamp '1970-01-01 00:00:00') - interval '7 days'
          then 'recent_4_7d'
        when p_post_date >= coalesce(p_checked_at, timestamp '1970-01-01 00:00:00') - interval '30 days'
          then 'warm_8_30d'
        else 'old_30d_plus'
      end as video_age_bucket
  )
  select case
    when total_checagens < 3 then base_next_check
    when video_age_bucket in ('new_0_3d', 'recent_4_7d', 'unknown') then base_next_check
    when video_age_bucket = 'warm_8_30d'
      and total_checagens >= 21
      then greatest(base_next_check, checked_at + interval '84 hours')
    when video_age_bucket = 'warm_8_30d'
      and priority_band in (5, 6)
      then greatest(base_next_check, checked_at + interval '12 hours')
    when video_age_bucket = 'warm_8_30d'
      then greatest(base_next_check, checked_at + interval '24 hours')
    when video_age_bucket = 'old_30d_plus'
      and total_checagens >= 21
      then greatest(base_next_check, checked_at + interval '84 hours')
    when video_age_bucket = 'old_30d_plus'
      then greatest(base_next_check, checked_at + interval '24 hours')
    else base_next_check
  end
  from base
$$;
