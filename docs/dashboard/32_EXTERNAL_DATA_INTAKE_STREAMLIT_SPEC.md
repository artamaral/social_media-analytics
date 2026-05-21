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
- garantir que a entity canonicamente associada exista antes de criar o creator
- criar a entity pelo fluxo de intake quando ela ainda nao existir
- garantir que os nichos/subnichos estejam resolvidos antes de associar o
  creator ao modelo analitico
- permitir solicitacao controlada de novos nichos/subnichos quando a
  classificacao ainda nao existir
- preparar o cadastro do canal em `public.creators` sem quebrar governanca

## Fluxo operacional

### Principio do fluxo na UI

A experiencia da tela deve seguir esta ordem:

1. Procurar entity existente.
2. Se a entity nao existir, criar solicitacao de entity pelo intake atual.
3. Resolver nicho/subnicho existente ou solicitar criacao de novo nicho/subnicho.
4. Criar o creator somente depois de `entity_id` e classificacao estarem
   resolvidos.
5. Confirmar que o creator entrou no fluxo normal de discovery/coleta.

O procedimento manual documentado continua valido e deve seguir do mesmo jeito.
A diferenca e que a UI deve transformar esse processo em uma jornada guiada,
sem exigir que o operador lembre a ordem tecnica das tabelas.

### 1. Procurar ou criar entity

Antes de qualquer cadastro em `public.creators`, a sub-view deve verificar se a
entity ja existe.

Entrada minima:

- `raw_name`
- `normalized_name` calculado ou sugerido
- `creator_type`
- `notes`

Resultados possiveis:

- entity encontrada: seguir para resolucao de nichos
- entity nao encontrada: criar registro em `public.entity_intake`
- duplicidade provavel: bloquear o fluxo e pedir revisao manual

Regra:

- nenhuma linha em `public.creators` pode ser criada sem `entity_id` resolvido

### 2. Resolver ou criar nicho/subnicho

Depois de identificar a entity, a UI deve confirmar a classificacao analitica
que sera vinculada ao creator.

Entrada minima:

- `niche`
- `sub_niche_name`

Resultados possiveis:

- nicho/subnicho existente: seguir para cadastro do creator
- subnicho inexistente, mas nicho existente: solicitar criacao controlada de
  novo subnicho
- nicho inexistente: solicitar criacao controlada de novo nicho e subnicho
- classificacao ambigua: bloquear o fluxo e pedir revisao manual

Metodo esperado para novos nichos:

- a UI deve oferecer uma acao de solicitacao de novo nicho/subnicho
- a criacao nao deve ser feita por SQL livre no Streamlit
- a implementacao futura deve usar RPC controlada ou um intake especifico para
  taxonomia
- enquanto esse metodo nao existir, novos nichos/subnichos devem continuar pelo
  procedimento manual documentado

### 3. Criar creator

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
- o creator tambem deve aguardar a classificacao de nicho/subnicho estar
  resolvida ou explicitamente marcada para revisao
- a primeira implementacao pode manter esses campos apenas na interface ou em
  uma tabela de intake propria futura, porque `public.entity_intake` atual nao
  possui colunas para `platform`, `username`, `channel_id` e `followers`

## Estados da sub-view

### Rascunho

Uso:

- formulario preenchido, ainda nao enviado
- pode conter dados de entity, nicho/subnicho e canal

Acao:

- validar campos obrigatorios localmente
- sugerir possiveis entities existentes antes de permitir nova criacao

### Enviado para intake

Uso:

- registro criado em `public.entity_intake`

Acao:

- exibir o registro na revisao baseada em `public.v_entity_intake_review`

### Entity resolvida

Uso:

- `review_result = READY_TO_INSERT`
- ou entity ja existente com `existing_entity_id` preenchido
- ou entity ja publicada e localizada em `public.entities`

Acao:

- permitir publicacao controlada via `public.publish_entity_intake()`
- depois reconsultar a view de revisao

### Nicho/subnicho resolvido

Uso:

- `sub_niche_id` resolvido
- ou solicitacao de novo nicho/subnicho registrada para revisao

Acao:

- liberar cadastro do creator quando a classificacao estiver confirmada
- manter bloqueado quando a classificacao estiver ambigua

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

RPC futura para taxonomia:

```text
public.create_taxonomy_intake_entry(
  p_niche text,
  p_sub_niche_name text,
  p_reason text,
  p_notes text
)
```

Comportamento esperado:

- registrar solicitacao de novo nicho/subnicho
- validar duplicidade por nome normalizado
- nao publicar automaticamente classificacoes novas
- permitir revisao antes de uso analitico

## Lacuna atual: cadastro em `public.creators`

O procedimento documentado hoje cobre bem a criacao de `entities` e vinculos de
`entity_sub_niches`, mas nao fecha sozinho o cadastro de uma linha em
`public.creators`.

Como `public.creators` exige `entity_id`, `platform` e `channel_id`, a sub-view
deve tratar isso como etapa final da jornada de inclusao.

Regra recomendada:

- nao criar creator enquanto `entity_id` nao estiver resolvido
- nao criar creator enquanto nicho/subnicho estiver inexistente ou ambiguo
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

- busca/criacao de entity
- resolucao/criacao de nicho e subnicho
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
2. Criar a etapa de busca de entity existente.
3. Criar a etapa de solicitacao de nova entity via `public.entity_intake`,
   sem escrita direta em tabelas finais.
4. Conectar a leitura de `public.v_entity_intake_review`.
5. Criar a etapa de resolucao de nicho/subnicho existente.
6. Definir o metodo controlado para solicitacao de novos nichos/subnichos.
7. Definir ou criar RPC separada para cadastrar `public.creators` apenas quando
   `entity_id` e classificacao estiverem resolvidos.
8. Validar o fluxo completo com um creator de teste.
9. Documentar o resultado no pipeline status antes de considerar a tela pronta.

## Validacoes obrigatorias

Antes de considerar a sub-view pronta:

- confirmar que `raw_name` nao gera duplicidade inesperada em `entities`
- confirmar que `sub_niche_name` encontra `sub_niche_id`
- confirmar que novos nichos/subnichos possuem metodo de intake ou procedimento
  manual documentado
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
- criar nicho/subnicho direto pela UI sem revisao pode degradar a taxonomia

## Decisao recomendada

Implementar a tela em quatro etapas guiadas:

1. Busca ou intake de entity usando o fluxo existente.
2. Resolucao ou solicitacao controlada de nicho/subnicho.
3. Cadastro de creator em `public.creators` somente depois de `entity_id` e
   classificacao resolvidos.
4. Confirmacao de entrada do creator no fluxo normal de discovery/coleta.

Essa separacao preserva a governanca ja documentada, respeita o fluxo manual
atual e transforma a UI em uma camada guiada de operacao, nao em uma porta de
escrita direta nas tabelas finais.
