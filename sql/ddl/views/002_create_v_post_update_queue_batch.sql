create or replace view public.v_post_update_queue_batch as
with eligible as (
  select
    q.post_id,
    q.priority_score,
    q.last_checked,
    q.next_check,
    q.needs_update,
    public.calculate_priority_band(q.priority_score) as priority_band
  from public.post_update_queue q
  where q.needs_update = true
    and q.next_check <= now()
),
quotas as (
  select *
  from (
    values
      (6, 4),
      (5, 4),
      (4, 4),
      (3, 3),
      (2, 3),
      (1, 2)
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
  from eligible e
),
primary_slice as (
  select
    r.post_id,
    r.priority_score,
    r.last_checked,
    r.next_check,
    r.needs_update,
    r.priority_band
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
  select * from primary_slice
  union all
  select
    post_id,
    priority_score,
    last_checked,
    next_check,
    needs_update,
    priority_band
  from remaining
  where refill_rank <= greatest(
    20 - (select count(*) from primary_slice),
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
  priority_band desc,
  next_check asc,
  last_checked asc nulls first,
  post_id
limit 20;
