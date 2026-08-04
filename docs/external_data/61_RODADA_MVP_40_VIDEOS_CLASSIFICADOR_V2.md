# Rodada MVP 40 videos - Classificador V2

## Objetivo

Rodar uma validacao ampliada do classificador V2 em `transcript_90s`, usando
`40` videos:

- `20` videos ja trabalhados: Batch 1 piloto + Batch 2/amostra aleatoria;
- `20` videos novos selecionados no Supabase com os filtros originais:
  `followers >= 150000`, `engagement_pct >= 2.0`, `video_type in (long, short)`
  e exclusao de `Acelerados`, `ACF` e `Tcar`;
- para os novos videos, a amostra ficou balanceada em `10 long` e `10 short`.

O objetivo desta rodada nao e corrigir video a video durante a execucao. A
rodada serve para revelar padroes recorrentes e decidir se o harness esta
pronto para MVP manual/cron ou se precisa de ate `5` ajustes sistemicos.

## Artefatos

- `61_RODADA_MVP_40_VIDEOS_CLASSIFICADOR_V2.csv`: lista canonica de execucao.
- CSVs temporarios na VPS: `tmp/transcripts_mvp40_lote_1.csv` ate
  `tmp/transcripts_mvp40_lote_4.csv`.
- Este documento: contrato operacional da rodada e modelo de analise final.

## Fonte dos 40 videos

| Lote | Linhas | Origem | Observacao |
| --- | ---: | --- | --- |
| `lote_1` | 1-10 | Batch 1 piloto | `33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv` |
| `lote_2` | 11-20 | Batch 2/amostra aleatoria | `55_AMOSTRA_ALEATORIA_TAXONOMIA_V2_10_VIDEOS_R1.csv` |
| `lote_3` | 21-30 | Novos elegiveis long | Supabase `posts` + `creators`, seed `20260804` |
| `lote_4` | 31-40 | Novos elegiveis short | Supabase `posts` + `creators`, seed `20260804` |

Validacao da selecao dos novos videos:

- videos ja usados excluidos da selecao nova: `36`;
- universo elegivel apos filtros: `3410`;
- longs elegiveis: `1493`;
- shorts elegiveis: `1917`;
- selecionados novos: `20`;
- nenhum creator dos novos combina com `Acelerados`, `ACF` ou `Tcar`.

## Regra operacional

Rodar somente:

```text
--stage transcript_90s
```

Nao rodar `title_metadata` nesta validacao. O modo `title_metadata` continua
apenas diagnostico.

Configuracao esperada:

- script versionado r42 ou superior;
- `--max-output-tokens 16000`;
- `--sleep-seconds 90`;
- `--timing`;
- WARP SOCKS5 em `socks5://127.0.0.1:11080`;
- cookies em `config/youtube_cookies.txt`;
- extractor args `youtube:player-client=android_vr`;
- transcricao local com `faster-whisper small` e fallback automatico para
  `medium` quando houver gatilho objetivo.

## Comandos VPS

Antes da execucao:

```bash
cd /opt/social-media-analytics
. .venv/bin/activate
python bin/classify_videos_gpt_v2.py --version
```

O resultado esperado deve ser `2026-08-04-r42-fallback-regression-guard` ou
versao posterior.

### Lote 1 - Batch 1 piloto

```bash
python bin/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id pINW53ErjQI \
  --post-id _j1gOOnjgcU \
  --post-id z55GnDEg7_U \
  --post-id CjFrJg6VCjc \
  --post-id nP0q6x1Uqs0 \
  --post-id JGzj254Kgs4 \
  --post-id 6qSnrkGd70I \
  --post-id aXbFPJMVGKw \
  --post-id RTZHxSE2t5M \
  --post-id UtWYJfldWHA \
  --include-already-classified \
  --max-output-tokens 16000 \
  --yt-dlp-cookies config/youtube_cookies.txt \
  --yt-dlp-user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --yt-dlp-proxy "socks5://127.0.0.1:11080" \
  --yt-dlp-extractor-args "youtube:player-client=android_vr" \
  --transcripts-output tmp/transcripts_mvp40_lote_1.csv \
  --sleep-seconds 90 \
  --timing \
  --write
```

### Lote 2 - Batch 2/amostra aleatoria

```bash
python bin/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id KwZFtY1w8FY \
  --post-id 0YeiiIpSrP0 \
  --post-id KONPXAjlkn8 \
  --post-id cwQIxaJDJAE \
  --post-id cLH17x4LiCA \
  --post-id fvt-UH964yA \
  --post-id Yel1puu2qGQ \
  --post-id UMEYwVvLsGM \
  --post-id Sth4l0Kc2NY \
  --post-id yAytAka2dfg \
  --include-already-classified \
  --max-output-tokens 16000 \
  --yt-dlp-cookies config/youtube_cookies.txt \
  --yt-dlp-user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --yt-dlp-proxy "socks5://127.0.0.1:11080" \
  --yt-dlp-extractor-args "youtube:player-client=android_vr" \
  --transcripts-output tmp/transcripts_mvp40_lote_2.csv \
  --sleep-seconds 90 \
  --timing \
  --write
```

