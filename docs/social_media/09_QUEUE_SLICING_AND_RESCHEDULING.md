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

### Politica de ordenacao dentro da banda

O score continua definindo a banda do post.

Mas, dentro de cada banda, a ordenacao deixa de ser por maior score e passa a ser FIFO por antiguidade:

- primeiro por `next_check` mais antigo
- depois por `last_checked` mais antigo
- depois por `post_id` como desempate estavel

Motivo:

- evitar que poucos posts dominem continuamente a propria banda
- manter prioridade macro por relevancia
- aumentar a justica operacional dentro de cada faixa

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

A view foi configurada inicialmente para montar um batch de `20` itens por execucao com as seguintes cotas:

- banda `6`: `4`
- banda `5`: `4`
- banda `4`: `4`
- banda `3`: `3`
- banda `2`: `3`
- banda `1`: `2`

Em 2026-05-08, a capacidade do lote foi aumentada para `40` itens por execucao, mantendo a mesma proporcao entre bandas:

- banda `6`: `8`
- banda `5`: `8`
- banda `4`: `8`
- banda `3`: `6`
- banda `2`: `6`
- banda `1`: `4`

Em 2026-05-17, a view passou a reservar uma fatia de cobertura minima antes da
fila normal por bandas:

- guardrail: ate `4` posts com `total_checagens < 3`
- fila normal por bandas: ate `36` posts

As cotas nominais da fila normal passaram a ser:

- banda `6`: `7`
- banda `5`: `7`
- banda `4`: `7`
- banda `3`: `6`
- banda `2`: `5`
- banda `1`: `4`

Em 2026-05-21, o lote operacional foi aumentado para `50` itens por execucao,
com reforco moderado do guardrail:

- guardrail: ate `6` posts com `total_checagens < 3`
- fila normal por bandas: ate `44` posts

As cotas nominais da fila normal passaram a ser:

- banda `6`: `8`
- banda `5`: `8`
- banda `4`: `8`
- banda `3`: `7`
- banda `2`: `7`
- banda `1`: `6`

Motivo:

- impedir que posts com menos de `3` snapshots fiquem para tras
- preservar a maior parte do lote para a priorizacao normal por banda
- cobrir a media atual de novos posts sem consumir capacidade excessiva

Ordem da fatia guardrail:

- `total_checagens asc`
- `created_at asc`
- `priority_score desc`
- `post_id`

Se alguma banda nao tiver itens suficientes:

- os slots restantes sao preenchidos por outros itens elegiveis

Motivo:

- manter prioridade
- evitar starvation
- permitir que faixas intermediarias sejam rechecadas
- evitar concentracao excessiva dos maiores scores dentro da mesma banda

### Comportamento importante do refill

O refill atual nao funciona em cascata para a proxima banda mais alta.

Ou seja:

- se a banda `6` nao preencher sua cota
- os slots livres nao vao automaticamente para a banda `5`
- nem depois para a banda `4`

Em vez disso, o refill e feito sobre um pool global de itens elegiveis restantes, ordenado por:

- `next_check asc`
- `last_checked asc nulls first`
- `priority_band desc`
- `post_id`

Consequencia pratica:

- uma banda intermediaria pode receber slots excedentes se tiver itens mais antigos no refill global
- por isso, a distribuicao final do batch pode diferir da cota nominal por banda

Este comportamento esta implementado de forma intencional no SQL atual e deve ser acompanhado em producao antes de qualquer ajuste.

Observacao FinOps:

- a mudanca aumenta a quantidade de snapshots gravados por execucao
- a chamada `videos.list` deve continuar em uma unica requisicao enquanto o lote ficar ate `50` IDs
- a mudanca foi observada em producao por alguns dias e nao apresentou aumento relevante de custos no Cloud Run
- a validacao de custo do worker pode ser considerada satisfatoria
- para o lote `50`, a validacao deve ser repetida por alguns dias antes de
  considerar a configuracao definitiva; o risco esperado e baixo, mas o custo
  por snapshot e o volume de writes no Supabase devem ser acompanhados

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

### Regra por idade e cobertura - 2026-06-15

Analises operacionais posteriores mostraram que a regra acima ficou
excessivamente sensivel ao volume acumulado. Como `priority_score` e calculado
a partir de views, likes e comments acumulados, posts antigos muito grandes
continuam voltando com cadencia curta mesmo quando ja possuem centenas de
snapshots.

Evidencias observadas:

- posts `old_30d_plus`, `priority_band = 6`, com `777` a `940` checagens
  estavam sendo reagendados em `30 minutes`
- simulacao com `old_30d_plus` desacelerado removeu `289` posts do `due_now`
- simulacao com `warm_8_30d` ja coberto (`3+` checagens) desacelerado removeu
  `130` posts do `due_now`
- `warm_8_30d` com menos de `3` checagens nao deve ser desacelerado por essa
  regra, pois ja pertence a politica de guardrail/cobertura minima

Regra implementada:

