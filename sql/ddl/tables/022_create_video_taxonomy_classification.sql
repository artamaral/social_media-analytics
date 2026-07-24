-- 022_create_video_taxonomy_classification.sql

-- Camada operacional para Taxonomia Video V2 e classificacoes GPT.
-- Esta DDL cria apenas o contrato de banco. Ela nao implementa ingestao,
-- coleta, worker, dashboard ou execucao em cloud.

CREATE TABLE IF NOT EXISTS public.video_taxonomy_versions (
  id BIGSERIAL PRIMARY KEY,
  taxonomy_version TEXT NOT NULL UNIQUE,
  taxonomy_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  source_topic_paths_file TEXT,
  source_topic_paths_sha256 TEXT,
  source_compatibility_file TEXT,
  source_compatibility_sha256 TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  activated_at TIMESTAMPTZ,

  CONSTRAINT video_taxonomy_versions_status_check CHECK (
    status IN ('draft', 'active', 'deprecated')
  )
);

COMMENT ON TABLE public.video_taxonomy_versions IS
  'Versoes operacionais da taxonomia de classificacao de videos automotivos.';

COMMENT ON COLUMN public.video_taxonomy_versions.taxonomy_version IS
  'Codigo estavel da versao, por exemplo taxonomia_video_v2.';


CREATE TABLE IF NOT EXISTS public.video_taxonomy_topic_paths (
  id BIGSERIAL PRIMARY KEY,
  taxonomy_version_id BIGINT NOT NULL
    REFERENCES public.video_taxonomy_versions(id) ON DELETE CASCADE,
  topic_path_code TEXT NOT NULL,
  label_pt TEXT NOT NULL,
  parent_code TEXT,
  level INTEGER NOT NULL,
  automotive_domain TEXT NOT NULL,
  default_activity_type TEXT NOT NULL,
  description TEXT,
  example_signals TEXT,
  allowed_in_pilot BOOLEAN NOT NULL DEFAULT false,
  requires_technical_context BOOLEAN NOT NULL DEFAULT false,
  allows_secondary_topic BOOLEAN NOT NULL DEFAULT false,
  is_active BOOLEAN NOT NULL DEFAULT true,
  source_row JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT video_taxonomy_topic_paths_unique UNIQUE (
    taxonomy_version_id,
    topic_path_code
  ),
  CONSTRAINT video_taxonomy_topic_paths_level_check CHECK (level >= 1),
  CONSTRAINT video_taxonomy_topic_paths_code_check CHECK (
    topic_path_code = lower(topic_path_code)
    AND topic_path_code !~ '[^a-z0-9_]'
    AND topic_path_code !~ '___'
  ),
  CONSTRAINT video_taxonomy_topic_paths_no_bare_motor_cambio_check CHECK (
    topic_path_code NOT IN ('motor', 'cambio')
  )
);

CREATE INDEX IF NOT EXISTS video_taxonomy_topic_paths_version_idx
  ON public.video_taxonomy_topic_paths (taxonomy_version_id, is_active);

CREATE INDEX IF NOT EXISTS video_taxonomy_topic_paths_parent_idx
  ON public.video_taxonomy_topic_paths (taxonomy_version_id, parent_code);

COMMENT ON TABLE public.video_taxonomy_topic_paths IS
  'Arvore navegavel topic_path da Taxonomia Video V2.';

COMMENT ON COLUMN public.video_taxonomy_topic_paths.topic_path_code IS
  'Codigo hierarquico em snake_case usando __ como separador tecnico.';


CREATE TABLE IF NOT EXISTS public.video_taxonomy_technical_compatibility (
  id BIGSERIAL PRIMARY KEY,
  taxonomy_version_id BIGINT NOT NULL
    REFERENCES public.video_taxonomy_versions(id) ON DELETE CASCADE,
  compatibility_id TEXT NOT NULL,
  topic_path_code TEXT NOT NULL,
  automotive_system TEXT,
  component TEXT,
  problem TEXT,
  compatibility_status TEXT NOT NULL,
  required_evidence TEXT,
  example_signals TEXT,
  validation_rule TEXT,
  allowed_in_pilot BOOLEAN NOT NULL DEFAULT false,
  is_active BOOLEAN NOT NULL DEFAULT true,
  source_row JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT video_taxonomy_technical_compatibility_unique UNIQUE (
    taxonomy_version_id,
    compatibility_id
  ),
  CONSTRAINT video_taxonomy_technical_compatibility_topic_fk FOREIGN KEY (
    taxonomy_version_id,
    topic_path_code
  ) REFERENCES public.video_taxonomy_topic_paths (
    taxonomy_version_id,
    topic_path_code
  ),
  CONSTRAINT video_taxonomy_technical_compatibility_status_check CHECK (
    compatibility_status IN (
      'allowed',
      'allowed_with_evidence',
      'not_applicable',
      'needs_review'
    )
  )
);

