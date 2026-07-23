-- 010_create_market_data_sources.sql

-- Cadastro das fontes externas usadas pela camada de inteligencia de mercado.
-- Fenabrave, SENATRAN/RENAVAM e Carros na Web sao fontes previstas para
-- ingestao estruturada no Supabase.
CREATE TABLE IF NOT EXISTS public.market_data_sources (
  id BIGSERIAL PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  data_role TEXT NOT NULL,
  structured_ingestion BOOLEAN NOT NULL DEFAULT false,
  priority INTEGER,
  access_type TEXT NOT NULL,
  official_url TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_data_sources_source_name_key UNIQUE (source_name),
  CONSTRAINT market_data_sources_priority_check CHECK (
    priority IS NULL OR priority > 0
  )
);

COMMENT ON TABLE public.market_data_sources IS
  'Cadastro de fontes externas automotivas usadas para analytics, contexto e ingestao estruturada.';

COMMENT ON COLUMN public.market_data_sources.source_name IS
  'Nome canonico da fonte, como Fenabrave ou SENATRAN/RENAVAM.';

COMMENT ON COLUMN public.market_data_sources.source_type IS
  'Tipo da fonte, como entidade_setorial, governo ou contexto_setorial.';

COMMENT ON COLUMN public.market_data_sources.data_role IS
  'Papel analitico principal da fonte, como emplacamento, frota ou contexto.';

COMMENT ON COLUMN public.market_data_sources.structured_ingestion IS
  'Indica se a fonte deve ser ingerida como dado estruturado no Supabase.';

COMMENT ON COLUMN public.market_data_sources.priority IS
  'Prioridade de uso da fonte dentro da arquitetura de dados externos.';

COMMENT ON COLUMN public.market_data_sources.access_type IS
  'Tipo de acesso da fonte, como publico_pdf, dados_abertos, publico_site ou restrito.';

COMMENT ON COLUMN public.market_data_sources.official_url IS
  'URL oficial da pagina principal da fonte.';

-- Exemplo de cadastro inicial:
--
-- INSERT INTO public.market_data_sources (
--   source_name,
--   source_type,
--   data_role,
--   structured_ingestion,
--   priority,
--   access_type,
--   official_url,
--   notes
-- )
-- VALUES (
--   'Fenabrave',
--   'entidade_setorial',
--   'emplacamento',
--   true,
--   1,
--   'publico_pdf',
--   'https://www.fenabrave.org.br/portalv2/Conteudo/Emplacamentos%20',
--   'Fonte pratica principal para emplacamentos e leitura mensal de mercado.'
-- );