```text
total_checagens < 3:
  manter politica atual e guardrail

new_0_3d e recent_4_7d:
  manter politica atual

warm_8_30d com total_checagens >= 3:
  priority_band 5 ou 6 -> minimo 12h
  priority_band 1 a 4 -> minimo 24h

old_30d_plus com total_checagens >= 3:
  priority_band 5 ou 6 -> minimo 12h
  priority_band 1 a 4 -> minimo 24h
```

Interpretacao:

- posts novos e recentes continuam responsivos
- posts sem cobertura minima continuam protegidos pelo guardrail
- posts `warm` e antigos ja cobertos deixam de competir com a mesma cadencia
  de posts em janela inicial de crescimento
- a regra continua simples o suficiente para operacao e auditoria

Implementacao:

- a funcao atual `calculate_next_check(priority_score, checked_at)` nao recebe
  `post_date` nem `total_checagens`
- por isso, foi criada uma sobrecarga de `calculate_next_check(...)` que recebe
  `post_date` e `total_checagens`
- o trigger deve buscar `posts.post_date` e o total historico de checagens antes
  de calcular o novo `next_check`
- a migration recalcula `next_check` de posts ja existentes em
  `post_update_queue` com `last_checked` preenchido
- migration de aplicacao:
  `sql/migrations/2026-06-15_004_queue_next_check_age_coverage_up.sql`
- migration de rollback:
  `sql/migrations/2026-06-15_004_queue_next_check_age_coverage_down.sql`

### Como `next_check` e definido

O campo `next_check` e controlado pelo banco, e nao pelo worker Python.

Fluxo:

1. no primeiro insert em `posts`, a funcao `add_to_queue()` cria o registro em `post_update_queue` com `next_check = now()`
2. isso torna o post novo elegivel para a primeira coleta
3. apos cada nova coleta em `post_metrics_history`, o trigger `refresh_post_queue_on_metrics()`:
   - recalcula `priority_score`
   - usa `collected_at` da nova coleta como base temporal
   - busca `post_date` em `posts`
   - conta o total historico de checagens do post
   - chama a sobrecarga `calculate_next_check(priority_score, collected_at, post_date, total_checagens)`
   - grava o novo `next_check` em `post_update_queue`

Consequencia pratica:

- o worker apenas insere historico em `post_metrics_history`
- toda a regra de agendamento da proxima checagem fica centralizada no SQL

---

## Impacto esperado

Com a mudanca, espera-se:

- rechecagem recorrente de posts recentes
- menos concentracao dos mesmos posts no topo
- maior cobertura das faixas intermediarias
- menor dependencia de regra de negocio no Python
- maior rotacao entre posts da mesma banda

---

## Validacao recomendada

Esta mudanca deve ser validada em conjunto com:

- [07_QUEUE_VALIDATION_CHECKLIST.md](C:/social_media-analytics/docs/social_media/07_QUEUE_VALIDATION_CHECKLIST.md:1)
- [08_QUEUE_CAPACITY_TEST.md](C:/social_media-analytics/docs/social_media/08_QUEUE_CAPACITY_TEST.md:1)

Pontos principais de validacao:

- posts recentes passarem a ter mais de uma coleta
- a view `v_post_update_queue_batch` retornar faixas variadas
- a ordem dentro da mesma banda refletir antiguidade de `next_check`
- a distribuicao final do batch ser lida considerando refill global, e nao cascata por banda
- backlog nao crescer indefinidamente
- mesmos posts nao dominarem sempre todos os slots
- custo do Cloud Run nao crescer de forma desproporcional
- quota do YouTube permanecer dentro de margem segura
- duracao media do Cloud Run e taxa de erro continuarem aceitaveis

### Indicador recomendado para Streamlit

Objetivo:

- acompanhar a idade real da ultima checagem por grupo de posts
- medir se a capacidade teorica esta chegando na base inteira
- identificar grupos com muitos posts acima de `3.2`, `5` ou `7` dias sem
  checagem
- manter contexto por banda de prioridade, idade do post e faixa de cobertura

View recomendada:

- `public.v_dashboard_queue_bottleneck_status`
- DDL: `sql/ddl/views/009_create_v_dashboard_queue_bottleneck_status.sql`

