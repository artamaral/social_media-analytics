create table public.entity_sub_niches (
  entity_id integer not null,
  sub_niche_id integer not null,
  constraint entity_sub_niches_pkey primary key (entity_id, sub_niche_id),
  constraint entity_sub_niches_entity_id_fkey foreign KEY (entity_id) references entities (id),
  constraint entity_sub_niches_sub_niche_id_fkey foreign KEY (sub_niche_id) references sub_niches (id)
) TABLESPACE pg_default;
