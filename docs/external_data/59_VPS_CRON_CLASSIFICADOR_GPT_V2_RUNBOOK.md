# Runbook VPS - Classificador GPT Taxonomia V2

## Objetivo

Registrar as decisoes operacionais para validar manualmente o classificador GPT
da Taxonomia Video V2 em uma VPS Hostinger.

O script esta implementado. O cron continua apenas como possibilidade futura e
nao deve ser configurado antes da aprovacao do Batch 1.

## Decisoes registradas

- a execucao operacional sera feita em uma VPS Hostinger
- o acesso de desenvolvimento sera feito pelo VS Code com Remote SSH
- o servidor esta em Ubuntu 24.04 LTS
- eventual agendamento podera ser feito por `cron` depois da validacao manual
- o diretorio base no servidor sera:

```text
/opt/social-media-analytics
```

- nao clonar o repositorio completo na VPS nesta fase
- subir apenas o script e arquivos auxiliares estritamente necessarios para
  executar o classificador
- manter credenciais, tokens, chaves e variaveis de ambiente fora do Git
- registrar logs das execucoes manuais em arquivo local para auditoria simples
- manter a implementacao pequena e operacional antes de evoluir para worker,
  container ou Google Cloud

## Por que nao clonar o repo completo agora

A etapa atual ainda e de validacao do classificador e do contrato de banco.
Clonar o repositorio completo na VPS aumentaria superficie operacional sem
necessidade imediata.

O deploy minimo permite:

- testar o classificador com menor friccao
- isolar dependencias de runtime
- reduzir risco de expor arquivos de desenvolvimento ou dados locais
- manter a VPS focada em executar uma rotina controlada

Quando a rotina amadurecer, a decisao pode ser reaberta para:

- clonar o repo completo
- usar deploy por GitHub Actions
- empacotar com Docker
- migrar para Google Cloud

## Acesso via VS Code

O acesso deve usar `Remote - SSH` no VS Code.

Configuracao local esperada no arquivo SSH do usuario, sem versionar o arquivo:

```sshconfig
Host hostinger-vps
  HostName <ip_ou_hostname_da_vps>
  User <usuario_ssh>
  Port 22
  IdentityFile <caminho_da_chave_privada_quando_usada>
  IdentitiesOnly yes
```

Regras:

- nao versionar IP publico, usuario real, senha ou chave privada
- preferir chave SSH a senha
- manter `known_hosts` local fora do repositorio
- usar o alias local `hostinger-vps` nos comandos operacionais, para evitar
  repetir IP, usuario e caminho da chave em chat, shell history e docs

Comandos locais de conexao:

```powershell
ssh hostinger-vps
```

Se precisar diagnosticar conexao:

```powershell
ssh -vvv hostinger-vps
```

Para copiar a versao atual do classificador:

```powershell
scp C:\social_media-analytics\scripts\video_classification\classify_videos_gpt_v2.py hostinger-vps:/opt/social-media-analytics/bin/classify_videos_gpt_v2.py
```

Para copiar o arquivo de cookies operacional quando existir:

```powershell
scp C:\social_media-analytics\tmp\youtube_cookies_from_paste.txt hostinger-vps:/opt/social-media-analytics/config/youtube_cookies.txt
```

O arquivo de cookies e segredo operacional. Ele deve ficar apenas em
`/opt/social-media-analytics/config/youtube_cookies.txt` na VPS, com permissao
restrita, e nao deve ser enviado para Git.

## Estrutura prevista no servidor

Diretorio base:

```bash
/opt/social-media-analytics
```

Estrutura recomendada:

```text
/opt/social-media-analytics/
  bin/
  config/
  logs/
  tmp/
  scripts/
    video_classification/
```

Uso esperado:

- `bin/`: script executavel do classificador
- `config/`: arquivos `.env` ou configuracoes locais nao versionadas
- `logs/`: logs do cron e execucoes
- `tmp/`: arquivos temporarios de audio/transcricao quando necessario
- `scripts/video_classification/`: arquivos auxiliares versionados, como
  `requirements.txt`

Script inicial:

```text
scripts/video_classification/classify_videos_gpt_v2.py
scripts/video_classification/requirements.txt
```

Destino recomendado na VPS:

