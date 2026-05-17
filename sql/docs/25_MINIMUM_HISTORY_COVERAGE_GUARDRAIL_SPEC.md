# MINIMUM HISTORY COVERAGE GUARDRAIL SPEC

## Objetivo

Definir uma estrutura permanente para impedir que posts fiquem perdidos por
falta de historico.

Depois do encerramento da fase 1 do backfill de `legacy_low`, o problema deixa
de ser apenas corrigir uma divida historica. A partir de agora, o sistema
precisa prevenir que novos posts envelhecam sem cobertura minima.

Esta especificacao define a politica de cobertura minima de historico.

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

## Estados de cobertura

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

## Fluxo operacional

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

### `bootstrap_low`

Acao:

- entrar em rotina de bootstrap normal
- receber snapshots iniciais de forma controlada

Objetivo:

- construir historico antes de virar risco

---

### `at_risk_bootstrap`

Acao:

- ter prioridade sobre `bootstrap_low` comum
- ser processado antes de cruzar a janela de `7 dias`

Objetivo:

- evitar que vire `recovery_low`

---

### `recovery_low`

Acao:

- entrar em fila de recuperacao
- ser tratado como alerta de cobertura

Objetivo:

- impedir recriacao de backlog legado

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
- separar falta normal de historico de falha operacional
- evitar olhar apenas `history_level = low`, que mistura causas diferentes

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

- `recovery_low = 0` ou residual muito baixo
- `at_risk_bootstrap` baixo e sem crescimento persistente
- `bootstrap_low` existe, mas nao envelhece sem snapshots

Alerta:

- qualquer crescimento recorrente de `recovery_low`
- `at_risk_bootstrap` acumulando semana contra semana
- posts com `0` ou `1` checagem chegando perto de `7` dias

Acao esperada em caso de alerta:

- revisar o bootstrap de novos posts
- executar rotina corretiva apenas para `recovery_low`
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

- `legacy_low` residual deve ser tratado como alerta, nao como backlog normal
- `bootstrap_low` precisa de rotina propria
- `at_risk_bootstrap` deve ser priorizado antes de virar recuperacao
- nenhuma automacao nova deve ser considerada saudavel sem logs e consulta de
  cobertura minima

---

## Status

Esta especificacao define a logica de prevencao.

Ainda falta implementar:

- view SQL de monitoramento de cobertura minima
- rotina de bootstrap para novos posts
- eventual rotina de recuperacao para `recovery_low`
