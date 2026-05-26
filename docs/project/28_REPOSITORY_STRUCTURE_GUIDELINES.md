# REPOSITORY STRUCTURE GUIDELINES

## Objetivo

Este documento define a diretriz estrutural do repositorio.

Ele nao descreve apenas a organizacao de `docs`, mas tambem a logica esperada
para:

- `sql`
- `scripts`
- documentacao operacional
- artefatos locais e temporarios
- local correto para arquivos novos

O objetivo e reduzir ambiguidade, evitar espalhamento de arquivos e preservar
coerencia entre as 3 frentes do projeto:

1. Dados social media
2. Dados de fontes externas
3. Dashboard

## Principio geral

Cada arquivo novo deve ser criado no local que representa sua natureza
principal, e nao apenas o assunto superficial do momento.

Regra pratica:

- se o arquivo e executavel, ele deve ficar em `scripts/`
- se o arquivo e SQL executavel, ele deve ficar em `sql/`
- se o arquivo e documentacao, ele deve ficar em `docs/`

## Estrutura alvo de alto nivel

```text
/
  README.md
  docs/
  scripts/
  sql/
```

### Papel de cada raiz

#### `README.md`

Arquivo de entrada do projeto.

Deve explicar:

- o que e o projeto
- quais sao as 3 frentes
- como elas se relacionam
- onde encontrar os documentos principais

#### `docs/`

Destino final da documentacao de projeto.

Deve concentrar:

- backlog
- roadmap
- status
- decisoes tecnicas
- specs
- runbooks
- validacoes
- planos de ingestao
- regras de organizacao

Observacao:

- esta e a raiz oficial da documentacao de projeto
- novos documentos devem nascer aqui, ja classificados pela frente correta

#### `scripts/`

Destino de codigo executavel, automacoes e utilitarios operacionais.

Deve concentrar:

- scripts Python
- launchers PowerShell
- requirements locais por fluxo
- artefatos operacionais controlados por frente

Nao deve concentrar:

- SQL executavel
- documentacao estrutural principal do projeto

#### `sql/`

Destino exclusivo de SQL executavel e artefatos diretamente ligados ao banco.

Deve concentrar:

- DDL
- DML
- migrations
- scripts de manutencao
- snapshots de schema

Nao deve concentrar:

- backlog
- roadmap
- status geral do projeto
- padroes de commit
- documentacao de produto

## Diretriz para `docs/`

### Estrutura alvo

```text
docs/
  README.md
  project/
  social_media/
  external_data/
  dashboard/
  data_model/
```

### `docs/project/`

Usar para documentos transversais de projeto.

Exemplos:

- backlog
- roadmap
- status consolidado
- decisoes tecnicas
- padrao de commit
- diretrizes estruturais

### `docs/social_media/`

Usar para documentos da frente de dados social media.

Exemplos:

- fila de rechecagem
- capacidade do worker
- FIFO
- score hibrido
- bootstrap
- backfill
- runbooks de scheduler

### `docs/external_data/`

Usar para documentos da frente de dados externos.

Exemplos:

- Fenabrave
- Carros na Web
- SENATRAN / RENAVAM
- calendario operacional mensal de fontes externas

### `docs/dashboard/`

Usar para documentos da frente de dashboard.

Exemplos:

- especificacao do app
- contrato de dados do dashboard
- runbooks de deploy do Streamlit
- criterios de pronto do MVP

### `docs/data_model/`

Usar para documentos de modelo de dados e organizacao estrutural.

Exemplos:

- quality checks
- intake de entities
- organizacao de tabelas
- taxonomia
- harmonizacao estrutural

## Diretriz para `sql/`

### Estrutura esperada

```text
sql/
  ddl/
    functions/
    tables/
    views/
    triggers/
    indexes/
    schema/
  dml/
  maintenance/
  migrations/
```

### `sql/ddl/tables/`

Usar para criacao de tabelas.

Exemplos:

- `create table`
- constraints estruturais da propria tabela

### `sql/ddl/views/`

Usar para views.

Exemplos:

- `create view`
- `create or replace view`
- views de consumo analitico do dashboard

Regra obrigatoria para filtros temporais:

- ao filtrar campo `timestamp` por periodo de calendario, nao usar
  `timestamp_col <= data_final` se `data_final` nao tiver horario final
  explicito
- usar limite superior exclusivo:

```sql
where timestamp_col >= period_start
  and timestamp_col < period_end + interval '1 day'
```

- quando a regra for puramente de calendario e o campo puder ser convertido com
  seguranca, usar:

```sql
where timestamp_col::date between period_start::date and period_end::date
```

- qualquer codigo gerado por GPT/Codex para semanas, meses ou periodos deve
  declarar se esta filtrando `date` ou `timestamp`
