# TESTE DE CAPACIDADE DA FILA

## Objetivo

Este teste verifica se a combinacao atual de regras da fila e suficiente para o volume de posts elegiveis por execucao do worker.

Premissas atuais:

- a frequencia de rechecagem e definida no SQL por `calculate_next_check(...)`
- a fila e fatiada por bandas de prioridade no SQL
- o worker busca apenas itens com `needs_update = true`
- o worker le a view `v_post_update_queue_batch`
- o worker processa no maximo `20` itens por execucao

---

## Por que este teste faz sentido

A regra de agendamento define quando cada post volta a ficar elegivel, mas nao limita quantos itens podem vencer ao mesmo tempo.

Se houver mais de `20` itens elegiveis em uma execucao:

- o worker processa apenas os `20` itens devolvidos pela view
- os demais ficam aguardando a proxima rodada
- se isso ocorrer continuamente, a fila pode formar backlog
- bandas intermediarias podem acumular backlog se a capacidade continuar insuficiente

Por isso, este teste mede se a capacidade operacional do worker acompanha o ritmo da fila.

---

## Regra atual de agendamento

Regra implementada no SQL:

- `700.000+` -> `30 minutes`
- `300.000 - 699.999` -> `1 hour`
- `150.000 - 299.999` -> `2 hours`
- `50.000 - 149.999` -> `4 hours`
- `10.000 - 49.999` -> `8 hours`
- `0 - 9.999` -> `12 hours`

Bandas e cotas da view:

- banda `6` -> `4`
- banda `5` -> `4`
- banda `4` -> `4`
- banda `3` -> `3`
- banda `2` -> `3`
- banda `1` -> `2`

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

## Teste 2. Quais itens a view esta priorizando agora

Query:

```sql
select
  post_id,
  priority_band,
  priority_score,
  last_checked,
  next_check
from public.v_post_update_queue_batch;
```

Interpretacao:

- mostra quem realmente sera entregue ao worker
- permite observar se as bandas estao sendo misturadas
- ajuda a detectar se o fatiamento esta funcionando

---

## Teste 3. Distribuicao da fila por faixa de prioridade

Query:

```sql
select
  public.calculate_priority_band(priority_score) as priority_band,
  count(*) as total_posts
from post_update_queue
where needs_update = true
group by 1
order by 1 desc;
```

Interpretacao:

- mostra quantos posts existem em cada banda
- ajuda a medir se as cotas ainda fazem sentido para a distribuicao real

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

## Teste 4.1 Verificar backlog por banda

Query:

```sql
select
  public.calculate_priority_band(priority_score) as priority_band,
  count(*) as itens_vencidos
from post_update_queue
where needs_update = true
  and next_check <= now()
group by 1
order by 1 desc;
```

Interpretacao:

- mostra se uma banda especifica esta ficando represada
- ajuda a identificar se as cotas precisam de ajuste

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
- a view entrega mais de uma banda por execucao

### Cenario de alerta

- sempre existem muitos itens elegiveis acima de `20`
- a view passa a repetir quase sempre o mesmo grupo
- bandas intermediarias quase nunca entram

### Cenario de problema estrutural

- backlog cresce a cada rodada
- posts recentes continuam com apenas `1` coleta
- a fila deixa de refletir a frequencia definida no SQL
- a fatia da view nao reduz o starvation entre bandas

---

## Observacao importante

Este teste nao prova sozinho que o modelo final de priorizacao e o ideal, mas ele mostra se a combinacao atual entre:

- regra de negocio
- volume da fila
- capacidade do worker

esta operacionalmente sustentavel.
