# Video Classification GPT V2

Script minimo para classificar videos com GPT usando a Taxonomia Video V2.

## Escopo

- busca videos em `public.posts`
- usa Taxonomia V2 carregada no Supabase
- chama `gpt-5-nano` para `title_metadata`
- valida JSON e regras semanticas basicas
- grava em `video_classification_results`,
  `video_classification_technical_contexts` e
  `video_classification_vehicle_entities`
- envia a taxonomia em formato compacto para reduzir custo e risco de resposta
  incompleta
- marca contexto tecnico fora da matriz V2 como `needs_review`, em vez de
  gravar como compativel
- usa `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md` como skill
  padrao, incluindo a regra documentada de `confidence_score`

Fora de escopo nesta versao:

- cron
- ingestao de videos
- transcricao por API
- dashboard
- fallback automatico para modelo maior

## Variaveis

```text
OPENAI_API_KEY
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
CLASSIFIER_MODEL_TITLE=gpt-5-nano
CLASSIFIER_MODEL_TRANSCRIPT=gpt-5-nano
```

O limite padrao de saida e `6000` tokens. Se a OpenAI retornar
`incomplete/max_output_tokens` para um video especifico, reprocessar com:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py --stage title_metadata --post-id Z8hPL7MGOxU --max-output-tokens 9000 --dry-run
```

## Uso local

Antes de rodar o classificador, aplicar no Supabase:

1. `sql/ddl/tables/022_create_video_taxonomy_classification.sql`
2. `sql/dml/seed_video_taxonomy_v2.sql`
3. `sql/ddl/views/023_create_v_video_classification_latest.sql`
4. `sql/ddl/tests/011_test_video_taxonomy_classification.sql`

Dry-run por titulo/metadados:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py --stage title_metadata --limit 1 --dry-run
```

Confirmar a versao do script copiado para a VPS:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py --version
```

A versao esperada apos alinhar a skill oficial e a regra de confianca e:

```text
classify_videos_gpt_v2.py 2026-07-24-r5-post-id-limit
```

Aliases equivalentes:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py --script-version
python scripts/video_classification/classify_videos_gpt_v2.py -V
```

Regra aplicada:

- `0.90` a `1.00`: evidencia direta, clara e especifica
- `0.70` a `0.89`: evidencia boa, mas com alguma ambiguidade
- `0.50` a `0.69`: evidencia parcial ou titulo pouco especifico
- abaixo de `0.50`: exige `needs_human_review=true`

Gravacao:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py --stage title_metadata --limit 1 --write
```

Quando `--post-id` e usado mais de uma vez, o script ajusta `--limit`
automaticamente para cobrir todos os IDs informados. Assim uma lista explicita
de videos nao fica truncada pelo default operacional de `5`.

Classificacao com transcript salvo em CSV:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --transcripts-csv docs/external_data/56_TRANSCRICOES_90S_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv \
  --limit 1 \
  --dry-run
```

## Deploy minimo na VPS

Copiar o script para:

```text
/opt/social-media-analytics/bin/classify_videos_gpt_v2.py
```

Criar configuracao fora do Git:

```text
/opt/social-media-analytics/config/classifier.env
```

Executar manualmente antes de ativar cron.
