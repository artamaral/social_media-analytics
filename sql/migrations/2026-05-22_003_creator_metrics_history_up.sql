-- Cria historico de metricas dinamicas de creators e sincroniza o estado atual.
-- Executar no Supabase SQL Editor.

ALTER TABLE public.creators
  ALTER COLUMN followers TYPE bigint USING followers::bigint,
  ADD COLUMN IF NOT EXISTS followers_collected_at timestamp with time zone,
  ADD COLUMN IF NOT EXISTS followers_source text,
  ADD COLUMN IF NOT EXISTS hidden_subscriber_count boolean,
  ADD COLUMN IF NOT EXISTS channel_view_count bigint,
  ADD COLUMN IF NOT EXISTS channel_video_count bigint;

CREATE TABLE IF NOT EXISTS public.creator_metrics_history (
  id bigserial PRIMARY KEY,
  creator_id integer NOT NULL REFERENCES public.creators(id),
  followers bigint,
  channel_view_count bigint,
  channel_video_count bigint,
  hidden_subscriber_count boolean,
  collected_at timestamp with time zone NOT NULL DEFAULT now(),
  source text NOT NULL DEFAULT 'youtube_channels_api'
);

CREATE INDEX IF NOT EXISTS idx_creator_metrics_history_creator_collected_at
ON public.creator_metrics_history (creator_id, collected_at DESC);

CREATE INDEX IF NOT EXISTS idx_creator_metrics_history_collected_at
ON public.creator_metrics_history (collected_at DESC);

CREATE OR REPLACE FUNCTION public.sync_creator_latest_metrics()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  UPDATE public.creators c
  SET
    followers = NEW.followers,
    followers_collected_at = NEW.collected_at,
    followers_source = NEW.source,
    hidden_subscriber_count = NEW.hidden_subscriber_count,
    channel_view_count = NEW.channel_view_count,
    channel_video_count = NEW.channel_video_count
  WHERE c.id = NEW.creator_id
    AND (
      c.followers_collected_at IS NULL
      OR NEW.collected_at >= c.followers_collected_at
    );

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_sync_creator_latest_metrics
ON public.creator_metrics_history;

CREATE TRIGGER trg_sync_creator_latest_metrics
AFTER INSERT ON public.creator_metrics_history
FOR EACH ROW
EXECUTE FUNCTION public.sync_creator_latest_metrics();

COMMENT ON TABLE public.creator_metrics_history
IS 'Snapshots de metricas dinamicas de creators, iniciando por inscritos/followers do YouTube.';

COMMENT ON FUNCTION public.sync_creator_latest_metrics()
IS 'Atualiza os campos correntes em creators a partir do snapshot mais recente inserido em creator_metrics_history.';
