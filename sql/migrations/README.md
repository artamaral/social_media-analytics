# Migrations SQL

## Como usar
1. Executar primeiro o arquivo `_up.sql` no Supabase SQL Editor.
2. Validar funções, triggers e dados.
3. Se necessário, executar o `_down.sql` correspondente.

## Convenção de nomes
`YYYY-MM-DD_NNN_descricao_up.sql`
`YYYY-MM-DD_NNN_descricao_down.sql`

## Migrations
- `2026-04-17_001_queue_recheck_rules_up.sql`
  - Centraliza prioridade e rechecagem no SQL.
- `2026-04-17_001_queue_recheck_rules_down.sql`
  - Remove rechecagem automática por trigger.
