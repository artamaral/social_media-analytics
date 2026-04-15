-- publish_entity_intake_manual_run.sql

-- Executar manualmente a função de publicação após revisar os dados em entity_intake.
-- Este é o comando operacional principal do fluxo manual.
SELECT public.publish_entity_intake();
