# QUEUE SLICING AND RESCHEDULING

## Objetivo

Documentar a mudanca estrutural na fila de rechecagem de posts.

Esta alteracao:

- corrige um bug que impedia a atividade principal do projeto
- muda a politica geral de selecao da fila
- centraliza as regras de negocio no SQL

---

## Problema observado

A fila era consumida com a combinacao:

- `needs_update = true`
- `next_check <= now()`
- `order by priority_score desc`
- `limit 20`

Esse desenho gerava dois problemas:

1. posts antigos com `needs_update = false` deixavam de voltar para a fila
2. posts com maior `priority_score` dominavam continuamente os slots disponiveis

Na pratica, isso fazia com que:

- posts recentes tivessem apenas uma coleta
- faixas intermediarias de prioridade sofressem starvation
- o objetivo principal de checagem periodica nao fosse atingido

---

## Evidencias que levaram a mudanca

- analise de `post_metrics_history` mostrou posts recentes com apenas `1` coleta
- analise de `post_update_queue` mostrou itens antigos presos em `needs_update = false`
- histograma de `priority_score` mostrou uma cauda longa com poucos outliers muito altos
- simulacao por faixas mostrou que apenas mudar `next_check` nao resolveria a disputa pelos `20` slots

---

## Causa raiz

A causa raiz nao era apenas agendamento inadequado.

O problema central estava no criterio de selecao da fila:

- a ordenacao pura por `priority_score desc`
- combinada com `limit 20`
- sem nenhum mecanismo de distribuicao entre faixas

Com isso, os posts mais fortes podiam ocupar continuamente a fila, mesmo quando existiam outros posts elegiveis em faixas relevantes.

---

## Solucao adotada

Foi adotada uma solucao em SQL com tres partes:

1. manter a regra de prioridade no banco
2. recalcular o `next_check` no banco
3. fatiar a fila por bandas de prioridade antes da leitura pelo worker

O worker deixa de ler `post_update_queue` diretamente e passa a ler a view:

- `public.v_post_update_queue_batch`

Assim, a fila entregue para o worker ja chega balanceada.

---

## Nova arquitetura da fila

### Regras mantidas no SQL

- `calculate_post_priority(...)`
- `calculate_priority_band(...)`
- `calculate_next_check(...)`
- `refresh_post_queue_on_metrics()`

### Leitura do worker

O worker passa a consultar:

- `v_post_update_queue_batch`

em vez de:

- `post_update_queue` com `order by priority_score desc limit 20`

---

## Bandas de prioridade

Bandas adotadas:

- banda `6`: `700.000+`
- banda `5`: `300.000 - 699.999`
- banda `4`: `150.000 - 299.999`
- banda `3`: `50.000 - 149.999`
- banda `2`: `10.000 - 49.999`
- banda `1`: `0 - 9.999`

Motivo:

- refletir melhor a distribuicao real observada no histograma
- reduzir o poder excessivo dos outliers
- permitir cobertura de faixas intermediarias

---

## Cotas da fila por execucao

A view foi configurada para montar um batch de `20` itens por execucao com as seguintes cotas:

- banda `6`: `4`
- banda `5`: `4`
- banda `4`: `4`
- banda `3`: `3`
- banda `2`: `3`
- banda `1`: `2`

Se alguma banda nao tiver itens suficientes:

- os slots restantes sao preenchidos por outros itens elegiveis

Motivo:

- manter prioridade
- evitar starvation
- permitir que faixas intermediarias sejam rechecadas

---

## Nova regra de agendamento

Regra adotada em `calculate_next_check(...)`:

- `700.000+` -> `30 minutes`
- `300.000 - 699.999` -> `1 hour`
- `150.000 - 299.999` -> `2 hours`
- `50.000 - 149.999` -> `4 hours`
- `10.000 - 49.999` -> `8 hours`
- `0 - 9.999` -> `12 hours`

Motivo:

- aproximar a frequencia do comportamento real esperado
- tornar o topo da fila mais responsivo
- manter a regra simples e editavel no banco

---

## Impacto esperado

Com a mudanca, espera-se:

- rechecagem recorrente de posts recentes
- menos concentracao dos mesmos posts no topo
- maior cobertura das faixas intermediarias
- menor dependencia de regra de negocio no Python

---

## Validacao recomendada

Esta mudanca deve ser validada em conjunto com:

- [07_QUEUE_VALIDATION_CHECKLIST.md](C:/social_media-analytics/sql/docs/07_QUEUE_VALIDATION_CHECKLIST.md:1)
- [08_QUEUE_CAPACITY_TEST.md](C:/social_media-analytics/sql/docs/08_QUEUE_CAPACITY_TEST.md:1)

Pontos principais de validacao:

- posts recentes passarem a ter mais de uma coleta
- a view `v_post_update_queue_batch` retornar faixas variadas
- backlog nao crescer indefinidamente
- mesmos posts nao dominarem sempre todos os slots

---

## Riscos remanescentes

- se o volume de itens elegiveis exceder continuamente a capacidade do worker, ainda pode haver backlog
- cotas e bandas podem precisar ajuste com dados reais
- a reducao do starvation nao significa eliminacao total de backlog

---

## Diretriz futura

Qualquer mudanca futura em:

- bandas de prioridade
- cotas por banda
- regra de `next_check`
- limite de itens por execucao

deve atualizar este documento, o checklist de validacao e o teste de capacidade.
