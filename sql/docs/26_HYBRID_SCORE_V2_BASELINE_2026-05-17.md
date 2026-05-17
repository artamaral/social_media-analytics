# HYBRID SCORE V2 BASELINE - 2026-05-17

## Objetivo

Registrar o baseline atual da comparacao entre a fila ativa e a fila analitica
`v2`.

Este arquivo deve ser usado como ponto de comparacao para futuras iteracoes da
formula `v2`, especialmente antes de qualquer promocao do score hibrido para a
fila ativa.

---

## Contexto

Estado operacional atual:

- a fila ativa usa `public.v_post_update_queue_batch`
- a fila ativa ja possui fatia guardrail de ate `4` slots
- os demais slots da fila ativa ainda usam `priority_score` e
  `calculate_priority_band(...)`
- o `priority_score_v2` continua apenas em modo analitico
- a fila `v2` avaliada usa `public.v_post_update_queue_batch_v2`

---

## Baseline 1. Comparacao detalhada

| comparison_status | coverage_status | history_level | active_priority_band | priority_band_v2 | total_posts | avg_total_checagens | avg_priority_score_v2 | avg_base_popularity | avg_velocity_score | avg_acceleration_score |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| active_only | covered | null | 6 | null | 7 | 469.00 | null | null | null | null |
| active_only | covered | null | 5 | null | 7 | 24.00 | null | null | null | null |
| active_only | covered | null | 4 | null | 7 | 15.86 | null | null | null | null |
| active_only | covered | null | 3 | null | 6 | 3.17 | null | null | null | null |
| active_only | covered | null | 2 | null | 2 | 10.50 | null | null | null | null |
| active_only | covered | null | 1 | null | 4 | 3.00 | null | null | null | null |
| active_only | guardrail_candidate | null | 1 | null | 2 | 0.00 | null | null | null | null |
| both | covered | full | 2 | 4 | 3 | 8.33 | 71.26 | 177.76 | 0.40 | 0.00 |
| both | guardrail_candidate | low | 2 | 6 | 1 | 0.00 | 148.01 | 148.01 | 0.00 | 0.00 |
| both | guardrail_candidate | low | 1 | 1 | 1 | 0.00 | 20.79 | 20.79 | 0.00 | 0.00 |
| v2_only | covered | full | null | 4 | 2 | 5.00 | 73.55 | 182.80 | 1.08 | 0.00 |
| v2_only | guardrail_candidate | full | null | 4 | 1 | 2.00 | 73.82 | 183.42 | 1.14 | 0.00 |
| v2_only | guardrail_candidate | full | null | 3 | 6 | 2.00 | 51.40 | 127.55 | 0.96 | 0.00 |
| v2_only | guardrail_candidate | full | null | 2 | 6 | 2.00 | 42.59 | 106.19 | 0.28 | 0.00 |
| v2_only | guardrail_candidate | full | null | 1 | 3 | 2.00 | 29.33 | 72.86 | 0.46 | 0.00 |
| v2_only | guardrail_candidate | low | null | 6 | 7 | 0.14 | 146.19 | 146.19 | 0.00 | 0.00 |
| v2_only | guardrail_candidate | low | null | 5 | 8 | 0.00 | 105.90 | 105.90 | 0.00 | 0.00 |
| v2_only | guardrail_candidate | low | null | 4 | 2 | 0.00 | 78.32 | 78.32 | 0.00 | 0.00 |

---

## Baseline 2. Resumo executivo

| comparison_status | history_level | priority_band_v2 | total_posts |
| --- | --- | --- | ---: |
| active_only | null | null | 35 |
| both | full | 4 | 3 |
| both | low | 6 | 1 |
| both | low | 1 | 1 |
| v2_only | full | 4 | 3 |
| v2_only | full | 3 | 6 |
| v2_only | full | 2 | 6 |
| v2_only | full | 1 | 3 |
| v2_only | low | 6 | 7 |
| v2_only | low | 5 | 8 |
| v2_only | low | 4 | 2 |

---

## Analise

