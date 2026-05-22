# Social Media Analytics

Plataforma de inteligencia automotiva organizada em 3 frentes principais:

1. Dados social media
2. Dados de fontes externas
3. Dashboard

## Visao Geral

O projeto conecta dados de conteudo, mercado e produto para apoiar analises de creators, videos, marcas, modelos e movimentos do setor automotivo.

As tres frentes trabalham de forma complementar:

- dados social media mostram atencao, conteudo e performance
- dados de fontes externas mostram mercado, catalogo e contexto estrutural
- o dashboard organiza o consumo analitico desses dados

## Frente 1. Dados Social Media

Objetivo:

- coletar, atualizar e analisar dados de creators e posts nas plataformas sociais

Escopo atual:

- YouTube como plataforma ativa
- arquitetura preparada para expansao futura para outras plataformas

### Atividades principais

- discovery e ingestao inicial de posts por creator
- atualizacao recorrente de metricas dos posts ja coletados
- historico temporal de views, likes e comments
- priorizacao e rechecagem por fila
- qualidade de coleta e cobertura minima de historico
- intake e governanca de entities e creators

### Estruturas principais

- `entities`
- `creators`
- `posts`
- `post_metrics_history`
- `post_update_queue`
- `pipeline_state`
- `entity_intake`

### Scripts principais

- `scripts/cloud_run/youtube_main_scraper/main.py`
- `scripts/cloud_run/postMetrics/main.py`
- `scripts/offline_backfill/legacy_low_backfill_phase1.py`

### Fluxos internos desta frente

#### A. Discovery / carga inicial de posts

Responsabilidades:

- ler creators da tabela `creators`
- controlar progresso com cursor em `pipeline_state`
- buscar uploads de canais do YouTube
- classificar videos como `short` ou `long`
- fazer upsert dos posts na tabela `posts`

Arquivos principais:

- `scripts/cloud_run/youtube_main_scraper/main.py`
- `scripts/cloud_run/youtube_main_scraper/requirements.txt`

Arquivo de apoio:

- `scripts/pipedream/youtube_scraper.py.txt`

#### B. Atualizacao de metricas

Responsabilidades:

- buscar posts pendentes em `post_update_queue`
- consultar estatisticas atualizadas na API do YouTube
- registrar historico em `post_metrics_history`
- atualizar os campos correntes em `posts`
- manter a fila reagendada para proximas rodadas

Arquivos principais:

- `scripts/cloud_run/postMetrics/main.py`
- `scripts/cloud_run/postMetrics/requirements.txt`

Arquivo de apoio:

- `scripts/pipedream/social_media-analytics__youtube_scraper_postMetrics.txt`

#### C. Backfill e cobertura minima

Responsabilidades:

- reduzir passivos historicos de posts com baixa cobertura
- preservar qualidade minima de historico
- alimentar futuras analises de crescimento, velocity e acceleration

Arquivos principais:

- `scripts/offline_backfill/legacy_low_backfill_phase1.py`
- `scripts/offline_backfill/run_legacy_low_backfill_phase1.ps1`

#### D. Intake e governanca

Responsabilidades:

- receber entradas controladas de entities
- revisar consistencia e duplicidade
- publicar registros aprovados para as tabelas definitivas

Arquivos principais:

- `sql/ddl/tables/009_create_entity_intake.sql`
- `sql/ddl/views/001_create_v_entity_intake_review.sql`
- `sql/dml/review_entity_intake.sql`
- `sql/dml/publish_entity_intake_manual_run.sql`

## Frente 2. Dados de Fontes Externas

Objetivo:

- incorporar dados estruturados de mercado e catalogo automotivo para enriquecer analises e cruzamentos com social media

### Subfrente A. Fenabrave

Objetivo:

- ingestao de emplacamentos e leitura mensal de mercado

Atividades principais:

- captura de arquivo fonte
- extracao e validacao de dados mensais
- normalizacao por segmento, marca e modelo
- rastreabilidade por arquivo, periodo e execucao

Implementacao atual:

- `scripts/fenabrave_ingestion/ingest_fenabrave_phase1.py`
- `scripts/fenabrave_ingestion/README.md`

Documentos principais:

- `docs/external_data/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md`
- `docs/external_data/23_FENABRAVE_PHASE1_INGESTION_SPEC.md`

### Subfrente B. Carros na Web

Objetivo:

- formar base estruturada de catalogo automotivo, versoes e ficha tecnica

Atividades principais:

