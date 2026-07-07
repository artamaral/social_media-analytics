# Fenabrave fase 2 - Plano do item 1

Data: 2026-07-07

## Item

`Ranking dos emplacamentos mes`

Pagina:

- 6

Recorte:

- automoveis
- comerciais leves

Periodo publicado:

- mensal

Fonte piloto:

- PDF oficial Fenabrave `2026_06_02.pdf`
- referencia operacional: `2026-06-01`

## Objetivo

Persistir no banco o ranking mensal de modelos mais emplacados da pagina 6 dos
PDFs Fenabrave, separando automoveis e comerciais leves, com rastreabilidade por
arquivo, preview operacional, validacao e backfill dos PDFs ja preservados.

Este item deve ser a primeira entrega executavel da fase 2 Fenabrave.

Depois de implementado, este item deve fazer parte da inclusao mensal automatica
dos dados Fenabrave. Ele nao deve permanecer como extracao manual avulsa: a cada
novo PDF mensal registrado e validado, a rotina Fenabrave deve executar o item
1, gravar os rankings no banco, atualizar o controle de extracao e sinalizar
falhas ou warnings do periodo.

## Decisao de escopo

Incluir:

- ranking mensal da pagina 6
- coluna esquerda da pagina como `vehicle_category = automoveis`
- coluna direita da pagina como `vehicle_category = comerciais_leves`
- posicao do ranking
- marca extraida do prefixo antes de `/`
- modelo extraido do texto depois de `/`
- nome bruto do PDF
- quantidade mensal de emplacamentos
- ligacao com `source_file_id`
- status de extracao por item

Nao incluir nesta entrega:

- ranking acumulado do item 2
- rankings por marca do item 3
- paginas de venda direta/varejo
- eletrificados
- normalizacao canonica definitiva de marca e modelo
- exibicao nova no Streamlit
- gravacao automatica sem preview

## Evidencia do teste exploratorio

No PDF de junho/2026, a pagina 6 apresentou boa extraibilidade por texto:

- `100` linhas estruturadas
- `50` linhas de automoveis
- `50` linhas de comerciais leves
- ranking iniciou em `1` e foi ate `50` em cada categoria
- as linhas foram extraidas em formato textual previsivel, por exemplo:
  - `1o VW/T CROSS 11.753`
  - `1o FIAT/STRADA 14.303`

Risco observado:

- alguns modelos possuem numeros no nome, como `IVECO/DAILY 30-130`
- o parser nao pode assumir que todo numero antes do ultimo token pertence ao
  volume
- a regra deve capturar o ultimo numero da entrada como `monthly_units` e manter
  o restante como nome bruto do modelo

## Modelo de dados

Usar uma tabela de ranking de modelos, compartilhavel futuramente com outros
itens de ranking por modelo.

Nome proposto:

```text
market_vehicle_model_rankings
```

Campos propostos para a primeira versao:

```text
id
source_file_id
reference_period
item_code
published_period_type
market_scope
vehicle_category
sales_channel
rank_position
brand_name_raw
model_name_raw
model_label_raw
monthly_units
market_share_pct
created_at
updated_at
```

Valores fixos do item 1:

```text
item_code = fenabrave_item_01_ranking_emplacamentos_mes
published_period_type = monthly
market_scope = Brasil
sales_channel = all
market_share_pct = null
```

Chave unica sugerida:

```text
source_file_id,
item_code,
published_period_type,
vehicle_category,
rank_position
```

Observacao:

- a chave unica nao deve depender de `brand_name_raw` ou `model_name_raw`, pois
  o mesmo ranking pode ser reprocessado com correcao de limpeza textual
- `source_file_id` e `item_code` permitem `replace` seguro por item

## Controle de extracao

Registrar o status do item 1 em tabela de controle da fase 2.

Nome proposto:

```text
market_fenabrave_extraction_items
```

Registro esperado para cada PDF:

