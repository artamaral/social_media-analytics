# Resultado do Baseline Humano e Contrato de Avaliacao GPT v1

## Objetivo

Consolidar a classificacao humana registrada no workbook `34`, comparar a
analise baseada em descricao com a analise apos os `90s` iniciais e preparar a
execucao equivalente pelo agente GPT.

## Fontes

- workbook humano:
  `docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.xlsx`
- snapshot normalizado deste resultado:
  `docs/external_data/36_BASELINE_HUMANO_DUAS_ETAPAS_V1.csv`
- taxonomia usada no teste: docs `31` e `32`
- achados de evolucao da taxonomia: doc `35`

O CSV `36` preserva os valores como classificados, inclusive termos fora da
taxonomia e combinacoes incoerentes. Ele nao e uma versao corrigida do baseline.

## Estrutura observada no workbook

O arquivo possui duas abas de classificacao humana:

- `execucao_humana_title`: interpretada neste piloto como a avaliacao pela
  descricao, antes do consumo do video
- `execucao_humana_transcricao_90s`: avaliacao depois dos `90s` iniciais; apesar
  do nome fisico da aba, o baseline representa a observacao humana do trecho e
  nao uma transcricao textual persistida

As abas `taxonomias` e `listas` continuam como apoio.

## Resumo quantitativo

| Indicador | Pela descricao | Depois de 90s |
| --- | ---: | ---: |
| Videos no lote | 10 | 10 |
| Marcados como `sim` em `classificacao_finalizada` | 2 | 9 |
| Marcados como `nao` | 6 | 1 |
| Sem status preenchido | 2 | 0 |

Entre as duas etapas:

- `7/10` videos tiveram alteracao em pelo menos um dos `11` campos de
  classificacao
- foram observadas `29` alteracoes de campo
- `niche` mudou em `3` videos
- `sub_niche` mudou em `6` videos
- `sub_sub_niche`, `content_type` e `audience_intent` mudaram em `3` videos cada
- marca e modelo mudaram em `2` videos cada
- ano ou geracao mudou em `3` videos
- sistema mudou em `1`, componente em `2` e problema em `1`
- considerando tambem a descoberta de conteudo nao automotivo em
  `pINW53ErjQI`, os `90s` trouxeram informacao decisiva ou complementar para
  `8/10` videos

## Comparacao por video

| `post_id` | Resultado pela descricao | Resultado depois de 90s | Leitura principal |
| --- | --- | --- | --- |
| `pINW53ErjQI` | sem classificacao; nao finalizado | sem taxonomia; finalizado | os `90s` mostraram que o video fala de golpe e nao e automotivo |
| `_j1gOOnjgcU` | apenas `manutencao` | `manutencao / bateria_12v / falha_sensor` e dimensoes tecnicas | o trecho permitiu preencher `7` campos, mas gerou incompatibilidades entre niche, subnicho, sistema e problema |
| `z55GnDEg7_U` | `manutencao / manutencao_motor / fazer_motor` | mesma rota, com `2021` e componente `motor` | os `90s` adicionaram detalhe; `fazer_motor`, `motor` e o formato de ano nao existem canonicamente |
| `CjFrJg6VCjc` | `Teste / comparativo`; nao finalizado | sem mudanca; nao finalizado | revelou lacunas para testes, durabilidade, performance e baterias de eletrificados |
| `nP0q6x1Uqs0` | `compra_venda / eletrico` | `compra_venda / eletreficado / eletrico`, com `2026` | evidencia de necessidade de nivel intermediario para eletrificados; termo foi registrado com grafia nao canonica |
| `JGzj254Kgs4` | `compra_venda / carro_popular` | `review / eletreficado / eletrico`, Changan Lumin 2026 | maior mudanca semantica do lote; a evidencia inicial induziu leitura diferente do conteudo |
| `6qSnrkGd70I` | `manutencao / arrefecimento` | sem mudanca | caso mais estavel; `radiador` revelou lacuna na lista de componentes |
| `aXbFPJMVGKw` | `mercado`, marca Volkswagen | `review / comparativo`, Changan Uni-T | os `90s` corrigiram marca, modelo, tema e intencao |
| `RTZHxSE2t5M` | apenas `mercado` | `mercado / comparativo`, com tipo e intencao | o trecho completou a leitura editorial, mas `comparativo` conflita com o parent atual de `sub_niche` |
| `UtWYJfldWHA` | `compra_venda / test_drive` | `review / lancamentos` | tema principal e subnicho mudaram; a combinacao final tambem conflita com os parents atuais |

## Qualidade e lacunas reveladas

### Taxonomia e coerencia

Na classificacao depois de `90s`, `8/10` videos possuem pelo menos um termo
fora da v1 ou uma relacao de parent incompativel com os CSVs `31` e `32`.

Principais casos:

