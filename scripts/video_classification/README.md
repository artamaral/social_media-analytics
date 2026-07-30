# Video Classification GPT V2

Script minimo para classificar videos com GPT usando a Taxonomia Video V2.

## Escopo

- busca videos em `public.posts`
- usa Taxonomia V2 carregada no Supabase
- chama `gpt-5-nano` para `title_metadata`
- baixa e corta os primeiros `90s` de audio com `yt-dlp` e `imageio-ffmpeg`
- transcreve localmente com `faster-whisper small`, CPU e `int8`
- usa `transcript_90s` como classificacao operacional quando a transcricao
  estiver disponivel, combinando titulo, metadados e transcript em uma chamada
- avalia a qualidade textual do transcript na mesma chamada `gpt-5-nano`
- valida JSON e regras semanticas basicas
- grava em `video_classification_results`,
  `video_classification_technical_contexts` e
  `video_classification_vehicle_entities`
- reconcilia `vehicle_entities[]` contra
  `public.v_carrosnaweb_vehicle_catalog` antes de gravar, preenchendo
  identificador e nomes canonicos quando houver match seguro
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
- ingestao persistente de descricao do YouTube
- dashboard
- fallback automatico para modelo maior

## Decisao de uso

O uso operacional recomendado e classificar uma vez por video com
`--stage transcript_90s`. Esse estagio envia titulo, metadados e transcript dos
primeiros `90s` no mesmo input.

Sem `--transcripts-csv`, o proprio script gera a transcricao local. Quando um
CSV e informado, ele e reutilizado para permitir replay das rodadas de
desenvolvimento.

`public.posts` nao possui descricao. Por padrao, o harness envia
`description = null`. Para testes manuais, um CSV externo de descricoes pode
ser informado com `--descriptions-csv`; isso adiciona a descricao ao JSON de
entrada sem alterar `public.posts` nem criar ingestao oficial.

`--stage title_metadata` continua disponivel para diagnostico, calibracao e
comparacao de sinal fraco, mas nao deve ser tratado como resultado operacional
final quando a transcricao ja existe.

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
2. `sql/ddl/tables/023_add_transcript_quality_to_video_classification.sql`
3. `sql/ddl/tables/024_add_catalog_model_match_to_video_vehicle_entities.sql`
4. `sql/ddl/views/022_create_v_carrosnaweb_vehicle_catalog.sql`
5. `sql/dml/seed_video_taxonomy_v2.sql`
6. `sql/ddl/views/023_create_v_video_classification_latest.sql`
7. `sql/ddl/tests/010_test_carrosnaweb_catalog.sql`
8. `sql/ddl/tests/011_test_video_taxonomy_classification.sql`

## Estrutura SQL

Cada execucao cria uma rodada e grava resultados por video:

```text
video_taxonomy_versions
  1:N -> video_classification_runs
           1:N -> video_classification_results
                    1:N -> video_classification_technical_contexts
                    1:N -> video_classification_vehicle_entities
```

Chaves principais:

- `video_classification_runs.taxonomy_version_id` ->
  `video_taxonomy_versions.id`
- `video_classification_results.run_id` ->
  `video_classification_runs.id`
- `video_classification_results.post_id` -> `posts.post_id`
- `video_classification_technical_contexts.classification_result_id` ->
  `video_classification_results.id`
- `video_classification_vehicle_entities.classification_result_id` ->
  `video_classification_results.id`
- `video_classification_vehicle_entities.catalog_row_id` aponta para o
  `catalog_row_id` exposto por `v_carrosnaweb_vehicle_catalog`, que vem de
  `market_carrosnaweb_model_years.id`
- `video_classification_vehicle_entities.catalog_model_id` aponta para
  `market_carrosnaweb_models.id` quando o texto sustenta modelo, mas nao ano

Resumo pratico:

- `video_classification_results` guarda a decisao principal do video.
- `video_classification_technical_contexts` guarda a lista repetivel de
  sistemas, componentes e problemas.
- `video_classification_vehicle_entities` guarda os veiculos extraidos e o
  match canonico Carros na Web quando possivel.

Dry-run por titulo/metadados:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py --stage title_metadata --limit 1 --dry-run
```

Extrair descricoes via YouTube Data API para os 10 videos canonicos do Batch 1:

```bash
python scripts/video_classification/extract_youtube_descriptions.py \
  --sample-csv docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv \
  --limit 10 \
  --output tmp/youtube_descriptions_batch1.csv
```

Classificar por titulo/metadados adicionando a descricao salva no CSV:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py \
  --stage title_metadata \
  --post-id pINW53ErjQI \
  --descriptions-csv tmp/youtube_descriptions_batch1.csv \
  --max-output-tokens 9000 \
  --dry-run
```

Confirmar a versao do script copiado para a VPS:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py --version
```

A versao esperada apos alinhar a skill oficial e a regra de confianca e:

```text
classify_videos_gpt_v2.py 2026-07-24-r7-faster-whisper-quality
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

Regra anti-inferencia:

- `fora_escopo` tem precedencia quando houver evidencia textual de moto,
  nao-automotivo, transito/comportamento ou entretenimento sem tema automotivo
  principal
- `sem_match_taxonomico` e usado quando o input parece automotivo, mas nao ha
  match seguro em nenhum `topic_path` especifico
- `sem_match_taxonomico` exige `confidence_score < 0.50`,
  `needs_human_review=true`, `validation_issues` e `technical_contexts=[]`
- titulo generico de alerta/cuidado/perigo nao autoriza inferir diagnostico,
  luz de painel, scanner, motor, cambio ou componente

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

Classificacao com transcricao local integrada:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id pINW53ErjQI \
  --transcripts-output tmp/transcripts_validacao.csv \
  --dry-run
