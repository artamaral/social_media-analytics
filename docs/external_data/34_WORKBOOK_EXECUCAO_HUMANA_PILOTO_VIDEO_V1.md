# Workbook de Execucao Humana do Piloto de Videos v1

## Objetivo

Consolidar em um unico arquivo Excel a base operacional da rodada humana do
piloto de `10` videos do Sprint 6.

O workbook existe para facilitar a classificacao manual em ambiente de
planilha, sem substituir os artefatos canonicos anteriores.

## Fonte de verdade desta fase

Este workbook deve ser usado em conjunto com:

- `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.md`
- `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.csv`
- `docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.md`
- `docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.csv`
- `docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.md`
- `docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv`
- `docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.xlsx`

Tambem e publicada uma copia compativel em:

- `docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.xlsm`

## Estrutura do arquivo

O workbook atualizado pelo avaliador humano possui quatro abas:

- `taxonomias`
- `execucao_humana_title`
- `execucao_humana_transcricao_90s`
- `listas`

A aba `listas` fica oculta e serve apenas como fonte dos dropdowns.

Mapeamento metodologico:

- `execucao_humana_title` registra a avaliacao informada como baseada na
  descricao, antes de assistir ao video
- `execucao_humana_transcricao_90s` registra a avaliacao depois de assistir aos
  `90s` iniciais; o nome da aba nao significa que uma transcricao textual tenha
  sido persistida no workbook

## Conteudo da aba `taxonomias`

Consolida em uma unica tabela os registros canonicos de:

- taxonomia principal do piloto
- dimensoes complementares do piloto

As colunas preservadas sao:

- `dimension`
- `code`
- `label_pt`
- `parent_code`
- `description`
- `example_signals`
- `allowed_in_pilot`

## Conteudo das abas de execucao humana

Cada linha representa um dos `10` videos primarios da amostra piloto.

Campos de apoio:

- `post_id`
- `video_url`
- `title`
- `creator`
- `video_type`
- `followers`
- `views`
- `likes`
- `comments`
- `engagement_pct`
- `post_date`
- `duration`

Campos de classificacao humana:

- `niche`
- `sub_niche`
- `sub_sub_niche`
- `content_type`
- `audience_intent`
- `vehicle_brand`
- `vehicle_model`
- `vehicle_year_or_generation`
- `automotive_system`
- `component`
- `problem`
- `observacoes`
- `classificacao_finalizada`

## Regras de preenchimento

- `video_url` usa link clicavel com texto `abrir_video`
- os campos fechados ou semifechados possuem dropdown com os valores canonicos
- os dropdowns nao bloqueiam digitacao manual fora da lista
- `sub_niche` aceita mais de um valor no mesmo campo, separados por `, `
- `observacoes` deve registrar duvidas, sinais ambigous e qualquer excecao de
  classificacao
- `classificacao_finalizada` deve ser preenchido com `sim` ou `nao`

## Entregas da classificacao humana

O workbook registra as duas entregas em abas separadas do mesmo arquivo, sempre
com os mesmos `10` videos e os mesmos campos:

- `entrega_1_descricao`: classificacao baseada na descricao, sem assistir ao
  video
- `entrega_2_90s_iniciais`: nova classificacao depois de assistir e ouvir os
  `90s` iniciais; quando o video for menor, usar o conteudo completo

Uma entrega nao deve sobrescrever a outra.

Na segunda entrega, qualquer mudanca de classificacao deve refletir a evidencia
adicional observada no inicio do video. A comparacao entre os dois arquivos
sera usada para identificar quais dimensoes dependem de transcricao ou consumo
do conteudo.

Pre-requisito:

- incluir a descricao dos `10` videos no material de execucao antes da Entrega
  1, pois o CSV canonico da amostra ainda nao possui a coluna `description`

Resultado consolidado:

- `docs/external_data/36_RESULTADO_BASELINE_HUMANO_E_CONTRATO_AVALIACAO_GPT_V1.md`
- `docs/external_data/36_BASELINE_HUMANO_DUAS_ETAPAS_V1.csv`

## Geracao

O arquivo e gerado por:

- `scripts/external_data/build_pilot_human_workbook.ps1`

Comando:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/external_data/build_pilot_human_workbook.ps1
```

O gerador valida automaticamente:

- `102` registros de taxonomia, alem do cabecalho
- `10` videos primarios, alem do cabecalho
- `10` hyperlinks de YouTube
- `12` campos com dropdown

## Observacao operacional

Abrir preferencialmente o arquivo `.xlsx` nesta versao. O `.xlsm` e mantido
para compatibilidade com a evolucao futura da rodada humana em Excel.

Na versao atual, o campo `sub_niche` permite multiplos valores por digitacao
manual no mesmo campo, mantendo o dropdown como sugestao inicial de valores
canonicos.

Validacao executada em 2026-07-16 no Excel desktop:

- aba `taxonomias`: `103` linhas e `7` colunas
- aba `execucao_humana`: `11` linhas e `25` colunas
- dropdowns ativos e editaveis nos `12` campos previstos
- `10` links clicaveis para os videos

## Estado atual do gerador

O script `build_pilot_human_workbook.ps1` ainda representa a estrutura anterior
com uma unica aba humana. Nao regenerar o workbook preenchido antes de atualizar
o script para preservar as duas abas e o baseline registrado.
