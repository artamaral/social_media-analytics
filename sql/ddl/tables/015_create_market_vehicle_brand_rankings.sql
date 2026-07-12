-- 015_create_market_vehicle_brand_rankings.sql

-- Rankings de marcas extraidos da Fenabrave. A modelagem cobre tanto rankings
-- com volume absoluto e share (itens 3 e 4) quanto rankings graficos por share
-- sem unidades publicadas (itens 13 a 16).
CREATE TABLE IF NOT EXISTS public.market_vehicle_brand_rankings (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  reference_period DATE NOT NULL,
  item_code TEXT NOT NULL,
  published_period_type TEXT NOT NULL,
  market_scope TEXT NOT NULL DEFAULT 'Brasil',
  vehicle_category TEXT NOT NULL,
  sales_channel TEXT NOT NULL DEFAULT 'all',
  rank_position INTEGER NOT NULL,
  brand_name_raw TEXT NOT NULL,
  units INTEGER,
  market_share_pct NUMERIC(8, 4),
  raw_label TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_vehicle_brand_rankings_unique UNIQUE (
    source_file_id,
    item_code,
    published_period_type,
    vehicle_category,
    rank_position
  ),
  CONSTRAINT market_vehicle_brand_rankings_period_type_check CHECK (
    published_period_type IN ('monthly', 'accumulated')
  ),
  CONSTRAINT market_vehicle_brand_rankings_category_check CHECK (
    vehicle_category IN ('automoveis', 'comerciais_leves')
  ),
  CONSTRAINT market_vehicle_brand_rankings_sales_channel_check CHECK (
    sales_channel IN ('all', 'retail', 'direct')
  ),
  CONSTRAINT market_vehicle_brand_rankings_rank_check CHECK (
    rank_position BETWEEN 1 AND 200
  ),
  CONSTRAINT market_vehicle_brand_rankings_units_check CHECK (
    units IS NULL OR units >= 0
  ),
  CONSTRAINT market_vehicle_brand_rankings_share_check CHECK (
    market_share_pct IS NULL OR market_share_pct BETWEEN 0 AND 100
  ),
  CONSTRAINT market_vehicle_brand_rankings_value_presence_check CHECK (
    units IS NOT NULL OR market_share_pct IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS market_vehicle_brand_rankings_period_idx
  ON public.market_vehicle_brand_rankings (
    reference_period,
    item_code,
    vehicle_category,
    rank_position
  );

COMMENT ON TABLE public.market_vehicle_brand_rankings IS
  'Rankings Fenabrave por marca, vinculados ao PDF original e ao item de extracao.';

COMMENT ON COLUMN public.market_vehicle_brand_rankings.item_code IS
  'Codigo estavel do item de extracao Fenabrave.';

COMMENT ON COLUMN public.market_vehicle_brand_rankings.vehicle_category IS
  'Categoria do ranking no PDF, como automoveis ou comerciais_leves.';

COMMENT ON COLUMN public.market_vehicle_brand_rankings.brand_name_raw IS
  'Nome bruto da marca como publicado no PDF Fenabrave.';

COMMENT ON COLUMN public.market_vehicle_brand_rankings.units IS
  'Volume publicado no ranking por marca da Fenabrave quando o PDF trouxer unidades; pode ficar nulo em rankings graficos por share.';
