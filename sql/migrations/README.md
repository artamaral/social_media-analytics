# Migrations SQL

## Como usar

1. Executar primeiro o arquivo `_up.sql` no Supabase SQL Editor.
2. Validar funcoes, triggers, views, indices e dados.
3. Se necessario, executar o `_down.sql` correspondente.

## Convencao de nomes

```text
YYYY-MM-DD_NNN_descricao_up.sql
YYYY-MM-DD_NNN_descricao_down.sql
```

## Migrations

- `2026-04-17_001_queue_recheck_rules_up.sql`
  - Centraliza prioridade e rechecagem no SQL.
- `2026-04-17_001_queue_recheck_rules_down.sql`
  - Remove rechecagem automatica por trigger.
- `2026-05-08_002_dashboard_on_demand_indexes_up.sql`
  - Cria indices para leituras sob demanda do dashboard online.
- `2026-05-08_002_dashboard_on_demand_indexes_down.sql`
  - Remove indices criados para o dashboard online.
- `2026-05-22_003_creator_metrics_history_up.sql`
  - Cria historico de metricas de creators, campos correntes em `creators` e trigger de sincronizacao.
- `2026-05-22_003_creator_metrics_history_down.sql`
  - Remove historico de metricas de creators, trigger e campos correntes adicionados.
- `2026-06-15_004_queue_next_check_age_coverage_up.sql`
  - Adiciona regra de `next_check` por idade do post e cobertura historica, ajusta trigger da fila, recalcula `next_check` existente e cria `v_dashboard_queue_bottleneck_status`.
- `2026-06-15_004_queue_next_check_age_coverage_down.sql`
  - Remove a view de gargalo da fila, remove a regra por idade/cobertura e volta o trigger para a regra baseada apenas em `priority_score`.
- `2026-06-15_005_dashboard_queue_batch_timezone_up.sql`
  - Cria `v_dashboard_post_update_queue_batch` com horarios da fila em UTC e America/Sao_Paulo, sem alterar a view operacional do worker.
- `2026-06-15_005_dashboard_queue_batch_timezone_down.sql`
  - Remove a view de dashboard com conversao explicita de timezone da fila.
- `2026-06-15_006_post_update_queue_next_check_timestamptz_up.sql`
  - Converte `post_update_queue.next_check` para `timestamp with time zone`, preservando valores existentes como UTC e recriando views dependentes.
- `2026-06-15_006_post_update_queue_next_check_timestamptz_down.sql`
  - Rollback bloqueado por seguranca; a reversao exige recriar views dependentes manualmente.
- `2026-06-15_007_queue_batch_50_guardrail_overflow_up.sql`
  - Alinha a fila operacional ao lote de 50, amplia guardrail protegido para 6 e inclui guardrail excedente no refill global.
- `2026-06-15_007_queue_batch_50_guardrail_overflow_down.sql`
  - Reverte a fila para o contrato anterior de lote 40 sem overflow de guardrail.
- `2026-06-16_008_queue_next_check_84h_rebucket_up.sql`
  - Aplica a regra final da Sprint 2: `84h` para warm/old com `21+` checagens, recalcula a fila existente e estreita o breakdown operacional de cobertura.
- `2026-06-16_008_queue_next_check_84h_rebucket_down.sql`
  - Restaura a regra anterior de `12h/24h` para warm/old cobertos e o breakdown antigo de cobertura.
- `2026-06-20_009_discovery_status_posts_evidence_up.sql`
  - Ajusta o status do discovery para usar `posts.created_at` como evidencia de resultado, mantendo `creator_metrics_history` como fallback legado.
- `2026-06-20_009_discovery_status_posts_evidence_down.sql`
  - Restaura a regra anterior de discovery baseada apenas em `creator_metrics_history`.
