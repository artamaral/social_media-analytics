# Video Classification GPT V2

Script minimo para classificar videos com GPT usando a Taxonomia Video V2.

## Escopo

- busca videos em `public.posts`
- usa Taxonomia V2 carregada no Supabase
- chama `gpt-5-nano` para `title_metadata`
- baixa e corta os primeiros `90s` de audio com `yt-dlp` e `imageio-ffmpeg`
- transcreve localmente com `faster-whisper small`, CPU e `int8`
- reprocessa automaticamente o mesmo audio com `faster-whisper medium` quando a
  qualidade, especificidade ou extracao de entidades/contexto indicar risco
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
- remove contexto tecnico generico sem valor analitico antes de gravar, como
  `market`, `motor/motor` e `powertrain/motor`
- promove `topic_path` generico ou `sem_match_taxonomico` para rota V2
  especifica quando titulo/transcript sustentam claramente autonomia,
  lancamento ou reparo de motor
- bloqueia falsos positivos de veiculo por palavras comuns e deduplica
  entidades canonicas mantendo `model_year` antes de `model`
- usa `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md` como skill
  padrao, incluindo a regra documentada de `confidence_score`

Fora de escopo nesta versao:

- cron
- ingestao de videos
- transcricao por API
- ingestao persistente de descricao do YouTube
- dashboard

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

A versao esperada apos o reforco conservador de curadoria e:

```text
classify_videos_gpt_v2.py 2026-08-03-r39-validation-repair
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

Teste manual recomendado na VPS:

```bash
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
  --yt-dlp-extractor-args "youtube:player-client=android_vr" \
  --transcripts-output tmp/transcripts_po_token_test.csv \
  --dry-run
```

O script apenas repassa `--plugin-dirs`, `--extractor-args` e `--proxy` ao
`yt-dlp`. Plugins, PO Tokens, cookies e configuracoes locais ficam fora do Git.
`mweb + bgutil` nao e mais o default operacional: em 2026-07-31, o provider
retornou `HTTP 500` em `POST /get_pot` e fez o `yt-dlp` ficar preso ate
timeout. Use `android_vr` como default na VPS.
Quando `--yt-dlp-cookies` e usado, o script copia o arquivo para um cookies
temporario em `audio-workdir`, usa essa copia no `yt-dlp` e apaga a copia ao
final. Isso evita que o `yt-dlp` tente regravar o arquivo original da VPS ao
encerrar e tambem evita depender de flags que variam por versao do `yt-dlp`.

O caminho operacional padrao usa `stable audio first`: baixa a fonte de
audio/video sem conversao pelo `yt-dlp`, preferindo audio leve `139/140` antes
do progressivo `18`, e corta/converte os primeiros `90s` com o `ffmpeg` do
`imageio-ffmpeg` em uma etapa separada. A conversao direta antiga do `yt-dlp`
fica apenas como recuperacao se esse caminho estavel falhar.
Timeout de download tambem e tratado como falha recuperavel para permitir a
tentativa direta de recuperacao.

Fallback automatico para `medium`:

- no `--stage transcript_90s` sem `--transcripts-csv`, o default e transcrever
  primeiro com `small` e acionar `medium` uma unica vez quando houver risco
  objetivo
- gatilhos: `transcript_quality_score < 0.70`, `quality_status=poor|empty`,
  `topic_path` ainda generico, `vehicle_entities[]` com `needs_review` /
  `not_found`, `technical_contexts[]` com `needs_review` ou termo tecnico
  estrategico sem contexto preenchido
- o audio baixado/cortado e reaproveitado; o fallback nao baixa o video de novo
- somente a classificacao final e gravada no Supabase; a tentativa inicial fica
  registrada de forma sanitizada em `input_payload.video.transcription_metadata`
- `--fallback-whisper-model medium`, `--fallback-quality-threshold 0.70` e
  `--disable-medium-fallback` controlam o comportamento
- quando `--transcripts-output` for usado, o CSV registra uma linha por
  tentativa, diferenciando `whisper_model`
- se o `medium` falhar, o script preserva a classificacao valida do `small`,
  marca `needs_human_review=true` e registra `fallback_error`

Diagnostico de tempo:

- use `--timing` para imprimir duracao por etapa sem alterar o fluxo de
  classificacao
- etapas medidas incluem download estavel, recuperacao direta, Whisper, chamada OpenAI,
  validacao, enriquecimento de veiculo e escrita no Supabase
- para medir um unico video completo, rode com `--post-id <id>` e
  `--include-already-classified`
- o intervalo padrao entre videos e `--sleep-seconds 60.0`, porque a VPS nao
  precisa priorizar velocidade e reprocessamento custa mais que uma pausa maior

O transcript completo pode ser preservado no CSV temporario, mas nao e gravado
no Supabase. O `input_payload` persistido contem apenas hash, tamanho, duracao e
proveniencia da transcricao. Quando houver fallback automatico, o payload
sanitizado tambem registra motivo, modelo inicial, modelo final e qualidade
inicial, sem gravar o texto completo.

Entidades de veiculo:

- o GPT devolve apenas `vehicle_brand_raw`, `vehicle_model_raw`,
  `vehicle_year`, `vehicle_generation` e evidencia textual
- o script tambem extrai veiculos diretamente de `title`, `description` e
  `transcript_90s`, sem enviar o catalogo Carros na Web ao GPT
- a entidade canonica de mercado para veiculo para no maximo em
  fabricante/modelo/ano; versao ou acabamento como `XR`, `GS`, `SE`, `LTZ` ou
  similares fica apenas na evidencia textual
- exemplos: `Yaris Cross XR` -> `Yaris Cross`, `Dolphin SE` -> `Dolphin`,
  `Dolphin Mini GS` -> `Dolphin Mini`
- para consumo analitico, usar os campos canonicos vindos do Carros na Web:
  `canonical_manufacturer_name`, `canonical_model_name` e
  `canonical_model_year`; os campos `*_raw` ficam para auditoria
- se houver match em nivel de modelo sem ano, `canonical_model_year` permanece
  nulo; o script nao escolhe ano artificialmente
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

Reparos conservadores antes da gravacao:

- `topic_path` e `topic_path_secondary` com typo mecanico so sao corrigidos
  quando existe exatamente um codigo canonico compativel na Taxonomia V2
- exemplo aceito: `mercado_procuto__lancamentos` ->
  `mercado_produto__lancamentos`
- `vehicle_entities[].entity_order` e reordenado pelo harness para evitar falha
  por indice `0` ou negativo retornado pelo modelo
- `confidence_score` e `transcript_quality.quality_score` em escala percentual
  (`85`, `92`) ou com `%` sao convertidos para escala `0..1`; valores acima
  da escala esperada sao limitados a `1.0` para evitar falha operacional por
  formato de score
- `tracao_dianteira`, `tracao_traseira` e `tracao_integral` sao atributos de
  contexto tecnico, nao `topic_path`; se o GPT devolver essas rotas sob
  `powertrain`, o script repara para `review_teste__review_veiculo` quando a
  rota existir
- contexto tecnico e enxugado antes da validacao: sensores preservam o nome do
  sensor e removem `limpeza` como problema, autonomia vira atributo,
  pleonasmos como `sistema_hibrido`/`manual_cambio` sao removidos, e detalhes
  como carbonizacao/borra/geometria ficam apenas em evidencia textual

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