Query base da view:

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens,
    max(collected_at) as last_snapshot_at
  from public.post_metrics_history
  group by post_id
),
current_batch as (
  select post_id
  from public.v_post_update_queue_batch
),
classified as (
  select
    p.post_id,
    p.post_date,
    q.priority_score,
    public.calculate_priority_band(q.priority_score) as priority_band,
    q.last_checked,
    q.next_check,
    coalesce(c.total_checagens, 0) as total_checagens,
    coalesce(c.last_snapshot_at, q.last_checked::timestamp, p.created_at) as effective_last_check,
    extract(
      epoch from (
        now()::timestamp - coalesce(c.last_snapshot_at, q.last_checked::timestamp, p.created_at)
      )
    ) / 86400 as staleness_days,
    case
      when b.post_id is not null then true
      else false
    end as in_current_batch,
    case
      when q.next_check <= now()::timestamp then true
      else false
    end as is_due_now,
    case
      when p.post_date >= now()::timestamp - interval '3 days' then 'new_0_3d'
      when p.post_date >= now()::timestamp - interval '7 days' then 'recent_4_7d'
      when p.post_date >= now()::timestamp - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket,
    case
      when coalesce(c.total_checagens, 0) < 3 then 'needs_coverage'
      when coalesce(c.total_checagens, 0) between 3 and 49 then 'covered_3_49'
      when coalesce(c.total_checagens, 0) between 50 and 199 then 'overchecked_50_199'
      when coalesce(c.total_checagens, 0) between 200 and 499 then 'overchecked_200_499'
      else 'overchecked_500_plus'
    end as check_band
  from public.post_update_queue q
  join public.posts p
    on p.post_id = q.post_id
  left join checks c
    on c.post_id = q.post_id
  left join current_batch b
    on b.post_id = q.post_id
  left join public.post_collection_failures f
    on f.post_id = q.post_id
  where q.needs_update = true
    and coalesce(f.status, 'active') <> 'unavailable'
)
select
  priority_band,
  video_age_bucket,
  check_band,
  count(*) as total_posts,
  round(avg(total_checagens)::numeric, 2) as media_checagens,
  max(total_checagens) as max_checagens,
  round(avg(staleness_days)::numeric, 2) as avg_staleness_days,
  round(
    (percentile_cont(0.5) within group (order by staleness_days))::numeric,
    2
  ) as p50_staleness_days,
  round(
    (percentile_cont(0.9) within group (order by staleness_days))::numeric,
    2
  ) as p90_staleness_days,
  round(
    (percentile_cont(0.95) within group (order by staleness_days))::numeric,
    2
  ) as p95_staleness_days,
  round(max(staleness_days)::numeric, 2) as max_staleness_days,
  count(*) filter (
    where staleness_days > 3.2
  ) as posts_acima_3_2d,
  count(*) filter (
    where staleness_days > 5
  ) as posts_acima_5d,
  count(*) filter (
    where staleness_days > 7
  ) as posts_acima_7d,
  count(*) filter (
    where is_due_now
  ) as posts_vencidos,
  count(*) filter (
    where in_current_batch
  ) as posts_no_batch_atual,
  min(effective_last_check) as oldest_effective_last_check,
  max(effective_last_check) as newest_effective_last_check,
  min(next_check) filter (
    where is_due_now
  ) as next_check_mais_atrasado
from classified
group by
  priority_band,
  video_age_bucket,
  check_band;
```

Leitura recomendada:

- `total_posts`: quantidade de posts no grupo
- `media_checagens`: media de snapshots historicos do grupo
- `avg_staleness_days`: media de dias desde a ultima checagem
- `p50_staleness_days`: mediana; metade dos posts esta abaixo/acima desse
  tempo sem checagem
- `p90_staleness_days`: 90% dos posts estao ate esse tempo sem checagem; os
  10% piores estao acima
- `p95_staleness_days`: 95% dos posts estao ate esse tempo sem checagem; os
  5% piores estao acima
- `max_staleness_days`: pior caso do grupo
- `posts_acima_3_2d`: posts acima da media teorica atual de rotacao completa
  da base (`3820 / 1200 ~= 3.2 dias`)
- `posts_acima_5d`: alerta intermediario de atraso
- `posts_acima_7d`: alerta forte de gargalo real
- `posts_vencidos`: posts cujo `next_check` ja venceu
- `posts_no_batch_atual`: posts do grupo que aparecem no lote atual de
  `v_post_update_queue_batch`
- `oldest_effective_last_check`: checagem mais antiga usada no calculo de
  staleness
- `next_check_mais_atrasado`: `next_check` mais antigo entre os posts vencidos

Indicadores principais para o dashboard:

- `posts_acima_3_2d`
- `posts_acima_5d`
- `posts_acima_7d`
- `p95_staleness_days`
- `max_staleness_days`
- `posts_no_batch_atual`

Meta operacional:

- `posts_acima_7d` deve ficar proximo de zero
- `p95_staleness_days` nao deve crescer semana contra semana
- se `posts_acima_3_2d` crescer muito, a capacidade media teorica nao esta
  chegando na base inteira

---

## Riscos remanescentes

- se o volume de itens elegiveis exceder continuamente a capacidade do worker, ainda pode haver backlog
- cotas e bandas podem precisar ajuste com dados reais
- a reducao do starvation nao significa eliminacao total de backlog
- o custo operacional pode migrar de Cloud Run para Supabase caso o volume de inserts em `post_metrics_history` cresca sem politica de retencao ou priorizacao

---

## Diretriz futura

Qualquer mudanca futura em:

- bandas de prioridade
- cotas por banda
- regra de `next_check`
- limite de itens por execucao

deve atualizar este documento, o checklist de validacao e o teste de capacidade.

