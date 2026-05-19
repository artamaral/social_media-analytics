-- 003_create_publish_entity_intake_function.sql

-- Criar função única para publicar registros da tabela entity_intake.
-- Esta função executa o fluxo completo:
-- 1) normaliza os nomes de entrada
-- 2) insere novas entities apenas quando ainda não existem
-- 3) insere vínculos em entity_sub_niches apenas quando ainda não existem
-- 4) marca os registros processados como published
CREATE OR REPLACE FUNCTION public.publish_entity_intake()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN

  -- Atualizar normalized_name da tabela de intake com base em raw_name.
  UPDATE public.entity_intake
  SET normalized_name = LOWER(TRIM(unaccent(raw_name)))
  WHERE normalized_name IS NULL
     OR normalized_name <> LOWER(TRIM(unaccent(raw_name)));

  -- Inserir novas entities apenas para registros pendentes/aprovados
  -- cujo normalized_name ainda não existe em public.entities
  -- e cujo sub_niche informado existe em public.sub_niches.
  INSERT INTO public.entities (name, niche, creator_type, normalized_name)
  SELECT
    ei.raw_name,
    ei.niche,
    ei.creator_type,
    ei.normalized_name
  FROM public.entity_intake ei
  LEFT JOIN public.entities e
    ON e.normalized_name = ei.normalized_name
  LEFT JOIN public.sub_niches sn
    ON LOWER(TRIM(unaccent(sn.name::text))) = LOWER(TRIM(unaccent(ei.sub_niche_name)))
  WHERE ei.status IN ('pending', 'approved')
    AND e.id IS NULL
    AND sn.id IS NOT NULL;

  -- Inserir vínculos em entity_sub_niches usando a entity já existente
  -- ou a entity recém inserida, evitando duplicidade pela PK composta.
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

  -- Marcar como published apenas os registros pendentes/aprovados
  -- cuja normalização foi preenchida.
  UPDATE public.entity_intake
  SET
    status = 'published',
    published_at = CURRENT_TIMESTAMP
  WHERE status IN ('pending', 'approved')
    AND normalized_name IS NOT NULL;

END;
$$;
