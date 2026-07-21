# Comparacao GPT 5.5 V1 vs V2 - Round 1

## Objetivo

Comparar a rodada exploratoria GPT 5.5 anterior, baseada na Taxonomia V1, com
uma nova classificacao dos mesmos `10` videos usando a proposta metodologica da
Taxonomia V2.

Esta comparacao nao e benchmark final de modelo. O objetivo e medir se a V2
reduz ambiguidades estruturais e registra melhor os conflitos entre tema,
atividade, formato editorial, entidade veicular e contexto tecnico.

## Fontes

- amostra canonica: `docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv`
- rodada anterior por titulo/metadados: `docs/external_data/37_RESULTADO_GPT55_EXPLORATORIO_TAXONOMIA_R1.csv`
- transcripts Whisper locais: `docs/external_data/38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.csv`
- rodada anterior com `90s`: `docs/external_data/39_RESULTADO_GPT55_90S_WHISPER_R1.csv`
- guia V2: `docs/external_data/40_TAXONOMIA_VIDEO_V2_GUIA_CLASSIFICACAO.md`
- nova rodada V2: `docs/external_data/41_RESULTADO_GPT55_TAXONOMIA_V2_R1.csv`

## Escopo da nova rodada

Foram geradas `20` classificacoes:

- `10` registros em `gpt55_v2_entrega_1_descricao`
- `10` registros em `gpt55_v2_entrega_2_90s_iniciais`

Na etapa de descricao, a evidencia continua limitada a titulo e metadados,
porque as descricoes reais ainda nao estao versionadas no repositorio. Na etapa
de `90s`, a entrada usada foi o transcript Whisper local do doc `38`.

## Mudanca estrutural principal

Na V1, a classificacao precisava escolher um `niche` dominante. Isso criava
disputas como:

```text
review vs mercado vs powertrain
manutencao vs diagnostico vs custo
eletrico como nicho vs eletrico como tipo de motorizacao
motor/cambio como tema vs motor/cambio como contexto tecnico
```

Na V2, essas leituras foram separadas em:

```text
automotive_domain
activity_type
topic_path
content_type
audience_intent
vehicle_brand/model/year
automotive_system/component/problem
taxonomy_gaps
validation_issues
```

Resultado: a V2 nao elimina todos os conflitos, mas deixa claro onde cada
conflito deve morar.

## Comparacao por etapa

### Entrega 1 - descricao/titulo/metadados

| Indicador | V1 | V2 |
| --- | ---: | ---: |
| Videos avaliados | `10/10` | `10/10` |
| Descricao real disponivel | `0/10` | `0/10` |
| Videos com rota explicita de fora de escopo | `0/10` | `1/10` |
| Casos `review + mercado + powertrain` representados sem escolher um unico eixo | `0/10` | `4/10` |
| Casos de custo/reparo de motor sem usar `motor` como nicho solto | parcial | `1/1` |
| Casos com `eletrico/flex` preservados como powertrain/contexto | parcial | `4/4` |

Leitura:

- a V2 melhora a etapa de descricao mesmo sem descricao real, porque cria rota
  controlada para `fora_escopo` e evita que `review`, `mercado` e `powertrain`
  concorram como se fossem a mesma dimensao
- a incerteza continua alta quando so existe titulo, especialmente em
  procedimentos de manutencao e videos com titulo editorial agressivo
- `needs_human_review` continua frequente na etapa 1 porque a evidencia ainda e
  fraca

### Entrega 2 - 90s iniciais

| Indicador | V1 | V2 |
| --- | ---: | ---: |
| Videos avaliados com transcript | `10/10` | `10/10` |
| Videos com rota explicita de fora de escopo | `0/10` | `1/10` |
| Videos em que powertrain fica como contexto sem deslocar mercado/review | parcial | `6/6` |
| Videos com `motor`/`cambio` contextualizados, nao soltos | parcial | `3/3` |
| Videos com necessidade clara de matriz de compatibilidade | `7/10` | `7/10` |
| Videos com conflito estrutural ainda exigindo revisao humana | `10/10` | `9/10` |

Leitura:

- os `90s` continuam sendo decisivos para separar casos de titulo ambiguo
- a V2 reduz conflito semantico, mas aumenta a visibilidade de lacunas reais:
  multi-componentes, compatibilidade sistema/componente/problema e entidades
  de marca/modelo/versao
- a unica classificacao que ficou praticamente resolvida sem revisao humana foi
  `pINW53ErjQI`, porque a V2 agora permite assumir `fora_escopo >
  transito_comportamento` sem forcar rótulos tecnicos incidentais

