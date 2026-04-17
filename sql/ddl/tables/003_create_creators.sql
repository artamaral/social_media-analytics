create table public.creators (
  id serial not null,
  entity_id integer not null,
  platform text not null,
  username text null,
  channel_id text not null,
  followers integer null,
  created_at timestamp without time zone null default CURRENT_TIMESTAMP,
  is_active boolean null default true,
  constraint creators_pkey primary key (id),
  constraint creators_channel_id_key unique (channel_id),
  constraint creators_entity_id_fkey foreign KEY (entity_id) references entities (id),
  constraint platform_check check (
    (
      platform = any (
        array[
          'youtube'::text,
          'instagram'::text,
          'tiktok'::text
        ]
      )
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_creators_entity on public.creators using btree (entity_id) TABLESPACE pg_default;

create unique INDEX IF not exists unique_creator_platform on public.creators using btree (platform, channel_id) TABLESPACE pg_default;