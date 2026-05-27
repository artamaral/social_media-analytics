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
fabricantes -> modelos -> fichas validas -> HTML bruto -> parser -> CSV/tabelas
```

Motivo:

- chamadas diretas com sessao e headers completos funcionaram para uma ficha
  valida
- headers simples podem causar erro 500
- tentativa de alterar manualmente o codigo acionou fluxo de captcha
- enumeracao massiva de IDs aumenta risco de bloqueio e gera chamadas inuteis

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
  -> HTML bruto das fichas
  -> parser de tabelas HTML
  -> dados tecnicos em formato longo
  -> normalizacao futura no Supabase
  -> consumo por Streamlit e ChatGPT
```

Resumo operacional consolidado para a frente:

```text
fabricantes -> modelos -> anos -> aplicacoes -> fichas -> parser -> atualizacao incremental
```

Observacao importante:

- esse fluxo resume a direcao do produto
- a etapa `anos` deixou de ser apenas opcional e passa a ser parte explicita do
  pipeline atual, porque o catalogo exige navegacao por `url_ano`
- a etapa `aplicacoes` passa a ser a listagem real por modelo/ano, incluindo
  cenarios com paginacao em `catalogo.asp`, antes da captura confiavel das
  fichas

## Escopo da fase 1

Objetivo da fase 1:

- provar discovery de fabricantes, modelos e fichas
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

Fora do escopo da fase 1:

- Selenium ou Playwright
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
      fichas.csv
      fichas_scrape_status.csv
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
  03_discover_fichas.py
  04_scrape_fichas.py
  05_parse_fichas.py
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

- `scripts/carrosnaweb_ingestion/01_discover_fabricantes.py` para gerar a
  primeira camada de discovery em CSV
- `scripts/carrosnaweb_ingestion/diagnostics/check_ficha_access.py` para
  diagnostico de acesso, classificacao de resposta, salvamento de HTML bruto e
  extracao exploratoria de tabela
- `scripts/carrosnaweb_ingestion/src/carrosnaweb_client.py` como cliente HTTP
  compartilhado com sessao aquecida
- `scripts/carrosnaweb_ingestion/02_discover_modelos.py` para a camada
  `fabricantes -> modelos`
- `scripts/carrosnaweb_ingestion/03_discover_anos.py` para a camada
  `modelos -> anos_modelo`
- `scripts/carrosnaweb_ingestion/04_discover_aplicacoes.py` para a camada
  `anos_modelo -> aplicacoes_modelo_ano`, com suporte a paginacao em
  `catalogo.asp`
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

Base tecnica preservada do estudo:

```text
BASE_URL = "https://www.carrosnaweb.com.br"
create_session()
warm_up_session(session)
safe_get(session, url, timeout=30, delay_min=1.5, delay_max=4.0)
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

Localizacao canonicamente esperada no repo:

```text
C:\social_media-analytics\scripts\carrosnaweb_ingestion\data\discovery\fabricantes.csv
```

Necessidade operacional:

- esse arquivo precisa existir antes de rodar
  `scripts/carrosnaweb_ingestion/02_discover_modelos.py`
- o script de modelos procura primeiro esse caminho
- se ele nao existir, o script de modelos tenta localizar `fabricantes.csv`
  automaticamente em subpastas proximas
- mesmo com esse fallback, o caminho acima deve ser tratado como fonte de
  verdade para evitar ambiguidade

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

Localizacao canonicamente esperada no repo:

```text
C:\social_media-analytics\scripts\carrosnaweb_ingestion\data\discovery\fabricantes.csv
```

Saida canonicamente esperada:

```text
C:\social_media-analytics\scripts\carrosnaweb_ingestion\data\discovery\modelos.csv
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

Localizacao canonicamente esperada no repo:

```text
C:\social_media-analytics\scripts\carrosnaweb_ingestion\data\discovery\modelos.csv
```

Saida canonicamente esperada:

```text
C:\social_media-analytics\scripts\carrosnaweb_ingestion\data\discovery\anos_modelo.csv
```

Logica:

- ler modelos
- acessar cada `url_modelo`
- extrair ano por parametro, texto do link ou URL
- aceitar links candidatos quando apontarem para `catalogo` ou `fichadetalhe`
- remover duplicados por URL

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

Saida:

```text
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv
```

### 6. Salvar anos_modelo.csv

O CSV deve ser salvo com:

```text
encoding="utf-8-sig"
index=False
```

O script deve imprimir:

- fabricante e modelo atuais
- URL do modelo
- quantidade de anos encontrados
- preview das linhas de anos encontradas

### 7. Discovery de aplicacoes por modelo/ano com paginacao

Script:

```text
scripts/carrosnaweb_ingestion/04_discover_aplicacoes.py
```

