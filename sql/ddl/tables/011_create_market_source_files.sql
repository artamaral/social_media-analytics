-- 011_create_market_source_files.sql

-- Registro de cada arquivo, URL ou publicacao capturada de uma fonte externa.
-- Para Fenabrave, esta tabela liga o PDF original salvo no Supabase Storage
-- ao periodo de referencia e ao processo de extracao.
CREATE TABLE IF NOT EXISTS public.market_source_files (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT NOT NULL REFERENCES public.market_data_sources(id),
  reference_period DATE NOT NULL,
  source_url TEXT NOT NULL,
  source_page_url TEXT,
  file_type TEXT NOT NULL,
  storage_bucket TEXT,
  storage_path TEXT,
  original_filename TEXT,
  file_size_bytes BIGINT,
  sha256 TEXT,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  extraction_status TEXT NOT NULL DEFAULT 'pending',
  extraction_method TEXT,
  extraction_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_source_files_unique_file UNIQUE (
    source_id,
    reference_period,
    source_url
  ),
  CONSTRAINT market_source_files_file_size_check CHECK (
    file_size_bytes IS NULL OR file_size_bytes > 0
  ),
  CONSTRAINT market_source_files_status_check CHECK (
    extraction_status IN (
      'pending',
      'downloaded',
      'stored',
      'extracted',
      'normalized',
      'validated',
      'failed'
    )
  )
);

COMMENT ON TABLE public.market_source_files IS
  'Arquivos e publicacoes capturados de fontes externas, com metadados de origem, storage e extracao.';

COMMENT ON COLUMN public.market_source_files.source_id IS
  'Fonte externa cadastrada em public.market_data_sources.';

COMMENT ON COLUMN public.market_source_files.reference_period IS
  'Periodo de referencia do dado, usando o primeiro dia do mes para publicacoes mensais.';

COMMENT ON COLUMN public.market_source_files.source_url IS
  'URL direta do arquivo ou publicacao usada como origem.';

COMMENT ON COLUMN public.market_source_files.source_page_url IS
  'Pagina oficial onde a publicacao ou arquivo foi encontrado.';

COMMENT ON COLUMN public.market_source_files.file_type IS
  'Tipo do arquivo ou origem, como pdf, csv, xlsx ou html.';

COMMENT ON COLUMN public.market_source_files.storage_bucket IS
  'Bucket do Supabase Storage onde a copia do arquivo original foi preservada.';

COMMENT ON COLUMN public.market_source_files.storage_path IS
  'Caminho do arquivo dentro do bucket do Supabase Storage.';

COMMENT ON COLUMN public.market_source_files.sha256 IS
  'Hash SHA-256 do arquivo capturado, usado para auditoria e deteccao de mudanca.';

COMMENT ON COLUMN public.market_source_files.extraction_status IS
  'Status operacional da extracao do arquivo.';

COMMENT ON COLUMN public.market_source_files.extraction_method IS
  'Metodo usado para extrair o dado, como pdf_table_extraction.';

-- Exemplo de registro para o PDF da Fenabrave de abril/2026:
--
-- INSERT INTO public.market_source_files (
--   source_id,
--   reference_period,
--   source_url,
--   source_page_url,
--   file_type,
--   storage_bucket,
--   storage_path,
--   original_filename,
--   file_size_bytes,
--   sha256,
--   extraction_status,
--   extraction_method,
--   extraction_notes
-- )
-- VALUES (
--   1,
--   DATE '2026-04-01',
--   'https://www.fenabrave.org.br/portal/files/2026_04_02.pdf',
--   'https://www.fenabrave.org.br/portalv2/Conteudo/Emplacamentos%20',
--   'pdf',
--   'market-source-files',
--   'fenabrave/2026/04/2026_04_02.pdf',
--   '2026_04_02.pdf',
--   123456,
--   'sha256_a_calcular',
--   'stored',
--   'pdf_table_extraction',
--   'PDF de abril/2026 ja preservado no Supabase Storage.'
-- );
