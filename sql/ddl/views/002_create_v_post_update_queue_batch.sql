create or replace view public.v_post_update_queue_batch as
with history_counts as (
  select
    post_id,
    count(*) as total_checagens
  from public.post_metrics_history
  group by post_id
),
eligible as (
  select
    q.post_id,
    q.priority_score,
    q.last_checked,
    q.next_check,
    q.needs_update,
    p.created_at,
    coalesce(h.total_checagens, 0) as total_checagens,
    public.calculate_priority_band(q.priority_score) as priority_band
  from public.post_update_queue q
  join public.posts p
    on p.post_id = q.post_id
  left join history_counts h
    on h.post_id = q.post_id
  left join public.post_collection_failures f
    on f.post_id = q.post_id
  where q.needs_update = true
    and q.next_check <= now()
    and coalesce(f.status, 'active') <> 'unavailable'
),
guardrail_ranked as (
  select
    e.*,
    row_number() over (
      order by
        e.total_checagens asc,
        e.created_at asc,
        e.priority_score desc,
        e.post_id
    ) as guardrail_rank
  from eligible e
  where e.total_checagens < 3
),
guardrail_slice as (
  select
    g.post_id,
    g.priority_score,
    g.last_checked,
    g.next_check,
    g.needs_update,
    g.created_at,
    g.total_checagens,
    g.priority_band,
    0 as slice_order
  from guardrail_ranked g
  where g.guardrail_rank <= 6
),
normal_eligible as (
  select e.*
  from eligible e
  where e.total_checagens >= 3
),
quotas as (
  select *
  from (
    values
      (6, 8),
      (5, 8),
      (4, 8),
      (3, 7),
      (2, 7),
      (1, 6)
  ) as t(priority_band, quota)
),
ranked as (
  select
    e.*,
    row_number() over (
      partition by e.priority_band
      order by
        e.next_check asc,
        e.last_checked asc nulls first,
        e.post_id
    ) as band_rank
  from normal_eligible e
),
primary_slice as (
  select
    r.post_id,
    r.priority_score,
    r.last_checked,
    r.next_check,
    r.needs_update,
    r.created_at,
    r.total_checagens,
    r.priority_band,
    1 as slice_order
  from ranked r
  join quotas q
    on q.priority_band = r.priority_band
  where r.band_rank <= q.quota
),
remaining as (
  select
    r.post_id,
    r.priority_score,
    r.last_checked,
    r.next_check,
    r.needs_update,
    r.created_at,
    r.total_checagens,
    r.priority_band,
    row_number() over (
      order by
        r.next_check asc,
        r.last_checked asc nulls first,
        r.priority_band desc,
        r.post_id
    ) as refill_rank
  from ranked r
  where not exists (
    select 1
    from primary_slice p
    where p.post_id = r.post_id
  )
),
final_batch as (
  select * from guardrail_slice
  union all
  select * from primary_slice
  union all
  select
    post_id,
    priority_score,
    last_checked,
    next_check,
    needs_update,
    created_at,
    total_checagens,
    priority_band,
    2 as slice_order
  from remaining
  where refill_rank <= greatest(
    50
    - (select count(*) from guardrail_slice)
    - (select count(*) from primary_slice),
    0
  )
)
select
  post_id,
  priority_score,
  last_checked,
  next_check,
  needs_update,
  priority_band
from final_batch
order by
  slice_order asc,
  case
    when slice_order = 0 then total_checagens
    else null
  end asc nulls last,
  case
    when slice_order = 0 then created_at
    else null
  end asc nulls last,
  priority_band desc,
  next_check asc,
  last_checked asc nulls first,
  post_id
limit 50;
