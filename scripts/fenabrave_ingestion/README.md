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

Se `.\.venv\Scripts\Activate.ps1` nao for reconhecido, a pasta `.venv` provavelmente ainda nao existe ou o terminal nao esta em `scripts\fenabrave_ingestion`.

Rode novamente a partir da raiz do projeto:

```powershell
cd C:\social_media-analytics\scripts\fenabrave_ingestion

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Se `py -3 -m venv .venv` falhar:

```powershell
python -m venv .venv
```

Para conferir se a `.venv` foi criada:

```powershell
Get-ChildItem .venv\Scripts
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
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

O periodo `2026-04-01` sera inferido automaticamente a partir do nome do arquivo `2026_04_02.pdf`.

Alternativa usando o helper PowerShell:

```powershell
.\run_fenabrave_phase1.ps1 `
  -Path "fenabrave/2026/04/2026_04_02.pdf" `
  -SourceUrl "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

O script deve imprimir:

- metadados do PDF baixado do Storage
- linhas extraidas da primeira tabela da pagina 1
- valores normalizados por segmento, usando apenas a coluna `mes_atual`
- checks locais de soma
- item 1 da fase 2, com ranking mensal da pagina 6 para automoveis e comerciais leves
- checks locais do item 1

O parser seleciona para `mes_atual` o primeiro volume inteiro nao negativo da linha. Ele procura primeiro nas celulas depois do rotulo e, se encontrar apenas percentuais negativos, faz fallback para a linha inteira. Isso evita confundir a coluna mensal com percentuais como `-9,23`, quando o PDF extrai as celulas fora da ordem visual.

Se `subtotal_plus_outros` aparecer com `expected=None`, significa que a linha `Total` nao foi extraida/identificada. Nesse caso o script mostra a soma calculada, por exemplo `479662`, e marca a validacao como `warning`, nao como falha bloqueante. Os checks de `Autos + Comerciais Leves` e `Caminhoes + Onibus` continuam sendo erros bloqueantes quando falham.

Nesta fase, os resultados de validacao ficam no terminal e no status do arquivo em `market_source_files`. O script nao tenta gravar `market_ingestion_validation_results`, porque essa tabela ainda nao faz parte da estrutura minima.

## Gravar no banco

Quando a tabela normalizada existir no Supabase e o dry-run estiver correto:

```powershell
python ingest_fenabrave_phase1.py --write `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

Por padrao, `--write` abre o PDF temporario e mostra uma caixa de dialogo:

```text
OK  = grava os dados e conclui o processo
NOK = nao grava normalizado e retorna erro no terminal
```

Se a abertura automatica do PDF nao for permitida, o script continua com a caixa de dialogo. Se a interface grafica nao estiver disponivel, a confirmacao cai para o terminal com `ok` ou `nok`.

Para reprocessar o mesmo arquivo e substituir dados ja carregados:

```powershell
python ingest_fenabrave_phase1.py --write --replace `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

## Parametros mensais

```text
--path
--source-url
```

Esses parametros mudam a cada mes. O `.env` nao deve ser editado para trocar o arquivo processado.

`--reference-period` existe como opcional apenas para excecoes. No fluxo normal, o script infere o mes pelo nome do arquivo no path:

```text
fenabrave/2026/04/2026_04_02.pdf -> 2026-04-01
```

O script carrega apenas a coluna `mes_atual`. Acumulados mensais ou anuais devem ser gerados depois por view SQL.

O item 1 da fase 2 faz parte da inclusao mensal padrao: quando o script roda sem opcao de contingencia, ele tambem extrai a pagina 6 e prepara/grava `market_vehicle_model_rankings` com o ranking mensal de automoveis e comerciais leves. Para contingencia operacional, use `--skip-phase2-item1` e registre a pendencia do item no controle mensal.

## Opcoes de revisao

Rodar gravacao sem tentar abrir o PDF, mas ainda perguntando OK/NOK:

```powershell
python ingest_fenabrave_phase1.py --write --no-open-pdf `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

Pular a revisao interativa:

```powershell
python ingest_fenabrave_phase1.py --write --no-review `
  --path "fenabrave/2026/04/2026_04_02.pdf" `
  --source-url "https://www.fenabrave.org.br/portal/files/2026_04_02.pdf"
```

Usar `--no-review` apenas em automacao confiavel ou quando a revisao ja tiver sido feita em uma execucao anterior.
