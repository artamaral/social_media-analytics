# Plano de ingestao Carros na Web - catalogo por CSV e fichas em on hold

Data: 2026-05-19

## Objetivo

Planejar a inclusao dos dados do Carros na Web no projeto como base estruturada
de catalogo automotivo a partir de CSVs recorrentes. Fichas tecnicas por
scraping ficam em `on_hold`.

## Status atual consolidado

- a fonte continua relevante como catalogo tecnico
- o usuario confirmou em 2026-07-15 que os CSVs de catalogo ja existem fora
  desta maquina
- esses CSVs devem ser baixados regularmente para detectar novas entradas
- os dados devem ser persistidos no Supabase e consumidos por uma view no
  Streamlit
- fichas tecnicas por scraping nao sao viaveis nesta etapa e ficam em
  `on_hold`
- diagnosticos antigos de ficha e parser exploratorio permanecem apenas como
  historico tecnico, nao como caminho operacional ativo

Esta fonte e importante porque complementa as bases de mercado com detalhes de
produto:

- fabricantes e modelos disponiveis no mercado brasileiro
- versoes por modelo
- ano, preco e configuracao
- motor, combustivel, cambio, torque e potencia
- dimensoes, peso, suspensao, freios, direcao, consumo e autonomia

O papel da fonte nao e substituir Fenabrave ou SENATRAN/RENAVAM. Para venda,
market share e demanda real, a verdade do projeto continua sendo emplacamento.
Carros na Web entra como base tecnica de produto para enriquecer analises de
conteudo, comparar modelos citados em videos e sustentar respostas tecnicas no
dashboard e no ChatGPT.

## Fonte

Fonte:

- Carros na Web

Dominio:

- `https://www.carrosnaweb.com.br`

Padrao de ficha tecnica:

```text
https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=<CODIGO>
```

Ficha piloto validada no estudo inicial:

```text
https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=44763
```

Veiculo da ficha piloto:

```text
Renault Kardian Evolution 1.0 AT 2026
```

## Decisao operacional principal

Usar CSVs recorrentes como fonte operacional.

O fluxo ativo da frente passa a ser:

```text
download recorrente dos CSVs
  -> armazenamento bruto/rastreavel
  -> validacao de schema, duplicidade e novas entradas
  -> persistencia no Supabase
  -> view analitica
  -> consumo no Streamlit
```

Motivo:

- os CSVs ja existem como artefatos de catalogo e nao dependem desta maquina
- baixar CSV regularmente e comparar versoes e mais repetivel do que tentar
  scrapear fichas tecnicas
- a necessidade analitica imediata e enxergar catalogo, cobertura e novas
  entradas no dashboard
- scraping de fichas tecnicas nao e viavel agora e nao deve travar a frente

Regra:

```text
Baixar CSVs recorrentes da fonte acordada
Persistir no banco com rastreabilidade
Criar view para Streamlit
Manter fichas tecnicas por scraping em on_hold
```

## Posicao na arquitetura do projeto

O fluxo segue o padrao do projeto:

```text
1. Ingestao
2. Armazenamento bruto
3. Processamento
4. Enriquecimento
5. Agregacao
6. Consumo
```

Aplicado ao Carros na Web:

```text
Download recorrente dos CSVs de catalogo
  -> armazenamento bruto/rastreavel
  -> validacao de schema e novas entradas
  -> persistencia no Supabase
  -> view analitica
  -> consumo por Streamlit e ChatGPT
```

Resumo operacional consolidado para a frente:

```text
CSVs de catalogo -> staging/rastreabilidade -> tabelas normalizadas -> view Streamlit
```

Observacao importante:

- fichas tecnicas por scraping ficam em `on_hold`
- qualquer codigo antigo de discovery/scraping deve ser tratado como
  diagnostico historico, nao como caminho ativo do sprint

## Escopo da fase 1

Objetivo da fase 1:

