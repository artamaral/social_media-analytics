-- 018_create_market_vehicle_electrified_registrations.sql

-- Registros Fenabrave de eletrificados, cobrindo os itens 6, 7 e 8 da fase 2:
-- mercado mensal consolidado e rankings mensais por marca para hibridos e
-- eletricos, separados por automoveis e comerciais leves.
CREATE TABLE IF NOT EXISTS public.market_vehicle_electrified_registrations (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  reference_period DATE NOT NULL,
  item_code TEXT NOT NULL,
  published_period_type TEXT NOT NULL DEFAULT 'monthly',
  market_scope TEXT NOT NULL DEFAULT 'Brasil',
  aggregation_level TEXT NOT NULL,
  powertrain_type TEXT NOT NULL,
  vehicle_category TEXT NOT NULL,
  rank_position INTEGER,
  brand_name_raw TEXT,
  model_name_raw TEXT,
  units INTEGER NOT NULL,
  market_share_pct NUMERIC(8, 4),
  raw_label TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_vehicle_electrified_registrations_unique UNIQUE (
    source_file_id,
    item_code,
    vehicle_category,
    aggregation_level,
    powertrain_type,
    rank_position,
    brand_name_raw,
    model_name_raw
  ),
  CONSTRAINT market_vehicle_electrified_period_type_check CHECK (
    published_period_type IN ('monthly')
  ),
  CONSTRAINT market_vehicle_electrified_aggregation_check CHECK (
    aggregation_level IN ('market', 'brand', 'model')
  ),
  CONSTRAINT market_vehicle_electrified_powertrain_check CHECK (
    powertrain_type IN ('hybrid', 'electric', 'total_electrified')
  ),
  CONSTRAINT market_vehicle_electrified_category_check CHECK (
    vehicle_category IN ('automoveis', 'comerciais_leves')
  ),
  CONSTRAINT market_vehicle_electrified_rank_check CHECK (
    rank_position IS NULL OR rank_position BETWEEN 1 AND 200
  ),
  CONSTRAINT market_vehicle_electrified_units_check CHECK (
    units >= 0
  ),
  CONSTRAINT market_vehicle_electrified_share_check CHECK (
    market_share_pct IS NULL OR market_share_pct BETWEEN 0 AND 100
  ),
  CONSTRAINT market_vehicle_electrified_market_shape_check CHECK (
    (
      aggregation_level = 'market'
      AND rank_position IS NULL
      AND brand_name_raw IS NULL
      AND model_name_raw IS NULL
      AND market_share_pct IS NULL
    )
    OR (
      aggregation_level = 'brand'
      AND rank_position IS NOT NULL
      AND brand_name_raw IS NOT NULL
      AND model_name_raw IS NULL
    )
    OR (
      aggregation_level = 'model'
      AND rank_position IS NOT NULL
      AND brand_name_raw IS NOT NULL
      AND model_name_raw IS NOT NULL
    )
  ),
  CONSTRAINT market_vehicle_electrified_total_scope_check CHECK (
    NOT (
      aggregation_level <> 'market'
      AND powertrain_type = 'total_electrified'
    )
  )
);

CREATE INDEX IF NOT EXISTS market_vehicle_electrified_registrations_period_idx
  ON public.market_vehicle_electrified_registrations (
    reference_period,
    item_code,
    vehicle_category,
    aggregation_level,
    powertrain_type,
    rank_position
  );

COMMENT ON TABLE public.market_vehicle_electrified_registrations IS
  'Registros Fenabrave de eletrificados por mercado, marca ou modelo, vinculados ao PDF original e ao item de extracao.';

COMMENT ON COLUMN public.market_vehicle_electrified_registrations.aggregation_level IS
  'Granularidade do bloco publicado no PDF: mercado consolidado, marca ou modelo.';

COMMENT ON COLUMN public.market_vehicle_electrified_registrations.powertrain_type IS
  'Tipo de propulsao publicado no PDF: hybrid, electric ou total_electrified no bloco consolidado.';

COMMENT ON COLUMN public.market_vehicle_electrified_registrations.brand_name_raw IS
  'Nome bruto da marca como publicado no ranking Fenabrave.';

COMMENT ON COLUMN public.market_vehicle_electrified_registrations.model_name_raw IS
  'Nome bruto do modelo quando houver ranking por modelo de eletrificados.';
