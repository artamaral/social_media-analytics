# MINIMUM HISTORY COVERAGE GUARDRAIL SPEC

## Objetivo

Definir uma estrutura permanente para impedir que posts fiquem perdidos por
falta de historico.

Depois do encerramento da fase 1 do backfill de `legacy_low`, o problema deixa
de ser apenas corrigir uma divida historica. A partir de agora, o sistema
precisa prevenir que novos posts envelhecam sem cobertura minima.

Esta especificacao define a politica de cobertura minima de historico.

Regra operacional simplificada:

```text
todo post com menos de 3 checagens entra no guardrail
```

Os nomes `bootstrap_low`, `at_risk_bootstrap` e `recovery_low` continuam uteis
para diagnostico, mas nao devem tornar a implementacao principal mais complexa.

---

## Problema

Todo post novo nasce com pouco ou nenhum historico.

Isso e esperado.

O problema aparece quando esse post:

- entra como `bootstrap_low`
- nao recebe snapshots suficientes
- envelhece alem da janela de cold start
- passa a ser `legacy_low`

Nesse caso, `legacy_low` deixa de ser apenas um problema legado e passa a ser
um indicador de falha de cobertura do pipeline.

---

## Principio operacional

Todo post deve atingir um minimo de historico antes de sair da janela de
bootstrap.

Regra conceitual:

```text
post novo
  -> deve receber cobertura minima
  -> antes de envelhecer
  -> para nao virar legacy_low
```

---

## Meta minima de cobertura

Meta inicial:

- todo post deve chegar a pelo menos `3` snapshots

Motivo:

- `0` snapshots: post invisivel para crescimento
- `1` snapshot: existe base, mas nao existe delta
- `2` snapshots: comeca a existir comparacao temporal
- `3` snapshots: melhora a leitura de trajetoria e reduz risco de falso sinal

Esta meta pode ser recalibrada, mas `3` snapshots e o alvo operacional inicial.

---

## Regra operacional simplificada

A implementacao principal do guardrail deve depender de uma regra simples:

```sql
total_checagens < 3
```

Todo post que ainda nao atingiu `3` snapshots deve disputar a fatia reservada
do guardrail.

Ordenacao recomendada:

```sql
order by
  total_checagens asc,
  created_at asc,
  priority_score desc nulls last,
  post_id
```

Interpretacao:

- primeiro entram posts com menos contexto
- dentro do mesmo nivel de contexto, entram os mais antigos
- `priority_score` atua apenas como desempate de valor

---

## Estados de cobertura para diagnostico

Os estados abaixo existem para leitura e monitoramento.

Eles nao devem ser a regra principal de implementacao do guardrail.

### 1. `bootstrap_low`

Definicao:

- post novo
- ainda dentro da janela de bootstrap
- historico insuficiente

Regra inicial:

```sql
created_at >= now() - interval '7 days'
and total_checagens < 3
```

Interpretacao:

- estado normal de cold start
- precisa de observacao inicial
- nao deve ser tratado como falha ainda

---

### 2. `at_risk_bootstrap`

Definicao:

- post ainda novo
- mas perto de sair da janela de bootstrap
- ainda sem cobertura minima

Regra inicial sugerida:

```sql
created_at < now() - interval '5 days'
and created_at >= now() - interval '7 days'
and total_checagens < 3
```

Interpretacao:

- este post esta em risco de virar `legacy_low`
- deve receber prioridade operacional antes de cruzar `7 dias`

---

### 3. `recovery_low`

Definicao:

- post ja antigo
- nao atingiu cobertura minima
- representa falha de cobertura recente

Regra inicial:

```sql
created_at < now() - interval '7 days'
and total_checagens < 3
```

Interpretacao:

- este estado substitui o uso informal de `legacy_low` como backlog permanente
- depois da limpeza historica, qualquer crescimento de `recovery_low` deve ser
  tratado como alerta operacional

---

### 4. `covered`

Definicao:

- post com cobertura minima

Regra inicial:

```sql
total_checagens >= 3
```

Interpretacao:

- o post pode seguir o fluxo normal de priorizacao e analise
- ainda pode precisar de novas coletas, mas nao esta perdido por falta de base

---

## Fluxo operacional simplificado

```text
posts
  -> total_checagens < 3?
     -> sim:
        entra na fatia guardrail
     -> nao:
        segue fila normal por priority_band
```

## Fluxo de cleanup temporario

```text
posts elegiveis para cleanup
  -> video_age_bucket em warm_8_30d ou old_30d_plus?
     -> sim:
        limpar ate total_checagens >= 3
     -> nao:
        video_age_bucket em new_0_3d ou recent_4_7d
        limpar ate total_checagens >= 2
        terceira checagem fica para o guardrail permanente
```

Para diagnostico, a leitura pode continuar separando `bootstrap_low`,
`at_risk_bootstrap` e `recovery_low`:

