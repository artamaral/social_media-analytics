create or replace function public.sync_post_latest()
returns trigger
language plpgsql
as $$
begin
  update public.posts
  set
    views = new.views,
    likes = new.likes,
    comments = new.comments,
    collected_at = new.collected_at
  where post_id = new.post_id;

  return new;
end;
$$;
