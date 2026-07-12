# INDICE DE DOCUMENTACAO

Este arquivo e a porta de entrada para a documentacao em `docs/`.

O projeto esta organizado em 3 frentes principais:

1. Dados social media
2. Dados de fontes externas
3. Dashboard

Tambem existe documentacao transversal de operacao, validacao e gestao.

## Regra de manutencao deste indice

Todo item novo gerado em `docs/` deve ser incorporado a este indice.

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

- [01_BACKLOG.md](/C:/social_media-analytics/docs/project/01_BACKLOG.md)
- [02_ROADMAP.md](/C:/social_media-analytics/docs/project/02_ROADMAP.md)
- [05_DECISOES_TECNICAS.md](/C:/social_media-analytics/docs/project/05_DECISOES_TECNICAS.md)

### Operacao e status

- [04_PIPELINE_STATUS.md](/C:/social_media-analytics/docs/project/04_PIPELINE_STATUS.md)
- [07_QUEUE_VALIDATION_CHECKLIST.md](/C:/social_media-analytics/docs/social_media/07_QUEUE_VALIDATION_CHECKLIST.md)
- [08_QUEUE_CAPACITY_TEST.md](/C:/social_media-analytics/docs/social_media/08_QUEUE_CAPACITY_TEST.md)
- [09_QUEUE_SLICING_AND_RESCHEDULING.md](/C:/social_media-analytics/docs/social_media/09_QUEUE_SLICING_AND_RESCHEDULING.md)
- [10_QUEUE_CAPACITY_RESULTS_2026-05-08.md](/C:/social_media-analytics/docs/social_media/10_QUEUE_CAPACITY_RESULTS_2026-05-08.md)
- [11_QUEUE_FIFO_VALIDATION_2026-05-08.md](/C:/social_media-analytics/docs/social_media/11_QUEUE_FIFO_VALIDATION_2026-05-08.md)

### Score hibrido e priorizacao

- [12_HYBRID_PRIORITY_SCORE_SPEC.md](/C:/social_media-analytics/docs/social_media/12_HYBRID_PRIORITY_SCORE_SPEC.md)
- [13_HYBRID_SCORE_EVALUATION_STRATEGY.md](/C:/social_media-analytics/docs/social_media/13_HYBRID_SCORE_EVALUATION_STRATEGY.md)
- [14_HYBRID_SCORE_VALIDATION_PLAN.md](/C:/social_media-analytics/docs/social_media/14_HYBRID_SCORE_VALIDATION_PLAN.md)
- [24_PHASE2_INITIAL_DATA_BASELINE_2026-05-17.md](/C:/social_media-analytics/docs/social_media/24_PHASE2_INITIAL_DATA_BASELINE_2026-05-17.md)
- [26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md](/C:/social_media-analytics/docs/social_media/26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md)

### Historico minimo, bootstrap e backfill

- [15_LOW_HISTORY_BOOTSTRAP_AND_BACKFILL_SPEC.md](/C:/social_media-analytics/docs/social_media/15_LOW_HISTORY_BOOTSTRAP_AND_BACKFILL_SPEC.md)
- [17_LEGACY_LOW_OFFLINE_BACKFILL_SPEC.md](/C:/social_media-analytics/docs/social_media/17_LEGACY_LOW_OFFLINE_BACKFILL_SPEC.md)
- [18_LEGACY_LOW_OFFLINE_BACKFILL_PHASE1_SPEC.md](/C:/social_media-analytics/docs/social_media/18_LEGACY_LOW_OFFLINE_BACKFILL_PHASE1_SPEC.md)
- [19_LEGACY_LOW_OFFLINE_BACKFILL_SCRIPT_DESIGN.md](/C:/social_media-analytics/docs/social_media/19_LEGACY_LOW_OFFLINE_BACKFILL_SCRIPT_DESIGN.md)
- [20_LEGACY_LOW_BACKFILL_RESULTS_2026-05-14.md](/C:/social_media-analytics/docs/social_media/20_LEGACY_LOW_BACKFILL_RESULTS_2026-05-14.md)
- [21_WINDOWS_SCHEDULER_BACKFILL_SETUP.md](/C:/social_media-analytics/docs/social_media/21_WINDOWS_SCHEDULER_BACKFILL_SETUP.md)
- [25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md](/C:/social_media-analytics/docs/social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md)