- definir origem e rotina de download dos CSVs existentes
- preservar cada CSV baixado com rastreabilidade de origem, data e hash/versao
- validar schema, duplicidades, campos obrigatorios e novas entradas
- persistir catalogo no Supabase
- criar view de consumo para Streamlit

Formato inicial:

- CSV recorrente baixado da fonte acordada
- staging local ou Storage para arquivo bruto
- Supabase para consumo analitico

Motivo para usar CSV:

- os arquivos ja existem fora desta maquina
- facilita comparacao de versoes e deteccao de novas entradas
- reduz risco operacional em relacao a scraping de ficha tecnica
- cria caminho direto para view no Streamlit

Pre-condicao real para executar esta fase:

- definir de onde os CSVs serao baixados e qual frequencia sera usada
- confirmar colunas reais e contrato minimo dos arquivos

Fora do escopo da fase 1:

- scraping de fichas tecnicas
- Playwright como caminho principal de coleta
- OCR obrigatorio
- captcha solving
- proxy rotation
- alta concorrencia
- parser de HTML de ficha

## Estrutura de pastas recomendada no repo

Como o repositorio ja organiza aquisicoes em `scripts/<fonte>`, a implementacao
deve adaptar a estrutura sugerida para ficar consistente com os codigos atuais.

Estrutura alvo para o fluxo ativo por CSV recorrente:

```text
scripts/carrosnaweb_ingestion/
  data/
    raw_csv/
      fabricantes.csv
      modelos.csv
      anos_modelo.csv
    staging/
      download_manifest.csv
      validation_status.csv
    processed/
      carrosnaweb_catalogo.csv
  src/
    downloader.py
    validator.py
    utils.py
  01_download_catalog_csvs.py
  02_validate_catalog_csvs.py
  03_prepare_catalog_load.py
  README.md
  requirements.txt
```

Estrutura historica de scraping de fichas:

- scripts e diagnosticos ligados a `fichas.csv`, HTML bruto e parser de ficha
  tecnica ficam como legado tecnico
- nao sao caminho ativo do Sprint 5
- nao devem ser usados para destravar a modelagem por CSV

O estudo inicial sugeria uma pasta raiz `carrosweb/`. Para este projeto, a
adaptacao para `scripts/carrosnaweb_ingestion/` evita criar uma ilha fora do
padrao atual e permite aproveitar a experiencia de `scripts/fenabrave_ingestion`
e `scripts/offline_backfill`.

## Codigo atual como base

A implementacao deve usar os codigos atuais como referencia operacional:

- `scripts/fenabrave_ingestion/README.md` para documentar setup, `.env` e modo
  de execucao
- `scripts/fenabrave_ingestion/ingest_fenabrave_phase1.py` como referencia de
  fluxo com `--dry-run`, validacao antes de escrita e mensagens operacionais
- `scripts/offline_backfill/legacy_low_backfill_phase1.py` como referencia de
  script local controlado, com limites e logs

Principios a reaproveitar:

- executar primeiro em modo limitado
- separar descoberta, coleta bruta, parser e carga
- manter artefatos intermediarios rastreaveis
- validar antes de considerar dado pronto para analise
- nao escrever em camada final sem revisao da qualidade

Estado atual de codigo versionado no repo:

- `scripts/carrosnaweb_ingestion/diagnostics/check_ficha_access.py` para
  diagnostico de acesso, classificacao de resposta, salvamento de HTML bruto e
  extracao exploratoria de tabela
- `scripts/carrosnaweb_ingestion/src/carrosnaweb_client.py` como cliente HTTP
  compartilhado com sessao aquecida
- `scripts/carrosnaweb_ingestion/02_discover_modelos.py` para a camada
  `fabricantes -> modelos`
- `scripts/carrosnaweb_ingestion/src/parser.py` para extrair a ficha tecnica a
  partir de `table/tr/td`
- `scripts/carrosnaweb_ingestion/07_parse_fichas.py` para converter HTML bruto
  em CSV estruturado

Leitura operacional:

