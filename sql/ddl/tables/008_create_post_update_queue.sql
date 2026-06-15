create table public.post_update_queue (
  post_id text not null,
  priority_score double precision null,
  last_checked timestamp with time zone null,
  next_check timestamp with time zone null,
  needs_update boolean null default true,
  constraint post_update_queue_pkey primary key (post_id)
) TABLESPACE pg_default;

create index IF not exists idx_queue_priority on public.post_update_queue using btree (needs_update, next_check, priority_score desc) TABLESPACE pg_default;
