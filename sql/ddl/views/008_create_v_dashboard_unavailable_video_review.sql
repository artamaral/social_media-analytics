create or replace view public.v_dashboard_unavailable_video_review as
select
  f.post_id,
  f.youtube_url,
  f.failure_count,
  f.first_failed_at,
  f.last_failed_at,
  f.last_success_at,
  f.status,
  f.last_failure_reason,
  f.human_review_status,
  f.human_reviewed_at,
  f.human_reviewed_by,
  f.human_review_notes,
  p.created_at,
  p.collected_at,
  p.views,
  p.likes,
  p.comments
from public.post_collection_failures f
left join public.posts p
  on p.post_id = f.post_id
where f.status in ('unavailable_candidate', 'unavailable')
order by
  f.status,
  f.failure_count desc,
  f.last_failed_at desc;
