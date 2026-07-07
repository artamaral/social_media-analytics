-- 014_create_market_vehicle_model_rankings.sql

-- Rankings de modelos extraidos da Fenabrave. A primeira carga prevista e o
-- item 1 da fase 2: ranking mensal de emplacamentos da pagina 6, separado em
-- automoveis e comerciais leves.
CREATE TABLE IF NOT EXISTS public.market_vehicle_model_rankings (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  reference_period DATE NOT NULL,
  item_code TEXT NOT NULL,
  published_period_type TEXT NOT NULL,
  market_scope TEXT NOT NULL DEFAULT 'Brasil',
  vehicle_category TEXT NOT NULL,
  sales_channel TEXT NOT NULL DEFAULT 'all',
  rank_position INTEGER NOT NULL,
  brand_name_raw TEXT,
  model_name_raw TEXT,
  model_label_raw TEXT NOT NULL,
  monthly_units INTEGER,
  market_share_pct NUMERIC(8, 4),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_vehicle_model_rankings_unique UNIQUE (
    source_file_id,
    item_code,
    published_period_type,
    vehicle_category,
    rank_position
  ),
  CONSTRAINT market_vehicle_model_rankings_period_type_check CHECK (
    published_period_type IN ('monthly', 'accumulated')
  ),
  CONSTRAINT market_vehicle_model_rankings_category_check CHECK (
    vehicle_category IN ('automoveis', 'comerciais_leves')
  ),
  CONSTRAINT market_vehicle_model_rankings_sales_channel_check CHECK (
    sales_channel IN ('all', 'retail', 'direct')
  ),
  CONSTRAINT market_vehicle_model_rankings_rank_check CHECK (
    rank_position BETWEEN 1 AND 200
  ),
  CONSTRAINT market_vehicle_model_rankings_units_check CHECK (
    monthly_units IS NULL OR monthly_units >= 0
  ),
  CONSTRAINT market_vehicle_model_rankings_share_check CHECK (
    market_share_pct IS NULL
    OR market_share_pct BETWEEN 0 AND 100
  )
);

CREATE INDEX IF NOT EXISTS market_vehicle_model_rankings_period_idx
  ON public.market_vehicle_model_rankings (
    reference_period,
    item_code,
    vehicle_category,
    rank_position
  );

COMMENT ON TABLE public.market_vehicle_model_rankings IS
  'Rankings Fenabrave por modelo, vinculados ao PDF original e ao item de extracao.';

COMMENT ON COLUMN public.market_vehicle_model_rankings.item_code IS
  'Codigo estavel do item de extracao Fenabrave.';

COMMENT ON COLUMN public.market_vehicle_model_rankings.vehicle_category IS
  'Categoria do ranking no PDF, como automoveis ou comerciais_leves.';

COMMENT ON COLUMN public.market_vehicle_model_rankings.model_label_raw IS
  'Nome bruto extraido do PDF, preservando marca/modelo como publicado.';

COMMENT ON COLUMN public.market_vehicle_model_rankings.monthly_units IS
  'Volume mensal de emplacamentos extraido do ranking publicado.';