- o codigo acima permanece como historico exploratorio
- a implementacao ativa deve criar a rotina de download/validacao/carga dos
  CSVs recorrentes
- fichas tecnicas seguem em `on_hold`

## Cliente HTTP

Arquivo alvo:

```text
scripts/carrosnaweb_ingestion/src/carrosnaweb_client.py
```

Responsabilidades:

- criar `requests.Session()`
- configurar headers de navegador
- aquecer sessao em `default.asp` e `avancada.asp`
- executar `GET` com delay aleatorio
- imprimir status HTTP, URL final e tamanho do HTML

Regras:

- usar sessao persistente
- usar headers completos
- aplicar delay aleatorio entre chamadas
- nao usar o cliente para burlar captcha
- visitar paginas publicas iniciais antes de requisitar paginas profundas
- registrar `status_code`, `final_url` e tamanho do HTML em toda chamada

Base tecnica preservada do estudo:

```text
BASE_URL = "https://www.carrosnaweb.com.br"
create_session()
warm_up_session(session)
safe_get(session, url, timeout=30, delay_min=1.5, delay_max=4.0)
```

## Classificacao obrigatoria de respostas

Antes de qualquer parser, o scraper deve classificar a resposta HTTP/HTML.

Status obrigatorios:

```text
success
http_error
site_error
validation_required
unexpected_page
parse_empty
exception
```

Regras de classificacao:

- `status_code != 200` deve virar `http_error`
- redirecionamento para `fichadetalheValida.asp` deve virar
  `validation_required`
- presenca de termos como `captcha`, `validacao` ou `preencha o campo com os
  caracteres` deve virar `validation_required`
- presenca de `Ocorreu um erro`, `internal server error` ou
  `500 - internal server error` deve virar `site_error`
- ausencia de texto esperado de ficha tecnica deve virar `unexpected_page`
- parser sem campos em uma pagina que nao e ficha deve virar erro de origem,
  nao erro de parser

Exemplo conceitual:

```python
def classify_response(response, html, page_text):
    final_url = response.url.lower()
    html_lower = html.lower()
    text_lower = page_text.lower()

    if response.status_code != 200:
        return "http_error", f"http_status_{response.status_code}"

    if "fichadetalhevalida.asp" in final_url:
        return "validation_required", "redirected_to_fichadetalhevalida"

    if any(term in html_lower or term in text_lower for term in [
        "preencha o campo com os caracteres",
        "captcha",
        "validacao",
    ]):
        return "validation_required", "captcha_or_validation_detected"

    if any(term in html_lower or term in text_lower for term in [
        "ocorreu um erro",
        "internal server error",
        "500 - internal server error",
    ]):
        return "site_error", "site_error_page"

    if "ficha tecnica" not in text_lower:
        return "unexpected_page", "missing_ficha_tecnica_text"

    return "success", None
```

## Step by step obrigatorio

O step by step do estudo inicial deve ser mantido nesta ordem.

### 1. Discovery de fabricantes

Script:

```text
scripts/carrosnaweb_ingestion/01_discover_fabricantes.py
```

Entrada:

```text
https://www.carrosnaweb.com.br/avancada.asp
```

Logica:

- abrir `avancada.asp`
- procurar todos os elementos `<select>`
- identificar select cujo `name` contenha `fabricante` ou `marca`
- extrair opcoes validas
- montar URL de catalogo por fabricante
- remover duplicados por URL

Saida:

```text
scripts/carrosnaweb_ingestion/data/discovery/fabricantes.csv
```

Colunas esperadas:

```text
fabricante
value
url
```

Resultado esperado no estudo inicial:

```text
aproximadamente 127 fabricantes
```

### 2. Salvar fabricantes.csv

O CSV deve ser salvo com:

```text
encoding="utf-8-sig"
index=False
```

O script deve imprimir:

- caminho salvo
- `df.head()`
- quantidade de fabricantes encontrados

### 3. Discovery de modelos por fabricante

