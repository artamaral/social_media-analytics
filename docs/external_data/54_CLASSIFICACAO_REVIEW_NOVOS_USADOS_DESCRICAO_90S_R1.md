# Classificacao review carros novos e usados - descricao vs 90s - R1

## Objetivo

Selecionar e classificar `10` videos ainda nao usados nas rodadas anteriores,
com foco em reviews de carros novos ou usados. A rodada usa a Taxonomia V2 atual
e compara duas evidencias:

- `descricao`: nesta base, representada por titulo e metadados, pois `posts`
  ainda nao armazena descricao real do YouTube;
- `transcricao_90s`: transcript local dos primeiros `90s` gerado com
  `yt-dlp + faster-whisper`.

## Artefatos

- `52_AMOSTRA_REVIEW_CARROS_NOVOS_USADOS_10_VIDEOS_R1.csv`
- `53_TRANSCRICOES_90S_REVIEW_CARROS_NOVOS_USADOS_R1.csv`
- `54_CLASSIFICACAO_REVIEW_NOVOS_USADOS_DESCRICAO_90S_R1.csv`

## Selecao

Todos os videos selecionados:

- sao `long`;
- nao aparecem nos `19` `post_id` ja usados nas rodadas anteriores;
- possuem creator com porte relevante;
- possuem sinais fortes de review, avaliacao, test drive, vale a pena,
  compra, carro novo ou carro usado.

## Resultado geral

| Indicador | Resultado |
| --- | ---: |
| Videos avaliados | 10 |
| Transcricoes com sucesso | 10 |
| Classificacoes por titulo/metadados | 10 |
| Classificacoes por 90s | 10 |
| Mudanca de `automotive_domain` apos 90s | 0 |
| Mudanca relevante de `topic_path` apos 90s | 1 |
| Casos que ganharam contexto tecnico apos 90s | 9 |
| Casos que ganharam ou reforcaram ano/versao apos 90s | 3 |

## Comparativo por video

| post_id | Descricao/titulo | 90s | Leitura |
| --- | --- | --- | --- |
| `P-Pr_DiYeTg` | `review_veiculo` + `mercado_usados` | Mantem rota e adiciona V8 aspirado, cambio automatico e tracao traseira | 90s aumenta muito a confianca e o contexto tecnico |
| `kqZ2uDy8Uko` | `test_drive` como rota principal | 90s mostra review completo com test drive como parte da entrega | Melhor rota principal vira `review_veiculo`; test drive fica secundario |
| `AdHJ5Xy0X48` | Review de Renault Boreal com custo-beneficio | 90s confirma review e adiciona lancamento/ano de lancamento 2025 | Precisa diferenciar `launch_year` de `model_year` |
| `jTtiWaybMvw` | Review de Duster usado | 90s confirma faixa de preco, robustez e manutencao barata | Reforca `mercado_usados` como secundario |
| `0CMfwALqz-E` | Review de Golf Variant 2017 com problemas | 90s confirma wagon/perua e problemas potenciais ainda genericos | Nao preencher problema tecnico especifico sem evidencia |
| `PpjLnq8mv50` | Review/compra do novo WR-V | 90s adiciona motor 1.5 flex, CVT, tracao dianteira, airbags, garantia e economia | Pede atributos comerciais alem de contexto tecnico |
| `x8kFKNMFsg0` | Review novo i20 2027 vs Tera | 90s confirma posicionamento entre HB20 e Creta e comparativo com Pulse/Tera | Sugere atributo de posicionamento de linha |
| `CJloy4kzRA8` | Review Renegade hibrido | 90s confirma hibrido leve, linha 2027, consumo e funcionamento do sistema | Sugere `hibrido_leve` como termo controlado |
| `-9Ggzcf1cFM` | Review Audi Q5 2026 | 90s adiciona SUV premium, tracao integral, tecnologia embarcada e tela do passageiro | Sugere atributos premium/tecnologia |
| `3gJE2PN7970` | Review BYD Song Pro 2026 | 90s adiciona motor 1.5 aspirado + bateria, comparativo e ausencia de carga rapida | Sugere vocabulario para arquitetura hibrida |

## Aprendizados

- A classificacao por titulo ja e forte para identificar `review_teste >
  review_veiculo` em quase todos os casos.
- Os `90s` raramente mudam o dominio, mas enriquecem muito entidades, versao,
  powertrain, atributos comerciais e tecnicos.
- Em review, termos como motor, cambio, suspensao, tecnologia e consumo quase
  sempre sao atributos do veiculo, nao tema de manutencao/diagnostico.
- `problem` deve ficar vazio quando o video apenas promete falar de problemas
  ou defeitos, sem evidenciar uma falha tecnica especifica nos 90s.
- Videos de carros usados precisam de atributo comercial de faixa de preco,
  robustez, desvalorizacao e custo de manter.
- Videos de carros novos precisam diferenciar ano/modelo, linha/model-year e ano
  de lancamento.

## Proposta de novos termos

### Topic path

Nao promover muitos novos `topic_path` nesta rodada. A arvore atual cobriu os
`10` videos sem categoria ad hoc.

Adicionar como candidatos de navegacao apenas se recorrencia continuar:

- `review_teste > review_usado`
- `review_teste > review_lancamento`
- `review_teste > test_drive_longo`

### Atributos comerciais/editoriais

Criar ou planejar eixo futuro de atributos, separado de `topic_path`:

- `faixa_preco`
- `custo_de_manter`
- `desvalorizacao`
- `robustez`
- `garantia`
- `motivos_para_comprar`
- `pontos_positivos_negativos`
- `posicionamento_de_linha`
- `comparativo_leve`
- `suv_premium`
- `wagon_perua`
- `muscle_car`

### Powertrain e tecnologia

Adicionar ao vocabulario controlado ou matriz tecnica apenas os termos
aprovados desta rodada:

- `cambio_automatico`
- `cambio_cvt`
- `tracao_traseira`
- `tracao_dianteira`
- `tracao_integral`

Observacao:

- `cambio_automatico` apareceu duplicado na proposta informal e foi mantido uma
  unica vez como termo canonico.
- os demais termos sugeridos na analise ficam como evidencia textual ou lacuna,
  mas nao entram nesta atualizacao.

## Recomendacao

Antes de expandir `topic_path`, criar `vehicle_attribute[]` ou
`review_context[]` em formato repetivel. Essa rodada mostrou que reviews
misturam varios atributos relevantes sem que eles devam virar subnicho.

Campos sugeridos para a proxima estrutura:

- `attribute_id`
- `post_id`
- `attribute_group`
- `attribute_code`
- `attribute_value`
- `evidence_text`
- `source_stage`
- `confidence_score`

Grupos iniciais:

- `commercial`
- `vehicle_body`
- `powertrain`
- `technology`
- `ownership`
- `comparison`
