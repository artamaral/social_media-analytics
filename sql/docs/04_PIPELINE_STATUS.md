# PIPELINE STATUS

## Visao geral

Este arquivo registra o estado operacional atual dos pipelines e rotinas de
coleta do projeto.

O objetivo e manter uma leitura simples de:

- o que esta rodando
- o que foi validado
- o que ainda esta em execucao controlada
- o que bloqueia a proxima etapa

---

## 1. Scraper principal

- Status: operacional
- Implementacao principal: `scripts/youtube_main_scraper/main.py`
- Objetivo: descoberta e ingestao principal de posts
- Observacao: continua sendo a origem normal de novos posts e alimenta a fila

---

## 2. Worker de metricas de posts

- Status: operacional
- Implementacao principal: `scripts/cloud_run/postMetrics/main.py`
- Fonte da fila: `public.v_post_update_queue_batch`
- Lote atual: `40` posts por execucao
- Validacao de custo: sem aumento relevante de custo no Cloud Run apos alguns dias em producao

### Comportamento validado

- leitura da fila via view fatiada
- `next_check` controlado no SQL
- FIFO dentro da banda
- refill global entre bandas quando ha sobra de cota

---

## 3. Backfill offline de `legacy_low` - fase 1

- Status: concluida
- Implementacao: `scripts/offline_backfill/legacy_low_backfill_phase1.py`
- Launcher agendado: `scripts/offline_backfill/run_legacy_low_backfill_phase1.ps1`
- Objetivo: inserir 1 snapshot inicial para posts antigos com historico insuficiente
- Escopo: apenas `legacy_low`
- Prioridade de selecao:
  - `total_checagens asc`
  - `priority_score_v2 desc`
- Tamanho do lote: `50`
- Frequencia atual do scheduler: `10` minutos
- Observacao de custo: consumo observado da API do YouTube segue baixo nesta frequencia
- Observacao operacional: logs por execucao agora sao obrigatorios em
  `scripts/offline_backfill/logs`

### Resultado da primeira execucao validada

- Ultimo snapshot inserido: `2026-05-14 21:27:43.970034`
- `legacy_low` antes: `511`
- `legacy_low` depois: `474`
- Reducao observada: `37`

### Interpretacao

- a fase 1 esta funcionando como esperado
- os snapshots foram inseridos em `post_metrics_history`
- os posts atendidos continuam `history_level = low`, o que e esperado nesta fase
- o objetivo imediato continua sendo reduzir o passivo legado, nao promover estado

### Encerramento da fase 1

- `legacy_low` residual observado: `3`
- composicao residual:
  - `legacy_low` com `0` checagens: `2`
  - `legacy_low` com `1` checagem: `1`
- os logs da execucao passaram a mostrar apenas `3` candidatos
- a fase 1 cumpriu o objetivo de drenar o passivo legado relevante
- o `low` remanescente da base passa a ser explicado principalmente por
  `bootstrap_low`, nao por backlog legado

### Trabalho restante antes da fase 2

- manter a fase 1 pausada, salvo necessidade de rodada corretiva pontual
- detalhar a fase 2 de promocao de estado para os legados agora com contexto
- desenhar o bootstrap de posts novos, que passa a ser a principal fonte de
  `low`
- acompanhar logs do scheduler junto com inserts no banco em qualquer futura
  retomada

### Atualizacao observada apos aproximadamente 12h

- `legacy_low` atual: `447`
- distribuicao atual de `history_level`:
  - `full`: `1785`
  - `low`: `636`
  - `partial`: `7`
- distribuicao de checagens:
  - principal concentracao atual em `2` checagens: `1033` posts
  - ainda existem `165` posts com `1` checagem

### Interpretacao da atualizacao

- a fase 1 segue drenando o passivo legado
- o seed historico em massa parece estar funcionando
- a promocao para `partial` ainda e residual, o que continua coerente com o
  desenho atual
- a estrategia passa a priorizar explicitamente posts com `0`, `1` e `2`
  checagens, nessa ordem, usando `priority_score_v2` como criterio secundario
  para acelerar a reducao do `legacy_low`

### Estimativa operacional atual

- base inicial de `legacy_low`: `511`
- lote configurado: `50`
- execucoes necessarias estimadas: aproximadamente `11`
- execucoes validadas ate agora: `1`
- execucoes ainda pendentes estimadas: aproximadamente `10`

---

## 4. Proximos checkpoints operacionais

### Guarda de cobertura minima

- especificacao registrada em:
  - `sql/docs/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md`
- objetivo:
  - impedir que posts com menos de `3` checagens fiquem para tras
- proximo passo:
  - aplicar e validar no banco a nova versao de `v_post_update_queue_batch`
  - manter `bootstrap_low`, `at_risk_bootstrap` e `recovery_low` apenas como
    diagnosticos de monitoramento
  - acompanhar se a fatia de `4` slots e suficiente para manter o guardrail sob controle

### Backfill legado fase 1

- confirmar reducao continua do `legacy_low`
- confirmar reducao dos blocos de `0`, `1` e `2` checagens
- confirmar inserts recorrentes em `post_metrics_history`
- confirmar que a selecao continua aderente a `total_checagens asc` e
  `priority_score_v2 desc`

### Fase 2 do legado

- desbloqueada do ponto de vista operacional
- depende agora de definicao da estrategia de promocao temporal entre snapshots
- baseline inicial registrado em:
  - `sql/docs/24_PHASE2_INITIAL_DATA_BASELINE_2026-05-17.md`

---

## 5. Problemas conhecidos

- posts seedados pela fase 1 nao saem imediatamente de `low`
- o `bootstrap_low` continua sendo a principal fonte de `low`
- sem guarda de cobertura minima, posts com menos de `3` checagens podem ficar
  para tras e recriar `legacy_low`
- a fase 2 ainda nao foi iniciada
- houve um incidente operacional no scheduler do Windows:
  - a tarefa ficou com a acao malformada
  - o script manual rodava, mas a execucao agendada falhava
  - a ausencia de log persistente atrasou o diagnostico

### Mitigacao aplicada

- a tarefa foi recriada com comando corrigido
- o launcher passou a gravar log por execucao e um arquivo `latest`
- troubleshooting de scheduler agora exige:
  - checar `Last Result`
  - checar log mais recente
  - checar novos inserts em `post_metrics_history`

---

## 6. Ultima verificacao manual

- Data: `2026-05-17`
- Resultado:
  - o script continua funcionando manualmente
  - o scheduler foi corrigido e passou a gerar log persistente por execucao
  - a fase 1 foi considerada encerrada com `legacy_low = 3`
  - o bloco residual de legado ficou em:
    - `0` checagens: `2`
    - `1` checagem: `1`
  - o foco operacional seguinte deixa de ser drenagem legado e passa a ser:
    - fase 2 do legado
    - implementacao do guarda de cobertura minima com regra `total_checagens < 3`
