-- validate_entity_links.sql

-- Validar a distribuição atual de creators por entity.
-- Útil para revisar se o remapeamento ficou coerente após deduplicação.
SELECT
  e.id AS entity_id,
  e.name AS entity_name,
  e.normalized_name,
  COUNT(c.id) AS total_creators
FROM public.entities e
LEFT JOIN public.creators c
  ON c.entity_id = e.id
GROUP BY e.id, e.name, e.normalized_name
ORDER BY total_creators DESC, e.id;

-- Validar vínculos entre entities e sub_niches.
SELECT
  e.id AS entity_id,
  e.name AS entity_name,
  sn.id AS sub_niche_id,
  sn.name AS sub_niche_name
FROM public.entity_sub_niches esn
JOIN public.entities e
  ON e.id = esn.entity_id
JOIN public.sub_niches sn
  ON sn.id = esn.sub_niche_id
ORDER BY e.name, sn.name;

-- Validar se existe alguma entity sem sub_niche associado.
SELECT
  e.id,
  e.name,
  e.normalized_name
FROM public.entities e
LEFT JOIN public.entity_sub_niches esn
  ON esn.entity_id = e.id
WHERE esn.entity_id IS NULL
ORDER BY e.name;

-- Validar se existe algum registro pendente no intake ainda não publicado.
SELECT
  id,
  raw_name,
  normalized_name,
  sub_niche_name,
  status,
  created_at
FROM public.entity_intake
WHERE status IN ('pending', 'approved')
ORDER BY created_at DESC, id DESC;
