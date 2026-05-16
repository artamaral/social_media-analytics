# Fenabrave ingestion - phase 1

Script local para extrair a primeira tabela da pagina 1 de um PDF da Fenabrave ja salvo no Supabase Storage.

Nesta fase, o upload do PDF e o registro inicial em `market_source_files` sao manuais. O script atua depois disso: le o PDF do Storage, extrai a tabela, normaliza os valores e valida os totais.

## Setup inicial

```powershell
cd scripts\fenabrave_ingestion
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` apenas com credenciais e configuracoes fixas:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
FENABRAVE_STORAGE_BUCKET
FENABRAVE_SOURCE_NAME
```

Nao coloque no `.env` os dados do arquivo mensal. O caminho do PDF, periodo de referencia e URL original devem ser informados no comando de execucao.

Nunca versionar `.env` nem expor `SUPABASE_SERVICE_ROLE_KEY` no Streamlit ou frontend.

## Execucao mensal

Executar apos o 5o dia util do mes, sempre para processar o mes anterior.

Exemplo para abril/2026:

```powershell
python ingest_fenabrave_phase1.py --dry-run `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --reference-period "2026-04-01" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

Alternativa usando o helper PowerShell:

```powershell
.\run_fenabrave_phase1.ps1 `
  -Path "fenabrave/2026/04/2026_04_02.pdf" `
  -ReferencePeriod "2026-04-01" `
  -SourceUrl "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

O script deve imprimir:

- metadados do PDF baixado do Storage
- linhas extraidas da primeira tabela da pagina 1
- valores normalizados por segmento
- checks locais de soma

## Gravar no banco

Quando as tabelas raw e normalizada existirem no Supabase e o dry-run estiver correto:

```powershell
python ingest_fenabrave_phase1.py --write `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --reference-period "2026-04-01" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

Para reprocessar o mesmo arquivo e substituir dados ja carregados:

```powershell
python ingest_fenabrave_phase1.py --write --replace `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --reference-period "2026-04-01" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

## Parametros mensais

```text
--path
--reference-period
--source-url
```

Esses parametros mudam a cada mes. O `.env` nao deve ser editado para trocar o arquivo processado.
