# LEGACY LOW OFFLINE BACKFILL SPECIFICATION

## Objetivo

Definir uma estrategia tecnica para um script offline de backfill voltado aos posts `legacy_low`.

O objetivo do script nao e substituir o pipeline principal.

O objetivo e:

- criar historico minimo para posts antigos subobservados
- reduzir a contaminacao do grupo `low`
- preparar esses posts para sair de `low` em coletas futuras

---

## Premissa central

No modelo `v2` atual, um unico snapshot offline nao e suficiente para tirar imediatamente um post do estado `low`.

Motivo:

- para sair de `low`, o modelo precisa de pelo menos um snapshot anterior utilizavel na janela de `6h`
- isso exige diferenca temporal util entre coletas

Conclusao:

- um snapshot offline isolado nao resolve completamente o estado
- mas cria a base necessaria para que uma coleta futura permita transicao para `partial`

---

## Estrategia recomendada

O backfill legado deve ser executado em duas fases.

Como diretriz de implementacao, o script offline deve reutilizar o maximo
possivel da estrutura ja existente em
`scripts/cloud_run/postMetrics/main.py`.

Isso significa que a implementacao nova deve nascer como adaptacao do pipeline
atual, e nao como um fluxo totalmente novo.

### Fase 1. Seed historico

Objetivo:

- inserir 1 snapshot inicial para o maior numero possivel de posts legados relevantes

Efeito esperado:

- remover a condicao de "sem historico nenhum"
- criar um ponto base para comparacoes futuras
- preparar o post para que uma coleta posterior possa gerar `partial`

### Fase 2. Promocao de estado

Objetivo:

- executar nova coleta posterior em subconjunto priorizado
- gerar segunda observacao temporalmente util

Efeito esperado:

- permitir que parte dos posts deixe de ser `low`
- promover posts para `partial`
- habilitar uso inicial de velocity

---

## Definicao de `legacy_low`

Para fins do script offline, um post e considerado `legacy_low` quando:

- nao e novo
- possui historico insuficiente
- nao esta apenas em fase natural de cold start

### Criterio inicial sugerido

Versao inicial:

- `created_at < now() - interval '7 days'`
- `total_checagens <= 1`

Observacao:

- esse criterio e inicial e pode ser recalibrado
- o objetivo e separar legado de bootstrap de novos posts

### Ajuste operacional posterior

Com a fase 1 em execucao e evidencias de baixo consumo da API do YouTube,
passou a fazer sentido ampliar momentaneamente o foco operacional para:

- `created_at < now() - interval '7 days'`
- `total_checagens <= 2`

Motivo:

- atacar apenas `<= 1` ajuda a semear historico
- atacar `0`, `1` e `2` checagens acelera a reducao do `legacy_low`
- isso direciona melhor o esforco para os posts ainda pouco observados

---

## Fase 1. Seed historico

### Objetivo operacional

Criar 1 snapshot para posts antigos que ainda nao possuem base minima de historico.

### O que o script deve fazer

1. selecionar posts `legacy_low`
2. ordenar por prioridade de correcao
3. buscar metricas atuais
4. inserir snapshot em `post_metrics_history`
5. deixar triggers atualizarem `posts` e `post_update_queue`

### Diretriz de reuso do codigo existente

O script offline deve usar, como base inicial, as mesmas responsabilidades ja
presentes no `postMetrics/main.py`:

- configuracao por variaveis de ambiente
- `HEADERS` para chamadas ao Supabase
- chamada ao endpoint `videos.list` da YouTube API
- normalizacao do payload de estatisticas
- insert em `post_metrics_history`

A diferenca principal deve ficar concentrada em:

- substituir `fetch_queue()` por uma funcao de selecao de `legacy_low`
- manter o restante do pipeline o mais proximo possivel do fluxo atual

### Prioridade sugerida para o lote

Ordem de prioridade recomendada:

1. maior `base_popularity`
2. menor `total_checagens`
3. `collected_at` mais antigo ou nulo

### Resultado esperado

- posts passam a ter pelo menos 1 snapshot historico
- o sistema reduz a quantidade de posts completamente cegos

### Limite operacional sugerido

Comecar com lote pequeno e controlado, por exemplo:

- `50`
- `100`

e ajustar conforme custo e tempo de execucao

---

## Fase 2. Promocao de estado

### Objetivo operacional

Executar uma nova coleta em posts seedados para criar diferenca temporal util.

### Condicao desejada

O segundo snapshot deve ocorrer com distancia suficiente para que o modelo consiga usar historico.

No modelo atual:

- alvo minimo: diferenca util de `6h`

### O que o script ou rotina complementar deve fazer

1. identificar posts que passaram pela fase 1
2. selecionar subconjunto priorizado
3. executar nova coleta apos janela temporal suficiente
4. inserir novo snapshot em `post_metrics_history`

### Resultado esperado

- parte dos posts deixa de ser `low`
- parte dos posts passa a `partial`
- velocity comeca a ficar disponivel

---

## O que nao fazer

O script offline nao deve:

- atualizar diretamente `posts`
- atualizar diretamente `post_update_queue`
- reimplementar regra dos triggers
- competir continuamente com o pipeline principal
- reescrever desnecessariamente funcoes que ja existem no `postMetrics/main.py`

O papel dele e:

- inserir snapshots de historico

E deixar o restante do comportamento seguir o fluxo normal do banco.

---

## Fluxo resumido

```text
Selecionar legacy_low
  -> ordenar por prioridade de correcao
  -> fase 1: inserir 1 snapshot
  -> aguardar janela temporal util
  -> fase 2: inserir novo snapshot
  -> observar quantos posts passam de low para partial
```

---

## Criterios de sucesso

### Fase 1

- reducao do numero de posts sem qualquer historico util
- criacao de base historica para posts antigos relevantes

### Fase 2

- reducao do numero de posts `legacy_low`
- aumento do numero de posts `partial`
- melhoria da cobertura dos posts antigos

---

## Queries de validacao sugeridas

### 1. Quantos posts legados ainda estao sem historico minimo

```sql
select
  count(*) as total_legacy_low
from posts p
left join (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) h on h.post_id = p.post_id
where p.created_at < now() - interval '7 days'
  and coalesce(h.total_checagens, 0) <= 1;
```

### 2. Quantos posts ganharam o primeiro snapshot

```sql
select
  count(*) as posts_com_1_snapshot
from (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) h
where h.total_checagens = 1;
```

### 3. Quantos posts conseguiram sair de `low`

```sql
select
  history_level,
  count(*) as total_posts
from public.v_post_priority_score_features_v2
group by history_level
order by history_level;
```

---

## Ordem recomendada de trabalho

1. implementar o bootstrap para posts novos
2. depois implementar fase 1 do backfill legado
3. por fim, implementar fase 2 de promocao de estado

Motivo:

- novos posts continuam entrando todos os dias
- sem bootstrap, o problema se renova continuamente
- o legado pode ser resolvido em modo corretivo

---

## Status

Esta especificacao descreve a recomendacao para o script offline de backfill legado.

Ainda nao define a implementacao em Python nem o cronograma operacional detalhado.
