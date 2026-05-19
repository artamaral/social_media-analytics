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

---

## Encerramento operacional da fase 1 - 2026-05-17

Depois das rodadas adicionais e da validacao do scheduler com logs persistentes,
a fase 1 do backfill legado foi considerada encerrada.

### Estado final observado do legado

| low_type   | total_checagens | history_level | total_posts |
| ---------- | --------------- | ------------- | ----------- |
| legacy_low | 0               | low           | 2           |
| legacy_low | 1               | low           | 1           |
| legacy_low | 2               | full          | 1034        |
| legacy_low | 2               | partial       | 239         |

### Leitura

- `legacy_low` residual: `3`
- composicao residual:
  - `2` posts com `0` checagens
  - `1` post com `1` checagem
- nao houve mais mudanca relevante entre leituras consecutivas
- o log do script passou a mostrar apenas `3` candidatos, confirmando que o
  passivo legado foi praticamente drenado

### Interpretacao

- a fase 1 cumpriu seu objetivo operacional
- o principal passivo legado deixou de ser um bloqueio
- o `low` remanescente da base passa a ser explicado majoritariamente por
  `bootstrap_low`
- a proxima frente tecnica deve sair de drenagem legado e ir para:
  - fase 2 de promocao de estado
  - tratamento de posts novos em `bootstrap_low`

### Decisao operacional

- pausar o scheduler da fase 1
- preservar logs como evidencia da ultima rodada
- tratar novas execucoes apenas como corretivas, se necessario

---

## Atualizacao de acompanhamento - 2026-05-15

Depois de aproximadamente `12h` com o scheduler executando a fase 1 do
backfill offline, foram observados os resultados abaixo.

### Resultado 4. Distribuicao atual de `history_level`

| history_level | total_posts |
| ------------- | ----------- |
| full          | 1785        |
| low           | 636         |
| partial       | 7           |

### Leitura

- a maior parte da base continua em `full`
- ainda existe um bloco relevante em `low`
- o grupo `partial` ainda e muito pequeno
- isso confirma que a fase 1 esta semeando historico, mas ainda nao esta
  promovendo estado de forma ampla

### Resultado 5. Distribuicao atual de `total_checagens`

| total_checagens | total_posts |
| --------------- | ----------- |
| 1               | 165         |
| 2               | 1033        |
| 3               | 230         |
| 4               | 16          |
| 5               | 184         |
| 6               | 84          |
| 7               | 5           |
| 8               | 12          |
| 9               | 13          |
| 10              | 3           |
| 11              | 9           |
| 12              | 6           |
| 13              | 22          |
| 14              | 61          |
| 15              | 31          |
| 16              | 1           |
| 18              | 2           |
| 19              | 5           |
| 20              | 2           |
| 22              | 3           |
| 23              | 26          |
| 24              | 8           |
| 43              | 1           |
| 82              | 1           |
| 92              | 1           |
| 97              | 1           |
| 173             | 1           |
| 181             | 1           |
| 185             | 1           |
| 203             | 1           |
| 261             | 6           |
| 265             | 2           |
| 273             | 1           |
| 277             | 1           |
| 281             | 7           |
| 442             | 1           |
| 446             | 1           |
| 455             | 1           |
| 605             | 8           |

### Leitura

- existe agora um bloco muito forte em `2` checagens (`1033` posts)
- isso e compativel com a hipotese de que a fase 1 conseguiu distribuir o seed
  historico em massa
- ainda permanecem `165` posts com apenas `1` checagem
- a cauda longa de posts hiperchecados permanece, mas nao invalida o objetivo
  do backfill legado

### Resultado 6. Contagem atual de `legacy_low`

- `legacy_low` atual: `447`

### Leitura

- houve nova reducao em relacao ao marco anterior de `474`
- a fase 1 continua produzindo drenagem do passivo legado
- a tarefa ainda nao pode ser considerada concluida

---

## Baseline para avaliacao no dia seguinte

Para avaliar o ganho real do `legacy_low` na proxima verificacao, usar estes
numeros como referencia:

- `legacy_low`: `447`
- `history_level = low`: `636`
- `history_level = partial`: `7`
- posts com `2` checagens: `1033`
- posts com `1` checagem: `165`

### Sinal positivo esperado na proxima leitura

- nova reducao de `legacy_low`
- reducao do bloco de `1` checagem
- aumento adicional do bloco de `2` checagens ou superior
- aumento gradual de `partial`

### Sinal de alerta

- `legacy_low` estagnar perto do valor atual
- bloco de `1` checagem parar de cair
- `partial` permanecer praticamente nulo mesmo apos novas rodadas

---

## Atualizacao de diretriz operacional - 2026-05-16

### Mudanca de foco da fase 1

Com base nos resultados parciais da execucao continua, a fase 1 passa a ter
foco mais direcionado nos posts com:

- `0` checagens
- `1` checagem
- `2` checagens

Motivo:

- esse conjunto representa os posts ainda mais proximos do estado sem contexto
- o objetivo imediato continua sendo reduzir o `legacy_low`
- neste momento, atacar esse grupo e mais importante do que continuar dando
  contexto adicional para posts ja mais distantes do estado inicial

### Impacto esperado dessa mudanca

- reduzir mais rapidamente o bloco residual de `low`
- acelerar a migracao de posts de `0` para `1` e de `1` para `2+` checagens
- deixar a base mais limpa para discutir a fase 2

### Regra operacional atual da selecao

Neste momento, a selecao da fase 1 deve seguir:

1. `total_checagens asc`
2. `priority_score_v2 desc`
3. `collected_at asc nulls first`
4. `post_id`

Interpretacao:

- primeiro entram os posts com `0` checagens
- depois os com `1`
- depois os com `2`
- dentro de cada grupo, entram antes os de maior `priority_score_v2`

### Observacao sobre o custo da API

Foi observado pela manha de `2026-05-16` que o consumo de tokens/quota da API
do YouTube permanecia baixo mesmo com execucao automatica a cada `10` minutos.

Interpretacao:

- nao ha bloqueio operacional imediato de quota para intensificar a fase 1
- a frequencia mais alta e aceitavel neste momento para reduzir o passivo
  legado antes de avancar