### Intake e organizacao de entidades

- [entity_intake_process.md](/C:/social_media-analytics/docs/data_model/entity_intake_process.md)
- [table_organization_v2.md](/C:/social_media-analytics/docs/data_model/table_organization_v2.md)

## 2. Dados de fontes externas

### Escopo e plano geral

- [22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md](/C:/social_media-analytics/docs/external_data/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md)
- [00_OFFLINE_OPERATIONS_CALENDAR.md](/C:/social_media-analytics/docs/external_data/00_OFFLINE_OPERATIONS_CALENDAR.md)

### Fenabrave

- [23_FENABRAVE_PHASE1_INGESTION_SPEC.md](/C:/social_media-analytics/docs/external_data/23_FENABRAVE_PHASE1_INGESTION_SPEC.md)
- [24_FENABRAVE_PHASE2_EXTENDED_DATA_PLAN.md](/C:/social_media-analytics/docs/external_data/24_FENABRAVE_PHASE2_EXTENDED_DATA_PLAN.md)
- [25_FENABRAVE_PHASE2_ITEM1_RANKING_EMPLACAMENTOS_MES_PLAN.md](/C:/social_media-analytics/docs/external_data/25_FENABRAVE_PHASE2_ITEM1_RANKING_EMPLACAMENTOS_MES_PLAN.md)
- [26_FENABRAVE_PHASE2_ITEMS13_18_TECHNICAL_PLAN.md](/C:/social_media-analytics/docs/external_data/26_FENABRAVE_PHASE2_ITEMS13_18_TECHNICAL_PLAN.md)

### Carros na Web

- [27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md](/C:/social_media-analytics/docs/external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md)

## 3. Dashboard

### Estrategia e implementacao

- [16_ONLINE_DASHBOARD_SUPABASE_SPEC.md](/C:/social_media-analytics/docs/dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md)
- [29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md](/C:/social_media-analytics/docs/dashboard/29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md)
- [31_DEAD_POST_REVIEW_STREAMLIT_SPEC.md](/C:/social_media-analytics/docs/dashboard/31_DEAD_POST_REVIEW_STREAMLIT_SPEC.md)

## 4. Documentacao transversal

### Qualidade, operacao e padroes

- [03_DATA_QUALITY_CHECKS.md](/C:/social_media-analytics/docs/data_model/03_DATA_QUALITY_CHECKS.md)
- [06_COMMIT_PATTERN.md](/C:/social_media-analytics/docs/project/06_COMMIT_PATTERN.md)
- [28_REPOSITORY_STRUCTURE_GUIDELINES.md](/C:/social_media-analytics/docs/project/28_REPOSITORY_STRUCTURE_GUIDELINES.md)
- [README_GESTAO_PROJETO.md](/C:/social_media-analytics/docs/project/README_GESTAO_PROJETO.md)

## Ordem sugerida de leitura

Para entender o projeto rapidamente:

1. [README.md](/C:/social_media-analytics/README.md)
2. [02_ROADMAP.md](/C:/social_media-analytics/docs/project/02_ROADMAP.md)
3. [04_PIPELINE_STATUS.md](/C:/social_media-analytics/docs/project/04_PIPELINE_STATUS.md)
4. [05_DECISOES_TECNICAS.md](/C:/social_media-analytics/docs/project/05_DECISOES_TECNICAS.md)
5. [16_ONLINE_DASHBOARD_SUPABASE_SPEC.md](/C:/social_media-analytics/docs/dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md)
6. [22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md](/C:/social_media-analytics/docs/external_data/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md)

## Observacao final

Este indice deve evoluir junto com o projeto.

Sempre que um novo documento entrar em `docs/`, atualize este arquivo na
mesma mudanca para manter a navegacao consistente.

