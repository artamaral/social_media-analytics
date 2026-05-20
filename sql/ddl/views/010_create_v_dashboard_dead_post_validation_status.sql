drop view if exists public.v_dashboard_dead_post_validation_status;

create view public.v_dashboard_dead_post_validation_status as
with dead_posts as (
  select
    post_id,
    status,
    human_review_status
  from public.post_collection_failures
  where status in ('unavailable_candidate', 'unavailable')
)
select
  now() as checked_at,
  count(*) as total_dead_posts,
  count(*) filter (where status = 'unavailable_candidate') as unavailable_candidates,
  count(*) filter (where status = 'unavailable') as unavailable_confirmed_by_system,
  count(*) filter (where human_review_status is null) as pending_human_review,
  count(*) filter (where human_review_status = 'confirmed_unavailable') as confirmed_unavailable,
  count(*) filter (where human_review_status = 'available_on_manual_check') as available_on_manual_check,
  count(*) filter (where human_review_status = 'unclear') as unclear,
  case
    when count(*) filter (where human_review_status is null) = 0
      then true
    else false
  end as dead_posts_review_ready
from dead_posts;

grant select on public.v_dashboard_dead_post_validation_status to anon;
grant select on public.v_dashboard_dead_post_validation_status to authenticated;
