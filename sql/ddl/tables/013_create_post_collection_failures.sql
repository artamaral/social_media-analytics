create table if not exists public.post_collection_failures (
  post_id text primary key references public.posts(post_id),
  youtube_url text generated always as (
    'https://www.youtube.com/watch?v=' || post_id
  ) stored,
  failure_count integer not null default 0,
  first_failed_at timestamp without time zone not null default now(),
  last_failed_at timestamp without time zone not null default now(),
  last_success_at timestamp without time zone,
  status text not null default 'active',
  last_failure_reason text,
  human_review_status text,
  human_reviewed_at timestamp without time zone,
  human_reviewed_by text,
  human_review_notes text,
  constraint post_collection_failures_status_check
    check (status in ('active', 'unavailable_candidate', 'unavailable', 'recovered')),
  constraint post_collection_failures_human_review_status_check
    check (
      human_review_status is null
      or human_review_status in ('confirmed_unavailable', 'available_on_manual_check', 'unclear')
    )
);

create index if not exists idx_post_collection_failures_status
  on public.post_collection_failures using btree (status, failure_count desc, last_failed_at desc);

create index if not exists idx_post_collection_failures_last_failed_at
  on public.post_collection_failures using btree (last_failed_at desc);