```text
posts
  -> total_checagens >= 3?
     -> sim:
        covered
     -> nao:
        -> created_at >= now() - 7 dias?
           -> sim:
              -> created_at < now() - 5 dias?
                 -> sim:
                    at_risk_bootstrap
                 -> nao:
                    bootstrap_low
           -> nao:
              recovery_low
```

---

## Politica de acao

A politica de acao deve ser unica:

- reservar uma fatia fixa do lote para posts com `total_checagens < 3`
- usar `total_checagens asc` como primeira prioridade
- usar `next_check asc` como segunda prioridade para drenar vencidos
- usar `created_at asc` como terceira prioridade
- usar `priority_score desc` apenas como desempate

Configuracao inicial recomendada:

- lote total do worker: `50`
- fatia guardrail: `6`
- fatia normal por bandas: `44`
- guardrail excedente pode disputar o refill global quando continuar vencido

Motivo:

- a media observada de posts novos e aproximadamente `27` por dia
- cada post precisa de `3` checagens para sair do guardrail
- `6` slots por hora geram ate `144` checagens por dia, assumindo execucao
  horaria do worker
- isso aumenta a margem do guardrail sem consumir capacidade demais da fila
  normal
- o lote total fica em `50`, ainda dentro de uma unica chamada
  `videos.list`

---

## Cleanup temporario da divida de guardrail

A politica permanente de `6` slots protegidos por execucao e suficiente para
operacao normal, mas nao e adequada para limpar rapidamente uma divida acumulada
grande sozinha. Por isso, guardrail excedente tambem pode disputar o refill
global quando continuar vencido.

Quando houver muitos posts antigos com `total_checagens < 3`, deve ser usada
uma rotina offline temporaria de cleanup. A rotina nao precisa levar todos os
posts novos ate `3`; a terceira checagem de novos e recentes deve ser absorvida
pelo guardrail permanente.

Regra de selecao do cleanup:

```text
needs_update = true
status != unavailable
warm_8_30d ou old_30d_plus: total_checagens < 3
new_0_3d ou recent_4_7d: total_checagens < 2
```

Ordem operacional:

```text
1. warm_8_30d e old_30d_plus primeiro
2. total_checagens asc
3. post_date asc
4. priority_score desc
5. post_id
```

Interpretacao:

- posts `warm_8_30d` e `old_30d_plus` sao limpos ate `3` checagens
- posts `new_0_3d` e `recent_4_7d` sao limpos apenas ate `2` checagens
- a terceira checagem dos novos e recentes fica para o guardrail permanente
- dentro de cada grupo, os menos observados entram primeiro
- dentro de cada camada, os videos mais velhos entram primeiro

Esta regra evita que a divida antiga continue ocupando a fatia permanente do
guardrail e libera capacidade para posts novos em janela de crescimento.

Importante:

- `history_level` nao deve ser usado como criterio de cleanup
- `priority_score_v2` nao deve ser usado como criterio de cleanup
- `priority_score` atual serve apenas como desempate
- videos confirmados como `unavailable` devem ser excluidos

### Baseline do cleanup - 2026-05-19 17h

Este baseline registra o estado inicial antes de avaliar a evolucao do
scheduler `guardrail-cleanup-backfill`.

Query usada para gerar o baseline:

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from public.post_metrics_history
  group by post_id
),
classified as (
  select
    p.post_id,
    case
      when p.post_date >= now() - interval '3 days' then 'new_0_3d'
      when p.post_date >= now() - interval '7 days' then 'recent_4_7d'
      when p.post_date >= now() - interval '30 days' then 'warm_8_30d'
      else 'old_30d_plus'
    end as video_age_bucket,
    coalesce(c.total_checagens, 0) as total_checagens
  from public.posts p
  join public.post_update_queue q
    on q.post_id = p.post_id
  left join checks c
    on c.post_id = p.post_id
  left join public.post_collection_failures f
    on f.post_id = p.post_id
  where q.needs_update = true
    and coalesce(f.status, 'active') <> 'unavailable'
    and (
      (
        p.post_date < now() - interval '7 days'
        and coalesce(c.total_checagens, 0) < 3
      )
      or (
        p.post_date >= now() - interval '7 days'
        and coalesce(c.total_checagens, 0) < 2
      )
    )
)
select
  video_age_bucket,
  total_checagens,
  count(*) as total_posts
from classified
group by 1, 2
order by
  case video_age_bucket
    when 'new_0_3d' then 1
    when 'recent_4_7d' then 2
    when 'warm_8_30d' then 3
    else 4
  end,
  total_checagens;
