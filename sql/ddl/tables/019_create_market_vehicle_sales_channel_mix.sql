-- 019_create_market_vehicle_sales_channel_mix.sql

-- Participacao Fenabrave por canal de venda, cobrindo os itens 11 e 12 da
-- fase 2: percentual de venda direta e varejo para automoveis, comerciais
-- leves e agregado autos + comerciais leves.
CREATE TABLE IF NOT EXISTS public.market_vehicle_sales_channel_mix (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  reference_period DATE NOT NULL,
  item_code TEXT NOT NULL,
  published_period_type TEXT NOT NULL,
  market_scope TEXT NOT NULL DEFAULT 'Brasil',
  vehicle_category TEXT NOT NULL,
  sales_channel TEXT NOT NULL,
  share_pct NUMERIC(8, 4) NOT NULL,
  raw_label TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_vehicle_sales_channel_mix_unique UNIQUE (
    source_file_id,
    item_code,
    published_period_type,
    vehicle_category,
    sales_channel
  ),
  CONSTRAINT market_vehicle_sales_channel_mix_period_type_check CHECK (
    published_period_type IN ('monthly', 'accumulated')
  ),
  CONSTRAINT market_vehicle_sales_channel_mix_category_check CHECK (
    vehicle_category IN ('automoveis', 'comerciais_leves', 'autos_comerciais_leves')
  ),
  CONSTRAINT market_vehicle_sales_channel_mix_sales_channel_check CHECK (
    sales_channel IN ('direct', 'retail')
  ),
  CONSTRAINT market_vehicle_sales_channel_mix_share_check CHECK (
    share_pct BETWEEN 0 AND 100
  )
);

CREATE INDEX IF NOT EXISTS market_vehicle_sales_channel_mix_period_idx
  ON public.market_vehicle_sales_channel_mix (
    reference_period,
    item_code,
    published_period_type,
    vehicle_category,
    sales_channel
  );

COMMENT ON TABLE public.market_vehicle_sales_channel_mix IS
  'Participacao Fenabrave de venda direta e varejo por categoria de veiculo, vinculada ao PDF original e ao item de extracao.';

COMMENT ON COLUMN public.market_vehicle_sales_channel_mix.vehicle_category IS
  'Categoria publicada no grafico Fenabrave: automoveis, comerciais_leves ou autos_comerciais_leves.';

COMMENT ON COLUMN public.market_vehicle_sales_channel_mix.sales_channel IS
  'Canal de venda publicado no grafico Fenabrave: direct ou retail.';

COMMENT ON COLUMN public.market_vehicle_sales_channel_mix.share_pct IS
  'Percentual publicado no grafico Fenabrave para o canal de venda e categoria.';
