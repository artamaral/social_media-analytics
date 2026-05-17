# PHASE 2 INITIAL DATA BASELINE - 2026-05-17

## Objetivo

Registrar um baseline inicial antes da fase 2 do legado.

O objetivo deste arquivo e evitar repetir o problema ocorrido na fase 1:

- execucao sem visibilidade suficiente
- dificuldade para provar progresso real
- tempo perdido sem confirmar se havia evolucao no dado

Este baseline passa a ser o ponto de comparacao oficial para a fase 2.

---

## Perguntas que este baseline deve responder

Antes de iniciar a fase 2, precisamos saber:

1. qual e a composicao atual do `low`
2. quanto do `low` ainda e legado e quanto ja e `bootstrap_low`
3. quantos posts legados ja tem `2` checagens e podem ganhar promocao temporal
4. qual e a massa atual em `partial`
5. qual e a massa atual em `full`

---

## Leitura executiva inicial

### Situacao do legado

No encerramento da fase 1, o backlog legado de baixa cobertura foi
praticamente drenado.

Estado observado:

| low_type   | total_checagens | history_level | total_posts |
| ---------- | --------------- | ------------- | ----------- |
| legacy_low | 0               | low           | 2           |
| legacy_low | 1               | low           | 1           |
| legacy_low | 2               | full          | 1034        |
| legacy_low | 2               | partial       | 239         |

Leitura:

- `legacy_low` residual: `3`
- a fase 1 cumpriu seu objetivo
- o foco deixa de ser dar primeiro snapshot
- o foco passa a ser promover temporalmente os legados que ja chegaram a
  `2` checagens

### Situacao atual do bootstrap

| low_type      | total_checagens | history_level | total_posts |
| ------------- | --------------- | ------------- | ----------- |
| bootstrap_low | 0               | low           | 185         |
| bootstrap_low | 1               | low           | 16          |
| bootstrap_low | 2               | full          | 4           |

Leitura:

- o `bootstrap_low` passa a ser a principal fonte residual de `low`
- isso significa que o problema estrutural remanescente nao e mais legado
- novos posts continuam entrando sem contexto historico suficiente

---

## Interpretacao do status atual dos dados

### O que ja foi resolvido

- o backlog legado praticamente deixou de ser um bloqueio
- a base antiga ganhou historico minimo
- existe agora uma massa grande de legados com `2` checagens e contexto
  suficiente para discutir promocao de estado

### O que ainda nao foi resolvido

- `bootstrap_low` continua entrando naturalmente
- a fase 2 ainda nao tem baseline formal de acompanhamento
- ainda precisamos provar que novas coletas realmente promovem posts de
  `partial` para `full` ou aumentam utilidade temporal do historico

---

## KPIs oficiais da fase 2

Durante a fase 2, estes indicadores devem ser acompanhados em toda rodada de
validacao.

### KPI 1. `legacy_low` residual

Objetivo:

- permanecer proximo de zero

Sinal esperado:

- continuar em nivel residual

### KPI 2. `legacy_low` com `2` checagens em `partial`

Objetivo:

- entender quantos legados ainda estao num estado intermediario

Sinal esperado:

- cair ao longo do tempo, se a fase 2 estiver promovendo estado

### KPI 3. `legacy_low` com `2` checagens em `full`

Objetivo:

- medir ganho de posts legados que ja passaram a ter historico maduro

Sinal esperado:

- subir ou se manter alto

### KPI 4. composicao do `bootstrap_low`

Objetivo:

- medir a pressao de entrada de novos posts sem historico

Sinal esperado:

- pode continuar alto, mesmo com a fase 2 funcionando
- nao deve ser usado como unico KPI para julgar sucesso da fase 2 do legado

---

## Query oficial do baseline da fase 2

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
)
select
  case
    when p.created_at >= now() - interval '7 days' then 'bootstrap_low'
    else 'legacy_low'
  end as low_type,
  coalesce(c.total_checagens, 0) as total_checagens,
  v.history_level,
  count(*) as total_posts
from posts p
left join checks c
  on c.post_id = p.post_id
left join public.v_post_priority_score_features_v2 v
  on v.post_id = p.post_id
where coalesce(c.total_checagens, 0) <= 2
group by 1, 2, 3
order by 1, 2, 3;
```

Uso:

- rodar antes da fase 2
- salvar os valores neste arquivo
- rodar novamente a cada checkpoint relevante
- comparar com esta baseline inicial

---

## Query resumida para status geral da base

```sql
select
  history_level,
  count(*) as total_posts
from public.v_post_priority_score_features_v2
group by history_level
order by history_level;
```

Objetivo:

- medir o tamanho atual de `full`, `low` e `partial`

---

## Query de foco especifico no legado

```sql
with checks as (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
)
select
  coalesce(c.total_checagens, 0) as total_checagens,
  v.history_level,
  count(*) as total_posts
from posts p
left join checks c
  on c.post_id = p.post_id
left join public.v_post_priority_score_features_v2 v
  on v.post_id = p.post_id
where p.created_at < now() - interval '7 days'
  and coalesce(c.total_checagens, 0) <= 2
group by 1, 2
order by 1, 2;
```

Objetivo:

- acompanhar especificamente a massa legado que pode evoluir durante a fase 2

---

## Sinais esperados de evolucao na fase 2

### Sinais positivos

- `legacy_low` residual continua proximo de zero
- posts legados em `partial` diminuem
- posts legados em `full` aumentam ou consolidam
- os checkpoints mostram mudanca real e mensuravel no grupo legado

### Sinais de alerta

- `legacy_low` volta a subir sem explicacao operacional
- `partial` legado fica estagnado por muitas rodadas
- as queries mostram pouca ou nenhuma mudanca apesar de novas execucoes
- o foco da leitura se confunde entre problema de legado e problema de
  `bootstrap_low`

---

## Conclusao

Este arquivo define o status inicial oficial para acompanhar a fase 2.

Diretriz:

- nenhuma execucao da fase 2 deve ser considerada bem-sucedida sem comparacao
  contra esta baseline
- `bootstrap_low` e `legacy_low` devem continuar sendo lidos separadamente
- sucesso da fase 2 do legado deve ser julgado principalmente pela evolucao do
  grupo legado, nao pelo `low` total isolado
