-- 013_create_market_fenabrave_extraction_items.sql

-- Controle de execucao dos itens extraidos dos PDFs Fenabrave. Cada item da
-- fase 2 possui status proprio por arquivo, permitindo carga mensal parcial,
-- reprocessamento por item e auditoria de pendencias sem misturar resultados.
CREATE TABLE IF NOT EXISTS public.market_fenabrave_extraction_items (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  reference_period DATE NOT NULL,
  item_code TEXT NOT NULL,
  item_label TEXT NOT NULL,
  pdf_page INTEGER NOT NULL,
  published_period_type TEXT NOT NULL,
  market_scope TEXT NOT NULL DEFAULT 'Brasil',
  status TEXT NOT NULL DEFAULT 'pending',
  row_count INTEGER,
  validation_status TEXT,
  validation_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_fenabrave_extraction_items_unique UNIQUE (
    source_file_id,
    item_code
  ),
  CONSTRAINT market_fenabrave_extraction_items_page_check CHECK (
    pdf_page > 0
  ),
  CONSTRAINT market_fenabrave_extraction_items_period_type_check CHECK (
    published_period_type IN ('monthly', 'accumulated')
  ),
  CONSTRAINT market_fenabrave_extraction_items_status_check CHECK (
    status IN (
      'pending',
      'extracted',
      'validated',
      'failed',
      'skipped',
      'warning_accepted'
    )
  ),
  CONSTRAINT market_fenabrave_extraction_items_validation_status_check CHECK (
    validation_status IS NULL
    OR validation_status IN ('passed', 'warning', 'failed')
  ),
  CONSTRAINT market_fenabrave_extraction_items_row_count_check CHECK (
    row_count IS NULL OR row_count >= 0
  )
);

CREATE INDEX IF NOT EXISTS market_fenabrave_extraction_items_period_idx
  ON public.market_fenabrave_extraction_items (
    reference_period,
    item_code,
    status
  );

COMMENT ON TABLE public.market_fenabrave_extraction_items IS
  'Status por item extraido de cada PDF Fenabrave, usado para rotina mensal, backfill e auditoria de cobertura.';

COMMENT ON COLUMN public.market_fenabrave_extraction_items.source_file_id IS
  'Arquivo Fenabrave de origem cadastrado em public.market_source_files.';

COMMENT ON COLUMN public.market_fenabrave_extraction_items.item_code IS
  'Codigo estavel do item da fase 2, como fenabrave_item_01_ranking_emplacamentos_mes.';

COMMENT ON COLUMN public.market_fenabrave_extraction_items.status IS
  'Status operacional do item no arquivo: pending, extracted, validated, failed, skipped ou warning_accepted.';
