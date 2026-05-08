# HYBRID PRIORITY SCORE SPECIFICATION

## Objetivo

Definir uma proposta tecnica para substituir o modelo atual de prioridade baseado apenas em score acumulado por um modelo hibrido que combine:

- popularidade estrutural
- crescimento recente
- aceleracao do crescimento

O objetivo de negocio e reduzir o efeito de concentracao permanente em posts historicamente grandes, sem perder a capacidade de identificar posts relevantes e tendencias emergentes.

Escopo atual desta especificacao:

- definir o modelo `v2` em modo analitico
- nao substituir a logica ativa do worker neste momento
- permitir comparacao com dados reais sem segundo Cloud Run

---

## Problema do modelo atual

O modelo atual privilegia o acumulado total de interacoes.

Exemplo conceitual:

```text
views + likes * 10 + comments * 20
```

Esse desenho mede principalmente popularidade historica.

Consequencias:

- posts grandes tendem a permanecer dominando a fila
- o sistema responde pouco a mudancas recentes
- tendencia emergente pode demorar para entrar no radar
- o comportamento favorece efeito de "rich get richer"

---

## Objetivo do modelo hibrido

O novo modelo precisa equilibrar:

1. relevancia historica
2. atividade recente
3. mudanca de ritmo da atividade

Perguntas que o score final deve responder:

- o post ja provou ser importante?
- o post esta crescendo agora?
- esse crescimento esta acelerando?

---

## Entradas necessarias

### Tabela `posts`

Campos esperados:

- `post_id`
- `views`
- `likes`
- `comments`
- `collected_at`

Uso:

- snapshot atual do post

### Tabela `post_metrics_history`

Campos esperados:

- `post_id`
- `collected_at`
- `views`
- `likes`
- `comments`

Uso:

- historico temporal para calcular velocidade e aceleracao

### Observacao de implementacao

Para a avaliacao `v2`, o modelo usa:

- `posts` como snapshot atual do post
- `post_metrics_history` para buscar snapshots anteriores

Essa decisao evita duplicar coleta e mantem a avaliacao no banco, em modo analitico.

---

## Componente 1. Base popularity

### Definicao

Medida de relevancia estrutural acumulada do post.

### Formula proposta

```text
base_popularity =
  ln(views + 1)
  + 10 * ln(likes + 1)
  + 20 * ln(comments + 1)
```

### Razao

- preserva a nocao de tamanho historico do post
- evita crescimento linear infinito do score
- reduz o poder excessivo de outliers muito grandes

### Interpretacao

Responde:

- "este post ja provou relevancia no geral?"

---

## Componente 2. Velocity

### Definicao

Medida de crescimento recente por unidade de tempo.

### Janela sugerida

- janela curta de 6 horas

### Formulas conceituais

```text
views_velocity_6h =
  (views_now - views_6h) / horas_entre_coletas

likes_velocity_6h =
  (likes_now - likes_6h) / horas_entre_coletas

comments_velocity_6h =
  (comments_now - comments_6h) / horas_entre_coletas
```

```text
velocity_raw =
  views_velocity_6h
  + 10 * likes_velocity_6h
  + 20 * comments_velocity_6h
```

```text
velocity_score =
  ln(greatest(velocity_raw, 0) + 1)
```

### Razao

- mede o ritmo atual de crescimento do post
- permite capturar tendencia recente
- evita depender apenas do acumulado historico

### Interpretacao

Responde:

- "este post esta ganhando atencao agora?"

---

## Componente 3. Acceleration

### Definicao

Medida da mudanca da velocidade.

Velocity mostra se o post cresce.
Acceleration mostra se o post esta crescendo mais rapido do que antes.

### Janelas sugeridas

- velocidade curta: 6 horas
- velocidade longa: 24 horas

### Formula conceitual

```text
acceleration_raw =
  velocity_raw_6h - velocity_raw_24h
```

```text
acceleration_score =
  ln(greatest(acceleration_raw, 0) + 1)
```

### Razao

- diferencia um post forte de um post em explosao
- permite detectar tendencia emergente antes que ela apareca apenas no acumulado
- funciona como bonus de "trending"

### Interpretacao

Responde:

- "o crescimento deste post esta ganhando forca?"

---

## Formula final

### Caso 1. Historico completo

Condicao:

- existe historico suficiente para calcular velocity de 6h
- existe historico suficiente para calcular acceleration com base em 24h

Formula:

```text
final_score =
  0.40 * base_popularity
  + 0.40 * velocity_score
  + 0.20 * acceleration_score
```

### Justificativa dos pesos