```text
/opt/social-media-analytics/bin/classify_videos_gpt_v2.py
/opt/social-media-analytics/scripts/video_classification/requirements.txt
```

Criacao da estrutura minima na VPS:

```bash
mkdir -p /opt/social-media-analytics/bin
mkdir -p /opt/social-media-analytics/config
mkdir -p /opt/social-media-analytics/logs
mkdir -p /opt/social-media-analytics/tmp
mkdir -p /opt/social-media-analytics/scripts/video_classification
chmod 700 /opt/social-media-analytics/config
```

## Preparacao do Supabase

Antes de executar o script na VPS, a estrutura de banco e a Taxonomia V2 devem
estar aplicadas no Supabase.

Aplicar nesta ordem pelo Supabase SQL Editor ou pela rotina operacional
equivalente:

1. `sql/ddl/tables/022_create_video_taxonomy_classification.sql`
2. `sql/ddl/tables/023_add_transcript_quality_to_video_classification.sql`
3. `sql/dml/seed_video_taxonomy_v2.sql`
4. `sql/ddl/views/023_create_v_video_classification_latest.sql`
5. `sql/ddl/tests/011_test_video_taxonomy_classification.sql`

O seed `sql/dml/seed_video_taxonomy_v2.sql` e uma carga estatica versionada,
nao um metodo de ingestao recorrente.

Resultado esperado apos o seed:

```text
topic_paths = 104
compatibility_rules = 91
controlled_terms = 59
```

## Variaveis e segredos

Segredos devem ficar apenas no servidor, fora do Git.

Exemplos:

```text
OPENAI_API_KEY
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
CLASSIFIER_MODEL_TITLE=gpt-5-nano
CLASSIFIER_MODEL_TRANSCRIPT=gpt-5-nano
```

Regras:

- nao colocar `.env` no repositorio
- nao enviar segredos em chat ou documentacao
- usar permissao restrita para arquivos de configuracao no servidor

Exemplo no servidor:

```bash
chmod 600 /opt/social-media-analytics/config/*.env
```

## Execucao manual inicial

Antes do cron, rodar manualmente em lote pequeno:

```bash
cd /opt/social-media-analytics
source .venv/bin/activate
python3 bin/classify_videos_gpt_v2.py --version
python3 bin/classify_videos_gpt_v2.py --stage title_metadata --limit 1 --dry-run
```

Se a versao exibida nao for `2026-07-24-r8-yt-dlp-cookies`, a VPS ainda esta
com uma copia antiga do script. Copiar novamente o arquivo versionado para
`/opt/social-media-analytics/bin/classify_videos_gpt_v2.py`.

Tambem sao validos os aliases `--script-version` e `-V`. Se nenhum desses
argumentos existir, a copia ainda esta baseada no commit remoto antigo
`a38495f`, anterior ao commit que adicionou o marcador de versao.

A execucao deve imprimir `skill_source` apontando para
`docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md` quando rodada a partir
do repositorio completo. Essa skill contem a regra oficial de confianca:

- `0.90` a `1.00`: evidencia direta, clara e especifica
- `0.70` a `0.89`: evidencia boa, mas com alguma ambiguidade
- `0.50` a `0.69`: evidencia parcial ou titulo pouco especifico
- abaixo de `0.50`: evidencia insuficiente e `needs_human_review=true`

A versao `r6-sem-match-guardrail` adiciona uma trava contra inferencia ruim:

- `fora_escopo` deve ser usado quando o input indicar moto, nao-automotivo,
  transito/comportamento ou entretenimento sem tema automotivo principal
- `sem_match_taxonomico` deve ser usado quando o input parece automotivo, mas
  nao sustenta nenhum `topic_path` especifico
- `sem_match_taxonomico` sempre exige `confidence_score < 0.50`,
  `needs_human_review=true`, `validation_issues` e nenhum contexto tecnico

O script usa `6000` como limite padrao de saida. Se uma chamada retornar
`incomplete/max_output_tokens`, reprocessar o mesmo video com limite maior:

```bash
python3 bin/classify_videos_gpt_v2.py --stage title_metadata --post-id Z8hPL7MGOxU --max-output-tokens 9000 --dry-run
```

