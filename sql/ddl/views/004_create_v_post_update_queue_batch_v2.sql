create or replace view public.v_post_update_queue_batch_v2 as
with eligible as (
  select
    q.post_id,
    q.priority_score,
    q.last_checked,
    q.next_check,
    q.needs_update,
    f.priority_score_v2,
    f.priority_band_v2,
    f.proposed_next_check_v2,
    f.history_level,
    f.base_popularity,
    f.velocity_score,
    f.acceleration_score
  from public.post_update_queue q
  join public.v_post_priority_score_features_v2 f
    on f.post_id = q.post_id
  where q.needs_update = true
    and q.next_check <= now()
),
quotas as (
  select *
  from (
    values
      (6, 8),
      (5, 8),
      (4, 8),
      (3, 6),
      (2, 6),
      (1, 4)
  ) as t(priority_band_v2, quota)
),
ranked as (
  select
    e.*,
    row_number() over (
      partition by e.priority_band_v2
      order by
        e.next_check asc,
        e.last_checked asc nulls first,
        e.post_id
    ) as band_rank
  from eligible e
),
primary_slice as (
  select
    r.*
  from ranked r
  join quotas q
    on q.priority_band_v2 = r.priority_band_v2
  where r.band_rank <= q.quota
),
remaining as (
  select
    r.*,
    row_number() over (
      order by
        r.next_check asc,
        r.last_checked asc nulls first,
        r.priority_band_v2 desc,
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
    priority_score_v2,
    priority_band_v2,
    proposed_next_check_v2,
    history_level,
    base_popularity,
    velocity_score,
    acceleration_score,
    band_rank
  from remaining
  where refill_rank <= greatest(
    40 - (select count(*) from primary_slice),
    0
  )
)
select
  post_id,
  priority_score,
  last_checked,
  next_check,
  needs_update,
  priority_score_v2,
  priority_band_v2,
  proposed_next_check_v2,
  history_level,
  base_popularity,
  velocity_score,
  acceleration_score
from final_batch
order by
  priority_band_v2 desc,
  next_check asc,
  last_checked asc nulls first,
  post_id
limit 40;
