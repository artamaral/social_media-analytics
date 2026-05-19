# UNAVAILABLE VIDEO HANDLING SPEC

## Objetivo

Definir como tratar videos que entram na fila de atualizacao, sao enviados para
`videos.list`, mas nao retornam em `items`.

Esse caso nao deve ficar preso indefinidamente no guardrail ou na fila normal.

Casos observados:

| post_id | youtube_url | status manual observado |
| --- | --- | --- |
| `BH0gnUODKwI` | `https://www.youtube.com/watch?v=BH0gnUODKwI` | indisponivel |
| `lFodaSeTE9A` | `https://www.youtube.com/watch?v=lFodaSeTE9A` | indisponivel |

Evidencia operacional:

- lote esperado: `40`
- itens processados: `38`
- os dois videos foram conferidos manualmente e estavam indisponiveis no
  YouTube

---

## Principio

Logs ajudam humanos, mas nao devem ser a fonte de verdade.

A fonte de verdade deve ser uma tabela no banco que registre:

- quais IDs nao voltaram da YouTube API
- quantas vezes isso aconteceu
- quando ocorreu
- qual URL deve ser conferida manualmente
- qual foi o resultado da revisao humana
- quando o post deve sair da fila ativa

---

## Tabela proposta

```sql
create table if not exists public.post_collection_failures (
  post_id text primary key references public.posts(post_id),
  youtube_url text generated always as (
    'https://www.youtube.com/watch?v=' || post_id
  ) stored,
  failure_count integer not null default 0,
  first_failed_at timestamp without time zone not null default now(),
  last_failed_at timestamp without time zone not null default now(),
  last_success_at timestamp without time zone,
  status text not null default 'active',
  last_failure_reason text,
  human_review_status text,
  human_reviewed_at timestamp without time zone,
  human_reviewed_by text,
  human_review_notes text
);
```

### Campo `youtube_url`

O campo `youtube_url` deve existir dentro da tabela para facilitar revisao
manual.

Exemplo:

```text
https://www.youtube.com/watch?v=BH0gnUODKwI
```

Motivo:

- o humano nao precisa montar a URL manualmente
- o dashboard pode renderizar o link diretamente
- a rotina semanal fica mais rapida e menos sujeita a erro
- a verificacao deixa de depender de copiar `post_id` do log

---

## Status sugeridos

### `active`

Estado inicial ou sem falha relevante.

### `unavailable_candidate`

O video foi enviado para `videos.list`, mas nao voltou em `items`.

### `unavailable`

O video teve falhas recorrentes ou revisao humana confirmou indisponibilidade.

Posts nesse estado devem ser excluidos da fila ativa.

### `recovered`

O video voltou a aparecer em uma coleta posterior.

---

## Funcao de registro proposta

O worker deve enviar ao banco:

- `requested_ids`
- `returned_ids`

O banco calcula os ausentes e atualiza os contadores.

```sql
create or replace function public.register_post_collection_result(
  p_requested_ids text[],
  p_returned_ids text[]
)
returns void
language plpgsql
as $$
declare
  missing_id text;
  returned_id text;
begin
  foreach returned_id in array p_returned_ids loop
    insert into public.post_collection_failures (
      post_id,
      failure_count,
      first_failed_at,
      last_failed_at,
      last_success_at,
      status,
      last_failure_reason
    )
    values (
      returned_id,
      0,
      now(),
      now(),
      now(),
      'recovered',
      null
    )
    on conflict (post_id) do update
      set
        failure_count = 0,
        last_success_at = now(),
        status = 'recovered',
        last_failure_reason = null;
  end loop;

  foreach missing_id in array (
    select array(
      select unnest(p_requested_ids)
      except
      select unnest(p_returned_ids)
    )
  ) loop
    insert into public.post_collection_failures (
      post_id,
      failure_count,
      first_failed_at,
      last_failed_at,
      status,
      last_failure_reason
    )
    values (
      missing_id,
      1,
      now(),
      now(),
      'unavailable_candidate',
      'not_returned_by_youtube_videos_list'
    )
    on conflict (post_id) do update
      set
        failure_count = public.post_collection_failures.failure_count + 1,
        last_failed_at = now(),
        status = case
          when public.post_collection_failures.failure_count + 1 >= 3
            then 'unavailable'
          else 'unavailable_candidate'
        end,
        last_failure_reason = 'not_returned_by_youtube_videos_list';
  end loop;
end;
$$;
```

