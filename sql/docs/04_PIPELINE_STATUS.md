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

- Status: em andamento
- Implementacao: `scripts/offline_backfill/legacy_low_backfill_phase1.py`
- Objetivo: inserir 1 snapshot inicial para posts antigos com historico insuficiente
- Escopo: apenas `legacy_low`
- Prioridade de selecao: `priority_score_v2 desc`
- Tamanho do lote: `50`

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

### Trabalho restante antes da fase 2

- continuar executando a fase 1 em lotes
- reduzir `legacy_low` progressivamente para perto de zero
- so depois detalhar e executar a fase 2 de promocao de estado

### Estimativa operacional atual

- base inicial de `legacy_low`: `511`
- lote configurado: `50`
- execucoes necessarias estimadas: aproximadamente `11`
- execucoes validadas ate agora: `1`
- execucoes ainda pendentes estimadas: aproximadamente `10`

---

## 4. Proximos checkpoints operacionais

### Backfill legado fase 1

- confirmar reducao continua do `legacy_low`
- confirmar inserts recorrentes em `post_metrics_history`
- confirmar que a selecao continua aderente a `priority_score_v2`

### Fase 2 do legado

- permanece bloqueada ate o fechamento da fase 1
- depende de nova janela temporal util entre snapshots

---

## 5. Problemas conhecidos

- ainda existe passivo de `legacy_low`
- posts seedados pela fase 1 nao saem imediatamente de `low`
- a fase 2 ainda nao foi iniciada

---

## 6. Ultima verificacao manual

- Data: `2026-05-14`
- Resultado:
  - backfill offline executado com sucesso
  - historico atualizado
  - passivo legado reduzido
  - atividade segue em andamento ate completar as rodadas restantes
