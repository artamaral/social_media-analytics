-- 024_add_catalog_model_match_to_video_vehicle_entities.sql

-- Adiciona match em nivel de modelo para entidades de veiculo classificadas.
-- catalog_row_id continua sendo usado apenas quando ha ano/modelo explicito.

ALTER TABLE public.video_classification_vehicle_entities
  ADD COLUMN IF NOT EXISTS catalog_model_id BIGINT,
  ADD COLUMN IF NOT EXISTS catalog_match_level TEXT;

ALTER TABLE public.video_classification_vehicle_entities
  DROP CONSTRAINT IF EXISTS video_classification_vehicle_entities_catalog_match_level_check;

ALTER TABLE public.video_classification_vehicle_entities
  ADD CONSTRAINT video_classification_vehicle_entities_catalog_match_level_check CHECK (
    catalog_match_level IS NULL
    OR catalog_match_level IN (
      'model_year',
      'model',
      'manufacturer',
      'ambiguous',
      'not_found'
    )
  );

CREATE INDEX IF NOT EXISTS video_classification_vehicle_entities_catalog_model_idx
  ON public.video_classification_vehicle_entities (catalog_model_id, catalog_row_id);

COMMENT ON COLUMN public.video_classification_vehicle_entities.catalog_model_id IS
  'Identificador canonico do modelo no catalogo Carros na Web quando o ano nao esta sustentado pela evidencia.';

COMMENT ON COLUMN public.video_classification_vehicle_entities.catalog_match_level IS
  'Nivel do match canonico: model_year, model, manufacturer, ambiguous ou not_found.';