- novos conceitos sugeridos: `orcamento`, `fazer_motor`, `retifica`,
  `bateria_powertrain`, capacidade de bateria, teste, durabilidade e performance
- termo de agrupamento necessario para eletrificados
- necessidade de categoria explicita para conteudo fora do escopo automotivo
- necessidade de multiplos subnichos ou, preferencialmente, eixos separados e
  relacoes de compatibilidade
- formato de ano precisa aceitar o valor real, como `2021`, e nao
  `exact_year 2021`

### Integridade do workbook

- a primeira aba se chama `execucao_humana_title`, mas o contrato informado e
  avaliacao pela descricao
- a descricao usada pelo humano nao esta persistida como coluna no workbook
- os titulos com virgula de `aXbFPJMVGKw` e `UtWYJfldWHA` ficaram truncados e
  deslocaram metadados de apoio por causa do CSV de origem
- o script gerador ainda cria uma unica aba humana; ele nao deve ser executado
  sobre este arquivo antes de ser atualizado para o novo contrato

Esses problemas nao invalidam as classificacoes nas colunas `M:Y`, mas precisam
ser corrigidos antes da avaliacao GPT para garantir entradas reproduziveis.

## Conclusao da analise humana

Os `90s` iniciais tiveram alto valor para completar e revisar a classificacao,
principalmente em videos com titulo editorial, ambiguo ou orientado a clique.
Ao mesmo tempo, a maior cobertura revelou que a taxonomia fechada v1 e as listas
independentes ainda nao conseguem representar o dominio sem termos livres ou
combinacoes inconsistentes.

O baseline humano deve ser tratado como referencia de calibracao, nao como
verdade absoluta. Os termos fora da v1 e as inconsistencias sao resultados do
teste e devem permanecer visiveis na comparacao com o GPT.

## Contrato da avaliacao pelo agente GPT

### Regra de isolamento

O agente classificador nao deve receber:

- as classificacoes humanas
- este resumo comparativo
- observacoes humanas
- resultados da outra etapa GPT antes de concluir a etapa corrente

As comparacoes so devem ocorrer depois que as duas saidas GPT estiverem
persistidas.

### Etapa GPT 1 - descricao

Para cada um dos mesmos `10` `post_id`:

- fornecer a descricao capturada em snapshot
- fornecer apenas metadados de identificacao estritamente necessarios
- nao fornecer audio, video, transcricao ou classificacao humana
- usar a taxonomia v1 dos docs `31` e `32`
- permitir que o agente registre lacuna sem inventar codigo canonico

Identificador da tentativa:

```text
gpt_entrega_1_descricao
```

### Etapa GPT 2 - primeiros 90s

Para cada video:

- fornecer a mesma descricao da Etapa 1
- adicionar a transcricao do intervalo `00:00-01:30`
- para videos menores que `90s`, usar a transcricao completa
- nao fornecer a classificacao humana nem a saida GPT da Etapa 1 no prompt
- usar a mesma taxonomia e o mesmo contrato de resposta

Identificador da tentativa:

```text
gpt_entrega_2_90s_iniciais
```

### Saida obrigatoria por tentativa

```text
post_id
evaluation_stage
niche
sub_niche
sub_sub_niche
content_type
audience_intent
vehicle_brand
vehicle_model
vehicle_year_or_generation
automotive_system
component
problem
confidence_score
evidence_summary
taxonomy_gaps
validation_issues
needs_human_review
```

O agente deve usar `null` quando nao houver evidencia. Termos novos devem ir em
`taxonomy_gaps`, sem substituir silenciosamente codigos canonicos.

### Validacoes antes da comparacao

- exatamente `10` resultados em cada etapa
- nenhum `post_id` duplicado ou ausente
- nenhuma classificacao humana presente no input do agente
- snapshot da descricao preservado com hash ou versao de captura
- transcricao limitada ao intervalo contratado
- resposta validada contra os codigos e parents dos CSVs `31` e `32`
- combinacao invalida registrada em `validation_issues`

### Comparacoes posteriores

Calcular separadamente:

1. humano descricao versus GPT descricao
2. humano 90s versus GPT 90s
3. mudancas humano entre descricao e 90s
4. mudancas GPT entre descricao e 90s
5. concordancia sobre quais campos ganharam ou mudaram com os `90s`
6. taxa de termos fora da taxonomia e de combinacoes invalidas

O `agreement_score` deve ser calculado somente depois de fechar seus pesos no
Sprint 6. Ate la, publicar concordancia exata por campo e divergencias brutas.

## Proximo passo operacional

Antes de executar o agente GPT:

1. corrigir o CSV de amostra para titulos com virgula
2. capturar e versionar a descricao dos `10` videos
3. gerar ou capturar a transcricao inicial de ate `90s`
4. definir o JSON Schema da saida
5. executar as duas etapas de forma cega
6. persistir os resultados antes de abrir o baseline humano para comparacao