- tabelas detalhadas e cards agregados devem usar a mesma janela temporal para
  evitar diferenca entre totais e listas

- views operacionais
- views analiticas
- views de revisao

### `sql/ddl/triggers/`

Usar para:

- funcoes que suportam trigger
- trigger functions
- logica operacional fortemente acoplada ao fluxo do banco

### `sql/ddl/indexes/`

Usar para:

- indices

### `sql/ddl/functions/`

Usar para:

- funcoes SQL reutilizaveis
- funcoes auxiliares de fila, score, validacao e publicacao
- funcoes que nao sao, por si so, triggers nem indices

### `sql/ddl/schema/`

Usar para snapshots consolidados do schema.

### `sql/dml/`

Usar para SQL operacional que consulta, revisa, publica ou ajusta dados sem
    alterar a estrutura do banco.

Exemplos:

- queries de revisao
- publicacao manual
- normalizacao operacional

### `sql/maintenance/`

Usar para manutencao corretiva ou saneamento.

Exemplos:

- deduplicacao
- validacao de links
- reparos controlados

### `sql/migrations/`

Usar para mudancas versionadas de banco com ordem temporal e possibilidade de
rollback.

Exemplos:

- `_up.sql`
- `_down.sql`

Regra:

- toda mudanca de banco aplicada de forma incremental e que precise de
  rastreabilidade operacional deve entrar aqui

## Diretriz para `scripts/`

### Estrutura esperada por frente

```text
scripts/
  cloud_run/
  offline_backfill/
  fenabrave_ingestion/
  pipedream/
```

No futuro, o esperado e expandir com estruturas como:

```text
scripts/
  carrosnaweb_ingestion/
  renavam_ingestion/
```

### Regra principal

Cada pasta em `scripts/` deve representar um fluxo executavel, uma automacao ou
uma integracao concreta.

Nao deve representar apenas um assunto conceitual.

### `scripts/cloud_run/`

Usar para entrypoints e pacotes preparados para execucao serverless.

Regra:

- se um fluxo e desenhado para Cloud Run ou runtime semelhante, ele deve morar
  aqui
- isso inclui o worker de metricas e o discovery principal quando a execucao
  oficial for empacotada para Cloud Run

### `scripts/offline_backfill/`

Usar para rotinas offline, controladas, geralmente manuais ou agendadas fora do
runtime principal.

### `scripts/fenabrave_ingestion/`

Usar para a ingestao da fonte externa Fenabrave.

Pode conter:

- script principal
- helper PowerShell
- `requirements.txt`
- `.env.example`
- README local
- `tmp/` e artefatos locais que precisem de controle operacional

### `scripts/pipedream/`

Usar apenas para exportacoes, rascunhos ou referencias de automacoes do
Pipedream.

Regra:

- nao deve ser tratado como implementacao principal quando ja existir versao
  Python ativa no repositorio

### `scripts/postMetrics/`

Estado atual:

- a pasta hoje nao representa um fluxo principal valido
- contem apenas `__pycache__`

Diretriz:

- nao usar esta pasta para novos arquivos
- se no futuro voltar a ser necessaria, ela deve ganhar um papel claro
- enquanto isso, deve ser tratada como sobra tecnica a ser limpa em momento
  apropriado

## Regras para arquivos auxiliares e temporarios

### `.env`

Pode existir dentro de pastas de script quando a rotina for local e isolada.

Regra:

- sempre acompanhar `.env.example` quando fizer sentido
- nunca versionar segredos reais

### `.venv`

Regra:

- ambientes virtuais nao devem ser tratados como parte estrutural do projeto
- podem existir localmente durante a operacao
- nao devem orientar a arquitetura do repositorio

### `__pycache__`

Regra:

- nao deve orientar organizacao de codigo
- nao criar estrutura nova baseada nisso

### `tmp/`

Usar apenas para artefatos intermediarios locais de execucao controlada.

Regra:

- se o artefato passar a ter valor de auditoria ou reprocessamento, ele deve
  ganhar uma pasta nomeada e documentada

### `logs/`

Pode existir dentro do fluxo que gera o log.

Regra:

- logs operacionais persistentes ficam junto do fluxo executavel correspondente
- o local do log deve ser documentado no README local ou runbook associado

## Regra de classificacao para arquivos novos

Antes de criar um arquivo novo, responder:

1. ele e codigo executavel?
2. ele e SQL executavel?
3. ele e documentacao?
4. ele e artefato temporario/local?
5. a qual frente principal ele pertence?

### Se for codigo executavel

- colocar em `scripts/<fluxo>/`

### Se for SQL executavel

- colocar em `sql/<categoria>/`

### Se for documentacao

