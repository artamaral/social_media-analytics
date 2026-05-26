-- check_creator_intake_dependencies.sql

-- Preflight para a view Cadastro > Criadores no Streamlit.
-- Rode antes de aplicar as RPCs quando o Supabase acusar objeto inexistente.

SELECT
  'public.entities' AS object_name,
  to_regclass('public.entities') IS NOT NULL AS exists
UNION ALL
SELECT
  'public.sub_niches' AS object_name,
  to_regclass('public.sub_niches') IS NOT NULL AS exists
UNION ALL
SELECT
  'public.entity_sub_niches' AS object_name,
  to_regclass('public.entity_sub_niches') IS NOT NULL AS exists
UNION ALL
SELECT
  'public.creators' AS object_name,
  to_regclass('public.creators') IS NOT NULL AS exists
UNION ALL
SELECT
  'public.entity_intake' AS object_name,
  to_regclass('public.entity_intake') IS NOT NULL AS exists
UNION ALL
SELECT
  'public.v_entity_intake_review' AS object_name,
  to_regclass('public.v_entity_intake_review') IS NOT NULL AS exists;
