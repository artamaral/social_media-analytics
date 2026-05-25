# Plano de estudo de dados externos automotivos

Data: 2026-05-15

## Objetivo

Definir quais dados externos automotivos serao usados no projeto, por que eles importam e como preparar o Supabase para recebe-los com rastreabilidade, qualidade e uso analitico no Streamlit e no ChatGPT via API.

Este plano tambem define uma fronteira importante:

- dados estruturados no Supabase: apenas Fenabrave e SENATRAN/RENAVAM
- contexto para textos e interpretacao: estudos e dados atuais de outras fontes setoriais ou macroeconomicas
- fora do plano atual: fontes pagas ou restritas, como SERPRO/SENATRAN

## Status consolidado da frente

- Fenabrave: ja possui modelagem inicial e processo local controlado
- SENATRAN/RENAVAM: continua em estudo de granularidade, dataset e schema final
- Carros na Web: tem papel analitico claro como catalogo tecnico, mas esta
  bloqueado por captcha e nao deve ser tratado como pipeline estruturado nem
  como modelagem final neste momento

## Principio central

Para analise de venda e market share no Brasil, a verdade principal deve ser emplacamento.

```text
Venda / market share / demanda real -> emplacamentos
Frota registrada / validacao governamental -> SENATRAN/RENAVAM
Contexto industrial, financeiro, tecnico ou setorial -> apenas apoio narrativo
```

O projeto nao deve confundir:

- emplacamento com producao
- frota registrada com venda mensal
- importacao com venda final
- dado contextual com dado estruturado do produto

## Escopo decidido

### Dados que entram no Supabase

1. Fenabrave
2. SENATRAN / RENAVAM

### Dados fora do Supabase no escopo atual

SERPRO/SENATRAN fica fora do plano atual porque e uma fonte paga/restrita.

MDIC/Comex Stat, Inmetro/PBE Veicular, ABVE, ANFAVEA, Banco Central, ABLA e outras fontes podem ser usadas como contexto para elaboracao de textos, interpretacao de movimentos de mercado e enriquecimento editorial, mas nao devem virar pipeline nem tabelas estruturadas neste momento.

## Perguntas que o estudo precisa responder

1. Qual dado da Fenabrave sera ingerido primeiro?
2. Qual dado aberto do SENATRAN/RENAVAM e realmente util para validar ou contextualizar frota?
3. Qual e a granularidade disponivel em cada fonte: mes, marca, modelo, segmento, UF ou municipio?
4. Qual formato publico existe: PDF, XLSX, CSV, API, painel ou arquivo aberto?
5. Como preservar fonte, periodo, data de captura e status de extracao?
6. Como o ChatGPT deve citar a origem ao responder no Streamlit?
7. Quais fontes devem ser usadas apenas como contexto textual e nao como base estruturada?

## Fontes estruturadas

### 1. Fenabrave

Papel no projeto:

- fonte pratica principal para emplacamentos e leitura mensal de mercado
- base inicial para ranking de marcas, segmentos e modelos
- fonte mais proxima da pergunta "quem vendeu mais?"

Uso esperado no Supabase:

- `market_vehicle_registrations`
- `market_brand_market_share`
- `market_model_rankings`
- `analytics_keywords` para marcas/modelos

Estado atual:

- ja existe modelagem inicial no repositorio para controle de fonte, arquivo
  capturado, serie mensal por segmento e view analitica inicial
- a frente ainda nao fechou se a modelagem final permanecera por segmento por
  mais tempo ou se ja deve expandir para `marca` e `modelo`

Pontos de atencao:

- releases publicos parecem ser PDF-first
- DMP pode oferecer dados personalizados, mas exige cadastro/acesso
- PDF deve ser tratado como fallback de ingestao, nao como formato ideal
- todo dado extraido precisa manter fonte, periodo e validacao contra o total publicado

Referencias:

- https://www.fenabrave.org.br/portalv2/Conteudo/Emplacamentos%20
- https://www.fenabrave.org.br/Dados/index2.html

