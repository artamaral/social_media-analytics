-- 001_create_entity_intake.sql

-- Criar tabela de entrada manual para cadastro controlado de entities e sub_niches.
-- Esta tabela será usada no Supabase UI como ponto único de entrada.
CREATE TABLE IF NOT EXISTS public.entity_intake (
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
