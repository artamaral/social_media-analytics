# HYBRID SCORE VALIDATION PLAN

## Objetivo

Definir um plano pratico para validar um modelo de score hibrido usando:

- SQL para extracao e comparacao
- Excel ou Pandas para analise detalhada

Este plano assume que:

- o modelo `v2` existe apenas como simulacao analitica
- nao ha segundo Cloud Run ativo
- a comparacao sera feita sobre os mesmos dados reais do banco

---

## Perguntas que a validacao deve responder

1. O modelo `v2` reduz a concentracao de checagens em poucos posts?
2. O modelo `v2` promove posts com poucas checagens, mas com potencial recente?
3. O modelo `v2` preserva prioridade para posts estruturalmente relevantes?
4. O lote `v2` fica mais distribuido por bandas ou perfis de crescimento?
5. O modelo `v2` melhora a cobertura sem perder coerencia operacional?

---

## Fontes de dados

### Banco de dados

- `posts`
- `post_metrics_history`
- `post_update_queue`
- `v_post_update_queue_batch`
- `v_post_update_queue_batch_v2` quando existir

### Ferramentas de analise

- SQL Editor do Supabase para extracao
- Excel para leitura visual rapida e filtros
- Pandas para consolidacao, cruzamento e graficos

---

## Etapa 1. Extracao SQL

### Dataset A. Lote atual

Objetivo:

- capturar os posts que o modelo atual escolheria

Query base:

```sql
select
  post_id,
  priority_band,
  priority_score,
  last_checked,
  next_check
from public.v_post_update_queue_batch;
```

### Dataset B. Lote `v2`

Objetivo:

- capturar os posts que o modelo novo escolheria

Query base:

```sql
select
  post_id,
  priority_band,
  priority_score,
  last_checked,
  next_check
from public.v_post_update_queue_batch_v2;
```

### Dataset C. Historico de checagens por post

Objetivo:

- medir concentracao de checagens

Query base:

```sql
select
  post_id,
  count(*) as total_checagens
from post_metrics_history
group by post_id;
```

### Dataset D. Snapshot completo de comparacao

Objetivo:

- cruzar score atual, historico e fila

Query base:

```sql
select
  p.post_id,
  p.views,
  p.likes,
  p.comments,
  p.collected_at,
  coalesce(h.total_checagens, 0) as total_checagens,
  q.priority_score as current_priority_score,
  q.last_checked,
  q.next_check,
  q.needs_update
from posts p
left join (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) h on h.post_id = p.post_id
left join post_update_queue q
  on q.post_id = p.post_id;
```

---

## Etapa 2. Analise em Excel

### Objetivo do Excel

Usar Excel para validacao visual rapida, sem depender de codigo.

### Abas sugeridas

1. `current_batch`
2. `v2_batch`
3. `checks_per_post`
4. `full_snapshot`
5. `comparison`

### Analises sugeridas

#### 1. Overlap entre lotes

Pergunta:

- quantos posts do lote atual tambem aparecem no lote `v2`?

Como fazer:

- usar `post_id` como chave
- marcar `in_current`
- marcar `in_v2`

#### 2. Novos posts promovidos pelo `v2`

Pergunta:

- quais posts entram no lote `v2` e nao estavam no lote atual?

Como fazer:

- filtro em `in_v2 = true` e `in_current = false`

#### 3. Concentacao de checagens

Pergunta:

- os posts promovidos pelo `v2` sao menos concentrados historicamente?

Como fazer:

- cruzar `total_checagens`
- comparar media e mediana entre:
  - lote atual
  - lote `v2`

#### 4. Distribuicao por banda

Pergunta:

- o `v2` muda a proporcao de bandas ou apenas troca posts dentro da mesma banda?

Como fazer:

- tabela dinamica por `priority_band`

#### 5. Perfil dos promovidos

Pergunta:

- o `v2` puxa posts com menos historico, mais crescimento ou ambos?

Como fazer:

- ordenar por `total_checagens`
- comparar score atual versus score `v2`

---

## Etapa 3. Analise em Pandas

### Objetivo do Pandas

Fazer comparacoes mais profundas e repetiveis.

### Arquivos sugeridos de entrada

- `current_batch.csv`
- `v2_batch.csv`
- `checks_per_post.csv`
- `full_snapshot.csv`

### Analises sugeridas

#### 1. Overlap percentual

Medir:

- `%` de posts iguais entre os dois lotes

#### 2. Media e mediana de checagens

Comparar entre:

- lote atual
- lote `v2`

#### 3. Distribuicao acumulada

Medir:

- quantos posts do lote estao em cada faixa de `total_checagens`

