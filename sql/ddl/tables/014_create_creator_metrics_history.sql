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
