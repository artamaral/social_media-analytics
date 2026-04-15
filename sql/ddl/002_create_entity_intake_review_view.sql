/*
revisão
Você usa uma view para enxergar:

se já existe entity
se o subnicho existe
se há risco de duplicidade
*/
  
CREATE OR REPLACE VIEW public.v_entity_intake_review AS
SELECT
  ei.id,
  ei.raw_name,
  ei.normalized_name,
  ei.sub_niche_name,
  ei.niche,
  ei.creator_type,
  ei.status,
  e.id AS existing_entity_id,
  e.name AS existing_entity_name,
  sn.id AS sub_niche_id,
  CASE
    WHEN sn.id IS NULL THEN 'SUB_NICHE_NOT_FOUND'
    WHEN e.id IS NOT NULL THEN 'ENTITY_ALREADY_EXISTS'
    ELSE 'READY_TO_INSERT'
  END AS review_result
FROM public.entity_intake ei
LEFT JOIN public.entities e
  ON e.normalized_name = ei.normalized_name
LEFT JOIN public.sub_niches sn
  ON LOWER(TRIM(unaccent(sn.name::text))) = LOWER(TRIM(unaccent(ei.sub_niche_name)));
