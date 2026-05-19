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

## Atualizacao operacional - guardrail cleanup

Depois da avaliacao do backlog de guardrail, a rotina offline deixa de ser
tratada como um backfill exclusivo de `legacy_low`.

A partir desta decisao, o objetivo operacional e limpar a divida de cobertura
minima para que o guardrail consiga voltar a proteger posts novos em fase de
crescimento.

Regra simplificada:

```text
warm_8_30d e old_30d_plus -> limpar ate 3 checagens
new_0_3d e recent_4_7d -> limpar ate 2 checagens
```

O script ainda esta em `scripts/offline_backfill/legacy_low_backfill_phase1.py`
por continuidade operacional, mas a selecao ativa passa a ser de
`guardrail cleanup`.

## Regra de elegibilidade atual

Um post entra no cleanup quando:

- `needs_update = true`
- nao esta confirmado como `unavailable` em `post_collection_failures`
- `video_age_bucket in ('warm_8_30d', 'old_30d_plus')` e
  `total_checagens < 3`
- ou `video_age_bucket in ('new_0_3d', 'recent_4_7d')` e
  `total_checagens < 2`

Interpretacao:

- o post esta subobservado
- warm e old representam divida de cobertura minima que deve ser limpa ate `3`
- new e recent devem chegar ate `2` para nao ficarem invisiveis, mas a terceira
  checagem fica para o guardrail permanente
- `history_level` nao deve ser usado como criterio de elegibilidade

### Observacao de estrategia

Inicialmente a fase 1 foi pensada para atacar `legacy_low` e depois
`<= 2` checagens com apoio de `priority_score_v2`.

Com a observacao atual, a estrategia muda para uma limpeza por meta de idade:

1. limpar todos os `warm_8_30d` e `old_30d_plus` ate `3` checagens
2. limpar `new_0_3d` e `recent_4_7d` ate `2` checagens
3. deixar o guardrail permanente completar a terceira checagem dos novos

Objetivo:

- limpar todos os posts muito antigos que ainda ocupam o guardrail
- garantir que nenhum post novo ou recente fique totalmente invisivel
- abrir espaco para o guardrail normal cuidar dos posts novos
- reduzir rapidamente a divida de cobertura minima

---

## Regra de priorizacao

Nao usar prioridade por banda.

Na estrategia operacional atual, o lote deve ser ordenado por:

1. `warm_8_30d` e `old_30d_plus` primeiro
2. `total_checagens asc`
3. `post_date asc`
4. `priority_score desc`
5. `post_id`

Motivo:

- o objetivo imediato e limpar todo warm e old ate `3` checagens
- new e recent devem chegar ate `2`, deixando a terceira para o guardrail
- `total_checagens` vem primeiro para limpar por camada
- `post_date` vem depois para atacar os videos mais velhos dentro da mesma camada
- `priority_score` e apenas desempate de valor
- `priority_score_v2` e `history_level` nao participam mais da selecao

### Implicacao operacional

Nesta fase, a fila offline de backfill nao tenta reproduzir o comportamento da
`v_post_update_queue_batch`.

Isso significa que:

- nao existe cota por banda
- nao existe refill por banda
- o objetivo e corrigir a divida de cobertura minima
- a prioridade principal e limpar divida warm/old ate `3`
- new/recent entram ate `2` para nao ficarem sem base inicial
- a idade do video decide quem entra primeiro dentro de cada camada

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
1. Selecionar lote de guardrail cleanup
2. Ordenar por bucket alvo, `total_checagens asc`, `post_date asc` e `priority_score desc`
3. Chamar YouTube API para os post_ids do lote
4. Normalizar resposta
5. Inserir snapshots em post_metrics_history
6. Deixar triggers atualizarem posts e post_update_queue
7. Registrar logs da execucao
```

### Mapeamento para o `postMetrics/main.py`

A implementacao do script offline deve, a principio, reaproveitar o mesmo
esqueleto funcional do arquivo
`scripts/cloud_run/postMetrics/main.py`.

Mapeamento esperado:

- `fetch_queue()`:
  - sera substituida por uma funcao de selecao do lote `legacy_low`
- `extract_ids()`:
  - deve ser reaproveitada sem mudanca, se possivel
- `fetch_youtube_stats()`:
  - deve ser reaproveitada sem mudanca, se possivel
- `normalize()`:
  - deve ser reaproveitada sem mudanca, se possivel
- `insert_history()`:
  - deve ser reaproveitada sem mudanca, se possivel
- `run_pipeline()`:
  - deve orquestrar o fluxo offline trocando apenas a origem dos `post_id`

Objetivo:

- reduzir divergencia entre pipeline online e script offline
- diminuir risco de comportamento inconsistente
- manter manutencao mais simples

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
  and coalesce(h.total_checagens, 0) <= 2
order by
  coalesce(h.total_checagens, 0) asc,
  f.priority_score_v2 desc,
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

Diretriz adicional:

- reaproveitar a mesma funcao `fetch_youtube_stats()` do `postMetrics/main.py`
  como referencia direta de implementacao

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

Diretriz adicional:

- reaproveitar a mesma funcao `insert_history()` do `postMetrics/main.py`
  como referencia direta de implementacao

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

- os posts `legacy_low` com `0`, `1` e `2` checagens recebem prioridade de reprocessamento
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
  and coalesce(h.total_checagens, 0) <= 2;
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

Atualizacao operacional em `2026-05-17`:

- a fase 1 foi considerada operacionalmente concluida
- o `legacy_low` residual observado caiu para `3`
- o scheduler pode ser pausado
- novas execucoes desta fase passam a ser apenas corretivas, se necessario

Proxima etapa:

- detalhar a fase 2 de promocao de estado
- tratar `bootstrap_low` como principal fonte remanescente de `low`