### 2. SENATRAN / RENAVAM

Papel no projeto:

- fonte governamental para frota registrada e validacao oficial
- apoio para distribuicao por UF, municipio e tipo de veiculo quando os dados abertos permitirem

Uso esperado no Supabase:

- `market_vehicle_fleet`
- `market_region_fleet`
- validacao cruzada contra totais agregados de emplacamentos, quando fizer sentido

Pontos de atencao:

- dado aberto publico e mais forte para frota registrada do que para venda mensal por modelo
- frota registrada nao e igual a venda mensal
- frota registrada tambem nao e necessariamente frota circulante
- qualquer uso precisa rotular claramente a metrica como frota/registro, nao venda

Estado atual:

- a fonte ja esta enquadrada como estruturada no escopo do projeto
- o dataset real, a granularidade util e a tabela normalizada final ainda nao
  foram fechados

### 2.1 O que significa modelagem final nesta frente

Para este plano, `modelagem final` significa definir:

- qual dataset publico entra de fato no projeto
- qual granularidade vira tabela persistida
- qual chave de rastreabilidade liga o dado ao arquivo ou publicacao original
- quais campos sao obrigatorios
- como a metrica sera rotulada para nao confundir frota com venda
- como a camada normalizada se conecta a marcas, modelos e regioes

Referencias:

- https://www.gov.br/transportes/pt-br/assuntos/transito/senatran/estatisticas-senatran
- https://dados.transportes.gov.br/dataset/registro-nacional-de-veiculos-automotores-renavam

## Fontes fora do pipeline atual

### Carros na Web

Status:

- fonte desejada para catalogo tecnico
- bloqueada por captcha no momento

Uso permitido agora:

- manter apenas como plano e referencia de produto
- nao assumir captura repetivel
- nao criar schema definitivo no Supabase antes de validar viabilidade etica e
  operacional da coleta

### 3. SERPRO / SENATRAN

Status:

- fora do plano atual

Motivo:

- fonte paga ou restrita
- pode exigir contrato, credenciamento ou pagamento
- nao deve ser assumida como dado aberto para o MVP

Uso permitido:

- apenas mencionar como alternativa futura se houver acesso, orcamento e justificativa clara

Referencias:

- https://loja.serpro.gov.br/arquivoseletronicossenatran
- https://loja.serpro.gov.br/painelveicular

### 4. MDIC / Comex Stat

Status:

- contexto, nao pipeline

Uso permitido:

- apoiar textos sobre importados, origem externa, cambio e pressao competitiva
- explicar movimentos de mercado quando houver evidencia atual

Restricao:

- nao criar tabelas no Supabase neste momento
- nao usar como base principal para ranking de venda

Referencia:

- https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta

### 5. Inmetro / PBE Veicular

Status:

- contexto, nao pipeline

Uso permitido:

- apoiar textos sobre eficiencia energetica, consumo, emissoes, eletrificacao e comparativos tecnicos

Restricao:

- nao criar tabelas de especificacao no Supabase neste momento
- nao transformar comparativo tecnico em ranking de mercado

Referencia:

- https://www.gov.br/inmetro/pt-br/assuntos/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/veiculos-automotivos-pbe-veicular

### 6. ABVE

Status:

- contexto, nao pipeline

Uso permitido:

- apoiar textos sobre eletrificados, BEV, PHEV, HEV, MHEV e infraestrutura de recarga
- complementar leitura de mercado quando o tema for eletrificacao

Restricao:

- nao substituir Fenabrave para ranking geral de venda
- nao criar tabelas estruturadas neste momento

Referencia:

- https://abve.org.br/

### 7. ANFAVEA

Status:

- contexto, nao pipeline

Uso permitido:

- apoiar textos sobre producao nacional, industria, exportacao, emprego e capacidade produtiva

Restricao:

- nao usar como verdade principal de venda no Brasil
- nao usar para medir market share de marcas com forte presenca de importados

Referencias:

- https://anfavea.com.br/site/carta-da-anfavea/
- https://anfavea.com.br/site/edicoes-em-excel/

