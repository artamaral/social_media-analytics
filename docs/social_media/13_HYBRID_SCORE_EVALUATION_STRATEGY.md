# HYBRID SCORE EVALUATION STRATEGY

## Objetivo

Documentar a estrategia recomendada para avaliar um novo modelo de score hibrido sem dobrar custo de operacao.

Esta estrategia foi desenhada para o contexto atual do projeto:

- existe apenas um pipeline real de coleta
- nao e desejavel rodar dois Cloud Runs em paralelo
- o banco de dados principal contem os dados reais necessarios para comparacao

---

## Problema operacional

Se uma nova logica de score exigisse um segundo worker ativo em producao:

- haveria duplicacao de chamadas do Cloud Run
- haveria duplicacao de uso da YouTube Data API
- haveria duplicacao de writes no Supabase
- o custo operacional subiria de forma relevante

Por esse motivo, a validacao da logica `v2` nao deve depender de uma segunda execucao real de coleta.

---

## Estrategia recomendada

Usar um modelo de avaliacao em duas camadas:

1. pipeline real continua unico e inalterado
2. logica `v2` existe apenas como simulacao analitica no banco

Em vez de executar duas coletas, o projeto compara:

- lote atual do modelo ativo
- lote hipotetico do modelo `v2`

usando os mesmos dados reais ja existentes em:

- `posts`
- `post_metrics_history`
- `post_update_queue`

---

## Principio central

O objetivo inicial nao e medir custo de duas operacoes reais.

O objetivo inicial e responder:

- o novo modelo escolheria posts melhores?
- a distribuicao da fila ficaria mais equilibrada?
- posts pouco revisitados ganhariam prioridade?
- posts historicamente gigantes perderiam dominancia excessiva?

Essas perguntas podem ser respondidas por comparacao analitica, sem rodar um segundo pipeline.

---

## Arquitetura recomendada

### Modelo ativo

Continuar usando:

- view ativa da fila
- triggers ativos
- worker ativo

Estado atual apos a inclusao do guardrail:

- `public.v_post_update_queue_batch` e a fonte real do worker
- ate `4` slots sao reservados para cobertura minima
- os demais slots continuam usando o score ativo atual
- `priority_score_v2` nao participa da fila real

### Modelo candidato

Criar apenas objetos analiticos paralelos, por exemplo:

- `calculate_post_priority_v2(...)`
- `calculate_priority_band_v2(...)`
- `calculate_next_check_v2(...)`
- `v_post_update_queue_batch_v2`

Importante:

- esses objetos nao devem ser conectados ao worker
- eles nao devem gravar em `post_metrics_history`
- eles nao devem atualizar `post_update_queue`

Eles existem apenas para comparacao e simulacao.

---

## O que pode ser comparado sem segundo Cloud Run

### Distribuicao do lote

Comparar:

- lote do modelo atual
- lote do modelo `v2`

Perguntas:

- quantos posts se repetem?
- quantos posts novos entram no lote `v2`?
- quais bandas mudam?

### Cobertura da base

Comparar:

- posts com poucas checagens no modelo atual
- posts que o modelo `v2` passaria a promover

### Concentracao

Comparar:

- posts com checagem extrema
- impacto do `v2` sobre a dominancia desses posts

### Backlog teorico

Comparar:

- backlog por banda no modelo atual
- redistribuicao esperada no modelo `v2`

---

## O que esta estrategia nao mede diretamente

Sem um segundo worker real, a estrategia nao mede diretamente:

- custo real por execucao do Cloud Run com a nova logica
- uso real adicional da quota do YouTube
- latencia real de escrita no Supabase causada pela nova politica

No entanto, como o lote operacional continua com o mesmo tamanho e a mudanca inicial e apenas de criterio de selecao, esses impactos tendem a ser pequenos na fase analitica.

---

## Vantagens

- evita custo dobrado
- usa dados reais
- nao interrompe o pipeline ativo
- permite comparar modelos lado a lado
- facilita rollback, porque nada operacional muda nessa fase

---

## Limitacoes

- nao substitui validacao operacional final
- depende da qualidade do historico existente
- mede politica de selecao, nao impacto total de runtime

---

## Criterio para promover a mudanca

So vale considerar troca do modelo ativo se a simulacao mostrar melhora consistente em:

- rotacao de posts dentro da fila
- reducao de concentracao extrema
- promocao de posts com poucas checagens e bom potencial
- manutencao da cobertura de posts relevantes

### Etapas para o `v2` virar padrao

1. Recalibrar a formula

- abandonar ou corrigir a ponderacao direta atual
- testar alternativa aditiva com bonus calibrado
- garantir que `history_level = low` nao tenha vantagem sistematica sobre
  `full`

2. Validar em modo analitico

- comparar `v_post_update_queue_batch` contra `v_post_update_queue_batch_v2`
- medir overlap de lote
- medir troca de posts por banda
- medir impacto em posts hiperchecados
- medir se o guardrail continua protegido

3. Validar com dados exportados

- usar SQL para gerar comparativos
- analisar em Excel ou Pandas
- documentar ganhos e perdas

4. Promover apenas a parte normal da fila

- manter a fatia guardrail como regra independente
- trocar o criterio dos slots normais somente depois da validacao
- o desenho alvo seria:
  - `4` slots guardrail
  - `36` slots por score `v2` recalibrado

5. Rollback simples

- manter a view ativa versionada em SQL
- se o `v2` piorar cobertura ou concentracao, voltar ao `priority_score`
  atual

---

## Proxima etapa

Depois da estrategia definida, a validacao deve seguir um plano pratico com:

- queries SQL
- analise tabular em Excel ou Pandas

Referencia:

- [14_HYBRID_SCORE_VALIDATION_PLAN.md](C:/social_media-analytics/docs/social_media/14_HYBRID_SCORE_VALIDATION_PLAN.md:1)

---

## Status

Esta estrategia descreve como avaliar o modelo `v2` sem dobrar custo operacional.

Ainda nao representa implementacao aprovada do score hibrido.

