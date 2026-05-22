create table if not exists public.creator_metrics_history (
  id bigserial primary key,
  creator_id integer not null references public.creators(id),
  followers bigint,
  channel_view_count bigint,
  channel_video_count bigint,
  hidden_subscriber_count boolean,
  collected_at timestamp with time zone not null default now(),
  source text not null default 'youtube_channels_api'
) TABLESPACE pg_default;

create index if not exists idx_creator_metrics_history_creator_collected_at
on public.creator_metrics_history using btree (creator_id, collected_at desc) TABLESPACE pg_default;

create index if not exists idx_creator_metrics_history_collected_at
on public.creator_metrics_history using btree (collected_at desc) TABLESPACE pg_default;

grant select, insert on public.creator_metrics_history
to anon, authenticated, service_role;

grant usage, select on sequence public.creator_metrics_history_id_seq
to anon, authenticated, service_role;

drop policy if exists creator_metrics_history_insert_worker
on public.creator_metrics_history;

create policy creator_metrics_history_insert_worker
on public.creator_metrics_history
for insert
to anon, authenticated, service_role
with check (
  source = 'youtube_channels_api'
);
