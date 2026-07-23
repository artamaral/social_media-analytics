# Enriquecimento da Taxonomia V2 por Titulos e Proxima Rodada com Transcricao

## Objetivo

Registrar a primeira rodada de enriquecimento da Taxonomia V2 usando titulos de
videos ja monitorados no Supabase e definir o proximo passo equivalente usando
transcricao.

Esta entrega nao altera banco, workbook, pipeline nem CSVs v1. Ela serve como
curadoria metodologica para evoluir os CSVs V2 `42` e `43`.

## Fonte e limite da busca

Fonte consultada:

- `public.posts`
- `public.creators`
- `public.entities`

Limitacao importante:

- `public.posts` nao possui coluna `description`
- a busca foi feita sobre `title`
- as descricoes reais ainda precisam ser capturadas em etapa futura, se forem
  usadas como evidencia

Filtros aplicados:

- excluir creators com `Acelerados`, `ACF` ou `Tcar`
- exigir `followers >= 150000`
- exigir `engagement_pct >= 2.0`
- buscar sinais nos titulos para:
  - `diagnostico`
  - `manutencao`
  - `review`
  - `mercado`
  - `powertrain`
  - `pos_venda`
  - `off_road`

Resultado da busca:

- `5179` posts lidos
- `1462` candidatos apos filtros de qualidade e termos no titulo
- `10` videos selecionados para a rodada de enriquecimento por titulo

## Videos selecionados e termos extraidos do titulo

| `post_id` | Creator | Termos extraidos do titulo | Leitura V2 sugerida pelo titulo | Observacao |
| --- | --- | --- | --- | --- |
| `nKEuKTAX-eA` | carupdicasautomotivas | `barulho`, `oficina_mecanica`, `carros_usados`, `dicas_automotivas` | `diagnostico` ou `pos_venda_reparacao` | Bom para enriquecer sintomas e sinais de oficina; sistema ainda indefinido |
| `ITBdyKnV5Pg` | Carros com Tiago | `manutencao_pesada`, `Honda_HR-V`, `quanto_custa` | `manutencao_reparo > custo_reparo > orcamento_manutencao` | Bom para custo/reparo; marca e modelo explicitos |
| `aXbFPJMVGKw` | CarroChefe | `avaliacao`, `Changan_Uni-T`, `2026`, `VW`, `Jeep`, `Toyota` | `review_teste > review_veiculo` | Comparacao editorial no titulo nao basta para `comparativo` |
| `nP0q6x1Uqs0` | Eletricarbr | `eletricos`, `BYD_Dolphin_SE`, `R$_159_mil`, `Brasil`, `novo` | `mercado_produto > mercado_eletrificados` | Mistura mercado, lancamento e powertrain |
| `xKNbBoiDt5g` | BF///MS | `caminhao`, `motorhome`, `Yellowstone` | `review_teste > review_veiculo` ou `mercado_produto > compra_venda` | `motorhome` foi removido da lista canonica nesta rodada |
| `RTZHxSE2t5M` | Meu Carro Life Style | `mecanicos`, `carros_descartaveis`, `mercado`, `panico` | `pos_venda_reparacao > gargalo_oficinas` | `carros_descartaveis` foi removido por ser linguagem editorial |
| `3AjI62lO8b8` | Autoesporte | `GWM_Haval_H7`, `preco`, `motor`, `dimensoes`, `SUV`, `4x4`, `H9`, `Tank_300` | `review_teste > review_veiculo`; possivel `topic_path_secondary = mercado_produto > preco_posicionamento` | `4x4` foi removido da lista canonica nesta rodada |
| `6qSnrkGd70I` | MEGA DICAS AUTOMOTIVAS | `agua_do_radiador`, `limpa`, `melhorar` | `manutencao_reparo > manutencao_preventiva > arrefecimento` | Encaixa bem na matriz tecnica com `radiador` e `fluido_arrefecimento` |
| `Ffmnzmm4Sf8` | canal da mecanica | `pneus`, `custo_beneficio`, `mercado`, `melhores` | `mercado_produto > preco_posicionamento` ou `manutencao_reparo > manutencao_preventiva > pneus` | Caso util para `topic_path_secondary` |
| `uZVDGJXqrgU` | MEGA DICAS AUTOMOTIVAS | `suspensao`, `macia`, `confortavel`, `sem_barulho`, `melhorar` | `manutencao_reparo > manutencao_preventiva > suspensao` | Bom para enriquecer problemas de conforto e ruido |

