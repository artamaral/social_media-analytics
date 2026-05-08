# RESULTADO DAS QUERIES DE VALIDACAO DA FILA - 2026-05-08

## Objetivo

Registrar os resultados das queries propostas em:

- [07_QUEUE_VALIDATION_CHECKLIST.md](C:/social_media-analytics/sql/docs/07_QUEUE_VALIDATION_CHECKLIST.md:1)
- [08_QUEUE_CAPACITY_TEST.md](C:/social_media-analytics/sql/docs/08_QUEUE_CAPACITY_TEST.md:1)

Premissa desta avaliacao:

- o sistema ja executou por varios dias seguidos sem erro de execucao
- por isso, este registro foca no estado atual da fila e dos dados
- nao ha necessidade de organizar a leitura por rodadas de coleta

---

## Contexto

- Data da avaliacao: 2026-05-08
- Ambiente: producao
- Worker: Cloud Run
- Frequencia do worker: preencher
- Limite por execucao: 20
- Versao da fila: fatiada por bandas com leitura via `v_post_update_queue_batch`

---

## Como preencher

Para cada query:

- registrar o resultado resumido
- registrar a leitura objetiva
- se necessario, anotar observacoes

Ao final:

- consolidar a conclusao
- classificar o estado atual
- registrar a proxima acao sugerida

---

## Query 1. Fila renovando

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Validar se a fila esta sendo renovada

Resultado:

- Fila esta sendo renovada

Leitura:

- todos os post_id tem next_check > que last_chack e need_update = true

Observacoes:

- Funcionando como esperado

---

## Query 2. View retornando bandas diferentes

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Validar se a view da fila esta retornando itens de bandas diferentes

Resultado:

- todas as bandas tem post

Leitura:

- cada banda tem a quantidade de post conforme o definido

Observacoes:

- Funcionando conforme o esperado

---

## Query 3. Posts recentes com mais de uma coleta

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Validar se posts recentes passaram a ter mais de 1 coleta

Resultado:

- Todos os post tem mais de uma coleta

Leitura:

- 9 posts tem 58 coletas

Observacoes:

- Funcionando conforme o esperado

---

## Query 4. Filas sem post correspondente

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Fila sem post correspondente

Resultado:

- Resultado ok para todas as queries com excessao de post sem nova coleta. Isso pode se dever a serem post sem relevancia que acabam ficando para tras na prioridade. 

Leitura:

- 2172 posts dos ultimos dois dias em coleta recente

Observacoes:

- cehcar a relevancia desses 2172 post para avaliar se realmente nao deveria haver coleta.

---

## Query 5. Historico sem post correspondente

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Historico sem post correspondente

Resultado:

- 0

Leitura:

- 0 posts

Observacoes:

- Funcionando conforme o esperado

---

## Query 6. Queue com agendamento invalido

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Queue com agendamento invalido

Resultado:

- 0

Leitura:

- 0 posts

Observacoes:

- Funcionando conforme o esperado

---

## Query 7. Posts sem coleta recente

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Posts sem coleta recente

Resultado:

- Resultado ok para todas as queries com excessao de post sem nova coleta. Isso pode se dever a serem post sem relevancia que acabam ficando para tras na prioridade. 

Leitura:

- 2172 posts dos ultimos dois dias em coleta recente

Observacoes:

- checar a relevancia desses 2172 post para avaliar se realmente nao deveria haver coleta.

---

## Query 8. Backlog total

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Monitorar risco operacional da fila
- `08_QUEUE_CAPACITY_TEST.md` -> Teste 4

Resultado:

- 2181 itens vencidos

Leitura:

- existe backlog

Observacoes:

- havaliar se esta dentro do plano de priorizacao

---

## Query 9. Backlog por banda

Referencia:

- `07_QUEUE_VALIDATION_CHECKLIST.md` -> Monitorar backlog por banda
- `08_QUEUE_CAPACITY_TEST.md` -> Teste 4.1

Resultado:

- itens vencidos por banda paracem estar bem balanceados.

Leitura:

- existe itens vencidos

Observacoes:

- avaliar se esta dentro do plano de priorizacao

---

## Query 10. Itens elegiveis agora

Referencia:

- `08_QUEUE_CAPACITY_TEST.md` -> Teste 1

Resultado:

- 2181

Leitura:

- existe itens em espera elegiveis para outra coleta

Observacoes:

- avaliar se esta dentro do plano de priorizacao

---

## Query 11. Itens priorizados pela view

Referencia:

- `08_QUEUE_CAPACITY_TEST.md` -> Teste 2

Resultado:

- Tdos os itens tem next_cehck > last_check e de acordo com a banda reduz o intervalo entre last_check e next_check aumenta o que demonstra que a fila priorizacao esta ok.

Leitura:

- priorizacao por banda esta funcionado

Observacoes:

- Funcionando conforme o esperado

---

## Query 12. Distribuicao da fila por banda

Referencia:

- `08_QUEUE_CAPACITY_TEST.md` -> Teste 3

Resultado:

- Fila bem distribuida como esperado

Leitura:

- priorizacao por banda esta funcionado

Observacoes:

- Funcionando conforme o esperado

---

## Consolidacao final

### Estado da fila

- saudavel / ~~alerta / problema estrutural~~

### Status da validacao

- ~~validado~~
- validado com ressalvas
- ~~nao validado~~

### Evidencias principais

- preencher
- preencher
- preencher

### Proxima acao sugerida

- Reavaliar as metricas da fila, existem post com muitos dados e post com poucos dados.
Os posts com maior volume de checagens pertencem quase integralmente às bandas 6 e 5. Eles seguem com `needs_update = true`, `last_checked` recente e `next_check` curto, o que confirma que a fila está operando conforme a regra atual. A concentração de centenas de checagens em poucos posts indica que o comportamento atual não é falha de execução, mas efeito direto da política de priorização e agendamento. A rechecagem existe, porém a cobertura permanece desbalanceada.


---

## Atualizacao de status relacionada

Se a validacao for suficiente, atualizar tambem:

- [07_QUEUE_VALIDATION_CHECKLIST.md](C:/social_media-analytics/sql/docs/07_QUEUE_VALIDATION_CHECKLIST.md:1)

Modelo:

```text
Status: validado em producao
Data da validacao: 2026-05-08
Resultado: preencher resumo curto
```
