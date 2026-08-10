# Comparacao pos-reprocessamento MVP40 com buckets de powertrain

Data: 2026-08-10

Round avaliado: `v2_transcript_90s_mvp40_powertrain_buckets_20260806`

## Objetivo

Comparar a rodada de `40` videos apos consolidar a classificacao operacional
de `powertrain` em dois buckets:

- `powertrain__eletrificados`
- `powertrain__ice`

A comparacao usa como baseline os CSVs `62_*`, exportados antes do
reprocessamento.

## Artefatos

- `63_COMPARACAO_POS_REPROCESSAMENTO_MVP40_POWERTRAIN_BUCKETS_20260806_RESULTADOS.csv`
- `63_COMPARACAO_POS_REPROCESSAMENTO_MVP40_POWERTRAIN_BUCKETS_20260806_TECHNICAL_CONTEXTS.csv`
- `63_COMPARACAO_POS_REPROCESSAMENTO_MVP40_POWERTRAIN_BUCKETS_20260806_VEHICLE_ENTITIES.csv`
- `63_COMPARACAO_POS_REPROCESSAMENTO_MVP40_POWERTRAIN_BUCKETS_20260806_COMPARACAO.csv`

## Resultado operacional

- videos esperados: `40`
- videos gravados na nova rodada: `30`
- falhas: `10`
- taxa de sucesso: `75%`
- criterio MVP registrado: pelo menos `85%` de sucesso operacional

Conclusao:

- a rodada ainda nao atende ao criterio operacional de MVP.

## Comparacao com baseline

O baseline tinha `38/40` resultados em `transcript_90s`. Dois videos ja nao
tinham resultado anterior:

- `NuLcOS208w0`
- `fgjijU3h7Cw`

Entre os `30` videos comparaveis:

- `topic_path` mudou em `13` videos
- `needs_human_review` no baseline: `16/30`
- `needs_human_review` na nova rodada: `17/30`
- melhoraram de revisao para sem revisao: `2`
- regrediram para revisao: `3`

## Melhorias observadas

- `0YeiiIpSrP0` mudou de
  `powertrain__hibrido__sistema_hibrido` para
  `powertrain__eletrificados`, que e o comportamento esperado.
- `CjFrJg6VCjc` mudou de `powertrain` para
  `review_teste__teste_autonomia`, reduzindo revisao humana.
- `ZspY7eFGJXo` mudou de `mercado_produto__lancamentos` para
  `mercado_produto__lancamentos__suv`, tambem reduzindo revisao humana.
- `BrKVhF-oG80` mudou de `diagnostico` para
  `diagnostico__scanner_obd2`, melhorando especificidade.

## Gargalos encontrados

### Falhas operacionais

Algumas falhas vieram de download/transcricao via YouTube, ainda sujeitas a
bloqueios de bot, cookies e variacao do `yt-dlp`.

Tambem houve falhas bloqueantes de validacao que nao deveriam derrubar o video:

- `vehicle_entity sem valor bruto extraido`
- `transcript_quality.quality_score deve ficar entre 0 e 1`

### Topic paths genericos

Ainda apareceram regressos ou classificacoes pouco especificas:

- `review_teste__review_veiculo` para `review_teste`
- `fora_escopo__transito_comportamento` para `fora_escopo`
- `fora_escopo__nao_automotivo` para `fora_escopo`

### Technical context

Foram exportados `43` contextos tecnicos na nova rodada:

- `20` com `allowed_with_evidence`
- `23` com `needs_review`

Isso indica que a matriz tecnica ainda esta mais restritiva do que o harness em
alguns casos, ou que o GPT ainda cria contextos tecnicos genericos demais.

## Ajustes sistemicos implementados

Para reduzir falhas evitaveis sem expandir a taxonomia, o classificador foi
ajustado para:

- descartar `vehicle_entities[]` completamente vazios antes da validacao;
- normalizar `confidence_score` e `transcript_quality.quality_score` quando o
  GPT retornar valores em escala percentual ou fracionaria, como `85`, `85%` ou
  `85/100`;
- promover `review_teste` para `review_teste__review_veiculo` quando houver
  evidencia de avaliacao/review/test drive de veiculo;
- promover `fora_escopo` para `fora_escopo__nao_automotivo` quando houver
  evidencia clara de moto, hospital, nobreak ou tema nao automotivo;
- promover `fora_escopo` para `fora_escopo__transito_comportamento` quando o
  foco for dirigir, transito, comportamento ou alerta sem tema tecnico;
- promover `off_road` para `off_road__preparacao_off_road` quando houver
  projeto, preparacao, trilha, suspensao ou caminhonete como proposta principal.

Esses reparos continuam conservadores: nao criam codigos novos, nao usam
inferencia externa e nao substituem evidencia textual.

## Recomendacao

Antes de outra rodada completa de `40` videos, reprocessar apenas os `10`
falhos e uma pequena amostra dos casos genericos para confirmar que os ajustes
eliminam as falhas bloqueantes sem aumentar falso positivo.

Se essa rodada controlada passar, repetir os `40` videos para nova medicao de
MVP.
