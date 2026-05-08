# Social Media Analytics

Pipeline de coleta e atualização de métricas de redes sociais, com foco atual em YouTube e persistência em Supabase.

O projeto cobre três frentes principais:

- discovery e ingestão inicial de vídeos por creator
- atualização recorrente de métricas dos posts já cadastrados
- intake e governança de entidades via SQL

## Resumo Rápido

O sistema funciona em torno destes blocos:

1. `entities` e `creators` definem quem será monitorado
2. o pipeline de discovery busca vídeos dos creators no YouTube e grava em `posts`
3. triggers e funções alimentam e reprogramam a fila `post_update_queue`
4. o pipeline de métricas salva snapshots em `post_metrics_history` e atualiza os valores correntes em `posts`
5. o intake de entidades permite revisar e publicar novas entradas com mais controle

## Estrutura do Repositório

```text
.
├── README.md
├── scripts
│   ├── cloud_run
│   │   ├── postMetrics
│   │   │   ├── main.py
│   │   │   └── requirements.txt
│   │   └── youtube_main_scraper
│   ├── pipedream
│   │   ├── social_media-analytics__youtube_scraper_postMetrics.txt
│   │   └── youtube_scraper.py.txt
│   └── youtube_main_scraper
│       ├── main.py
│       └── requirements.txt
└── sql
    ├── ddl
    │   ├── indexes
    │   ├── schema
    │   ├── tables
    │   ├── triggers
    │   └── views
    ├── dml
    ├── docs
    ├── maintenance
    └── migrations
```

## Arquitetura dos Pipelines

### 1. Discovery / ingestão inicial

Arquivos principais:

- `scripts/youtube_main_scraper/main.py`
- `scripts/youtube_main_scraper/requirements.txt`

Responsabilidades:

- ler creators da tabela `creators`
- controlar progresso com cursor em `pipeline_state`
- buscar uploads de canais do YouTube
- classificar vídeos como `short` ou `long`
- fazer upsert dos posts na tabela `posts`

Também existe uma versão de apoio em:

- `scripts/pipedream/youtube_scraper.py.txt`

### 2. Atualização de métricas

Arquivos principais:

- `scripts/cloud_run/postMetrics/main.py`
- `scripts/cloud_run/postMetrics/requirements.txt`

Responsabilidades:

- buscar posts pendentes em `post_update_queue`
- consultar estatísticas atualizadas na API do YouTube
- registrar histórico em `post_metrics_history`
- atualizar os campos correntes em `posts`
- marcar itens da fila como processados

Também existe uma versão de apoio em:

- `scripts/pipedream/social_media-analytics__youtube_scraper_postMetrics.txt`

### 3. Intake e revisão de entidades

Arquivos principais no banco:

- `sql/ddl/tables/009_create_entity_intake.sql`
- `sql/ddl/views/001_create_v_entity_intake_review.sql`
- `sql/dml/review_entity_intake.sql`
- `sql/dml/publish_entity_intake_manual_run.sql`

Responsabilidades:

- receber entradas brutas de entidades
- normalizar nomes
- revisar duplicidade e consistência
- publicar registros aprovados para as tabelas definitivas

## Estrutura SQL

O diretório `sql/` está organizado por finalidade.

### `sql/ddl`

Definição estrutural do banco:

- `tables/`: criação das tabelas principais
- `views/`: views operacionais e de revisão
- `triggers/`: funções e triggers de sincronização e queue
- `indexes/`: índices e funções auxiliares
- `schema/`: snapshot consolidado do schema

Exemplos:

- `sql/ddl/tables/001_create_entities.sql`
- `sql/ddl/tables/004_create_posts.sql`
- `sql/ddl/tables/008_create_post_update_queue.sql`
- `sql/ddl/views/002_create_v_post_update_queue_batch.sql`
- `sql/ddl/triggers/002_queue_scheduling_functions.sql`

### `sql/dml`

Scripts operacionais de leitura, revisão e publicação.

Exemplos:

- `sql/dml/review_entity_intake.sql`
- `sql/dml/publish_entity_intake_manual_run.sql`
- `sql/dml/intake_normalization_check.sql`

### `sql/maintenance`

Scripts de manutenção e saneamento.

Exemplos:

- `sql/maintenance/deduplicate_entities.sql`
- `sql/maintenance/validate_entity_link.sql`

### `sql/migrations`

Migrations versionadas com arquivos `_up.sql` e `_down.sql`.

Exemplos:

- `sql/migrations/2026-04-17_001_queue_recheck_rules_up.sql`
- `sql/migrations/2026-04-17_001_queue_recheck_rules_down.sql`

### `sql/docs`

Documentação interna do projeto.

Exemplos:

- `sql/docs/02_ROADMAP.md`
- `sql/docs/05_DECISOES_TECNICAS.md`
- `sql/docs/07_QUEUE_VALIDATION_CHECKLIST.md`
- `sql/docs/09_QUEUE_SLICING_AND_RESCHEDULING.md`
- `sql/docs/entity_intake_process.md`

## Modelo de Dados

### `entities`

Entidades de negócio monitoradas, como marcas, pessoas ou operações.

### `creators`

Perfis ou canais ligados a uma entidade. O schema suporta múltiplas plataformas, mas a automação atual está focada em YouTube.

### `posts`

Tabela principal de posts ou vídeos coletados, com os valores mais recentes de views, likes e comments.

### `post_metrics_history`

Histórico temporal das métricas coletadas.

### `post_update_queue`

