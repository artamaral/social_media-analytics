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
