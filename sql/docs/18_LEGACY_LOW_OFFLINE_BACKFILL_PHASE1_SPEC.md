# LEGACY LOW OFFLINE BACKFILL PHASE 1 SPECIFICATION

## Objetivo

Definir a implementacao da fase 1 do backfill offline para posts `legacy_low`.

Nesta fase, o objetivo e:

- inserir 1 snapshot inicial para posts antigos com historico insuficiente
- reduzir o numero de posts completamente cegos
- preparar a base para que coletas futuras permitam transicao de `low` para `partial`

---

## Escopo desta fase

Esta fase trata apenas:

- posts `legacy_low`
- 1 coleta offline por post

Esta fase nao tenta:

- tirar imediatamente o post de `low`
- construir velocity completa
- resolver bootstrap de posts novos

---

## Premissa operacional

Os dados atuais indicam:

- `511` posts `legacy_low`
- `204` posts `bootstrap_low`

O foco desta especificacao e apenas o conjunto `legacy_low`.

---

## Regra de elegibilidade

Um post entra na fase 1 do backfill quando:

- `created_at < now() - interval '7 days'`
- `total_checagens <= 1`

Interpretacao:

- o post nao e novo
- o post esta subobservado
- o caso representa divida historica, nao cold start

---

## Regra de priorizacao

Nao usar prioridade por banda.

O lote deve ser ordenado apenas por:

- `priority_score_v2 desc`

Desempates sugeridos:

1. `total_checagens asc`
2. `collected_at asc nulls first`
3. `post_id`

Motivo:

- simplifica a implementacao
- usa diretamente a nova logica analitica do modelo `v2`
- evita adicionar outra camada de regra antes de validar o score

### Implicacao operacional

Nesta fase, a fila offline de backfill nao tenta reproduzir o comportamento da
`v_post_update_queue_batch`.

Ela usa apenas:

- `priority_score_v2` para ordenar os `legacy_low`
- desempates simples para garantir determinismo

Isso significa que:

- a prioridade vem do score analitico do `v2`
- nao existe cota por banda
- nao existe refill por banda
- o objetivo e corrigir historico legado, nao simular a fila online

---

## Tamanho do lote

Tamanho inicial sugerido:

- `50` posts por execucao

Justificativa:

- com `511` posts `legacy_low`, isso gera aproximadamente `11` lotes
- mantem o volume operacional controlado
- facilita observacao de tempo de execucao e comportamento do banco

---

## Fluxo do script

```text
1. Selecionar lote de legacy_low
2. Ordenar por priority_score_v2 desc
3. Chamar YouTube API para os post_ids do lote
4. Normalizar resposta
5. Inserir snapshots em post_metrics_history
6. Deixar triggers atualizarem posts e post_update_queue
7. Registrar logs da execucao
```

---

## Query de selecao do lote

Referencia conceitual:

```sql
select
  p.post_id,
  p.created_at,
  p.collected_at,
  coalesce(h.total_checagens, 0) as total_checagens,
  f.priority_score_v2,
  f.priority_band_v2,
  f.history_level
from posts p
left join (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) h on h.post_id = p.post_id
join public.v_post_priority_score_features_v2 f
  on f.post_id = p.post_id
where p.created_at < now() - interval '7 days'
  and coalesce(h.total_checagens, 0) <= 1
order by
  f.priority_score_v2 desc,
  coalesce(h.total_checagens, 0) asc,
  p.collected_at asc nulls first,
  p.post_id
limit 50;
```

---

## Chamada da YouTube API

O script deve seguir o mesmo principio operacional do pipeline atual:

- usar `videos.list`
- `part=statistics`
- enviar multiplos `post_id` em uma unica chamada

Objetivo:

- minimizar numero de requests HTTP
- manter o custo sob controle

---

## Persistencia

O script deve inserir em:

- `post_metrics_history`

Campos minimos:

- `post_id`
- `views`
- `likes`
- `comments`
- `collected_at`

O script nao deve:

- atualizar `posts` diretamente
- atualizar `post_update_queue` diretamente

Essas atualizacoes devem continuar sendo feitas pelos triggers do banco.

---

## Logs recomendados

Cada execucao deve registrar:

- quantidade de posts selecionados
- quantidade de posts retornados pela YouTube API
- quantidade de inserts realizados
- post_ids com falha
- duracao total

Campos uteis para log:

- `batch_id`
- `started_at`
- `finished_at`
- `selected_posts`
- `api_returned_posts`
- `inserted_posts`
- `failed_posts`

---

## Criterios de sucesso da fase 1

- os posts `legacy_low` recebem ao menos 1 snapshot
- a quantidade de posts sem historico diminui
- o script roda sem interferir no pipeline principal
- o tempo por lote permanece aceitavel

---

## Validacoes recomendadas

### 1. Quantos `legacy_low` ainda restam

```sql
select
  count(*) as total_legacy_low
from posts p
left join (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) h on h.post_id = p.post_id
where p.created_at < now() - interval '7 days'
  and coalesce(h.total_checagens, 0) <= 1;
```

### 2. Quantos posts ganharam seu primeiro snapshot

```sql
select
  count(*) as posts_com_1_snapshot
from (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) h
where h.total_checagens = 1;
```

### 3. Quantos posts seedados podem migrar no futuro para `partial`

```sql
select
  history_level,
  count(*) as total_posts
from public.v_post_priority_score_features_v2
group by history_level
order by history_level;
```

---

## O que esperar apos a fase 1

Resultado esperado:

- os posts ainda podem continuar `low` imediatamente
- mas deixarao de estar completamente sem base historica
- ficarao prontos para futura promocao de estado

Interpretacao correta:

- fase 1 prepara
- fase 2 promove

---

## Proxima etapa

Depois da fase 1:

- definir a fase 2 de promocao de estado
- decidir se a segunda coleta vira script offline complementar ou se sera absorvida por outra rotina

---

## Status

Esta especificacao descreve a implementacao da fase 1 do backfill offline para `legacy_low`.

Ainda nao representa script implementado.
