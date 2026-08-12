-- 012_test_fenabrave_monthly_packet_rpc.sql
--
-- Structural checks for the GPT-facing Fenabrave monthly packet RPC.
-- Run after applying sql/ddl/functions/009_create_fenabrave_monthly_packet_rpc.sql.

SELECT
  public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') ->> 'status' AS autos_status,
  public.get_fenabrave_monthly_packet('2026-07-01'::date, 'comerciais_leves') ->> 'status' AS comerciais_leves_status,
  public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos_comerciais_leves') ->> 'status' AS autos_comerciais_leves_status;


SELECT
  jsonb_typeof(public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos')) AS autos_packet_type,
  jsonb_typeof(public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') -> 'totals') AS autos_totals_type,
  jsonb_typeof(public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') -> 'channel_mix') AS autos_channel_mix_type,
  jsonb_typeof(public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') -> 'brand_share_total') AS autos_brand_share_total_type,
  jsonb_typeof(public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') -> 'model_leaders') AS autos_model_leaders_type,
  jsonb_typeof(public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') -> 'electrified') AS autos_electrified_type;


SELECT
  jsonb_array_length(
    COALESCE(
      public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') -> 'model_leaders' -> 'overall' -> 'autos',
      '[]'::jsonb
    )
  ) AS autos_overall_top_n,
  jsonb_array_length(
    COALESCE(
      public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') -> 'model_leaders' -> 'retail' -> 'autos',
      '[]'::jsonb
    )
  ) AS autos_retail_top_n,
  jsonb_array_length(
    COALESCE(
      public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos') -> 'model_leaders' -> 'direct' -> 'autos',
      '[]'::jsonb
    )
  ) AS autos_direct_top_n;


SELECT
  jsonb_array_length(
    COALESCE(
      public.get_fenabrave_monthly_packet('2026-07-01'::date, 'comerciais_leves') -> 'model_leaders' -> 'overall' -> 'comerciais_leves',
      '[]'::jsonb
    )
  ) AS comerciais_leves_overall_top_n,
  jsonb_array_length(
    COALESCE(
      public.get_fenabrave_monthly_packet('2026-07-01'::date, 'comerciais_leves') -> 'model_leaders' -> 'retail' -> 'comerciais_leves',
      '[]'::jsonb
    )
  ) AS comerciais_leves_retail_top_n,
  jsonb_array_length(
    COALESCE(
      public.get_fenabrave_monthly_packet('2026-07-01'::date, 'comerciais_leves') -> 'model_leaders' -> 'direct' -> 'comerciais_leves',
      '[]'::jsonb
    )
  ) AS comerciais_leves_direct_top_n;


SELECT
  jsonb_typeof(
    public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos_comerciais_leves') -> 'model_leaders' -> 'overall'
  ) AS combined_overall_type,
  jsonb_typeof(
    public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos_comerciais_leves') -> 'electrified' -> 'categories'
  ) AS combined_electrified_categories_type,
  jsonb_typeof(
    public.get_fenabrave_monthly_packet('2026-07-01'::date, 'autos_comerciais_leves') -> 'editorial_notes'
  ) AS combined_editorial_notes_type;


SELECT
  public.get_fenabrave_monthly_packet('2026-07-01'::date, 'motos') AS invalid_scope_response;


SELECT
  public.get_fenabrave_monthly_packet('2035-01-01'::date, 'autos') AS missing_month_response;
