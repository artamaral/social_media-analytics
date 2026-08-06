# Analise das Transcricoes para Enriquecimento da Taxonomia V2 - R1

## Objetivo

Analisar os transcripts dos primeiros `90s` do doc `45` e registrar a
atualizacao controlada dos CSVs V2:

- `42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv`
- `43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv`

Esta etapa continua metodologica. Ela nao altera banco, workbook, pipeline ou
CSVs v1.

## Regra de curadoria

`ruido` passa a ser o codigo canonico para sintoma sonoro. `barulho` fica como
sinonimo e sinal textual em `example_signals`.

Termos removidos da lista canonica nesta rodada:

- `motorhome`
- `4x4`
- `carros_descartaveis`
- `efeito_dolphin`

Esses termos podem continuar como sinais, entidades descritivas ou retorica
editorial, mas nao como `topic_path_code`.

## Analise por video

| `post_id` | Leitura dos 90s | Termos brutos | Candidatos canonicos | Termos rejeitados |
| --- | --- | --- | --- | --- |
| `nKEuKTAX-eA` | Diagnostico de ruido em suspensao, com lista de componentes provaveis | `barulho`, `pivo`, `bieleta`, `bandeja`, `terminal_axial` | `diagnostico__ruido`, `diagnostico__ruido_suspensao`, `pivo_suspensao`, `bieleta`, `bandeja_suspensao`, `terminal_axial`, `problem = ruido` | `barulho` como codigo canonico |
| `ITBdyKnV5Pg` | Manutencao pesada em Honda HR-V 2020, com suspensao, freios, motor e cambio CVT | `manutencao_pesada`, `bucha_balanca`, `problema_cronico`, `disco_dianteiro`, `oleo_motor`, `filtros`, `velas`, `cambio_CVT`, `limaria` | `manutencao_pesada`, `bucha_balanca`, `disco_freio`, `oleo_motor`, `filtro_oleo`, `filtro_motor`, `vela`, `cambio_cvt`, `oleo_cambio`, `filtro_cambio`, `carter_cambio`, `limaria`, `oleo_degradado` | `cambio` solto |
| `aXbFPJMVGKw` | Review de Changan Uni-T com preco, SUV medio, motor turbo, autopilotagem, motorizacao e cambio | `preco`, `SUV_medio`, `motor_1_5_turbo`, `autopilotagem`, `motorizacao`, `cambio` | manter `review_teste__review_veiculo`; reforcar contexto `powertrain`, `motor_15_turbo_flex`, `cambio_dupla_embreagem` quando evidenciado | `cambio` solto |
| `nP0q6x1Uqs0` | Mercado de eletricos com BYD Dolphin, preco, bateria, autonomia e efeito Dolphin | `carro_eletrico`, `BYD_Dolphin`, `preco`, `efeito_Dolphin`, `bateria`, `autonomia` | manter `mercado_produto__mercado_eletrificados`, `powertrain`, `bateria_tracao`, `autonomia` | `efeito_dolphin` como codigo canonico |
| `xKNbBoiDt5g` | Apresentacao de Volvo transformado em motorhome; foco em veiculo especial/uso familiar | `caminhao`, `Volvo`, `motorhome`, `motor_casa`, `uso_familiar` | manter como entidade/tipo descritivo; usar `review_teste__review_veiculo` se entrar na amostra | `motorhome` como codigo canonico |
| `RTZHxSE2t5M` | Pos-venda e reparacao: carros chineses, eletrificados, hibridos, pecas, oficinas, SKD/CKD e nacionalizacao | `mecanicos`, `pecas`, `oficinas`, `gargalo`, `reparacao`, `chineses`, `eletrificados`, `hibridos`, `SKD`, `CKD`, `nacionalizacao` | `pos_venda_reparacao__gargalo_oficinas`, `pos_venda_reparacao__pecas_reposicao`, `pos_venda_reparacao__skd_ckd`, `pos_venda_reparacao__nacionalizacao`, `powertrain__eletrificados` | `carros_descartaveis` como codigo canonico |
| `3AjI62lO8b8` | Lancamento de SUV GWM Haval H7 com hibrido plug-in, preco e pegada off-road | `GWM_Haval_H7`, `2026`, `hibrido_plug_in`, `preco`, `SUV`, `off-road`, `H9` | `mercado_produto__lancamentos__suv`, `mercado_produto__preco_posicionamento`, `powertrain__eletrificados`, `sistema_hibrido_plug_in` | `4x4` como codigo canonico |
| `6qSnrkGd70I` | Procedimento de limpeza e troca de fluido de arrefecimento | `fluido_arrefecimento`, `limpa_radiador`, `aditivo`, `lavagem`, `drenagem`, `agua_torneira` | `manutencao_reparo__manutencao_preventiva__arrefecimento`, `aditivo_arrefecimento`, `agua_desmineralizada`, `limpa_radiador`, `filtro_arrefecimento`, `sistema_sujo` | inferir `superaquecimento` sem evidencia |
| `Ffmnzmm4Sf8` | Guia de pneus custo-beneficio com preco, qualidade, resistencia, conforto, durabilidade e aderencia | `pneus`, `custo_beneficio`, `preco`, `qualidade`, `resistencia`, `conforto`, `durabilidade`, `aderencia` | `mercado_produto__preco_posicionamento__custo_beneficio`, `manutencao_reparo__manutencao_preventiva__pneus`, `pneu`, `aderencia`, `durabilidade`, `conforto`, `resistencia` | tratar `aro_13_17` como categoria canonica agora |
| `uZVDGJXqrgU` | Instalacao de Retani Buffer em molas do Creta para reduzir trepidacao, batida seca e melhorar conforto | `Retani_Buffer`, `molas`, `Creta`, `trepidacao`, `batida_seca`, `amortecedor`, `conforto`, `estabilidade` | `manutencao_reparo__manutencao_preventiva__suspensao`, `mola`, `amortecedor`, `batida_seca`, `carro_desconfortavel`, `ruido` | `Retani_Buffer` como codigo canonico nesta rodada |