- discovery de fabricantes
- discovery de modelos
- discovery de fichas validas
- coleta de HTML bruto
- parsing de ficha tecnica
- geracao inicial em CSV antes de schema definitivo no Supabase

Estado atual:

- frente em fase de plano de ingestao

Documento principal:

- `docs/external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md`

### Subfrente C. SENATRAN / RENAVAM

Objetivo:

- adicionar camada governamental de frota registrada e validacao estrutural

Atividades previstas:

- avaliar os dados abertos disponiveis
- definir granularidade util
- separar claramente frota de venda e emplacamento
- modelar futura camada normalizada no Supabase

Estado atual:

- frente em fase de estudo e definicao de granularidade

Documento principal:

- `docs/external_data/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md`

### Regra geral desta frente

- Fenabrave sustenta leitura de emplacamento e mercado
- Carros na Web sustenta leitura tecnica de produto e catalogo
- SENATRAN / RENAVAM sustenta leitura de frota registrada e validacao governamental

## Frente 3. Dashboard

Objetivo:

- transformar os dados das frentes 1 e 2 em uma camada de consumo analitico online

Direcao atual:

- dashboard interno
- Streamlit como solucao atual
- Supabase como fonte sob demanda

### Atividades principais

- criacao de views analiticas no banco
- exibicao de indicadores de qualidade dos dados
- overview executivo
- ranking de creators
- crescimento semanal
- cruzamento entre conteudo, mercado e catalogo
- cadastro operacional guiado de criadores
- cadastro operacional guiado da rotina mensal Fenabrave
- consumo seguro sem expor credenciais sensiveis

### Views principais

- `v_dashboard_creator_summary`
- `v_dashboard_post_growth_7d`
- `v_dashboard_data_quality_status`

### Documento principal

- `docs/dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md`

### Estado atual do app Streamlit

- tema visual inicial aplicado com sidebar escura, cards contrastados e acento coral
- pagina de Data Quality implementada com KPIs e monitoramento operacional
- mockup operacional de `Cadastro de Criadores` implementado no app
- mockup operacional de `Cadastro Fenabrave` implementado no app
- integracao SQL dessas duas views ainda pendente

## Relacao Entre as Frentes

- a frente de dados social media mostra comportamento de conteudo e audiencia
- a frente de fontes externas adiciona mercado, emplacamento, frota e ficha tecnica
- a frente de dashboard reune tudo em visualizacao analitica e consulta operacional

## Estrutura do Repositorio

```text
.
├── README.md
├── docs
│   ├── dashboard
│   ├── data_model
│   ├── external_data
│   ├── project
│   └── social_media
├── scripts
│   ├── cloud_run
│   │   ├── postMetrics
│   │   │   ├── main.py
│   │   │   └── requirements.txt
│   │   └── youtube_main_scraper
│   ├── fenabrave_ingestion
│   ├── offline_backfill
│   ├── pipedream
│   │   ├── social_media-analytics__youtube_scraper_postMetrics.txt
│   │   └── youtube_scraper.py.txt
│   ├── postMetrics
│   └── youtube_main_scraper
│       ├── main.py
│       └── requirements.txt
└── sql
    ├── ddl
    │   ├── functions
    │   ├── indexes
    │   ├── schema
    │   ├── tables
    │   ├── triggers
    │   └── views
    ├── dml
    ├── maintenance
    └── migrations
```

### Leitura por frente

#### Social media

- `scripts/cloud_run/youtube_main_scraper/`
- `scripts/cloud_run/postMetrics/`
- `scripts/offline_backfill/`

#### Fontes externas

- `scripts/fenabrave_ingestion/`
- futura `scripts/carrosnaweb_ingestion/`

#### Dashboard

- views SQL em `sql/ddl/views/`
- docs analiticas em `docs/dashboard/`
- futura app Streamlit

## Estrutura SQL

O diretorio `sql/` esta organizado por finalidade.

### `sql/ddl`

Definicao estrutural do banco:

- `functions/`: funcoes SQL reutilizaveis e auxiliares
- `tables/`: criacao das tabelas principais
- `views/`: views operacionais, analiticas e de revisao
- `triggers/`: funcoes e triggers de sincronizacao e queue
- `indexes/`: indices e funcoes auxiliares
- `schema/`: snapshot consolidado do schema

### `sql/dml`

Scripts operacionais de leitura, revisao e publicacao.

### `sql/maintenance`

Scripts de manutencao e saneamento.

### `sql/migrations`

Migrations versionadas com arquivos `_up.sql` e `_down.sql`.

## Setup Local

### Pre-requisitos

