DROP TRIGGER IF EXISTS trg_sync_creator_latest_metrics
ON public.creator_metrics_history;

DROP FUNCTION IF EXISTS public.sync_creator_latest_metrics();

DROP INDEX IF EXISTS public.idx_creator_metrics_history_collected_at;
DROP INDEX IF EXISTS public.idx_creator_metrics_history_creator_collected_at;

DROP TABLE IF EXISTS public.creator_metrics_history;

ALTER TABLE public.creators
  DROP COLUMN IF EXISTS channel_video_count,
  DROP COLUMN IF EXISTS channel_view_count,
  DROP COLUMN IF EXISTS hidden_subscriber_count,
  DROP COLUMN IF EXISTS followers_source,
  DROP COLUMN IF EXISTS followers_collected_at,
  ALTER COLUMN followers TYPE integer USING followers::integer;
