# Plano de ingestao Carros na Web - modelos e ficha tecnica

Data: 2026-05-19

## Objetivo

Planejar a inclusao dos dados do Carros na Web no projeto como base estruturada
de catalogo automotivo, modelos e ficha tecnica.

## Status atual consolidado

- a fonte continua relevante como catalogo tecnico
- a descoberta inicial de fabricantes funcionou e encontrou aproximadamente
  `127` fabricantes
- a descoberta de modelos funcionou melhor quando passou a considerar links
  `catalogomodelo.asp?` e `catalogo.asp?`, com sessao aquecida e CSV
  persistido
- a nova camada descoberta no fluxo e `anos_modelo.csv`: modelos levam para
  anos, e anos podem levar para fichas
- algumas URLs de ano nao contem links de ficha e podem retornar pagina de erro
- a captura direta de fichas continua sujeita a erro 500, pagina de erro,
  validacao/captcha e ambiente Python incorreto
- o diagnostico de acesso ja conseguiu retornar `success` para fichas reais
  como `44763`, `22547` e `4801`
- o parser de tabela dentro do HTML ja conseguiu extrair linhas tecnicas a
  partir de tags `table` / `tr` / `td`
- por isso, a frente deve validar primeiro `anos_modelo.csv` e gerar
  `anos_modelo_validos.csv` antes de qualquer parser final ou schema definitivo
  no Supabase

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

Nao enumerar IDs sequenciais.

O scraper deve usar somente URLs reais descobertas por paginas publicas do
catalogo:

```text
fabricantes -> modelos -> anos do modelo -> fichas validas -> HTML bruto -> parser -> CSV/tabelas
```

Motivo:

- chamadas diretas com sessao e headers completos funcionaram para uma ficha
  valida
- headers simples podem causar erro 500
- tentativa de alterar manualmente o codigo acionou fluxo de captcha
- enumeracao massiva de IDs aumenta risco de bloqueio e gera chamadas inuteis
- no estado atual, o captcha esta bloqueando a captura consistente e impede
  tratar esta fonte como pipeline repetivel

Regra:

```text
Nao usar range(44763, 50000)
Nao tentar descobrir fichas por forca bruta
Nao tentar burlar captcha
Usar apenas URLs publicadas no catalogo
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
Discovery de catalogo
  -> CSVs de controle local
  -> validacao das paginas de ano
  -> HTML bruto das fichas
  -> parser de tabelas HTML
  -> dados tecnicos em formato longo
  -> normalizacao futura no Supabase
  -> consumo por Streamlit e ChatGPT
```

Resumo operacional consolidado para a frente:

```text
fabricantes -> modelos -> fichas -> parser -> atualizacao incremental
```

Observacao importante:

- esse fluxo resume a direcao do produto
- quando o catalogo do site exigir uma etapa intermediaria por ano, ela continua
  valida como subetapa tecnica entre `modelos` e `fichas`

## Escopo da fase 1

Objetivo da fase 1:

- provar discovery de fabricantes, modelos, anos e fichas
- validar URLs de ano antes de procurar fichas
- baixar HTML apenas de fichas validas descobertas no catalogo
- parsear tabelas de ficha tecnica
- salvar dados em CSV para reuso e auditoria
- manter logs simples de debug para entender cada etapa

Formato inicial:

- CSV local
- HTML bruto local
- Python com `requests`, `BeautifulSoup` e `pandas`

Motivo para comecar em CSV:

- reduz complexidade antes de criar schema definitivo
- facilita inspecao manual dos resultados
- preserva os passos intermediarios do discovery
- permite validar qualidade antes de levar para Supabase

Pre-condicao real para executar esta fase:

- confirmar que a captura consegue ocorrer de forma etica, repetivel e sem
  bypass de protecao
- se essa pre-condicao nao for atendida, a frente deve permanecer em espera
  antes de qualquer decisao de schema

Fora do escopo da fase 1:

- Playwright como caminho principal de coleta
- OCR obrigatorio
- captcha solving
- proxy rotation
- alta concorrencia
- scheduler incremental
- schema definitivo no Supabase

## Estrutura de pastas recomendada no repo

Como o repositorio ja organiza aquisicoes em `scripts/<fonte>`, a implementacao
deve adaptar a estrutura sugerida para ficar consistente com os codigos atuais.

Estrutura alvo:

```text
scripts/carrosnaweb_ingestion/
  data/
    discovery/
      fabricantes.csv
      modelos.csv
      anos_modelo.csv
      anos_modelo_validos.csv
      fichas.csv
      test_fichas_15.csv
      fichas_scrape_status.csv
    debug_html/
    raw_html/
      fichas/
    processed/
      ficha_tecnica.csv
  src/
    carrosnaweb_client.py
    discovery.py
    parser.py
    utils.py
  01_discover_fabricantes.py
  02_discover_modelos.py
  03_discover_anos.py
  04_validate_anos.py
  05_discover_fichas.py
  06_scrape_fichas.py
  07_parse_fichas.py
  diagnostics/
    debug_url.py
    test_playwright.py
  README.md
  requirements.txt
```

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