Se a execucao falhar com `technical_context sem compatibilidade e sem
needs_review`, atualizar a VPS para a versao `2026-07-24-r3-context-review`.
Essa versao preserva a trava de compatibilidade, mas converte combinacoes
tecnicas fora da matriz V2 para `needs_review`, impedindo que o lote falhe por
um contexto generico como `motor` ou `off_road` sem componente/problema.

Depois de validar a resposta e o contrato de banco:

```bash
python3 bin/classify_videos_gpt_v2.py --stage title_metadata --limit 1 --write
```

Instalar as dependencias versionadas antes da primeira transcricao:

```bash
python3 -m pip install -r /opt/social-media-analytics/scripts/video_classification/requirements.txt
```

Sem `--transcripts-csv`, `transcript_90s` baixa o audio, limita o trecho aos
primeiros `90s` e transcreve localmente com `faster-whisper small`, CPU e
`compute_type=int8`. O modelo e carregado uma vez por execucao.

## Decisao operacional: chamada combinada

Quando a transcricao dos `90s` estiver disponivel, a rotina operacional deve
executar uma unica classificacao com:

```bash
python3 bin/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id <post_id> \
  --transcripts-output /opt/social-media-analytics/tmp/transcripts_validacao.csv \
  --dry-run
```

Se o `yt-dlp` retornar `Sign in to confirm you're not a bot`, usar cookies
exportados do navegador em arquivo local fora do Git:

```bash
python3 bin/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id <post_id> \
  --yt-dlp-cookies /opt/social-media-analytics/config/youtube_cookies.txt \
  --yt-dlp-user-agent "<user_agent_do_navegador>" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --transcripts-output /opt/social-media-analytics/tmp/transcripts_validacao.csv \
  --dry-run
```

O arquivo `/opt/social-media-analytics/config/youtube_cookies.txt` e secreto
operacional. Ele nao deve ser commitado nem copiado para `docs/`, `tmp/` ou
logs.

Quando os cookies forem extraidos de uma chamada `requests` do navegador, usar
tambem o `user-agent` da mesma chamada. Sem isso, a sessao pode funcionar na
maquina local e ainda assim ser recusada na VPS por diferenca de ambiente.

Se mesmo com cookies e headers o YouTube continuar exigindo validacao de bot,
o proximo teste manual controlado e usar PO Token Provider plugin do `yt-dlp`.
O script aceita as flags genericas:

```bash
--yt-dlp-plugin-dir /opt/social-media-analytics/config/yt_dlp_plugins
--yt-dlp-extractor-args "youtube:player-client=default,mweb"
```

Primeira tentativa recomendada:

```bash
cd /opt/social-media-analytics
source .venv/bin/activate
python -m pip install -U yt-dlp bgutil-ytdlp-pot-provider
```

Se Docker estiver disponivel, subir o provider HTTP local:

```bash
docker run --name bgutil-provider -d -p 127.0.0.1:4416:4416 --init brainicism/bgutil-ytdlp-pot-provider
```

Se o IP da VPS continuar bloqueado, nao usar `warp-cli connect` global no host.
O teste validado e isolar WARP em container e expor apenas um SOCKS5 local para
o `yt-dlp`:

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

O resultado esperado do trace e `warp=on`. O `warp-cli` global ja causou perda
de DNS/rota na VPS e deve permanecer desligado.

Exemplo:

```bash
UA="$(cat /opt/social-media-analytics/config/youtube_user_agent.txt)"

python3 bin/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id <post_id> \
  --yt-dlp-cookies /opt/social-media-analytics/config/youtube_cookies.txt \
  --yt-dlp-user-agent "$UA" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --yt-dlp-proxy "socks5://127.0.0.1:11080" \
  --yt-dlp-extractor-args "youtube:player-client=default,mweb" \
  --yt-dlp-extractor-args "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416" \
  --transcripts-output /opt/social-media-analytics/tmp/transcripts_po_token_test.csv \
  --dry-run
```

Tokens, cookies e diretorios de plugin em `config/` sao segredo/configuracao
operacional da VPS e nao devem ser versionados.

Usar `--yt-dlp-plugin-dir` apenas se o plugin for instalado manualmente fora do
venv.

