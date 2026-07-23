# Comparacao da Taxonomia V2 enriquecida - 20 videos R1

Data: 2026-07-23

## Objetivo

Rodar novamente a classificacao GPT exploratoria usando a Taxonomia V2
enriquecida pelos docs `46` e `47`, agora sobre os `20` registros com
transcricoes salvas.

Esta rodada usa os transcripts locais ja versionados:

- `38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.csv`
- `45_TRANSCRICOES_90S_ENRIQUECIMENTO_TAXONOMIA_V2_R1.csv`

Resultado gerado:

- `48_RESULTADO_GPT55_TAXONOMIA_V2_ENRIQUECIDA_20VIDEOS_R1.csv`

## Escopo da rodada

Foram avaliadas `20` linhas de entrada:

- `10` do lote piloto original (`piloto_38`);
- `10` do lote de enriquecimento (`enriquecimento_45`).

Ha `16` videos unicos, porque `4` videos aparecem nos dois lotes:

- `aXbFPJMVGKw`
- `nP0q6x1Uqs0`
- `RTZHxSE2t5M`
- `6qSnrkGd70I`

Essas duplicidades foram preservadas de proposito para manter rastreabilidade
com as duas rodadas.

## Resultado resumido dos 20 registros

| `automotive_domain` | Linhas |
| --- | ---: |
| `manutencao_reparo` | 6 |
| `mercado_produto` | 5 |
| `review_teste` | 5 |
| `pos_venda_reparacao` | 2 |
| `diagnostico` | 1 |
| `fora_escopo` | 1 |

Linhas marcadas com `needs_human_review = true`: `4/20`.

Motivos principais de revisao humana:

- videos com multiplos sistemas e componentes na mesma fala;
- necessidade futura de suporte a multi-componente/multi-sistema;
- videos em que o tipo de veiculo/uso ainda nao tem contrato canonico
  (`motorhome`);
- casos de reparo com diagnostico, custo e manutencao no mesmo conteudo.

## Comparacao contra a rodada anterior do piloto

Para os `10` videos do piloto, a comparacao foi feita contra:

- `41_RESULTADO_GPT55_TAXONOMIA_V2_R1.csv`
- etapa `gpt55_v2_entrega_2_90s_iniciais`

Resultado por campo:

| Campo | Iguais | Alterados |
| --- | ---: | ---: |
| `automotive_domain` | 10 | 0 |
| `activity_type` | 10 | 0 |
| `topic_path` | 10 | 0 |
| `content_type` | 7 | 3 |
| `audience_intent` | 9 | 1 |
| `automotive_system` | 8 | 2 |
| `component` | 7 | 3 |
| `problem` | 7 | 3 |
| `needs_human_review` | 3 | 7 |

Leitura:

- a estrutura principal da V2 ficou estavel;
- a V2 enriquecida nao mudou o tema principal dos `10` videos do piloto;
- as mudancas vieram na camada de contexto tecnico, problema e revisao humana;
- `topic_path_secondary` resolveu sobreposicoes que antes apareciam como
  ambiguidade, especialmente `review + compra_venda`, `review + preco` e
  `mercado + powertrain`.

## Principais diferencas por video do piloto

| `post_id` | Diferenca principal |
| --- | --- |
| `pINW53ErjQI` | Sem mudanca estrutural; reforcado que mencoes a problema mecanico sao incidentais em `fora_escopo`. |
| `_j1gOOnjgcU` | Mantem `limpeza_componentes`, mas explicita multi-sistema: `eletrica_eletronica` e `motor`. |
| `z55GnDEg7_U` | Mantem `troca_motor`, mas adiciona problemas mais especificos: `desgaste` e `oleo_vencido`. |
| `CjFrJg6VCjc` | Mantem `teste_autonomia`; remove problema/revisao quando nao ha falha comprovada. |
| `nP0q6x1Uqs0` | Mantem `mercado_eletrificados`; `powertrain > eletrico` passa a secundario/contexto. |
| `JGzj254Kgs4` | Mantem `review_veiculo`; adiciona secundario `compra_venda > carro_popular`. |
| `6qSnrkGd70I` | Mantem `arrefecimento`; componentes e problemas agora ficam mais canonicos. |
| `aXbFPJMVGKw` | Mantem `review_veiculo`; adiciona secundario `preco_posicionamento > custo_beneficio`. |
| `RTZHxSE2t5M` | Mantem `gargalo_oficinas`; remove preenchimento tecnico de veiculo especifico. |
| `UtWYJfldWHA` | Mantem `lancamentos`; adiciona secundario `review_veiculo` e contexto `motor_flex`. |

## Comparacao contra a rodada de enriquecimento anterior

Para os `10` videos do lote `45`, a comparacao anterior nao era um CSV de
classificacao GPT completo. A referencia e a leitura curatorial do doc `46`.

O resultado atual confirma a maior parte da leitura anterior:

| `post_id` | Antes no doc `46` | Agora na rodada `48` | Diferenca |
| --- | --- | --- | --- |
| `nKEuKTAX-eA` | `diagnostico__ruido_suspensao` | `diagnostico > ruido_suspensao` | Confirmado; `barulho` segue apenas como sinal. |
| `ITBdyKnV5Pg` | `manutencao_pesada` | `manutencao_reparo > custo_reparo > manutencao_pesada` | Confirmado, com secundario `cambio_cvt` e multi-sistema. |
| `aXbFPJMVGKw` | `review_veiculo` | `review_teste > review_veiculo` | Confirmado; adiciona secundario de custo-beneficio. |
| `nP0q6x1Uqs0` | `mercado_eletrificados` | `mercado_produto > mercado_eletrificados` | Confirmado; `efeito_dolphin` continua rejeitado como codigo. |
| `xKNbBoiDt5g` | `review_veiculo`, motorhome descritivo | `review_teste > review_veiculo` | Confirmado com revisao humana por falta de contrato para tipo de uso. |
| `RTZHxSE2t5M` | `gargalo_oficinas` | `pos_venda_reparacao > gargalo_oficinas` | Confirmado; pecas fica como secundario. |
| `3AjI62lO8b8` | `lancamentos__suv` | `mercado_produto > lancamentos > suv` | Confirmado; plug-in fica como contexto/tema secundario. |
| `6qSnrkGd70I` | `arrefecimento` | `manutencao_reparo > manutencao_preventiva > arrefecimento` | Confirmado; problema `superaquecimento` segue nao inferido. |
| `Ffmnzmm4Sf8` | `custo_beneficio` + pneus | `mercado_produto > preco_posicionamento > custo_beneficio` | Confirmado; pneus fica como secundario/contexto tecnico. |
| `uZVDGJXqrgU` | `suspensao` | `manutencao_reparo > manutencao_preventiva > suspensao` | Confirmado; Retani Buffer segue como produto/insumo, nao codigo. |

## O que melhorou com a taxonomia nova

### 1. Menos falso conflito entre tema e contexto

Videos de review e mercado continuam com tema principal claro, enquanto
`powertrain` entra como contexto ou `topic_path_secondary`.

Exemplos:

- `nP0q6x1Uqs0`: mercado de eletrificados com contexto eletrico;
- `3AjI62lO8b8`: lancamento de SUV com contexto hibrido plug-in;
- `UtWYJfldWHA`: lancamento com contexto flex.

### 2. Sintomas ficaram mais bem separados

`ruido`, `vibracao`, `perda_potencia`, `luzes_painel` e `direcao_puxando`
agora podem ser usados como rotas de diagnostico ou problemas tecnicos,
conforme a evidencia.

Exemplo:

- `nKEuKTAX-eA`: `diagnostico > ruido_suspensao`, com `problem = ruido`.

### 3. Manutencao preventiva ganhou granularidade

A atualizacao por fonte Moura criou rotas que ajudam conteudos de checklist e
revisao periodica:

- `revisao_10k`
- `oleo_filtros`
- `filtro_ar`
- `filtro_combustivel`
- `alinhamento_balanceamento`
- `correias_tensores`
- `controle_revisao`

Nenhum dos `20` videos exigiu `revisao_10k` como rota principal, mas a nova
rota resolve uma lacuna real para conteudos de checklist amplo.

### 4. A matriz tecnica ficou mais util

Casos como `6qSnrkGd70I`, `ITBdyKnV5Pg` e `_j1gOOnjgcU` deixaram de depender
de termos livres para componentes como:

- `fluido_arrefecimento`
- `aditivo_arrefecimento`
- `limpa_radiador`
- `filtro_arrefecimento`
- `cambio_cvt`
- `filtro_cambio`
- `bateria_12v`
- `sensor_maf`
- `sensor_oxigenio`

## Gargalos que permanecem

### Multi-sistema e multi-componente

`ITBdyKnV5Pg` e `_j1gOOnjgcU` mostram que um unico campo de sistema/componente
sera pouco para videos reais de oficina ou dica multipla.

Recomendacao:

- resolvido operacionalmente no doc `50` com `technical_context[]` em CSV
  filho, usando multiplas entradas `{automotive_system, component, problem,
  evidence_text}`.

### Entidade/tipo de uso do veiculo

`xKNbBoiDt5g` mostra que `motorhome` nao deve virar `topic_path`, mas tambem
nao deve desaparecer.

Recomendacao:

- criar campo futuro `vehicle_use_type` ou `vehicle_body_use`, separado de
  `topic_path`.

### Produto/insumo tecnico

`uZVDGJXqrgU` mostra que produtos como `Retani_Buffer` podem ser relevantes,
mas nao sao sistema, componente nem problema.

Recomendacao:

- avaliar campo futuro `aftermarket_product` ou `technical_product`.

### Score ainda nao deve ser fechado

A rodada ainda e exploratoria. Nao calcular `agreement_score` definitivo
porque:

- o lote tem duplicidades;
- a rodada anterior do lote `45` era curatorial, nao classificacao completa;
- ainda falta contrato de multi-componente.

## Conclusao

A Taxonomia V2 enriquecida esta mais estavel no eixo principal:

- `automotive_domain`, `activity_type` e `topic_path` do piloto ficaram
  inalterados contra a rodada anterior;
- as mudancas relevantes ocorreram onde deveriam ocorrer: contexto tecnico,
  problema, tema secundario e necessidade de revisao humana;
- os `20` registros conseguem ser classificados sem criar categoria ad hoc.

Proximo passo recomendado:

1. transformar `technical_context` em estrutura repetivel;
2. validar o CSV `50` contra a matriz de compatibilidade `43`;
3. decidir se o workbook deve ganhar uma aba filha de contexto tecnico ou se o
   CSV separado basta para a proxima rodada;
4. so depois disso reabrir `agreement_score`.