---

## Integracao com a fila ativa

Quando a tabela existir, `public.v_post_update_queue_batch` deve excluir videos
confirmados como indisponiveis.

Regra:

```sql
and coalesce(f.status, 'active') <> 'unavailable'
```

Essa exclusao deve acontecer dentro do SQL da view, nao no worker Python.

---

## View para dashboard

O dashboard deve consumir uma view especifica para revisao de videos
indisponiveis.

Nome sugerido:

- `public.v_dashboard_unavailable_video_review`

Query conceitual:

```sql
create or replace view public.v_dashboard_unavailable_video_review as
select
  f.post_id,
  f.youtube_url,
  f.failure_count,
  f.first_failed_at,
  f.last_failed_at,
  f.last_success_at,
  f.status,
  f.last_failure_reason,
  f.human_review_status,
  f.human_reviewed_at,
  f.human_reviewed_by,
  f.human_review_notes,
  p.created_at,
  p.collected_at,
  p.views,
  p.likes,
  p.comments
from public.post_collection_failures f
left join public.posts p
  on p.post_id = f.post_id
where f.status in ('unavailable_candidate', 'unavailable')
order by
  f.status,
  f.failure_count desc,
  f.last_failed_at desc;
```

Objetivo:

- permitir revisao humana pelo dashboard
- mostrar a URL completa
- expor status, contagem de falhas e motivo
- reduzir dependencia de logs para operar a rotina

---

## Processo humano de revisao

1. Abrir a view de revisao no dashboard.
2. Clicar em `youtube_url`.
3. Conferir o estado do video no YouTube.
4. Atualizar `human_review_status`.
5. Se confirmado indisponivel, manter ou marcar `status = 'unavailable'`.

Status humanos sugeridos:

- `confirmed_unavailable`
- `available_on_manual_check`
- `unclear`

---

## Query semanal de revisao

```sql
select
  post_id,
  youtube_url,
  failure_count,
  status,
  last_failure_reason,
  first_failed_at,
  last_failed_at,
  human_review_status,
  human_reviewed_at
from public.post_collection_failures
where status in ('unavailable_candidate', 'unavailable')
order by
  status,
  failure_count desc,
  last_failed_at desc;
```

Resultado esperado:

- lista pequena
- todos os `unavailable_candidate` revisados periodicamente
- nenhum video indisponivel preso no guardrail

---

## Status

Implementacao preparada no repositorio.

Arquivos SQL:

- `sql/ddl/tables/013_create_post_collection_failures.sql`
- `sql/ddl/functions/005_post_collection_failure_functions.sql`
- `sql/ddl/views/008_create_v_dashboard_unavailable_video_review.sql`
- `sql/ddl/views/002_create_v_post_update_queue_batch.sql`
- `sql/ddl/views/004_create_v_post_update_queue_batch_v2.sql`

Worker:

- `scripts/cloud_run/postMetrics/main.py`

Rotinas de teste:

- `scripts/cloud_run/postMetrics/test_missing_video_ids.py`
- `sql/ddl/tests/001_test_post_collection_failure_segmentation.sql`

Ainda falta executar no Supabase:

1. Criar a tabela `post_collection_failures`.
2. Criar a funcao `register_post_collection_result(...)`.
3. Criar a view `v_dashboard_unavailable_video_review`.
4. Recriar as views de fila para aplicar a exclusao de `status = 'unavailable'`.
5. Rodar o teste SQL transacional antes de liberar a rotina em producao.
