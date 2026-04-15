-- review_entity_intake.sql

-- Consultar a view de revisão para inspecionar os registros da tabela entity_intake
-- antes da publicação. Use esta query no dia a dia para validar:
-- 1) se a entity já existe
-- 2) se o sub_niche existe
-- 3) se o registro está pronto para inserção
SELECT *
FROM public.v_entity_intake_review
ORDER BY created_at DESC, id DESC;
