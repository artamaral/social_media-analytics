create table public.post_metrics_history (
  id serial not null,
  post_id text not null,
  collected_at timestamp without time zone null default now(),
  views integer null,
  likes integer null,
  comments integer null,
  constraint post_metrics_history_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_post_metrics_history_post_id on public.post_metrics_history using btree (post_id) TABLESPACE pg_default;

create index IF not exists idx_post_metrics_history_collected_at on public.post_metrics_history using btree (collected_at) TABLESPACE pg_default;

create index IF not exists idx_post_metrics_history_post_date on public.post_metrics_history using btree (post_id, collected_at desc) TABLESPACE pg_default;

create trigger trg_sync_post
after INSERT on post_metrics_history for EACH row
execute FUNCTION sync_post_latest ();