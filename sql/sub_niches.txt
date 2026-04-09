create table public.sub_niches (
  id serial not null,
  name public.citext not null,
  constraint sub_niches_pkey primary key (id),
  constraint sub_niches_name_key unique (name)
) TABLESPACE pg_default;

create unique INDEX IF not exists unique_sub_niche_name on public.sub_niches using btree (name) TABLESPACE pg_default;