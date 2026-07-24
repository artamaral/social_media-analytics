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

Gravacao:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py --stage title_metadata --limit 1 --write
```

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