Script:

```text
scripts/carrosnaweb_ingestion/02_discover_modelos.py
```

Entrada:

```text
scripts/carrosnaweb_ingestion/data/discovery/fabricantes.csv
```

Logica:

- ler fabricantes
- acessar cada URL de fabricante
- encontrar links contendo `catalogomodelo.asp?` ou `catalogo.asp?`
- extrair o nome do modelo via query string `modelo`, `varnome` ou texto do
  link
- capturar `codigo_modelo` quando existir na query string
- remover duplicados por URL

Saida:

```text
scripts/carrosnaweb_ingestion/data/discovery/modelos.csv
```

Colunas esperadas:

```text
fabricante
modelo
codigo_modelo
url_modelo
href_original
texto_link
params
```

### 4. Salvar modelos.csv

O CSV deve ser salvo com:

```text
encoding="utf-8-sig"
index=False
```

O script deve imprimir:

- fabricante atual
- URL acessada
- quantidade de modelos encontrados por fabricante
- total de modelos unicos
- preview do CSV

### 5. Discovery de anos por modelo

Script:

```text
scripts/carrosnaweb_ingestion/03_discover_anos.py
```

Entrada:

```text
scripts/carrosnaweb_ingestion/data/discovery/modelos.csv
```

Logica:

- ler modelos
- acessar cada `url_modelo`
- encontrar links de catalogo ou ficha que indiquem ano
- extrair ano de parametros como `ano`, `anomod`, `anoini`, `anofim`, do texto
  do link ou da URL
- remover duplicados por URL

Exemplo de URL esperada:

```text
https://www.carrosnaweb.com.br/catalogo.asp?fabricante=Audi&varnome=A3 Sedan&anoini=2023&anofim=2023
```

Saida:

```text
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv
```

Colunas esperadas:

```text
fabricante
modelo
ano
url_ano
url_modelo_origem
href_original
texto_link
params
```

### 6. Validar URLs de ano

Script:

```text
scripts/carrosnaweb_ingestion/04_validate_anos.py
```

Entrada:

```text
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv
```

Tarefa imediata:

- abrir cada `url_ano`
- registrar status HTTP
- registrar URL final
- registrar tamanho do HTML
- verificar se contem `fichadetalhe.asp`
- verificar se contem `Ocorreu um erro`
- salvar apenas paginas validas em `anos_modelo_validos.csv`

Saida:

```text
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo_validos.csv
```

Colunas esperadas:

```text
fabricante
modelo
ano
url_ano
http_status
final_url
html_size
has_ficha_links
has_error_text
status
reason
checked_at
```

Status sugeridos:

```text
valid_year_page
no_ficha_links
site_error
http_error
unexpected_page
```

Regra:

```text
Somente `valid_year_page` pode alimentar a descoberta de fichas.
```

### 7. Discovery de fichas por ano valido

Script:

```text
scripts/carrosnaweb_ingestion/05_discover_fichas.py
```

Entrada:

```text
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo_validos.csv
```

Logica:

- ler apenas paginas de ano validadas
- acessar cada `url_ano`
- encontrar links contendo `fichadetalhe.asp?codigo=`
- extrair `codigo_ficha` via query string
- usar o texto do link como `versao`, quando disponivel
- remover duplicados por URL

Regra critica:

```text
O script nao pode enumerar IDs.
Ele deve capturar somente links publicados nas paginas validas de catalogo/ano.
```

Saida:

```text
scripts/carrosnaweb_ingestion/data/discovery/fichas.csv
```

Colunas esperadas:

```text
fabricante
modelo
ano
versao
codigo_ficha
url_ficha
url_ano_origem
href_original
```

Saida opcional para teste limitado:

```text
scripts/carrosnaweb_ingestion/data/discovery/test_fichas_15.csv
```

### 8. Salvar fichas.csv

O CSV deve ser salvo com:

```text
encoding="utf-8-sig"
index=False
```

O script deve imprimir:

