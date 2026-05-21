# Inclusao de dados externos no Streamlit

## Objetivo

Definir uma area operacional no dashboard Streamlit para registrar novos dados
externos e pedidos de inclusao na base sem inserir diretamente nas tabelas
finais do banco.

Esta tela deve funcionar como uma camada de intake controlado. Ela nao substitui
os scripts, validacoes e funcoes SQL ja existentes. O objetivo inicial e reduzir
erro manual, deixar o fluxo mais visivel e preparar o caminho para operacoes
controladas via RPC.

## Referencias atuais

Procedimento base para novo creator/entity:

- `docs/data_model/entity_intake_process.md`
- `sql/ddl/tables/009_create_entity_intake.sql`
- `sql/ddl/views/001_create_v_entity_intake_review.sql`
- `sql/dml/review_entity_intake.sql`
- `sql/dml/publish_entity_intake_manual_run.sql`
- `sql/maintenance/validate_entity_link.sql`

Tabelas finais relacionadas:

- `public.entities`
- `public.entity_sub_niches`
- `public.creators`

Regra principal ja documentada:

```text
Nunca inserir manualmente direto em public.entities ou public.entity_sub_niches.
Toda entrada manual de entity/sub_niche deve passar por public.entity_intake.
```

## Pagina proposta

Nome sugerido:

```text
Inclusao de dados externos
```

Papel da pagina:

- concentrar fluxos manuais de entrada de dados ainda nao automatizados
- separar dados externos estruturados de acoes operacionais do pipeline
- permitir revisao antes de publicar qualquer informacao no modelo principal
- criar trilha clara para futuras RPCs controladas

Escopo inicial:

- sub-view para novo criador de conteudo
- espaco futuro para fontes externas como Fenabrave, Carros na Web e outras
  entradas de apoio
- exibicao de status/revisao dos registros pendentes

Fora do escopo inicial:

- escrita direta em `public.creators` sem entity validada
- escrita direta em `public.entities`
- escrita direta em `public.entity_sub_niches`
- upload/processamento automatico de PDFs da Fenabrave
- crawler ou scraper disparado pela tela
- uso de `SUPABASE_SERVICE_ROLE_KEY` no Streamlit

## Sub-view: novo criador de conteudo

Nome sugerido:

```text
Novo criador de conteudo
```

Objetivo:

- registrar um creator/canal novo de forma guiada
- garantir que a entity canonicamente associada exista ou seja criada pelo
  fluxo de intake
- preparar o cadastro do canal em `public.creators` sem quebrar governanca

## Fluxo operacional

### 1. Entrada de dados

Campos iniciais da sub-view:

- `raw_name`
- `sub_niche_name`
- `niche`
- `creator_type`
- `platform`
- `username`
- `channel_id`
- `followers`
- `notes`

Campos mapeados diretamente para `public.entity_intake`:

- `raw_name`
- `sub_niche_name`
- `niche`
- `creator_type`
- `notes`
- `status`

Campos que pertencem ao cadastro final de creator:

- `platform`
- `username`
- `channel_id`
- `followers`

Regra:

- os campos de creator devem ficar em estado pendente ate a entity existir e
  possuir `entity_id` resolvido
- a primeira implementacao pode manter esses campos apenas na interface ou em
  uma tabela de intake propria futura, porque `public.entity_intake` atual nao
  possui colunas para `platform`, `username`, `channel_id` e `followers`

## Estados da sub-view

### Rascunho

Uso:

- formulario preenchido, ainda nao enviado

Acao:

- validar campos obrigatorios localmente

### Enviado para intake

Uso:

- registro criado em `public.entity_intake`

Acao:

- exibir o registro na revisao baseada em `public.v_entity_intake_review`

### Pronto para publicar entity

Uso:

- `review_result = READY_TO_INSERT`
- ou entity ja existente com `existing_entity_id` preenchido
- `sub_niche_id` resolvido

Acao:

- permitir publicacao controlada via `public.publish_entity_intake()`
- depois reconsultar a view de revisao

### Entity publicada

Uso:

- registro em `entity_intake` esta `published`
- entity ja existe em `public.entities`

Acao:

- liberar etapa de cadastro do canal em `public.creators`

### Creator pronto para coleta

Uso:

- `public.creators` possui linha com `entity_id`, `platform` e `channel_id`

Acao:

- o fluxo de discovery pode considerar esse creator nas proximas execucoes

## Contrato de dados atual

### Leitura

View existente:

```text
public.v_entity_intake_review
```

Campos relevantes:

- `id`
- `raw_name`
- `normalized_name`
- `sub_niche_name`
- `niche`
- `creator_type`
- `notes`
- `status`
- `existing_entity_id`
- `existing_entity_name`
- `sub_niche_id`
- `matched_sub_niche_name`
- `review_result`

