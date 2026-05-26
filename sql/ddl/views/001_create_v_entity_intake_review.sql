-- 002_create_v_entity_intake_review.sql

-- Criar view de revisão para validar o que entrou na tabela entity_intake.
-- A view mostra:
-- 1) se a entity já existe na tabela entities
-- 2) se o sub_niche informado existe na tabela sub_niches
-- 3) o status de revisão do registro antes da publicação
CREATE OR REPLACE VIEW public.v_entity_intake_review AS
SELECT
  ei.id,
  ei.raw_name,
  ei.normalized_name,
  ei.sub_niche_name,
  ei.niche,
  ei.creator_type,
  ei.notes,
  ei.status,
  ei.created_at,
  e.id AS existing_entity_id,
  e.name AS existing_entity_name,
  sn.id AS sub_niche_id,
  sn.name AS matched_sub_niche_name,
  CASE
    WHEN ei.normalized_name IS NULL THEN 'NORMALIZATION_MISSING'
    WHEN sn.id IS NULL THEN 'SUB_NICHE_NOT_FOUND'
    WHEN e.id IS NOT NULL THEN 'ENTITY_ALREADY_EXISTS'
    ELSE 'READY_TO_INSERT'
  END AS review_result
FROM public.entity_intake ei
LEFT JOIN public.entities e
  ON e.normalized_name = ei.normalized_name
LEFT JOIN public.sub_niches sn
  ON LOWER(TRIM(unaccent(sn.name::text))) = LOWER(TRIM(unaccent(ei.sub_niche_name)));

GRANT SELECT ON public.v_entity_intake_review TO anon;
GRANT SELECT ON public.v_entity_intake_review TO authenticated;
