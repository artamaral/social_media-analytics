/*
raw_name: nome como você digitou
normalized_name: nome normalizado para checagem
sub_niche_name: subnicho escolhido manualmente
niche: no seu caso, quase sempre automotivo
creator_type: personal, media, etc.
notes: observações de negócio
status: estágio do cadastro
*/


CREATE TABLE public.entity_intake (
  id BIGSERIAL PRIMARY KEY,
  raw_name TEXT NOT NULL,
  normalized_name TEXT,
  sub_niche_name TEXT NOT NULL,
  niche TEXT NOT NULL DEFAULT 'automotivo',
  creator_type TEXT NOT NULL DEFAULT 'personal',
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'approved', 'published', 'rejected')
  ),
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TIMESTAMP WITHOUT TIME ZONE,
  published_at TIMESTAMP WITHOUT TIME ZONE
);

INSERT INTO public.entity_sub_niches (entity_id, sub_niche_id)
SELECT
  e.id,
  sn.id
FROM public.entity_intake ei
JOIN public.entities e
  ON e.normalized_name = ei.normalized_name
JOIN public.sub_niches sn
  ON LOWER(TRIM(unaccent(sn.name::text))) = LOWER(TRIM(unaccent(ei.sub_niche_name)))
LEFT JOIN public.entity_sub_niches esn
  ON esn.entity_id = e.id
 AND esn.sub_niche_id = sn.id
WHERE ei.status IN ('pending', 'approved')
  AND esn.entity_id IS NULL;