```

Se o YouTube bloquear o download com `Sign in to confirm you're not a bot`,
exporte cookies do navegador para um arquivo fora do Git e informe o caminho:

```bash
python scripts/video_classification/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id pINW53ErjQI \
  --yt-dlp-cookies config/youtube_cookies.txt \
  --yt-dlp-user-agent "<user_agent_do_navegador>" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --transcripts-output tmp/transcripts_validacao.csv \
  --dry-run
```

Quando os cookies vierem de uma chamada `requests` do navegador, passar tambem
o `user-agent` da mesma chamada ajuda a manter a sessao coerente na VPS.

Teste manual com PO Token Provider plugin do `yt-dlp`:

```bash
python -m pip install -U yt-dlp bgutil-ytdlp-pot-provider
```

Se Docker estiver disponivel na VPS:

```bash
docker run --name bgutil-provider -d -p 127.0.0.1:4416:4416 --init brainicism/bgutil-ytdlp-pot-provider
```

Para IP de datacenter bloqueado pelo YouTube, usar WARP apenas isolado em
container, expondo SOCKS5 local para o `yt-dlp`:

```bash
docker run -d \
  --name warproxy-test \
  --restart unless-stopped \
  -p 127.0.0.1:11080:1080 \
  ghcr.io/kingcc/warproxy:latest

curl -4 --max-time 30 \
  -x socks5h://127.0.0.1:11080 \
  https://www.cloudflare.com/cdn-cgi/trace | egrep 'warp|ip|colo'
```

```bash
python scripts/video_classification/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id pINW53ErjQI \
  --yt-dlp-cookies config/youtube_cookies.txt \
  --yt-dlp-user-agent "<user_agent_do_navegador>" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --yt-dlp-proxy "socks5://127.0.0.1:11080" \
  --yt-dlp-extractor-args "youtube:player-client=default,mweb" \
  --yt-dlp-extractor-args "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416" \
  --transcripts-output tmp/transcripts_po_token_test.csv \
  --dry-run
```

O script apenas repassa `--plugin-dirs`, `--extractor-args` e `--proxy` ao
`yt-dlp`. Plugins, PO Tokens, cookies e configuracoes locais ficam fora do Git.

Se o caminho direto do `yt-dlp` falhar com `ffmpeg exited with code -11`, o
classificador usa fallback estavel: baixa a fonte de audio/video sem conversao
pelo `yt-dlp`, preferindo audio leve `139/140` antes do progressivo `18`, e
corta/converte os primeiros `90s` com o `ffmpeg` do `imageio-ffmpeg` em uma
etapa separada.

O transcript completo pode ser preservado no CSV temporario, mas nao e gravado
no Supabase. O `input_payload` persistido contem apenas hash, tamanho, duracao e
proveniencia da transcricao.

Entidades de veiculo:

- o GPT devolve apenas `vehicle_brand_raw`, `vehicle_model_raw`,
  `vehicle_year`, `vehicle_generation` e evidencia textual
- o script tambem extrai veiculos diretamente de `title`, `description` e
  `transcript_90s`, sem enviar o catalogo Carros na Web ao GPT
- o script consulta `v_carrosnaweb_vehicle_catalog` antes de inserir em
  `video_classification_vehicle_entities`; em `--dry-run`, o JSON impresso
  tambem inclui os campos resolvidos e entidades encontradas pelo script apos a
  validacao do schema GPT
- match unico por marca/modelo/ano grava `entity_status=matched` e
  `catalog_row_id` + `catalog_model_id`
- match sem ano suficiente para identificar modelo grava `catalog_model_id`,
  `catalog_match_level=model` e deixa `catalog_row_id` nulo, sem escolher ano
  artificial
- quando o texto cita apenas modelo unico, como `Kwid`, o script preenche a
  montadora canonica do catalogo, como `Renault`
- modelos que tambem sao palavras comuns exigem marca explicita e proxima no
  texto antes de virar entidade; a lista inicial condicionada e `100`, `tipo`,
  `bora` e `link`
- exemplos rejeitados sem marca proxima: `100%`, `bora para o canal`,
  `tipo SKD` e `link na descricao`
- entidade explicita nao encontrada grava `not_found`

Instalar dependencias:

```bash
python3 -m pip install -r scripts/video_classification/requirements.txt
```

## Deploy minimo na VPS

Conexao local esperada via alias SSH:

```powershell
ssh hostinger-vps
```

Copiar o script para:

```text
/opt/social-media-analytics/bin/classify_videos_gpt_v2.py
```

Criar configuracao fora do Git:

```text
/opt/social-media-analytics/config/classifier.env
/opt/social-media-analytics/config/youtube_cookies.txt
```

Estrutura minima na VPS:

```bash
mkdir -p /opt/social-media-analytics/bin
mkdir -p /opt/social-media-analytics/config
mkdir -p /opt/social-media-analytics/logs
mkdir -p /opt/social-media-analytics/tmp
mkdir -p /opt/social-media-analytics/scripts/video_classification
chmod 700 /opt/social-media-analytics/config
```

Copiar arquivos pelo PowerShell local:

```powershell
scp C:\social_media-analytics\scripts\video_classification\classify_videos_gpt_v2.py hostinger-vps:/opt/social-media-analytics/bin/classify_videos_gpt_v2.py
scp C:\social_media-analytics\scripts\video_classification\requirements.txt hostinger-vps:/opt/social-media-analytics/scripts/video_classification/requirements.txt
scp C:\social_media-analytics\tmp\youtube_cookies_from_paste.txt hostinger-vps:/opt/social-media-analytics/config/youtube_cookies.txt
```

O arquivo de cookies e segredo operacional e nao deve ser commitado.

Executar manualmente antes de ativar cron.

O cron permanece desativado ate a validacao do Batch 1 e confirmacao explicita.