CREATE INDEX IF NOT EXISTS video_taxonomy_technical_compatibility_lookup_idx
  ON public.video_taxonomy_technical_compatibility (
    taxonomy_version_id,
    topic_path_code,
    automotive_system,
    component,
    problem
  );

COMMENT ON TABLE public.video_taxonomy_technical_compatibility IS
  'Matriz tecnica que limita combinacoes coerentes entre topic_path, sistema, componente e problema.';


CREATE TABLE IF NOT EXISTS public.video_taxonomy_terms (
  id BIGSERIAL PRIMARY KEY,
  taxonomy_version_id BIGINT NOT NULL
    REFERENCES public.video_taxonomy_versions(id) ON DELETE CASCADE,
  dimension TEXT NOT NULL,
  term_code TEXT NOT NULL,
  label_pt TEXT,
  description TEXT,
  source_reference TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT video_taxonomy_terms_unique UNIQUE (
    taxonomy_version_id,
    dimension,
    term_code
  ),
  CONSTRAINT video_taxonomy_terms_code_check CHECK (
    term_code = lower(term_code)
    AND term_code !~ '[^a-z0-9_]'
  )
);

CREATE INDEX IF NOT EXISTS video_taxonomy_terms_dimension_idx
  ON public.video_taxonomy_terms (taxonomy_version_id, dimension, is_active);

COMMENT ON TABLE public.video_taxonomy_terms IS
  'Termos controlados auxiliares usados pelo harness GPT, como content_type, audience_intent e context_role.';


CREATE TABLE IF NOT EXISTS public.video_classification_runs (
  id BIGSERIAL PRIMARY KEY,
  round_id TEXT NOT NULL,
  taxonomy_version_id BIGINT NOT NULL
    REFERENCES public.video_taxonomy_versions(id),
  classification_stage TEXT NOT NULL,
  model_used TEXT NOT NULL,
  prompt_contract_version TEXT NOT NULL,
  output_schema_version TEXT NOT NULL,
  input_source TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'planned',
  total_requested INTEGER,
  total_succeeded INTEGER,
  total_failed INTEGER,
  error_summary TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT video_classification_runs_stage_check CHECK (
    classification_stage IN ('title_metadata', 'transcript_90s')
  ),
  CONSTRAINT video_classification_runs_status_check CHECK (
    status IN ('planned', 'running', 'completed', 'failed', 'cancelled')
  ),
  CONSTRAINT video_classification_runs_counts_check CHECK (
    (total_requested IS NULL OR total_requested >= 0)
    AND (total_succeeded IS NULL OR total_succeeded >= 0)
    AND (total_failed IS NULL OR total_failed >= 0)
  )
);

CREATE INDEX IF NOT EXISTS video_classification_runs_lookup_idx
  ON public.video_classification_runs (
    taxonomy_version_id,
    classification_stage,
    status,
    created_at DESC
  );

COMMENT ON TABLE public.video_classification_runs IS
  'Execucoes de classificacao GPT por estagio e versao de taxonomia.';