## Curadoria dos termos

### Termos removidos da lista canonica

| Termo | Decisao | Motivo |
| --- | --- | --- |
| `motorhome` | remover | Melhor tratar como tipo/uso de veiculo ou entidade descritiva, nao como termo taxonomico V2 agora |
| `4x4` | remover | Pode ser sinal textual para `off_road`, mas nao precisa virar termo canonico nesta etapa |
| `carros_descartaveis` | remover | Linguagem editorial/opinativa, nao categoria tecnica ou taxonomica estavel |

### Candidatos mantidos para avaliar na V2

| Tipo | Termos |
| --- | --- |
| Sintomas/problemas | `barulho`, `ruido`, `carro_desconfortavel`, `suspensao_dura`, `sistema_sujo` |
| Componentes/sistemas | `radiador`, `fluido_arrefecimento`, `pneus`, `suspensao` |
| Mercado/produto | `custo_beneficio`, `preco_posicionamento`, `mercado_eletrificados` |
| Entidades veiculares | `Honda_HR-V`, `Changan_Uni-T`, `BYD_Dolphin_SE`, `GWM_Haval_H7`, `Tank_300`, `H9` |
| Regra estrutural | `topic_path_secondary` para `review + preco`, `review + off_road` e `manutencao + mercado` |

## Como repetir usando transcricao

Objetivo da proxima etapa:

- usar evidencia textual mais rica que o titulo
- separar termo editorial de termo tecnico
- identificar componentes, problemas e sistemas com mais seguranca
- confirmar quais candidatos de titulo devem virar codigos canonicos

Entrada recomendada:

- os mesmos `10` videos listados neste documento
- transcript local dos primeiros `90s`
- se o video tiver menos de `90s`, usar a duracao completa
- manter `source_method = yt-dlp+faster-whisper-local`

Campos minimos da extracao por transcricao:

```text
post_id
video_url
transcription_status
transcript_90s
extracted_raw_terms
candidate_canonical_terms
rejected_terms
suggested_topic_path
suggested_topic_path_secondary
suggested_automotive_system
suggested_component
suggested_problem
taxonomy_gaps
validation_issues
needs_human_review
```

Regras da extracao:

- nao promover termo de fala para codigo canonico automaticamente
- manter `motorhome`, `4x4` e `carros_descartaveis` fora da lista canonica,
  salvo revisao humana futura
- se `4x4` aparecer na fala, tratar como sinal textual de off-road ou
  capacidade de tracao, nao como codigo canonico nesta rodada
- se `motorhome` aparecer, registrar como entidade/tipo de uso descritivo
- se `carros_descartaveis` aparecer, registrar como retorica editorial
- preencher `component` e `problem` somente quando houver compatibilidade com
  `automotive_system`
- marcar `needs_human_review = true` quando houver multiplos sistemas,
  multiplos componentes ou conflito entre tema principal e tema secundario

## Criterio de aceite da proxima etapa

- os `10` videos deste documento possuem transcript ou falha registrada
- cada video tem lista separada de:
  - termos brutos extraidos
  - candidatos canonicos
  - termos rejeitados
- a extracao por transcricao confirma ou corrige a leitura feita pelo titulo
- nenhuma categoria canonica nova e criada sem justificativa
- os aprendizados alimentam uma revisao futura dos CSVs `42` e `43`

## Resultado da etapa com transcricao

A etapa com transcricao foi executada e documentada em:

- `docs/external_data/45_TRANSCRICOES_90S_ENRIQUECIMENTO_TAXONOMIA_V2_R1.md`
- `docs/external_data/45_TRANSCRICOES_90S_ENRIQUECIMENTO_TAXONOMIA_V2_R1.csv`
- `docs/external_data/46_ANALISE_TRANSCRICOES_ENRIQUECIMENTO_TAXONOMIA_V2_R1.md`

Decisao principal:

- `ruido` virou codigo canonico para sintoma sonoro
- `barulho` ficou como sinonimo e sinal textual
- `motorhome`, `4x4`, `carros_descartaveis` e `efeito_dolphin` permaneceram
  fora da lista canonica
- os CSVs `42` e `43` foram enriquecidos com caminhos e compatibilidades
  derivados dos transcripts