## Comparacao por video

| `post_id` | Aprendizado V2 vs V1 |
| --- | --- |
| `pINW53ErjQI` | A V1 deixava `niche` vazio e registrava lacuna. A V2 cria rota operacional: `fora_escopo > transito_comportamento`. As mencoes a carro fervendo e marcha quebrada ficam incidentais. |
| `_j1gOOnjgcU` | A V1 precisava escolher multiplos `sub_niche` em uma coluna. A V2 usa `manutencao_reparo > manutencao_preventiva > limpeza_componentes` e explicita o problema futuro: multiplos componentes e sistemas. |
| `z55GnDEg7_U` | A V1 ficava em `manutencao_motor`. A V2 separa `reparo_corretivo`, `troca_motor`, `motor_conjunto`, `falha_de_motor`, ano e entidade Renault Kwid 2021. Diagnostico vira evidencia dentro do reparo. |
| `CjFrJg6VCjc` | A V1 colocava `powertrain/eletrico` como nicho. A V2 entende que o video e um teste: `review_teste > teste_autonomia`, com `powertrain` e `bateria_tracao` como contexto tecnico. |
| `nP0q6x1Uqs0` | A V1 oscilava entre `powertrain` e `mercado`. A V2 prioriza `mercado_produto > mercado_eletrificados`, preservando bateria/autonomia/garantia como contexto e lacunas. |
| `JGzj254Kgs4` | A V1 tinha disputa entre `review` e `compra_venda`. A V2 mostra que titulo sugere compra/venda, mas os `90s` indicam review de produto; ainda falta `topic_path_secondary` ou regra de dominancia. |
| `6qSnrkGd70I` | A V1 ja funcionava bem em `manutencao/arrefecimento`. A V2 melhora por separar `radiador`, `fluido_arrefecimento` e `sistema_sujo` como compatibilidade futura. |
| `aXbFPJMVGKw` | A V1 tratava como review/test drive com lacunas. A V2 preserva review como dominio, registra `motor_15_turbo_flex` e `cambio_dupla_embreagem` como contexto de powertrain, sem transformar cambio em nicho solto. |
| `RTZHxSE2t5M` | A V1 aproximava como `mercado/lancamentos`. A V2 encaixa melhor em `pos_venda_reparacao > gargalo_oficinas`, que e o verdadeiro foco dos `90s`. |
| `UtWYJfldWHA` | A V1 tinha conflito `mercado` vs `review`. A V2 resolve: `automotive_domain = mercado_produto`, `activity_type = lancamento`, `content_type = review`, com flex/powertrain como contexto. |

## Lacunas que permanecem

A V2 revelou lacunas mais precisas, nao apenas mais categorias:

- `topic_path_secondary` ou eixo de tema secundario para casos como review de
  produto com decisao de compra
- suporte controlado a multiplos componentes e talvez multiplos sistemas em
  videos educativos de manutencao
- matriz de compatibilidade entre `topic_path`, `automotive_system`,
  `component` e `problem`
- normalizacao de entidades, especialmente marca, modelo, versao e ano
- decisao sobre quando `problem` deve ser vazio em testes tecnicos sem falha,
  como autonomia de eletrico
- codigos canonicos para `sensor_maf`, `sonda_lambda`, `bateria_tracao`,
  `radiador`, `fluido_arrefecimento`, `cambio_dupla_embreagem`,
  `gargalo_oficinas`, `skd_ckd` e `tropicalizacao`

## Conclusao

A V2 e melhor que a V1 para o piloto porque troca a pergunta "qual nicho unico
do video?" por "qual dominio, atividade, rota, formato e contexto tecnico?".

O ganho mais importante nao e apenas mais acerto de rotulo. O ganho e que os
conflitos passam a ser auditaveis:

- `review + mercado + powertrain` deixa de ser erro e vira combinacao valida
- `manutencao + diagnostico + custo` pode ser descrito sem colapsar tudo em
  `motor`
- `fora_escopo` deixa de depender de campo vazio
- `eletrico`, `hibrido`, `flex` e `diesel` ficam em powertrain/contexto, nao em
  eletrica/eletronica

Resolucao operacional inicial:

1. `docs/external_data/42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv`
2. `docs/external_data/43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv`

Esses dois CSVs resolvem o gargalo imediato da rodada: a arvore V2 passa a ter
um contrato tabular e as combinacoes tecnicas deixam de depender apenas de
texto livre no guia. Banco, workbook e pipeline ainda permanecem inalterados.
