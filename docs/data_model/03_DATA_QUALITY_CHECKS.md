# DATA QUALITY CHECKS

## Coleta de posts

- Todos os posts devem ter pelo menos 1 registro em `post_metrics_history`.
- `collected_at` nunca pode ser `NULL`.

## Atualizacao

- Cada post deve ser atualizado ao menos 1 vez por dia.

## Integridade

- Nenhum creator deve ficar sem posts.
- Nenhum post deve ficar sem creator.

## Queries de validacao

### Posts sem historico

```sql
SELECT p.id, p.post_id
FROM public.posts p
LEFT JOIN public.post_metrics_history h ON p.post_id = h.post_id
WHERE h.post_id IS NULL;
```

Auditoria detalhada para Sprint 1:

- `sql/dml/audit_posts_without_snapshots.sql`

Objetivo:

- listar apenas posts com `0` snapshots em `post_metrics_history`
- separar posts ativos de `unavailable_candidate` e `unavailable`
- trazer contexto de creator, idade do video, fila e revisao humana

### Ultima coleta por post

```sql
SELECT *
FROM public.posts
WHERE collected_at IS NULL;
```

Auditoria detalhada para Sprint 1:

- `sql/dml/audit_posts_collected_at_sync.sql`

Objetivo:

- listar posts com `posts.collected_at` nulo
- comparar `posts.collected_at` com o ultimo snapshot em `post_metrics_history`
- separar inconsistencias por `failure_status` e idade do video
- identificar casos em que ha snapshot, mas o campo corrente em `posts` nao foi sincronizado

### Gaps de coleta nas ultimas 24h

```sql
SELECT post_id
FROM public.post_metrics_history
GROUP BY post_id
HAVING MAX(collected_at) < NOW() - INTERVAL '24 hours';
```

## Checks obrigatorios para o dashboard

Antes de usar rankings ou graficos como sinal de negocio, consultar:

```sql
SELECT *
FROM public.v_dashboard_data_quality_status;
```

Regra:

- se `is_analytics_ready = false`, o dashboard pode abrir, mas deve mostrar alerta de confiabilidade
- rankings devem ser interpretados como exploratorios ate os problemas serem corrigidos
- nenhuma decisao de marketing deve ser tomada sem validar os indicadores de qualidade
