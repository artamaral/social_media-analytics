-- 004_create_unique_index_entities_normalized_name.sql

-- Criar índice único em normalized_name para impedir que duas entities
-- com a mesma forma normalizada sejam inseridas no futuro.
CREATE UNIQUE INDEX IF NOT EXISTS unique_entities_normalized_name
ON public.entities (normalized_name);
