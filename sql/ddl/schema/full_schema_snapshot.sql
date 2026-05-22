-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.creators (
  id integer NOT NULL DEFAULT nextval('creators_id_seq'::regclass),
  entity_id integer NOT NULL,
  platform text NOT NULL CHECK (platform = ANY (ARRAY['youtube'::text, 'instagram'::text, 'tiktok'::text])),
  username text,
  channel_id text NOT NULL UNIQUE,
  followers bigint,
  followers_collected_at timestamp with time zone,
  followers_source text,
  hidden_subscriber_count boolean,
  channel_view_count bigint,
  channel_video_count bigint,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  is_active boolean DEFAULT true,
  CONSTRAINT creators_pkey PRIMARY KEY (id),
  CONSTRAINT creators_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id)
);
CREATE TABLE public.creator_metrics_history (
  id bigint NOT NULL DEFAULT nextval('creator_metrics_history_id_seq'::regclass),
  creator_id integer NOT NULL,
  followers bigint,
  channel_view_count bigint,
  channel_video_count bigint,
  hidden_subscriber_count boolean,
  collected_at timestamp with time zone NOT NULL DEFAULT now(),
  source text NOT NULL DEFAULT 'youtube_channels_api'::text,
  CONSTRAINT creator_metrics_history_pkey PRIMARY KEY (id),
  CONSTRAINT creator_metrics_history_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.creators(id)
);
CREATE TABLE public.entities (
  id integer NOT NULL DEFAULT nextval('entities_id_seq'::regclass),
  name USER-DEFINED NOT NULL,
  niche text NOT NULL DEFAULT 'automotivo'::text,
  creator_type text NOT NULL DEFAULT 'personal'::text,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  normalized_name text,
  CONSTRAINT entities_pkey PRIMARY KEY (id)
);
CREATE TABLE public.entity_sub_niches (
  entity_id integer NOT NULL,
  sub_niche_id integer NOT NULL,
  CONSTRAINT entity_sub_niches_pkey PRIMARY KEY (entity_id, sub_niche_id),
  CONSTRAINT entity_sub_niches_sub_niche_id_fkey FOREIGN KEY (sub_niche_id) REFERENCES public.sub_niches(id),
  CONSTRAINT entity_sub_niches_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id)
);
CREATE TABLE public.pipeline_state (
  id text NOT NULL,
  value text,
  CONSTRAINT pipeline_state_pkey PRIMARY KEY (id)
);
CREATE TABLE public.post_metrics_history (
  id integer NOT NULL DEFAULT nextval('post_metrics_history_id_seq'::regclass),
  post_id text NOT NULL,
  collected_at timestamp without time zone DEFAULT now(),
  views integer,
  likes integer,
  comments integer,
  CONSTRAINT post_metrics_history_pkey PRIMARY KEY (id)
);
CREATE TABLE public.post_update_queue (
  post_id text NOT NULL,
  priority_score double precision,
  last_checked timestamp with time zone,
  next_check timestamp without time zone,
  needs_update boolean DEFAULT true,
  CONSTRAINT post_update_queue_pkey PRIMARY KEY (post_id)
);
CREATE TABLE public.posts (
  id integer NOT NULL DEFAULT nextval('posts_id_seq'::regclass),
  creator_id integer,
  post_id text UNIQUE,
  title text,
  post_date timestamp without time zone,
  views integer,
  likes integer,
  comments integer,
  duration integer,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  video_type text NOT NULL CHECK (video_type = ANY (ARRAY['short'::text, 'long'::text])),
  collected_at timestamp without time zone,
  CONSTRAINT posts_pkey PRIMARY KEY (id),
  CONSTRAINT posts_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.creators(id)
);
CREATE TABLE public.sub_niches (
  id integer NOT NULL DEFAULT nextval('sub_niches_id_seq'::regclass),
  name USER-DEFINED NOT NULL UNIQUE,
  CONSTRAINT sub_niches_pkey PRIMARY KEY (id)
);