### 8. Banco Central

Status:

- contexto, nao pipeline

Uso permitido:

- apoiar textos sobre credito, juros, financiamento e ciclo de compra

Restricao:

- nao criar tabelas de indicadores financeiros neste momento
- nao tratar credito como dado de venda

Referencia:

- https://www3.bcb.gov.br/sgspub/index.jsp

### 9. ABLA

Status:

- contexto, nao pipeline

Uso permitido:

- apoiar textos sobre locadoras, frota corporativa e compras por canal

Restricao:

- nao substituir emplacamento geral
- nao criar tabelas estruturadas neste momento

Referencia:

- https://www.abla.com.br/

## Priorizacao inicial

### Fase 1 - Fenabrave

Objetivo:

- criar a primeira ingestao de emplacamentos
- validar extracao, totais e periodos
- gerar a primeira view de consumo para Streamlit e ChatGPT

Especificacao detalhada:

- `23_FENABRAVE_PHASE1_INGESTION_SPEC.md`

Entregaveis:

- tabela de controle de fonte
- tabela de arquivo/fonte capturada
- raw da primeira tabela extraida
- tabela normalizada por segmento
- validacao contra o PDF ou fonte original
- view analitica inicial

### Fase 2 - SENATRAN / RENAVAM

Objetivo:

- avaliar dados abertos oficiais de frota registrada
- definir quais campos agregam valor ao produto
- carregar apenas o que ajudar na validacao e contexto estrutural de frota

Entregaveis:

- matriz de campos disponiveis
- decisao de granularidade
- tabela normalizada de frota, se o dado aberto justificar
- validacao de rotulos para nao confundir frota com venda

### Fase 3 - Contexto textual

Objetivo:

- documentar como fontes #4 em diante podem apoiar textos e interpretacoes
- evitar transformar toda fonte interessante em pipeline

Entregaveis:

- regra de uso contextual
- lista de fontes permitidas para consulta pontual
- padrao de citacao no texto gerado pelo ChatGPT

## Modelo recomendado no Supabase

### Controle de fontes

```sql
public.market_data_sources
public.market_source_files
public.market_ingestion_runs
```

Objetivo:

- registrar origem
- registrar URL ou arquivo
- registrar periodo de referencia
- registrar data de captura
- registrar status de extracao
- permitir auditoria de cada resposta do ChatGPT

Campos minimos:

```text
source_name
source_type
source_url
access_type
file_type
reference_period
captured_at
license_notes
ingestion_status
checksum
```

### Camada raw

Tabelas raw permitidas no escopo atual:

```sql
public.raw_fenabrave_tables
public.raw_renavam_fleet
```

Objetivo:

- preservar o dado original extraido
- permitir reprocessamento
- separar parsing de modelagem analitica

### Camada normalizada

Tabelas normalizadas permitidas no escopo atual:

```sql
public.market_vehicle_registrations
public.market_brand_market_share
public.market_model_rankings
public.market_vehicle_fleet
```

Fora do escopo atual:

```text
market_vehicle_imports
market_vehicle_production
market_vehicle_specs
market_credit_indicators
market_rental_fleet
market_electrified_registrations
```

Essas tabelas nao devem ser criadas agora. Os temas podem aparecer em textos apenas como contexto consultado e citado.

### Taxonomia e harmonizacao

```sql
public.analytics_keywords
public.market_brands
public.market_models
public.market_source_aliases
```

Objetivo:

- mapear `vw` para `Volkswagen`
- mapear `gm` para `Chevrolet`
- mapear nomes diferentes entre Fenabrave, YouTube e SENATRAN/RENAVAM
- evitar duplicidade de marcas/modelos

## Contrato de resposta do ChatGPT no Streamlit

O ChatGPT deve consultar primeiro o Supabase para qualquer resposta de dados estruturados.

Busca externa ao vivo deve acontecer apenas quando:

- o usuario pedir explicitamente contexto externo atual
- o dado nao existir no Supabase
- houver duvida de fonte ou divergencia
- a resposta for editorial e precisar de contexto recente

