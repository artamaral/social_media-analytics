# PO Token yt-dlp para transcricao na VPS

## Objetivo

Registrar a tentativa operacional controlada de usar PO Tokens com `yt-dlp` na
VPS para viabilizar a aquisicao de audio dos primeiros `90s` dos videos do
YouTube.

Esta decisao nao altera o contrato do classificador GPT. O classificador segue
recebendo texto em `transcript_90s`; o PO Token atua apenas na etapa anterior,
de obtencao do audio/transcricao.

## Contexto

O teste local com cookies conseguiu baixar/transcrever o video
`6UvttnM06xU`, mas a mesma sessao foi recusada na VPS com:

```text
Sign in to confirm you're not a bot
```

A leitura operacional e que o bloqueio esta ligado a reputacao/ambiente do IP
da VPS e aos mecanismos atuais de validacao do YouTube. A documentacao do
`yt-dlp` registra que o YouTube vem exigindo PO Tokens para algumas requisicoes
de video, GVS e subtitles, e que esses tokens precisam ser fornecidos
externamente ou por plugin.

## Decisao

- testar PO Token Provider plugin apenas em execucao manual na VPS;
- manter o cron suspenso ate validacao explicita;
- nao embutir token, cookie, proxy, conta Google ou segredo no Git;
- nao adotar Tor, proxy residencial ou conta descartavel como solucao padrao
  nesta fase;
- manter `--transcripts-csv` como fallback operacional validado para o
  classificador;
- documentar qualquer plugin instalado na VPS antes de transformar isso em
  rotina.

## Implementacao no script

O classificador passa a aceitar flags genericas para repassar configuracao ao
`yt-dlp`:

```bash
--yt-dlp-plugin-dir <path>
--yt-dlp-extractor-args "<args>"
```

Isso permite usar plugins de PO Token sem acoplar o projeto a um plugin
especifico.

## Plugin recomendado para o primeiro teste

Primeira tentativa na VPS: `bgutil-ytdlp-pot-provider`.

Motivo:

- e citado pelo guia de PO Token do `yt-dlp` como plugin de provider;
- pode operar com provider HTTP local, evitando depender de browser grafico na
  VPS;
- e mais adequado para servidor headless do que alternativas que precisam
  abrir Chrome/Chromium.

Instalacao Python no venv da VPS:

```bash
cd /opt/social-media-analytics
source .venv/bin/activate
python -m pip install -U yt-dlp bgutil-ytdlp-pot-provider
```

Se Docker estiver disponivel, subir provider HTTP local:

```bash
docker run --name bgutil-provider -d -p 127.0.0.1:4416:4416 --init brainicism/bgutil-ytdlp-pot-provider
```

Se Docker nao estiver disponivel, a alternativa e instalar Node.js e seguir a
instalacao nativa do provider. Essa alternativa deve ser documentada depois do
teste, para nao transformar a VPS em ambiente complexo prematuramente.

Exemplo com client `mweb`:

```bash
python bin/classify_videos_gpt_v2.py \
  --stage transcript_90s \
  --post-id 6UvttnM06xU \
  --max-output-tokens 9000 \
  --yt-dlp-cookies config/youtube_cookies.txt \
  --yt-dlp-user-agent "$(cat config/youtube_user_agent.txt)" \
  --yt-dlp-referer "https://www.youtube.com/" \
  --yt-dlp-extractor-args "youtube:player-client=default,mweb" \
  --yt-dlp-extractor-args "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416" \
  --transcripts-output tmp/transcripts_po_token_test.csv \
  --dry-run
```

Se for instalado um plugin manual fora do venv, usar tambem
`--yt-dlp-plugin-dir <path>`.

Quando o bloqueio vier da reputacao do IP da VPS, usar WARP apenas isolado em
container. O teste validado usa `warproxy` como SOCKS5 local:

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

O resultado esperado e `warp=on`. O classificador deve entao receber:

```bash
--yt-dlp-proxy "socks5://127.0.0.1:11080"
```

Nao usar `warp-cli connect` global no host, pois esse modo ja causou falha de
DNS/rota na VPS.

Se o `yt-dlp` passar pela barreira de bot mas falhar em conversao com
`ffmpeg exited with code -11`, o fallback do classificador deve preferir audio
leve `139/140` antes do progressivo `18`. O formato `139` foi validado no teste
manual com WARP/PO Token para `JGzj254Kgs4`.

## Validacao

Um teste manual com PO Token so sera considerado aprovado se:

- `yt-dlp` baixar o audio do video na VPS sem erro de bot/sign-in;
- se WARP for necessario, `curl` via proxy local deve retornar `warp=on`;
- `faster-whisper` gerar `transcript_90s`;
- o GPT classificar em `--dry-run` sem erro de schema;
- uma execucao `--write` gravar resultado, contexto tecnico e qualidade textual
  no Supabase;
- o arquivo de token/cookie nao aparecer no Git.

## Riscos

- PO Tokens sao dependentes de implementacao do YouTube e podem mudar sem
  aviso;
- alguns tokens podem ser ligados a sessao, visitor id, video id ou client;
- usar conta Google/cookies em automacao pode gerar risco operacional para a
  conta;
- IPs de datacenter podem continuar bloqueados mesmo com cookies;
- a solucao nao e equivalente a YouTube Data API oficial.

## Status

Status atual: `em_teste_manual`.

O classificador esta validado com CSV de transcript. A aquisicao automatica de
audio na VPS segue como gargalo separado ate que o teste com PO Token seja
concluido.
