-- deduplicate_entities.sql

-- Criar tabela de mapeamento de entities duplicadas para entities canônicas.
-- A regra atual escolhe como canônica a entity com menor id para cada normalized_name.

CREATE TABLE IF NOT EXISTS public.entity_mapping AS
WITH canon AS (
  SELECT
    normalized_name,
    MIN(id) AS canonical_id
  FROM public.entities
  GROUP BY normalized_name
)
SELECT
  e.id AS old_id,
  c.canonical_id
FROM public.entities e
JOIN canon c
  ON e.normalized_name = c.normalized_name
WHERE e.id <> c.canonical_id;

-- Consultar o mapeamento detalhado para revisão manual.
-- Esta query mostra nome antigo, nome canônico e normalized_name correspondente.
SELECT
  m.old_id,
  e_old.name AS old_name,
  m.canonical_id,
  e_canon.name AS canonical_name,
  e_old.normalized_name
FROM public.entity_mapping m
JOIN public.entities e_old
  ON m.old_id = e_old.id
JOIN public.entities e_canon
  ON m.canonical_id = e_canon.id
ORDER BY m.canonical_id, m.old_id;

-- Consultar visão agrupada de duplicados para auditoria.
-- Esta query ajuda a entender clusters de nomes equivalentes.
SELECT
  e_canon.id AS canonical_id,
  e_canon.name AS canonical_name,
  e_canon.normalized_name,
  COUNT(e_old.id) AS total_duplicates,
  ARRAY_AGG(e_old.name) AS all_variations,
  ARRAY_AGG(e_old.id) AS all_ids
FROM public.entity_mapping m
JOIN public.entities e_old
  ON m.old_id = e_old.id
JOIN public.entities e_canon
  ON m.canonical_id = e_canon.id
GROUP BY e_canon.id, e_canon.name, e_canon.normalized_name
ORDER BY total_duplicates DESC;

-- Remover conflitos prévios em entity_sub_niches antes de atualizar entity_id.
-- Isso evita violação da PK composta (entity_id, sub_niche_id).
DELETE FROM public.entity_sub_niches
WHERE (entity_id, sub_niche_id) IN (
  SELECT
    m.old_id,
    esn.sub_niche_id
  FROM public.entity_sub_niches esn
  JOIN public.entity_mapping m
    ON esn.entity_id = m.old_id
  JOIN public.entity_sub_niches esn2
    ON esn2.entity_id = m.canonical_id
   AND esn2.sub_niche_id = esn.sub_niche_id
);

-- Atualizar creators para apontarem para a entity canônica.
UPDATE public.creators c
SET entity_id = m.canonical_id
FROM public.entity_mapping m
WHERE c.entity_id = m.old_id;

-- Atualizar entity_sub_niches para apontar para a entity canônica.
UPDATE public.entity_sub_niches esn
SET entity_id = m.canonical_id
FROM public.entity_mapping m
WHERE esn.entity_id = m.old_id;

-- Excluir entities duplicadas após atualização dos vínculos.
DELETE FROM public.entities
WHERE id IN (
  SELECT old_id
  FROM public.entity_mapping
);

-- Validar que não restaram duplicidades por normalized_name.
SELECT
  normalized_name,
  COUNT(*) AS total
FROM public.entities
GROUP BY normalized_name
HAVING COUNT(*) > 1
ORDER BY total DESC, normalized_name;
