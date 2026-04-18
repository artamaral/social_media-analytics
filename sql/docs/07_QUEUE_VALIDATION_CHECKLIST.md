# VALIDACAO DA FILA DE RECHECK

## Objetivo

Este documento serve para validar se a fila de rechecagem periodica de posts esta funcionando corretamente apos alteracoes em:

- triggers
- funcoes SQL
- regras de prioridade
- bandas e cotas da fila
- regras de agendamento
- worker do Cloud Run

---

## Status da mudanca atual

Status: pendente de validacao em producao

Commit relacionado:

```text
feat(sql): centraliza prioridade e rechecagem da queue no banco
```

Como documentar que um commit esta pendente de validacao:

- manter esta secao com `Status: pendente de validacao em producao`
- citar o commit ou a mensagem de commit
- apos validacao, atualizar para `Status: validado em producao`
- registrar a data da validacao e um resumo curto do resultado

Modelo para atualizacao futura:

```text
Status: validado em producao
Data da validacao: YYYY-MM-DD
Resultado: rechecagem voltou a ocorrer para posts recentes e fila segue reagendando corretamente
```

Mudanca estrutural relacionada:

- [09_QUEUE_SLICING_AND_RESCHEDULING.md](C:/social_media-analytics/sql/docs/09_QUEUE_SLICING_AND_RESCHEDULING.md:1)

---

## Validacoes principais

### 1. Validar se a fila esta sendo renovada

Query:

```sql
select
  post_id,
  priority_score,
  needs_update,
  last_checked,
  next_check
from post_update_queue
where last_checked is not null
order by last_checked desc
limit 50;
```

Esperado:

- `last_checked` preenchido
- `next_check` maior que `last_checked`
- `needs_update = true`

Sinal de problema:

- `needs_update = false` para itens processados recentemente
- `next_check <= last_checked`

---

### 1.1 Validar se a view da fila esta retornando itens de bandas diferentes

Query:

```sql
select
  priority_band,
  count(*) as total_posts
from public.v_post_update_queue_batch
group by priority_band
order by priority_band desc;
```

Esperado:

- mais de uma banda presente no lote
- o lote nao ser composto apenas pelos maiores scores absolutos

Sinal de problema:

- a view retornar apenas banda alta continuamente
- ausencia persistente de bandas intermediarias mesmo com elegiveis

---

### 2. Validar se posts recentes passaram a ter mais de 1 coleta

Esta e a prova principal de que o recheck voltou a acontecer.

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

Esperado:

- com o passar das horas, comecam a aparecer posts com `2`, `3` ou mais coletas
- nao ficar tudo concentrado apenas em `1`

Sinal de problema:

- todos os posts recentes continuarem com apenas `1` coleta

---

### 3. Procurar inconsistencias entre filas, posts e historico

Fila sem post correspondente:

```sql
select count(*) as filas_sem_post
from post_update_queue q
left join posts p on p.post_id = q.post_id
where p.post_id is null;
```

Historico sem post correspondente:

```sql
select count(*) as historicos_sem_post
from post_metrics_history h
left join posts p on p.post_id = h.post_id
where p.post_id is null;
```

Queue com agendamento invalido:

```sql
select count(*) as queue_com_agendamento_invalido
from post_update_queue
where last_checked is not null
  and next_check <= last_checked;
```

Posts sem coleta recente:

```sql
select count(*) as posts_sem_coleta_recente
from posts
where collected_at is null
   or collected_at < now() - interval '2 days';
```

Esperado:

- contagens muito baixas ou zero para inconsistencias

Sinal de problema:

- filas sem post
- historico sem post
- itens com `next_check` atrasado em relacao a `last_checked`

---

### 4. Monitorar risco operacional da fila

Itens vencidos aguardando processamento:

```sql
select
  count(*) as itens_vencidos
from post_update_queue
where needs_update = true
  and next_check <= now();
```

Esperado:

- o numero pode oscilar, mas nao deve crescer continuamente sem voltar

Sinal de problema:

- backlog so cresce
- Cloud Run nao da vazao ao volume da fila

---

### 4.1 Monitorar backlog por banda

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

Esperado:

- backlog distribuido de forma controlada
- faixas intermediarias nao acumularem indefinidamente sem entrar na view

Sinal de problema:

- bandas intermediarias crescendo sem nunca aparecer no batch

---

## Janela recomendada de validacao

Sugestao pratica apos deploy:

1. Esperar 2 ou 3 execucoes do Cloud Run.
2. Rodar as queries acima.
3. Verificar se posts recentes ja comecaram a ter 2 ou mais coletas.
4. Validar que a fila segue com `needs_update = true` e `next_check` futuro.

---

## Criterio de sucesso

A mudanca pode ser considerada validada quando:

- posts recentes deixam de concentrar 100 por cento das ocorrencias em apenas `1` coleta
- `post_update_queue` passa a renovar `last_checked` e `next_check`
- itens processados permanecem elegiveis para futuras rodadas
- a view `v_post_update_queue_batch` retorna distribuicao coerente entre bandas
- nao ha crescimento anormal de backlog

---

## Observacoes

- ausencia de erro no deploy nao prova que a regra de negocio esta correta
- a validacao precisa ser feita em dados reais apos algumas execucoes do scheduler
- qualquer alteracao futura de prioridade ou frequencia deve atualizar este checklist