Esse estagio deve receber titulo, metadados e transcricao no mesmo input. A
execucao por `title_metadata` fica reservada para diagnostico, calibracao,
comparacao de custo/qualidade ou triagem preliminar, nao para resultado final
quando o transcript ja existir.

O transcript usado nessa rotina vem de `faster-whisper` local. Um CSV existente
pode ser passado com `--transcripts-csv` para replay e comparacao.

Se a aquisicao direta falhar com `ffmpeg exited with code -11`, a versao
`2026-07-30-r17-audio-first-fallback` tenta automaticamente um caminho mais
estavel: baixar a fonte sem conversao pelo `yt-dlp`, preferindo audio leve
`139/140` antes do progressivo `18`, e cortar/converter com o `ffmpeg` do
`imageio-ffmpeg` fora do `yt-dlp`.

O transcript completo nao e gravado no Supabase. O banco recebe a avaliacao de
qualidade, evidencias curtas e metadados sanitizados da transcricao.

A chamada combinada aumenta o custo em relacao ao titulo puro porque adiciona
tokens de entrada da transcricao, mas evita duplicar prompt, taxonomia, matriz
de compatibilidade e JSON de saida em duas chamadas completas.

## Cron suspenso

O agendamento permanece suspenso ate a validacao manual do Batch 1 e confirmacao
explicita do classificador.

Formato esperado:

```cron
# Exemplo futuro, ainda nao ativar sem script validado
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# roda o classificador em janela controlada
# 15 * * * * /opt/social-media-analytics/bin/run_classifier.sh >> /opt/social-media-analytics/logs/classifier.log 2>&1
```

Regras:

- cron deve rodar com lote pequeno no inicio
- logs devem ir para `/opt/social-media-analytics/logs/`
- erros devem ser preservados no log
- nao rodar em alta concorrencia
- nao competir agressivamente com outros fluxos OpenAI

## Relacao com Taxonomia V2

O script inicial deve seguir os contratos:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_OUTPUT_SCHEMA_V2.json`
- `sql/ddl/tables/022_create_video_taxonomy_classification.sql`
- `sql/ddl/views/023_create_v_video_classification_latest.sql`
- `sql/ddl/tests/011_test_video_taxonomy_classification.sql`

Modelos definidos:

- classificacao por titulo/metadados: `gpt-5-nano`
- transcricao operacional dos `90s`: `faster-whisper small`, CPU e `int8`
- classificacao por transcricao: `gpt-5-nano`
- sem fallback automatico para `gpt-5.4-mini`

## Validacao antes de ativar cron

Antes de ativar o agendamento:

- confirmar que a VPS acessa Supabase e OpenAI
- validar que o script roda manualmente em lote pequeno
- confirmar que logs sao gravados
- confirmar que nenhuma credencial aparece no log
- confirmar que a resposta GPT valida contra schema JSON
- confirmar que inserts no Supabase respeitam as constraints
- confirmar que `transcript_quality` e coerente com `confidence_score`
- confirmar que o transcript completo nao aparece em `input_payload`
- confirmar que falhas ficam registradas sem interromper proximas execucoes
- confirmar que a versao `2026-07-30-r18-topic-context-vehicle-guards` preserva
  `review_teste`/`mercado_produto` como tema principal quando `powertrain` e
  apenas atributo tecnico
- confirmar que o matcher nao cria entidades para `100%`, `bora para o canal`,
  `tipo SKD` ou `link na descricao`

## Fora de escopo

- clonar o repositorio completo na VPS
- deploy por CI/CD
- Docker
- Google Cloud
- dashboard
- worker persistente
- ingestao de novos videos
- scraping

## Proximo passo

Copiar o script minimo de classificacao para
`/opt/social-media-analytics/bin/` e executa-lo manualmente antes de ativar o
cron.

Status em 2026-07-24:

- script inicial criado em `scripts/video_classification/classify_videos_gpt_v2.py`

Status em 2026-07-30:

- versao `2026-07-30-r18-topic-context-vehicle-guards` preparada para nova
  rodada manual do Batch 1
- cron continua suspenso ate validacao explicita da classificacao reforcada
- seed estatico criado em `sql/dml/seed_video_taxonomy_v2.sql`
- cron continua desativado ate validacao manual na VPS