Fila de atualização incremental dos posts.

### `pipeline_state`

Armazena estados simples do pipeline, como cursor de processamento.

### `entity_intake`

Tabela de entrada controlada para revisão e publicação de novas entidades.

## Setup Local

### Pré-requisitos

- Python 3.10+ recomendado
- projeto Supabase já provisionado
- chave de API do YouTube Data API

### Variáveis de ambiente

Os scripts dependem destas variáveis:

```env
YOUTUBE_API_KEY=your_youtube_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_key
BATCH_SIZE=3
```

Notas:

- `BATCH_SIZE` é usado no pipeline de discovery e define quantos creators são processados por execução
- `SUPABASE_KEY` precisa ter permissão para leitura e escrita nas tabelas utilizadas

### Instalação de dependências

Para o pipeline de métricas:

```powershell
pip install -r scripts/cloud_run/postMetrics/requirements.txt
```

Para o pipeline de discovery:

```powershell
pip install -r scripts/youtube_main_scraper/requirements.txt
```

## Ordem Recomendada de Provisionamento SQL

Se você estiver montando um ambiente novo no Supabase, esta é uma ordem segura para aplicar os artefatos.

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

### 3. Criar funções e triggers

Aplicar:

1. `sql/ddl/triggers/001_trg_sync_post.sql`
2. `sql/ddl/triggers/002_add_to_queue.sql`
3. `sql/ddl/triggers/002_queue_scheduling_functions.sql`
4. `sql/ddl/triggers/003_refresh_post_queue_on_metrics.sql`

### 4. Criar índices e auxiliares

Aplicar:

1. `sql/ddl/indexes/001_create_publish_entity_intake_function.sql`
2. `sql/ddl/indexes/002_create_unique_index_entities_normalized_name.sql`

### 5. Aplicar migrations posteriores

Se o ambiente exigir a lógica mais recente de fila e rechecagem:

1. `sql/migrations/2026-04-17_001_queue_recheck_rules_up.sql`

Use o respectivo arquivo `_down.sql` apenas para rollback controlado.

## Fluxos de Uso

### Fluxo A: discovery / carga inicial de posts

1. cadastrar `entities` e `creators`
2. garantir que `pipeline_state` esteja inicializado
3. executar o discovery script
4. validar se `posts` foi populada
5. confirmar se a fila começou a receber posts via trigger

### Fluxo B: atualização de métricas

1. consultar os itens elegíveis em `post_update_queue` ou `v_post_update_queue_batch`
2. executar o pipeline de métricas
3. validar inserts em `post_metrics_history`
4. validar atualização dos campos correntes em `posts`
5. conferir reagendamento de `next_check` na fila

### Fluxo C: intake e governança de entidades

1. inserir registros em `entity_intake`
2. revisar itens pela view `v_entity_intake_review`
3. executar scripts de revisão em `sql/dml`
4. publicar manualmente os aprovados
5. rodar scripts de manutenção quando necessário

## Como Rodar

### Discovery local

O script em `scripts/youtube_main_scraper/main.py` expõe a função `run(request)`, mas a lógica principal está em `run_pipeline()`. Para uso local, o caminho mais simples é adaptar uma chamada Python que importe o módulo e execute `run_pipeline()`.

Uso típico:

- preparar variáveis de ambiente
- instalar dependências
- executar o módulo/script no ambiente escolhido

### Métricas em Cloud Run

O diretório `scripts/cloud_run/postMetrics` contém uma função Python preparada para ambiente serverless com `functions-framework`.

Dependências atuais:

```text
requests==2.31.0
functions-framework==3.*
```

### Pipedream

Os arquivos em `scripts/pipedream` parecem representar exportações ou versões de apoio dos workflows principais.

## Lógica da Fila

A fila de rechecagem não é apenas uma lista de pendências; ela já incorpora prioridade e reagendamento.

Pontos importantes:

- `add_to_queue()` insere um post novo na fila com `next_check = now()`
- `calculate_post_priority()` gera um score a partir de views, likes e comments
- `calculate_next_check()` define o próximo horário de rechecagem por faixa de prioridade
- `refresh_post_queue_on_metrics()` atualiza score, `last_checked`, `next_check` e `needs_update`
- `v_post_update_queue_batch` monta um lote balanceado por faixas de prioridade, com limite total de 20 itens

Isso significa que a lógica operacional da fila está parcialmente centralizada no SQL, não apenas no código Python.

## Documentação Operacional

Além deste README, há documentação interna útil em:

- `sql/docs/04_PIPELINE_STATUS.md`
- `sql/docs/05_DECISOES_TECNICAS.md`
- `sql/docs/08_QUEUE_CAPACITY_TEST.md`
- `sql/docs/09_QUEUE_SLICING_AND_RESCHEDULING.md`
- `sql/docs/README_GESTAO_PROJETO.md`

## Estado Atual do Projeto

O projeto já tem uma base funcional de MVP para:

- cadastrar e organizar entidades e creators
- coletar vídeos no YouTube
- classificar vídeos curtos e longos
- armazenar métricas atuais
- manter histórico temporal
- atualizar posts por fila
- operar intake e revisão de entidades no banco

Ainda há espaço para evolução em:

- documentação de deploy passo a passo
- testes automatizados
- observabilidade e logs
- retries e tratamento de falhas externas
- padronização final entre scripts Python, Cloud Run e Pipedream
- consolidação do papel de `scripts/cloud_run/youtube_main_scraper`, que hoje existe sem implementação visível