- Python 3.10+ recomendado
- projeto Supabase ja provisionado
- chave de API do YouTube Data API

### Variaveis de ambiente

Os scripts dependem destas variaveis:

```env
YOUTUBE_API_KEY=your_youtube_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_key
BATCH_SIZE=3
```

Notas:

- `BATCH_SIZE` e usado no pipeline de discovery e define quantos creators sao processados por execucao
- `SUPABASE_KEY` precisa ter permissao para leitura e escrita nas tabelas utilizadas

### Instalacao de dependencias

Para o pipeline de metricas:

```powershell
pip install -r scripts/cloud_run/postMetrics/requirements.txt
```

Para o pipeline de discovery:

```powershell
pip install -r scripts/cloud_run/youtube_main_scraper/requirements.txt
```

Para Fenabrave:

```powershell
cd scripts\fenabrave_ingestion
pip install -r requirements.txt
```

## Ordem Recomendada de Provisionamento SQL

Se voce estiver montando um ambiente novo no Supabase, esta e uma ordem segura para aplicar os artefatos.

### 1. Criar tabelas base

Aplicar, nesta ordem:

1. `sql/ddl/tables/001_create_entities.sql`
2. `sql/ddl/tables/002_create_sub_niches.sql`
3. `sql/ddl/tables/003_create_creators.sql`
4. `sql/ddl/tables/004_create_posts.sql`
5. `sql/ddl/tables/005_create_post_metrics_history.sql`
6. `sql/ddl/tables/006_create_entity_sub_niches.sql`
7. `sql/ddl/tables/007_create_pipeline_state.sql`
8. `sql/ddl/tables/008_create_post_update_queue.sql`
9. `sql/ddl/tables/009_create_entity_intake.sql`

### 2. Criar views

Aplicar:

1. `sql/ddl/views/001_create_v_entity_intake_review.sql`
2. `sql/ddl/views/002_create_v_post_update_queue_batch.sql`

### 3. Criar funcoes e triggers

Aplicar:

1. `sql/ddl/triggers/001_trg_sync_post.sql`
2. `sql/ddl/triggers/002_add_to_queue.sql`
3. `sql/ddl/functions/002_queue_scheduling_functions.sql`
4. `sql/ddl/triggers/003_refresh_post_queue_on_metrics.sql`

### 4. Criar indices e auxiliares

Aplicar:

1. `sql/ddl/functions/001_create_publish_entity_intake_function.sql`
2. `sql/ddl/indexes/002_create_unique_index_entities_normalized_name.sql`

### 5. Aplicar migrations posteriores

Se o ambiente exigir a logica mais recente de fila e rechecagem:

1. `sql/migrations/2026-04-17_001_queue_recheck_rules_up.sql`

Use o respectivo arquivo `_down.sql` apenas para rollback controlado.

## Documentacao Operacional

Documentos importantes por frente:

### Social media

- `docs/project/04_PIPELINE_STATUS.md`
- `docs/project/05_DECISOES_TECNICAS.md`
- `docs/social_media/08_QUEUE_CAPACITY_TEST.md`
- `docs/social_media/09_QUEUE_SLICING_AND_RESCHEDULING.md`

### Fontes externas

- `docs/external_data/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md`
- `docs/external_data/23_FENABRAVE_PHASE1_INGESTION_SPEC.md`
- `docs/external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md`

### Dashboard

- `docs/dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md`

## Estado Atual do Projeto

### Dados social media

- YouTube operacional como plataforma principal
- worker de metricas ativo
- fila com priorizacao e rechecagem no SQL
- backfill e cobertura historica em evolucao

### Dados de fontes externas

- Fenabrave com implementacao inicial no repositorio
- Carros na Web em fase de plano de ingestao
- SENATRAN / RENAVAM em fase de estudo

### Dashboard

- estrategia definida
- views analiticas principais ja preparadas
- app Streamlit inicial em construcao
- mockup de `Cadastro de Criadores` pronto para validacao visual e de processo
- mockup de `Cadastro Fenabrave` pronto para validacao visual e de processo
- ligacao SQL das views de cadastro ainda pendente

## Proximos Passos Sugeridos

- expandir a documentacao de multiplataforma para alem do YouTube
- consolidar a frente de fontes externas em schema e ingestao versionados
- ligar o `Cadastro de Criadores` ao SQL com busca, review e publicacao controlada
- ligar o `Cadastro Fenabrave` ao SQL com metadados, preview e validacao do periodo
- implementar o restante do app inicial do dashboard consumindo as views do Supabase