- modelo atual
- URL do modelo
- quantidade de fichas encontradas por modelo
- total de fichas unicas
- preview do CSV

### 9. Scraper de fichas apenas com URLs validas

Script:

```text
scripts/carrosnaweb_ingestion/06_scrape_fichas.py
```

Entrada:

```text
scripts/carrosnaweb_ingestion/data/discovery/fichas.csv
```

Parametros esperados:

```text
--max-items
--input-csv
--output-status-csv
```

Primeiro teste recomendado:

```text
max_items=10
```

Classificacao logica das respostas:

```text
success
http_error
site_error
validation_required
unexpected_page
parse_empty
exception
```

Regras:

- salvar HTML apenas quando `logical_status = success`
- parar a execucao quando detectar captcha
- registrar status de cada tentativa
- nao retentar agressivamente

Saidas:

```text
scripts/carrosnaweb_ingestion/data/raw_html/fichas/<codigo>.html
scripts/carrosnaweb_ingestion/data/discovery/fichas_scrape_status.csv
```

### 10. Parser de tabela HTML

Arquivo:

```text
scripts/carrosnaweb_ingestion/src/parser.py
```

Responsabilidades:

- limpar texto de celulas
- extrair titulo da pagina
- detectar grupos da ficha tecnica
- extrair pares `field` e `value`
- capturar URLs de imagens embutidas em celulas
- gerar registros em formato longo

Formato esperado por registro:

```text
fabricante
modelo
ano
versao
codigo_ficha
url_ficha
page_title
group
field
value
image_urls
collection_status
raw_html_path
```

Campos esperados nas fichas:

- Ano
- Preco
- Propulsao
- Combustivel
- Configuracao
- Plataforma
- Motor
- Aspiracao
- Cilindros
- Codigo do motor
- Torque
- Cambio
- Codigo do cambio
- Suspensao
- Freios
- Direcao
- Dimensoes
- Desempenho
- Consumo
- Autonomia

### 11. Salvar raw HTML

O HTML bruto deve ser preservado em:

```text
scripts/carrosnaweb_ingestion/data/raw_html/fichas/<codigo>.html
```

Encoding operacional sugerido:

```text
encoding="iso-8859-1"
errors="ignore"
```

Motivo:

- permite reprocessar parser sem chamar o site novamente
- reduz risco de bloqueio
- cria evidencia local para auditoria de parsing

### 12. Salvar dados estruturados

Script:

```text
scripts/carrosnaweb_ingestion/07_parse_fichas.py
```

Entrada:

```text
scripts/carrosnaweb_ingestion/data/raw_html/fichas/
```

Saida:

```text
scripts/carrosnaweb_ingestion/data/processed/ficha_tecnica.csv
```

O CSV deve consolidar todos os registros extraidos dos HTMLs brutos.

### 13. Rodar validacoes de qualidade

Validacoes iniciais:

```python
df = pd.read_csv("data/discovery/fabricantes.csv")
print(df.shape)
print(df.head())
print(df["fabricante"].nunique())
```

```python
df = pd.read_csv("data/discovery/modelos.csv")
print(df.shape)
print(df.head())
print(df["url_modelo"].duplicated().sum())
```

```python
df = pd.read_csv("data/discovery/anos_modelo.csv")
print(df.shape)
print(df.head())
print(df["url_ano"].duplicated().sum())
```

```python
df = pd.read_csv("data/discovery/anos_modelo_validos.csv")
print(df.shape)
print(df["status"].value_counts(dropna=False))
print(df["has_ficha_links"].value_counts(dropna=False))
```

```python
df = pd.read_csv("data/discovery/fichas.csv")
print(df.shape)
print(df.head())
print(df["codigo_ficha"].duplicated().sum())
```

```python
df = pd.read_csv("data/processed/ficha_tecnica.csv")
print(df.shape)
print(df.head())
print(df["group"].value_counts())
print(df[df["field"].str.contains("Codigo do motor", na=False)])
```

