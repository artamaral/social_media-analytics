# LOW HISTORY BOOTSTRAP AND BACKFILL SPECIFICATION

## Objetivo

Definir uma estrategia tecnica para tratar dois tipos diferentes de posts com pouco historico:

1. posts novos que ainda nao tiveram tempo de gerar historico
2. posts legados que deveriam ter historico, mas ficaram sem cobertura suficiente

Essa separacao e necessaria porque ambos aparecem como `low`, mas representam problemas diferentes.

---

## Problema

No modelo hibrido, posts com pouco historico tendem a cair no fallback.

Sem tratamento adicional, isso cria dois riscos:

- posts novos entram como `low` e podem nunca ganhar historico suficiente para sair desse estado
- posts antigos sem historico contaminam a avaliacao do modelo, porque misturam cold start com falha operacional passada

Isso torna o grupo `low` heterogeneo demais e dificulta tanto o ranking quanto a interpretacao dos dados.

---

## Separacao conceitual do grupo `low`

### Classe 1. `bootstrap_low`

Definicao:

- post novo
- pouco ou nenhum historico
- estado natural de cold start

Interpretacao:

- nao e erro
- e um item que ainda precisa ser observado para gerar dados

### Classe 2. `legacy_low`

Definicao:

- post nao novo
- historico insuficiente
- estado causado por cobertura incompleta do pipeline anterior

Interpretacao:

- nao e um cold start legitimo
- e uma divida operacional de historico

---

## Objetivo da politica de bootstrap

Garantir que todo post novo receba observacao inicial suficiente para:

- deixar de ser um `low` permanente
- gerar pelo menos os primeiros snapshots
- permitir que velocity e acceleration possam existir no futuro

Sem isso, o modelo hibrido corre o risco de nunca descobrir se o post novo esta acelerando.

---

## Objetivo da politica de backfill legado

Regularizar a base antiga para que:

- posts legados sem historico nao permaneçam misturados com cold start
- o modelo hibrido seja avaliado em base menos contaminada
- posts antigos relevantes recuperem historico minimo utilizavel

---

## Politica proposta para posts novos

### Principio

Todo post novo deve passar por uma fase explicita de descoberta.

Durante essa fase:

- ele nao deve depender do score hibrido completo
- ele precisa de uma politica minima de observacao

### Estado operacional sugerido

Nome conceitual:

- `bootstrap_low`

### Regra de entrada

Um post entra em bootstrap quando:

- foi criado recentemente
- ainda nao possui historico suficiente

Exemplos de criterio:

- `created_at` dentro de uma janela inicial
- `total_checagens < N`

### Objetivo da fase

Gerar:

- 1 snapshot inicial
- depois mais 1 ou 2 snapshots adicionais

Isso permite sair do estado:

- "nao tenho historico algum"

para o estado:

- "ja tenho dados minimos para medir crescimento"

### Resultado esperado

- posts novos deixam de se perder na fila
- o sistema reduz o risco de cegueira sobre tendencias emergentes

---

## Politica proposta para posts legados

### Principio

Posts antigos sem historico nao devem competir como se fossem apenas novos.

Eles precisam de um tratamento corretivo, nao apenas de discovery continuo.

### Estado operacional sugerido

Nome conceitual:

- `legacy_low`

### Regra de entrada

Um post entra nessa classe quando:

- nao e novo
- nao possui historico suficiente

### Objetivo da fase

Construir historico minimo para regularizar o post.

### Estrategia recomendada

Executar um processo offline de backfill:

- sem alterar o pipeline principal
- sem depender de uma segunda rotina continua
- usando lote controlado e priorizacao

### Resultado esperado

- posts antigos deixam de ficar presos como `low`
- a avaliacao do score hibrido fica mais confiavel

---

## Diferenca entre os dois tratamentos

### Bootstrap de novos posts

- recorrente
- faz parte do desenho normal do sistema
- existe para gerar os primeiros dados

### Backfill de legados

- corretivo
- extraordinario ou eventual
- existe para limpar divida historica

---

## Fluxo conceitual

```text
post_id
  -> tem historico suficiente?
     -> sim:
        entra no modelo hibrido normal
     -> nao:
        -> post e novo?
           -> sim:
              tratar como bootstrap_low
           -> nao:
              tratar como legacy_low
```

---

## Consequencias de nao tratar isso

Sem bootstrap:

- novos posts entram como `low`
- continuam sem historico
- podem nunca ganhar visibilidade suficiente

Sem backfill legado:

- posts antigos sem historico seguem contaminando a base
- o grupo `low` mistura cold start com falha operacional
- a calibracao do modelo fica enviesada

---

## Diretriz de implementacao

Esta especificacao sugere duas etapas separadas:

### Etapa 1. Primeiro implementar posts novos

Motivo:

- o problema de novos `low` e continuo
- a cada nova rodada entram novos posts
- se bootstrap nao existir, o problema se renova sem parar

### Etapa 2. Depois atacar o legado

Motivo:

- legado pode ser resolvido com script offline
- e uma correcao direcionada
- nao precisa bloquear a criacao da politica para novos posts

---

## Status

Esta especificacao define a separacao conceitual e operacional entre:

- `bootstrap_low`
- `legacy_low`

Ainda nao define a implementacao SQL nem o script offline detalhado.