Faixas sugeridas:

- `0-2`
- `3-10`
- `11-50`
- `51+`

#### 4. Concentracao extrema

Comparar:

- quantos posts do lote atual estao no top 1 por cento de checagens
- quantos posts do lote `v2` estao no top 1 por cento de checagens

#### 5. Analise de candidatos ignorados

Pergunta:

- quais posts com score interessante continuam fora do lote?

### Graficos sugeridos

- histograma de `total_checagens`
- boxplot de `total_checagens` por lote
- barras por banda
- scatter de `priority_score` vs `total_checagens`

---

## Indicadores de decisao

### Indicadores principais

- overlap entre lote atual e lote `v2`
- media de `total_checagens` por lote
- mediana de `total_checagens` por lote
- quantidade de posts com `0-2` checagens promovidos pelo `v2`
- quantidade de posts muito hiper-checados ainda dominando o lote `v2`

### Sinais positivos

- menor media de checagens no lote `v2`
- maior diversidade de posts com baixa cobertura
- preservacao de posts relevantes no lote

### Sinais de alerta

- `v2` substitui posts relevantes por ruido
- `v2` reduz demais a presenca de posts estruturalmente fortes
- `v2` quase nao muda a concentracao

---

## Criterio de validacao

O modelo `v2` pode ser considerado promissor se:

- reduzir a concentracao de hiper-checagem
- promover posts com baixa cobertura sem perder coerencia
- manter banda ou relevancia estrutural em nivel aceitavel
- produzir lote mais equilibrado do que o atual

---

## Entregaveis da validacao

1. export CSV das queries SQL
2. planilha Excel com filtros e tabelas dinamicas
3. notebook ou script Pandas com estatisticas comparativas
4. resumo final em Markdown

---

## Resumo final recomendado

Ao final da avaliacao, documentar:

- principais ganhos do `v2`
- principais perdas ou riscos
- recomendacao:
  - seguir para SQL real
  - ajustar formula
  - ajustar pesos
  - descartar proposta

---

## Status

Este plano descreve a validacao recomendada do score hibrido antes de qualquer troca no modelo ativo.

---

## Registro de feedback da primeira avaliacao

Achado relevante:

- o grupo `history_level = low` apareceu com score medio superior ao grupo `history_level = full`

Interpretacao:

- a formula ponderada direta favoreceu indevidamente o fallback
- `base_popularity` esta em escala muito superior a `velocity_score` e `acceleration_score`
- o grupo `full` esta sendo penalizado em vez de enriquecido por sinais temporais

Implicacao:

- o modelo `v2` ainda nao deve ser promovido para SQL ativo
- a formula precisa ser recalibrada antes da proxima rodada de validacao

Pergunta adicional obrigatoria nas proximas validacoes:

- o fallback `low` continua com vantagem sistematica sobre `full`?

---

## Query de referencia para comparar `full` versus `low`

Esta query deve ser mantida como referencia nas proximas iteracoes do modelo, porque ela evidencia se o fallback `history_level = low` continua sendo favorecido indevidamente.

```sql
with full_top as (
  select
    post_id,
    history_level,
    priority_score_v2,
    priority_band_v2,
    base_popularity,
    velocity_score,
    acceleration_score
  from public.v_post_priority_score_features_v2
  where history_level = 'full'
  order by priority_score_v2 desc
  limit 50
),
low_top as (
  select
    post_id,
    history_level,
    priority_score_v2,
    priority_band_v2,
    base_popularity,
    velocity_score,
    acceleration_score
  from public.v_post_priority_score_features_v2
  where history_level = 'low'
  order by priority_score_v2 desc
  limit 50
)
select
  grupo,
  count(*) as total_posts,
  round(avg(priority_score_v2)::numeric, 2) as avg_priority_score_v2,
  round(min(priority_score_v2)::numeric, 2) as min_priority_score_v2,
  round(max(priority_score_v2)::numeric, 2) as max_priority_score_v2,
  round(avg(base_popularity)::numeric, 2) as avg_base_popularity,
  round(avg(coalesce(velocity_score, 0))::numeric, 2) as avg_velocity_score,
  round(avg(coalesce(acceleration_score, 0))::numeric, 2) as avg_acceleration_score
from (
  select 'full_top_50' as grupo, * from full_top
  union all
  select 'low_top_50' as grupo, * from low_top
) t
group by grupo
order by grupo;
```

Objetivo:

- comparar a escala do score final entre os dois grupos
- verificar se `base_popularity`, `velocity_score` e `acceleration_score` estao contribuindo de forma equilibrada
- identificar rapidamente descalibracao da formula