As validacoes devem ser documentadas depois em `03_DATA_QUALITY_CHECKS.md`
quando a fase 1 gerar os primeiros arquivos reais.

## Campos com valores em imagem

Alguns valores podem aparecer como imagem, por exemplo:

```html
<img src="..\campoImagem\imgValor1.asp"> cm<sup>3</sup>
<img src="..\campoImagem\imgValor4.asp"> cv
```

Campos possivelmente afetados:

- deslocamento
- potencia maxima
- peso
- comprimento

Regra da fase 1:

- nao bloquear MVP por OCR
- capturar `value` textual disponivel
- capturar `image_urls`
- registrar a necessidade de OCR como evolucao futura

Exemplo conceitual:

```python
{
    "field": "Potencia maxima",
    "value": "cv (A) 120 cv (G) a 5000 rpm",
    "image_urls": ["https://www.carrosnaweb.com.br/campoImagem/imgValor4.asp"]
}
```

## Prints de debug obrigatorios no MVP

Manter prints claros durante o MVP:

```python
print(f"[DEBUG] URL acessada: {url}")
print(f"[DEBUG] Status HTTP: {response.status_code}")
print(f"[DEBUG] Tamanho HTML: {len(response.text)}")
print(f"[DEBUG] URL final: {response.url}")
print(f"[DEBUG] Grupo detectado: {current_group}")
print(f"[DEBUG] Campo extraido: {field} = {value}")
print(f"[DEBUG] Imagens encontradas no campo: {image_urls}")
print(f"[ERROR] Erro ao processar codigo {codigo}: {exc}")
print(sys.executable)
print(sys.version)
```

Depois que a fase 1 estiver validada, avaliar troca de `print` por `logging`.

## Regras anti-bloqueio e etica operacional

Nao implementar:

```text
captcha solving
bypass de protecao
proxy rotation agressivo
enumeracao massiva de IDs
alta concorrencia
```

Implementar:

```text
delay aleatorio
sessao persistente
discovery por links reais
validacao de paginas de ano
limite de itens por execucao
status logging
parada ao detectar captcha
```

## Licoes aprendidas adicionais

### Ambiente de execucao

O scraper deve rodar em Python local real, terminal, PyCharm configurado
corretamente ou ambiente cloud real. Nao validar scraping HTTP em ambiente web
que transforme `requests` em `XMLHttpRequest`, porque isso pode produzir erro
de CORS/ambiente e confundir o diagnostico.

Sempre imprimir no topo dos scripts de diagnostico:

```python
import sys
print(sys.executable)
print(sys.version)
```

### Playwright

Playwright fica permitido apenas como diagnostico ou alternativa futura. Ele nao
deve ser a primeira solucao de coleta.

Aprendizados:

- Python 3.7 32-bit pode falhar com Playwright
- Python 3.12 64-bit foi validado para importar Playwright
- acessar ficha diretamente com Playwright tambem pode retornar erro 500
- Playwright nao substitui a necessidade de navegar pelo fluxo publico correto

Comando de diagnostico:

```powershell
python -c "from playwright.sync_api import sync_playwright; print('playwright ok')"
```

## Requirements sugerido

Dependencias iniciais:

```text
requests
beautifulsoup4
pandas
```

Dependencia opcional apenas para diagnostico:

```text
playwright
```

Instalacao opcional do navegador para diagnostico com Playwright:

```powershell
pip install playwright
playwright install chromium
```

Regra:

- `requests`, `BeautifulSoup` e `pandas` sao o caminho principal do MVP
- `playwright` nao deve virar dependencia obrigatoria enquanto a coleta por
  sessao HTTP e discovery publico ainda estiver sendo validada

## Proximo passo recomendado

Antes de implementar SQL ou Streamlit, fechar o contrato dos CSVs recorrentes:

Tarefa imediata:

```text
Definir rotina de CSV:
- origem/caminho de download
- frequencia de verificacao
- lista de arquivos esperados
- colunas obrigatorias por arquivo
- regra de hash/versao
- destino bruto
- tabelas normalizadas
- view inicial para Streamlit
```

Essa tarefa agora tambem esta refletida no roadmap do projeto.

## Parser validado no HTML

Status:

- legado tecnico / `on_hold`

O comportamento validado na ficha atual permanece como evidencia historica:

- os dados tecnicos estao dentro de estruturas `table` no HTML
- a extracao precisa percorrer `tr` e `td`
- uma mesma linha pode conter 2 colunas utilitarias ou 4 celulas no padrao
  `campo -> valor -> campo -> valor`
- grupos como `MOTOR`, `TRANSMISSAO` e semelhantes podem ser inferidos por
  linhas com texto unico em caixa alta

Direcao atual do parser:

- nao executar no Sprint 5
- nao bloquear a ingestao por CSV
- retomar apenas se surgir fonte viavel e repetivel sem scraping fragil

## Roadmap de implementacao

### Prioridade 1 - contrato dos CSVs

Definir:

```text
origem dos CSVs
frequencia de download
campos obrigatorios
chave natural de fabricante/modelo/ano
regra de hash/versao
criterio de nova entrada
```

### Prioridade 2 - banco

```text
tabela de arquivos fonte
tabelas de catalogo normalizadas
validacoes de carga
upsert incremental
```

### Prioridade 3 - Streamlit

```text
view analitica inicial
tela ou bloco de consulta no dashboard
indicadores de cobertura e novas entradas
```

### Prioridade 4 - fichas tecnicas

Status: `on_hold`.

Nao implementar scraping de ficha tecnica nesta etapa.

## Evolucao futura

Depois do MVP:

1. Trocar CSV por SQLite ou Postgres.
2. Criar tabela `carrosnaweb_fichas`.
3. Criar tabela `carrosnaweb_specs_long`.
4. Criar normalizacao de unidades.
5. Criar parser especifico para potencia, torque, cilindrada, peso, consumo e
   dimensoes.
6. Implementar OCR apenas para imagens `campoImagem`.
7. Trocar prints por `logging`.
8. Criar scheduler incremental.
9. Integrar com taxonomia de marcas/modelos usada por YouTube, Fenabrave e
   SENATRAN/RENAVAM.

## Uso analitico esperado

Perguntas que a base deve ajudar a responder:

- quais modelos aparecem mais nos videos e qual e a ficha tecnica deles?
- creators falam mais de SUVs, hatches, eletricos ou modelos premium?
- modelos com melhor consumo recebem mais atencao em reviews?
- videos de comparativo citam modelos tecnicamente equivalentes?
- crescimento de interesse em um modelo acompanha emplacamento da marca ou
  segmento?

O ChatGPT deve separar claramente:

```text
Ficha tecnica / catalogo -> Carros na Web
Venda / market share -> Fenabrave
Frota registrada -> SENATRAN/RENAVAM
Performance social -> YouTube
```

## Criterio de pronto da fase 1

A fase 1 estara pronta quando:

- origem dos CSVs recorrentes estiver documentada
- rotina de download estiver definida com frequencia, responsavel, destino e
  regra de substituicao/versao
- arquivos baixados preservarem hash/versao, data de download e status de
  validacao
- tabelas iniciais no Supabase persistirem fabricantes, modelos e anos do
  modelo
- validacoes cobrirem schema esperado, duplicidades, campos obrigatorios e
  deteccao de novas entradas
- view analitica inicial estiver criada para Streamlit
- fichas tecnicas por scraping estiverem explicitamente em `on_hold`

## Regra de decisao para fichas tecnicas

Fichas tecnicas por scraping ficam em `on_hold`.

So retomar essa frente se surgir fonte viavel, repetivel e sem bypass fragil.
Essa pendencia nao bloqueia o catalogo por CSV nem a view do Streamlit.

## Commit sugerido

```text
docs(carrosnaweb): define contrato de catalogo por csv
```