```text
source_file_id
reference_period
item_code = fenabrave_item_01_ranking_emplacamentos_mes
item_label = Ranking dos emplacamentos mes
pdf_page = 6
published_period_type = monthly
status
row_count
validation_status
validation_notes
```

Estados esperados:

- `pending`: PDF existe, mas item ainda nao foi processado
- `extracted`: preview gerado, ainda nao liberado
- `validated`: linhas gravadas e checks aprovados
- `failed`: parser ou validacao falhou
- `skipped`: item nao aplicavel ao PDF, se algum layout historico nao tiver a
  pagina/bloco

## Parser

Entrada:

- bytes do PDF vindo do Storage ou arquivo local de teste
- pagina `6`

Metodo principal:

1. extrair texto da pagina com `pdfplumber`
2. ignorar cabecalho, rodape e linhas sem ranking
3. identificar entradas com padrao `No MARCA/MODELO VALOR`
4. separar ate duas entradas por linha, pois a pagina traz automoveis e
   comerciais leves lado a lado
5. classificar a primeira entrada como `automoveis`
6. classificar a segunda entrada como `comerciais_leves`
7. capturar:
   - `rank_position`
   - `model_label_raw`
   - `brand_name_raw`
   - `model_name_raw`
   - `monthly_units`

Regra de parsing da entrada:

```text
<rank>o <model_label_raw> <monthly_units>
```

Onde:

- `<rank>` e inteiro
- `<monthly_units>` e o ultimo numero da entrada
- `<model_label_raw>` e todo o texto entre o rank e o ultimo numero
- `brand_name_raw` e o trecho antes de `/`
- `model_name_raw` e o trecho depois de `/`

Fallback:

- se uma linha tiver apenas uma entrada, manter a categoria esperada pela
  posicao visual ou marcar warning
- se o parser nao conseguir separar marca/modelo, gravar `model_label_raw`,
  deixar marca/modelo nulos e bloquear validacao final ate revisao

## Preview operacional

Antes de gravar, exibir:

- periodo
- `source_file_id`
- `storage_path`
- quantidade de linhas extraidas
- top 10 automoveis
- top 10 comerciais leves
- checks de ranking
- warnings de parsing

Exemplo de preview esperado:

```text
vehicle_category     rank_position  model_label_raw      monthly_units
automoveis           1              VW/T CROSS           11753
automoveis           2              VW/POLO              10939
comerciais_leves     1              FIAT/STRADA          14303
comerciais_leves     2              FIAT/TORO            4202
```

## Validacoes

### Validacoes obrigatorias

O item so pode ser marcado como `validated` se:

- pagina 6 existir no PDF
- `reference_period` do arquivo for igual ao periodo da carga
- houver exatamente `50` linhas de `automoveis`
- houver exatamente `50` linhas de `comerciais_leves`
- cada categoria tiver rankings de `1` a `50`
- nao houver `rank_position` duplicado dentro da mesma categoria
- `monthly_units` for inteiro positivo em todas as linhas
- `model_label_raw` nao estiver vazio
- ao menos `95%` das linhas tiverem `brand_name_raw` e `model_name_raw`
  separados
- unidades estiverem em ordem decrescente dentro de cada categoria, aceitando
  empates
- a quantidade gravada no banco bater com `row_count` do controle de extracao

### Validacoes de consistencia

Comparar o item 1 com a tabela ja existente
`market_vehicle_registrations_segment`, quando o periodo ja estiver carregado:

- soma do ranking de automoveis deve ser menor ou igual ao segmento `autos`
- soma do ranking de comerciais leves deve ser menor ou igual ao segmento
  `comerciais_leves`
- se a soma do top 50 for maior que o total do segmento correspondente, bloquear
  a validacao

Observacao:

- a soma do ranking top 50 nao precisa bater com o total do segmento, pois a
  pagina e um ranking, nao uma tabela exaustiva de todos os modelos

### Validacoes de reprocessamento

- rodar `--dry-run` nao deve gravar linhas
- rodar `--write` sem `--replace` nao deve duplicar linhas
- rodar `--write --replace` deve apagar e recriar somente:
  - mesmo `source_file_id`
  - mesmo `item_code`
  - mesmo `published_period_type`
