# Calendario operacional offline

Data: 2026-05-15

## Objetivo

Centralizar as atividades offline que precisam ser executadas manualmente ou semi-manualmente no projeto, indicando frequencia, responsavel, documentacao de referencia e comando principal.

Este calendario evita que tarefas importantes fiquem escondidas em scripts ou conversas.

## Regras gerais

- Toda atividade offline deve ter documentacao de execucao.
- Toda atividade que altera dados deve ter validacao antes de ser considerada concluida.
- Credenciais ficam em `.env` local ou secrets seguros, nunca no Git.
- Quando uma atividade deixar de ser necessaria, registrar o motivo na documentacao correspondente.

## Atividades mensais

### Fenabrave - extracao de emplacamentos

Frequencia:

- mensal
- executar apos o 5o dia util do mes
- sempre processar o mes anterior

Responsavel:

- Arthur para upload manual do PDF e confirmacao da fonte
- Codex/ChatGPT para apoio tecnico, revisao e manutencao do script

Documentacao:

- `sql/docs/23_FENABRAVE_PHASE1_INGESTION_SPEC.md`
- `scripts/fenabrave_ingestion/README.md`

Etapas:

1. Baixar o PDF mensal da Fenabrave.
2. Fazer upload manual no bucket privado `market-source-files`.
3. Registrar ou conferir o arquivo em `public.market_source_files`.
4. Rodar o script em `--dry-run`.
5. Revisar a extracao impressa no terminal.
6. Quando as tabelas raw e normalizada estiverem disponiveis, rodar em `--write`.
7. Na caixa de dialogo, conferir o PDF aberto e marcar `OK` ou `NOK`.
8. Conferir validacoes.

Comando PowerShell - setup inicial:

```powershell
cd scripts\fenabrave_ingestion
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Se `.\.venv\Scripts\Activate.ps1` nao for reconhecido, recriar a venv a partir da raiz do projeto:

```powershell
cd C:\social_media-analytics\scripts\fenabrave_ingestion
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Fallback se `py` nao estiver disponivel:

```powershell
python -m venv .venv
```

Comando PowerShell - dry-run mensal:

```powershell
cd scripts\fenabrave_ingestion
.\.venv\Scripts\Activate.ps1

python ingest_fenabrave_phase1.py --dry-run `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --reference-period "2026-04-01" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

Comando PowerShell - gravar no Supabase:

```powershell
cd scripts\fenabrave_ingestion
.\.venv\Scripts\Activate.ps1

python ingest_fenabrave_phase1.py --write `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --reference-period "2026-04-01" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

Comando PowerShell - reprocessar arquivo ja carregado:

```powershell
cd scripts\fenabrave_ingestion
.\.venv\Scripts\Activate.ps1

python ingest_fenabrave_phase1.py --write --replace `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --reference-period "2026-04-01" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

Resultado esperado:

- PDF preservado no Storage
- arquivo registrado em `market_source_files`
- tabela extraida revisada
- operador confirma `OK` antes da gravacao definitiva
- checks locais aprovados
- dados prontos para uso analitico apos carga definitiva

## Atividades sob demanda

### Backfill offline de posts legacy_low

Frequencia:

- sob demanda
- usar apenas quando houver necessidade operacional de recuperar historico de posts antigos

Responsavel:

- Arthur para decisao de execucao
- Codex/ChatGPT para revisao tecnica e troubleshooting

Documentacao:

- `sql/docs/17_LEGACY_LOW_OFFLINE_BACKFILL_SPEC.md`
- `sql/docs/18_LEGACY_LOW_OFFLINE_BACKFILL_PHASE1_SPEC.md`
- `sql/docs/19_LEGACY_LOW_OFFLINE_BACKFILL_SCRIPT_DESIGN.md`
- `sql/docs/20_LEGACY_LOW_BACKFILL_RESULTS_2026-05-14.md`
- `sql/docs/21_WINDOWS_SCHEDULER_BACKFILL_SETUP.md`

Script:

- `scripts/offline_backfill/legacy_low_backfill_phase1.py`
- `scripts/offline_backfill/run_legacy_low_backfill_phase1.ps1`

Comando PowerShell:

```powershell
cd scripts\offline_backfill
.\run_legacy_low_backfill_phase1.ps1
```

Resultado esperado:

- posts legados recebem snapshot historico inicial
- resultados devem ser validados conforme documentacao da fase

## Atividades futuras candidatas

Estas atividades ainda nao fazem parte do calendario recorrente:

- ingestao SENATRAN/RENAVAM
- automacao do download/upload da Fenabrave
- backfill historico grande de PDFs da Fenabrave
- criacao de rotina automatizada no Scheduler

Elas so devem entrar neste calendario quando houver script, runbook e criterio de validacao definidos.