### Lote 3 - Novos elegiveis long

```bash
python bin/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id R3y-lSe0K4s \
  --post-id BrKVhF-oG80 \
  --post-id NuLcOS208w0 \
  --post-id Xx1TYZnPYK8 \
  --post-id ZspY7eFGJXo \
  --post-id fgjijU3h7Cw \
  --post-id DWYtJ3UHTXs \
  --post-id 4_qw9-un9D0 \
  --post-id 4VPqBe4zjpo \
  --post-id FaobcvNYgUc \
  --include-already-classified \
  --max-output-tokens 16000 \
  --yt-dlp-cookies config/youtube_cookies.txt \
  --yt-dlp-user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --yt-dlp-proxy "socks5://127.0.0.1:11080" \
  --yt-dlp-extractor-args "youtube:player-client=android_vr" \
  --transcripts-output tmp/transcripts_mvp40_lote_3.csv \
  --sleep-seconds 90 \
  --timing \
  --write
```

### Lote 4 - Novos elegiveis short

```bash
python bin/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id 9jdCcUr6KDI \
  --post-id TukIrroE8Z4 \
  --post-id Bcf0ikE2Aac \
  --post-id 4FsnWZmuiQ0 \
  --post-id ouOjW0d1hxw \
  --post-id OlnXxCHKisM \
  --post-id XSkI9I7hEIw \
  --post-id PusuX6OzOC0 \
  --post-id VzRl2S0RkPc \
  --post-id 5oLUBF-Iu6k \
  --include-already-classified \
  --max-output-tokens 16000 \
  --yt-dlp-cookies config/youtube_cookies.txt \
  --yt-dlp-user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --yt-dlp-proxy "socks5://127.0.0.1:11080" \
  --yt-dlp-extractor-args "youtube:player-client=android_vr" \
  --transcripts-output tmp/transcripts_mvp40_lote_4.csv \
  --sleep-seconds 90 \
  --timing \
  --write
```

## Regra de parada durante a rodada

Nao corrigir caso isolado durante a execucao. Parar apenas se ocorrer uma das
condicoes sistemicas:

- falha de download/transcricao acima de `30%` no lote;
- erro de schema impedindo gravacao de varios videos;
- incompatibilidade SQL/taxonomia que bloqueie varios videos;
- regressao clara que contamine dados gravados.

Quando houver uma falha isolada, registrar o erro e seguir para o proximo lote.

## Analise pos-rodada

Depois dos quatro lotes, extrair do Supabase:

- total de videos processados, sucessos e falhas operacionais;
- tempo medio por video a partir dos logs com `--timing`;
- quantidade de fallbacks `small -> medium`;
- fallbacks aceitos e rejeitados;
- `needs_human_review` por lote;
- distribuicao de `topic_path`;
- `taxonomy_gaps` e `validation_issues` recorrentes;
- contextos tecnicos com `needs_review`;
- entidades de veiculo por `catalog_match_level`;
- entidades `not_found` e possiveis falsos positivos;
- casos de `sem_match_taxonomico`.

## Criterio de MVP

Considerar pronto para MVP manual/cron somente se:

- pelo menos `85%` dos videos forem gravados sem falha operacional;
- menos de `25%` ficarem com `needs_human_review`;
- nenhum erro recorrente exigir correcao manual video a video;
- `vehicle_entities` gravar canonico ate `fabricante/modelo/ano`, sem
  versao/trim como entidade;
- `technical_contexts[]` nao trouxer feature como `problem`;
- fallback medium nao substituir resultado melhor do small quando houver
  regressao semantica.

Se os criterios nao forem atingidos, o proximo ciclo deve ter no maximo `5`
ajustes sistemicos priorizados por recorrencia.

## Template de resultado

Preencher apos a execucao:

| Metrica | Resultado |
| --- | ---: |
| Videos planejados | 40 |
| Videos gravados com sucesso | a preencher |
| Falhas operacionais | a preencher |
| Taxa de sucesso operacional | a preencher |
| Videos com fallback medium | a preencher |
| Fallbacks rejeitados por regressao | a preencher |
| `needs_human_review` | a preencher |
| `sem_match_taxonomico` | a preencher |
| Entidades `matched` | a preencher |
| Entidades `not_found` | a preencher |

Principais padroes a registrar:

- falhas de download/transcricao;
- problemas de taxonomia;
- problemas de contexto tecnico;
- problemas de entidade veicular;
- recomendacao objetiva para MVP.

## Fora do escopo

- ativar cron;
- criar ingestao nova;
- alterar dashboard;
- expandir taxonomia por versao/acabamento;
- corrigir videos individualmente durante a rodada.
