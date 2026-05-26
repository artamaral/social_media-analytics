-- 006_creator_intake_rpc_functions.sql

-- Controlled RPC helpers for the Streamlit creator intake screen.
-- These functions keep Streamlit away from direct SQL/table writes while
-- preserving the existing entity_intake governance flow.
--
-- Required order before running this file:
-- 1) sql/ddl/tables/009_create_entity_intake.sql
-- 2) sql/ddl/views/001_create_v_entity_intake_review.sql
-- 3) sql/ddl/functions/001_create_publish_entity_intake_function.sql

DROP FUNCTION IF EXISTS public.search_creators_for_intake(text, text);
DROP FUNCTION IF EXISTS public.create_creator_from_resolved_entity(integer, text, text, text, integer);
DROP FUNCTION IF EXISTS public.create_creator_from_resolved_entity(integer, text, text, text, bigint);

CREATE OR REPLACE FUNCTION public.search_entities_for_intake(
  p_raw_name text
)
RETURNS TABLE (
  entity_id integer,
  entity_name text,
  niche text,
  creator_type text,
  normalized_name text,
  match_type text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_raw_name text;
  v_normalized_name text;
BEGIN
  v_raw_name := NULLIF(BTRIM(p_raw_name), '');

  IF v_raw_name IS NULL THEN
    RAISE EXCEPTION 'p_raw_name is required' USING ERRCODE = '22023';
  END IF;

  v_normalized_name := LOWER(BTRIM(unaccent(v_raw_name)));

  RETURN QUERY
  SELECT
    e.id AS entity_id,
    e.name::text AS entity_name,
    e.niche,
    e.creator_type,
    e.normalized_name,
    CASE
      WHEN LOWER(BTRIM(e.name::text)) = LOWER(v_raw_name) THEN 'display_name'
      WHEN e.normalized_name = v_normalized_name THEN 'normalized_name'
      ELSE 'partial_name'
    END AS match_type
  FROM public.entities e
  WHERE LOWER(BTRIM(e.name::text)) = LOWER(v_raw_name)
     OR e.normalized_name = v_normalized_name
     OR e.name::text ILIKE ('%' || v_raw_name || '%')
  ORDER BY
    CASE
      WHEN LOWER(BTRIM(e.name::text)) = LOWER(v_raw_name) THEN 1
      WHEN e.normalized_name = v_normalized_name THEN 2
      ELSE 3
    END,
    e.name::text
  LIMIT 20;
END;
$$;


CREATE OR REPLACE FUNCTION public.search_creators_for_intake(
  p_platform text,
  p_channel_id text
)
RETURNS TABLE (
  creator_id integer,
  entity_id integer,
  entity_name text,
  platform text,
  username text,
  channel_id text,
  followers bigint,
  is_active boolean
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_platform text;
  v_channel_id text;
BEGIN
  v_platform := LOWER(NULLIF(BTRIM(p_platform), ''));
  v_channel_id := NULLIF(BTRIM(p_channel_id), '');

  IF v_platform IS NULL THEN
    RAISE EXCEPTION 'p_platform is required' USING ERRCODE = '22023';
  END IF;

  IF v_channel_id IS NULL THEN
    RAISE EXCEPTION 'p_channel_id is required' USING ERRCODE = '22023';
  END IF;

  RETURN QUERY
  SELECT
    c.id AS creator_id,
    c.entity_id,
    e.name::text AS entity_name,
    c.platform,
    c.username,
    c.channel_id,
    c.followers,
    c.is_active
  FROM public.creators c
  JOIN public.entities e ON e.id = c.entity_id
  WHERE c.channel_id = v_channel_id
     OR (c.platform = v_platform AND c.channel_id = v_channel_id)
  ORDER BY c.id;
END;
$$;


CREATE OR REPLACE FUNCTION public.list_sub_niches_for_intake()
RETURNS TABLE (
  sub_niche_id integer,
  sub_niche_name text
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    sn.id AS sub_niche_id,
    sn.name::text AS sub_niche_name
  FROM public.sub_niches sn
  ORDER BY sn.name::text;
$$;


CREATE OR REPLACE FUNCTION public.create_entity_intake_entry(
  p_raw_name text,
  p_sub_niche_name text,
  p_niche text DEFAULT 'automotivo',
  p_creator_type text DEFAULT 'personal',
  p_notes text DEFAULT NULL
)
RETURNS TABLE (
  id bigint,
  raw_name text,
  normalized_name text,
  sub_niche_name text,
  niche text,
  creator_type text,
  notes text,
  status text,
  created_at timestamp without time zone,
  existing_entity_id integer,
  existing_entity_name text,
  sub_niche_id integer,
  matched_sub_niche_name text,
  review_result text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_raw_name text;
  v_sub_niche_name text;
  v_niche text;
  v_creator_type text;
  v_notes text;
  v_intake_id bigint;
BEGIN
  v_raw_name := NULLIF(BTRIM(p_raw_name), '');
  v_sub_niche_name := NULLIF(BTRIM(p_sub_niche_name), '');
  v_niche := COALESCE(NULLIF(BTRIM(p_niche), ''), 'automotivo');
  v_creator_type := COALESCE(NULLIF(BTRIM(p_creator_type), ''), 'personal');
  v_notes := NULLIF(BTRIM(p_notes), '');

  IF v_raw_name IS NULL THEN
    RAISE EXCEPTION 'p_raw_name is required' USING ERRCODE = '22023';
  END IF;

  IF v_sub_niche_name IS NULL THEN
    RAISE EXCEPTION 'p_sub_niche_name is required' USING ERRCODE = '22023';
  END IF;

  INSERT INTO public.entity_intake (
    raw_name,
    normalized_name,
    sub_niche_name,
    niche,
    creator_type,
    notes,
    status
  )
  VALUES (
    v_raw_name,
    LOWER(BTRIM(unaccent(v_raw_name))),
    v_sub_niche_name,
    v_niche,
    v_creator_type,
    v_notes,
    'pending'
  )
  RETURNING public.entity_intake.id INTO v_intake_id;

  RETURN QUERY
  SELECT
    r.id,
    r.raw_name,
    r.normalized_name,
    r.sub_niche_name,
    r.niche,
    r.creator_type,
    r.notes,
    r.status,
    r.created_at,
    r.existing_entity_id,
    r.existing_entity_name::text,
    r.sub_niche_id,
    r.matched_sub_niche_name::text,
    r.review_result
  FROM public.v_entity_intake_review r
  WHERE r.id = v_intake_id;
END;
$$;


CREATE OR REPLACE FUNCTION public.create_creator_from_resolved_entity(
  p_entity_id integer,
  p_platform text,
  p_username text,
  p_channel_id text,
  p_followers bigint DEFAULT NULL
)
RETURNS TABLE (
  creator_id integer,
  entity_id integer,
  platform text,
  username text,
  channel_id text,
  followers bigint,
  is_active boolean,
  created_at timestamp without time zone
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_platform text;
  v_username text;
  v_channel_id text;
  v_followers bigint;
  v_creator_id integer;
BEGIN
  v_platform := LOWER(NULLIF(BTRIM(p_platform), ''));
  v_username := NULLIF(BTRIM(p_username), '');
  v_channel_id := NULLIF(BTRIM(p_channel_id), '');
  v_followers := p_followers;

  IF p_entity_id IS NULL THEN
    RAISE EXCEPTION 'p_entity_id is required' USING ERRCODE = '22023';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM public.entities e WHERE e.id = p_entity_id) THEN
    RAISE EXCEPTION 'entity_id % not found', p_entity_id USING ERRCODE = '23503';
  END IF;

  IF v_platform NOT IN ('youtube', 'instagram', 'tiktok') THEN
    RAISE EXCEPTION 'invalid platform: %', COALESCE(v_platform, '<null>') USING ERRCODE = '22023';
  END IF;

  IF v_channel_id IS NULL THEN
    RAISE EXCEPTION 'p_channel_id is required' USING ERRCODE = '22023';
  END IF;

  IF v_followers IS NOT NULL AND v_followers < 0 THEN
    RAISE EXCEPTION 'followers cannot be negative' USING ERRCODE = '22023';
  END IF;

  IF EXISTS (SELECT 1 FROM public.creators c WHERE c.channel_id = v_channel_id) THEN
    RAISE EXCEPTION 'channel_id already exists: %', v_channel_id USING ERRCODE = '23505';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.creators c
    WHERE c.platform = v_platform
      AND c.channel_id = v_channel_id
  ) THEN
    RAISE EXCEPTION 'platform/channel_id already exists: %/%', v_platform, v_channel_id USING ERRCODE = '23505';
  END IF;

  INSERT INTO public.creators (
    entity_id,
    platform,
    username,
    channel_id,
    followers,
    is_active
  )
  VALUES (
    p_entity_id,
    v_platform,
    v_username,
    v_channel_id,
    v_followers,
    true
  )
  RETURNING public.creators.id INTO v_creator_id;

  RETURN QUERY
  SELECT
    c.id AS creator_id,
    c.entity_id,
    c.platform,
    c.username,
    c.channel_id,
    c.followers,
    c.is_active,
    c.created_at
  FROM public.creators c
  WHERE c.id = v_creator_id;
END;
$$;


REVOKE ALL ON FUNCTION public.search_entities_for_intake(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_creators_for_intake(text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_sub_niches_for_intake() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.create_entity_intake_entry(text, text, text, text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.create_creator_from_resolved_entity(integer, text, text, text, bigint) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.search_entities_for_intake(text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.search_creators_for_intake(text, text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.list_sub_niches_for_intake() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.create_entity_intake_entry(text, text, text, text, text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.create_creator_from_resolved_entity(integer, text, text, text, bigint) TO anon, authenticated;