- classificar pelo papel principal:
  - `project`
  - `social_media`
  - `external_data`
  - `dashboard`
  - `data_model`

### Se for artefato temporario

- manter junto do fluxo local, nunca como centro da estrutura do projeto

## Regra de branches para criacao e atualizacao de arquivos

A `main` e a fonte canonica para documentacao geral, decisoes tecnicas,
roadmap, status operacional, indices e regras estruturais.

Branches de feature podem manter documentos de trabalho enquanto a entrega
esta em descoberta ou implementacao, mas nao devem reter por muito tempo
decisoes que ja viraram verdade do projeto.

### Criar arquivo novo

- se o arquivo descreve uma ideia, experimento visual ou proposta ainda nao
  implementada, criar na branch da feature correspondente
- se o arquivo descreve uma decisao aprovada, contrato de dados, runbook
  operacional, roadmap ou status real do projeto, criar ou sincronizar na
  `main`
- arquivos de design ainda nao implementados podem permanecer apenas na branch
  de feature ate virarem execucao aprovada

### Atualizar arquivo existente

Antes de alterar um documento existente, verificar:

1. o arquivo e especifico da feature?
2. o arquivo e uma fonte global de verdade do projeto?
3. a alteracao deve existir na `main` agora?

Se a alteracao afetar `README.md`, `docs/README.md`, roadmap, status,
decisoes tecnicas, regras de workflow ou contrato de dados aprovado, a mudanca
deve ser levada para a `main` no mesmo ciclo de trabalho ou em um commit de
documentacao separado.

### Sincronizacao entre branches

- trazer `main` para a branch de feature antes de sessoes relevantes de trabalho
- levar docs globais da feature para `main` quando um marco funcional for
  validado
- preferir commits pequenos de documentacao quando o codigo da feature ainda
  nao deve entrar na `main`
- deixar na branch de feature apenas documentos de proposta, design ou
  experimento que ainda nao representam estado real do projeto

## Mapeamento dos arquivos atuais

### Documentacao em `docs/project/`

- `01_BACKLOG.md`
- `02_ROADMAP.md`
- `04_PIPELINE_STATUS.md`
- `05_DECISOES_TECNICAS.md`
- `06_COMMIT_PATTERN.md`
- `README.md`
- `README_GESTAO_PROJETO.md`
- `28_REPOSITORY_STRUCTURE_GUIDELINES.md`

### Documentacao em `docs/social_media/`

- `07_QUEUE_VALIDATION_CHECKLIST.md`
- `08_QUEUE_CAPACITY_TEST.md`
- `09_QUEUE_SLICING_AND_RESCHEDULING.md`
- `10_QUEUE_CAPACITY_RESULTS_2026-05-08.md`
- `11_QUEUE_FIFO_VALIDATION_2026-05-08.md`
- `12_HYBRID_PRIORITY_SCORE_SPEC.md`
- `13_HYBRID_SCORE_EVALUATION_STRATEGY.md`
- `14_HYBRID_SCORE_VALIDATION_PLAN.md`
- `15_LOW_HISTORY_BOOTSTRAP_AND_BACKFILL_SPEC.md`
- `17_LEGACY_LOW_OFFLINE_BACKFILL_SPEC.md`
- `18_LEGACY_LOW_OFFLINE_BACKFILL_PHASE1_SPEC.md`
- `19_LEGACY_LOW_OFFLINE_BACKFILL_SCRIPT_DESIGN.md`
- `20_LEGACY_LOW_BACKFILL_RESULTS_2026-05-14.md`
- `21_WINDOWS_SCHEDULER_BACKFILL_SETUP.md`
- `24_PHASE2_INITIAL_DATA_BASELINE_2026-05-17.md`
- `25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md`
- `26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md`

### Documentacao em `docs/external_data/`

- `00_OFFLINE_OPERATIONS_CALENDAR.md`
- `22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md`
- `23_FENABRAVE_PHASE1_INGESTION_SPEC.md`
- `27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md`

### Documentacao em `docs/dashboard/`

- `16_ONLINE_DASHBOARD_SUPABASE_SPEC.md`
- `29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md`

### Documentacao em `docs/data_model/`

- `03_DATA_QUALITY_CHECKS.md`
- `entity_intake_process.md`
- `table_organization_v2.md`

## Regra de manutencao do indice

Todo item novo gerado em documentacao deve ser incorporado ao indice de
documentacao.

- `docs/README.md`

Se um documento novo nao entrar no indice, a documentacao deve ser considerada
incompleta.

## Regra final

Quando houver duvida sobre onde um arquivo deve ficar, escolher o local pelo
papel estrutural do arquivo e nao pela tarefa momentanea que motivou sua
criacao.