Entrada:

```text
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv
```

Regra critica:

```text
O script nao pode enumerar IDs.
Ele deve capturar somente links publicados nas paginas reais do catalogo.
```

Saida:

```text
scripts/carrosnaweb_ingestion/data/discovery/aplicacoes_modelo_ano.csv
```

Colunas esperadas:

```text
fabricante
modelo
ano
pagina_lista
url_ano_origem
url_lista_atual
codigo_ficha
url_ficha
versao
href_original
texto_link
params
```

Regras adicionais:

- a camada deve suportar listas grandes com `next page`
- a paginacao deve ser seguida apenas quando a URL continuar pertencendo ao
  mesmo contexto de fabricante, modelo e ano
- os links coletados devem apontar para `fichadetalhe.asp?codigo=...`
- deduplicar por `codigo_ficha` e `url_ficha`

### 8. Scraper de fichas apenas com URLs validas

Script:

```text
scripts/carrosnaweb_ingestion/05_scrape_fichas.py
```

Entrada:

```text
scripts/carrosnaweb_ingestion/data/discovery/aplicacoes_modelo_ano.csv
```

### 9. Parser de tabela HTML

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
codigo
page_url
page_title
group
field
value
image_urls
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

### 10. Salvar raw HTML

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

### 11. Salvar dados estruturados

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

### 12. Rodar validacoes de qualidade

Validacoes iniciais:

```python
df = pd.read_csv("data/discovery/fabricantes.csv")
print(df.shape)
print(df.head())
print(df["fabricante"].nunique())
```

```python
df = pd.read_csv("scripts/carrosnaweb_ingestion/data/discovery/modelos.csv")
print(df.shape)
print(df.head())
print(df["url_modelo"].duplicated().sum())
```

```python
df = pd.read_csv("scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv")
print(df.shape)
print(df.head())
print(df["url_ano"].duplicated().sum())
```

```python
df = pd.read_csv("scripts/carrosnaweb_ingestion/data/discovery/fichas.csv")
print(df.shape)
print(df.head())
print(df["codigo"].duplicated().sum())
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

## Dependencia entre CSVs

Contrato atual entre as camadas de discovery:

```text
01_discover_fabricantes.py
  output -> scripts/carrosnaweb_ingestion/data/discovery/fabricantes.csv

02_discover_modelos.py
  input  -> scripts/carrosnaweb_ingestion/data/discovery/fabricantes.csv
  output -> scripts/carrosnaweb_ingestion/data/discovery/modelos.csv

03_discover_anos.py
  input  -> scripts/carrosnaweb_ingestion/data/discovery/modelos.csv
  output -> scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv

04_discover_aplicacoes.py
  input  -> scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv
  output -> scripts/carrosnaweb_ingestion/data/discovery/aplicacoes_modelo_ano.csv
```

Implicacao pratica:

- se `fabricantes.csv` ainda nao foi gerado, `02_discover_modelos.py` nao deve
  ser executado
- se `modelos.csv` ainda nao foi gerado, `03_discover_anos.py` nao deve ser
  executado
- o fluxo correto no repo passa a ser rodar primeiro o script de fabricantes e
  depois o script de modelos e o script de anos

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
scripts/carrosnaweb_ingestion/data/raw_html/fichas/
scripts/carrosnaweb_ingestion/data/processed/
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
```

Resultado esperado:

```text
scripts/carrosnaweb_ingestion/data/discovery/modelos.csv
scripts/carrosnaweb_ingestion/data/discovery/anos_modelo.csv
```

### Prioridade 4 - HTML bruto e parser

Implementar:

```text
scripts/carrosnaweb_ingestion/04_discover_aplicacoes.py
scripts/carrosnaweb_ingestion/05_scrape_fichas.py
scripts/carrosnaweb_ingestion/src/parser.py
scripts/carrosnaweb_ingestion/07_parse_fichas.py
```

Resultado esperado:

```text
scripts/carrosnaweb_ingestion/data/discovery/aplicacoes_modelo_ano.csv
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
- `modelos.csv` existir e nao tiver URLs duplicadas relevantes
- `fichas.csv` existir e tiver codigos unicos descobertos por catalogo
- `fichas_scrape_status.csv` registrar status de coleta
- HTML bruto de uma amostra limitada estiver salvo localmente
- `ficha_tecnica.csv` tiver registros em formato longo
- campos com imagens estiverem preservando `image_urls`
- nenhuma coleta tiver dependido de enumeracao sequencial de IDs
- captcha, bloqueio ou erro 500 estiverem registrados como status operacional

## Commit sugerido

```text
docs(roadmap): adiciona plano de ingestao carrosnaweb
```