## Atualizacoes aplicadas

### `topic_path`

Foram adicionados caminhos para:

- `diagnostico__ruido`
- `diagnostico__ruido_suspensao`
- `manutencao_reparo__manutencao_preventiva__cambio_cvt`
- `manutencao_reparo__custo_reparo__manutencao_pesada`
- `mercado_produto__preco_posicionamento__custo_beneficio`
- `mercado_produto__lancamentos__suv`

Foram reforcados com novos sinais:

- `manutencao_reparo__manutencao_preventiva__suspensao`
- `manutencao_reparo__manutencao_preventiva__pneus`
- `off_road`
- `off_road__trilha`

Foi removido como caminho canonico:

- `off_road__4x4`

`4x4` permanece apenas como sinal textual de off-road.

### Compatibilidade tecnica

A matriz tecnica passou a cobrir melhor:

- `suspensao`: pivo, bieleta, bandeja, terminal axial, bucha de balanca, mola e
  amortecedor
- `freios`: disco de freio e desgaste
- `transmissao`: cambio CVT, oleo de cambio, filtros, carter e limaria
- `motor`: oleo, filtros, vela e desgaste
- `arrefecimento`: aditivo, agua desmineralizada, limpa radiador, filtro e
  sistema sujo
- `pneus`: pneu com atributos de aderencia, durabilidade, conforto e
  resistencia
- `powertrain`: hibrido plug-in e bateria de tracao

## Impacto nos 10 videos

Com a atualizacao, os `10` videos conseguem ser explicados sem categoria ad
hoc:

- `nKEuKTAX-eA`: `diagnostico__ruido_suspensao`
- `ITBdyKnV5Pg`: `manutencao_reparo__custo_reparo__manutencao_pesada`
- `aXbFPJMVGKw`: `review_teste__review_veiculo`
- `nP0q6x1Uqs0`: `mercado_produto__mercado_eletrificados`
- `xKNbBoiDt5g`: `review_teste__review_veiculo`, com `motorhome` como entidade
  descritiva
- `RTZHxSE2t5M`: `pos_venda_reparacao__gargalo_oficinas`
- `3AjI62lO8b8`: `mercado_produto__lancamentos__suv`
- `6qSnrkGd70I`: `manutencao_reparo__manutencao_preventiva__arrefecimento`
- `Ffmnzmm4Sf8`: `mercado_produto__preco_posicionamento__custo_beneficio`
- `uZVDGJXqrgU`: `manutencao_reparo__manutencao_preventiva__suspensao`

## Proximo passo

Rodar uma nova classificacao GPT usando os CSVs `42` e `43` atualizados como
contrato fechado da Taxonomia V2 enriquecida.
