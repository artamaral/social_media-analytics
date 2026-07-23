-- 021_create_market_carrosnaweb_catalog.sql

-- Catalogo Carros na Web importado a partir de CSVs recorrentes de fabricantes,
-- modelos e anos/modelo. A camada serve para homogeneizar entidades de veiculo
-- extraidas de descricoes e transcricoes, sem depender de fichas tecnicas.

CREATE TABLE IF NOT EXISTS public.market_carrosnaweb_manufacturers (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  manufacturer_name TEXT NOT NULL,
  manufacturer_param TEXT,
  manufacturer_key TEXT NOT NULL,
  source_value TEXT,
  manufacturer_url TEXT,
  params JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_carrosnaweb_manufacturers_unique UNIQUE (
    source_file_id,
    manufacturer_key
  )
);

CREATE INDEX IF NOT EXISTS market_carrosnaweb_manufacturers_key_idx
  ON public.market_carrosnaweb_manufacturers (manufacturer_key);

COMMENT ON TABLE public.market_carrosnaweb_manufacturers IS
  'Fabricantes do catalogo Carros na Web importados de CSV recorrente.';

COMMENT ON COLUMN public.market_carrosnaweb_manufacturers.manufacturer_name IS
  'Nome bruto/canonico do fabricante conforme o CSV.';

COMMENT ON COLUMN public.market_carrosnaweb_manufacturers.manufacturer_param IS
  'Valor de fabricante extraido do campo params quando disponivel.';

COMMENT ON COLUMN public.market_carrosnaweb_manufacturers.manufacturer_key IS
  'Chave normalizada para matching e homogeneizacao de entidades.';


CREATE TABLE IF NOT EXISTS public.market_carrosnaweb_models (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  manufacturer_name TEXT NOT NULL,
  manufacturer_param TEXT,
  manufacturer_key TEXT NOT NULL,
  model_name TEXT NOT NULL,
  model_param TEXT,
  model_key TEXT NOT NULL,
  model_code TEXT,
  model_url TEXT,
  href_original TEXT,
  link_text TEXT,
  params JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_carrosnaweb_models_unique UNIQUE (
    source_file_id,
    manufacturer_key,
    model_key
  )
);

CREATE INDEX IF NOT EXISTS market_carrosnaweb_models_lookup_idx
  ON public.market_carrosnaweb_models (manufacturer_key, model_key);

CREATE INDEX IF NOT EXISTS market_carrosnaweb_models_model_key_idx
  ON public.market_carrosnaweb_models (model_key);

COMMENT ON TABLE public.market_carrosnaweb_models IS
  'Modelos do catalogo Carros na Web importados de CSV recorrente.';

COMMENT ON COLUMN public.market_carrosnaweb_models.model_param IS
  'Valor de modelo extraido do campo params quando disponivel.';

COMMENT ON COLUMN public.market_carrosnaweb_models.model_key IS
  'Chave normalizada do modelo para matching e homogeneizacao.';


CREATE TABLE IF NOT EXISTS public.market_carrosnaweb_model_years (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  manufacturer_name TEXT NOT NULL,
  manufacturer_param TEXT,
  manufacturer_key TEXT NOT NULL,
  model_name TEXT NOT NULL,
  model_param TEXT,
  model_key TEXT NOT NULL,
  model_year INTEGER NOT NULL,
  param_year_start INTEGER,
  param_year_end INTEGER,
  year_url TEXT,
  source_model_url TEXT,
  href_original TEXT,
  link_text TEXT,
  params JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_carrosnaweb_model_years_unique UNIQUE (
    source_file_id,
    manufacturer_key,
    model_key,
    model_year
  ),
  CONSTRAINT market_carrosnaweb_model_years_year_check CHECK (
    model_year BETWEEN 1900 AND 2100
  ),
  CONSTRAINT market_carrosnaweb_model_years_param_year_start_check CHECK (
    param_year_start IS NULL OR param_year_start BETWEEN 1900 AND 2100
  ),
  CONSTRAINT market_carrosnaweb_model_years_param_year_end_check CHECK (
    param_year_end IS NULL OR param_year_end BETWEEN 1900 AND 2100
  )
);

CREATE INDEX IF NOT EXISTS market_carrosnaweb_model_years_lookup_idx
  ON public.market_carrosnaweb_model_years (
    manufacturer_key,
    model_key,
    model_year
  );

CREATE INDEX IF NOT EXISTS market_carrosnaweb_model_years_model_key_idx
  ON public.market_carrosnaweb_model_years (model_key, model_year);

COMMENT ON TABLE public.market_carrosnaweb_model_years IS
  'Anos/modelo do catalogo Carros na Web importados de CSV recorrente.';

COMMENT ON COLUMN public.market_carrosnaweb_model_years.model_year IS
  'Ano/modelo publicado no CSV.';

COMMENT ON COLUMN public.market_carrosnaweb_model_years.param_year_start IS
  'Valor anoini extraido de params quando disponivel.';

COMMENT ON COLUMN public.market_carrosnaweb_model_years.param_year_end IS
  'Valor anofim extraido de params quando disponivel.';
