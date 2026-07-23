# Carros na Web - catalogo no Supabase para homogeneizacao de veiculos

## Objetivo

Persistir no Supabase os CSVs de catalogo do Carros na Web para servir como
base de referencia de fabricantes, modelos e anos/modelo em classificacoes de
videos automotivos.

Esta entrega nao usa ficha tecnica, nao usa HTML bruto e nao retoma scraping de
fichas. O objetivo e corrigir e homogeneizar entidades de veiculo extraidas de:

- descricao do video;
- transcricao dos primeiros `90s`;
- classificacao humana;
- classificacao assistida por GPT.

## Fonte

Snapshot inicial usado nesta etapa:

- commit Git: `4ace350`
- caminho original: `scripts/carrosnaweb_ingestion/data/discovery/`

CSVs usados:

- `fabricantes.csv`
- `modelos.csv`
- `anos_modelo.csv`

CSV excluido:

- `aplicacoes_modelo_ano_test.csv`

Motivo da exclusao:

- o arquivo foi criado para explorar aplicacoes/fichas tecnicas por ano/modelo;
- fichas tecnicas permanecem em `on_hold`;
- a camada atual deve cobrir apenas catalogo de fabricante, modelo e ano.

## Modelagem no Supabase

DDL versionada:

- `sql/ddl/tables/021_create_market_carrosnaweb_catalog.sql`
- `sql/ddl/views/022_create_v_carrosnaweb_vehicle_catalog.sql`
- `sql/ddl/tests/010_test_carrosnaweb_catalog.sql`

Tabelas:

- `public.market_carrosnaweb_manufacturers`
- `public.market_carrosnaweb_models`
- `public.market_carrosnaweb_model_years`

View:

- `public.v_carrosnaweb_vehicle_catalog`

A view consolida o nivel usado para validacao de entidades:

- `manufacturer_name`
- `manufacturer_key`
- `model_name`
- `model_key`
- `model_year`
- metadados de origem do CSV via `source_file_id`

## Campos canonicos

### Fabricante

Origem:

- coluna `fabricante`
- coluna `value`
- URL do fabricante

Uso:

- `manufacturer_name`: texto original/canonico do CSV;
- `manufacturer_param`: valor de fabricante quando derivavel;
- `manufacturer_key`: chave normalizada para matching.

### Modelo

Origem:

- coluna `fabricante`
- coluna `modelo`
- coluna `codigo_modelo`
- coluna `params`

Uso:

- `model_name`: texto original/canonico do CSV;
- `model_param`: valor `params.modelo`, quando disponivel;
- `model_key`: chave normalizada para matching;
- `params`: JSON bruto preservado.

### Ano/modelo

Origem:

- coluna `fabricante`
- coluna `modelo`
- coluna `ano`
- coluna `params`

Uso:

- `model_year`: ano/modelo numerico;
- `model_param`: valor `params.varnome`, quando disponivel;
- `param_year_start`: valor `params.anoini`;
- `param_year_end`: valor `params.anofim`;
- `params`: JSON bruto preservado.

## Script de ingestao

Utilitario:

```powershell
python scripts\carrosnaweb_ingestion\ingest_carrosnaweb_catalog.py --dry-run
```

Carga no Supabase:

```powershell
python scripts\carrosnaweb_ingestion\ingest_carrosnaweb_catalog.py --write
```

Variaveis esperadas para `--write`:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` ou `SUPABASE_KEY`

O script:

- registra a fonte `Carros na Web` em `market_data_sources`;
- registra cada CSV em `market_source_files`;
- calcula `sha256`;
- vincula cada linha importada a um `source_file_id`;
- valida schema, obrigatoriedade, duplicidades e `params`;
- preserva dados originais e adiciona chaves normalizadas.

## Validacoes

O `dry-run` deve confirmar aproximadamente:

- `127` fabricantes;
- `1458` modelos;
- `8914` anos/modelo;
- nenhuma carga de `aplicacoes_modelo_ano_test.csv`.

Buscas de validacao local:

- `BYD Dolphin`;
- `Renault Kwid`;
- `Changan Uni T`;
- `Hyundai HB20`.

Se um termo nao existir no catalogo, ele nao deve ser inventado como match. O
resultado futuro deve ser marcado como `needs_review`.

Resultado validado localmente em 2026-07-23:

- `fabricantes.csv`: `127` linhas;
- `modelos.csv`: `1458` linhas;
- `anos_modelo.csv`: `8914` linhas;
- `aplicacoes_modelo_ano_test.csv`: nao carregado;
- `BYD Dolphin`, `Renault Kwid`, `Changan Uni T` e `Hyundai HB20` encontrados
  na validacao local.

Carga REST em 2026-07-23:

- status: concluida;
- fonte `Carros na Web` registrada/encontrada como `source_id = 2`;
- `market_carrosnaweb_manufacturers`: `127` linhas;
- `market_carrosnaweb_models`: `1458` linhas;
- `market_carrosnaweb_model_years`: `8914` linhas;
- `aplicacoes_modelo_ano_test.csv`: nao carregado.

Validacao REST apos carga:

- `BYD Dolphin`: encontrado na view;
- `Renault Kwid`: encontrado na view;
- `Changan Uni-T`: encontrado na view;
- `Hyundai HB20`: encontrado na view.

## Uso na classificacao de videos

A taxonomia V2 continua separando:

- `topic_path`: rota de conteudo;
- `technical_context[]`: sistemas, componentes e problemas;
- entidades de veiculo: marca, modelo e ano.

O catalogo Carros na Web atua apenas no terceiro eixo.

Fluxo esperado:

1. Extrair `vehicle_brand`, `vehicle_model` e `vehicle_year_or_generation` da
   descricao/transcricao.
2. Normalizar a chave textual dos campos extraidos.
3. Comparar contra `v_carrosnaweb_vehicle_catalog`.
4. Se houver match, sugerir fabricante/modelo/ano canonicos.
5. Se houver conflito ou ausencia, marcar `vehicle_entity_status = needs_review`.

O catalogo nao deve alterar `topic_path`, `content_type` ou
`audience_intent`.

## Fora de escopo

- ficha tecnica;
- scraping de fichas;
- carga de HTML bruto;
- alteracao do workbook humano;
- alteracao do pipeline de classificacao;
- matriz completa de aliases comerciais.

## Proximo passo recomendado

Criar uma estrutura repetivel futura `vehicle_entity[]`, similar ao
`technical_context[]`, para videos que citam varios veiculos, comparativos ou
versoes especificas.
