-- 022_create_v_carrosnaweb_vehicle_catalog.sql

-- View inicial de consulta do catalogo Carros na Web para validar e
-- homogeneizar entidades de veiculo extraidas de descricoes/transcricoes.
CREATE OR REPLACE VIEW public.v_carrosnaweb_vehicle_catalog AS
SELECT
  y.id AS catalog_row_id,
  y.source_file_id,
  s.source_name,
  f.reference_period,
  f.sha256 AS source_file_sha256,
  y.manufacturer_name,
  y.manufacturer_key,
  y.model_name,
  y.model_key,
  y.model_year,
  y.manufacturer_param,
  y.model_param,
  y.param_year_start,
  y.param_year_end,
  y.year_url,
  y.source_model_url,
  y.params
FROM public.market_carrosnaweb_model_years y
JOIN public.market_source_files f
  ON f.id = y.source_file_id
JOIN public.market_data_sources s
  ON s.id = f.source_id;

COMMENT ON VIEW public.v_carrosnaweb_vehicle_catalog IS
  'Catalogo Carros na Web em fabricante/modelo/ano para matching de entidades automotivas extraidas de videos.';
