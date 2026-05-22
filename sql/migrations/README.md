# Migrations SQL

## Como usar

1. Executar primeiro o arquivo `_up.sql` no Supabase SQL Editor.
2. Validar funcoes, triggers, views, indices e dados.
3. Se necessario, executar o `_down.sql` correspondente.

## O que sao arquivos up e down

Migrations existem para aplicar mudancas no banco de forma rastreavel e
reversivel.

O arquivo `_up.sql` aplica a mudanca planejada. Ele pode criar tabelas,
adicionar colunas, criar indices, funcoes, triggers ou views.

O arquivo `_down.sql` desfaz a mudanca aplicada pelo `_up.sql`. Ele deve ser
usado apenas como rollback controlado quando a alteracao causar problema ou
quando for necessario voltar o banco ao estado anterior.

Fluxo recomendado:

1. Revisar o `_up.sql`.
2. Executar o `_up.sql`.
3. Validar o resultado no banco.
4. Manter o `_down.sql` como plano de retorno.
5. Executar o `_down.sql` somente se houver necessidade real de rollback.

Exemplo:

```text
2026-05-22_003_creator_metrics_history_up.sql
```

Aplica a criacao do historico de metricas de creators.

```text
2026-05-22_003_creator_metrics_history_down.sql
```

Remove essa estrutura caso seja necessario desfazer a mudanca.

Antes de executar qualquer `_down.sql`, avaliar perda de dados. Rollbacks que
removem tabelas ou colunas tambem removem os dados armazenados nelas.

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