```

| video_age_bucket | total_checagens | total_posts |
| --- | ---: | ---: |
| new_0_3d | 0 | 41 |
| recent_4_7d | 0 | 75 |
| recent_4_7d | 1 | 43 |
| warm_8_30d | 2 | 548 |
| old_30d_plus | 1 | 1 |
| old_30d_plus | 2 | 806 |

Leitura:

- warm e old ainda concentram a maior divida operacional do guardrail
- `old_30d_plus` tem `807` posts abaixo da meta de `3` checagens
- `warm_8_30d` tem `548` posts abaixo da meta de `3` checagens
- novos e recentes ainda possuem `116` posts com `0` checagens
- recentes possuem mais `43` posts com apenas `1` checagem

Meta de curto prazo:

- reduzir `warm_8_30d` e `old_30d_plus` abaixo de `3` checagens para zero
- reduzir `new_0_3d` e `recent_4_7d` abaixo de `2` checagens para zero
- depois disso, pausar o cleanup offline e deixar o guardrail permanente
  completar a terceira checagem dos novos e recentes

### Resultado parcial apos cleanup - 2026-05-19

O scheduler `guardrail-cleanup-backfill` foi pausado pelo usuario apos reduzir
o backlog operacional a um residual pequeno.

| video_age_bucket | total_checagens | total_posts |
| --- | ---: | ---: |
| warm_8_30d | 2 | 6 |
| old_30d_plus | 1 | 1 |
| old_30d_plus | 2 | 2 |

Leitura:

- restam `9` posts no alvo do cleanup temporario
- se todos estiverem vivos, faltariam `10` coletas para cumprir a meta
  temporaria
- `4` dos `9` posts ja constam na lista de possiveis dead posts, mas ainda
  aparecem com baixa cobertura
- posts confirmados manualmente como dead/unavailable continuam aparecendo em
  outras metricas; isso indica que a exclusao por status precisa ser
  padronizada fora da fila ativa

Decisao operacional:

- manter o scheduler pausado ate auditar os `9` residuos
- confirmar manualmente possiveis dead posts e marcar `status = 'unavailable'`
  quando aplicavel
- antes de considerar o guardrail limpo, ajustar metricas e views operacionais
  para excluir posts confirmados como `unavailable`

---

## Query de monitoramento diario

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
),
classified as (
  select
    p.post_id,
    p.created_at,
    coalesce(c.total_checagens, 0) as total_checagens,
    case
      when coalesce(c.total_checagens, 0) >= 3 then 'covered'
      when p.created_at < now() - interval '7 days' then 'recovery_low'
      when p.created_at < now() - interval '5 days' then 'at_risk_bootstrap'
      else 'bootstrap_low'
    end as coverage_status
  from posts p
  left join checks c
    on c.post_id = p.post_id
)
select
  coverage_status,
  total_checagens,
  count(*) as total_posts
from classified
group by 1, 2
order by 1, 2;
```

Uso:

- acompanhar diariamente
- monitorar o tamanho total do guardrail
- separar diagnostico de cold start e falha operacional quando necessario
- evitar olhar apenas `history_level = low`, que mistura causas diferentes

---

## Query operacional do guardrail

Esta e a query conceitual da fatia guardrail.

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
)
select
  p.post_id,
  p.created_at,
  p.collected_at,
  coalesce(c.total_checagens, 0) as total_checagens,
  q.priority_score,
  public.calculate_priority_band(q.priority_score) as priority_band
from posts p
left join checks c
  on c.post_id = p.post_id
left join post_update_queue q
  on q.post_id = p.post_id
where coalesce(c.total_checagens, 0) < 3
order by
  coalesce(c.total_checagens, 0) asc,
  p.created_at asc,
  q.priority_score desc nulls last,
  p.post_id
limit 4;
```

Uso:

- selecionar a fatia minima de cobertura
- garantir que posts com menos de `3` checagens nao fiquem presos atras da
  priorizacao normal por banda

---

## Query de alerta para recuperacao

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
)
select
  p.post_id,
  p.created_at,
  p.collected_at,
  coalesce(c.total_checagens, 0) as total_checagens
from posts p
left join checks c
  on c.post_id = p.post_id
where p.created_at < now() - interval '7 days'
  and coalesce(c.total_checagens, 0) < 3
order by
  coalesce(c.total_checagens, 0) asc,
  p.created_at asc,
  p.post_id;
```

Uso:

- listar posts que ja viraram `recovery_low`
- essa lista deve ser pequena apos o encerramento da fase 1
- crescimento dessa lista indica falha da politica de bootstrap

---

## Metodo semanal de checagem para `legacy_low`

Depois da fase 1, `legacy_low` deixa de ser um backlog esperado.

A checagem semanal deve confirmar se algum post novo envelheceu sem atingir a
cobertura minima de `3` snapshots.

Para fins operacionais, a checagem usa o nome `recovery_low`, mas ela responde
a pergunta pratica:

```text
existe algum post que virou legacy_low novamente?
```