Toda resposta baseada em mercado deve separar:

```text
dado estruturado usado
fonte
periodo de referencia
data de captura
metrica usada
limite conhecido da fonte
contexto externo consultado, se houver
```

Exemplo:

```text
Dado estruturado: Fenabrave
Periodo: abril/2026
Metrica: emplacamentos
Capturado em: 2026-05-15
Observacao: emplacamento usado como proxy de venda.
Contexto adicional: nao utilizado.
```

## Validacoes obrigatorias antes de usar no dashboard

Para qualquer fonte estruturada:

- verificar se o periodo foi carregado uma unica vez
- validar totais contra a publicacao original
- validar que percentuais batem com os totais
- validar que marcas/modelos foram normalizados
- preservar linhas que nao conseguiram ser classificadas
- registrar divergencias e ajustes manuais

Para Fenabrave:

- total por segmento deve bater com o PDF ou fonte estruturada
- `Autos + Comerciais Leves` deve bater com subtotal informado
- acumulado deve ser consistente com meses anteriores ja carregados
- ranking por marca/modelo deve preservar posicao original

Para SENATRAN/RENAVAM:

- distinguir frota registrada de venda/emplacamento mensal
- registrar nivel geografico usado
- evitar comparar diretamente frota com emplacamentos sem rotulo claro

Para fontes contextuais:

- nao ingerir no Supabase
- consultar apenas quando houver pergunta ou texto que demande contexto
- citar a fonte no texto gerado
- nao misturar contexto com ranking estruturado

## Entregaveis do estudo

1. Matriz de Fenabrave e SENATRAN/RENAVAM.
2. Decisao de granularidade por fonte estruturada.
3. Modelo inicial de tabelas no Supabase apenas para essas duas fontes.
4. Query de validacao por fonte estruturada.
5. Processo de ingestao para Fenabrave.
6. Processo de avaliacao de dados abertos SENATRAN/RENAVAM.
7. Processo de harmonizacao de marcas/modelos.
8. Regra de uso contextual para as demais fontes.
9. Contrato de uso pelo Streamlit e ChatGPT.

## Ordem recomendada de execucao

1. Definir Fenabrave como piloto de ingestao.
2. Criar tabelas de controle de fonte e arquivos.
3. Extrair 1 PDF da Fenabrave e carregar raw.
4. Normalizar a primeira tabela de emplacamentos por segmento.
5. Validar totais contra o PDF.
6. Criar primeira view de consumo para Streamlit.
7. Criar prompt/funcao do ChatGPT para responder usando apenas dados carregados.
8. Expandir Fenabrave para marca/modelo.
9. Avaliar dados abertos SENATRAN/RENAVAM.
10. Documentar regra de uso contextual para fontes #4 em diante.

## Criterio de sucesso

O estudo estara pronto quando o projeto conseguir responder, via Supabase e sem buscar na web em tempo real:

```text
Quais marcas ganharam participacao no mes?
Quais segmentos cresceram mais?
O crescimento de uma marca no YouTube acompanha emplacamento?
Quais montadoras aparecem mais nos titulos e tambem vendem mais?
Qual e o contexto de frota registrada para uma regiao ou tipo de veiculo?
```

Para perguntas editoriais, o ChatGPT podera consultar fontes #4 em diante como contexto, mas deve deixar claro que esses dados nao fazem parte da base estruturada do projeto.

## Decisao provisoria

Enquanto o estudo nao for concluido:

- usar Fenabrave como fonte pratica principal de emplacamentos
- usar SENATRAN/RENAVAM como validacao governamental e frota
- manter SERPRO/SENATRAN fora do plano atual por ser pago/restrito
- usar fontes #4 em diante apenas como contexto para textos e interpretacao
- nao usar ANFAVEA como verdade de venda
- nao fazer o ChatGPT depender de busca web para cada pergunta
- manter Supabase como camada persistente e auditavel apenas para as fontes estruturadas escolhidas