CREATE TABLE IF NOT EXISTS public.video_classification_results (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL
    REFERENCES public.video_classification_runs(id) ON DELETE CASCADE,
  taxonomy_version_id BIGINT NOT NULL
    REFERENCES public.video_taxonomy_versions(id),
  post_id TEXT NOT NULL REFERENCES public.posts(post_id),
  evaluation_stage TEXT NOT NULL,
  input_evidence_level TEXT NOT NULL,
  automotive_domain TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  topic_path TEXT NOT NULL,
  topic_path_secondary TEXT,
  content_type TEXT,
  audience_intent TEXT,
  confidence_score NUMERIC(4, 3) NOT NULL,
  evidence_summary TEXT NOT NULL,
  taxonomy_gaps TEXT,
  validation_issues TEXT,
  needs_human_review BOOLEAN NOT NULL DEFAULT false,
  transcript_quality_score NUMERIC(4, 3),
  transcript_quality_status TEXT NOT NULL DEFAULT 'not_evaluated',
  transcript_quality_issues TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  transcript_quality_impact TEXT NOT NULL DEFAULT 'none',
  needs_retranscription BOOLEAN NOT NULL DEFAULT false,
  model_used TEXT NOT NULL,
  prompt_contract_version TEXT NOT NULL,
  output_schema_version TEXT NOT NULL,
  input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  raw_response JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT video_classification_results_unique UNIQUE (
    run_id,
    post_id,
    evaluation_stage
  ),
  CONSTRAINT video_classification_results_stage_check CHECK (
    evaluation_stage IN ('title_metadata', 'transcript_90s')
  ),
  CONSTRAINT video_classification_results_confidence_check CHECK (
    confidence_score >= 0
    AND confidence_score <= 1
  ),
  CONSTRAINT video_classification_results_transcript_quality_score_check CHECK (
    transcript_quality_score IS NULL
    OR (
      transcript_quality_score >= 0
      AND transcript_quality_score <= 1
    )
  ),
  CONSTRAINT video_classification_results_transcript_quality_status_check CHECK (
    transcript_quality_status IN (
      'not_evaluated',
      'usable',
      'partially_usable',
      'poor',
      'empty'
    )
  ),
  CONSTRAINT video_classification_results_transcript_quality_impact_check CHECK (
    transcript_quality_impact IN ('none', 'low', 'medium', 'high')
  ),
  CONSTRAINT video_classification_results_transcript_quality_issues_check CHECK (
    transcript_quality_issues <@ ARRAY[
      'too_short',
      'truncated',
      'incoherent',
      'degraded_entities',
      'degraded_technical_terms',
      'excessive_noise'
    ]::TEXT[]
  ),
  CONSTRAINT video_classification_results_transcript_quality_consistency_check CHECK (
    (
      transcript_quality_status NOT IN ('poor', 'empty')
      OR needs_retranscription
    )
    AND (
      transcript_quality_impact <> 'medium'
      OR (needs_human_review AND confidence_score <= 0.69)
    )
    AND (
      transcript_quality_impact <> 'high'
      OR (needs_human_review AND confidence_score <= 0.49)
    )
  ),
  CONSTRAINT video_classification_results_topic_fk FOREIGN KEY (
    taxonomy_version_id,
    topic_path
  ) REFERENCES public.video_taxonomy_topic_paths (
    taxonomy_version_id,
    topic_path_code
  ),
  CONSTRAINT video_classification_results_secondary_topic_fk FOREIGN KEY (
    taxonomy_version_id,
    topic_path_secondary
  ) REFERENCES public.video_taxonomy_topic_paths (
    taxonomy_version_id,
    topic_path_code
  )
);

CREATE INDEX IF NOT EXISTS video_classification_results_post_idx
  ON public.video_classification_results (post_id, evaluation_stage, created_at DESC);

CREATE INDEX IF NOT EXISTS video_classification_results_topic_idx
  ON public.video_classification_results (taxonomy_version_id, topic_path);

COMMENT ON TABLE public.video_classification_results IS
  'Resultado agregado da classificacao GPT por video e estagio.';


