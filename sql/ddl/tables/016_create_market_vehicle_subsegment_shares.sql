-- 016_create_market_vehicle_subsegment_shares.sql

-- Shares Fenabrave por subsegmento de automoveis (item 5 da fase 2).
CREATE TABLE IF NOT EXISTS public.market_vehicle_subsegment_shares (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  reference_period DATE NOT NULL,
  item_code TEXT NOT NULL,
  published_period_type TEXT NOT NULL DEFAULT 'mixed',
  market_scope TEXT NOT NULL DEFAULT 'Brasil',
  vehicle_category TEXT NOT NULL,
  sales_channel TEXT NOT NULL DEFAULT 'all',
  subsegment_name TEXT NOT NULL,
  current_month_share_pct NUMERIC(8, 4) NOT NULL,
  current_year_accum_share_pct NUMERIC(8, 4) NOT NULL,
  prior_year_accum_share_pct NUMERIC(8, 4) NOT NULL,
  raw_label TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_vehicle_subsegment_shares_unique UNIQUE (
    source_file_id,
    item_code,
    vehicle_category,
    subsegment_name
  ),
  CONSTRAINT market_vehicle_subsegment_shares_period_type_check CHECK (
    published_period_type = 'mixed'
  ),
  CONSTRAINT market_vehicle_subsegment_shares_category_check CHECK (
    vehicle_category IN ('automoveis')
  ),
  CONSTRAINT market_vehicle_subsegment_shares_sales_channel_check CHECK (
    sales_channel IN ('all')
  ),
  CONSTRAINT market_vehicle_subsegment_current_month_check CHECK (
    current_month_share_pct BETWEEN 0 AND 100
  ),
  CONSTRAINT market_vehicle_subsegment_current_year_check CHECK (
    current_year_accum_share_pct BETWEEN 0 AND 100
  ),
  CONSTRAINT market_vehicle_subsegment_prior_year_check CHECK (
    prior_year_accum_share_pct BETWEEN 0 AND 100
  )
);

CREATE INDEX IF NOT EXISTS market_vehicle_subsegment_shares_period_idx
  ON public.market_vehicle_subsegment_shares (
    reference_period,
    item_code,
    vehicle_category,
    subsegment_name
  );

COMMENT ON TABLE public.market_vehicle_subsegment_shares IS
  'Shares Fenabrave por subsegmento de automoveis, vinculados ao PDF original e ao item de extracao.';

COMMENT ON COLUMN public.market_vehicle_subsegment_shares.subsegment_name IS
  'Nome normalizado do subsegmento publicado no PDF, sem prefixos tecnicos como AU -.';

COMMENT ON COLUMN public.market_vehicle_subsegment_shares.current_month_share_pct IS
  'Participacao percentual do subsegmento no mes corrente do periodo.';

COMMENT ON COLUMN public.market_vehicle_subsegment_shares.current_year_accum_share_pct IS
  'Participacao percentual acumulada do ano corrente (n).';

COMMENT ON COLUMN public.market_vehicle_subsegment_shares.prior_year_accum_share_pct IS
  'Participacao percentual acumulada do ano anterior (n-1), mantida separada do acumulado corrente.';
