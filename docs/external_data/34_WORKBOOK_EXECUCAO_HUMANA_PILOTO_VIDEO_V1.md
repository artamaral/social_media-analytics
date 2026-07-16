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
- `docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.xlsm`

## Estrutura do arquivo

O workbook possui tres abas:

- `taxonomias`
- `execucao_humana`
- `listas`

A aba `listas` fica oculta e serve apenas como fonte dos dropdowns.

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

## Conteudo da aba `execucao_humana`

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

## Geracao

O arquivo e gerado por:

- `scripts/external_data/build_pilot_human_workbook.ps1`

Comando:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/external_data/build_pilot_human_workbook.ps1
```

## Observacao operacional

O workbook e publicado em formato `.xlsm` para manter compatibilidade com a
evolucao futura da rodada humana em Excel.

Na versao atual, o campo `sub_niche` permite multiplos valores por digitacao
manual no mesmo campo, mantendo o dropdown como sugestao inicial de valores
canonicos.