### 1. O overlap entre ativo e `v2` ainda e baixo

Resumo:

- `active_only`: `35`
- `both`: `5`
- `v2_only`: `35`

Leitura:

- apenas `5` posts aparecem nos dois lotes
- o `v2` esta propondo um lote muito diferente do lote ativo
- isso confirma que a troca para `v2` teria impacto operacional alto

Conclusao:

- o `v2` nao deve ser promovido diretamente
- antes, precisa passar por recalibracao e nova validacao

---

### 2. O `v2` ainda favorece muitos posts com pouca cobertura

No grupo `v2_only`, aparecem muitos posts `guardrail_candidate`.

Principais sinais:

- `v2_only low banda 6`: `7` posts
- `v2_only low banda 5`: `8` posts
- `v2_only low banda 4`: `2` posts

Leitura:

- o `v2` ainda esta promovendo posts `low` para bandas altas
- esses posts nao possuem velocity nem acceleration
- o score alto vem basicamente de `base_popularity`

Conclusao:

- o problema observado na primeira avaliacao continua presente
- o fallback `low` ainda esta forte demais

---

### 3. Os sinais temporais ainda aparecem fracos

Nos grupos `full`, os valores medios de `velocity_score` ficam baixos:

- `both full banda 4`: `0.40`
- `v2_only full banda 4`: `1.08`
- `v2_only full banda 3`: `0.96`
- `v2_only full banda 2`: `0.28`

Ja `acceleration_score` aparece como `0.00` em todos os grupos agregados.

Leitura:

- a formula atual ainda e dominada por base popularity
- velocity ajuda pouco
- acceleration praticamente nao influencia este baseline

Conclusao:

- o `v2` ainda nao esta se comportando como modelo de tendencia
- ele esta se comportando majoritariamente como um score de popularidade base

---

### 4. A fila ativa esta mais concentrada em posts maduros

O grupo `active_only` mostra:

- banda `6`: media de `469` checagens
- banda `5`: media de `24` checagens
- bandas intermediarias com posts ja cobertos

Leitura:

- a fila ativa segue priorizando posts maduros e historicamente relevantes
- isso preserva estabilidade operacional
- mas tambem confirma que a fila ativa ainda pode concentrar checagens em
  posts antigos e muito observados

Conclusao:

- existe motivo para evoluir o modelo
- mas o `v2` atual ainda nao e a alternativa certa

---

## Diagnostico do estado atual do `v2`

Estado:

- util como simulacao analitica
- ainda descalibrado para promocao
- sensivel demais ao fallback `low`
- pouco sensivel a acceleration neste baseline

Principal problema:

- componentes continuam em escalas diferentes
- `base_popularity` domina
- `low` preserva base inteira
- `full` ainda sofre reducao pela ponderacao direta

Diretriz:

- nao promover o `v2` atual para a fila ativa
- recalibrar a formula antes da proxima comparacao
- manter guardrail separado e independente

---

## Proxima iteracao recomendada

Testar uma versao `v2.1` com modelo aditivo calibrado.

Exemplo conceitual:

```text
priority_score_v2_1 =
  base_popularity
  + velocity_bonus
  + acceleration_bonus
  + coverage_adjustment
```

Objetivo:

- impedir que `full` seja penalizado por ter historico
- impedir que `low` ganhe vantagem sistematica
- deixar velocity e acceleration atuarem como bonus real
- preservar guardrail como regra separada de cobertura minima

---

## Criterios para comparacao futura

Na proxima avaliacao, comparar contra este baseline:

- overlap entre ativo e `v2`
- quantidade de `v2_only low` em bandas altas
- quantidade de `v2_only full` em bandas intermediarias e altas
- media de `velocity_score`
- media de `acceleration_score`
- impacto sobre posts hiperchecados
- preservacao do guardrail

Sinal de melhora:

- menos `low` em bandas `5` e `6`
- mais `full` e `partial` com velocity relevante
- menor dependencia de `base_popularity`
- overlap mais explicavel com a fila ativa
- reducao de hiperconcentracao sem perder relevancia
