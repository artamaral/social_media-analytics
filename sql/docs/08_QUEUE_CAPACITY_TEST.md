# TESTE DE CAPACIDADE DA FILA

## Objetivo

Este teste verifica se a combinacao atual de regras da fila e suficiente para o volume de posts elegiveis por execucao do worker.

Premissas atuais:

- a frequencia de rechecagem e definida no SQL por `calculate_next_check(...)`
- o worker busca apenas itens com `needs_update = true`
- o worker busca apenas itens com `next_check <= now()`
- o worker ordena por `priority_score desc`
- o worker processa no maximo `20` itens por execucao

---

## Por que este teste faz sentido

A regra de agendamento define quando cada post volta a ficar elegivel, mas nao limita quantos itens podem vencer ao mesmo tempo.

Se houver mais de `20` itens elegiveis em uma execucao:

- o worker processa apenas os `20` primeiros
- os demais ficam aguardando a proxima rodada
- se isso ocorrer continuamente, a fila pode formar backlog
- posts de menor prioridade podem demorar mais do que o esperado para serem revisitados

Por isso, este teste mede se a capacidade operacional do worker acompanha o ritmo da fila.

---

## Regra atual de agendamento

Regra implementada no SQL:

- `score >= 50000` -> `1 hour`
- `score >= 20000` -> `3 hours`
- `score >= 5000` -> `6 hours`
- `score < 5000` -> `12 hours`

---

## Teste 1. Quantos itens estao elegiveis agora

Query:

```sql
select
  count(*) as itens_elegiveis_agora
from post_update_queue
where needs_update = true
  and next_check <= now();
```

Interpretacao:

- se o numero fica entre `0` e `20`, a fila esta sob controle na rodada atual
- se passa de `20` com frequencia, existe disputa por capacidade
- se cresce continuamente, existe backlog estrutural

---

## Teste 2. Quais itens estao no topo da fila agora

Query:

```sql
select
  post_id,
  priority_score,
  last_checked,
  next_check
from post_update_queue
where needs_update = true
  and next_check <= now()
order by priority_score desc
limit 100;
```

Interpretacao:

- mostra quem esta sendo priorizado
- permite observar se os mesmos posts ficam sempre no topo
- ajuda a detectar concentracao excessiva nos scores mais altos

---

## Teste 3. Distribuicao da fila por faixa de prioridade

Query:

```sql
select
  case
    when priority_score >= 50000 then '1h'
    when priority_score >= 20000 then '3h'
    when priority_score >= 5000 then '6h'
    else '12h'
  end as faixa,
  count(*) as total_posts
from post_update_queue
where needs_update = true
group by 1
order by 1;
```

Interpretacao:

- mostra quantos posts existem em cada faixa de frequencia
- se houver muitos posts na faixa de `1h`, o limite de `20` por execucao pode nao ser suficiente

---

## Teste 4. Verificar se o backlog esta crescendo

Query:

```sql
select
  count(*) as itens_vencidos
from post_update_queue
where needs_update = true
  and next_check <= now();
```

Uso recomendado:

- rodar em momentos diferentes do dia
- comparar os resultados ao longo de algumas horas

Interpretacao:

- se o numero sobe e depois volta, o worker esta absorvendo a fila
- se o numero so sobe, a capacidade esta abaixo da demanda

---

## Teste 5. Verificar se posts recentes estao sendo revisitados

Query:

```sql
select
  total_coletas,
  count(*) as total_posts
from (
  select
    post_id,
    count(*) as total_coletas
  from post_metrics_history
  where collected_at >= now() - interval '5 days'
  group by post_id
) t
group by total_coletas
order by total_coletas;
```

Interpretacao:

- se comecarem a aparecer posts com `2`, `3` ou mais coletas, o recheck esta acontecendo
- se tudo continuar concentrado em `1`, a fila nao esta retornando os posts como esperado

---

## Como observar o comportamento real

Sugestao pratica:

1. Deixar o worker rodar por algumas execucoes.
2. Rodar os testes 1, 2, 3 e 4 em intervalos regulares.
3. Ao final de algumas horas, rodar o teste 5.
4. Comparar se o backlog diminui, estabiliza ou cresce.

---

## Criterios de leitura

### Cenario saudavel

- a quantidade de itens elegiveis nao cresce continuamente
- posts recentes passam a ter mais de `1` coleta
- a fila nao fica permanentemente acima da capacidade de `20` por rodada

### Cenario de alerta

- sempre existem muitos itens elegiveis acima de `20`
- os mesmos posts dominam o topo repetidamente
- posts de baixa prioridade quase nunca entram

### Cenario de problema estrutural

- backlog cresce a cada rodada
- posts recentes continuam com apenas `1` coleta
- a fila deixa de refletir a frequencia definida no SQL

---

## Observacao importante

Este teste nao prova sozinho que o modelo final de priorizacao e o ideal, mas ele mostra se a combinacao atual entre:

- regra de negocio
- volume da fila
- capacidade do worker

esta operacionalmente sustentavel.
