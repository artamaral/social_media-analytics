# Amostra Piloto de 10 Videos v1

## Objetivo

Definir a lista canonica da fase 3 do Sprint 6 para a primeira rodada de
validacao humano vs IA.

Esta amostra deve ser usada como universo fechado da rodada inicial, sem
substituicoes livres fora das regras definidas neste documento.

## Fonte de verdade desta fase

Os artefatos canonicos desta fase sao:

- este documento
- `docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv`

Eles devem ser usados junto com:

- `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.md`
- `docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.md`

## Regras usadas para montar a amostra

- fonte real: `posts` + `creators` no Supabase
- divisao fixa:
  - `5` videos `short`
  - `5` videos `long`
- exclusoes obrigatorias:
  - `Acelerados`
  - `ACF`
  - `Tcar`
- filtro minimo de porte do creator:
  - `followers >= 150000`
- filtro minimo de engajamento:
  - `engagement_pct >= 2.0`
- formula usada:
  - `engagement_pct = ((likes + comments) / views) * 100`

## Criterios metodologicos da amostra

Esta amostra nao busca representatividade estatistica.

Ela foi montada para equilibrar:

- casos claros de classificacao
- casos com titulo ambiguo ou editorialmente carregado
- temas de `powertrain`
- temas de `manutencao`
- temas de `mercado` ou `compra_venda`

## Lista canonica da rodada inicial

### Shorts primarios

1. `pINW53ErjQI` | `edumartins car` | `MUITO CUIDADO AO DIRIGIR!`
   - motivo: alto alcance, titulo ambiguo, bom engajamento
2. `_j1gOOnjgcU` | `carupdicasautomotivas` | `Quase ninguém faz! #dicasautomotivas #mecanicadescomplicada #mecanicaautomotiva`
   - motivo: caso curto com sinal de manutencao
3. `z55GnDEg7_U` | `Carros com Tiago` | `Quanto custa o motor do Kwid ?`
   - motivo: mistura custo e detalhe tecnico
4. `CjFrJg6VCjc` | `Carros com Tiago` | `Testei a autonomia do Byd Dolphin Mini Gs no extremo`
   - motivo: caso claro de `powertrain`
5. `nP0q6x1Uqs0` | `Eletricarbr` | `Brasil Cheio de Elétricos por Culpa Dele: NOVO BYD Dolphin SE - R$ 159 Mil`
   - motivo: caso claro de `powertrain` com viés de mercado/lancamento

### Longs primarios

1. `JGzj254Kgs4` | `CarroChefe` | `O CARRO POPULAR DE VERDADE! 25 SALÁRIOS MIMOS POR UM UMZ ERO KM COMPLETO! VC TERIA?`
   - motivo: forte sinal de `compra_venda`
2. `6qSnrkGd70I` | `MEGA DICAS AUTOMOTIVAS` | `NÃO TIRO MAIS DO CARRO! COMO MELHORAR E DEIXAR A ÁGUA DO RADIADOR REALMENTE LIMPA PRA SEMPRE!`
   - motivo: caso claro de `manutencao` / `arrefecimento`
3. `aXbFPJMVGKw` | `CarroChefe` | `ACABOU PRA VW, JEEP E TOYOTA! Avaliação Changan Uni-T 2026`
   - motivo: review com titulo agressivo
4. `RTZHxSE2t5M` | `Meu Carro Life Style` | `MECÂNICOS EM PÂNICO? MILHARES DE CARROS DESCARTÁVEIS DESPEJADOS em nosso MERCADO! E AGORA?`
   - motivo: caso forte de `mercado`
5. `UtWYJfldWHA` | `Quatrorodas` | `R$ 169.990! Caoa Changan Uni-T estreia NACIONAL, FLEX e é equipado como CARRO DE LUXO`
   - motivo: mistura `mercado` / `review` com sinal de `powertrain`

## Alternates canonicos

### Shorts alternativos

1. `ITBdyKnV5Pg` | `Carros com Tiago`
2. `KzlGcX0HjZY` | `CarroChefe`
3. `NxOia4iUyV8` | `Carros com Tiago`

### Longs alternativos

1. `xKNbBoiDt5g` | `BF///MS`
2. `Ffmnzmm4Sf8` | `canal da mecanica`
3. `WhpT__pTf50` | `canal da mecanica`

## Regras de substituicao

Um video primario so pode ser substituido por um alternate se ocorrer pelo
menos uma das condicoes abaixo:

- metadado essencial ausente:
  - `title`
  - `video_type`
  - `views`
  - `likes`
  - `comments`
  - `duration`
  - `creator`
- creator entrar nas exclusoes da fase
- evidência de engajamento ficar abaixo do filtro usado para a shortlist
- duplicacao excessiva comprometer a variedade tematica da rodada

## Checklist de validacao da amostra

Antes de iniciar a classificacao humana:

- confirmar exatamente `5 short` e `5 long`
- confirmar ausencia de `Acelerados`, `ACF` e `Tcar`
- confirmar `followers >= 150000` em todos os creators
- confirmar `engagement_pct >= 2.0` em todos os videos primarios
- confirmar pelo menos:
  - `2` casos claramente classificaveis
  - `2` casos com titulo ambiguo ou carregado
  - `1` caso claro de `powertrain`
  - `1` caso claro de `manutencao`
  - `1` caso claro de `mercado` ou `compra_venda`

## Fora de escopo desta fase

- classificacao humana dos `10` videos
- prompt final da IA
- execucao da rodada automatica
- revisao de `agreement_score`
