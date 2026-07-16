CREATE TABLE IF NOT EXISTS public.youtube_discovery_heartbeats (
  id BIGSERIAL PRIMARY KEY,
  started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
  finished_at TIMESTAMP WITHOUT TIME ZONE,
  status TEXT NOT NULL,
  processed_creators INTEGER NOT NULL DEFAULT 0,
  attempted_creators INTEGER NOT NULL DEFAULT 0,
  inserted_or_updated_posts INTEGER NOT NULL DEFAULT 0,
  errors INTEGER NOT NULL DEFAULT 0,
  total_creators INTEGER,
  batch_size INTEGER,
  cursor_start INTEGER,
  cursor_end INTEGER,
  error_summary TEXT,
  CONSTRAINT youtube_discovery_heartbeats_status_check CHECK (
    status IN ('running', 'success', 'partial_error', 'failed', 'no_creators')
  )
);

CREATE INDEX IF NOT EXISTS youtube_discovery_heartbeats_started_at_idx
  ON public.youtube_discovery_heartbeats (started_at DESC);

CREATE INDEX IF NOT EXISTS youtube_discovery_heartbeats_status_started_at_idx
  ON public.youtube_discovery_heartbeats (status, started_at DESC);

COMMENT ON TABLE public.youtube_discovery_heartbeats IS
  'Heartbeat operacional do youtube_main_scraper, registrando cada execucao do worker de discovery.';

ALTER TABLE public.youtube_discovery_heartbeats DISABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE ON public.youtube_discovery_heartbeats
  TO anon, authenticated, service_role;

GRANT USAGE, SELECT ON SEQUENCE public.youtube_discovery_heartbeats_id_seq
  TO anon, authenticated, service_role;
