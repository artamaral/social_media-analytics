-- 009_create_fenabrave_monthly_packet_rpc.sql
--
-- Canonical read-only RPC for GPT-facing Fenabrave monthly analysis packets.
-- The packet is returned as jsonb so GPT clients can consume a stable
-- structure without direct access to raw tables or ad-hoc SQL.

DROP FUNCTION IF EXISTS public.get_fenabrave_monthly_packet(date, text);

CREATE OR REPLACE FUNCTION public.get_fenabrave_monthly_packet(
  p_reference_period date,
  p_scope text DEFAULT 'autos_comerciais_leves'
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_reference_period date := date_trunc('month', p_reference_period)::date;
  v_previous_reference_period date := (date_trunc('month', p_reference_period) - interval '1 month')::date;
  v_scope text := lower(trim(coalesce(p_scope, 'autos_comerciais_leves')));
  v_primary_vehicle_category text;
  v_source_page_url text;
  v_source_url text;
  v_packet jsonb;
BEGIN
  IF p_reference_period IS NULL THEN
    RETURN jsonb_build_object(
      'status', 'invalid_request',
      'reference_period', NULL,
      'scope', v_scope,
      'reason', 'p_reference_period is required.'
    );
  END IF;

  IF v_scope NOT IN ('autos', 'comerciais_leves', 'autos_comerciais_leves') THEN
    RETURN jsonb_build_object(
      'status', 'invalid_scope',
      'reference_period', to_char(v_reference_period, 'YYYY-MM'),
      'scope', v_scope,
      'reason', 'Scope must be autos, comerciais_leves or autos_comerciais_leves.'
    );
  END IF;

  v_primary_vehicle_category := CASE v_scope
    WHEN 'autos' THEN 'automoveis'
    WHEN 'comerciais_leves' THEN 'comerciais_leves'
    ELSE 'autos_comerciais_leves'
  END;

  SELECT
    f.source_page_url,
    f.source_url
  INTO
    v_source_page_url,
    v_source_url
  FROM public.market_source_files f
  JOIN public.market_data_sources s
    ON s.id = f.source_id
  WHERE lower(s.source_name) = 'fenabrave'
    AND date_trunc('month', f.reference_period)::date = v_reference_period
    AND f.extraction_status = 'validated'
  ORDER BY f.id DESC
  LIMIT 1;

  IF v_source_url IS NULL THEN
    RETURN jsonb_build_object(
      'status', 'not_available',
      'reference_period', to_char(v_reference_period, 'YYYY-MM'),
      'scope', v_scope,
      'reason', 'No validated Fenabrave source file found for the requested month.'
    );
  END IF;

  WITH requested_categories AS (
    SELECT *
    FROM (
      VALUES
        ('autos', 'automoveis'),
        ('comerciais_leves', 'comerciais_leves')
    ) AS t(scope_key, vehicle_category)
    WHERE v_scope = 'autos_comerciais_leves'
       OR (v_scope = 'autos' AND scope_key = 'autos')
       OR (v_scope = 'comerciais_leves' AND scope_key = 'comerciais_leves')
  ),
  totals_base AS (
    SELECT
      COALESCE(SUM(s.mes_atual), 0)::bigint AS current_month_units,
      SUM(s.previous_month_units)::bigint AS previous_month_units
    FROM public.v_market_registration_segment_summary s
    WHERE s.reference_period = v_reference_period
      AND s.segment_code = ANY (
        CASE v_scope
          WHEN 'autos' THEN ARRAY['autos']
          WHEN 'comerciais_leves' THEN ARRAY['comerciais_leves']
          ELSE ARRAY['autos', 'comerciais_leves']
        END
      )
  ),
  channel_mix_current AS (
    SELECT
      sales_channel,
      share_pct
    FROM public.v_market_fenabrave_sales_channel_mix
    WHERE reference_period = v_reference_period
      AND item_code = 'fenabrave_item_11_participacao_venda_direta_varejo_mes'
      AND vehicle_category = v_primary_vehicle_category
  ),
  channel_mix_previous AS (
    SELECT
      sales_channel,
      share_pct
    FROM public.v_market_fenabrave_sales_channel_mix
    WHERE reference_period = v_previous_reference_period
      AND item_code = 'fenabrave_item_11_participacao_venda_direta_varejo_mes'
      AND vehicle_category = v_primary_vehicle_category
  ),
  channel_mix_json AS (
    SELECT jsonb_build_object(
      'available', COUNT(*) FILTER (WHERE c.sales_channel IS NOT NULL) = 2,
      'retail_share_pct', MAX(CASE WHEN c.sales_channel = 'retail' THEN c.share_pct END),
      'direct_share_pct', MAX(CASE WHEN c.sales_channel = 'direct' THEN c.share_pct END),
      'retail_delta_pp_vs_prev_month',
        CASE
          WHEN MAX(CASE WHEN c.sales_channel = 'retail' THEN c.share_pct END) IS NULL
            OR MAX(CASE WHEN p.sales_channel = 'retail' THEN p.share_pct END) IS NULL
            THEN NULL
          ELSE ROUND(
            MAX(CASE WHEN c.sales_channel = 'retail' THEN c.share_pct END)
            - MAX(CASE WHEN p.sales_channel = 'retail' THEN p.share_pct END),
            2
          )
        END,
      'direct_delta_pp_vs_prev_month',
        CASE
          WHEN MAX(CASE WHEN c.sales_channel = 'direct' THEN c.share_pct END) IS NULL
            OR MAX(CASE WHEN p.sales_channel = 'direct' THEN p.share_pct END) IS NULL
            THEN NULL
          ELSE ROUND(
            MAX(CASE WHEN c.sales_channel = 'direct' THEN c.share_pct END)
            - MAX(CASE WHEN p.sales_channel = 'direct' THEN p.share_pct END),
            2
          )
        END
    ) AS payload
    FROM channel_mix_current c
    FULL JOIN channel_mix_previous p
      ON p.sales_channel = c.sales_channel
  ),
  brand_total_current AS (
    SELECT
      rank_position,
      brand_name_raw,
      market_share_pct
    FROM public.v_market_fenabrave_brand_rankings
    WHERE reference_period = v_reference_period
      AND item_code = 'fenabrave_item_17_participacao_mercado_marca_mes'
      AND vehicle_category = v_primary_vehicle_category
      AND rank_position <= 11
  ),
  brand_total_previous AS (
    SELECT
      brand_name_raw,
      market_share_pct
    FROM public.v_market_fenabrave_brand_rankings
    WHERE reference_period = v_previous_reference_period
      AND item_code = 'fenabrave_item_17_participacao_mercado_marca_mes'
      AND vehicle_category = v_primary_vehicle_category
      AND rank_position <= 11
  ),
  brand_total_json AS (
    SELECT COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'rank', c.rank_position,
          'brand', c.brand_name_raw,
          'share_pct', c.market_share_pct,
          'delta_pp_vs_prev_month',
            CASE
              WHEN p.market_share_pct IS NULL THEN NULL
              ELSE ROUND(c.market_share_pct - p.market_share_pct, 2)
            END
        )
        ORDER BY c.rank_position
      ),
      '[]'::jsonb
    ) AS payload
    FROM brand_total_current c
    LEFT JOIN brand_total_previous p
      ON p.brand_name_raw = c.brand_name_raw
  ),
  brand_retail_current AS (
    SELECT
      rank_position,
      brand_name_raw,
      market_share_pct
    FROM public.v_market_fenabrave_brand_rankings
    WHERE reference_period = v_reference_period
      AND item_code = 'fenabrave_item_13_ranking_marca_emplacamento_varejo_mes'
      AND vehicle_category = v_primary_vehicle_category
      AND rank_position <= 10
  ),
  brand_retail_previous AS (
    SELECT
      brand_name_raw,
      market_share_pct
    FROM public.v_market_fenabrave_brand_rankings
    WHERE reference_period = v_previous_reference_period
      AND item_code = 'fenabrave_item_13_ranking_marca_emplacamento_varejo_mes'
      AND vehicle_category = v_primary_vehicle_category
      AND rank_position <= 10
  ),
  brand_retail_json AS (
    SELECT COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'rank', c.rank_position,
          'brand', c.brand_name_raw,
          'share_pct', c.market_share_pct,
          'delta_pp_vs_prev_month',
            CASE
              WHEN p.market_share_pct IS NULL THEN NULL
              ELSE ROUND(c.market_share_pct - p.market_share_pct, 2)
            END
        )
        ORDER BY c.rank_position
      ),
      '[]'::jsonb
    ) AS payload
    FROM brand_retail_current c
    LEFT JOIN brand_retail_previous p
      ON p.brand_name_raw = c.brand_name_raw
  ),
  brand_direct_current AS (
    SELECT
      rank_position,
      brand_name_raw,
      market_share_pct
    FROM public.v_market_fenabrave_brand_rankings
    WHERE reference_period = v_reference_period
      AND item_code = 'fenabrave_item_15_ranking_marca_emplacamento_direta_mes'
      AND vehicle_category = v_primary_vehicle_category
      AND rank_position <= 10
  ),
  brand_direct_previous AS (
    SELECT
      brand_name_raw,
      market_share_pct
    FROM public.v_market_fenabrave_brand_rankings
    WHERE reference_period = v_previous_reference_period
      AND item_code = 'fenabrave_item_15_ranking_marca_emplacamento_direta_mes'
      AND vehicle_category = v_primary_vehicle_category
      AND rank_position <= 10
  ),
  brand_direct_json AS (
    SELECT COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'rank', c.rank_position,
          'brand', c.brand_name_raw,
          'share_pct', c.market_share_pct,
          'delta_pp_vs_prev_month',
            CASE
              WHEN p.market_share_pct IS NULL THEN NULL
              ELSE ROUND(c.market_share_pct - p.market_share_pct, 2)
            END
        )
        ORDER BY c.rank_position
      ),
      '[]'::jsonb
    ) AS payload
    FROM brand_direct_current c
    LEFT JOIN brand_direct_previous p
      ON p.brand_name_raw = c.brand_name_raw
  ),
  overall_model_ranked AS (
    SELECT
      c.scope_key,
      r.rank_position,
      row_number() OVER (
        PARTITION BY c.scope_key
        ORDER BY r.rank_position
      ) AS row_num,
      jsonb_build_object(
        'rank', r.rank_position,
        'brand', r.brand_name_raw,
        'model', r.model_name_raw,
        'label', r.model_label_raw,
        'units', r.monthly_units,
        'share_pct', r.market_share_pct
      ) AS row_payload
    FROM requested_categories c
    JOIN public.v_market_fenabrave_model_rankings r
      ON r.vehicle_category = c.vehicle_category
     AND r.reference_period = v_reference_period
     AND r.item_code = 'fenabrave_item_01_ranking_emplacamentos_mes'
  ),
  overall_model_json AS (
    SELECT
      scope_key,
      COALESCE(jsonb_agg(row_payload ORDER BY rank_position), '[]'::jsonb) AS payload
    FROM overall_model_ranked
    WHERE row_num <= 5
    GROUP BY scope_key
  ),
  retail_model_ranked AS (
    SELECT
      c.scope_key,
      r.rank_position,
      row_number() OVER (
        PARTITION BY c.scope_key
        ORDER BY r.rank_position
      ) AS row_num,
      jsonb_build_object(
        'rank', r.rank_position,
        'brand', r.brand_name_raw,
        'model', r.model_name_raw,
        'label', r.model_label_raw,
        'units', r.monthly_units,
        'share_pct', r.market_share_pct
      ) AS row_payload
    FROM requested_categories c
    JOIN public.v_market_fenabrave_model_rankings r
      ON r.vehicle_category = c.vehicle_category
     AND r.reference_period = v_reference_period
     AND r.item_code = 'fenabrave_item_20_modelos_emplacados_varejo_mes'
  ),
  retail_model_json AS (
    SELECT
      scope_key,
      COALESCE(jsonb_agg(row_payload ORDER BY rank_position), '[]'::jsonb) AS payload
    FROM retail_model_ranked
    WHERE row_num <= 5
    GROUP BY scope_key
  ),
  direct_model_ranked AS (
    SELECT
      c.scope_key,
      r.rank_position,
      row_number() OVER (
        PARTITION BY c.scope_key
        ORDER BY r.rank_position
      ) AS row_num,
      jsonb_build_object(
        'rank', r.rank_position,
        'brand', r.brand_name_raw,
        'model', r.model_name_raw,
        'label', r.model_label_raw,
        'units', r.monthly_units,
        'share_pct', r.market_share_pct
      ) AS row_payload
    FROM requested_categories c
    JOIN public.v_market_fenabrave_model_rankings r
      ON r.vehicle_category = c.vehicle_category
     AND r.reference_period = v_reference_period
     AND r.item_code = 'fenabrave_item_19_modelos_emplacados_venda_direta_mes'
  ),
  direct_model_json AS (
    SELECT
      scope_key,
      COALESCE(jsonb_agg(row_payload ORDER BY rank_position), '[]'::jsonb) AS payload
    FROM direct_model_ranked
    WHERE row_num <= 5
    GROUP BY scope_key
  ),
  model_leaders_json AS (
    SELECT jsonb_build_object(
      'overall',
        COALESCE(
          (
            SELECT jsonb_object_agg(c.scope_key, COALESCE(o.payload, '[]'::jsonb))
            FROM requested_categories c
            LEFT JOIN overall_model_json o
              ON o.scope_key = c.scope_key
          ),
          '{}'::jsonb
        ),
      'retail',
        COALESCE(
          (
            SELECT jsonb_object_agg(c.scope_key, COALESCE(r.payload, '[]'::jsonb))
            FROM requested_categories c
            LEFT JOIN retail_model_json r
              ON r.scope_key = c.scope_key
          ),
          '{}'::jsonb
        ),
      'direct',
        COALESCE(
          (
            SELECT jsonb_object_agg(c.scope_key, COALESCE(d.payload, '[]'::jsonb))
            FROM requested_categories c
            LEFT JOIN direct_model_json d
              ON d.scope_key = c.scope_key
          ),
          '{}'::jsonb
        )
    ) AS payload
  ),
  electrified_market_current AS (
    SELECT
      c.scope_key,
      r.powertrain_type,
      r.units,
      r.market_share_pct
    FROM requested_categories c
    JOIN public.v_market_fenabrave_electrified_registrations r
      ON r.vehicle_category = c.vehicle_category
     AND r.reference_period = v_reference_period
     AND r.item_code = 'fenabrave_item_06_mercado_eletrificados_mes'
     AND r.aggregation_level = 'market'
  ),
  electrified_market_previous AS (
    SELECT
      c.scope_key,
      r.powertrain_type,
      r.units
    FROM requested_categories c
    JOIN public.v_market_fenabrave_electrified_registrations r
      ON r.vehicle_category = c.vehicle_category
     AND r.reference_period = v_previous_reference_period
     AND r.item_code = 'fenabrave_item_06_mercado_eletrificados_mes'
     AND r.aggregation_level = 'market'
  ),
  electrified_market_rows AS (
    SELECT
      c.scope_key,
      c.powertrain_type,
      c.units,
      c.market_share_pct,
      p.units AS previous_units
    FROM electrified_market_current c
    LEFT JOIN electrified_market_previous p
      ON p.scope_key = c.scope_key
     AND p.powertrain_type = c.powertrain_type
  ),
  electrified_market_json AS (
    SELECT
      c.scope_key,
      CASE
        WHEN COUNT(r.powertrain_type) = 0 THEN
          jsonb_build_object(
            'available', false,
            'reason', 'No validated electrified market summary available.',
            'powertrains', '{}'::jsonb
          )
        ELSE
          jsonb_build_object(
            'available', true,
            'powertrains',
              COALESCE(
                jsonb_object_agg(
                  r.powertrain_type,
                  jsonb_build_object(
                    'units', r.units,
                    'market_share_pct', r.market_share_pct,
                    'previous_units', r.previous_units,
                    'mom_pct',
                      CASE
                        WHEN r.previous_units IS NULL OR r.previous_units = 0 THEN NULL
                        ELSE ROUND(((r.units::numeric / r.previous_units::numeric) - 1) * 100, 2)
                      END
                  )
                ) FILTER (WHERE r.powertrain_type IS NOT NULL),
                '{}'::jsonb
              )
          )
      END AS payload
    FROM requested_categories c
    LEFT JOIN electrified_market_rows r
      ON r.scope_key = c.scope_key
    GROUP BY c.scope_key
  ),
  electrified_brand_ranked AS (
    SELECT
      c.scope_key,
      r.powertrain_type,
      r.rank_position,
      row_number() OVER (
        PARTITION BY c.scope_key, r.powertrain_type
        ORDER BY r.rank_position
      ) AS row_num,
      jsonb_build_object(
        'rank', r.rank_position,
        'brand', r.brand_name_raw,
        'units', r.units,
        'share_pct', r.market_share_pct
      ) AS row_payload
    FROM requested_categories c
    JOIN public.v_market_fenabrave_electrified_registrations r
      ON r.vehicle_category = c.vehicle_category
     AND r.reference_period = v_reference_period
     AND r.aggregation_level = 'brand'
     AND r.powertrain_type IN ('hybrid', 'electric')
  ),
  electrified_brand_payloads AS (
    SELECT
      scope_key,
      powertrain_type,
      COALESCE(jsonb_agg(row_payload ORDER BY rank_position), '[]'::jsonb) AS payload
    FROM electrified_brand_ranked
    WHERE row_num <= 5
    GROUP BY scope_key, powertrain_type
  ),
  electrified_brand_json AS (
    SELECT
      c.scope_key,
      CASE
        WHEN COUNT(b.powertrain_type) = 0 THEN
          jsonb_build_object(
            'available', false,
            'reason', 'No validated electrified brand rankings available.',
            'powertrains', '{}'::jsonb
          )
        ELSE
          jsonb_build_object(
            'available', true,
            'powertrains',
              COALESCE(
                jsonb_object_agg(b.powertrain_type, b.payload)
                  FILTER (WHERE b.powertrain_type IS NOT NULL),
                '{}'::jsonb
              )
          )
      END AS payload
    FROM requested_categories c
    LEFT JOIN electrified_brand_payloads b
      ON b.scope_key = c.scope_key
    GROUP BY c.scope_key
  ),
  electrified_model_ranked AS (
    SELECT
      c.scope_key,
      r.powertrain_type,
      r.rank_position,
      row_number() OVER (
        PARTITION BY c.scope_key, r.powertrain_type
        ORDER BY r.rank_position
      ) AS row_num,
      jsonb_build_object(
        'rank', r.rank_position,
        'brand', r.brand_name_raw,
        'model', r.model_name_raw,
        'units', r.units,
        'share_pct', r.market_share_pct
      ) AS row_payload
    FROM requested_categories c
    JOIN public.v_market_fenabrave_electrified_registrations r
      ON r.vehicle_category = c.vehicle_category
     AND r.reference_period = v_reference_period
     AND r.aggregation_level = 'model'
     AND r.powertrain_type IN ('hybrid', 'electric')
  ),
  electrified_model_payloads AS (
    SELECT
      scope_key,
      powertrain_type,
      COALESCE(jsonb_agg(row_payload ORDER BY rank_position), '[]'::jsonb) AS payload
    FROM electrified_model_ranked
    WHERE row_num <= 5
    GROUP BY scope_key, powertrain_type
  ),
  electrified_model_json AS (
    SELECT
      c.scope_key,
      CASE
        WHEN COUNT(m.powertrain_type) = 0 THEN
          jsonb_build_object(
            'available', false,
            'reason', 'No validated electrified model rankings available for this category.',
            'powertrains', '{}'::jsonb
          )
        ELSE
          jsonb_build_object(
            'available', true,
            'powertrains',
              COALESCE(
                jsonb_object_agg(m.powertrain_type, m.payload)
                  FILTER (WHERE m.powertrain_type IS NOT NULL),
                '{}'::jsonb
              )
          )
      END AS payload
    FROM requested_categories c
    LEFT JOIN electrified_model_payloads m
      ON m.scope_key = c.scope_key
    GROUP BY c.scope_key
  ),
  electrified_categories_json AS (
    SELECT COALESCE(
      jsonb_object_agg(
        c.scope_key,
        jsonb_build_object(
          'available',
            COALESCE((em.payload ->> 'available')::boolean, false)
            OR COALESCE((eb.payload ->> 'available')::boolean, false)
            OR COALESCE((tm.payload ->> 'available')::boolean, false),
          'market_summary', COALESCE(em.payload, jsonb_build_object(
            'available', false,
            'reason', 'No validated electrified market summary available.',
            'powertrains', '{}'::jsonb
          )),
          'top_brands', COALESCE(eb.payload, jsonb_build_object(
            'available', false,
            'reason', 'No validated electrified brand rankings available.',
            'powertrains', '{}'::jsonb
          )),
          'top_models', COALESCE(tm.payload, jsonb_build_object(
            'available', false,
            'reason', 'No validated electrified model rankings available for this category.',
            'powertrains', '{}'::jsonb
          ))
        )
      ),
      '{}'::jsonb
    ) AS payload
    FROM requested_categories c
    LEFT JOIN electrified_market_json em
      ON em.scope_key = c.scope_key
    LEFT JOIN electrified_brand_json eb
      ON eb.scope_key = c.scope_key
    LEFT JOIN electrified_model_json tm
      ON tm.scope_key = c.scope_key
  )
  SELECT jsonb_build_object(
    'status', 'ok',
    'source_name', 'Fenabrave',
    'reference_period', to_char(v_reference_period, 'YYYY-MM'),
    'scope', v_scope,
    'source_page_url', v_source_page_url,
    'source_url', v_source_url,
    'retrieved_from_db_at', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
    'totals',
      (
        SELECT jsonb_build_object(
          'available', current_month_units > 0,
          'current_month_units', current_month_units,
          'previous_month_units', previous_month_units,
          'mom_pct',
            CASE
              WHEN previous_month_units IS NULL OR previous_month_units = 0 THEN NULL
              ELSE ROUND(((current_month_units::numeric / previous_month_units::numeric) - 1) * 100, 2)
            END
        )
        FROM totals_base
      ),
    'channel_mix', (SELECT payload FROM channel_mix_json),
    'brand_share_total', (SELECT payload FROM brand_total_json),
    'brand_share_retail', (SELECT payload FROM brand_retail_json),
    'brand_share_direct', (SELECT payload FROM brand_direct_json),
    'model_leaders', (SELECT payload FROM model_leaders_json),
    'electrified', jsonb_build_object(
      'available', EXISTS (SELECT 1 FROM requested_categories),
      'categories', (SELECT payload FROM electrified_categories_json)
    ),
    'editorial_notes', jsonb_build_object(
      'market_proxy_warning', 'Emplacamento e proxy de mercado, nao prova venda final ao consumidor.',
      'causality_warning', 'Separar fato, sinal e hipotese; nao inferir causalidade sem evidencia externa.',
      'scope_warning',
        CASE v_scope
          WHEN 'autos' THEN 'Leitura focada apenas em autos.'
          WHEN 'comerciais_leves' THEN 'Leitura focada apenas em comerciais leves.'
          ELSE 'Leitura principal em autos + comerciais leves, com liderancas separadas por categoria quando houver diferenca.'
        END
    )
  )
  INTO v_packet;

  RETURN COALESCE(
    v_packet,
    jsonb_build_object(
      'status', 'not_available',
      'reference_period', to_char(v_reference_period, 'YYYY-MM'),
      'scope', v_scope,
      'reason', 'Packet could not be built from the validated Fenabrave layer.'
    )
  );
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_fenabrave_monthly_packet(date, text) TO anon, authenticated;
