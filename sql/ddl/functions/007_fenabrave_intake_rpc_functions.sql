-- 007_fenabrave_intake_rpc_functions.sql
--
-- Controlled RPC helpers for the Streamlit Fenabrave intake screen.
-- These functions expose only the metadata flow needed by the dashboard
-- without requiring direct table writes from the app.

DROP FUNCTION IF EXISTS public.list_fenabrave_source_files(integer);
DROP FUNCTION IF EXISTS public.upsert_fenabrave_source_file(
  date,
  text,
  text,
  text,
  text,
  text,
  bigint,
  text,
  text,
  text,
  text
);

CREATE OR REPLACE FUNCTION public.list_fenabrave_source_files(
  p_limit integer DEFAULT 12
)
RETURNS TABLE (
  source_file_id bigint,
  source_name text,
  reference_period date,
  source_url text,
  source_page_url text,
  storage_bucket text,
  storage_path text,
  original_filename text,
  file_size_bytes bigint,
  sha256 text,
  extraction_status text,
  extraction_method text,
  extraction_notes text,
  captured_at timestamptz
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    f.id AS source_file_id,
    s.source_name::text,
    f.reference_period,
    f.source_url,
    f.source_page_url,
    f.storage_bucket,
    f.storage_path,
    f.original_filename,
    f.file_size_bytes,
    f.sha256,
    f.extraction_status,
    f.extraction_method,
    f.extraction_notes,
    f.captured_at
  FROM public.market_source_files f
  JOIN public.market_data_sources s
    ON s.id = f.source_id
  WHERE LOWER(s.source_name) = 'fenabrave'
  ORDER BY f.reference_period DESC, f.id DESC
  LIMIT LEAST(GREATEST(COALESCE(p_limit, 12), 1), 24);
$$;


CREATE OR REPLACE FUNCTION public.upsert_fenabrave_source_file(
  p_reference_period date,
  p_source_url text,
  p_source_page_url text,
  p_storage_bucket text,
  p_storage_path text,
  p_original_filename text,
  p_file_size_bytes bigint DEFAULT NULL,
  p_sha256 text DEFAULT NULL,
  p_extraction_status text DEFAULT 'stored',
  p_extraction_method text DEFAULT 'pdf_table_extraction',
  p_extraction_notes text DEFAULT NULL
)
RETURNS TABLE (
  source_file_id bigint,
  source_name text,
  reference_period date,
  source_url text,
  source_page_url text,
  storage_bucket text,
  storage_path text,
  original_filename text,
  file_size_bytes bigint,
  sha256 text,
  extraction_status text,
  extraction_method text,
  extraction_notes text,
  captured_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_source_id bigint;
  v_reference_period date;
  v_source_url text;
  v_source_page_url text;
  v_storage_bucket text;
  v_storage_path text;
  v_original_filename text;
  v_file_size_bytes bigint;
  v_sha256 text;
  v_extraction_status text;
  v_extraction_method text;
  v_extraction_notes text;
  v_source_file_id bigint;
BEGIN
  v_reference_period := p_reference_period;
  v_source_url := NULLIF(BTRIM(p_source_url), '');
  v_source_page_url := NULLIF(BTRIM(p_source_page_url), '');
  v_storage_bucket := NULLIF(BTRIM(p_storage_bucket), '');
  v_storage_path := NULLIF(BTRIM(p_storage_path), '');
  v_original_filename := NULLIF(BTRIM(p_original_filename), '');
  v_file_size_bytes := p_file_size_bytes;
  v_sha256 := NULLIF(BTRIM(p_sha256), '');
  v_extraction_status := COALESCE(NULLIF(BTRIM(p_extraction_status), ''), 'stored');
  v_extraction_method := COALESCE(NULLIF(BTRIM(p_extraction_method), ''), 'pdf_table_extraction');
  v_extraction_notes := NULLIF(BTRIM(p_extraction_notes), '');

  IF v_reference_period IS NULL THEN
    RAISE EXCEPTION 'p_reference_period is required' USING ERRCODE = '22023';
  END IF;

  IF v_source_url IS NULL THEN
    RAISE EXCEPTION 'p_source_url is required' USING ERRCODE = '22023';
  END IF;

  IF v_source_page_url IS NULL THEN
    RAISE EXCEPTION 'p_source_page_url is required' USING ERRCODE = '22023';
  END IF;

  IF v_storage_bucket IS NULL THEN
    RAISE EXCEPTION 'p_storage_bucket is required' USING ERRCODE = '22023';
  END IF;

  IF v_storage_path IS NULL THEN
    RAISE EXCEPTION 'p_storage_path is required' USING ERRCODE = '22023';
  END IF;

  IF v_original_filename IS NULL THEN
    RAISE EXCEPTION 'p_original_filename is required' USING ERRCODE = '22023';
  END IF;

  IF v_file_size_bytes IS NOT NULL AND v_file_size_bytes <= 0 THEN
    RAISE EXCEPTION 'p_file_size_bytes must be positive when provided' USING ERRCODE = '22023';
  END IF;

  SELECT s.id
  INTO v_source_id
  FROM public.market_data_sources s
  WHERE LOWER(s.source_name) = 'fenabrave'
  LIMIT 1;

  IF v_source_id IS NULL THEN
    RAISE EXCEPTION 'Fenabrave source not found in public.market_data_sources' USING ERRCODE = 'P0001';
  END IF;

  INSERT INTO public.market_source_files (
    source_id,
    reference_period,
    source_url,
    source_page_url,
    file_type,
    storage_bucket,
    storage_path,
    original_filename,
    file_size_bytes,
    sha256,
    extraction_status,
    extraction_method,
    extraction_notes
  )
  VALUES (
    v_source_id,
    v_reference_period,
    v_source_url,
    v_source_page_url,
    'pdf',
    v_storage_bucket,
    v_storage_path,
    v_original_filename,
    v_file_size_bytes,
    v_sha256,
    v_extraction_status,
    v_extraction_method,
    v_extraction_notes
  )
  ON CONFLICT (source_id, reference_period, source_url)
  DO UPDATE SET
    source_page_url = EXCLUDED.source_page_url,
    storage_bucket = EXCLUDED.storage_bucket,
    storage_path = EXCLUDED.storage_path,
    original_filename = EXCLUDED.original_filename,
    file_size_bytes = COALESCE(EXCLUDED.file_size_bytes, public.market_source_files.file_size_bytes),
    sha256 = COALESCE(EXCLUDED.sha256, public.market_source_files.sha256),
    extraction_status = EXCLUDED.extraction_status,
    extraction_method = EXCLUDED.extraction_method,
    extraction_notes = EXCLUDED.extraction_notes
  RETURNING id INTO v_source_file_id;

  RETURN QUERY
  SELECT
    f.id AS source_file_id,
    s.source_name::text,
    f.reference_period,
    f.source_url,
    f.source_page_url,
    f.storage_bucket,
    f.storage_path,
    f.original_filename,
    f.file_size_bytes,
    f.sha256,
    f.extraction_status,
    f.extraction_method,
    f.extraction_notes,
    f.captured_at
  FROM public.market_source_files f
  JOIN public.market_data_sources s
    ON s.id = f.source_id
  WHERE f.id = v_source_file_id;
END;
$$;


GRANT EXECUTE ON FUNCTION public.list_fenabrave_source_files(integer) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_fenabrave_source_file(
  date,
  text,
  text,
  text,
  text,
  text,
  bigint,
  text,
  text,
  text,
  text
) TO anon, authenticated;