- reprocessar o mesmo PDF deve manter `100` linhas finais

## Backfill

O backfill do item 1 deve ser feito para todos os PDFs Fenabrave ja registrados
em `market_source_files` e com PDF preservado no Storage.

Ordem:

```text
1. Listar PDFs Fenabrave com storage_bucket e storage_path
2. Criar ou atualizar controle do item 1 como pending
3. Rodar dry-run do item 1 para cada PDF
4. Gerar relatorio de cobertura
5. Revisar periodos com warning ou failed
6. Rodar write para periodos aprovados
7. Rodar validacoes SQL
8. Marcar item como validated ou failed por periodo
9. Gerar relatorio final de cobertura
```

Regra:

- carregar todos os meses aplicaveis antes de considerar o item 1 pronto para
  consumo analitico

## Primeira atividade de implementacao

Atividade:

- preparar a base persistente do item 1 antes de escrever o parser

Objetivo:

- criar o contrato minimo de banco e validacao para que a extracao da pagina 6
  tenha destino claro, reprocessamento seguro e cobertura auditavel
- preparar a estrutura para que o item 1 seja chamado pela rotina mensal
  automatica da Fenabrave, junto com os demais itens ativos da fase 2

Resultado esperado:

- DDL versionada para controle de itens Fenabrave fase 2
- DDL versionada para ranking mensal de modelos
- queries de validacao inicial documentadas ou versionadas
- contrato de campos confirmado para o parser
- nenhum dado real carregado ainda

### Escopo da atividade 1

Criar ou preparar:

- `market_fenabrave_extraction_items`
- `market_vehicle_model_rankings`
- constraints e indices minimos
- comentarios de uso das tabelas, quando o padrao SQL do repositorio permitir
- query de cobertura do item 1 por PDF
- query de validacao de duplicidade e quantidade de linhas
- contrato de status que permita a rotina mensal diferenciar sucesso, warning,
  falha e pendencia do item 1

Nao criar nesta atividade:

- parser Python
- carga de dados reais
- view de dashboard
- alteracao no Streamlit
- backfill historico

### Arquivos esperados

Arquivos SQL sugeridos:

```text
sql/ddl/tables/013_create_market_fenabrave_extraction_items.sql
sql/ddl/tables/014_create_market_vehicle_model_rankings.sql
```

Arquivo opcional de validacoes:

```text
sql/ddl/tests/002_test_fenabrave_item1_model_rankings.sql
```

Se o repositorio preferir manter validacoes junto da especificacao, registrar as
queries neste plano e criar o arquivo de teste apenas quando a carga existir.

### DDL conceitual - controle do item

Tabela:

```text
public.market_fenabrave_extraction_items
```

Campos:

```text
id bigserial primary key
source_file_id bigint not null references public.market_source_files(id)
reference_period date not null
item_code text not null
item_label text not null
pdf_page integer not null
published_period_type text not null
market_scope text not null default 'Brasil'
status text not null default 'pending'
row_count integer
validation_status text
validation_notes text
created_at timestamptz not null default now()
updated_at timestamptz not null default now()
```

Constraints minimas:

```text
unique(source_file_id, item_code)
status in ('pending', 'extracted', 'validated', 'failed', 'skipped', 'warning_accepted')
published_period_type in ('monthly', 'accumulated')
validation_status is null or in ('passed', 'warning', 'failed')
row_count is null or row_count >= 0
pdf_page > 0
```

Indice recomendado:

```text
(reference_period, item_code, status)
```

### DDL conceitual - ranking de modelos

Tabela:

```text
public.market_vehicle_model_rankings
```

Campos:

```text
id bigserial primary key
source_file_id bigint not null references public.market_source_files(id)
reference_period date not null
item_code text not null
published_period_type text not null
market_scope text not null default 'Brasil'
vehicle_category text not null
sales_channel text not null default 'all'
rank_position integer not null
brand_name_raw text
model_name_raw text
model_label_raw text not null
monthly_units integer
market_share_pct numeric(8, 4)
created_at timestamptz not null default now()
updated_at timestamptz not null default now()
```

Constraints minimas:

```text
unique(source_file_id, item_code, published_period_type, vehicle_category, rank_position)
published_period_type in ('monthly', 'accumulated')
vehicle_category in ('automoveis', 'comerciais_leves')
sales_channel in ('all', 'retail', 'direct')
rank_position between 1 and 200
monthly_units is null or monthly_units >= 0
market_share_pct is null or market_share_pct between 0 and 100
```

Indice recomendado:

```text
(reference_period, item_code, vehicle_category, rank_position)
```

### Contrato do item 1

Para o item 1, todo insert deve usar:

```text
item_code = fenabrave_item_01_ranking_emplacamentos_mes
published_period_type = monthly
market_scope = Brasil
sales_channel = all
market_share_pct = null
vehicle_category in ('automoveis', 'comerciais_leves')
rank_position between 1 and 50
monthly_units not null
```

Campos obrigatorios para cada linha do item 1:

- `source_file_id`
- `reference_period`
- `item_code`
- `published_period_type`
- `vehicle_category`
- `sales_channel`
- `rank_position`
- `model_label_raw`
- `monthly_units`

Campos desejaveis, mas que podem virar warning antes de bloquear:

- `brand_name_raw`
- `model_name_raw`

Contrato na rotina mensal:

- quando um novo PDF Fenabrave mensal estiver registrado em
  `market_source_files`, a rotina deve criar ou atualizar o controle do item 1
  para esse `source_file_id`
- apos a fase 1 validar o periodo base, a rotina deve executar o parser do item
  1 em modo operacional
- se a extracao passar, a rotina deve gravar `100` linhas esperadas e marcar o
  item como `validated`
- se houver divergencia revisavel, a rotina deve manter os dados fora do consumo
  analitico ou marcar `warning_accepted` apenas apos aceite explicito
- se a extracao falhar, a rotina deve marcar `failed` e manter a falha visivel
  na cobertura mensal
- o item 1 deve poder ser reprocessado isoladamente sem afetar a fase 1 nem os
  demais itens da fase 2

### Query de cobertura inicial

Objetivo:

- identificar todos os PDFs Fenabrave existentes e o status do item 1.

Query conceitual:

```sql
SELECT
  f.reference_period,
  f.id AS source_file_id,
  f.storage_bucket,
  f.storage_path,
  f.extraction_status AS source_file_status,
  i.status AS item_status,
  i.row_count,
  i.validation_status,
  CASE
    WHEN i.id IS NULL THEN 'missing_control'
    WHEN i.status IN ('validated', 'warning_accepted') THEN 'covered'
    WHEN i.status IN ('pending', 'extracted') THEN 'pending'
    WHEN i.status = 'failed' THEN 'failed'
    ELSE 'review'
  END AS coverage_status
FROM public.market_source_files f
JOIN public.market_data_sources s ON s.id = f.source_id
LEFT JOIN public.market_fenabrave_extraction_items i
  ON i.source_file_id = f.id
 AND i.item_code = 'fenabrave_item_01_ranking_emplacamentos_mes'
WHERE s.source_name = 'Fenabrave'
ORDER BY f.reference_period;
```

### Query de validacao estrutural inicial

Objetivo:

- validar que a tabela do item 1 tem exatamente `50` posicoes por categoria em
  cada PDF processado.

Query conceitual:

