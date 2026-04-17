create table public.pipeline_state (
  id text not null,
  value text null,
  constraint pipeline_state_pkey primary key (id)
) TABLESPACE pg_default;