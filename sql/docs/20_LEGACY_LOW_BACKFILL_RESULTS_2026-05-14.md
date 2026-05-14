# LEGACY LOW BACKFILL RESULTS - 2026-05-14

## Objetivo desta execucao

Registrar os resultados observados na primeira execucao validada da fase 1 do
backfill offline de `legacy_low`.

Escopo desta rodada:

- inserir 1 snapshot inicial para posts `legacy_low`
- validar que o script escreve corretamente em `post_metrics_history`
- validar que o passivo legado comeca a cair
- validar que a selecao continua coerente com `priority_score_v2`

---

## Contexto operacional

- Script: `scripts/offline_backfill/legacy_low_backfill_phase1.py`
- Fonte de selecao: `legacy_low` ordenado por `priority_score_v2 desc`
- Tamanho do lote configurado: `50`
- Fase avaliada: fase 1

Observacao:

- esta rodada nao tem como objetivo tirar posts de `low`
- esta rodada tem como objetivo semear historico

---

## Resultado 1. Insercao no historico

### Evidencia

- ultimo `collected_at` observado em `post_metrics_history`:
  - `2026-05-14 21:27:43.970034`

### Leitura

- o script inseriu novos snapshots com sucesso
- os registros mais recentes de `post_metrics_history` batem com a execucao do backfill

---

## Resultado 2. Reducao de `legacy_low`

### Valores observados

- `legacy_low` antes da execucao: `511`
- `legacy_low` depois da execucao: `474`
- reducao observada: `37`

### Leitura

- a fase 1 produziu reducao real do passivo legado
- o comportamento esta alinhado com a expectativa da especificacao
- a base ainda nao foi regularizada por completo

---

## Resultado 3. Coerencia da selecao por `priority_score_v2`

### Evidencia resumida

Os posts observados no topo da validacao apresentaram:

- `total_checagens = 1` para varios dos itens processados nesta rodada
- `history_level = low`
- `collected_at` recente e coerente com a execucao
- `priority_score_v2` alto dentro do conjunto `legacy_low`

Exemplos observados:

- `yNn0jl4u41o` -> `priority_score_v2 = 221.24714873854`
- `dqWr5Aw_Ifw` -> `priority_score_v2 = 216.754762116684`
- `nIlVxInp4Pg` -> `priority_score_v2 = 215.751452934247`
- `L8A8X25mS4A` -> `priority_score_v2 = 208.19814494861`
- `aEJGRo27lqI` -> `priority_score_v2 = 201.898160221325`

### Leitura

- a rodada esta aderente ao criterio de selecao definido para a fase 1
- o script esta priorizando os `legacy_low` mais fortes segundo `priority_score_v2`
- a logica de banda nao esta sendo usada, conforme especificacao

---

## Interpretacao geral

Esta primeira execucao valida os objetivos principais da fase 1:

- o script roda com sucesso
- o historico entra em `post_metrics_history`
- o passivo de `legacy_low` comeca a cair
- a selecao observada e coerente com a regra documentada

Ao mesmo tempo, o resultado confirma o comportamento esperado desta fase:

- os posts continuam `history_level = low`
- a fase 1 prepara a base
- a promocao de estado continua sendo assunto da fase 2

---

## Status da tarefa

- fase 1: iniciada e validada
- fase 1: ainda nao concluida
- fase 2: nao iniciada

---

## Trabalho restante

Com base na base inicial e no lote atual:

- `legacy_low` inicial: `511`
- lote alvo por execucao: `50`

Estimativa operacional:

- execucoes totais aproximadas para cobrir a base inicial: `11`
- execucoes concluidas e validadas: `1`
- execucoes restantes aproximadas: `10`

Diretriz:

- continuar a fase 1 ate reduzir `legacy_low` para perto de zero
- nao iniciar fase 2 antes de concluir essa limpeza inicial

---

## Conclusao

Resultado da rodada: validado com sucesso.

Conclusao operacional:

- o backfill offline da fase 1 esta funcionando
- o foco agora e repetir a rotina ate fechar a maior parte do passivo legado
- a fase 2 permanece pendente e so deve ser detalhada depois do encerramento da fase 1
