create table public.entities (
  id serial not null,
  name public.citext not null,
  niche text not null default 'automotivo'::text,
  creator_type text not null default 'personal'::text,
  created_at timestamp without time zone null default CURRENT_TIMESTAMP,
  normalized_name text null,
  constraint entities_pkey primary key (id)
) TABLESPACE pg_default;

create unique INDEX IF not exists unique_entities_normalized on public.entities using btree (normalized_name) TABLESPACE pg_default;