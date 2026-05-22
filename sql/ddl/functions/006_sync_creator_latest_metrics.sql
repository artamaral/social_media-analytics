create or replace function public.sync_creator_latest_metrics()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  update public.creators c
  set
    followers = new.followers,
    followers_collected_at = new.collected_at,
    followers_source = new.source,
    hidden_subscriber_count = new.hidden_subscriber_count,
    channel_view_count = new.channel_view_count,
    channel_video_count = new.channel_video_count
  where c.id = new.creator_id
    and (
      c.followers_collected_at is null
      or new.collected_at >= c.followers_collected_at
    );

  return new;
end;
$$;

drop trigger if exists trg_sync_creator_latest_metrics
on public.creator_metrics_history;

create trigger trg_sync_creator_latest_metrics
after insert on public.creator_metrics_history
for each row
execute function public.sync_creator_latest_metrics();