Antes de continuar para parser final de ficha tecnica, corrigir e validar a
etapa `anos_modelo.csv`.

Tarefa imediata:

```text
Criar validacao de url_ano:
- abrir cada url_ano
- registrar status HTTP
- registrar final_url
- verificar se contem fichadetalhe.asp
- verificar se contem Ocorreu um erro
- salvar apenas URLs validas em anos_modelo_validos.csv
```

Essa tarefa agora tambem esta refletida no roadmap do projeto.

## Parser validado no HTML

O comportamento validado na ficha atual e:

- os dados tecnicos estao dentro de estruturas `table` no HTML
- a extracao precisa percorrer `tr` e `td`
- uma mesma linha pode conter 2 colunas utilitarias ou 4 celulas no padrao
  `campo -> valor -> campo -> valor`
- grupos como `MOTOR`, `TRANSMISSAO` e semelhantes podem ser inferidos por
  linhas com texto unico em caixa alta

Direcao atual do parser:

- salvar HTML bruto localmente
- extrair pares `field` e `value`
- manter `group`
- preservar `image_urls` quando houver imagem embutida no valor
- produzir formato longo para futura normalizacao

## Roadmap de implementacao

### Prioridade 1 - estrutura

Criar estrutura:

```text
scripts/carrosnaweb_ingestion/src/
scripts/carrosnaweb_ingestion/data/discovery/
scripts/carrosnaweb_ingestion/data/debug_html/
scripts/carrosnaweb_ingestion/data/raw_html/fichas/
scripts/carrosnaweb_ingestion/data/processed/
scripts/carrosnaweb_ingestion/diagnostics/
```

Criar arquivos base:

```text
scripts/carrosnaweb_ingestion/src/carrosnaweb_client.py
scripts/carrosnaweb_ingestion/requirements.txt
scripts/carrosnaweb_ingestion/README.md
```

### Prioridade 2 - primeiro discovery

Implementar e testar:

```text
scripts/carrosnaweb_ingestion/src/carrosnaweb_client.py
scripts/carrosnaweb_ingestion/01_discover_fabricantes.py
```

Resultado esperado:

```text
scripts/carrosnaweb_ingestion/data/discovery/fabricantes.csv
```

Com aproximadamente:

```text
127 fabricantes
```

### Prioridade 3 - modelos e fichas

Implementar:

```text
scripts/carrosnaweb_ingestion/02_discover_modelos.py
scripts/carrosnaweb_ingestion/03_discover_anos.py
scripts/carrosnaweb_ingestion/04_validate_anos.py
```

Resultado esperado:

```text
scripts/carrosnaweb_ingestion/data/discovery/modelos.csv
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo_validos.csv
```

### Prioridade 4 - fichas, HTML bruto e parser

Implementar:

```text
scripts/carrosnaweb_ingestion/05_discover_fichas.py
scripts/carrosnaweb_ingestion/06_scrape_fichas.py
scripts/carrosnaweb_ingestion/src/parser.py
scripts/carrosnaweb_ingestion/07_parse_fichas.py
```

Resultado esperado:

```text
scripts/carrosnaweb_ingestion/data/discovery/fichas.csv
scripts/carrosnaweb_ingestion/data/raw_html/fichas/<codigo>.html
scripts/carrosnaweb_ingestion/data/processed/ficha_tecnica.csv
```

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

- `fabricantes.csv` existir e tiver fabricantes unicos
- `modelos.csv` existir e nao tiver `url_modelo` duplicadas relevantes
- `anos_modelo.csv` existir e tiver anos extraidos por fabricante/modelo
- `anos_modelo_validos.csv` existir e separar `valid_year_page`,
  `no_ficha_links`, `site_error`, `http_error` e `unexpected_page`
- `fichas.csv` existir e tiver codigos unicos descobertos por catalogo
- `fichas_scrape_status.csv` registrar status de coleta
- HTML bruto de uma amostra limitada estiver salvo localmente
- `ficha_tecnica.csv` tiver registros em formato longo
- campos com imagens estiverem preservando `image_urls`
- nenhuma coleta tiver dependido de enumeracao sequencial de IDs
- captcha, bloqueio ou erro 500 estiverem registrados como status operacional

## Regra de decisao antes de schema definitivo

Antes de criar qualquer modelagem final no Supabase para esta fonte, o projeto
deve concluir:

- se a captura e viavel sem bypass de protecao
- se a cobertura obtida justifica a frente como base estruturada
- se a coleta consegue ser repetivel com risco operacional aceitavel

## Commit sugerido

```text
docs(scraper): documenta aprendizado do pipeline carrosweb
```