### Query semanal resumida

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
),
coverage as (
  select
    p.post_id,
    p.created_at,
    p.collected_at,
    coalesce(c.total_checagens, 0) as total_checagens,
    case
      when coalesce(c.total_checagens, 0) >= 3 then 'covered'
      when p.created_at < now() - interval '7 days' then 'recovery_low'
      when p.created_at < now() - interval '5 days' then 'at_risk_bootstrap'
      else 'bootstrap_low'
    end as coverage_status
  from posts p
  left join checks c
    on c.post_id = p.post_id
)
select
  coverage_status,
  total_checagens,
  count(*) as total_posts
from coverage
group by 1, 2
order by 1, 2;
```

### Query semanal de detalhe

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
)
select
  p.post_id,
  p.created_at,
  p.collected_at,
  coalesce(c.total_checagens, 0) as total_checagens
from posts p
left join checks c
  on c.post_id = p.post_id
where p.created_at < now() - interval '7 days'
  and coalesce(c.total_checagens, 0) < 3
order by
  coalesce(c.total_checagens, 0) asc,
  p.created_at asc,
  p.post_id;
```

### Criterio de leitura semanal

Saudavel:

- total de posts com `total_checagens < 3` controlado
- `recovery_low = 0` ou residual muito baixo
- posts com `0` e `1` checagem nao acumulam

Alerta:

- total do guardrail cresce semana contra semana
- qualquer crescimento recorrente de `recovery_low`
- posts com `0` ou `1` checagem chegando perto de `7` dias

Acao esperada em caso de alerta:

- revisar a fatia guardrail
- subir temporariamente a fatia de `4` para `6` se houver acumulacao
- executar rotina corretiva se houver `recovery_low`
- registrar o resultado em `04_PIPELINE_STATUS.md`

---

## Indicadores de saude

### Saudavel

- `recovery_low` proximo de zero
- `at_risk_bootstrap` baixo e em queda
- `bootstrap_low` existe, mas avanca para `covered`
- posts novos chegam a `3` snapshots antes de `7 dias`

### Alerta

- `recovery_low` cresce
- `at_risk_bootstrap` acumula
- `bootstrap_low` fica estagnado em `0` ou `1` checagem
- `history_level = low` cresce sem explicacao por novos posts

---

## Relacao com documentos existentes

### Score hibrido `v2`

O guardrail e independente do score hibrido `v2`.

Estado atual:

- guardrail faz parte da fila ativa
- `v2` continua em modo analitico
- os slots normais da fila ativa ainda usam o `priority_score` atual

Desenho alvo futuro, se o `v2` for aprovado:

- `6` slots guardrail por `total_checagens < 3`
- `44` slots normais por score `v2` recalibrado

Regra:

- a promocao do `v2` nao deve remover nem enfraquecer o guardrail

---

### Documento 15

`15_LOW_HISTORY_BOOTSTRAP_AND_BACKFILL_SPEC.md` separa conceitualmente:

- `bootstrap_low`
- `legacy_low`

Esta especificacao complementa esse documento criando a politica permanente
para impedir que `bootstrap_low` vire `legacy_low`.

### Documento 17 e 18

`17_LEGACY_LOW_OFFLINE_BACKFILL_SPEC.md` e
`18_LEGACY_LOW_OFFLINE_BACKFILL_PHASE1_SPEC.md` tratam da correcao do backlog
legado.

Esta especificacao trata da prevencao continua.

### Documento 24

`24_PHASE2_INITIAL_DATA_BASELINE_2026-05-17.md` registra o baseline da fase 2 e
mostra que o `low` remanescente passou a ser principalmente `bootstrap_low`.

Esta especificacao define como esse `bootstrap_low` deve ser monitorado daqui
em diante.

---

## Decisao operacional

A partir do encerramento da fase 1:

- qualquer post com menos de `3` checagens entra no guardrail
- `legacy_low` residual deve ser tratado como alerta, nao como backlog normal
- `bootstrap_low`, `at_risk_bootstrap` e `recovery_low` sao diagnosticos, nao
  regras principais de implementacao
- nenhuma automacao nova deve ser considerada saudavel sem logs e consulta de
  cobertura minima

---

## Status

Esta especificacao define a logica de prevencao e a primeira implementacao na
fila ativa.

Implementado:

- fatia guardrail de ate `6` slots dentro de `public.v_post_update_queue_batch`
- regra operacional `total_checagens < 3`
- ordenacao da fatia guardrail por:
  - `total_checagens asc`
  - `next_check asc`
  - `created_at asc`
  - `priority_score desc`
- preenchimento do restante do lote com a fila normal por bandas e refill
  global, incluindo guardrail excedente vencido

Ainda falta implementar:

- view SQL de monitoramento de cobertura minima
- monitoramento semanal do volume com `total_checagens < 3`
