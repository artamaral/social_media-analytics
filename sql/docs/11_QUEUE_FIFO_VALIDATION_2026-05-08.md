# QUEUE FIFO VALIDATION - PLAN AND RESULTS

## Objetivo

Validar a mudanca na fila que manteve:

- prioridade por banda definida pelo score
- cotas por banda na view

e alterou:

- a ordem interna de cada banda para FIFO por `next_check`

Este documento concentra no mesmo lugar:

- plano de validacao
- execucao das queries
- registro dos resultados
- conclusao final

---

## Mudanca sob validacao

Escopo:

- `v_post_update_queue_batch`

Comportamento esperado:

- o score continua definindo a banda
- a view continua aplicando cotas por banda
- dentro da mesma banda, o post com `next_check` mais antigo entra antes

Objetivo de negocio:

- reduzir a concentracao de checagens em poucos posts dentro da mesma banda
- melhorar a rotacao dos posts sem perder prioridade macro por relevancia

---

## Hipotese

Se a mudanca estiver correta:

- a fila continuara priorizando posts de maior banda
- dentro da banda, a rotacao ficara mais equilibrada
- posts com poucas checagens terao mais chance de entrar
- a cobertura da base melhorara sem quebrar o recheck recorrente

---

## Criterios de sucesso

- a view retorna mais de uma banda
- a ordem dentro da banda respeita `next_check` mais antigo
- os mesmos posts deixam de dominar continuamente a propria banda
- posts com poucas checagens comecam a ganhar rotacao
- backlog nao cresce sem controle
- posts recentes continuam sendo revisitados
- o aumento do lote para `40` nao piora de forma relevante o custo por snapshot
- Cloud Run, YouTube quota e Supabase writes permanecem dentro de limites aceitaveis

---

## Como executar

1. Aplicar a view nova no banco.
2. Deixar o worker rodar apos a mudanca.
3. Rodar as queries abaixo.
4. Registrar os resultados neste mesmo arquivo.
5. Concluir com:
   - validado
   - validado com ressalvas
   - nao validado

---

## Contexto da execucao

- Data da validacao: 2026-05-08
- Ambiente: producao
- Worker: Cloud Run
- Frequencia do worker: preencher
- Limite por execucao: 40
- View validada: `public.v_post_update_queue_batch`

Distribuicao esperada por execucao:

- banda `6`: `8`
- banda `5`: `8`
- banda `4`: `8`
- banda `3`: `6`
- banda `2`: `6`
- banda `1`: `4`

Observacao:

- esta validacao precisa incluir custo e FinOps antes de considerar o aumento definitivo

---

## Query 1. Lote atual entregue ao worker

Objetivo:

- validar diversidade entre bandas
- validar FIFO dentro da banda

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

Resultado:

- preencher

Leitura:

- preencher

---

## Query 2. Backlog vencido por banda

Objetivo:

- ver se alguma banda continua represada

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

Resultado:

- preencher

Leitura:

- preencher

---

## Query 3. Distribuicao de checagens por post

Objetivo:

- medir concentracao de checagens

Query:

```sql
select
  total_checagens,
  count(*) as total_posts
from (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) t
group by total_checagens
order by total_checagens;
```

Resultado:

- preencher

Leitura:

- preencher

---

## Query 4. Posts com checagem extrema

Objetivo:

- confirmar se a concentracao continua nos mesmos posts

Query:

```sql
select
  p.post_id,
  count(*) as total_checagens,
  public.calculate_post_priority(p.views, p.likes, p.comments) as priority_score,
  public.calculate_priority_band(
    public.calculate_post_priority(p.views, p.likes, p.comments)
  ) as priority_band,
  q.last_checked,
  q.next_check,
  q.needs_update
from posts p
join post_metrics_history h
  on h.post_id = p.post_id
left join post_update_queue q
  on q.post_id = p.post_id
group by
  p.post_id,
  p.views,
  p.likes,
  p.comments,
  q.last_checked,
  q.next_check,
  q.needs_update
having count(*) >= 50
order by total_checagens desc, priority_score desc;
```

Resultado:

- preencher

Leitura:

- preencher

---

## Query 5. Posts com poucas checagens e score alto

Objetivo:

- validar se posts ainda pouco revisitados comecam a entrar no ciclo

Query:

```sql
select
  p.post_id,
  coalesce(h.total_checagens, 0) as total_checagens,
  public.calculate_post_priority(p.views, p.likes, p.comments) as priority_score,
  public.calculate_priority_band(
    public.calculate_post_priority(p.views, p.likes, p.comments)
  ) as priority_band,
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
  on q.post_id = p.post_id
where coalesce(h.total_checagens, 0) <= 2
order by priority_score desc nulls last
limit 100;
```

Resultado:

- preencher

Leitura:

- preencher

---

## Query 6. Posts recentes revisitados

Objetivo:

- garantir que o recheck continua acontecendo

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

Resultado:

- preencher

Leitura:

- preencher

---

## Query 7. Validacao FinOps e custos

Objetivo:

- medir se o aumento para `40` posts por execucao melhora cobertura sem degradar custo unitario

Indicadores a registrar:

- custo diario do Cloud Run antes e depois
- duracao media por execucao
- total de execucoes por dia
- total de snapshots inseridos em `post_metrics_history`
- custo por snapshot
- uso diario de quota da YouTube Data API
- erros ou retries do worker
- crescimento diario de writes no Supabase

Resultado:

- preencher

Leitura:

- preencher

---

## Conclusao final

### Estado da mudanca

- validado
- validado com ressalvas
- nao validado

### Resumo

- preencher

### Evidencias principais

- preencher
- preencher
- preencher

### Proxima acao sugerida

- manter como esta
- ajustar cotas por banda
- ajustar `calculate_next_check(...)`
- aumentar frequencia do worker
- ajustar limite por execucao
- revisar custo/FinOps antes de manter lote `40`
- outra: preencher

---

## Registro em decisoes tecnicas se validado

Se o resultado final for `validado`, registrar no arquivo:

- [05_DECISOES_TECNICAS.md](C:/social_media-analytics/sql/docs/05_DECISOES_TECNICAS.md:1)

Texto sugerido:

```text
Validacao em producao:
- data: 2026-05-08
- resultado: FIFO por `next_check` dentro da banda validado
- efeito observado: maior rotacao dentro das bandas, com preservacao da prioridade macro por score
```
