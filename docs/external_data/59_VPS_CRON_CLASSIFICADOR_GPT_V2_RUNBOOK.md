# Runbook VPS - Classificador GPT Taxonomia V2 via Cron

## Objetivo

Registrar as decisoes operacionais para executar o futuro classificador GPT da
Taxonomia Video V2 em uma VPS Hostinger via `cron`.

Esta entrega documenta ambiente e modo de deploy. Ela ainda nao implementa o
script de classificacao.

## Decisoes registradas

- a execucao operacional sera feita em uma VPS Hostinger
- o acesso de desenvolvimento sera feito pelo VS Code com Remote SSH
- o servidor esta em Ubuntu 24.04 LTS
- o agendamento sera feito por `cron`
- o diretorio base no servidor sera:

```text
/opt/social-media-analytics
```

- nao clonar o repositorio completo na VPS nesta fase
- subir apenas o script e arquivos auxiliares estritamente necessarios para
  executar o classificador
- manter credenciais, tokens, chaves e variaveis de ambiente fora do Git
- registrar logs em arquivo local no servidor para auditoria simples
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
- manter a VPS focada em executar uma rotina agendada

Quando a rotina amadurecer, a decisao pode ser reaberta para:

- clonar o repo completo
- usar deploy por GitHub Actions
- empacotar com Docker
- migrar para Google Cloud

## Acesso via VS Code

O acesso deve usar `Remote - SSH` no VS Code.

Configuracao local esperada no arquivo SSH do usuario:

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
```

Uso esperado:

- `bin/`: script executavel do classificador
- `config/`: arquivos `.env` ou configuracoes locais nao versionadas
- `logs/`: logs do cron e execucoes
- `tmp/`: arquivos temporarios de audio/transcricao quando necessario

## Variaveis e segredos

Segredos devem ficar apenas no servidor, fora do Git.

Exemplos:

```text
OPENAI_API_KEY
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
CLASSIFIER_MODEL_TITLE=gpt-5-nano
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
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

## Cron

O agendamento final ainda sera definido depois da implementacao do script.

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

O script futuro deve seguir os contratos:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_OUTPUT_SCHEMA_V2.json`
- `sql/ddl/tables/022_create_video_taxonomy_classification.sql`
- `sql/ddl/views/023_create_v_video_classification_latest.sql`
- `sql/ddl/tests/011_test_video_taxonomy_classification.sql`

Modelos definidos:

- classificacao por titulo/metadados: `gpt-5-nano`
- transcricao dos `90s`: `gpt-4o-mini-transcribe`
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
- confirmar que falhas ficam registradas sem interromper proximas execucoes

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

Desenvolver o script minimo de classificacao para ser copiado para
`/opt/social-media-analytics/bin/` e executado manualmente antes de ativar o
cron.