CREATE TABLE IF NOT EXISTS public.video_classification_technical_contexts (
  id BIGSERIAL PRIMARY KEY,
  classification_result_id BIGINT NOT NULL
    REFERENCES public.video_classification_results(id) ON DELETE CASCADE,
  taxonomy_version_id BIGINT NOT NULL
    REFERENCES public.video_taxonomy_versions(id),
  context_order INTEGER NOT NULL,
  topic_path TEXT NOT NULL,
  topic_path_secondary TEXT,
  automotive_system TEXT,
  component TEXT,
  problem TEXT,
  context_role TEXT NOT NULL,
  evidence_text TEXT NOT NULL,
  compatibility_status TEXT NOT NULL,
  validation_issue TEXT,
  needs_human_review BOOLEAN NOT NULL DEFAULT false,
  raw_context JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT video_classification_technical_contexts_unique UNIQUE (
    classification_result_id,
    context_order
  ),
  CONSTRAINT video_classification_technical_contexts_order_check CHECK (
    context_order >= 1
  ),
  CONSTRAINT video_classification_technical_contexts_role_check CHECK (
    context_role IN ('primary', 'secondary', 'supporting', 'incidental')
  ),
  CONSTRAINT video_classification_technical_contexts_status_check CHECK (
    compatibility_status IN (
      'allowed',
      'allowed_with_evidence',
      'not_applicable',
      'needs_review'
    )
  ),
  CONSTRAINT video_classification_technical_contexts_no_concat_check CHECK (
    COALESCE(automotive_system, '') NOT LIKE '%;%'
    AND COALESCE(component, '') NOT LIKE '%;%'
    AND COALESCE(problem, '') NOT LIKE '%;%'
  ),
  CONSTRAINT video_classification_technical_contexts_problem_check CHECK (
    problem IS NULL OR problem <> 'barulho'
  ),
  CONSTRAINT video_classification_technical_contexts_topic_fk FOREIGN KEY (
    taxonomy_version_id,
    topic_path
  ) REFERENCES public.video_taxonomy_topic_paths (
    taxonomy_version_id,
    topic_path_code
  ),
  CONSTRAINT video_classification_technical_contexts_secondary_topic_fk FOREIGN KEY (
    taxonomy_version_id,
    topic_path_secondary
  ) REFERENCES public.video_taxonomy_topic_paths (
    taxonomy_version_id,
    topic_path_code
  )
);

CREATE INDEX IF NOT EXISTS video_classification_technical_contexts_result_idx
  ON public.video_classification_technical_contexts (classification_result_id, context_order);

CREATE INDEX IF NOT EXISTS video_classification_technical_contexts_lookup_idx
  ON public.video_classification_technical_contexts (
    taxonomy_version_id,
    topic_path,
    automotive_system,
    component,
    problem
  );

COMMENT ON TABLE public.video_classification_technical_contexts IS
  'Lista repetivel technical_context[] produzida pelo classificador GPT.';


CREATE TABLE IF NOT EXISTS public.video_classification_vehicle_entities (
  id BIGSERIAL PRIMARY KEY,
  classification_result_id BIGINT NOT NULL
    REFERENCES public.video_classification_results(id) ON DELETE CASCADE,
  entity_order INTEGER NOT NULL,
  vehicle_brand_raw TEXT,
  vehicle_model_raw TEXT,
  vehicle_year INTEGER,
  vehicle_generation TEXT,
  evidence_text TEXT NOT NULL,
  entity_status TEXT NOT NULL,
  canonical_manufacturer_name TEXT,
  canonical_model_name TEXT,
  canonical_model_year INTEGER,
  catalog_row_id BIGINT,
  match_source TEXT,
  match_confidence NUMERIC(4, 3),
  validation_issue TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT video_classification_vehicle_entities_unique UNIQUE (
    classification_result_id,
    entity_order
  ),
  CONSTRAINT video_classification_vehicle_entities_order_check CHECK (
    entity_order >= 1
  ),
  CONSTRAINT video_classification_vehicle_entities_year_check CHECK (
    vehicle_year IS NULL OR vehicle_year BETWEEN 1900 AND 2100
  ),
  CONSTRAINT video_classification_vehicle_entities_canonical_year_check CHECK (
    canonical_model_year IS NULL OR canonical_model_year BETWEEN 1900 AND 2100
  ),
  CONSTRAINT video_classification_vehicle_entities_status_check CHECK (
    entity_status IN (
      'extracted',
      'matched',
      'not_found',
      'needs_review'
    )
  ),
  CONSTRAINT video_classification_vehicle_entities_match_confidence_check CHECK (
    match_confidence IS NULL
    OR (match_confidence >= 0 AND match_confidence <= 1)
  ),
  CONSTRAINT video_classification_vehicle_entities_has_raw_value_check CHECK (
    vehicle_brand_raw IS NOT NULL
    OR vehicle_model_raw IS NOT NULL
    OR vehicle_year IS NOT NULL
    OR vehicle_generation IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS video_classification_vehicle_entities_result_idx
  ON public.video_classification_vehicle_entities (classification_result_id, entity_order);

CREATE INDEX IF NOT EXISTS video_classification_vehicle_entities_raw_idx
  ON public.video_classification_vehicle_entities (vehicle_brand_raw, vehicle_model_raw, vehicle_year);

COMMENT ON TABLE public.video_classification_vehicle_entities IS
  'Entidades de veiculo extraidas pelo GPT e preparadas para homogeneizacao com catalogos externos.';