#### 0.40 Base popularity

- ancora o modelo em relevancia estrutural
- evita que ruido de curto prazo domine o score

#### 0.40 Velocity

- da o mesmo peso para crescimento recente
- torna o sistema responsivo ao momento atual

#### 0.20 Acceleration

- adiciona sensibilidade a tendencia emergente
- recebe peso menor por ser sinal mais ruidoso

---

## Mapeamento inicial de bandas para `v2`

Para permitir execucao analitica e comparacao com o modelo atual, a proposta `v2` usa um mapeamento inicial de `final_score` para bandas:

- banda `6`: `>= 120`
- banda `5`: `>= 90`
- banda `4`: `>= 70`
- banda `3`: `>= 50`
- banda `2`: `>= 35`
- banda `1`: abaixo de `35`

Importante:

- esses cortes sao provisórios
- foram definidos para permitir experimentacao inicial
- devem ser recalibrados com distribuicao real do `priority_score_v2`

### Agendamento inicial de `v2`

Na simulacao analitica, o `v2` usa o mesmo modelo conceitual de bandas para agendamento:

- banda `6` -> `30 minutes`
- banda `5` -> `1 hour`
- banda `4` -> `2 hours`
- banda `3` -> `4 hours`
- banda `2` -> `8 hours`
- banda `1` -> `12 hours`

Objetivo:

- isolar o efeito da nova formula de score
- sem introduzir outra mudanca estrutural ao mesmo tempo

---

## Regra de fallback

### Caso 2. Historico parcial

Condicao:

- existe historico suficiente para velocity
- nao existe historico suficiente para acceleration

Formula:

```text
final_score =
  0.60 * base_popularity
  + 0.40 * velocity_score
```

### Razao

- mantem estabilidade quando acceleration nao pode ser calculada
- ainda permite que crescimento recente influencie a prioridade

### Caso 3. Historico insuficiente

Condicao:

- nao existe historico suficiente para velocity

Formula:

```text
final_score = base_popularity
```

### Razao

- posts novos ou com pouca coleta ainda precisam entrar na fila
- o sistema nao deve depender de historico completo para funcionar

---

## Esquema operacional do fluxo

```text
1. Ler snapshot atual do post
2. Buscar historico recente em post_metrics_history
3. Classificar nivel de historico:
   - full
   - partial
   - low
4. Calcular base_popularity
5. Se houver historico:
   - calcular velocity
6. Se houver historico suficiente:
   - calcular acceleration
7. Aplicar formula correspondente
8. Gerar final_score
9. Converter final_score em banda
10. Converter banda em next_check
11. Comparar com o modelo ativo em modo analitico

Observacao:

- nesta fase, o fluxo `v2` nao atualiza `post_update_queue`
- o modelo `v2` existe apenas para comparacao
```

---

## Exemplo intuitivo

### Post A

- muito grande historicamente
- crescimento recente baixo
- aceleracao baixa

Resultado esperado:

- continua relevante
- perde dominancia excessiva

### Post B

- tamanho medio
- crescimento recente forte
- aceleracao positiva

Resultado esperado:

- sobe na fila
- recebe mais atencao operacional

### Post C

- pequeno historicamente
- crescimento recente muito forte
- aceleracao muito alta

Resultado esperado:

- entra no radar mais cedo
- pode ganhar prioridade mesmo sem acumulado gigante

---

## Beneficios esperados

- reduzir a concentracao permanente em posts historicamente grandes
- aumentar sensibilidade a mudancas recentes
- melhorar cobertura de conteudo emergente
- equilibrar relevancia historica com tendencia atual
- tornar a fila mais alinhada com dinamica real de crescimento

No contexto atual do projeto, ha um beneficio adicional:

- validar a politica `v2` sem dobrar custo operacional

---

## Riscos e observacoes

- velocity e acceleration dependem de historico suficientemente denso
- posts com pouca coleta dependerao mais de fallback
- acceleration pode ser ruidosa em posts muito pequenos
- pesos e janelas devem ser recalibrados apos observacao em producao

---

## Decisoes pendentes

- janelas definitivas para velocity e acceleration
- criterio minimo de historico para sair do fallback
- recalibracao dos cortes provisórios de banda
- politica de rollout e validacao comparativa com o modelo atual
- decisao final sobre promocao do `v2` para logica ativa

---

## Status

Esta especificacao descreve a proposta conceitual do novo modelo.

Existe implementacao `v2` apenas em modo analitico para comparacao com dados reais.

Ainda nao representa logica aprovada para substituir o modelo ativo.
