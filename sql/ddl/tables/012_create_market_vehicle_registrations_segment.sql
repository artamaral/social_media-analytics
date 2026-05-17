-- 012_create_market_vehicle_registrations_segment.sql

-- Serie mensal normalizada de emplacamentos por segmento, extraida da
-- primeira tabela do PDF Fenabrave. A tabela guarda apenas os campos
-- efetivamente gerados pela extracao: segment_code, segmento e mes_atual,
-- alem dos campos de rastreabilidade do arquivo e periodo.
CREATE TABLE IF NOT EXISTS public.market_vehicle_registrations_segment (
  id BIGSERIAL PRIMARY KEY,
  source_file_id BIGINT NOT NULL REFERENCES public.market_source_files(id),
  reference_period DATE NOT NULL,
  segment_code TEXT NOT NULL,
  segmento TEXT NOT NULL,
  mes_atual INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT market_vehicle_reg_segment_unique UNIQUE (
    source_file_id,
    reference_period,
    segment_code
  ),
  CONSTRAINT market_vehicle_reg_segment_mes_atual_check CHECK (
    mes_atual >= 0
  )
);

COMMENT ON TABLE public.market_vehicle_registrations_segment IS
  'Serie mensal de emplacamentos por segmento Fenabrave, vinculada ao arquivo original.';

COMMENT ON COLUMN public.market_vehicle_registrations_segment.source_file_id IS
  'Arquivo de origem cadastrado em public.market_source_files.';

COMMENT ON COLUMN public.market_vehicle_registrations_segment.reference_period IS
  'Periodo de referencia do dado, usando o primeiro dia do mes.';

COMMENT ON COLUMN public.market_vehicle_registrations_segment.segment_code IS
  'Codigo normalizado do segmento extraido, como autos ou comerciais_leves.';

COMMENT ON COLUMN public.market_vehicle_registrations_segment.segmento IS
  'Nome legivel do segmento exibido no preview de extracao.';

COMMENT ON COLUMN public.market_vehicle_registrations_segment.mes_atual IS
  'Volume de emplacamentos do mes atual extraido da primeira tabela Fenabrave.';

-- Exemplo de registro para o PDF da Fenabrave de abril/2026:
--
-- INSERT INTO public.market_vehicle_registrations_segment (
--   source_file_id,
--   reference_period,
--   segment_code,
--   segmento,
--   mes_atual
-- )
-- VALUES (
--   1,
--   DATE '2026-04-01',
--   'autos',
--   'Autos',
--   187313
-- );
