# Fenabrave ingestion - phase 1

Script local para extrair a primeira tabela da pagina 1 de um PDF da Fenabrave ja salvo no Supabase Storage.

Nesta fase, o upload do PDF e o registro inicial em `market_source_files` podem ser manuais. O script atua depois disso: baixa o PDF do Storage, extrai a tabela, normaliza os valores e valida os totais.

## Setup

```powershell
cd scripts\fenabrave_ingestion
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` com as credenciais do Supabase e o caminho do PDF no bucket privado.

Nunca versionar `.env` nem expor `SUPABASE_SERVICE_ROLE_KEY` no Streamlit ou frontend.

## Dry run

Use primeiro sem gravar no banco:

```powershell
python ingest_fenabrave_phase1.py --dry-run
```

O script deve imprimir:

- metadados do PDF baixado do Storage
- linhas extraidas da primeira tabela da pagina 1
- valores normalizados por segmento
- checks locais de soma

## Gravar no banco

Quando as tabelas raw e normalizada existirem no Supabase:

```powershell
python ingest_fenabrave_phase1.py --write
```

Para reprocessar o mesmo arquivo e substituir dados ja carregados:

```powershell
python ingest_fenabrave_phase1.py --write --replace
```

## Variaveis

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
FENABRAVE_STORAGE_BUCKET
FENABRAVE_STORAGE_PATH
FENABRAVE_REFERENCE_PERIOD
FENABRAVE_SOURCE_URL
FENABRAVE_SOURCE_NAME
```