### Escrita recomendada

Primeira escrita:

```text
public.entity_intake
```

Metodo preferido para o Streamlit:

- RPC controlada para inserir registros em `entity_intake`
- ou, em fase inicial, manter o cadastro manual pelo Supabase UI e usar o
  Streamlit apenas para revisar

RPC futura sugerida:

```text
public.create_entity_intake_entry(
  p_raw_name text,
  p_sub_niche_name text,
  p_niche text,
  p_creator_type text,
  p_notes text
)
```

Comportamento esperado:

- inserir em `public.entity_intake`
- preencher `status = 'pending'`
- nao inserir diretamente em `public.entities`
- nao inserir diretamente em `public.entity_sub_niches`

## Lacuna atual: cadastro em `public.creators`

O procedimento documentado hoje cobre bem a criacao de `entities` e vinculos de
`entity_sub_niches`, mas nao fecha sozinho o cadastro de uma linha em
`public.creators`.

Como `public.creators` exige `entity_id`, `platform` e `channel_id`, a sub-view
deve tratar isso como segunda etapa.

Regra recomendada:

- nao criar creator enquanto `entity_id` nao estiver resolvido
- validar unicidade de `channel_id`
- validar unicidade de `(platform, channel_id)`
- validar `platform` contra os valores aceitos:
  - `youtube`
  - `instagram`
  - `tiktok`

RPC futura sugerida:

```text
public.create_creator_from_resolved_entity(
  p_entity_id integer,
  p_platform text,
  p_username text,
  p_channel_id text,
  p_followers integer
)
```

Comportamento esperado:

- validar se `entity_id` existe em `public.entities`
- validar `platform`
- rejeitar `channel_id` duplicado
- inserir em `public.creators`
- retornar o `creator_id`

## Experiencia da tela

### Layout

Pagina:

```text
Inclusao de dados externos
```

Sub-views iniciais:

- `Novo criador de conteudo`
- `Revisao de intake`
- `Fontes externas futuras`

### Novo criador de conteudo

Blocos:

- formulario de entity
- formulario de canal/plataforma
- validacao local
- resultado de revisao
- acoes permitidas

Campos obrigatorios:

- `raw_name`
- `sub_niche_name`
- `niche`
- `creator_type`
- `platform`
- `channel_id`

Campos opcionais:

- `username`
- `followers`
- `notes`

### Revisao de intake

Tabela baseada em:

```text
public.v_entity_intake_review
```

Colunas recomendadas:

- `raw_name`
- `sub_niche_name`
- `status`
- `review_result`
- `existing_entity_id`
- `existing_entity_name`
- `sub_niche_id`
- `matched_sub_niche_name`
- `notes`

Filtros:

- status
- review_result
- sub_niche_name
- raw_name

## Sequencia recomendada de implementacao

1. Criar a pagina Streamlit `Inclusao de dados externos`.
2. Criar a sub-view `Novo criador de conteudo` apenas como formulario e revisao,
   sem escrita direta em tabelas finais.
3. Conectar a leitura de `public.v_entity_intake_review`.
4. Definir ou criar RPC para inserir em `public.entity_intake`.
5. Definir ou criar RPC separada para cadastrar `public.creators` apenas quando
   `entity_id` estiver resolvido.
6. Validar o fluxo completo com um creator de teste.
7. Documentar o resultado no pipeline status antes de considerar a tela pronta.

## Validacoes obrigatorias

Antes de considerar a sub-view pronta:

- confirmar que `raw_name` nao gera duplicidade inesperada em `entities`
- confirmar que `sub_niche_name` encontra `sub_niche_id`
- confirmar que `channel_id` nao existe em `public.creators`
- confirmar que `(platform, channel_id)` nao existe em `public.creators`
- confirmar que nenhum segredo sensivel e usado no Streamlit
- confirmar que a tela nao permite publicacao sem revisao
- confirmar que creator criado entra no fluxo normal de discovery/coleta

## Riscos

- misturar entity e creator em uma unica escrita pode quebrar governanca
- cadastrar canal antes de resolver `entity_id` cria orphan operacional
- permitir SQL livre no Streamlit reduz auditabilidade
- duplicidade de `channel_id` pode afetar discovery e historico
- sub_niche inexistente pode publicar uma entity sem classificacao util

## Decisao recomendada

Implementar a tela em duas etapas:

1. Intake e revisao de entity/sub_niche usando o fluxo existente.
2. Cadastro de creator em `public.creators` somente depois de `entity_id`
   resolvido.

Essa separacao preserva a governanca ja documentada e evita que o dashboard
vire uma porta de escrita direta nas tabelas finais.