```sql
SELECT
  source_file_id,
  reference_period,
  vehicle_category,
  COUNT(*) AS row_count,
  MIN(rank_position) AS min_rank,
  MAX(rank_position) AS max_rank,
  COUNT(DISTINCT rank_position) AS distinct_ranks,
  SUM(CASE WHEN monthly_units IS NULL OR monthly_units <= 0 THEN 1 ELSE 0 END)
    AS invalid_units,
  SUM(CASE WHEN model_label_raw IS NULL OR trim(model_label_raw) = '' THEN 1 ELSE 0 END)
    AS missing_model_label
FROM public.market_vehicle_model_rankings
WHERE item_code = 'fenabrave_item_01_ranking_emplacamentos_mes'
GROUP BY source_file_id, reference_period, vehicle_category
ORDER BY reference_period, vehicle_category;
```

Regra de aceite da query:

- `row_count = 50`
- `min_rank = 1`
- `max_rank = 50`
- `distinct_ranks = 50`
- `invalid_units = 0`
- `missing_model_label = 0`

### Passo a passo da atividade 1

1. Revisar os DDLs existentes de Fenabrave:
   `010_create_market_data_sources.sql`,
   `011_create_market_source_files.sql` e
   `012_create_market_vehicle_registrations_segment.sql`.
2. Criar DDL de `market_fenabrave_extraction_items` seguindo os padroes de
   nomes, constraints e timestamps do repositorio.
3. Criar DDL de `market_vehicle_model_rankings` com o contrato minimo do item 1,
   mas sem limitar a tabela a apenas este item.
4. Adicionar constraints para impedir categorias, periodo publicado, canal e
   valores numericos invalidos.
5. Adicionar indices para consultas por periodo, item, categoria e ranking.
6. Documentar no proprio SQL ou neste plano as queries de cobertura e validacao.
7. Conferir que o DDL nao exige dados reais para ser aplicado.
8. Marcar a atividade pronta para o parser somente quando as tabelas tiverem
   destino claro e reprocessamento seguro por chave unica.

### Criterios de pronto da atividade 1

A atividade 1 esta pronta quando:

- os arquivos SQL estiverem criados e versionados
- a modelagem permitir gravar `100` linhas por PDF para o item 1
- existir chave unica que impeça duplicidade por `source_file_id`, categoria e
  posicao
- existir controle de status por `source_file_id` e `item_code`
- o controle de status for suficiente para integrar o item 1 a inclusao mensal
  automatica da Fenabrave
- as queries de cobertura e validacao estiverem documentadas
- nenhuma dependencia do parser ou do Streamlit for necessaria para aplicar o
  DDL

### Proxima atividade depois desta

Depois da atividade 1, implementar a atividade 2:

- parser `dry-run` da pagina 6 para um PDF local ou baixado do Storage, gerando
  preview estruturado do item 1 sem gravar no banco

## Views futuras

Depois que o item 1 estiver carregado e validado, criar view de consumo.

Nome sugerido:

```text
v_market_fenabrave_model_rankings
```

Filtro minimo para consumo:

```text
item_code = 'fenabrave_item_01_ranking_emplacamentos_mes'
published_period_type = 'monthly'
status in ('validated', 'warning_accepted')
```

A view deve expor:

- periodo
- categoria
- rank
- marca
- modelo
- emplacamentos mensais
- fonte
- URL do PDF
- storage path
- data de captura
- status de validacao

## Criterios de aceite

O item 1 sera considerado concluido quando:

- DDL das tabelas necessarias estiver versionada
- parser da pagina 6 estiver implementado
- `dry-run` gerar preview claro para junho/2026
- validacoes obrigatorias passarem para junho/2026
- todos os PDFs ja carregados tiverem status conhecido para o item 1
- todos os periodos aplicaveis estiverem gravados ou documentados como excecao
- reprocessamento com `--replace` estiver validado
- cobertura historica nao mostrar `missing_from_db` para item 1
- nenhuma linha for gravada sem `source_file_id`, `reference_period`,
  `vehicle_category`, `rank_position`, `model_label_raw` e `monthly_units`

## Proximas atividades apos o item 1

Depois da conclusao do item 1:

- resolver a pendencia do item 2, confirmando onde esta o ranking acumulado dos
  emplacamentos e se a pagina indicada precisa ser corrigida
- implementar o item 3, ranking por marca mes da pagina 8, em entrega separada
