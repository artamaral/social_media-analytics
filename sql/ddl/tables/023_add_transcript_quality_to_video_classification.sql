-- Adiciona qualidade textual do transcript a instalacoes existentes.

ALTER TABLE public.video_classification_results
  ADD COLUMN IF NOT EXISTS transcript_quality_score NUMERIC(4, 3),
  ADD COLUMN IF NOT EXISTS transcript_quality_status TEXT NOT NULL
    DEFAULT 'not_evaluated',
  ADD COLUMN IF NOT EXISTS transcript_quality_issues TEXT[] NOT NULL
    DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN IF NOT EXISTS transcript_quality_impact TEXT NOT NULL
    DEFAULT 'none',
  ADD COLUMN IF NOT EXISTS needs_retranscription BOOLEAN NOT NULL
    DEFAULT false;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'video_classification_results_transcript_quality_score_check'
  ) THEN
    ALTER TABLE public.video_classification_results
      ADD CONSTRAINT video_classification_results_transcript_quality_score_check
      CHECK (
        transcript_quality_score IS NULL
        OR (
          transcript_quality_score >= 0
          AND transcript_quality_score <= 1
        )
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'video_classification_results_transcript_quality_status_check'
  ) THEN
    ALTER TABLE public.video_classification_results
      ADD CONSTRAINT video_classification_results_transcript_quality_status_check
      CHECK (
        transcript_quality_status IN (
          'not_evaluated',
          'usable',
          'partially_usable',
          'poor',
          'empty'
        )
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'video_classification_results_transcript_quality_impact_check'
  ) THEN
    ALTER TABLE public.video_classification_results
      ADD CONSTRAINT video_classification_results_transcript_quality_impact_check
      CHECK (transcript_quality_impact IN ('none', 'low', 'medium', 'high'));
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'video_classification_results_transcript_quality_issues_check'
  ) THEN
    ALTER TABLE public.video_classification_results
      ADD CONSTRAINT video_classification_results_transcript_quality_issues_check
      CHECK (
        transcript_quality_issues <@ ARRAY[
          'too_short',
          'truncated',
          'incoherent',
          'degraded_entities',
          'degraded_technical_terms',
          'excessive_noise'
        ]::TEXT[]
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'video_classification_results_transcript_quality_consistency_check'
  ) THEN
    ALTER TABLE public.video_classification_results
      ADD CONSTRAINT video_classification_results_transcript_quality_consistency_check
      CHECK (
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
      );
  END IF;
END
$$;

COMMENT ON COLUMN public.video_classification_results.transcript_quality_score IS
  'Nota GPT de qualidade textual do transcript recebido; nao mede o audio original.';

COMMENT ON COLUMN public.video_classification_results.transcript_quality_issues IS
  'Sinais controlados de degradacao textual identificados pelo classificador.';
