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
- [51_CARROSNAWEB_CATALOGO_SUPABASE_HOMOGENEIZACAO_VEICULOS.md](/C:/social_media-analytics/docs/external_data/51_CARROSNAWEB_CATALOGO_SUPABASE_HOMOGENEIZACAO_VEICULOS.md)

### Enrichment e classificacao de videos

- [29_SPEC-INGESTAO-VALIDACAO-NICHOS-SUBNICHOS.md](/C:/social_media-analytics/docs/external_data/29_SPEC-INGESTAO-VALIDACAO-NICHOS-SUBNICHOS.md)
- [30_SPEC_PREMISSAS_OPENAI_CLASSIFICACAO_TRANSCRICAO.md](/C:/social_media-analytics/docs/external_data/30_SPEC_PREMISSAS_OPENAI_CLASSIFICACAO_TRANSCRICAO.md)
- [31_TAXONOMIA_PILOTO_VIDEO_V1.md](/C:/social_media-analytics/docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.md)
- [32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.md](/C:/social_media-analytics/docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.md)
- [33_AMOSTRA_PILOTO_10_VIDEOS_V1.md](/C:/social_media-analytics/docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.md)
- [34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.md](/C:/social_media-analytics/docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.md)
- [35_ACHADOS_POS_TESTE_TAXONOMIA_CLASSIFICACAO_V1.md](/C:/social_media-analytics/docs/external_data/35_ACHADOS_POS_TESTE_TAXONOMIA_CLASSIFICACAO_V1.md)
- [36_RESULTADO_BASELINE_HUMANO_E_CONTRATO_AVALIACAO_GPT_V1.md](/C:/social_media-analytics/docs/external_data/36_RESULTADO_BASELINE_HUMANO_E_CONTRATO_AVALIACAO_GPT_V1.md)
- [37_ANALISE_GPT55_EXPLORATORIA_TAXONOMIA_R1.md](/C:/social_media-analytics/docs/external_data/37_ANALISE_GPT55_EXPLORATORIA_TAXONOMIA_R1.md)
- [38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.md](/C:/social_media-analytics/docs/external_data/38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.md)
- [39_COMPARACAO_HUMANO_GPT55_90S_R1.md](/C:/social_media-analytics/docs/external_data/39_COMPARACAO_HUMANO_GPT55_90S_R1.md)
- [40_TAXONOMIA_VIDEO_V2_GUIA_CLASSIFICACAO.md](/C:/social_media-analytics/docs/external_data/40_TAXONOMIA_VIDEO_V2_GUIA_CLASSIFICACAO.md)
- [41_COMPARACAO_GPT55_V1_V2_R1.md](/C:/social_media-analytics/docs/external_data/41_COMPARACAO_GPT55_V1_V2_R1.md)
- [42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv](/C:/social_media-analytics/docs/external_data/42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv)
- [43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv](/C:/social_media-analytics/docs/external_data/43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv)
- [44_ENRIQUECIMENTO_TAXONOMIA_V2_TITULOS_E_PROXIMA_TRANSCRICAO.md](/C:/social_media-analytics/docs/external_data/44_ENRIQUECIMENTO_TAXONOMIA_V2_TITULOS_E_PROXIMA_TRANSCRICAO.md)
- [45_TRANSCRICOES_90S_ENRIQUECIMENTO_TAXONOMIA_V2_R1.md](/C:/social_media-analytics/docs/external_data/45_TRANSCRICOES_90S_ENRIQUECIMENTO_TAXONOMIA_V2_R1.md)
- [46_ANALISE_TRANSCRICOES_ENRIQUECIMENTO_TAXONOMIA_V2_R1.md](/C:/social_media-analytics/docs/external_data/46_ANALISE_TRANSCRICOES_ENRIQUECIMENTO_TAXONOMIA_V2_R1.md)
- [47_ANALISE_FONTE_MOURA_MANUTENCAO_PREVENTIVA_TAXONOMIA_V2.md](/C:/social_media-analytics/docs/external_data/47_ANALISE_FONTE_MOURA_MANUTENCAO_PREVENTIVA_TAXONOMIA_V2.md)
- [48_RESULTADO_GPT55_TAXONOMIA_V2_ENRIQUECIDA_20VIDEOS_R1.csv](/C:/social_media-analytics/docs/external_data/48_RESULTADO_GPT55_TAXONOMIA_V2_ENRIQUECIDA_20VIDEOS_R1.csv)
- [49_COMPARACAO_TAXONOMIA_V2_ENRIQUECIDA_20VIDEOS_R1.md](/C:/social_media-analytics/docs/external_data/49_COMPARACAO_TAXONOMIA_V2_ENRIQUECIDA_20VIDEOS_R1.md)
- [50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.md](/C:/social_media-analytics/docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.md)
- [52_AMOSTRA_REVIEW_CARROS_NOVOS_USADOS_10_VIDEOS_R1.csv](/C:/social_media-analytics/docs/external_data/52_AMOSTRA_REVIEW_CARROS_NOVOS_USADOS_10_VIDEOS_R1.csv)
- [53_TRANSCRICOES_90S_REVIEW_CARROS_NOVOS_USADOS_R1.csv](/C:/social_media-analytics/docs/external_data/53_TRANSCRICOES_90S_REVIEW_CARROS_NOVOS_USADOS_R1.csv)
- [54_CLASSIFICACAO_REVIEW_NOVOS_USADOS_DESCRICAO_90S_R1.md](/C:/social_media-analytics/docs/external_data/54_CLASSIFICACAO_REVIEW_NOVOS_USADOS_DESCRICAO_90S_R1.md)
- [54_CLASSIFICACAO_REVIEW_NOVOS_USADOS_DESCRICAO_90S_R1.csv](/C:/social_media-analytics/docs/external_data/54_CLASSIFICACAO_REVIEW_NOVOS_USADOS_DESCRICAO_90S_R1.csv)
- [55_AMOSTRA_ALEATORIA_TAXONOMIA_V2_10_VIDEOS_R1.csv](/C:/social_media-analytics/docs/external_data/55_AMOSTRA_ALEATORIA_TAXONOMIA_V2_10_VIDEOS_R1.csv)
- [56_TRANSCRICOES_90S_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv](/C:/social_media-analytics/docs/external_data/56_TRANSCRICOES_90S_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv)
- [57_CLASSIFICACAO_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.md](/C:/social_media-analytics/docs/external_data/57_CLASSIFICACAO_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.md)
- [57_CLASSIFICACAO_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv](/C:/social_media-analytics/docs/external_data/57_CLASSIFICACAO_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv)
- [50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.csv](/C:/social_media-analytics/docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.csv)

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

