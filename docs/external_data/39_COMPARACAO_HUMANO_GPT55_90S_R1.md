# Comparacao Humano vs GPT 5.5 com 90s - Round 1

## Objetivo

Comparar a classificacao humana `entrega_2_90s_iniciais` com a classificacao
exploratoria `gpt55_entrega_2_90s_iniciais` gerada a partir dos transcripts
Whisper locais.

Esta comparacao usa divergencias brutas e concordancia exata por campo. O
`agreement_score` ponderado ainda nao deve ser calculado.

## Fontes

- baseline humano: `docs/external_data/36_BASELINE_HUMANO_DUAS_ETAPAS_V1.csv`
- transcripts Whisper: `docs/external_data/38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.csv`
- resultado GPT 5.5 com 90s: `docs/external_data/39_RESULTADO_GPT55_90S_WHISPER_R1.csv`
- taxonomia v1: docs `31` e `32`

## Resultado quantitativo

| Campo | Concordancia exata |
| --- | ---: |
| `niche` | `7/10` |
| `sub_niche` | `4/10` |
| `sub_sub_niche` | `6/10` |
| `content_type` | `6/10` |
| `audience_intent` | `8/10` |
| `vehicle_brand` | `10/10` |
| `vehicle_model` | `9/10` |
| `vehicle_year_or_generation` | `5/10` |
| `automotive_system` | `4/10` |
| `component` | `6/10` |
| `problem` | `9/10` |

Leitura:

- houve boa convergencia em entidades explicitas, especialmente marca e modelo
- a maior divergencia ficou em `sub_niche`, `automotive_system` e
  `vehicle_year_or_generation`
- as divergencias confirmam que a v1 mistura tema, formato, motorizacao,
  componente e detalhe tecnico em eixos que ainda estao frouxos

## Comparacao por video

| `post_id` | Leitura |
| --- | --- |
| `pINW53ErjQI` | humano e GPT concordam que nao deve receber taxonomia automotiva; GPT registrou lacuna explicita `fora_escopo_automotivo` |
| `_j1gOOnjgcU` | ambos veem manutencao, mas GPT expandiu para multiplos subnichos/componentes: bateria, sensores, velas e motor |
| `z55GnDEg7_U` | ambos convergem em manutencao de motor, Renault Kwid e falha de motor; GPT trocou `fazer_motor` por `problema_cronico` e registrou `retifica_motor`, `troca_motor` e `orcamento_reparo` como lacunas |
| `CjFrJg6VCjc` | humano manteve `Teste/comparativo`; GPT classificou como `powertrain/eletrico`; ambos indicam lacuna para teste de autonomia, bateria de tracao e eletrificados |
| `nP0q6x1Uqs0` | humano priorizou `compra_venda/eletreficado`; GPT priorizou `mercado/lancamentos`; ambos apontam eletricos e necessidade de eixo para eletrificados |
| `JGzj254Kgs4` | ambos identificam Changan Lumin eletrico e decisao de compra; GPT manteve `test_drive` como subniche canonico e registrou conflito com compra/venda |
| `6qSnrkGd70I` | forte concordancia em manutencao/arrefecimento; GPT evitou `radiador` como componente canonico porque ele ainda nao existe na v1 |
| `aXbFPJMVGKw` | ambos convergem em review, Changan Uni-T e decisao de compra; GPT adicionou powertrain e cambio como detalhe tecnico do transcript |
| `RTZHxSE2t5M` | ambos convergem em mercado e entender mercado; humano usou `comparativo`, GPT usou `lancamentos` como aproximacao e registrou lacuna para pos-venda/pecas/oficinas |
| `UtWYJfldWHA` | ambos convergem em lancamento/review, Caoa Changan Uni-T e acompanhar lancamento; divergencia principal e niche `review` vs `mercado` |

## Achados para Taxonomia v2

- incluir `fora_escopo_automotivo` como rota controlada, sem forcar conteudos
  incidentais de transito em nichos automotivos
- separar `topic_path` de `activity_type`: casos como teste de autonomia,
  review de lancamento e mercado de eletrificados precisam de mais de um eixo
- criar dimensao ou subarvore para `eletrificados`, cobrindo `eletrico`,
  `hibrido`, `bateria_tracao`, `autonomia`, `regeneracao`, `garantia_bateria`
  e `consumo_energia`
- adicionar componentes ausentes com compatibilidade:
  `radiador`, `fluido_arrefecimento`, `bateria_tracao`, `sensor_maf`,
  `sonda_lambda`, `vela`, `motor_conjunto`
- criar temas de reparo/custo:
  `orcamento_reparo`, `retifica_motor`, `troca_motor`, `manutencao_corretiva`
- separar mercado de produto de pos-venda:
  `pecas_reposicao`, `gargalo_reparacao`, `nacionalizacao`, `skd_ckd`
- substituir `exact_year` como codigo unico por dois campos:
  `year_reference_type = exact_year` e `vehicle_year = 2026`

## Conclusao

Os `90s` aumentaram muito a qualidade da classificacao GPT 5.5 em entidades,
intencao e evidencia tecnica. A divergencia restante nao parece ser so falha do
modelo: ela mostra que a taxonomia v1 ainda nao consegue representar bem
conteudos com multiplas camadas, como `review + mercado + powertrain` ou
`manutencao + diagnostico + custo`.

Proxima decisao recomendada: desenhar a Taxonomia v2 com `automotive_domain`,
`activity_type`, `topic_path`, entidades do veiculo e matrizes de
compatibilidade tecnica.
