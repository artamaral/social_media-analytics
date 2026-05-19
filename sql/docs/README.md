# INDICE DE DOCUMENTACAO

Este arquivo e a porta de entrada para a documentacao em `sql/docs`.

O projeto esta organizado em 3 frentes principais:

1. Dados social media
2. Dados de fontes externas
3. Dashboard

Tambem existe documentacao transversal de operacao, validacao e gestao.

## Regra de manutencao deste indice

Todo item novo gerado em `sql/docs` deve ser incorporado a este indice.

Isso inclui:

- novos planos
- novas especificacoes
- novos resultados de validacao
- novos runbooks operacionais
- novos baselines
- novos documentos de decisao

Se um documento novo for criado e nao for listado aqui, a documentacao deve ser
considerada incompleta.

## 1. Dados social media

### Planejamento e direcionamento

- [01_BACKLOG.md](/C:/social_media-analytics/sql/docs/01_BACKLOG.md)
- [02_ROADMAP.md](/C:/social_media-analytics/sql/docs/02_ROADMAP.md)
- [05_DECISOES_TECNICAS.md](/C:/social_media-analytics/sql/docs/05_DECISOES_TECNICAS.md)

### Operacao e status

- [04_PIPELINE_STATUS.md](/C:/social_media-analytics/sql/docs/04_PIPELINE_STATUS.md)
- [07_QUEUE_VALIDATION_CHECKLIST.md](/C:/social_media-analytics/sql/docs/07_QUEUE_VALIDATION_CHECKLIST.md)
- [08_QUEUE_CAPACITY_TEST.md](/C:/social_media-analytics/sql/docs/08_QUEUE_CAPACITY_TEST.md)
- [09_QUEUE_SLICING_AND_RESCHEDULING.md](/C:/social_media-analytics/sql/docs/09_QUEUE_SLICING_AND_RESCHEDULING.md)
- [10_QUEUE_CAPACITY_RESULTS_2026-05-08.md](/C:/social_media-analytics/sql/docs/10_QUEUE_CAPACITY_RESULTS_2026-05-08.md)
- [11_QUEUE_FIFO_VALIDATION_2026-05-08.md](/C:/social_media-analytics/sql/docs/11_QUEUE_FIFO_VALIDATION_2026-05-08.md)

### Score hibrido e priorizacao

- [12_HYBRID_PRIORITY_SCORE_SPEC.md](/C:/social_media-analytics/sql/docs/12_HYBRID_PRIORITY_SCORE_SPEC.md)
- [13_HYBRID_SCORE_EVALUATION_STRATEGY.md](/C:/social_media-analytics/sql/docs/13_HYBRID_SCORE_EVALUATION_STRATEGY.md)
- [14_HYBRID_SCORE_VALIDATION_PLAN.md](/C:/social_media-analytics/sql/docs/14_HYBRID_SCORE_VALIDATION_PLAN.md)
- [24_PHASE2_INITIAL_DATA_BASELINE_2026-05-17.md](/C:/social_media-analytics/sql/docs/24_PHASE2_INITIAL_DATA_BASELINE_2026-05-17.md)
- [26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md](/C:/social_media-analytics/sql/docs/26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md)

### Historico minimo, bootstrap e backfill

- [15_LOW_HISTORY_BOOTSTRAP_AND_BACKFILL_SPEC.md](/C:/social_media-analytics/sql/docs/15_LOW_HISTORY_BOOTSTRAP_AND_BACKFILL_SPEC.md)
- [17_LEGACY_LOW_OFFLINE_BACKFILL_SPEC.md](/C:/social_media-analytics/sql/docs/17_LEGACY_LOW_OFFLINE_BACKFILL_SPEC.md)
- [18_LEGACY_LOW_OFFLINE_BACKFILL_PHASE1_SPEC.md](/C:/social_media-analytics/sql/docs/18_LEGACY_LOW_OFFLINE_BACKFILL_PHASE1_SPEC.md)
- [19_LEGACY_LOW_OFFLINE_BACKFILL_SCRIPT_DESIGN.md](/C:/social_media-analytics/sql/docs/19_LEGACY_LOW_OFFLINE_BACKFILL_SCRIPT_DESIGN.md)
- [20_LEGACY_LOW_BACKFILL_RESULTS_2026-05-14.md](/C:/social_media-analytics/sql/docs/20_LEGACY_LOW_BACKFILL_RESULTS_2026-05-14.md)
- [21_WINDOWS_SCHEDULER_BACKFILL_SETUP.md](/C:/social_media-analytics/sql/docs/21_WINDOWS_SCHEDULER_BACKFILL_SETUP.md)
- [25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md](/C:/social_media-analytics/sql/docs/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md)

### Intake e organizacao de entidades

- [entity_intake_process.md](/C:/social_media-analytics/sql/docs/entity_intake_process.md)
- [table_organization_v2.md](/C:/social_media-analytics/sql/docs/table_organization_v2.md)

## 2. Dados de fontes externas

### Escopo e plano geral

- [22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md](/C:/social_media-analytics/sql/docs/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md)
- [00_OFFLINE_OPERATIONS_CALENDAR.md](/C:/social_media-analytics/sql/docs/00_OFFLINE_OPERATIONS_CALENDAR.md)

### Fenabrave

- [23_FENABRAVE_PHASE1_INGESTION_SPEC.md](/C:/social_media-analytics/sql/docs/23_FENABRAVE_PHASE1_INGESTION_SPEC.md)

### Carros na Web

- [27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md](/C:/social_media-analytics/sql/docs/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md)

## 3. Dashboard

### Estrategia e implementacao

- [16_ONLINE_DASHBOARD_SUPABASE_SPEC.md](/C:/social_media-analytics/sql/docs/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md)

## 4. Documentacao transversal

### Qualidade, operacao e padroes

- [03_DATA_QUALITY_CHECKS.md](/C:/social_media-analytics/sql/docs/03_DATA_QUALITY_CHECKS.md)
- [06_COMMIT_PATTERN.md](/C:/social_media-analytics/sql/docs/06_COMMIT_PATTERN.md)
- [28_REPOSITORY_STRUCTURE_GUIDELINES.md](/C:/social_media-analytics/sql/docs/28_REPOSITORY_STRUCTURE_GUIDELINES.md)
- [README_GESTAO_PROJETO.md](/C:/social_media-analytics/sql/docs/README_GESTAO_PROJETO.md)

## Ordem sugerida de leitura

Para entender o projeto rapidamente:

1. [README.md](/C:/social_media-analytics/README.md)
2. [02_ROADMAP.md](/C:/social_media-analytics/sql/docs/02_ROADMAP.md)
3. [04_PIPELINE_STATUS.md](/C:/social_media-analytics/sql/docs/04_PIPELINE_STATUS.md)
4. [05_DECISOES_TECNICAS.md](/C:/social_media-analytics/sql/docs/05_DECISOES_TECNICAS.md)
5. [16_ONLINE_DASHBOARD_SUPABASE_SPEC.md](/C:/social_media-analytics/sql/docs/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md)
6. [22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md](/C:/social_media-analytics/sql/docs/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md)

## Observacao final

Este indice deve evoluir junto com o projeto.

Sempre que um novo documento entrar em `sql/docs`, atualize este arquivo na
mesma mudanca para manter a navegacao consistente.
